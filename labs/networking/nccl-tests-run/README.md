# Lab 7.3 — nccl-tests sur un vrai cluster

**Lab de type `gpu` : la partie qui exige des GPU n'a pas été exécutée.**

| Élément | État |
|---|---|
| `run_all_reduce.sbatch` (2 nœuds x 8 GPU, `all_reduce_perf`, journaux NCCL par processus, `NCCL_TESTS_MIN_BW`) | linté (`bash -n`, `shellcheck`), **jamais lancé sur des GPU** |
| `parse_nccl_tests.py` (parse du tableau, plateau, taille à 90 %, ajustement α-β, comparaison à l'attendu, `#wrong`) | testé (9 tests) sur des tables **synthétiques** |
| `fixtures/all_reduce_synthetic_*.txt` | **SYNTHÉTIQUES** : générées par `make_sample.py` à partir du modèle d'anneau α-β du module perf-models, avec 1,5 % de bruit à graine fixe ; **pas des mesures** |

```bash
PYTHON=/chemin/vers/python ./verify.sh                       # partie A : lint + analyseur
python3 parse_nccl_tests.py fixtures/all_reduce_synthetic_degraded.txt --expect-busbw 48   # exit 1 : plateau à 55 %
# partie B (vrai cluster) :
export NCCL_TESTS_DIR=/chemin/nccl-tests MIN_BUSBW_GBS=45        # plateau attendu (pour l'analyseur)
sbatch run_all_reduce.sbatch                                     # options nccl-tests en plus : sbatch run_all_reduce.sbatch -a 3
python3 parse_nccl_tests.py nccl-allreduce-<jobid>.out --expect-busbw "$MIN_BUSBW_GBS"
```

Le format du tableau a été relu dans `nccl-tests/src/util.cu` (2026-10-24) ; il change avec les options (`-I`, `-U`). L'analyseur ignore les lignes qu'il ne reconnaît pas. La variable `NCCL_TESTS_MIN_BW` (échec si le débit de bus moyen est inférieur à 0,9 fois sa valeur) vient de `src/common.cu` ; ce « moyen » est la moyenne de toutes les tailles du balayage (« Avg bus bandwidth », 17 Go/s pour un plateau de 48 sur les tables synthétiques) : le script la lit dans `MIN_AVG_BUSBW_GBS` (moyenne d'un essai antérieur du même balayage), pas dans le plateau attendu `MIN_BUSBW_GBS`, que seul l'analyseur utilise. `NCCL_TESTS_SPLIT` affiche un seul tableau (le débit d'un groupe, moyenné sur les rangs ; `-a 3` retient le rang le plus lent), pas un tableau par groupe.

Hypothèses du script : `srun --mpi=pmix` (réglable par `SRUN_MPI`), `nccl-tests` compilé avec `MPI=1`, 8 GPU par nœud. À adapter à votre site.
