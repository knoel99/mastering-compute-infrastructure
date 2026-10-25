"""Correctness of the Triton kernels under TRITON_INTERPRET=1 (CPU), plus the traffic ledger."""
import os

import pytest
import torch

import traffic
import triton_kernels as T

assert os.environ.get("TRITON_INTERPRET") == "1", "run through verify.sh or export TRITON_INTERPRET=1"
torch.manual_seed(0)


@pytest.mark.parametrize("n", [1, 127, 128, 1000])
def test_add_is_exact_for_any_length(n):
    x, y = torch.randn(n), torch.randn(n)
    assert torch.equal(T.add(x, y), x + y)


def test_fused_add_relu_equals_the_two_operations():
    x, y = torch.randn(1000), torch.randn(1000)
    assert torch.equal(T.fused_add_relu(x, y), torch.relu(x + y))


@pytest.mark.parametrize("cols", [1, 7, 64, 100, 129])
def test_softmax_matches_torch_for_non_power_of_two_widths(cols):
    x = torch.randn(11, cols) * 3
    torch.testing.assert_close(T.softmax(x), torch.softmax(x, dim=1), rtol=1e-5, atol=1e-7)


def test_softmax_is_stable_for_huge_inputs():
    x = torch.randn(4, 50)
    x[0] += 1000.0  # exp(1000) overflows float32 unless the row maximum is subtracted
    out = T.softmax(x)
    assert not torch.isnan(out).any() and not torch.isinf(out).any()
    torch.testing.assert_close(out.sum(dim=1), torch.ones(4), rtol=1e-5, atol=1e-5)


def test_matmul_with_shapes_that_are_not_multiples_of_the_blocks():
    a, b = torch.randn(20, 35), torch.randn(35, 18)
    torch.testing.assert_close(T.matmul(a, b), a @ b, rtol=1e-4, atol=1e-4)


def test_traffic_ledger_matches_the_closed_form():
    m, n = 64, 128
    r = traffic.report(m, n)
    assert r["reads"] == 5 * m * n + 2 * m
    assert r["writes"] == 3 * m * n + 2 * m
    assert r["ops"] == 5
    assert 3.9 < r["ratio"] < 4.1  # theoretical speed-up of a bandwidth-bound softmax: about 4
