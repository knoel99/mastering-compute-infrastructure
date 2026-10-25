"""Discrete-event simulation of the same loop (lab 11.3), in simulated time.

Entities: N actors (sync -> rollout -> put), one FIFO queue of capacity Q
trajectories, one learner (takes b trajectories, spends s_L, version += 1).
Two ways to apply back-pressure when the queue is full:
  policy="block"   the actor finishes its rollout, then waits for a free slot
                   (it holds a finished trajectory that keeps ageing);
  policy="credit"  the actor must obtain one of K credits BEFORE it starts;
                   a credit comes back when the learner takes the trajectory.
Durations are drawn with mean 1 around the nominal value:
  dist="det"  no noise;  "exp"  exponential;  "lognormal"  with coefficient of variation cv.
Pure Python + numpy RNG with a seed: same seed, same result. No wall clock.
"""
import heapq
from collections import deque

import numpy as np


class Draw:
    def __init__(self, dist, rng, cv=0.5):
        self.dist, self.rng, self.cv = dist, rng, cv
        if dist == "lognormal":
            self.sigma = float(np.sqrt(np.log(1 + cv * cv)))
            self.mu = -0.5 * self.sigma ** 2

    def __call__(self, mean):
        if self.dist == "det" or mean == 0:
            return mean
        if self.dist == "exp":
            return float(self.rng.exponential(mean))
        if self.dist == "lognormal":
            return float(mean * np.exp(self.mu + self.sigma * self.rng.standard_normal()))
        raise ValueError(self.dist)


def simulate(n_actors, m, t_roll, t_sync, b, s_L, queue_cap=None, policy="block",
             credits=None, dist="det", cv=0.5, horizon=600.0, warmup=0.1, seed=0):
    """Return a dict of statistics measured after the warm-up fraction of the horizon."""
    rng = np.random.default_rng(seed)
    draw = Draw(dist, rng, cv)
    INF = float("inf")
    queue_cap = INF if queue_cap is None else queue_cap
    ev, seq = [], 0                       # (time, seq, kind, payload)

    def push(t, kind, payload=None):
        nonlocal seq
        heapq.heappush(ev, (t, seq, kind, payload))
        seq += 1

    queue = deque()                       # (v_read, t_enqueue)
    blocked = deque()                     # (actor, v_read) finished, waiting for a slot ("block" policy)
    waiting_for_credit = deque()          # idle actors ("credit" policy)
    free_credits = INF if credits is None else credits
    version, learner_busy = 0, False
    t_warm = horizon * warmup
    # statistics (only after warm-up unless stated)
    lags, waits = [], []
    consumed_steps = updates = 0
    busy_time = 0.0
    q_area, last_t, blocked_area = 0.0, 0.0, 0.0
    arrivals = 0
    wait_all, dep_all = 0.0, 0

    def start_cycle(a, t):
        push(t + draw(t_sync), "synced", a)

    def enqueue(v_read, t):
        nonlocal arrivals
        queue.append((v_read, t))
        if t >= t_warm:
            arrivals += 1

    def try_start_actor(a, t):
        nonlocal free_credits
        if policy == "credit" and free_credits < 1:
            waiting_for_credit.append(a)
            return
        if policy == "credit":
            free_credits -= 1
        start_cycle(a, t)

    def try_learner(t):
        nonlocal learner_busy, free_credits
        if learner_busy or len(queue) < b:
            return
        batch = [queue.popleft() for _ in range(b)]
        for v_read, t_enq in batch:
            nonlocal wait_all, dep_all
            wait_all += t - t_enq
            dep_all += 1
            if t >= t_warm:
                lags.append(version - v_read)
                waits.append(t - t_enq)
        learner_busy = True
        dur = draw(s_L)
        push(t + dur, "learned", (dur, t))
        if policy == "credit":
            free_credits += b
            while waiting_for_credit and free_credits >= 1:
                free_credits -= 1
                start_cycle(waiting_for_credit.popleft(), t)
        # a slot was freed: let blocked actors in
        while blocked and len(queue) < queue_cap:
            a, v_read = blocked.popleft()
            enqueue(v_read, t)
            try_start_actor(a, t)

    for a in range(n_actors):
        try_start_actor(a, 0.0)

    while ev:
        t, _, kind, payload = heapq.heappop(ev)
        if t > horizon:
            break
        if t >= t_warm:
            lo = max(last_t, t_warm)
            q_area += len(queue) * (t - lo)
            blocked_area += len(blocked) * (t - lo)
        last_t = t
        if kind == "synced":
            push(t + draw(t_roll), "rolled", (payload, version))
        elif kind == "rolled":
            a, v_read = payload
            if len(queue) < queue_cap:
                enqueue(v_read, t)
                try_start_actor(a, t)
            else:
                blocked.append((a, v_read))
            try_learner(t)
        elif kind == "learned":
            dur, t_take = payload
            version += 1
            learner_busy = False
            if t_take >= t_warm:
                updates += 1
                consumed_steps += b * m
                busy_time += dur
            try_learner(t)
    span = horizon - t_warm
    mean = lambda x: float(np.mean(x)) if len(x) else float("nan")
    return {
        "steps_per_s": consumed_steps / span,
        "updates_per_s": updates / span,
        "learner_util": busy_time / span,
        "mean_lag": mean(lags),
        "p95_lag": float(np.percentile(lags, 95)) if lags else float("nan"),
        "max_lag": int(max(lags)) if lags else 0,
        "mean_queue_wait_s": mean(waits),
        "mean_queue_len": q_area / span,
        "mean_blocked_actors": blocked_area / span,
        "arrival_rate_traj_s": arrivals / span,
        "trajectories_consumed": len(lags),
        "queue_len_end": len(queue),
    }
