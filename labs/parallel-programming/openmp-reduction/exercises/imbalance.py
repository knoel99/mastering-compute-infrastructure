#!/usr/bin/env python3
"""Load imbalance of an OpenMP loop schedule, computed from the rules of the specification.

usage: imbalance.py N THREADS SCHEDULE [CHUNK] [--cost uniform|triangular]
  SCHEDULE: static     blocks of about N/THREADS iterations, one per thread (no CHUNK)
            static,c   chunks of CHUNK iterations dealt round-robin in thread order
  triangular cost: iteration i costs i + 1 units; uniform: 1 unit.
Prints the work units given to each thread and imbalance = max / mean (1.0 = perfect).
The best possible speedup of the loop on THREADS threads is THREADS / imbalance.
For schedule(static) without chunk the specification only says "approximately equal"; like libgomp
(GCC 13) this script gives one extra iteration to the first N mod THREADS threads.
"""
import argparse


def owners(n, t, chunk):
    if chunk is None:
        q, r = divmod(n, t)
        sizes = [q + (1 if k < r else 0) for k in range(t)]
        return [k for k in range(t) for _ in range(sizes[k])]
    return [(i // chunk) % t for i in range(n)]


def imbalance(n, t, chunk, cost):
    work = [0] * t
    for i, th in enumerate(owners(n, t, chunk)):
        work[th] += (i + 1) if cost == "triangular" else 1
    mean = sum(work) / t
    return work, max(work) / mean


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("n", type=int)
    ap.add_argument("threads", type=int)
    ap.add_argument("schedule", choices=["static"])
    ap.add_argument("chunk", type=int, nargs="?")
    ap.add_argument("--cost", default="triangular", choices=["uniform", "triangular"])
    a = ap.parse_args()
    work, imb = imbalance(a.n, a.threads, a.chunk, a.cost)
    print(f"N={a.n} threads={a.threads} static chunk={a.chunk or 'none'} cost={a.cost}: units per thread {work}")
    print(f"imbalance = {imb:.4f}; best possible speedup = {a.threads / imb:.2f} (ideal {a.threads})")
