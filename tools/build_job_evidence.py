#!/usr/bin/env python3
"""Turn the skill quotes of each job posting into `evidence` entries that tools/verify_quotes.py checks.

A posting's quotes must appear verbatim in the text of the page that was actually read: `source_url`
(an ATS JSON endpoint or the public page), else `url`. Postings withheld on purpose (no URL) get no evidence.
Existing `verified` flags are kept when the quote and URL are unchanged.
    python3 tools/build_job_evidence.py [data/jobs/<unit>.json ...]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build(p):
    url = p.get("source_url") or p.get("url")
    if not url:
        return []
    old = {(e.get("url"), e.get("quote")): e.get("verified") for e in p.get("evidence", [])}
    by_quote = {}
    for s in p.get("skills", []):
        by_quote.setdefault(s["quote"], []).append(f"{s['id']} ({s['level']})")
    ev = []
    for q, ids in by_quote.items():
        e = {"claim": "Skill(s): " + ", ".join(ids), "url": url, "quote": q, "source": "web"}
        if old.get((url, q)) is not None:
            e["verified"] = old[(url, q)]
        ev.append(e)
    return ev


def main(argv):
    files = [Path(a) for a in argv] or sorted((ROOT / "data" / "jobs").glob("*.json"))
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        n = 0
        for p in d.get("postings", []):
            p["evidence"] = build(p)
            n += len(p["evidence"])
        f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{f}: {len(d.get('postings', []))} postings, {n} evidence entries")


if __name__ == "__main__":
    main(sys.argv[1:])
