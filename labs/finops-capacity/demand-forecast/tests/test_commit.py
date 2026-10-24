import numpy as np
import pytest

import commit
import forecast


def test_cost_hand_computed():
    d = np.array([[2.0, 4.0]])
    # L=3: committed 3*2 GPU-weeks at r=1, on-demand excess (0 + 1) at o=2 -> 168 * (6 + 2)
    assert commit.cost(3.0, d, r=1.0, o=2.0)[0] == pytest.approx(168.0 * 8.0)


def test_cost_with_cap_and_penalty():
    d = np.array([[10.0]])
    # L=2, excess 8: on-demand min(8, cap=5)=5, unmet 3 -> 168 * (1*2 + 2*5 + 4*3)
    assert commit.cost(2.0, d, r=1.0, o=2.0, cap=5.0, penalty=4.0)[0] == pytest.approx(168.0 * 24.0)


def test_optimal_commit_is_the_critical_quantile():
    d = np.arange(100, dtype=float).reshape(1, -1)
    assert commit.optimal_commit(d, r=1.0, o=4.0) == 74.0          # 1 - 1/4 = 0.75 -> smallest L with F(L) >= 0.75


def test_never_commit_when_the_commitment_is_dearer():
    d = np.arange(100, dtype=float).reshape(1, -1)
    assert commit.optimal_commit(d, r=4.0, o=4.0) == 0.0
    assert commit.optimal_commit(d, r=5.0, o=4.0) == 0.0


@pytest.fixture(scope="module")
def sc():
    fit = forecast.fit_trend_season(forecast.synth_history(104, seed=0))
    return forecast.scenarios(fit, 52, 600, seed=1)


def test_closed_form_matches_the_grid_minimizer(sc):
    L = commit.optimal_commit(sc, 2.6, 4.0)
    Lg, mean_g = commit.best_commit_grid(sc, 2.6, 4.0, step=0.5)
    assert abs(L - Lg) <= 0.5
    assert commit.cost(L, sc, 2.6, 4.0).mean() <= mean_g * (1 + 1e-6)


def test_moving_the_commitment_either_way_costs_more(sc):
    L = commit.optimal_commit(sc, 2.6, 4.0)
    base = commit.cost(L, sc, 2.6, 4.0).mean()
    assert commit.cost(0.9 * L, sc, 2.6, 4.0).mean() > base
    assert commit.cost(1.1 * L, sc, 2.6, 4.0).mean() > base


def test_probability_of_exceeding_the_commitment_is_the_price_ratio(sc):
    rep = commit.risk_report(commit.optimal_commit(sc, 2.6, 4.0), sc, 2.6, 4.0)
    assert rep["p_week_above_commit"] == pytest.approx(2.6 / 4.0, abs=0.01)


def test_shortage_risk_pushes_the_commitment_up(sc):
    plain = commit.optimal_commit(sc, 2.6, 4.0)
    guarded, _ = commit.best_commit_grid(sc, 2.6, 4.0, cap=10.0, penalty=20.0, step=1.0)
    assert guarded > plain


def test_report_fields_and_ordering(sc):
    L = commit.optimal_commit(sc, 2.6, 4.0)
    rep = commit.risk_report(L, sc, 2.6, 4.0)
    assert rep["p95_cost"] >= rep["mean_cost"]
    assert rep["mean_cost"] < rep["all_on_demand_mean_cost"]
    assert rep["p_scenario_with_unmet"] == 0.0
    assert 0.0 <= rep["unused_commit_frac"] <= 1.0


def test_unused_commitment_grows_with_the_commitment(sc):
    lo = commit.risk_report(60.0, sc, 2.6, 4.0)["unused_commit_frac"]
    hi = commit.risk_report(200.0, sc, 2.6, 4.0)["unused_commit_frac"]
    assert hi > lo
