#!/usr/bin/env python3
"""How many GPUs to commit for, given demand scenarios (newsvendor problem with a price for the shortfall).

D has shape (n_scenarios, weeks) and holds the number of GPUs demanded each week.
r = price of one committed GPU-hour (paid whether used or not); o = price of one on-demand GPU-hour.
Committing L GPUs for the whole horizon costs, for one scenario:
    H * ( r * L * weeks + o * sum_t min(max(D_t - L, 0), cap) + penalty * sum_t unmet_t )
"""
import numpy as np

H = 168.0  # hours per week


def cost(L, D, r, o, cap=None, penalty=0.0):
    """Cost of every scenario (array of length n_scenarios) when committing L GPUs.

    cap: most GPUs obtainable on demand at any time (None = unlimited). penalty: cost of one unserved GPU-hour."""
    D = np.asarray(D, dtype=float)
    excess = np.maximum(D - L, 0.0)
    on_demand = excess if cap is None else np.minimum(excess, cap)
    unmet = excess - on_demand
    return H * (r * L * D.shape[1] + o * on_demand.sum(axis=1) + penalty * unmet.sum(axis=1))


def optimal_commit(D, r, o):
    """Closed form without cap or penalty: the pooled demand quantile at the critical ratio 1 - r/o.

    Returns 0.0 when r >= o (committing never pays). Use method='inverted_cdf' so that the answer is
    the exact minimizer of the sample cost."""
    if r >= o:
        return 0.0
    return float(np.quantile(np.asarray(D, dtype=float).ravel(), 1.0 - r / o, method="inverted_cdf"))


def best_commit_grid(D, r, o, cap=None, penalty=0.0, step=1.0):
    """Numerical minimizer of the mean cost over a grid of commitments (needed when cap/penalty are set)."""
    D = np.asarray(D, dtype=float)
    grid = np.arange(0.0, D.max() + step, step)
    means = np.array([cost(L, D, r, o, cap, penalty).mean() for L in grid])
    i = int(np.argmin(means))
    return float(grid[i]), float(means[i])


def risk_report(L, D, r, o, cap=None, penalty=0.0):
    """Numbers to put in front of a decision maker for a given commitment L."""
    D = np.asarray(D, dtype=float)
    weeks = D.shape[1]
    c = cost(L, D, r, o, cap, penalty)
    excess = np.maximum(D - L, 0.0)
    unmet = excess - (excess if cap is None else np.minimum(excess, cap))
    committed_hours = L * weeks
    return {
        "commit_gpus": float(L),
        "mean_cost": float(c.mean()),
        "p95_cost": float(np.quantile(c, 0.95)),
        "p_week_above_commit": float((D > L).mean()),
        "p_scenario_with_unmet": float((unmet > 0).any(axis=1).mean()),
        "unused_commit_frac": float(np.maximum(L - D, 0.0).sum(axis=1).mean() / committed_hours) if L > 0 else 0.0,
        "all_on_demand_mean_cost": float(cost(0.0, D, r, o, cap, penalty).mean()),
    }
