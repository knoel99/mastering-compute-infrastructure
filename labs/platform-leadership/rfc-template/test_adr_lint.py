from pathlib import Path

import pytest

import adr_lint

HERE = Path(__file__).parent
GOOD = (HERE / "example_adr.md").read_text(encoding="utf-8")


def errs(old, new):
    assert old in GOOD, old
    return adr_lint.lint(GOOD.replace(old, new, 1))


def test_the_example_adr_passes():
    assert adr_lint.lint(GOOD) == []


def test_the_blank_template_does_not_pass():
    assert adr_lint.lint((HERE / "adr_template.md").read_text(encoding="utf-8"))


@pytest.mark.parametrize("title", adr_lint.SECTIONS)
def test_each_missing_section_is_reported(title):
    mutated = GOOD.replace(f"## {title}\n", f"## Autre {title}\n")
    assert any(f"missing section '## {title}'" in e for e in adr_lint.lint(mutated))


def test_status_needs_a_known_word_and_a_date():
    assert any("Statut" in e for e in errs("Accepté le 2026-03-02.", "Accepté."))
    assert any("Statut" in e for e in errs("Accepté le 2026-03-02.", "Validé le 2026-03-02."))
    assert not any("Statut" in e for e in errs("Accepté le 2026-03-02.", "Remplacé le 2026-04-01"))


def test_at_least_two_alternatives_each_with_a_reason():
    only_one = GOOD.split("- **Pool réservé")[0] + "\n## Conséquences" + GOOD.split("## Conséquences")[1]
    assert any("rejected alternatives" in e for e in adr_lint.lint(only_one))
    assert any("without a reason" in e for e in errs("Écartée parce que le coût", "Écartée car le coût"))


def test_both_kinds_of_consequences_and_a_revision_signal():
    assert any("Négatives" in e for e in errs("**Négatives**", "**Autres**"))
    assert any("Positives" in e for e in errs("**Positives**", "**Bien**"))
    assert any("Signal de révision" in e for e in errs("Signal de révision :", "Remarque :"))
    assert any("Signal de révision" in e for e in errs("Signal de révision :", "Signal de révision seulement"))  # the colon is required


def test_title_length_and_unfinished_markers():
    assert any("title" in e for e in errs("# ADR-001 — ", "# Décision — "))
    assert any("unfinished" in e for e in errs("## Décision\n", "## Décision\n\nTODO.\n"))
    assert any("words" in e for e in adr_lint.lint("# ADR-001 — x\n\n## Statut\n\nAccepté le 2026-01-01.\n"))
    assert any("words" in e for e in adr_lint.lint(GOOD + "\n" + "mot " * 800))
    assert any("words" in e for e in adr_lint.lint(GOOD.split("## Décision")[0]))  # about 100 words: still too short


def test_french_elision_counts_as_a_reason():
    assert adr_lint.BECAUSE.search("Écartée parce qu'un seul serveur")
    assert adr_lint.BECAUSE.search("Écartée parce qu\u2019elle change")
    assert not adr_lint.BECAUSE.search("Écartée car le coût")
    assert not adr_lint.BECAUSE.search("Écartée parce quelque chose")
