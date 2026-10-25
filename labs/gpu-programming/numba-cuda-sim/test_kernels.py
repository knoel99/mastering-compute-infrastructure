"""Correctness of the Numba kernels in the CUDA simulator, against vectorized NumPy.

Simulator launches are slow (one Python thread per CUDA thread), so sizes are tiny. The tests
assert results and counters, never timings."""
import numpy as np
import pytest

import kernels as K

rng = np.random.default_rng(0)


def test_vec_add_handles_a_length_that_is_not_a_multiple_of_the_block():
    a, b = rng.standard_normal(100).astype(np.float32), rng.standard_normal(100).astype(np.float32)
    c = np.zeros(100, np.float32)
    K.launch_1d(K.vec_add, 100, 64, a, b, c)  # 2 blocks = 128 threads for 100 elements
    np.testing.assert_array_equal(c, a + b)


def test_unguarded_kernel_is_caught_by_the_simulator():
    a = np.ones(100, np.float32)
    with pytest.raises(IndexError):
        K.launch_1d(K.vec_add_unguarded, 100, 64, a, a, np.zeros(100, np.float32))


def test_reduction_matches_the_numpy_tree_bit_for_bit():
    x = rng.standard_normal(256).astype(np.float32)
    assert K.reduce_sum(x, 64) == K.numpy_tree_sum(x, 64)  # same additions in the same order
    np.testing.assert_allclose(K.reduce_sum(x, 64), x.astype(np.float64).sum(), rtol=1e-5, atol=1e-5)


def test_reduction_of_integers_is_exact():
    x = np.arange(1, 201, dtype=np.int64)
    assert K.reduce_sum(x, 32) == 20100


def test_missing_barriers_break_the_reduction():
    """Race: without __syncthreads the tree reads shared memory before it is written. The simulator
    schedules threads like the OS does, so the failure is not guaranteed on a given run; we allow 6
    attempts and require at least one wrong result (observed: every attempt fails)."""
    x = rng.standard_normal(256).astype(np.float32)
    good = K.numpy_tree_sum(x, 64)
    wrong = sum(K.reduce_sum(x, 64, sync=False) != good for _ in range(6))
    assert wrong >= 1


def test_scan_matches_cumsum_exactly():
    x = rng.integers(0, 10, 100).astype(np.int64)
    np.testing.assert_array_equal(K.inclusive_scan(x, 32), np.cumsum(x))


def test_tiled_matmul_matches_numpy_and_naive():
    A, B = rng.standard_normal((32, 32)).astype(np.float32), rng.standard_normal((32, 32)).astype(np.float32)
    C_tiled, _ = K.matmul(K.make_matmul_tiled(16), A, B, 16)
    C_naive, _ = K.matmul(K.make_matmul_naive(), A, B, 16)
    np.testing.assert_allclose(C_tiled, A @ B, rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(C_naive, A @ B, rtol=1e-4, atol=1e-4)


def test_tiled_matmul_with_edges_not_multiple_of_the_tile():
    A, B = rng.standard_normal((10, 7)).astype(np.float32), rng.standard_normal((7, 9)).astype(np.float32)
    C, _ = K.matmul(K.make_matmul_tiled(4), A, B, 4)
    np.testing.assert_allclose(C, A @ B, rtol=1e-4, atol=1e-4)


def test_shared_memory_divides_global_loads_by_the_tile_size():
    """Deterministic counters: naive = 2 N^3 loads, tiled = 2 N^3 / T."""
    n, tile = 32, 16
    A, B = rng.standard_normal((n, n)).astype(np.float32), rng.standard_normal((n, n)).astype(np.float32)
    _, naive = K.matmul(K.make_matmul_naive(count=True), A, B, tile)
    _, tiled = K.matmul(K.make_matmul_tiled(tile, count=True), A, B, tile)
    assert naive == 2 * n ** 3
    assert tiled == 2 * n ** 3 // tile
    assert naive // tiled == tile


@pytest.mark.parametrize("pad", [0, 1])
def test_transpose_with_and_without_padding(pad):
    M = rng.standard_normal((12, 20)).astype(np.float32)
    np.testing.assert_array_equal(K.transpose(M, tile=8, pad=pad), M.T)
