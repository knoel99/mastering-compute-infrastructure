import os
import re

import pytest

import capacity
import rfc_lint

HERE = os.path.dirname(__file__)
IMPL = os.environ.get("IMPL", "starter")
REQ = capacity.load(os.path.join(HERE, "..", IMPL, "requirements.yaml"))
GOOD = open(os.path.join(HERE, "..", "reference", "rfc.md"), encoding="utf-8").read()  # fixed, independent of IMPL


def test_my_rfc_passes_the_linter():
    mine = open(os.path.join(HERE, "..", IMPL, "rfc.md"), encoding="utf-8").read()
    assert rfc_lint.lint(mine, REQ) == []


def test_the_reference_rfc_passes():
    assert rfc_lint.lint(GOOD, REQ) == []


def test_number_parsing_accepts_french_formats():
    assert rfc_lint.number("317 161") == 317161
    assert rfc_lint.number("2,7") == 2.7
    assert rfc_lint.number("1 349 040") == 1349040


@pytest.mark.parametrize("title", rfc_lint.SECTIONS)
def test_each_missing_section_is_reported(title):
    mutated = GOOD.replace(f"## {title}\n", f"## Renamed {title}\n")
    assert any(f"missing section '## {title}'" in e for e in rfc_lint.lint(mutated, REQ))


def errs_for(old, new):
    assert old in GOOD, old
    return rfc_lint.lint(GOOD.replace(old, new, 1), REQ)


def test_too_few_options():
    mutated = GOOD.replace("### Option C — ", "### Variante C — ").replace("### Option D — ", "### Variante D — ")
    assert any("2 options" in e for e in rfc_lint.lint(mutated, REQ))


def test_option_without_pros_and_cons():
    assert any("Inconvénients" in e for e in errs_for("Inconvénients : coût de **570 709 u**", "Remarque : coût de **570 709 u**"))


def test_weights_must_sum_to_100():
    assert any("weights sum" in e for e in errs_for("| Coût | 30 |", "| Coût | 20 |"))


def test_total_must_be_the_weighted_sum():
    assert any("Total of 'Option C'" in e for e in errs_for("| 2,7 | 3,0 | 4,3 | 3,7 |", "| 2,7 | 3,0 | 4,6 | 3,7 |"))


def test_scores_stay_between_1_and_5():
    assert any("between 1 and 5" in e for e in errs_for("| Coût | 30 | 1 | 1 | 5 | 1 |", "| Coût | 30 | 1 | 1 | 6 | 1 |"))


def test_risk_without_mitigation_and_bad_levels():
    assert any("without mitigation" in e for e in errs_for("| moyenne | élevée | règle de bascule", "| moyenne | élevée |  | règle de bascule"))
    assert any("probability and impact" in e for e in errs_for("| faible | élevée | somme de contrôle", "| rare | élevée | somme de contrôle"))


def test_at_least_five_risks():
    lines = [l for l in GOOD.splitlines() if l.startswith("| Perte de la seule") or l.startswith("| Les prix réels") or l.startswith("| Dépassement du budget")]
    mutated = GOOD
    for l in lines:
        mutated = mutated.replace(l + "\n", "")
    assert any("Risques needs a table" in e for e in rfc_lint.lint(mutated, REQ))


def test_text_cost_must_match_the_model():
    assert any("differs from the model" in e for e in errs_for("Coût mensuel total : 317 161 u", "Coût mensuel total : 300 000 u"))


def test_design_block_is_required():
    mutated = re.sub(r"```json.*?```", "", GOOD, flags=re.S)
    assert any("```json block" in e for e in rfc_lint.lint(mutated, REQ))


def test_design_violating_an_slo_is_rejected_even_if_the_cost_is_consistent():
    mutated = GOOD.replace('"dev": {"market": "reserved", "gpus": 4}', '"dev": {"market": "reserved", "gpus": 2}')
    mutated = mutated.replace("Coût mensuel total : 317 161 u", "Coût mensuel total : 308 401 u")
    errs = rfc_lint.lint(mutated, REQ)
    assert any("violates the SLO of: dev" in e for e in errs) and not any("differs from the model" in e for e in errs)


def test_design_over_budget_is_rejected():
    mutated = GOOD.replace('"pretrain": {"market": "spot"}', '"pretrain": {"market": "on_demand"}')
    mutated = mutated.replace("Coût mensuel total : 317 161 u", "Coût mensuel total : 580 388 u")
    assert any("over the budget" in e for e in rfc_lint.lint(mutated, REQ))


def test_limits_part_unfinished_marker_and_length():
    assert any("Hypothèses et limites" in e for e in errs_for("### Hypothèses et limites", "### Remarques"))
    assert any("unfinished marker" in e for e in errs_for("## Questions ouvertes\n", "## Questions ouvertes\n\nTODO\n"))
    assert any("words" in e for e in rfc_lint.lint("## Contexte\nbref\n", REQ))
