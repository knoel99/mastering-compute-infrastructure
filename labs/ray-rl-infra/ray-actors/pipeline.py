"""Lab 11.1 - a small Ray pipeline: stateless tasks and a pool of stateful actors.

The data are synthetic and deterministic given a seed (CPU only, no GPU).
`load_s` SIMULATES the time a real model needs to be read from disk: it is a
sleep, not a measurement of any real model.
"""
import os
import time

import numpy as np
import ray
from ray.util import ActorPool

DIM = 256


def make_doc(i, seed=0, n=20_000):
    """Deterministic pseudo-document number `i`."""
    return np.random.default_rng([seed, i]).standard_normal(n)


def featurize_np(x, dim=DIM):
    """Stateless preprocessing: standardise, then fold into `dim` bins."""
    x = (x - x.mean()) / (x.std() + 1e-12)
    return x[: (len(x) // dim) * dim].reshape(-1, dim).mean(axis=0)


def build_model(seed=0, dim=DIM, load_s=0.0):
    """The 'model': expensive to build (simulated load), cheap to call."""
    if load_s:
        time.sleep(load_s)
    return np.random.default_rng(seed).standard_normal((dim, dim)) / np.sqrt(dim)


def score_np(w, feat):
    return float(np.tanh(w @ feat).sum())


# ---------------------------------------------------------------- serial reference
def run_serial(n_docs, seed=0):
    w = build_model(seed)
    return [score_np(w, featurize_np(make_doc(i, seed))) for i in range(n_docs)]


# ---------------------------------------------------------------- Ray: tasks
@ray.remote
def featurize(i, seed=0):
    return featurize_np(make_doc(i, seed))


@ray.remote
def score_with_rebuild(feat, seed=0, load_s=0.0):
    """Anti-pattern: a task has no state, so it rebuilds the model every call."""
    w = build_model(seed, load_s=load_s)
    return score_np(w, feat), 1, os.getpid()


# ---------------------------------------------------------------- Ray: actors
@ray.remote
class Scorer:
    """Stateful worker: the model is built once, in __init__."""

    def __init__(self, seed=0, load_s=0.0):
        self.w = build_model(seed, load_s=load_s)
        self.init_count = 1
        self.calls = 0

    def score(self, feat):
        self.calls += 1
        return score_np(self.w, feat)

    def info(self):
        return {"pid": os.getpid(), "init_count": self.init_count, "calls": self.calls}


def run_tasks(n_docs, seed=0, load_s=0.0):
    """Stateless version. Returns (scores, number of model builds, set of pids)."""
    feats = [featurize.remote(i, seed) for i in range(n_docs)]
    out = ray.get([score_with_rebuild.remote(f, seed, load_s) for f in feats])
    return [o[0] for o in out], sum(o[1] for o in out), {o[2] for o in out}


def run_actors(n_docs, n_actors, seed=0, load_s=0.0):
    """Stateful version. Returns (scores, number of model builds, infos per actor)."""
    feats = [featurize.remote(i, seed) for i in range(n_docs)]
    actors = [Scorer.remote(seed, load_s) for _ in range(n_actors)]
    pool = ActorPool(actors)
    scores = list(pool.map(lambda a, f: a.score.remote(f), feats))
    infos = ray.get([a.info.remote() for a in actors])
    for a in actors:
        ray.kill(a)
    return scores, sum(i["init_count"] for i in infos), infos
