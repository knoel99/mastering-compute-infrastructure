"""Tests of the parallelism planner. IMPL=starter|reference chooses the code under test."""
import math

import pytest

import planner as P

H100 = dict(hbm_bytes=80e9, peak_flops=989e12)


# ---- ZeRO model state: the figures of Figure 1 of the ZeRO paper (7.5 B parameters, 64-way data parallelism)
def test_zero_figure_1_of_the_paper():
    psi, dp = 7.5e9, 64
    assert P.zero_state_bytes(psi, dp, 0) == pytest.approx(120e9)
    assert P.zero_state_bytes(psi, dp, 1) == pytest.approx(31.40625e9)  # paper: 31.4 GB
    assert P.zero_state_bytes(psi, dp, 2) == pytest.approx(16.640625e9)  # paper: 16.6 GB
    assert P.zero_state_bytes(psi, dp, 3) == pytest.approx(1.875e9)  # paper: 1.9 GB


def test_zero_stages_decrease_and_dp1_changes_nothing():
    vals = [P.zero_state_bytes(1e9, 8, st) for st in range(4)]
    assert vals == sorted(vals, reverse=True) and len(set(vals)) == 4
    assert len({P.zero_state_bytes(1e9, 1, st) for st in range(4)}) == 1


def test_zero_rejects_unknown_stage():
    with pytest.raises(ValueError):
        P.zero_state_bytes(1e9, 8, 4)


def test_model_parallelism_divides_parameters_first():
    assert P.model_state_bytes(8e9, 2, 4, 1, 0) == pytest.approx(P.zero_state_bytes(1e9, 1, 0))
    assert P.model_state_bytes(8e9, 2, 4, 8, 3) == pytest.approx(16 * 8e9 / (2 * 4 * 8))


# ---- activations: Table 2 of Korthikanti et al. 2022
S, B, H, A = 2048, 1, 4096, 32


def test_activation_formula_without_parallelism():
    assert P.activation_bytes_per_layer(S, B, H, A) == pytest.approx(S * B * H * (34 + 5 * A * S / H))


def test_activation_tensor_parallel_baseline_and_sequence_parallel():
    t = 8
    base = S * B * H * (10 + 24 / t + 5 * A * S / (H * t))
    assert P.activation_bytes_per_layer(S, B, H, A, t) == pytest.approx(base)
    # tensor + sequence parallelism divides EVERYTHING by t
    assert P.activation_bytes_per_layer(S, B, H, A, t, sequence_parallel=True) == pytest.approx(
        P.activation_bytes_per_layer(S, B, H, A) / t)


def test_selective_recomputation_drops_the_attention_term():
    assert P.activation_bytes_per_layer(S, B, H, A, recompute="selective") == pytest.approx(S * B * H * 34)
    assert P.activation_bytes_per_layer(S, B, H, A, 8, True, "selective") == pytest.approx(S * B * H * 34 / 8)


def test_full_recomputation_keeps_only_the_layer_input():
    assert P.activation_bytes_per_layer(S, B, H, A, recompute="full") == 2 * S * B * H


def test_activation_recompute_value_must_be_known():
    with pytest.raises(ValueError):
        P.activation_bytes_per_layer(S, B, H, A, recompute="sometimes")


def test_first_stage_stores_all_layers_worth_whatever_the_pipeline_size():
    per = 1000.0
    for p in (1, 2, 4, 8):
        assert P.activation_bytes_first_stage(32, per, p, m=64) == pytest.approx(32 * per)


def test_first_stage_with_few_microbatches_and_with_interleaving():
    assert P.activation_bytes_first_stage(32, 1000.0, 8, m=2) == pytest.approx(32 / 8 * 2 * 1000.0)
    assert P.activation_bytes_first_stage(32, 1000.0, 8, m=64, v=2) == pytest.approx(32 * 1000.0 * (1 + 7 / 16))


# ---- pipeline and communication
def test_bubble_fraction():
    assert P.pipeline_bubble_fraction(1, 8) == 0.0
    assert P.pipeline_bubble_fraction(8, 64) == pytest.approx(7 / 64)
    assert P.pipeline_bubble_fraction(8, 64, v=4) == pytest.approx(7 / 256)
    with pytest.raises(ValueError):
        P.pipeline_bubble_fraction(4, 0)


def test_ring_allreduce_matches_the_alpha_beta_formula():
    assert P.ring_allreduce_seconds(1 << 30, 1, 25e9) == 0.0
    t = P.ring_allreduce_seconds(2**30, 8, 25e9, alpha=5e-6)
    assert t == pytest.approx(14 * 5e-6 + 2 * 7 / 8 * 2**30 / 25e9)


def test_zero3_costs_one_and_a_half_times_the_baseline_volume():
    base = P.dp_comm_seconds(1e9, 64, 2, 100e9)
    z3 = P.dp_comm_seconds(1e9, 64, 3, 100e9)
    assert z3 / base == pytest.approx(1.5)
    assert P.dp_comm_seconds(1e9, 1, 3, 100e9) == 0.0
    assert P.dp_comm_seconds(1e9, 64, 0, 100e9) == pytest.approx(P.dp_comm_seconds(1e9, 64, 1, 100e9))


def test_dp_volume_equals_one_ring_allreduce_of_the_gradients_for_stages_0_to_2():
    psi, dp, bw = 1e9, 16, 50e9
    assert P.dp_comm_seconds(psi, dp, 2, bw) == pytest.approx(P.ring_allreduce_seconds(2 * psi, dp, bw))


def test_tp_communication_is_four_allreduces_per_layer():
    one = P.ring_allreduce_seconds(S * B * H * 2, 8, 400e9)
    assert P.tp_comm_seconds(10, S, B, H, 8, 400e9) == pytest.approx(10 * 4 * one)
    assert P.tp_comm_seconds(10, S, B, H, 1, 400e9) == 0.0


def test_pipeline_point_to_point_traffic():
    one = S * B * H * 2 / 25e9  # one activation over 25 GB/s
    assert P.pp_comm_seconds(64, S, B, H, 1, False, 25e9) == pytest.approx(64 * 2 * one)
    assert P.pp_comm_seconds(64, S, B, H, 8, True, 25e9) == pytest.approx(64 * 2 * one / 8)


# ---- layouts
def test_feasible_layouts_small_case():
    got = P.feasible_layouts(8, 4, 8)
    assert got == [(1, 1, 8), (1, 2, 4), (1, 4, 2), (1, 8, 1), (2, 1, 4), (2, 2, 2), (2, 4, 1), (4, 1, 2), (4, 2, 1)]


def test_feasible_layouts_respect_the_node_and_the_layer_count():
    for tp, pp, dp in P.feasible_layouts(64, 8, 80):
        assert tp * pp * dp == 64 and 8 % tp == 0 and 80 % pp == 0


MODEL_7B = dict(psi=7e9, layers=32, h=4096, a=32, s=4096)
CLUSTER_8 = dict(n_gpus=8, bw_tp=400e9, bw_dp=400e9, mfu=0.4, **H100)


def test_evaluate_7b_plain_data_parallel_does_not_fit_but_zero3_does():
    layout = dict(tp=1, pp=1, dp=8, stage=0, b=1, global_batch=64, sp=False, recompute="full")
    r0 = P.evaluate(MODEL_7B, CLUSTER_8, layout)
    assert r0["state_gb"] == pytest.approx(112.0) and not r0["fits"]
    r3 = P.evaluate(MODEL_7B, CLUSTER_8, dict(layout, stage=3))
    assert r3["state_gb"] == pytest.approx(14.0) and r3["fits"]
    assert r3["bubble"] == 0.0 and r3["t_tp_s"] == 0.0 and r3["microbatches"] == 8


def test_evaluate_reports_pipeline_bubble_and_tp_traffic():
    layout = dict(tp=2, pp=4, dp=1, stage=0, b=1, global_batch=32, sp=True, recompute="selective")
    r = P.evaluate(MODEL_7B, CLUSTER_8, layout)
    assert r["microbatches"] == 32 and r["bubble"] == pytest.approx(3 / 32)
    assert r["t_tp_s"] > 0 and r["t_pp_s"] > 0 and r["t_dp_s"] == 0.0
    comm = (r["t_tp_s"] + r["t_pp_s"] + r["t_dp_s"]) / r["t_compute_s"]
    assert r["overhead_no_overlap"] == pytest.approx(r["bubble"] + comm + r["recompute_cost"])
    assert r["overhead_dp_hidden"] == pytest.approx(r["bubble"] + (r["t_tp_s"] + r["t_pp_s"]) / r["t_compute_s"] + r["recompute_cost"])
    assert r["overhead_dp_hidden"] <= r["overhead_no_overlap"]
    assert r["recompute_cost"] == pytest.approx(0.07)  # selective recomputation, Table 4 of Korthikanti et al.
    assert P.evaluate(MODEL_7B, CLUSTER_8, dict(layout, recompute="full"))["recompute_cost"] == pytest.approx(0.39)


def test_evaluate_keeps_a_memory_margin():
    layout = dict(tp=1, pp=1, dp=8, stage=3, b=1, global_batch=64, sp=False, recompute="full")
    tight = dict(CLUSTER_8, hbm_bytes=1.05 * 14e9 / 0.9 * 0.9)  # barely above the model state: the 10 % margin must reject it
    assert P.evaluate(MODEL_7B, tight, layout)["fits"] is False


def test_evaluate_validates_its_inputs():
    with pytest.raises(ValueError):
        P.evaluate(MODEL_7B, CLUSTER_8, dict(tp=2, pp=2, dp=1, stage=0, b=1, global_batch=8))  # 4 != 8 GPUs
    with pytest.raises(ValueError):
        P.evaluate(MODEL_7B, CLUSTER_8, dict(tp=1, pp=1, dp=8, stage=0, b=3, global_batch=64))  # 8 not a multiple of 3
    with pytest.raises(ValueError):
        P.evaluate(MODEL_7B, CLUSTER_8, dict(tp=1, pp=3, dp=8, stage=0, b=1, global_batch=64))
