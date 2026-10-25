#!/usr/bin/env python3
"""Time torch.distributed all-reduce for a range of message sizes (gloo backend, CPU).

Run:  torchrun --nproc_per_node=4 bench_allreduce.py --out allreduce.json
"""
import argparse
import json
import os
import statistics
import time

import torch
import torch.distributed as dist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-exp", type=int, default=8, help="smallest message: 2**min_exp float32 elements")
    ap.add_argument("--max-exp", type=int, default=22)
    ap.add_argument("--repeat", type=int, default=15)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--out", default="allreduce.json")
    args = ap.parse_args()

    dist.init_process_group(backend="gloo")
    rank, world = dist.get_rank(), dist.get_world_size()
    rows = []
    for e in range(args.min_exp, args.max_exp + 1):
        n = 2**e
        x = torch.ones(n, dtype=torch.float32)
        y = x.clone()
        dist.all_reduce(y)  # correctness check on a separate buffer: the sum of `world` ones is `world`
        if not bool((y == world).all()):
            raise RuntimeError(f"all_reduce returned a wrong sum for {n} elements")
        for _ in range(args.warmup):
            dist.all_reduce(x)
        times = []
        for _ in range(args.repeat):
            dist.barrier()
            t0 = time.perf_counter()
            dist.all_reduce(x)
            times.append(time.perf_counter() - t0)
        # the collective ends when the slowest rank ends: take the max across ranks of each rank's median
        med = torch.tensor([statistics.median(times)], dtype=torch.float64)
        dist.all_reduce(med, op=dist.ReduceOp.MAX)
        rows.append({"bytes": 4 * n, "seconds_median_max_rank": med.item(), "seconds_min_rank0": min(times)})
        # note: x is reduced in place, so its values grow as world**k over the repetitions (harmless for timing in
        # float32 up to about 64 ranks and 20 repetitions); only the check on `y` above verifies the result.
    if rank == 0:
        with open(args.out, "w") as f:
            json.dump({"world_size": world, "backend": "gloo", "torch": torch.__version__,
                       "cpu_count": os.cpu_count(), "rows": rows}, f, indent=1)
        print(f"rank0: wrote {args.out} ({len(rows)} sizes, world={world})")
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
