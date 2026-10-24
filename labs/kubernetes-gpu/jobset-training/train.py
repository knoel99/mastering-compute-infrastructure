#!/usr/bin/env python3
"""A deliberately tiny DDP trainer with checkpoint/resume, launched by torchrun in the JobSet and TrainJob manifests.

It is a stand-in for a real training script: a linear model fitted on synthetic data. What it keeps from the real
thing is the part the infrastructure cares about: rendezvous through torchrun, one all-reduce per step,
an atomic checkpoint written by rank 0 on a shared volume, and a resume from the latest checkpoint after a restart.
Backend: NCCL if CUDA is available, otherwise gloo (CPU), so the same file runs in the sandbox and on a GPU cluster.
"""
import argparse
import os
import tempfile
import time
from pathlib import Path

import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP

DIM = 16


def batch(step: int, rank: int, seed: int, true_w: torch.Tensor):
    g = torch.Generator().manual_seed(seed * 1_000_003 + step * 997 + rank)
    x = torch.randn(32, DIM, generator=g)
    return x, x @ true_w


def save_atomic(path: Path, state: dict) -> None:
    """Write to a temporary file in the same directory, then rename: a reader never sees a half-written checkpoint."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "wb") as f:
        torch.save(state, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--ckpt-dir", default="ckpt")
    ap.add_argument("--ckpt-every", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--die-at-step", type=int, default=-1, help="failure injection: the rank DIE_RANK exits once at this step")
    a = ap.parse_args()

    dist.init_process_group("nccl" if torch.cuda.is_available() else "gloo")
    rank, world = dist.get_rank(), dist.get_world_size()
    device = torch.device("cuda", int(os.environ.get("LOCAL_RANK", 0))) if torch.cuda.is_available() else torch.device("cpu")
    ckpt_dir = Path(a.ckpt_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt = ckpt_dir / "latest.pt"
    marker = ckpt_dir / "died.once"

    torch.manual_seed(a.seed)
    true_w = torch.randn(DIM, 1, generator=torch.Generator().manual_seed(1234))
    model = nn.Linear(DIM, 1, bias=False).to(device)
    opt = torch.optim.SGD(model.parameters(), lr=0.05)
    start = 0
    if ckpt.exists():
        state = torch.load(ckpt, map_location=device)
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["opt"])
        start = state["step"]
    ddp = DDP(model)
    if rank == 0:
        print(f"world_size={world} backend={dist.get_backend()} resuming_from_step={start}", flush=True)

    loss = torch.tensor(float("nan"))
    for step in range(start, a.steps):
        if step == a.die_at_step and rank == int(os.environ.get("DIE_RANK", "1")) and not marker.exists():
            marker.write_text("died")
            print(f"rank {rank}: injected failure at step {step}", flush=True)
            os._exit(1)
        x, y = batch(step, rank, a.seed, true_w)
        loss = nn.functional.mse_loss(ddp(x.to(device)), y.to(device))
        opt.zero_grad()
        loss.backward()           # DDP all-reduces the gradients here
        opt.step()
        if (step + 1) % a.ckpt_every == 0:
            if rank == 0:
                save_atomic(ckpt, {"step": step + 1, "model": model.state_dict(), "opt": opt.state_dict()})
                print(f"checkpoint step={step + 1} loss={loss.item():.5f}", flush=True)
            dist.barrier()
    if rank == 0:
        print(f"done step={a.steps} final_loss={loss.item():.6f}", flush=True)
    dist.destroy_process_group()


if __name__ == "__main__":
    t0 = time.time()
    main()
