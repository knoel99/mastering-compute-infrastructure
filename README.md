# mastering-compute-infrastructure

Parcours d'apprentissage pour devenir **compute infrastructure engineer** : opérer des clusters GPU, ordonnancer (Slurm, Kubernetes), entraîner à grande échelle, tenir les pannes, piloter la capacité multi-fournisseurs.

**Site (français)** : <https://knoel99.github.io/mastering-compute-infrastructure/>

Le contenu est un ensemble de pages HTML statiques (style dérivé de [`polytechnique-llga`](https://github.com/knoel99/polytechnique-llga)) :

- **Cours** : des modules en pages longues (fiche, plan de séances, chapitres avec exemples chiffrés, labs exécutables, exercices corrigés, checkpoint de sortie, références).
- **Projets de portfolio** : des livrables publiables, réalisables sans GPU dans leur version de base.
- **Enquête sur les masters HPC** (France, États-Unis, Chine, monde) croisée avec des offres d'emploi, avec données sourcées dans `data/`.
- **Point de départ** : comparaison d'un profil de référence (`CAREER.md` du dépôt [Certifications](https://github.com/knoel99/Certifications)) au métier visé.

## Mise en ligne (GitHub Pages)

Les pages rendues sont commitées à côté de leurs sources (`.nojekyll`, pas de CI) : réglages du dépôt → *Pages* → *Deploy from a branch* → branche voulue, dossier `/ (root)`.

## Travailler sur le dépôt

```bash
sudo apt install pandoc            # >= 3.1
pip install pyyaml                 # build et contrôles
python3 tools/gen_site.py          # accueil, feuille de route, navigation (depuis data/curriculum.json)
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
