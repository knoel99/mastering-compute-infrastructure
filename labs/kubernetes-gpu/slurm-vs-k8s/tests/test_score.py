import random

import pytest

import score as sc

OPTIONS, CRITERIA, SCENARIOS = sc.load()
TABLE = sc.scores_of(CRITERIA)


def test_every_criterion_scores_every_option_between_1_and_5_with_a_justification():
    assert set(OPTIONS) == {"slurm", "k8s", "hybrid"}
    for name, c in CRITERIA.items():
        assert set(c["scores"]) == set(OPTIONS) == set(c["why"]), name
        assert all(isinstance(v, int) and 1 <= v <= 5 for v in c["scores"].values()), name
        assert all(len(w) > 20 for w in c["why"].values()), name


def test_scenarios_use_only_known_criteria_and_weights_in_range():
    for name, s in SCENARIOS.items():
        assert set(s["weights"]) == set(CRITERIA), name
        assert all(0 <= v <= 5 for v in s["weights"].values()) and sum(s["weights"].values()) > 0, name
        assert set(s.get("must", {})) <= set(CRITERIA), name


def test_score_is_a_weighted_mean_scaled_to_100():
    flat = {c: 1 for c in CRITERIA}
    assert sc.weighted({c: 5 for c in CRITERIA}, flat) == 100.0
    assert sc.weighted({c: 1 for c in CRITERIA}, flat) == 20.0
    assert sc.weighted({"a": 5, "b": 1}, {"a": 1, "b": 0}) == 100.0      # a zero weight removes the criterion


def test_all_zero_weights_are_rejected():
    with pytest.raises(ValueError):
        sc.weighted({"a": 3}, {"a": 0})


def test_raising_the_weight_of_a_criterion_where_an_option_is_above_its_own_mean_raises_its_score():
    rng = random.Random(5)
    for _ in range(200):
        w = {c: rng.randint(0, 5) for c in CRITERIA}
        w[next(iter(w))] += 1                                             # keep the total positive
        o = rng.choice(list(TABLE))
        mean = sc.weighted(TABLE[o], w) / 20.0                            # mean score on the 1..5 scale
        c = rng.choice(list(CRITERIA))
        if TABLE[o][c] > mean + 1e-9:
            w2 = dict(w); w2[c] += 1
            assert sc.weighted(TABLE[o], w2) > sc.weighted(TABLE[o], w)


def test_a_hard_requirement_removes_an_option_even_if_its_total_is_highest():
    table = {"a": {"x": 5, "y": 1}, "b": {"x": 3, "y": 4}}
    assert sc.winner(table, {"x": 5, "y": 1}, {}) == "a"
    assert sc.winner(table, {"x": 5, "y": 1}, {"y": 3}) == "b"
    assert sc.winner(table, {"x": 5, "y": 1}, {"y": 5}) is None


def test_sensitivity_is_deterministic_and_sums_to_one():
    s = SCENARIOS["research-lab"]
    a = sc.sensitivity(TABLE, s["weights"], s["must"], draws=500, seed=3)
    b = sc.sensitivity(TABLE, s["weights"], s["must"], draws=500, seed=3)
    assert a == b and abs(sum(a.values()) - 1.0) < 1e-9


def test_clear_cases_are_stable_and_contested_cases_are_visible():
    stab = {}
    for name, s in SCENARIOS.items():
        base = sc.winner(TABLE, s["weights"], s.get("must", {}))
        stab[name] = sc.sensitivity(TABLE, s["weights"], s.get("must", {}), draws=1500, seed=0)[base]
    assert stab["research-lab"] > 0.75 and stab["sovereign-hpc-center"] > 0.75 and stab["inference-first-startup"] > 0.75
    assert min(stab.values()) < 0.95          # at least one scenario is not a landslide


def test_breakeven_finds_the_weight_that_flips_the_decision():
    s = SCENARIOS["enterprise-platform"]
    w = sc.breakeven(TABLE, s["weights"], s.get("must", {}), "ops_cost")
    assert w is not None and w > s["weights"]["ops_cost"]
    flipped = dict(s["weights"], ops_cost=w)
    assert sc.winner(TABLE, flipped, s.get("must", {})) != sc.winner(TABLE, s["weights"], s.get("must", {}))
