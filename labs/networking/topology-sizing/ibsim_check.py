#!/usr/bin/env python3
"""Run a real OpenSM (fat-tree routing engine) on a simulated InfiniBand fabric (ibsim).

The fabric is generated from the same parameters as the calculator in fabric.py:
radix r, leaf_down endpoints per leaf, one link from every leaf to each of the u = r - leaf_down spines.
Checks: (1) OpenSM's `ftree` engine accepts the topology, (2) the discovered switch/endpoint/link counts equal the
calculator's, (3) the leaf forwarding tables spread remote destinations over the uplinks (max-min <= 1).
Needs the Ubuntu/Debian packages ibsim-utils, opensm and infiniband-diags (the simulator is synthetic: no packets flow).
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from fabric import size_fabric

SIM_SO = "/usr/lib/x86_64-linux-gnu/umad2sim/libumad2sim.so"


def netfile(radix: int, down: int, leaves: int, drop_link: bool = False) -> str:
    """ibsim net description: spines S0..S(u-1), leaves L0.., hosts H0..; link leaf l <-> spine s.

    ibsim wants every declared port connected, so a switch is declared with the number of its highest connected
    port: with drop_link the last uplink of the last leaf is removed and both its ends shrink by one port.
    """
    up = radix - down
    sg = lambda i: "0002c90200%06x" % (0x1000 + i)  # noqa: E731
    lg = lambda i: "0002c90201%06x" % (0x2000 + i)  # noqa: E731
    hg = lambda i: "0002c90300%06x" % (0x3000 + i)  # noqa: E731
    slid = lambda s: 1 + s  # noqa: E731
    llid = lambda l: 1 + up + l  # noqa: E731
    hlid = lambda h: 1 + up + leaves + h  # noqa: E731
    dropped = (leaves - 1, up - 1) if drop_link else None  # (leaf, spine) link removed
    out: list[str] = []
    for s in range(up):
        ports = [l for l in range(leaves) if dropped != (l, s)]
        out.append(f'Switch {len(ports)} "S-{sg(s)}" # "spine{s}" base port 0 lid {slid(s)} lmc 0')
        for l in ports:
            out.append(f'[{l + 1}] "S-{lg(l)}"[{down + s + 1}] # "leaf{l}" lid {llid(l)} 4xEDR')
    for l in range(leaves):
        spines = [s for s in range(up) if dropped != (l, s)]
        out.append(f'Switch {down + len(spines)} "S-{lg(l)}" # "leaf{l}" base port 0 lid {llid(l)} lmc 0')
        for h in range(down):
            out.append(f'[{h + 1}] "H-{hg(l * down + h)}"[1] # "host{l * down + h}" lid {hlid(l * down + h)} 4xEDR')
        for s in spines:
            out.append(f'[{down + s + 1}] "S-{sg(s)}"[{l + 1}] # "spine{s}" lid {slid(s)} 4xEDR')
    for h in range(leaves * down):
        l = h // down
        out.append(f'Ca 1 "H-{hg(h)}" # "host{h} HCA-1"')
        out.append(f'[1] "S-{lg(l)}"[{h % down + 1}] # lid {hlid(h)} lmc 0 "leaf{l}" lid {llid(l)} 4xEDR')
    return "\n".join(out) + "\n"


def run(cmd: list[str], env: dict, timeout: int = 60) -> str:
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout, check=False)
    return r.stdout + r.stderr


def check(radix: int, down: int, leaves: int, drop_link: bool = False, show_links: bool = False) -> dict:
    fab = size_fabric(leaves * down, radix, down, levels=2)
    tmp = Path(tempfile.mkdtemp(prefix="ibsim-"))
    (tmp / "net.txt").write_text(netfile(radix, down, leaves, drop_link), encoding="utf-8")
    env = dict(os.environ, LD_PRELOAD=SIM_SO, OSM_CACHE_DIR=str(tmp), OSM_TMP_DIR=str(tmp))
    sim = subprocess.Popen(["ibsim", "-s", str(tmp / "net.txt")], stdout=open(tmp / "ibsim.log", "w"), stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            if "Network simulator ready" in (tmp / "ibsim.log").read_text():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("ibsim did not become ready: " + (tmp / "ibsim.log").read_text()[-300:])
        guid = run(["ibstat", "-p"], env).split()[-1]
        run(["opensm", "-g", guid, "-f", str(tmp / "osm.log"), "-R", "ftree", "-o", "-r", "--dump_files_dir", str(tmp)], env)
        osm = (tmp / "osm.log").read_text()
        disc = run(["ibnetdiscover"], env)
        switches = {m.group(1): int(m.group(2)) for m in re.finditer(r'^Switch\s+\d+ "S-\w+"\s+# "(\w+)" base port 0 lid (\d+)', disc, re.M)}
        cas = len(re.findall(r"^Ca\s", disc, re.M))
        sections = re.split(r"^(?=Switch|Ca)", disc, flags=re.M)
        sw_sections = [s for s in sections if s.startswith("Switch")]
        host_links = sum(len(re.findall(r'^\[\d+\]\s+"H-', s, re.M)) for s in sw_sections)
        sw_links = sum(len(re.findall(r'^\[\d+\]\s+"S-', s, re.M)) for s in sw_sections) // 2
        link_lines: list[str] = []
        if show_links:  # one host link of the last leaf, as printed by iblinkinfo (lane rate, state, width)
            last = f'"leaf{leaves - 1}"'
            link_lines = [l.strip() for l in run(["iblinkinfo"], env).splitlines() if l.lstrip().startswith("0x") and last in l][:1]
        spread = {}
        for name, lid in switches.items():
            if not name.startswith("leaf"):
                continue
            lft = run(["ibroute", str(lid)], env)
            ports = {}
            for m in re.finditer(r"^0x[0-9a-f]+ (\d+) : \(Channel Adapter portguid \S+: 'host(\d+) HCA-1'\)", lft, re.M):
                port, host = int(m.group(1)), int(m.group(2))
                if host // down != int(name[4:]):
                    ports[port] = ports.get(port, 0) + 1
            spread[name] = ports
        return {
            "ftree_ok": "ftree tables configured on all switches" in osm,
            "subnet_up": "SUBNET UP" in osm,
            "engine": "ftree" if "ftree tables configured on all switches" in osm else ("minhop" if "minhop tables configured on all switches" in osm else "unknown"),
            "osm_notes": [l.split("-> ", 1)[-1] for l in osm.splitlines() if "not a fat-tree" in l or "cannot build lid matrices" in l or "tables configured" in l],
            "switches": len(switches),
            "hosts": cas,
            "host_links": host_links,
            "switch_links": sw_links,
            "expected": {"switches": fab.switches, "hosts": fab.endpoints, "host_links": fab.host_links, "switch_links": fab.tier1_links},
            "uplink_spread": spread,
            "link_lines": link_lines,
        }
    finally:
        sim.terminate()
        sim.wait(timeout=10)
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radix", type=int, default=8)
    ap.add_argument("--down", type=int, default=4)
    ap.add_argument("--leaves", type=int, default=8)
    ap.add_argument("--drop-link", action="store_true", help="negative control: remove one leaf-spine link")
    ap.add_argument("--iblinkinfo", action="store_true", help="also print one host link as seen by iblinkinfo")
    a = ap.parse_args()
    res = check(a.radix, a.down, a.leaves, a.drop_link, a.iblinkinfo)
    exp = res["expected"]
    ok = res["ftree_ok"] and res["subnet_up"]
    ok &= (res["switches"], res["hosts"], res["host_links"], res["switch_links"]) == (exp["switches"], exp["hosts"], exp["host_links"], exp["switch_links"])
    worst = 0
    for name, ports in res["uplink_spread"].items():
        vals = list(ports.values())
        worst = max(worst, max(vals) - min(vals)) if vals else worst
    ok &= worst <= 1
    print(f"radix={a.radix} down={a.down} up={a.radix - a.down} leaves={a.leaves}: engine={res['engine']} switches={res['switches']}/{exp['switches']} "
          f"hosts={res['hosts']}/{exp['hosts']} host_links={res['host_links']}/{exp['host_links']} switch_links={res['switch_links']}/{exp['switch_links']} "
          f"max_uplink_imbalance={worst}")
    print("OpenSM said:", "; ".join(res["osm_notes"]))
    print("leaf0 remote destinations per uplink port:", res["uplink_spread"].get("leaf0"))
    for line in res["link_lines"]:
        print("iblinkinfo:", line)
    print("OK ibsim-opensm" if ok else "FAIL ibsim-opensm")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
