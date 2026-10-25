#!/usr/bin/env python3
"""Write three SYNTHETIC GPU-style Chrome traces (hand-made, NOT captured from a GPU).

The sandbox has no GPU, so there is no real Kineto GPU trace to read. These files imitate the
structure of one (CPU lane with launch events, GPU lane with kernels and copies, Kineto category
names) with durations chosen to illustrate three bottlenecks. Their purpose is to exercise the
reading skill and trace_report.py; they carry no performance information about any real GPU.

    python3 make_fixture.py OUTDIR
"""
import json
import os
import random
import sys

CPU, GPU = 1000, 0  # pid of the host process, pid of the device lane (as in Kineto: device id)


def ev(cat, name, pid, tid, ts, dur):
    return {"ph": "X", "cat": cat, "name": name, "pid": pid, "tid": tid, "ts": round(ts, 3), "dur": round(dur, 3)}


def launch_bound(rng):
    """200 tiny element-wise kernels; the CPU needs 18 us per launch, each kernel lasts about 5 us."""
    events, t_cpu, t_gpu = [], 0.0, 0.0
    for i in range(200):
        events.append(ev("cpu_op", "aten::mul", CPU, 1, t_cpu, 7.0))
        events.append(ev("cuda_runtime", "cudaLaunchKernel", CPU, 1, t_cpu + 2.0, 5.0))
        k = 4.0 + rng.random() * 2.0
        t_gpu = max(t_gpu, t_cpu + 7.0)  # a kernel cannot start before its launch returns
        events.append(ev("kernel", "elementwise_kernel", GPU, 7, t_gpu, k))
        t_gpu += k
        t_cpu += 18.0
    return events


def gpu_bound(rng):
    """12 big GEMM-like kernels queued ahead by the CPU: the device never waits."""
    events, t_gpu = [], 0.0
    for i in range(12):
        events.append(ev("cpu_op", "aten::mm", CPU, 1, i * 20.0, 12.0))
        events.append(ev("cuda_runtime", "cudaLaunchKernel", CPU, 1, i * 20.0 + 3.0, 6.0))
        k = 850.0 + rng.random() * 100.0
        events.append(ev("kernel", "gemm_kernel", GPU, 7, t_gpu, k))
        t_gpu += k + 2.0
    events.append(ev("cuda_runtime", "cudaStreamSynchronize", CPU, 1, 240.0, t_gpu - 240.0))
    return events


def transfer_bound(rng):
    """Each step copies 4 ms of data from pageable memory, then computes for 300 us."""
    events, t = [], 0.0
    for i in range(10):
        events.append(ev("cpu_op", "aten::to", CPU, 1, t, 20.0))
        events.append(ev("gpu_memcpy", "Memcpy HtoD (Pageable -> Device)", GPU, 7, t + 20.0, 4000.0))
        t += 4020.0
        events.append(ev("kernel", "gemm_kernel", GPU, 7, t, 300.0 + rng.random() * 20.0))
        t += 330.0
    return events


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    for name, fn, seed in [("launch_bound", launch_bound, 1), ("gpu_bound", gpu_bound, 2), ("transfer_bound", transfer_bound, 3)]:
        trace = {"traceEvents": fn(random.Random(seed)), "displayTimeUnit": "ms",
                 "otherData": {"synthetic": True, "note": "hand-made by make_fixture.py, NOT captured from a GPU"}}
        with open(os.path.join(outdir, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(trace, f, indent=0, sort_keys=True)
            f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
