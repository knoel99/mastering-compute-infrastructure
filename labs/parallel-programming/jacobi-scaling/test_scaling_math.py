#!/usr/bin/env python3
"""Tests of scaling_math.py. Run with pytest, or directly: python3 test_scaling_math.py"""
import math

import scaling_math as sm


def close(a, b, tol=1e-12):
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def test_summarize():
    s = sm.summarize([1, 2, 3, 4, 100])  # one outlier: the median and quartiles do not move (a mean would give 22)
    assert s == {"n": 5, "median": 3.0, "p25": 2.0, "p75": 4.0}


def test_speedup_efficiency():
    assert close(sm.speedup(1.0, 0.3125), 3.2)
    assert close(sm.efficiency(1.0, 0.3125, 4), 0.8)
    assert close(sm.efficiency(143.2, 143.2, 1), 1.0)


def test_karp_flatt():
    assert close(sm.karp_flatt(3.2, 4), 1 / 12)    # (1/3.2 - 1/4) / (1 - 1/4)
    assert close(sm.karp_flatt(3.0, 4), 1 / 9)     # (1/3 - 1/4) / (1 - 1/4)
    assert close(sm.karp_flatt(2.0, 2), 0.0)       # perfect speedup: no serial fraction
    assert close(sm.karp_flatt(1.0, 8), 1.0)       # no speedup at all: everything is serial


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_") and callable(f)]
    for t in tests:
        t()
    print(f"OK scaling_math: {len(tests)} tests passed (summarize, speedup, efficiency, Karp-Flatt)")
