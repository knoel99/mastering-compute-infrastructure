#!/usr/bin/env python3
"""Read a Chrome-trace JSON written by torch.profiler (Kineto) and name the bottleneck.

    python3 trace_report.py trace.json

Two analyses, whichever events the trace contains:
  * CPU operators (category "cpu_op"): self time per operator (inclusive duration minus direct children);
  * GPU activity (categories "kernel", "gpu_memcpy", "gpu_memset"): utilization of the device, idle gaps,
    duration of the kernels, share of copies, then a VERDICT: launch-bound, transfer-bound, GPU-bound or mixed.

The thresholds of the verdict are this course's heuristics (chapter 7), not NVIDIA rules.
Category names are those of Kineto (pytorch/kineto, libkineto/include/ActivityType.h).
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict

CPU_CATS = {"cpu_op", "user_annotation"}
GPU_CATS = {"kernel", "gpu_memcpy", "gpu_memset"}
EPS = 1e-6

# heuristics (microseconds / fractions)
SHORT_KERNEL_US = 50.0
LOW_UTILIZATION = 0.6
HIGH_UTILIZATION = 0.85
COPY_SHARE = 0.5


def load_events(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [e for e in data["traceEvents"] if e.get("ph") == "X" and "dur" in e and "ts" in e]


def self_times(events: list[dict]) -> dict[str, dict]:
    """Per operator name: number of calls and total self time (us). Nesting is per (pid, tid)."""
    threads: dict[tuple, list[dict]] = defaultdict(list)
    for e in events:
        if e.get("cat") in CPU_CATS:
            threads[(e["pid"], e["tid"])].append(e)
    out: dict[str, dict] = defaultdict(lambda: {"calls": 0, "self_us": 0.0})

    def close(entry: list) -> None:
        _, name, dur, children = entry
        out[name]["calls"] += 1
        out[name]["self_us"] += dur - children

    for evs in threads.values():
        evs.sort(key=lambda e: (e["ts"], -e["dur"]))
        stack: list[list] = []  # [end, name, dur, direct children duration]
        for e in evs:
            while stack and e["ts"] >= stack[-1][0] - EPS:
                close(stack.pop())
            if stack:
                stack[-1][3] += e["dur"]
            stack.append([e["ts"] + e["dur"], e["name"], e["dur"], 0.0])
        while stack:
            close(stack.pop())
    return dict(out)


def merged_busy(intervals: list[tuple[float, float]]) -> float:
    """Total length of the union of intervals."""
    total, cur_s, cur_e = 0.0, None, None
    for s, e in sorted(intervals):
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                total += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        total += cur_e - cur_s
    return total


def gpu_summary(events: list[dict]) -> dict | None:
    gpu = [e for e in events if e.get("cat") in GPU_CATS]
    if not gpu:
        return None
    kernels = [e for e in gpu if e["cat"] == "kernel"]
    copies = [e for e in gpu if e["cat"] in ("gpu_memcpy", "gpu_memset")]
    span = max(e["ts"] + e["dur"] for e in gpu) - min(e["ts"] for e in gpu)
    busy = merged_busy([(e["ts"], e["ts"] + e["dur"]) for e in gpu])
    kernel_us = sum(e["dur"] for e in kernels)
    copy_us = sum(e["dur"] for e in copies)
    s = {"span_us": span, "busy_us": busy, "utilization": busy / span, "kernels": len(kernels),
         "kernel_us": kernel_us, "copy_us": copy_us,
         "copy_share": copy_us / (kernel_us + copy_us) if kernel_us + copy_us else 0.0,
         "median_kernel_us": statistics.median(e["dur"] for e in kernels) if kernels else 0.0}
    s["verdict"] = verdict(s)
    return s


def verdict(s: dict) -> str:
    if s["copy_share"] > COPY_SHARE:
        return "TRANSFER-BOUND: copies take most of the device time (pinned memory? bigger chunks? overlap?)"
    if s["utilization"] < LOW_UTILIZATION and s["median_kernel_us"] < SHORT_KERNEL_US:
        return "LAUNCH-BOUND: many short kernels and an idle device (fuse, CUDA graphs, torch.compile, bigger batch)"
    if s["utilization"] >= HIGH_UTILIZATION:
        return "GPU-BOUND: the device is busy; split compute- vs memory-bound with Nsight Compute"
    return "MIXED: the device idles but kernels are not tiny; look for CPU stalls (data loading, synchronization)"


def main(path: str) -> None:
    ev = load_events(path)
    st = self_times(ev)
    print(f"{len(ev)} complete events in {path}")
    if st:
        print(f"{'operator':<34}{'calls':>6}{'self us':>11}{'share':>8}")
        total = sum(v["self_us"] for v in st.values())
        for name, v in sorted(st.items(), key=lambda kv: -kv[1]["self_us"])[:8]:
            print(f"{name:<34}{v['calls']:>6}{v['self_us']:>11.1f}{100 * v['self_us'] / total:>7.1f}%")
    g = gpu_summary(ev)
    if g is None:
        print("no GPU activity in this trace (CPU-only profile)")
        return
    print(f"GPU: span {g['span_us']:.0f} us, busy {g['busy_us']:.0f} us, utilization {100 * g['utilization']:.1f} %")
    print(f"GPU: {g['kernels']} kernels, median {g['median_kernel_us']:.1f} us, copies {100 * g['copy_share']:.1f} % of device time")
    print("VERDICT:", g["verdict"])


if __name__ == "__main__":
    main(sys.argv[1])
