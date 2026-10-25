#!/usr/bin/env python3
"""Count the memory traffic of the softmax written as separate PyTorch operations, and compare it
with one fused kernel that reads each element once and writes it once.

The ledger counts the elements of the tensors that REALLY go in and out of each operation as the code
executes them; nothing is assumed. (The Triton fused-softmax tutorial gives the same totals in a comment:
read 5MN + 2M, write 3MN + 2M.) This is an idealized DRAM-traffic count: it ignores caches, which can
absorb some re-reads of small tensors on a real GPU.

    python3 traffic.py [M N]
"""
from __future__ import annotations

import sys

import torch


class Ledger:
    """Runs operations and counts the elements read (inputs) and written (outputs)."""

    def __init__(self) -> None:
        self.reads = 0
        self.writes = 0
        self.ops = 0

    def op(self, fn, *inputs: torch.Tensor) -> torch.Tensor:
        out = fn(*inputs)
        self.reads += sum(t.numel() for t in inputs)
        self.writes += out.numel()
        self.ops += 1
        return out


def unfused_softmax(x: torch.Tensor, led: Ledger) -> torch.Tensor:
    m = led.op(lambda t: t.max(dim=1).values, x)                    # read MN, write M
    z = led.op(lambda t, mm: t - mm[:, None], x, m)                 # read MN + M, write MN
    e = led.op(torch.exp, z)                                        # read MN, write MN
    s = led.op(lambda t: t.sum(dim=1), e)                           # read MN, write M
    return led.op(lambda t, ss: t / ss[:, None], e, s)              # read MN + M, write MN


def fused_traffic(m: int, n: int) -> tuple[int, int]:
    """One kernel: read the matrix once, write the result once."""
    return m * n, m * n


def report(m: int, n: int, bytes_per_elem: int = 4) -> dict:
    x = torch.randn(m, n)
    led = Ledger()
    y = unfused_softmax(x, led)
    assert torch.allclose(y, torch.softmax(x, dim=1), rtol=1e-5, atol=1e-7)
    fr, fw = fused_traffic(m, n)
    unfused_bytes = (led.reads + led.writes) * bytes_per_elem
    fused_bytes = (fr + fw) * bytes_per_elem
    return {"M": m, "N": n, "ops": led.ops, "reads": led.reads, "writes": led.writes,
            "unfused_bytes": unfused_bytes, "fused_bytes": fused_bytes, "ratio": unfused_bytes / fused_bytes}


if __name__ == "__main__":
    M, N = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) == 3 else (4096, 2048)
    r = report(M, N)
    print(f"softmax of a {M} x {N} float32 matrix as {r['ops']} separate operations:")
    print(f"  reads  {r['reads']:>12} elements  (5MN + 2M = {5 * M * N + 2 * M})")
    print(f"  writes {r['writes']:>12} elements  (3MN + 2M = {3 * M * N + 2 * M})")
    print(f"  traffic {r['unfused_bytes'] / 2**20:.1f} MiB unfused versus {r['fused_bytes'] / 2**20:.1f} MiB fused -> x{r['ratio']:.3f}")
