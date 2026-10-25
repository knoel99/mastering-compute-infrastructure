#!/usr/bin/env python3
"""MPI ranks x OpenMP threads: same grid, same cores, different splits.

usage: python3 hybrid_compare.py --jacobi ./jacobi [--cores 4] [--reps 7] [--n 1536] [--iters 30]
For every divisor T of --cores, runs  mpirun -np cores/T --map-by slot:PE=T --bind-to core  with OMP_NUM_THREADS=T
(--misbound adds the same layouts with the T threads of each rank squeezed onto one core),
interleaving the layouts over the repetitions in a fixed random order. Prints the median wall time of the loop,
the fingerprint of the field (must be identical for every layout) and the bytes sent in the halo exchanges.
"""
import argparse
import os
import random
import re
import subprocess
from statistics import median

ap = argparse.ArgumentParser()
ap.add_argument("--jacobi", default="./jacobi")
ap.add_argument("--cores", type=int, default=4)
ap.add_argument("--reps", type=int, default=7)
ap.add_argument("--n", type=int, default=1536)
ap.add_argument("--iters", type=int, default=30)
ap.add_argument("--misbound", action="store_true",
                help="also run each hybrid layout with --bind-to core and no PE=T: the T threads of a rank share ONE core")
a = ap.parse_args()
layouts = [(a.cores // t, t, "PE") for t in range(1, a.cores + 1) if a.cores % t == 0]
if a.misbound:
    layouts += [(a.cores // t, t, "one core") for t in range(2, a.cores + 1) if a.cores % t == 0]
jobs = [(l, r) for l in layouts for r in range(a.reps)]
random.Random(0).shuffle(jobs)
res = {l: [] for l in layouts}  # key: (ranks, threads, binding)
fp = {}
for (ranks, thr, binding), _ in jobs:
    mapping = ["--map-by", f"slot:PE={thr}"] if binding == "PE" else []
    cmd = ["mpirun", "--oversubscribe", *mapping, "--bind-to", "core", "-np", str(ranks), a.jacobi,
           "--nx", str(a.n), "--ny", str(a.n), "--iters", str(a.iters)]
    if os.geteuid() == 0:
        cmd.insert(1, "--allow-run-as-root")
    out = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, OMP_NUM_THREADS=str(thr)), check=True).stdout
    line = [l for l in out.splitlines() if l.startswith("p=")][-1]
    kv = dict(x.split("=", 1) for x in line.split())
    res[(ranks, thr, binding)].append(float(kv["t_total"]))
    fp[(ranks, thr, binding)] = (kv["checksum"], int(kv["bytes_total"]))
print(f"{'ranks':>5} {'threads':>7} {'binding':>9} {'median ms':>10} {'min ms':>8} {'bytes in halos':>15} checksum")
for l in layouts:
    print(f"{l[0]:>5} {l[1]:>7} {l[2]:>9} {median(res[l]) * 1e3:>10.1f} {min(res[l]) * 1e3:>8.1f} {fp[l][1]:>15} {fp[l][0]}")
assert len({v[0] for v in fp.values()}) == 1, "the field must not depend on the layout"
print("OK same field for every layout:", re.sub(r"[()',]", "", str(next(iter(fp.values()))[0])))
