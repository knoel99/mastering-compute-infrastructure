"""Tests for lab 11.2. Deterministic parts use exact or tight checks; the Ray parts are structural."""
import numpy as np
import pytest

import loop_ray
import loop_sim
from learner import Learner
from replay import ReplayBuffer
from toy_env import Corridor, policy_probs, rollout

ENV = Corridor(length=16, horizon=60, slip=0.1)
RANDOM = ENV.expected_return(np.zeros((16, 2)))
OPT = ENV.expected_return(np.tile([-30.0, 30.0], (16, 1)))


# ---------------------------------------------------------------- environment
def test_exact_return_matches_monte_carlo():
    theta = np.zeros((16, 2))
    theta[:, 1] = 0.5
    rng = np.random.default_rng(0)
    tr = rollout(ENV, theta, 0, rng, n_traj=4000)
    mc = np.mean([t["r"].sum() for t in tr])
    assert mc == pytest.approx(ENV.expected_return(theta), abs=0.03)


def test_rollout_records_behaviour_probabilities_and_is_seeded():
    theta = np.random.default_rng(1).standard_normal((16, 2))
    a = rollout(ENV, theta, 7, np.random.default_rng(5), n_traj=2)
    b = rollout(ENV, theta, 7, np.random.default_rng(5), n_traj=2)
    for x, y in zip(a, b):
        assert np.array_equal(x["s"], y["s"]) and np.array_equal(x["a"], y["a"])
    t = a[0]
    assert np.allclose(t["mu"], policy_probs(theta)[t["s"], t["a"]])
    assert t["version"] == 7 and t["n"] == len(t["s"])


# ---------------------------------------------------------------- replay buffer
def test_replay_buffer_fifo_capacity_and_ages():
    buf = ReplayBuffer(3)
    for v in range(5):
        buf.add({"version": v})
    assert len(buf) == 3 and buf.inserted == 5
    assert [t["version"] for t in buf.items] == [2, 3, 4]
    assert buf.ages_in_versions(10) == [8, 7, 6]
    assert [t["version"] for t in buf.pop_oldest(2)] == [2, 3] and len(buf) == 1
    with pytest.raises(ValueError):
        ReplayBuffer(0)
    with pytest.raises(ValueError):
        ReplayBuffer(2).sample(np.random.default_rng(0), 1)


def test_replay_sampling_is_uniform_and_seeded():
    buf = ReplayBuffer(10)
    for v in range(10):
        buf.add({"version": v})
    a = [t["version"] for t in buf.sample(np.random.default_rng(3), 5000)]
    b = [t["version"] for t in buf.sample(np.random.default_rng(3), 5000)]
    assert a == b
    counts = np.bincount(a, minlength=10) / 5000
    assert np.all(np.abs(counts - 0.1) < 0.02)
    assert np.mean(a) == pytest.approx(4.5, abs=0.15)   # mean age of a full buffer ~ (capacity-1)/2


# ---------------------------------------------------------------- learner
def test_gradient_step_improves_expected_return_on_policy():
    learner = Learner(16, lr=1.0)
    batch = rollout(ENV, learner.theta, 0, np.random.default_rng(0), n_traj=600)
    before = ENV.expected_return(learner.theta)
    learner.update(batch)
    assert ENV.expected_return(learner.theta) > before + 0.02
    assert learner.version == 1


def test_correction_is_neutral_on_policy_and_clips_the_ratio_at_one():
    theta = np.random.default_rng(2).standard_normal((16, 2))
    batch = rollout(ENV, theta, 0, np.random.default_rng(1), n_traj=20)
    naive, fixed = Learner(16, correct=False), Learner(16, correct=True)
    naive.theta, fixed.theta = theta.copy(), theta.copy()
    g1, _ = naive.gradient(batch)
    g2, _ = fixed.gradient(batch)
    assert np.allclose(g1, g2)                       # pi == mu -> rho == 1 everywhere


def test_importance_weight_is_min_of_one_and_pi_over_mu():
    one_step = lambda mu: [{"s": np.array([0]), "a": np.array([1]), "r": np.array([1.0]),
                            "mu": np.array([mu]), "version": 0, "n": 1}]
    naive, fixed = Learner(4, correct=False), Learner(4, correct=True)   # theta = 0 -> pi(1|0) = 0.5
    g_naive, _ = naive.gradient(one_step(1.0))
    g_half, _ = fixed.gradient(one_step(1.0))        # pi / mu = 0.5 -> weight 0.5
    g_clip, _ = fixed.gradient(one_step(0.1))        # pi / mu = 5   -> clipped to 1
    assert np.allclose(g_half, 0.5 * g_naive)
    assert np.allclose(g_clip, g_naive)


# ---------------------------------------------------------------- controlled-lag simulation
def test_simulation_is_reproducible_from_a_seed():
    a = loop_sim.run(8, True, updates=40, b=4, seed=3, env=ENV)
    b = loop_sim.run(8, True, updates=40, b=4, seed=3, env=ENV)
    c = loop_sim.run(8, True, updates=40, b=4, seed=4, env=ENV)
    assert a["curve"] == b["curve"] and np.array_equal(a["theta"], b["theta"])
    assert a["curve"] != c["curve"]


def test_simulated_lag_is_exactly_the_configured_lag():
    r = loop_sim.run(5, False, updates=30, b=3, seed=0, env=ENV)
    per_update = np.array(r["lags"]).reshape(30, 3)
    assert np.array_equal(per_update[:, 0], np.minimum(np.arange(30), 5))


def test_no_lag_means_the_correction_changes_nothing():
    a = loop_sim.run(0, False, updates=30, b=4, seed=1, env=ENV)
    b = loop_sim.run(0, True, updates=30, b=4, seed=1, env=ENV)
    assert np.allclose(a["theta"], b["theta"])


def test_on_policy_learning_reaches_most_of_the_optimum():
    r = loop_sim.run(0, True, updates=120, b=4, seed=0, env=ENV)
    assert r["final"] > RANDOM + 0.9 * (OPT - RANDOM)


def test_staleness_hurts_without_correction_and_correction_helps():
    seeds = range(4)
    naive = np.mean([loop_sim.run(128, False, updates=400, b=4, seed=s, env=ENV)["final"] for s in seeds])
    fixed = np.mean([loop_sim.run(128, True, updates=400, b=4, seed=s, env=ENV)["final"] for s in seeds])
    assert fixed > naive + 0.1                       # this holds for THIS toy and these settings
    assert fixed > RANDOM + 0.8 * (OPT - RANDOM)


# ---------------------------------------------------------------- real Ray actors (structural only)
def test_ray_queue_loop_learns_and_measures_staleness(ray_ctx):
    r = loop_ray.run_ray(n_actors=4, updates=60, mode="queue", step_cost_s=2e-4, update_cost_s=0.005)
    assert r["actors_seen"] == [0, 1, 2, 3]
    assert r["trajectories"] >= 60 * 4 and r["steps"] > 0
    assert min(r["lags"]) >= 0 and r["max_lag"] >= r["mean_lag"] >= 0
    assert r["final_return"] > RANDOM + 0.5 * (OPT - RANDOM)
    assert 0.0 <= r["learner_wait_frac"] <= 1.0


def test_ray_credits_bound_staleness_before_the_rollout(ray_ctx):
    kw = dict(n_actors=12, updates=50, mode="queue", step_cost_s=2e-4, update_cost_s=0.02)
    free = loop_ray.run_ray(credits=None, **kw)
    capped = loop_ray.run_ray(credits=4, **kw)       # K = b: about one batch alive at a time
    assert capped["mean_lag"] < 0.6 * free["mean_lag"]
    assert capped["mean_lag"] < 2.0


def test_ray_replay_age_follows_buffer_size_over_fresh_rate(ray_ctx):
    r = loop_ray.run_ray(n_actors=4, updates=80, mode="replay", replay_ratio=1.0, replay_capacity=64,
                         step_cost_s=2e-4)
    predicted = (64 / 2) / 4        # half the buffer, divided by the 4 fresh trajectories per update
    assert 0.5 * predicted < r["mean_lag"] < 1.5 * predicted
