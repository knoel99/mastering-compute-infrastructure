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
