"""FSDP2 versus DDP on the same init and the same data: losses, global gradient norm, final parameters.

    torchrun --standalone --nproc_per_node=4 equivalence.py

Also shows the classic mistake of clipping with the norm of the *local* shard instead of the global norm.
"""
import json
import sys
from datetime import timedelta

import torch
import torch.distributed as dist
from torch import nn
from torch.distributed.fsdp import fully_shard
from torch.distributed.tensor import DTensor
from torch.nn.parallel import DistributedDataParallel as DDP

from fsdp_memory import D_MODEL, N_BLOCKS, N_CLASSES, build, local

MAX_NORM, STEPS, GLOBAL_BATCH = 0.5, 3, 64


def batch(step, rank, world):
    g = torch.Generator().manual_seed(1000 + step)
    x = torch.randn(GLOBAL_BATCH, D_MODEL, generator=g)
    y = torch.randint(0, N_CLASSES, (GLOBAL_BATCH,), generator=g)
    per = GLOBAL_BATCH // world
    return x[rank * per:(rank + 1) * per], y[rank * per:(rank + 1) * per]


def main():
    torch.set_num_threads(1)
    dist.init_process_group("gloo", timeout=timedelta(seconds=120))
    rank, world = dist.get_rank(), dist.get_world_size()
    ddp = DDP(build())
    fsdp = build()
    for b in fsdp[:N_BLOCKS]:
        fully_shard(b)
    fully_shard(fsdp)
    opt_a = torch.optim.SGD(ddp.parameters(), lr=0.1)
    opt_b = torch.optim.SGD(fsdp.parameters(), lr=0.1)
    rows = []
    for step in range(STEPS):
        x, y = batch(step, rank, world)
        out = []
        for model, opt in ((ddp, opt_a), (fsdp, opt_b)):
            opt.zero_grad(set_to_none=True)
            loss = nn.functional.cross_entropy(model(x), y)
            loss.backward()
            local_sq = sum(float(local(p.grad).double().pow(2).sum()) for p in model.parameters())  # before clipping
            norm = nn.utils.clip_grad_norm_(model.parameters(), MAX_NORM)  # global norm, returned before clipping
            out.append((loss.item(), float(norm.full_tensor() if isinstance(norm, DTensor) else norm), local_sq ** 0.5))
            opt.step()
        rows.append(out)
    full_a = torch.cat([p.detach().reshape(-1) for p in ddp.parameters()])
    full_b = torch.cat([(p.full_tensor() if isinstance(p, DTensor) else p).detach().reshape(-1) for p in fsdp.parameters()])
    res = {
        "rank": rank,
        "max_abs_param_diff": float((full_a - full_b).abs().max()),
        "norm_ddp": [r[0][1] for r in rows], "norm_fsdp": [r[1][1] for r in rows],
        "local_shard_norm_fsdp": [r[1][2] for r in rows],
        "loss_ddp": [r[0][0] for r in rows], "loss_fsdp": [r[1][0] for r in rows],
    }
    allres = [None] * world
    dist.all_gather_object(allres, res)
    if rank == 0:
        json.dump(allres, open(sys.argv[1] if len(sys.argv) > 1 else "/dev/stdout", "w"), indent=1)
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
