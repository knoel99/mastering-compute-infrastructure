# Projet 1 — Mini-cluster Slurm instrumenté

Énoncé complet : `projects/homelab-slurm/index.md` (page du site).

```
starter/      cluster.yml et une règle d'exemple (fournis) ; config.py, exporter.py à écrire ; rules/ à compléter
reference/    solution de référence (à consulter après votre tentative)
fixtures/     sorties RÉELLES de Slurm 23.11.4 (sacctmgr, sinfo, squeue, sshare), capturées dans le bac à sable
tests/        24 tests ; IMPL=starter|reference choisit le code testé ; fake_sacctmgr.py imite le vrai
verify.sh     hors ligne : référence verte, départ rouge
verify-live.sh  sur un vrai Slurm (root) : applique cluster.yml deux fois, lit de vraies métriques, drain d'un nœud   (écrit et linté ; PAS encore exécuté de bout en bout par l'auteur)
```

Prérequis : `promtool` (`sudo apt-get install prometheus`), Python avec `pytest` et `pyyaml`. Pour `verify-live.sh` :
root et le Slurm du bac à sable du module 5 (`labs/slurm/slurm-sandbox`), qui est **démonté et dont la base est purgée**
à la fin.

```bash
export PYTHON=/chemin/vers/python
IMPL=starter $PYTHON -m pytest -q tests     # votre travail : 22 échecs sur 24 au départ
PYTHON=$PYTHON bash verify.sh               # hors ligne : référence verte (24), départ rouge
sudo PYTHON=$PYTHON bash verify-live.sh     # en direct, avec la solution de référence
sudo PYTHON=$PYTHON IMPL=starter bash verify-live.sh   # en direct, avec VOTRE code
```

`fixtures/` est une capture : réexécutez les commandes (voir l'en-tête de `reference/exporter.py`) sur votre version
de Slurm avant de supposer que les formats sont identiques.
