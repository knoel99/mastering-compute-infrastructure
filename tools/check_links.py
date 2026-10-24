#!/usr/bin/env python3
"""Check every external link of the site (courses, projects, pages, data/resources).

    python3 tools/check_links.py            # all pages
    python3 tools/check_links.py courses/perf-models     # only that page (the data/ links are skipped)
Classification: ok (2xx/3xx), blocked (401/403/429/999: the server refuses robots, link probably fine),
broken (404/410/DNS/connection error). Exit status 1 only when something is broken.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import fetch_text  # noqa: E402

LINK = re.compile(r"\]\((https?://[^)\s]+)\)|<(https?://[^>\s]+)>")


def urls_of(md_files, with_data=True):
    found = {}
    for f in md_files:
        for m in LINK.finditer(f.read_text(encoding="utf-8")):
            u = (m.group(1) or m.group(2)).rstrip(".,;")
            found.setdefault(u, set()).add(f.parent.relative_to(ROOT).as_posix() or "index")
    for jf in (ROOT / "data").glob("**/*.json") if with_data else ():
        if jf.name in ("curriculum.json", "nav.json"):
            continue
        for u in re.findall(r'"(?:url|urls?)"\s*:\s*"(https?://[^"]+)"', jf.read_text(encoding="utf-8")):
            found.setdefault(u, set()).add(jf.relative_to(ROOT).as_posix())
    return found


def probe(url):
    req = urllib.request.Request(url, headers={"User-Agent": fetch_text.UA, "Accept": "*/*"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30, context=fetch_text.ctx()) as r:
            r.read(2048)
            return "ok", r.status
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429, 999):
            return "blocked", e.code
        return ("broken" if e.code in (404, 410) else "blocked"), e.code
    except Exception as e:  # noqa: BLE001
        return "broken", type(e).__name__


def main(argv):
    if argv:
        mds = [ROOT / a.rstrip("/") / "index.md" for a in argv]
    else:
        mds = [p for p in ROOT.rglob("index.md") if p.relative_to(ROOT).parts[0] not in {"data", "specs", "tools", "labs", ".git"}]
    urls = urls_of(mds, with_data=not argv)
    with ThreadPoolExecutor(8) as ex:
        res = dict(zip(urls, ex.map(probe, urls)))
    bad = 0
    for u, (state, code) in sorted(res.items(), key=lambda kv: kv[1]):
        if state != "ok":
            print(f"{state.upper():8} {code}  {u}   <- {', '.join(sorted(urls[u]))[:90]}")
            bad += state == "broken"
    print(f"{sum(1 for s, _ in res.values() if s == 'ok')} ok, {sum(1 for s, _ in res.values() if s == 'blocked')} blocked, {bad} broken, {len(res)} total")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
