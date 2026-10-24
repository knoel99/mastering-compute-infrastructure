import json
import subprocess
import sys
from pathlib import Path

import pytest

import review
import sla

HERE = Path(__file__).resolve().parent.parent
ORIGINAL = (HERE / "fictional_contract.md").read_text(encoding="utf-8")
NEGOTIATED = (HERE / "fictional_contract_negotiated.md").read_text(encoding="utf-8")
RUBRIC = review.load_rubric(HERE / "rubric.yaml")
EXPECTED = json.loads((HERE / "expected.json").read_text())


def test_contracts_are_labelled_fictional():
    for text in (ORIGINAL, NEGOTIATED):
        assert "FICTIONAL" in text.splitlines()[0]


@pytest.mark.parametrize("name,text", [("fictional_contract.md", ORIGINAL), ("fictional_contract_negotiated.md", NEGOTIATED)])
def test_every_item_matches_the_answer_key(name, text):
    rep = review.review(text, RUBRIC)
    assert {f["id"]: f["status"] for f in rep["findings"]} == EXPECTED[name]["statuses"]
    assert rep["deal_breakers_red"] == EXPECTED[name]["deal_breakers_red"]


def test_negotiation_raises_the_score_and_clears_the_deal_breakers():
    a, b = review.review(ORIGINAL, RUBRIC), review.review(NEGOTIATED, RUBRIC)
    assert b["score"] > a["score"] + 40
    assert a["deal_breakers_red"] and not b["deal_breakers_red"]


def test_numbers_are_extracted_from_the_text():
    rep = {f["id"]: f for f in review.review(ORIGINAL, RUBRIC)["findings"]}
    assert rep["min_term"]["evidence"] == "36"
    assert rep["availability_target"]["evidence"] == "99.5"
    assert rep["credit_cap"]["evidence"] == "10"
    assert rep["liability"]["evidence"] == "3"
    assert rep["replacement_time"]["evidence"].startswith("missing")


def test_threshold_directions():
    item_hi = {"id": "x", "kind": "number", "pattern": r"T=(\d+)", "worse": "higher", "green": 10, "amber": 20}
    item_lo = {"id": "y", "kind": "number", "pattern": r"T=(\d+)", "worse": "lower", "green": 20, "amber": 10}
    assert [review.evaluate(item_hi, "T=%d" % v)[0] for v in (5, 15, 30)] == ["green", "amber", "red"]
    assert [review.evaluate(item_lo, "T=%d" % v)[0] for v in (25, 15, 5)] == ["green", "amber", "red"]


def test_score_is_bounded_and_weighted():
    rep = review.review(NEGOTIATED, RUBRIC)
    assert 0.0 <= rep["score"] <= 100.0
    all_green = review.review("", {"categories": ["c"], "items": [
        {"id": "f", "category": "c", "weight": 1, "kind": "flag", "red_if": ["zzz"], "title": "t", "ask": "a"}]})
    assert all_green["score"] == 100.0


def test_negotiation_list_puts_red_first_then_weight():
    order = review.to_negotiate(review.review(ORIGINAL, RUBRIC))
    statuses = [f["status"] for f in order]
    assert statuses == sorted(statuses, key=lambda s: {"red": 0, "amber": 1}[s])
    reds = [f["weight"] for f in order if f["status"] == "red"]
    assert reds == sorted(reds, reverse=True)


def test_cli_exit_status_reflects_deal_breakers():
    cmd = [sys.executable, str(HERE / "review.py"), str(HERE / "rubric.yaml")]
    bad = subprocess.run([sys.executable, str(HERE / "review.py"), str(HERE / "fictional_contract.md"), str(HERE / "rubric.yaml")], capture_output=True, text=True)
    good = subprocess.run([sys.executable, str(HERE / "review.py"), str(HERE / "fictional_contract_negotiated.md"), str(HERE / "rubric.yaml")], capture_output=True, text=True)
    assert bad.returncode == 1 and good.returncode == 0 and "contract score" in good.stdout


def test_availability_per_node_hour():
    # one node of 64 down for 36 h in a 30-day month
    assert sla.monthly_availability(36, 64, 30) == pytest.approx(1 - 36 / (64 * 720))


def test_credit_tiers_and_cap():
    tiers = [(99.5, 5), (99.0, 10)]
    assert sla.credit_percent(99.9, tiers) == 0
    assert sla.credit_percent(99.3, tiers) == 5
    assert sla.credit_percent(98.0, tiers) == 10
    assert sla.credit_percent(90.0, tiers, cap=10) == 10


def test_credit_is_far_below_the_value_of_the_lost_training_time():
    # 64 nodes x 8 GPUs, price 3.0 u per GPU-hour, 36 h of one node down stops the whole 512-GPU job
    availability = 100 * sla.monthly_availability(36, 64, 30)
    credit = sla.credit_value(512 * 720 * 3.0, sla.credit_percent(availability, [(99.5, 5), (99.0, 10)], cap=10))
    lost = sla.lost_training_value(512, 36, 3.0)
    assert credit == 0.0 and lost == pytest.approx(55296.0)
