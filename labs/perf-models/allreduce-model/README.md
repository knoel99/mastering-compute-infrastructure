# Lab 2.2 — α-β : prédire puis mesurer

Mesure le temps d'un `all_reduce` pour des messages de 1 Kio à 16 Mio sur 4 processus (backend `gloo`, CPU), ajuste le modèle de l'anneau $T=2(p-1)\alpha+2\frac{p-1}{p}\frac{n}{B}$ et compare prédiction et mesure.

```bash
python3 -m pip install torch numpy --index-url https://download.pytorch.org/whl/cpu   # ou votre installation habituelle
OMP_NUM_THREADS=1 torchrun --nproc_per_node=4 bench_allreduce.py --out allreduce.json
python3 fit_alpha_beta.py allreduce.json
./verify.sh
```

Sur un nœud multi-GPU, remplacez `gloo` par `nccl` et placez les tenseurs sur GPU : voir « Pour aller plus loin » dans le module `perf-models`.
