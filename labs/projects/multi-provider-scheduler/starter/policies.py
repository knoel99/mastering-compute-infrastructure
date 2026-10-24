"""Placement policies — TO WRITE (milestone 2). A policy answers where to run a waiting job and how often to checkpoint.

Interface used by sim.simulate:
    policy.choose(job, remaining_min, now, offers, free) -> offer id, or None to keep waiting
        `free` maps offer id -> free GPUs; an offer without room for job.gpus is not eligible.
    policy.ckpt_interval(job, offer) -> minutes of progress between checkpoints, math.inf for none
"""
import math  # noqa: F401


def young_daly_min(ckpt_cost_min, mtbf_min):
    """T* = sqrt(2 C M) (see project 3)."""
    raise NotImplementedError


def waste_fraction(interval_min, ckpt_cost_min, mtbf_min, restart_min):
    """W(T) = C/T + (T/2 + R)/M."""
    raise NotImplementedError


class Cheapest:
    """The lowest price per hour among offers with room (ties: by id), spot or not.
    Checkpoint every 240 minutes of progress on a spot offer, never on an on-demand offer."""

    def choose(self, job, remaining_min, now, offers, free):
        raise NotImplementedError

    def ckpt_interval(self, job, offer):
        raise NotImplementedError


class OnDemandOnly:
    """The cheapest ON-DEMAND offer with room; never a spot offer; never checkpoints."""

    def choose(self, job, remaining_min, now, offers, free):
        raise NotImplementedError

    def ckpt_interval(self, job, offer):
        raise NotImplementedError


class Hedged:
    """Minimise the EXPECTED cost per productive GPU-hour, with a deadline guard and a Young-Daly interval.

    For an offer with hazard h per hour: M = 60/h minutes, T* = young_daly_min(C, M), waste W = waste_fraction(T*, C, M, R)
    capped at max_waste; expected cost per productive GPU-hour = price / (1 - W). An on-demand offer has W = 0.
    A SPOT offer is eligible only if now + startup + remaining/(1 - W) + guard_min <= deadline.
    Ties break on the offer id. The checkpoint interval is max(C + 1, round(T*)), or math.inf without hazard."""

    def __init__(self, guard_min=60, max_waste=0.9):
        self.guard, self.max_waste = guard_min, max_waste

    def choose(self, job, remaining_min, now, offers, free):
        raise NotImplementedError

    def ckpt_interval(self, job, offer):
        raise NotImplementedError
