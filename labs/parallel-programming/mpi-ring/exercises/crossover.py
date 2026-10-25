#!/usr/bin/env python3
"""Message size above which the ring all-reduce beats recursive doubling (alpha-beta model).

usage: crossover.py P ALPHA_SECONDS BANDWIDTH_BYTES_PER_SECOND
    T_ring   = 2 (p-1) alpha + 2 (p-1)/p * n / B
    T_recdbl = log2(p) * (alpha + n / B)           (p a power of two)
Setting T_ring = T_recdbl gives
    n* = alpha * B * (2 (p-1) - log2 p) / (log2 p - 2 (p-1)/p)         valid for p >= 4.
"""
import math
import sys


def t_ring(p, n, alpha, bw):
    return 2 * (p - 1) * alpha + 2 * (p - 1) / p * n / bw


def t_recdbl(p, n, alpha, bw):
    return math.log2(p) * (alpha + n / bw)


def crossover(p, alpha, bw):
    lg = math.log2(p)
    return alpha * bw * (2 * (p - 1) - lg) / (lg - 2 * (p - 1) / p)


if __name__ == "__main__":
    p, alpha, bw = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    n = crossover(p, alpha, bw)
    print(f"p={p} alpha={alpha * 1e6:g} us B={bw / 1e9:g} GB/s: n* = {n:.0f} bytes ({n / alpha / bw:.2f} alpha*B)")
    for k in (0.5, 1.0, 2.0):
        m = k * n
        print(f"  n = {k:g} n*: ring {t_ring(p, m, alpha, bw) * 1e6:9.2f} us   recursive doubling {t_recdbl(p, m, alpha, bw) * 1e6:9.2f} us")
