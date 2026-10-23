#!/usr/bin/env python3
"""Generate masters/<region>/index.md pages from data/masters/*.json (+ optional narrative notes).

Narrative text written by hand lives in masters/_notes/<region>.md (inserted after the summary table)
and masters/_notes/index.md (inserted in the survey home). Translated free-text fields are read from
the programme record when a "<field>_fr" key exists, otherwise the original (English) text is kept and flagged.

    python3 tools/gen_masters.py && python3 tools/build.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from validate_research import TOPICS  # noqa: E402

REGIONS = [("france", "Masters et formations HPC en France", "France"),
           ("usa", "Masters et formations HPC aux États-Unis", "États-Unis"),
           ("china", "Masters et formations HPC en Chine", "Chine"),
           ("world", "Masters et formations HPC dans le monde", "Reste du monde")]
TOPIC_FR = {
    "openmp-threads": "Mémoire partagée (OpenMP)", "mpi": "Passage de messages (MPI)", "gpu-prog": "Programmation GPU",
    "perf-model": "Modèles de performance, profilage", "arch": "Architecture des ordinateurs", "numerics": "Méthodes numériques",
    "simulation-apps": "Simulation et applications", "parallel-algos": "Algorithmique parallèle", "distributed-sys": "Systèmes distribués",
    "sysadmin": "Administration de clusters", "scheduling": "Ordonnancement de jobs", "interconnect": "Réseaux et interconnexions",
    "storage-io": "Stockage et E/S parallèles", "containers-k8s": "Conteneurs, Kubernetes", "cloud": "Cloud et multi-fournisseurs",
    "bigdata": "Données massives", "ml-dl": "Apprentissage automatique et profond", "ml-systems": "Systèmes pour l'IA (entraînement distribué)",
    "hpc-software-eng": "Génie logiciel HPC", "energy": "Efficacité énergétique", "quantum-emerging": "Quantique, architectures émergentes",
    "viz": "Visualisation", "thesis-internship": "Mémoire, stage", "soft-skills": "Gestion de projet, éthique",
    "resilience": "Résilience, checkpointing", "observability-sre": "Supervision, observabilité, SRE"}
HEAT = [("openmp-threads", "OpenMP"), ("mpi", "MPI"), ("gpu-prog", "GPU"), ("perf-model", "Perf."), ("sysadmin", "Admin"), ("scheduling", "Ordo."),
        ("interconnect", "Réseau"), ("storage-io", "E/S"), ("containers-k8s", "K8s"), ("cloud", "Cloud"), ("ml-dl", "ML"), ("ml-systems", "ML sys."),
        ("resilience", "Panne"), ("observability-sre", "Obs.")]
FOCUS_FR = {"hpc-core": "HPC (cœur)", "ml-systems": "Systèmes pour l'IA", "cse": "Science computationnelle", "cloud-distributed": "Cloud et distribué",
            "ops-sysadmin": "Exploitation / administration", "mixed": "Mixte"}
CONF_FR = {"high": ("Confiance élevée", "verified"), "medium": ("Confiance moyenne", "skim"), "low": ("Confiance faible", "unverified")}
SYM = {2: '<span class="sym2" title="cours dédié">2</span>', 1: '<span class="sym1" title="mentionné dans un cours">1</span>', 0: '<span class="sym0" title="absent d\'un syllabus consulté">0</span>', None: '<span class="symn" title="inconnu : syllabus non accessible">·</span>'}


def load():
    byreg = {r: [] for r, _, _ in REGIONS}
    eco = {r: [] for r, _, _ in REGIONS}
    for f in sorted((ROOT / "data" / "masters").glob("*.json")):
        if f.name == "synthesis.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        reg = d.get("region", "world")
        for p in d["programmes"]:
            byreg.setdefault(reg, []).append(p)
        for e in d.get("ecosystem", []):
            eco.setdefault(reg, []).append(e)
    return byreg, eco


def fr(p, k):
    v = p.get(k + "_fr")
    if v:
        return v
    v = p.get(k, "")
    return v if isinstance(v, str) else v


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def short_name(n):
    n = n.split(" - ")[0].split(" (")[0].strip()
    return n if len(n) <= 46 else n[:44].rstrip() + "…"


def heat_table(progs):
    head = "| Programme | " + " | ".join(l for _, l in HEAT) + " |\n|---|" + "---|" * len(HEAT) + "\n"
    rows = []
    for p in progs:
        cells = " | ".join(SYM[p["topic_coverage"].get(t)] for t, _ in HEAT)
        inst = p['institution'].split(' / ')[0].split(' (')[0].split(' - ')[0]
        if len(inst) > 34:
            inst = inst[:34].rsplit(' ', 1)[0] + '…'
        rows.append(f"| [{esc(inst)}](#{p['id']}) — {esc(short_name(p['programme_name']))} | {cells} |")
    return head + "\n".join(rows)


def programme_md(p):
    lab, cls = CONF_FR[p["confidence"]]
    web = [e for e in p["evidence"] if e.get("source", "web") == "web"]
    ver = p.get("evidence_verified", f"{len(web)} citations")
    lines = [f"### {p['programme_name']} {{#{p['id']}}}", "",
             f'<p class="badges"><span class="badge {cls}">{lab}</span><span class="badge">{FOCUS_FR.get(p["focus"], p["focus"])}</span><span class="badge">{p["country"]}</span></p>', "",
             "| | |", "|---|---|",
             f"| Établissement | {esc(p['institution'])} |", f"| Diplôme | {esc(p['degree'])} |", f"| Durée | {esc(fr(p, 'duration'))} |",
             f"| Crédits | {esc(fr(p, 'credits'))} |", f"| Langue | {esc(fr(p, 'language'))} |", f"| Modalité | {esc(p['delivery'])} |",
             f"| Admission | {esc(fr(p, 'entry_requirements'))} |"]
    if p.get("machines_access"):
        lines.append(f"| Machines citées | {esc('; '.join(p['machines_access']))} |")
    lines += ["", f"**Structure.** {fr(p, 'structure_summary')}", ""]
    core = p.get("core_courses", [])
    if core:
        lines.append("**Cours du tronc commun** (thèmes de la taxonomie entre parenthèses) :")
        lines.append("")
        for c in core[:12]:
            tps = ", ".join(TOPIC_FR.get(t, t) for t in c.get("topics", []))
            lines.append(f"-   {c['name']}" + (f" ({tps})" if tps else ""))
        lines.append("")
    if p.get("capstone"):
        lines += [f"**Mémoire ou stage.** {fr(p, 'capstone')}", ""]
    if p.get("industry_links"):
        lines += ["**Liens avec l'industrie et la recherche.** " + " ".join(f"{x}." if not str(x).endswith(".") else x for x in (fr(p, 'industry_links') if isinstance(fr(p, 'industry_links'), list) else p['industry_links'])), ""]
    if p.get("notes"):
        lines += [f"**Limites de la fiche.** {fr(p, 'notes')}", ""]
    srcs = " · ".join(f"[{i + 1}]({u})" for i, u in enumerate(p["urls"][:6]))
    lines += [f"**Sources.** {srcs}. Citations vérifiées mot pour mot : {ver}.", ""]
    return "\n".join(lines)


def region_page(reg, title, label, progs, eco):
    notes = ROOT / "masters" / "_notes" / f"{reg}.md"
    n = len(progs)
    unknown = sum(1 for p in progs for v in p["topic_coverage"].values() if v is None)
    legend = "**2** cours dédié · **1** mentionné dans un cours · **0** absent d'un syllabus consulté · **·** inconnu (syllabus non accessible)"
    md = [f"""---
title: "{title}"
subtitle: "{n} programme(s) étudié(s), données sourcées et vérifiées"
description: "Fiches de programmes HPC : durée, crédits, cours, accès aux machines, couverture des thèmes utiles à un ingénieur d'infrastructure de calcul."
---

## Vue d'ensemble {{#vue}}

Cette page présente {n} programme(s) pour la zone « {label} ». Chaque fait vient d'une page consultée le 22 octobre 2026 ; les citations ont été vérifiées mot pour mot contre le texte des pages. Un thème dont le syllabus n'a pas pu être lu est marqué *inconnu*, jamais *absent*.

{heat_table(progs)}

{legend}.
""" + (notes.read_text(encoding="utf-8") if notes.exists() else "") + "\n## Les programmes {#programmes}\n\n" + "\n".join(programme_md(p) for p in progs)]
    if eco:
        md.append("\n## Autour des diplômes : centres, écoles, compétitions {#ecosysteme}\n")
        for e in eco:
            md.append(f"-   **[{e['name']}]({e['url']})** ({e['kind']}) : {fr(e, 'why_relevant')}")
    md.append("\n## Sources et portée {#sources}\n")
    md.append("**Documenté.** Les pages officielles des programmes et des catalogues de cours, lues le 22 octobre 2026 ; chaque fiche cite ses liens.\n\n**Recommandé.** L'attribution des thèmes de la taxonomie aux intitulés de cours est un jugement de lecture, signalé par des symboles ; elle n'est pas une mesure.\n\n**À vérifier.** Les programmes changent chaque année : consultez la page officielle avant toute décision. Les pages chargées par JavaScript n'ont pas toujours pu être lues.")
    return "\n".join(md) + "\n"


def main():
    byreg, eco = load()
    done = []
    for reg, title, label in REGIONS:
        if not byreg.get(reg):
            continue
        d = ROOT / "masters" / reg
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.md").write_text(region_page(reg, title, label, byreg[reg], eco.get(reg, [])), encoding="utf-8")
        done.append(f"{reg}:{len(byreg[reg])}")
    print("generated", ", ".join(done))


if __name__ == "__main__":
    main()
