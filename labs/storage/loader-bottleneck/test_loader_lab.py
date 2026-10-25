"""Fast tests for loader_lab: determinism, model limits, decision table, one tiny real DataLoader run."""
import pytest

import loader_lab as L


def test_dataset_is_deterministic_and_has_the_requested_straggler_rate():
    a = L.SyntheticDataset(2000, 0.0, 0.0, slow_frac=0.05, slow_mult=10, seed=7)
    b = L.SyntheticDataset(2000, 0.0, 0.0, slow_frac=0.05, slow_mult=10, seed=7)
    assert [a.is_slow(i) for i in range(2000)] == [b.is_slow(i) for i in range(2000)]
    n_slow = sum(a.is_slow(i) for i in range(2000))
    assert 60 <= n_slow <= 140  # 5 % of 2000 = 100, binomial std about 10: a generous 4-sigma window
    x1, i1 = a[5]
    x2, i2 = b[5]
    assert i1 == i2 == 5 and bool((x1 == x2).all())


def test_model_limits():
    kw = dict(batch_size=8, io_s=0.006, cpu_s=0.001, step_s=0.012, cores=4)
    serial = L.predict_stall(0, **kw)
    assert serial == pytest.approx(8 * 0.007 / (8 * 0.007 + 0.012))
    stalls = [L.predict_stall(w, **kw) for w in (1, 2, 4, 8, 16)]
    assert stalls == sorted(stalls, reverse=True), "more workers never increase the predicted stall"
    assert stalls[-1] == 0.0 and stalls[0] > 0.75


def test_cpu_ceiling_does_not_move_with_more_workers():
    kw = dict(batch_size=8, io_s=0.0, cpu_s=0.010, step_s=0.012, cores=4)
    assert L.predict_stall(4, **kw) == pytest.approx(L.predict_stall(64, **kw))
    assert L.predict_stall(4, **kw) == pytest.approx(1 - 0.012 * 4 / (8 * 0.010))


@pytest.mark.parametrize("stall,util,workers,expected", [
    (0.01, 0.1, 4, "GPU-bound"),
    (0.60, 0.0, 0, "serial loading"),
    (0.50, 0.15, 4, "latency-bound"),
    (0.50, 0.95, 4, "CPU-bound"),
    (0.40, 0.55, 8, "CPU-bound"),     # 8 workers x 0.55 = 4.4 cores busy out of 4
])
def test_decision_table(stall, util, workers, expected):
    assert L.diagnose(stall, util, workers, cores=4).startswith(expected)


def test_tiny_real_run_reports_sane_numbers():
    ds = L.SyntheticDataset(10_000, 0.002, 0.0)
    for w in (0, 2):
        r = L.run(ds, w, 2, batch_size=4, step_s=0.002, n_batches=10, warmup=1)
        assert 0.0 <= r.stall <= 1.0 and r.batches_per_s > 0
