#!/usr/bin/env python3
"""Ablation: in the "hedged" policy, does the PLACEMENT rule or the CHECKPOINT INTERVAL do the work?

Four variants over the same seeds, jobs and interruption luck:
  cheapest             cheapest placement, a checkpoint every 240 min on spot   (the baseline)
  cheapest+young-daly  cheapest placement, Young-Daly interval (the one of "hedged")
  hedged+240           hedged placement (expected cost, deadline guard), 240-min interval
  hedged               hedged placement, Young-Daly interval
Not covered by the tests: run it to reproduce the table of the project page (python3 ablation.py --seeds 20).
"""
import argparse
import math
import sys

import compare
import policies


class CheapestYoungDaly(policies.Cheapest):
    def ckpt_interval(self, job, offer):
        return policies.Hedged().ckpt_interval(job, offer)


class HedgedFixed240(policies.Hedged):
    def ckpt_interval(self, job, offer):
        return math.inf if offer.hazard == 0 else 240


VARIANTS = {"cheapest": policies.Cheapest, "cheapest+young-daly": CheapestYoungDaly,
            "hedged+240": HedgedFixed240, "hedged": policies.Hedged}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    a = ap.parse_args()
    compare.POLICIES.update(VARIANTS)
    rows = {n: compare.run_policy(n, range(a.seeds)) for n in VARIANTS}
    print(f"{'variant':<20} {'cost (u)':>9} {'misses':>7} {'interruptions':>14} {'lost job-h':>11}")
    for n, r in rows.items():
        mean = {k: sum(x[k] for x in r) / len(r) for k in ("cost", "misses", "interruptions", "lost_h")}
        print(f"{n:<20} {mean['cost']:9.0f} {mean['misses']:7.2f} {mean['interruptions']:14.1f} {mean['lost_h']:11.1f}")
    print("\npaired differences (a - b; negative = a is better):")
    for a_name, b_name in (("cheapest+young-daly", "cheapest"), ("hedged+240", "cheapest"),
                           ("hedged", "cheapest+young-daly"), ("hedged", "hedged+240")):
        for key in ("cost", "misses"):
            d = compare.paired_diff(rows[a_name], rows[b_name], key)
            print(f"  {key:<7} {a_name} - {b_name}: {d['mean']:9.1f}  [{d['lo']:9.1f},{d['hi']:9.1f}]  a better on {d['wins']}/{d['n']} seeds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
