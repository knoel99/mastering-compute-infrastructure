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
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
