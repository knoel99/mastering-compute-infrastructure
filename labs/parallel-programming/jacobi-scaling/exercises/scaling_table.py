#!/usr/bin/env python3
"""Speedup, efficiency and Karp-Flatt fraction from a list of (p, time) pairs; optional cost column.

usage: scaling_table.py P:TIME [P:TIME ...]          (the first pair must be p=1)
Uses the tested functions of the lab, ../scaling_math.py (tests in ../test_scaling_math.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scaling_math as analysis  # noqa: E402  (the lab directory must be on the path first)

if __name__ == "__main__":
    pairs = [(int(a), float(b)) for a, b in (x.split(":") for x in sys.argv[1:])]
    t1 = pairs[0][1]
    print(f"{'p':>4} {'T':>8} {'S':>7} {'E':>6} {'e(p)':>7} {'p*T':>8}")
    for p, t in pairs:
        s = analysis.speedup(t1, t)
        e = f"{analysis.karp_flatt(s, p):7.3f}" if p > 1 else f"{'-':>7}"
        print(f"{p:>4} {t:>8.2f} {s:>7.2f} {analysis.efficiency(t1, t, p):>6.2f} {e} {p * t:>8.1f}")
