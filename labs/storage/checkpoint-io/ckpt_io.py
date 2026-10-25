"""Checkpoint write strategies and their cost model (lab 8.3).

Everything here works on a plain byte buffer, because the I/O cost of a checkpoint depends on how many bytes
go where, not on what they mean. A real training state would be a dict of tensors (see labs/fault-tolerance).

SIMULATED parts, labelled as such on the course page:
  * `throttle_mbps` slows the writer down to a chosen rate (a stand-in for a shared, slower file system);
  * `snapshot` is a host-memory copy (a stand-in for the GPU-to-host copy, there is no GPU here).
"""
from __future__ import annotations

import mmap
import os
import threading
import time
from dataclasses import dataclass, field

import numpy as np

MIB = 1 << 20
ALIGN = 4096  # O_DIRECT needs buffers, offsets and lengths aligned to the logical block size (4096 is safe)


def make_state(nbytes: int, seed: int = 0) -> np.ndarray:
    """Pseudo-random bytes: incompressible, so no layer below can cheat with zero pages or compression."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=nbytes, dtype=np.uint8)


def _pace(written: int, t0: float, mbps: float | None) -> None:
    """Sleep so that the cumulative rate never exceeds `mbps` MiB/s (simulated slow storage)."""
    if not mbps:
        return
    due = written / (mbps * MIB)
    now = time.perf_counter() - t0
    if due > now:
        time.sleep(due - now)


def write_buffered(path: str, buf: np.ndarray, chunk: int = 8 * MIB, throttle_mbps: float | None = None) -> None:
    """Plain write(): the page cache absorbs the bytes, nothing says they are durable."""
    mv = memoryview(buf)
    t0 = time.perf_counter()
    with open(path, "wb") as f:
        for off in range(0, len(buf), chunk):
            f.write(mv[off:off + chunk])
            _pace(min(off + chunk, len(buf)), t0, throttle_mbps)


def fsync_dir(dirname: str) -> None:
    fd = os.open(dirname, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_atomic(path: str, buf: np.ndarray, chunk: int = 8 * MIB, throttle_mbps: float | None = None,
                 fail_after: int | None = None) -> None:
    """Durable and atomic: write a temporary file, fsync it, rename it, fsync the directory.

    `fail_after` (tests only) raises after that many bytes, to prove that no partial file becomes visible.
    """
    tmp = path + ".tmp"
    mv = memoryview(buf)
    t0 = time.perf_counter()
    with open(tmp, "wb") as f:
        for off in range(0, len(buf), chunk):
            if fail_after is not None and off >= fail_after:
                raise OSError("injected failure")
            f.write(mv[off:off + chunk])
            _pace(min(off + chunk, len(buf)), t0, throttle_mbps)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    fsync_dir(os.path.dirname(os.path.abspath(path)))


def write_direct(path: str, buf: np.ndarray, chunk: int = 8 * MIB) -> None:
    """O_DIRECT: bypass the page cache. Buffers, offsets and lengths must be aligned (an unaligned write fails with EINVAL).

    Raises OSError if the file system refuses O_DIRECT (support depends on the file system and the kernel).
    """
    n = len(buf)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_DIRECT
    fd = os.open(path, flags, 0o644)
    try:
        bounce = mmap.mmap(-1, chunk)  # anonymous mapping: page aligned
        mv = memoryview(buf)
        for off in range(0, n, chunk):
            piece = mv[off:off + chunk]
            m = len(piece)
            padded = -(-m // ALIGN) * ALIGN
            bounce[:m] = piece
            if padded > m:
                bounce[m:padded] = bytes(padded - m)
            os.write(fd, memoryview(bounce)[:padded])
        os.ftruncate(fd, n)
        os.fsync(fd)
    finally:
        os.close(fd)


def read_back_equal(path: str, buf: np.ndarray) -> bool:
    return np.array_equal(np.fromfile(path, dtype=np.uint8), buf)


def proc_io() -> dict[str, int]:
    """Kernel I/O counters of this process (/proc/self/io): write_bytes is the number of bytes really sent to the storage layer (proc_pid_io(5))."""
    out = {}
    with open("/proc/self/io") as f:
        for line in f:
            k, v = line.split(":")
            out[k.strip()] = int(v)
    return out


@dataclass
class AsyncCheckpointer:
    """Two-phase checkpoint: a blocking snapshot, then a background persistence (one in flight at most).

    The staging buffer is allocated and touched once (`prepare`) and reused: on the sandbox VM the first touch of
    256 MiB of fresh memory took about a second, tens of times a steady-state copy (it varies from run to run). Real trainers do the same
    with a reused pinned buffer.
    """

    directory: str
    throttle_mbps: float | None = None
    _thread: threading.Thread | None = field(default=None, init=False)
    _error: BaseException | None = field(default=None, init=False)
    _stage: np.ndarray | None = field(default=None, init=False)

    def prepare(self, nbytes: int) -> None:
        self._stage = np.empty(nbytes, dtype=np.uint8)
        self._stage[:] = 0  # first touch now, not inside the first checkpoint

    def _persist(self, path: str) -> None:
        try:
            write_atomic(path, self._stage, throttle_mbps=self.throttle_mbps)
        except BaseException as e:  # noqa: BLE001 - re-raised in wait()
            self._error = e

    def save(self, step: int, state: np.ndarray) -> dict[str, float]:
        """Return the time this call blocked the caller: waiting for the previous write + the snapshot copy."""
        if self._stage is None or len(self._stage) != len(state):
            self.prepare(len(state))
        t0 = time.perf_counter()
        self.wait()  # the staging buffer is still being written: at most one persistence in flight
        t1 = time.perf_counter()
        np.copyto(self._stage, state)  # the consistent snapshot: the only part that must stop training
        t2 = time.perf_counter()
        path = os.path.join(self.directory, f"ckpt-{step:06d}.bin")
        self._thread = threading.Thread(target=self._persist, args=(path,), daemon=True)
        self._thread.start()
        return {"wait": t1 - t0, "snapshot": t2 - t1, "blocked": t2 - t0}

    def wait(self) -> None:
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        if self._error is not None:
            err, self._error = self._error, None
            raise err


def simulate_training(n_steps: int, step_s: float, ckpt_every: int, mode: str, state: np.ndarray,
                      directory: str, throttle_mbps: float | None = None) -> dict[str, float]:
    """A training loop whose GPU step is a sleep (SIMULATED), with a checkpoint every `ckpt_every` steps.

    mode: 'none' | 'sync' (write_atomic in the loop) | 'async' (AsyncCheckpointer).
    Returns wall time, ideal time and the overhead fraction (wall - ideal) / ideal.
    """
    ck = AsyncCheckpointer(directory, throttle_mbps) if mode == "async" else None
    if ck is not None:
        ck.prepare(len(state))
    blocked = 0.0
    t0 = time.perf_counter()
    for step in range(1, n_steps + 1):
        time.sleep(step_s)
        if mode != "none" and step % ckpt_every == 0:
            b0 = time.perf_counter()
            if mode == "sync":
                write_atomic(os.path.join(directory, f"ckpt-{step:06d}.bin"), state, throttle_mbps=throttle_mbps)
            else:
                ck.save(step, state)
            blocked += time.perf_counter() - b0
    wall = time.perf_counter() - t0  # the persistence still running at the end is not part of the steady-state cost
    if ck is not None:
        ck.wait()  # ... but we must not leak the thread
    ideal = n_steps * step_s
    return {"wall_s": wall, "ideal_s": ideal, "blocked_s": blocked, "overhead": (wall - ideal) / ideal}


def fit_alpha_beta(sizes_bytes: list[float], times_s: list[float]) -> tuple[float, float]:
    """Least squares T = alpha + S / B on the relative error (weights 1/T), returns (alpha_s, B_bytes_per_s)."""
    s = np.asarray(sizes_bytes, dtype=float)
    t = np.asarray(times_s, dtype=float)
    w = 1.0 / t
    a = np.vstack([np.ones_like(s), s]).T * w[:, None]
    (alpha, inv_b), *_ = np.linalg.lstsq(a, t * w, rcond=None)
    if inv_b <= 0:
        raise ValueError("non-positive slope: the times do not grow with the size")
    return float(max(alpha, 0.0)), float(1.0 / inv_b)


def predict(alpha: float, bandwidth: float, size_bytes: float) -> float:
    return alpha + size_bytes / bandwidth


def median_rel_error(sizes: list[float], times: list[float], alpha: float, bandwidth: float) -> float:
    errs = [abs(predict(alpha, bandwidth, s) - t) / t for s, t in zip(sizes, times)]
    return float(np.median(errs))
