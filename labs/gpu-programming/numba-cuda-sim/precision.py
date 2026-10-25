#!/usr/bin/env python3
"""Numerical-precision experiments that need no GPU (chapter 6 of the course).

Everything is deterministic (fixed seeds) except nothing: no timing, no threads.

    python3 precision.py            # prints the tables quoted in the course
"""
from __future__ import annotations

import numpy as np
import torch

# (exponent bits, explicitly stored mantissa bits) of each format.
FORMATS = {
    "float32": (torch.float32, 8, 23),
    "float16": (torch.float16, 5, 10),
    "bfloat16": (torch.bfloat16, 8, 7),
    "fp8 e4m3": (torch.float8_e4m3fn, 4, 3),
    "fp8 e5m2": (torch.float8_e5m2, 5, 2),
}


def format_table() -> list[dict]:
    rows = []
    for name, (dt, e, m) in FORMATS.items():
        fi = torch.finfo(dt)
        rows.append({"format": name, "exp_bits": e, "mant_bits": m, "eps": float(fi.eps),
                     "max": float(fi.max), "smallest_normal": float(fi.smallest_normal)})
    return rows


def round_mantissa(x: np.ndarray, bits: int) -> np.ndarray:
    """Round float32 values to `bits` explicit mantissa bits (round to nearest even), keeping the
    float32 exponent range. bits=7 reproduces bfloat16 exactly (tested); bits=10 EMULATES the input
    rounding of TF32 (not the output of a tensor core: rounding details of the hardware may differ)."""
    u = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32).astype(np.uint64)
    shift = 23 - bits
    lsb = (u >> shift) & 1
    u = (u + (1 << (shift - 1)) - 1 + lsb) >> shift << shift
    return u.astype(np.uint32).view(np.float32)


def fp16_sequential_sum_of_ones(n: int) -> float:
    """Accumulate n ones in float16, one after the other (what a float16 accumulator does)."""
    return float(np.cumsum(np.ones(n, dtype=np.float16), dtype=np.float16)[-1])


def underflow_fractions(scale: float, n: int = 20000, seed: int = 0) -> tuple[float, float, float]:
    """Gradients with log-uniform magnitudes in [2^-30, 2^0]. Returns the share that is 0 once cast to
    float16 (a) unscaled, (b) after multiplying by `scale`, and (c) the share that overflows to inf
    after scaling (float16 maximum: 65504)."""
    rng = np.random.default_rng(seed)
    g = (2.0 ** rng.uniform(-30, 0, n)).astype(np.float32)
    plain = np.mean(g.astype(np.float16) == 0)
    with np.errstate(over="ignore"):  # overflow to inf is exactly what we count
        scaled16 = (g * np.float32(scale)).astype(np.float16)
    return float(plain), float(np.mean(scaled16 == 0)), float(np.mean(np.isinf(scaled16)))


def order_dependence(n: int = 4096, trials: int = 20, seed: int = 0) -> dict:
    """The same 4096 float32 numbers summed in `trials` different orders (as an unordered atomicAdd
    would): how many distinct results, and how far from the float64 sum?"""
    rng = np.random.default_rng(seed)
    x = (rng.standard_normal(n) * np.logspace(0, 3, n)).astype(np.float32)
    exact = float(x.astype(np.float64).sum())
    results = set()
    for _ in range(trials):
        results.add(float(np.cumsum(rng.permutation(x), dtype=np.float32)[-1]))
    vals = np.array(sorted(results))
    return {"distinct": len(results), "spread": float(vals.max() - vals.min()), "exact_f64": exact,
            "max_abs_err": float(np.abs(vals - exact).max())}


def tree_vs_sequential(n: int = 1 << 14, seed: int = 1) -> dict:
    """float32 error of a sequential sum versus a halving tree, against the float64 sum."""
    rng = np.random.default_rng(seed)
    x = (1.0 + 0.1 * rng.standard_normal(n)).astype(np.float32)
    exact = float(x.astype(np.float64).sum())
    seq = float(np.cumsum(x, dtype=np.float32)[-1])
    v = x.copy()
    while v.shape[0] > 1:
        h = v.shape[0] // 2
        v = v[:h] + v[h : 2 * h]
    return {"exact": exact, "sequential_err": abs(seq - exact), "tree_err": abs(float(v[0]) - exact)}


def matmul_input_rounding_error(n: int = 256, seed: int = 2) -> dict:
    """Relative Frobenius error of C = round(A) @ round(B) (accumulated in float64) against the exact
    product of the float32 inputs: the cost of low-precision INPUTS with exact accumulation."""
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n)).astype(np.float32)
    B = rng.standard_normal((n, n)).astype(np.float32)
    ref = A.astype(np.float64) @ B.astype(np.float64)
    out = {}
    for name, bits in [("tf32 (emulated, 10 bits)", 10), ("bfloat16 (7 bits)", 7), ("2 mantissa bits (e5m2 precision)", 2)]:
        Ar, Br = round_mantissa(A, bits), round_mantissa(B, bits)
        C = Ar.astype(np.float64) @ Br.astype(np.float64)
        out[name] = float(np.linalg.norm(C - ref) / np.linalg.norm(ref))
    return out


def main() -> None:
    print("== formats (torch.finfo) ==")
    print(f"{'format':<10}{'exp':>4}{'mant':>5}{'eps':>12}{'max':>12}{'smallest normal':>18}")
    for r in format_table():
        print(f"{r['format']:<10}{r['exp_bits']:>4}{r['mant_bits']:>5}{r['eps']:>12.3g}{r['max']:>12.4g}{r['smallest_normal']:>18.3g}")
    print()
    print("== float16 accumulator: sum of n ones ==")
    for n in (1000, 2048, 4096, 100000):
        print(f"n={n:>6}  sum={fp16_sequential_sum_of_ones(n):.0f}")
    print()
    print("== loss scaling: gradients with magnitudes in [2^-30, 2^0] cast to float16 ==")
    print(f"{'scale':<8}{'zeros':>9}{'inf':>9}")
    for e in (0, 8, 16, 24):
        _, zeros, infs = underflow_fractions(2.0 ** e)
        print(f"2^{e:<6}{100 * zeros:>8.1f}%{100 * infs:>8.1f}%")
    print()
    o = order_dependence()
    print("== summation order (float32, 4096 values, 20 random orders) ==")
    print(f"distinct results: {o['distinct']}, spread {o['spread']:.4g}, worst error vs float64 {o['max_abs_err']:.4g} (sum = {o['exact_f64']:.2f})")
    t = tree_vs_sequential()
    print(f"sequential float32 error {t['sequential_err']:.4g} versus tree {t['tree_err']:.4g} (sum = {t['exact']:.1f})")
    print()
    print("== relative error of C = round(A) @ round(B), n = 256, exact accumulation ==")
    for k, v in matmul_input_rounding_error().items():
        print(f"{k:<36}{v:.2e}")


if __name__ == "__main__":
    main()
