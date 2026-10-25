# Lab 9.3 — Reproduire et diagnostiquer un hang

Une boucle d'entraînement data-parallel à quatre rangs `gloo` avec un bug injecté sur le rang 2 à l'étape 4, et une procédure d'enquête reproductible. Deux bugs :

- `--bug skip` : le rang 2 saute le all-reduce du gradient de cette étape (un `continue` local). Les collectives s'apparient **par ordre** : les autres rangs apparient leur all-reduce de l'étape 4 avec celui de l'étape 5 du rang 2. La boucle semble avancer, les gradients sont mélangés, et le job ne se bloque qu'à la fin.
- `--bug stuck` : le rang 2 reste bloqué pendant le chargement de son lot (`time.sleep`), hors de toute collective ; les autres l'attendent dans le all-reduce de l'étape 4.

## Ce qui est simulé et ce qui est réel

- **Réel** : les processus `gloo`, `torchrun`, le délai maximal du groupe de processus, `TORCH_DISTRIBUTED_DEBUG=DETAIL`, `monitored_barrier`, `faulthandler` (messages d'erreur copiés de la sortie).
- **Analogue écrit pour ce lab** : `collective_journal.py` reproduit l'idée du *flight recorder* NCCL de PyTorch (tampon circulaire des collectives avec numéro de séquence, état, site d'appel, thread de surveillance qui écrit un fichier par rang) pour `gloo`, parce que le vrai flight recorder (`TORCH_NCCL_TRACE_BUFFER_SIZE`, `TORCH_NCCL_DUMP_ON_TIMEOUT`) n'existe que pour le backend NCCL. L'étape d'entraînement est étiquetée **à la main** (`journal.tag`) ; le vrai outil s'appuie sur la pile d'appels. `analyze_journal.py` imite le raisonnement de l'analyseur officiel, il n'en reprend pas le code.
- **Non exécuté** : tout ce qui concerne NCCL et GPU (commandes du flight recorder réel données dans le cours, non lancées).

## Fichiers

`train_hang.py` (le programme et ses bugs), `collective_journal.py`, `analyze_journal.py`, `verify.sh` (huit scénarios, environ 60 s, CPU presque inactif).

## Lancer à la main

```bash
export PYTHON=/chemin/vers/python OMP_NUM_THREADS=1 GLOO_SOCKET_IFNAME=lo
R="$PYTHON -m torch.distributed.run --standalone --nproc_per_node=4"
$R train_hang.py --bug skip --timeout 5 --journal-dir /tmp/j       # échoue après le délai
$PYTHON analyze_journal.py /tmp/j
TORCH_DISTRIBUTED_DEBUG=DETAIL $R train_hang.py --bug skip --timeout 30   # échoue tout de suite, explicite
$R train_hang.py --bug stuck --timeout 5 --journal-dir /tmp/j2 --stacks-dir /tmp/s2
$R train_hang.py --bug stuck --monitored --timeout 5                # "Rank 2 failed to pass monitoredBarrier"
$R train_hang.py --bug none --timeout 5                             # le programme corrigé
```

## Ce que `verify.sh` prouve

1. Avec le bug `skip`, le rang 0 affiche « step 8 done » (progression apparente), jamais « step 9 done », et tous les rangs finissent par « Timed out waiting ».
2. Avec `TORCH_DISTRIBUTED_DEBUG=DETAIL`, l'erreur nomme l'incohérence tout de suite : le rang 2 est dans `BARRIER` quand les autres sont dans `ALLREDUCE`.
3. Le journal localise la **cause** : première divergence au numéro de séquence 4, où le rang 2 exécute la collective étiquetée `step=5` au lieu de `step=4`.
4. Avec `stuck`, le journal montre trois rangs en attente dans la collective 4 et le rang 2 sans rien en cours ; la pile Python du rang 2 est hors de `all_reduce`, celle du rang 0 dedans.
4b. La voie de production : `kill -USR1` envoyé aux processus de **son propre** `torchrun` (trouvés par `pgrep -P`) écrit les piles sans arrêter les rangs ; le script arrête ensuite son `torchrun` par son PID et ne laisse aucun processus.
5. `monitored_barrier` placé avant la collective fait dire au rang 0 « Rank 2 failed to pass monitoredBarrier ».
5b. `TORCH_DISTRIBUTED_DEBUG=DETAIL` nomme aussi le rang manquant, parce que son enveloppe pose un `monitored_barrier` avant chaque collective.
6. Le programme corrigé se termine avec le code 0.

## Ce qu'il ne prouve pas

- Aucune durée n'est assertée (les délais de 5 s servent seulement à borner l'attente). Le scénario suppose pourtant que les seuils du journal (2 à 2,5 s) et de `faulthandler` (3 s) restent inférieurs au délai du groupe (5 s) : sur une machine très chargée, une exécution peut échouer à tort, et il suffit de la relancer.
- `TORCH_DISTRIBUTED_DEBUG=DETAIL` n'est exercé que sur des collectives simples : avec DDP sur `gloo` CPU ce niveau a fait planter les processus avec PyTorch 2.14.1 (voir le lab 9.1).
- Le thread de surveillance suppose que l'attente d'une collective relâche le verrou global de l'interpréteur, ce qui est le cas pour `gloo` ici ; il n'a pas été vérifié pour d'autres backends.
