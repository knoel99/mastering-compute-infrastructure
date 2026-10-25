#!/usr/bin/env python3
"""Generate the SYNTHETIC NCCL_DEBUG=INFO fixtures used by the lab (deterministic, no GPU involved).

Every message template below was read in the NCCL sources (NVIDIA/nccl, master, read on 2026-10-24):
  src/init.cc            "comm %p rank %d nRanks %d nNodes %d localRanks %d localRank %d MNNVL %d"
                         "Ring %02d : %d -> %d -> %d", "Trees%s" (" [%d] %d/%d/%d->%d->%d" per channel)
                         "%d coll channels, %d collnet channels, %d nvls channels, %d p2p channels, %d p2p channels per peer"
                         "... comm %p rank %d nranks %d cudaDev %d nvmlDev %d busId %lx commId 0x%llx - Init COMPLETE"
                         "Using network %s"
  src/graph/search.cc    "Pattern %d, crossNic %d, nChannels %d, bw %f/%f, type %s/%s, sameChannels %d"
  src/graph/topo.cc      "NET/%s : GPU Direct RDMA %s for HCA %d '%s'"
  src/transport/p2p.cc   "Channel %02d/%01d : %d[%d] -> %d[%d] via P2P/CUMEM"
  src/transport/net.cc   "Channel %02d/%d : %d[%d] -> %d[%d] [send] via NET/%s/%d/GDRDMA"
The numbers (bandwidths, ids, pids) are invented: the files test a parser, they describe no real machine.
"""
from __future__ import annotations

import random
from pathlib import Path

HERE = Path(__file__).parent / "fixtures"
GPUS = 8
CHANNELS = 4
VERSION = "NCCL version 2.30.3+cuda13.0"


def ring_order(channel: int, nodes: int) -> list[int]:
    """Ranks in ring order for one channel: each node is walked from a different GPU so that the
    GPU leaving the node (hence the NIC used) changes from channel to channel."""
    order = []
    for n in range(nodes):
        order += [n * GPUS + (channel * 2 + i) % GPUS for i in range(GPUS)]
    return order


def gen(nodes: int = 2, *, socket: bool = False, missing_hca: dict[int, int] | None = None, gdr_off: set[tuple[int, int]] | None = None,
        no_init_complete: set[int] | None = None, warn: bool = False) -> str:
    rng = random.Random(1234)  # deterministic pointers
    n_ranks = nodes * GPUS
    missing_hca = missing_hca or {}
    gdr_off = gdr_off or set()
    no_init_complete = no_init_complete or set()
    out = [VERSION]

    def nic_name(node: int, k: int) -> str:
        """NIC used by GPU k of a node: its own card, or the previous one when its card is missing (invented rule);
        the /GDRDMA suffix is dropped when GPU Direct RDMA is disabled for that card."""
        h = (k - 1) % GPUS if missing_hca.get(node) == k else k
        return f"IB/{h}" + ("" if (node, h) in gdr_off else "/GDRDMA")

    for r in range(n_ranks):
        node, k = divmod(r, GPUS)
        host = f"node-{node + 1:02d}"
        p = lambda msg, r=r, host=host, k=k: out.append(f"{host}:{4000 + r}:{4000 + r} [{k}] NCCL INFO {msg}")  # noqa: E731
        ptr = f"0x{rng.getrandbits(40):x}"
        p(f"Bootstrap: Using eth0:10.1.0.{11 + node}<0>")
        if socket:
            p("Using network Socket")
        else:
            p("Initialized NET plugin IB")
            p("Using network IB")
            for h in range(GPUS):
                if missing_hca.get(node) == h:
                    continue
                state = "Disabled" if (node, h) in gdr_off else "Enabled"
                p(f"NET/IB : GPU Direct RDMA {state} for HCA {h} 'mlx5_{h}'")
        p(f"comm {ptr} rank {r} nRanks {n_ranks} nNodes {nodes} localRanks {GPUS} localRank {k} MNNVL 0")
        p(f"Pattern 4, crossNic {1 if socket else 0}, nChannels {CHANNELS}, bw 40.000000/{12.0 if socket else 40.0:f}, type NVL/{'SYS' if socket else 'PIX'}, sameChannels 1")
        trees = ""
        for c in range(CHANNELS):
            order = ring_order(c, nodes)
            i = order.index(r)
            prev, nxt = order[i - 1], order[(i + 1) % n_ranks]
            p(f"Ring {c:02d} : {prev} -> {r} -> {nxt}")
            trees += f" [{c}] {nxt if nxt // GPUS == node else -1}/-1/-1->{r}->{prev if prev // GPUS == node else -1}"
        p(f"Trees{trees}")
        p(f"{CHANNELS} coll channels, 0 collnet channels, 0 nvls channels, {CHANNELS} p2p channels, 2 p2p channels per peer")
        for c in range(CHANNELS):
            order = ring_order(c, nodes)
            i = order.index(r)
            nxt = order[(i + 1) % n_ranks]
            prv = order[i - 1]
            if nxt // GPUS == node:
                p(f"Channel {c:02d}/0 : {r}[{k}] -> {nxt}[{nxt % GPUS}] via P2P/CUMEM")
            else:
                dev = "Socket/0" if socket else nic_name(node, k)
                p(f"Channel {c:02d}/0 : {r}[{k}] -> {nxt}[{nxt % GPUS}] [send] via NET/{dev}")
            if prv // GPUS != node:
                dev = "Socket/0" if socket else nic_name(node, k)
                p(f"Channel {c:02d}/0 : {prv}[{prv % GPUS}] -> {r}[{k}] [receive] via NET/{dev}")
        if warn:
            out.append(f"[2026-05-05 06:16:47] {host}:{4000 + r}:{4000 + r} [{k}] transport/net_ib.cc:1212 NCCL WARN NET/IB : Got async event : port error")
        if r not in no_init_complete:
            p(f"ncclCommInitRank comm {ptr} rank {r} nranks {n_ranks} cudaDev {k} nvmlDev {k} busId {0x1b000 + 0x1000 * k:x} commId 0x{rng.getrandbits(60):x} - Init COMPLETE")
    return "\n".join(out) + "\n"


PUBLIC = """\
# PUBLIC excerpt: NCCL user guide, "Logging" page, https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting/logging.html
# (page header shows NCCL 2.32; excerpts are labelled there as "NCCL logs; only the relevant lines are shown"; read on 2026-10-24)
NCCL version 2.30.3+cuda13.0
[2026-05-05 06:16:47] node-01:189884:189884 [3] plugin/net.cc:334 NCCL WARN Failed to initialize any NET plugin
[2026-05-05 06:16:47] node-01:189884:189884 [3] plugin/net.cc:208 (ncclNetPluginInit) NCCL ATTN Failed to initialize NET plugin IB
node-01:3873285:3873285 [0] NCCL INFO Initialized NET plugin IB
node-01:3873285:3873285 [0] NCCL INFO Assigned NET plugin IB to comm
node-01:3873285:3873285 [0] NCCL INFO Using network IB
node-01:3873285:3873285 [0] NCCL INFO DMA-BUF is available on GPU device 0
"""


def main() -> None:
    HERE.mkdir(exist_ok=True)
    hdr = "# SYNTHETIC fixture generated by make_fixtures.py (formats read in the NCCL sources; values invented)\n"
    files = {
        "healthy_2node_ib.log": gen(2),
        "socket_fallback.log": gen(2, socket=True),
        "degraded_rail.log": gen(2, missing_hca={1: 5}, gdr_off={(0, 3)}),
        "hang_in_init.log": gen(2, no_init_complete={11}),
        "healthy_with_warning.log": gen(2, warn=True),
    }
    for name, text in files.items():
        (HERE / name).write_text(hdr + text, encoding="utf-8")
    (HERE / "public_nccl_docs.log").write_text(PUBLIC, encoding="utf-8")
    for name in [*files, "public_nccl_docs.log"]:
        print(name, len((HERE / name).read_text().splitlines()), "lines")


if __name__ == "__main__":
    main()
