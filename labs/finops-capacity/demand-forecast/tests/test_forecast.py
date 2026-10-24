import numpy as np
import pytest

import forecast


def test_history_is_deterministic_positive_and_growing():
    a, b = forecast.synth_history(104, seed=0), forecast.synth_history(104, seed=0)
    assert np.array_equal(a, b)
    assert (a > 0).all() and a[-26:].mean() > a[:26].mean()


def test_different_seeds_differ():
    assert not np.array_equal(forecast.synth_history(104, seed=0), forecast.synth_history(104, seed=1))


def test_fit_recovers_the_growth_of_a_clean_series():
    d = forecast.synth_history(104, seed=0, growth_per_year=0.35, noise=0.02, campaigns_per_year=0.0, season_amp=0.1)
    g = forecast.growth_per_year(forecast.fit_trend_season(d))
    assert g == pytest.approx(0.35, abs=0.05)


def test_point_forecast_continues_the_curve():
    d = forecast.synth_history(104, seed=0, noise=0.0, campaigns_per_year=0.0)
    fit = forecast.fit_trend_season(d)
    pf = forecast.point_forecast(fit, 10)
    assert pf.shape == (10,) and (pf > 0).all()
    assert pf[0] == pytest.approx(d[-1], rel=0.1)


def test_scenarios_shape_positivity_and_seed():
    fit = forecast.fit_trend_season(forecast.synth_history(104, seed=0))
    a = forecast.scenarios(fit, 52, 200, seed=3)
    assert a.shape == (200, 52) and (a > 0).all()
    assert np.array_equal(a, forecast.scenarios(fit, 52, 200, seed=3))


def test_scenario_median_is_near_the_point_forecast():
    fit = forecast.fit_trend_season(forecast.synth_history(104, seed=0))
    med = np.median(forecast.scenarios(fit, 52, 1000, seed=3), axis=0)
    pf = forecast.point_forecast(fit, 52)
    assert np.median(med / pf) == pytest.approx(1.0, abs=0.2)


def test_backtest_reports_three_numbers_and_a_valid_coverage():
    d = forecast.synth_history(104, seed=0)
    b = forecast.backtest(d, 78, seed=0)
    assert set(b) == {"mae_model", "mae_naive", "coverage_10_90"}
    assert 0.0 <= b["coverage_10_90"] <= 1.0 and b["mae_model"] > 0
