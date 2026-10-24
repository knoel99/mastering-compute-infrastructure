#!/usr/bin/env python3
"""Weighted decision matrix with hard requirements and a sensitivity analysis.

score(option) = 100 * sum_c w_c * s_oc / (5 * sum_c w_c)           (s in 1..5, w >= 0, so the score is in [20, 100])

The matrix is a judgement, so the useful output is not the winner but how robust it is: `sensitivity` redraws every weight
(multiplied by a factor drawn uniformly in [1 - wj, 1 + wj]) and, with probability `p`, moves each score by +-1, then counts
how often each eligible option wins. A winner that survives these perturbations is a decision; one that does not is a debate.
"""
import argparse
import random
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent


def load(criteria_file=None, scenarios_file=None):
    c = yaml.safe_load(Path(criteria_file or HERE / "criteria.yaml").read_text())
    s = yaml.safe_load(Path(scenarios_file or HERE / "scenarios.yaml").read_text())["scenarios"]
    return c["options"], c["criteria"], s


def scores_of(criteria: dict) -> dict:
    """option -> criterion -> score"""
    opts = next(iter(criteria.values()))["scores"].keys()
    return {o: {c: v["scores"][o] for c, v in criteria.items()} for o in opts}


def weighted(option_scores: dict, weights: dict) -> float:
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("at least one weight must be positive")
    return 100.0 * sum(weights[c] * option_scores[c] for c in weights) / (5.0 * total)


def eligible(option_scores: dict, must: dict) -> bool:
    return all(option_scores[c] >= minimum for c, minimum in must.items())


def rank(table: dict, weights: dict, must: dict) -> list:
    """[(option, score, eligible)] sorted: eligible options first, then by decreasing score (ties: alphabetical)."""
    rows = [(o, weighted(s, weights), eligible(s, must)) for o, s in table.items()]
    return sorted(rows, key=lambda r: (not r[2], -r[1], r[0]))


def winner(table: dict, weights: dict, must: dict):
    top = rank(table, weights, must)[0]
    return top[0] if top[2] else None


def sensitivity(table: dict, weights: dict, must: dict, draws: int = 2000, seed: int = 0, wj: float = 0.5, p: float = 0.25) -> dict:
    """Share of random perturbations in which each option wins (None = no eligible option)."""
    rng = random.Random(seed)
    wins = {o: 0 for o in table}
    wins[None] = 0
    for _ in range(draws):
        w = {c: max(0.0, v * rng.uniform(1 - wj, 1 + wj)) for c, v in weights.items()}
        if sum(w.values()) == 0:
            continue
        t = {o: {c: min(5, max(1, s + (rng.choice((-1, 1)) if rng.random() < p else 0))) for c, s in sc.items()} for o, sc in table.items()}
        wins[winner(t, w, must)] += 1
    return {o: n / draws for o, n in wins.items() if n}


def breakeven(table: dict, weights: dict, must: dict, criterion: str, step: float = 0.05, limit: float = 50.0):
    """Smallest weight of `criterion` (others unchanged) at which the winner differs from the base winner, or None."""
    base = winner(table, weights, must)
    w = dict(weights)
    for k in range(int(limit / step) + 1):
        x = round(k * step, 10)
        w[criterion] = x
        if sum(w.values()) > 0 and winner(table, w, must) != base:
            return x
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--criteria")
    ap.add_argument("--scenarios")
    a = ap.parse_args()
    options, criteria, scenarios = load(a.criteria, a.scenarios)
    table = scores_of(criteria)
    print(f"{'scenario':<24} {'slurm':>6} {'k8s':>6} {'hybrid':>6}  {'winner':<8} {'margin':>6}  stability (share of {a.draws} perturbed draws won by each option)")
    for name, sc in scenarios.items():
        rows = rank(table, sc["weights"], sc.get("must", {}))
        by = {o: (s, ok) for o, s, ok in rows}
        win = rows[0][0] if rows[0][2] else "none"
        margin = rows[0][1] - rows[1][1] if len(rows) > 1 else 0.0
        cells = " ".join(f"{by[o][0]:>6.1f}" + ("" if by[o][1] else "x") for o in ("slurm", "k8s", "hybrid"))
        sens = sensitivity(table, sc["weights"], sc.get("must", {}), a.draws, a.seed)
        stab = ", ".join(f"{o} {100 * f:.0f}%" for o, f in sorted(sens.items(), key=lambda kv: -kv[1]))
        print(f"{name:<24} {cells}  {win:<8} {margin:>6.1f}  {stab}")
    print("x = ineligible (a hard requirement is not met); scores are in [20, 100]")


if __name__ == "__main__":
    main()
