#!/usr/bin/env python3
"""Run a scaling study of ./jacobi: strong and weak scaling, repetitions in randomised order.

usage: python3 run_study.py --jacobi ./jacobi --out study.json [--reps 9] [--procs 1,2,4]
                            [--n 1536] [--iters 30] [--rows-per-rank 1536] [--seed 0] [--quick]

Design (chapter 8 of the course):
  strong : global grid n x n, p ranks, 1-D decomposition, plus the 2-D decomposition for the largest p;
  weak   : rows_per_rank * p rows by n columns (constant work per rank);
  comm   : the strong configurations again with --skip-sweep (exchanges only), to time the transfers alone.
Every (configuration, repetition) pair is one mpirun; the whole list is shuffled with --seed so that
slow drifts of the machine do not line up with one configuration. The 1-minute load average before
each run is stored: on a shared machine it tells which runs to distrust.
"""
import argparse
import json
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone


def parse_line(text):
    """The last 'p=... key=value ...' line printed by jacobi -> dict of numbers/strings."""
    line = [l for l in text.splitlines() if l.startswith("p=")][-1]
    out = {}
    for kv in line.split():
        k, v = kv.split("=", 1)
        try:
            out[k] = int(v)
        except ValueError:
            try:
                out[k] = float(v)
            except ValueError:
                out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jacobi", default="./jacobi")
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=9)
    ap.add_argument("--procs", default="1,2,4")
    ap.add_argument("--n", type=int, default=1536)
    ap.add_argument("--iters", type=int, default=30)
    ap.add_argument("--rows-per-rank", type=int, default=1536)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--threads", type=int, default=1, help="OMP_NUM_THREADS per rank")
    ap.add_argument("--quick", action="store_true", help="tiny sizes, 2 repetitions: structure only")
    a = ap.parse_args()
    if a.quick:
        a.reps, a.n, a.iters, a.rows_per_rank = 2, 384, 10, 384
    procs = [int(x) for x in a.procs.split(",")]
    pmax = max(procs)
    configs = []
    for p in procs:
        configs.append(dict(kind="strong", p=p, decomp="1d", nx=a.n, ny=a.n))
        configs.append(dict(kind="comm", p=p, decomp="1d", nx=a.n, ny=a.n))
        if p == pmax and p > 1:
            configs.append(dict(kind="strong", p=p, decomp="2d", nx=a.n, ny=a.n))
        if p > 1:  # weak scaling at p=1 is the strong run at p=1 when rows_per_rank == n; run it anyway
            configs.append(dict(kind="weak", p=p, decomp="1d", nx=a.n, ny=a.rows_per_rank * p))
    configs.append(dict(kind="weak", p=1, decomp="1d", nx=a.n, ny=a.rows_per_rank))
    jobs = [dict(c, rep=r) for c in configs for r in range(a.reps)]
    random.Random(a.seed).shuffle(jobs)

    mpirun = ["mpirun", "--oversubscribe", "--mca", "mpi_yield_when_idle", "1"]
    if os.geteuid() == 0:
        mpirun.append("--allow-run-as-root")
    env = dict(os.environ, OMP_NUM_THREADS=str(a.threads))
    cpu = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "unknown")
    meta = dict(loadavg1_at_start=os.getloadavg()[0], date_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), cpus=os.cpu_count(), cpu_model=cpu,
                kernel=platform.release(), threads_per_rank=a.threads, seed=a.seed, reps=a.reps, iters=a.iters,
                mpirun=subprocess.run(["mpirun", "--version"], capture_output=True, text=True).stdout.splitlines()[0])
    runs = []
    for j in jobs:
        bind = ["--bind-to", "core"] if j["p"] * a.threads <= (os.cpu_count() or 1) and a.threads == 1 else ["--bind-to", "none"]
        cmd = mpirun + bind + ["-np", str(j["p"]), a.jacobi, "--nx", str(j["nx"]), "--ny", str(j["ny"]), "--iters",
                               str(a.iters), "--decomp", j["decomp"]]
        if j["kind"] == "comm":
            cmd.append("--skip-sweep")
        load = os.getloadavg()[0]
        res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)
        if res.returncode != 0:
            sys.exit(f"mpirun failed: {' '.join(cmd)}\n{res.stderr[-500:]}")
        runs.append(dict(j, load1=load, **parse_line(res.stdout)))
    json.dump(dict(meta=meta, runs=runs, finished=time.time()), open(a.out, "w"), indent=1)
    print(f"wrote {len(runs)} runs to {a.out}")


if __name__ == "__main__":
    main()
