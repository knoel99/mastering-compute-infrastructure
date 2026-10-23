#!/usr/bin/env python3
"""Measure memory bandwidth (STREAM copy/add) and GEMM throughput, then compare them to a roofline.

The roofline here is built from the machine's own measurements, not from a datasheet:
    attainable(I) = min(P_gemm, I * B_add)
with I the arithmetic intensity (FLOP per byte of ideal memory traffic).
"""
import argparse
import json
import os
import platform
import time

import numpy as np


def timeit(fn, repeat=7, warmup=2):
    """Return (min, median) wall time in seconds. The minimum is the least noisy estimate of capability."""
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return min(times), float(np.median(times))


def stream(array_mib, repeat):
    """STREAM 'copy' (a = b: 1 read + 1 write) and 'add' (a = b + c: 2 reads + 1 write), float64."""
    n = array_mib * 2**20 // 8
    a = np.zeros(n)
    b = np.random.default_rng(0).random(n)
    c = np.random.default_rng(1).random(n)
    t_copy, _ = timeit(lambda: np.copyto(a, b), repeat)
    t_add, _ = timeit(lambda: np.add(b, c, out=a), repeat)
    return {
        "array_mib": array_mib,
        "copy_gbs": 16 * n / t_copy / 1e9,  # 8 B read + 8 B written per element
        "add_gbs": 24 * n / t_add / 1e9,    # 16 B read + 8 B written per element
    }


def gemm(sizes, repeat):
    """Square float32 GEMM. Ideal traffic: read A and B once, write C once = 3 n^2 elements."""
    out = []
    rng = np.random.default_rng(2)
    for n in sizes:
        a = rng.random((n, n), dtype=np.float32)
        b = rng.random((n, n), dtype=np.float32)
        t, _ = timeit(lambda: a @ b, repeat)
        flops = 2 * n**3
        out.append({"n": n, "gflops": flops / t / 1e9, "intensity_flop_per_byte": flops / (3 * n * n * 4)})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--array-mib", type=int, default=128, help="size of each STREAM array (must exceed the last-level cache)")
    ap.add_argument("--sizes", type=int, nargs="+", default=[64, 128, 256, 512, 1024, 2048])
    ap.add_argument("--repeat", type=int, default=7)
    ap.add_argument("--quick", action="store_true", help="small sizes, for tests")
    ap.add_argument("--out", default="results.json")
    args = ap.parse_args()
    if args.quick:
        args.array_mib, args.sizes, args.repeat = 64, [64, 256, 512], 3

    s = stream(args.array_mib, args.repeat)
    g = gemm(args.sizes, args.repeat)
    peak = max(r["gflops"] for r in g)
    ridge = peak / s["add_gbs"]  # FLOP/byte where the memory roof meets the compute roof
    for r in g:
        r["roofline_gflops"] = min(peak, r["intensity_flop_per_byte"] * s["add_gbs"])
        r["measured_over_roofline"] = r["gflops"] / r["roofline_gflops"]
    result = {
        "machine": {"cpu_count": os.cpu_count(), "platform": platform.platform(), "numpy": np.__version__,
                    "omp_num_threads": os.environ.get("OMP_NUM_THREADS")},
        "stream": s,
        "gemm": g,
        "peak_gemm_gflops": peak,
        "ridge_flop_per_byte": ridge,
    }
    with open(args.out, "w") as f:
        json.dump(result, f, indent=1)
    print(f"stream_add_gbs={s['add_gbs']:.1f} copy_gbs={s['copy_gbs']:.1f} "
          f"peak_gemm_gflops={peak:.1f} ridge_flop_per_byte={ridge:.2f}")
    for r in g:
        print(f"  n={r['n']:5d} I={r['intensity_flop_per_byte']:7.1f} FLOP/B  "
              f"measured={r['gflops']:8.1f} GFLOP/s  roofline={r['roofline_gflops']:8.1f}  ratio={r['measured_over_roofline']:.2f}")


if __name__ == "__main__":
    main()
