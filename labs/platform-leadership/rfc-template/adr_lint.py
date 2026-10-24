#!/usr/bin/env python3
"""Mechanical checks of an ADR (architecture decision record) of one page.

An ADR is judged by people; this linter only enforces what a machine can: the structure, a dated status, at least
two rejected alternatives with a reason, written positive AND negative consequences, a signal that would reopen the
decision, and a length that fits one page. For a full RFC see labs/projects/capstone-rfc (rfc_lint.py).
"""
import re
import sys

SECTIONS = ["Statut", "Contexte", "Décision", "Alternatives écartées", "Conséquences"]
STATUS = re.compile(r"^(Proposé|Accepté|Remplacé|Rejeté) le \d{4}-\d{2}-\d{2}\.?$")
FORBIDDEN = re.compile(r"\b(TODO|TBD|XXX|à compléter)\b", re.I)
BECAUSE = re.compile(r"parce qu(e |['’])", re.I)  # 'parce que' and the elisions 'parce qu'un', 'parce qu'elle'


def words(text):
    return len(re.findall(r"[A-Za-zÀ-ÿ]{2,}", text))


def section(text, title):
    m = re.search(rf"^## {re.escape(title)}\s*$", text, re.M)
    if not m:
        return None
    nxt = re.compile(r"^## ", re.M).search(text, m.end())
    return text[m.end(): nxt.start() if nxt else len(text)]


def lint(text):
    errs = []
    if not re.match(r"# ADR-\d{3} — \S", text):
        errs.append("the title must look like '# ADR-001 — title'")
    for t in SECTIONS:
        if section(text, t) is None:
            errs.append(f"missing section '## {t}'")
    n = words(text)
    if not 120 <= n <= 700:
        errs.append(f"{n} words (an ADR is one page: 120 to 700)")
    if FORBIDDEN.search(text):
        errs.append("unfinished marker (TODO/TBD/XXX/à compléter)")
    status = (section(text, "Statut") or "").strip().splitlines()
    if status and not STATUS.match(status[0].strip()):
        errs.append("Statut must be e.g. 'Accepté le 2026-03-02'")
    alts = [l for l in (section(text, "Alternatives écartées") or "").splitlines() if l.startswith("- ")]
    if len(alts) < 2:
        errs.append(f"{len(alts)} rejected alternatives (need >= 2)")
    for a in alts:
        if not BECAUSE.search(a):
            errs.append(f"alternative without a reason ('parce que' / 'parce qu''): {a[:50]}")
    cons = section(text, "Conséquences") or ""
    for kind in ("Positives", "Négatives"):
        block = re.search(rf"\*\*{kind}\*\*\s*:?\s*\n((?:\s*- .+\n?)+)", cons)
        if not block:
            errs.append(f"Conséquences needs a '**{kind}**' list with at least one item")
    if not re.search(r"Signal de révision\s*:\s*\S", cons):
        errs.append("Conséquences needs a line 'Signal de révision : ...' saying when to reopen the decision")
    return errs


def main():
    errs = lint(open(sys.argv[1], encoding="utf-8").read())
    for e in errs:
        print("-", e)
    print("adr: ok" if not errs else f"adr: {len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
