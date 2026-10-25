#!/usr/bin/env python3
"""Profile one forward+backward step of the tiny transformer on the CPU with torch.profiler and
export a Chrome trace.

    python3 profile_cpu.py --out trace.json [--attention explicit|sdpa] [--summary summary.json]

Open trace.json in https://ui.perfetto.dev or chrome://tracing, or read it with trace_report.py.
"""
import argparse
import json

import torch
from torch.profiler import ProfilerActivity, profile, record_function

import tiny_model as tm


def run(attention: str, out: str, summary: str | None, threads: int = 2) -> dict:
    torch.set_num_threads(threads)  # keep the shared sandbox usable
    model, x = tm.build(attention)
    for _ in range(2):  # warm-up: first calls allocate and initialize
        tm.step(model, x)
    with profile(activities=[ProfilerActivity.CPU], record_shapes=True, with_flops=True) as prof:
        with record_function("train_step"):
            tm.step(model, x)
    prof.export_chrome_trace(out)
    rows = {}
    for e in prof.key_averages():
        rows[e.key] = {"calls": e.count, "self_cpu_us": e.self_cpu_time_total, "flops": e.flops}
    matmul = sum(rows[n]["flops"] for n in ("aten::mm", "aten::addmm", "aten::bmm") if n in rows)
    result = {"attention": attention, "ops": rows, "total_flops": sum(r["flops"] for r in rows.values()),
              "matmul_flops": matmul, "forward_matmul_flops": tm.forward_matmul_flops()}
    if summary:
        with open(summary, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--attention", choices=["explicit", "sdpa"], default="explicit")
    ap.add_argument("--summary")
    a = ap.parse_args()
    r = run(a.attention, a.out, a.summary)
    top = sorted(r["ops"].items(), key=lambda kv: -kv[1]["self_cpu_us"])[:8]
    print(f"{'operator':<34}{'calls':>6}{'self CPU us':>13}{'MFLOP':>10}")
    for name, v in top:
        print(f"{name:<34}{v['calls']:>6}{v['self_cpu_us']:>13.0f}{v['flops'] / 1e6:>10.1f}")
    print(f"profiler FLOPs of mm+addmm+bmm: {r['matmul_flops']:.0f} = {r['matmul_flops'] / r['forward_matmul_flops']:.3f} x analytic forward FLOPs")
