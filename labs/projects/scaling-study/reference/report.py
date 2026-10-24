#!/usr/bin/env python3
"""Turn results.json (+ an alpha-beta fit) into report.md: tables, formulas, threats to validity."""
import argparse
import json
import sys
from pathlib import Path
from statistics import median

import analysis

THREATS = """\
- The "processes" share the same four virtual CPUs and communicate over the loopback interface:
  the measured all-reduce is a property of this machine, not of a GPU cluster.
- Few repetitions: the interquartile range is the spread of the per-run medians, with {reps} runs per point.
- The communication time includes the wait for the slowest rank (load imbalance and scheduler noise).
- Warm-up steps are discarded; caches and CPU frequency are not controlled.
- The model is fitted on one message-size sweep and validated on the same machine, not on another.
"""


def fmt(x, nd=3):
    return "-" if x is None else f"{x:.{nd}f}"


def build(results, fitres, peak_gflops=None):
    allpts = results["points"]
    pts = [x for x in allpts if not x.get("decomposed")]  # decomposed runs carry an extra barrier
    rows = analysis.analyze(pts, fitres["alpha_s"], fitres["B_bytes_per_s"],
                            peak_gflops * 1e9 if peak_gflops else None)
    reps = min(r["reps"] for r in rows)
    out = ["# Scaling study report", "",
           f"Machine: {pts[0]['cpu_count']} logical CPUs, torch {pts[0]['torch']}, backend gloo.",
           f"Model: MLP, {pts[0]['n_params']} parameters, gradient message {pts[0]['grad_bytes']} bytes.",
           f"Design: {reps} runs per point, {pts[0]['steps']} measured steps after {pts[0]['warmup']} warm-up steps.", "",
           "## Alpha-beta fit", "",
           f"alpha = {fitres['alpha_s'] * 1e6:.1f} us, B = {fitres['B_bytes_per_s'] / 1e9:.3f} GB/s", "",
           "Ring model: `T(n) = 2(p-1) alpha + 2(p-1)/p * n/B`.", "",
           "## Results", "",
           "| mode | p | step (s) | IQR (s) | speedup | efficiency | Karp-Flatt | comm share | predicted (s) | model error | utilisation |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['mode']} | {r['world']} | {fmt(r['step_s'], 4)} | {fmt(r['step_iqr_s'], 4)} | "
                   f"{fmt(r.get('speedup'), 2)} | {fmt(r['efficiency'], 2)} | {fmt(r.get('karp_flatt'), 3)} | "
                   f"{fmt(r['comm_share'], 2)} | {fmt(r['predicted_s'], 4)} | {fmt(r['pred_rel_error'], 2)} | "
                   f"{fmt(r.get('utilization'), 3)} |")
    dec = [x for x in allpts if x.get("decomposed")]
    if dec:
        out += ["", "## Communication breakdown", "",
                "| mode | p | pack (s) | wait (s) | all-reduce (s) | ring model (s) | all-reduce / model |", "|---|---|---|---|---|---|---|"]
        for key in sorted({(x["mode"], x["world"]) for x in dec}):
            g = [x for x in dec if (x["mode"], x["world"]) == key]
            med = lambda k: median(median(x[k]) for x in g)
            model = analysis.ring_allreduce_time(g[0]["grad_bytes"], key[1], fitres["alpha_s"], fitres["B_bytes_per_s"])
            ratio = med("allreduce_s") / model if model else None
            out.append(f"| {key[0]} | {key[1]} | {fmt(med('pack_s'), 4)} | {fmt(med('wait_s'), 4)} | "
                       f"{fmt(med('allreduce_s'), 4)} | {fmt(model, 4)} | {fmt(ratio, 2)} |")
        out += ["", "The extra barrier of `--decompose` perturbs the step time: use these runs to explain, not to report speedups."]
    out += ["", "## Definitions", "",
            "- speedup `S = t1 / tp` (strong scaling), efficiency `E = t1 / (p tp)` (strong) or `t1 / tp` (weak).",
            "- Karp-Flatt `e = (1/S - 1/p) / (1 - 1/p)`: if e grows with p, the loss is not a fixed serial part.",
            "- utilisation (MFU of this study) = `6 * params * batch_per_rank / compute_time / peak`; "
            "`peak` must be measured (GEMM micro-benchmark), here: "
            + (f"{peak_gflops} GFLOP/s." if peak_gflops else "not provided, column left empty."),
            "", "## Threats to validity", "", THREATS.format(reps=reps)]
    return "\n".join(out), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--fit", required=True, help="JSON with alpha_s and B_bytes_per_s")
    ap.add_argument("--peak-gflops", type=float)
    ap.add_argument("--out", default="report.md")
    a = ap.parse_args()
    text, _ = build(json.load(open(a.results)), json.load(open(a.fit)), a.peak_gflops)
    Path(a.out).write_text(text + "\n")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
