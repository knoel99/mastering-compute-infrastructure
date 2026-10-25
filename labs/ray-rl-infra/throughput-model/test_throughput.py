"""Model / simulation consistency tests (lab 11.3). Simulated time only: no wall clock anywhere."""
import math

import pytest

import des
import model as M
import plan

P = dict(m=200, t_roll=2.0, t_sync=0.2, b=4, s_L=1.0)   # an illustrative loop, not a real system


def sim(n, **kw):
    args = dict(P, **kw)
    return des.simulate(n, **args)


def rel(a, b):
    return abs(a - b) / b


# ---- the closed forms themselves
def test_alpha_beta_and_broadcast():
    assert M.sync_time(1e-3, 1e9, 1e9) == pytest.approx(1.001)
    star = M.broadcast_time(1e-3, 1e9, 1e9, 8, "star")
    tree = M.broadcast_time(1e-3, 1e9, 1e9, 8, "tree")
    assert star == pytest.approx(8.001) and tree == pytest.approx(4 * 1.001)
    assert tree < star and M.broadcast_time(1e-3, 1e9, 1e9, 1, "tree") == pytest.approx(1.001)


def test_n_star_and_regimes():
    c = M.consumption_capacity(P["b"], P["m"], P["s_L"])
    assert c == pytest.approx(800.0)
    ns = M.n_star(P["m"], P["t_roll"], P["t_sync"], P["b"], P["s_L"])
    assert ns == pytest.approx(8.8)
    assert M.actors_needed(P["m"], P["t_roll"], P["t_sync"], P["b"], P["s_L"]) == 9
    below = M.throughput(8, **P)
    above = M.throughput(9, **P)
    assert below < c and above == pytest.approx(c)
    assert M.replay_ratio(8, **P) >= 1.0 > M.replay_ratio(9, **P)


def test_credits_for_lag_is_consistent_with_lag_formula():
    k = M.credits_for_lag(3.0, P["b"])
    assert k == 12
    assert M.lag_updates(40, **P, policy="credit", credits=k) <= 3.0 + 1e-9
    assert M.lag_updates(40, **P, policy="credit", credits=k + P["b"]) > 3.0


# ---- model against simulation
@pytest.mark.parametrize("n", [2, 4, 6, 8, 12, 24])
def test_throughput_matches_simulation_deterministic(n):
    assert rel(sim(n, queue_cap=8)["steps_per_s"], M.throughput(n, **P)) < 0.02


@pytest.mark.parametrize("n", [3, 6, 20])
def test_throughput_matches_simulation_with_noise(n):
    r = sim(n, queue_cap=8, dist="lognormal", cv=0.3, horizon=6000, seed=3)
    assert rel(r["steps_per_s"], M.throughput(n, **P)) < 0.06


def test_saturation_point():
    ns = M.n_star(P["m"], P["t_roll"], P["t_sync"], P["b"], P["s_L"])
    far_below = sim(int(ns) - 4, queue_cap=8)
    far_above = sim(int(ns) + 8, queue_cap=8)
    assert far_below["learner_util"] < 0.8
    assert far_above["learner_util"] > 0.98
    xs = [sim(n, queue_cap=8)["steps_per_s"] for n in range(1, 16)]
    assert all(b >= a - 1e-6 for a, b in zip(xs, xs[1:]))        # monotone in N
    assert max(xs) <= M.consumption_capacity(P["b"], P["m"], P["s_L"]) * 1.01


def test_littles_law_on_the_queue():
    for n in (6, 20):
        r = sim(n, queue_cap=8, dist="exp", horizon=8000, seed=5)
        assert rel(r["mean_queue_len"], r["arrival_rate_traj_s"] * r["mean_queue_wait_s"]) < 0.03


def test_lag_actor_bound_and_learner_bound():
    for n in (2, 4):  # clearly actor-bound
        r = sim(n, queue_cap=8, dist="lognormal", cv=0.3, horizon=8000, seed=1)
        assert abs(r["mean_lag"] - M.lag_updates(n, **P)) < 0.4
    for n in (16, 24):  # clearly learner-bound, "block" policy
        r = sim(n, queue_cap=8, dist="lognormal", cv=0.3, horizon=8000, seed=1)
        assert rel(r["mean_lag"], M.lag_updates(n, **P, policy="block", queue_cap=8)) < 0.08


def test_credits_bound_the_lag_where_blocking_does_not():
    n = 24
    blk = sim(n, queue_cap=8, policy="block", dist="lognormal", cv=0.3, horizon=8000, seed=1)
    cre = sim(n, queue_cap=8, policy="credit", credits=8, dist="lognormal", cv=0.3, horizon=8000, seed=1)
    assert cre["mean_lag"] < 0.4 * blk["mean_lag"]
    assert cre["p95_lag"] <= 2 * 8 / P["b"] + 1        # K / b = 2 batches in the loop (a statistical, not a hard, bound)
    assert rel(cre["mean_lag"], M.lag_updates(n, **P, policy="credit", credits=8)) < 0.08
    assert cre["steps_per_s"] <= M.credit_throughput_ceiling(8, P["m"], P["t_roll"], P["t_sync"]) * 1.02
    assert cre["steps_per_s"] < blk["steps_per_s"]     # the price of the bound: lost throughput
    # with enough credits the throughput comes back
    big = sim(n, queue_cap=8, policy="credit", credits=24, dist="lognormal", cv=0.3, horizon=8000, seed=1)
    assert rel(big["steps_per_s"], blk["steps_per_s"]) < 0.05


def test_credits_are_held_by_trajectories_not_by_actors():
    r = sim(12, queue_cap=16, policy="credit", credits=24, dist="lognormal", cv=0.3, horizon=8000, seed=1)
    assert rel(r["mean_lag"], M.lag_updates(12, **P, policy="credit", queue_cap=16, credits=24)) < 0.08
    assert M.lag_updates(12, **P, policy="credit", queue_cap=16, credits=24) == pytest.approx(6.0)
    assert M.lag_updates(12, **P, policy="credit", queue_cap=4, credits=24) == pytest.approx(4.0)  # N + Q = 16


def test_unbounded_queue_grows_linearly_and_lag_with_it():
    n = 16
    short = sim(n, queue_cap=None, horizon=2000)
    long = sim(n, queue_cap=None, horizon=4000)
    slope = (M.production_rate(n, P["m"], P["t_roll"], P["t_sync"]) - M.consumption_capacity(P["b"], P["m"], P["s_L"])) / P["m"]  # traj/s
    assert rel(long["queue_len_end"], slope * 4000) < 0.06
    assert long["mean_lag"] > 1.5 * short["mean_lag"]


def test_same_seed_same_result_and_different_seed_differs():
    a = sim(10, queue_cap=8, dist="exp", seed=11, horizon=1500)
    b = sim(10, queue_cap=8, dist="exp", seed=11, horizon=1500)
    c = sim(10, queue_cap=8, dist="exp", seed=12, horizon=1500)
    assert a == b and a != c


def test_plan_cli_function():
    r = plan.plan(**P, queue_cap=8, actor_price_h=1.0, learner_price_h=10.0)
    assert r["actors_needed"] == 9 and r["throughput_steps_s"] == pytest.approx(800.0)
    assert r["price_per_hour"] == pytest.approx(19.0)
    assert r["cost_per_million_steps"] == pytest.approx(19.0 / 3600 / 800 * 1e6)
    assert math.isfinite(r["lag_block"]) and r["lag_credit"] <= r["lag_block"]
    r2 = plan.plan(**P, queue_cap=8, replay_ratio=2.0)       # reuse halves the fresh-data capacity
    assert r2["actors_needed"] == 5 and r2["throughput_steps_s"] == pytest.approx(400.0)
    assert r2["learner_util"] == pytest.approx(1.0)
