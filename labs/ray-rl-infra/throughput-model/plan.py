"""Size an actor-learner loop from the command line (lab 11.3).

Example:
  python3 plan.py --m 200 --t-roll 2.0 --t-sync 0.2 --b 4 --s-l 1.0 --queue-cap 8 \
      --actor-price-h 0.40 --learner-price-h 3.00
Prices are INPUTS that you read on a provider's price page the same day:
this script contains no real price.
"""
import argparse
import json

import model as M


def plan(m, t_roll, t_sync, b, s_L, queue_cap=8, credits=None, replay_ratio=1.0,
         actor_price_h=None, learner_price_h=None, actors=None):
    n_real = M.n_star(m, t_roll, t_sync, b, s_L, replay_ratio)
    n_int = M.actors_needed(m, t_roll, t_sync, b, s_L, replay_ratio)
    n = actors if actors is not None else n_int
    x = M.throughput(n, m, t_roll, t_sync, b, s_L, replay_ratio)
    produced = M.production_rate(n, m, t_roll, t_sync)
    capacity = M.consumption_capacity(b, m, s_L) / replay_ratio   # fresh steps/s once data is reused R times
    out = {
        "capacity_steps_s": M.consumption_capacity(b, m, s_L) / replay_ratio,
        "n_star": n_real,
        "actors_needed": n_int,
        "actors": n,
        "throughput_steps_s": x,
        "learner_util": min(1.0, produced / capacity),
        "actor_util": min(1.0, capacity / produced),
        "lag_block": M.lag_updates(n, m, t_roll, t_sync, b, s_L, "block", queue_cap),
        "lag_credit": M.lag_updates(n, m, t_roll, t_sync, b, s_L, "credit", None, credits),
    }
    if actor_price_h is not None and learner_price_h is not None:
        total = n * actor_price_h + learner_price_h
        out["price_per_hour"] = total
        out["cost_per_million_steps"] = M.cost_per_million_steps(total, x)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--m", type=float, required=True, help="environment steps per trajectory")
    ap.add_argument("--t-roll", type=float, required=True, help="seconds per trajectory on one actor")
    ap.add_argument("--t-sync", type=float, default=0.0, help="seconds to fetch the weights")
    ap.add_argument("--b", type=int, required=True, help="trajectories per learner update")
    ap.add_argument("--s-l", type=float, required=True, help="learner seconds per update")
    ap.add_argument("--queue-cap", type=int, default=8)
    ap.add_argument("--credits", type=int, default=None)
    ap.add_argument("--replay-ratio", type=float, default=1.0)
    ap.add_argument("--actors", type=int, default=None, help="force N instead of the minimum")
    ap.add_argument("--actor-price-h", type=float, default=None)
    ap.add_argument("--learner-price-h", type=float, default=None)
    a = ap.parse_args(argv)
    r = plan(a.m, a.t_roll, a.t_sync, a.b, a.s_l, a.queue_cap, a.credits, a.replay_ratio,
             a.actor_price_h, a.learner_price_h, a.actors)
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
