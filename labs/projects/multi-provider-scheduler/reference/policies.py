"""Placement policies. A policy answers two questions: where to run a waiting job, and how often to checkpoint."""
import math


def young_daly_min(ckpt_cost_min, mtbf_min):
    """First-order optimal compute time between checkpoints, T* = sqrt(2 C M) (see project 3)."""
    return math.sqrt(2.0 * ckpt_cost_min * mtbf_min)


def waste_fraction(interval_min, ckpt_cost_min, mtbf_min, restart_min):
    """W(T) = C/T + (T/2 + R)/M : checkpoint overhead plus expected rework and restart per unit of time."""
    return ckpt_cost_min / interval_min + (interval_min / 2.0 + restart_min) / mtbf_min


def fits(offers, free, job):
    return [o for o in offers if free[o.id] >= job.gpus]


class Cheapest:
    """Cheapest offer with room, spot or not; a checkpoint every 240 minutes of progress."""

    def choose(self, job, remaining_min, now, offers, free):
        cand = fits(offers, free, job)
        return min(cand, key=lambda o: (o.price, o.id)).id if cand else None

    def ckpt_interval(self, job, offer):
        return math.inf if offer.hazard == 0 else 240


class OnDemandOnly:
    """Cheapest on-demand offer with room; never a spot offer; no checkpoint (nothing interrupts)."""

    def choose(self, job, remaining_min, now, offers, free):
        cand = [o for o in fits(offers, free, job) if o.market == "on_demand"]
        return min(cand, key=lambda o: (o.price, o.id)).id if cand else None

    def ckpt_interval(self, job, offer):
        return math.inf


class Hedged:
    """Minimise the EXPECTED cost per productive GPU-hour, with a deadline guard and a Young-Daly interval.

    expected cost per productive GPU-hour = price / (1 - W(T*)); an offer is eligible only if the expected
    completion time (remaining work / (1 - W) + startup) leaves `guard` minutes before the deadline.
    """

    def __init__(self, guard_min=60, max_waste=0.9):
        self.guard, self.max_waste = guard_min, max_waste

    def _waste(self, job, offer):
        if offer.hazard == 0:
            return 0.0
        mtbf = 60.0 / offer.hazard
        t = young_daly_min(job.ckpt_cost_min, mtbf)
        return min(self.max_waste, waste_fraction(t, job.ckpt_cost_min, mtbf, job.restart_cost_min))

    def choose(self, job, remaining_min, now, offers, free):
        best = None
        for o in fits(offers, free, job):
            w = self._waste(job, o)
            expected_finish = now + o.startup_min + remaining_min / (1.0 - w)
            if expected_finish + self.guard > job.deadline_min and o.market == "spot":
                continue
            key = (o.price / (1.0 - w), o.id)
            if best is None or key < best[0]:
                best = (key, o.id)
        return best[1] if best else None

    def ckpt_interval(self, job, offer):
        if offer.hazard == 0:
            return math.inf
        return max(job.ckpt_cost_min + 1, round(young_daly_min(job.ckpt_cost_min, 60.0 / offer.hazard)))
