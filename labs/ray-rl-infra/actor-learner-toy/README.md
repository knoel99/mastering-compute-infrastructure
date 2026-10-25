# Lab 11.2 — Boucle acteur-apprenant minimale

Un environnement jouet (un couloir de 16 cases), un apprenant à gradient de politique, un tampon de rejeu, des acteurs qui produisent des trajectoires avec des poids éventuellement périmés. Deux versions de la boucle :

- `loop_sim.py` : **déterministe**, l'obsolescence est un paramètre (`lag`) et la courbe est reproductible à la graine près ;
- `loop_ray.py` : de **vrais acteurs Ray**, l'obsolescence et le débit résultent du timing.

```
toy_env.py    Corridor (glissement 10 %, horizon 60), rollout() qui enregistre mu(a|s), expected_return() EXACT
learner.py    REINFORCE tabulaire ; correct=True applique rho = min(1, pi/mu) à chaque pas (poids tronqué de V-trace)
replay.py     tampon FIFO de trajectoires, échantillonnage uniforme, âges en versions
loop_sim.py   boucle à obsolescence imposée ; courbes reproductibles
loop_ray.py   acteurs Ray, ray.put des poids, modes « queue » (avec crédits) et « replay »
test_toy.py   15 tests
report.py     les tableaux cités dans le cours
verify.sh     pytest, report.py, « OK actor-learner-toy »
```

```bash
export PYTHON=/chemin/vers/python   # ray, numpy, pytest
PYTHON=$PYTHON bash verify.sh       # environ 75 s
```

## Ce qui est simulé, et ce qui ne l'est pas

- **Simulé** : l'environnement est un jouet ; `step_cost_s` (0,3 ms par pas) et `update_cost_s` (10 ou 30 ms) imitent un simulateur et un apprenant plus lourds par des `sleep`. Aucune de ces durées n'est une mesure d'un système réel.
- **Simplification assumée** : `correct=True` n'est **pas** V-trace. C'est le poids d'importance tronqué `rho = min(1, pi/mu)` appliqué à un estimateur de Monte-Carlo, sans trace de valeur. Le but est de rendre l'écart de politique mesurable, pas de reproduire IMPALA.
- **Réel** : Ray 2.59.0, ses acteurs, `ray.put` / `ray.wait`, les crédits. La partie B n'est pas reproductible bit à bit (l'entrelacement des acteurs décide) ; les tests n'y affirment que des propriétés de structure.

## Hypothèse à garder en tête

Dans ce jouet, l'obsolescence dégrade l'apprentissage sans correction et la correction tronquée l'atténue (partie A). C'est un résultat **de ce jouet, avec ces réglages** (couloir de 16 cases, taux d'apprentissage 1,0, 4 trajectoires par mise à jour, 8 graines). Il ne dit rien du réglage d'un entraînement de grand modèle.

## Sortie réelle (VM de test, 4 vCPU, Python 3.13, Ray 2.59.0, 2026-10-25)

```
A. controlled lag, 8 seeds, 400 updates, b=4 trajectories per update, lr=1.0
    lag  update rule  mean final  worst run  runs < 0.75
      0        naive       0.811      0.810         0/8
      0   clipped IS       0.811      0.810         0/8
     32        naive       0.705      0.490         6/8
     32   clipped IS       0.798      0.692         1/8
    128        naive       0.602     -0.232         7/8
    128   clipped IS       0.802      0.697         1/8
B. real Ray actors (simulated env step 0.3 ms, simulated update 10 ms), queue mode, no credits
     N  steps/s  upd/s  mean lag  p95  learner wait  final return
     1     2075   19.1      0.25    1          0.72          0.79
     2     3723   31.6      0.49    1          0.54          0.79
     4     4733   41.5      0.99    1          0.39          0.78
     8     3132   27.9      1.95    5          0.59          0.80
    K  steps/s  mean lag  p95   K/b
 None     2418      3.72   10   nan
    8     1578      1.89    8   2.0
    4     1883      0.99    1   1.0
```

Les valeurs de la partie B changent d'une exécution à l'autre ; celles de la partie A sont identiques à chaque exécution (graines fixées).

## Pour aller plus loin

Remplacez le jouet par un petit réseau PyTorch CPU ; ajoutez une vraie V-trace ; rendez l'apprenant asynchrone du pilote (un acteur Ray dédié) ; reliez les mesures de la partie B au modèle du laboratoire 11.3 (`throughput-model`).
