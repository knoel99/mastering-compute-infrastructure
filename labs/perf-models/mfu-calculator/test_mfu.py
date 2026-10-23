import math

import pytest

import mfu


def test_dense_flops_per_token_is_6n():
    assert mfu.flops_per_token(7e9) == 6 * 7e9


def test_attention_term_matches_palm_appendix_b_formula():
    # 7B-class configuration used in the module text: L=32, H=32, Q=128, T=4096
    f = mfu.flops_per_token(7e9, 32, 32, 128, 4096)
    assert f == 6 * 7e9 + 12 * 32 * 32 * 128 * 4096
    assert math.isclose((f - 6 * 7e9) / (6 * 7e9), 0.1534, abs_tol=5e-4)  # attention adds ~15 % at T=4096


def test_llama3_table4_rows_with_dense_bf16_peak_989():
    # Llama 3 405B, Table 4: (TFLOPs/GPU, reported BF16 MFU in %) with peak 989 TFLOP/s dense BF16 on H100
    for tflops, reported in [(430, 43), (400, 41), (380, 38)]:
        computed = 100 * mfu.mfu_from_tflops_per_gpu(tflops, 989)
        assert abs(computed - reported) < 1.0  # the paper rounds; 400/989 = 40.4 % is reported as 41 %


def test_roundtrip_step_time_and_mfu():
    f = mfu.flops_per_token(7e9, 32, 32, 128, 4096)
    tokens_step, gpus, peak = 2**22, 64, 989e12
    t = mfu.step_time_for_mfu(0.40, tokens_step, f, gpus, peak)
    got = mfu.mfu(mfu.tokens_per_second(tokens_step, t), f, gpus, peak)
    assert math.isclose(got, 0.40, rel_tol=1e-12)


def test_module_text_example_7b_on_64_gpus():
    f = mfu.flops_per_token(7e9, 32, 32, 128, 4096)
    got = mfu.mfu(mfu.tokens_per_second(2**22, 7.0), f, 64, 989e12)
    assert math.isclose(got, 0.4586, abs_tol=5e-4)


@pytest.mark.parametrize("bad", [dict(n_params=0), dict(n_params=-1)])
def test_invalid_params_rejected(bad):
    with pytest.raises(ValueError):
        mfu.flops_per_token(**bad)


def test_sparse_peak_gives_half_the_mfu():
    # classic trap: using the 'with sparsity' peak (1979 TFLOP/s BF16 for H100 SXM) instead of the dense one (989)
    dense = mfu.mfu_from_tflops_per_gpu(400, 989)
    sparse = mfu.mfu_from_tflops_per_gpu(400, 1979)
    assert math.isclose(sparse / dense, 989 / 1979, rel_tol=1e-9)
