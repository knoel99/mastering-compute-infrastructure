# Lab 12.3 — Matrice de décision Slurm / Kubernetes

Type : **sandbox**. Une grille pondérée (`criteria.yaml` : 12 critères, 3 options, un score de 1 à 5 et une justification par case), cinq profils d'équipe (`scenarios.yaml` : poids de 0 à 5 et exigences éliminatoires), et `score.py` qui calcule les scores, applique les exigences, et mesure la **robustesse** du résultat en perturbant poids et scores.

## Honnêteté

Les scores sont le **jugement du parcours au 2026-10-24**, pas des mesures ; les profils sont des composites fictifs. L'outil ne tranche pas : il rend un désaccord explicite et montre si l'on peut le résoudre en changeant un poids. Un biais connu : l'option « hybride » reprend les points forts des deux autres et paie surtout sur la simplicité d'exploitation ; l'exercice 10 du module le met à l'épreuve.

## Lancer

```bash
python3 -m pip install pytest pyyaml
PYTHON=python3 bash verify.sh     # 9 tests, le tableau des cinq profils, un point de bascule
python3 score.py --draws 5000 --seed 1
```

## Pour aller plus loin

Remplacez les scores par les vôtres, ajoutez un critère « taille de l'équipe d'exploitation » et une option « cloud géré », puis regardez quels profils changent de vainqueur.
