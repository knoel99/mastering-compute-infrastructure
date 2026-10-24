#!/usr/bin/env python3
"""Why a training job needs gang scheduling: partial placement by a pod-by-pod scheduler can deadlock.

Model (a simulation with its assumptions, not a measurement of a real scheduler):
  * `jobs` identical jobs, each made of `pods` pods that each need one whole free node (8-GPU nodes);
  * the pods of the jobs reach the scheduler in a uniformly random interleaving;
  * a pod-by-pod scheduler binds each pod to a free node if there is one, otherwise the pod waits;
  * a job makes progress only when ALL its pods are bound (collective training: one missing rank = no step);
  * a job that is complete finishes and releases its nodes, so the cluster is DEADLOCKED exactly when no job is complete
    after all pods have arrived and some pods still wait.
A gang scheduler binds a job only if its whole set of pods fits: partial placements never exist.
"""
import argparse
import random
from math import comb


def exact_two_jobs(nodes: int, pods: int) -> float:
    """Exact deadlock probability for 2 jobs: the first `nodes` arrivals must hold at most pods-1 pods of each job."""
    if nodes >= 2 * pods:
        return 0.0
    total = comb(2 * pods, pods)
    bad = sum(comb(nodes, a) * comb(2 * pods - nodes, pods - a)
              for a in range(max(0, nodes - pods + 1), min(nodes, pods - 1) + 1) if 0 <= pods - a <= 2 * pods - nodes)
    return bad / total


def simulate(nodes: int, pods: int, jobs: int, trials: int, seed: int, gang: bool = False) -> float:
    """Monte Carlo estimate of the deadlock probability with `jobs` jobs."""
    rng = random.Random(seed)
    arrivals = [j for j in range(jobs) for _ in range(pods)]
    deadlocks = 0
    for _ in range(trials):
        rng.shuffle(arrivals)
        if gang:
            continue          # a gang scheduler never leaves a job partially bound
        free, bound = nodes, [0] * jobs
        for j in arrivals:
            if free:
                free -= 1
                bound[j] += 1
        if max(bound) < pods and free == 0:
            deadlocks += 1
    return deadlocks / trials


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pods", type=int, default=8, help="pods (=nodes) per job")
    ap.add_argument("--trials", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=12)
    a = ap.parse_args()
    print(f"2 jobs of {a.pods} pods, each pod needs one whole 8-GPU node; random arrival order; {a.trials} trials, seed {a.seed}")
    print(f"{'nodes':>5} {'GPUs held when deadlocked':>26} {'P(deadlock) exact':>18} {'simulated':>10} {'with gang':>10}")
    for n in range(a.pods, 2 * a.pods + 1, 2):
        print(f"{n:>5} {n * 8:>26} {exact_two_jobs(n, a.pods):>18.3f} {simulate(n, a.pods, 2, a.trials, a.seed):>10.3f} "
              f"{simulate(n, a.pods, 2, a.trials, a.seed, gang=True):>10.3f}")


if __name__ == "__main__":
    main()
