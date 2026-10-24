# Projet 3 — Entraîneur tolérant aux pannes

Énoncé complet : `projects/resilient-trainer/index.md` (page du site).

```
starter/      code à compléter : ckpt.py (naïf), supervisor.py et goodput.py (à écrire), train.py (fourni)
reference/    solution de référence : à consulter après votre propre tentative
tests/        19 tests, partagés ; IMPL=starter|reference choisit le code testé
verify.sh     prouve : référence verte, départ rouge
```

Prérequis : un Python avec PyTorch CPU (`pip install torch --index-url https://download.pytorch.org/whl/cpu`) et `pytest`.

```bash
export PYTHON=/chemin/vers/python
IMPL=starter $PYTHON -m pytest -q tests     # votre travail : 16 échecs sur 19 au départ
PYTHON=$PYTHON bash verify.sh               # référence verte (19), départ rouge (16 échecs)
```

Pannes injectables dans `train.py` (variable `FAULT`, une seule fois par dossier de travail) : `kill:N`, `hang:N`, `torn:N`.

Mesurer le coût d'un checkpoint pour une taille d'état donnée :

```bash
$PYTHON starter/train.py --workdir /tmp/w --steps 60 --ckpt-every 10 --pad-mb 64
$PYTHON starter/goodput.py --workdir /tmp/w --mtbf-hours 3.09 --restart-seconds 300
```
