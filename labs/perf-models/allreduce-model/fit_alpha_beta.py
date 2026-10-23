#!/usr/bin/env python3
"""Fit the ring all-reduce model T(n) = 2(p-1)*alpha + 2(p-1)/p * n/B to measured times.

The model is linear in the message size n:  T = a + b*n  with
    a = 2(p-1) * alpha        ->  alpha = a / (2(p-1))
    b = 2(p-1) / (p * B)      ->  B     = 2(p-1) / (p * b)
"""
import argparse
import json
import sys

import numpy as np


def fit(rows, p, min_bytes):
    n = np.array([r["bytes"] for r in rows], dtype=float)
    t = np.array([r["seconds_median_max_rank"] for r in rows], dtype=float)
    sel = n >= min_bytes
    # weighted least squares in relative error: divide each equation by t so that small sizes are not ignored
    A = np.vstack([np.ones(sel.sum()), n[sel]]).T / t[sel][:, None]
    y = np.ones(sel.sum())
    (a, b), *_ = np.linalg.lstsq(A, y, rcond=None)
    alpha = a / (2 * (p - 1))
    B = 2 * (p - 1) / (p * b)
    pred = a + b * n
    rel_err = np.abs(pred - t) / t
    return {"alpha_s": float(alpha), "B_bytes_per_s": float(B), "a": float(a), "b": float(b),
            "median_rel_error_fit_range": float(np.median(rel_err[sel])),
            "max_rel_error_fit_range": float(np.max(rel_err[sel])),
            "predictions": [{"bytes": int(x), "measured_s": float(m), "predicted_s": float(q)} for x, m, q in zip(n, t, pred)]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("measurements")
    ap.add_argument("--min-bytes", type=int, default=64 * 1024, help="ignore sizes below this when fitting")
    ap.add_argument("--out", default="fit.json")
    args = ap.parse_args()
    d = json.load(open(args.measurements))
    p = d["world_size"]
    res = fit(d["rows"], p, args.min_bytes)
    res["world_size"] = p
    json.dump(res, open(args.out, "w"), indent=1)
    print(f"p={p}  alpha={res['alpha_s']*1e6:.1f} us  B={res['B_bytes_per_s']/1e9:.2f} GB/s  "
          f"median relative error on fit range = {res['median_rel_error_fit_range']*100:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
