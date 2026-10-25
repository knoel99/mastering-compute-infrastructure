import math

import pytest

import placement as P

SEEDS = range(60)


def pool(id="a", provider="A", price=4.0, hazard=0.0, p=1.0, startup=0.1):
    return P.Pool(id, provider, price, hazard, p, startup)


def job(**kw):
    base = dict(gpus=8, work_h=10.0, deadline_h=100.0, ckpt_gb=100.0, data_gb=0.0, ckpt_cost_h=0.1,
                restart_h=0.2, home="A")
    base.update(kw)
    return P.Job(**base)


NET = P.Network(egress_u_per_gb=0.1, gbit_per_s=10.0, efficiency=0.8)
FREE_NET = P.Network(egress_u_per_gb=0.0, gbit_per_s=10.0, efficiency=0.8)


# ---- formulas ----------------------------------------------------------------------------------------------------

def test_young_daly_exact():
    assert P.young_daly(0.05, 10.0) == pytest.approx(1.0)
    assert P.young_daly(0.1, 10.0) == pytest.approx(math.sqrt(2.0))


def test_waste_at_optimum_has_closed_form():
    c, m, r = 0.05, 8.0, 0.2
    t = P.young_daly(c, m)
    assert P.waste(t, c, m, r) == pytest.approx(math.sqrt(2 * c / m) + r / m)


def test_waste_is_minimal_near_young_daly():
    c, m, r = 0.05, 8.0, 0.2
    t = P.young_daly(c, m)
    assert P.waste(t, c, m, r) < P.waste(t / 3, c, m, r)
    assert P.waste(t, c, m, r) < P.waste(t * 3, c, m, r)


def test_price_per_useful_hour():
    j = job()
    assert P.price_per_useful_hour(pool(price=10.0, hazard=0.0), j) == 10.0
    p = pool(price=4.0, hazard=0.125)
    m = 8.0
    w = math.sqrt(2 * j.ckpt_cost_h / m) + j.restart_h / m
    assert P.price_per_useful_hour(p, j) == pytest.approx(4.0 / (1 - w))
    assert P.price_per_useful_hour(pool(hazard=50.0), j) == math.inf  # waste >= 1: never worth it


def test_transfer_hours():
    assert P.transfer_hours(112, 10, 0.8) == pytest.approx(112 * 8 / 8 / 3600)
    with pytest.raises(ValueError):
        P.transfer_hours(1, 0)


def test_move_cost_cases():
    j = job(ckpt_gb=100, data_gb=1000)
    home = frozenset(["A"])
    assert P.move_cost(j, NET, "A", "A", home) == (0.0, 0.0)
    usd, h = P.move_cost(j, NET, "A", "B", home)          # checkpoint + dataset
    assert usd == pytest.approx(1100 * 0.1) and h == pytest.approx(P.transfer_hours(1100, 10, 0.8))
    usd, h = P.move_cost(j, NET, "B", "B", frozenset(["A", "B"]))   # already there
    assert (usd, h) == (0.0, 0.0)
    usd, h = P.move_cost(j, NET, "A", "B", frozenset(["A", "B"]))   # dataset cached at B, checkpoint is not
    assert usd == pytest.approx(100 * 0.1)


# ---- common random numbers -----------------------------------------------------------------------------------------

def test_draws_are_reproducible_and_seed_dependent():
    p = pool(hazard=0.2, p=0.5)
    assert [P.available(3, p, k) for k in range(20)] == [P.available(3, p, k) for k in range(20)]
    assert [P.available(3, p, k) for k in range(40)] != [P.available(4, p, k) for k in range(40)]
    assert P.preempt_after(3, p, 1.0) == P.preempt_after(3, p, 1.0)
    assert P.preempt_after(3, pool(hazard=0), 1.0) == math.inf


def test_draw_statistics_match_parameters():
    p = pool(hazard=0.25, p=0.3)
    freq = sum(P.available(1, p, k) for k in range(6000)) / 6000
    assert freq == pytest.approx(0.3, abs=0.03)
    mean = sum(P.preempt_after(1, p, k * 0.25) for k in range(4000)) / 4000
    assert mean == pytest.approx(1 / 0.25, rel=0.1)


# ---- engine: exact timelines ---------------------------------------------------------------------------------------

def test_timeline_without_preemption_is_exact():
    p = pool(price=4.0, startup=0.1)
    r = P.simulate(job(), [p], NET, P.Stay("a"), seed=1)
    assert r["finish_h"] == pytest.approx(0.1 + 10.0)
    assert r["cost"] == pytest.approx(8 * 4.0 * 10.1)
    assert (r["moves"], r["preemptions"], r["allocations"], r["late"]) == (0, 0, 1, False)


def test_timeline_with_one_forced_preemption_is_exact():
    p = pool(price=4.0, hazard=0.1, startup=0.1)        # M = 10 h, C = 0.1 h -> T* = sqrt(2) h
    j = job(work_h=5.0)
    ts = math.sqrt(2.0)
    r = P.simulate(j, [p], NET, P.Stay("a"), seed=1, forced={1: 3.0})
    # allocation 1: 0.1 startup, chunk (ts) + ckpt 0.1 -> 1.6142 saved ts; second chunk would end at 3.0284 > 3.0
    # allocation 2: 0.1 startup + 0.2 restart = 0.3; remaining 5 - ts; two full chunks with checkpoints, last chunk alone
    rem = 5.0 - ts
    full = 2
    last = rem - full * ts
    second = 0.3 + full * (ts + 0.1) + last
    assert r["preemptions"] == 1 and r["allocations"] == 2
    assert r["finish_h"] == pytest.approx(3.0 + second)
    assert r["cost"] == pytest.approx(8 * 4.0 * (3.0 + second))


def test_preemption_during_startup_loses_nothing_and_costs_the_billed_time():
    p = pool(price=1.0, hazard=0.1, startup=0.5)
    r = P.simulate(job(work_h=2.0, gpus=1), [p], NET, P.Stay("a"), seed=1, forced={1: 0.2})
    assert r["preemptions"] == 1
    # no checkpoint to reload: no restart cost; T* = sqrt(2) h, so one checkpoint (0.1 h) before the last 0.586 h
    assert r["finish_h"] == pytest.approx(0.2 + 0.5 + 2.0 + 0.1)


def test_unavailable_pool_delays_but_does_not_bill():
    p = pool(p=0.2, price=1.0, startup=0.0)
    r = P.simulate(job(work_h=1.0, gpus=1), [p], NET, P.Stay("a"), seed=5)
    assert r["cost"] == pytest.approx(1.0)
    assert r["finish_h"] >= 1.0


def test_engine_matches_first_order_waste_model():
    c, rr, haz = 0.05, 0.1, 0.15
    p = pool(price=1.0, hazard=haz, p=1.0, startup=0.0)
    j = job(work_h=60.0, gpus=1, ckpt_cost_h=c, restart_h=rr, deadline_h=1e9)
    rs = P.run_many(j, [p], NET, P.Stay("a"), range(300))
    mean_cost = sum(r["cost"] for r in rs) / len(rs)
    predicted = j.work_h * P.price_per_useful_hour(p, j)
    assert mean_cost == pytest.approx(predicted, rel=0.15)


# ---- policies ------------------------------------------------------------------------------------------------------

POOLS = [pool("a-od", "A", 10.0, 0.0, 0.9), pool("a-spot", "A", 4.0, 0.15, 0.6, 0.15),
         pool("b-spot", "B", 3.0, 0.30, 0.8, 0.15)]


def test_stay_never_moves():
    j = job(work_h=40.0, ckpt_cost_h=0.05, restart_h=0.17)
    for r in P.run_many(j, POOLS, NET, P.Stay("a-spot"), SEEDS):
        assert r["moves"] == 0 and r["egress"] == 0


def test_cheapest_chases_the_list_price_and_pays_egress():
    j = job(work_h=40.0, data_gb=1000, ckpt_cost_h=0.05, restart_h=0.17)
    rs = P.run_many(j, POOLS, NET, P.Cheapest(), SEEDS)
    assert all(r["moves"] == 1 for r in rs)                  # one move to b-spot, then it stays there
    assert all(r["egress"] == pytest.approx((100 + 1000) * 0.1) for r in rs)


def test_first_available_falls_back_to_the_pool_that_grants_now():
    st = P.State(0.0, 40.0, "A", frozenset(["A"]), 0)
    spot = POOLS[1]
    refused = next(s for s in range(200) if not P.available(s, POOLS[2], 0) and not P.available(s, spot, 0)
                   and P.available(s, POOLS[0], 0))
    assert P.FirstAvailable().choose(job(), POOLS, NET, st, refused, 0.25).id == "a-od"
    granted = next(s for s in range(200) if P.available(s, POOLS[2], 0))
    assert P.FirstAvailable().choose(job(), POOLS, NET, st, granted, 0.25).id == "b-spot"


def test_on_demand_trap_costs_more_than_waiting_for_spot():
    # one on-demand pool and one spot pool that is often full: grabbing whatever grants now ends up on on-demand
    pools = [pool("od", "A", 10.0, 0.0, 1.0), pool("sp", "A", 3.0, 0.0, 0.3)]
    j = job(work_h=20.0, gpus=1)
    fa = P.summarize(P.run_many(j, pools, NET, P.FirstAvailable(), SEEDS))
    st = P.summarize(P.run_many(j, pools, NET, P.Stay("sp"), SEEDS))
    assert fa["cost"] > st["cost"] * 1.5
    assert fa["finish_h"] < st["finish_h"]                   # ...but it finishes sooner: that is the trade


def test_aware_does_not_move_when_the_data_is_too_heavy():
    heavy = job(work_h=40.0, data_gb=500_000, ckpt_cost_h=0.05, restart_h=0.17)
    for r in P.run_many(heavy, POOLS, NET, P.Aware(), SEEDS):
        assert r["moves"] == 0


def test_aware_moves_at_once_when_moving_is_free_and_the_other_pool_is_much_cheaper():
    pools = [pool("a", "A", 10.0, 0.0, 1.0), pool("b", "B", 1.0, 0.0, 1.0)]
    r = P.simulate(job(), pools, FREE_NET, P.Aware(), seed=0)
    assert r["moves"] == 1
    assert r["cost"] == pytest.approx(8 * 1.0 * (10.0 + 0.1))


def test_aware_equals_cheapest_when_nothing_else_differs():
    pools = [pool("a", "A", 5.0, 0.0, 1.0), pool("b", "B", 3.0, 0.0, 1.0)]
    j = job(ckpt_gb=0.0, data_gb=0.0)
    a = P.run_many(j, pools, FREE_NET, P.Aware(0.0), range(10))
    c = P.run_many(j, pools, FREE_NET, P.Cheapest(), range(10))
    assert all(r["moves"] == 1 for r in c)
    assert P.paired_diff(a, c)[0] == pytest.approx(0.0)


def test_time_value_makes_aware_prefer_the_reliable_pool():
    pools = [pool("od", "A", 10.0, 0.0, 1.0), pool("sp", "A", 5.0, 0.2, 1.0)]
    j = job(work_h=40.0, ckpt_cost_h=0.1, restart_h=0.3)
    st = P.State(0.0, 40.0, "A", frozenset(["A"]), 0)
    assert P.Aware(0.0).choose(j, pools, NET, st, 0, 0.25).id == "sp"
    assert P.Aware(1000.0).choose(j, pools, NET, st, 0, 0.25).id == "od"


def test_aware_score_is_infinite_when_waste_reaches_one():
    bad = pool("bad", "A", 1.0, 80.0, 1.0)
    st = P.State(0.0, 10.0, "A", frozenset(["A"]), 0)
    assert P.Aware().score(job(), bad, NET, st, 0, 0.25) == math.inf


# ---- comparison ----------------------------------------------------------------------------------------------------

def test_paired_diff_of_a_run_with_itself_is_zero():
    rs = P.run_many(job(), POOLS, NET, P.Stay("a-od"), range(10))
    mean, half = P.paired_diff(rs, rs)
    assert mean == 0 and half == 0


def test_paired_diff_known_values():
    a = [{"cost": 10.0}, {"cost": 12.0}, {"cost": 14.0}, {"cost": 16.0}]
    b = [{"cost": 9.0}, {"cost": 10.0}, {"cost": 11.0}, {"cost": 12.0}]
    mean, half = P.paired_diff(a, b)           # differences 1, 2, 3, 4: mean 2.5, sd sqrt(5/3)
    assert mean == pytest.approx(2.5)
    assert half == pytest.approx(1.96 * math.sqrt(5 / 3) / 2)
    assert P.paired_diff(a[:1], b[:1])[1] == math.inf


def test_summarize_fields():
    s = P.summarize(P.run_many(job(), POOLS, NET, P.Stay("a-od"), range(5)))
    assert set(s) == {"cost", "finish_h", "late", "moves", "preemptions", "egress"}
    assert s["moves"] == 0 and 0 <= s["late"] <= 1
