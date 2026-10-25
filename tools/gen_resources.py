#!/usr/bin/env python3
"""Generate resources/index.md from data/resources/learning.json (verified references).

Only items whose evidence quote was verified verbatim (evidence.verified true, written by
tools/verify_quotes.py --write) are listed as verified; the others are listed in a separate
"à vérifier" block so that the page never overstates what was checked.
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
f = ROOT / "data" / "resources" / "learning.json"
KIND = {"book": "Livres", "course": "Cours ouverts", "paper": "Articles et rapports à lire", "certification": "Certifications",
        "docs": "Documentations de référence", "community": "Communautés et conférences", "tool": "Outils"}
ORDER = ["paper", "book", "course", "docs", "certification", "community", "tool"]
LEVEL = {"intro": "introduction", "intermediate": "intermédiaire", "advanced": "avancé"}
COST = {"free": "gratuit", "paid": "payant", "unknown": "coût non précisé"}


def line(it):
    bits = [f"**[{it['title']}]({it['url']})**"]
    meta = [x for x in (it.get("by"), str(it.get("year") or "")) if x]
    if meta:
        bits.append(", ".join(meta))
    tags = [LEVEL.get(it.get("level"), ""), COST.get(it.get("cost"), "")]
    tags = [t for t in tags if t]
    s = " · ".join(bits)
    if tags:
        s += f" ({', '.join(tags)})"
    return f"-   {s}. {it.get('why', '')}"


def main():
    if not f.exists():
        print("no data/resources/learning.json yet")
        return
    d = json.loads(f.read_text(encoding="utf-8"))
    items = d.get("items", [])
    ok = [i for i in items if (i.get("evidence") or {}).get("verified")]
    ko = [i for i in items if i not in ok]
    by = defaultdict(list)
    for it in ok:
        by[it["kind"]].append(it)
    out = [f"""---
title: "Ressources"
subtitle: "{len(ok)} ressources vérifiées : lectures, cours ouverts, certifications, documentations, communautés"
description: "Références à lire pour devenir compute infrastructure engineer, chacune vérifiée à sa source le 22 octobre 2026."
numbered: true
---

## Comment utiliser cette page {{#usage}}

Chaque ressource listée ici a été ouverte à sa source : le titre, les auteurs ou le fournisseur et l'adresse correspondent à la page cible, et une citation de cette page a été vérifiée mot pour mot. Les modules renvoient vers ces ressources avec l'usage précis (« lire la section 3 pour… »).

Les certifications évoluent vite : relisez la page officielle de l'examen avant de vous inscrire. Cette page ne donne ni prix ni format qui ne figurent pas sur la page officielle.
"""]
    for k in ORDER:
        if by.get(k):
            out.append(f"\n## {KIND[k]} {{#{k}}}\n")
            out += [line(i) for i in sorted(by[k], key=lambda x: (x.get("level", ""), x["title"]))]
    if ko:
        out.append("\n## Pistes non vérifiées {#a-verifier}\n\nCes ressources ont été repérées mais leur page n'a pas pu être relue avec succès : traitez-les comme des pistes à confirmer.\n")
        out += [line(i) for i in ko]
    out.append("\n## Sources et portée {#sources}\n\n**Documenté.** Ressources relues à leur source le 22 octobre 2026 (outil `tools/verify_quotes.py`).\n\n**Recommandé.** Le tri par type et le commentaire d'usage sont des choix de ce parcours.\n\n**À vérifier.** Les offres de formation et de certification changent : confirmez sur la page officielle.\n")
    (ROOT / "resources").mkdir(exist_ok=True)
    (ROOT / "resources" / "index.md").write_text("\n".join(out), encoding="utf-8")
    print(f"resources/index.md: {len(ok)} verified, {len(ko)} to check")


if __name__ == "__main__":
    main()
