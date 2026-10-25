"""Lab 8.2: the same synthetic token dataset in four layouts, read sequentially and in random order.

Layouts: one file per sample, tar shards (WebDataset convention), one packed binary file (nanoGPT style,
read with pread or mmap), Parquet with fixed-size row groups. Everything is measured with COUNTERS, not clocks:
opens issued by Python (audit hook), read syscalls and bytes returned by them (/proc/self/io: syscr, rchar) and bytes
that really came from the block layer (/proc/self/io: read_bytes), after the page cache of the dataset files has
been dropped with posix_fadvise(DONTNEED). Throughput on a warm cache is printed for information only.

The data is SYNTHETIC (seeded pseudo-random 16-bit "tokens"); only the layout matters here, not the content.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tarfile
import time
from dataclasses import dataclass, field

import numpy as np

SAMPLE_TOKENS = 8192  # tokens per sample, 2 bytes each
SAMPLE_BYTES = SAMPLE_TOKENS * 2  # 16 KiB


def sample_bytes(i: int, seed: int = 0) -> bytes:
    rng = np.random.default_rng((seed, i))
    return rng.integers(0, 50000, size=SAMPLE_TOKENS, dtype=np.uint16).tobytes()


def digest(i: int, payload: bytes) -> int:
    """Order-independent checksum term: lets a reader prove it read the right bytes for the right index."""
    return int.from_bytes(hashlib.blake2b(payload + i.to_bytes(8, "little"), digest_size=8).digest(), "little")


@dataclass
class Dataset:
    root: str
    n: int
    shards: int
    rows_per_group: int
    files_dir: str = ""
    shard_paths: list[str] = field(default_factory=list)
    packed_path: str = ""
    parquet_path: str = ""
    shard_index: list[tuple[int, int, int]] = field(default_factory=list)  # sample i -> (shard, offset, size)

    def all_paths(self) -> list[str]:
        files = [os.path.join(self.files_dir, f) for f in sorted(os.listdir(self.files_dir))]
        return files + self.shard_paths + [self.packed_path] + ([self.parquet_path] if self.parquet_path else [])


def build(root: str, n: int = 4096, shards: int = 8, rows_per_group: int = 256, with_parquet: bool = True,
          seed: int = 0) -> Dataset:
    """Write the four layouts under `root` and return the description (incl. the tar index)."""
    assert n % shards == 0 and n % rows_per_group == 0
    ds = Dataset(root, n, shards, rows_per_group)
    ds.files_dir = os.path.join(root, "files")
    os.makedirs(ds.files_dir, exist_ok=True)
    os.makedirs(os.path.join(root, "shards"), exist_ok=True)
    per = n // shards
    ds.packed_path = os.path.join(root, "packed.bin")
    index: list[tuple[int, int, int]] = []
    with open(ds.packed_path, "wb") as packed:
        for k in range(shards):
            path = os.path.join(root, "shards", f"shard-{k:05d}.tar")
            ds.shard_paths.append(path)
            with tarfile.open(path, "w", format=tarfile.GNU_FORMAT) as tar:
                for i in range(k * per, (k + 1) * per):
                    payload = sample_bytes(i, seed)
                    with open(os.path.join(ds.files_dir, f"{i:06d}.bin"), "wb") as f:
                        f.write(payload)
                    packed.write(payload)
                    meta = json.dumps({"id": i, "tokens": SAMPLE_TOKENS}).encode()
                    for ext, data in (("bin", payload), ("json", meta)):  # same basename = same sample
                        ti = tarfile.TarInfo(f"{i:06d}.{ext}")
                        ti.size = len(data)
                        tar.addfile(ti, io.BytesIO(data))
    for k, path in enumerate(ds.shard_paths):  # tar index: where does each .bin payload start?
        with tarfile.open(path, "r") as tar:
            for ti in tar:
                if ti.name.endswith(".bin"):
                    index.append((k, ti.offset_data, ti.size))
    ds.shard_index = index
    if with_parquet:
        import pyarrow as pa
        import pyarrow.parquet as pq
        ds.parquet_path = os.path.join(root, "data.parquet")
        table = pa.table({"id": pa.array(range(n), pa.int64()),
                          "tokens": pa.array([sample_bytes(i, seed) for i in range(n)], pa.binary())})
        pq.write_table(table, ds.parquet_path, row_group_size=rows_per_group, compression="NONE")
    os.sync()
    return ds


# ---------------------------------------------------------------- readers: each returns the checksum it computed

def read_files(ds: Dataset, order) -> int:
    acc = 0
    for i in order:
        with open(os.path.join(ds.files_dir, f"{i:06d}.bin"), "rb") as f:
            acc ^= digest(i, f.read())
    return acc


def read_tar_sequential(ds: Dataset, order=None) -> int:
    acc = 0
    for path in ds.shard_paths:
        with tarfile.open(path, "r|") as tar:  # stream mode: strictly sequential, no seek
            for ti in tar:
                if ti.name.endswith(".bin"):
                    acc ^= digest(int(ti.name.split(".")[0]), tar.extractfile(ti).read())
    return acc


def read_tar_random(ds: Dataset, order) -> int:
    fds: dict[int, int] = {}
    acc = 0
    try:
        for i in order:
            k, off, size = ds.shard_index[i]
            if k not in fds:
                fds[k] = os.open(ds.shard_paths[k], os.O_RDONLY)
            acc ^= digest(i, os.pread(fds[k], size, off))
    finally:
        for fd in fds.values():
            os.close(fd)
    return acc


def read_packed_pread(ds: Dataset, order) -> int:
    acc = 0
    fd = os.open(ds.packed_path, os.O_RDONLY)
    try:
        for i in order:
            acc ^= digest(i, os.pread(fd, SAMPLE_BYTES, i * SAMPLE_BYTES))
    finally:
        os.close(fd)
    return acc


def read_packed_mmap(ds: Dataset, order) -> int:
    acc = 0
    mm = np.memmap(ds.packed_path, dtype=np.uint8, mode="r")
    for i in order:
        acc ^= digest(i, bytes(mm[i * SAMPLE_BYTES:(i + 1) * SAMPLE_BYTES]))
    del mm
    return acc


def read_parquet_sequential(ds: Dataset, order=None) -> int:
    import pyarrow.parquet as pq
    acc = 0
    pf = pq.ParquetFile(ds.parquet_path)
    i = 0
    for g in range(pf.num_row_groups):
        col = pf.read_row_group(g, columns=["tokens"]).column("tokens")
        for v in col.to_pylist():
            acc ^= digest(i, v)
            i += 1
    return acc


def read_parquet_random(ds: Dataset, order) -> int:
    """Worst case on purpose: every sample re-reads its whole row group (no cache of the last group)."""
    import pyarrow.parquet as pq
    acc = 0
    pf = pq.ParquetFile(ds.parquet_path)
    for i in order:
        g, r = divmod(i, ds.rows_per_group)
        col = pf.read_row_group(g, columns=["tokens"]).column("tokens")
        acc ^= digest(i, col[r].as_py())
    return acc


READERS = {
    ("files", "sequential"): read_files,
    ("files", "random"): read_files,
    ("tar shards", "sequential"): read_tar_sequential,
    ("tar shards", "random"): read_tar_random,
    ("packed pread", "sequential"): read_packed_pread,
    ("packed pread", "random"): read_packed_pread,
    ("packed mmap", "random"): read_packed_mmap,
    ("parquet", "sequential"): read_parquet_sequential,
    ("parquet", "random"): read_parquet_random,
}


# ---------------------------------------------------------------- measurement

def proc_io() -> dict[str, int]:
    out = {}
    with open("/proc/self/io") as f:
        for line in f:
            k, v = line.split(":")
            out[k.strip()] = int(v)
    return out


def drop_cache(paths: list[str]) -> None:
    """Ask the kernel to evict the clean pages of these files (no root needed; dirty pages must be flushed first)."""
    for p in paths:
        fd = os.open(p, os.O_RDONLY)
        try:
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        finally:
            os.close(fd)


class OpenCounter:
    """Counts Python-level open() calls on dataset files via the audit hook (what the loader itself asked for)."""

    def __init__(self, prefix: str):
        self.prefix, self.count, self.active = prefix, 0, False
        sys.addaudithook(self._hook)

    def _hook(self, event, args):
        if self.active and event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            if os.fspath(args[0]).startswith(self.prefix):
                self.count += 1


_COUNTER: OpenCounter | None = None


def measure(ds: Dataset, fmt: str, pattern: str, order: list[int]) -> dict:
    """Run one reader cold, then once more warm. Returns counters per sample and the checksum check."""
    global _COUNTER
    if _COUNTER is None:
        _COUNTER = OpenCounter(ds.root)
    fn = READERS[(fmt, pattern)]
    expected = 0
    for i in order:
        expected ^= digest(i, sample_bytes(i))
    drop_cache(ds.all_paths())
    io0, _COUNTER.count, _COUNTER.active = proc_io(), 0, True
    t0 = time.perf_counter()
    got = fn(ds, order)
    cold_s = time.perf_counter() - t0
    _COUNTER.active = False
    io1 = proc_io()
    t0 = time.perf_counter()
    fn(ds, order)
    warm_s = time.perf_counter() - t0
    n, payload = len(order), len(order) * SAMPLE_BYTES
    return {
        "format": fmt, "pattern": pattern, "samples": n, "checksum_ok": got == expected,
        "opens": _COUNTER.count,
        "read_syscalls_per_sample": (io1["syscr"] - io0["syscr"]) / n,
        "requested_over_payload": (io1["rchar"] - io0["rchar"]) / payload,
        "device_over_payload": (io1["read_bytes"] - io0["read_bytes"]) / payload,
        "warm_samples_per_s": n / warm_s,
        "cold_samples_per_s": n / cold_s,
    }
