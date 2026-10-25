#!/usr/bin/env python3
"""Toy resumable trainer for the preemption rehearsal. It trains NOTHING: the "model" is one integer updated by a
deterministic rule, so a run that was preempted and resumed must end with exactly the value of an uninterrupted run.

It shows the three things a job needs to survive a preemption anywhere: an atomic checkpoint written to storage that
outlives the VM, an automatic resume, and (optionally) a handler for the termination notice (SIGTERM).
"""
import argparse
import json
import os
import signal
import sys
import tempfile
from pathlib import Path

MOD = 1_000_000_007


def update(state, step):
    return (state * 31 + step) % MOD


def load(ckpt_dir):
    path = Path(ckpt_dir) / "ckpt.json"
    if not path.exists():
        return 0, 0
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["step"], data["state"]


def save(ckpt_dir, step, state):
    """Atomic: write a temporary file in the same directory, flush it to disk, then rename over the old one."""
    Path(ckpt_dir).mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=ckpt_dir, prefix=".ckpt-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump({"step": step, "state": state}, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, Path(ckpt_dir) / "ckpt.json")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--total-steps", type=int, default=200)
    ap.add_argument("--ckpt-every", type=int, default=25)
    ap.add_argument("--attempt", type=int, default=1, help="1 for the first VM, 2 after the first preemption, ...")
    ap.add_argument("--preempt-at-step", type=int, default=0, help="SIMULATED preemption, first attempt only")
    ap.add_argument("--preempt-mode", choices=["kill", "term"], default="kill",
                    help="kill: SIGKILL, no notice. term: SIGTERM, the handler gets a notice and saves")
    args = ap.parse_args(argv)

    step, state = load(args.ckpt_dir)
    print(f"attempt={args.attempt} resumed_from_step={step}", flush=True)

    def on_notice(signum, frame):  # the termination notice: save what we have, then leave
        save(args.ckpt_dir, step, state)
        print(f"attempt={args.attempt} notice_saved_step={step}", flush=True)
        sys.exit(143)

    if args.preempt_mode == "term":
        signal.signal(signal.SIGTERM, on_notice)
    for s in range(step + 1, args.total_steps + 1):
        state = update(state, s)
        step = s
        if s % args.ckpt_every == 0:
            save(args.ckpt_dir, step, state)
        if args.attempt == 1 and args.preempt_at_step and s == args.preempt_at_step:
            os.kill(os.getpid(), signal.SIGKILL if args.preempt_mode == "kill" else signal.SIGTERM)
    save(args.ckpt_dir, step, state)
    print(f"attempt={args.attempt} done step={step} state={state}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
