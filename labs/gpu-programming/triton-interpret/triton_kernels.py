"""Triton kernels: vector add, fused add + ReLU, row-wise softmax, tiled matrix product.

Triton's programming unit is a *program instance* that works on a BLOCK of data (a tile), not a
thread. The same source runs on a GPU or, with TRITON_INTERPRET=1, in an interpreter on the CPU that
executes each program instance sequentially with NumPy (Triton debugging guide). The interpreter checks
logic and indexing; it says nothing about speed.
"""
import torch
import triton
import triton.language as tl


@triton.jit
def add_kernel(x_ptr, y_ptr, out_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
    pid = tl.program_id(axis=0)
    offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements  # the last program may run past the end
    x = tl.load(x_ptr + offsets, mask=mask)
    y = tl.load(y_ptr + offsets, mask=mask)
    tl.store(out_ptr + offsets, x + y, mask=mask)


@triton.jit
def fused_add_relu_kernel(x_ptr, y_ptr, out_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
    """relu(x + y) in ONE pass: 2 reads + 1 write per element instead of 3 + 2 for two kernels."""
    pid = tl.program_id(axis=0)
    offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements
    x = tl.load(x_ptr + offsets, mask=mask)
    y = tl.load(y_ptr + offsets, mask=mask)
    tl.store(out_ptr + offsets, tl.maximum(x + y, 0.0), mask=mask)


@triton.jit
def softmax_kernel(x_ptr, out_ptr, n_cols, row_stride, BLOCK_SIZE: tl.constexpr):
    """One program per row; the whole row lives in registers/SRAM: read once, write once."""
    row = tl.program_id(axis=0)
    cols = tl.arange(0, BLOCK_SIZE)
    mask = cols < n_cols
    x = tl.load(x_ptr + row * row_stride + cols, mask=mask, other=-float("inf"))
    x = x - tl.max(x, axis=0)  # numerical stability: subtract the row maximum
    num = tl.exp(x)
    den = tl.sum(num, axis=0)
    tl.store(out_ptr + row * row_stride + cols, num / den, mask=mask)


@triton.jit
def matmul_kernel(a_ptr, b_ptr, c_ptr, M, N, K,
                  stride_am, stride_ak, stride_bk, stride_bn, stride_cm, stride_cn,
                  BLOCK_M: tl.constexpr, BLOCK_N: tl.constexpr, BLOCK_K: tl.constexpr):
    """C = A @ B, one program per (BLOCK_M x BLOCK_N) tile of C, looping over K in BLOCK_K slices."""
    pid_m = tl.program_id(axis=0)
    pid_n = tl.program_id(axis=1)
    offs_m = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
    offs_n = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)
    offs_k = tl.arange(0, BLOCK_K)
    acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)  # accumulate in float32
    for k0 in range(0, K, BLOCK_K):
        a = tl.load(a_ptr + offs_m[:, None] * stride_am + (k0 + offs_k)[None, :] * stride_ak,
                    mask=(offs_m[:, None] < M) & ((k0 + offs_k)[None, :] < K), other=0.0)
        b = tl.load(b_ptr + (k0 + offs_k)[:, None] * stride_bk + offs_n[None, :] * stride_bn,
                    mask=((k0 + offs_k)[:, None] < K) & (offs_n[None, :] < N), other=0.0)
        acc = tl.dot(a, b, acc)
    tl.store(c_ptr + offs_m[:, None] * stride_cm + offs_n[None, :] * stride_cn, acc,
             mask=(offs_m[:, None] < M) & (offs_n[None, :] < N))


# ------------------------------------------------------------------ host wrappers
def add(x: torch.Tensor, y: torch.Tensor, block: int = 128) -> torch.Tensor:
    out = torch.empty_like(x)
    n = x.numel()
    add_kernel[(triton.cdiv(n, block),)](x, y, out, n, BLOCK_SIZE=block)
    return out


def fused_add_relu(x: torch.Tensor, y: torch.Tensor, block: int = 128) -> torch.Tensor:
    out = torch.empty_like(x)
    n = x.numel()
    fused_add_relu_kernel[(triton.cdiv(n, block),)](x, y, out, n, BLOCK_SIZE=block)
    return out


def softmax(x: torch.Tensor) -> torch.Tensor:
    rows, cols = x.shape
    out = torch.empty_like(x)
    softmax_kernel[(rows,)](x, out, cols, x.stride(0), BLOCK_SIZE=triton.next_power_of_2(cols))
    return out


def matmul(a: torch.Tensor, b: torch.Tensor, bm: int = 16, bn: int = 16, bk: int = 16) -> torch.Tensor:
    M, K = a.shape
    _, N = b.shape
    c = torch.empty((M, N), dtype=torch.float32)
    matmul_kernel[(triton.cdiv(M, bm), triton.cdiv(N, bn))](
        a, b, c, M, N, K, a.stride(0), a.stride(1), b.stride(0), b.stride(1), c.stride(0), c.stride(1),
        BLOCK_M=bm, BLOCK_N=bn, BLOCK_K=bk)
    return c
