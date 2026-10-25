#!/usr/bin/env python3
"""Fit alpha and B on a micro-benchmark, then compare the alpha-beta predictions with the all-reduce rows.

usage: python3 model_vs_measure.py bench.json
Model (module perf-models, chapter 6):
    T_ring   = 2 (p-1) alpha + 2 (p-1)/p * n / B
    T_recdbl = log2(p) * (alpha + n / B)
alpha and B are fitted twice, by least squares on the RELATIVE error of alpha + n/B:
    "pp"  on the ping-pong rows (two ranks, the rest idle),
    "xch" on the exchange rows (all ranks swap with a neighbour at the same time, like a ring step).
Prints, for each all-reduce row, measured time, both predictions and measured/predicted.
"""
import json
import sys

import numpy as np


def fit_alpha_beta(ns, ts):
    """Least squares on relative error: minimise sum(((alpha + n/B) - t) / t)^2."""
    ns, ts = np.asarray(ns, float), np.asarray(ts, float)
    A = np.column_stack([1.0 / ts, ns / ts])
    (alpha, inv_b), *_ = np.linalg.lstsq(A, np.ones_like(ts), rcond=None)
    return float(alpha), float(1.0 / inv_b)


def predict(kind, p, n, alpha, B):
    if kind == "ring":
        return 2 * (p - 1) * alpha + 2 * (p - 1) / p * n / B
    if kind == "recdbl":
        return np.log2(p) * (alpha + n / B)
    raise ValueError(kind)


def main(path):
    d = json.load(open(path))
    p = d["p"]
    fits = {}
    for tag, kind in (("pp", "pingpong"), ("xch", "exchange")):
        pts = [(x["bytes"], x["seconds"]) for x in d["rows"] if x["kind"] == kind]
        fits[tag] = fit_alpha_beta([n for n, _ in pts], [t for _, t in pts])
        print(f"p={p} label={d['label']} fit on {kind}: alpha = {fits[tag][0] * 1e6:.1f} us, B = {fits[tag][1] / 1e9:.2f} GB/s")
    py = {x["bytes"]: x["seconds"] for x in d["rows"] if x["kind"] == "pyloop"}
    print(f"{'bytes':>9} {'kind':>7} {'measured_us':>12} {'model_pp_us':>12} {'meas/pp':>8} {'model_xch_us':>13} {'meas/xch':>9} {'xch+python_us':>14} {'meas/(xch+py)':>14}")
    ratios = {"pp": [], "xch": [], "xch+py": []}
    for x in d["rows"]:
        if x["kind"] in ("ring", "recdbl"):
            m = {t: predict(x["kind"], p, x["bytes"], *fits[t]) for t in fits}
            for t in m:
                ratios[t].append(x["seconds"] / m[t])
            extra = py[x["bytes"]] if x["kind"] == "ring" else 0.0  # the Python loop cost, ring only
            m3 = m["xch"] + extra
            if x["kind"] == "ring":
                ratios["xch+py"].append(x["seconds"] / m3)
            print(f"{x['bytes']:>9} {x['kind']:>7} {x['seconds'] * 1e6:>12.1f} {m['pp'] * 1e6:>12.1f} {x['seconds'] / m['pp']:>8.2f} "
                  f"{m['xch'] * 1e6:>13.1f} {x['seconds'] / m['xch']:>9.2f} {m3 * 1e6:>14.1f} {x['seconds'] / m3:>14.2f}")
        elif x["kind"] == "mpi":
            print(f"{x['bytes']:>9} {'mpi':>7} {x['seconds'] * 1e6:>12.1f}")
    for t in ratios:
        print(f"median measured/model with the {t} fit: {np.median(ratios[t]):.2f}" + (" (ring rows only)" if t == "xch+py" else ""))
    assert all(a > 0 and b > 0 for a, b in fits.values())
    return fits, ratios


if __name__ == "__main__":
    main(sys.argv[1])
