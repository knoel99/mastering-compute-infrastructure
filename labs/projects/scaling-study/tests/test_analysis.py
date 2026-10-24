import pytest

import analysis


def test_summarize():
    s = analysis.summarize([1, 2, 3, 4, 5])
    assert s == {"n": 5, "median": 3.0, "p25": 2.0, "p75": 4.0}


def test_speedup_efficiency_karp_flatt():
    assert analysis.speedup(1.0, 0.3125) == pytest.approx(3.2)
    assert analysis.efficiency(1.0, 0.3125, 4) == pytest.approx(0.8)
    assert analysis.karp_flatt(3.2, 4) == pytest.approx(1 / 12)
    assert analysis.karp_flatt(2.0, 2) == pytest.approx(0.0, abs=1e-12)


def test_ring_allreduce_time():
    assert analysis.ring_allreduce_time(4e6, 1, 1e-5, 2e9) == 0.0
    assert analysis.ring_allreduce_time(4e6, 4, 1e-5, 2e9) == pytest.approx(6e-5 + 0.003)


def test_predict_step_strong_and_weak():
    comm = analysis.ring_allreduce_time(4e6, 4, 1e-5, 2e9)
    assert analysis.predict_step(0.08, 0.002, 4, "strong", 4e6, 1e-5, 2e9) == pytest.approx(0.02 + 0.002 + comm)
    assert analysis.predict_step(0.08, 0.002, 4, "weak", 4e6, 1e-5, 2e9) == pytest.approx(0.08 + 0.002 + comm)
    assert analysis.predict_step(0.08, 0.002, 1, "strong", 4e6, 1e-5, 2e9) == pytest.approx(0.082)


def test_utilization():
    assert analysis.utilization(6 * 1e6 * 64, 0.01, 1e11) == pytest.approx(0.384)


def point(mode, p, step, comm, compute, opt, rep):
    j = 1 + 0.01 * rep  # tiny per-run variation
    return {"mode": mode, "world": p, "rep": rep, "grad_bytes": 4_000_000, "flops_per_step_per_rank": 3.84e8,
            "step_s": [step * j] * 5, "comm_s": [comm * j] * 5, "compute_s": [compute * j] * 5, "opt_s": [opt * j] * 5}


def test_analyze_computes_rows_from_points():
    pts = []
    for rep in range(3):
        pts.append(point("strong", 1, 0.100, 0.0, 0.098, 0.002, rep))
        pts.append(point("strong", 2, 0.065, 0.010, 0.049, 0.002, rep))
        pts.append(point("weak", 1, 0.100, 0.0, 0.098, 0.002, rep))
        pts.append(point("weak", 2, 0.125, 0.025, 0.098, 0.002, rep))
    rows = {(r["mode"], r["world"]): r for r in analysis.analyze(pts, 1e-5, 2e9, peak_flops=1e11)}
    s2 = rows[("strong", 2)]
    assert s2["speedup"] == pytest.approx(0.100 / 0.065, rel=1e-6)
    assert s2["efficiency"] == pytest.approx(0.100 / 0.065 / 2, rel=1e-6)
    assert s2["karp_flatt"] == pytest.approx(analysis.karp_flatt(0.100 / 0.065, 2), rel=1e-6)
    assert s2["comm_share"] == pytest.approx(0.010 / 0.065, rel=1e-6)
    k = 1.01  # medians over the three repetitions pick the middle run, scaled by 1 + 0.01 * 1
    assert s2["predicted_s"] == pytest.approx(
        analysis.predict_step(0.098 * k, 0.002 * k, 2, "strong", 4e6, 1e-5, 2e9), rel=1e-6)
    assert s2["utilization"] == pytest.approx(3.84e8 / (0.049 * k) / 1e11, rel=1e-6)
    w2 = rows[("weak", 2)]
    assert w2["efficiency"] == pytest.approx(0.100 / 0.125, rel=1e-6)
    assert "speedup" not in w2
    assert rows[("strong", 1)]["karp_flatt"] is None
