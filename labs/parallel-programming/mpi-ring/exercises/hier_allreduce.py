#!/usr/bin/env python3
"""Flat ring vs two-level all-reduce, alpha-beta model with ILLUSTRATIVE parameters (not measurements).

usage: hier_allreduce.py N_BYTES NODES RANKS_PER_NODE
Parameters below are example values: intra-node alpha 2 us, 300 GB/s; inter-node alpha 10 us, 25 GB/s.
  flat ring over all p = nodes*g ranks, limited by the slowest link:
      T_flat = 2 (p-1) alpha_o + 2 (p-1)/p * n / B_o
  two levels (every rank has its own inter-node link and works on its own n/g slice):
      T_hier = [reduce-scatter in the node] + [ring all-reduce of n/g bytes among the nodes] + [all-gather in the node]
             = (g-1) alpha_i + (g-1)/g n/B_i  +  2 (m-1) alpha_o + 2 (m-1)/m (n/g)/B_o  +  (g-1) alpha_i + (g-1)/g n/B_i
"""
import sys

ALPHA_I, B_I = 2e-6, 300e9
ALPHA_O, B_O = 10e-6, 25e9


def t_flat(n, m, g):
    p = m * g
    return 2 * (p - 1) * ALPHA_O + 2 * (p - 1) / p * n / B_O


def t_hier(n, m, g):
    intra = (g - 1) * ALPHA_I + (g - 1) / g * n / B_I
    inter = 2 * (m - 1) * ALPHA_O + 2 * (m - 1) / m * (n / g) / B_O
    return 2 * intra + inter


if __name__ == "__main__":
    n, m, g = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    f, h = t_flat(n, m, g), t_hier(n, m, g)
    print(f"n={n / 1e6:g} MB, {m} nodes x {g} ranks: flat ring {f * 1e3:.3f} ms, two-level {h * 1e3:.3f} ms, ratio {f / h:.2f}")
