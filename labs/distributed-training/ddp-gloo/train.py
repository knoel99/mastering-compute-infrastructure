"""Train the lab MLP on a seeded synthetic task, with or without DistributedDataParallel.

    python3 train.py --out single.json                         # one process, whole global batch
    torchrun --standalone --nproc_per_node=4 train.py --out ddp.json

With torchrun (WORLD_SIZE set) the model is wrapped in DDP over the gloo backend; otherwise it
runs in a single process. Rank 0 writes a JSON file (losses, final parameter digest, bucket
information, communication statistics) and a .pt file with the final flat parameter vector.
"""
import argparse
import json
import os
import statistics
import time
from datetime import timedelta

import torch
import torch.distributed as dist
from torch import nn
from torch.nn.parallel import DistributedDataParallel as DDP

from common import build_model, flat_params, global_batch, shard_bounds


class CommStats:
    """Counts the all-reduce calls DDP issues (one per bucket) and the bytes they carry."""

    def __init__(self, world):
        self.world, self.calls, self.bytes, self.in_flight_s = world, 0, 0, 0.0

    def hook(self, state, bucket):
        buf = bucket.buffer()
        t0 = time.perf_counter()
        self.calls += 1
        self.bytes += buf.numel() * buf.element_size()
        buf.div_(self.world)  # same as DDP's default hook: divide first, then sum
        fut = dist.all_reduce(buf, async_op=True).get_future()

        def done(f):
            self.in_flight_s += time.perf_counter() - t0
            return f.value()[0]

        return fut.then(done)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--global-batch", type=int, default=64)
    ap.add_argument("--optim", choices=["sgd", "adamw"], default="sgd")
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--bucket-cap-mb", type=float, default=None)
    ap.add_argument("--uneven", action="store_true", help="ragged split of the global batch (a bug)")
    ap.add_argument("--hook", action="store_true", help="count buckets and bytes with a communication hook")
    ap.add_argument("--timing", action="store_true", help="also time a no_sync (no communication) loop")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    torch.set_num_threads(1)
    distributed = "WORLD_SIZE" in os.environ
    if distributed:
        dist.init_process_group("gloo", timeout=timedelta(seconds=60))
    rank = dist.get_rank() if distributed else 0
    world = dist.get_world_size() if distributed else 1

    model = build_model(a.seed)
    stats = CommStats(world)
    if distributed:
        kw = {} if a.bucket_cap_mb is None else {"bucket_cap_mb": a.bucket_cap_mb}
        model = DDP(model, **kw)
        if a.hook:
            model.register_comm_hook(None, stats.hook)
    opt = (torch.optim.SGD(model.parameters(), lr=a.lr) if a.optim == "sgd"
           else torch.optim.AdamW(model.parameters(), lr=a.lr))
    loss_fn = nn.MSELoss()

    def step_fn(step, sync=True):
        x, y = global_batch(step, a.global_batch, a.seed)
        lo, hi = shard_bounds(a.global_batch, rank, world, a.uneven) if distributed else (0, a.global_batch)
        opt.zero_grad(set_to_none=True)
        ctx = model.no_sync() if (distributed and not sync) else torch.enable_grad()
        with ctx:
            loss = loss_fn(model(x[lo:hi]), y[lo:hi])
            loss.backward()
        opt.step()
        return loss.item() * (hi - lo), float(hi - lo)  # (sum of per-sample losses, samples)

    local, durations = [], []
    for step in range(a.steps):
        t0 = time.perf_counter()
        local.append(step_fn(step))
        durations.append(time.perf_counter() - t0)
    stat = torch.tensor(local, dtype=torch.float64)  # one collective for all the logging, outside the timed loop
    if distributed:
        dist.all_reduce(stat)
    losses = (stat[:, 0] / stat[:, 1]).tolist()  # global mean loss per step, weighted by samples

    flat = flat_params(model.module if distributed else model)  # final parameters of the training loop
    result = {"world": world, "optim": a.optim, "steps": a.steps, "global_batch": a.global_batch,
              "uneven": a.uneven, "losses_global": losses}
    if distributed:
        d = model._get_ddp_logging_data()  # private API: names may change between releases
        result["ddp_rebuilt_bucket_sizes"] = [int(s) for s in str(d.get("rebuilt_bucket_sizes", "")).split(", ") if s]
        result["ddp_total_param_bytes"] = int(d["total_parameter_size_bytes"])
        result["ddp_bucket_cap_bytes"] = int(d["bucket_cap_bytes"])
        if a.hook:
            result["hook_calls"] = stats.calls
            result["hook_bytes"] = stats.bytes
            result["hook_in_flight_s_per_step"] = stats.in_flight_s / a.steps
    if a.timing:
        if distributed:
            dist.barrier()
        local_durations = []
        for step in range(a.steps):
            t0 = time.perf_counter()
            step_fn(a.steps + step, sync=False)
            local_durations.append(time.perf_counter() - t0)
        warm = min(5, a.steps // 2)  # skip the first steps: bucket rebuild, allocator warm-up
        result["step_s_sync_median"] = statistics.median(durations[warm:])
        result["step_s_no_sync_median"] = statistics.median(local_durations[warm:])
        if distributed:  # isolated all-reduce time of each bucket, to compare with the exposed cost
            iso = 0.0
            for nbytes in result["ddp_rebuilt_bucket_sizes"]:
                buf, reps = torch.zeros(nbytes // 4), []
                for _ in range(15):
                    dist.barrier()
                    t0 = time.perf_counter()
                    dist.all_reduce(buf)
                    reps.append(time.perf_counter() - t0)
                iso += statistics.median(reps[3:])
            result["isolated_allreduce_s_per_step"] = iso
    # every rank must hold the same parameters: compare with rank 0's copy
    if distributed:
        ref = flat.clone()
        dist.broadcast(ref, src=0)
        result["max_abs_diff_to_rank0"] = float((flat - ref).abs().max())
    if rank == 0:
        torch.save(flat, a.out.replace(".json", ".pt"))
        result["param_checksum"] = float(flat.double().sum())
        with open(a.out, "w") as f:
            json.dump(result, f, indent=1)
        print(f"world={world} optim={a.optim} final_global_loss={losses[-1]:.6f} "
              f"max_abs_diff_to_rank0={result.get('max_abs_diff_to_rank0', 'n/a')}")
    if distributed:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
