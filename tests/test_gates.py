import shutil
import tempfile
import unittest
from html import escape
from pathlib import Path

from tools.gates import Code, _html_contains, check_gates

REPO = Path(__file__).resolve().parents[1]
MARKER = "<!-- derived from module front matter. build_site overwrites this file. -->"
BOOT = (
    '<script>(function(){try{var t=localStorage.getItem("mci-theme");'
    'if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t);}'
    "catch(e){}})();</script>"
)
KATEX_JS = (
    "<script>window.backupDefine = window.define; window.define = undefined;</script>"
    '<script src="https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/katex.min.js" '
    'integrity="sha384-QFFtAGzvvj+bfgCGxXJlNZZR1nXEZgvG8tDLCCY1F19xl20WlfTYgguB4VcNdxYk" '
    'crossorigin="anonymous"></script>'
)
KATEX_CSS = (
    "<script>window.define = window.backupDefine; window.backupDefine = undefined;</script>"
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/katex.min.css" '
    'integrity="sha384-3rdsX6e5mueWyoweR9NIVmtEsUkokpBT/0ALqKKIBMr9j4qhHkaIkAcGgsE6uVlp" '
    'crossorigin="anonymous">'
)
TERMS = (
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
)
STAMPED = frozenset({"TPE", "Hyperband/ASHA"})
PUBLISHING = (
    "assets/paper.css",
    "assets/theme.js",
    "assets/closing-d0.html",
    "assets/closing-d1.html",
    "assets/closing-d2.html",
    ".nojekyll",
    ".github/workflows/gates.yml",
)


def _show(report) -> str:
    return "\n".join(
        f"{item.code.value} {item.path} {item.message}" for item in report.findings
    )


def _fill(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _front(title: str, depth: int, mci: str | None = None) -> str:
    prefix = "../" * depth
    lines = [
        "---",
        f'title: "{title}"',
        "lang: fr",
        "format:",
        "  html:",
        "    theme: none",
        f"    css: {prefix}assets/paper.css",
        "    html-math-method:",
        "      method: katex",
        '      url: "https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/katex.min.js"',
        f"    include-before-body: {prefix}generated/chrome-d{depth}.html",
        f"    include-after-body: {prefix}assets/closing-d{depth}.html",
    ]
    if mci is not None:
        lines.append(mci.rstrip("\n"))
    lines.append("---")
    return "\n".join(lines) + "\n"


def _bare(title: str, status: str) -> str:
    return f'---\ntitle: "{title}"\nlang: fr\nmci:\n  status: {status}\n  order: 1\n---\n'


def _html(body: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="fr">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        + KATEX_JS
        + "\n"
        + KATEX_CSS
        + "\n"
        "</head>\n"
        "<body>\n"
        + body
        + "\n</body>\n</html>\n"
    )


def _card(depth: int, slug: str, title: str) -> str:
    return f"[{title}]({'../' * depth}modules/{slug}/). Annexe. Squelette"


def _chrome(depth: int, slug: str, title: str) -> str:
    prefix = "../" * depth

    def site(rel: str) -> str:
        return f"{prefix}{rel}"

    home = site("index.html")
    lines = [
        MARKER,
        BOOT,
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
        f'<a href="{site("parcours/index.html")}">Parcours</a>',
        f'<a href="{site("glossaire/index.html")}">Glossaire</a>',
        f'<a href="{site("programmes/index.html")}">Programmes</a>',
        f'<a href="{prefix}modules/{slug}/">{escape(title)}</a>',
        "</nav>",
        '<main id="main">',
    ]
    return "\n".join(lines) + "\n"


def _glossary_section() -> str:
    lines = ["## Glossaire", ""]
    for term in TERMS:
        lines.append(f"### {term}")
        lines.append("")
        lines.append("Anticipé." if term in STAMPED else "Définition courte.")
        lines.append("")
    return "\n".join(lines)


def _copy_publishing(dest: Path) -> None:
    for rel in PUBLISHING:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, target)


def _valid_tree(root: Path) -> None:
    slug = "a-glossaire"
    title = "Glossaire"
    section = _glossary_section()
    qmd = (
        _front(title, 2, "mci:\n  status: skeleton\n  order: 1")
        + "## Objectifs\n\nPoser les termes.\n\n"
        + "## Travaux pratiques prévus\n\nUn atelier court.\n\n"
        + section
        + "## Sources\n\nDocumentation interne.\n"
    )
    _fill(root, f"modules/{slug}/index.qmd", qmd)
    _fill(
        root,
        "index.qmd",
        _front("Accueil", 0) + "\nPage d'accueil.\n\n{{< include generated/home-cards.md >}}\n",
    )
    _fill(
        root,
        "parcours/index.qmd",
        _front("Parcours", 1)
        + "\n## Acquis\n\nDéjà vu.\n\n## À consolider\n\nÀ revoir.\n\n"
        + "## À apprendre\n\nLa suite.\n\n"
        + "{{< include ../generated/parcours-sequence.md >}}\n",
    )
    _fill(
        root,
        "glossaire/index.qmd",
        _front("Glossaire", 1) + "\n{{< include ../generated/glossaire.md >}}\n",
    )
    _fill(
        root,
        "programmes/index.qmd",
        _front("Programmes", 1) + "\n## À venir\n\nLe détail viendra ensuite.\n",
    )
    _fill(root, "generated/home-cards.md", f"{MARKER}\n- {_card(0, slug, title)}\n")
    _fill(root, "generated/parcours-sequence.md", f"{MARKER}\n1. {_card(1, slug, title)}\n")
    _fill(root, "generated/glossaire.md", f"{MARKER}\n{section.strip(chr(10))}\n")
    for depth in (0, 1, 2):
        _fill(root, f"generated/chrome-d{depth}.html", _chrome(depth, slug, title))
    _copy_publishing(root)
    _fill(
        root,
        "index.html",
        _html(f'<a href="modules/{slug}/">{title}</a>\n<p>Annexe. Squelette.</p>'),
    )
    _fill(
        root,
        "parcours/index.html",
        _html(f'<a href="../modules/{slug}/">{title}</a>\n<p>Annexe. Squelette.</p>'),
    )
    _fill(
        root,
        "glossaire/index.html",
        _html(
            f'<a href="../modules/{slug}/">{title}</a>\n<pre>\n' + "\n".join(TERMS) + "\n</pre>"
        ),
    )
    _fill(
        root,
        "programmes/index.html",
        _html(f'<a href="../modules/{slug}/">{title}</a>'),
    )
    _fill(
        root,
        f"modules/{slug}/index.html",
        _html(
            f'<a href="../../modules/{slug}/">{title}</a>\n'
            "<h2>Objectifs</h2>\n<h2>Travaux pratiques prévus</h2>"
        ),
    )


class GateTests(unittest.TestCase):
    def test_html_accepts_pandoc_apostrophe(self) -> None:
        straight = "Exercice 2. Lire la RAM de l'hôte"
        curly = "Exercice 2. Lire la RAM de l\u2019hôte"
        self.assertTrue(_html_contains(curly, straight))
        self.assertFalse(_html_contains("Exercice 2. Lire la RAM", straight))

    def test_skeleton_missing_travaux(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _fill(
                root,
                "modules/m05-court/index.qmd",
                _bare("Court", "skeleton") + "## Objectifs\n\nUn but.\n",
            )
            report = check_gates(root)
        self.assertFalse(report.ok)
        self.assertTrue(
            any(
                item.code == Code.MISSING_SECTION and "Travaux pratiques prévus" in item.message
                for item in report.findings
            ),
            _show(report),
        )

    def test_minimal_skeleton_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _valid_tree(root)
            report = check_gates(root)
        self.assertTrue(report.ok, _show(report))

    def test_full_page_without_examen_fails(self) -> None:
        body = (
            "## Objectifs\n\nUn but.\n\n"
            "## Prérequis\n\nAucun.\n\n"
            "## Notes de cours\n\nDes notes.\n\n"
            "## Exercices\n\n### Exercice 1\n\nA.\n\n### Exercice 2\n\nB.\n\n"
            "### Exercice 3\n\nC.\n\n### Exercice 4\n\nD.\n\n"
            "## Projet solo\n\nSeul.\n\n"
            "## Projet de groupe\n\nEnsemble.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _fill(
                root,
                "modules/m04-laboratoire/index.qmd",
                _bare("Laboratoire", "full") + body,
            )
            report = check_gates(root)
        self.assertFalse(report.ok)
        self.assertTrue(
            any(
                item.code == Code.MISSING_SECTION and "Examen" in item.message
                for item in report.findings
            ),
            _show(report),
        )

    def test_rpeak_group_requires_both_figures(self) -> None:
        for figure in ("16,32 PFlop", "16.32 PFlop"):
            with self.subTest(figure=figure):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    _fill(
                        root,
                        "modules/m06-chiffre/index.qmd",
                        _bare("Mesure", "skeleton")
                        + f"## Objectifs\n\n{figure}\n\n## Travaux pratiques prévus\n\nUn atelier.\n",
                    )
                    report = check_gates(root)
                self.assertFalse(report.ok)
                self.assertTrue(
                    any(item.code == Code.FACT_GROUP for item in report.findings),
                    _show(report),
                )

    def test_synthese_without_step_anchor_fails(self) -> None:
        text = (REPO / "programmes" / "synthese.md").read_text(encoding="utf-8")
        lines = text.splitlines()
        start = lines.index("## Auto-formation") + 1
        items: list[str] = []
        for line in lines[start:]:
            if not line.strip():
                continue
            if line.startswith("#"):
                break
            number, dot, rest = line.partition(". ")
            if number.isdigit() and dot:
                items.append("<li>" + rest + "</li>")
        body = '<ol type="1">\n' + "\n".join(items) + "\n</ol>"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            programme = root / "programmes"
            programme.mkdir()
            for name in ("records.py", "domain.py", "check_links.py"):
                shutil.copyfile(REPO / "programmes" / name, programme / name)
            _fill(root, "programmes/synthese.html", _html(body))
            report = check_gates(root)
        self.assertFalse(report.ok, _show(report))
        self.assertTrue(
            any(
                item.code == Code.PROGRAMMES and item.message.startswith("ancre absente : etape-")
                for item in report.findings
            ),
            _show(report),
        )

    def test_skeleton_prerequis_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _fill(
                root,
                "modules/m07-avant/index.qmd",
                _bare("Avant", "skeleton")
                + "## Objectifs\n\nUn but.\n\n## Prérequis\n\nUn acquis.\n\n"
                + "## Travaux pratiques prévus\n\nUn atelier.\n",
            )
            report = check_gates(root)
        self.assertFalse(report.ok)
        self.assertTrue(
            any(
                item.code == Code.FORBIDDEN_SECTION and "Prérequis" in item.message
                for item in report.findings
            ),
            _show(report),
        )


if __name__ == "__main__":
    unittest.main()
