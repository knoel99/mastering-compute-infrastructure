"""Structural tests of the profiling lab. They assert counters, FLOP counts and verdicts, never the
duration of an operator (the sandbox is shared and timings vary)."""
import filecmp
import json
import os

import pytest

import make_fixture
import profile_cpu
import tiny_model as tm
import trace_report as tr

HERE = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="module")
def explicit(tmp_path_factory):
    d = tmp_path_factory.mktemp("prof")
    r = profile_cpu.run("explicit", str(d / "trace.json"), str(d / "summary.json"))
    return r, str(d / "trace.json")


@pytest.fixture(scope="module")
def sdpa(tmp_path_factory):
    d = tmp_path_factory.mktemp("prof_sdpa")
    return profile_cpu.run("sdpa", str(d / "trace.json"), None)


def test_operator_call_counts_follow_from_the_model(explicit):
    ops = explicit[0]["ops"]
    assert ops["aten::addmm"]["calls"] == 4 * tm.LAYERS            # 4 linear layers per block, forward
    assert ops["aten::mm"]["calls"] == 8 * tm.LAYERS               # backward: grad of input + grad of weight
    assert ops["aten::bmm"]["calls"] == 6 * tm.LAYERS              # 2 forward + 4 backward batched products


def test_profiler_flops_equal_three_times_the_forward_flops(explicit):
    """forward + backward = 3 x forward for matrix products (backward does two products per forward one)."""
    r = explicit[0]
    assert r["matmul_flops"] == pytest.approx(3 * tm.forward_matmul_flops(), rel=1e-9)  # mm + addmm + bmm only


def test_trace_is_a_valid_chrome_trace_with_the_annotated_step(explicit):
    ev = tr.load_events(explicit[1])
    assert sum(e["cat"] == "cpu_op" for e in ev) > 200
    step = [e for e in ev if e["name"] == "train_step"]
    assert len(step) == 1


def test_self_times_add_up_to_the_annotated_step(explicit):
    ev = tr.load_events(explicit[1])
    step = next(e for e in ev if e["name"] == "train_step")
    inside = [e for e in ev if e["pid"] == step["pid"] and e["tid"] == step["tid"]
              and e["ts"] >= step["ts"] - 1e-6 and e["ts"] + e["dur"] <= step["ts"] + step["dur"] + 1e-6]
    total_self = sum(v["self_us"] for v in tr.self_times(inside).values())
    assert total_self == pytest.approx(step["dur"], rel=1e-6)  # nesting is consistent: nothing double-counted


def test_fused_attention_removes_the_explicit_softmax_and_batched_products(explicit, sdpa):
    e_ops, s_ops = explicit[0]["ops"], sdpa["ops"]
    assert e_ops["aten::softmax"]["calls"] == tm.LAYERS
    assert "aten::softmax" not in s_ops
    assert e_ops["aten::bmm"]["calls"] > s_ops.get("aten::bmm", {"calls": 0})["calls"]


def test_self_time_of_a_hand_built_nesting():
    ev = [{"ph": "X", "cat": "cpu_op", "name": n, "pid": 1, "tid": 1, "ts": ts, "dur": d}
          for n, ts, d in [("parent", 0, 100), ("child", 10, 30), ("child", 50, 20), ("other", 120, 10)]]
    st = tr.self_times(ev)
    assert st["parent"]["self_us"] == 50 and st["child"]["calls"] == 2 and st["other"]["self_us"] == 10


def test_merged_busy_counts_overlaps_once():
    assert tr.merged_busy([(0, 10), (5, 15), (20, 30)]) == 25


def test_fixtures_are_reproducible_and_flagged_synthetic(tmp_path):
    make_fixture.main(str(tmp_path))
    for name in ("launch_bound", "gpu_bound", "transfer_bound"):
        assert filecmp.cmp(tmp_path / f"{name}.json", os.path.join(HERE, "fixtures", f"{name}.json"), shallow=False)
        assert json.load(open(tmp_path / f"{name}.json"))["otherData"]["synthetic"] is True


@pytest.mark.parametrize("name,word", [("launch_bound", "LAUNCH-BOUND"), ("gpu_bound", "GPU-BOUND"),
                                       ("transfer_bound", "TRANSFER-BOUND")])
def test_verdict_on_each_synthetic_scenario(name, word):
    g = tr.gpu_summary(tr.load_events(os.path.join(HERE, "fixtures", f"{name}.json")))
    assert g["verdict"].startswith(word)


def test_launch_bound_numbers():
    g = tr.gpu_summary(tr.load_events(os.path.join(HERE, "fixtures", "launch_bound.json")))
    assert g["kernels"] == 200 and g["utilization"] < 0.4 and g["median_kernel_us"] < 10


def test_cpu_only_trace_has_no_gpu_summary(explicit):
    assert tr.gpu_summary(tr.load_events(explicit[1])) is None
