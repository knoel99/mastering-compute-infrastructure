# Lab 10.3 — Superviseur de relance

Un superviseur qui lance un entraîneur, détecte un **plantage** (code de sortie) ou un **blocage** (fichier de pulsation qui ne bouge plus), tue **tout le groupe de processus**, classe l'incident, **exclut** les nœuds fautifs et relance depuis le dernier checkpoint, avec un budget de relances et une garde « aucun progrès ».

Tout est **simulé** : `worker.py` ne fait aucun entraînement, il compte des pas, écrit un checkpoint JSON atomique et plante ou se bloque selon un plan de pannes (`FAULT_PLAN`) lié à un nom de nœud. Les « nœuds » sont des étiquettes (`NODE_NAME`), il n'y a pas de matériel.

```
worker.py                     entraîneur simulé (plantage, blocage, pannes « decay »)
reference/supervisor.py       solution de référence : classify, kill_group, Supervisor, CLI
starter/supervisor.py         squelette à compléter (mêmes noms)
test_supervisor.py            10 tests, IMPL=starter|reference choisit le code testé
xid_triage.py, test_xid.py    triage d'un journal noyau (Xid) ; fixture SYNTHÉTIQUE dans fixtures/
examples/train.sbatch         script Slurm résilient (--requeue, --signal) : lint seulement, non exécuté (il demande des GPU)
examples/job.yaml             Job Kubernetes avec podFailurePolicy : lint seulement, non exécuté (pas de cluster)
examples/requeue_demo.sbatch  démonstration SANS GPU de scontrol requeue sur un vrai Slurm
slurm_demo.sh                 partie B facultative : lance la démonstration sur le bac à sable Slurm du module 5
verify.sh                     référence verte, départ rouge, triage Xid, lint des exemples
```

```bash
export PYTHON=/chemin/vers/python   # pytest suffit
IMPL=starter   $PYTHON -m pytest -q test_supervisor.py   # 10 échecs au départ
PYTHON=$PYTHON bash verify.sh                           # référence verte, départ rouge
sudo bash slurm_demo.sh                                 # partie B, environ 5 minutes, facultative
```

**Branche vérifiée** : `verify.sh` (référence verte, départ rouge, triage Xid, shellcheck et yamllint des exemples). **Branche non vérifiée** : `train.sbatch` et `job.yaml` n'ont été que lintés. `slurm_demo.sh` (avec `requeue_demo.sbatch`) a été exécuté de bout en bout une fois sur Slurm 23.11.4 (bac à sable du module 5, 5 min 44 s, 2026-10-24) et a affiché « OK slurm requeue demo: job 1 completed after 2 requeues » ; `verify.sh` ne le lance pas, car il dépend de Slurm et prend plusieurs minutes.

Remarque sur les tests : le délai de détection d'un blocage est de 1 s dans les tests, et aucune assertion ne porte sur une durée mesurée ; elles portent sur les événements du journal `supervisor.jsonl` et sur la mort réelle du petit-fils du processus bloqué (lu dans `/proc`, en traitant un zombie comme mort).
