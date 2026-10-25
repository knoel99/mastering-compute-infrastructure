"""Deterministic actor-learner loop with a CONTROLLED policy lag (lab 11.2).

At learner update u, each of the b trajectories was collected with the weights of version
max(0, u - lag): the simulation fixes the staleness instead of letting timing decide it, so
that the effect of staleness can be isolated and the curve is reproducible from a seed.
"""
import numpy as np

from learner import Learner
from toy_env import Corridor, rollout


def run(lag, correct, updates=300, b=8, lr=1.0, seed=0, length=8, eval_every=10, env=None):
    env = env or Corridor(length=length)
    learner = Learner(env.length, lr=lr, correct=correct)
    history = [learner.snapshot()]            # history[v] = weights of version v
    curve, lags = [], []
    for u in range(updates):
        v_act = max(0, u - lag)
        batch = []
        for j in range(b):
            rng = np.random.default_rng([seed, u, j])
            batch += rollout(env, history[v_act], v_act, rng)
        lags += [learner.version - t["version"] for t in batch]
        learner.update(batch)
        history.append(learner.snapshot())
        if (u + 1) % eval_every == 0 or u == 0:
            curve.append((u + 1, env.expected_return(learner.theta)))
    return {"curve": curve, "lags": lags, "final": curve[-1][1], "theta": learner.theta}
