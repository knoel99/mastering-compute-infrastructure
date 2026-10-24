#!/usr/bin/env python3
"""One data-parallel measurement point: p processes (gloo, CPU), naive gradient all-reduce, phase timers.

Every rank computes forward and backward on its own batch, then ALL gradients are flattened and
summed with ONE all-reduce (no bucketing, no overlap with the backward pass): this is the
textbook data parallelism that the alpha-beta model describes, not torch DDP.
Rank 0 writes the JSON result. The per-step value of a phase is the maximum over ranks.
comm_s = packing + waiting for the slowest rank + the all-reduce itself; --decompose measures them separately.
"""
import argparse
import json
import os
import socket
import sys
import time

import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch import nn


def mlp(hidden, layers):
    mods = []
    for _ in range(layers):
        mods += [nn.Linear(hidden, hidden), nn.ReLU()]
    return nn.Sequential(*mods, nn.Linear(hidden, 1))


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def worker(rank, world, args, port):
    os.environ["MASTER_ADDR"] = "127.0.0.1"
    os.environ["MASTER_PORT"] = str(port)
    torch.set_num_threads(1)
    dist.init_process_group("gloo", rank=rank, world_size=world)
    torch.manual_seed(0)  # identical initial weights on every rank
    model = mlp(args.hidden, args.layers)
    params = list(model.parameters())
    n_params = sum(p.numel() for p in params)
    opt = torch.optim.SGD(params, lr=1e-3)
    recs = []
    for step in range(args.warmup + args.steps):
        g = torch.Generator().manual_seed(1000 * rank + step)
        x = torch.randn(args.batch_per_rank, args.hidden, generator=g)
        y = torch.randn(args.batch_per_rank, 1, generator=g)
        t0 = time.perf_counter()
        loss = nn.functional.mse_loss(model(x), y)
        opt.zero_grad()
        loss.backward()
        t1 = time.perf_counter()
        pack = wait = allr = 0.0
        if world > 1:
            a = time.perf_counter()
            flat = torch.cat([p.grad.reshape(-1) for p in params])
            b = time.perf_counter()
            if args.decompose:  # an extra barrier separates "waiting for the slowest rank" from the collective
                dist.barrier()
            c = time.perf_counter()
            dist.all_reduce(flat)
            d = time.perf_counter()
            flat.div_(world)
            off = 0
            for p in params:
                p.grad.copy_(flat[off:off + p.numel()].view_as(p.grad))
                off += p.numel()
            e = time.perf_counter()
            pack, wait, allr = (b - a) + (e - d), c - b, d - c
        t2 = time.perf_counter()
        opt.step()
        t3 = time.perf_counter()
        recs.append((t1 - t0, t2 - t1, t3 - t2, pack, wait, allr))
    gathered = [None] * world
    dist.all_gather_object(gathered, recs)
    if rank == 0:
        steps = range(args.warmup, args.warmup + args.steps)
        phase = lambda k: [max(gathered[r][s][k] for r in range(world)) for s in steps]
        total = [max(sum(gathered[r][s][:3]) for r in range(world)) for s in steps]
        result = {
            "world": world, "hidden": args.hidden, "layers": args.layers, "n_params": n_params,
            "batch_per_rank": args.batch_per_rank, "steps": args.steps, "warmup": args.warmup,
            "grad_bytes": 4 * n_params, "flops_per_step_per_rank": 6 * n_params * args.batch_per_rank,
            "step_s": total, "compute_s": phase(0), "comm_s": phase(1), "opt_s": phase(2),
            "torch": torch.__version__, "cpu_count": os.cpu_count(),
        }
        if args.decompose:
            result.update({"decomposed": True, "pack_s": phase(3), "wait_s": phase(4), "allreduce_s": phase(5)})
        with open(args.out, "w") as f:
            json.dump(result, f)
    dist.barrier()
    dist.destroy_process_group()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world-size", type=int, default=1)
    ap.add_argument("--hidden", type=int, default=512)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--batch-per-rank", type=int, default=64)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--decompose", action="store_true", help="split comm into pack / wait / allreduce (adds a barrier)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    mp.spawn(worker, args=(args.world_size, args, free_port()), nprocs=args.world_size, join=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
