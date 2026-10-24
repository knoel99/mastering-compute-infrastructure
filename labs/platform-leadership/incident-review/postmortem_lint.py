#!/usr/bin/env python3
"""Mechanical checks of a post-mortem, including consistency with the incident log it describes.

A post-mortem is judged by people; this linter only enforces structure (blameless sections, a timeline, actions that
have an owner, a date and a verification) and that the durations written in the text equal those computed from the
log. The blame vocabulary check is a hint, not a verdict.
"""
import argparse
import re
import sys

import timeline

SECTIONS = ["Résumé", "Impact", "Chronologie", "Cause racine", "Facteurs contributifs", "Ce qui a bien marché",
            "Ce qui a mal marché", "Actions", "Leçons"]
# 'par erreur de' is flagged only before a capitalised name (a person); the group is case-sensitive although the rest is not.
# 'faute de' (= for lack of) is NOT flagged: "faute de métrique" describes the system.
BLAME = re.compile(r"\b(a oublié|ont oublié|par négligence|incompétent|par erreur de (?-i:[A-Z][a-z]+)|c['’]est la faute|sa faute|leur faute)\b", re.I)
FORBIDDEN = re.compile(r"\b(TODO|TBD|XXX|à compléter)\b", re.I)


def section(text, title):
    m = re.search(rf"^## {re.escape(title)}\s*$", text, re.M)
    if not m:
        return None
    nxt = re.compile(r"^## ", re.M).search(text, m.end())
    return text[m.end(): nxt.start() if nxt else len(text)]


def table(block):
    rows = []
    for line in block.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                rows.append(cells)
        elif rows:
            break
    return rows


def minutes_of(text, label):
    m = re.search(rf"{label}\s*:\s*(?:(\d+) h\s*)?(\d+) min", text)
    return None if not m else int(m.group(1) or 0) * 60 + int(m.group(2))


def lint(text, events=None, gpus=None):
    errs = []
    for t in SECTIONS:
        if section(text, t) is None:
            errs.append(f"missing section '## {t}'")
    n = len(re.findall(r"[A-Za-zÀ-ÿ]{2,}", text))
    if not 300 <= n <= 1500:
        errs.append(f"{n} words (expected 300-1500)")
    if FORBIDDEN.search(text):
        errs.append("unfinished marker (TODO/TBD/XXX/à compléter)")
    if (section(text, "Chronologie") or "") and len(re.findall(r"\b\d{2}:\d{2}\b", section(text, "Chronologie"))) < 6:
        errs.append("Chronologie needs at least 6 timestamped lines (HH:MM)")
    impact = section(text, "Impact") or ""
    if len(re.findall(r"\d", impact)) < 4 or "GPU-heures" not in impact:
        errs.append("Impact must quantify the loss in GPU-heures")
    for t in ("Résumé", "Cause racine", "Facteurs contributifs"):
        if BLAME.search(section(text, t) or ""):
            errs.append(f"'{t}' contains blame vocabulary: describe the system, not the person")
    actions = table(section(text, "Actions") or "")
    if len(actions) < 4 or [c.lower() for c in actions[0][:4]] != ["action", "propriétaire", "échéance", "vérification"]:
        errs.append("Actions needs a table | Action | Propriétaire | Échéance | Vérification | with >= 3 rows")
    else:
        for r in actions[1:]:
            if len(r) < 4 or not all(r[:4]):
                errs.append(f"action with an empty field: {r[0][:40]}")
            elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", r[2]):
                errs.append(f"action '{r[0][:30]}': Échéance must be YYYY-MM-DD")
            elif len(r[3].split()) < 3:
                errs.append(f"action '{r[0][:30]}': Vérification must say how success is checked")
    if events is not None:
        d = timeline.durations(events)
        for label, key in (("Délai de détection", "ttd"), ("Délai d'acquittement", "tta"), ("Délai d'atténuation", "ttm")):
            got = minutes_of(text, label)
            if got is None:
                errs.append(f"the text must state '{label} : X h YY min'")
            elif abs(got - d[key] / 60.0) > 1:
                errs.append(f"'{label}' says {got} min, the log gives {d[key] / 60.0:.0f} min")
        if gpus:
            m = re.search(r"GPU-heures sans progression\s*:\s*([\d\s,.]+)", impact)
            if not m:
                errs.append("Impact must state 'GPU-heures sans progression : N'")
            else:
                got = float(re.sub(r"\s", "", m.group(1)).replace(",", ".").rstrip("."))
                want = timeline.gpu_hours_idle(gpus, events)
                if abs(got - want) > 0.01 * want:
                    errs.append(f"GPU-heures sans progression: text says {got}, the log gives {want:.1f}")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("postmortem")
    ap.add_argument("--log")
    ap.add_argument("--gpus", type=int)
    a = ap.parse_args()
    events = timeline.parse(open(a.log, encoding="utf-8").read()) if a.log else None
    errs = lint(open(a.postmortem, encoding="utf-8").read(), events, a.gpus)
    for e in errs:
        print("-", e)
    print("postmortem: ok" if not errs else f"postmortem: {len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
