#!/usr/bin/env python3
"""Score a GPU capacity contract against rubric.yaml. Deterministic: regular expressions, no model.

Usage: python3 review.py CONTRACT.md RUBRIC.yaml [--json] [--fail-below SCORE]
Exit status 1 when a deal-breaker item is red or the score is below --fail-below.
"""
import argparse
import json
import re
import sys

import yaml

POINTS = {"green": 1.0, "amber": 0.5, "red": 0.0}


def load_rubric(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def evaluate(item, text):
    """Return (status, evidence). Status is green, amber or red."""
    kind = item["kind"]
    if kind == "number":
        m = re.search(item["pattern"], text)
        if not m:
            return "red", "missing: no number found"
        value = float(m.group(1))
        if item["worse"] == "higher":
            status = "green" if value <= item["green"] else "amber" if value <= item["amber"] else "red"
        else:
            status = "green" if value >= item["green"] else "amber" if value >= item["amber"] else "red"
        return status, "%g" % value
    for pat in item.get("green_if", []):
        if re.search(pat, text):
            return "green", re.search(pat, text).group(0)
    for key, status in (("red_if", "red"), ("amber_if", "amber")):
        for pat in item.get(key, []):
            m = re.search(pat, text)
            if m:
                return status, m.group(0)
    return "green", ""


def review(text, rubric):
    findings = []
    for item in rubric["items"]:
        status, evidence = evaluate(item, text)
        findings.append({"id": item["id"], "title": item["title"], "category": item["category"], "weight": item["weight"],
                         "deal_breaker": bool(item.get("deal_breaker")), "status": status, "evidence": evidence, "ask": item["ask"]})
    total = sum(f["weight"] for f in findings)
    score = 100.0 * sum(f["weight"] * POINTS[f["status"]] for f in findings) / total
    by_cat = {}
    for c in rubric["categories"]:
        fs = [f for f in findings if f["category"] == c]
        by_cat[c] = 100.0 * sum(f["weight"] * POINTS[f["status"]] for f in fs) / sum(f["weight"] for f in fs)
    blockers = [f["id"] for f in findings if f["deal_breaker"] and f["status"] == "red"]
    return {"score": score, "by_category": by_cat, "deal_breakers_red": blockers, "findings": findings}


def to_negotiate(report):
    """Findings that are not green, most important first (red before amber, then weight)."""
    rank = {"red": 0, "amber": 1}
    fs = [f for f in report["findings"] if f["status"] != "green"]
    return sorted(fs, key=lambda f: (rank[f["status"]], -f["weight"], f["id"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("contract")
    ap.add_argument("rubric")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-below", type=float, default=None)
    a = ap.parse_args(argv)
    text = open(a.contract, encoding="utf-8").read()
    report = review(text, load_rubric(a.rubric))
    if a.json:
        json.dump(report, sys.stdout, indent=1)
        print()
    else:
        n = {s: sum(f["status"] == s for f in report["findings"]) for s in POINTS}
        print("contract score %.0f/100  (%d green, %d amber, %d red)" % (report["score"], n["green"], n["amber"], n["red"]))
        print("by category: " + "  ".join("%s %.0f" % (c, v) for c, v in report["by_category"].items()))
        print("deal-breakers red: %s" % (", ".join(report["deal_breakers_red"]) or "none"))
        for f in to_negotiate(report):
            print("%-5s w%d %-22s %s  [%s]" % (f["status"].upper(), f["weight"], f["id"], f["title"], f["evidence"][:48]))
    bad = bool(report["deal_breakers_red"]) or (a.fail_below is not None and report["score"] < a.fail_below)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
