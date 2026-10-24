"""Discrete-time simulator (one tick = one minute) of GPU jobs placed on spot and on-demand offers.

Semantics (the tests rely on them):
* A waiting job is offered to the policy at the start of every minute, FIFO by arrival. If the policy returns an
  offer with enough free GPUs, the allocation starts THAT minute and is billed from that minute.
* An allocation first spends offer.startup_min minutes starting up, then (after an interruption only)
  job.restart_cost_min minutes reloading state, then computes. Computing runs in chunks of `interval` minutes of
  progress, each followed by ckpt_cost_min minutes of checkpoint (no progress); the progress of a chunk is SAVED
  when its checkpoint completes. The last chunk is not followed by a checkpoint. interval = math.inf: no checkpoint.
* An interruption ends the allocation at the start of a minute, loses all unsaved progress, and the job is offered
  to the policy again in the same minute. For a spot allocation the time to interruption is exponential with rate
  hazard/60 per minute and is drawn from a generator seeded by (seed, job, allocation number): every policy meets the
  SAME interruption luck for the same allocation (common random numbers), which makes comparisons far less noisy.
* `forced` = {(job_id, allocation_number): billed_minutes} overrides the draw, to test exact timelines.
"""
import math
import random
from dataclasses import dataclass, field


@dataclass
class _Alloc:
    job: object
    offer: object
    start: int
    number: int
    interval: float
    startup_left: int
    restart_left: int
    fail_after: float  # billed minutes after which the allocation is interrupted
    billed: int = 0
    phase: str = "compute"  # compute | ckpt
    phase_left: float = 0.0
    progress: int = 0
    saved: int = 0
    ckpt_min: int = 0


@dataclass
class Result:
    cost: float
    jobs: dict
    ledger: list
    max_concurrent: dict
    deadline_misses: int
    unfinished: int
    interruptions: int
    lost_min: int
    horizon_min: int


def _fail_after(seed, job, number, hazard):
    if hazard <= 0:
        return math.inf
    u = random.Random(f"{seed}-{job.id}-{number}").random()
    return max(1, math.ceil(-math.log(1.0 - u) / (hazard / 60.0)))


def simulate(offers, jobs, policy, seed=0, horizon_min=14 * 24 * 60, forced=None):
    forced = forced or {}
    by_id = {o.id: o for o in offers}
    free = {o.id: o.capacity for o in offers}
    max_conc = {o.id: 0 for o in offers}
    waiting, running, ledger = [], [], []
    state = {j.id: {"saved": 0, "allocs": 0, "interruptions": 0, "lost": 0, "ckpt": 0, "billed": 0, "cost": 0.0,
                    "finish": None, "first_alloc": None} for j in jobs}
    pending = sorted(jobs, key=lambda j: (j.arrival_min, j.id))
    nxt = 0

    def release(a, now):
        free[a.offer.id] += a.job.gpus
        ledger.append((a.job.id, a.offer.id, a.start, now, a.job.gpus, a.offer.price))
        st = state[a.job.id]
        st["billed"] += a.billed
        st["cost"] += a.billed * a.job.gpus * a.offer.price / 60.0
        st["ckpt"] += a.ckpt_min

    for now in range(horizon_min):
        while nxt < len(pending) and pending[nxt].arrival_min <= now:
            waiting.append(pending[nxt])
            nxt += 1
        # interruptions: end allocations that have reached their failure time
        for a in list(running):
            if a.billed >= a.fail_after:
                running.remove(a)
                release(a, now)
                st = state[a.job.id]
                st["interruptions"] += 1
                st["lost"] += a.progress - a.saved
                st["saved"] = a.saved
                waiting.append(a.job)
        # placement, FIFO by arrival then id
        for job in sorted(waiting, key=lambda j: (j.arrival_min, j.id)):
            remaining = job.work_min - state[job.id]["saved"]
            choice = policy.choose(job, remaining, now, offers, dict(free))
            if choice is None or free[choice] < job.gpus:
                continue
            offer = by_id[choice]
            st = state[job.id]
            st["allocs"] += 1
            if st["first_alloc"] is None:
                st["first_alloc"] = now
            number = st["allocs"]
            free[offer.id] -= job.gpus
            max_conc[offer.id] = max(max_conc[offer.id], offer.capacity - free[offer.id])
            fail = forced.get((job.id, number), _fail_after(seed, job, number, offer.hazard))
            a = _Alloc(job, offer, now, number, policy.ckpt_interval(job, offer), offer.startup_min,
                       job.restart_cost_min if number > 1 else 0, fail, progress=st["saved"], saved=st["saved"])
            a.phase_left = min(a.interval, job.work_min - a.progress)
            running.append(a)
            waiting.remove(job)
        # advance every allocation by one minute
        for a in list(running):
            a.billed += 1
            if a.startup_left > 0:
                a.startup_left -= 1
            elif a.restart_left > 0:
                a.restart_left -= 1
            elif a.phase == "compute":
                a.progress += 1
                a.phase_left -= 1
                if a.progress >= a.job.work_min:
                    running.remove(a)
                    release(a, now + 1)
                    state[a.job.id]["finish"] = now + 1
                elif a.phase_left <= 0:
                    a.phase, a.phase_left = "ckpt", a.job.ckpt_cost_min
            else:
                a.phase_left -= 1
                a.ckpt_min += 1
                if a.phase_left <= 0:
                    a.saved = a.progress
                    a.phase = "compute"
                    a.phase_left = min(a.interval, a.job.work_min - a.progress)
        if nxt >= len(pending) and not waiting and not running:
            break
    for a in running:  # horizon reached: bill what was used
        release(a, horizon_min)
    jobs_out = {}
    for j in jobs:
        s = state[j.id]
        jobs_out[j.id] = {**s, "deadline_missed": s["finish"] is None or s["finish"] > j.deadline_min}
    total = sum(s["cost"] for s in state.values())
    return Result(total, jobs_out, ledger, max_conc,
                  sum(v["deadline_missed"] for v in jobs_out.values()),
                  sum(1 for v in jobs_out.values() if v["finish"] is None),
                  sum(v["interruptions"] for v in jobs_out.values()),
                  sum(v["lost"] for v in jobs_out.values()), horizon_min)
