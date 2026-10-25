# Lab 3.1 — OpenMP : réduction, ordonnancement, faux partage, tâches

Six petits programmes C (OpenMP, GCC) qui rendent visibles les notions du chapitre 2 du module
`parallel-programming`. Tout tourne sur un portable CPU ; testé avec GCC 13.3 (libgomp, `_OPENMP=201511`, soit OpenMP 4.5)
sur une VM Linux à 4 vCPU, le 2026-10-25.

| Programme | Ce qu'il montre | Ce que `verify.sh` affirme |
|---|---|---|
| `sum_variants.c` | somme de 2^25 entiers stockés en `double` : boucle séquentielle, `simd`, course de données, `critical`, `atomic`, `reduction`, `reduction`+`simd`, réduction écrite à la main | toute variante correcte rend EXACTEMENT la somme attendue ; la boucle en course est exacte avec 1 thread (elle n'est jamais jugée avec 4) |
| `false_sharing.c` | histogrammes par thread : `packed` (56 octets par thread), `padded` (64 octets), `private` (tableau local fusionné à la fin) | même histogramme partout ; nombre de lignes de cache partagées (3 pour 4 threads en `packed`, 0 sinon), calculé par adresses |
| `fs_counters.c` | un compteur par thread, `volatile` ou atomique, rangé compact ou aligné : montre que l'effet du faux partage dépend du matériel | le total des compteurs est exact |
| `schedule_demo.c` | quel thread exécute quelle itération, avec `schedule(runtime)` piloté par `OMP_SCHEDULE` ; déséquilibre = max/moyenne de la charge ; temps prédit = charge max × temps par unité | `static` : un bloc par thread ; `static,1` : tourniquet exact ; `static,4` : paquets de 4 ; couverture de toutes les itérations en `dynamic` et `guided` ; déséquilibre 1,75 (`static`) et 1,00 (`static,1`) sur une boucle triangulaire |
| `default_schedule.c` | l'ordonnancement par défaut quand aucune clause `schedule` n'est écrite (laissé à l'implémentation par la spécification) | rien : affiche le motif de votre runtime (blocs statiques avec libgomp 13.3) |
| `tasks_fib.c` | tâches OpenMP et seuil de coupure sur fib(n) | résultat exact ; nombre de tâches créées = nombre prédit par un parcours séquentiel de la récursion |

`exercises/` contient les petits calculateurs utilisés par les corrigés (`imbalance.py`, `line_sharing.py`) ;
`verify.sh` vérifie qu'ils retrouvent les chiffres du programme C.

## Lancer

```bash
bash verify.sh                      # ~5 s ; compile avec gcc -O2 -fopenmp -Wall -Wextra
# à la main
gcc -O2 -fopenmp -Wall -Wextra -o sum_variants sum_variants.c
OMP_NUM_THREADS=4 ./sum_variants reduction 33554432 7
OMP_SCHEDULE=static,1 OMP_NUM_THREADS=4 ./schedule_demo 2000 triangular 60
OMP_NUM_THREADS=4 OMP_PROC_BIND=true OMP_PLACES=cores ./false_sharing packed 100000000 7
```

## Ce que `verify.sh` ne juge pas

Aucun temps. Les durées sont **imprimées** (minimum et médiane de plusieurs répétitions) pour que vous les
compariez au modèle, mais la machine peut être partagée : un seuil sur le temps rendrait le script faux un jour sur deux.
La boucle `race` est un comportement indéfini : le script montre son résultat sans le juger quand 4 threads tournent.
Sur la VM de test, l'effet du faux partage n'apparaît que si chaque thread incrémente des compteurs choisis par la donnée
(histogramme) ou avec des incréments atomiques ; un simple accumulateur `volatile` par thread n'a montré aucun écart mesurable
(voir le chapitre 2 du cours) : l'effet dépend de la microarchitecture.

## Pour aller plus loin

Ajoutez `schedule(nonmonotonic:dynamic)`, `collapse(2)` sur une double boucle, ou `taskloop` ; mesurez avec `OMP_PROC_BIND=spread`
au lieu de `close`. Sur une machine à deux sockets, ajoutez `numactl --interleave=all` et constatez l'effet du premier accès (*first touch*) :
la VM du bac à sable n'a qu'un domaine NUMA, ce lab ne peut pas le montrer.
