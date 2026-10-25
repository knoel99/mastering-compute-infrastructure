#!/usr/bin/env python3
"""Exact switching threshold of the `aware` policy (lab 13.1, step 5; example 5.2 of the course).

For each value of lam (u per hour of delay), find by bisection the dataset size (GB) above which the score of
`Aware` prefers to stay on --src rather than move to --dst, at the very start of the job (checkpoint and dataset
at the home provider). The score is Aware.score of the implementation under test, so this script is only as good as
your Aware.score. EVERYTHING HERE IS SYNTHETIC (see scenarios.py).

The score depends on whether a pool grants capacity right now. To make the threshold independent of one random
draw, the script picks a seed for which BOTH pools refuse at slot 0: each then pays its expected wait slot_h / p_avail.

Usage: python3 threshold.py [--impl reference|starter] [--lam 0 40 400] [--src a-spot] [--dst c-spot]
Prints one line per lam and a structural CRITERION line (the threshold shrinks when time becomes more valuable).
"""
import argparse
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", default="reference", choices=["reference", "starter"])
    ap.add_argument("--lam", type=float, nargs="+", default=[0.0, 40.0, 400.0])
    ap.add_argument("--src", default="a-spot")
    ap.add_argument("--dst", default="c-spot")
    args = ap.parse_args()
    sys.path.insert(0, str(HERE / args.impl))
    sys.path.insert(0, str(HERE))
    P = importlib.import_module("placement")
    S = importlib.import_module("scenarios")

    pools, job, net = S.build(P, 0)
    by_id = {p.id: p for p in pools}
    src, dst = by_id[args.src], by_id[args.dst]
    seed = next(s for s in range(10_000) if not P.available(s, src, 0) and not P.available(s, dst, 0))

    def prefers_moving(lam, data_gb):
        _, job_d, net_d = S.build(P, data_gb)
        st = P.State(0.0, job_d.work_h, job_d.home, frozenset([job_d.home]), 0)
        pol = P.Aware(lam)
        return pol.score(job_d, dst, net_d, st, seed, 0.25) < pol.score(job_d, src, net_d, st, seed, 0.25)

    thresholds = []
    for lam in args.lam:
        if not prefers_moving(lam, 0.0):
            thresholds.append(0.0)
        else:
            lo, hi = 0.0, 1e7          # lo: moving is preferred; hi: staying is preferred
            for _ in range(80):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if prefers_moving(lam, mid) else (lo, mid)
            thresholds.append(lo)
        print(f"lam = {lam:6g} u/h : {args.src} -> {args.dst} stops paying above {thresholds[-1]:10.0f} GB")
    ordered = sorted(zip(args.lam, thresholds))
    ok = all(b <= a + 1e-6 for (_, a), (_, b) in zip(ordered, ordered[1:])) and all(t > 0 for t in thresholds)
    print("CRITERION (threshold positive and non-increasing with lam): " + ("OK" if ok else "NOT MET"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
