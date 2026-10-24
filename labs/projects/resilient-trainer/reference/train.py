#!/usr/bin/env python3
"""Small CPU trainer with deterministic data, dropout, AdamW and fault injection hooks.

FAULT=kill:N   SIGKILL itself just before step N      (once per workdir)
FAULT=hang:N   sleep forever just before step N       (once per workdir)
FAULT=torn:N   die in the middle of the checkpoint written at step N (once)
"""
import argparse
import json
import os
import random
import signal
import sys
import time
from pathlib import Path

import torch
from torch import nn

import ckpt


def build(seed):
    torch.manual_seed(seed)
    model = nn.Sequential(nn.Linear(16, 64), nn.ReLU(), nn.Dropout(0.1), nn.Linear(64, 1))
    opt = torch.optim.AdamW(model.parameters(), lr=1e-2)
    return model, opt


def batch(seed, step):
    """Deterministic data: the batch depends only on (seed, step), so the data cursor is the step."""
    g = torch.Generator().manual_seed(seed * 1_000_003 + step)
    x = torch.randn(32, 16, generator=g)
    w = torch.linspace(-1, 1, 16)
    y = (x @ w).unsqueeze(1) + 0.1 * torch.randn(32, 1, generator=g)
    return x, y


def fault_for(workdir):
    spec = os.environ.get("FAULT", "")
    if not spec or (Path(workdir) / ".fault-done").exists():
        return None, None
    kind, _, n = spec.partition(":")
    return kind, int(n)


def trigger(workdir):
    (Path(workdir) / ".fault-done").write_text("1")


def snapshot(model, opt, step, pad):
    state = {
        "step": step,
        "model": model.state_dict(),
        "opt": opt.state_dict(),
        "rng_torch": torch.get_rng_state(),
        "rng_python": random.getstate(),
    }
    if pad is not None:
        state["pad"] = pad
    return state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--steps", type=int, default=120)
    ap.add_argument("--ckpt-every", type=int, default=10)
    ap.add_argument("--keep", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--pad-mb", type=float, default=0.0, help="extra dummy state, to emulate a larger model")
    args = ap.parse_args()

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    model, opt = build(args.seed)
    pad = torch.zeros(int(args.pad_mb * 262144)) if args.pad_mb else None

    step, state, skipped = ckpt.load_latest(work)
    if state is not None:
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["opt"])
        torch.set_rng_state(state["rng_torch"])
        random.setstate(state["rng_python"])
    else:
        step = 0
    with open(work / "events.jsonl", "a") as ev:
        ev.write(json.dumps({"event": "start", "resumed_from": step, "skipped": skipped}) + "\n")

    kind, at = fault_for(work)
    heartbeat = work / "heartbeat"
    model.train()
    with open(work / "loss.jsonl", "a") as log, open(work / "ckpt.jsonl", "a") as cj:
        while step < args.steps:
            if kind in ("kill", "hang") and step + 1 == at:
                trigger(work)
                if kind == "kill":
                    os.kill(os.getpid(), signal.SIGKILL)
                while True:
                    time.sleep(3600)
            step += 1
            x, y = batch(args.seed, step)
            loss = nn.functional.mse_loss(model(x), y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            log.write(json.dumps({"step": step, "loss": loss.item()}) + "\n")
            log.flush()
            heartbeat.touch()
            if step % args.ckpt_every == 0:
                torn = kind == "torn" and step == at
                if torn:
                    trigger(work)
                t0 = time.perf_counter()
                path = ckpt.save(work, step, snapshot(model, opt, step, pad), keep=args.keep, crash_midwrite=torn)
                cj.write(json.dumps({"step": step, "seconds": time.perf_counter() - t0, "bytes": path.stat().st_size}) + "\n")
                cj.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
