---
title: "Plans détaillés des modules"
subtitle: "Acquis visés, chapitres, labs et sources à lire pour chacun des modules du parcours"
description: "Plan de chacun des 16 modules : ce qui est rédigé est signalé, le reste est un plan prêt à être rédigé."
---

## Comment lire cette page {#lecture}

Cette page donne le plan de **chaque module du parcours**, qu'il soit déjà rédigé ou non. Un module rédigé a sa page complète (fiche, plan de séances, chapitres, labs vérifiés, exercices corrigés) ; un module marqué « plan » n'a pas encore son cours : ses chapitres, ses labs prévus et ses sources à lire sont donnés pour que vous puissiez commencer à travailler dessus avec les références officielles en attendant.

Les sources citées dans les rubriques « Sources à lire et faits à vérifier » ne sont **pas** des faits établis : ce sont les références sur lesquelles le futur cours devra s'appuyer, et les affirmations chiffrées qu'il faudra relire à la source avant de les écrire.


## Phase 0 — Fondations : machines et performance {#phase0}

### Module 01 — Linux, systèmes et diagnostic de performance (rédigé, 24 h) {#linux-systems}

Le socle commun à tout ce qui suit : processus, mémoire, cgroups, NUMA, systemd, réseau et stockage vus par un exploitant de cluster.

**Cours complet :** [Linux, systèmes et diagnostic de performance](courses/linux-systems/index.html).

**Ce que vous saurez vérifier :**

-   Cartographier une machine (CPU, NUMA, PCIe, NIC, GPU) et dire quel chemin les données empruntent
-   Expliquer cgroups v2 et namespaces, et ce que Slurm et Kubernetes en font
-   Mener un diagnostic de nœud lent avec la méthode USE et les outils standard
-   Écrire un script d'exploitation Bash/Python robuste (codes retour, idempotence, journalisation)

**Chapitres :**

1.  Modèle d'exécution Linux : processus, signaux, ordonnanceur, mémoire virtuelle, page cache, OOM killer
2.  cgroups v2 et namespaces : hiérarchie, contrôleurs cpu/memory/io, ce que font conteneurs et ordonnanceurs
3.  Topologie matérielle et NUMA : lscpu, hwloc, numactl, affinités, topologie PCIe, nvidia-smi topo
4.  Mesurer avant d'optimiser : méthode USE, perf, vmstat/iostat/sar, flamegraphs, introduction à bpftrace
5.  systemd, journald, limites (memlock, nofile), hugepages, paramètres noyau utiles aux nœuds de calcul
6.  Réseau Linux : ip, ss, ethtool, MTU, bonding, tc ; premiers pas RDMA (renvoi au module réseau)
7.  Stockage Linux : blocs, NVMe, xfs/ext4, fio, page cache, O_DIRECT
8.  Pannes matérielles vues du système : dmesg, EDAC/ECC, SMART, ipmitool/Redfish ; scripts d'exploitation robustes

**Labs :**

-   **Cartographier une machine** (bac à sable, sans GPU) : Script qui produit un rapport JSON (CPU, NUMA, mémoire, disques, interfaces) à partir de lscpu/numactl/sysfs ; tests sur la sortie.
-   **cgroups v2 à la main** (bac à sable, sans GPU) : Créer un cgroup, limiter mémoire/CPU, provoquer un OOM contrôlé. Si le bac à sable ne permet pas l'écriture cgroup, basculer le lab en 'cluster' et le dire.
-   **fio et page cache** (bac à sable, sans GPU) : Mesurer lecture/écriture avec et sans page cache, comprendre O_DIRECT ; script qui compare et trace.

**Sources à lire et faits à vérifier :**

-   Brendan Gregg, méthode USE et Systems Performance (2e éd., 2020)
-   Documentation noyau cgroup v2 (kernel.org)
-   Comportement du OOM killer et de memory.max

**Projets qui s'appuient sur ce module :** Projet 1.

### Module 02 — Architecture matérielle et modèles de performance (rédigé, 24 h) {#perf-models}

Prédire avant de mesurer : hiérarchie mémoire, roofline, Amdahl/Gustafson, modèle α-β des communications et MFU.

**Cours complet :** [Architecture matérielle et modèles de performance](courses/perf-models/index.html).

**Ce que vous saurez vérifier :**

-   Calculer l'intensité arithmétique d'un noyau et le situer sur un roofline
-   Prédire le gain maximal d'une parallélisation (Amdahl, Gustafson) et le comparer à une mesure
-   Estimer le temps d'un all-reduce avec le modèle α-β puis le valider par une mesure
-   Calculer le MFU d'un entraînement à partir de ses FLOP et de son temps par pas

**Chapitres :**

1.  Du transistor au nœud : cœurs, SIMD, hiérarchie mémoire, bande passante, latence
2.  Le GPU vu comme machine à débit : SM, warps, HBM, tenseurs ; comparaison CPU/GPU
3.  Mesurer proprement : benchmarks, variance, warm-up, minimum vs médiane, STREAM, GEMM
4.  Le modèle roofline : intensité arithmétique, bornes mémoire et calcul, lecture de profils
5.  Passage à l'échelle : loi d'Amdahl, loi de Gustafson, scalabilité forte et faible, efficacité parallèle
6.  Le modèle de communication α-β (Hockney) et les collectives : arbre, anneau, bande passante optimale
7.  FLOP d'un transformeur, MFU et HFU : 6ND, attention, coût mémoire des paramètres/optimiseur/activations
8.  Études de passage à l'échelle reproductibles : plan d'expérience, tracé, rapport honnête

**Labs :**

-   **STREAM et GEMM : bandes passantes et pic** (bac à sable, sans GPU) : Mesurer la bande passante mémoire et le débit GEMM de la machine (NumPy), tracer son roofline, comparer au pic théorique du CPU.
-   **α-β : prédire puis mesurer** (bac à sable, sans GPU) : Avec torch.distributed gloo sur 4 processus : mesurer des all-reduce de tailles variées, ajuster α et β par régression, comparer la prédiction du modèle en anneau.
-   **Calculateur de MFU** (bac à sable, sans GPU) : Outil Python testé qui calcule FLOP/pas d'un transformeur donné et MFU à partir d'un temps mesuré ; cas de test tirés de valeurs publiées et citées.

**Sources à lire et faits à vérifier :**

-   Williams, Waterman, Patterson (2009), roofline, CACM
-   Hockney (1994) et Thakur et al. (2005) pour les collectives
-   Chowdhery et al. (PaLM, 2022) pour la définition du MFU
-   FLOP de l'attention : formules de Kaplan et al. 2020 / Megatron-LM

**Projets qui s'appuient sur ce module :** Projet 2, Projet 6.


## Phase 1 — Calcul parallèle et GPU {#phase1}

### Module 03 — Programmation parallèle : OpenMP, MPI et études de passage à l'échelle (plan, 30 h) {#parallel-programming}

Le noyau commun de tous les masters HPC : mémoire partagée, passage de messages, collectives, et la discipline d'une étude de scalabilité.

**Prérequis :** module 2 (Architecture matérielle et modèles de performance).

**Ce que vous saurez vérifier :**

-   Paralléliser une boucle avec OpenMP en justifiant partage, réduction et ordonnancement
-   Écrire un programme MPI avec communications point-à-point et collectives, sans interblocage
-   Mener une étude de scalabilité forte et faible et expliquer l'écart au modèle
-   Relier les collectives MPI à ce que NCCL fait pour l'entraînement

**Chapitres :**

1.  Parallélisme : tâches, données, pipeline ; mémoire partagée contre mémoire distribuée
2.  OpenMP : régions parallèles, partage, réductions, ordonnancement, faux partage, tâches
3.  MPI, les bases : rangs, communicateurs, point-à-point bloquant et non bloquant, interblocages
4.  MPI, les collectives : broadcast, reduce, allreduce, alltoall ; algorithmes et coûts
5.  Décomposition de domaine, halos et recouvrement calcul/communication
6.  E/S parallèles et reproductibilité numérique : MPI-IO, sommes non associatives, graines
7.  Hybride MPI+OpenMP, placement et binding ; lancement sous Slurm
8.  Étudier la scalabilité : plan d'expérience, efficacité, goulots, rapport

**Labs :**

-   **OpenMP : réduction et faux partage** (bac à sable, sans GPU) : Programme C avec OpenMP : somme, faux partage, effet du schedule ; mesures et comparaison au modèle.
-   **MPI : anneau, halo et all-reduce** (bac à sable, sans GPU) : Implémenter un all-reduce en anneau à la main avec MPI (OpenMPI/mpi4py dans le bac à sable, 4 rangs locaux), comparer à MPI_Allreduce.
-   **Jacobi 2D : étude de scalabilité** (bac à sable, sans GPU) : Solveur Jacobi avec décomposition de domaine ; scalabilité forte/faible sur les cœurs disponibles ; tracé et analyse.

**Sources à lire et faits à vérifier :**

-   Norme MPI (mpi-forum.org), spécification OpenMP (openmp.org)
-   Patarasuk & Yuan (2009), all-reduce optimal en bande passante
-   Cours de référence cités par les masters (EPCC, Berkeley CS267)

**Projets qui s'appuient sur ce module :** Projet 2.

### Module 04 — Programmation GPU : CUDA, Triton et profilage (plan, 30 h) {#gpu-programming}

Comprendre un noyau GPU assez pour juger un profil : hiérarchie mémoire, occupation, coalescence, streams, puis Triton et Nsight.

**Prérequis :** module 2 (Architecture matérielle et modèles de performance).

**Ce que vous saurez vérifier :**

-   Écrire un noyau CUDA (Numba) avec mémoire partagée et le comparer à une version vectorisée
-   Expliquer la coalescence, l'occupation et la divergence de warps sur un exemple chiffré
-   Lire un profil Nsight/PyTorch Profiler et nommer le goulot (calcul, mémoire, lancement)
-   Expliquer ce qu'apporte FlashAttention, la fusion de noyaux et la précision mixte

**Chapitres :**

1.  Le modèle d'exécution CUDA : grille, blocs, warps, SM ; synchronisation
2.  Hiérarchie mémoire GPU : globale, partagée, registres, constantes ; coalescence et conflits de bancs
3.  Écrire des noyaux : réduction, produit matriciel par tuiles, scan ; erreurs classiques
4.  Streams, événements, copies asynchrones, mémoire épinglée, recouvrement transfert/calcul
5.  Triton : programmer par blocs, auto-réglage, quand préférer Triton à CUDA
6.  Précision numérique : FP32, TF32, BF16, FP16, FP8 ; sommes, mise à l'échelle de perte, déterminisme
7.  Profiler : Nsight Systems/Compute, PyTorch Profiler, métriques clés, lecture d'une trace
8.  Techniques d'accélération : fusion, FlashAttention, torch.compile, CUDA graphs, quand elles paient

**Labs :**

-   **Noyaux CUDA dans le simulateur Numba** (bac à sable, sans GPU) : Noyaux Numba (réduction, matmul par tuiles) exécutés avec NUMBA_ENABLE_CUDASIM=1 ; tests de justesse ; version GPU réelle documentée mais non exécutée.
-   **Triton en mode interpréteur** (bac à sable, sans GPU) : Noyau Triton d'addition fusionnée et softmax exécutés avec TRITON_INTERPRET=1 si l'installation CPU est possible ; sinon lab 'gpu' documenté et linté.
-   **Lire une trace de profil** (bac à sable, sans GPU) : Profil PyTorch Profiler sur CPU d'un petit transformeur ; exporter la trace Chrome, identifier les opérateurs dominants ; transposition au profil GPU expliquée.

**Sources à lire et faits à vérifier :**

-   Documentation CUDA C++ Programming Guide (NVIDIA)
-   Dao et al. (2022) FlashAttention
-   Tillet et al. (2019) Triton
-   Documentation Numba CUDA simulator et Triton interpreter : vérifier la disponibilité sur CPU

**Projets qui s'appuient sur ce module :** Projet 2.


## Phase 2 — Exploiter un cluster {#phase2}

### Module 05 — Slurm et exploitation d'un cluster HPC (rédigé, 32 h) {#slurm}

L'ordonnanceur de référence du calcul scientifique et de l'entraînement : partitions, QOS, fairshare, GRES, préemption, comptabilité, santé des nœuds.

**Prérequis :** module 1 (Linux, systèmes et diagnostic de performance).

**Cours complet :** [Slurm et exploitation d'un cluster HPC](courses/slurm/index.html).

**Ce que vous saurez vérifier :**

-   Écrire et soumettre des jobs (batch, tableaux, dépendances, interactifs) avec ressources GPU
-   Configurer partitions, QOS, fairshare et préemption pour une politique donnée
-   Lire sacct/sreport et expliquer l'utilisation et les files d'attente d'un cluster
-   Diagnostiquer un nœud drainé et un job en attente (raisons Slurm)

**Chapitres :**

1.  Architecture : slurmctld, slurmd, slurmdbd, munge ; flux de vie d'un job
2.  Soumettre : sbatch, srun, salloc ; ressources, GRES/GPU, tableaux, dépendances, scripts robustes
3.  Politique : partitions, QOS, associations, fairshare, priorité multifactorielle, backfill
4.  Préemption, réservations, limites, gang scheduling, jobs de grande taille et fragmentation
5.  GPU et topologie : gres.conf, cgroups, MIG, binding, topology.conf, placement sensible au réseau
6.  Comptabilité et reporting : sacct, sreport, sshare, tableaux de bord d'utilisation
7.  Santé des nœuds : drain, prolog/epilog, NHC, burn-in, remise en service
8.  Conteneurs et environnements : pyxis/enroot, apptainer, modules/Spack ; Slurm sur Kubernetes (aperçu)

**Labs :**

-   **Un Slurm réel dans le bac à sable** (bac à sable, sans GPU) : Installer munge, MariaDB, slurmdbd et slurmctld/slurmd sur une seule machine (apt, Slurm 23.11), créer comptes et QOS, soumettre des jobs. Constat de départ : sans base de comptabilité, les jobs restent en InvalidAccount ; documenter la solution (slurmdbd) et fournir un script d'installation reproductible.
-   **Fairshare, QOS et préemption** (bac à sable, sans GPU) : Deux comptes concurrents, un QOS préemptif ; observer sshare/sprio/squeue ; critères chiffrés.
-   **Drain, prolog et vérification de santé** (bac à sable, sans GPU) : Script de vérification de nœud appelé en prolog/epilog ; drainer automatiquement sur échec ; tests.

**Sources à lire et faits à vérifier :**

-   Documentation officielle Slurm (slurm.schedmd.com) : slurm.conf, gres.conf, cgroup.conf, sacctmgr, priority multifactor
-   Yoo, Jette, Grondona (2003)
-   Version testée et date à indiquer ; ne pas écrire 'dernière version' sans lecture de la source officielle

**Projets qui s'appuient sur ce module :** Projet 1, Projet 6.

### Module 06 — Provisioning, images et santé des nœuds GPU (plan, 24 h) {#provisioning}

Du châssis nu au nœud en production : installation, images, configuration, pilotes, tests de recette et supervision matérielle.

**Prérequis :** module 1 (Linux, systèmes et diagnostic de performance).

**Ce que vous saurez vérifier :**

-   Décrire la chaîne PXE → image → configuration → enregistrement dans l'ordonnanceur
-   Écrire des rôles Ansible idempotents et des modules Terraform pour un cluster
-   Valider un nœud GPU avant mise en service (pilote, DCGM diag, burn-in, bande passante)
-   Concevoir une procédure de remplacement et de mise à jour sans interrompre la production

**Chapitres :**

1.  Cycle de vie d'un nœud : recette, installation, exploitation, retrait
2.  Démarrage réseau et images : PXE/iPXE, outils de provisioning bare-metal (MAAS, Warewulf, BCM : forces et limites)
3.  Gestion de configuration : Ansible, idempotence, inventaires, secrets
4.  Terraform pour l'infrastructure : état, modules, environnements, dérive
5.  La pile GPU : pilote, CUDA, Fabric Manager, DCGM, conteneurs GPU ; compatibilités et pièges de versions
6.  Recette et burn-in : DCGM diagnostics, gpu-burn, nccl-tests, tests mémoire/PCIe/NVLink
7.  Mises à jour et pannes : rolling updates, firmware, gestion des RMA, traçabilité
8.  BMC, Redfish, IPMI et supervision hors bande

**Labs :**

-   **Un rôle Ansible de nœud de calcul** (bac à sable, sans GPU) : Rôle Ansible (muni de molecule ou ansible-playbook --check) qui configure limites, sysctl, services ; tests d'idempotence en local connection.
-   **Terraform : une flotte décrite en code** (bac à sable, sans GPU) : Module Terraform avec provider local/null et sorties ; terraform validate/plan en local ; gestion de la dérive expliquée.
-   **Recette d'un nœud GPU** (GPU requis) : Script de recette qui enchaîne nvidia-smi, DCGM diag, gpu-burn, nccl-tests ; lint et simulation des sorties pour le test ; exécution réelle documentée (GPU requis).

**Sources à lire et faits à vérifier :**

-   Documentation NVIDIA DCGM (dcgmi diag) et Fabric Manager
-   Documentation Ansible et Terraform
-   Capacités actuelles des outils de provisioning HPC (vérifier sur sites officiels)

**Projets qui s'appuient sur ce module :** Projet 1, Projet 6.

### Module 07 — Réseaux haute performance : InfiniBand, RoCE et NCCL (plan, 28 h) {#networking}

Pourquoi un entraînement multi-nœuds est limité par le réseau : topologies, RDMA, NVLink, NCCL, mesures et diagnostic.

**Prérequis :** module 1 (Linux, systèmes et diagnostic de performance), module 2 (Architecture matérielle et modèles de performance).

**Ce que vous saurez vérifier :**

-   Comparer InfiniBand et RoCE (contrôle de congestion, perte, configuration) et choisir selon le besoin
-   Dimensionner une topologie fat-tree et un taux de sur-souscription
-   Expliquer comment NCCL choisit anneau/arbre et lire ses journaux (NCCL_DEBUG)
-   Mesurer bande passante et latence (ib_write_bw, nccl-tests) et interpréter un écart

**Chapitres :**

1.  Rappels réseau : latence, bande passante, débit utile, MTU, contrôle de flux et de congestion
2.  RDMA et verbs : pourquoi contourner le noyau ; GPUDirect RDMA et GPUDirect Storage
3.  InfiniBand : sous-réseau, SM, routage, adaptive routing, NDR/XDR ; opérations quotidiennes
4.  Ethernet pour l'IA : RoCE v2, PFC, ECN, DCQCN, problèmes de perte ; comparaison honnête avec IB
5.  Topologies : fat-tree, rail-optimized, dragonfly ; sur-souscription ; placement sensible à la topologie
6.  Dans le nœud : NVLink, NVSwitch, PCIe, affinité GPU-NIC
7.  NCCL : algorithmes (anneau, arbre, CollNet/SHARP), protocoles, variables d'environnement utiles, journaux
8.  Mesure et diagnostic : nccl-tests, perftest, hangs, liens dégradés, erreurs silencieuses

**Labs :**

-   **Dimensionner un fat-tree** (bac à sable, sans GPU) : Calculateur Python testé : nombre de commutateurs/câbles pour N GPU, sur-souscription, bande passante de bissection ; comparaison à des configurations publiées et citées.
-   **Lire un journal NCCL** (bac à sable, sans GPU) : Analyseur de logs NCCL_DEBUG (jeux de logs d'exemple fournis et étiquetés comme synthétiques ou publics) qui extrait topologie, algorithme, interfaces ; tests.
-   **nccl-tests sur un vrai cluster** (GPU requis) : Procédure et script pour exécuter nccl-tests (all_reduce_perf) sous Slurm et interpréter busbw ; lint ; exécution réelle documentée.

**Sources à lire et faits à vérifier :**

-   Documentation NCCL (docs.nvidia.com/deeplearning/nccl) et dépôt nccl-tests
-   Guides InfiniBand/RoCE de NVIDIA (Mellanox) ; DCQCN (Zhu et al. 2015)
-   Chiffres de bande passante par génération (NVLink, NDR) : citer les fiches constructeur

**Projets qui s'appuient sur ce module :** Projet 2, Projet 6.

### Module 08 — Stockage et E/S pour l'entraînement (plan, 24 h) {#storage}

Nourrir les GPU et sauvegarder sans les arrêter : systèmes de fichiers parallèles, objet, cache, chargeurs de données et E/S de checkpoint.

**Prérequis :** module 1 (Linux, systèmes et diagnostic de performance).

**Ce que vous saurez vérifier :**

-   Choisir entre système de fichiers parallèle, NFS et stockage objet pour un usage donné
-   Dimensionner le débit nécessaire pour un entraînement et pour un checkpoint
-   Diagnostiquer un entraînement limité par ses données (profilage du chargeur)
-   Concevoir un cache de données à plusieurs niveaux

**Chapitres :**

1.  Besoins d'E/S d'un entraînement : lecture de jeu de données, checkpoints, journaux, artefacts
2.  Systèmes de fichiers parallèles : Lustre, GPFS/Storage Scale, BeeGFS, WEKA : architecture, métadonnées, striping
3.  NFS, objet (S3), FUSE et caches : cohérence, latence, coût ; comparaisons honnêtes
4.  Formats de données pour l'entraînement : shards, WebDataset, Parquet, Arrow, mmap, tokens pré-packés
5.  Chargeurs de données : workers, prefetch, pinned memory, goulots CPU ; mesurer avec un profileur
6.  E/S de checkpoint : débit, atomicité, asynchrone, parallèle ; coût d'un checkpoint
7.  Mise en cache : NVMe local, cache distribué, pré-chauffage ; invalidation ; GPUDirect Storage
8.  Capacité, durée de vie des données, sauvegardes, quotas, coût au To

**Labs :**

-   **Démasquer un chargeur de données lent** (bac à sable, sans GPU) : Boucle PyTorch avec Dataset synthétique ; varier workers/prefetch ; mesurer débit et temps d'attente GPU simulé ; tableau de décision.
-   **Shards et lecture séquentielle** (bac à sable, sans GPU) : Convertir un jeu en shards tar/Parquet ; comparer lecture aléatoire et séquentielle avec fio/Python ; chiffrer l'écart.
-   **Coût d'un checkpoint** (bac à sable, sans GPU) : Écrire des checkpoints de tailles variées (sync/async/fsync) et modéliser débit et temps de blocage.

**Sources à lire et faits à vérifier :**

-   Documentation Lustre (lustre.org), BeeGFS, GPFS ; Mohan et al. (CheckFreq, FAST 2021)
-   Chiffres de débit par fournisseur : à citer ou ordre de grandeur
-   Documentation PyTorch DataLoader et WebDataset

**Projets qui s'appuient sur ce module :** Projet 3, Projet 6.


## Phase 3 — Systèmes d'entraînement distribué {#phase3}

### Module 09 — Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline (plan, 36 h) {#distributed-training}

Le cœur du métier côté entraînement : choisir un parallélisme, estimer mémoire et communication, atteindre un bon MFU et déboguer l'instabilité numérique.

**Prérequis :** module 2 (Architecture matérielle et modèles de performance), module 4 (Programmation GPU : CUDA, Triton et profilage), module 7 (Réseaux haute performance : InfiniBand, RoCE et NCCL).

**Ce que vous saurez vérifier :**

-   Choisir DDP, FSDP, tensor, pipeline ou expert parallelism pour un modèle et un cluster donnés, chiffres à l'appui
-   Estimer la mémoire par GPU (paramètres, gradients, optimiseur, activations) et la réduire (ZeRO, checkpointing d'activations)
-   Lancer un job multi-processus avec torchrun et déboguer un deadlock de collective
-   Distinguer un bug de distribution d'une instabilité numérique et rendre un run reproductible

**Chapitres :**

1.  Panorama : données, modèle, pipeline, experts, séquence ; la grille de parallélismes 3D/4D
2.  DDP : buckets, recouvrement, synchronisation, torchrun, rendezvous ; erreurs classiques
3.  Mémoire d'un entraînement : paramètres, gradients, états d'optimiseur, activations ; ZeRO 1/2/3 et FSDP
4.  Parallélisme tensoriel et de séquence ; parallélisme pipeline et bulles ; parallélisme d'experts
5.  Choisir et dimensionner : placer les dimensions sur la topologie, règle du pouce, exemples chiffrés
6.  MFU en pratique : mesurer, expliquer l'écart, leviers (taille de lot, recouvrement, fusion, précision)
7.  Numérique et déterminisme : pics de perte, normes de gradient, NaN, reproductibilité bit-à-bit et ses limites
8.  Déboguer le distribué : deadlocks, hangs, désynchronisation, divergence entre un run mono-GPU et distribué ; outils
9.  Écosystème : Megatron-LM, DeepSpeed, TorchTitan, Accelerate/Lightning ; comment lire leurs configurations

**Labs :**

-   **DDP à quatre processus sur CPU** (bac à sable, sans GPU) : Entraînement DDP avec torchrun --nproc_per_node=4 backend gloo ; vérifier l'équivalence avec un run mono-processus à la tolérance près ; mesurer le coût de communication.
-   **FSDP : mesurer la mémoire par rang** (bac à sable, sans GPU) : FSDP2/fully_shard sur CPU gloo ; comparer à DDP ; calculer la mémoire attendue et la comparer à la mesure (par tailles de tenseurs).
-   **Reproduire et diagnostiquer un hang** (bac à sable, sans GPU) : Script où un rang saute une collective ; utiliser le watchdog/timeout et les traces pour localiser ; procédure d'enquête reproductible.

**Sources à lire et faits à vérifier :**

-   Narayanan et al. (2021) Megatron-LM
-   Rajbhandari et al. (2020) ZeRO ; Zhao et al. (2023) PyTorch FSDP
-   Documentation PyTorch : torchrun, DDP, fully_shard (FSDP2), DTensor
-   Hugging Face Ultra-Scale Playbook ; Austin et al. How to Scale Your Model
-   Llama 3 (Dubey et al. 2024) : MFU et configuration de parallélisme, à citer depuis le papier

**Projets qui s'appuient sur ce module :** Projet 2, Projet 3, Projet 6.

### Module 10 — Pannes, checkpointing et reprise automatique (rédigé, 28 h) {#fault-tolerance}

À grande échelle les pannes sont la norme : modèle de panne, checkpoints rapides et corrects, entraînement élastique, reprise sans intervention humaine.

**Prérequis :** module 9 (Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline), module 8 (Stockage et E/S pour l'entraînement).

**Cours complet :** [Pannes, checkpointing et reprise automatique](courses/fault-tolerance/index.html).

**Ce que vous saurez vérifier :**

-   Modéliser la fiabilité d'un job (MTBF d'un cluster, temps perdu, intervalle de checkpoint optimal)
-   Écrire un checkpoint atomique, complet (modèle, optimiseur, RNG, curseur de données) et le tester par injection de pannes
-   Concevoir une boucle de reprise automatique qui détecte, isole le nœud fautif et relance
-   Expliquer les pannes GPU/réseau courantes (Xid, ECC, liens, hangs NCCL) et les premières actions

**Chapitres :**

1.  Pannes à grande échelle : taxonomie (matériel, réseau, logiciel, humaine), données publiées, loi des grands nombres
2.  Modèle de coût : formule de Young/Daly, goodput, temps perdu, arbitrage fréquence/coût de checkpoint
3.  Checkpoint correct : atomicité, état complet, reproductibilité de la reprise, sharding, formats (DCP, safetensors)
4.  Checkpoints rapides : asynchrones, en mémoire, multi-niveaux, couche de stockage, déduplication
5.  Détection : watchdogs, heartbeats, timeouts NCCL, métriques de lenteur, nœuds 'stragglers' et silencieux
6.  Reprise et élasticité : torchrun élastique, retrait d'un nœud, redimensionnement ; pipeline de relance sous Slurm/Kubernetes
7.  Erreurs GPU courantes : Xid, ECC, thermique, liens NVLink/IB dégradés ; conduite à tenir
8.  Tests de chaos et procédures : injection de pannes, game days, runbooks, post-mortems sans blâme

**Labs :**

-   **Intervalle de checkpoint optimal** (bac à sable, sans GPU) : Simulation Monte-Carlo de pannes ; comparer l'intervalle de Young/Daly au minimum simulé ; tracé et tests.
-   **Checkpoint atomique et reprise exacte** (bac à sable, sans GPU) : Entraîneur PyTorch CPU avec checkpoint complet (modèle, optimiseur, RNG, itérateur de données) ; kill -9 aléatoire ; vérifier que la perte reprend sans saut et que le résultat final est identique.
-   **Superviseur de relance** (bac à sable, sans GPU) : Superviseur qui détecte un hang par heartbeat, tue et relance depuis le dernier checkpoint valide, avec limite de relances ; tests.

**Sources à lire et faits à vérifier :**

-   Llama 3 (Dubey et al. 2024) : interruptions sur 54 jours, répartition des causes ; citer chiffres exacts depuis le papier
-   Kokolis et al. (2024) fiabilité des clusters de recherche ML de Meta ; Hu et al. (NSDI 2024)
-   Young (1974), Daly (2006) ; Mohan et al. CheckFreq ; Wang et al. Gemini (SOSP 2023) ; documentation PyTorch DCP et torch.distributed.elastic
-   Documentation NVIDIA sur les codes Xid

**Projets qui s'appuient sur ce module :** Projet 3, Projet 6.

### Module 11 — Ray, infrastructure d'apprentissage par renforcement et boucles en ligne (plan, 28 h) {#ray-rl-infra}

Les charges qui ne sont pas un simple gros job : acteurs, rollouts distribués, apprenant et acteurs, synchronisation de politique, tampons de rejeu, traitement de données orchestré.

**Prérequis :** module 9 (Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline).

**Ce que vous saurez vérifier :**

-   Expliquer le modèle de Ray (tâches, acteurs, objets) et choisir quand l'utiliser
-   Concevoir une architecture acteur-apprenant avec synchronisation de politique et tampon de rejeu
-   Dimensionner collecte de données et apprentissage pour une boucle en ligne (débit, latence, obsolescence)
-   Orchestrer des traitements de données CPU/GPU hétérogènes sur une même flotte

**Chapitres :**

1.  Pourquoi un framework distribué général : tâches, acteurs, ressources, ordonnancement dans Ray
2.  Ray en pratique : objets partagés, placement groups, gestion de la mémoire, tolérance aux pannes, autoscaling
3.  Ray Train et Ray Data : entraînement distribué, ingestion, traitement par lots et en flux
4.  RL pour un ingénieur d'infrastructure : boucle observation-action-récompense, PPO/GRPO en une page, post-entraînement des modèles
5.  Architectures acteur-apprenant : rollouts distribués, synchronisation de poids, obsolescence, tampons de rejeu
6.  Boucles en ligne et temps réel : latence de bout en bout, files, contre-pression, déséquilibre acteurs/apprenants
7.  Hétérogénéité : GPU d'entraînement, GPU d'évaluation moins chers, CPU ; placement et files par type
8.  Ray sur Kubernetes (KubeRay) et sur Slurm ; observabilité d'une application Ray ; alternatives (Dask, Spark, Kubeflow)

**Labs :**

-   **Acteurs et tâches Ray** (bac à sable, sans GPU) : Pipeline de traitement avec tâches/acteurs Ray local ; mesure d'efficacité, tolérance à la mort d'un acteur ; tests.
-   **Boucle acteur-apprenant minimale** (bac à sable, sans GPU) : Environnement jouet, N acteurs, un apprenant, tampon de rejeu, synchronisation de politique ; mesurer obsolescence et débit ; courbe d'apprentissage reproductible.
-   **Modèle de débit d'une boucle en ligne** (bac à sable, sans GPU) : Modèle analytique + simulation événementielle : combien d'acteurs pour saturer un apprenant ; tests de cohérence modèle/simulation.

**Sources à lire et faits à vérifier :**

-   Moritz et al. (2018) Ray (OSDI) ; documentation Ray 2.x
-   Documentation KubeRay
-   Descriptions publiques d'architectures acteur-apprenant (IMPALA, Espeholt et al. 2018 ; documentation d'outils RLHF/GRPO open source)
-   Vérifier l'installation de ray sur le bac à sable (CPU) avant d'annoncer des labs 'vérifiés'

**Projets qui s'appuient sur ce module :** Projet 6.


## Phase 4 — Plateforme cloud-native et multi-fournisseurs {#phase4}

### Module 12 — Kubernetes pour l'IA : GPU, files d'attente et gang scheduling (plan, 28 h) {#kubernetes-gpu}

Ce que Kubernetes sait et ne sait pas faire pour l'entraînement : GPU Operator, MIG, Kueue, Volcano, JobSet, KubeRay, topologie et comparaison honnête avec Slurm.

**Prérequis :** module 1 (Linux, systèmes et diagnostic de performance), module 5 (Slurm et exploitation d'un cluster HPC).

**Ce que vous saurez vérifier :**

-   Exposer des GPU à des pods (device plugin, GPU Operator, MIG, time-slicing) et en comprendre les limites
-   Mettre en place files d'attente et gang scheduling (Kueue ou Volcano) avec quotas et préemption
-   Lancer un entraînement multi-nœuds avec JobSet/Kubeflow Trainer et un cluster Ray avec KubeRay
-   Choisir Slurm, Kubernetes ou les deux (Slurm sur Kubernetes) selon l'équipe et la charge

**Chapitres :**

1.  Rappel d'architecture : ce qui est acquis pour un lecteur déjà exploitant de Kubernetes, et ce qui change avec les GPU
2.  GPU dans Kubernetes : device plugin, GPU Operator, runtime conteneur, MIG, time-slicing, DRA (Dynamic Resource Allocation)
3.  Files d'attente et gang scheduling : Kueue, Volcano, ClusterQueue, quotas, préemption, équité
4.  Charges d'entraînement : JobSet, Kubeflow Trainer (ex Training Operator), indexed jobs, rendez-vous, réseau haute performance (RDMA, multus)
5.  Topologie et placement : affinités, topology-aware scheduling, étiquettes de nœuds, pannes de nœud
6.  Stockage et données : volumes, CSI, caches, accès objet, performances
7.  Slurm ou Kubernetes ? Retours publics sur les deux, modèles hybrides (Slurm sur K8s), critères de choix
8.  Exploitation : mises à jour, sécurité (RBAC, Pod Security, réseau), multi-tenance, coûts

**Labs :**

-   **Kueue : files, quotas, préemption** (bac à sable, sans GPU) : Manifestes ClusterQueue/LocalQueue/WorkloadPriorityClass validés hors ligne (kubernetes-validate/kubeconform si installable) et simulation de la logique d'admission en Python testée ; exécution sur cluster documentée.
-   **JobSet : un entraînement multi-nœuds** (cluster) : Manifestes JobSet/Trainer pour torchrun multi-nœuds ; validation de schéma ; exécution réelle documentée.
-   **Matrice de décision Slurm / Kubernetes** (bac à sable, sans GPU) : Grille de critères pondérée avec scénarios d'équipes ; script de calcul de score testé ; justification écrite.

**Sources à lire et faits à vérifier :**

-   Documentation Kubernetes (device plugins, DRA), NVIDIA GPU Operator, Kueue (kueue.sigs.k8s.io), Volcano, JobSet, KubeRay
-   Retours publics sur Slurm sur Kubernetes (Slinky/SchedMD, CoreWeave SUNK) : vérifier les pages officielles
-   Vérifier l'état de DRA et des versions de Kubernetes à la date du jour

**Projets qui s'appuient sur ce module :** Projet 6.

### Module 13 — Flotte multi-fournisseurs : SkyPilot, GPU clouds, hyperscalers et centres HPC (plan, 28 h) {#multi-cloud}

Placer, déborder et basculer des charges entre fournisseurs sans réécrire les jobs : abstraction de la capacité, bascule, préemption et paysage de l'offre.

**Prérequis :** module 12 (Kubernetes pour l'IA : GPU, files d'attente et gang scheduling), module 10 (Pannes, checkpointing et reprise automatique).

**Ce que vous saurez vérifier :**

-   Cartographier l'offre GPU (hyperscalers, GPU clouds, centres HPC, colocation) et ses modèles de capacité
-   Décrire un job indépendant du fournisseur (SkyPilot ou équivalent) et son placement sensible aux coûts
-   Concevoir une stratégie de débordement et de bascule qui survit à la préemption
-   Identifier les coûts cachés (sorties de données, stockage, réseau, latence d'accès)

**Chapitres :**

1.  Le paysage de l'offre GPU : hyperscalers, GPU clouds, fournisseurs européens, centres nationaux, colocation
2.  Modèles de capacité : à la demande, réservé, spot/préemptible, engagements, contrats de capacité
3.  Abstraire le fournisseur : SkyPilot, Terraform multi-fournisseurs, Kubernetes fédéré ; ce que chacun résout
4.  Données et gravité : où vivent les données, sorties de données, caches régionaux, résidence et conformité
5.  Placement et files : politiques de coût, de latence et de fiabilité ; préemption et reprise entre fournisseurs
6.  Réseau et identité : VPN/peering, identités fédérées, comptes, quotas, segmentation
7.  HPC publics : accès aux centres nationaux et européens (appels à projets, quotas), articulation avec le cloud
8.  Gouvernance : inventaire, étiquetage, coûts par équipe, nettoyage des ressources oubliées

**Labs :**

-   **Simulateur de placement sensible aux coûts** (bac à sable, sans GPU) : Simulateur Python : offres de plusieurs fournisseurs (prix/disponibilité synthétiques, étiquetés), jobs préemptibles ; comparer politiques ; tests.
-   **Un job SkyPilot indépendant du fournisseur** (cluster) : YAML SkyPilot avec ressources, file_mounts, setup/run, restart on preemption ; validation de schéma/linter ; exécution réelle documentée (compte cloud requis).
-   **Coût réel d'un déménagement de données** (bac à sable, sans GPU) : Calculateur (avec barèmes cités et datés) de sortie de données, stockage et temps de transfert ; scénarios ; tests.

**Sources à lire et faits à vérifier :**

-   Yang et al. (2023) SkyPilot (NSDI) ; documentation SkyPilot
-   Pages tarifaires officielles : toujours citer la source et la date, ne jamais figer un prix sans lien
-   Pages d'accès aux centres HPC (GENCI/Jean Zay, EuroHPC JU AI Factories, TACC/ACCESS) : citer les appels en cours
-   Capacités et offres des GPU clouds : changent vite, section 'à vérifier'

**Projets qui s'appuient sur ce module :** Projet 4, Projet 6.

### Module 14 — Observabilité et fiabilité d'une flotte GPU (rédigé, 24 h) {#observability}

Diagnostiquer en minutes un job bloqué, un GPU silencieux ou une courbe cassée : métriques GPU, journaux, traces, SLO de jobs et goodput.

**Prérequis :** module 1 (Linux, systèmes et diagnostic de performance), module 5 (Slurm et exploitation d'un cluster HPC).

**Cours complet :** [Observabilité et fiabilité d'une flotte GPU](courses/observability/index.html).

**Ce que vous saurez vérifier :**

-   Instrumenter une flotte GPU (DCGM, node exporter, exportateurs Slurm/Kubernetes) avec Prometheus
-   Définir des SLI/SLO de plateforme (disponibilité de capacité, délai d'attente, goodput) et des alertes utiles
-   Détecter automatiquement un job bloqué, un nœud lent et un GPU dégradé
-   Relier métriques système et métriques de modèle (MLflow/W&B) pour trouver la cause d'une régression

**Chapitres :**

1.  Ce qu'on observe : système, GPU, réseau, jobs, modèle ; le piège des métriques moyennes
2.  Métriques GPU : DCGM et dcgm-exporter (utilisation, mémoire, température, puissance, Xid, NVLink) ; ce que l'utilisation GPU ne dit pas
3.  Prometheus et Grafana pour le calcul : modèle de données, règles d'enregistrement, cardinalité, rétention ; spécificités HPC
4.  Journaux et traces : Loki/ELK, corrélation par job, traçage distribué des étapes d'entraînement
5.  Observabilité des ordonnanceurs : exportateurs Slurm, kube-state-metrics, files d'attente, temps d'attente
6.  SLO de plateforme : disponibilité, délai d'attente, goodput ; alertes qui réveillent pour de bonnes raisons
7.  Détection de pannes silencieuses : hangs NCCL, stragglers, erreurs ECC, dérives de débit ; tests de santé continus
8.  Suivi d'expériences et reproductibilité : MLflow, W&B, configuration, versions de code et de données

**Labs :**

-   **Un exportateur de métriques de nœud testé** (bac à sable, sans GPU) : Exportateur Prometheus Python (prometheus_client) pour une source de métriques simulée au format dcgm-exporter ; tests ; scrape local.
-   **Règles d'alerte testées avec promtool** (bac à sable, sans GPU) : Règles Prometheus (job bloqué, nœud lent, GPU chaud) testées avec promtool test rules (paquet apt prometheus si disponible).
-   **Détecteur de job bloqué** (bac à sable, sans GPU) : Détecteur par stagnation de métriques + heartbeat ; faux positifs et faux négatifs chiffrés sur séries simulées.

**Sources à lire et faits à vérifier :**

-   Documentation NVIDIA DCGM et dcgm-exporter
-   Documentation Prometheus (règles, promtool), Grafana, Loki, MLflow
-   Pièges d'interprétation de DCGM_FI_DEV_GPU_UTIL : citer la documentation

**Projets qui s'appuient sur ce module :** Projet 5, Projet 1, Projet 6.

### Module 15 — FinOps, capacité, énergie et achats de calcul (plan, 24 h) {#finops-capacity}

Prévoir la demande, choisir le bon mélange de matériel et de contrats, lire un contrat GPU et négocier : le volet technique de l'achat de calcul.

**Prérequis :** module 2 (Architecture matérielle et modèles de performance).

**Ce que vous saurez vérifier :**

-   Construire un modèle de coût total (TCO) comparant achat, colocation, réservation et à la demande
-   Prévoir la demande de calcul d'une équipe de recherche et en déduire la capacité à contractualiser
-   Lire un contrat de capacité GPU (SLA, remplacement, engagement, sorties) et repérer les clauses à négocier
-   Estimer puissance, refroidissement et densité par rack, et leur effet sur le coût et le calendrier

**Chapitres :**

1.  FinOps pour l'IA : cadre, unités (GPU-heure, coût par token, coût par expérience), allocation et responsabilité
2.  Utilisation réelle : taux d'occupation, goodput, gaspillage, files d'attente et coût de l'inactivité
3.  Prévoir la demande : modèles d'usage d'une équipe de recherche, scénarios, marges, plans de capacité
4.  Modèle de coût total : achat, colocation, location à long terme, réservé, spot ; amortissement, valeur résiduelle
5.  Énergie et datacenter : puissance par GPU et par rack, refroidissement (air, liquide), PUE, délais de raccordement
6.  Lire un contrat de capacité : SLA, disponibilité, remplacement de nœud, engagement minimum, transfert, support
7.  Négocier : leviers, alternatives crédibles, calendrier, bonnes et mauvaises pratiques ; rôle de l'ingénieur dans l'achat
8.  Matrices de décision et RFP techniques ; indicateurs de pilotage trimestriels

**Labs :**

-   **Modèle de TCO paramétrable** (bac à sable, sans GPU) : Outil Python testé : achat/colocation/réservé/à la demande/spot ; sensibilité aux hypothèses ; hypothèses étiquetées et sourcées ou 'exemple'.
-   **Prévision de demande de calcul** (bac à sable, sans GPU) : Génération de scénarios de demande, calcul de capacité à engager et du risque de pénurie/gaspillage ; tests.
-   **Lecture d'un contrat de capacité** (bac à sable, sans GPU) : Grille d'analyse de clauses appliquée à un contrat fictif fourni (clairement fictif) ; script qui note les clauses ; corrigé détaillé.

**Sources à lire et faits à vérifier :**

-   FinOps Foundation Framework et 'FinOps for AI' (pages officielles)
-   Chiffres de puissance par GPU/rack : fiches constructeur datées ; ordres de grandeur sinon
-   Aucun prix ni condition contractuelle réels sans lien et date ; les exemples sont fictifs et marqués comme tels

**Projets qui s'appuient sur ce module :** Projet 4, Projet 6.


## Phase 5 — Production et leadership {#phase5}

### Module 16 — Plateforme interne, sécurité, production et leadership (rédigé, 28 h) {#platform-leadership}

Transformer un cluster en plateforme que des chercheurs adoptent : expérience développeur, sécurité multi-locataire, fiabilité de production, direction d'équipe et entretien.

**Prérequis :** module 5 (Slurm et exploitation d'un cluster HPC), module 12 (Kubernetes pour l'IA : GPU, files d'attente et gang scheduling), module 14 (Observabilité et fiabilité d'une flotte GPU).

**Cours complet :** [Plateforme interne, sécurité, production et leadership](courses/platform-leadership/index.html).

**Ce que vous saurez vérifier :**

-   Concevoir une plateforme de calcul self-service (sessions interactives, files, quotas, modèles de jobs)
-   Définir un modèle de sécurité multi-locataire (identité, isolation, secrets, audit) pour des GPU partagés
-   Instituer des pratiques de production : astreinte, gestion d'incident, post-mortems, revues de conception
-   Préparer un entretien de compute infrastructure lead : conception, dépannage, leadership, négociation

**Chapitres :**

1.  La plateforme comme produit : utilisateurs, besoins, adoption, mesure de la vélocité des chercheurs
2.  Sessions interactives et environnements de développement : VM/conteneurs GPU, notebooks, partage de matériel
3.  Sécurité d'une plateforme GPU partagée : identité, isolation, secrets, réseau, chaîne d'approvisionnement logicielle, audit
4.  Fiabilité de production : SLO, astreinte, gestion d'incident, post-mortems, revues de conception (RFC/ADR)
5.  Évolutions et migrations : changer de scheduler, de fournisseur, de génération de GPU sans casser les utilisateurs
6.  Diriger une petite équipe d'infrastructure : recrutement, priorités, dette, relation avec la recherche, communication
7.  Contribuer et se rendre visible : open source, articles, présentations ; construire un portfolio crédible
8.  Entretiens : exercices de conception de cluster, cas de dépannage commentés, récits d'expérience structurés, questions à poser

**Labs :**

-   **Écrire une RFC de plateforme** (bac à sable, sans GPU) : Modèle de RFC/ADR avec grille de relecture automatisée (sections, décisions, alternatives, risques, métriques) et script de lint ; exemple complet fourni.
-   **Post-mortem d'un incident simulé** (bac à sable, sans GPU) : Jeu de logs et chronologie synthétiques (clairement étiquetés) ; trouver la cause, écrire le post-mortem ; corrigé détaillé.
-   **Exercice de conception : de 8 à 256 GPU** (bac à sable, sans GPU) : Énoncé d'entretien de conception avec grille d'évaluation et réponses de niveaux différents ; calculateur de dimensionnement testé.

**Sources à lire et faits à vérifier :**

-   Google SRE Book / SRE Workbook (accès libre)
-   Documentation Open OnDemand, JupyterHub, Slurm ; modèles de menaces pour GPU partagés (documentation NVIDIA, CNCF)
-   Aucune promesse d'emploi ou de salaire

**Projets qui s'appuient sur ce module :** Projet 6.


## Projets {#projets}

### Projet 1 — Mini-cluster Slurm instrumenté (24 h) {#homelab-slurm}

Un cluster Slurm de test reproductible par script, avec comptabilité, politique d'équité et tableau de bord de supervision.

**Modules mobilisés :** 1, 6, 5, 14.

**Plan :** Script d'installation reproductible (munge, MariaDB, slurmdbd, slurmctld/slurmd), configuration de comptes/QOS/fairshare, exportateur de métriques Slurm, règles d'alerte testées avec promtool, tableau de bord Grafana en JSON. Vérifié dans le bac à sable avec Slurm 23.11 ; version multi-nœuds avec conteneurs en extension.

### Projet 2 — Étude de passage à l'échelle d'un entraînement (20 h) {#scaling-study}

Mesurer, modéliser et expliquer comment un entraînement distribué passe à l'échelle, avec un rapport honnête.

**Modules mobilisés :** 2, 3, 4, 7, 9.

**Plan :** Entraînement DDP/FSDP (gloo, CPU) à 1, 2, 4 processus ; plan d'expérience, mesure du temps par pas et de la communication, ajustement du modèle α-β, calcul de MFU/efficacité, rapport reproductible (script unique, graphes, ADR). Variante GPU en extension avec coût indicatif.

### Projet 3 — Entraîneur tolérant aux pannes (24 h) {#resilient-trainer}

Un entraînement qui survit à kill -9, aux nœuds lents et aux checkpoints corrompus, avec preuves automatisées.

**Modules mobilisés :** 8, 9, 10.

**Plan :** Entraîneur PyTorch CPU avec checkpoint atomique complet, superviseur de relance, injection de pannes, tests qui prouvent la reprise exacte (perte continue, état RNG et données), rapport de coût de checkpoint et de goodput.

### Projet 4 — Placement multi-fournisseurs sensible aux coûts (24 h) {#multi-provider-scheduler}

Un simulateur et une politique de placement/bascule, avec les manifestes qui la matérialiseraient sur de vrais fournisseurs.

**Modules mobilisés :** 13, 15, 12.

**Plan :** Simulateur Python d'offres (données synthétiques étiquetées comme telles), politiques de placement et de bascule comparées par différences appariées sur les mêmes graines, tâches SkyPilot et manifestes Kueue générés puis validés hors ligne de façon structurelle, ADR sur les compromis coût, fiabilité et latence. Un module Terraform validé avec terraform validate est proposé en extension.

### Projet 5 — Observabilité GPU et détection de pannes silencieuses (20 h) {#gpu-observability}

Exportateurs, règles d'alerte testées et détecteurs qui trouvent un job bloqué ou un GPU dégradé en quelques minutes.

**Modules mobilisés :** 14, 5, 10.

**Plan :** Exportateur de métriques au format dcgm-exporter alimenté par un simulateur de nœuds, règles Prometheus avec tests promtool, détecteur de job bloqué et de straggler avec taux de faux positifs mesurés, tableau de bord et runbook.

### Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU (40 h) {#capstone-rfc}

Le projet de synthèse : un document de conception complet, un modèle de capacité et de coût exécutable, des runbooks et une démonstration.

**Modules mobilisés :** 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16.

**Plan :** RFC d'une plateforme de calcul pour une équipe de recherche en IA (cahier des charges fictif fourni), modèle de capacité/coût testé, politique d'ordonnancement, plan de fiabilité et d'observabilité, plan de migration, runbooks, revue contradictoire par grille ; soutenance orale de 20 minutes avec questions types.

