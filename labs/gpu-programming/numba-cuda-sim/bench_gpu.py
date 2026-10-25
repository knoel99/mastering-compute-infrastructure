#!/usr/bin/env python3
"""GPU branch of the lab. NEVER EXECUTED in the course sandbox (no GPU): it is only byte-compiled
(python -m py_compile). Run it on a machine with an NVIDIA GPU:

    NUMBA_ENABLE_CUDASIM=0 python3 bench_gpu.py

It times the tiled and naive Numba kernels against torch.matmul (vendor library) and the
reduction against torch.sum, with CUDA events and a warm-up, and prints achieved GFLOP/s so that
you can place the points on the roofline of the GPU (module perf-models).
"""
import os

os.environ.setdefault("NUMBA_ENABLE_CUDASIM", "0")

import numpy as np  # noqa: E402
import torch  # noqa: E402
from numba import cuda  # noqa: E402

import kernels as K  # noqa: E402


def time_ms(fn, reps: int = 20) -> float:
    fn()  # warm-up (includes JIT compilation)
    cuda.synchronize()
    start, end = cuda.event(), cuda.event()
    start.record()
    for _ in range(reps):
        fn()
    end.record()
    end.synchronize()
    return cuda.event_elapsed_time(start, end) / reps


def main() -> None:
    if not cuda.is_available():
        raise SystemExit("no CUDA device: run this on a GPU machine (the simulator cannot time anything)")
    n, tile = 2048, 16
    A = np.random.default_rng(0).standard_normal((n, n)).astype(np.float32)
    B = np.random.default_rng(1).standard_normal((n, n)).astype(np.float32)
    dA, dB, dC = cuda.to_device(A), cuda.to_device(B), cuda.device_array((n, n), np.float32)
    loads = cuda.to_device(np.zeros(1, np.int64))
    grid, block = (n // tile, n // tile), (tile, tile)
    naive, tiled = K.make_matmul_naive(), K.make_matmul_tiled(tile)
    tA, tB = torch.from_numpy(A).cuda(), torch.from_numpy(B).cuda()
    flops = 2.0 * n ** 3
    for name, fn in [
        ("numba naive", lambda: naive[grid, block](dA, dB, dC, loads)),
        ("numba tiled", lambda: tiled[grid, block](dA, dB, dC, loads)),
        ("torch.matmul fp32", lambda: torch.matmul(tA, tB)),
    ]:
        ms = time_ms(fn)
        print(f"{name:<20}{ms:9.3f} ms {flops / (ms * 1e6):10.1f} GFLOP/s")


if __name__ == "__main__":
    main()
