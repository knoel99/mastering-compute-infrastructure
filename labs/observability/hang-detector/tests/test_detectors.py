import statistics

import pytest

import detectors as D
import evaluate as E
import sim
from watch import Stagnation


def obs(t, steps=100, phase="train", alive=True, util=96.0, tensor=0.55):
    return sim.Obs(t, alive, steps, phase, util, tensor, 600.0)


# ------------------------------------------------------------------ unit behaviour
def test_step_stall_alarms_only_after_the_window_and_resets_on_progress():
    d = D.StepStall(60)
    assert [d.update(obs(t, steps=5)) for t in (0, 15, 30, 45, 60)] == [False, False, False, False, True]
    assert d.update(obs(75, steps=6)) is False


def test_step_stall_ignores_an_absent_series():
    d = D.StepStall(30)
    assert not any(d.update(obs(t, steps=None, phase=None, alive=False)) for t in range(0, 300, 15))


def test_heartbeat_sees_a_dead_process_but_not_a_spinning_one():
    d = D.Heartbeat(60)
    assert not any(d.update(obs(t, steps=7)) for t in range(0, 600, 15))             # alive, no progress: silent
    d = D.Heartbeat(60)
    assert any(d.update(obs(t, steps=None, phase=None, alive=False)) for t in range(0, 120, 15))


def test_phase_aware_gives_checkpoints_their_own_allowance():
    d = D.PhaseAware(120, allow={"ckpt": 600.0})
    ckpt = [d.update(obs(t, steps=10, phase="ckpt")) for t in range(0, 500, 15)]
    assert not any(ckpt)                                                             # 8 minutes of checkpoint: fine
    d = D.PhaseAware(120, allow={"ckpt": 600.0})
    assert any(d.update(obs(t, steps=10, phase="ckpt")) for t in range(0, 700, 15))   # 11 minutes: too long
    d = D.PhaseAware(120)
    assert any(d.update(obs(t, steps=10, phase="train")) for t in range(0, 200, 15))  # training stall: 2 minutes


def test_anyof_updates_every_member():
    a, b = D.StepStall(30), D.Heartbeat(30)
    both = D.AnyOf(a, b)
    for t in range(0, 60, 15):
        both.update(obs(t, steps=3))
    assert a.last == 3 and b.since is None


def test_wall_clock_watcher():
    w = Stagnation(3.0)
    assert [w.update(t, 5) for t in (0.0, 1.0, 2.9, 3.0)] == [False, False, False, True]
    assert w.update(3.1, 6) is False and w.update(5.0, None) is False


# ------------------------------------------------------------------ simulator
def test_simulation_is_reproducible_and_hangs_freeze_the_counter():
    a, ta = sim.simulate(7, fault="hang")
    b, tb = sim.simulate(7, fault="hang")
    assert a == b and ta == tb
    after = [o for o in a if o.t >= ta]
    assert len({o.steps for o in after}) == 1 and all(o.tensor == 0.0 and o.util > 90 for o in after)


# ------------------------------------------------------------------ what the assumptions imply (structural claims)
@pytest.fixture(scope="module")
def results():
    cfg = {"util": lambda: D.UtilLow(300), "hb": lambda: D.Heartbeat(60),
           "stall60": lambda: D.StepStall(60), "stall600": lambda: D.StepStall(600),
           "stall900": lambda: D.StepStall(900), "phase240": lambda: D.PhaseAware(240),
           "pair": lambda: D.AnyOf(D.PhaseAware(240), D.Heartbeat(60))}
    for w in (30, 120, 480):
        cfg[f"s{w}"] = (lambda w=w: D.StepStall(w))
    return E.evaluate(cfg, n_healthy=40, n_hang=40, n_crash=20)


def test_utilization_alone_is_blind_to_a_spinning_hang(results):
    assert results["util"]["hang_found_pct"] == 0            # by construction of the hang model: a hypothesis, not a measurement
    assert results["util"]["crash_found_pct"] == 100         # but it does see an idle allocation


def test_heartbeat_finds_crashes_not_hangs(results):
    assert results["hb"]["crash_found_pct"] == 100 and results["hb"]["hang_found_pct"] == 0


def test_short_windows_drown_in_checkpoint_pauses(results):
    assert results["stall60"]["healthy_alarm_pct"] >= 90


def test_window_beyond_the_longest_pause_has_no_false_alarm_but_a_long_delay(results):
    r = results["stall900"]
    assert r["healthy_alarms"] == 0 and r["hang_found_pct"] == 100
    assert 900 <= r["delay_median"] <= 900 + sim.SCRAPE_S + sim.STEP_S


def test_phase_awareness_buys_a_shorter_window_at_zero_false_alarms(results):
    assert results["phase240"]["healthy_alarms"] == 0
    assert results["phase240"]["delay_median"] < results["stall600"]["delay_median"] / 2
    assert results["pair"]["crash_found_pct"] == 100 and results["pair"]["hang_found_pct"] == 100


def test_false_alarms_fall_and_delay_grows_with_the_window(results):
    fa = [results[k]["healthy_alarms"] for k in ("s30", "s120", "s480")]
    dl = [results[k]["delay_median"] for k in ("s30", "s120", "s480")]
    assert fa == sorted(fa, reverse=True) and dl == sorted(dl)
