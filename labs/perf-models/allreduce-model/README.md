# Lab 2.2 — α-β : prédire puis mesurer

Mesure le temps d'un `all_reduce` pour des messages de 1 Kio à 16 Mio sur 4 processus (backend `gloo`, CPU), ajuste le modèle de l'anneau $T=2(p-1)\alpha+2\frac{p-1}{p}\frac{n}{B}$ et compare prédiction et mesure. Les quatre processus partagent les mêmes cœurs et communiquent par la boucle locale : ce n'est pas un réseau, et les valeurs ajustées (sur la VM de test à 4 vCPU, relevés du 2026-10-25 sur quinze exécutions : α de 250 à 910 µs et B de 0,7 à 1,9 Go/s) varient fortement d'une exécution à l'autre. Seule la méthode se transpose.

```bash
python3 -m pip install torch numpy --index-url https://download.pytorch.org/whl/cpu   # ou votre installation habituelle
OMP_NUM_THREADS=1 torchrun --nproc_per_node=4 bench_allreduce.py --out allreduce.json
python3 fit_alpha_beta.py allreduce.json
./verify.sh
```

Sur un nœud multi-GPU, remplacez `gloo` par `nccl` et placez les tenseurs sur GPU : voir « Pour aller plus loin » dans le module `perf-models`.
