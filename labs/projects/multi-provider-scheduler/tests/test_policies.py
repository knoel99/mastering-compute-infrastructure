import math

import pytest

import data
import policies as P


def offers():
    return [data.Offer("od", "p", "r", "on_demand", 10.0, 64, 0.0, 5),
            data.Offer("sa", "p", "r", "spot", 4.0, 64, 0.15, 8),
            data.Offer("sb", "q", "r", "spot", 3.0, 64, 1.5, 8)]


def job(work=600, deadline=100_000, gpus=8, ckpt=3, restart=10):
    return data.Job("j", 0, gpus, work, deadline, ckpt, restart)


def free(**over):
    f = {"od": 64, "sa": 64, "sb": 64}
    f.update(over)
    return f


def test_young_daly_and_waste_formulas():
    assert P.young_daly_min(3, 100) == pytest.approx(math.sqrt(600))
    assert P.waste_fraction(24.0, 3, 100, 10) == pytest.approx(3 / 24 + (12 + 10) / 100)


def test_cheapest_picks_the_lowest_price_that_fits():
    assert P.Cheapest().choose(job(), 600, 0, offers(), free()) == "sb"
    assert P.Cheapest().choose(job(), 600, 0, offers(), free(sb=0)) == "sa"
    assert P.Cheapest().choose(job(), 600, 0, offers(), {"od": 0, "sa": 0, "sb": 0}) is None
    assert P.Cheapest().choose(job(gpus=32), 600, 0, offers(), free(sb=16, sa=16)) == "od"


def test_on_demand_only_never_returns_spot():
    assert P.OnDemandOnly().choose(job(), 600, 0, offers(), free()) == "od"
    assert P.OnDemandOnly().choose(job(), 600, 0, offers(), free(od=0)) is None
    assert P.OnDemandOnly().ckpt_interval(job(), offers()[0]) == math.inf


def test_hedged_prefers_lower_expected_cost_per_productive_hour_over_lower_price():
    o = {x.id: x for x in offers()}
    j = job()
    cost = {}
    for oid in ("sa", "sb"):
        mtbf = 60.0 / o[oid].hazard
        t = P.young_daly_min(j.ckpt_cost_min, mtbf)
        cost[oid] = o[oid].price / (1 - P.waste_fraction(t, j.ckpt_cost_min, mtbf, j.restart_cost_min))
    assert o["sb"].price < o["sa"].price and cost["sa"] < cost["sb"]  # cheaper per hour, dearer per useful hour
    assert P.Hedged().choose(j, 600, 0, offers(), free()) == "sa"


def test_hedged_deadline_guard_moves_a_tight_job_to_on_demand():
    relaxed = job(work=600, deadline=100_000)
    tight = job(work=600, deadline=640)  # 600 min of work, 40 min of slack: a spot offer's expected waste breaks it
    assert P.Hedged().choose(relaxed, 600, 0, offers(), free()) in ("sa", "sb")
    assert P.Hedged().choose(tight, 600, 0, offers(), free()) == "od"


def test_hedged_checkpoint_interval_is_young_daly():
    o = offers()
    j = job()
    assert P.Hedged().ckpt_interval(j, o[2]) == max(j.ckpt_cost_min + 1, round(math.sqrt(2 * 3 * (60 / 1.5))))
    assert P.Hedged().ckpt_interval(j, o[1]) == round(math.sqrt(2 * 3 * (60 / 0.15)))
    assert P.Hedged().ckpt_interval(j, o[0]) == math.inf
