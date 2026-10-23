#!/usr/bin/env python3
"""Gate for airy, projector-readable prose (specs/module-contract.md §1, rules A1-A3; adapted from polytechnique-llga).

Usage (repository root):
    python3 tools/check_airiness.py                       # every course and project, summary
    python3 tools/check_airiness.py courses/slurm         # one page, every violation

A "block" is a paragraph, or one item of a bulleted / numbered list, outside
code, display math, tables, headings, raw HTML and the references / sources sections.
Each block must satisfy:
    A1  at most WORDS words (an inline formula counts as one word);
    A2  at most INLINE inline formulas $…$;
    A3  no inline formula longer than LONG characters of TeX (spaces ignored):
        a formula that long belongs on its own line, as display math $$…$$.
Box openers (::: def …) and their [Title]{.tag} line are not prose.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDS, INLINE, LONG = 100, 6, 50

FENCE = re.compile(r"^(```|~~~)")
TABLE_RULE = re.compile(r"^\s*-{3,}(\s+-{3,})*\s*$")
INLINE_RE = re.compile(r"(?<![\\$])\$(?!\$)([^$\n]+?)(?<!\\)\$(?!\$)")
ITEM_RE = re.compile(r"^\s{0,6}(?:[-*+]|\d+\.)\s+")


def blocks(src: str):
    """Yield (line number, text) for every prose block of a module source."""
    lines = src.split("\n")
    i, n = 0, len(lines)
    if lines and lines[0] == "---":  # YAML front matter
        i = lines.index("---", 1) + 1
    buf, start, in_code, in_math = [], 0, False, False

    def flush():
        nonlocal buf
        if buf:
            text = "\n".join(buf)
            if not any(TABLE_RULE.match(l) or l.lstrip().startswith(("|", "+-")) for l in buf):
                yield start, text
        buf = []

    while i < n:
        line = lines[i]
        s = line.strip()
        if s.startswith(("## Lectures et références", "## Sources et portée", "## Sources")):
            yield from flush()
            # skip to next level-2 heading
            i += 1
            while i < n and not lines[i].startswith("## "):
                i += 1
            continue
        if FENCE.match(s):
            yield from flush()
            in_code = not in_code
            i += 1
            continue
        if in_code:
            i += 1
            continue
        if in_math:
            if s.endswith("$$"):
                in_math = False
            i += 1
            continue
        if s.startswith("$$"):
            yield from flush()
            if s == "$$" or not s.endswith("$$") or len(s) < 4:
                in_math = True
            i += 1
            continue
        if not s or s.startswith((":::", "#", "<")) or re.fullmatch(r"\[[^\]]*\]\{\.tag\}", s):
            yield from flush()
            i += 1
            continue
        if ITEM_RE.match(line) and buf:
            yield from flush()
        if not buf:
            start = i + 1
        buf.append(line)
        i += 1
    yield from flush()


def violations(src: str):
    out = []
    for ln, text in blocks(src):
        text = re.sub(r"^\[[^\]]*\]\{\.tag\}\s*", "", ITEM_RE.sub("", text, count=1))
        text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.S)
        maths = INLINE_RE.findall(text)
        words = len(INLINE_RE.sub("X", text).split())
        if words > WORDS:
            out.append((ln, "A1", f"{words} words"))
        if len(maths) > INLINE:
            out.append((ln, "A2", f"{len(maths)} inline formulas"))
        for m in maths:
            if len(m.replace(" ", "")) > LONG:
                out.append((ln, "A3", f"long inline ${m[:60]}{'…' if len(m) > 60 else ''}$"))
    return out


def pages(args):
    if args:
        return [ROOT / a.rstrip("/") / "index.md" if not a.endswith(".md") else ROOT / a for a in args]
    return sorted(list((ROOT / "courses").glob("*/index.md")) + list((ROOT / "projects").glob("*/index.md")))


def main(args):
    bad = 0
    for md in pages(args):
        if md.parent.name.startswith("_"):
            continue
        name = md.parent.relative_to(ROOT).as_posix()
        v = violations(md.read_text(encoding="utf-8"))
        if v:
            bad += 1
            counts = {r: sum(1 for x in v if x[1] == r) for r in ("A1", "A2", "A3")}
            print(f"{name}: FAIL " + " ".join(f"{r}={c}" for r, c in counts.items()))
            if args:
                for ln, rule, msg in v:
                    print(f"  line {ln}: {rule} {msg}")
        else:
            print(f"{name}: ok")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
