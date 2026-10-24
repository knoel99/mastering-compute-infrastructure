import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import decision_matrix as dm  # noqa: E402

SCORES = {"A": {"cost": 9, "speed": 3}, "B": {"cost": 5, "speed": 7}}


def test_weights_are_normalized_and_ranking_follows_them():
    assert dm.normalize({"cost": 2, "speed": 2}) == {"cost": 0.5, "speed": 0.5}
    assert dm.rank(SCORES, {"cost": 3, "speed": 1})[0] == "A"
    assert dm.rank(SCORES, {"cost": 1, "speed": 3})[0] == "B"


def test_total_scores_hand_computed():
    t = dm.total_scores(SCORES, {"cost": 1, "speed": 1})
    assert t["A"] == pytest.approx(6.0) and t["B"] == pytest.approx(6.0)


def test_win_probabilities_sum_to_one_and_split_when_options_tie():
    p = dm.win_probability(SCORES, {"cost": 1, "speed": 1}, rel=0.5, draws=2000, seed=1)
    assert sum(p.values()) == pytest.approx(1.0) and 0.3 < p["A"] < 0.7


def test_flip_weight_finds_the_tipping_point():
    f = dm.flip_weight(SCORES, {"cost": 2, "speed": 1}, "speed")
    assert f is not None and 1.0 < f < 4.0
    assert dm.flip_weight(SCORES, {"cost": 100, "speed": 1}, "cost") is None


def test_the_example_of_the_module_page():
    assert dm.rank(dm.EXAMPLE_SCORES, dm.EXAMPLE_WEIGHTS)[0] == "reserved_1y"
    t = dm.total_scores(dm.EXAMPLE_SCORES, dm.EXAMPLE_WEIGHTS)
    assert t["reserved_1y"] == pytest.approx(6.3) and t["lease_3y"] == pytest.approx(6.2)
    p = dm.win_probability(dm.EXAMPLE_SCORES, dm.EXAMPLE_WEIGHTS, rel=0.5, draws=5000, seed=0)
    assert 0.55 < p["reserved_1y"] < 0.72 and p["own_colo"] == 0.0
    assert 1.1 < dm.flip_weight(dm.EXAMPLE_SCORES, dm.EXAMPLE_WEIGHTS, "cost_at_high_util") < 1.3
