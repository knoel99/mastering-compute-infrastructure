#!/usr/bin/env python3
"""Back-of-the-envelope sizing for a dense-transformer training run, as asked in a design interview.

Every function states its assumption in its docstring: in an interview, the assumption you say aloud matters as much
as the number. FLOPs per token = 6 x parameters (forward + backward, dense model, attention ignored).
"""
import argparse
import math
import sys

SECONDS_PER_DAY = 86400.0


def train_flops(params, tokens):
    """Total training FLOPs: 6 x P x D."""
    return 6.0 * params * tokens


def training_days(params, tokens, gpus, peak_flops, mfu):
    """Days to train: FLOPs / (GPUs x peak x MFU x 86400). MFU = achieved over peak FLOP/s (see the perf-models module)."""
    return train_flops(params, tokens) / (gpus * peak_flops * mfu) / SECONDS_PER_DAY


def gpus_for_deadline(params, tokens, days, peak_flops, mfu, gpus_per_node=8):
    """Smallest number of GPUs, rounded UP to whole nodes, that finishes within `days`."""
    exact = train_flops(params, tokens) / (days * SECONDS_PER_DAY * peak_flops * mfu)
    return int(math.ceil(exact / gpus_per_node) * gpus_per_node)


def nodes(gpus, gpus_per_node=8):
    return int(math.ceil(gpus / gpus_per_node))


def checkpoint_bytes(params, bytes_per_param):
    """Checkpoint size. bytes_per_param is an ASSUMPTION you must state, e.g. 14 = bf16 weights (2) + fp32 master
    weights (4) + two fp32 Adam moments (8); gradients are not saved."""
    return params * bytes_per_param


def checkpoint_seconds(size_bytes, write_gb_per_s):
    """Time to write a checkpoint at an aggregate write bandwidth in GB/s (10^9 bytes)."""
    return size_bytes / (write_gb_per_s * 1e9)


def job_mtbf_hours(gpus, gpu_failure_rate_per_hour):
    """Mean time between failures of a job that uses all its GPUs: 1 / (gpus x rate)."""
    return 1.0 / (gpus * gpu_failure_rate_per_hour)


def young_daly_goodput(ckpt_min, mtbf_min, restart_min):
    """(period T* in minutes, useful-work fraction) at the Young-Daly period T* = sqrt(2 C M)."""
    t = math.sqrt(2.0 * ckpt_min * mtbf_min)
    return t, 1.0 - (ckpt_min / t + (t / 2.0 + restart_min) / mtbf_min)


def summary(params, tokens, gpus, peak_flops, mfu, bytes_per_param, write_gb_per_s, gpu_failure_rate, restart_min):
    days = training_days(params, tokens, gpus, peak_flops, mfu)
    size = checkpoint_bytes(params, bytes_per_param)
    ckpt_min = checkpoint_seconds(size, write_gb_per_s) / 60.0
    mtbf_h = job_mtbf_hours(gpus, gpu_failure_rate)
    t_star, g = young_daly_goodput(ckpt_min, mtbf_h * 60.0, restart_min)
    return {"flops": train_flops(params, tokens), "nodes": nodes(gpus), "days_ideal": days,
            "checkpoint_gb": size / 1e9, "checkpoint_s": ckpt_min * 60.0, "job_mtbf_h": mtbf_h,
            "ckpt_period_min": t_star, "goodput": g, "days_with_failures": days / g}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", type=float, required=True)
    ap.add_argument("--tokens", type=float, required=True)
    ap.add_argument("--gpus", type=int, required=True)
    ap.add_argument("--peak-tflops", type=float, required=True)
    ap.add_argument("--mfu", type=float, required=True)
    ap.add_argument("--bytes-per-param", type=float, required=True, help="state your assumption")
    ap.add_argument("--write-gb-s", type=float, required=True)
    ap.add_argument("--gpu-failure-rate", type=float, required=True, help="failures per GPU-hour (an assumption)")
    ap.add_argument("--restart-min", type=float, default=15.0)
    a = ap.parse_args()
    s = summary(a.params, a.tokens, a.gpus, a.peak_tflops * 1e12, a.mfu, a.bytes_per_param, a.write_gb_s,
                a.gpu_failure_rate, a.restart_min)
    print(f"training compute         : {s['flops']:.2e} FLOP")
    print(f"nodes of 8 GPUs          : {s['nodes']}")
    print(f"ideal duration           : {s['days_ideal']:.1f} days")
    print(f"checkpoint               : {s['checkpoint_gb']:.0f} GB, {s['checkpoint_s']:.0f} s to write")
    print(f"job MTBF                 : {s['job_mtbf_h']:.1f} h")
    print(f"Young-Daly period        : {s['ckpt_period_min']:.0f} min, goodput {s['goodput']:.3f}")
    print(f"duration with failures   : {s['days_with_failures']:.1f} days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
