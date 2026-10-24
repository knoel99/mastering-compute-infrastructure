import math

import pytest

import goodput

C, M, R = 60.0, 6 * 3600.0, 300.0


def test_young_daly_formula():
    assert goodput.young_daly(60.0, 21600.0) == pytest.approx(1609.97, rel=1e-4)


def test_model_is_minimised_at_young_daly():
    t = goodput.young_daly(C, M)
    w = goodput.waste_fraction
    assert w(t, C, M, R) < w(0.5 * t, C, M, R) and w(t, C, M, R) < w(2 * t, C, M, R)
    assert w(1000.0, C, M, R) == pytest.approx(C / 1000.0 + (500.0 + R) / M)


def test_simulation_agrees_with_model_near_optimum():
    t = goodput.young_daly(C, M)
    sim = goodput.simulate(t, C, M, R, horizon=5e7, seed=1)
    assert sim == pytest.approx(1 - goodput.waste_fraction(t, C, M, R), abs=0.02)

    # second anchor, where failures are frequent (the first-order model no longer applies): with exponential
    # failures, a failure during a checkpoint losing it and none during a restart, securing one segment of
    # T + C seconds takes on average (M + R) * (exp((T + C) / M) - 1) seconds.
    t, c, m, r = 100.0, 50.0, 300.0, 10.0
    exact = t / ((m + r) * (math.exp((t + c) / m) - 1.0))
    assert goodput.simulate(t, c, m, r, horizon=1e7, seed=1) == pytest.approx(exact, rel=0.02)


def test_simulation_optimum_is_near_young_daly():
    t = goodput.young_daly(C, M)
    g = {k: goodput.simulate(k * t, C, M, R, horizon=5e7, seed=1) for k in (0.25, 1.0, 4.0)}
    assert g[1.0] > g[0.25] and g[1.0] > g[4.0]


def test_no_failures_means_only_checkpoint_overhead():
    g = goodput.simulate(100.0, 10.0, 1e18, R, horizon=10000.0, seed=0)
    assert g == pytest.approx(100.0 / 110.0, rel=1e-6)
