<!-- derived from module front matter. build_site overwrites this file. -->
## Glossaire

### epoch

Un epoch est un passage complet du jeu d'entraînement dans le modèle.

### batch

Un batch est le paquet d'exemples traité avant une mise à jour des poids.

### transfer learning

Le transfer learning réutilise les poids d'un modèle déjà entraîné pour une tâche nouvelle.

### kernel CUDA

Un kernel CUDA est la fonction lancée par l'hôte et exécutée en parallèle sur le GPU.

### warp

Un warp est le groupe de 32 threads qu'un GPU NVIDIA exécute ensemble.

### SM

Un SM est le multiprocesseur du GPU qui reçoit les blocs et exécute leurs warps.

### coalescence

La coalescence fusionne les lectures voisines d'un warp en peu de transactions mémoire.

### HBM3

HBM3 est une mémoire empilée à haute bande passante, utilisée comme mémoire du GPU.

### NVLink

NVLink est le lien NVIDIA qui relie un CPU Grace et un GPU Hopper, ou bien des GPU entre eux.

### NCCL

NCCL est la bibliothèque NVIDIA qui exécute les collectives entre plusieurs GPU.

### all-reduce

Un all-reduce additionne les tableaux de tous les ranks et renvoie le résultat à chacun.

### rank

Un rank est l'entier qui identifie un processus dans un groupe de communication.

### DDP/FSDP

DDP garde une copie entière du modèle sur chaque rank, et FSDP répartit les paramètres entre les ranks.

### Spack

Spack construit un logiciel scientifique et ses dépendances dans un environnement isolé.

### Slurm

Slurm choisit des nœuds libres et y démarre le job.

### TPE

Anticipé. TPE choisit le prochain essai à partir d'un modèle des essais déjà observés.

### Hyperband/ASHA

Anticipé. Hyperband et ASHA arrêtent tôt les essais faibles et reportent le budget sur les essais qui restent.
