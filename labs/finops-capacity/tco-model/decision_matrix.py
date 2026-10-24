#!/usr/bin/env python3
"""Weighted decision matrix and its robustness to the weights (all inputs FICTIONAL, see the module page).

scores: {option: {criterion: score on a 0-10 scale, higher is better}}; weights: {criterion: weight >= 0}.
"""
import random


def normalize(weights):
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def total_scores(scores, weights):
    w = normalize(weights)
    return {opt: sum(w[c] * s[c] for c in w) for opt, s in scores.items()}


def rank(scores, weights):
    t = total_scores(scores, weights)
    return sorted(t, key=lambda o: -t[o])


def win_probability(scores, weights, rel=0.5, draws=5000, seed=0):
    """Share of random weight vectors (each weight multiplied by U(1-rel, 1+rel)) in which each option ranks first."""
    rng = random.Random(seed)
    wins = {o: 0 for o in scores}
    for _ in range(draws):
        w = {k: v * rng.uniform(1 - rel, 1 + rel) for k, v in weights.items()}
        wins[rank(scores, w)[0]] += 1
    return {o: n / draws for o, n in wins.items()}


def flip_weight(scores, weights, criterion, step=0.01):
    """Smallest multiplier (searched upward from 1 in steps) of one weight that changes the winner; None if none up to x10."""
    base = rank(scores, weights)[0]
    f = 1.0
    while f <= 10.0:
        w = dict(weights)
        w[criterion] = weights[criterion] * f
        if rank(scores, w)[0] != base:
            return round(f, 2)
        f += step
    return None


# FICTIONAL example of chapter 8 of the module page: invented scores (0-10) and weights.
EXAMPLE_SCORES = {
    "own_colo": {"cost_at_high_util": 9, "flexibility": 3, "time_to_capacity": 3, "ops_load": 3, "risk_supply": 4},
    "lease_3y": {"cost_at_high_util": 7, "flexibility": 4, "time_to_capacity": 7, "ops_load": 7, "risk_supply": 6},
    "reserved_1y": {"cost_at_high_util": 5, "flexibility": 6, "time_to_capacity": 8, "ops_load": 8, "risk_supply": 6},
    "on_demand_spot": {"cost_at_high_util": 3, "flexibility": 10, "time_to_capacity": 6, "ops_load": 9, "risk_supply": 3},
}
EXAMPLE_WEIGHTS = {"cost_at_high_util": 3, "flexibility": 2, "time_to_capacity": 2, "ops_load": 1, "risk_supply": 2}


def main():
    t = total_scores(EXAMPLE_SCORES, EXAMPLE_WEIGHTS)
    print("weighted totals (FICTIONAL scores): " + "  ".join("%s %.2f" % (o, t[o]) for o in rank(EXAMPLE_SCORES, EXAMPLE_WEIGHTS)))
    p = win_probability(EXAMPLE_SCORES, EXAMPLE_WEIGHTS, rel=0.5, draws=5000, seed=0)
    print("first place in 5000 random weight vectors (+/-50%): " + "  ".join("%s %.1f%%" % (o, 100 * v) for o, v in p.items()))
    print("weight multiplier that changes the winner: " + "  ".join("%s %s" % (c, flip_weight(EXAMPLE_SCORES, EXAMPLE_WEIGHTS, c)) for c in EXAMPLE_WEIGHTS))


if __name__ == "__main__":
    main()
