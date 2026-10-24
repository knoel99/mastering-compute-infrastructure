"""Checkpoint interval: closed-form models and a Monte-Carlo simulator.

Notation (all times in seconds)
    delta  cost of one checkpoint that blocks the training loop (C in the course)
    mtbf   mean time between failures of the whole job (M)
    r      restart cost: detection + relaunch + checkpoint load (R)
    tau    useful compute between two checkpoints (T)

The simulated system is the one assumed by Young and Daly: the job computes for tau seconds,
then writes a checkpoint for delta seconds. A failure destroys everything since the last
*completed* checkpoint, then the job pays r seconds to restart (a failure can strike during
the restart too). Failures form a renewal process in wall-clock time.
"""
import math

import numpy as np


def young(delta, mtbf):
    """First-order optimum, Young (1974): tau = sqrt(2 * delta * M)."""
    return math.sqrt(2.0 * delta * mtbf)


def daly_first(delta, mtbf):
    """First-order optimum of the compute interval alone (checkpoint time removed)."""
    return math.sqrt(2.0 * delta * mtbf) - delta


def daly_high(delta, mtbf):
    """Higher-order estimate (Daly 2006) of the optimal compute interval, valid for delta < 2M."""
    if delta >= 2.0 * mtbf:
        return mtbf
    x = delta / (2.0 * mtbf)
    return math.sqrt(2.0 * delta * mtbf) * (1.0 + math.sqrt(x) / 3.0 + x / 9.0) - delta


def waste_first_order(tau, delta, mtbf, r):
    """Fraction of wall time not spent on useful work, first-order: delta/tau + (tau/2 + r)/M."""
    return delta / tau + (tau / 2.0 + r) / mtbf


def wall_per_work_exact(tau, delta, mtbf, r):
    """Exact expected wall time per second of useful work for exponential failures.

    E[wall] / work = M * exp(r/M) * (exp((tau+delta)/M) - 1) / tau
    """
    return mtbf * math.exp(r / mtbf) * math.expm1((tau + delta) / mtbf) / tau


def goodput_exact(tau, delta, mtbf, r):
    return 1.0 / wall_per_work_exact(tau, delta, mtbf, r)


def argmin_exact(delta, mtbf, r):
    """Numerical minimiser of the exact expected wall time (golden-section on a log grid)."""
    lo, hi = 1e-3 * mtbf, 5.0 * mtbf
    phi = (math.sqrt(5.0) - 1.0) / 2.0
    a, b = math.log(max(lo, delta * 1e-3)), math.log(hi)
    f = lambda lt: wall_per_work_exact(math.exp(lt), delta, mtbf, r)  # noqa: E731
    c, d = b - phi * (b - a), a + phi * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(120):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - phi * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + phi * (b - a)
            fd = f(d)
    return math.exp((a + b) / 2.0)


class FailureClock:
    """Renewal process of failure instants. shape=None -> exponential, else Weibull(shape)
    rescaled so that the mean inter-failure time is exactly `mtbf`."""

    def __init__(self, mtbf, seed, shape=None):
        self.rng = np.random.default_rng(seed)
        self.mtbf, self.shape = mtbf, shape
        self.scale = mtbf if shape is None else mtbf / math.gamma(1.0 + 1.0 / shape)
        self.buf, self.i, self.t = [], 0, 0.0

    def _draw(self):
        n = 4096
        x = self.rng.exponential(self.mtbf, n) if self.shape is None else self.scale * self.rng.weibull(self.shape, n)
        self.buf, self.i = x.tolist(), 0

    def next_after_last(self):
        if self.i >= len(self.buf):
            self._draw()
        self.t += self.buf[self.i]
        self.i += 1
        return self.t


def simulate(tau, delta, mtbf, r, work, seed, shape=None):
    """Return (goodput, number_of_failures) for `work` seconds of useful computation."""
    clock = FailureClock(mtbf, seed, shape)
    nxt = clock.next_after_last()
    wall = done = 0.0
    fails = 0
    while done < work:
        seg = min(tau, work - done)
        need = seg + delta
        if wall + need <= nxt:  # segment and its checkpoint complete before the next failure
            wall += need
            done += seg
            continue
        fails += 1
        wall = nxt
        while True:  # restart; another failure may strike while restarting
            nxt = clock.next_after_last()
            if nxt >= wall + r:
                wall += r
                break
            wall = nxt
    return work / wall, fails


def mean_goodput(tau, delta, mtbf, r, work, seeds, shape=None):
    """Mean and standard error of the goodput over independent seeds (common random numbers
    across tau values: the same seeds give the same failure instants)."""
    g = np.array([simulate(tau, delta, mtbf, r, work, s, shape)[0] for s in seeds])
    return float(g.mean()), float(g.std(ddof=1) / math.sqrt(len(g)))
