# Lab 4.2 — Noyaux CUDA dans le simulateur Numba

**Type : `sandbox`.** **Vérifié ici (Numba 0.68.0, simulateur `NUMBA_ENABLE_CUDASIM=1`) :** les noyaux Numba (somme par blocs, scan, produit matriciel par tuiles, transposition), leurs tests, le comptage des lectures globales, les expériences de précision. **Non exécuté ici :** `bench_gpu.py` (octet-compilé seulement) et les programmes `cuda/*.cu` (compilés avec `nvcc` si présent, jamais lancés : pas de GPU).

Le simulateur exécute un thread Python par thread CUDA : il vérifie la **logique** (indices, barrières, atomiques), pas la **vitesse**. Il ne simule ni warps ni bancs de mémoire partagée (voir le lab 4.1). Un chronométrage dans le simulateur ne signifie rien.

~~~bash
python3 -m pip install numba torch numpy pytest
NUMBA_ENABLE_CUDASIM=1 python3 -m pytest -q test_kernels.py test_precision.py
python3 demo.py loads        # lectures globales : naïf contre tuilé
python3 demo.py errors       # deux erreurs classiques
python3 demo.py atomics      # observation : l'ordre des atomiques varie-t-il d'un lancement à l'autre ?
python3 precision.py         # formats, accumulateur FP16, mise à l'échelle, ordre des sommes
./verify.sh
~~~

## Contenu

| Fichier | Rôle |
|---|---|
| `kernels.py` | `vec_add`, somme par blocs, scan, `matmul` naïf et par tuiles (avec compteur de lectures), transposition |
| `precision.py` | tables de formats (`torch.finfo`), accumulateur FP16, mise à l'échelle de perte, ordre des sommes, arrondi émulé |
| `test_kernels.py`, `test_precision.py` | 19 tests (compteurs et égalités binaires exactes là où le code est déterministe) |
| `cuda/reduce_matmul.cu`, `cuda/streams_overlap.cu` | jumeaux CUDA C++ des noyaux et pipeline de streams (GPU requis) |
| `bench_gpu.py` | branche GPU : noyaux Numba contre `torch.matmul` avec événements CUDA (**non exécuté**) |

## Honnêteté

- `round_mantissa(x, 10)` **émule** l'arrondi des entrées de TF32 ; ce n'est pas la sortie d'un cœur tensoriel (le mode d'arrondi matériel peut différer). Avec 7 bits, il reproduit exactement `torch.bfloat16` (testé).
- Le test « barrières manquantes » (`sync=False`) dépend de l'ordonnancement des threads par le système : il accorde 6 essais et exige au moins un résultat faux (observé : tous faux).
- Sur 30 lancements d'une somme par `cuda.atomic.add` (256 valeurs `float32`, 4 blocs), le simulateur a donné un seul résultat : c'est une **observation**, pas une garantie. Il ne montre donc pas la non-reproductibilité d'`atomicAdd` d'un vrai GPU, et `precision.py` la remplace par des sommes dans des ordres aléatoires.
