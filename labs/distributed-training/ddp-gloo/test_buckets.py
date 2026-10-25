"""Unit tests of the bucket predictor (pure Python, deterministic)."""
from buckets import MiB, predict_buckets


def test_single_bucket_when_everything_fits():
    assert predict_buckets([100, 200, 300], cap_mb=1) == [600]


def test_bucket_closes_when_limit_is_reached_and_may_overshoot():
    # limit 1 MiB: 600k + 600k = 1.2M >= 1 MiB closes the bucket (overshoot by the last tensor)
    sizes = [600_000, 600_000, 10]
    assert predict_buckets(sizes, cap_mb=1) == [1_200_000, 10]


def test_exact_limit_closes_bucket():
    assert predict_buckets([MiB, 5], cap_mb=1) == [MiB, 5]


def test_default_uses_small_first_bucket():
    sizes = [2 * MiB, 3 * MiB, 4 * MiB]
    # default: first limit 1 MiB (closed by the first tensor), then 25 MiB
    assert predict_buckets(sizes, cap_mb=None) == [2 * MiB, 7 * MiB]
    # explicit cap: the first bucket obeys the same limit as the others
    assert predict_buckets(sizes, cap_mb=4) == [2 * MiB + 3 * MiB, 4 * MiB]


def test_total_is_preserved():
    sizes = [1000 * (i + 1) for i in range(50)]
    for cap in (None, 0.001, 0.01, 1):
        assert sum(predict_buckets(sizes, cap)) == sum(sizes)
