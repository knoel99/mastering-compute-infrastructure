#!/usr/bin/env python3
"""Lab 8.2 driver, part A: counters for four layouts x two access patterns on a freshly built synthetic dataset.

Usage: python3 run_shards.py [--dir DIR] [--samples 4096] [--random 1024] [--out result.json]
DIR should be on a disk-backed file system (not tmpfs): posix_fadvise(DONTNEED) is what makes reads cold, and tmpfs pages are memory.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import tempfile

import shard_lab as S


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None)
    ap.add_argument("--samples", type=int, default=4096)
    ap.add_argument("--random", type=int, default=1024, help="how many samples the random pattern reads")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    try:
        import pyarrow  # noqa: F401
        with_parquet = True
    except ImportError:
        with_parquet = False
        print("pyarrow is not installed: the Parquet rows are skipped (pip install pyarrow)")
    root = tempfile.mkdtemp(prefix="shard-lab-", dir=args.dir)
    try:
        ds = S.build(root, n=args.samples, with_parquet=with_parquet)
        with open("/sys/block/vda/queue/read_ahead_kb") as f:
            ra = f.read().strip()
    except OSError:
        ra = "unknown"
    try:
        print("dataset: %d samples x %d KiB = %d MiB; %d tar shards; Parquet row group = %d rows = %d MiB; readahead of vda: %s KiB"
              % (ds.n, S.SAMPLE_BYTES // 1024, ds.n * S.SAMPLE_BYTES >> 20, ds.shards, ds.rows_per_group,
                 ds.rows_per_group * S.SAMPLE_BYTES >> 20, ra))
        order_seq = list(range(ds.n))
        order_rnd = random.Random(0).sample(range(ds.n), args.random)
        print("%-13s %-10s %6s %6s %9s %9s %9s %12s" % ("layout", "pattern", "n", "opens", "read()/smp", "asked/pay", "device/pay", "warm smp/s"))
        rows = []
        for (fmt, pat) in S.READERS:
            if fmt == "parquet" and not with_parquet:
                continue
            m = S.measure(ds, fmt, pat, order_seq if pat == "sequential" else order_rnd)
            rows.append(m)
            print("%-13s %-10s %6d %6s %9.2f %9.2f %9.2f %12.0f%s" % (
                fmt, pat, m["samples"], "n/a" if fmt == "parquet" else m["opens"], m["read_syscalls_per_sample"],
                m["requested_over_payload"], m["device_over_payload"], m["warm_samples_per_s"],
                "" if m["checksum_ok"] else "  CHECKSUM MISMATCH"))
        print("asked/pay = bytes returned by read syscalls (rchar) / bytes the loader needed; device/pay = bytes really fetched from the storage layer (read_bytes) / same.")
        if args.out:
            with open(args.out, "w") as f:
                json.dump({"dataset": {"n": ds.n, "shards": ds.shards, "rows_per_group": ds.rows_per_group,
                                       "sample_bytes": S.SAMPLE_BYTES, "readahead_kb": ra}, "rows": rows}, f, indent=1)
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
