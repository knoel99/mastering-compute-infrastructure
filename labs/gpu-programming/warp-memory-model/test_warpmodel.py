"""Deterministic tests of the warp model. Exact values are legitimate here: the code is
deterministic and every expected value is derived by hand in the course (chapters 1 and 2)."""
import importlib
import os

import pytest

m = importlib.import_module(os.environ.get("WARPMODEL_MODULE", "warpmodel"))


@pytest.mark.parametrize("stride,sectors", [(1, 4), (2, 8), (4, 16), (8, 32), (32, 32)])
def test_strided_float32_sectors(stride, sectors):
    addrs = [lane * stride * 4 for lane in range(32)]
    assert m.sectors_touched(addrs, 4) == sectors


def test_misaligned_unit_stride_touches_one_more_sector():
    assert m.sectors_touched([4 + lane * 4 for lane in range(32)], 4) == 5


def test_same_address_is_one_sector():
    assert m.sectors_touched([128] * 32, 4) == 1


def test_float64_unit_stride_needs_eight_sectors():
    assert m.sectors_touched([lane * 8 for lane in range(32)], 8) == 8


def test_aos_field_access():
    assert m.sectors_touched([lane * 16 for lane in range(32)], 4) == 16


@pytest.mark.parametrize("stride,degree", [(1, 1), (2, 2), (3, 1), (4, 4), (16, 16), (32, 32), (33, 1)])
def test_bank_conflict_degree_by_stride(stride, degree):
    assert m.bank_conflict_degree([lane * stride for lane in range(32)]) == degree


def test_broadcast_is_not_a_conflict():
    assert m.bank_conflict_degree([5] * 32) == 1


def test_two_words_one_broadcast_one_conflict():
    # lanes 0-15 read word 0, lanes 16-31 read word 32: same bank, two distinct words
    assert m.bank_conflict_degree([0] * 16 + [32] * 16) == 2


def test_divergence_cost():
    alt = [lane % 2 == 0 for lane in range(32)]
    assert m.divergence_cost(alt, 10, 7) == 17
    assert m.divergence_cost([True] * 32, 10, 7) == 10
    assert m.divergence_cost([False] * 32, 10, 7) == 7
    assert m.divergence_cost([True] * 32, 10, 0) == 10
    assert m.divergence_cost(alt, 10, 0) == 10  # an empty else costs nothing


def test_occupancy_full():
    r = m.occupancy(256, 32, 0)
    assert (r["blocks_per_sm"], r["warps_per_sm"], r["occupancy"], r["limiter"]) == (8, 64, 1.0, "threads")


def test_occupancy_register_limited():
    r = m.occupancy(256, 128, 0)  # 65536 / (128 * 256) = 2 blocks
    assert (r["blocks_per_sm"], r["warps_per_sm"], r["limiter"]) == (2, 16, "registers")
    assert r["occupancy"] == 0.25


def test_occupancy_shared_memory_limited():
    r = m.occupancy(128, 32, 48 * 1024)  # 164 KiB / 48 KiB = 3 blocks
    assert (r["blocks_per_sm"], r["warps_per_sm"], r["limiter"]) == (3, 12, "shared memory")


def test_occupancy_block_count_limited_by_tiny_blocks():
    r = m.occupancy(32, 32, 0)  # 1 warp per block, at most 32 blocks per SM = 32 warps
    assert (r["blocks_per_sm"], r["warps_per_sm"], r["limiter"]) == (32, 32, "blocks")
    assert r["occupancy"] == 0.5


def test_threads_not_multiple_of_32_waste_lanes():
    r = m.occupancy(48, 32, 0)  # 2 warps per block, the second one half empty
    assert r["warps_per_sm"] == (2048 // 64) * 2


def test_invalid_arguments():
    with pytest.raises(ValueError):
        m.occupancy(2048, 32, 0)
    with pytest.raises(ValueError):
        m.occupancy(128, 300, 0)
