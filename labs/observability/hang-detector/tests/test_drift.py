import random

import drift


def series(n=400, drop_at=200, drop=0.03, sd=0.01, seed=5):
    rng = random.Random(seed)
    return [100.0 * (1 - (drop if i >= drop_at else 0.0)) * rng.gauss(1, sd) for i in range(n)]


def test_cusum_catches_a_three_percent_drop_the_threshold_cannot_see():
    xs = series()
    i = drift.cusum_drop(xs)
    assert i is not None and 200 <= i <= 260          # found, and not before the drop
    assert drift.fixed_threshold(xs, drop=0.10) is None


def test_cusum_is_quiet_on_a_healthy_series():
    assert sum(drift.cusum_drop(series(drop=0.0, seed=s)) is not None for s in range(200)) <= 6   # ~1 % expected
