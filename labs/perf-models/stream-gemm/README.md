# Lab 2.1 — STREAM et GEMM : bandes passantes et pic

Mesure la bande passante mémoire (STREAM *copy* et *add*) et le débit de produit matriciel (GEMM, float32) de votre machine, puis construit **son propre roofline**.

```bash
python3 -m pip install numpy
python3 stream_gemm.py            # mesure complète (≈ 1 min), écrit results.json
./verify.sh                       # contrôle de cohérence rapide (bac à sable, sans GPU)
```

Lecture des résultats : voir le chapitre 4 du module `perf-models` (roofline) et le lab 2.1.
Sortie typique : `stream_add_gbs=… peak_gemm_gflops=… ridge_flop_per_byte=…`.
