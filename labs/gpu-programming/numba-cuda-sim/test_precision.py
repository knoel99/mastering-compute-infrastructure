"""Tests of the precision experiments: exact where the code is deterministic and the expected
value is derived by hand in the course; tolerant otherwise."""
import numpy as np
import torch

import precision as P


def test_format_table_matches_the_bit_layouts():
    for r in P.format_table():
        assert r["eps"] == 2.0 ** -r["mant_bits"], r["format"]
    t = {r["format"]: r for r in P.format_table()}
    assert t["float16"]["max"] == 65504.0
    assert t["fp8 e4m3"]["max"] == 448.0
    assert t["fp8 e5m2"]["max"] == 57344.0
    assert t["bfloat16"]["smallest_normal"] == t["float32"]["smallest_normal"]  # same exponent range


def test_rounding_to_7_bits_is_bfloat16():
    x = np.random.default_rng(3).standard_normal(10000).astype(np.float32)
    ref = torch.from_numpy(x).to(torch.bfloat16).to(torch.float32).numpy()
    np.testing.assert_array_equal(P.round_mantissa(x, 7), ref)


def test_rounding_is_idempotent_and_within_half_ulp():
    x = np.random.default_rng(4).standard_normal(10000).astype(np.float32)
    r = P.round_mantissa(x, 10)
    np.testing.assert_array_equal(P.round_mantissa(r, 10), r)
    assert np.max(np.abs(r - x) / np.abs(x)) <= 2.0 ** -11 * (1 + 1e-6)


def test_float16_accumulator_stalls_at_2048():
    assert P.fp16_sequential_sum_of_ones(1000) == 1000
    assert P.fp16_sequential_sum_of_ones(2048) == 2048
    assert P.fp16_sequential_sum_of_ones(100000) == 2048


def test_loss_scaling_removes_underflow_until_it_overflows():
    plain, z0, i0 = P.underflow_fractions(1.0)
    assert 0.10 < plain < 0.25 and z0 == plain and i0 == 0.0
    _, z8, i8 = P.underflow_fractions(2.0 ** 8)
    assert z8 == 0.0 and i8 == 0.0
    _, z24, i24 = P.underflow_fractions(2.0 ** 24)
    assert z24 == 0.0 and i24 > 0.1  # too large a scale overflows: why the scale must be dynamic


def test_summation_order_changes_the_float32_result():
    o = P.order_dependence()
    assert o["distinct"] >= 2 and o["spread"] > 0


def test_tree_is_more_accurate_than_sequential_accumulation():
    t = P.tree_vs_sequential()
    assert t["tree_err"] < t["sequential_err"]


def test_lower_precision_inputs_cost_accuracy_in_the_expected_order():
    e = P.matmul_input_rounding_error(n=128)
    v = list(e.values())
    assert v[0] < v[1] < v[2]
    assert v[0] < 1e-3 and v[1] < 1e-2
