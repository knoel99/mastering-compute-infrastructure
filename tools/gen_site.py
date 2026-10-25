#!/usr/bin/env python3
"""Generate index.md (home), path/index.md (roadmap) and data/nav.json from data/curriculum.json.

A module or project whose page (courses/<id>/index.md, projects/<id>/index.md) does not exist yet is
shown as "en préparation" (grey card, no link): the site never advertises content that is not there.

    python3 tools/gen_site.py && python3 tools/build.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = json.loads((ROOT / "data" / "curriculum.json").read_text(encoding="utf-8"))
MODS = {m["id"]: m for m in C["modules"]}
PROJ = {p["id"]: p for p in C["projects"]}
PHASES = {p["n"]: p for p in C["phases"]}
HPW = 12  # reference pace: hours per week
PROJ_BY_PHASE = {0: [], 1: [], 2: ["homelab-slurm"], 3: ["scaling-study", "resilient-trainer"], 4: ["multi-provider-scheduler", "gpu-observability"], 5: ["capstone-rfc"]}


def phase_weeks():
    """Week ranges of the phases at HPW hours a week, written back to data/curriculum.json (weeks_hint), so that the
    module pages (generated 'Place dans le parcours') and the roadmap give the same weeks."""
    start, changed = 1, False
    for n in sorted(PHASES):
        h = sum(m["hours"] for m in C["modules"] if m["phase"] == n) + sum(PROJ[i]["hours"] for i in PROJ_BY_PHASE[n])
        w = max(1, round(h / HPW))
        hint = f"semaines {start}-{start + w - 1}"
        if PHASES[n].get("weeks_hint") != hint:
            PHASES[n]["weeks_hint"], changed = hint, True
        start += w
    if changed:
        (ROOT / "data" / "curriculum.json").write_text(json.dumps(C, ensure_ascii=False, indent=1), encoding="utf-8")


def hfmt(x):
    """Hours in French notation: 30 -> "30", 30.5 -> "30,5"."""
    x = round(float(x), 2)
    return str(int(x)) if x == int(x) else f"{x:g}".replace(".", ",")


def has_course(i):
    return (ROOT / "courses" / i / "index.md").exists()


def has_project(i):
    return (ROOT / "projects" / i / "index.md").exists()


def verification_label(i):
    """'labs vérifiés' or 'non vérifié', read from the badges of the course page."""
    import yaml
    text = (ROOT / "courses" / i / "index.md").read_text(encoding="utf-8")
    meta = yaml.safe_load(text.split("\n---\n", 1)[0].lstrip("-\n")) or {}
    classes = {b.get("class") for b in meta.get("badges", [])}
    return "non vérifié" if "unverified" in classes else "labs vérifiés" if "verified" in classes else "rédigé"


def has_page(rel):
    return (ROOT / rel / "index.md").exists()


def status_label(m):
    return {"core": "Cœur", "skim": "Fondation", "bonus": "Bonus"}[m["status"]]


def card_course(m):
    meta = f"Module {m['number']:02d} · {hfmt(m['hours'])} h · {status_label(m)}"
    if has_course(m["id"]):
        return (f'<a class="card" href="courses/{m["id"]}/index.html"><h4>{m["title"]}</h4>'
                f'<p class="meta">{meta}</p><p>{m["summary"]}</p></a>')
    return (f'<div class="card" style="opacity:.78;border-style:dashed"><h4>{m["title"]}</h4>'
            f'<p class="meta">{meta} · en préparation</p><p>{m["summary"]}</p></div>')


def card_project(p):
    meta = f"Projet {p['number']} · {hfmt(p['hours'])} h"
    if has_project(p["id"]):
        return (f'<a class="card" href="projects/{p["id"]}/index.html"><h4>{p["title"].split(" — ", 1)[-1]}</h4>'
                f'<p class="meta">{meta}</p><p>{p["summary"]}</p></a>')
    return (f'<div class="card" style="opacity:.78;border-style:dashed"><h4>{p["title"].split(" — ", 1)[-1]}</h4>'
            f'<p class="meta">{meta} · en préparation</p><p>{p["summary"]}</p></div>')


def phase_blocks(card_fn):
    out = []
    for n in sorted(PHASES):
        ms = [m for m in C["modules"] if m["phase"] == n]
        out.append(f'### Phase {n} — {PHASES[n]["title"]} {{#phase{n} .phase .unnumbered}}\n')
        out.append(f'<p class="sub-line">{PHASES[n]["goal"]}</p>')
        out.append('<div class="cards">\n' + "\n".join(card_fn(m) for m in ms) + "\n</div>")
    return "\n\n".join(out)


def total_hours():
    mh = sum(m["hours"] for m in C["modules"])
    ph = sum(p["hours"] for p in C["projects"])
    return mh, ph


def write(rel, text):
    f = ROOT / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


def home():
    mh, ph = total_hours()
    n_av = sum(has_course(m["id"]) for m in C["modules"])
    n_pr = sum(has_project(p["id"]) for p in C["projects"])
    masters_ready = has_page("masters")
    complete = n_av == len(C["modules"]) and n_pr == len(C["projects"])
    rest_note = "." if complete else " ; les autres apparaissent en gris, avec leur plan, pour que vous voyiez où va le parcours."
    txt = f"""---
title: "Mastering Compute Infrastructure"
subtitle: "Un parcours pour devenir compute infrastructure engineer : cours, labs vérifiés, projets de portfolio et enquête sur les masters HPC"
description: "Parcours d'apprentissage en français pour opérer des clusters GPU, ordonnancer, entraîner à grande échelle et piloter la capacité multi-fournisseurs."
numbered: true
toc-inline: false
---

<p class="lead">Un <em>compute infrastructure engineer</em> fait tourner les machines sur lesquelles on entraîne les modèles d'IA : clusters GPU, ordonnanceurs, réseaux, stockage, fiabilité, coût. Ce site rassemble de quoi apprendre ce métier de manière structurée : {len(C['modules'])} modules en {len(PHASES)} phases, {len(C['projects'])} projets de portfolio, des labs exécutables et une enquête sourcée sur les masters HPC en France, aux États-Unis, en Chine et dans le monde.</p>

<div class="hero-actions">
<a class="cta" href="#cours">Voir les cours</a>
<a class="cta cta-ghost" href="path/index.html">Feuille de route</a>
<a class="cta cta-ghost" href="syllabus/index.html">Plans détaillés</a>
<a class="cta cta-ghost" href="profile/index.html">Point de départ</a>
{'<a class="cta cta-ghost" href="market/index.html">Analyse du marché</a>' if has_page("market") else ''}
{'<a class="cta cta-ghost" href="masters/index.html">Enquête sur les masters HPC</a>' if masters_ready else ''}
</div>

## État du chantier {{#etat}}

Ce site est construit module par module, et chaque page est vérifiée avant d'être publiée. **{n_av} module(s) sur {len(C['modules'])} et {n_pr} projet(s) sur {len(C['projects'])} sont publiés**{rest_note}

-   **Documenté** : chaque chiffre sur un système réel renvoie à sa source ; sinon il est présenté comme un ordre de grandeur.
-   **Vérifié** : les calculs des exemples et des corrigés sont refaits en Python, les labs « bac à sable » s'exécutent sans GPU (`verify.sh`), les pages passent des contrôles mécaniques (`tools/check_gates.py`).
-   **Honnête** : un lab non exécuté porte le badge « non vérifié » ; une valeur incertaine est signalée « à vérifier ».

## Le parcours en un coup d'œil {{#parcours}}

Volume total : **{hfmt(mh)} h de modules et {hfmt(ph)} h de projets**, soit environ {round((mh + ph) / HPW)} semaines à {HPW} h par semaine. Le détail, les jalons et les parcours courts sont dans la [feuille de route](path/index.html).

| Phase | Modules | Volume |
|---|---|---|
""" + "\n".join(
        f"| {n} — {PHASES[n]['title']} | {', '.join(str(m['number']) for m in C['modules'] if m['phase']==n)} | {hfmt(sum(m['hours'] for m in C['modules'] if m['phase']==n))} h |"
        for n in sorted(PHASES)) + f"""

## Cours {{#cours}}

Chaque cours est une longue page unique : fiche, plan de séances, chapitres avec exemples chiffrés, labs, exercices corrigés, checkpoint de sortie et références. Le badge **Cœur** signale un module indispensable à tous ; **Fondation** un module de base que vous pouvez survoler si vous le pratiquez déjà. La section « Comment travailler ce module » de chaque cours donne la priorité selon votre profil d'entrée.

{phase_blocks(card_course)}

## Projets de portfolio {{#projets}}

Chaque projet mobilise plusieurs modules et produit un dépôt que vous pouvez publier et présenter en entretien. Ils sont réalisables sans GPU dans leur version de base.

<div class="cards">
""" + "\n".join(card_project(p) for p in C["projects"]) + f"""
</div>

## Ce que demande le marché {{#marche}}

{"Une analyse sourcée d'offres d'emploi d'infrastructure de calcul publiées aux États-Unis, en Europe et en Chine, dans les laboratoires d'IA, les grands groupes, les clouds GPU et les centres HPC : les compétences demandées, ce qui change d'une région à l'autre, et ce que le parcours couvre. <a href=\"market/index.html\">Lire l'analyse</a>." if has_page("market") else "L'analyse des offres d'emploi est en cours de rédaction."}

## Enquête sur les masters HPC {{#masters}}

{"Une analyse sourcée des masters orientés calcul haute performance en France, aux États-Unis, en Chine et dans le reste du monde, croisée avec les offres d'emploi de compute infrastructure : ce que les masters enseignent, ce qu'ils n'enseignent presque pas, et ce que ce parcours ajoute. <a href=\"masters/index.html\">Lire l'enquête</a>." if masters_ready else "L'enquête sur les masters HPC (France, États-Unis, Chine, monde) est en cours de rédaction."}

## Comment utiliser ce site {{#usage}}

1.  Lisez le [point de départ](profile/index.html) : il décrit le métier et cinq profils d'entrée, et propose une grille d'autodiagnostic pour choisir quels modules travailler à fond et lesquels survoler.
2.  Préparez votre [environnement de travail](lab-setup/index.html) si la page est publiée : un portable CPU suffit pour la base.
3.  Suivez les phases dans l'ordre. Dans chaque module, faites les trois questions de positionnement avant de lire.
4.  Faites les labs et lancez leur `verify.sh` : un lab compte quand sa vérification passe.
5.  Terminez chaque phase par son jalon (voir la feuille de route), puis par le projet associé.

## Sources et portée {{#sources}}

Ce site est un ensemble de notes d'étude indépendantes, rédigées à partir de documentations officielles, d'articles publiés et de fiches de formation publiques. Il n'est affilié à aucun établissement, éditeur ou employeur et ne remplace ni un diplôme ni une certification. Les contrats de contenu et les contrôles qui encadrent chaque page sont dans le dossier `specs/` et `tools/` du dépôt.
"""
    write("index.md", txt)


def profile_paths():
    rows = ["| Profil d'entrée | À fond (A) | Survol guidé (C) | Volume indicatif |", "|---|---|---|---|"]
    ph = sum(p["hours"] for p in C["projects"])
    for pr in C["profiles"]:
        a = [m for m in C["modules"] if m["study"][pr["id"]] == "A"]
        c = [m for m in C["modules"] if m["study"][pr["id"]] == "C"]
        h = sum(m["hours"] * (0.25 if m["study"][pr["id"]] == "C" else 1) for m in C["modules"]) + ph
        rows.append(f"| {pr['name']} | {', '.join(str(m['number']) for m in a) or '—'} | {', '.join(str(m['number']) for m in c) or '—'} | {round(h / 10) * 10} h |")
    return "\n".join(rows)


def priorities():
    head = "| Module | " + " | ".join(p["name"] for p in C["profiles"]) + " |"
    rows = [head, "|---|" + "---|" * len(C["profiles"])]
    for m in C["modules"]:
        rows.append(f"| [{m['number']}. {m['title']}](../courses/{m['id']}/index.html) | " + " | ".join(m["study"][p["id"]] for p in C["profiles"]) + " |")
    return "\n".join(rows)


def profile_page():
    f = ROOT / "profile" / "index.md"
    if not f.exists():
        return
    t = f.read_text(encoding="utf-8")
    beg, end = "<!-- gen:priorities -->", "<!-- /gen:priorities -->"
    if beg in t:
        t = t[:t.index(beg)] + beg + "\n" + priorities() + "\n" + end + t[t.index(end) + len(end):]
        f.write_text(t, encoding="utf-8")


def roadmap():
    mh, ph = total_hours()
    rows, tot = [], 0
    jal = {0: "Rapport de mesure reproductible (roofline, α-β) et calculateur de MFU testé.",
           1: "Étude de scalabilité d'un solveur MPI et noyaux GPU validés par leurs tests.",
           2: "Projet 1, exigences R1 à R4 : la comptabilité Slurm décrite en code, appliquée par différence, convergente. R5 à R7 (exportateur, alertes, vérification en direct) se terminent en phase 4, après le module 14.",
           3: "Projets 2 et 3 : étude de passage à l'échelle et entraîneur tolérant aux pannes.",
           4: "Projets 4 et 5 : placement multi-fournisseurs et observabilité GPU.",
           5: "Projet 6 : RFC de plateforme de 8 à 256 GPU et soutenance de 20 minutes."}
    proj_by_phase = PROJ_BY_PHASE
    for n in sorted(PHASES):
        ms = [m for m in C["modules"] if m["phase"] == n]
        hm = sum(m["hours"] for m in ms)
        hp = sum(PROJ[i]["hours"] for i in proj_by_phase[n])
        tot += hm + hp
        rows.append(f"| {n} — {PHASES[n]['title']} | {', '.join(m['id'] for m in ms)} | {hfmt(hm)} h | {', '.join(str(PROJ[i]['number']) for i in proj_by_phase[n]) or '—'} ({hfmt(hp)} h) | {round((hm + hp) / HPW)} sem. | {jal[n]} |")
    short = ["perf-models", "slurm", "distributed-training", "fault-tolerance", "multi-cloud"]
    short_p = ["scaling-study", "resilient-trainer"]
    sh = sum(MODS[i]["hours"] for i in short) + sum(PROJ[i]["hours"] for i in short_p)
    txt = f"""---
title: "Feuille de route"
subtitle: "{len(PHASES)} phases, {hfmt(tot)} h au total, jalons et parcours courts"
description: "Séquence des phases, volumes horaires, jalons de validation et parcours accélérés."
numbered: true
---

## Comment lire cette feuille de route {{#lecture}}

Le volume total est de **{hfmt(mh)} h de modules et {hfmt(ph)} h de projets**, soit **{hfmt(tot)} h**. À titre de repère, {HPW} h par semaine donnent environ {round(tot / HPW)} semaines (les numéros de semaine des pages de module supposent ce rythme) ; 25 h par semaine, environ {round(tot / 25)} semaines ; un temps plein de 35 h, environ {round(tot / 35)} semaines. Ce sont des ordres de grandeur : un module que vous maîtrisez déjà se parcourt en deux ou trois heures grâce à ses questions de positionnement.

Un rythme hebdomadaire type de {HPW} h : deux séances de lecture de 3 h, une séance de lab de 3 h, et 3 h d'exercices et de relecture. Tenez un journal d'apprentissage dans un dépôt public : c'est aussi une pièce de portfolio.

## Les six phases {{#phases}}

| Phase | Modules | Volume | Projets | Durée à {HPW} h/sem. | Jalon de validation |
|---|---|---|---|---|---|
""" + "\n".join(rows) + f"""

Chaque phase se termine par son jalon : tant que le livrable n'existe pas et que ses vérifications ne passent pas, la phase n'est pas terminée, quel que soit le temps passé.

## Pourquoi cet ordre {{#ordre}}

-   **Phase 0 d'abord**, parce que tout le reste consiste à poser un modèle de performance, à le mesurer et à expliquer l'écart.
-   **Calcul parallèle et GPU avant l'ordonnancement**, parce qu'on ne règle pas un ordonnanceur pour des charges qu'on ne sait pas décrire.
-   **L'exploitation du cluster avant l'entraînement distribué**, parce que les pannes et les goulots d'un entraînement se situent presque toujours dans le réseau, le stockage ou l'ordonnanceur.
-   **Le multi-fournisseurs en phase 4**, parce qu'il suppose de savoir reprendre un job après une panne (phase 3).
-   **Le leadership en dernier**, parce qu'on dirige mieux ce qu'on a opéré soi-même.

## Parcours court : l'essentiel en {hfmt(sh)} h {{#court}}

Si vous n'avez pas le temps de tout suivre, ce sous-ensemble couvre le noyau technique de l'entraînement à grande échelle : {', '.join(f"{MODS[i]['title']}" for i in short)}, plus les projets {', '.join(PROJ[i]['title'].split(' — ')[0] for i in short_p)}. Il ne remplace pas le parcours complet : l'exploitation du réseau, du stockage, de Kubernetes et de la capacité manque.

Ces modules supposent des bases à survoler : module 1, chapitres 1 et 5, pour Slurm ; module 4, chapitres 1, 2 et 7, et module 7, chapitres 1 et 7, pour l'entraînement distribué ; module 8, chapitre 6 (E/S de checkpoint), pour les pannes et le projet 3 ; module 12, chapitre 3 (Kueue), pour le multi-fournisseurs.

## Parcours selon votre profil d'entrée {{#profils}}

Le [point de départ](../profile/index.html) décrit cinq profils d'entrée et leurs priorités module par module. Le tableau en déduit un volume d'étude indicatif : les modules à fond et normaux comptent pour leur volume, les modules survolés pour un quart, les projets pour leur volume. C'est un ordre de grandeur, à corriger avec les questions de positionnement.

{profile_paths()}

## Suivre sa progression {{#suivi}}

-   Après chaque module : cochez son checkpoint de sortie, produit pour chaque capacité la preuve demandée.
-   Après chaque phase : publiez le livrable du jalon dans un dépôt, avec un fichier `README.md` et une décision d'architecture d'une page.
-   Tous les deux mois : relisez l'enquête sur les masters et les offres d'emploi, et notez ce qui a changé.
"""
    write("path/index.md", txt)


def syllabus():
    out = ["""---
title: "Plans détaillés des modules"
subtitle: "Acquis visés, chapitres, labs et sources à lire pour chacun des modules du parcours"
description: "Plan de chacun des modules : acquis, chapitres, labs et sources."
---

## Comment lire cette page {#lecture}

Cette page résume chaque module du parcours : acquis, chapitres, labs et sources. La page complète de chaque module (fiche, plan de séances, chapitres, labs, exercices corrigés) est liée depuis son résumé. Le statut de vérification d'un module est celui de son badge : « labs vérifiés » quand tous ses labs ont tourné, « non vérifié » quand une partie demande un GPU, un cluster ou un cloud.

Les rubriques « Sources à lire » donnent les références sur lesquelles s'appuie chaque module ; les chiffres qu'elles mentionnent sont à relire à la source, comme dans les pages des modules.
"""]
    for ph in sorted(PHASES):
        out.append(f"\n## Phase {ph} — {PHASES[ph]['title']} {{#phase{ph}}}\n")
        for m in [m for m in C["modules"] if m["phase"] == ph]:
            done = has_course(m["id"])
            tag = verification_label(m["id"]) if done else "plan"
            title = f"[{m['title']}](../courses/{m['id']}/index.html)" if done else m["title"]   # the syllabus lives in syllabus/
            out.append(f"### Module {m['number']:02d} — {m['title']} ({tag}, {hfmt(m['hours'])} h) {{#{m['id']}}}\n")
            out.append(f"{m['summary']}\n")
            if m["prerequisites"]:
                out.append("**Prérequis :** " + ", ".join(f"module {MODS[i]['number']} ({MODS[i]['title']})" for i in m["prerequisites"]) + ".\n")
            if done:
                out.append(f"**Cours complet :** {title}.\n")
            out.append("**Ce que vous saurez vérifier :**\n")
            out += [f"-   {o}" for o in m["outcomes"]]
            out.append("\n**Chapitres :**\n")
            out += [f"{i}.  {c}" for i, c in enumerate(m["chapters"], 1)]
            out.append("\n**Labs :**\n")
            out += [f"-   **{l['title']}** ({'bac à sable, sans GPU' if l['kind'] == 'sandbox' else 'cluster' if l['kind'] == 'cluster' else 'GPU requis'}) : {l['idea']}" for l in m["labs"]]
            out.append("\n**Sources à lire :**\n")
            out += [f"-   {f}" for f in m["facts"]]
            feeds = [PROJ[i] for i in m.get("feeds", []) if i in PROJ]
            if feeds:
                out.append("\n**Projets qui s'appuient sur ce module :** " + ", ".join(f"Projet {p['number']}" for p in feeds) + ".\n")
    out.append("\n## Projets {#projets}\n")
    for p in C["projects"]:
        out.append(f"### {p['title']} ({hfmt(p['hours'])} h) {{#{p['id']}}}\n")
        out.append(f"{p['summary']}\n")
        out.append("**Modules mobilisés :** " + ", ".join(f"{MODS[i]['number']}" for i in p["modules"]) + ".\n")
        out.append(f"**Plan :** {p['idea']}\n")
    write("syllabus/index.md", "\n".join(out) + "\n")


def nav():
    seq = []

    def add(rel, label):
        if (ROOT / rel / "index.md").exists():
            seq.append({"href": f"{rel}/index.html", "label": label})
    add("profile", "Point de départ")
    add("market", "Ce que demande le marché")
    for rel, label in (("masters", "Enquête sur les masters HPC"), ("masters/france", "Masters en France"),
                       ("masters/usa", "Masters aux États-Unis"), ("masters/china", "Masters en Chine"),
                       ("masters/world", "Masters dans le monde")):
        add(rel, label)
    add("path", "Feuille de route")
    add("syllabus", "Plans détaillés des modules")
    add("lab-setup", "Environnement de travail")
    for m in sorted(C["modules"], key=lambda m: m["number"]):
        add(f"courses/{m['id']}", f"Module {m['number']:02d} — {m['title']}")
    for p in sorted(C["projects"], key=lambda p: p["number"]):
        add(f"projects/{p['id']}", p["title"])
    add("resources", "Ressources")
    write("data/nav.json", json.dumps({"sequence": seq}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    phase_weeks()
    nav()
    home()
    roadmap()
    syllabus()
    profile_page()
    nav()
    print("generated index.md, path/index.md, data/nav.json")
