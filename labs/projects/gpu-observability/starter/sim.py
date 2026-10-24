"""Synthetic GPU cluster telemetry.

ALL VALUES ARE ILLUSTRATIVE: they are not measurements of real hardware. The hang model encodes a
commonly reported signature (see the project page): a stuck collective keeps kernels spinning, so the
utilisation stays high while the tensor pipe is idle and the power drops. Validate it on real GPUs.
"""
import random
from dataclasses import dataclass

MODEL = "SIM-GPU 80GB"
BUSY = {"util": 96.0, "power": 620.0, "sm_clock": 1980.0, "temp": 62.0, "tensor": 0.55}
IDLE = {"util": 0.0, "power": 70.0, "sm_clock": 345.0, "temp": 38.0, "tensor": 0.0}
JITTER = {"util": 1.5, "power": 20.0, "sm_clock": 10.0, "temp": 1.5, "tensor": 0.02}


@dataclass(frozen=True)
class Sample:
    t: float
    host: str
    gpu: int
    job: str  # "" when the GPU is not allocated
    util: float
    power: float
    sm_clock: float
    temp: float
    tensor: float
    xid: int


@dataclass(frozen=True)
class Fault:
    kind: str  # hang | idle | straggler | xid
    start_s: float
    job: str = ""
    host: str = ""
    gpu: int = -1
    code: int = 79  # xid only


class ClusterSim:
    """jobs maps a job id to the hosts it spans; every host has gpus_per_host GPUs, all allocated to its job."""

    def __init__(self, jobs, gpus_per_host=8, seed=0, scrape_s=15.0):
        self.jobs, self.gpus, self.scrape_s = jobs, gpus_per_host, scrape_s
        self.rng = random.Random(seed)

    def _noise(self, key, mean):
        v = self.rng.gauss(mean, JITTER[key])
        return min(100.0, max(0.0, v)) if key == "util" else max(0.0, v)

    def _sample(self, t, job, host, gpu, faults):
        level = dict(BUSY)
        xid = 0
        active = [f for f in faults if t >= f.start_s]
        for f in active:
            if f.kind == "hang" and f.job == job:
                level.update(util=98.0, power=250.0, tensor=0.0)
            elif f.kind == "idle" and f.job == job:
                level.update(IDLE)
            elif f.kind == "straggler" and f.job == job:
                level.update(tensor=BUSY["tensor"] * 0.6, power=BUSY["power"] * 0.9)
                if (f.host, f.gpu) == (host, gpu):
                    level.update(sm_clock=BUSY["sm_clock"] * 0.6, temp=84.0, power=BUSY["power"] * 0.8)
            elif f.kind == "xid" and (f.host, f.gpu) == (host, gpu):
                xid = f.code
        s = {k: self._noise(k, v) for k, v in level.items()}
        return Sample(t, host, gpu, job, s["util"], s["power"], s["sm_clock"], s["temp"], s["tensor"], xid)

    def frames(self, duration_s, faults=()):
        """Yield (t, [Sample]) every scrape_s seconds."""
        t = 0.0
        while t <= duration_s:
            frame = [self._sample(t, job, host, g, faults)
                     for job, hosts in self.jobs.items() for host in hosts for g in range(self.gpus)]
            yield t, frame
            t += self.scrape_s
