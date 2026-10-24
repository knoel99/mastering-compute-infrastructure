#!/usr/bin/env python3
"""Experiment plan and runner: strong and weak scaling, repetitions, randomised run order."""
import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def plan(world_sizes, modes, reps, global_batch, rank_batch, seed=0):
    """Return the list of runs. Order is shuffled with a fixed seed: it removes drift bias
    (thermal state, noisy neighbours) while staying reproducible."""
    items = []
    for mode in modes:
        for p in world_sizes:
            if mode == "strong":
                if global_batch % p:
                    raise ValueError(f"global batch {global_batch} not divisible by {p}")
                b = global_batch // p
            elif mode == "weak":
                b = rank_batch
            else:
                raise ValueError(f"unknown mode {mode}")
            items += [{"mode": mode, "world": p, "batch_per_rank": b, "rep": r} for r in range(reps)]
    random.Random(seed).shuffle(items)
    return items


def run_point(item, args):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "r.json"
        cmd = [sys.executable, str(HERE / "bench.py"), "--world-size", str(item["world"]),
               "--hidden", str(args.hidden), "--layers", str(args.layers),
               "--batch-per-rank", str(item["batch_per_rank"]), "--steps", str(args.steps),
               "--warmup", str(args.warmup), "--out", str(out)] + (["--decompose"] if args.decompose else [])
        subprocess.run(cmd, check=True, env={**os.environ, "OMP_NUM_THREADS": "1"}, capture_output=True, text=True)
        return {**item, **json.loads(out.read_text())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world-sizes", default="1,2,4")
    ap.add_argument("--modes", default="strong,weak")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--global-batch", type=int, default=256)
    ap.add_argument("--rank-batch", type=int, default=64)
    ap.add_argument("--hidden", type=int, default=512)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results.json")
    ap.add_argument("--decompose", action="store_true", help="pass --decompose to bench.py")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    items = plan([int(x) for x in args.world_sizes.split(",")], args.modes.split(","), args.reps,
                 args.global_batch, args.rank_batch, args.seed)
    if args.dry_run:
        for i in items:
            print(json.dumps(i))
        return 0
    points = []
    for k, item in enumerate(items, 1):
        print(f"[{k}/{len(items)}] {item}", flush=True)
        points.append(run_point(item, args))
    Path(args.out).write_text(json.dumps({"args": vars(args), "points": points}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
