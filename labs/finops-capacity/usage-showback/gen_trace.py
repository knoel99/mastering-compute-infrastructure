#!/usr/bin/env python3
"""SYNTHETIC multi-team job trace in the format of `sacct -X -P` (made-up numbers, seeded, reproducible).

A strict-FIFO scheduler places the jobs on a fleet of GPUs, so waits and idle capacity are consistent with each other.
Usage: python3 gen_trace.py [--seed 7] [--days 28] [--gpus 64] > fixtures/synthetic_sacct.txt
"""
import argparse
import heapq
import math
import random
import sys
from datetime import datetime, timedelta

START = datetime(2026, 9, 1, 0, 0, 0)
HEADER = "JobID|Account|User|Partition|State|Submit|Start|End|ElapsedRaw|AllocTRES|NNodes"
# account: (jobs per day, GPU sizes, median hours, sigma)
TEAMS = {
    "nlp": (0.8, (16, 32), 30.0, 0.6),
    "vision": (2.5, (8, 16), 8.0, 0.7),
    "eval": (25.0, (1, 2, 4), 0.5, 0.6),
    "dev": (12.0, (1, 2), 1.5, 0.9),
}
# state probabilities: FAILED, TIMEOUT, NODE_FAIL, CANCELLED, PREEMPTED (the rest COMPLETED)
STATES = {"nlp": (0.06, 0.02, 0.05, 0.03, 0.0), "vision": (0.05, 0.03, 0.02, 0.04, 0.02),
          "eval": (0.04, 0.02, 0.0, 0.03, 0.0), "dev": (0.08, 0.05, 0.0, 0.10, 0.0)}


def make_jobs(rng, days):
    jobs = []
    for acct, (per_day, sizes, median, sigma) in TEAMS.items():
        t = 0.0
        while True:
            t += rng.expovariate(per_day / 24.0)  # hours
            if t >= days * 24:
                break
            gpus = rng.choice(sizes)
            hours = min(rng.lognormvariate(math.log(median), sigma), 96.0)
            u = rng.random()
            acc, state, frac = 0.0, "COMPLETED", 1.0
            for name, p in zip(("FAILED", "TIMEOUT", "NODE_FAIL", "CANCELLED", "PREEMPTED"), STATES[acct]):
                acc += p
                if u < acc:
                    state = name
                    frac = 1.0 if name == "TIMEOUT" else rng.uniform(0.05, 0.95)
                    break
            jobs.append({"acct": acct, "user": acct + "_u%d" % rng.randint(1, 4), "submit_h": t, "gpus": gpus,
                         "hours": max(hours * frac, 1 / 60), "state": state})
    jobs.sort(key=lambda j: j["submit_h"])
    return jobs


def fifo(jobs, capacity):
    """Strict FIFO (head-of-line blocking): a job never starts before an earlier-submitted one."""
    running, free, prev = [], capacity, 0.0
    for j in jobs:
        t = max(j["submit_h"], prev)
        while True:
            while running and running[0][0] <= t:
                free += heapq.heappop(running)[1]
            if free >= j["gpus"]:
                break
            t = running[0][0]
        j["start_h"], j["end_h"] = t, t + j["hours"]
        free -= j["gpus"]
        heapq.heappush(running, (j["end_h"], j["gpus"]))
        prev = t
    return jobs


def fmt(h):
    return (START + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%S")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--days", type=int, default=28)
    ap.add_argument("--gpus", type=int, default=64)
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)
    jobs = fifo(make_jobs(rng, a.days), a.gpus)
    out = ["# SYNTHETIC trace (gen_trace.py seed=%d days=%d gpus=%d): made-up numbers, not a real cluster" % (a.seed, a.days, a.gpus), HEADER]
    for i, j in enumerate(sorted(jobs, key=lambda j: j["start_h"]), start=1):
        end = fmt(j["end_h"])
        el = int(round((j["end_h"] - j["start_h"]) * 3600))
        nodes = max(1, j["gpus"] // 8)
        tres = "billing=%d,cpu=%d,gres/gpu=%d,mem=%dG,node=%d" % (j["gpus"], j["gpus"] * 8, j["gpus"], j["gpus"] * 64, nodes)
        out.append("|".join([str(i), j["acct"], j["user"], "train", j["state"], fmt(j["submit_h"]), fmt(j["start_h"]), end, str(el), tres, str(nodes)]))
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
