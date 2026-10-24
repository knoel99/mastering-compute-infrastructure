"""Checkpoints — NAIVE VERSION. It works on a good day and loses your run on a bad one.

Your job (milestones 1 and 2 of the project): make it atomic, checksummed, rotating,
with a fallback to the previous checkpoint. Keep these four function signatures,
train.py and the tests depend on them.
"""
from pathlib import Path

import torch


def list_ckpts(d):
    out = []
    for p in Path(d).glob("ckpt-*.pt"):
        out.append((int(p.stem.split("-")[1]), p))
    return sorted(out)


def save(workdir, step, state, keep=3, crash_midwrite=False):
    d = Path(workdir) / "ckpt"
    d.mkdir(parents=True, exist_ok=True)
    final = d / f"ckpt-{step:08d}.pt"
    # TODO: this writes straight to the final name. A crash in the middle leaves a torn
    # file that looks like the newest checkpoint. Also: no fsync, no rotation (keep is ignored).
    if crash_midwrite:
        import io
        import os

        buf = io.BytesIO()
        torch.save(state, buf)
        final.write_bytes(buf.getvalue()[: len(buf.getvalue()) // 2])
        os._exit(137)
    torch.save({"step": step, "model": state["model"]}, final)  # TODO: optimizer, RNG states are missing
    return final


def load_latest(workdir):
    d = Path(workdir) / "ckpt"
    if not d.is_dir() or not list_ckpts(d):
        return None, None, []
    step, path = list_ckpts(d)[-1]
    # TODO: a corrupted newest file raises here and the job can never restart.
    return step, torch.load(path, map_location="cpu", weights_only=True), []
