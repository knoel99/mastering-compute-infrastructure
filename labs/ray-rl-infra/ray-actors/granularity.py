"""Task granularity and Ray overhead.

SIMULATED work: each task sleeps for `d` seconds, so the measurement does not
depend on how busy the CPUs of a shared machine are. What is measured is the
cost of Ray's scheduling per task (submit, lease a worker, run, return).
Efficiency E = useful time / (slots x wall time).
"""
import statistics
import time

import ray


@ray.remote
def nap(d):
    time.sleep(d)
    return d


@ray.remote
def nap_chunk(d, k):
    for _ in range(k):
        time.sleep(d)
    return d * k


@ray.remote
def noop():
    return None


def efficiency(d, total_useful=1.6, slots=4, chunk=1):
    """Run total_useful/d naps of d seconds, `chunk` naps per Ray task."""
    n = max(slots, round(total_useful / d))
    n_tasks = max(1, n // chunk)
    ray.get([nap.remote(0.0) for _ in range(slots * 2)])  # warm the workers up
    t0 = time.perf_counter()
    if chunk == 1:
        ray.get([nap.remote(d) for _ in range(n_tasks)])
    else:
        ray.get([nap_chunk.remote(d, chunk) for _ in range(n_tasks)])
    wall = time.perf_counter() - t0
    useful = n_tasks * chunk * d
    return {"d_s": d, "chunk": chunk, "tasks": n_tasks, "wall_s": wall,
            "efficiency": useful / (slots * wall)}


def overhead_per_task(reps=200):
    """Median round trip of an empty task and of an empty actor call, in seconds."""
    @ray.remote
    class Echo:
        def ping(self):
            return None

    a = Echo.remote()
    ray.get(a.ping.remote())
    ray.get(noop.remote())
    t_task, t_actor = [], []
    for _ in range(reps):
        t0 = time.perf_counter()
        ray.get(noop.remote())
        t_task.append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        ray.get(a.ping.remote())
        t_actor.append(time.perf_counter() - t0)
    ray.kill(a)
    return statistics.median(t_task), statistics.median(t_actor)
