# Projet 4 — Placement multi-fournisseurs sensible aux coûts

Énoncé complet : `projects/multi-provider-scheduler/index.md` (page du site).

```
starter/      data.py (fourni) ; sim.py, policies.py, compare.py, manifests.py à écrire
reference/    solution de référence (à consulter après votre tentative)
tests/        29 tests partagés ; IMPL=starter|reference choisit le code testé
verify.sh     prouve : référence verte, départ rouge
```

**Toutes les données sont inventées** (prix en unités arbitraires, capacités, taux d'interruption) : ne les lisez pas
comme le marché. Remplacez-les par vos propres relevés, pris le jour même sur les pages de prix des fournisseurs.

Prérequis : Python avec `pytest`, `pyyaml` et `yamllint` (`pip install pytest pyyaml yamllint`).

```bash
export PYTHON=/chemin/vers/python
IMPL=starter $PYTHON -m pytest -q tests     # votre travail : 28 échecs sur 29 au départ
PYTHON=$PYTHON bash verify.sh               # référence verte (29), départ rouge
cd reference && python3 compare.py --seeds 20
```

Les manifestes (SkyPilot, Kueue) sont validés **structurellement** : formes et références croisées, pas contre les
schémas officiels (aucun cluster, aucune CRD, aucun compte cloud dans le bac à sable).
