"""Lab 11.1 report: run everything once and print the numbers quoted in the course."""
import os
import sys
import tempfile
import time

import numpy as np
import ray

import fault
import granularity
import pipeline

N_DOCS = 40


def main():
    ray.init(num_cpus=4, include_dashboard=False, logging_level="ERROR", log_to_driver=False)
    print(f"ray {ray.__version__}, logical resources: {ray.cluster_resources()['CPU']:.0f} CPU")

    # 1. correctness: tasks and actors against the serial reference
    serial = pipeline.run_serial(N_DOCS)
    s_t, builds_t, pids = pipeline.run_tasks(N_DOCS, load_s=0.05)
    s_a, builds_a, infos = pipeline.run_actors(N_DOCS, n_actors=4, load_s=0.05)
    assert np.allclose(s_t, serial) and np.allclose(s_a, serial)
    print(f"model builds for {N_DOCS} documents: tasks={builds_t}  actors={builds_a}"
          f"  (simulated load 50 ms per build)")

    # 2. granularity (simulated work: sleeps)
    print("granularity (4 slots, 1.6 s of useful sleep each):")
    rows = [granularity.efficiency(0.001), granularity.efficiency(0.01),
            granularity.efficiency(0.1), granularity.efficiency(0.001, chunk=100)]
    for r in rows:
        print(f"  d={r['d_s']*1e3:6.1f} ms  chunk={r['chunk']:3d}  tasks={r['tasks']:5d}"
              f"  wall={r['wall_s']:.2f} s  efficiency={r['efficiency']:.2f}")
    t_task, t_actor = granularity.overhead_per_task()
    print(f"median round trip: empty task {t_task*1e3:.2f} ms, empty actor call {t_actor*1e3:.2f} ms")

    # 3. failures
    with tempfile.TemporaryDirectory() as d:
        a = fault.Counter.remote()
        ray.get(a.inc.remote())
        a.die.remote()
        try:
            fault.call_until_alive(a.inc.remote, timeout_s=3.0)
            out0 = "still alive?!"
        except ray.exceptions.RayActorError:
            out0 = "RayActorError"
        b = fault.Counter.options(max_restarts=1).remote()
        for _ in range(3):
            ray.get(b.inc.remote())
        b.die.remote()
        out1 = fault.call_until_alive(b.inc.remote)
        ck = os.path.join(d, "c.json")
        c = fault.Counter.options(max_restarts=1).remote(ck)
        for _ in range(3):
            ray.get(c.inc.remote())
        c.die.remote()
        out2 = fault.call_until_alive(c.inc.remote)
        print(f"max_restarts=0: next call -> {out0}")
        print(f"max_restarts=1, no checkpoint: counter was 3, next inc -> {out1}")
        print(f"max_restarts=1, checkpoint   : counter was 3, next inc -> {out2}")
        for retries in (0, -1):
            log, marker = os.path.join(d, f"l{retries}"), os.path.join(d, f"m{retries}")
            h = fault.Counter.options(max_restarts=1, max_task_retries=retries).remote()
            try:
                res = ray.get(h.work.remote(7, log, marker))
            except ray.exceptions.RayActorError:
                res = "RayActorError"
            print(f"max_task_retries={retries:2d}: result={res!s:14} side effects of call 7:"
                  f" {open(log).read().split()}")
    ray.shutdown()
    print("OK ray-actors (demo)")


if __name__ == "__main__":
    sys.exit(main())
