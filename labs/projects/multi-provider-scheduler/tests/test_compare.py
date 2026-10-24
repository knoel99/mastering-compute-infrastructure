import pytest

import compare
import data
import policies
import sim

SEEDS = range(8)


def rows():
    return {n: compare.run_policy(n, SEEDS, n_jobs=30) for n in compare.POLICIES}


def test_hedged_is_cheaper_than_both_baselines_on_every_seed():
    r = rows()
    for base in ("cheapest", "on-demand"):
        d = compare.paired_diff(r["hedged"], r[base], "cost")
        assert d["wins"] == d["n"] == len(SEEDS) and d["hi"] < 0


def test_hedged_misses_fewer_deadlines_than_both_baselines():
    r = rows()
    for base in ("cheapest", "on-demand"):
        d = compare.paired_diff(r["hedged"], r[base], "misses")
        assert d["mean"] < 0 and d["hi"] < 0


def test_cheapest_per_hour_is_not_cheapest_overall():
    """The lowest price per hour is not the lowest cost: Cheapest pays for rework after interruptions."""
    r = rows()
    assert compare.paired_diff(r["cheapest"], r["hedged"], "cost")["lo"] > 0
    assert sum(x["lost_h"] for x in r["cheapest"]) > 5 * sum(x["lost_h"] for x in r["hedged"])


def test_mean_ci_contains_the_mean_and_is_reproducible():
    xs = [3.0, 5.0, 4.0, 6.0, 5.5, 4.5]
    m, lo, hi = compare.mean_ci(xs)
    assert lo <= m <= hi and (m, lo, hi) == compare.mean_ci(xs)
    m, lo, hi = compare.mean_ci(list(range(100)))  # sd 29, n 100: the normal 95 % half-width is about 5.7
    assert (m, lo, hi) == compare.mean_ci(list(range(100)))
    assert 4.8 < m - lo < 6.6 and 4.8 < hi - m < 6.6


def test_paired_diff_fields():
    d = compare.paired_diff([{"x": 1}, {"x": 2}], [{"x": 3}, {"x": 1}], "x")
    assert d["n"] == 2 and d["wins"] == 1 and d["mean"] == -0.5
    tie = compare.paired_diff([{"x": 1}, {"x": 2}, {"x": 5}], [{"x": 3}, {"x": 1}, {"x": 5}], "x")
    assert tie["n"] == 3 and tie["wins"] == 1  # a tie is not a win


def test_run_policy_replays_the_seed_for_the_jobs_and_for_the_interruption_luck():
    seeds = [2, 5]
    rows_ = compare.run_policy("cheapest", seeds, n_jobs=12)
    for row, s in zip(rows_, seeds):
        r = sim.simulate(data.default_offers(), data.make_jobs(12, seed=s), policies.Cheapest(), seed=s)
        assert row["cost"] == pytest.approx(r.cost) and row["misses"] == r.deadline_misses
        assert row["unfinished"] == r.unfinished and row["interruptions"] == r.interruptions
        assert row["lost_h"] == pytest.approx(r.lost_min / 60.0)
