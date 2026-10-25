import pytest

import iosizing as z


def test_read_bandwidth_and_units():
    assert z.read_bandwidth(256, 8000, 2) == 4_096_000
    assert z.read_bandwidth(8, 1000, 100_000) == 800e6


def test_checkpoint_size_and_bandwidth():
    assert z.checkpoint_state_bytes(70e9) == pytest.approx(980e9)
    assert z.checkpoint_write_bandwidth(980e9, 1800, 0.10) == pytest.approx(980e9 / 180)
    assert z.transfer_time(1e9, 1e9, 0.5) == pytest.approx(1.5)


def test_striping_helpers():
    assert z.stripes_needed(6e9, 1.5e9) == 4 and z.stripes_needed(6.1e9, 1.5e9) == 5 and z.stripes_needed(1, 1e9) == 1
    assert z.aggregate_bandwidth(10, 1e9, 4, 1e9) == 4e9   # server side is the limit
    assert z.aggregate_bandwidth(2, 1e9, 4, 1e9) == 2e9    # client side is the limit


def test_metadata_and_requests():
    assert z.metadata_operations(1000, 3, 2) == 6000
    assert z.prefixes_needed(z.requests_per_second(20e9, 8 * 2**20), 5500) == 1
    assert z.prefixes_needed(20_000, 5500) == 4


@pytest.mark.parametrize("x", [0.25, 0.5, 0.75])
def test_simulation_matches_the_analytic_hit_ratios(x):
    n, epochs = 3000, 8
    lru = z.simulate_epoch_hit_ratio(n, int(x * n), epochs, "lru", seed=1)
    pin = z.simulate_epoch_hit_ratio(n, int(x * n), epochs, "pinned", seed=1)
    assert lru == pytest.approx(z.lru_epoch_hit_ratio(x), abs=0.03)
    assert pin == pytest.approx(z.pinned_cache_hit_ratio(x), abs=0.03)
    assert pin > lru  # the whole point: with random epochs, never evicting beats LRU for any cache smaller than the data


def test_lru_formula_values():
    assert z.lru_epoch_hit_ratio(0.0) == 0.0
    assert z.lru_epoch_hit_ratio(0.5) == pytest.approx(0.5 + 0.5 * __import__("math").log(0.5))
    assert z.lru_epoch_hit_ratio(0.5) < 0.16 < 0.5  # LRU keeps about a third of what a never-evicting cache keeps


def test_cache_larger_than_data_hits_always():
    assert z.simulate_epoch_hit_ratio(100, 100, 3, "lru") == 1.0
    assert z.lru_epoch_hit_ratio(1.0) == 1.0 and z.pinned_cache_hit_ratio(1.5) == 1.0


def test_effective_bandwidth_is_a_harmonic_mix():
    assert z.effective_read_bandwidth(0.0, 6e9, 1e9) == pytest.approx(1e9)
    assert z.effective_read_bandwidth(1.0, 6e9, 1e9) == pytest.approx(6e9)
    assert 1e9 < z.effective_read_bandwidth(0.5, 6e9, 1e9) < 3.5e9   # well below the arithmetic mean: slow bytes dominate


def test_retention():
    s = 980e9
    assert z.retained_checkpoint_bytes(s, 100_000, 500, 3, 10) == pytest.approx(23 * s)
    assert z.retained_checkpoint_bytes(s, 1000, 500, 3, 10) == pytest.approx(2 * s)   # only 2 checkpoints exist
    assert z.monthly_cost(2e12, 10.0, copies=2) == pytest.approx(40.0)


def test_alpha_beta_helpers():
    assert z.half_performance_size(0.005, 1e9) == pytest.approx(5e6)
    assert z.request_efficiency(5e6, 0.005, 1e9) == pytest.approx(0.5)      # at n_1/2 the efficiency is exactly one half
    assert z.request_efficiency(1e3, 0.005, 1e9) < 0.001 and z.request_efficiency(1e12, 0.005, 1e9) > 0.999
    assert z.in_flight(1000, 0.02) == pytest.approx(20)


def test_checkpoint_overheads():
    assert z.sync_overhead(240, 1800) == pytest.approx(240 / 1800)
    assert z.async_overhead(3, 240, 1800) == pytest.approx(3 / 1800)         # the write fits in the interval: only the snapshot blocks
    assert z.async_overhead(3, 240, 180) == pytest.approx((3 + 60) / 180)    # the write outlasts the interval: the excess blocks
    assert z.async_overhead(3, 240, 180) < z.sync_overhead(240, 180)


def test_sticky_assignment_beats_random_assignment_with_a_never_evicting_cache():
    kw = dict(dataset=40e12, nodes=32, need_per_node=3e9, backend_total=40e9, cache_per_node=30.72e12, epochs=20)
    sticky = z.epoch_times(assignment="sticky", **kw)
    rand = z.epoch_times(assignment="random", **kw)
    assert sticky[0] == pytest.approx(rand[0])                          # epoch 1 is cold for both
    assert sticky[1] == pytest.approx(40e12 / 32 / 3e9)                 # from epoch 2 the share is local: full speed
    assert all(r >= s - 1e-9 for r, s in zip(rand, sticky))
    assert rand == sorted(rand, reverse=True)                           # random assignment improves slowly but never gets worse
    assert sum(rand) > 1.5 * sum(sticky)
    with pytest.raises(ValueError):
        z.epoch_times(assignment="x", **kw)


def test_rotation_peak_and_free_space_guard():
    assert z.peak_checkpoint_bytes(980e9, 3) == pytest.approx(4 * 980e9)
    assert z.free_space_ok(1.1e12, 980e9) and not z.free_space_ok(1.0e12, 980e9)
    assert z.free_space_ok(980e9, 980e9, margin=0.0)


def test_seen_probability_and_required_hit_ratio():
    assert z.seen_probability(4, 3) == pytest.approx(0.4375)
    assert z.seen_probability(32, 1) == 0.0 and z.seen_probability(32, 2) == pytest.approx(1 / 32)
    h = z.required_hit_ratio(3e9, 6e9, 1e9)
    assert h == pytest.approx(0.8)
    assert z.effective_read_bandwidth(h, 6e9, 1e9) == pytest.approx(3e9)   # the hit ratio really reaches the target
