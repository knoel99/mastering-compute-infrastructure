"""CUDA kernels written with Numba (the same source runs on a GPU and in the CPU simulator).

Run in the simulator:  NUMBA_ENABLE_CUDASIM=1 (must be set BEFORE numba is imported; conftest.py
and demo.py do it). On a machine with an NVIDIA GPU set NUMBA_ENABLE_CUDASIM=0 and the same
kernels compile for the device: see bench_gpu.py (never executed in the course sandbox).

Each kernel is built by a factory so that tile sizes are compile-time constants, as shared-memory
array shapes must be. Index convention: x is the fastest-varying thread index, so consecutive
threads of a warp touch consecutive columns (coalesced accesses on a real GPU).
"""
from __future__ import annotations

import numpy as np
from numba import cuda, float32, int64


# ------------------------------------------------------------------ chapter 1: the grid
@cuda.jit
def vec_add(a, b, c):
    i = cuda.grid(1)  # blockIdx.x * blockDim.x + threadIdx.x
    if i < c.shape[0]:  # guard: the grid is rounded up to whole blocks
        c[i] = a[i] + b[i]


@cuda.jit
def vec_add_unguarded(a, b, c):
    """Classic bug: no bounds check. A real GPU may corrupt memory silently; the simulator raises."""
    i = cuda.grid(1)
    c[i] = a[i] + b[i]


def launch_1d(kernel, n: int, tpb: int, *args):
    kernel[(n + tpb - 1) // tpb, tpb](*args)


# ------------------------------------------------------------------ chapter 3: reduction
def make_block_sum(tpb: int, dtype=float32, sync: bool = True):
    """Tree reduction of one block in shared memory; one partial sum per block.

    With sync=False the two barriers are removed: a data race (classic error, chapter 3)."""

    @cuda.jit
    def block_sum(x, partial):
        sm = cuda.shared.array(tpb, dtype)
        t = cuda.threadIdx.x
        i = cuda.grid(1)
        sm[t] = x[i] if i < x.shape[0] else 0
        if sync:
            cuda.syncthreads()
        s = tpb // 2
        while s > 0:
            if t < s:
                sm[t] += sm[t + s]
            if sync:
                cuda.syncthreads()
            s //= 2
        if t == 0:
            partial[cuda.blockIdx.x] = sm[0]

    return block_sum


def reduce_sum(x: np.ndarray, tpb: int = 64, sync: bool = True) -> np.floating:
    """Two-stage sum: one kernel for the per-block partials, the host adds the partials."""
    blocks = (x.shape[0] + tpb - 1) // tpb
    partial = np.zeros(blocks, dtype=x.dtype)
    make_block_sum(tpb, float32 if x.dtype == np.float32 else int64, sync)[blocks, tpb](x, partial)
    return partial.sum(dtype=x.dtype)


def numpy_tree_sum(x: np.ndarray, tpb: int) -> np.floating:
    """Same additions, same order, in vectorized numpy: the oracle for bitwise comparisons."""
    blocks = (x.shape[0] + tpb - 1) // tpb
    padded = np.zeros(blocks * tpb, dtype=x.dtype)
    padded[: x.shape[0]] = x
    v = padded.reshape(blocks, tpb)
    s = tpb // 2
    while s > 0:
        v = v[:, :s] + v[:, s : 2 * s]
        s //= 2
    return v[:, 0].sum(dtype=x.dtype)


# ------------------------------------------------------------------ chapter 3: scan
def make_block_scan(tpb: int):
    """Inclusive scan (Hillis-Steele) of one block; also writes each block's total."""

    @cuda.jit
    def block_scan(x, out, block_totals):
        sm = cuda.shared.array(tpb, int64)
        t = cuda.threadIdx.x
        i = cuda.grid(1)
        sm[t] = x[i] if i < x.shape[0] else 0
        cuda.syncthreads()
        offset = 1
        while offset < tpb:
            v = int64(0)
            if t >= offset:
                v = sm[t - offset]
            cuda.syncthreads()  # everyone has READ before anyone WRITES
            sm[t] += v
            cuda.syncthreads()  # everyone has WRITTEN before the next round reads
            offset *= 2
        if i < x.shape[0]:
            out[i] = sm[t]
        if t == tpb - 1:
            block_totals[cuda.blockIdx.x] = sm[t]

    return block_scan


@cuda.jit
def add_block_offsets(out, offsets, tpb):
    i = cuda.grid(1)
    if i < out.shape[0]:
        out[i] += offsets[i // tpb]


def inclusive_scan(x: np.ndarray, tpb: int = 32) -> np.ndarray:
    """Scan in three steps: per-block scans, scan of the block totals on the host, add offsets."""
    blocks = (x.shape[0] + tpb - 1) // tpb
    out = np.zeros_like(x)
    totals = np.zeros(blocks, dtype=x.dtype)
    make_block_scan(tpb)[blocks, tpb](x, out, totals)
    offsets = np.concatenate(([0], np.cumsum(totals)[:-1])).astype(x.dtype)
    add_block_offsets[blocks, tpb](out, offsets, tpb)
    return out


# ------------------------------------------------------------------ chapter 3: matrix product
def make_matmul_naive(count: bool = False):
    """One thread per output element; every operand is read from global memory each time.
    With count=True each global load increments loads[0] (an atomic counter)."""

    @cuda.jit
    def matmul_naive(A, B, C, loads):
        col, row = cuda.grid(2)
        if row < C.shape[0] and col < C.shape[1]:
            acc = float32(0)
            for k in range(A.shape[1]):
                acc += A[row, k] * B[k, col]
                if count:
                    cuda.atomic.add(loads, 0, 2)
            C[row, col] = acc

    return matmul_naive


def make_matmul_tiled(tile: int, count: bool = False):
    """Tiled product: each block stages a tile of A and a tile of B in shared memory, so every
    value read from global memory is used `tile` times."""

    @cuda.jit
    def matmul_tiled(A, B, C, loads):
        sA = cuda.shared.array((tile, tile), float32)
        sB = cuda.shared.array((tile, tile), float32)
        tx = cuda.threadIdx.x
        ty = cuda.threadIdx.y
        col, row = cuda.grid(2)
        M = A.shape[0]
        K = A.shape[1]
        N = B.shape[1]
        acc = float32(0)
        for t0 in range(0, K, tile):
            a_col = t0 + tx
            b_row = t0 + ty
            if row < M and a_col < K:
                sA[ty, tx] = A[row, a_col]
                if count:
                    cuda.atomic.add(loads, 0, 1)
            else:
                sA[ty, tx] = 0.0
            if b_row < K and col < N:
                sB[ty, tx] = B[b_row, col]
                if count:
                    cuda.atomic.add(loads, 0, 1)
            else:
                sB[ty, tx] = 0.0
            cuda.syncthreads()  # the tile is complete before anyone uses it
            for k in range(tile):
                acc += sA[ty, k] * sB[k, tx]
            cuda.syncthreads()  # everyone is done with the tile before it is overwritten
        if row < M and col < N:
            C[row, col] = acc

    return matmul_tiled


def matmul(kernel, A: np.ndarray, B: np.ndarray, tile: int, loads: np.ndarray | None = None):
    M, N = A.shape[0], B.shape[1]
    C = np.zeros((M, N), dtype=np.float32)
    loads = np.zeros(1, dtype=np.int64) if loads is None else loads
    grid = ((N + tile - 1) // tile, (M + tile - 1) // tile)
    kernel[grid, (tile, tile)](A, B, C, loads)
    return C, int(loads[0])


# ------------------------------------------------------------------ chapter 2: transpose
def make_transpose(tile: int, pad: int = 0):
    """Tiled transpose. pad=1 is the padding trick that removes bank conflicts on a real GPU
    (invisible in the simulator, which has no banks: see ../warp-memory-model)."""

    @cuda.jit
    def transpose(src, dst):
        sm = cuda.shared.array((tile, tile + pad), float32)
        tx = cuda.threadIdx.x
        ty = cuda.threadIdx.y
        x, y = cuda.grid(2)
        if y < src.shape[0] and x < src.shape[1]:
            sm[ty, tx] = src[y, x]
        cuda.syncthreads()
        x2 = cuda.blockIdx.y * tile + tx
        y2 = cuda.blockIdx.x * tile + ty
        if y2 < dst.shape[0] and x2 < dst.shape[1]:
            dst[y2, x2] = sm[tx, ty]

    return transpose


def transpose(src: np.ndarray, tile: int = 8, pad: int = 0) -> np.ndarray:
    dst = np.zeros((src.shape[1], src.shape[0]), dtype=src.dtype)
    grid = ((src.shape[1] + tile - 1) // tile, (src.shape[0] + tile - 1) // tile)
    make_transpose(tile, pad)[grid, (tile, tile)](src, dst)
    return dst
