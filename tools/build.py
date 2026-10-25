#!/usr/bin/env python3
"""Render every index.md of the site to index.html with Pandoc.

The site is plain static HTML served by GitHub Pages straight from the branch
(.nojekyll, no CI): rendered pages are committed next to their Markdown source,
exactly like polytechnique-llga does with Quarto.

Usage (repository root):
    python3 tools/build.py                 # render everything
    python3 tools/build.py courses/slurm   # render some pages (directories or index.md paths)
    python3 tools/build.py --check         # render in memory; exit 1 if a committed page differs
Requires pandoc >= 3.1 (apt install pandoc) and PyYAML.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "data", "specs", "labs", "tools", "assets", ".build-tmp", "node_modules"}
KATEX = "https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/"
SITE_TITLE = "Mastering Compute Infrastructure"
# Pinned KaTeX tags with subresource integrity (same pins as polytechnique-llga).
JS_TAG = ('<script>window.backupDefine = window.define; window.define = undefined;</script>'
          f'<script src="{KATEX}katex.min.js" integrity="sha384-QFFtAGzvvj+bfgCGxXJlNZZR1nXEZgvG8tDLCCY1F19xl20WlfTYgguB4VcNdxYk" crossorigin="anonymous"></script>')
CSS_TAG = ('<script>window.define = window.backupDefine; window.backupDefine = undefined;</script>'
           f'<link rel="stylesheet" href="{KATEX}katex.min.css" integrity="sha384-3rdsX6e5mueWyoweR9NIVmtEsUkokpBT/0ALqKKIBMr9j4qhHkaIkAcGgsE6uVlp" crossorigin="anonymous">')
JS_RE = re.compile(r'<script\s+defer=""\s+src="' + re.escape(KATEX) + r'katex\.min\.js"></script>|<script\s+defer\s+src="' + re.escape(KATEX) + r'katex\.min\.js"></script>')
CSS_RE = re.compile(r'<link\s+rel="stylesheet"\s+href="' + re.escape(KATEX) + r'katex\.min\.css"\s*/?>')


def sources(args):
    if args:
        out = []
        for a in args:
            p = (ROOT / a).resolve()
            out.append(p if p.name == "index.md" else p / "index.md")
        return out
    found = []
    for p in sorted(ROOT.rglob("index.md")):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS or "_notes" in rel.parts:   # _notes holds source fragments, not pages
            continue
        found.append(p)
    return found


def load_nav():
    f = ROOT / "data" / "nav.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"sequence": []}


def split_front(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (yaml.safe_load(m.group(1)) or {}, text[m.end():]) if m else ({}, text)


def render(md: Path, nav) -> str:
    rel = md.parent.relative_to(ROOT)
    depth = len(rel.parts)
    root = "../" * depth
    meta, _ = split_front(md.read_text(encoding="utf-8"))
    href = (rel / "index.html").as_posix() if depth else "index.html"
    extra = {"root": root,
             "pagetitle": f"{meta.get('title', 'Page')} — {SITE_TITLE}" if depth else f"{SITE_TITLE}",
             "bodyclass": "has-sidetoc home" if not depth else "has-sidetoc"}
    seq = nav.get("sequence", [])
    idx = next((i for i, s in enumerate(seq) if s["href"] == href), None)
    if idx is not None:
        if idx > 0:
            extra["prev"] = seq[idx - 1]
        if idx + 1 < len(seq):
            extra["next"] = seq[idx + 1]
    if depth and "crumbs" not in meta:
        crumbs = [{"href": "index.html", "label": "Accueil"}]
        if rel.parts[0] == "courses":
            crumbs.append({"href": "index.html#cours", "label": "Cours"})
        elif rel.parts[0] == "projects":
            crumbs.append({"href": "index.html#projets", "label": "Projets"})
        elif rel.parts[0] == "masters" and depth > 1:
            crumbs.append({"href": "masters/index.html", "label": "Masters HPC"})
        extra["crumbs"] = crumbs
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as t:
        yaml.safe_dump(extra, t, allow_unicode=True)
        meta_file = t.name
    cmd = ["pandoc", "-f", "markdown-smart+fenced_divs+bracketed_spans+fenced_code_attributes+definition_lists",
           "-t", "html5", "--standalone", "--no-highlight" if False else "--highlight-style=pygments",
           f"--katex={KATEX}", "--template", str(ROOT / "tools" / "template.html"),
           "--lua-filter", str(ROOT / "tools" / "filters.lua"),
           "--metadata-file", meta_file, "--wrap=none", str(md)]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=md.parent)
    Path(meta_file).unlink(missing_ok=True)
    if res.returncode != 0:
        raise SystemExit(f"pandoc failed on {md}:\n{res.stderr}")
    html = res.stdout
    html = JS_RE.sub(lambda _: JS_TAG, html)
    html = CSS_RE.sub(lambda _: CSS_TAG, html)
    if "katex" in html.lower() and (JS_TAG not in html or CSS_TAG not in html):
        # a page with math must carry the two pinned tags; a page without math must carry none
        if 'class="math' in html:
            raise SystemExit(f"{md}: KaTeX tags not restored")
    return html


def main(argv):
    check = "--check" in argv
    args = [a for a in argv if not a.startswith("--")]
    nav = load_nav()
    stale = []
    for md in sources(args):
        html = render(md, nav)
        out = md.with_name("index.html")
        if check:
            if not out.exists() or out.read_text(encoding="utf-8") != html:
                stale.append(out.relative_to(ROOT).as_posix())
        else:
            out.write_text(html, encoding="utf-8")
            print("rendered", out.relative_to(ROOT).as_posix())
    if check:
        if stale:
            print("STALE rendered pages (run python3 tools/build.py):")
            for s in stale:
                print("  ", s)
            sys.exit(1)
        print("all rendered pages are up to date")


if __name__ == "__main__":
    main(sys.argv[1:])
