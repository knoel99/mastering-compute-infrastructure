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
    errs = []
    for t in SECTIONS:
        if section(text, t) is None:
            errs.append(f"missing section '## {t}'")
    if not 1500 <= words(text) <= 8000:
        errs.append(f"{words(text)} words (expected 1500-8000)")
    if FORBIDDEN.search(text):
        errs.append("unfinished marker (TODO/TBD/XXX/à compléter)")

    opts = section(text, "Options considérées") or ""
    heads = re.findall(r"^### Option ([A-Z]) — .+$", opts, re.M)
    if len(heads) < 3:
        errs.append(f"{len(heads)} options (need >= 3, each '### Option X — title')")
    for body in re.split(r"^### Option ", opts, flags=re.M)[1:]:
        for w in ("Avantages", "Inconvénients"):
            if w not in body:
                errs.append(f"an option lacks '{w}'")

    dec = table(section(text, "Décision") or "")
    if len(dec) < 4 or [c.lower() for c in dec[0][:2]] != ["critère", "poids"]:
        errs.append("Décision needs a table starting with | Critère | Poids | then one column per option")
    else:
        body = [r for r in dec[1:] if r[0].lower() != "total"]
        try:
            weights = [number(r[1]) for r in body]
            if abs(sum(weights) - 100) > 1e-9:
                errs.append(f"decision weights sum to {sum(weights):g}, not 100")
            total_row = next((r for r in dec[1:] if r[0].lower() == "total"), None)
            if total_row is None:
                errs.append("Décision table needs a Total row")
            else:
                for j in range(2, len(dec[0])):
                    scores = [number(r[j]) for r in body]
                    if not all(1 <= s <= 5 for s in scores):
                        errs.append(f"scores of column '{dec[0][j]}' must be between 1 and 5")
                    expected = sum(w * s for w, s in zip(weights, scores)) / 100.0
                    if abs(number(total_row[j]) - expected) > 0.005:
                        errs.append(f"Total of '{dec[0][j]}' is {total_row[j]}, weighted sum is {expected:.2f}")
        except (ValueError, IndexError):
            errs.append("Décision table has a non-numeric weight or score")

    risks = table(section(text, "Risques") or "")
    if len(risks) < 6 or [c.lower() for c in risks[0][:4]] != ["risque", "probabilité", "impact", "mitigation"]:
        errs.append("Risques needs a table | Risque | Probabilité | Impact | Mitigation | with >= 5 rows")
    else:
        for r in risks[1:]:
            if len(r) < 4 or not r[3].strip():
                errs.append(f"risk without mitigation: {r[0][:40]}")
            elif r[1].lower() not in LEVELS or r[2].lower() not in LEVELS:
                errs.append(f"risk '{r[0][:40]}': probability and impact must be in {sorted(LEVELS)}")

    cap = section(text, "Capacité et coûts") or ""
    m = re.search(r"```json\s*(\{.*?\})\s*```", cap, re.S)
    if not m:
        errs.append("Capacité et coûts needs the design as a ```json block")
    else:
        try:
            design = json.loads(m.group(1))
            result = capacity.evaluate(req, design)
            cm = re.search(r"Coût mensuel total\s*:\s*([\d\s  .,]+?)\s*u\b", cap)
            if not cm:
                errs.append("Capacité et coûts must state 'Coût mensuel total : N u'")
            elif abs(number(cm.group(1)) - result["cost_u"]) > 0.005 * result["cost_u"]:
                errs.append(f"stated cost {cm.group(1)} u differs from the model ({result['cost_u']:.0f} u)")
            if not result["within_budget"]:
                errs.append("the chosen design is over the budget of the requirements")
            if not result["all_slo_ok"]:
                bad = [k for k, v in result["classes"].items() if not v["slo_ok"]]
                errs.append(f"the chosen design violates the SLO of: {', '.join(bad)}")
        except (ValueError, KeyError, TypeError, AttributeError, ArithmeticError) as exc:
            errs.append(f"design block cannot be evaluated: {exc}")
    if not re.search(r"^#{3,4} Hypothèses et limites\s*$", cap, re.M):  # a heading, not a passing mention
        errs.append("Capacité et coûts needs a '### Hypothèses et limites' part")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rfc")
    ap.add_argument("--requirements", default="requirements.yaml")
    a = ap.parse_args()
    errs = lint(open(a.rfc, encoding="utf-8").read(), capacity.load(a.requirements))
    for e in errs:
        print("-", e)
    print("rfc: ok" if not errs else f"rfc: {len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
