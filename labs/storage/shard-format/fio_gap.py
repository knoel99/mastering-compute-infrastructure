#!/usr/bin/env python3
"""Lab 8.2 driver, part B: how much does the request size cost? fio with O_DIRECT, queue depth 1, one file.

Fits T(bs) = alpha + bs / B on the mean time per request (1 / IOPS), the alpha-beta model of the perf-models
module applied to a block device, and prints the half-performance size n_1/2 = alpha * B.

Usage: python3 fio_gap.py [--dir DIR] [--runtime 2] [--out result.json]   (needs the `fio` command)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile

import numpy as np

CASES = [("read", "1M"), ("randread", "1M"), ("randread", "128k"), ("randread", "16k"), ("randread", "4k")]


def parse_size(s: str) -> int:
    return int(s[:-1]) * {"k": 1024, "M": 1024 * 1024}[s[-1]]


def run_fio(path: str, rw: str, bs: str, runtime: int) -> dict:
    cmd = ["fio", "--name=gap", f"--filename={path}", "--size=512M", "--direct=1", "--ioengine=psync", f"--rw={rw}",
           f"--bs={bs}", f"--runtime={runtime}", "--time_based", "--output-format=json"]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    j = json.loads(out[out.index("{"):])["jobs"][0]["read"]
    return {"rw": rw, "bs": bs, "bs_bytes": parse_size(bs), "iops": j["iops"], "bw_bytes_per_s": j["bw_bytes"],
            "lat_mean_us": j["lat_ns"]["mean"] / 1e3}


def fit(rows: list[dict]) -> dict:
    """Least squares of T = alpha + bs/B on the random-read rows, weights 1/T (relative error)."""
    rr = [r for r in rows if r["rw"] == "randread"]
    s = np.array([r["bs_bytes"] for r in rr], dtype=float)
    t = np.array([1.0 / r["iops"] for r in rr])
    w = 1.0 / t
    (alpha, inv_b), *_ = np.linalg.lstsq(np.vstack([np.ones_like(s), s]).T * w[:, None], t * w, rcond=None)
    b = 1.0 / inv_b
    pred = alpha + s / b
    return {"alpha_us": alpha * 1e6, "B_mib_s": b / 2**20, "n_half_kib": alpha * b / 1024,
            "median_rel_error": float(np.median(np.abs(pred - t) / t))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None)
    ap.add_argument("--runtime", type=int, default=2)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if shutil.which("fio") is None:
        raise SystemExit("fio is not installed (apt-get install fio)")
    d = tempfile.mkdtemp(prefix="fio-gap-", dir=args.dir)
    try:
        path = os.path.join(d, "f.dat")
        rows = [run_fio(path, rw, bs, args.runtime) for rw, bs in CASES]
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("%-9s %5s %9s %11s %12s" % ("pattern", "bs", "IOPS", "MiB/s", "mean lat us"))
    for r in rows:
        print("%-9s %5s %9.0f %11.0f %12.1f" % (r["rw"], r["bs"], r["iops"], r["bw_bytes_per_s"] / 2**20, r["lat_mean_us"]))
    f = fit(rows)
    seq, small = rows[0], rows[-1]
    gap = seq["bw_bytes_per_s"] / small["bw_bytes_per_s"]
    print("alpha-beta fit on random reads: alpha = %.0f us, B = %.0f MiB/s, half-performance size = %.0f KiB, median error %.0f %%"
          % (f["alpha_us"], f["B_mib_s"], f["n_half_kib"], 100 * f["median_rel_error"]))
    print("gap: sequential 1M reads give %.0fx the bandwidth of random 4k reads" % gap)
    if args.out:
        with open(args.out, "w") as fh:
            json.dump({"rows": rows, "fit": f, "gap": gap}, fh, indent=1)


if __name__ == "__main__":
    main()
