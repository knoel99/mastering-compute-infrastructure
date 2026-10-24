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
    raise NotImplementedError("TODO: implement cost (see the docstring and tests/)")


def optimal_commit(D, r, o):
    """Closed form without cap or penalty: the pooled demand quantile at the critical ratio 1 - r/o.

    Returns 0.0 when r >= o (committing never pays). Use method='inverted_cdf' so that the answer is
    the exact minimizer of the sample cost."""
    raise NotImplementedError("TODO: implement optimal_commit (see the docstring and tests/)")


def best_commit_grid(D, r, o, cap=None, penalty=0.0, step=1.0):
    """Numerical minimizer of the mean cost over a grid of commitments (needed when cap/penalty are set)."""
    raise NotImplementedError("TODO: implement best_commit_grid (see the docstring and tests/)")


def risk_report(L, D, r, o, cap=None, penalty=0.0):
    """Numbers to put in front of a decision maker for a given commitment L."""
    raise NotImplementedError("TODO: implement risk_report (see the docstring and tests/)")
