# Projet 5 — Observabilité GPU et détection de pannes silencieuses

Énoncé complet : `projects/gpu-observability/index.md` (page du site).

```
starter/      sim.py (fourni) ; exporter.py, detectors.py, dashboard.py, rules/ à écrire ou compléter
reference/    solution de référence (à consulter après votre tentative)
tests/        28 tests partagés ; IMPL=starter|reference choisit le code testé
verify.sh     prouve : référence verte, départ rouge
```

Prérequis : `promtool` (`sudo apt-get install prometheus`, testé avec 2.45.3) et un Python avec `pytest` et `pyyaml`.

```bash
export PYTHON=/chemin/vers/python
IMPL=starter $PYTHON -m pytest -q tests        # votre travail : 26 échecs sur 28 au départ
PYTHON=$PYTHON bash verify.sh                  # référence verte (28), départ rouge
cd starter/rules && promtool check rules gpu.rules.yml && promtool test rules gpu.rules.test.yml
```

Le simulateur produit des valeurs **illustratives**, pas des mesures de matériel réel. Son modèle de blocage
(utilisation haute, activité tensorielle nulle, puissance en baisse) est une hypothèse à valider sur GPU.

Non validé ici : aucun GPU ni vrai dcgm-exporter ; l'exportateur n'a pas été scruté par un vrai Prometheus (`promtool`
et un client HTTP de test seulement) ; `dashboard.json` n'a pas été importé dans Grafana. Les tests des détecteurs
fixent les délais exacts ((k - 1) scrapes) ; les tests de règles ne détectent pas un seuil déplacé de peu (80 -> 84,9 C).

Mutants des détecteurs : sept modifications de `reference/detectors.py` (plus de ré-armement, échelle sans le facteur
1,4826, moyenne à la place de la médiane pour le traînard puis pour le job bloqué, comparaison à deux côtés, plancher
d'échelle à 0, délai sans le filtre « après la panne ») font échouer `tests/test_detectors.py`. Les seuils des règles
`promtool` proches des valeurs de test restent le sujet de l'extension « Mutants plus fins ».
