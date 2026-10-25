# Lab 11.3 — Modèle de débit d'une boucle en ligne

Un modèle analytique (`model.py`) et une simulation à événements discrets (`des.py`) d'une boucle acteurs-apprenant : combien d'acteurs faut-il pour saturer un apprenant, combien coûte l'obsolescence, et où placer la contre-pression. Le temps est **simulé** : aucune assertion ne dépend d'une horloge, la graine fixe tout.

```
model.py            formules : débit, N*, utilisation, obsolescence (loi de Little), crédits, coût par million de pas
des.py              simulation : acteurs (sync, rollout, put), file bornée, apprenant (b trajectoires, s_L), deux politiques
                    de contre-pression : "block" (l'acteur garde sa trajectoire finie) et "credit" (crédit pris AVANT)
plan.py             dimensionnement en ligne de commande (les prix sont des ENTRÉES : aucun prix réel dans le code)
test_throughput.py  20 tests : modèle contre simulation, loi de Little, saturation, file non bornée, graines
report.py           les tableaux cités au chapitre 6
sweep.py            balayage du nombre d'acteurs N et de crédits K (exercice 11)
make_log.py         compteurs de la boucle simulée au format d'un journal (exercice 7)
verify.sh           pytest, report.py, « OK throughput-model »
```

```bash
export PYTHON=/chemin/vers/python   # numpy, pytest
PYTHON=$PYTHON bash verify.sh       # moins de 10 s
python3 plan.py --m 200 --t-roll 2.0 --t-sync 0.2 --b 4 --s-l 1.0 --queue-cap 8
```

## Ce qui est simulé

Tout : la boucle `m=200, t_roll=2,0 s, t_sync=0,2 s, b=4, s_L=1,0 s` est **illustrative**, pas la mesure d'un système. Le modèle est validé contre la simulation (même paramètres), non contre un système réel. Pour le confronter à des acteurs Ray, voir le laboratoire 11.2, partie B : l'obsolescence mesurée y suit le même ordre de grandeur (`N/b` pour des acteurs qui attendent leur tour).

## Sortie réelle (2026-10-25, graine 1, durées lognormales de coefficient de variation 0,3)

```
learner capacity C = 800 steps/s ; N* = 8.80 -> 9 actors
  N      P  X model   X sim  util  lag mod  lag sim  blocked | credit X credit lag  model
  8    727      727     725  0.90     2.19     2.94      0.0 |      577       2.00   2.19
 10    909      800     794  1.00     4.50     4.41      1.3 |      577       2.00   2.00
 24   2182      800     804  1.00     8.00     8.00     15.2 |      577       2.00   2.00
credit policy, N = 24 actors: how many credits K?
  K   X sim  learner util  lag model  lag sim  p95 lag
  8     577          0.72       2.00     2.00        3
 14     799          0.99       3.50     3.50        5
```

## Limites

- Le modèle d'obsolescence est une estimation de champ moyen : proche de la saturation (ici `N` entre 6 et 9) il sous-estime, parce que la file se remplit avant que le débit n'atteigne le plafond (écart de 0,8 mise à jour pour `N=8`).
- Une seule file et un seul apprenant ; pas de panne ; durées indépendantes. Un réseau partagé, des acteurs hétérogènes ou une perte d'acteur demandent un autre modèle.
