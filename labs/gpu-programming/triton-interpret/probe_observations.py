#!/usr/bin/env python3
"""Reproduce the three version-specific OBSERVATIONS quoted in chapter 5 of the course.

These are observations of one Triton version (3.8.0 on Linux without a GPU), not guarantees, so
verify.sh does not assert them. Run it to see what YOUR version does:

    python3 probe_observations.py

1. bfloat16 in the interpreter: the documentation says it is unsupported. Does it fail loudly?
2. @triton.autotune in the interpreter: does it run?
3. A missing mask in add_kernel (run in a child process because the interpreter may kill it).
"""
import os
import subprocess
import sys

os.environ["TRITON_INTERPRET"] = "1"

import torch  # noqa: E402
import triton  # noqa: E402
import triton.language as tl  # noqa: E402

import triton_kernels as T  # noqa: E402


def probe_bfloat16() -> None:
    x = torch.ones(8).to(torch.bfloat16)
    try:
        out = T.add(x, x)
        print(f"bfloat16: no exception; 1 + 1 gave {out[0].item():.4g} (expected 2) -> correct: {bool(torch.equal(out, x + x))}")
    except Exception as e:  # noqa: BLE001 - we report whatever the interpreter raises
        print("bfloat16: exception ->", repr(e)[:120])


def probe_autotune() -> None:
    @triton.autotune(configs=[triton.Config({"BLOCK_SIZE": 64}), triton.Config({"BLOCK_SIZE": 128})], key=["n_elements"])
    @triton.jit
    def k(x_ptr, y_ptr, out_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
        offsets = tl.program_id(axis=0) * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
        mask = offsets < n_elements
        tl.store(out_ptr + offsets, tl.load(x_ptr + offsets, mask=mask) + tl.load(y_ptr + offsets, mask=mask), mask=mask)

    x, y, out = torch.randn(100), torch.randn(100), torch.empty(100)
    try:
        k[lambda meta: (triton.cdiv(100, meta["BLOCK_SIZE"]),)](x, y, out, 100)
        print("autotune: ran without error")
    except Exception as e:  # noqa: BLE001
        print("autotune: exception ->", repr(e)[:120])


_NO_MASK_CHILD = """
import os
os.environ["TRITON_INTERPRET"] = "1"
import torch, triton, triton.language as tl

@triton.jit
def add_no_mask(x_ptr, y_ptr, out_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
    offsets = tl.program_id(axis=0) * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    tl.store(out_ptr + offsets, tl.load(x_ptr + offsets) + tl.load(y_ptr + offsets))

x, y, out = torch.randn(1000), torch.randn(1000), torch.empty(1000)
add_no_mask[(triton.cdiv(1000, 128),)](x, y, out, 1000, BLOCK_SIZE=128)
print("child: finished without error")
"""


def probe_missing_mask() -> None:
    r = subprocess.run([sys.executable, "-X", "faulthandler", "-c", _NO_MASK_CHILD], capture_output=True, text=True, timeout=120, cwd=os.path.dirname(os.path.abspath(__file__)))
    verdict = "exit status %d" % r.returncode
    for word in ("Segmentation fault", "Aborted"):
        if word in r.stderr:
            verdict += f" ({word})"
    print("missing mask: child process ->", verdict)


if __name__ == "__main__":
    print("triton", triton.__version__, "(interpreter mode)")
    probe_bfloat16()
    probe_autotune()
    probe_missing_mask()
