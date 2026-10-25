#!/usr/bin/env python3
"""GPU branch of the lab. NEVER EXECUTED in the course sandbox (no GPU): only byte-compiled.

    python3 bench_gpu.py        # on a machine with an NVIDIA GPU, TRITON_INTERPRET unset

Compares the Triton fused softmax with torch.softmax and with the five-operation version, and shows
@triton.autotune choosing BLOCK_SIZE. In the interpreter, autotune cannot run (Triton 3.8.0 raises
"0 active drivers"), which is why it lives here and not in the tested kernels.
"""
import torch
import triton
import triton.language as tl

import traffic


# BLOCK_SIZE must cover a whole row (>= n_cols = 2048 below): a smaller block would silently skip the
# end of each row, return a wrong softmax and look "faster". Only the number of warps is tuned among
# valid sizes; the output is checked against torch.softmax in main().
@triton.autotune(configs=[triton.Config({"BLOCK_SIZE": b}, num_warps=w) for b in (2048, 4096) for w in (4, 8)],
                 key=["n_cols"])
@triton.jit
def softmax_autotuned(x_ptr, out_ptr, n_cols, row_stride, BLOCK_SIZE: tl.constexpr):
    row = tl.program_id(0)
    cols = tl.arange(0, BLOCK_SIZE)
    mask = cols < n_cols
    x = tl.load(x_ptr + row * row_stride + cols, mask=mask, other=-float("inf"))
    x = x - tl.max(x, axis=0)
    num = tl.exp(x)
    tl.store(out_ptr + row * row_stride + cols, num / tl.sum(num, axis=0), mask=mask)


def main() -> None:
    if not torch.cuda.is_available():
        raise SystemExit("no CUDA device: this benchmark needs a GPU")
    m, n = 4096, 2048
    x = torch.randn(m, n, device="cuda")
    out = torch.empty_like(x)
    fused = lambda: softmax_autotuned[(m,)](x, out, n, x.stride(0))
    unfused = lambda: traffic.unfused_softmax(x, traffic.Ledger())
    native = lambda: torch.softmax(x, dim=1)
    r = traffic.report(m, n)
    fused()
    torch.testing.assert_close(out, torch.softmax(x, dim=1), rtol=1e-4, atol=1e-6)  # correctness before speed
    for name, fn in [("triton fused", fused), ("torch.softmax", native), ("5 separate ops", unfused)]:
        ms = triton.testing.do_bench(fn)
        print(f"{name:<16}{ms:8.3f} ms")
    print(f"idealized traffic ratio unfused/fused = {r['ratio']:.2f}")


if __name__ == "__main__":
    main()
