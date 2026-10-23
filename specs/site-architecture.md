# Architecture du site

Site statique servi par **GitHub Pages directement depuis la branche** (`.nojekyll`, pas de CI) : les pages HTML rendues sont **commitées** à côté de leurs sources Markdown, comme `polytechnique-llga` le fait avec Quarto. Ici le moteur est **Pandoc ≥ 3.1** (disponible partout, pas de dépendance Python lourde).

## Arborescence

```
index.md / index.html          accueil : parcours, arbre des modules, projets, masters, ressources
assets/paper.css, theme.js     style (dérivé de LLGA : contraste ≥ 7:1, clair/sombre, mobile, sommaire latéral)
profile/                       cible du parcours et écart avec CAREER.md (lecteur de référence)
path/                          feuille de route : phases, semaines, jalons
masters/                       enquête sur les masters HPC (synthèse, France, USA, Chine, monde, ressources)
courses/<id>/index.md|html     un module = une longue page (specs/module-contract.md)
projects/<id>/index.md|html    un projet de portfolio (specs/project-contract.md)
resources/                     lectures, cours ouverts, certifications, communautés (data/resources/learning.json)
lab-setup/                     environnement de travail : local, cloud, budget
labs/<module>/<lab>/           code des labs (verify.sh pour les labs « sandbox »)
labs/projects/<id>/            code de départ et référence des projets
data/                          données de recherche (masters, offres, ressources) + nav.json
specs/  tools/                 contrats, outils rejouables
```

## Navigation

`data/nav.json` : `sequence` ordonne les pages (précédent/suivant). Le sommaire latéral est construit par `theme.js` à partir des `h2/h3` ayant un `id`.

## Rendu

`python3 tools/build.py` rend chaque `index.md` en `index.html` (gabarit `tools/template.html`, filtre `tools/filters.lua` : `::: sol` devient un `<details>` repliable, tableaux défilants). KaTeX 0.19.0 est épinglé avec empreintes d'intégrité (mêmes que `polytechnique-llga`). `--check` échoue si une page commitée diffère du rendu.

## Mise en ligne

Réglages du dépôt → Pages → *Deploy from a branch* → `main` / `/ (root)`. URL : `https://knoel99.github.io/mastering-compute-infrastructure/`. Le dossier `data/`, `specs/` et `tools/` restent publics et servent de preuves.

## Preuve (Definition of Done d'une page)

`python3 tools/check_gates.py` (contrats), `python3 tools/check_airiness.py`, `python3 tools/build.py --check`, `python3 tools/check_gates.py --labs` (exécute les `verify.sh`), `python3 tools/validate_research.py` (données).
