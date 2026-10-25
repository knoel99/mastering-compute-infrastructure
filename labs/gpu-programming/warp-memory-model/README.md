# Lab 4.1 — Le warp et la mémoire, en modèle

**Type : `sandbox`** (Python pur, aucun GPU). **Ce qui est vérifié ici :** le modèle et ses tests. **Ce qui n'est pas exécuté ici :** les programmes CUDA C++ de `cuda/`, qui demandent un GPU (ils sont seulement compilés avec `nvcc` 12.0 si celui-ci est installé).

Le simulateur CUDA de Numba n'implémente pas les warps (documentation Numba, section « Limitations »). La coalescence, les conflits de bancs et la divergence ne s'y observent donc pas : ce lab les **modélise** à partir de ce que dit la documentation NVIDIA, puis vous demande de réécrire le modèle.

~~~bash
python3 warpmodel.py report                          # les tables du chapitre 2
python3 warpmodel.py occupancy --threads 256 --regs 32
WARPMODEL_MODULE=starter.warpmodel python3 -m pytest -q test_warpmodel.py   # échoue : à vous de jouer
./verify.sh
~~~

## Contenu

| Fichier | Rôle |
|---|---|
| `warpmodel.py` | solution de référence : secteurs de 32 octets, conflits de bancs, divergence, occupation |
| `starter/warpmodel.py` | quatre fonctions à écrire ; les tests doivent échouer tant qu'elles ne le sont pas |
| `test_warpmodel.py` | 25 tests exacts (code déterministe, valeurs dérivées à la main dans le cours) |
| `cuda/access_patterns.cu` | copie avec pas : à lancer sur GPU pour confronter la prédiction à la mesure |
| `cuda/transpose.cu` | transposition naïve, par tuile, par tuile avec colonne de remplissage |

## Limites du modèle (à lire)

- Les secteurs de 32 octets valent pour la capacité de calcul 6.0 et plus (guide des bonnes pratiques CUDA, §10.2.1). Les caches (L1, L2) peuvent absorber une partie du surcoût réel : le modèle donne le trafic de **chaque requête de warp**, pas le temps.
- L'occupation est une borne haute : le modèle ignore la granularité d'allocation des registres et de la mémoire partagée. Utilisez l'API d'occupation de CUDA ou la section Occupancy de Nsight Compute pour la valeur réelle.
- Les limites par SM par défaut sont celles de la capacité de calcul 8.0 (A100) : guide de programmation CUDA, annexe « Compute Capabilities ».
- La prédiction de `access_patterns.cu` (rapport de trafic) est **falsifiable** : si votre GPU la contredit, notez l'écart et cherchez pourquoi (cache L2, taille de secteur, ECC).
