#!/usr/bin/env python3
"""Calculations used by the exercises and worked examples of the provisioning module (standard library only).

Every subcommand prints its inputs and its result; nothing here is measured, the inputs come from the exercise text or
from a source cited on the page.

  calc.py llama                                  # consistency check of Table 5 of the Llama 3 paper
  calc.py mttf --ref-gpus 8 --ref-days 47.7 --gpus 1024 --measured-hours 7.9
  calc.py rolling --nodes 64 --batch 8 --walltime-h 24 --reboot-h 0.25
  calc.py dcgm --nodes 32 --minutes 35 --parallel 32
  calc.py busbw --ranks 8 --size-gib 4 --ms 36 --baseline 400
  calc.py spares --nodes 256 --rate-per-1000-node-days 2.5 --repair-days 10 --quantile 0.95
  calc.py compat --driver 570 --cuda 13.0
  calc.py mig --request 3g.20gb=3 --request 2g.10gb=4 --request 1g.5gb=6
"""
import argparse
import math
import sys

# Table 5 of "The Llama 3 Herd of Models" (arXiv 2407.21783), read 2026-10-24: (component, count, printed percent).
LLAMA_TABLE5 = [
    ("Faulty GPU", 148, 30.1), ("GPU HBM3 Memory", 72, 17.2), ("Software Bug", 54, 12.9),
    ("Network Switch/Cable", 35, 8.4), ("Host Maintenance", 32, 7.6), ("GPU SRAM Memory", 19, 4.5),
    ("GPU System Processor", 17, 4.1), ("NIC", 7, 1.7), ("NCCL Watchdog Timeouts", 7, 1.7),
    ("Silent Data Corruption", 6, 1.4), ("GPU Thermal Interface + Sensor", 6, 1.4), ("SSD", 3, 0.7),
    ("Power Supply", 3, 0.7), ("Server Chassis", 2, 0.5), ("IO Expansion Board", 2, 0.5), ("Dependency", 2, 0.5),
    ("CPU", 2, 0.5), ("System Memory", 2, 0.5)]
# CUDA Compatibility guide, minor-version-compatibility table (read 2026-10-24): CUDA major -> minimal driver major.
CUDA_MIN_DRIVER = {11: 450, 12: 525, 13: 580}
# MIG User Guide, "Getting Started with MIG", example output of `nvidia-smi mig -lgip` and `nvidia-smi mig -lgipp` on an
# A100-SXM4-40GB (read 2026-10-25): profile -> (allowed start slices, memory slices out of 8, compute slices out of 7).
# Compute slices = SMs of the profile / 14 (1g = 14 SMs, 7g = 98 SMs in that output). The +me profile is left out.
MIG_A100_40GB = {
    "7g.40gb": ((0,), 8, 7), "4g.20gb": ((0,), 4, 4), "3g.20gb": ((0, 4), 4, 3),
    "2g.10gb": ((0, 2, 4), 2, 2), "1g.10gb": ((0, 2, 4, 6), 2, 1), "1g.5gb": ((0, 1, 2, 3, 4, 5, 6), 1, 1)}


def llama(_):
    total = sum(c for _, c, _ in LLAMA_TABLE5)
    printed = sum(p for _, _, p in LLAMA_TABLE5)
    print(f"sum of counts      : {total}  (the text says 419 unexpected interruptions)")
    print(f"sum of printed %   : {printed:.1f}")
    bad = [(n, c, p, 100 * c / total) for n, c, p in LLAMA_TABLE5 if abs(100 * c / total - p) > 0.06]
    for n, c, p, q in bad:
        print(f"mismatch           : {n}: {c}/{total} = {q:.1f} % but the table prints {p} %")
    print(f"interruptions/day  : {466 / 54:.2f} total, {419 / 54:.2f} unexpected, {47 / 54:.2f} planned (466, 419, 47 over 54 days)")
    return 0


def mttf(a):
    ref_hours = a.ref_days * 24
    predicted = ref_hours / (a.gpus / a.ref_gpus)
    print(f"reference MTTF     : {a.ref_gpus} GPUs -> {a.ref_days} days = {ref_hours:.1f} h")
    print(f"1/N prediction     : {a.gpus} GPUs -> {predicted:.2f} h")
    print(f"measured           : {a.measured_hours} h  (ratio measured/predicted = {a.measured_hours / predicted:.2f})")
    print(f"GPU ratio / MTTF ratio : {a.gpus / a.ref_gpus:.0f} / {ref_hours / a.measured_hours:.0f}")
    return 0


def rolling(a):
    waves = math.ceil(a.nodes / a.batch)
    per_wave = a.walltime_h + a.reboot_h
    print(f"nodes={a.nodes} batch={a.batch} -> {waves} waves")
    print(f"worst case per wave: wait for the longest job ({a.walltime_h} h) + reboot and validation ({a.reboot_h} h) = {per_wave} h")
    print(f"worst case total   : {waves * per_wave:.2f} h = {waves * per_wave / 24:.2f} days")
    print(f"capacity offline   : at most {a.batch}/{a.nodes} = {100 * a.batch / a.nodes:.1f} % of the nodes at any time")
    return 0


def dcgm(a):
    waves = math.ceil(a.nodes / a.parallel)
    print(f"{a.nodes} nodes, {a.minutes} min each (upper bound), {a.parallel} in parallel -> {waves} wave(s), at most {waves * a.minutes} min = {waves * a.minutes / 60:.2f} h")
    return 0


def busbw(a):
    size = a.size_gib * 2 ** 30
    algbw = size / (a.ms / 1000) / 1e9
    factor = 2 * (a.ranks - 1) / a.ranks
    bus = algbw * factor
    print(f"algbw = S/t        : {size:.4g} B / {a.ms} ms = {algbw:.1f} GB/s")
    print(f"factor 2(n-1)/n    : n={a.ranks} -> {factor:.3f}")
    print(f"busbw = algbw * f  : {bus:.1f} GB/s  ({100 * bus / a.baseline:.0f} % of the baseline {a.baseline})")
    return 0


def poisson_quantile(lmbda, q):
    k, term, cdf = 0, math.exp(-lmbda), math.exp(-lmbda)
    while cdf < q:
        k += 1
        term *= lmbda / k
        cdf += term
    return k, cdf


def spares(a):
    rate = a.rate_per_1000_node_days / 1000
    failures_per_week = a.nodes * rate * 7
    in_repair = a.nodes * rate * a.repair_days  # Little's law: arrival rate x time in the system
    k, cdf = poisson_quantile(in_repair, a.quantile)
    print(f"failures per week  : {a.nodes} x {rate:.4f} x 7 = {failures_per_week:.2f}")
    print(f"nodes in repair    : mean {in_repair:.2f} (Little: arrival rate x {a.repair_days} days)")
    print(f"Poisson quantile   : P(in repair <= {k}) = {cdf:.3f} >= {a.quantile}  -> keep {k} spare nodes")
    return 0


def compat(a):
    major = int(a.cuda.split(".")[0])
    need = CUDA_MIN_DRIVER.get(major)
    if need is None:
        print(f"CUDA {a.cuda}: no entry in the table")
        return 2
    ok = a.driver >= need
    print(f"CUDA {a.cuda} needs driver >= {need}; driver {a.driver} -> {'OK' if ok else 'TOO OLD'}")
    return 0 if ok else 1


def mig_geometries(table):
    """Every multiset of profiles that fits on one GPU: no overlapping memory slices, at most 7 compute slices.

    Returns {sorted tuple of profile names: one placement [(profile, start), ...]}."""
    names = sorted(table, key=lambda n: (-table[n][1], -table[n][2], n))
    found = {}

    def walk(i, used, compute, placed):
        key = tuple(sorted(p for p, _ in placed))
        if key and key not in found:
            found[key] = list(placed)
        for j in range(i, len(names)):
            starts, mem, comp = table[names[j]]
            if compute + comp > 7:
                continue
            for s in starts:
                cells = set(range(s, s + mem))
                if cells & used or (placed and j == i and placed[-1][0] == names[j] and s <= placed[-1][1]):
                    continue
                walk(j, used | cells, compute + comp, placed + [(names[j], s)])
    walk(0, frozenset(), 0, [])
    return found


def mig(a):
    table = MIG_A100_40GB
    want = {}
    for r in a.request:
        name, n = r.split("=")
        if name not in table:
            print(f"unknown profile {name}; known: {', '.join(table)}")
            return 2
        want[name] = want.get(name, 0) + int(n)
    names = sorted(want)
    geos = mig_geometries(table)
    vecs = [(tuple(g.count(n) for n in names), g) for g in geos]
    vecs = [(v, g) for v, g in vecs if any(v)]
    comp = sum(table[n][2] * k for n, k in want.items())
    mem = sum(table[n][1] * k for n, k in want.items())
    print("requests           : " + ", ".join(f"{k} x {n}" for n, k in sorted(want.items())))
    print(f"lower bounds       : compute {comp}/7 -> {math.ceil(comp / 7)} GPU(s), memory {mem}/8 -> {math.ceil(mem / 8)} GPU(s)")
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def best(rest):
        if not any(rest):
            return 0, ()
        top = None
        for v, g in vecs:
            if not any(min(x, y) for x, y in zip(v, rest)):
                continue
            nxt = tuple(max(0, r - x) for r, x in zip(rest, v))
            n, plan = best(nxt)
            if top is None or n + 1 < top[0]:
                top = (n + 1, (g,) + plan)
        return top
    n, plan = best(tuple(want[k] for k in names))
    print(f"one-GPU geometries : {len(geos)} distinct multisets fit on one GPU (memory placement + 7 compute slices)")
    print(f"minimum            : {n} GPU(s)")
    left = dict(want)
    rows = []
    for g in plan:
        chosen = []
        for p in g:
            if left.get(p, 0) > 0:
                left[p] -= 1
                chosen.append(p)
        place = sorted(geos[tuple(sorted(chosen))], key=lambda x: x[1])
        rows.append((sum(table[p][2] for p, _ in place), place))
    idle_c = idle_m = 0
    for i, (_, place) in enumerate(sorted(rows, key=lambda r: -r[0])):
        uc = 7 - sum(table[p][2] for p, _ in place)
        um = 8 - sum(table[p][1] for p, _ in place)
        idle_c += uc
        idle_m += um
        shown = " ".join(f"{p}@{s}" for p, s in place)
        print(f"  GPU {i}: {shown:<48} idle: {uc} compute, {um} memory slice(s)")
    print(f"idle in total      : {idle_c}/{7 * n} compute slices ({100 * idle_c / (7 * n):.1f} %), {idle_m}/{8 * n} memory slices ({100 * idle_m / (8 * n):.1f} %)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("llama").set_defaults(fn=llama)
    p = sub.add_parser("mttf"); p.set_defaults(fn=mttf)
    p.add_argument("--ref-gpus", type=int, required=True); p.add_argument("--ref-days", type=float, required=True)
    p.add_argument("--gpus", type=int, required=True); p.add_argument("--measured-hours", type=float, required=True)
    p = sub.add_parser("rolling"); p.set_defaults(fn=rolling)
    p.add_argument("--nodes", type=int, required=True); p.add_argument("--batch", type=int, required=True)
    p.add_argument("--walltime-h", type=float, required=True); p.add_argument("--reboot-h", type=float, required=True)
    p = sub.add_parser("dcgm"); p.set_defaults(fn=dcgm)
    p.add_argument("--nodes", type=int, required=True); p.add_argument("--minutes", type=float, required=True)
    p.add_argument("--parallel", type=int, required=True)
    p = sub.add_parser("busbw"); p.set_defaults(fn=busbw)
    p.add_argument("--ranks", type=int, required=True); p.add_argument("--size-gib", type=float, required=True)
    p.add_argument("--ms", type=float, required=True); p.add_argument("--baseline", type=float, required=True)
    p = sub.add_parser("spares"); p.set_defaults(fn=spares)
    p.add_argument("--nodes", type=int, required=True); p.add_argument("--rate-per-1000-node-days", type=float, required=True)
    p.add_argument("--repair-days", type=float, required=True); p.add_argument("--quantile", type=float, default=0.95)
    p = sub.add_parser("compat"); p.set_defaults(fn=compat)
    p.add_argument("--driver", type=int, required=True); p.add_argument("--cuda", required=True)
    p = sub.add_parser("mig"); p.set_defaults(fn=mig)
    p.add_argument("--request", action="append", required=True, help="profile=count, e.g. 3g.20gb=2 (A100-SXM4-40GB table)")
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
