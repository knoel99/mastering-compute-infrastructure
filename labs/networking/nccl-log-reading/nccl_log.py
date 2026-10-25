#!/usr/bin/env python3
"""Parse an NCCL_DEBUG=INFO log and report topology, transports and likely problems.

Usage:  python3 nccl_log.py LOG [--json] [--expect code1,code2]
Exit status 0 when the set of error-level findings equals the --expect set (default: empty set).

The message formats come from the NCCL sources (see make_fixtures.py).  Formats change between NCCL versions:
a line that does not match is ignored, never an error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

LINE = re.compile(
    r"^(?:\[(?P<ts>[^\]]+)\]\s+)?(?P<host>[\w.\-]+):(?P<pid>\d+):(?P<tid>\d+)\s+\[(?P<dev>\d+)\]\s+"
    r"(?:(?P<src>[\w/.+\-]+:\d+)\s+(?:\((?P<fn>\w+)\)\s+)?)?NCCL\s+(?P<level>[A-Z]+)\s+(?P<msg>.*?)\s*$"
)
VERSION = re.compile(r"^NCCL version (\S+)")
COMM = re.compile(r"comm (0x[0-9a-f]+) rank (\d+) nRanks (\d+) nNodes (\d+) localRanks (\d+) localRank (\d+) MNNVL (\d+)")
INIT_DONE = re.compile(r"comm (0x[0-9a-f]+) rank (\d+) nranks (\d+) cudaDev (\d+) nvmlDev (\d+) busId ([0-9a-f]+) commId (0x[0-9a-f]+) - Init COMPLETE")
RING = re.compile(r"^Ring (\d+) : (-?\d+) -> (\d+) -> (-?\d+)$")
TREES = re.compile(r"^Trees(( \[\d+\] -?\d+/-?\d+/-?\d+->\d+->-?\d+)+)$")
PATTERN = re.compile(r"^Pattern (\d+), crossNic (\d+), nChannels (\d+), bw ([\d.]+)/([\d.]+), type (\w+)/(\w+), sameChannels (\d+)")
CHANNELS = re.compile(r"^(\d+) coll channels, (\d+) collnet channels, (\d+) nvls channels, (\d+) p2p channels, (\d+) p2p channels per peer")
HCA = re.compile(r"^NET/(\w+) : GPU Direct RDMA (Enabled|Disabled) for HCA (\d+) '([^']+)'")
USING_NET = re.compile(r"^Using network (\w+)")
P2P = re.compile(r"^Channel (\d+)/(\d+) : (\d+)\[(\d+)\] -> (\d+)\[(\d+)\] via (P2P/[\w ]+?|SHM[\w/]*)\s*$")
NET = re.compile(r"^Channel (\d+)/(\d+) : (\d+)\[(\d+)\] -> (\d+)\[(\d+)\] \[(send|receive)\] via NET/(\w+)/(\d+)(?:\((\d+)\))?(/GDRDMA)?")


def parse(text: str) -> dict:
    version = None
    procs: dict[tuple[str, str], dict] = {}
    hcas: dict[str, dict[int, dict]] = defaultdict(dict)
    networks: set[str] = set()
    warnings: list[str] = []
    transports: dict[str, int] = defaultdict(int)
    send_dev: dict[str, set[int]] = defaultdict(set)
    patterns: list[dict] = []
    for raw in text.splitlines():
        if raw.startswith("#"):
            continue
        m = VERSION.match(raw)
        if m:
            version = m.group(1)
            continue
        m = LINE.match(raw)
        if not m:
            continue
        host, pid, level, msg = m.group("host"), m.group("pid"), m.group("level"), m.group("msg")
        if level in ("WARN", "ATTN"):
            warnings.append(f"{host}: {msg}")
            continue
        if level != "INFO":
            continue
        proc = procs.setdefault((host, pid), {"host": host, "rings": {}, "init_complete": False, "comm": None})
        if (g := COMM.search(msg)):
            proc["comm"] = {"rank": int(g[2]), "nranks": int(g[3]), "nnodes": int(g[4]), "local_ranks": int(g[5]), "local_rank": int(g[6])}
        elif (g := INIT_DONE.search(msg)):
            proc["init_complete"] = True
            proc.setdefault("cuda_dev", int(g[4]))
        elif (g := RING.match(msg)):
            proc["rings"][int(g[1])] = (int(g[2]), int(g[4]))
        elif TREES.match(msg):
            proc["trees"] = msg.count("[")
        elif (g := PATTERN.match(msg)):
            patterns.append({"pattern": int(g[1]), "cross_nic": int(g[2]), "channels": int(g[3]), "bw_intra": float(g[4]), "bw_inter": float(g[5]), "type_intra": g[6], "type_inter": g[7]})
        elif (g := CHANNELS.match(msg)):
            proc["coll_channels"] = int(g[1])
        elif (g := HCA.match(msg)):
            hcas[host][int(g[3])] = {"name": g[4], "gdr": g[2] == "Enabled"}
        elif (g := USING_NET.match(msg)):
            networks.add(g[1])
        elif (g := P2P.match(msg)):
            transports[g[7]] += 1
        elif (g := NET.match(msg)):
            transports[f"NET/{g[8]}" + ("/GDRDMA" if g[11] else "")] += 1
            if g[7] == "send":  # logged by the sending process: the device index is that host's NIC
                send_dev[host].add(int(g[9]))
    return {"version": version, "procs": procs, "hcas": hcas, "networks": sorted(networks), "warnings": warnings,
            "transports": dict(transports), "send_dev": {h: sorted(v) for h, v in send_dev.items()}, "patterns": patterns}


def ring_is_single_cycle(links: dict[int, tuple[int, int]], nranks: int) -> bool:
    """links[rank] = (prev, next).  True when following `next` visits all nranks ranks once and prev is consistent."""
    if len(links) != nranks:
        return False
    for r, (prev, nxt) in links.items():
        if nxt not in links or links[nxt][0] != r:
            return False
    seen, cur = set(), next(iter(links))
    while cur not in seen:
        seen.add(cur)
        cur = links[cur][1]
    return len(seen) == nranks


def analyse(rep: dict) -> dict:
    procs = list(rep["procs"].values())
    comms = [p["comm"] for p in procs if p["comm"]]
    findings: list[dict] = []

    def add(code: str, severity: str, detail: str) -> None:
        findings.append({"code": code, "severity": severity, "detail": detail})

    nranks = max((c["nranks"] for c in comms), default=0)
    nnodes = max((c["nnodes"] for c in comms), default=0)
    local = max((c["local_ranks"] for c in comms), default=0)
    ranks_seen = sorted(c["rank"] for c in comms)
    if nranks and len(set(ranks_seen)) < nranks:
        missing = sorted(set(range(nranks)) - set(ranks_seen))
        add("ranks_missing", "error", f"{len(set(ranks_seen))}/{nranks} ranks logged their communicator; missing ranks {missing[:8]}")
    stuck = sorted(p["comm"]["rank"] for p in procs if p["comm"] and not p["init_complete"])
    if stuck:
        add("init_incomplete", "error", f"ranks without 'Init COMPLETE': {stuck[:8]} (stuck in initialisation or log truncated)")
    nets = rep["networks"]
    if "Socket" in nets:
        add("socket_network", "error", "NCCL uses the Socket (TCP) transport between nodes: no RDMA network was selected")
    elif not nets:
        add("no_network_line", "warn", "no 'Using network' line: log level too low or NCCL older than the format read here")
    counts = {h: len(v) for h, v in rep["hcas"].items()}
    if len(set(counts.values())) > 1:
        add("hca_mismatch", "error", f"hosts see different numbers of HCAs: {counts}")
    elif counts and local and min(counts.values()) < local:
        add("hca_fewer_than_gpus", "warn", f"{min(counts.values())} HCAs for {local} GPUs per node")
    off = [f"{h}:{d['name']}" for h, v in rep["hcas"].items() for d in v.values() if not d["gdr"]]
    if off:
        add("gdr_disabled", "warn", f"GPU Direct RDMA disabled for {off}")
    by_channel: dict[int, dict[int, tuple[int, int]]] = defaultdict(dict)
    for p in procs:
        if p["comm"]:
            for c, link in p["rings"].items():
                by_channel[c][p["comm"]["rank"]] = link
    if nranks and len(set(ranks_seen)) == nranks:
        broken = [c for c, links in sorted(by_channel.items()) if not ring_is_single_cycle(links, nranks)]
        if broken:
            add("ring_broken", "error", f"ring channels {broken} are not a single cycle over {nranks} ranks")
    if rep["warnings"]:
        add("warnings", "warn", f"{len(rep['warnings'])} WARN/ATTN lines, first: {rep['warnings'][0]}")
    if rep["send_dev"] and counts:
        used = {h: len(v) for h, v in rep["send_dev"].items()}
        add("rails_used", "info", f"NICs carrying ring traffic per host: {used} out of {counts}")
    errors = sorted({f["code"] for f in findings if f["severity"] == "error"})
    chans = sorted({p.get("coll_channels") for p in procs if p.get("coll_channels")})
    summary = {
        "version": rep["version"], "ranks_logged": len(set(ranks_seen)), "nranks": nranks, "nodes": nnodes, "network": nets,
        "hcas_per_host": counts, "coll_channels": chans, "init_complete": sum(1 for p in procs if p["init_complete"]),
        "transports": rep["transports"],
    }
    return {"summary": summary, "findings": findings, "errors": errors}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("log")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--expect", default="", help="comma-separated error codes that must be the only errors")
    a = ap.parse_args()
    res = analyse(parse(Path(a.log).read_text(encoding="utf-8", errors="replace")))
    s = res["summary"]
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"{Path(a.log).name}: NCCL {s['version']}; {s['ranks_logged']}/{s['nranks']} ranks on {s['nodes']} nodes; network {','.join(s['network']) or '?'}; "
              f"HCAs per host {s['hcas_per_host']}; channels {s['coll_channels']}; init complete on {s['init_complete']} ranks")
        for f in res["findings"]:
            print(f"  [{f['severity'].upper():5}] {f['code']}: {f['detail']}")
    expected = {c for c in a.expect.split(",") if c}
    ok = set(res["errors"]) == expected
    print(("OK" if ok else "UNEXPECTED") + f" errors={res['errors']} expected={sorted(expected)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
