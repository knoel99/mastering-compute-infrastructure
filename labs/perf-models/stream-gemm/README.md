# Lab 2.1 — STREAM et GEMM : bandes passantes et pic

Mesure la bande passante mémoire (STREAM *copy* et *add*) et le débit de produit matriciel (GEMM, float32) de votre machine, puis construit **son propre roofline**.

```bash
python3 -m pip install numpy
python3 stream_gemm.py            # mesure complète (quelques secondes), écrit results.json
./verify.sh                       # contrôle de cohérence rapide (bac à sable, sans GPU)
```

Lecture des résultats : voir le chapitre 4 du module `perf-models` (roofline) et le lab 2.1.
Sortie typique : `stream_add_gbs=… peak_gemm_gflops=… ridge_flop_per_byte=…`.

Limites à connaître :

- La bande passante vient d'opérations NumPy élémentaires, **mono-thread** : elle ne dépend pas de `OMP_NUM_THREADS` et sous-estime ce que tous les cœurs ensemble tireraient de la mémoire. Le GEMM, lui, utilise tous les threads BLAS. Le point de rupture mêle donc les deux et est un peu surestimé.
- Les comptes d'octets de STREAM (copie 16, addition 24 octets par élément en `float64`) et ceux du GEMM `float32` (3 n² éléments de 4 octets) sont écrits dans `results.json`, et `verify.sh` les contrôle.
- La mesure complète fait dix répétitions par noyau, le minimum demandé au chapitre 3 du module. `--quick` (petites tailles, trois répétitions) ne sert qu'au contrôle de cohérence de `verify.sh` et aux essais rapides, pas à un rapport.
- `verify.sh` ne vérifie que des bornes basses très larges sur les débits (machine partagée) et l'algèbre du roofline ; un rapport mesure/roofline supérieur à 1 reste possible sur la pente mémoire (GEMM en cache).
