"""Offline detectors over simulated scrapes, and their evaluation (false alarms, detection delay)."""
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
        """flags: {key: bool} for this scrape."""
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
    """A job is stalled when the median tensor-pipe activity of its GPUs stays below tensor_max."""

    def __init__(self, tensor_max=0.05, scrapes=20):
        self.p = _Persistent("job_stalled", scrapes)
        self.tensor_max = tensor_max

    def update(self, t, samples):
        return self.p.step(t, {j: statistics.median(s.tensor for s in g) < self.tensor_max for j, g in by_job(samples).items()})


class Straggler:
    """A GPU is a straggler when its SM clock is z_thr robust standard deviations below its job's median."""

    def __init__(self, z_thr=6.0, scrapes=8, scale_floor=5.0):
        self.p = _Persistent("straggler", scrapes)
        self.z_thr, self.floor = z_thr, scale_floor

    def update(self, t, samples):
        flags = {}
        for job, group in by_job(samples).items():
            clocks = [s.sm_clock for s in group]
            med = statistics.median(clocks)
            mad = statistics.median(abs(c - med) for c in clocks)
            scale = max(1.4826 * mad, self.floor)  # the floor keeps a quiet fleet from producing huge z-scores
            for s in group:
                flags[f"{s.host}/{s.gpu}"] = (s.sm_clock - med) / scale < -self.z_thr
        return self.p.step(t, flags)


def run(detector, sim, duration_s, faults=()):
    alerts = []
    for t, frame in sim.frames(duration_s, faults):
        alerts += detector.update(t, frame)
    return alerts


def false_alarm_rate(make_detector, make_sim, seeds, duration_s):
    """Alerts per GPU-hour on fault-free runs. Zero alerts only bounds the rate: about 3/GPU-hours at 95 %."""
    n_alerts = gpu_hours = 0
    for seed in seeds:
        sim = make_sim(seed)
        n_gpus = sum(len(h) for h in sim.jobs.values()) * sim.gpus
        n_alerts += len(run(make_detector(), sim, duration_s))
        gpu_hours += n_gpus * duration_s / 3600.0
    return n_alerts / gpu_hours, gpu_hours


def detection_delay(make_detector, make_sim, fault, key, duration_s, seed=0):
    """Seconds between the fault start and the first alert for `key`; None when never detected."""
    hits = [a for a in run(make_detector(), make_sim(seed), duration_s, [fault]) if a.key == key and a.t >= fault.start_s]
    return None if not hits else hits[0].t - fault.start_s
