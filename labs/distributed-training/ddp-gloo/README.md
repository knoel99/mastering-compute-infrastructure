# Lab 9.1 — DDP à quatre processus sur CPU

Entraînement d'un petit MLP (1,35 million de paramètres, fp32) avec `DistributedDataParallel` sur quatre processus `gloo` lancés par `torchrun`, comparé à un entraînement mono-processus sur le même lot global. Aucun GPU : les « rangs » sont des processus d'une même machine, le réseau est le bouclage local. La **méthode** est celle d'un cluster, pas les débits.

## Fichiers

| Fichier | Rôle |
|---|---|
| `common.py` | modèle, données synthétiques **seedées** (le lot global d'une étape est identique quel que soit le nombre de processus), découpage du lot par rang |
| `train.py` | entraînement mono-processus ou DDP ; options `--hook` (compte les all-reduce et les octets), `--timing` (coût de communication), `--bucket-cap-mb`, `--uneven` (découpage inégal, un bug) |
| `buckets.py`, `test_buckets.py` | prédit le découpage en seaux de DDP ; 5 tests unitaires |
| `compare.py`, `check_ddp.py` | comparaison des paramètres finaux, assertions de `verify.sh` |
| `unused_param_demo.py` | l'erreur classique « Expected to have finished reduction in the prior iteration » et sa correction |
| `numerics_demo.py` | la non-associativité de l'addition flottante, base du chapitre 7 |
| `verify.sh` | enchaîne le tout (environ 45 s sur 4 vCPU) |

## Lancer

```bash
export PYTHON=/chemin/vers/python    # PyTorch CPU + pytest
export OMP_NUM_THREADS=1 GLOO_SOCKET_IFNAME=lo
$PYTHON train.py --steps 12 --out single.json
$PYTHON -m torch.distributed.run --standalone --nproc_per_node=4 train.py --steps 12 --hook --timing --out ddp.json
$PYTHON compare.py single.json ddp.json
$PYTHON buckets.py                      # seaux prédits ; ddp.json contient ddp_rebuilt_bucket_sizes
bash verify.sh
```

Variantes à essayer : `--optim adamw --lr 0.003` (écart plus grand que SGD : Adam divise par une racine), `--bucket-cap-mb 1` (autre découpage, autres bits), `--uneven` (le bug du dernier lot inégal).

## Observations citées dans le cours (VM de 4 vCPU, PyTorch 2.14.1 CPU, non assertées)

```bash
# 30 étapes (valeur par défaut), un processus contre DDP à 4 : SGD, puis AdamW
$PYTHON train.py --out s.json && $PYTHON -m torch.distributed.run --standalone --nproc_per_node=4 train.py --out d.json && $PYTHON compare.py s.json d.json
$PYTHON train.py --optim adamw --lr 0.003 --out sa.json && $PYTHON -m torch.distributed.run --standalone --nproc_per_node=4 train.py --optim adamw --lr 0.003 --out da.json && $PYTHON compare.py sa.json da.json
# 12 étapes, trois découpages en seaux : le défaut (2 seaux) diffère de --bucket-cap-mb 1 (6 seaux), qui est identique à 0.25 (mêmes 6 seaux)
```

Valeurs relevées : écart maximal de 7,5e-09 (SGD) et de 1,35e-06 (AdamW, relatif 7,3e-06) ; 7,5e-09 entre le cap par défaut et `--bucket-cap-mb 1` ; 0 entre `--bucket-cap-mb 1` et `0.25` ; 8,3e-03 avec `--uneven`.

## Ce que `verify.sh` prouve

- DDP à 4 processus et un seul processus partent du même état et voient les mêmes données : écart maximal des paramètres inférieur à 1e-5 après 12 étapes (mesuré : de l'ordre de 1e-8 ; **pas** égalité bit à bit, voir chapitre 7).
- Deux exécutions identiques de DDP donnent exactement les mêmes bits (ordre fixe de l'anneau `gloo`).
- Le prédicteur de seaux (`buckets.py`) retrouve les tailles que DDP journalise après la reconstruction de la fin de la première itération, pour le cap par défaut et pour `--bucket-cap-mb 1`.
- Le crochet de communication compte `1 + (étapes - 1) x seaux` all-reduce et exactement `étapes x octets de paramètres` octets : la première itération n'a qu'un seul seau.
- Un découpage inégal du lot change visiblement le résultat (écart supérieur à 1e-4).
- L'erreur de paramètre inutilisé est reproduite (code de sortie 1, nom du paramètre `a.weight` dans le message avec `TORCH_DISTRIBUTED_DEBUG=INFO`), puis corrigée (code 0).

## Ce qu'il ne prouve pas

- Aucune durée n'est assertée. Les temps affichés (pas avec et sans communication, all-reduce isolé) sont informatifs : sur 4 vCPU partagés entre les 4 rangs, calcul et communication se disputent probablement les mêmes cœurs (explication non testée) : on n'observe **pas** de recouvrement utile comme sur un GPU.
- `model._get_ddp_logging_data()` est une API privée, testée avec PyTorch 2.14.1 (CPU) ; ses clés (`rebuilt_bucket_sizes`) peuvent changer.
- `TORCH_DISTRIBUTED_DEBUG=DETAIL` avec DDP sur `gloo` CPU a fait **planter** les processus (SIGSEGV) à la construction de DDP avec cette version : le lab n'utilise que `INFO` avec DDP (le niveau `DETAIL` est utilisé sans DDP dans le lab 9.3).
- NCCL, GPU, plusieurs nœuds : non testés ici.

## Pour aller plus loin

Sur un nœud à GPU : remplacer `gloo` par `nccl`, ajouter `device_ids=[local_rank]`, et lire `Avg backward comm/comp overlap time` avec `TORCH_DISTRIBUTED_DEBUG=DETAIL` (documenté, non exécuté ici).
