import json
import statistics
import subprocess

import pytest


def bench(py, impl, tmp_path, world, **kw):
    out = tmp_path / f"b{world}.json"
    cmd = [py, str(impl / "bench.py"), "--world-size", str(world), "--hidden", "64", "--layers", "2",
           "--batch-per-rank", "16", "--steps", "6", "--warmup", "2", "--out", str(out)]
    r = subprocess.run(cmd, cwd=impl, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-500:]
    return json.loads(out.read_text())


def test_single_process_has_no_communication(py, impl, tmp_path):
    d = bench(py, impl, tmp_path, 1)
    assert statistics.median(d["comm_s"]) < 1e-4


def test_two_processes_communicate_and_schema_is_stable(py, impl, tmp_path):
    d = bench(py, impl, tmp_path, 2)
    assert statistics.median(d["comm_s"]) > 1e-4
    for k in ("step_s", "compute_s", "comm_s", "opt_s"):
        assert len(d[k]) == 6  # warm-up steps are not in the series
    assert d["n_params"] == 2 * (64 * 64 + 64) + 65
    assert d["grad_bytes"] == 4 * d["n_params"]
    assert d["flops_per_step_per_rank"] == 6 * d["n_params"] * 16
    assert all(s >= c for s, c in zip(d["step_s"], d["compute_s"]))


def test_decompose_splits_communication(py, impl, tmp_path):
    out = tmp_path / "d.json"
    cmd = [py, str(impl / "bench.py"), "--world-size", "2", "--hidden", "64", "--layers", "2",
           "--batch-per-rank", "16", "--steps", "6", "--warmup", "2", "--decompose", "--out", str(out)]
    r = subprocess.run(cmd, cwd=impl, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-500:]
    d = json.loads(out.read_text())
    assert d["decomposed"] and len(d["allreduce_s"]) == 6
    assert statistics.median(d["allreduce_s"]) > 0 and statistics.median(d["wait_s"]) >= 0
    # Each phase is the maximum over ranks, so the SUM of the maxima can exceed the maximum of the sums
    # (the rank that waits longest is not the one whose collective is slowest). What always holds:
    # a component never exceeds the communication time of the same step.
    for k in ("allreduce_s", "wait_s", "pack_s"):
        assert all(x <= c + 1e-9 for x, c in zip(d[k], d["comm_s"])), k
