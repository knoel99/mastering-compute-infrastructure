"""Sweep the number of actors and the number of credits on the simulated loop (lab 11.3).

Example (exercise 11 of the course):
  python3 sweep.py --m 4096 --t-roll 120 --t-sync 1.683 --b 64 --s-l 90 --queue-cap 128 \
      --n 87 104 --credits 128 192 --horizon 60000 --seed 2
X/C is the simulated throughput divided by the learner capacity b*m/s_L.
"""
import argparse

import des
import model as M


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--m", type=float, required=True)
    ap.add_argument("--t-roll", type=float, required=True)
    ap.add_argument("--t-sync", type=float, default=0.0)
    ap.add_argument("--b", type=int, required=True)
    ap.add_argument("--s-l", type=float, required=True)
    ap.add_argument("--queue-cap", type=int, default=None)
    ap.add_argument("--n", type=int, nargs="+", required=True, help="numbers of actors")
    ap.add_argument("--credits", type=int, nargs="*", default=[], help="credit counts (policy credit)")
    ap.add_argument("--horizon", type=float, default=8000.0)
    ap.add_argument("--cv", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    cap = M.consumption_capacity(a.b, a.m, a.s_l)
    nstar = M.n_star(a.m, a.t_roll, a.t_sync, a.b, a.s_l)
    print(f"capacity C = {cap:.0f} steps/s ; N* = {nstar:.2f} ; lognormal durations, cv = {a.cv}, seed = {a.seed}")
    print(f"{'N':>5} {'policy':>8} {'K':>5} {'X/C':>6} {'learner busy':>13} {'lag mean':>9} {'lag p95':>8}")
    runs = [("block", None)] + [("credit", k) for k in a.credits]
    for n in a.n:
        for pol, k in runs:
            r = des.simulate(n, a.m, a.t_roll, a.t_sync, a.b, a.s_l, queue_cap=a.queue_cap, policy=pol,
                             credits=k, dist="lognormal", cv=a.cv, horizon=a.horizon, seed=a.seed)
            print(f"{n:>5} {pol:>8} {str(k or '-'):>5} {r['steps_per_s'] / cap:>6.3f} {r['learner_util']:>13.2f} "
                  f"{r['mean_lag']:>9.2f} {r['p95_lag']:>8.0f}")


if __name__ == "__main__":
    main()
