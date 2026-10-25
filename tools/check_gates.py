#!/usr/bin/env python3
"""Mechanical gates ("Prove" step) for courses, projects and the site.

Contracts: specs/module-contract.md (courses), specs/project-contract.md (projects),
specs/site-architecture.md (site). Run from the repository root:

    python3 tools/check_gates.py                 # everything
    python3 tools/check_gates.py courses/slurm   # some pages, verbose
    python3 tools/check_gates.py --labs          # also run labs/*/*/verify.sh (sandbox labs)
Exit status 0 = every gate holds.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_airiness import violations as airiness  # noqa: E402

COURSE_SECTIONS = ["intro", "fiche", "acquis", "seances", "avant"]
TAIL_SECTIONS = ["labs", "ex", "exit", "refs", "sources"]
PROJECT_SECTIONS = ["contexte", "cahier", "jalons", "livrables", "criteres", "pistes", "extensions", "portfolio"]
MIN_WORDS, MAX_WORDS = 4500, 18000

FRONT_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
H_RE = re.compile(r"^(#{2,3}) (.+?)\s*\{#([\w-]+)[^}]*\}\s*$", re.M)
CH_RE = re.compile(r"^## (\d+)\. .*\{#ch(\d+)\}\s*$", re.M)
EXO_RE = re.compile(r"^::: exo\s*\n(.*?)^:::\s*$", re.S | re.M)
SOL_RE = re.compile(r"^::: sol[^\n]*\n(.*?)^:::\s*$", re.S | re.M)
# a lab is a "### Lab N.M — title {#lab-N-M}" sub-section followed by a ::: lab box (or, in older pages, a box whose tag carries the title)
LAB_RE = re.compile(r"^### (Lab \d+\.\d+ — .+?) \{#lab-[\w-]+\}\s*\n+::: lab\s*$|^::: lab\s*\n\[(Lab \d+\.\d+ — [^\]]+)\]\{\.tag\}", re.M)
FENCE_RE = re.compile(r"^(```|~~~)(.*)$", re.M)
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
DUR_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s*h$")


def split(path: Path):
    text = path.read_text(encoding="utf-8")
    m = FRONT_RE.match(text)
    if not m:
        return None, text
    return yaml.safe_load(m.group(1)) or {}, text[m.end():]


def prose_words(body: str) -> int:
    t = re.sub(r"<!-- gen:(\w+) -->.*?<!-- /gen:\1 -->", "", body, flags=re.S)   # parts generated from data/curriculum.json
    t = re.sub(r"^(```|~~~).*?^\1\s*$", "", t, flags=re.S | re.M)
    t = re.sub(r"\$\$.*?\$\$", "", t, flags=re.S)
    t = re.sub(r"\$[^$\n]*\$", "", t)
    return len(re.findall(r"[A-Za-zÀ-ÿ]{2,}", t))


def table_rows(section: str):
    rows = []
    for line in section.splitlines():
        if line.startswith("|") and not re.match(r"^\|[-| :]+\|$", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows[1:] if rows else []


def section_text(body: str, anchor: str) -> str:
    """Text of a section, sub-sections included (up to the next heading of the same or a higher level)."""
    m = re.search(r"^(#{2,3}) .*\{#" + re.escape(anchor) + r"[^}]*\}\s*$", body, re.M)
    if not m:
        return ""
    nxt = re.compile(r"^#{2,%d} " % len(m.group(1)), re.M).search(body, m.end())
    return body[m.end(): nxt.start() if nxt else len(body)]


def check_course(path: Path):
    errs = []
    meta, body = split(path)
    cid = path.parent.name
    if meta is None:
        return ["no YAML front matter"]
    for k in ("title", "subtitle", "description", "module", "prerequisites", "status", "badges", "labs"):
        if k not in meta:
            errs.append(f"front matter: missing {k}")
    mod = meta.get("module", {}) or {}
    for k in ("id", "number", "phase", "hours", "level"):
        if k not in mod:
            errs.append(f"front matter: module.{k} missing")
    if mod.get("id") != cid:
        errs.append(f"module.id {mod.get('id')!r} != directory {cid!r}")
    if meta.get("status") not in ("core", "skim", "bonus"):
        errs.append("status must be core|skim|bonus")
    # anchors, order
    heads = [(lvl, title, a) for lvl, title, a in H_RE.findall(body)]
    ids = [a for _, _, a in heads]
    need = COURSE_SECTIONS + [f"ch{n}" for n in range(1, 2)] + TAIL_SECTIONS
    for a in COURSE_SECTIONS + TAIL_SECTIONS:
        if a not in ids:
            errs.append(f"missing section {{#{a}}}")
    if len(ids) != len(set(ids)):
        errs.append("duplicate heading ids")
    chs = [(int(n), int(m)) for n, m in CH_RE.findall(body)]
    nums = [n for n, _ in chs]
    if not 5 <= len(chs) <= 10:
        errs.append(f"{len(chs)} chapters (expected 5-10)")
    if nums != list(range(1, len(nums) + 1)) or any(n != m for n, m in chs):
        errs.append(f"chapters not numbered 1..N with matching ids: {chs}")
    order = [a for a in ids if a in COURSE_SECTIONS + TAIL_SECTIONS or re.fullmatch(r"ch\d+", a)]
    expect = COURSE_SECTIONS + [f"ch{n}" for n in nums] + TAIL_SECTIONS
    if order != expect:
        errs.append(f"section order is {order}, expected {expect}")
    # session plan
    seances = section_text(body, "seances")
    rows = table_rows(seances)
    hdr = next((l for l in seances.splitlines() if l.startswith("|")), "")
    if [c.strip() for c in hdr.strip("|").split("|")] != ["Séance", "Durée", "Niveau", "Contenu", "Pratique"]:
        errs.append("session plan header must be | Séance | Durée | Niveau | Contenu | Pratique |")
    total, levels = 0.0, []
    for r in rows:
        if len(r) != 5:
            errs.append(f"session row has {len(r)} cells: {r[:2]}")
            continue
        m = DUR_RE.match(r[1])
        if not m:
            errs.append(f"session duration {r[1]!r} not like '3 h'")
            continue
        d = float(m.group(1).replace(",", "."))
        if not 1.5 <= d <= 3.5:
            errs.append(f"session {r[0]}: {d} h outside 1.5-3.5 h")
        total += d
        if r[2] not in ("1", "2", "3"):
            errs.append(f"session {r[0]}: level {r[2]!r}")
        else:
            levels.append(int(r[2]))
    if rows and abs(total - float(mod.get("hours", -1))) > 1e-6:
        errs.append(f"session durations sum to {total} h, module.hours is {mod.get('hours')}")
    if levels != sorted(levels):
        errs.append(f"session levels decrease: {levels}")
    # positioning checks
    avant = section_text(body, "avant")
    if len(re.findall(r"^\d+\.\s", avant, re.M)) < 3:
        errs.append("'Avant de commencer' needs 3 numbered questions")
    # exercises
    exos = EXO_RE.findall(body)
    sols = SOL_RE.findall(body)
    if len(exos) < 8:
        errs.append(f"{len(exos)} exercises (need >= 8)")
    grades = {1: 0, 2: 0, 3: 0}
    for e in exos:
        m = re.search(r"★+", e.split("\n", 1)[0])
        if not m:
            errs.append("exercise without ★ grade: " + e.strip()[:50])
        else:
            grades[len(m.group(0))] = grades.get(len(m.group(0)), 0) + 1
    for g, c in grades.items():
        if len(exos) >= 8 and c < 2:
            errs.append(f"fewer than 2 exercises graded {'★' * g}")
    ex_section = section_text(body, "ex")
    if len(re.findall(r"^::: sol", ex_section, re.M)) < len(re.findall(r"^::: exo", ex_section, re.M)):
        errs.append("some exercises have no ::: sol")
    # labs
    labs = LAB_RE.findall(body)
    if len(labs) < 2:
        errs.append(f"{len(labs)} labs (need >= 2)")
    fm_labs = meta.get("labs", []) or []
    for lab in fm_labs:
        d = ROOT / "labs" / cid / lab.get("id", "?")
        if not (d / "README.md").exists():
            errs.append(f"lab {lab.get('id')}: missing {d.relative_to(ROOT)}/README.md")
        if lab.get("kind") == "sandbox" and not (d / "verify.sh").exists():
            errs.append(f"lab {lab.get('id')}: sandbox lab without verify.sh")
        if lab.get("kind") not in ("sandbox", "cluster", "gpu"):
            errs.append(f"lab {lab.get('id')}: kind must be sandbox|cluster|gpu")
    has_verified = any(b.get("class") == "verified" for b in meta.get("badges", []))
    if has_verified and any(l.get("kind") != "sandbox" for l in fm_labs):
        errs.append("badge 'verified' but some labs are not sandbox labs: use class 'unverified' or split")
    # code fences carry a language
    fences = FENCE_RE.findall(body)
    for i in range(0, len(fences), 2):
        if not fences[i][1].strip():
            errs.append("code fence without language")
            break
    # words
    w = prose_words(body)
    if not MIN_WORDS <= w <= MAX_WORDS:
        errs.append(f"{w} prose words (expected {MIN_WORDS}-{MAX_WORDS})")
    # internal links
    for target in LINK_RE.findall(body):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        base, _, frag = target.partition("#")
        if not base:
            if frag and frag not in ids and not re.search(r"\{#" + re.escape(frag) + r"[ }]", body):
                errs.append(f"broken anchor #{frag}")
            continue
        p = (path.parent / base).resolve()
        planned = json.loads((ROOT / "data" / "curriculum.json").read_text(encoding="utf-8"))
        rel_t = p.relative_to(ROOT).as_posix() if str(p).startswith(str(ROOT)) else ""
        if any(rel_t.startswith(f"projects/{pr['id']}") for pr in planned["projects"]) or any(rel_t.startswith(f"courses/{m['id']}") for m in planned["modules"]):
            continue  # planned page: the link is legitimate even if the page is not published yet
        if p.is_dir():
            p = p / "index.html"
        if not (p.exists() or p.with_suffix(".md").exists() or (p.parent / "index.md").exists() and p.name == "index.html"):
            errs.append(f"broken link {target}")
    # airiness
    for ln, rule, msg in airiness(path.read_text(encoding="utf-8")):
        errs.append(f"airiness {rule} line {ln}: {msg}")
    return errs


def check_project(path: Path):
    errs = []
    meta, body = split(path)
    pid = path.parent.name
    if meta is None:
        return ["no YAML front matter"]
    for k in ("title", "subtitle", "description", "project", "badges"):
        if k not in meta:
            errs.append(f"front matter: missing {k}")
    pr = meta.get("project", {}) or {}
    for k in ("id", "number", "hours", "modules"):
        if k not in pr:
            errs.append(f"front matter: project.{k} missing")
    if pr.get("id") != pid:
        errs.append(f"project.id {pr.get('id')!r} != directory {pid!r}")
    ids = [a for _, _, a in H_RE.findall(body)]
    for a in PROJECT_SECTIONS:
        if a not in ids:
            errs.append(f"missing section {{#{a}}}")
    planned_ids = {m["id"] for m in json.loads((ROOT / "data" / "curriculum.json").read_text(encoding="utf-8"))["modules"]}
    for m in pr.get("modules", []) or []:
        if m not in planned_ids:  # a module may be planned but not written yet
            errs.append(f"project.modules: unknown module {m}")
    jal = section_text(body, "jalons")
    if len(re.findall(r"^\d+\.\s|^\|\s*\d", jal, re.M)) < 3:
        errs.append("fewer than 3 milestones")
    crit = section_text(body, "criteres")
    if len(re.findall(r"^\s*[-*]\s|^\|", crit, re.M)) < 4:
        errs.append("fewer than 4 acceptance criteria")
    if prose_words(body) < 1200:
        errs.append(f"only {prose_words(body)} prose words (project needs >= 1200)")
    for ln, rule, msg in airiness(path.read_text(encoding="utf-8")):
        errs.append(f"airiness {rule} line {ln}: {msg}")
    return errs


def check_site():
    errs = []
    if not (ROOT / ".nojekyll").exists():
        errs.append(".nojekyll missing")
    if not (ROOT / "index.md").exists() or not (ROOT / "index.html").exists():
        errs.append("home page index.md/index.html missing")
    for f in ("assets/paper.css", "assets/theme.js"):
        if not (ROOT / f).exists():
            errs.append(f"{f} missing")
    # every rendered page is up to date
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "build.py"), "--check"], capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("rendered pages stale or build failed:\n" + (r.stdout + r.stderr).strip())
    # home links to every course and project
    home = (ROOT / "index.md").read_text(encoding="utf-8") if (ROOT / "index.md").exists() else ""
    for d in sorted((ROOT / "courses").glob("*/index.md")) + sorted((ROOT / "projects").glob("*/index.md")):
        if d.parent.name.startswith("_"):
            continue
        rel = d.parent.relative_to(ROOT).as_posix()
        if rel + "/index.html" not in home:
            errs.append(f"home page does not link {rel}/")
    # every relative link and every #anchor of the rendered pages resolves
    pages = [h for h in ROOT.rglob("*.html") if not {".git", "data", "tools"} & set(h.relative_to(ROOT).parts)]
    html_cache = {h: h.read_text(encoding="utf-8") for h in pages}
    for h, text in html_cache.items():
        for m in re.finditer(r'(?:href|src)="([^"#?]*)(?:\?[^"#]*)?(?:#([^"]*))?"', text):
            url, anchor = m.group(1), m.group(2)
            if re.match(r"^(https?:|mailto:|data:|javascript:)", url):
                continue
            target = (h.parent / url).resolve() if url else h
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errs.append(f"broken link in {h.relative_to(ROOT)}: {url}")
            elif anchor and target.suffix == ".html":
                body = html_cache.get(target) or target.read_text(encoding="utf-8")
                if f'id="{anchor}"' not in body:
                    errs.append(f"missing anchor in {h.relative_to(ROOT)}: {url}#{anchor}")
    # no leftover probes, no secrets, no withheld names
    for p in ROOT.rglob("*"):
        if p.is_file() and ".git" not in p.parts and p.suffix in {".md", ".html", ".json", ".py", ".sh", ".yml", ".yaml"}:
            t = p.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"\b(ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,})\b", t):
                errs.append(f"possible secret in {p.relative_to(ROOT)}")
            if re.search(r"(?i)\buma\.bot\b|app\.dover\.com/apply/UMA", t) and "tools/" not in p.as_posix():
                errs.append(f"withheld employer reference in {p.relative_to(ROOT)}")
    if (ROOT / "courses" / "_probe").exists():
        errs.append("courses/_probe must be removed")
    return errs


def run_labs():
    errs = []
    for v in sorted((ROOT / "labs").glob("*/*/verify.sh")):
        r = subprocess.run(["bash", str(v)], capture_output=True, text=True, cwd=v.parent, timeout=900)
        status = "ok" if r.returncode == 0 else f"FAIL ({r.returncode})"
        print(f"  lab {v.parent.relative_to(ROOT / 'labs')}: {status}")
        if r.returncode != 0:
            errs.append(f"lab {v.parent.relative_to(ROOT / 'labs')} verify.sh failed:\n{(r.stdout + r.stderr)[-800:]}")
    return errs


def main(argv):
    labs = "--labs" in argv
    args = [a for a in argv if not a.startswith("--")]
    failed = 0
    if args:
        targets = [ROOT / a.rstrip("/") / "index.md" for a in args]
    else:
        targets = sorted(list((ROOT / "courses").glob("*/index.md")) + list((ROOT / "projects").glob("*/index.md")))
    for t in targets:
        if t.parent.name.startswith("_"):
            continue
        kind = t.parent.parent.name
        errs = check_course(t) if kind == "courses" else check_project(t) if kind == "projects" else []
        rel = t.parent.relative_to(ROOT).as_posix()
        print(f"{rel}: {'ok' if not errs else str(len(errs)) + ' error(s)'}")
        for e in errs:
            print("   -", e)
        failed += bool(errs)
    if not args:
        errs = check_site()
        print(f"site: {'ok' if not errs else str(len(errs)) + ' error(s)'}")
        for e in errs:
            print("   -", e)
        failed += bool(errs)
    if labs:
        errs = run_labs()
        failed += bool(errs)
        for e in errs:
            print("   -", e)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
