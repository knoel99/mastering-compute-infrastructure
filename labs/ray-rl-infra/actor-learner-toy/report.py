"""Lab 11.2 report: the numbers quoted in chapter 5 of the course.

Part A is deterministic (seeded, controlled lag). Part B runs real Ray actors: it is NOT
reproducible bit for bit, so only structure is asserted in test_toy.py; the figures printed here
come from one run on the machine that executes this script.
"""
import sys

import numpy as np
import ray

import loop_ray
import loop_sim
from toy_env import Corridor

ENV = Corridor(length=16, horizon=60, slip=0.1)
RANDOM = ENV.expected_return(np.zeros((16, 2)))
OPT = ENV.expected_return(np.tile([-30.0, 30.0], (16, 1)))


def part_a(seeds=8, updates=400):
    print(f"A. controlled lag, {seeds} seeds, {updates} updates, b=4 trajectories per update, lr=1.0")
    print(f"   expected return: random policy {RANDOM:.3f}, optimum about {OPT:.3f}")
    print(f"   {'lag':>4} {'update rule':>12} {'mean final':>11} {'worst run':>10} {'runs < 0.75':>12}")
    for lag in (0, 32, 128):
        for correct in (False, True):
            finals = [loop_sim.run(lag, correct, updates=updates, b=4, seed=s, env=ENV)["final"]
                      for s in range(seeds)]
            name = "clipped IS" if correct else "naive"
            print(f"   {lag:>4} {name:>12} {np.mean(finals):>11.3f} {min(finals):>10.3f} "
                  f"{sum(f < 0.75 for f in finals):>9d}/{seeds}")


def curve_demo(updates=400):
    print("   learning curve, seed 0 (expected return every 50 updates; reproducible bit for bit)")
    for lag, correct in ((0, False), (32, False), (32, True)):
        c = loop_sim.run(lag, correct, updates=updates, b=4, seed=0, env=ENV, eval_every=50)["curve"]
        name = "clipped IS" if correct else "naive"
        print(f"   lag={lag:>3} {name:>10}: " + " ".join(f"{v:5.2f}" for _, v in c[1:]))


def part_b():
    ray.init(num_cpus=4, include_dashboard=False, logging_level="ERROR", log_to_driver=False)
    print("B. real Ray actors (simulated env step 0.3 ms, simulated update 10 ms), queue mode, no credits")
    print(f"   {'N':>3} {'steps/s':>8} {'upd/s':>6} {'mean lag':>9} {'p95':>4} {'learner wait':>13} {'final return':>13}")
    base = dict(updates=100, mode="queue", step_cost_s=3e-4, update_cost_s=0.01)
    res = {}
    for n in (1, 2, 4, 8):
        r = res[n] = loop_ray.run_ray(n_actors=n, **base)
        print(f"   {n:>3} {r['steps_per_s']:>8.0f} {r['updates_per_s']:>6.1f} {r['mean_lag']:>9.2f} "
              f"{r['p95_lag']:>4.0f} {r['learner_wait_frac']:>13.2f} {r['final_return']:>13.2f}")
    for n, r in res.items():   # structure only: no assertion depends on a duration
        assert r["actors_seen"] == list(range(n)) and r["steps"] > 0, "every actor must contribute"
    print("   credits (N=16, simulated update 30 ms): staleness is bounded BEFORE the rollout")
    print(f"   {'K':>5} {'steps/s':>8} {'mean lag':>9} {'p95':>4} {'K/b':>5}")
    for k in (None, 8, 4):
        r = loop_ray.run_ray(n_actors=16, updates=100, mode="queue", credits=k, step_cost_s=3e-4,
                             update_cost_s=0.03)
        print(f"   {str(k):>5} {r['steps_per_s']:>8.0f} {r['mean_lag']:>9.2f} {r['p95_lag']:>4.0f} "
              f"{(k / 4 if k else float('nan')):>5.1f}")
    print("   replay (N=4, buffer 64 trajectories, b=4)")
    print(f"   {'ratio':>6} {'mean lag':>9} {'predicted (cap/2)/(b/ratio)':>28}")
    for ratio in (1.0, 2.0):
        r = loop_ray.run_ray(n_actors=4, updates=100, mode="replay", replay_ratio=ratio,
                             replay_capacity=64, step_cost_s=3e-4)
        print(f"   {ratio:>6.1f} {r['mean_lag']:>9.2f} {(32 / (4 / ratio)):>28.1f}")
    ray.shutdown()


if __name__ == "__main__":
    part_a()
    curve_demo()
    part_b()
    print("OK actor-learner-toy (report)")
    sys.exit(0)
