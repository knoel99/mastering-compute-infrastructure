import math

import pytest

import yd

D, M, R = 60.0, 3.09 * 3600.0, 300.0


def test_young_value_and_scaling():
    assert yd.young(60.0, 11124.0) == pytest.approx(math.sqrt(2 * 60.0 * 11124.0))
    # a cluster 4x larger fails 4x more often: the optimal period halves
    assert yd.young(D, M / 4) == pytest.approx(yd.young(D, M) / 2)


def test_daly_high_matches_numerical_optimum():
    t_num = yd.argmin_exact(D, M, R)
    assert yd.daly_high(D, M) == pytest.approx(t_num, rel=0.005)
    # Young's formula includes the checkpoint time; Daly's compute interval does not
    assert abs(yd.young(D, M) - t_num) / t_num < 0.06


def test_first_order_breaks_when_checkpoint_is_not_small():
    d_big = M / 2  # a checkpoint as long as half the MTBF: the first-order assumption is false
    t_num = yd.argmin_exact(d_big, M, R)
    assert abs(yd.young(d_big, M) - t_num) / t_num > 0.25


def test_optimum_is_flat():
    g_opt = yd.goodput_exact(yd.argmin_exact(D, M, R), D, M, R)
    for k in (0.5, 2.0):
        g = yd.goodput_exact(k * yd.young(D, M), D, M, R)
        assert 0 < g_opt - g < 0.03  # a factor 2 in either direction costs less than 3 points


@pytest.mark.parametrize("tau", [600, 1155, 2300])
def test_monte_carlo_agrees_with_exact_formula(tau):
    mean, se = yd.mean_goodput(tau, D, M, R, work=1.5e6, seeds=range(30))
    assert abs(mean - yd.goodput_exact(tau, D, M, R)) < 4 * se + 0.002


def test_simulation_is_deterministic():
    a = yd.simulate(1000, D, M, R, 5e5, seed=3)
    b = yd.simulate(1000, D, M, R, 5e5, seed=3)
    assert a == b and a[1] > 0


def test_young_stays_close_to_best_for_bursty_failures():
    grid = [round(yd.young(D, M) * k) for k in (0.5, 0.75, 1.0, 1.5, 2.0)]
    g = {t: yd.mean_goodput(t, D, M, R, work=1.5e6, seeds=range(30), shape=0.7)[0] for t in grid}
    assert max(g.values()) - g[grid[2]] < 0.02
