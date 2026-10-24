# Projet 2 — Étude de passage à l'échelle d'un entraînement

Énoncé complet : `projects/scaling-study/index.md` (page du site).

```
starter/      bench.py (fourni) ; fit_model.py, analysis.py, run_study.py, report.py à écrire
reference/    solution de référence et example_report.md (à consulter après votre étude)
tests/        23 tests partagés ; IMPL=starter|reference choisit le code testé
verify.sh     prouve : référence verte, départ rouge
```

Prérequis : Python avec PyTorch CPU, numpy et pytest ; 4 processeurs (virtuels ou non) de préférence.

```bash
export PYTHON=/chemin/vers/python
IMPL=starter $PYTHON -m pytest -q tests        # votre travail : 20 échecs sur 23 au départ
PYTHON=$PYTHON bash verify.sh                  # référence verte, départ rouge
```

Une mesure isolée (les ranks sont des processus gloo sur 127.0.0.1) :

```bash
OMP_NUM_THREADS=1 $PYTHON starter/bench.py --world-size 2 --batch-per-rank 64 --out /tmp/b2.json
```

Le balayage des tailles de message d'un all-reduce vient du lab 2.2 : `labs/perf-models/allreduce-model/bench_allreduce.py`.

## Ce que `verify.sh` prouve, et ce qu'il ne prouve pas

- Référence verte, départ rouge **pour la bonne raison** : les 20 échecs du départ sont des `NotImplementedError` (le script refuse toute autre erreur). `bench.py` est fourni : ses 3 tests passent aussi au départ.
- Les tests d'analyse, d'ajustement et de rapport utilisent des **données synthétiques écrites à la main** ; seuls `bench.py` et le test de bout en bout lancent de vrais processus `gloo`.
- Aucun nombre de la page (tableaux de résultats, `example_report.md`) n'est rejoué par `verify.sh` : ils viennent d'exécutions uniques sur une VM à 4 processeurs virtuels, et un second essai donne des valeurs différentes (mêmes conclusions qualitatives).
- Un seul seuil dépend du temps : `test_two_processes_communicate_and_schema_is_stable` exige une communication médiane supérieure à 100 µs (de l'ordre de 0,7 à 1,1 ms mesuré ici).
- Trois altérations de `bench.py` ne sont pas détectées : la division du gradient par le nombre de rangs, la barrière de `--decompose`, et l'échange des phases « attente » et « all-reduce ». Les détecter demanderait des assertions sur des durées.
