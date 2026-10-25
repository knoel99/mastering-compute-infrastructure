"""A small data-parallel loop with a bug that makes the job hang (run with torchrun).

    torchrun --standalone --nproc_per_node=4 train_hang.py --bug skip      --journal-dir J --stacks-dir S
    torchrun --standalone --nproc_per_node=4 train_hang.py --bug stuck     ...
    torchrun --standalone --nproc_per_node=4 train_hang.py --bug none      ...   # the fixed program

Bugs (both injected on rank 2 at step 4):
  skip   rank 2 skips the gradient all-reduce of that step (a data-dependent `continue`, e.g. an
         empty batch or a NaN guard that is local to one rank). Collectives are matched by ORDER, so the
         other ranks pair their step-4 all-reduce with rank 2's step-5 one: the loop appears to work,
         the gradients are silently mixed up, and the job only hangs at the end.
  stuck  rank 2 is blocked while loading its batch, outside any collective (think: a data loader
         worker that never returns). The other ranks wait for it in the step-4 all-reduce.
"""
import argparse
import faulthandler
import os
import signal
import sys
import time
from datetime import timedelta

import torch
import torch.distributed as dist

from collective_journal import Journal

BUG_RANK, BUG_STEP, STEPS = 2, 4, 10


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bug", choices=["none", "skip", "stuck"], default="none")
    ap.add_argument("--timeout", type=float, default=8.0, help="process-group timeout in seconds")
    ap.add_argument("--journal-dir", default=None)
    ap.add_argument("--stacks-dir", default=None, help="write Python stacks of every thread after --stack-after s")
    ap.add_argument("--stack-after", type=float, default=3.0)
    ap.add_argument("--monitored", action="store_true", help="monitored_barrier before the all-reduce of every step")
    a = ap.parse_args()

    dist.init_process_group("gloo", timeout=timedelta(seconds=a.timeout))
    rank, world = dist.get_rank(), dist.get_world_size()
    journal = Journal(rank, world, a.journal_dir or os.devnull) if a.journal_dir else None
    if a.stacks_dir:
        os.makedirs(a.stacks_dir, exist_ok=True)
        f = open(os.path.join(a.stacks_dir, f"rank{rank}.txt"), "w")
        faulthandler.register(signal.SIGUSR1, file=f, all_threads=True)  # `kill -USR1 <pid>` in production
        faulthandler.dump_traceback_later(a.stack_after, file=f)  # automatic variant, used by verify.sh

    def all_reduce(t):
        journal.all_reduce(t) if journal else dist.all_reduce(t)

    t0 = time.time()

    def log(msg):
        print(f"[{time.time() - t0:5.1f}s] rank {rank} {msg}", flush=True)

    try:
        for step in range(STEPS):
            if journal:
                journal.tag = f"step={step}"
            # 1. "load the batch" (this is where the `stuck` bug blocks, outside any collective)
            if rank == BUG_RANK and step == BUG_STEP and a.bug == "stuck":
                log(f"blocks while loading the batch of step {step}, outside any collective")
                time.sleep(3600)
            grad = torch.full((1000,), float(rank + 1))
            # 2. optional synchronisation check: rank 0 names the ranks that do not arrive in time
            if a.monitored:
                dist.monitored_barrier(timeout=timedelta(seconds=3))
            # 3. gradient all-reduce (this is where the `skip` bug leaves the other ranks waiting)
            if rank == BUG_RANK and step == BUG_STEP and a.bug == "skip":
                log(f"skips the all-reduce of step {step}")
                continue
            all_reduce(grad)
            if rank == 0:
                log(f"step {step} done, reduced value {grad[0].item():.0f}")
        log("loop finished, entering final barrier")
        if journal:
            journal.tag = "final"
            journal.barrier()
        else:
            dist.barrier()
        log("final barrier passed")
    except Exception as e:  # a collective timed out or the peers went away
        log(f"FAILED {type(e).__name__}: {str(e).splitlines()[0][:160]}")
        if journal:
            journal.dump(f"exception: {type(e).__name__}")
        sys.exit(3)
    faulthandler.cancel_dump_traceback_later()
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
