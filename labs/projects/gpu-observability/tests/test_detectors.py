import pytest

import detectors
from sim import ClusterSim, Fault

JOBS = {"A": ["h0", "h1"], "B": ["h2", "h3"]}
HOURS = 4 * 3600


def make_sim(seed):
    return ClusterSim(JOBS, gpus_per_host=8, seed=seed)


@pytest.mark.parametrize("make", [detectors.StalledJob, detectors.Straggler])
def test_no_false_alarm_on_healthy_runs(make):
    rate, gpu_hours = detectors.false_alarm_rate(make, make_sim, range(8), HOURS)
    assert gpu_hours == 8 * 4 * 32
    assert rate == 0.0


def test_stalled_job_detects_a_hang_within_the_expected_delay():
    fault = Fault("hang", 1800, job="A")
    delay = detectors.detection_delay(detectors.StalledJob, make_sim, fault, "A", 3600)
    assert delay is not None and delay <= 20 * 15 + 15


def test_naive_utilisation_alert_is_blind_to_a_hang():
    fault = Fault("hang", 1800, job="A")
    assert detectors.detection_delay(detectors.NaiveUtilStall, make_sim, fault, "A", 3600) is None


def test_idle_allocation_is_caught_by_both_because_utilisation_is_really_zero():
    fault = Fault("idle", 1800, job="B")
    assert detectors.detection_delay(detectors.NaiveUtilStall, make_sim, fault, "B", 3600) is not None
    assert detectors.detection_delay(detectors.StalledJob, make_sim, fault, "B", 3600) is not None


def test_straggler_is_found_quickly_and_only_that_gpu_is_flagged():
    fault = Fault("straggler", 1800, job="B", host="h3", gpu=5)
    alerts = detectors.run(detectors.Straggler(), make_sim(0), 3600, [fault])
    assert {a.key for a in alerts} == {"h3/5"}
    assert alerts[0].t - 1800 <= 8 * 15 + 15


def test_detectors_do_not_confuse_the_two_failure_modes():
    straggler = Fault("straggler", 1800, job="B", host="h3", gpu=5)
    hang = Fault("hang", 1800, job="A")
    assert detectors.run(detectors.StalledJob(), make_sim(0), 3600, [straggler]) == []
    assert detectors.run(detectors.Straggler(), make_sim(0), 3600, [hang]) == []


def test_alert_is_raised_once_per_episode():
    fault = Fault("hang", 600, job="A")
    alerts = detectors.run(detectors.StalledJob(), make_sim(0), 3600, [fault])
    assert [a.key for a in alerts] == ["A"]
