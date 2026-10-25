"""Scaling metrics: speedup, efficiency, Karp-Flatt, ring model prediction, utilisation."""
from collections import defaultdict
from statistics import median

import numpy as np


def summarize(xs):
    a = np.asarray(xs, dtype=float)
    return {"n": int(a.size), "median": float(np.median(a)),
            "p25": float(np.percentile(a, 25)), "p75": float(np.percentile(a, 75))}


def speedup(t1, tp):
    return t1 / tp


def efficiency(t1, tp, p):
    return t1 / (p * tp)


def karp_flatt(s, p):
    """Experimentally determined serial fraction e = (1/S - 1/p) / (1 - 1/p), p > 1."""
    return (1.0 / s - 1.0 / p) / (1.0 - 1.0 / p)


def ring_allreduce_time(n_bytes, p, alpha, bandwidth):
    if p == 1:
        return 0.0
    return 2 * (p - 1) * alpha + 2 * (p - 1) / p * n_bytes / bandwidth


def predict_step(compute_1, opt_1, p, mode, n_bytes, alpha, bandwidth):
    """Predicted step time from ONE single-process measurement and the fitted ring model.

    strong: the global batch is split, compute shrinks like 1/p; weak: per-rank compute is constant.
    The optimiser step touches every parameter on every rank, so it does not shrink.
    """
    comp = compute_1 / p if mode == "strong" else compute_1
    return comp + opt_1 + ring_allreduce_time(n_bytes, p, alpha, bandwidth)


def utilization(flops_per_rank_step, compute_seconds, peak_flops):
    """Achieved FLOP/s of one rank during forward+backward, over its MEASURED peak: U_c of this study.

    Not the MFU of module 2, which uses the full step time and the datasheet dense peak.
    """
    return flops_per_rank_step / compute_seconds / peak_flops


def analyze(points, alpha, bandwidth, peak_flops=None):
    """points: [{"mode","world","rep", **bench result}] -> one row per (mode, world)."""
    groups = defaultdict(list)
    for pt in points:
        groups[(pt["mode"], pt["world"])].append(pt)
    base = {}
    for (mode, p), pts in groups.items():
        if p == 1:
            base[mode] = {
                "step": median(median(x["step_s"]) for x in pts),
                "compute": median(median(x["compute_s"]) for x in pts),
                "opt": median(median(x["opt_s"]) for x in pts),
            }
    rows = []
    for (mode, p), pts in sorted(groups.items()):
        run_medians = [median(x["step_s"]) for x in pts]
        step = median(run_medians)
        comm = median(median(x["comm_s"]) for x in pts)
        row = {"mode": mode, "world": p, "reps": len(pts), "step_s": step,
               "step_iqr_s": summarize(run_medians)["p75"] - summarize(run_medians)["p25"],
               "comm_share": comm / step, "efficiency": base[mode]["step"] / step if mode == "weak"
               else efficiency(base[mode]["step"], step, p)}
        if mode == "strong":
            row["speedup"] = speedup(base[mode]["step"], step)
            row["karp_flatt"] = karp_flatt(row["speedup"], p) if p > 1 else None
        n_bytes = pts[0]["grad_bytes"]
        row["predicted_s"] = predict_step(base[mode]["compute"], base[mode]["opt"], p, mode, n_bytes, alpha, bandwidth)
        row["pred_rel_error"] = abs(row["predicted_s"] - step) / step
        if peak_flops:
            c = median(median(x["compute_s"]) for x in pts)
            row["utilization"] = utilization(pts[0]["flops_per_step_per_rank"], c, peak_flops)
        rows.append(row)
    return rows
