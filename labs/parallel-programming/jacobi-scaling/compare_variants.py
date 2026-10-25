#!/usr/bin/env python3
"""Compare Jacobi variants on the same grid and the same number of ranks, interleaved in random order.

usage: python3 compare_variants.py --jacobi ./jacobi [--np 4] [--n 1536] [--iters 30] [--reps 9]
Variants: plain (1-D, blocking wait), overlap (1-D, interior swept while the halos travel), 2d, 2d+overlap,
check-every-1 (a residual all-reduce after EVERY sweep). Prints the median and the minimum of the loop time
and the medians of the halo and all-reduce times (max over ranks). The field must be identical in all variants.
"""
import argparse
import os
import random
import statistics as st
import subprocess

VARIANTS = {"plain": [], "overlap": ["--overlap"], "2d": ["--decomp", "2d"], "2d+overlap": ["--decomp", "2d", "--overlap"],
            "check-every-1": ["--check-every", "1"]}
ap = argparse.ArgumentParser()
ap.add_argument("--jacobi", default="./jacobi")
ap.add_argument("--np", type=int, default=4)
ap.add_argument("--n", type=int, default=1536)
ap.add_argument("--iters", type=int, default=30)
ap.add_argument("--reps", type=int, default=9)
a = ap.parse_args()
jobs = [(k, r) for k in VARIANTS for r in range(a.reps)]
random.Random(1).shuffle(jobs)
res = {k: [] for k in VARIANTS}
checksums = set()
for k, _ in jobs:
    cmd = ["mpirun", "--oversubscribe", "--bind-to", "core", "-np", str(a.np), a.jacobi, "--nx", str(a.n), "--ny", str(a.n),
           "--iters", str(a.iters)] + VARIANTS[k]
    if os.geteuid() == 0:
        cmd.insert(1, "--allow-run-as-root")
    out = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, OMP_NUM_THREADS="1"), check=True).stdout
    kv = dict(x.split("=", 1) for x in out.split() if "=" in x)
    res[k].append((float(kv["t_total"]), float(kv["t_halo"]), float(kv["t_red"])))
    checksums.add(kv["checksum"])
print(f"{a.np} ranks, {a.n}x{a.n} grid, {a.iters} sweeps, {a.reps} repetitions, load average at end {os.getloadavg()[0]:.2f}")
print(f"{'variant':>14} {'T median ms':>12} {'T min ms':>9} {'halo ms':>8} {'allreduce ms':>13}")
for k, v in res.items():
    print(f"{k:>14} {st.median(x[0] for x in v) * 1e3:>12.1f} {min(x[0] for x in v) * 1e3:>9.1f} "
          f"{st.median(x[1] for x in v) * 1e3:>8.2f} {st.median(x[2] for x in v) * 1e3:>13.3f}")
assert len(checksums) == 1, f"the field differs between variants: {checksums}"
print("OK same field for every variant:", checksums.pop())
