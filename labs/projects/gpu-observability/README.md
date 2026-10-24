# Projet 5 — Observabilité GPU et détection de pannes silencieuses

Énoncé complet : `projects/gpu-observability/index.md` (page du site).

```
starter/      sim.py (fourni) ; exporter.py, detectors.py, dashboard.py, rules/ à écrire ou compléter
reference/    solution de référence (à consulter après votre tentative)
tests/        21 tests partagés ; IMPL=starter|reference choisit le code testé
verify.sh     prouve : référence verte, départ rouge
```

Prérequis : `promtool` (`sudo apt-get install prometheus`, testé avec 2.45.3) et un Python avec `pytest` et `pyyaml`.

```bash
export PYTHON=/chemin/vers/python
IMPL=starter $PYTHON -m pytest -q tests        # votre travail : 19 échecs sur 21 au départ
PYTHON=$PYTHON bash verify.sh                  # référence verte (21), départ rouge
cd starter/rules && promtool check rules gpu.rules.yml && promtool test rules gpu.rules.test.yml
```

Le simulateur produit des valeurs **illustratives**, pas des mesures de matériel réel. Son modèle de blocage
(utilisation haute, activité tensorielle nulle, puissance en baisse) est une hypothèse à valider sur GPU.
