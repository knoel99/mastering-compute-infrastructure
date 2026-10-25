#!/usr/bin/env python3
"""Lab 8.1 driver: three experiments and a decision table.

A  latency-bound loader (simulated 6 ms remote read per sample, 5 % of reads 10x slower): workers and prefetch.
B  CPU-bound loader (simulated 8 ms of decode per sample, no I/O wait): where adding workers stops helping.
C  the PyTorch profiler on the same loop: the `enumerate(DataLoader)` row.

Usage: python3 run_lab.py [--batches 40] [--no-in-order] [--out result.json]
(--no-in-order: DataLoader(in_order=False) in parts A and B, to test the in-order-delivery explanation of the model gap.)
"""
from __future__ import annotations

import argparse
import json
import os

import loader_lab as L

BATCH, STEP_S = 8, 0.012  # 8 samples per batch, 12 ms per (simulated) GPU step: the GPU wants 83 batches/s
IO_S, IO_CPU_S, SLOW_FRAC, SLOW_MULT = 0.006, 0.001, 0.05, 10.0
CPU_S = 0.008


def fmt(r: L.Result, pred: float, cores: int) -> str:
    return "%7d %8s %8.1f %7.0f %% %7.0f %% %7.2f   %s" % (
        r.workers, r.prefetch if r.prefetch else "-", r.batches_per_s, 100 * r.stall, 100 * pred, r.worker_cpu_util,
        L.diagnose(r.stall, r.worker_cpu_util, r.workers, cores))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", type=int, default=40)
    ap.add_argument("--no-in-order", action="store_true", help="pass in_order=False to the DataLoader (parts A and B)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    in_order = not args.no_in_order
    cores = os.cpu_count() or 1
    out: dict = {"cores": cores, "batch": BATCH, "step_s": STEP_S}
    head = "%7s %8s %8s %9s %9s %7s   %s" % ("workers", "prefetch", "batch/s", "stall", "model", "cpu/wkr", "diagnosis")

    ds = L.SyntheticDataset(10**6, IO_S, IO_CPU_S, SLOW_FRAC, SLOW_MULT)
    print("A. latency-bound loader (SIMULATED reads), GPU step %.0f ms, %d cores" % (1e3 * STEP_S, cores))
    print(head)
    rows_a = []
    for w in (0, 1, 2, 4, 8):
        r = L.run(ds, w, 2, BATCH, STEP_S, args.batches, in_order=in_order)
        pred = L.predict_stall(w, BATCH, IO_S, IO_CPU_S, STEP_S, cores, SLOW_FRAC, SLOW_MULT)
        print(fmt(r, pred, cores))
        rows_a.append({"workers": w, "prefetch": 2, "stall": r.stall, "pred": pred, "batches_per_s": r.batches_per_s,
                       "cpu_util": r.worker_cpu_util, "diagnosis": L.diagnose(r.stall, r.worker_cpu_util, w, cores)})
    print("   prefetch_factor sweep with 8 workers")
    sweep = []
    for p in (1, 2, 4, 8):
        r = L.run(ds, 8, p, BATCH, STEP_S, args.batches, in_order=in_order)
        pred = L.predict_stall(8, BATCH, IO_S, IO_CPU_S, STEP_S, cores, SLOW_FRAC, SLOW_MULT)
        print(fmt(r, pred, cores))
        sweep.append({"prefetch": p, "stall": r.stall, "batches_per_s": r.batches_per_s})
    out["A"], out["A_prefetch"] = rows_a, sweep

    ds_cpu = L.SyntheticDataset(10**6, 0.0, CPU_S)
    print("\nB. CPU-bound loader (SIMULATED %.0f ms decode per sample, no I/O wait)" % (1e3 * CPU_S))
    print(head + "    cpu/sample")
    rows_b, cpu_per_sample = [], None
    for w in (1, 2, 4, 8):
        r = L.run(ds_cpu, w, 2, BATCH, STEP_S, args.batches, in_order=in_order)
        cps = r.child_cpu_s / (r.batches * BATCH)
        if w == 2:
            cpu_per_sample = cps  # calibrate on the unsaturated run: measured CPU per sample, not the nominal 8 ms
        pred = L.predict_stall(w, BATCH, 0.0, cpu_per_sample or cps, STEP_S, cores)
        print(fmt(r, pred, cores) + "  %5.1f ms" % (1e3 * cps))
        rows_b.append({"workers": w, "stall": r.stall, "pred": pred, "batches_per_s": r.batches_per_s,
                       "cpu_per_sample_s": cps, "cpu_util": r.worker_cpu_util,
                       "diagnosis": L.diagnose(r.stall, r.worker_cpu_util, w, cores)})
    out["B"] = rows_b

    print("\nC. torch.profiler (CPU), 12 batches, GPU step simulated: rows that name the DataLoader")
    prof = {}
    for w in (0, 4):
        rows = L.profile_loader(ds, w, BATCH, STEP_S, 12)
        prof[str(w)] = rows
        for row in rows:
            print("   workers=%d  %-62s calls=%d  total=%7.1f ms  per call=%6.1f ms" % (
                w, row["name"], row["count"], row["cpu_total_ms"], row["cpu_total_ms"] / row["count"]))
    out["C"] = prof
    print("\n   pin_memory: not measured here (no CUDA device); see the course page for what to test on a GPU node.")
    if args.out:
        with open(args.out, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
