"""Print counters of the simulated loop in a log-like format (used by exercise 7 of the course).

The loop is ILLUSTRATIVE (simulated time, lognormal durations with cv 0.3, seed 7): these lines
come from des.py, they are not the logs of a real system.
"""
import sys

import des
import model as M

P = dict(m=256, t_roll=3.0, t_sync=0.2, b=4, s_L=0.5)
Q = 16


def main(argv):
    ns = [int(a) for a in argv] or [16, 32]
    print(f"# m={P['m']} steps/traj  b={P['b']} traj/update  queue capacity={Q}  policy=block")
    for n in ns:
        r = des.simulate(n, **P, queue_cap=Q, policy="block", dist="lognormal", cv=0.3,
                         horizon=3000.0, seed=7)
        print(f"N={n:<3d} steps/s={r['steps_per_s']:6.0f}  learner_busy={r['learner_util']:.2f}  "
              f"queue_len_mean={r['mean_queue_len']:5.1f}/{Q}  actors_blocked_mean={r['mean_blocked_actors']:5.1f}  "
              f"lag_mean={r['mean_lag']:5.2f}  lag_p95={r['p95_lag']:4.0f}")
    c = M.consumption_capacity(P["b"], P["m"], P["s_L"])
    print(f"# (for the solution) C={c:.0f} steps/s  N*={M.n_star(P['m'], P['t_roll'], P['t_sync'], P['b'], P['s_L']):.2f}")


if __name__ == "__main__":
    main(sys.argv[1:])
