import json
import os
import subprocess

import pytest

import analysis
import report
import run_study


def test_plan_covers_every_point_with_replications():
    items = run_study.plan([1, 2, 4], ["strong", "weak"], 3, 256, 64)
    assert len(items) == 18
    for mode in ("strong", "weak"):
        for p in (1, 2, 4):
            grp = [i for i in items if i["mode"] == mode and i["world"] == p]
            assert sorted(i["rep"] for i in grp) == [0, 1, 2]
            expected = 256 // p if mode == "strong" else 64
            assert {i["batch_per_rank"] for i in grp} == {expected}


def test_plan_order_is_shuffled_but_reproducible():
    a = run_study.plan([1, 2, 4], ["strong", "weak"], 3, 256, 64, seed=0)
    b = run_study.plan([1, 2, 4], ["strong", "weak"], 3, 256, 64, seed=0)
    c = run_study.plan([1, 2, 4], ["strong", "weak"], 3, 256, 64, seed=1)
    ordered = sorted(a, key=lambda i: (i["mode"], i["world"], i["rep"]))
    assert a == b and a != c and a != ordered


def test_plan_rejects_indivisible_global_batch():
    with pytest.raises(ValueError):
        run_study.plan([1, 3], ["strong"], 1, 256, 64)


def test_end_to_end_small_study(tmp_path, py, impl):
    out = tmp_path / "results.json"
    cmd = [py, str(impl / "run_study.py"), "--world-sizes", "1,2", "--modes", "strong", "--reps", "1",
           "--steps", "4", "--warmup", "1", "--hidden", "64", "--layers", "2", "--global-batch", "64",
           "--out", str(out)]
    r = subprocess.run(cmd, cwd=impl, capture_output=True, text=True, timeout=180, env=os.environ)
    assert r.returncode == 0, r.stderr
    pts = json.loads(out.read_text())["points"]
    assert sorted((p["world"], p["batch_per_rank"]) for p in pts) == [(1, 64), (2, 32)]
    rows = analysis.analyze(pts, 1e-5, 2e9)
    assert [x["world"] for x in rows] == [1, 2]


def test_dry_run_prints_the_plan(py, impl):
    r = subprocess.run([py, str(impl / "run_study.py"), "--dry-run", "--reps", "2"], cwd=impl,
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0
    assert len(r.stdout.strip().splitlines()) == 2 * 3 * 2


def synthetic_results():
    def pt(mode, p, step, comm, compute, rep):
        return {"mode": mode, "world": p, "rep": rep, "grad_bytes": 4_000_000, "n_params": 1_000_000,
                "flops_per_step_per_rank": 3.84e8, "steps": 5, "warmup": 2, "cpu_count": 4, "torch": "x",
                "step_s": [step] * 5, "comm_s": [comm] * 5, "compute_s": [compute] * 5, "opt_s": [0.002] * 5}
    pts = []
    for rep in range(3):
        pts += [pt("strong", 1, 0.100, 0.0, 0.098, rep), pt("strong", 2, 0.065, 0.010, 0.049, rep)]
    return {"points": pts}


def test_report_has_required_sections_and_numbers():
    text, rows = report.build(synthetic_results(), {"alpha_s": 1e-5, "B_bytes_per_s": 2e9}, peak_gflops=100)
    for needle in ("## Alpha-beta fit", "## Results", "## Definitions", "## Threats to validity",
                   "Karp-Flatt", "alpha = 10.0 us", "B = 2.000 GB/s"):
        assert needle in text, needle
    assert "| strong | 2 | 0.0650 |" in text
    assert "0.77" in text  # efficiency 0.100 / (2 * 0.065)
    threats = text.split("## Threats to validity")[1]
    assert sum(line.startswith("- ") for line in threats.splitlines()) >= 4  # at least four threats, one per bullet


def test_report_adds_breakdown_when_runs_are_decomposed():
    res = synthetic_results()
    extra = [dict(x, decomposed=True, step_s=[9.0] * 5, pack_s=[0.001] * 5, wait_s=[0.002] * 5,
                  allreduce_s=[0.006] * 5) for x in res["points"]]
    res["points"] += extra
    text, _ = report.build(res, {"alpha_s": 1e-5, "B_bytes_per_s": 2e9})
    assert "## Communication breakdown" in text and "perturbs" in text
    assert "| strong | 2 | 0.0650 |" in text  # headline table ignores the perturbed runs
