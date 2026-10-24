# Lab 16.2 — Post-mortem d'un incident simulé

**`incident.log` est SYNTHÉTIQUE** : un journal inventé pour l'exercice, sans système, cluster ni personne réels.
`timeline.py` en tire les jalons (anomalie, détection, acquittement, atténuation, résolution), les durées et les
GPU-heures sans progression ; `postmortem_lint.py` contrôle la structure d'un post-mortem **et** que les durées écrites
dans le texte égalent celles du journal.

```bash
python3 timeline.py incident.log 128
python3 postmortem_lint.py postmortem_example.md --log incident.log --gpus 128
PYTHON=python3 bash verify.sh
```

Exercice : lisez le journal **avant** `postmortem_example.md`, trouvez la cause et rédigez votre propre post-mortem, puis
comparez. Le vérificateur de vocabulaire de blâme est un indice, pas un verdict.
