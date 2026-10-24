import compare

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


def test_paired_diff_fields():
    d = compare.paired_diff([{"x": 1}, {"x": 2}], [{"x": 3}, {"x": 1}], "x")
    assert d["n"] == 2 and d["wins"] == 1 and d["mean"] == -0.5
