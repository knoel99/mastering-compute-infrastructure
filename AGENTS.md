# AGENTS.md — gates « spec → implémentation → preuve » pour mastering-compute-infrastructure

Ce dépôt est un **site de cours en HTML** (GitHub Pages), pas une application. Il reprend la discipline légère de `polytechnique-llga` : un contrat avant un gros ajout, des preuves mécaniques avant « terminé ».

## Principes

1. **Contrat avant réécriture** — un nouveau module ou projet suit `specs/module-contract.md` / `specs/project-contract.md`.
2. **Preuves avant « terminé »** — `python3 tools/check_gates.py` passe, les pages sont rendues (`python3 tools/build.py --check`), les labs « sandbox » passent (`--labs`).
3. **Aucun fait sans source** — tout chiffre sur un système réel est sourcé ou présenté comme ordre de grandeur. Les données de recherche suivent `specs/research-contract.md` (`python3 tools/validate_research.py`).
4. **Honnêteté des badges** — « labs vérifiés » seulement si les `verify.sh` ont été exécutés ; sinon « non vérifié ».
5. **Français pour la prose, anglais pour le code** — voir `specs/module-contract.md` §1.
6. **Lisible au vidéoprojecteur** — `assets/paper.css` est la référence visuelle (contraste ≥ 7:1 en clair et en sombre) ; `tools/check_airiness.py` impose la prose aérée.
7. **Confidentialité** — pas de noms de clients de l'auteur ; pas de mention de l'employeur visé ; pas de secrets.

## Gates obligatoires (Definition of Done)

- [ ] **Contrat** : le module/projet respecte son contrat (en-tête YAML, ancres, plan de séances dont la somme vaut le volume, ≥ 8 exercices corrigés, ≥ 2 labs).
- [ ] **Rendu** : `index.html` rendu depuis `index.md` (`python3 tools/build.py`), `--check` propre.
- [ ] **Accueil** : la page est liée depuis `index.md` ; `data/nav.json` à jour.
- [ ] **Prose aérée** : `python3 tools/check_airiness.py` propre.
- [ ] **Labs** : `python3 tools/check_gates.py --labs` propre pour les labs sandbox ; les autres sont linté et étiquetés.
- [ ] **Sources** : liens vérifiés (`python3 tools/check_links.py`), ressources présentes dans `data/resources/learning.json` ou datées.
- [ ] **Visuel** : une page testée en clair, sombre et mobile (pas de défilement horizontal).

## Flux de travail

| Phase | Sortie |
|---|---|
| **Spec** | Contrat dans `specs/` (objectifs, plan, preuves). |
| **Plan** | Liste des fichiers touchés (page, labs, nav, accueil). |
| **Implémenter** | Markdown + code des labs. |
| **Prouver** | `tools/check_gates.py`, `tools/build.py --check`, `--labs`. |

## Fichiers clés

- `specs/README.md` — index des contrats
- `specs/module-contract.md`, `specs/project-contract.md`, `specs/research-contract.md`, `specs/site-architecture.md`
- `tools/build.py`, `tools/check_gates.py`, `tools/check_airiness.py`, `tools/validate_research.py`
- `data/` — données de recherche et `nav.json`
