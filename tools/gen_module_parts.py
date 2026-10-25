#!/usr/bin/env python3
"""Generate the shared parts of every course page from data/curriculum.json (idempotent).

In courses/<id>/index.md this script:
  * writes the "Pour qui", "Prérequis" and "Projets liés" rows of the module fiche from the curriculum
    (generic, by entry profile, never about one person; prerequisites and projects never drift);
  * writes two sub-sections of the introduction between markers, regenerated on every run:
      ### Place dans le parcours {#place}        phase, prerequisites, what the module prepares, projects,
                                                market skills it covers (data/coverage.json, if present)
      ### Comment travailler ce module {#travailler}   priority by entry profile and study method
  * keeps the page structure aligned with the LLGA and MVA course pages: "0. Avant de commencer" with
    "0.1. Questions de positionnement", one "### Lab N.M — title" sub-section per lab, and the four
    parts of "Sources et portée" as sub-sections.
    python3 tools/gen_module_parts.py [module-id ...] && python3 tools/build.py courses
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = json.loads((ROOT / "data" / "curriculum.json").read_text(encoding="utf-8"))
MODS = {m["id"]: m for m in C["modules"]}
PHASES = {p["n"]: p for p in C["phases"]}
PROFILES = C["profiles"]
PRIO = {"A": "à fond", "B": "normal", "C": "survol guidé"}
PRIO_WHY = {"A": "tous les chapitres, tous les labs et les exercices ★★★",
            "B": "les chapitres dans l'ordre, les labs, les exercices ★ et ★★",
            "C": "les questions de positionnement, les chapitres signalés ci-dessous, un lab et le checkpoint"}
SOURCES_PARTS = [("Documenté.", "Documenté", "documente"), ("Recommandé.", "Recommandé", "recommande"),
                 ("À vérifier.", "À vérifier", "a-verifier"),
                 ("Mesuré dans le bac à sable, pas vérifié sur un cloud.", "Mesuré dans le bac à sable, pas vérifié sur un cloud", "mesure-bac-a-sable"),
                 ("Hors périmètre.", "Hors périmètre", "hors-perimetre")]


def mlink(i):
    m = MODS[i]
    return f"[module {m['number']} — {m['title']}](../{i}/index.html)"


def skill_labels():
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from market_analysis import SKILL_FR
        return SKILL_FR
    except Exception:  # noqa: BLE001
        return {}


def place(m):
    followers = [x["id"] for x in C["modules"] if m["id"] in x["prerequisites"]]
    projects = [p for p in C["projects"] if m["id"] in p["modules"]]
    ph = PHASES[m["phase"]]
    lines = ["### Place dans le parcours {#place}", "",
             f"-   **Phase {m['phase']} — {ph['title']}** ({ph['weeks_hint']}) : {ph['goal'][0].lower() + ph['goal'][1:]}"]
    lines.append("-   **S'appuie sur** : " + (", ".join(mlink(i) for i in sorted(m["prerequisites"], key=lambda i: MODS[i]["number"])) if m["prerequisites"] else "aucun module ; c'est un point d'entrée") + ".")
    if followers:
        lines.append("-   **Prépare** : " + ", ".join(mlink(i) for i in followers) + ".")
    if projects:
        lines.append("-   **Projets qui s'en servent** : " + ", ".join(f"[{p['title'].split(' — ')[0]} — {p['title'].split(' — ', 1)[-1]}](../../projects/{p['id']}/index.html)" for p in projects) + ".")
    cov_f = ROOT / "data" / "coverage.json"
    if cov_f.exists():
        cov = json.loads(cov_f.read_text(encoding="utf-8")).get("modules", {}).get(m["id"], {})
        fr = skill_labels()
        taught = sorted((s for s, v in cov.items() if (v.get("depth", 0) if isinstance(v, dict) else v) >= 2),
                        key=lambda s: -(cov[s].get("depth", 0) if isinstance(cov[s], dict) else cov[s]))
        if taught and fr:
            lines.append("-   **Compétences demandées dans les offres d'emploi et travaillées ici** : "
                         + ", ".join(fr.get(s, s) for s in taught) + " (voir [l'analyse du marché](../../market/index.html#couverture)).")
    return "\n".join(lines)


def travailler(m):
    rows = ["### Comment travailler ce module {#travailler}", "",
            "Le parcours s'adresse à plusieurs profils d'entrée, décrits dans le [point de départ](../../profile/index.html). "
            "Le tableau donne la priorité conseillée pour ce module ; les questions de positionnement (section 0.1) la confirment ou la corrigent.", "",
            "| Profil d'entrée | Priorité | Ce que cela veut dire ici |", "|---|---|---|"]
    for p in PROFILES:
        c = m["study"][p["id"]]
        rows.append(f"| {p['name']} | {PRIO[c]} | {PRIO_WHY[c]} |")
    rows += ["", f"**À ne pas survoler.** {m['focus']}", "",
             "**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, "
             "en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices "
             "dans l'ordre des étoiles. Terminez par le checkpoint de sortie : une capacité compte quand sa preuve existe."]
    return "\n".join(rows)


def block(text, name, content):
    beg, end = f"<!-- gen:{name} -->", f"<!-- /gen:{name} -->"
    new = f"{beg}\n{content}\n{end}"
    if beg in text:
        return re.sub(re.escape(beg) + r".*?" + re.escape(end), lambda _: new, text, flags=re.S)
    return None


def insert_before_heading(text, anchor, content):
    m = re.search(r"^#{2,3} .*\{#" + re.escape(anchor) + r"\}\s*$", text, re.M)
    if not m:
        raise SystemExit(f"anchor #{anchor} not found")
    return text[:m.start()] + content + "\n\n" + text[m.start():]


def restructure(text):
    # 0. Avant de commencer + 0.1
    text = re.sub(r"^## Avant de commencer \{#avant\}\s*$", "## 0. Avant de commencer {#avant}", text, flags=re.M)
    if "{#positionnement}" not in text:
        text = re.sub(r"^(## 0\. Avant de commencer \{#avant\}\s*\n)", r"\1\n### 0.1. Questions de positionnement {#positionnement}\n\n", text, flags=re.M)
    # labs: one sub-section per lab, title moved from the box tag to the heading
    def lab(mm):
        num, title = mm.group(1), mm.group(2).strip()
        return f"### Lab {num} — {title} {{#lab-{num.replace('.', '-')}}}\n\n::: lab\n"
    text = re.sub(r"^::: lab\s*\n\[Lab (\d+\.\d+) — ([^\]]+)\]\{\.tag\}[ \t]*\n", lab, text, flags=re.M)
    # sources: the four bold lead-ins become sub-sections
    m = re.search(r"^## Sources et portée \{#sources\}\s*$", text, re.M)
    if m:
        head, tail = text[:m.end()], text[m.end():]
        for lead, title, anchor in SOURCES_PARTS:
            tail = re.sub(r"^\*\*" + re.escape(lead) + r"\*\*\s*", f"### {title} {{#{anchor}}}\n\n", tail, count=1, flags=re.M)
        text = head + tail
    return text


def fiche(text, m):
    """Rows of the module fiche that must agree with data/curriculum.json: who it is for, prerequisites, projects."""
    row = f"| Pour qui | {m['audience']} |"
    text, n = re.subn(r"^\| Statut pour le lecteur de référence \|.*\|[ \t]*$", lambda _: row, text, flags=re.M)
    if not n:
        text = re.sub(r"^\| Pour qui \|.*\|[ \t]*$", lambda _: row, text, flags=re.M)
    pre = ", ".join(f"[Module {MODS[i]['number']} — {MODS[i]['title']}](../{i}/index.html)"
                    for i in sorted(m["prerequisites"], key=lambda i: MODS[i]["number"])) or "aucun"
    if m.get("prerequisites_note"):
        pre += f", {m['prerequisites_note']}"
    text = re.sub(r"^\| Prérequis \|.*\|[ \t]*$", lambda _: f"| Prérequis | {pre} |", text, flags=re.M)
    projects = [p for p in C["projects"] if m["id"] in p["modules"]]
    proj = ", ".join(f"[{p['title']}](../../projects/{p['id']}/index.html)" for p in projects) or "aucun"
    text = re.sub(r"^\| (Projets liés|Projets qui s'appuient sur ce module) \|.*\|[ \t]*$", lambda _: f"| Projets liés | {proj} |", text, flags=re.M)
    return re.sub(r"^(\|.*\|)\n(#{2,3} )", r"\1\n\n\2", text, flags=re.M)   # a table is followed by a blank line


def main(argv):
    ids = argv or [m["id"] for m in C["modules"]]
    for i in ids:
        f = ROOT / "courses" / i / "index.md"
        if not f.exists():
            continue
        m = MODS[i]
        t = f.read_text(encoding="utf-8")
        t = fiche(t, m)
        t = restructure(t)
        for name, anchor, fn in (("place", "seances", place), ("travailler", "avant", travailler)):
            r = block(t, name, fn(m))
            if r is None:
                r = insert_before_heading(t, anchor, f"<!-- gen:{name} -->\n{fn(m)}\n<!-- /gen:{name} -->")
            t = r
        f.write_text(t, encoding="utf-8")
        print(f"updated courses/{i}/index.md")


if __name__ == "__main__":
    main(sys.argv[1:])
