# Projet 3 — Entraîneur tolérant aux pannes

Énoncé complet : `projects/resilient-trainer/index.md` (page du site).

```
starter/      code à compléter : ckpt.py (naïf), supervisor.py et goodput.py (à écrire), train.py (fourni)
reference/    solution de référence : à consulter après votre propre tentative
tests/        19 tests, partagés ; IMPL=<dossier> choisit le code testé (starter, reference ou votre copie)
verify.sh     prouve : référence verte, départ rouge
```

Prérequis : un Python avec PyTorch CPU (`pip install torch --index-url https://download.pytorch.org/whl/cpu`) et `pytest`.

```bash
export PYTHON=/chemin/vers/python
IMPL=starter $PYTHON -m pytest -q tests     # votre travail : 17 échecs sur 19 au départ
PYTHON=$PYTHON bash verify.sh               # référence verte (19), départ rouge (17 échecs)
cp -r starter mon-code                      # travaillez dans une copie : verify.sh exige que starter/ échoue encore
IMPL=mon-code $PYTHON -m pytest -q tests
```

Pannes injectables dans `train.py` (variable `FAULT`, une seule fois par dossier de travail) : `kill:N`, `hang:N`, `torn:N`.

Mesurer le coût d'un checkpoint pour une taille d'état donnée (sur **votre** code complété : le `ckpt.py` de départ n'écrit ni somme de contrôle ni `fsync` et ne sauvegarde pas le remplissage ; `reference/` sert de comparaison) :

```bash
$PYTHON mon-code/train.py --workdir /tmp/w --steps 60 --ckpt-every 10 --pad-mb 64
$PYTHON mon-code/goodput.py --workdir /tmp/w --mtbf-hours 3.09 --restart-seconds 300
```

`--mtbf-hours 3.09` vient de 1 296 h / 419 pannes imprévues (Llama Team, 2024, § 3.3.4) ; `--restart-seconds 300` est une valeur **supposée**, sans source.

Étiquettes d'honnêteté : les données d'entraînement sont synthétiques (générées par `train.py`) ; les pannes sont injectées par `FAULT`, jamais observées ; les temps de checkpoint dépendent de votre disque ; le test de blocage utilise un délai de 3 s qu'une machine très chargée pourrait dépasser (voir la page du projet).
