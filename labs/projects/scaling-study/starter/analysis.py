"""Scaling metrics — TO WRITE (milestone 3). Keep these signatures."""


def summarize(xs):
    """{"n", "median", "p25", "p75"} of a list of numbers."""
    raise NotImplementedError


def speedup(t1, tp):
    raise NotImplementedError


def efficiency(t1, tp, p):
    raise NotImplementedError


def karp_flatt(s, p):
    """Experimentally determined serial fraction e = (1/S - 1/p) / (1 - 1/p), for p > 1."""
    raise NotImplementedError


def ring_allreduce_time(n_bytes, p, alpha, bandwidth):
    """2(p-1)*alpha + 2(p-1)/p * n/B ; zero when p == 1."""
    raise NotImplementedError


def predict_step(compute_1, opt_1, p, mode, n_bytes, alpha, bandwidth):
    """Step time predicted from ONE single-process measurement plus the ring model.
    strong: compute shrinks like 1/p; weak: per-rank compute is constant; the optimiser step
    touches every parameter on every rank, so it does not shrink."""
    raise NotImplementedError


def utilization(flops_per_rank_step, compute_seconds, peak_flops):
    """Achieved FLOP/s of one rank during forward+backward divided by its peak (the MFU of this study)."""
    raise NotImplementedError


def analyze(points, alpha, bandwidth, peak_flops=None):
    """points: [{"mode", "world", "rep", **result of bench.py}] -> one row per (mode, world) with
    reps, step_s (median over runs of the per-run median), step_iqr_s, comm_share, efficiency,
    and for strong scaling speedup and karp_flatt (None at p = 1); predicted_s, pred_rel_error;
    utilization when peak_flops is given. Baselines come from the p = 1 runs of the SAME mode;
    weak-scaling efficiency is t1 / tp."""
    raise NotImplementedError
