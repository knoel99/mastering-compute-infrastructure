#!/usr/bin/env python3
"""Experiment plan and runner — TO WRITE (milestone 1).

plan(world_sizes, modes, reps, global_batch, rank_batch, seed=0) -> list of
    {"mode", "world", "batch_per_rank", "rep"}
  strong: batch_per_rank = global_batch // world (ValueError if not divisible);
  weak: batch_per_rank = rank_batch; unknown mode: ValueError.
  The order is shuffled with random.Random(seed): reproducible, and it removes drift bias.

CLI (see tests/test_study.py): --world-sizes 1,2,4 --modes strong,weak --reps 3 --global-batch 256
  --rank-batch 64 --hidden 512 --layers 4 --steps 30 --warmup 5 --seed 0 --out results.json --decompose --dry-run
  --decompose is forwarded to bench.py. --dry-run prints one JSON line per run; otherwise each run launches bench.py (OMP_NUM_THREADS=1)
  and the file gets {"args": ..., "points": [{**item, **bench result}]}.
"""
import sys


def plan(world_sizes, modes, reps, global_batch, rank_batch, seed=0):
    raise NotImplementedError


def main():
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
