"""Measure per-rank memory of DDP versus FSDP2 (fully_shard) on CPU, by tensor sizes.

    torchrun --standalone --nproc_per_node=4 fsdp_memory.py --mode ddp   --out ddp.json
    torchrun --standalone --nproc_per_node=4 fsdp_memory.py --mode fsdp  --out fsdp.json
    torchrun --standalone --nproc_per_node=4 fsdp_memory.py --mode fsdp --no-reshard --out fsdp_nr.json

What is measured (after two AdamW steps, fp32):
  * persistent bytes per rank = parameters + gradients + optimizer state actually held by the rank
    (for FSDP2 these are the local shards, read with DTensor.to_local());
  * the peak number of *unsharded* parameter bytes observed at the entry of each block of the forward pass;
  * the peak resident-set size reached while building the model and running the steps (VmHWM).
"""
import argparse
import json
import os
import time
from datetime import timedelta

import torch
import torch.distributed as dist
from torch import nn
from torch.nn.parallel import DistributedDataParallel as DDP

D_MODEL, D_FF, N_BLOCKS, N_CLASSES = 512, 2048, 8, 10


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.up, self.down = nn.Linear(D_MODEL, D_FF), nn.Linear(D_FF, D_MODEL)

    def forward(self, x):
        return x + self.down(torch.relu(self.up(x)))


def build(seed=0):
    torch.manual_seed(seed)
    return nn.Sequential(*[Block() for _ in range(N_BLOCKS)], nn.Linear(D_MODEL, N_CLASSES))


def local(t):
    """The local tensor of a DTensor, or the tensor itself."""
    return t.to_local() if hasattr(t, "to_local") else t


def nbytes(t):
    return t.numel() * t.element_size()


def reset_peak_rss():
    with open("/proc/self/clear_refs", "w") as f:
        f.write("5")  # reset the peak resident-set size (VmHWM) to the current RSS


def rss_kib(field):
    with open("/proc/self/status") as f:
        return next(int(line.split()[1]) for line in f if line.startswith(field))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["ddp", "fsdp"], required=True)
    ap.add_argument("--no-reshard", action="store_true", help="fsdp: reshard_after_forward=False on every block")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    torch.set_num_threads(1)
    dist.init_process_group("gloo", timeout=timedelta(seconds=120))
    rank, world = dist.get_rank(), dist.get_world_size()
    reset_peak_rss()
    rss0 = rss_kib("VmRSS:")

    model = build()
    total_params = sum(p.numel() for p in model.parameters())
    live_samples = []  # unsharded parameter bytes seen at the entry of each block (forward)

    if a.mode == "ddp":
        model = DDP(model)
        blocks = list(model.module[:N_BLOCKS])
    else:
        from torch.distributed.fsdp import fully_shard

        blocks = list(model[:N_BLOCKS])
        for b in blocks:
            fully_shard(b, reshard_after_forward=not a.no_reshard)
        fully_shard(model)  # root group: the classifier head (and anything left over)

    def live_unsharded():
        return sum(nbytes(p) for p in model.parameters() if not hasattr(p, "to_local"))

    for b in blocks:  # registered after fully_shard: runs after FSDP's own all-gather hook
        b.register_forward_pre_hook(lambda m, args: live_samples.append(live_unsharded()))

    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    g = torch.Generator().manual_seed(rank)
    t0 = time.perf_counter()
    for _ in range(2):
        x = torch.randn(64, D_MODEL, generator=g)
        y = torch.randint(0, N_CLASSES, (64,), generator=g)
        live_samples.clear()
        opt.zero_grad(set_to_none=True)
        loss = nn.functional.cross_entropy(model(x), y)
        loss.backward()
        grad_bytes = sum(nbytes(local(p.grad)) for p in model.parameters() if p.grad is not None)
        opt.step()
    step_s = (time.perf_counter() - t0) / 2

    param_bytes = sum(nbytes(local(p)) for p in model.parameters())
    opt_bytes = sum(nbytes(local(v)) for st in opt.state.values() for v in st.values() if torch.is_tensor(v) and v.dim() > 0)
    rec = {
        "rank": rank, "world": world, "mode": a.mode, "no_reshard": a.no_reshard,
        "total_params": total_params, "param_bytes": param_bytes, "grad_bytes": grad_bytes,
        "opt_bytes": opt_bytes, "persistent_bytes": param_bytes + grad_bytes + opt_bytes,
        "peak_unsharded_param_bytes": max(live_samples),
        "peak_rss_delta_kib": rss_kib("VmHWM:") - rss0, "step_s": step_s,
    }
    recs = [None] * world
    dist.all_gather_object(recs, rec)
    if rank == 0:
        with open(a.out, "w") as f:
            json.dump(recs, f, indent=1)
        mib = 1 / 2**20
        print(f"{a.mode}{' no-reshard' if a.no_reshard else ''}: params={total_params} "
              f"persistent/rank MiB={[round(r['persistent_bytes'] * mib, 1) for r in recs]} "
              f"peak unsharded MiB={recs[0]['peak_unsharded_param_bytes'] * mib:.1f} "
              f"peak RSS delta MiB={[round(r['peak_rss_delta_kib'] / 1024) for r in recs]}")
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
