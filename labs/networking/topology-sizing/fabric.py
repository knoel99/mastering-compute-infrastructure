#!/usr/bin/env python3
"""Fat-tree (folded Clos) sizing calculator for GPU training fabrics.

Model (all switches have the same radix r = number of ports):
  * level 1 : one switch, up to r endpoints;
  * level 2 : leaves and spines.  A leaf has `leaf_down` ports towards endpoints and
              r - leaf_down ports towards spines (one link to each of the u spines).
  * level 3 : leaves, aggregation switches ("spine" below) grouped in pods, and cores.
              Tiers above the leaf are non-blocking (r/2 down, r/2 up).

Oversubscription is only modelled at the leaf tier: ratio = leaf_down / leaf_up.
The model ignores management nodes, storage fabrics, spare ports and breakout cables.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Fabric:
    endpoints: int
    radix: int
    levels: int
    leaf_down: int
    leaf_up: int
    leaves: int
    spines: int
    cores: int
    host_links: int
    tier1_links: int  # leaf -> spine
    tier2_links: int  # spine -> core (level 3 only)

    @property
    def switches(self) -> int:
        return self.leaves + self.spines + self.cores

    @property
    def oversubscription(self) -> float:
        """Endpoint capacity divided by the narrowest uplink capacity (>= 1)."""
        if self.levels == 1:
            return 1.0
        narrowest = min(self.tier1_links, self.tier2_links) if self.levels == 3 else self.tier1_links
        return max(1.0, self.endpoints / narrowest)

    def bisection_tbps(self, link_gbps: float) -> float:
        """Bisection bandwidth in Tb/s, one direction, for the worst-case cut."""
        cap = self.endpoints
        if self.levels >= 2:
            cap = min(cap, self.tier1_links)
        if self.levels == 3:
            cap = min(cap, self.tier2_links)
        return cap / 2 * link_gbps / 1000.0

    def optical_transceivers(self) -> int:
        """Two transceivers per inter-switch link (assumes every such link is optical)."""
        return 2 * (self.tier1_links + self.tier2_links)

    def as_dict(self, link_gbps: float = 400.0) -> dict:
        d = asdict(self)
        d.update(
            switches=self.switches,
            oversubscription=round(self.oversubscription, 3),
            bisection_tbps=round(self.bisection_tbps(link_gbps), 3),
            optical_transceivers=self.optical_transceivers(),
        )
        return d


def capacity(radix: int, levels: int, leaf_down: int | None = None) -> int:
    """Largest number of endpoints reachable with `levels` tiers."""
    d = radix // 2 if leaf_down is None else leaf_down
    if levels == 1:
        return radix
    if levels == 2:
        return d * radix
    if levels == 3:
        return d * radix * radix // 2
    raise ValueError("levels must be 1, 2 or 3")


def size_fabric(endpoints: int, radix: int, leaf_down: int | None = None, levels: int | None = None) -> Fabric:
    if endpoints < 1 or radix < 4 or radix % 2:
        raise ValueError("need endpoints >= 1 and an even radix >= 4")
    d = radix // 2 if leaf_down is None else leaf_down
    if not 1 <= d < radix:
        raise ValueError("leaf_down must be in [1, radix-1]")
    u = radix - d
    if levels is None:
        levels = next((lv for lv in (1, 2, 3) if capacity(radix, lv, d) >= endpoints), 0)
        if not levels:
            raise ValueError(f"{endpoints} endpoints exceed the 3-level capacity {capacity(radix, 3, d)}")
    elif capacity(radix, levels, d) < endpoints:
        raise ValueError(f"{levels} levels cannot hold {endpoints} endpoints with radix {radix}")
    if levels == 1:
        return Fabric(endpoints, radix, 1, endpoints, 0, 1, 0, 0, endpoints, 0, 0)
    leaves = math.ceil(endpoints / d)
    t1 = leaves * u
    if levels == 2:
        return Fabric(endpoints, radix, 2, d, u, leaves, math.ceil(t1 / radix), 0, endpoints, t1, 0)
    half = radix // 2
    pods = math.ceil(leaves / half)
    spines = pods * u
    t2 = spines * half
    return Fabric(endpoints, radix, 3, d, u, leaves, spines, math.ceil(t2 / radix), endpoints, t1, t2)


# Header sizes of a RoCE v2 packet over IPv4 (Linux include/rdma/ib_pack.h: IB_ETH_BYTES 14, IB_IP4_BYTES 20,
# IB_UDP_BYTES 8, IB_BTH_BYTES 12, IB_ICRC_BYTES 4), plus the Ethernet frame check sequence, preamble and
# inter-frame gap (24 bytes, standard Ethernet values NOT re-read for this module).
IB_MTUS = (256, 512, 1024, 2048, 4096)  # enum ibv_mtu of libibverbs
ROCE_IP_OVERHEAD = 20 + 8 + 12 + 4
ROCE_FRAME_OVERHEAD = 14 + ROCE_IP_OVERHEAD
ETHERNET_WIRE_EXTRA = 24


def min_ip_mtu(payload: int) -> int:
    """Smallest IP MTU able to carry one RoCE v2 packet with `payload` bytes (IP + UDP + BTH + payload + ICRC)."""
    return payload + ROCE_IP_OVERHEAD


def largest_ib_mtu(ip_mtu: int) -> int:
    """Largest InfiniBand MTU whose packets fit in an IP MTU (0 if none)."""
    return max((m for m in IB_MTUS if min_ip_mtu(m) <= ip_mtu), default=0)


def goodput_fraction(payload: int) -> float:
    """Payload bytes divided by the bytes the packet occupies on the wire."""
    return payload / (payload + ROCE_FRAME_OVERHEAD + ETHERNET_WIRE_EXTRA)


def al_fares(k: int) -> dict:
    """k-ary fat-tree of Al-Fares, Loukissas and Vahdat (SIGCOMM 2008)."""
    if k % 2:
        raise ValueError("k must be even")
    return {"hosts": k**3 // 4, "switches": 5 * k * k // 4, "core": (k // 2) ** 2, "pods": k}


def rail_optimized(nodes: int, rails: int, radix: int, leaf_down: int | None = None) -> dict:
    """One independent fabric per rail (rail r links GPU r of every node)."""
    per_rail = size_fabric(nodes, radix, leaf_down)
    return {
        "rails": rails,
        "per_rail": per_rail.as_dict(),
        "total_switches": rails * per_rail.switches,
        "total_host_links": rails * per_rail.host_links,
    }


def effective_bandwidth(link_gbs: float, oversub: float, crossing_fraction: float) -> float:
    """Toy model: a fraction f of the bytes crosses the oversubscribed tier at B/o, the rest at B.

    Time per byte = ((1 - f) + f*o) / B, hence B_eff = B / (1 + f*(o - 1)).
    """
    if not 0 <= crossing_fraction <= 1 or oversub < 1:
        raise ValueError("need 0 <= f <= 1 and oversub >= 1")
    return link_gbs / (1 + crossing_fraction * (oversub - 1))


def compare_published(path: Path | None = None) -> list[dict]:
    """Recompute the published component counts and report the differences."""
    path = path or Path(__file__).with_name("published.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for row in data["superpod_h100"]["rows"]:
        fab = size_fabric(row["gpus"], data["superpod_h100"]["radix"])
        out.append(
            {
                "su": row["su"],
                "gpus": row["gpus"],
                "published": {k: row.get(k) for k in ("leaf", "spine", "core")},
                "computed": {"leaf": fab.leaves, "spine": fab.spines, "core": fab.cores},
                "match": row.get("leaf") == fab.leaves and row.get("spine") == fab.spines and (row.get("core") or 0) == fab.cores,
                "note": row.get("note", ""),
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--endpoints", type=int, help="number of GPU network ports (one per endpoint)")
    ap.add_argument("--radix", type=int, default=64)
    ap.add_argument("--leaf-down", type=int, help="leaf ports towards endpoints (default radix/2)")
    ap.add_argument("--link-gbps", type=float, default=400.0)
    ap.add_argument("--compare", action="store_true", help="recompute published configurations")
    ap.add_argument("--goodput", type=int, nargs="+", metavar="PAYLOAD", help="goodput of RoCE v2 packets of these payload sizes (bytes)")
    args = ap.parse_args()
    if args.goodput:
        for m in args.goodput:
            print(f"payload {m:>5} B: goodput {goodput_fraction(m):.4f} = {50 * goodput_fraction(m):.2f} GB/s of 50; needs IP MTU >= {min_ip_mtu(m)}")
        print("largest IB MTU for IP MTU 1500:", largest_ib_mtu(1500))
        return
    if args.compare:
        for r in compare_published():
            flag = "OK  " if r["match"] else "DIFF"
            print(f"{flag} SU={r['su']:>2} gpus={r['gpus']:>6} published={r['published']} computed={r['computed']} {r['note']}")
        return
    if args.endpoints is None:
        ap.error("--endpoints or --compare required")
    fab = size_fabric(args.endpoints, args.radix, args.leaf_down)
    print(json.dumps(fab.as_dict(args.link_gbps), indent=2))


if __name__ == "__main__":
    main()
