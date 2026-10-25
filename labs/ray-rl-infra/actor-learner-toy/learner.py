"""Policy-gradient learner with an optional clipped importance weight (lab 11.2).

This is REINFORCE with a tabular baseline V[s]. `correct=True` multiplies each step's gradient
by rho_t = min(1, pi(a_t|s_t) / mu(a_t|s_t)), the truncated importance weight of V-trace
(Espeholt et al., 2018) WITHOUT the rest of V-trace (no value trace, Monte-Carlo returns): a
simplification for a toy, not a re-implementation of IMPALA.
"""
import numpy as np

from toy_env import policy_probs


class Learner:
    def __init__(self, length, lr=0.5, lr_v=0.1, correct=False, rho_bar=1.0):
        self.theta = np.zeros((length, 2))
        self.v = np.zeros(length)
        self.lr, self.lr_v, self.correct, self.rho_bar = lr, lr_v, correct, rho_bar
        self.version = 0

    def snapshot(self):
        return self.theta.copy()

    def gradient(self, batch):
        probs = policy_probs(self.theta)
        g = np.zeros_like(self.theta)
        dv = np.zeros_like(self.v)
        for tr in batch:
            G = np.cumsum(tr["r"][::-1])[::-1]               # undiscounted return-to-go
            adv = G - self.v[tr["s"]]
            if self.correct:
                rho = np.minimum(self.rho_bar, probs[tr["s"], tr["a"]] / tr["mu"])
            else:
                rho = np.ones_like(adv)
            onehot = np.zeros((len(tr["s"]), 2))
            onehot[np.arange(len(tr["s"])), tr["a"]] = 1.0
            coef = (rho * adv)[:, None] * (onehot - probs[tr["s"]])
            np.add.at(g, tr["s"], coef)
            np.add.at(dv, tr["s"], G - self.v[tr["s"]])
        return g / len(batch), dv / len(batch)

    def update(self, batch):
        g, dv = self.gradient(batch)
        self.theta += self.lr * g
        self.v += self.lr_v * dv
        self.version += 1
        return self.version
