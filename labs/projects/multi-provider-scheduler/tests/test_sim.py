import math

import pytest

import data
import policies
import sim


class Fixed:
    """Toy policy: always the given offer, a fixed checkpoint interval."""

    def __init__(self, offer_id, interval=60):
        self.offer_id, self.interval = offer_id, interval

    def choose(self, job, remaining_min, now, offers, free):
        return self.offer_id if free[self.offer_id] >= job.gpus else None

    def ckpt_interval(self, job, offer):
        return self.interval


class Recorder(Fixed):
    """Fixed, and remembers what the engine offered: (now, remaining work) at each call."""

    def __init__(self, *args):
        super().__init__(*args)
        self.calls = []

    def choose(self, job, remaining_min, now, offers, free):
        self.calls.append((now, remaining_min))
        return super().choose(job, remaining_min, now, offers, free)


class Blind(Fixed):
    """Ignores `free`: the engine itself must refuse an allocation that does not fit."""

    def choose(self, job, remaining_min, now, offers, free):
        return self.offer_id


def toy_offer(price=6.0, capacity=64, hazard=0.0, startup=10):
    return data.Offer("o", "p", "r", "spot" if hazard else "on_demand", price, capacity, hazard, startup)


def toy_job(jid="j", arrival=0, gpus=8, work=300, deadline=10_000, ckpt=5, restart=0):
    return data.Job(jid, arrival, gpus, work, deadline, ckpt, restart)


def test_timeline_without_interruption():
    # startup 10, then 5 chunks of 60 with 4 checkpoints of 5: 10 + 300 + 20 = 330
    r = sim.simulate([toy_offer()], [toy_job(arrival=7)], Fixed("o", 60))
    assert r.jobs["j"]["finish"] == 7 + 330
    assert r.jobs["j"]["billed"] == 330 and r.jobs["j"]["interruptions"] == 0
    assert r.jobs["j"]["ckpt"] == 20  # 4 checkpoints of 5 minutes
    assert r.cost == pytest.approx(330 * 8 * 6.0 / 60)


def test_no_checkpoint_when_interval_is_infinite():
    r = sim.simulate([toy_offer()], [toy_job()], Fixed("o", math.inf))
    assert r.jobs["j"]["finish"] == 310 and r.jobs["j"]["ckpt"] == 0


def test_forced_interruption_loses_unsaved_progress_and_replaces_immediately():
    # interrupted after 100 billed minutes: chunk 1 saved at minute 10+65=75, 25 minutes of chunk 2 are lost.
    # second allocation: startup 10, remaining 240 = 4 chunks, 3 checkpoints -> 10 + 255; total finish = 100 + 265
    # (the second allocation is forced too, so that the test does not depend on the random draw)
    forced = {("j", 1): 100, ("j", 2): 10**6}
    pol = Recorder("o", 60)
    r = sim.simulate([toy_offer(hazard=0.2)], [toy_job(restart=0)], pol, forced=forced)
    j = r.jobs["j"]
    assert j["finish"] == 365 and j["interruptions"] == 1 and j["lost"] == 25
    assert pol.calls[0] == (0, 300) and (100, 240) in pol.calls  # offered again the SAME minute, 60 minutes saved
    assert j["billed"] == 365 and r.cost == pytest.approx(365 * 8 * 6.0 / 60)


def test_interruption_during_a_checkpoint_saves_nothing_of_that_chunk():
    # billed minute 72 falls inside the first checkpoint (minutes 70 to 75): all 60 minutes of chunk 1 are lost.
    # second allocation: startup 10 + 5 chunks of 60 + 4 checkpoints of 5 = 330; finish = 72 + 330
    forced = {("j", 1): 72, ("j", 2): 10**6}
    r = sim.simulate([toy_offer(hazard=0.2)], [toy_job(restart=0)], Fixed("o", 60), forced=forced)
    assert r.jobs["j"]["lost"] == 60 and r.jobs["j"]["finish"] == 72 + 330


def test_restart_cost_is_paid_only_after_an_interruption():
    forced = {("j", 1): 100, ("j", 2): 10**6}
    r = sim.simulate([toy_offer(hazard=0.2)], [toy_job(restart=7)], Fixed("o", 60), forced=forced)
    assert r.jobs["j"]["finish"] == 365 + 7 and r.jobs["j"]["lost"] == 25


def test_job_waits_when_capacity_is_full():
    jobs = [toy_job("a", 0, 8, 60), toy_job("b", 0, 8, 60)]
    r = sim.simulate([toy_offer(capacity=8)], jobs, Fixed("o", math.inf))
    assert r.jobs["a"]["finish"] == 70
    assert r.jobs["b"]["first_alloc"] == 70 and r.jobs["b"]["finish"] == 140
    assert r.max_concurrent["o"] == 8
    r = sim.simulate([toy_offer(capacity=8)], jobs, Blind("o", math.inf))  # a policy that ignores `free`
    assert r.jobs["b"]["first_alloc"] == 70 and r.max_concurrent["o"] == 8


def test_deadline_miss_and_unfinished_are_reported():
    r = sim.simulate([toy_offer()], [toy_job(deadline=100)], Fixed("o", math.inf))
    assert r.deadline_misses == 1 and r.unfinished == 0
    r2 = sim.simulate([toy_offer()], [toy_job(work=5000)], Fixed("o", math.inf), horizon_min=100)
    assert r2.unfinished == 1 and r2.deadline_misses == 1
    assert r2.jobs["j"]["billed"] == 100 and r2.cost == pytest.approx(100 * 8 * 6.0 / 60)  # billed up to the horizon


def test_interruption_luck_is_common_to_all_policies_and_monotone_in_hazard():
    j = toy_job()
    a = sim._fail_after(3, j, 1, 0.5)
    assert a == sim._fail_after(3, j, 1, 0.5)
    assert sim._fail_after(3, j, 1, 1.0) <= a
    assert sim._fail_after(3, j, 1, 0.0) == math.inf
    assert sim._fail_after(3, j, 2, 0.5) != a  # a new allocation number is a new draw
    assert sim._fail_after(4, j, 1, 0.5) != a  # a new seed is a new draw
    # engine level: job "j" meets the same luck alone and in a crowd (other jobs on the same offer must not
    # shift its random draws), which a single global generator would break
    spot = toy_offer(hazard=0.5)
    alone = sim.simulate([spot], [j], Fixed("o", 60), seed=3).jobs["j"]
    crowd = sim.simulate([spot], [toy_job("a", 0, 8, 900), j, toy_job("z", 5, 8, 400)], Fixed("o", 60), seed=3).jobs["j"]
    assert alone["interruptions"] >= 1
    assert (alone["interruptions"], alone["lost"], alone["finish"]) == (crowd["interruptions"], crowd["lost"], crowd["finish"])


@pytest.mark.parametrize("make", [policies.Cheapest, policies.OnDemandOnly, policies.Hedged])
def test_capacity_and_cost_accounting_hold_on_the_default_scenario(make):
    offers = data.default_offers()
    r = sim.simulate(offers, data.make_jobs(30, seed=1), make(), seed=1)
    for o in offers:
        assert r.max_concurrent[o.id] <= o.capacity
    ledger_cost = sum((end - start) * gpus * price / 60.0 for _, _, start, end, gpus, price in r.ledger)
    assert r.cost == pytest.approx(ledger_cost)
    assert r.cost == pytest.approx(sum(v["cost"] for v in r.jobs.values()))


def test_same_seed_same_result_different_seed_different_result():
    offers, jobs = data.default_offers(), data.make_jobs(20, seed=2)
    a = sim.simulate(offers, jobs, policies.Cheapest(), seed=5)
    assert a.cost == sim.simulate(offers, jobs, policies.Cheapest(), seed=5).cost
    assert a.cost != sim.simulate(offers, jobs, policies.Cheapest(), seed=6).cost
