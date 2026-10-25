import shutil
import tempfile
import unittest
from html import escape
from pathlib import Path

from tools.gates import (
    Code,
    _annex_qmd,
    _derive_chrome,
    _derive_glossary,
    _derive_home_cards,
    _derive_parcours,
    _describe_programmes,
    _html_contains,
    _load_catalog,
    check_gates,
)

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


def _sync_derived(root: Path) -> None:
    catalog = _load_catalog(root)
    publication = _describe_programmes(root, catalog.modules)
    _fill(root, "generated/home-cards.md", _derive_home_cards(catalog.modules))
    _fill(
        root,
        "generated/parcours-sequence.md",
        _derive_parcours(catalog.modules, publication.anchors),
    )
    _fill(root, "generated/glossaire.md", _derive_glossary(_annex_qmd(root, catalog.modules)))
    for depth in (0, 1, 2):
        _fill(
            root,
            f"generated/chrome-d{depth}.html",
            _derive_chrome(catalog.modules, depth, publication.links),
        )


def _full_page(title: str, order: int, extras: str) -> str:
    exercises = "".join(f"### Exercice {i}\n\nFaire {i}.\n\n" for i in range(1, 5))
    questions = "".join(f"### Question {i}\n\nRépondre {i}.\n\n" for i in range(1, 4))
    return (
        _front(title, 2, f"mci:\n  status: full\n  order: {order}")
        + "## Objectifs\n\nLire la page.\n\n"
        + "## Prérequis\n\nAucun acquis particulier.\n\n"
        + "## Notes de cours\n\nDes notes.\n\n"
        + extras
        + "## Exercices\n\n"
        + exercises
        + "## Projet solo\n\nSeul.\n\n## Projet de groupe\n\nEnsemble.\n\n"
        + "## Examen\n\n"
        + questions
        + "## Sources\n\nNotes internes.\n"
    )


def _link_lines(depth: int, modules: list[tuple[str, str, str, str]]) -> str:
    prefix = "../" * depth
    return "\n".join(
        f'<a href="{prefix}modules/{slug}/">{title}</a> {track}. {status}.'
        for slug, title, track, status in modules
    )


class InferenceGateTests(unittest.TestCase):
    def test_banned_document_file(self) -> None:
        ext = "." + "pd" + "f"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ("quote" + ext)).write_bytes(b"x")
            report = check_gates(root)
        self.assertTrue(
            any(
                item.code == Code.INFERENCE and item.message == f"fichier interdit : {ext}"
                for item in report.findings
            ),
            _show(report),
        )

    def test_banned_word(self) -> None:
        word = "confiden" + "tiel"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _fill(root, "note.md", f"Le mot {word} est là.\n")
            report = check_gates(root)
        self.assertTrue(
            any(item.code == Code.INFERENCE and item.message == "chaîne interdite" for item in report.findings),
            _show(report),
        )

    def test_banned_extension_mention(self) -> None:
        mention = "table" + "." + "xls" + "x"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _fill(root, "note.md", f"Voir {mention}.\n")
            report = check_gates(root)
        self.assertTrue(
            any(item.code == Code.INFERENCE and "mention interdite" in item.message for item in report.findings),
            _show(report),
        )

    def test_programme_handbook_mention_is_kept(self) -> None:
        mention = "handbook" + "." + "pd" + "f"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _fill(root, "programmes/usa.md", f"Voir {mention}.\n")
            report = check_gates(root)
        self.assertFalse(
            any(
                item.code == Code.INFERENCE and "mention interdite" in item.message
                for item in report.findings
            ),
            _show(report),
        )

    def test_course_marker_requires_inference_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _fill(root, "modules/m01-anatomie-noeud/index.qmd", _bare("Anatomie", "skeleton"))
            report = check_gates(root)
        self.assertTrue(
            any(
                item.code == Code.INFERENCE and item.message == "page d'inférence absente"
                for item in report.findings
            ),
            _show(report),
        )

    def test_station_prices_must_sit_together(self) -> None:
        extras = (
            "## Decode et prefill\n\nTexte.\n\n"
            "## Spark et Station\n\nTexte.\n\n"
            "## Prix de la DGX Station\n\n90 000 et 105 000 seulement.\n\n"
            "## Rigs WRX90\n\nTexte.\n\n"
            "## Mac Studio\n\nTexte.\n\n"
            "## Concurrence et débit\n\nTexte.\n\n"
            "## Bruit\n\nTexte.\n\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _fill(root, "modules/m16-machines/index.qmd", _full_page("Machines", 2, extras))
            report = check_gates(root)
        self.assertTrue(
            any(
                item.code == Code.INFERENCE and "91 532" in item.message
                for item in report.findings
            ),
            _show(report),
        )

    def test_missing_image(self) -> None:
        extras = "## Grille de prix\n\n![graphique](absent.png)\n\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _fill(root, "modules/m15-blackwell/index.qmd", _full_page("Prix", 2, extras))
            report = check_gates(root)
        self.assertTrue(
            any(
                item.code == Code.INFERENCE and item.message == "image absente : absent.png"
                for item in report.findings
            ),
            _show(report),
        )

    def test_complete_inference_section_passes(self) -> None:
        refs = "\n".join(
            [
                "https://github.com/datawhalechina/zero-to-sglang",
                "https://datawhalechina.github.io/zero-to-sglang/eng/",
                "https://x.com/YichiZ03",
                "https://www.sglang.io/blog/hicache",
                "https://docs.sglang.io/docs/advanced_features/hicache",
                "25 octobre 2026",
            ]
        )
        price = (
            "90 000 vient de rapport-concurrence-spark-station-20261022.md. "
            "105 000 vient de configs-wrx90. "
            "91 532 vient de rapport-blackwell-prix-20261023.md. "
            "Les trois prix ne concordent pas."
        )
        pages = [
            ("m14-inference", "Inférence", 2, "## Carte de la section\n\nLa carte.\n\n## Références\n\n" + refs + "\n\n"),
            (
                "m15-blackwell",
                "Prix",
                3,
                "## Grille de prix\n\nLa grille.\n\n## Euros par gigaoctet\n\nLe ratio.\n\n"
                "## Tendances et régimes\n\nLes fits.\n\n## Lecture des courbes\n\n"
                "résumé uniquement, rapport complet manquant\n\n",
            ),
            (
                "m16-machines",
                "Machines",
                4,
                "## Decode et prefill\n\nTexte.\n\n## Spark et Station\n\nTexte.\n\n"
                f"## Prix de la DGX Station\n\n{price}\n\n## Rigs WRX90\n\nTexte.\n\n"
                "## Mac Studio\n\nTexte.\n\n## Concurrence et débit\n\nTexte.\n\n## Bruit\n\nTexte.\n\n",
            ),
            (
                "m17-cloud",
                "Cloud",
                5,
                "## Location réservée et achat local\n\nTexte.\n\n## Coût par jeton\n\nTexte.\n\n",
            ),
            (
                "m18-precision",
                "Précision",
                6,
                "## Débit\n\nTexte.\n\n## Mémoire\n\nTexte.\n\n## Qualité\n\nTexte.\n\n",
            ),
        ]
        modules = [("a-glossaire", "Glossaire", "Annexe", "Squelette")]
        modules.extend((slug, title, "Offre B", "Cours") for slug, title, _order, _extras in pages)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _valid_tree(root)
            for slug, title, order, extras in pages:
                qmd = _full_page(title, order, extras)
                _fill(root, f"modules/{slug}/index.qmd", qmd)
                headings = [
                    "Objectifs",
                    "Prérequis",
                    "Notes de cours",
                    "Exercices",
                    "Projet solo",
                    "Projet de groupe",
                    "Examen",
                    "Exercice 1",
                    "Exercice 2",
                    "Exercice 3",
                    "Exercice 4",
                    "Question 1",
                    "Question 2",
                    "Question 3",
                ]
                if slug == "m15-blackwell":
                    headings.append("résumé uniquement, rapport complet manquant")
                if slug == "m16-machines":
                    headings.append(price)
                body = "\n".join(f"<h2>{item}</h2>" for item in headings) + "\n" + extras
                _fill(
                    root,
                    f"modules/{slug}/index.html",
                    _html(body + "\n" + _link_lines(2, modules)),
                )
            _sync_derived(root)
            for rel, depth in (
                ("index.html", 0),
                ("parcours/index.html", 1),
                ("glossaire/index.html", 1),
                ("programmes/index.html", 1),
                ("modules/a-glossaire/index.html", 2),
            ):
                previous = (root / rel).read_text(encoding="utf-8")
                _fill(root, rel, previous.replace("</body>", _link_lines(depth, modules) + "\n</body>"))
            report = check_gates(root)
        self.assertTrue(report.ok, _show(report))


if __name__ == "__main__":
    unittest.main()
