"""Why a distributed run is not bit-identical to a single-process run: floating-point addition is not associative.

    python3 numerics_demo.py          # prints the numbers quoted in chapter 7
    python3 numerics_demo.py --check  # asserts their structural properties (used by verify.sh)

Everything is seeded; the printed values are deterministic on a given PyTorch build and CPU (the exact bits
may differ across platforms, which is itself the point of chapter 7).
"""
import argparse

import torch


def finfo_rows():
    rows = []
    for dt in (torch.float32, torch.float16, torch.bfloat16):
        fi = torch.finfo(dt)
        rows.append({"dtype": str(dt).replace("torch.", ""), "bits": fi.bits, "eps": fi.eps, "max": fi.max, "tiny": fi.tiny})
    return rows


def sum_order_spread(n=1_000_000, orderings=20, seed=0):
    """Sum the same n float32 numbers in `orderings` random orders: the float32 results differ in the last bits."""
    g = torch.Generator().manual_seed(seed)
    x = torch.randn(n, generator=g)
    exact = float(x.double().sum())
    sums = []
    for _ in range(orderings):
        perm = torch.randperm(n, generator=g)
        sums.append(float(x[perm].sum()))
    spread = (max(sums) - min(sums)) / abs(exact)
    return {"n": n, "distinct_sums": len(set(sums)), "relative_spread": spread, "exact_float64": exact,
            "max_error_vs_float64": max(abs(s - exact) for s in sums)}


def rank_order_mismatch(n=1_000_000, seed=0):
    """Sum four per-rank vectors in two association orders (left to right vs pairwise), as two collective algorithms might."""
    g = torch.Generator().manual_seed(seed)
    r = [torch.randn(n, generator=g) for _ in range(4)]
    out = {}
    for dt in (torch.float32, torch.bfloat16):
        a, b, c, d = (v.to(dt) for v in r)
        left = ((a + b) + c) + d
        pair = (a + b) + (c + d)
        out[str(dt).replace("torch.", "")] = float((left != pair).float().mean())
    return out


def bf16_accumulation_stall(steps=10_000, increment=1e-3):
    """Add `increment` `steps` times: fp32 gives steps*increment, a bf16 accumulator stops growing."""
    acc32, acc16 = torch.tensor(0.0), torch.tensor(0.0, dtype=torch.bfloat16)
    inc16 = torch.tensor(increment, dtype=torch.bfloat16)
    for _ in range(steps):
        acc32 += increment
        acc16 += inc16
    return {"expected": steps * increment, "fp32": float(acc32), "bf16": float(acc16)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    torch.set_num_threads(1)
    fi, ss, ro, st = finfo_rows(), sum_order_spread(), rank_order_mismatch(), bf16_accumulation_stall()
    print("dtype      bits  eps         max         smallest normal")
    for r in fi:
        print(f"{r['dtype']:<10} {r['bits']:>4}  {r['eps']:.3e}  {r['max']:.3e}  {r['tiny']:.3e}")
    print(f"sum of {ss['n']} float32 numbers in {20} orders: {ss['distinct_sums']} distinct results, relative spread {ss['relative_spread']:.2e}, "
          f"largest error vs float64 {ss['max_error_vs_float64']:.2e}")
    print("elements that differ between ((a+b)+c)+d and (a+b)+(c+d):", ", ".join(f"{k} {100 * v:.1f} %" for k, v in ro.items()))
    print(f"accumulating 1e-3 ten thousand times: expected {st['expected']:.1f}, float32 {st['fp32']:.3f}, bfloat16 {st['bf16']:.3f}")
    if a.check:
        eps = {r["dtype"]: r["eps"] for r in fi}
        assert eps["bfloat16"] > 50 * eps["float32"] and eps["float16"] < eps["bfloat16"]
        assert ss["distinct_sums"] > 1 and 0 < ss["relative_spread"] < 1e-3, ss  # non-associativity is visible but small
        assert all(0.05 < v < 0.6 for v in ro.values()), ro  # the two association orders disagree on a large share of elements
        assert abs(st["fp32"] - st["expected"]) < 0.05 and st["bf16"] < 0.5 * st["expected"], st  # the bf16 accumulator stalls
        print("OK numerics_demo: properties hold")


if __name__ == "__main__":
    main()
