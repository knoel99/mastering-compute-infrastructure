"""Scaling metrics of chapter 8: summary of repeated runs, speedup, efficiency, Karp-Flatt serial fraction.

Self-contained on purpose: this lab does not depend on the files of any project. Project 2 (scaling-study)
asks you to write these functions again in its own code; test_scaling_math.py holds their tests.
"""
import numpy as np


def summarize(xs):
    """Number of runs, median and quartiles: robust to one slow outlier, unlike the mean."""
    a = np.asarray(xs, dtype=float)
    return {"n": int(a.size), "median": float(np.median(a)),
            "p25": float(np.percentile(a, 25)), "p75": float(np.percentile(a, 75))}


def speedup(t1, tp):
    """S = T1 / Tp."""
    return t1 / tp


def efficiency(t1, tp, p):
    """E = S / p = T1 / (p Tp)."""
    return t1 / (p * tp)


def karp_flatt(s, p):
    """Experimentally determined serial fraction e = (1/S - 1/p) / (1 - 1/p), p > 1."""
    return (1.0 / s - 1.0 / p) / (1.0 - 1.0 / p)
