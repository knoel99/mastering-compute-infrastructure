"""The same toy loop on real Ray actors (lab 11.2): staleness and throughput EMERGE from timing.

Driver = learner. N `RolloutActor`s each have one rollout in flight. Weights are published with
`ray.put` (one copy in the object store, shared by all actors of the node). Two ways to feed the
learner:
  mode="replay"  trajectories go into a FIFO replay buffer; the learner samples batches uniformly
                 and does about `replay_ratio` updates worth of data per fresh batch;
  mode="queue"   IMPALA-style: each trajectory is consumed once, oldest first. With `credits=K`
                 an actor is only given new work if (in flight + queued) < K, so staleness is bounded
                 BEFORE the rollout starts; credits=None gives no back-pressure.
`step_cost_s` and `update_cost_s` SIMULATE a heavier simulator and a heavier learner with sleeps.
"""
import time

import numpy as np
import ray

from learner import Learner
from replay import ReplayBuffer
from toy_env import Corridor, rollout


@ray.remote
class RolloutActor:
    def __init__(self, actor_id, seed, length, horizon, step_cost_s):
        self.id, self.seed, self.calls = actor_id, seed, 0
        self.env = Corridor(length=length, horizon=horizon)
        self.step_cost_s = step_cost_s

    def rollout(self, theta, version, n_traj):
        rng = np.random.default_rng([self.seed, self.id, self.calls])
        self.calls += 1
        t0 = time.perf_counter()
        trajs = rollout(self.env, theta, version, rng, n_traj, self.step_cost_s)
        return {"actor": self.id, "trajs": trajs, "busy_s": time.perf_counter() - t0}


def run_ray(n_actors=4, updates=120, b=4, mode="replay", replay_ratio=1.0, replay_capacity=64,
            credits=None, traj_per_call=1, sync_every=1, lr=1.0, correct=True,
            step_cost_s=2e-4, update_cost_s=0.0, seed=0, length=16, horizon=60, eval_every=10):
    env = Corridor(length=length, horizon=horizon)
    learner = Learner(length, lr=lr, correct=correct)
    rng = np.random.default_rng([seed, 999])
    actors = [RolloutActor.remote(i, seed, length, horizon, step_cost_s) for i in range(n_actors)]
    buf = ReplayBuffer(replay_capacity if mode == "replay" else 10 ** 9)
    weights_ref, weights_version = ray.put(learner.snapshot()), 0
    pending, idle = {}, list(range(n_actors))
    lags, curve, actors_seen, busy = [], [], set(), 0.0
    steps = ingested = 0
    wait_s = 0.0
    t_start = time.perf_counter()

    def fill():
        # give work to idle actors, respecting the credits (queue mode only)
        while idle:
            alive = len(pending) * traj_per_call + len(buf)
            if mode == "queue" and credits is not None and alive + traj_per_call > credits:
                return
            i = idle.pop(0)
            pending[actors[i].rollout.remote(weights_ref, weights_version, traj_per_call)] = i

    try:
        fill()
        while learner.version < updates:
            t0 = time.perf_counter()
            ready, _ = ray.wait(list(pending), num_returns=1)
            wait_s += time.perf_counter() - t0
            res = ray.get(ready[0])
            idle.append(pending.pop(ready[0]))
            actors_seen.add(res["actor"])
            busy += res["busy_s"]
            for t in res["trajs"]:
                buf.add(t)
                steps += t["n"]
                ingested += 1
            fill()
            while learner.version < updates and len(buf) >= b:
                if mode == "replay":
                    if (learner.version + 1) * b > replay_ratio * ingested:
                        break
                    batch = buf.sample(rng, b)
                else:
                    batch = buf.pop_oldest(b)
                lags += [learner.version - t["version"] for t in batch]
                if mode == "queue":
                    fill()          # credits come back when the learner TAKES the batch, before the update ends
                learner.update(batch)
                if update_cost_s:
                    time.sleep(update_cost_s)
                if learner.version % sync_every == 0:
                    weights_ref, weights_version = ray.put(learner.snapshot()), learner.version
                if learner.version % eval_every == 0 or learner.version == 1:
                    curve.append((learner.version, env.expected_return(learner.theta)))
                fill()
        wall = time.perf_counter() - t_start
    finally:
        for a in actors:   # killing the actors also drops their in-flight rollouts
            ray.kill(a)
    return {
        "n_actors": n_actors, "mode": mode, "credits": credits, "wall_s": wall,
        "steps": steps, "trajectories": ingested, "steps_per_s": steps / wall,
        "updates_per_s": learner.version / wall,
        "mean_lag": float(np.mean(lags)), "p95_lag": float(np.percentile(lags, 95)),
        "max_lag": int(max(lags)), "learner_wait_frac": wait_s / wall,
        "actor_busy_per_traj_s": busy / max(1, ingested),
        "final_return": env.expected_return(learner.theta), "curve": curve,
        "actors_seen": sorted(actors_seen), "lags": lags,
    }
