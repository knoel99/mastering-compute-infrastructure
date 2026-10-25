"""A toy environment and an exact evaluator (lab 11.2).

Corridor: states 0..L-1, start in 0, actions 0 = left and 1 = right. The goal is state L-1
(reward +1, episode ends). Every other step costs `step_cost`. With probability `slip` the
action is flipped. The episode is cut after `horizon` steps.
"""
import numpy as np


class Corridor:
    def __init__(self, length=8, horizon=40, slip=0.1, step_cost=0.01):
        self.length, self.horizon, self.slip, self.step_cost = length, horizon, slip, step_cost

    def reset(self):
        return 0

    def step(self, s, a, rng):
        if rng.random() < self.slip:
            a = 1 - a
        s2 = min(self.length - 1, s + 1) if a == 1 else max(0, s - 1)
        done = s2 == self.length - 1
        return s2, (1.0 if done else -self.step_cost), done

    def expected_return(self, theta):
        """Exact expected return of the softmax policy theta (shape [L, 2]), by backward induction."""
        L, H = self.length, self.horizon
        p_right = policy_probs(theta)[:, 1]
        v = np.zeros(L)                       # value with 0 steps left
        for _ in range(H):
            nv = np.zeros(L)
            for s in range(L - 1):
                total = 0.0
                for a, pa in ((1, p_right[s]), (0, 1.0 - p_right[s])):
                    for eff, pe in ((a, 1.0 - self.slip), (1 - a, self.slip)):
                        s2 = min(L - 1, s + 1) if eff == 1 else max(0, s - 1)
                        r = 1.0 if s2 == L - 1 else -self.step_cost
                        total += pa * pe * (r + (0.0 if s2 == L - 1 else v[s2]))
                nv[s] = total
            v = nv
        return float(v[0])


def policy_probs(theta):
    z = theta - theta.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def rollout(env, theta, version, rng, n_traj=1, step_cost_s=0.0):
    """Collect `n_traj` trajectories with the (possibly stale) policy `theta`.

    Each trajectory records the probability mu(a|s) of the action actually taken: the learner
    needs it to correct for the lag between the actor's policy and its own.
    `step_cost_s` > 0 SIMULATES a heavier simulator by sleeping step_cost_s per step.
    """
    import time
    probs = policy_probs(theta)
    out = []
    for _ in range(n_traj):
        s, S, A, R, MU = env.reset(), [], [], [], []
        for _ in range(env.horizon):
            a = 1 if rng.random() < probs[s, 1] else 0
            s2, r, done = env.step(s, a, rng)
            S.append(s); A.append(a); R.append(r); MU.append(probs[s, a])
            s = s2
            if done:
                break
        if step_cost_s:
            time.sleep(step_cost_s * len(S))
        out.append({"s": np.array(S), "a": np.array(A), "r": np.array(R), "mu": np.array(MU),
                    "version": version, "n": len(S)})
    return out
