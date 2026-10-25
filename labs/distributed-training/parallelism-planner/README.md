# Lab 9.4 — Un planificateur de parallélisme testé

Un calculateur de mémoire et de communication pour choisir `(tp, pp, dp, étape ZeRO)`. **C'est un modèle, pas une mesure** : chaque formule cite sa source (ZeRO, Korthikanti et al. 2022, Narayanan et al. 2021, modèle α-β du module `perf-models`), et chaque bande passante, pic ou MFU est un paramètre d'entrée que l'appelant doit justifier.

```
starter/planner.py     fonctions à écrire (NotImplementedError), ring_allreduce_seconds fourni
reference/planner.py   solution de référence : à lire APRÈS votre tentative
mesh.py                arithmétique des rangs d'une grille N-D (fourni, testé contre DeviceMesh de PyTorch)
mesh_demo.py           l'extrait de l'exemple 1.2 du cours (sortie exacte vérifiée)
placement_demo.py      l'extrait de l'exemple 5.1 du cours : nœuds traversés par les groupes TP et DP (sortie exacte vérifiée)
mesh_check.py          lancé avec torchrun : mesh.py contre torch.distributed.device_mesh (4 processus gloo)
tp_mlp_check.py        MLP à parallélisme tensoriel sur 2 processus gloo (opérateurs f et g de Megatron) contre le MLP dense
configs/, check_configs.py   exemples de configuration Megatron, DeepSpeed, TorchTitan (chapitre 9) : analysés, jamais exécutés
scenario.py            énumère les dispositions d'un job et classe celles qui tiennent en mémoire (chapitre 5)
tests/                 28 tests ; IMPL=starter|reference choisit le code testé
verify.sh              prouve : référence verte, départ rouge pour la bonne raison, scénario et DeviceMesh
```

## Lancer

```bash
export PYTHON=/chemin/vers/python          # pytest ; PyTorch CPU pour mesh_check.py
IMPL=starter $PYTHON -m pytest -q tests    # votre travail : 22 échecs sur 28 au départ
IMPL=reference $PYTHON scenario.py --top 12        # le tableau du chapitre 5
IMPL=reference $PYTHON scenario.py --top 6 --sort dp_hidden
bash verify.sh
```

## Ce que `verify.sh` prouve

- La référence passe les 28 tests ; le départ échoue sur 22 tests, tous par `NotImplementedError` (le script refuse toute autre erreur).
- Les chiffres de la figure 1 de l'article ZeRO (7,5 milliards de paramètres, 64 rangs : 120, 31,4, 16,6 et 1,9 Go) sont retrouvés.
- Les formules d'activations du tableau 2 de Korthikanti et al. et le fait que le premier étage d'un pipeline 1F1B garde « toutes les couches » quel que soit `p` sont testés.
- `scenario.py` n'affiche que des dispositions qui tiennent dans 90 % de 80 Go.
- `mesh.py` retrouve les groupes de `DeviceMesh` de PyTorch, et `placement_demo.py` donne la sortie exacte de l'exemple 5.1 (nœuds traversés par les groupes TP et DP).
- Un MLP à parallélisme tensoriel sur deux processus (A découpée par colonnes, B par lignes) donne la sortie et les gradients du MLP dense (erreur de l'ordre de 1e-14 en float64) avec **un** all-reduce en passe avant et **un** en passe arrière.
- Les fichiers de `configs/` sont analysés (`bash -n`, `json`, `ast`) et leur arithmétique est vérifiée : 4 x 4 x 2 x 2 = 64 GPU et 256 micro-batches pour la commande Megatron, `train_batch_size = micro-batch x accumulation x GPU` pour DeepSpeed.

## Ce qu'il ne prouve pas

- Aucun chiffre du scénario n'est une mesure : le modèle ignore l'efficacité perdue sur de petites matrices, le déséquilibre des étapes, les termes de latence, la fragmentation mémoire et le recouvrement. Le classement qu'il affiche est un filtre et une borne, pas un ordre à suivre.
- Les surcoûts de recalcul (7 % sélectif, 39 % complet) viennent d'**une** mesure d'un modèle de 22 milliards de paramètres sur A100 (tableau 4 de Korthikanti et al.) ; remplacez-les par les vôtres.
- Aucune comparaison avec un entraînement réel n'est faite dans ce lab.
- Les fichiers de `configs/` ne prouvent rien sur Megatron-LM, DeepSpeed ni TorchTitan : aucun des trois n'est installé, la commande et les recettes n'ont pas été lancées.
