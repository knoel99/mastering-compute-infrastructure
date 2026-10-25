# Lab 3.3 — Jacobi 2D : décomposition de domaine et étude de passage à l'échelle

Un solveur de Laplace par itération de Jacobi, en C avec MPI (décomposition 1D ou 2D, échange de halos par `Isend`/`Irecv`,
recouvrement optionnel) et OpenMP (hybride), puis une étude de passage à l'échelle, fort et faible, avec intervalles de confiance.
Testé avec Open MPI 4.1.6 et GCC 13.3 le 2026-10-25, sur une VM Linux à 4 vCPU (Intel Xeon à 2,8 GHz, un seul domaine NUMA).

```bash
sudo apt-get install -y openmpi-bin libopenmpi-dev python3-venv
python3 -m venv ~/pp-venv && . ~/pp-venv/bin/activate     # Ubuntu 24.04 refuse pip hors d'un environnement virtuel (PEP 668)
python3 -m pip install mpi4py numpy
bash verify.sh                                     # ~1 min ; PYTHON=... si besoin
mpicc -O2 -fopenmp -o jacobi jacobi.c -lm
python3 run_study.py --jacobi ./jacobi --out study.json --reps 9     # ~1,5 min ; l'étude complète
python3 analyze_study.py study.json --svg speedup.svg
python3 hybrid_compare.py --jacobi ./jacobi --reps 9 --misbound     # rangs x threads, bien ou mal liés
```

| Fichier | Rôle |
|---|---|
| `jacobi.c` | le solveur ; sortie sur une ligne `clé=valeur` : temps (max sur les rangs), compteurs de messages et d'octets, empreinte du champ, résidus |
| `check_jacobi.py` | assertions structurelles de `verify.sh` |
| `run_study.py`, `analyze_study.py` | plan d'expérience (ordre aléatoire à graine fixe, répétitions), médiane + intervalle bootstrap, gain, efficacité, Karp-Flatt (fonctions de `scaling_math.py` ; le projet 2 vous les fera réécrire), décomposition du temps, tracé SVG |
| `scaling_math.py`, `test_scaling_math.py` | `summarize`, `speedup`, `efficiency`, `karp_flatt` et leurs tests (lancés par `verify.sh`, sans pytest) |
| `hybrid_compare.py` | mêmes cœurs, répartitions rangs × threads, avec ou sans liaison correcte |
| `compare_variants.py` | plain, recouvrement, 2D, 2D+recouvrement, résidu à chaque balayage : médiane et minimum, ordre aléatoire ; vérifie que le champ ne change pas |
| `repro_sum.py`, `mpiio_demo.py` | sommes non associatives (naïve contre à ordre fixe) et écriture MPI-IO collective indépendante du nombre de rangs |
| `slurm_launch.sh`, `slurm_hybrid.sbatch` | **partie D, facultative** : lancement hybride sous un vrai Slurm (voir ci-dessous) |
| `exercises/` | `halo_sizing.py`, `scaling_table.py`, `slurm_hybrid_2nodes.sbatch` (corrigés des exercices) |

## Ce que `verify.sh` affirme

* Le champ final est **identique bit à bit** (même empreinte) pour 1 à 4 rangs, en 1D et en 2D, avec et sans recouvrement, avec 2 threads
  par rang, avec résidu tous les 5 balayages : empreinte = somme modulo 2^64 des motifs binaires des cellules (indépendante de l'ordre).
* Le résidu en norme max est identique partout ; celui en norme 2 ne l'est qu'à l'arrondi (somme flottante réduite par `MPI_Allreduce`).
* Les compteurs de halo valent exactement `16·((py−1)·nx + (px−1)·ny)` octets et `2·((py−1)·px + (px−1)·py)` messages par balayage,
  jusqu'à 9 rangs (sur-souscrits : on compte, on ne chronomètre pas).
* Une étude miniature (2 répétitions, grille 384×384) traverse tout le pipeline ; le SVG produit est bien formé et sans couleur codée en dur.
* Les sommes à ordre fixe donnent le même résultat pour p = 1 à 5 ; le fichier MPI-IO a la même empreinte SHA-256 pour p = 1 à 5.
* **Aucun temps n'est jugé.** `analyze_study.py` imprime des temps réels, qui varient d'une exécution à l'autre sur une VM partagée.

## Partie D — lancement sous Slurm (hors `verify.sh` par défaut)

`RUN_SLURM=1 bash verify.sh` (ou `bash slurm_launch.sh`) démarre le Slurm mono-nœud du module 5 s'il n'y en a pas déjà un (et ne l'arrête que
s'il l'a démarré), lance `slurm_hybrid.sbatch` (2 tâches × 2 CPU) avec `mpirun` dans l'allocation, vérifie les liaisons rapportées et que l'empreinte
du champ égale celle d'un run à un rang. Exécuté avec succès le 2026-10-25 avec Slurm 23.11.4 ; il demande les droits root et plusieurs
paquets : il n'est donc pas lancé par défaut. Deux constats de ce script : le lancement direct par `srun` est **refusé** par l'Open MPI du paquet Ubuntu
(« direct launched using srun, but OMPI was not built with SLURM's PMI support »), et le Slurm du bac à sable utilise `task/none`, donc Slurm ne lie
aucun processus à un cœur : c'est `mpirun --bind-to core` qui le fait.
`exercises/slurm_hybrid_2nodes.sbatch` demande deux nœuds : il est seulement linté (`bash -n`, `shellcheck`), jamais exécuté.
