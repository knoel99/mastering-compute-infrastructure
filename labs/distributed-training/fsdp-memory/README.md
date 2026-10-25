# Lab 9.2 — FSDP : mesurer la mémoire par rang

`fully_shard` (FSDP2) sur quatre processus `gloo` CPU, comparé à DDP. La mémoire est mesurée **par tailles de tenseurs** (paramètres, gradients, états d'AdamW réellement détenus par chaque rang, lus avec `DTensor.to_local()`), puis comparée à une prédiction écrite à partir des seules formes des tenseurs. Le pic de mémoire résidente (`VmHWM`) est affiché à titre indicatif.

## Fichiers

| Fichier | Rôle |
|---|---|
| `fsdp_memory.py` | modèle de 16,8 millions de paramètres (8 blocs `512 -> 2048 -> 512` et une tête à 10 classes), mesure par rang pour `--mode ddp`, `--mode fsdp`, `--mode fsdp --no-reshard` |
| `predict.py`, `test_predict.py` | prédiction par formes de tenseurs (découpage `torch.chunk` sur la dimension 0) ; 7 tests |
| `equivalence.py` | même initialisation et mêmes données : DDP contre FSDP2 sur trois étapes (pertes, norme globale du gradient, paramètres finaux), et l'erreur de la norme **locale** |
| `check_memory.py`, `verify.sh` | assertions (environ 45 s sur 4 vCPU) |

## Lancer

```bash
export PYTHON=/chemin/vers/python    # PyTorch CPU >= 2.6 (fully_shard), pytest
export OMP_NUM_THREADS=1 GLOO_SOCKET_IFNAME=lo
R="$PYTHON -m torch.distributed.run --standalone --nproc_per_node=4"
$R fsdp_memory.py --mode ddp --out ddp.json
$R fsdp_memory.py --mode fsdp --out fsdp.json
$R fsdp_memory.py --mode fsdp --no-reshard --out fsdp_nr.json
$R equivalence.py eq.json
bash verify.sh
```

## Ce que `verify.sh` prouve

- Les octets de paramètres, de gradients et d'états d'optimiseur mesurés sur chaque rang sont **exactement** ceux prédits (arithmétique entière sur les tailles) : DDP 16 octets par paramètre, FSDP2 le quart, avec un léger déséquilibre dû à la tête `(10, 512)` découpée en lignes 3, 3, 3, 1.
- Le pic de paramètres non partitionnés, observé à l'entrée de chaque bloc de la passe avant, vaut un bloc plus la tête avec `reshard_after_forward=True` et tout le modèle sans re-partition.
- FSDP2 et DDP, partis du même état, donnent les mêmes paramètres à 1e-5 près après trois étapes et la même norme globale de gradient à 1e-3 près (relatif) ; la norme du seul fragment local vaut environ la moitié de la norme globale, et la racine de la somme des carrés des fragments retrouve la norme globale.
- Le pic de mémoire résidente de DDP dépasse de plus de 15 % celui de FSDP2 (seuil volontairement lâche).

## Ce qu'il ne prouve pas

- Le pic en **passe arrière** n'est pas mesuré (échantillonnage à l'entrée des blocs de la passe avant seulement). Les gradients non partitionnés, transitoires avant la réduction-dispersion, ne sont pas comptés non plus.
- La mémoire résidente mélange initialisation (chaque rang construit d'abord le modèle complet avant de le partitionner), tampons de communication et allocateur : elle ne se lit pas comme les tailles de tenseurs. C'est la raison d'être de l'initialisation sur le périphérique `meta` (non testée ici).
- Aucun GPU : pas de flux CUDA, donc aucun recouvrement des all-gather avec le calcul.

## Pour aller plus loin

Appliquer `fully_shard` par couche **et** à la racine est ce qui rend le pic petit : essayez de ne l'appeler que sur la racine et relisez le pic de paramètres non partitionnés. Sur GPU, ajoutez `MixedPrecisionPolicy(param_dtype=torch.bfloat16, reduce_dtype=torch.float32)` (non testé ici).
