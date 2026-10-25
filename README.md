# mastering-compute-infrastructure

Parcours d'apprentissage pour devenir **compute infrastructure engineer** : opérer des clusters GPU, ordonnancer (Slurm, Kubernetes), entraîner à grande échelle, tenir les pannes, piloter la capacité multi-fournisseurs.

**Site (français)** : <https://knoel99.github.io/mastering-compute-infrastructure/>

Le contenu est un ensemble de pages HTML statiques (style dérivé de [`polytechnique-llga`](https://github.com/knoel99/polytechnique-llga)) :

- **Cours** : des modules en pages longues (fiche, plan de séances, chapitres avec exemples chiffrés, labs exécutables, exercices corrigés, bilan de sortie, références).
- **Projets de portfolio** : des livrables publiables, réalisables sans GPU dans leur version de base.
- **Enquête sur les masters HPC** (France, États-Unis, Chine, monde) croisée avec des offres d'emploi, avec données sourcées dans `data/`.
- **Point de départ** : le métier, cinq profils d'entrée (plateforme et SRE, HPC, ML, logiciel, étudiant), leurs priorités module par module et une grille d'autodiagnostic.
- **Ce que demande le marché** : une analyse sourcée de 96 offres d'emploi aux États-Unis, en Europe et en Chine (laboratoires d'IA, grands groupes, clouds GPU, constructeurs, centres HPC), et la couverture de chaque compétence par le parcours.
- **Cohérence du parcours** : la revue croisée des seize modules et des six projets, ses corrections et les conventions de notation communes.

## État d'avancement

| Élément | Statut |
|---|---|
| Modules rédigés (page, labs, exercices corrigés) | 16 sur 16, voir la feuille de route : la plupart ont un lab exécuté sans GPU ; les modules 6, 7, 12 et 13 ont une partie GPU ou cloud seulement vérifiée statiquement, et le disent dans leur badge `unverified` |
| Projets de portfolio | 6 sur 6 : entraînement résilient, étude de passage à l'échelle, observabilité GPU, ordonnanceur multi-fournisseurs, RFC de capacité, Slurm de laboratoire |
| Enquête sur les masters et offres d'emploi | faite, avec citations vérifiées mécaniquement (`tools/verify_quotes.py`) ; 96 offres publiques, 937 citations retrouvées mot pour mot |
| Revue de cohérence | faite le 25 octobre 2026 : 126 constats croisés (121 retenus et corrigés), 300 défauts locaux vérifiés ; voir la page « Cohérence du parcours » |

**Ce qui est vérifié.** Les labs « bac à sable » ont un `verify.sh` exécuté sur une machine virtuelle Linux sans GPU ; les projets ont un gabarit qui échoue et une référence qui réussit ; le projet 1 a aussi été vérifié sur un vrai Slurm 23.11.4. **Ce qui ne l'est pas** : aucun GPU, aucun cluster multi-nœuds, aucun cloud n'a été utilisé. Les parties qui l'exigent ne sont que vérifiées statiquement (lint, validation de schéma) et le disent dans leur badge `unverified` et dans les sections « À vérifier » de chaque page. Les données de prix, de pannes et de demande des exemples sont fictives et étiquetées comme telles.

## Mise en ligne (GitHub Pages)

Les pages rendues sont commitées à côté de leurs sources (`.nojekyll`, pas de CI) : réglages du dépôt → *Pages* → *Deploy from a branch* → branche voulue, dossier `/ (root)`.

## Travailler sur le dépôt

```bash
sudo apt install pandoc            # >= 3.1
pip install pyyaml                 # build et contrôles
python3 tools/gen_site.py          # accueil, feuille de route, plans, navigation (depuis data/curriculum.json)
python3 tools/gen_module_parts.py  # parties générées des modules (pour qui, prérequis, place, comment travailler)
python3 tools/market_analysis.py && python3 tools/gen_market.py   # analyse du marché (data/jobs, data/coverage.json)
python3 tools/build.py             # rend chaque index.md en index.html
python3 tools/check_gates.py       # contrats des cours/projets + site
python3 tools/check_gates.py --labs   # exécute aussi les verify.sh des labs « bac à sable »
python3 tools/check_links.py       # liens externes
python3 tools/validate_research.py && python3 tools/verify_quotes.py   # données de recherche
```

Les règles (contrats, honnêteté des badges, langue, interdits) sont dans [`AGENTS.md`](AGENTS.md) et `specs/`.

## Structure

```
index.md|html          accueil généré (tools/gen_site.py)
profile/  path/  masters/  resources/  lab-setup/
courses/<id>/          un module = une longue page
projects/<id>/         un projet de portfolio
labs/<module>/<lab>/   code des labs ; verify.sh pour les labs « sandbox »
data/                  curriculum.json, nav.json, enquête (masters, offres, ressources)
specs/  tools/         contrats et outils rejouables
assets/                paper.css, theme.js
```

## Licence

Voir `LICENSE`.
