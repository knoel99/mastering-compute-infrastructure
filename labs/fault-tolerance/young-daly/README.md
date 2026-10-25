# Lab 10.1 — Intervalle de checkpoint optimal (Young, Daly, Monte-Carlo)

Compare trois choses : les formules de Young et de Daly, le modèle exact de l'espérance du temps d'horloge pour des pannes exponentielles, et une **simulation de Monte-Carlo** de l'entraînement qui subit des pannes. La simulation est un modèle (il n'y a ni GPU ni vrai cluster) : elle vérifie les mathématiques, pas un système réel.

```
yd.py         formules (young, daly_first, daly_high, modèle exact, argmin numérique) et simulateur
sweep.py      balayage de la période, tableau, JSON et graphique SVG (échelle log)
test_yd.py    9 tests : formules, accord Monte-Carlo / modèle exact, planéité de l'optimum, pannes en rafales
verify.sh     lance les tests puis un balayage avec les valeurs du cours et affiche une ligne « OK young-daly »
```

```bash
export PYTHON=/chemin/vers/python   # numpy et pytest suffisent
PYTHON=$PYTHON bash verify.sh
$PYTHON sweep.py --delta 60 --mtbf-hours 3.09 --restart 300 --svg yd.svg
```

Ligne attendue (sortie réelle du bac à sable, 2026-10-24) :

```
OK young-daly: Young tau=1155 s, Daly tau=1116 s, exact argmin tau=1116 s; goodput at Young 0.8767 vs best sampled 0.8767
```

Ce que le lab ne fait pas : il ne mesure aucun coût de checkpoint réel (voir le projet *resilient-trainer*), et ses pannes sont des tirages aléatoires, pas des données de production. Les assertions portent sur des tolérances statistiques, jamais sur des durées d'exécution.
