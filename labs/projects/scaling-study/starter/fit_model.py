"""Ring all-reduce alpha-beta fit with a bootstrap confidence interval — TO WRITE (milestone 2).

Model (seconds, bytes): T(n) = 2(p-1)*alpha + 2(p-1)/p * n/B. It is linear in n: T = a + b*n,
so alpha = a / (2(p-1)) and B = 2(p-1) / (p*b).
`rows` is a list of {"bytes": n, "seconds": t}; keep these signatures, the tests use them.
"""


def to_params(a, b, p):
    """(a, b) of the line T = a + b*n  ->  (alpha in s, B in bytes/s)."""
    raise NotImplementedError


def fit(rows, p, min_bytes=0):
    """Least squares on the RELATIVE error (divide each equation by its measured time), ignoring
    messages smaller than min_bytes. Return {"alpha_s", "B_bytes_per_s", "median_rel_error"}."""
    raise NotImplementedError


def bootstrap_ci(rows, p, min_bytes=0, n_boot=500, seed=0, level=0.95):
    """Percentile bootstrap: resample the (size, time) points with replacement, refit, take the
    percentiles. Return {"alpha_s": [lo, hi], "B_bytes_per_s": [lo, hi]}. Reproducible for a given seed."""
    raise NotImplementedError


def load_rows(path):
    """Read the output of labs/perf-models/allreduce-model/bench_allreduce.py -> (rows, world_size)."""
    raise NotImplementedError
