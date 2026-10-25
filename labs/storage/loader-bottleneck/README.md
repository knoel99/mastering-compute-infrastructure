# Lab 8.1 — Démasquer un chargeur de données lent

Une vraie boucle PyTorch (`DataLoader`, processus *workers*, files de prélecture) consomme un jeu de données **synthétique**.
Le lab mesure le temps passé à attendre `next()` (le « stall »), le CPU réellement consommé par les workers et ce que
dit le profileur, puis compare la mesure à un modèle du premier ordre et applique une table de décision.

## Ce qui est réel, ce qui est simulé

| Élément | Statut |
|---|---|
| `DataLoader`, workers, `prefetch_factor`, mise en file, ordre de livraison | **réel** (PyTorch CPU, testé avec 2.14.1 le 2026-10-24) |
| Temps d'attente autour de `next()`, CPU des workers (`/proc/<pid>/stat`), `torch.profiler` | **mesuré** |
| Lecture distante de 6 ms par échantillon, dont 5 % dix fois plus lentes | **simulé** (`time.sleep`) |
| Décodage de 1 ms (partie A) ou 8 ms (partie B) par échantillon | **simulé** (boucle sur `time.process_time`, donc du vrai CPU) |
| Pas GPU de 12 ms | **simulé** (`time.sleep`) |
| `pin_memory` | **non mesuré** : il n'y a pas de GPU ; l'option n'a d'effet qu'avec CUDA |

## Fichiers

- `loader_lab.py` : le jeu de données, `run()` (la boucle mesurée), `predict_stall()` (le modèle), `diagnose()` (la table de décision), `profile_loader()`.
- `run_lab.py` : trois expériences (A : lecture à latence ; B : décodage CPU ; C : profileur), sortie JSON optionnelle ; `--no-in-order` passe `in_order=False` au `DataLoader`.
- `test_loader_lab.py` : tests rapides (déterminisme, limites du modèle, table de décision, un vrai petit `DataLoader`).
- `verify.sh` : tests puis expériences puis assertions.

```bash
export PYTHON=/chemin/vers/python   # avec torch, numpy, pytest
bash verify.sh                      # environ 30 s sur 4 vCPU
python3 run_lab.py --batches 100    # mesures plus longues, donc plus stables
```

## Ce que `verify.sh` affirme (et ce qu'il n'affirme pas)

Aucune durée absolue. Il vérifie : l'écart entre le *stall* mesuré et le modèle reste sous 25 points (35 points pour le chargeur CPU à 4 et 8 workers) ; le *stall* baisse quand on
ajoute des workers ; les workers d'un chargeur à latence sont presque inactifs (compteur CPU) ; sur un chargeur CPU, passer de 4 à 8 workers
ne gagne pas plus de 50 % ; le CPU mesuré par échantillon est de l'ordre du coût de décodage ; le profileur nomme bien les itérateurs du `DataLoader`.

Sortie réelle (VM de test à 4 vCPU, 2026-10-24) :

```
OK loader-bottleneck: stall 0/1/2/4/8 workers = 88 % / 86 % / 74 % / 50 % / 14 %; CPU-bound ceiling 52.1 -> 53.0 batch/s (4 -> 8 workers)
```

## Réserves

- Le modèle (taux moyen) est **optimiste** avec 8 workers : il prédit 0 % de *stall* alors qu'on mesure 13 % à 17 %. La livraison des batchs dans l'ordre **n'explique pas** l'écart : `python3 run_lab.py --no-in-order` (`DataLoader(in_order=False)`) donne 16 % à 19 % sur six exécutions. La cause reste inconnue ; hypothèse non testée : la variabilité des temps de service et la file de taille finie, que des taux moyens ignorent.
- Sur une machine chargée par d'autres processus, les valeurs de la partie B bougent (les 4 vCPU sont partagés) ; les assertions ont des marges larges pour cela. La table de décision lit le CPU par worker, qui baisse quand d'autres processus prennent des cœurs (8 workers à 0,36 cœur chacun ont été diagnostiqués « à latence » à tort sur une machine partagée) : `verify.sh` ne vérifie donc le diagnostic « CPU » que pour 1 worker.
- PyTorch émet un avertissement quand `num_workers` dépasse le nombre de CPU ; le lab le masque (les workers dorment la plupart du temps).
- `_worker_cpu` lit l'attribut privé `_workers` de l'itérateur ; sans lui, le lab retombe sur `getrusage(RUSAGE_CHILDREN)` après arrêt des workers.

## Pour aller plus loin

Sur un nœud GPU : mettre `pin_memory=True`, comparer le temps de copie hôte vers GPU avec et sans, et lire le profil CUDA (`ProfilerActivity.CUDA`). Non exécuté ici.
