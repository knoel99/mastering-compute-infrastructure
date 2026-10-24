"""Directory checkpoints committed by a single rename, with a manifest written last.

Layout of one checkpoint:   <root>/step-00000040/{model.pt, optim.pt, ..., MANIFEST.json}
Protocol (what makes the checkpoint atomic and verifiable):
  1. write every part into <root>/step-00000040.tmp/ and fsync each file;
  2. write MANIFEST.json (size and sha256 of each part) last, fsync it, fsync the directory;
  3. rename the directory to its final name (atomic on a POSIX file system) and fsync <root>.
A reader accepts a directory only if MANIFEST.json exists and every hash matches, so a crash at
any point leaves either the previous checkpoint or the new one, never a mixture.
"""
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

import torch

NAME = re.compile(r"^step-(\d{8})$")


def _fsync_dir(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def committed(root):
    """[(step, path)] of committed directories, oldest first (validity is NOT checked here)."""
    out = []
    for p in Path(root).glob("step-*"):
        m = NAME.match(p.name)
        if m and p.is_dir():
            out.append((int(m.group(1)), p))
    return sorted(out)


def save(root, step, parts, keep=3, after_part=None):
    """Write `parts` (name -> object accepted by torch.save) as checkpoint `step`.

    after_part(name) is called once a part is durable: tests use it to die in the middle of a
    save, and the chaos lab uses it to simulate a slow storage backend.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for stale in root.glob("*.tmp"):
        shutil.rmtree(stale, ignore_errors=True)
    final = root / f"step-{step:08d}"
    tmp = root / f"step-{step:08d}.tmp"
    if final.exists():  # a previous life left this step behind
        if verify(final) is None:
            return final  # already durable and valid: saving twice is a no-op
        quarantine = root / (final.name + ".corrupt")  # keep the evidence, free the name
        shutil.rmtree(quarantine, ignore_errors=True)
        os.rename(final, quarantine)
    tmp.mkdir()
    files = {}
    for name, obj in parts.items():
        p = tmp / f"{name}.pt"
        with open(p, "wb") as f:
            torch.save(obj, f)
            f.flush()
            os.fsync(f.fileno())
        files[p.name] = {"bytes": p.stat().st_size, "sha256": _sha256(p)}
        if after_part:
            after_part(name)
    with open(tmp / "MANIFEST.json", "w") as f:
        json.dump({"step": step, "files": files}, f, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    _fsync_dir(tmp)
    os.rename(tmp, final)  # the commit point
    _fsync_dir(root)
    for _, old in committed(root)[:-keep]:
        shutil.rmtree(old, ignore_errors=True)
    return final


def verify(path):
    """Return None if the directory is a valid checkpoint, else a short reason."""
    mf = Path(path) / "MANIFEST.json"
    if not mf.is_file():
        return "no MANIFEST.json"
    try:
        files = json.loads(mf.read_text())["files"]
    except Exception as exc:  # noqa: BLE001
        return f"unreadable manifest ({exc.__class__.__name__})"
    for name, meta in files.items():
        p = Path(path) / name
        if not p.is_file():
            return f"{name} missing"
        if p.stat().st_size != meta["bytes"]:
            return f"{name} has the wrong size"
        if _sha256(p) != meta["sha256"]:
            return f"{name} sha256 mismatch"
    return None


def load_latest(root):
    """(step, parts, skipped): newest checkpoint that verifies; `skipped` lists rejected ones."""
    skipped = []
    for step, path in reversed(committed(root)):
        why = verify(path)
        if why:
            skipped.append((path.name, why))
            continue
        parts = {p.stem: torch.load(p, map_location="cpu", weights_only=True) for p in sorted(path.glob("*.pt"))}
        return step, parts, skipped
    return None, None, skipped
