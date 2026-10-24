import pytest

import goodput

C, M, R = 60.0, 6 * 3600.0, 300.0


def test_young_daly_formula():
    assert goodput.young_daly(60.0, 21600.0) == pytest.approx(1609.97, rel=1e-4)


def test_model_is_minimised_at_young_daly():
    t = goodput.young_daly(C, M)
    w = goodput.waste_fraction
    assert w(t, C, M, R) < w(0.5 * t, C, M, R) and w(t, C, M, R) < w(2 * t, C, M, R)


def test_simulation_agrees_with_model_near_optimum():
    t = goodput.young_daly(C, M)
    sim = goodput.simulate(t, C, M, R, horizon=5e7, seed=1)
    assert sim == pytest.approx(1 - goodput.waste_fraction(t, C, M, R), abs=0.02)


def test_simulation_optimum_is_near_young_daly():
    t = goodput.young_daly(C, M)
    g = {k: goodput.simulate(k * t, C, M, R, horizon=5e7, seed=1) for k in (0.25, 1.0, 4.0)}
    assert g[1.0] > g[0.25] and g[1.0] > g[4.0]


def test_no_failures_means_only_checkpoint_overhead():
    g = goodput.simulate(100.0, 10.0, 1e18, R, horizon=10000.0, seed=0)
    assert g == pytest.approx(100.0 / 110.0, rel=1e-6)
