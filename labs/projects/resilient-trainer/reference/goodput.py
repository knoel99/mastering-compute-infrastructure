#!/usr/bin/env python3
"""Checkpoint interval: Young-Daly first-order model and a Monte Carlo check.

Notation (seconds): C = cost of one checkpoint, M = mean time between failures,
R = restart cost, T = compute time between two checkpoints.
First-order waste fraction: W(T) = C/T + (T/2 + R)/M, minimised at T = sqrt(2*C*M).
"""
import argparse
import json
import math
import random
import statistics
import sys
from pathlib import Path


def young_daly(c, mtbf):
    return math.sqrt(2.0 * c * mtbf)


def waste_fraction(t, c, mtbf, restart):
    return c / t + (t / 2.0 + restart) / mtbf


def simulate(t, c, mtbf, restart, horizon, seed=0):
    """Goodput = useful compute / wall time, with exponential failures.

    A failure loses all compute since the last *completed* checkpoint and costs `restart`.
    """
    rng = random.Random(seed)
    done = 0.0  # compute secured by a completed checkpoint
    wall = 0.0
    next_fail = rng.expovariate(1.0 / mtbf)
    while done < horizon:
        segment = min(t, horizon - done)
        need = segment + c  # compute then checkpoint
        if wall + need <= next_fail:
            wall += need
            done += segment
        else:
            wall = next_fail + restart
            next_fail = wall + rng.expovariate(1.0 / mtbf)
    return horizon / wall


def measured_cost(workdir):
    """Median checkpoint duration in seconds from a trainer's ckpt.jsonl."""
    rows = [json.loads(line) for line in (Path(workdir) / "ckpt.jsonl").read_text().splitlines() if line]
    return statistics.median(r["seconds"] for r in rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt-seconds", type=float)
    ap.add_argument("--workdir", help="read the checkpoint cost from this trainer workdir")
    ap.add_argument("--mtbf-hours", type=float, required=True)
    ap.add_argument("--restart-seconds", type=float, default=300.0)
    args = ap.parse_args()
    c = args.ckpt_seconds if args.ckpt_seconds is not None else measured_cost(args.workdir)
    m = args.mtbf_hours * 3600.0
    t_opt = young_daly(c, m)
    print(f"C = {c:.3f} s, MTBF = {m:.0f} s, R = {args.restart_seconds:.0f} s")
    print(f"Young-Daly period T* = {t_opt:.1f} s")
    print(f"{'T (s)':>10} {'model goodput':>14} {'simulated':>10}")
    for k in (0.25, 0.5, 1.0, 2.0, 4.0):
        t = t_opt * k
        g_model = 1.0 - waste_fraction(t, c, m, args.restart_seconds)
        g_sim = simulate(t, c, m, args.restart_seconds, horizon=5e7, seed=1)
        print(f"{t:10.1f} {g_model:14.4f} {g_sim:10.4f}" + ("   <- T*" if k == 1.0 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
