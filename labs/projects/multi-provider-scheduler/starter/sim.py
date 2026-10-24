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
    """TO WRITE (milestone 1). Follow the semantics above, one loop iteration per minute, in this order:
    1. jobs whose arrival_min has come join the waiting list;
    2. allocations whose billed minutes reached fail_after end (interruption): release GPUs, count the
       interruption, add the unsaved progress to `lost`, put the job back on the waiting list;
    3. waiting jobs, FIFO by (arrival_min, id), are offered to policy.choose(job, remaining_min, now, offers, free);
       a valid choice starts an allocation THIS minute (fail_after = forced.get((job.id, n)) or _fail_after(...));
    4. every running allocation advances one minute and is billed one minute: startup, then restart cost (only
       from the second allocation of a job), then compute/checkpoint chunks; the job finishes when its progress
       reaches work_min (end = now + 1, GPUs released).
    Return a Result: cost = sum of billed_minutes x gpus x price / 60 per allocation, `ledger` = list of
    (job_id, offer_id, start, end, gpus, price), max_concurrent per offer, deadline_misses, unfinished,
    interruptions, lost_min, and jobs[id] = {finish, billed, cost, interruptions, lost, ckpt, first_alloc,
    saved, allocs, deadline_missed}. Stop early when nothing is left to do."""
    raise NotImplementedError
