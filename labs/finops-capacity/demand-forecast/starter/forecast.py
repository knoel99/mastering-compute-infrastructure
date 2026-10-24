#!/usr/bin/env python3
"""Weekly GPU-demand history (SYNTHETIC), trend + season fit, and bootstrap demand scenarios.

Demand D_t is the average number of GPUs a research team wants in week t. The history generator is a
made-up model (exponential growth, yearly seasonality, log-normal noise, Poisson-arriving training campaigns):
it stands in for the accounting export you would use in real life (see lab 15.1).
"""
import numpy as np

PERIOD = 52  # weeks


def synth_history(weeks=104, seed=0, base=40.0, growth_per_year=0.35, season_amp=0.15, noise=0.10,
                  campaigns_per_year=3.0, campaign_gpus=96.0, campaign_weeks=(3, 8)):
    """SYNTHETIC weekly demand, in GPUs. Deterministic for a given seed."""
    rng = np.random.default_rng(seed)
    t = np.arange(weeks)
    level = base * np.exp(np.log1p(growth_per_year) * t / PERIOD)
    season = 1.0 + season_amp * np.sin(2.0 * np.pi * t / PERIOD + 0.6)
    d = level * season * np.exp(rng.normal(0.0, noise, weeks))
    for _ in range(rng.poisson(campaigns_per_year * weeks / PERIOD)):
        start = int(rng.integers(0, weeks))
        length = int(rng.integers(*campaign_weeks))
        d[start:start + length] += campaign_gpus * rng.uniform(0.5, 1.0)
    return d


def design(t):
    w = 2.0 * np.pi * np.asarray(t, dtype=float) / PERIOD
    return np.column_stack([np.ones_like(w), np.asarray(t, dtype=float), np.sin(w), np.cos(w)])


def fit_trend_season(d):
    """Least squares on log-demand: intercept + linear trend + one yearly harmonic. Keeps the residuals."""
    d = np.asarray(d, dtype=float)
    x = design(np.arange(len(d)))
    beta, *_ = np.linalg.lstsq(x, np.log(d), rcond=None)
    return {"beta": beta, "resid": np.log(d) - x @ beta, "n": len(d)}


def growth_per_year(fit):
    """Yearly growth implied by the fitted trend (e.g. 0.35 = +35 % per year)."""
    return float(np.expm1(fit["beta"][1] * PERIOD))


def point_forecast(fit, horizon):
    t = np.arange(fit["n"], fit["n"] + horizon)
    return np.exp(design(t) @ fit["beta"])


def scenarios(fit, horizon, n_scen, seed=0, block=4, slope_sd=0.10):
    """Demand scenarios: fitted curve + block-bootstrapped residuals + a random change of the yearly growth.

    slope_sd is the standard deviation of the extra log-growth per year drawn for each scenario."""
    rng = np.random.default_rng(seed)
    t = np.arange(fit["n"], fit["n"] + horizon)
    base = design(t) @ fit["beta"]
    res, m = fit["resid"], len(fit["resid"])
    out = np.empty((n_scen, horizon))
    for i in range(n_scen):
        eps = []
        while len(eps) < horizon:
            s = int(rng.integers(0, m - block + 1))
            eps.extend(res[s:s + block])
        slope = rng.normal(0.0, slope_sd)
        out[i] = np.exp(base + slope * (t - fit["n"] + 1) / PERIOD + np.array(eps[:horizon]))
    return out


def backtest(d, split, n_scen=500, seed=0, naive_window=8):
    """Fit on d[:split], compare with d[split:]: MAE of the point forecast, MAE of a naive 'last weeks' mean,
    and the share of observed weeks inside the 10-90 % band of the scenarios."""
    d = np.asarray(d, dtype=float)
    fit = fit_trend_season(d[:split])
    h = len(d) - split
    pf = point_forecast(fit, h)
    sc = scenarios(fit, h, n_scen, seed=seed)
    lo, hi = np.quantile(sc, 0.10, axis=0), np.quantile(sc, 0.90, axis=0)
    naive = np.full(h, d[split - naive_window:split].mean())
    return {
        "mae_model": float(np.abs(pf - d[split:]).mean()),
        "mae_naive": float(np.abs(naive - d[split:]).mean()),
        "coverage_10_90": float(((d[split:] >= lo) & (d[split:] <= hi)).mean()),
    }
