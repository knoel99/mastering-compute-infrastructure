#!/usr/bin/env python3
"""Prints the simulator results quoted in chapter 3 of the course.

    python3 demo.py loads      # global-memory loads: naive vs tiled matrix product
    python3 demo.py errors     # the two classic errors, caught or not by the simulator
    python3 demo.py atomics    # does the simulator reorder atomic additions between launches? (observation)
"""
import os
import sys

os.environ.setdefault("NUMBA_ENABLE_CUDASIM", "1")

import numpy as np  # noqa: E402

import kernels as K  # noqa: E402
from numba import cuda  # noqa: E402


def loads() -> None:
    n = 32
    rng = np.random.default_rng(0)
    A, B = rng.standard_normal((n, n)).astype(np.float32), rng.standard_normal((n, n)).astype(np.float32)
    print(f"N = {n}: product of two {n}x{n} float32 matrices, global loads counted by an atomic counter")
    for tile in (8, 16):
        _, tiled = K.matmul(K.make_matmul_tiled(tile, count=True), A, B, tile)
        print(f"  tile {tile:>2}: {tiled:>6} loads")
    _, naive = K.matmul(K.make_matmul_naive(count=True), A, B, 16)
    print(f"  naive  : {naive:>6} loads  (= 2 N^3 = {2 * n ** 3})")


def errors() -> None:
    a = np.ones(100, np.float32)
    try:
        K.launch_1d(K.vec_add_unguarded, 100, 64, a, a, np.zeros(100, np.float32))
        print("unguarded kernel: no error")
    except IndexError as e:
        print("unguarded kernel: IndexError ->", str(e)[:70])
    x = np.random.default_rng(0).standard_normal(256).astype(np.float32)
    good = K.numpy_tree_sum(x, 64)
    wrong = sum(K.reduce_sum(x, 64, sync=False) != good for _ in range(5))
    print(f"reduction without barriers: {wrong} wrong results out of 5 launches")


@cuda.jit
def atomic_sum(x, out):
    i = cuda.grid(1)
    if i < x.shape[0]:
        cuda.atomic.add(out, 0, x[i])


def atomics() -> None:
    """30 launches of a float32 sum done with cuda.atomic.add: how many distinct results? On a real GPU
    the order of the atomic additions may change from launch to launch; in the simulator we observed one
    result (an observation about this version, not a guarantee, so no test asserts it)."""
    x = (np.random.default_rng(0).standard_normal(256) * np.logspace(0, 6, 256)).astype(np.float32)
    results = set()
    for _ in range(30):
        out = np.zeros(1, np.float32)
        atomic_sum[4, 64](x, out)
        results.add(float(out[0]))
    print(f"atomic float32 sum: {len(results)} distinct result(s) over 30 launches")


if __name__ == "__main__":
    {"loads": loads, "errors": errors, "atomics": atomics}[sys.argv[1] if len(sys.argv) > 1 else "loads"]()
