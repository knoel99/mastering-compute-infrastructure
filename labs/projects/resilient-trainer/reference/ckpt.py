"""Atomic, checksummed, rotating checkpoints (reference solution)."""
import hashlib
import io
import os
import re
from pathlib import Path

import torch

MAGIC = b"MCICKPT1"
NAME_RE = re.compile(r"^ckpt-(\d{8})\.pt$")


def _name(step):
    return f"ckpt-{step:08d}.pt"


def pack(state):
    """Serialise a state dict as MAGIC + sha256(payload) + payload."""
    buf = io.BytesIO()
    torch.save(state, buf)
    payload = buf.getvalue()
    return MAGIC + hashlib.sha256(payload).digest() + payload


def unpack(blob):
    """Inverse of pack(); raises ValueError on a truncated or corrupted blob."""
    if len(blob) < 40 or blob[:8] != MAGIC:
        raise ValueError("bad header")
    digest, payload = blob[8:40], blob[40:]
    if hashlib.sha256(payload).digest() != digest:
        raise ValueError("checksum mismatch")
    return torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)


def _fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def list_ckpts(d):
    """Return [(step, path)] sorted by step, newest last."""
    out = []
    for p in Path(d).glob("ckpt-*.pt"):
        m = NAME_RE.match(p.name)
        if m:
            out.append((int(m.group(1)), p))
    return sorted(out)


def save(workdir, step, state, keep=3, crash_midwrite=False):
    """Write the checkpoint atomically, then drop all but the `keep` newest.

    crash_midwrite is a fault-injection hook: write half of the file, then die
    the way a killed node would, leaving a torn temporary file behind.
    """
    d = Path(workdir) / "ckpt"
    d.mkdir(parents=True, exist_ok=True)
    for stale in d.glob("*.tmp"):
        stale.unlink()
    blob = pack(state)
    final = d / _name(step)
    tmp = d / (_name(step) + ".tmp")
    with open(tmp, "wb") as f:
        if crash_midwrite:
            f.write(blob[: len(blob) // 2])
            f.flush()
            os.fsync(f.fileno())
            os._exit(137)
        f.write(blob)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, final)
    _fsync_dir(d)
    for _, old in list_ckpts(d)[:-keep]:
        old.unlink()
    return final


def load_latest(workdir):
    """Return (step, state, skipped) for the newest checkpoint that verifies.

    `skipped` lists (filename, reason) for every newer file that was rejected.
    Returns (None, None, skipped) when nothing usable exists.
    """
    d = Path(workdir) / "ckpt"
    skipped = []
    if not d.is_dir():
        return None, None, skipped
    for step, path in reversed(list_ckpts(d)):
        try:
            return step, unpack(path.read_bytes()), skipped
        except Exception as exc:  # corrupted file: fall back to the previous one
            skipped.append((path.name, str(exc)))
    return None, None, skipped
