"""Simulated training-job telemetry, one observation per scrape (default 15 s).

EVERYTHING HERE IS ASSUMED, NOT MEASURED. The pause distributions (checkpoint, evaluation, data stall) are
choices made for this lab; the hang signature (utilization stays high, tensor pipe idle, heartbeat thread alive)
is the hypothesis used by the course, plausible (a communication kernel that spins while waiting for peers) but neither sourced nor measured by the author on a GPU.
The lab shows what such assumptions imply for a detector; measure YOUR pauses before copying a threshold.
"""
import random
from dataclasses import dataclass
from typing import Optional

SCRAPE_S = 15.0
STEP_S = 2.0           # seconds per optimizer step while training
CKPT_EVERY_S = 1800.0  # checkpoint cadence
EVAL_EVERY_S = 7200.0
STALL_RATE = 1 / 43200  # data stalls: one per 12 h on average


@dataclass(frozen=True)
class Obs:
    t: float
    alive: bool              # the trainer's heartbeat thread answers
    steps: Optional[int]     # train_steps_total; None when the series is absent (process gone)
    phase: Optional[str]     # train | ckpt | eval ; None when absent
    util: float              # DCGM_FI_DEV_GPU_UTIL, percent
    tensor: float            # DCGM_FI_PROF_PIPE_TENSOR_ACTIVE, ratio
    power: float             # DCGM_FI_DEV_POWER_USAGE, watts


def pauses(rng, horizon_s):
    """Non-training intervals (start, end, kind), sorted, without overlap."""
    iv = []
    t = rng.uniform(300, CKPT_EVERY_S)
    while t < horizon_s:
        d = rng.uniform(30, 90) if rng.random() < 0.9 else rng.uniform(120, 420)  # 10 % slow checkpoints
        iv.append((t, t + d, "ckpt"))
        t += CKPT_EVERY_S
    t = rng.uniform(1800, EVAL_EVERY_S)
    while t < horizon_s:
        iv.append((t, t + rng.uniform(120, 300), "eval"))
        t += EVAL_EVERY_S
    t = 0.0
    while True:
        t += rng.expovariate(STALL_RATE)
        if t >= horizon_s:
            break
        iv.append((t, t + rng.uniform(20, 200), "data_stall"))
    iv.sort()
    out = []
    for s, e, k in iv:
        if not out or s >= out[-1][1]:
            out.append((s, e, k))
    return out


def simulate(seed, hours=6.0, fault=None, scrape_s=SCRAPE_S):
    """Return (observations, fault_time_s). fault: None | 'hang' | 'crash'."""
    rng = random.Random(seed)
    horizon = hours * 3600.0
    iv = pauses(rng, horizon)
    step_s = STEP_S * rng.uniform(0.95, 1.05)
    t_fault = None
    if fault:
        t_fault = rng.uniform(1800, horizon - 1800)
        for s, e, _ in iv:                      # a hang strikes inside the training loop, not inside a pause
            if s <= t_fault < e:
                t_fault = e
    def train_time(t):
        t = min(t, t_fault) if (fault == "hang" and t_fault is not None) else t
        paused = sum(max(0.0, min(t, e) - s) for s, e, _ in iv)
        return t - paused
    def noise(mean, sd, lo=0.0, hi=None):
        v = max(lo, rng.gauss(mean, sd))
        return min(v, hi) if hi is not None else v
    obs, t = [], 0.0
    while t <= horizon:
        if fault == "crash" and t >= t_fault:
            obs.append(Obs(t, False, None, None, noise(0.3, 0.3), 0.0, noise(70, 3)))
        elif fault == "hang" and t >= t_fault:
            obs.append(Obs(t, True, int(train_time(t) / step_s), "train", noise(98, 1, hi=100), 0.0, noise(250, 15)))
        else:
            kind = next((k for s, e, k in iv if s <= t < e), "train")
            steps = int(train_time(t) / step_s)
            if kind == "ckpt":
                o = Obs(t, True, steps, "ckpt", noise(8, 3, hi=100), 0.0, noise(180, 20))
            elif kind == "eval":
                o = Obs(t, True, steps, "eval", noise(85, 5, hi=100), noise(0.35, 0.03), noise(480, 30))
            elif kind == "data_stall":
                o = Obs(t, True, steps, "train", noise(5, 3, hi=100), 0.0, noise(150, 15))
            else:
                o = Obs(t, True, steps, "train", noise(96, 1.5, hi=100), noise(0.55, 0.02), noise(620, 20))
            obs.append(o)
        t += scrape_s
    return obs, t_fault
