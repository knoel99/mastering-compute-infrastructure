# Lab 3.2 — MPI : collectives, anneau fait main, interblocages, halo

Open MPI + mpi4py + numpy, 2 à 8 rangs sur une seule machine (mémoire partagée : ce n'est **pas** un réseau). Testé avec Open MPI 4.1.6
(paquet Ubuntu 24.04 `openmpi-bin libopenmpi-dev`) et mpi4py 4.1.2, le 2026-10-25, sur une VM Linux à 4 vCPU.

```bash
sudo apt-get install -y openmpi-bin libopenmpi-dev python3-venv
python3 -m venv ~/pp-venv && . ~/pp-venv/bin/activate     # Ubuntu 24.04 refuse pip hors d'un environnement virtuel (PEP 668)
python3 -m pip install mpi4py numpy
bash verify.sh        # ~45 s ; PYTHON=/chemin/vers/python bash verify.sh si besoin
```

En root dans un conteneur, `verify.sh` ajoute `--allow-run-as-root` ; dans tous les cas il ajoute `--oversubscribe` (plus de rangs que de cœurs).

| Fichier | Rôle |
|---|---|
| `collectives_tour.py` | un appel de chaque collective sur 4 rangs, avec la disposition des données affichée ; vérifie `allreduce = reduce_scatter + allgather` |
| `ringlib.py` | all-reduce en anneau (reduce-scatter puis all-gather) et par doublement récursif, écrits avec `Sendrecv` ; un compteur de messages et d'octets émis |
| `check_allreduce.py` | compare avec `MPI_Allreduce` (entiers : égalité exacte ; flottants : égalité à l'arrondi) et vérifie les formules par comptage : 2(p−1) messages et 2(p−1)/p·n octets pour l'anneau, log2 p messages et log2 p·n octets pour le doublement récursif |
| `deadlock_demo.py` | deux rangs s'échangent un tampon en `Send`/`Recv`, `Ssend`, `Sendrecv` ou `Isend` ; `verify.sh` lance chaque cas sous `timeout` (code 124 = bloqué) |
| `halo_stencil.py` | schéma à trois points en 1D avec cellules fantômes, version bloquante et version avec recouvrement ; doit égaler le calcul séquentiel **bit à bit** ; octets émis comptés |
| `bench_allreduce.py`, `model_vs_measure.py` | mesure ping-pong, échange simultané, anneau, doublement récursif, `MPI_Allreduce` ; ajuste α et B (erreur relative) puis compare au modèle |
| `exercises/` | scripts des corrigés : `ring_shift.py` (anneau bogué et corrections), `fp_assoc.py`, `crossover.py`, `hier_allreduce.py` |

## Ce que `verify.sh` affirme, et ce qu'il ne dit pas

* **Affirmé** : résultats exacts, compteurs égaux aux formules (p = 2, 3, 4, 5, 8), halo identique au séquentiel, `Ssend` croisé bloque,
  `Sendrecv`/`Isend`/ordre pair-impair terminent. Les temps ne sont jamais jugés.
* **Spécifique à Open MPI 4.1.6** : un `Send` croisé de 2 048 octets passe et un de 1 048 576 octets bloque (limite *eager* de 4 096 octets
  du transport mémoire partagé `vader`, valeur lue avec `ompi_info`). Le standard MPI n'impose rien ici ; `verify.sh` n'affirme ce
  comportement que si `mpirun --version` annonce Open MPI, et se contente de l'afficher ailleurs.
* **Non expliqué** : le modèle α-β ajusté sur le ping-pong sous-estime l'anneau écrit en Python d'un facteur de l'ordre de 4 ; l'ajout du coût de
  la boucle Python (mesuré avec une communication factice) ramène l'écart à environ 1,2 à 1,4 sur trois exécutions ; il reste un facteur
  2 à 9 sur le doublement récursif des gros messages, que ce lab n'explique pas (hypothèses : copie en deux temps du transport mémoire
  partagé, contention sur le bus mémoire).

## Pour aller plus loin

Forcez l'algorithme de `MPI_Allreduce` : `mpirun --mca coll_tuned_use_dynamic_rules 1 --mca coll_tuned_allreduce_algorithm 4 ...`
(valeurs lues avec `ompi_info --param coll tuned --level 9` : 3 doublement récursif, 4 anneau, 6 Rabenseifner) et répétez 10 fois :
l'écart entre exécutions est du même ordre que l'écart entre algorithmes. Sur un cluster, remplacez les rangs locaux par deux nœuds et
relisez le modèle à deux niveaux (chapitre 4).
