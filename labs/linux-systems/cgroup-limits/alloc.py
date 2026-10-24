#!/usr/bin/env python3
"""Allocate and touch memory in 10 MiB steps until the kernel stops us. Prints progress."""
import sys

chunks = []
for i in range(1, 31):
    block = bytearray(10 * 1024 * 1024)
    block[::4096] = b"x" * len(block[::4096])  # bytearray(n) already zero-fills, so every page is touched at allocation; this write is belt and braces
    chunks.append(block)
    print(f"allocated {i * 10} MiB", flush=True)
print("no limit hit", file=sys.stderr)
