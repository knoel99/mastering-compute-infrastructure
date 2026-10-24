#!/usr/bin/env python3
"""Compare policies over many seeds: mean and bootstrap 95 % interval of cost and deadline misses."""
import argparse
import random
import statistics
import sys

import data
import policies
import sim

POLICIES = {"cheapest": policies.Cheapest, "on-demand": policies.OnDemandOnly, "hedged": policies.Hedged}


def run_policy(name, seeds, n_jobs=30, offers=None):
    offers = offers or data.default_offers()
    rows = []
    for s in seeds:
        r = sim.simulate(offers, data.make_jobs(n_jobs, seed=s), POLICIES[name](), seed=s)
        rows.append({"cost": r.cost, "misses": r.deadline_misses, "unfinished": r.unfinished,
                     "interruptions": r.interruptions, "lost_h": r.lost_min / 60.0})
    return rows


def mean_ci(xs, n_boot=2000, seed=0, level=0.95):
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(xs, k=len(xs))) for _ in range(n_boot))
    lo = means[int((1 - level) / 2 * n_boot)]
    hi = means[int((1 + level) / 2 * n_boot) - 1]
    return statistics.fmean(xs), lo, hi


def paired_diff(rows_a, rows_b, key, n_boot=2000, seed=0):
    """Mean of (a - b) per seed with a bootstrap 95 % interval, and the number of seeds where a < b.
    The same jobs and the same interruption luck are replayed for every policy, so the PAIRED difference is the
    meaningful comparison; two overlapping intervals of means say little."""
    diffs = [float(x[key]) - float(y[key]) for x, y in zip(rows_a, rows_b)]
    m, lo, hi = mean_ci(diffs, n_boot, seed)
    return {"mean": m, "lo": lo, "hi": hi, "wins": sum(1 for d in diffs if d < 0), "n": len(diffs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--jobs", type=int, default=30)
    a = ap.parse_args()
    results = {}
    print(f"{'policy':<10} {'cost (u)':>22} {'deadline misses':>22} {'interruptions':>14} {'lost GPU-job-h':>15}")
    for name in POLICIES:
        rows = run_policy(name, range(a.seeds), a.jobs)
        c, cl, ch = mean_ci([r["cost"] for r in rows])
        m, ml, mh = mean_ci([float(r["misses"]) for r in rows])
        print(f"{name:<10} {c:9.0f} [{cl:7.0f},{ch:7.0f}] {m:7.2f} [{ml:5.2f},{mh:5.2f}] "
              f"{statistics.fmean(r['interruptions'] for r in rows):14.1f} {statistics.fmean(r['lost_h'] for r in rows):15.1f}")
        results[name] = rows
    print("\npaired differences over the same seeds (a - b; negative = a is better):")
    for a_name, b_name in (("hedged", "cheapest"), ("hedged", "on-demand"), ("cheapest", "on-demand")):
        for key in ("cost", "misses"):
            d = paired_diff(results[a_name], results[b_name], key)
            print(f"  {key:<7} {a_name} - {b_name}: {d['mean']:9.1f}  [{d['lo']:9.1f},{d['hi']:9.1f}]  a better on {d['wins']}/{d['n']} seeds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
