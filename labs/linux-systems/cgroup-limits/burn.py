#!/usr/bin/env python3
"""Busy loop for N wall-clock seconds; print the share of one CPU actually obtained."""
import sys
import time

wall = float(sys.argv[1])
t0, c0 = time.monotonic(), time.process_time()
while time.monotonic() - t0 < wall:
    pass
print(f"{(time.process_time() - c0) / (time.monotonic() - t0):.3f}")
