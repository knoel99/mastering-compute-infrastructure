"""Contract for the module that lands as tools/gates.py.

A maintainer adds one module by creating modules/<slug>/index.qmd.
They do not edit another list. The mci block in that file is the record.
Track is not a field. Then they run the two commands.

    python3 tools/build.py
    python3 tools/check_gates.py

The production import uses the names defined below.

    from pathlib import Path
    from tools.gates import CheckReport, Code, build_site, check_gates

    report = check_gates(Path("."))
    raise SystemExit(0 if report.ok else 1)

    report = build_site(Path("."))

build_site raises QuartoMissing when the quarto executable cannot be started,
and RenderFailed when a render exits non-zero. A bad page is a Finding on the
returned CheckReport. check_gates does not render and does not write.

A fixture test drives the same function.

    report = check_gates(fixture)
    assert not report.ok
    assert any(item.code == Code.MISSING_SECTION for item in report.findings)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from html import escape
from pathlib import Path
from typing import NamedTuple, NewType

import yaml

__all__ = [
    "CheckReport",
    "Code",
    "Finding",
    "QuartoMissing",
    "RenderFailed",
    "build_site",
    "check_gates",
]

ModuleId = NewType("ModuleId", str)

_SLUG = re.compile(r"^(?:m\d{2}|a)-[a-z0-9]+(?:-[a-z0-9]+)*$")
_HAND_LINK = re.compile(r"modules/[a-z0-9]+(?:-[a-z0-9]+)*/")
_FRONT = re.compile(r"\A---[ \t]*\r?\n(.*?)(?:\r?\n---[ \t]*(?:\r?\n|\Z))", re.DOTALL)
_FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
_ATX = re.compile(r"(#{1,6})[ \t]+(\S.*?)\s*$")
_MCI_KEYS = frozenset({"status", "order", "hours", "jalon"})
_FOREIGN_THEME = "llga" + "-theme"
_SKIP_DIRS = frozenset({".git", ".quarto", "__pycache__", ".pytest_cache"})
_TEXT_SUFFIXES = frozenset(
    {".qmd", ".html", ".css", ".js", ".md", ".yml", ".yaml", ".txt"}
)
# Quarto 1.7.32 rewrites the pinned URL and drops the integrity hash.
# The stylesheet href becomes katex.min.jskatex.min.css.
_UNPINNED_JS = re.compile(
    r"""<script\b[^>]*?\bsrc=['"]https://cdn\.jsdelivr\.net/npm/katex@0\.19\.0/[^'"]+['"][^>]*>\s*</script>""",
    re.IGNORECASE | re.DOTALL,
)
_UNPINNED_CSS = re.compile(
    r"""<link\b[^>]*?\bhref=['"]https://cdn\.jsdelivr\.net/npm/katex@0\.19\.0/[^'"]+['"][^>]*>""",
    re.IGNORECASE | re.DOTALL,
)

DERIVED_MARK = (
    "<!-- derived from module front matter. build_site overwrites this file. -->"
)
HOME_CARDS = "generated/home-cards.md"
PARCOURS_SEQUENCE = "generated/parcours-sequence.md"
GLOSSARY_FRAGMENT = "generated/glossaire.md"
CHROME = {
    0: "generated/chrome-d0.html",
    1: "generated/chrome-d1.html",
    2: "generated/chrome-d2.html",
}
CLOSINGS = {
    0: "assets/closing-d0.html",
    1: "assets/closing-d1.html",
    2: "assets/closing-d2.html",
}
PAPER_CSS = "assets/paper.css"
THEME_JS = "assets/theme.js"
THEME_KEY = "mci-theme"
KATEX_JS_URL = "https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/katex.min.js"
KATEX_CSS_URL = "https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/katex.min.css"
KATEX_JS_TAG = (
    "<script>window.backupDefine = window.define; window.define = undefined;</script>"
    '<script src="https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/katex.min.js" '
    'integrity="sha384-QFFtAGzvvj+bfgCGxXJlNZZR1nXEZgvG8tDLCCY1F19xl20WlfTYgguB4VcNdxYk" '
    'crossorigin="anonymous"></script>'
)
KATEX_CSS_TAG = (
    "<script>window.define = window.backupDefine; window.backupDefine = undefined;</script>"
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/katex.min.css" '
    'integrity="sha384-3rdsX6e5mueWyoweR9NIVmtEsUkokpBT/0ALqKKIBMr9j4qhHkaIkAcGgsE6uVlp" '
    'crossorigin="anonymous">'
)
_THEME_BOOT = (
    '<script>(function(){try{var t=localStorage.getItem("mci-theme");'
    'if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t);}'
    "catch(e){}})();</script>"
)
WORKFLOW_MUST_CONTAIN = (
    "pull_request",
    "python3 tools/check_gates.py",
    "python3 tools/build.py",
    "git status --porcelain",
)
WORKFLOW_FORBIDDEN = (
    "deploy-pages",
    "peaceiris/actions-gh-pages",
    "upload-pages-artifact",
    "pages: write",
)
FORBIDDEN_CLAIMS = (
    "certificat délivré",
    "délivre un certificat",
    "obtient le certificat",
    "certificat du DLI",
    "awards a certificate",
    "DLI certificate",
)
EXERCISE_PREFIX = "Exercice"
QUESTION_PREFIX = "Question"
PROGRAMMES_HEADING = "À venir"
REQUIRED_TERMS = frozenset(
    {
        "epoch",
        "batch",
        "transfer learning",
        "kernel CUDA",
        "warp",
        "SM",
        "coalescence",
        "HBM3",
        "NVLink",
        "NCCL",
        "all-reduce",
        "rank",
        "DDP/FSDP",
        "Spack",
        "Slurm",
        "TPE",
        "Hyperband/ASHA",
    }
)
_CSS_HOOKS = (
    "prefers-color-scheme",
    "data-theme",
    "prefers-contrast",
    ".def",
    ".thm",
    ".note",
)


class Status(StrEnum):
    FULL = "full"
    SKELETON = "skeleton"


class Track(StrEnum):
    FONDATION = "fondation"
    ANNEXE = "annexe"
    JALON = "jalon"
    OFFRE_A = "offre-a"
    OFFRE_B = "offre-b"


class Marker(StrEnum):
    CONFIRME = "Confirmé"
    ANTICIPE = "Anticipé"


class Heading(StrEnum):
    OBJECTIFS = "Objectifs"
    PREREQUIS = "Prérequis"
    NOTES = "Notes de cours"
    EXERCICES = "Exercices"
    PROJET_SOLO = "Projet solo"
    PROJET_GROUPE = "Projet de groupe"
    EXAMEN = "Examen"
    SOURCES = "Sources"
    TRAVAUX = "Travaux pratiques prévus"
    GLOSSAIRE = "Glossaire"


class GapHeading(StrEnum):
    ACQUIS = "Acquis"
    CONSOLIDER = "À consolider"
    APPRENDRE = "À apprendre"


class SiteKind(StrEnum):
    HOME = "home"
    PARCOURS = "parcours"
    GLOSSAIRE = "glossaire"
    PROGRAMMES = "programmes"


class Code(StrEnum):
    EMPTY_CATALOG = "empty-catalog"
    SLUG = "slug"
    FRONT_MATTER = "front-matter"
    UNKNOWN_KEY = "unknown-key"
    DUPLICATE_ORDER = "duplicate-order"
    MISSING_SECTION = "missing-section"
    FORBIDDEN_SECTION = "forbidden-section"
    EMPTY_SECTION = "empty-section"
    EXERCISE_COUNT = "exercise-count"
    EXAM_SHAPE = "exam-shape"
    FACT_MARKER = "fact-marker"
    FACT_SOURCE = "fact-source"
    FACT_GROUP = "fact-group"
    FORBIDDEN_CLAIM = "forbidden-claim"
    LISTING_DRIFT = "listing-drift"
    CHROME_DRIFT = "chrome-drift"
    GLOSSARY_DRIFT = "glossary-drift"
    GLOSSARY_TERM = "glossary-term"
    ANNEX_COUNT = "annex-count"
    HAND_LINK = "hand-link"
    INCLUDE = "include"
    MISSING_LINK = "missing-link"
    MISSING_QMD = "missing-qmd"
    MISSING_HTML = "missing-html"
    LANG = "lang"
    GAP = "gap"
    PROGRAMMES = "programmes"
    THEME = "theme"
    BRAND = "brand"
    KATEX = "katex"
    WORKFLOW = "workflow"
    NOJEKYLL = "nojekyll"


TRACK_LABEL: dict[Track, str] = {
    Track.FONDATION: "Fondation",
    Track.ANNEXE: "Annexe",
    Track.JALON: "Jalon",
    Track.OFFRE_A: "Offre A",
    Track.OFFRE_B: "Offre B",
}
STATUS_LABEL: dict[Status, str] = {
    Status.FULL: "Cours",
    Status.SKELETON: "Squelette",
}


class QuartoMissing(RuntimeError):
    def __init__(self, executable: str) -> None:
        super().__init__(executable)
        self.executable = executable


class RenderFailed(RuntimeError):
    def __init__(self, rel_qmd: str, returncode: int) -> None:
        super().__init__(f"{rel_qmd} exited {returncode}")
        self.rel_qmd = rel_qmd
        self.returncode = returncode


@dataclass(frozen=True)
class Finding:
    code: Code
    path: str
    message: str


@dataclass(frozen=True)
class CheckReport:
    findings: tuple[Finding, ...]

    @property
    def ok(self) -> bool:
        return not self.findings


@dataclass(frozen=True)
class Module:
    """One module record parsed from front matter.

    slug, title, status, order, hours, and jalon are the stored fields.
    track is derived from the slug on every read. hours and jalon are None
    when the author omitted them.
    """

    slug: ModuleId
    title: str
    status: Status
    order: int
    hours: int | None = None
    jalon: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, Status):
            raise ValueError("status")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title")
        if not isinstance(self.slug, str) or _SLUG.fullmatch(self.slug) is None:
            raise ValueError("slug")
        if (
            not isinstance(self.order, int)
            or isinstance(self.order, bool)
            or self.order < 1
        ):
            raise ValueError("order")
        if self.hours is not None and (
            not isinstance(self.hours, int)
            or isinstance(self.hours, bool)
            or self.hours < 1
        ):
            raise ValueError("hours")
        if self.jalon is not None and (
            not isinstance(self.jalon, str) or not self.jalon.strip()
        ):
            raise ValueError("jalon")

    @property
    def track(self) -> Track:
        return _track_of(self.slug)


@dataclass(frozen=True)
class Catalog:
    """Modules in path order, plus findings from the scan boundary.

    The constructor sorts modules by (order, slug). Duplicate orders stay
    in the tuple so later checks still see those pages. A directory that
    fails to parse is absent here and present as a finding.
    """

    modules: tuple[Module, ...]
    findings: tuple[Finding, ...]

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(self.modules, key=lambda module: (module.order, module.slug))
        )
        object.__setattr__(self, "modules", ordered)


@dataclass(frozen=True)
class SectionRule:
    required: tuple[Heading, ...]
    forbidden: tuple[Heading, ...]
    min_exercises: int
    min_questions: int


@dataclass(frozen=True)
class Fact:
    """One recognizable claim.

    pattern is tested inside a heading block. The block is the heading line
    plus the body up to the next heading of the same or higher level.
    The block must contain marker. source, when set, must occur in the
    Sources section. group, when set, is page-wide. One match forces every
    fact that shares the group name to match somewhere on the page.
    """

    name: str
    pattern: re.Pattern[str]
    marker: Marker
    source: str | None = None
    group: str | None = None


@dataclass(frozen=True)
class SitePage:
    rel_qmd: str
    depth: int
    kind: SiteKind


@dataclass(frozen=True)
class HtmlPage:
    rel_html: str
    depth: int
    html: str
    require_titles: bool


class _Heading(NamedTuple):
    level: int
    start: int
    line_end: int
    text: str


def _track_of(slug: str) -> Track:
    if _SLUG.fullmatch(slug) is None:
        raise ValueError(slug)
    if slug.startswith("a-"):
        return Track.ANNEXE
    number = int(slug[1:3])
    if number == 0:
        return Track.JALON
    if number <= 3:
        return Track.FONDATION
    if number <= 9:
        return Track.OFFRE_A
    return Track.OFFRE_B


def _href(depth: int, slug: ModuleId) -> str:
    if depth < 0:
        raise ValueError("depth")
    return f"{'../' * depth}modules/{slug}/"


def _site_href(depth: int, rel: str) -> str:
    if depth < 0:
        raise ValueError("depth")
    return f"{'../' * depth}{rel}"


def _chrome_ref(depth: int) -> str:
    return _site_href(depth, CHROME[depth])


def _closing_ref(depth: int) -> str:
    return _site_href(depth, CLOSINGS[depth])


def _css_ref(depth: int) -> str:
    return _site_href(depth, PAPER_CSS)


def _theme_src(depth: int) -> str:
    return _site_href(depth, THEME_JS)


def _checked(rule: SectionRule) -> SectionRule:
    overlap = set(rule.required) & set(rule.forbidden)
    if overlap:
        raise RuntimeError(f"section rule overlap {overlap!r}")
    return rule


SECTION_RULES: Mapping[Status, SectionRule] = {
    Status.FULL: _checked(
        SectionRule(
            required=(
                Heading.OBJECTIFS,
                Heading.PREREQUIS,
                Heading.NOTES,
                Heading.EXERCICES,
                Heading.PROJET_SOLO,
                Heading.PROJET_GROUPE,
                Heading.EXAMEN,
            ),
            forbidden=(),
            min_exercises=4,
            min_questions=3,
        )
    ),
    # Prérequis and Notes on a skeleton are a full page that skipped its sections.
    Status.SKELETON: _checked(
        SectionRule(
            required=(Heading.OBJECTIFS, Heading.TRAVAUX),
            forbidden=(
                Heading.PREREQUIS,
                Heading.NOTES,
                Heading.EXERCICES,
                Heading.PROJET_SOLO,
                Heading.PROJET_GROUPE,
                Heading.EXAMEN,
            ),
            min_exercises=0,
            min_questions=0,
        )
    ),
}


def _fact(
    name: str,
    pattern: str,
    marker: Marker,
    source: str | None = None,
    group: str | None = None,
    flags: int = 0,
) -> Fact:
    return Fact(name, re.compile(pattern, flags), marker, source, group)


FACTS: tuple[Fact, ...] = (
    _fact("top500-id", r"180311", Marker.CONFIRME, "top500.org"),
    _fact("rmax", r"9[.,]86\s*PFlop", Marker.CONFIRME, "top500.org"),
    _fact("rpeak-2026", r"16[.,]32\s*PFlop", Marker.CONFIRME, "top500.org", "rpeak"),
    _fact("rpeak-2024", r"11[.,]20\s*PFlop", Marker.CONFIRME, "top500.org", "rpeak"),
    _fact("power", r"160[.,]16\s*kW", Marker.CONFIRME, "top500.org"),
    _fact(
        "rank-192",
        r"(?:TOP500.{0,24}192|rang\s+192|rank\s+192)",
        Marker.CONFIRME,
        "top500.org",
    ),
    _fact("xh3000", r"BullSequana XH3000", Marker.CONFIRME, "top500.org"),
    _fact("ndr200", r"NDR200", Marker.CONFIRME, "top500.org"),
    _fact(
        "cores-top500",
        r"(?<![0-9])47[\s\u00a0]?328(?![0-9])",
        Marker.CONFIRME,
        "top500.org",
        "cores",
    ),
    _fact(
        "cores-eviden",
        r"(?<![0-9])25[\s\u00a0]?000(?![0-9])",
        Marker.CONFIRME,
        "globenewswire.com",
        "cores",
    ),
    _fact(
        "cpu-partition",
        r"(?<![0-9])8[\s\u00a0]?448(?![0-9])",
        Marker.CONFIRME,
        "globenewswire.com",
    ),
    _fact(
        "storage-en",
        r"2[.,]8\s*P[Bo]",
        Marker.CONFIRME,
        "globenewswire.com",
        "storage",
    ),
    _fact(
        "storage-fr",
        r"(?<![0-9.,])2\s*P[Bo](?![0-9.,])",
        Marker.CONFIRME,
        "globenewswire.com",
        "storage",
    ),
    _fact(
        "nodes-58",
        r"58\s+(?:nœuds|noeuds|quad)",
        Marker.CONFIRME,
        "globenewswire.com",
    ),
    _fact("superchips", r"232\s+super", Marker.CONFIRME, "globenewswire.com"),
    _fact("quantum-2", r"Quantum-2", Marker.CONFIRME, "globenewswire.com"),
    _fact("gh200-120", r"GH200 120GB", Marker.CONFIRME, "HPC-Works"),
    _fact("driver", r"560\.35\.03", Marker.CONFIRME, "HPC-Works"),
    _fact("neoverse", r"Neoverse-V2", Marker.CONFIRME, "HPC-Works"),
    _fact("romeo1", r"romeo1\.univ-reims\.fr", Marker.CONFIRME, "HPC-Works"),
    _fact("romeo2", r"romeo2\.univ-reims\.fr", Marker.CONFIRME, "HPC-Works"),
    _fact("mem-mib", r"97[\s\u00a0]?871\s*MiB", Marker.CONFIRME, "HPC-Works"),
    _fact("cpus-288", r"288 CPUs", Marker.CONFIRME, "HPC-Works"),
    _fact("mlx5", r"mlx5_[0-3]", Marker.CONFIRME, "HPC-Works"),
    _fact("armgpu", r"constraint=armgpu", Marker.CONFIRME, "HPC-Works"),
    _fact(
        "fiche-dl",
        r"Introduction au Deep Learning",
        Marker.CONFIRME,
        "https://romeo.univ-reims.fr/21_formations.html/340/Introduction_au_Deep_Learning_",
    ),
    _fact(
        "fiche-romeo",
        r"Utiliser ROMEO2025",
        Marker.CONFIRME,
        "https://romeo.univ-reims.fr/21_formations.html/341/Utiliser_ROMEO2025_et_ses_GPU_pour_le_HPC_et_l_IA",
    ),
    _fact(
        "fiche-cuda",
        r"CUDA Python",
        Marker.CONFIRME,
        "https://romeo.univ-reims.fr/21_formations.html/339/Programmation_GPU_avec_CUDA_Python",
    ),
    _fact(
        "fiche-multigpu",
        r"Acc[eé]l[eé]rez vos projets",
        Marker.CONFIRME,
        "https://romeo.univ-reims.fr/21_formations.html/342/Accelerez_vos_projets_IA_avec_le_HPC_et_les_multi-GPU",
    ),
    _fact(
        "fiche-hpo",
        r"hyperparamètres",
        Marker.CONFIRME,
        "https://romeo.univ-reims.fr/21_formations.html/343/Optimisation_Multi-GPU_des_Hyperparametres_et_des_Modeles_d_IA_sur_Supercalculateur",
    ),
    _fact("helper-arm", r"romeo_load_armgpu_env", Marker.ANTICIPE),
    _fact("helper-x64", r"romeo_load_x64cpu_env", Marker.ANTICIPE),
    _fact("slurm-pin", r"Slurm\s*23\.11", Marker.ANTICIPE),
    _fact("spack-pin", r"Spack\s*1\.0", Marker.ANTICIPE),
    _fact("c2c", r"NVLink-C2C", Marker.ANTICIPE),
    _fact("gbps-900", r"900\s*Go/s", Marker.ANTICIPE),
    _fact("gbps-150", r"150\s*Go/s", Marker.ANTICIPE),
    _fact("optuna", r"Optuna", Marker.ANTICIPE, flags=re.IGNORECASE),
    _fact("hyperband", r"Hyperband", Marker.ANTICIPE, flags=re.IGNORECASE),
    _fact("asha", r"\bASHA\b", Marker.ANTICIPE),
    _fact("tpe", r"\bTPE\b", Marker.ANTICIPE),
    _fact("login-user", r"login@romeo1", Marker.ANTICIPE),
)

SITE_PAGES: tuple[SitePage, ...] = (
    SitePage("index.qmd", 0, SiteKind.HOME),
    SitePage("parcours/index.qmd", 1, SiteKind.PARCOURS),
    SitePage("glossaire/index.qmd", 1, SiteKind.GLOSSAIRE),
    SitePage("programmes/index.qmd", 1, SiteKind.PROGRAMMES),
)
SITE_INCLUDES = {
    SiteKind.HOME: HOME_CARDS,
    SiteKind.PARCOURS: "../" + PARCOURS_SEQUENCE,
    SiteKind.GLOSSAIRE: "../" + GLOSSARY_FRAGMENT,
    SiteKind.PROGRAMMES: None,
}


def _read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    if text.startswith("\ufeff"):
        text = text[1:]
    return text


def _clean_heading(raw: str) -> str:
    text = raw.strip()
    for _ in range(2):
        text = re.sub(r"\s+\{[^{}]*\}\s*$", "", text)
        text = re.sub(r"\s+#+\s*$", "", text)
        text = text.strip()
    return text


def _headings(text: str) -> tuple[_Heading, ...]:
    found: list[_Heading] = []
    fence: str | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        marker = _FENCE.match(line)
        if fence is not None:
            if (
                marker is not None
                and marker.group(1)[0] == fence[0]
                and len(marker.group(1)) >= len(fence)
            ):
                fence = None
            offset += len(line)
            continue
        if marker is not None:
            fence = marker.group(1)
            offset += len(line)
            continue
        match = _ATX.match(line.rstrip("\r\n"))
        if match is not None:
            found.append(
                _Heading(
                    len(match.group(1)),
                    offset,
                    offset + len(line),
                    _clean_heading(match.group(2)),
                )
            )
        offset += len(line)
    return tuple(found)


def _section_slice(text: str, title: str) -> str | None:
    heads = _headings(text)
    for index, head in enumerate(heads):
        if head.level != 2 or head.text != title:
            continue
        end = len(text)
        for nxt in heads[index + 1 :]:
            if nxt.level <= 2:
                end = nxt.start
                break
        return text[head.start : end]
    return None


def _section_bodies(text: str, title: str) -> tuple[str, ...]:
    heads = _headings(text)
    bodies: list[str] = []
    for index, head in enumerate(heads):
        if head.level != 2 or head.text != title:
            continue
        end = len(text)
        for nxt in heads[index + 1 :]:
            if nxt.level <= 2:
                end = nxt.start
                break
        bodies.append(text[head.line_end : end])
    return tuple(bodies)


def _h2_texts(text: str) -> tuple[str, ...]:
    return tuple(head.text for head in _headings(text) if head.level == 2)


def _h3_texts(text: str) -> tuple[str, ...]:
    return tuple(head.text for head in _headings(text) if head.level == 3)


def _h3_under(text: str, title: str) -> tuple[str, ...]:
    found: list[str] = []
    inside = False
    for head in _headings(text):
        if head.level <= 2:
            inside = head.level == 2 and head.text == title
            continue
        if inside and head.level == 3:
            found.append(head.text)
    return tuple(found)


def _fact_blocks(text: str) -> tuple[str, ...]:
    heads = _headings(text)
    if not heads:
        return (text,) if text else ()
    blocks: list[str] = []
    if heads[0].start > 0:
        blocks.append(text[: heads[0].start])
    for index, head in enumerate(heads):
        end = len(text)
        for nxt in heads[index + 1 :]:
            if nxt.level <= head.level:
                end = nxt.start
                break
        blocks.append(text[head.start : end])
    return tuple(blocks)


def _front_mapping(text: str) -> dict[str, object] | None:
    match = _FRONT.match(text)
    if match is None:
        return None
    loaded = yaml.safe_load(match.group(1))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("front matter illisible")
    return loaded


def _front_has_mci(text: str) -> bool:
    match = _FRONT.match(text)
    if match is None:
        return re.search(r"(?m)^mci:\s*", text) is not None
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return re.search(r"(?m)^mci:\s*", match.group(1)) is not None
    return isinstance(data, dict) and "mci" in data


def _parse_module(slug: str, text: str, rel: str) -> tuple[Module | None, tuple[Finding, ...]]:
    findings: list[Finding] = []
    try:
        data = _front_mapping(text)
    except (yaml.YAMLError, ValueError):
        return None, (Finding(Code.FRONT_MATTER, rel, "front matter illisible"),)
    if data is None:
        return None, (Finding(Code.FRONT_MATTER, rel, "front matter absent"),)
    title = data.get("title")
    title_text = title.strip() if isinstance(title, str) else None
    if not title_text:
        findings.append(Finding(Code.FRONT_MATTER, rel, "titre absent ou vide"))
    mci = data.get("mci", None)
    if "mci" not in data or mci is None:
        findings.append(Finding(Code.FRONT_MATTER, rel, "bloc mci manquant"))
        return None, tuple(findings)
    if not isinstance(mci, dict):
        findings.append(Finding(Code.FRONT_MATTER, rel, "bloc mci illisible"))
        return None, tuple(findings)
    for key in sorted(str(item) for item in mci):
        if key not in _MCI_KEYS:
            findings.append(Finding(Code.UNKNOWN_KEY, rel, f"clé mci inconnue : {key}"))
    raw_status = mci.get("status")
    status: Status | None
    try:
        status = Status(raw_status) if isinstance(raw_status, str) else None
    except ValueError:
        status = None
    if status is None:
        findings.append(Finding(Code.FRONT_MATTER, rel, "status hors full et skeleton"))
    raw_order = mci.get("order")
    order = raw_order if type(raw_order) is int and raw_order >= 1 else None
    if order is None:
        findings.append(Finding(Code.FRONT_MATTER, rel, "order n'est pas un entier positif"))
    if "hours" not in mci or mci.get("hours") is None:
        hours: int | None = None
    elif type(mci.get("hours")) is int and mci["hours"] >= 1:
        hours = mci["hours"]
    else:
        hours = None
        findings.append(Finding(Code.FRONT_MATTER, rel, "hours n'est pas un entier positif"))
    raw_jalon = mci.get("jalon")
    if "jalon" not in mci or raw_jalon is None:
        jalon: str | None = None
    elif isinstance(raw_jalon, str) and raw_jalon.strip():
        jalon = raw_jalon
    else:
        jalon = None
        findings.append(Finding(Code.FRONT_MATTER, rel, "jalon n'est pas un texte"))
    if findings or title_text is None or status is None or order is None:
        return None, tuple(findings)
    try:
        module = Module(ModuleId(slug), title_text, status, order, hours, jalon)
    except ValueError:
        return None, (Finding(Code.FRONT_MATTER, rel, "bloc mci refusé"),)
    return module, ()


def _load_catalog(root: Path) -> Catalog:
    """Scan modules/*/index.qmd and parse mci at the boundary.

    Use yaml.safe_load on the front matter only. Return Module values, never
    a YAML dict. Every subdirectory of modules/ must match the slug grammar.
    modules/_template.qmd is not a directory and is ignored. Missing modules/
    yields empty-catalog. A slug directory with no index.qmd, a missing mci
    block, a non-string title, a status outside Status, a non-int order, a
    non-int hours, a non-string jalon, or an unknown mci key becomes a
    finding and omits that module. Duplicate order values become
    duplicate-order findings and keep both modules. Known mci keys are
    status, order, hours, and jalon.
    """
    modules_dir = root / "modules"
    if not modules_dir.is_dir():
        return Catalog(
            (),
            (Finding(Code.EMPTY_CATALOG, "modules", "aucun module"),),
        )
    findings: list[Finding] = []
    modules: list[Module] = []
    saw_directory = False
    for child in sorted(modules_dir.iterdir(), key=lambda path: path.name):
        if not child.is_dir():
            continue
        saw_directory = True
        slug = child.name
        rel = f"modules/{slug}/index.qmd"
        if _SLUG.fullmatch(slug) is None:
            findings.append(Finding(Code.SLUG, f"modules/{slug}", "nom de dossier hors grammaire"))
            continue
        text = _read_text(child / "index.qmd")
        if text is None:
            findings.append(Finding(Code.MISSING_QMD, rel, "index.qmd manquant"))
            continue
        module, parsed = _parse_module(slug, text, rel)
        findings.extend(parsed)
        if module is not None:
            modules.append(module)
    if not saw_directory and not findings:
        findings.append(Finding(Code.EMPTY_CATALOG, "modules", "aucun module"))
    by_order: dict[int, list[Module]] = {}
    for module in modules:
        by_order.setdefault(module.order, []).append(module)
    for order, group in sorted(by_order.items()):
        if len(group) < 2:
            continue
        for module in group:
            findings.append(
                Finding(
                    Code.DUPLICATE_ORDER,
                    f"modules/{module.slug}/index.qmd",
                    f"ordre {order} répété",
                )
            )
    return Catalog(tuple(modules), tuple(findings))


def _card_lines(modules: Sequence[Module], depth: int) -> tuple[str, ...]:
    """Return one listing line per module.

    Parts, in order, are the markdown link from _href, TRACK_LABEL, STATUS_LABEL,
    ``{hours} h`` when hours is set, and jalon when jalon is set. Join parts
    with ". ". Omit empty parts.
    """
    lines: list[str] = []
    for module in modules:
        parts = [
            f"[{module.title}]({_href(depth, module.slug)})",
            TRACK_LABEL[module.track],
            STATUS_LABEL[module.status],
        ]
        if module.hours is not None:
            parts.append(f"{module.hours} h")
        if module.jalon:
            parts.append(module.jalon)
        lines.append(". ".join(part for part in parts if part))
    return tuple(lines)


def _derive_home_cards(modules: Sequence[Module]) -> str:
    """Return the depth-0 listing that index.qmd includes.

    The text starts with DERIVED_MARK and a newline, then one "- " line per
    module from _card_lines at depth 0, and ends with a single trailing newline.
    No timestamp.
    """
    body = "".join(f"- {line}\n" for line in _card_lines(modules, 0))
    return f"{DERIVED_MARK}\n{body}"


def _derive_parcours(modules: Sequence[Module]) -> str:
    """Return the depth-1 sequence that parcours/index.qmd includes.

    Same parts as the home cards, from _card_lines at depth 1. Number the
    lines from 1 using ``f"{n}. "``. Same marker and trailing newline as the
    home listing.
    """
    body = "".join(
        f"{number}. {line}\n"
        for number, line in enumerate(_card_lines(modules, 1), start=1)
    )
    return f"{DERIVED_MARK}\n{body}"


def _derive_chrome(modules: Sequence[Module], depth: int) -> str:
    """Return the opening chrome for one relative depth.

    Start with DERIVED_MARK. Include a skip link "Aller au contenu", a top
    bar whose brand is "Infra de calcul", a Sommaire button, and a Thème
    button. Include an empty side TOC nav#sidetoc. Include nav#mci-nav with
    Accueil, Parcours, Glossaire, and Programmes via _site_href, then one
    anchor per module via _href(depth, slug) and the module title. Open
    main#main and do not close it. The matching close lives in the static
    closing file for that depth. No module list belongs in theme.js.
    """
    if depth not in CHROME:
        raise ValueError("depth")
    home = _site_href(depth, "index.html")
    parcours = _site_href(depth, "parcours/index.html")
    glossaire = _site_href(depth, "glossaire/index.html")
    programmes = _site_href(depth, "programmes/index.html")
    lines = [
        DERIVED_MARK,
        _THEME_BOOT,
        '<a class="skip" href="#main">Aller au contenu</a>',
        '<header class="topbar">',
        (
            '<button type="button" class="tb-btn" id="toc-toggle" '
            'aria-controls="sidetoc" aria-expanded="false">'
            '<span class="tb-label">Sommaire</span></button>'
        ),
        f'<a class="brand" href="{home}">Infra de calcul</a>',
        '<span class="tb-title" id="tb-title"></span>',
        '<button type="button" class="tb-btn" id="theme-toggle">Thème</button>',
        "</header>",
        '<div class="layout">',
        '<nav id="sidetoc" class="sidetoc" aria-label="Sommaire"></nav>',
        '<div class="content">',
        '<nav id="mci-nav">',
        f'<a href="{home}">Accueil</a>',
        f'<a href="{parcours}">Parcours</a>',
        f'<a href="{glossaire}">Glossaire</a>',
        f'<a href="{programmes}">Programmes</a>',
    ]
    for module in modules:
        lines.append(f'<a href="{_href(depth, module.slug)}">{escape(module.title)}</a>')
    lines.extend(["</nav>", '<main id="main">'])
    return "\n".join(lines) + "\n"


def _derive_glossary(annex_qmd: str | None) -> str:
    """Return the Glossaire section of the annex, prefixed by DERIVED_MARK.

    When annex_qmd is None or the section is missing, return the marker and
    a trailing newline. Otherwise return the marker, a newline, and the
    section body from the Glossaire heading through the line before the next
    level-2 heading. Do not include later sections of the annex.
    """
    if not annex_qmd:
        return DERIVED_MARK + "\n"
    chunk = _section_slice(annex_qmd, Heading.GLOSSAIRE.value)
    if chunk is None:
        return DERIVED_MARK + "\n"
    return DERIVED_MARK + "\n" + chunk.strip("\n") + "\n"


def _html_contains(html: str, needle: str) -> bool:
    """Return whether needle occurs in html.

    Pandoc rewrites an ASCII apostrophe as U+2019. Both forms match.
    """

    def fold(value: str) -> str:
        return value.replace("\u2019", "'").replace("\u2018", "'")

    return fold(needle) in fold(html)


def _page_findings(
    module: Module,
    qmd: str,
    html: str | None,
    qmd_path: str,
    html_path: str,
) -> tuple[Finding, ...]:
    """Apply SECTION_RULES[module.status] to one module.

    Read headings from the qmd. A required heading that is absent is
    missing-section. A forbidden heading that is present is forbidden-section.
    A required section with an empty body is empty-section. Count level-3
    headings under Exercices whose text starts with EXERCISE_PREFIX, and
    under Examen whose text starts with QUESTION_PREFIX. A short count is
    exercise-count or exam-shape. The qmd must contain lang: fr, _css_ref(2),
    _chrome_ref(2), _closing_ref(2), and KATEX_JS_URL. When html is None,
    emit missing-html and skip HTML checks. When html is present, it must
    contain lang="fr" and the text of every required heading, exercise
    heading, and question heading. _html_contains accepts the Pandoc
    apostrophe in that HTML.
    """
    rule = SECTION_RULES[module.status]
    findings: list[Finding] = []
    for heading in rule.required:
        bodies = _section_bodies(qmd, heading.value)
        if not bodies:
            findings.append(
                Finding(Code.MISSING_SECTION, qmd_path, f"section manquante : {heading.value}")
            )
        elif not any(body.strip() for body in bodies):
            findings.append(
                Finding(Code.EMPTY_SECTION, qmd_path, f"section vide : {heading.value}")
            )
    for heading in rule.forbidden:
        if _section_bodies(qmd, heading.value):
            findings.append(
                Finding(
                    Code.FORBIDDEN_SECTION,
                    qmd_path,
                    f"section interdite : {heading.value}",
                )
            )
    exercises: list[str] = []
    if _section_bodies(qmd, Heading.EXERCICES.value):
        exercises = [
            item
            for item in _h3_under(qmd, Heading.EXERCICES.value)
            if item.startswith(EXERCISE_PREFIX)
        ]
        if len(exercises) < rule.min_exercises:
            findings.append(
                Finding(
                    Code.EXERCISE_COUNT,
                    qmd_path,
                    f"moins de {rule.min_exercises} exercices",
                )
            )
    questions: list[str] = []
    if _section_bodies(qmd, Heading.EXAMEN.value):
        questions = [
            item
            for item in _h3_under(qmd, Heading.EXAMEN.value)
            if item.startswith(QUESTION_PREFIX)
        ]
        if len(questions) < rule.min_questions:
            findings.append(
                Finding(
                    Code.EXAM_SHAPE,
                    qmd_path,
                    f"moins de {rule.min_questions} questions",
                )
            )
    if re.search(r"lang:\s*fr\b", qmd) is None:
        findings.append(Finding(Code.LANG, qmd_path, "lang: fr manquant"))
    for ref in (_css_ref(2), _chrome_ref(2), _closing_ref(2)):
        if ref not in qmd:
            findings.append(Finding(Code.INCLUDE, qmd_path, f"référence manquante : {ref}"))
    if KATEX_JS_URL not in qmd:
        findings.append(Finding(Code.KATEX, qmd_path, "URL KaTeX manquante"))
    if html is None:
        findings.append(Finding(Code.MISSING_HTML, html_path, "index.html manquant"))
        return tuple(findings)
    if 'lang="fr"' not in html:
        findings.append(Finding(Code.LANG, html_path, 'lang="fr" manquant'))
    for text in [heading.value for heading in rule.required] + exercises + questions:
        if not _html_contains(html, text):
            findings.append(Finding(Code.MISSING_SECTION, html_path, f"HTML sans : {text}"))
    return tuple(findings)


def _fact_findings(rel_path: str, text: str) -> tuple[Finding, ...]:
    """Apply FACTS and FORBIDDEN_CLAIMS to one page body.

    Split text into heading blocks. A block that matches a fact pattern must
    contain that fact's marker, or the finding is fact-marker. Any match
    requires a non-empty Sources section. Each matched source substring must
    appear there, or the finding is fact-source. For a group name that
    matched at least once, every fact with that group must match on the page,
    or the finding is fact-group. A FORBIDDEN_CLAIMS substring is
    forbidden-claim. Scan the whole qmd, front matter included, so a jalon
    line is visible to the registry.
    """
    findings: list[Finding] = []
    matched: set[str] = set()
    for block in _fact_blocks(text):
        for fact in FACTS:
            if fact.pattern.search(block) is None:
                continue
            matched.add(fact.name)
            if fact.marker.value not in block:
                findings.append(
                    Finding(
                        Code.FACT_MARKER,
                        rel_path,
                        f"marqueur {fact.marker.value} manquant pour {fact.name}",
                    )
                )
    if matched:
        sources = _section_slice(text, Heading.SOURCES.value)
        blank = sources is None or not "\n".join(sources.splitlines()[1:]).strip()
        if blank:
            findings.append(Finding(Code.FACT_SOURCE, rel_path, "section Sources vide ou absente"))
        else:
            assert sources is not None
            for fact in FACTS:
                if fact.name in matched and fact.source and fact.source not in sources:
                    findings.append(
                        Finding(
                            Code.FACT_SOURCE,
                            rel_path,
                            f"source manquante pour {fact.name}",
                        )
                    )
    seen_groups: set[str] = set()
    for fact in FACTS:
        if not fact.group or fact.name not in matched or fact.group in seen_groups:
            continue
        seen_groups.add(fact.group)
        missing = [other.name for other in FACTS if other.group == fact.group and other.name not in matched]
        if missing:
            findings.append(Finding(Code.FACT_GROUP, rel_path, f"groupe {fact.group} incomplet"))
    for claim in FORBIDDEN_CLAIMS:
        if claim in text:
            findings.append(Finding(Code.FORBIDDEN_CLAIM, rel_path, "formulation interdite"))
    return tuple(findings)


def _glossary_findings(
    catalog: Catalog,
    texts: Mapping[str, str],
) -> tuple[Finding, ...]:
    """Enforce a single annex and a single definition list.

    Exactly one module with track ANNEXE is required, or the finding is
    annex-count. That module's qmd must contain each REQUIRED_TERMS value as
    a level-3 heading under Glossaire, or the finding is glossary-term.
    Any other page whose level-3 headings include a required term is
    glossary-term. glossaire/index.html must contain each required term.
    """
    findings: list[Finding] = []
    annexes = [module for module in catalog.modules if module.track == Track.ANNEXE]
    annex_rel: str | None = None
    if len(annexes) != 1:
        findings.append(Finding(Code.ANNEX_COUNT, "modules", "une seule annexe est requise"))
    else:
        annex_rel = f"modules/{annexes[0].slug}/index.qmd"
        present = set(_h3_under(texts.get(annex_rel, ""), Heading.GLOSSAIRE.value))
        for term in sorted(REQUIRED_TERMS):
            if term not in present:
                findings.append(
                    Finding(Code.GLOSSARY_TERM, annex_rel, f"terme manquant : {term}")
                )
    for rel in sorted(texts):
        if not rel.endswith(".qmd") or rel == annex_rel:
            continue
        extra = sorted(set(_h3_texts(texts[rel])) & REQUIRED_TERMS)
        for term in extra:
            findings.append(
                Finding(Code.GLOSSARY_TERM, rel, f"terme défini hors annexe : {term}")
            )
    html_rel = "glossaire/index.html"
    html = texts.get(html_rel)
    if html is None:
        findings.append(Finding(Code.GLOSSARY_TERM, html_rel, "glossaire/index.html manquant"))
    else:
        for term in sorted(REQUIRED_TERMS):
            if term not in html:
                findings.append(Finding(Code.GLOSSARY_TERM, html_rel, f"terme manquant : {term}"))
    return tuple(findings)


def _site_findings(
    page: SitePage,
    qmd: str | None,
    html: str | None,
) -> tuple[Finding, ...]:
    """Check one fixed site page.

    When qmd is None, emit missing-qmd and skip the qmd checks. When html
    is None, emit missing-html. A qmd that matches _HAND_LINK is hand-link.
    When SITE_INCLUDES[kind] is a path, the qmd must contain that path or
    the finding is include. PARCOURS must contain each GapHeading or the
    finding is gap. PROGRAMMES must contain a single level-2
    PROGRAMMES_HEADING and must not contain an mci block. Any extra level-2
    heading on that page is programmes. A present qmd must contain lang: fr,
    _css_ref(page.depth), _chrome_ref(page.depth), and _closing_ref(page.depth).
    Present html must contain lang="fr".
    """
    findings: list[Finding] = []
    html_rel = Path(page.rel_qmd).with_suffix(".html").as_posix()
    if qmd is None:
        findings.append(Finding(Code.MISSING_QMD, page.rel_qmd, "fichier qmd manquant"))
    else:
        if _HAND_LINK.search(qmd):
            findings.append(Finding(Code.HAND_LINK, page.rel_qmd, "lien modules/ écrit à la main"))
        include = SITE_INCLUDES[page.kind]
        if include is not None and include not in qmd:
            findings.append(Finding(Code.INCLUDE, page.rel_qmd, f"include manquant : {include}"))
        if page.kind == SiteKind.PARCOURS:
            present = set(_h2_texts(qmd))
            for gap in GapHeading:
                if gap.value not in present:
                    findings.append(
                        Finding(Code.GAP, page.rel_qmd, f"rubrique manquante : {gap.value}")
                    )
        if page.kind == SiteKind.PROGRAMMES:
            if _h2_texts(qmd) != (PROGRAMMES_HEADING,):
                findings.append(
                    Finding(Code.PROGRAMMES, page.rel_qmd, "un seul titre À venir est requis")
                )
            if _front_has_mci(qmd):
                findings.append(Finding(Code.PROGRAMMES, page.rel_qmd, "bloc mci interdit"))
        if re.search(r"lang:\s*fr\b", qmd) is None:
            findings.append(Finding(Code.LANG, page.rel_qmd, "lang: fr manquant"))
        for ref in (_css_ref(page.depth), _chrome_ref(page.depth), _closing_ref(page.depth)):
            if ref not in qmd:
                findings.append(Finding(Code.INCLUDE, page.rel_qmd, f"référence manquante : {ref}"))
    if html is None:
        findings.append(Finding(Code.MISSING_HTML, html_rel, "index.html manquant"))
    elif 'lang="fr"' not in html:
        findings.append(Finding(Code.LANG, html_rel, 'lang="fr" manquant'))
    return tuple(findings)


def _drift_message(expected: str, actual: str | None) -> str:
    if actual is None:
        return "fichier dérivé manquant"
    limit = min(len(expected), len(actual))
    index = next((i for i in range(limit) if expected[i] != actual[i]), limit)
    snippet = actual[index : index + 40].replace("\n", "\\n")
    return f"fichier dérivé différent au caractère {index + 1} : {snippet}"


def _derived_findings(
    modules: Sequence[Module],
    annex_qmd: str | None,
    files: Mapping[str, str | None],
) -> tuple[Finding, ...]:
    """Compare committed generated files to the derivers.

    HOME_CARDS must equal _derive_home_cards. PARCOURS_SEQUENCE must equal
    _derive_parcours. Each CHROME depth must equal _derive_chrome.
    GLOSSARY_FRAGMENT must equal _derive_glossary(annex_qmd). A mismatch or
    a missing file is listing-drift, chrome-drift, or glossary-drift.
    """
    expected = (
        (HOME_CARDS, _derive_home_cards(modules), Code.LISTING_DRIFT),
        (PARCOURS_SEQUENCE, _derive_parcours(modules), Code.LISTING_DRIFT),
        (CHROME[0], _derive_chrome(modules, 0), Code.CHROME_DRIFT),
        (CHROME[1], _derive_chrome(modules, 1), Code.CHROME_DRIFT),
        (CHROME[2], _derive_chrome(modules, 2), Code.CHROME_DRIFT),
        (GLOSSARY_FRAGMENT, _derive_glossary(annex_qmd), Code.GLOSSARY_DRIFT),
    )
    findings: list[Finding] = []
    for rel, want, code in expected:
        got = files.get(rel)
        if got != want:
            findings.append(Finding(code, rel, _drift_message(want, got)))
    return tuple(findings)


def _link_findings(
    modules: Sequence[Module],
    pages: Sequence[HtmlPage],
) -> tuple[Finding, ...]:
    """Require every published HTML page to link the catalog.

    Each page's html must contain _href(page.depth, module.slug) for every
    module. When require_titles is true, it must also contain module.title,
    TRACK_LABEL[module.track], STATUS_LABEL[module.status], the hours
    integer followed by " h" when hours is set, and the jalon when set.
    A miss is missing-link. Home and parcours set require_titles. Module
    pages and the other site pages still require the hrefs.
    """
    findings: list[Finding] = []
    for page in pages:
        for module in modules:
            href = _href(page.depth, module.slug)
            if href not in page.html:
                findings.append(Finding(Code.MISSING_LINK, page.rel_html, f"lien absent : {href}"))
            if not page.require_titles:
                continue
            bits = [module.title, TRACK_LABEL[module.track], STATUS_LABEL[module.status]]
            if module.hours is not None:
                bits.append(f"{module.hours} h")
            if module.jalon:
                bits.append(module.jalon)
            for bit in bits:
                if not _html_contains(page.html, bit):
                    findings.append(
                        Finding(Code.MISSING_LINK, page.rel_html, f"mention absente : {bit}")
                    )
    return tuple(findings)


def _has_en_dir(root: Path) -> bool:
    for dirpath, dirnames, _filenames in os.walk(root):
        parts = Path(dirpath).resolve().relative_to(root.resolve()).parts
        if any(part in _SKIP_DIRS for part in parts):
            dirnames.clear()
            continue
        if "en" in dirnames:
            return True
    return False


def _publishing_files(root: Path, html_rels: Sequence[str]) -> dict[str, str | None]:
    files: dict[str, str | None] = {}
    for rel in (".nojekyll", PAPER_CSS, THEME_JS, *CLOSINGS.values(), *html_rels):
        files[rel] = _read_text(root / rel)
    workflow = root / ".github" / "workflows"
    if not workflow.is_dir():
        files[".github/workflows"] = None
    else:
        entries = sorted(path for path in workflow.iterdir() if path.is_file())
        if not entries:
            files[".github/workflows"] = None
        else:
            files[".github/workflows"] = ""
            for path in entries:
                files[path.relative_to(root).as_posix()] = _read_text(path) or ""
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if any(part in _SKIP_DIRS for part in Path(rel).parts):
            continue
        if path.suffix.lower() not in _TEXT_SUFFIXES and path.name != ".nojekyll":
            continue
        files.setdefault(rel, _read_text(path))
    if _has_en_dir(root):
        files["en/"] = ""
    return files


def _publishing_findings(files: Mapping[str, str | None]) -> tuple[Finding, ...]:
    """Check theme, KaTeX, brand, nojekyll, and the workflow text.

    .nojekyll must exist. paper.css must contain prefers-color-scheme,
    data-theme, prefers-contrast, .def, .thm, and .note. theme.js must
    contain THEME_KEY and must not contain "modules/". Each closing file
    must contain _theme_src for its depth.     Every published html must contain
    KATEX_JS_TAG and KATEX_CSS_TAG each once. The previous theme key must be
    absent from the tree texts, and a directory named en must be absent. Every workflow
    file under .github/workflows must contain each WORKFLOW_MUST_CONTAIN
    entry and must not contain a WORKFLOW_FORBIDDEN entry. The joined
    workflow text must include those required commands. A missing workflows
    directory is workflow.
    """
    findings: list[Finding] = []
    if files.get(".nojekyll") is None:
        findings.append(Finding(Code.NOJEKYLL, ".nojekyll", ".nojekyll manquant"))
    css = files.get(PAPER_CSS)
    if css is None:
        findings.append(Finding(Code.THEME, PAPER_CSS, "paper.css manquant"))
    else:
        for hook in _CSS_HOOKS:
            if hook not in css:
                findings.append(Finding(Code.THEME, PAPER_CSS, f"css sans {hook}"))
    script = files.get(THEME_JS)
    if script is None:
        findings.append(Finding(Code.THEME, THEME_JS, "theme.js manquant"))
    else:
        if THEME_KEY not in script:
            findings.append(Finding(Code.THEME, THEME_JS, "clé de thème absente"))
        if "modules/" in script:
            findings.append(Finding(Code.THEME, THEME_JS, "liste de modules dans theme.js"))
    for depth, rel in CLOSINGS.items():
        closing = files.get(rel)
        src = _theme_src(depth)
        if closing is None:
            findings.append(Finding(Code.THEME, rel, "fermeture manquante"))
        elif src not in closing:
            findings.append(Finding(Code.THEME, rel, f"script de thème absent : {src}"))
    for rel, text in files.items():
        if text is None or not _published_html(rel):
            continue
        for tag in (KATEX_JS_TAG, KATEX_CSS_TAG):
            if text.count(tag) != 1:
                findings.append(Finding(Code.KATEX, rel, "balise KaTeX absente ou dupliquée"))
                break
    for rel, text in files.items():
        if text and _FOREIGN_THEME in text:
            findings.append(Finding(Code.BRAND, rel, "clé de thème interdite"))
    if "en/" in files:
        findings.append(Finding(Code.BRAND, "en", "dossier en interdit"))
    if files.get(".github/workflows") is None and not any(
        rel.startswith(".github/workflows/") for rel in files
    ):
        findings.append(
            Finding(Code.WORKFLOW, ".github/workflows", "dossier workflows manquant")
        )
    else:
        workflow_files = {
            rel: text or ""
            for rel, text in files.items()
            if rel.startswith(".github/workflows/")
        }
        if not workflow_files:
            findings.append(
                Finding(Code.WORKFLOW, ".github/workflows", "dossier workflows manquant")
            )
        joined = "\n".join(workflow_files[rel] for rel in sorted(workflow_files))
        for rel in sorted(workflow_files):
            text = workflow_files[rel]
            for needle in WORKFLOW_MUST_CONTAIN:
                if needle not in text:
                    findings.append(
                        Finding(Code.WORKFLOW, rel, f"workflow incomplet : {needle}")
                    )
            for banned in WORKFLOW_FORBIDDEN:
                if banned in text:
                    findings.append(Finding(Code.WORKFLOW, rel, "commande workflow interdite"))
        for needle in WORKFLOW_MUST_CONTAIN:
            if workflow_files and needle not in joined:
                findings.append(
                    Finding(Code.WORKFLOW, ".github/workflows", f"workflow incomplet : {needle}")
                )
    return tuple(findings)


def _published_html(rel: str) -> bool:
    if rel in {
        "index.html",
        "parcours/index.html",
        "glossaire/index.html",
        "programmes/index.html",
    }:
        return True
    parts = rel.split("/")
    return len(parts) == 3 and parts[0] == "modules" and parts[2] == "index.html"


def _html_rel(rel_qmd: str) -> str:
    return Path(rel_qmd).with_suffix(".html").as_posix()


def _annex_qmd(root: Path, modules: Sequence[Module]) -> str | None:
    annexes = [module for module in modules if module.track == Track.ANNEXE]
    if len(annexes) != 1:
        return None
    return _read_text(root / "modules" / annexes[0].slug / "index.qmd")


def check_gates(root: Path) -> CheckReport:
    """Return every contract failure under root.

    Never write. Never invoke Quarto. Raise FileNotFoundError when root is
    not a directory. Content and publish problems are findings, not exceptions.
    Read the tree, then concatenate findings in this order.

    1. Catalog boundary findings from _load_catalog.
    2. Derived-file drift from _derived_findings.
    3. Each module's _page_findings, _fact_findings, in catalog order.
    4. _glossary_findings.
    5. _site_findings in SITE_PAGES order.
    6. _link_findings.
    7. _publishing_findings.

    report.ok is true only when that tuple is empty. Module HTML is depth 2.
    Pass require_titles for index.html and parcours/index.html only.
    """
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    catalog = _load_catalog(root)
    module_text: dict[str, str] = {}
    module_html: dict[str, str | None] = {}
    for module in catalog.modules:
        rel = f"modules/{module.slug}/index.qmd"
        html_rel = f"modules/{module.slug}/index.html"
        module_text[rel] = _read_text(root / rel) or ""
        module_html[html_rel] = _read_text(root / html_rel)
    annex_qmd = _annex_qmd(root, catalog.modules)
    derived = {
        rel: _read_text(root / rel)
        for rel in (HOME_CARDS, PARCOURS_SEQUENCE, GLOSSARY_FRAGMENT, *CHROME.values())
    }
    findings: list[Finding] = list(catalog.findings)
    findings.extend(_derived_findings(catalog.modules, annex_qmd, derived))
    for module in catalog.modules:
        rel = f"modules/{module.slug}/index.qmd"
        html_rel = f"modules/{module.slug}/index.html"
        findings.extend(
            _page_findings(module, module_text[rel], module_html[html_rel], rel, html_rel)
        )
        findings.extend(_fact_findings(rel, module_text[rel]))
    texts = dict(module_text)
    site_qmd: dict[str, str | None] = {}
    site_html: dict[str, str | None] = {}
    for page in SITE_PAGES:
        qmd = _read_text(root / page.rel_qmd)
        html_rel = _html_rel(page.rel_qmd)
        html = _read_text(root / html_rel)
        site_qmd[page.rel_qmd] = qmd
        site_html[html_rel] = html
        if qmd is not None:
            texts[page.rel_qmd] = qmd
    glossaire_html = site_html.get("glossaire/index.html")
    if glossaire_html is not None:
        texts["glossaire/index.html"] = glossaire_html
    findings.extend(_glossary_findings(catalog, texts))
    pages: list[HtmlPage] = []
    for page in SITE_PAGES:
        html_rel = _html_rel(page.rel_qmd)
        html = site_html[html_rel]
        findings.extend(_site_findings(page, site_qmd[page.rel_qmd], html))
        if html is not None:
            pages.append(
                HtmlPage(
                    html_rel,
                    page.depth,
                    html,
                    page.kind in {SiteKind.HOME, SiteKind.PARCOURS},
                )
            )
    for module in catalog.modules:
        html_rel = f"modules/{module.slug}/index.html"
        html = module_html[html_rel]
        if html is not None:
            pages.append(HtmlPage(html_rel, 2, html, False))
    findings.extend(_link_findings(catalog.modules, pages))
    html_rels = [page.rel_html for page in pages]
    findings.extend(_publishing_findings(_publishing_files(root, html_rels)))
    return CheckReport(tuple(findings))


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except OSError:
            pass
        raise


def _require_quarto(quarto: str) -> None:
    try:
        proc = subprocess.run(
            [quarto, "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise QuartoMissing(quarto) from exc
    if proc.returncode != 0:
        raise QuartoMissing(quarto)


def _restore_tag(html: str, tag: str, unpinned: re.Pattern[str]) -> str:
    token = "\u0000MCI_KATEX_PIN\u0000"
    protected = html.replace(tag, token)
    stripped = unpinned.sub("", protected)
    if html.count(tag) == 1 and stripped == protected:
        return html
    cleaned = stripped.replace(token, "")
    if "</head>" in cleaned:
        return cleaned.replace("</head>", tag + "</head>", 1)
    return cleaned + tag


def _restore_katex(html: str) -> str:
    html = _restore_tag(html, KATEX_JS_TAG, _UNPINNED_JS)
    return _restore_tag(html, KATEX_CSS_TAG, _UNPINNED_CSS)


def _render_qmd(quarto: str, root: Path, rel_qmd: str) -> None:
    proc = subprocess.run(
        [quarto, "render", rel_qmd],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        if detail:
            print(detail, file=sys.stderr)
        raise RenderFailed(rel_qmd, proc.returncode)
    html_path = root / _html_rel(rel_qmd)
    if not html_path.is_file():
        return
    original = html_path.read_text(encoding="utf-8")
    restored = _restore_katex(original)
    if restored != original:
        _atomic_write(html_path, restored)


def build_site(root: Path, *, quarto: str = "quarto") -> CheckReport:
    """Write derived files, render every author page, restore KaTeX, and re-check.

    Raise QuartoMissing before any write when quarto cannot be started.
    Write each derived file by os.replace from a temporary file in the same
    directory. Render every parsed module and every site qmd, even when
    index.html already exists. Make KATEX_JS_TAG and KATEX_CSS_TAG occur once
    in each published HTML file, replacing an unpinned katex 0.19.0 tag when
    one is present and inserting the tag before </head> when it is absent.
    Raise RenderFailed with rel_qmd and returncode when a render exits
    non-zero. Return check_gates(root) after a complete render. A second run
    on an unchanged tree leaves identical bytes.
    """
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    _require_quarto(quarto)
    catalog = _load_catalog(root)
    annex_qmd = _annex_qmd(root, catalog.modules)
    derived = {
        HOME_CARDS: _derive_home_cards(catalog.modules),
        PARCOURS_SEQUENCE: _derive_parcours(catalog.modules),
        CHROME[0]: _derive_chrome(catalog.modules, 0),
        CHROME[1]: _derive_chrome(catalog.modules, 1),
        CHROME[2]: _derive_chrome(catalog.modules, 2),
        GLOSSARY_FRAGMENT: _derive_glossary(annex_qmd),
    }
    for rel, text in derived.items():
        _atomic_write(root / rel, text)
    targets = [f"modules/{module.slug}/index.qmd" for module in catalog.modules]
    targets.extend(page.rel_qmd for page in SITE_PAGES if (root / page.rel_qmd).is_file())
    for rel in targets:
        _render_qmd(quarto, root, rel)
    return check_gates(root)
