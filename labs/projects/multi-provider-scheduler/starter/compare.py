#!/usr/bin/env python3
"""Compare policies over many seeds — TO WRITE (milestone 3).

POLICIES maps a name to a policy class. Keep these signatures; tests/test_compare.py uses them.
"""
import sys

import data  # noqa: F401
import policies
import sim  # noqa: F401

POLICIES = {"cheapest": policies.Cheapest, "on-demand": policies.OnDemandOnly, "hedged": policies.Hedged}


def run_policy(name, seeds, n_jobs=30, offers=None):
    """For each seed: data.make_jobs(n_jobs, seed=seed), sim.simulate(..., seed=seed) with a fresh policy.
    Return a list of dicts {cost, misses, unfinished, interruptions, lost_h} (lost_h = lost minutes / 60)."""
    raise NotImplementedError


def mean_ci(xs, n_boot=2000, seed=0, level=0.95):
    """(mean, lo, hi): percentile bootstrap of the mean, reproducible for a given seed."""
    raise NotImplementedError


def paired_diff(rows_a, rows_b, key, n_boot=2000, seed=0):
    """{mean, lo, hi, wins, n} of (a - b) per seed for `key`, with a bootstrap interval; wins = seeds where a < b.
    The same jobs and the same interruption luck are replayed for every policy: the PAIRED difference is the
    meaningful comparison, not the overlap of two intervals of means."""
    raise NotImplementedError


def main():
    raise NotImplementedError("print the table of means with intervals and the paired differences")


if __name__ == "__main__":
    sys.exit(main())
