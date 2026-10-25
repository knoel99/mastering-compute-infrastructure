#!/usr/bin/env python3
"""Floating-point addition is commutative but NOT associative."""
a, b, c = 0.1, 0.2, 0.3
print("(0.1 + 0.2) + 0.3 =", repr((a + b) + c))
print("0.1 + (0.2 + 0.3) =", repr(a + (b + c)))
print("equal:", (a + b) + c == a + (b + c))
big = 1e16
print("(1e16 + 1) - 1e16 =", repr((big + 1.0) - big), "   (1e16 - 1e16) + 1 =", repr((big - big) + 1.0))
