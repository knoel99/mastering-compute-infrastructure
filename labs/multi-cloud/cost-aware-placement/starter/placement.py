"""STARTER. Write the seven functions marked TODO (young_daly, waste, price_per_useful_hour, transfer_hours, move_cost,
Aware.score, paired_diff); the engine, the draws and the other policies are provided.
Read ../README.md and the docstrings, then run:  IMPL=starter python -m pytest -q tests

Cost-aware placement of ONE long GPU job across providers, with preemption and data gravity.

Every number the module consumes is an INPUT: the scenario in scenarios.py is SYNTHETIC (prices in arbitrary units
`u`, invented availabilities and hazards). Do not read it as the market.

Time is in hours, money in u. The engine is event-driven, not tick-based:

* A job needs `work_h` hours of useful compute on `gpus` GPUs. Checkpoints (cost `ckpt_cost_h`, billed, no progress)
  are taken every T* hours of progress on a preemptible pool, T* = sqrt(2 C M) (Young-Daly, first order), M = 1/hazard.
  The last chunk is not followed by a checkpoint. A non-preemptible pool never checkpoints.
* A pool grants capacity in slots of `slot_h` hours: a request in slot k succeeds with probability `p_avail`,
  independently per (seed, pool, slot). A refused request waits for the next slot (not billed).
* An allocation is billed from the grant: `startup_h`, then `restart_h` if a checkpoint must be reloaded, then compute.
  A preemption (exponential time, rate `hazard` per hour, drawn from (seed, pool, grant time)) ends the
  allocation; everything since the last completed checkpoint is lost.
* State (checkpoint of `ckpt_gb`, dataset of `data_gb`) lives at a provider. Starting on another provider first
  copies the checkpoint, and the dataset if that provider has no copy yet (data_at), at `egress_u_per_gb` and at the
  link speed; the copy time is wall-clock, not billed on GPUs. A provider that holds a copy keeps it.
* All draws depend only on (seed, pool, slot or grant time), never on the policy: every policy meets the SAME luck.
"""
import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Pool:
    id: str
    provider: str
    price: float       # u per GPU-hour
    hazard: float      # preemptions per hour of allocation (0: not preemptible)
    p_avail: float     # probability that a request is granted in a given slot
    startup_h: float   # billed hours between the grant and the first useful hour


@dataclass(frozen=True)
class Job:
    gpus: int
    work_h: float
    deadline_h: float
    ckpt_gb: float
    data_gb: float
    ckpt_cost_h: float
    restart_h: float
    home: str          # provider that holds the checkpoint and the dataset at time 0


@dataclass(frozen=True)
class Network:
    egress_u_per_gb: float   # between two different providers
    gbit_per_s: float
    efficiency: float = 0.8


@dataclass(frozen=True)
class State:
    t: float
    remaining_h: float
    ckpt_at: str
    data_at: frozenset
    slot: int


# ---- formulas -------------------------------------------------------------------------------------------------

def young_daly(ckpt_cost_h, mtbf_h):
    """First-order optimal compute time between checkpoints, T* = sqrt(2 C M)."""
    raise NotImplementedError("TODO")


def waste(interval_h, ckpt_cost_h, mtbf_h, restart_h):
    """Fraction of allocated time that is not useful progress: W(T) = C/T + (T/2 + R)/M."""
    raise NotImplementedError("TODO")


def price_per_useful_hour(pool, job):
    """Expected price of one useful GPU-hour: price / (1 - W(T*)); infinity if the waste reaches 1."""
    raise NotImplementedError("TODO")


def transfer_hours(gb, gbit_per_s, efficiency=0.8):
    """Wall-clock hours to copy gb gigabytes over the link."""
    raise NotImplementedError("TODO")


def move_cost(job, net, ckpt_at, to_provider, data_at):
    """(egress cost in u, copy time in hours) to start on `to_provider` given where the state lives now."""
    raise NotImplementedError("TODO")


# ---- common random numbers -----------------------------------------------------------------------------------------

def _u(seed, kind, pool_id, slot):
    return random.Random(f"{seed}|{kind}|{pool_id}|{slot}").random()


def available(seed, pool, slot):
    return _u(seed, "avail", pool.id, slot) < pool.p_avail


def preempt_after(seed, pool, t_grant):
    """Hours of allocation before the preemption, drawn from (seed, pool, grant time rounded to 1e-4 h)."""
    if pool.hazard <= 0:
        return math.inf
    return -math.log(1.0 - _u(seed, "preempt", pool.id, f"{t_grant:.4f}")) / pool.hazard


# ---- policies -------------------------------------------------------------------------------------------------

class Stay:
    """Always the same pool, wait for capacity there."""

    def __init__(self, pool_id):
        self.pool_id = pool_id

    def choose(self, job, pools, net, st, seed, slot_h):
        return next(p for p in pools if p.id == self.pool_id)


class Cheapest:
    """The price chaser: lowest LIST price among all pools, wait for capacity there. Ignores waste and moving costs."""

    def choose(self, job, pools, net, st, seed, slot_h):
        return min(pools, key=lambda p: (p.price, p.id))


class FirstAvailable:
    """What an `any_of` failover does: the cheapest pool that grants capacity right now (all pools if none does).

    Beware the on-demand trap: when the spot pools refuse, the job lands on the on-demand pool, which is never
    preempted, so nothing ever moves it back to spot.
    """

    def choose(self, job, pools, net, st, seed, slot_h):
        now = [p for p in pools if available(seed, p, st.slot)] or list(pools)
        return min(now, key=lambda p: (p.price, p.id))


class Aware:
    """Minimise price per useful hour x remaining GPU-hours + egress + lam x expected duration (u per hour of delay).

    The expected duration counts the copy, the wait for capacity (0 if the pool grants now, else slot_h / p_avail)
    and remaining / (1 - W). `lam` is the value of time: it must come from the business (deadline penalty), not
    from the code.
    """

    def __init__(self, lam=0.0):
        self.lam = lam

    def score(self, job, pool, net, st, seed, slot_h):
        raise NotImplementedError("TODO")

    def choose(self, job, pools, net, st, seed, slot_h):
        return min(pools, key=lambda p: (self.score(job, p, net, st, seed, slot_h), p.id))


# ---- engine ---------------------------------------------------------------------------------------------------------

def simulate(job, pools, net, policy, seed=0, slot_h=0.25, horizon_h=5000.0, forced=None):
    """Run one job to completion (or to the horizon). forced = {allocation_number: billed_hours_before_preemption}."""
    forced = forced or {}
    t, saved, cost, egress = 0.0, 0.0, 0.0, 0.0
    ckpt_at, data_at = job.home, frozenset([job.home])
    allocs = moves = preempts = 0
    eps = 1e-9
    while job.work_h - saved > eps and t < horizon_h:
        slot = int(t / slot_h + eps)
        st = State(t, job.work_h - saved, ckpt_at, data_at, slot)
        pool = policy.choose(job, pools, net, st, seed, slot_h)
        usd, copy_h = move_cost(job, net, ckpt_at, pool.provider, data_at)
        if pool.provider != ckpt_at or pool.provider not in data_at:   # a change of provider, even a free one
            egress += usd
            cost += usd
            t += copy_h
            moves += 1
            ckpt_at, data_at = pool.provider, data_at | {pool.provider}
        slot = int(t / slot_h + eps)
        while not available(seed, pool, slot) and t < horizon_h:
            slot += 1
            t = slot * slot_h
        if t >= horizon_h:
            break
        allocs += 1
        overhead = pool.startup_h + (job.restart_h if saved > 0 else 0.0)
        cut = forced.get(allocs, preempt_after(seed, pool, t))
        interval = young_daly(job.ckpt_cost_h, 1.0 / pool.hazard) if pool.hazard > 0 else math.inf
        used, todo, done_here, finished, preempted = overhead, job.work_h - saved, 0.0, False, False
        if cut < overhead:
            used, preempted = cut, True
        else:
            while True:
                chunk = min(interval, todo)
                if cut < used + chunk:
                    used, preempted = cut, True
                    break
                used += chunk
                todo -= chunk
                if todo <= eps:
                    finished = True
                    break
                if cut < used + job.ckpt_cost_h:
                    used, preempted = cut, True
                    break
                used += job.ckpt_cost_h
                done_here += chunk
        cost += used * job.gpus * pool.price
        t += used
        if finished:
            saved = job.work_h
        else:
            saved += done_here
            preempts += preempted
    done = job.work_h - saved <= eps
    return {"cost": cost, "finish_h": t if done else math.inf, "moves": moves, "preemptions": preempts,
            "egress": egress, "late": (not done) or t > job.deadline_h, "allocations": allocs}


# ---- comparison -----------------------------------------------------------------------------------------------------

def run_many(job, pools, net, policy, seeds, **kw):
    return [simulate(job, pools, net, policy, seed=s, **kw) for s in seeds]


def summarize(results):
    n = len(results)
    fin = [r["finish_h"] for r in results if math.isfinite(r["finish_h"])]
    return {"cost": sum(r["cost"] for r in results) / n,
            "finish_h": sum(fin) / len(fin) if fin else math.inf,
            "late": sum(r["late"] for r in results) / n,
            "moves": sum(r["moves"] for r in results) / n,
            "preemptions": sum(r["preemptions"] for r in results) / n,
            "egress": sum(r["egress"] for r in results) / n}


def paired_diff(a, b, key="cost"):
    """Mean of (a - b) per seed and the half-width of a normal 95 % interval. a and b are result lists, same seeds."""
    raise NotImplementedError("TODO")
