"""Ring all-reduce alpha-beta fit with a bootstrap confidence interval.

Model (seconds, bytes): T(n) = 2(p-1)*alpha + 2(p-1)/p * n/B, linear in n: T = a + b*n.
"""
import json

import numpy as np


def _solve(n, t):
    """Least squares on relative error: each equation divided by its measured time."""
    A = np.vstack([np.ones(len(n)), n]).T / t[:, None]
    (a, b), *_ = np.linalg.lstsq(A, np.ones(len(n)), rcond=None)
    return a, b


def to_params(a, b, p):
    return a / (2 * (p - 1)), 2 * (p - 1) / (p * b)  # alpha (s), B (bytes/s)


def fit(rows, p, min_bytes=0):
    n = np.array([r["bytes"] for r in rows], dtype=float)
    t = np.array([r["seconds"] for r in rows], dtype=float)
    sel = n >= min_bytes
    a, b = _solve(n[sel], t[sel])
    alpha, bw = to_params(a, b, p)
    rel = np.abs(a + b * n[sel] - t[sel]) / t[sel]
    return {"alpha_s": float(alpha), "B_bytes_per_s": float(bw), "median_rel_error": float(np.median(rel))}


def bootstrap_ci(rows, p, min_bytes=0, n_boot=500, seed=0, level=0.95):
    """Percentile CI by resampling the (size, time) points with replacement."""
    rng = np.random.default_rng(seed)
    n = np.array([r["bytes"] for r in rows], dtype=float)
    t = np.array([r["seconds"] for r in rows], dtype=float)
    sel = np.flatnonzero(n >= min_bytes)
    al, bw = [], []
    for _ in range(n_boot):
        idx = rng.choice(sel, size=len(sel), replace=True)
        if len(set(n[idx])) < 2:
            continue
        a, b = _solve(n[idx], t[idx])
        if b <= 0:
            continue
        alpha, bwid = to_params(a, b, p)
        al.append(alpha)
        bw.append(bwid)
    q = [(1 - level) / 2 * 100, (1 + level) / 2 * 100]
    return {"alpha_s": [float(x) for x in np.percentile(al, q)],
            "B_bytes_per_s": [float(x) for x in np.percentile(bw, q)]}


def load_rows(path):
    """Rows of ../perf-models allreduce-model bench output -> [{bytes, seconds}]."""
    d = json.load(open(path))
    return [{"bytes": r["bytes"], "seconds": r["seconds_median_max_rank"]} for r in d["rows"]], d["world_size"]
