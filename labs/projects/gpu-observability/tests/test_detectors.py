import pytest

import detectors
from sim import ClusterSim, Fault, Sample

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
    # the fault starts on a scrape, so the delay is exactly (k - 1) intervals for a persistence of k = 20
    assert delay == (20 - 1) * 15


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
    assert alerts[0].t - 1800 == (8 - 1) * 15  # persistence k = 8: (k - 1) intervals when the fault starts on a scrape


def test_detectors_do_not_confuse_the_two_failure_modes():
    straggler = Fault("straggler", 1800, job="B", host="h3", gpu=5)
    hang = Fault("hang", 1800, job="A")
    assert detectors.run(detectors.StalledJob(), make_sim(0), 3600, [straggler]) == []
    assert detectors.run(detectors.Straggler(), make_sim(0), 3600, [hang]) == []


def test_alert_is_raised_once_per_episode():
    fault = Fault("hang", 600, job="A")
    alerts = detectors.run(detectors.StalledJob(), make_sim(0), 3600, [fault])
    assert [a.key for a in alerts] == ["A"]


# --- hand-built telemetry: each test pins one property of the robust statistics or of the bookkeeping ---

class Script:
    """A scripted telemetry source with the interface of ClusterSim.frames()."""

    def __init__(self, frames):
        self._frames = frames

    def frames(self, duration_s, faults=()):
        return iter(self._frames)


def sample(host, gpu, t, clock=1980.0, tensor=0.55, job="A"):
    return Sample(t, host, gpu, job, 96.0, 620.0, clock, 62.0, tensor, 0)


def straggler_keys(clocks, scrapes=3):
    frames = [(i * 15.0, [sample(f"h{g // 8}", g % 8, i * 15.0, clock=c) for g, c in enumerate(clocks)])
              for i in range(scrapes)]
    return {a.key for a in detectors.run(detectors.Straggler(scrapes=scrapes), Script(frames), 15.0 * scrapes)}


def test_stalled_job_is_decided_by_the_median_gpu_not_the_mean():
    # 5 of 8 GPUs idle, 3 busy: the median activity is 0 although the mean (0.34) is far above the threshold
    def build(t):
        return [sample("h0", g, t, tensor=0.0 if g < 5 else 0.9) for g in range(8)]

    frames = [(i * 15.0, build(i * 15.0)) for i in range(4)]
    alerts = detectors.run(detectors.StalledJob(scrapes=3), Script(frames), 45)
    assert [(a.kind, a.key) for a in alerts] == [("job_stalled", "A")]


def test_stalled_job_alerts_again_after_it_recovered():
    pattern = [0.0] * 3 + [0.55] + [0.0] * 3  # stalled, one healthy scrape, stalled again
    frames = [(i * 15.0, [sample("h0", g, i * 15.0, tensor=v) for g in range(2)]) for i, v in enumerate(pattern)]
    alerts = detectors.run(detectors.StalledJob(scrapes=3), Script(frames), 90)
    assert [a.t for a in alerts] == [30.0, 90.0]


def test_straggler_ignores_a_gpu_that_is_faster_than_its_job():
    assert straggler_keys([1980.0] * 15 + [3000.0]) == set()


def test_straggler_scale_floor_keeps_a_quiet_job_from_alarming():
    # all clocks equal: the MAD is 0, the scale is the 5 MHz floor; 20 MHz below is z = -4, 40 MHz below is z = -8
    assert straggler_keys([1980.0] * 15 + [1960.0]) == set()
    assert straggler_keys([1980.0] * 15 + [1940.0]) == {"h1/7"}


def test_straggler_scale_is_1_4826_times_the_mad():
    # median 1980, MAD 5, scale = 1.4826 x 5 = 7.41 MHz: 40 MHz below is z = -5.4 (quiet), 50 MHz below is z = -6.7
    base = [1980.0] * 5 + [1970.0] * 2 + [1990.0] * 2
    assert straggler_keys(base + [1940.0]) == set()
    assert straggler_keys(base + [1930.0]) == {"h1/1"}


def test_straggler_is_measured_against_the_median_not_the_mean():
    # 4 of 10 GPUs are slow: the median is still the healthy clock, so exactly those 4 are flagged
    assert straggler_keys([1980.0] * 6 + [1000.0] * 4) == {"h0/6", "h0/7", "h1/0", "h1/1"}


def test_detection_delay_counts_from_the_fault_not_from_an_earlier_alert():
    def make_sim(seed):  # job A is stalled at the start, recovers at t = 60 and stalls again at the fault (t = 300)
        frames = []
        for i in range(40):
            t = i * 15.0
            stalled = t < 60 or t >= 300
            frames.append((t, [sample("h0", g, t, tensor=0.0 if stalled else 0.55) for g in range(2)]))
        return Script(frames)

    delay = detectors.detection_delay(lambda: detectors.StalledJob(scrapes=3), make_sim, Fault("hang", 300, job="A"), "A", 600)
    assert delay == 2 * 15
