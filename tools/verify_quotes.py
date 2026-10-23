#!/usr/bin/env python3
"""Mechanically verify research evidence: every web quote must appear verbatim in the cited page.

For each data/{masters,jobs,resources}/*.json (except synthesis.json) the script re-reads each evidence
URL through tools/fetch_text.py (same cache as the researchers) and checks that the quote is a substring
of the page text after normalisation (case, spaces, punctuation and typographic variants ignored).

    python3 tools/verify_quotes.py                       # report only
    python3 tools/verify_quotes.py --write               # write evidence[].verified, recompute confidence
    python3 tools/verify_quotes.py data/masters/fr-a.json --write
Writing rules: programme/posting confidence = high if >= 75 % of its web evidence is verified, medium if
>= 40 %, else low; memory-sourced evidence never counts as verified. Unreachable pages are listed.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import fetch_text  # noqa: E402


def norm(s):
    s = unicodedata.normalize("NFKC", s).lower()
    s = s.replace("’", "'").replace("‘", "'")
    return re.sub(r"[\W_]+", "", s)


def check(url, quote, cache):
    if url not in cache:
        try:
            cache[url] = fetch_text.get(url)[0]
        except Exception as e:  # noqa: BLE001
            cache[url] = None
            print(f"   unreachable {url}: {type(e).__name__}")
    text = cache[url]
    if text is None:
        return None
    return norm(quote) in norm(text)


def evidence_items(d):
    for p in d.get("programmes", []) + d.get("postings", []):
        yield p, p.get("evidence", [])
    for e in d.get("ecosystem", []):
        yield e, e.get("evidence", [])
    for it in d.get("items", []):
        ev = it.get("evidence")
        yield it, [ev] if isinstance(ev, dict) else (ev or [])


def conf(frac):
    return "high" if frac >= 0.75 else "medium" if frac >= 0.40 else "low"


def main(argv):
    write = "--write" in argv
    args = [a for a in argv if not a.startswith("--")]
    files = [Path(a).resolve() for a in args] or sorted((ROOT / "data").glob("masters/*.json")) + sorted((ROOT / "data").glob("jobs/*.json")) + sorted((ROOT / "data").glob("resources/*.json"))
    cache = {}
    tot_ok = tot = 0
    for f in files:
        if f.name == "synthesis.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        ok = n = unreach = 0
        for owner, evs in evidence_items(d):
            o = m = 0
            for e in evs:
                if e.get("source", "web") != "web":
                    continue
                m += 1
                r = check(e.get("url", ""), e.get("quote", ""), cache)
                e["verified"] = bool(r) if r is not None else False
                if r is None:
                    unreach += 1
                    e["verified"] = False
                o += bool(r)
            n += m
            ok += o
            if write and m and "confidence" in owner:
                owner["confidence"] = conf(o / m)
            if write and m:
                owner["evidence_verified"] = f"{o}/{m}"
        tot += n
        tot_ok += ok
        print(f"{f.relative_to(ROOT)}: {ok}/{n} web quotes verbatim ({unreach} on unreachable pages)")
        if write:
            v = d.setdefault("verification", {})
            v.update({"status": "verified", "checked_claims": n, "verified_quotes": ok, "method": "tools/verify_quotes.py (verbatim substring in cached page text)"})
            f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"TOTAL {tot_ok}/{tot} verified" + (" (written)" if write else " (dry run)"))


if __name__ == "__main__":
    main(sys.argv[1:])
