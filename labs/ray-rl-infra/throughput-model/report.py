"""Lab 11.3 report: the tables quoted in chapter 6 of the course (simulated time, seed 1)."""
import model as M
import des

P = dict(m=200, t_roll=2.0, t_sync=0.2, b=4, s_L=1.0)   # an ILLUSTRATIVE loop, not a measured system
Q, K = 8, 8
SIM = dict(dist="lognormal", cv=0.3, horizon=8000, seed=1)


def main():
    cap = M.consumption_capacity(P["b"], P["m"], P["s_L"])
    ns = M.n_star(P["m"], P["t_roll"], P["t_sync"], P["b"], P["s_L"])
    print(f"loop: m={P['m']} steps/traj, t_roll={P['t_roll']} s, t_sync={P['t_sync']} s, "
          f"b={P['b']} traj/update, s_L={P['s_L']} s")
    print(f"learner capacity C = {cap:.0f} steps/s ; N* = {ns:.2f} -> {M.actors_needed(**P)} actors")
    print()
    print(f"{'N':>3} {'P':>6} {'X model':>8} {'X sim':>7} {'util':>5} {'lag mod':>8} "
          f"{'lag sim':>8} {'blocked':>8} | {'credit X':>8} {'credit lag':>10} {'model':>6}")
    worst = 0.0
    for n in (2, 4, 6, 8, 10, 12, 16, 24):
        p = M.production_rate(n, P["m"], P["t_roll"], P["t_sync"])
        x = M.throughput(n, **P)
        blk = des.simulate(n, **P, queue_cap=Q, policy="block", **SIM)
        cre = des.simulate(n, **P, queue_cap=Q, policy="credit", credits=K, **SIM)
        lm = M.lag_updates(n, **P, policy="block", queue_cap=Q)
        lc = M.lag_updates(n, **P, policy="credit", credits=K)
        worst = max(worst, abs(blk["steps_per_s"] - x) / x)
        print(f"{n:>3} {p:>6.0f} {x:>8.0f} {blk['steps_per_s']:>7.0f} {blk['learner_util']:>5.2f} "
              f"{lm:>8.2f} {blk['mean_lag']:>8.2f} {blk['mean_blocked_actors']:>8.1f} | "
              f"{cre['steps_per_s']:>8.0f} {cre['mean_lag']:>10.2f} {lc:>6.2f}")
    print()
    print(f"credits for a lag target of 2 updates: K = {M.credits_for_lag(2.0, P['b'])}")
    print()
    print("credit policy, N = 24 actors: how many credits K?")
    print(f"{'K':>3} {'X sim':>7} {'learner util':>13} {'lag model':>10} {'lag sim':>8} {'p95 lag':>8}")
    for k in (8, 10, 12, 14, 16, 24):
        r = des.simulate(24, **P, queue_cap=Q, policy="credit", credits=k, **SIM)
        print(f"{k:>3} {r['steps_per_s']:>7.0f} {r['learner_util']:>13.2f} "
              f"{M.lag_updates(24, **P, policy='credit', credits=k):>10.2f} {r['mean_lag']:>8.2f} {r['p95_lag']:>8.0f}")
    print(f"largest |X sim - X model| / X model over the table: {worst:.1%}")
    assert worst < 0.06, "model and simulation disagree on throughput"


if __name__ == "__main__":
    main()
