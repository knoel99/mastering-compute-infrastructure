#!/usr/bin/env python3
"""Mechanical checks of an RFC (markdown), including consistency between the text and the capacity model.

A good RFC is judged by a human review grid; this linter only catches what a machine can: missing sections,
too few options, weights that do not sum to 100, a total that is not the weighted sum, risks without mitigation,
and a monthly cost in the text that disagrees with the model evaluated on the design embedded in the RFC.
"""
import argparse
import json
import re
import sys

import capacity

SECTIONS = ["Contexte", "Objectifs et non-objectifs", "Exigences", "Options considérées", "Décision",
            "Capacité et coûts", "Fiabilité", "Observabilité", "Sécurité", "Migration", "Risques",
            "Questions ouvertes", "Annexes"]
LEVELS = {"faible", "moyenne", "élevée"}
FORBIDDEN = re.compile(r"\b(TODO|TBD|XXX|à compléter)\b", re.I)


def words(text):
    return len(re.findall(r"[A-Za-zÀ-ÿ]{2,}", text))


def section(text, title):
    m = re.search(rf"^## {re.escape(title)}\s*$", text, re.M)
    if not m:
        return None
    nxt = re.compile(r"^## ", re.M).search(text, m.end())
    return text[m.end(): nxt.start() if nxt else len(text)]


def table(block):
    """Rows of the first markdown table of `block` as lists of cells (header first, separator removed)."""
    rows = []
    for line in block.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                rows.append(cells)
        elif rows:
            break
    return rows


def number(s):
    return float(re.sub(r"[\s  ]", "", s).replace(",", "."))


def lint(text, req):
    """TO WRITE (milestone 4). Return a list of problem strings (empty = the RFC passes). Check, in this spirit:
    * every title of SECTIONS exists as a '## Title' line  -> "missing section '## Title'"
    * 1500 to 8000 words, no TODO/TBD/XXX/à compléter marker
    * Options considérées: at least 3 '### Option X — title', each with the words Avantages and Inconvénients
    * Décision: a table | Critère | Poids | option columns... | whose weights sum to 100, scores between 1 and 5,
      and a Total row equal to the weighted sum (sum(w x s) / 100) within 0.005
    * Risques: a table | Risque | Probabilité | Impact | Mitigation | with at least 5 rows, no empty mitigation,
      probability and impact in LEVELS
    * Capacité et coûts: a ```json design block that capacity.evaluate accepts, a line 'Coût mensuel total : N u'
      within 0.5 % of the model, a design inside the budget and inside every SLO, and a '### Hypothèses et limites' sub-heading
    The error messages are matched loosely by tests/test_rfc_lint.py; read it to see the wording it expects."""
    raise NotImplementedError


def main():
    raise NotImplementedError("print the problems, then 'rfc: ok' or 'rfc: N problem(s)'; exit 1 on problems")


if __name__ == "__main__":
    sys.exit(main())
