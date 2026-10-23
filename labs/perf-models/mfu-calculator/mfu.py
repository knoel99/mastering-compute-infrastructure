#!/usr/bin/env python3
"""Model FLOPs utilization (MFU), following the definition of the PaLM paper (Appendix B).

    FLOPs per token (training) = 6 N + 12 L H Q T
        6 N        : 2N forward + 4N backward matmul FLOPs of an N-parameter decoder-only model
        12 L H Q T : self-attention term (L layers, H heads, head dimension Q, sequence length T)
    MFU = (tokens/s * FLOPs per token) / (n_gpus * peak FLOP/s per GPU)

Rematerialization (activation checkpointing) is NOT counted: that is what separates MFU from HFU.
"""
import argparse


def flops_per_token(n_params, n_layers=0, n_heads=0, head_dim=0, seq_len=0):
    if n_params <= 0:
        raise ValueError("n_params must be positive")
    attention = 12 * n_layers * n_heads * head_dim * seq_len
    return 6 * n_params + attention


def tokens_per_second(tokens_per_step, step_seconds):
    if step_seconds <= 0 or tokens_per_step <= 0:
        raise ValueError("tokens_per_step and step_seconds must be positive")
    return tokens_per_step / step_seconds


def mfu(tokens_per_s, flops_tok, n_gpus, peak_flops_per_gpu):
    if n_gpus <= 0 or peak_flops_per_gpu <= 0:
        raise ValueError("n_gpus and peak_flops_per_gpu must be positive")
    return tokens_per_s * flops_tok / (n_gpus * peak_flops_per_gpu)


def mfu_from_tflops_per_gpu(achieved_tflops, peak_tflops):
    """MFU when a run reports achieved model TFLOP/s per GPU (as Table 4 of the Llama 3 paper does)."""
    if peak_tflops <= 0:
        raise ValueError("peak_tflops must be positive")
    return achieved_tflops / peak_tflops


def step_time_for_mfu(target_mfu, tokens_per_step, flops_tok, n_gpus, peak_flops_per_gpu):
    """Step time that corresponds to a target MFU (inverse of the formula above)."""
    return tokens_per_step * flops_tok / (target_mfu * n_gpus * peak_flops_per_gpu)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--params", type=float, required=True, help="N, number of parameters (e.g. 7e9)")
    ap.add_argument("--layers", type=int, default=0)
    ap.add_argument("--heads", type=int, default=0)
    ap.add_argument("--head-dim", type=int, default=0)
    ap.add_argument("--seq-len", type=int, default=0)
    ap.add_argument("--tokens-per-step", type=float, required=True)
    ap.add_argument("--step-seconds", type=float, required=True)
    ap.add_argument("--gpus", type=int, required=True)
    ap.add_argument("--peak-tflops", type=float, required=True, help="DENSE peak of the precision you train in, per GPU")
    a = ap.parse_args()
    f = flops_per_token(a.params, a.layers, a.heads, a.head_dim, a.seq_len)
    tps = tokens_per_second(a.tokens_per_step, a.step_seconds)
    m = mfu(tps, f, a.gpus, a.peak_tflops * 1e12)
    print(f"FLOPs/token = {f:.3e}   tokens/s = {tps:,.0f}   MFU = {100 * m:.1f} %")


if __name__ == "__main__":
    main()
