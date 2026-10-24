#!/usr/bin/env python3
"""A small, fully deterministic CPU trainer whose complete state can be checkpointed.

State that must survive a crash for the run to be *identical* to an uninterrupted one:
  model weights, optimizer moments, learning-rate schedule position, the global RNG (dropout masks)
  and the data cursor (which epoch, which position in the shuffled order).
`--omit` leaves one of them out on purpose, to measure what it protects.
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

import torch
from torch import nn

import ckpt

PARTS = ("model", "optim", "sched", "rng", "cursor")
OMITTABLE = {"optimizer": "optim", "scheduler": "sched", "rng": "rng", "cursor": "cursor"}


class Cursor:
    """Shuffled epochs. State = (epoch, position, generator state at the start of the epoch)."""

    def __init__(self, n, bs, seed):
        self.n, self.bs = n, bs
        self.gen = torch.Generator().manual_seed(seed)
        self.epoch, self.pos = 0, 0
        self._start_epoch()

    def _start_epoch(self):
        self.epoch_state = self.gen.get_state()
        self.perm = torch.randperm(self.n, generator=self.gen)

    def next_indices(self):
        if self.pos + self.bs > self.n:
            self.epoch, self.pos = self.epoch + 1, 0
            self._start_epoch()
        idx = self.perm[self.pos:self.pos + self.bs]
        self.pos += self.bs
        return idx

    def state(self):
        return {"epoch": self.epoch, "pos": self.pos, "epoch_state": self.epoch_state}

    def load(self, st):
        self.gen.set_state(st["epoch_state"])
        self.epoch, self.pos = int(st["epoch"]), int(st["pos"])
        self._start_epoch()  # redraws the same permutation and leaves the generator where it was


class Trainer:
    def __init__(self, seed=0, steps=60, n=512, d=16, bs=16, omit=()):
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        self.seed, self.steps, self.omit = seed, steps, set(omit)
        g = torch.Generator().manual_seed(1234)  # the dataset itself is fixed
        self.x = torch.randn(n, d, generator=g)
        self.y = torch.sin(self.x @ torch.randn(d, 1, generator=g)) + 0.05 * torch.randn(n, 1, generator=g)
        torch.manual_seed(seed)
        self.model = nn.Sequential(nn.Linear(d, 64), nn.ReLU(), nn.Dropout(0.1), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 1))
        self.opt = torch.optim.Adam(self.model.parameters(), lr=1e-2)
        self.sched = torch.optim.lr_scheduler.LambdaLR(self.opt, lambda t: 0.5 * (1 + math.cos(math.pi * min(t, steps) / steps)))
        self.cursor = Cursor(n, bs, seed)
        self.step = 0
        self.losses = {}

    def parts(self):
        full = {"model": self.model.state_dict(), "optim": self.opt.state_dict(), "sched": self.sched.state_dict(),
                "rng": {"torch": torch.get_rng_state()}, "cursor": self.cursor.state()}
        skip = {OMITTABLE[o] for o in self.omit}
        return {k: v for k, v in full.items() if k not in skip}

    def restore(self, parts):
        self.model.load_state_dict(parts["model"])
        if "optim" in parts:
            self.opt.load_state_dict(parts["optim"])
        if "sched" in parts:
            self.sched.load_state_dict(parts["sched"])
        if "rng" in parts:
            torch.set_rng_state(parts["rng"]["torch"])
        if "cursor" in parts:
            self.cursor.load(parts["cursor"])

    def train_step(self):
        idx = self.cursor.next_indices()
        self.model.train()
        loss = nn.functional.mse_loss(self.model(self.x[idx]), self.y[idx])
        self.opt.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.opt.step()
        self.sched.step()
        self.step += 1
        return loss.item()

    def digest(self):
        h = hashlib.sha256()
        for sd in (self.model.state_dict(), self.opt.state_dict()["state"]):
            for k in sorted(sd, key=str):
                items = sd[k].items() if isinstance(sd[k], dict) else [("", sd[k])]
                for kk, v in sorted(items, key=lambda t: str(t[0])):
                    if torch.is_tensor(v):
                        h.update(v.detach().numpy().tobytes())
        return h.hexdigest()


def run(workdir, steps, ckpt_every, seed=0, omit=(), stop_after=None, sleep_ms=0.0, slow_ckpt_ms=0.0, log=True, verbose=False):
    """Train from the latest valid checkpoint up to `steps` (or `stop_after`). Returns the Trainer."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    tr = Trainer(seed=seed, steps=steps, omit=omit)
    torn = len(list((workdir / "ckpt").glob("*.tmp"))) if (workdir / "ckpt").is_dir() else 0
    step, parts, skipped = ckpt.load_latest(workdir / "ckpt")
    if parts:
        tr.restore(parts)
        tr.step = step
    if verbose:
        print(f"READY resumed_from={tr.step} torn_tmp_found={torn} skipped={len(skipped)}", flush=True)
    delay = (lambda name: time.sleep(slow_ckpt_ms / 1000.0)) if slow_ckpt_ms else None
    logf = open(workdir / "loss.jsonl", "a") if log else None
    stop = steps if stop_after is None else min(steps, stop_after)
    while tr.step < stop:
        s = tr.step
        loss = tr.train_step()
        tr.losses[s] = loss
        if logf:
            logf.write(json.dumps({"step": s, "loss": repr(loss)}) + "\n")
            logf.flush()
        if sleep_ms:
            time.sleep(sleep_ms / 1000.0)
        if tr.step % ckpt_every == 0 and tr.step < steps:
            ckpt.save(workdir / "ckpt", tr.step, tr.parts(), after_part=delay)
    if tr.step >= steps:
        (workdir / "final.json").write_text(json.dumps({"step": tr.step, "digest": tr.digest()}))
    return tr


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--steps", type=int, default=100)
    ap.add_argument("--ckpt-every", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--omit", action="append", default=[], choices=sorted(OMITTABLE))
    ap.add_argument("--sleep-ms", type=float, default=0.0, help="simulated compute time per step")
    ap.add_argument("--slow-ckpt-ms", type=float, default=0.0, help="simulated storage latency per checkpoint part")
    a = ap.parse_args(argv)
    run(a.workdir, a.steps, a.ckpt_every, a.seed, a.omit, None, a.sleep_ms, a.slow_ckpt_ms, verbose=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
