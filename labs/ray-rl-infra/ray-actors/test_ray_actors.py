"""Tests for lab 11.1. Assertions are on values, counters and ratios, never on a duration."""
import numpy as np
import pytest
import ray

import fault
import granularity
import pipeline

N_DOCS = 24


def test_numpy_pieces_are_deterministic():
    assert np.array_equal(pipeline.make_doc(3, seed=1), pipeline.make_doc(3, seed=1))
    assert not np.array_equal(pipeline.make_doc(3, seed=1), pipeline.make_doc(4, seed=1))


def test_tasks_match_serial(ray_ctx):
    serial = pipeline.run_serial(N_DOCS)
    scores, builds, pids = pipeline.run_tasks(N_DOCS, load_s=0.0)
    assert np.allclose(scores, serial, rtol=1e-9, atol=1e-12)
    assert builds == N_DOCS  # a stateless task rebuilds the model on every call
    assert len(pids) >= 2    # and the work really ran in several processes


def test_actors_match_serial_and_build_once(ray_ctx):
    serial = pipeline.run_serial(N_DOCS)
    scores, builds, infos = pipeline.run_actors(N_DOCS, n_actors=3)
    assert np.allclose(scores, serial, rtol=1e-9, atol=1e-12)  # ActorPool.map keeps the order
    assert builds == 3                                          # one build per actor
    assert sum(i["calls"] for i in infos) == N_DOCS
    assert len({i["pid"] for i in infos}) == 3                  # one dedicated process each


def test_granularity_efficiency_is_ordered(ray_ctx):
    fine = granularity.efficiency(0.001)
    coarse = granularity.efficiency(0.1)
    chunked = granularity.efficiency(0.001, chunk=100)
    for r in (fine, coarse, chunked):
        assert 0.0 < r["efficiency"] <= 1.05
    assert coarse["efficiency"] > fine["efficiency"]
    assert chunked["efficiency"] > fine["efficiency"]


def test_default_actor_is_lost_when_its_process_dies(ray_ctx):
    a = fault.Counter.remote()
    assert ray.get(a.inc.remote()) == 1
    a.die.remote()
    with pytest.raises(ray.exceptions.RayActorError):
        fault.call_until_alive(a.inc.remote, timeout_s=3.0)


def test_restarted_actor_loses_its_state_unless_checkpointed(ray_ctx, tmp_path):
    plain = fault.Counter.options(max_restarts=1).remote()
    for _ in range(3):
        ray.get(plain.inc.remote())
    pid0 = ray.get(plain.pid.remote())
    plain.die.remote()
    assert fault.call_until_alive(plain.inc.remote) == 1   # state reset by the restart
    assert ray.get(plain.pid.remote()) != pid0              # a new process

    ck = str(tmp_path / "counter.json")
    kept = fault.Counter.options(max_restarts=1).remote(ck)
    for _ in range(3):
        ray.get(kept.inc.remote())
    kept.die.remote()
    assert fault.call_until_alive(kept.inc.remote) == 4    # 3 recovered from the checkpoint + 1


def test_actor_task_semantics_at_most_once_vs_at_least_once(ray_ctx, tmp_path):
    def run(max_task_retries, name):
        log, marker = str(tmp_path / f"{name}.log"), str(tmp_path / f"{name}.marker")
        a = fault.Counter.options(max_restarts=1, max_task_retries=max_task_retries).remote()
        try:
            res = ray.get(a.work.remote(7, log, marker))
        except ray.exceptions.RayActorError:
            res = "RayActorError"
        with open(log) as f:
            return res, f.read().split()

    res, lines = run(0, "amo")
    assert res == "RayActorError" and lines == ["7"]          # at most once: lost, no duplicate
    res, lines = run(-1, "alo")
    assert res == 7 and lines == ["7", "7"]                   # at least once: done, side effect twice


def test_task_retries(ray_ctx, tmp_path):
    ok = str(tmp_path / "m_ok")
    assert ray.get(flaky(ok, 3)) == "ok"
    with pytest.raises(ray.exceptions.WorkerCrashedError):
        ray.get(flaky(str(tmp_path / "m_ko"), 0))


def flaky(marker, retries):
    return fault.flaky_task.options(max_retries=retries).remote(marker)
