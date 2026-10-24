"""Offline detectors over simulated scrapes — TO WRITE (milestone 3). Helpers and the anti-pattern are given."""
import statistics
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Alert:
    kind: str
    key: str  # job id, or "host/gpu"
    t: float


class _Persistent:
    """Raise an alert once a condition has held for `need` consecutive scrapes; re-arm when it clears."""

    def __init__(self, kind, need):
        self.kind, self.need = kind, need
        self.run = defaultdict(int)
        self.raised = set()

    def step(self, t, flags):
        out = []
        for key, bad in flags.items():
            self.run[key] = self.run[key] + 1 if bad else 0
            if not bad:
                self.raised.discard(key)
            elif self.run[key] >= self.need and key not in self.raised:
                self.raised.add(key)
                out.append(Alert(self.kind, key, t))
        return out


def by_job(samples):
    jobs = defaultdict(list)
    for s in samples:
        if s.job:
            jobs[s.job].append(s)
    return jobs


class NaiveUtilStall:
    """ANTI-PATTERN kept for the demonstration: 'the job is stalled when its GPU utilisation is near zero'."""

    def __init__(self, util_max=5.0, scrapes=20):
        self.p = _Persistent("naive_util_stall", scrapes)
        self.util_max = util_max

    def update(self, t, samples):
        return self.p.step(t, {j: statistics.median(s.util for s in g) < self.util_max for j, g in by_job(samples).items()})


class StalledJob:
    """TO WRITE. A job is stalled when the median tensor-pipe activity of its GPUs stays below tensor_max
    (default 0.05) for `scrapes` (default 20) consecutive scrapes. update(t, samples) -> [Alert("job_stalled", job, t)]."""

    def __init__(self, tensor_max=0.05, scrapes=20):
        raise NotImplementedError

    def update(self, t, samples):
        raise NotImplementedError


class Straggler:
    """TO WRITE. Flag the GPU whose SM clock is more than z_thr (default 6) robust standard deviations
    below the median of its job, for `scrapes` (default 8) consecutive scrapes. Robust scale =
    max(1.4826 * MAD, scale_floor=5.0 MHz). update(t, samples) -> [Alert("straggler", "host/gpu", t)]."""

    def __init__(self, z_thr=6.0, scrapes=8, scale_floor=5.0):
        raise NotImplementedError

    def update(self, t, samples):
        raise NotImplementedError


def run(detector, sim, duration_s, faults=()):
    """All alerts raised while replaying sim.frames(duration_s, faults)."""
    raise NotImplementedError


def false_alarm_rate(make_detector, make_sim, seeds, duration_s):
    """(alerts per GPU-hour, GPU-hours observed) on fault-free runs, one fresh detector and sim per seed."""
    raise NotImplementedError


def detection_delay(make_detector, make_sim, fault, key, duration_s, seed=0):
    """Seconds between fault.start_s and the first alert for `key` (None if never detected)."""
    raise NotImplementedError
