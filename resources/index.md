---
title: "Ressources"
subtitle: "58 ressources vérifiées : lectures, cours ouverts, certifications, documentations, communautés"
description: "Références à lire pour devenir compute infrastructure engineer, chacune vérifiée à sa source entre le 22 et le 25 octobre 2026."
numbered: true
---

## Comment utiliser cette page {#usage}

Chaque ressource listée ici a été ouverte à sa source : le titre, les auteurs ou le fournisseur et l'adresse correspondent à la page cible, et une citation de cette page a été vérifiée mot pour mot. Les modules renvoient vers ces ressources avec l'usage précis (« lire la section 3 pour… »).

Les certifications évoluent vite : relisez la page officielle de l'examen avant de vous inscrire. Cette page ne donne ni prix ni format qui ne figurent pas sur la page officielle.


## Articles et rapports à lire {#paper}

-   **[Bandwidth optimal all-reduce algorithms for clusters of workstations](https://www.cs.fsu.edu/~xyuan/paper/09jpdc.pdf)** · Patarasuk, Yuan, 2009 (avancé, gratuit). Borne inférieure de données émises par un all-reduce et algorithme en anneau optimal.
-   **[Characterization of Large Language Model Development in the Datacenter](https://arxiv.org/abs/2403.07648)** · Hu et al., 2024 (avancé, gratuit). Caractérisation de charges de développement de LLM et de leurs pannes dans un centre de calcul.
-   **[DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](https://arxiv.org/abs/2401.09670)** · Zhong et al., 2024 (avancé, gratuit). Séparer prefill et décodage sur des GPU différents, chaque phase dimensionnée selon son objectif de latence (TTFT, TPOT) : la référence de la désagrégation en inférence.
-   **[Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM](https://arxiv.org/abs/2104.04473)** · Narayanan et al., 2021 (avancé, gratuit). Combinaison des parallélismes de données, tensoriel et pipeline à grande échelle.
-   **[Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180)** · Kwon et al., 2023 (avancé, gratuit). Le papier de vLLM : gérer le cache KV par pages, comme la mémoire virtuelle d'un système d'exploitation, pour moins fragmenter la mémoire et grouper plus de requêtes.
-   **[FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135)** · Dao et al., 2022 (avancé, gratuit). Un exemple de noyau gouverné par le trafic mémoire : lien direct avec le roofline.
-   **[MegaScale: Scaling Large Language Model Training to More Than 10,000 GPUs](https://arxiv.org/abs/2402.15627)** · Jiang et al., 2024 (avancé, gratuit). Retour d'expérience de ByteDance sur l'efficacité, le diagnostic et la tolérance aux pannes à plus de 10 000 GPU.
-   **[PaLM: Scaling Language Modeling with Pathways](https://arxiv.org/abs/2204.02311)** · Chowdhery et al., 2022 (avancé, gratuit). Définition du MFU (section 4.1) et formule des FLOP par token (annexe B).
-   **[PyTorch FSDP: Experiences on Scaling Fully Sharded Data Parallel](https://arxiv.org/abs/2304.11277)** · Zhao et al., 2023 (avancé, gratuit). Conception et retours d'expérience de FSDP, base du module 9.
-   **[Revisiting Reliability in Large-Scale Machine Learning Research Clusters](https://arxiv.org/abs/2410.21680)** · Kokolis et al., 2024 (avancé, gratuit). Étude de la fiabilité de grands clusters de recherche en apprentissage automatique.
-   **[The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783)** · Dubey et al., 2024 (avancé, gratuit). Tableau 4 (MFU par configuration de parallélisme) et section 3.3.4 sur la fiabilité à 16 000 GPU.
-   **[ZeRO: Memory Optimizations Toward Training Trillion Parameter Models](https://arxiv.org/abs/1910.02054)** · Rajbhandari et al., 2020 (avancé, gratuit). Section 3.1 : 16 octets par paramètre en précision mixte avec Adam ; partition des états d'optimiseur.
-   **[In Search of an Understandable Consensus Algorithm](https://www.usenix.org/conference/atc14/technical-sessions/presentation/ongaro)** · Diego Ongaro, John Ousterhout, 2014 (intermédiaire, gratuit). Raft (USENIX ATC 2014) : élection d'un leader, réplication du journal, sûreté et changement de membres, à lire avant de raisonner sur la disponibilité d'un plan de contrôle.
-   **[Ray: A Distributed Framework for Emerging AI Applications](https://arxiv.org/abs/1712.05889)** · Moritz et al., 2017 (intermédiaire, gratuit). Modèle de tâches et d'acteurs de Ray, base du module 11.
-   **[Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-134.html)** · Williams, Waterman, Patterson, 2008 (intermédiaire, gratuit). Version rapport technique de l'article du modèle roofline (version CACM 2009 : doi:10.1145/1498765.1498785).
-   **[Scientific Benchmarking of Parallel Computing Systems: Twelve Ways to Tell the Masses when Reporting Performance Results](https://evaluate.inf.usi.ch/node/366)** · Hoefler, Belli, 2015 (intermédiaire, gratuit). Règles de mesure et de rapport statistique ; base des chapitres 3 et 8 du module 2.

## Livres {#book}

-   **[The Kubebuilder Book](https://book.kubebuilder.io/)** · Projet Kubebuilder (kubernetes-sigs), 2026 (intermédiaire, gratuit). Écrire sa propre API Kubernetes et son contrôleur en Go : boucle de réconciliation, finalizers, versionnage d'API, réconciliation périodique.
-   **[The Rust Programming Language](https://doc.rust-lang.org/book/)** · Steve Klabnik, Carol Nichols, Chris Krycho, avec des contributions de la communauté Rust, 2026 (introduction, gratuit). Le livre officiel du langage, gratuit en ligne ; la version consultée le 2026-10-25 suppose Rust 1.97.0 (sorti le 2026-07-09) et l'édition 2024.

## Cours ouverts {#course}

-   **[CMU 15-418/15-618 Parallel Computer Architecture and Programming](https://www.cs.cmu.edu/~418/)** · 2026 (intermédiaire, coût non précisé). Public syllabus and assignments for parallel hardware and programming (multicore, GPUs, 'C-like' parallel languages); sister course of Stanford CS149 with a systems-programming flavour.
-   **[CMU 15-442/15-642 Machine Learning Systems](https://mlsyscourse.org/)** · 2026 (intermédiaire, coût non précisé). Public schedule covering data/ZeRO, model and pipeline parallelism, GPU architecture and CUDA, GEMM on modern GPUs and LLM serving: the most direct ML-systems syllabus found for a training/inference platform engineer.
-   **[DOE facility user training](https://www.nersc.gov/users/training/)** · 2026 (intermédiaire, coût non précisé). National computing centres publish training for their users; NERSC lists new-user training and SpinUp workshops and OLCF archives materials for Frontier. Details of content were not readable (JavaScript calendar), so use as pointers to current events.
-   **[Deep Learning Systems](https://dlsyscourse.org/)** · 2026 (intermédiaire, coût non précisé). Hands-on view of what sits under PyTorch: automatic differentiation, an NDArray library with CPU/CUDA backends, memory coalescing and tiling; useful background before operating GPU training platforms.
-   **[IDRIS training catalogue](http://www.idris.fr/docs/formations/catalogue-formations)** · 2026 (intermédiaire, coût non précisé). Short, free (for CNRS and university staff) or CNRS-Formation-Entreprise courses taught by the Jean Zay support team, including a multi-GPU deep-learning scaling course; the course pages are public syllabi that fit a self-study path in parallel programming and distributed training. Registration site was under maintenance on the page read, so check dates.
-   **[ROMEO](https://romeo.univ-reims.fr)** · 2026 (intermédiaire, coût non précisé). Un centre de calcul académique qui propose des formations courtes sur GPU, multi-GPU et IA sur supercalculateur, ouvertes au-delà des étudiants du master CHPS.
-   **[Stanford CS149 Parallel Computing](https://cs149.stanford.edu/)** · 2026 (intermédiaire, coût non précisé). Best public syllabus found for the hardware/software boundary of parallel systems: multicore and SIMD, work scheduling, CUDA, DNN execution on GPUs, datacenter-scale AI serving, coherence and synchronisation, with programming assignments including CUDA kernels and a Trainium2 kernel.
-   **[Stanford CS336 Language Modeling from Scratch](https://cs336.stanford.edu/)** · 2026 (intermédiaire, coût non précisé). A public course where one assignment is explicitly systems: profile, write a Triton FlashAttention2 kernel and build a memory-efficient distributed training loop, which is the user-level view of what a GPU-cluster platform must serve.
-   **[UC Berkeley CS267 Applications of Parallel Computers](https://sites.google.com/lbl.gov/cs267-spr2025)** · 2026 (intermédiaire, coût non précisé). Long-running reference course (Demmel, Yelick and others) on programming parallel computers for science and engineering; public site with syllabus; part of the Berkeley Designated Emphasis in Computational Science and Engineering.
-   **[A Tour of Go](https://go.dev/tour/)** · Projet Go (go.dev), 2026 (introduction, gratuit). Introduction interactive en quatre sections avec exercices : un premier pas pour lire puis écrire le Go des contrôleurs, agents de nœud et outils de flotte.

## Documentations de référence {#docs}

-   **[Slurm — Topology Guide](https://slurm.schedmd.com/topology.html)** · SchedMD, 2026 (avancé, gratuit). topology/tree, topology/block et --switches (module 5, chapitre 5).
-   **[AMD ROCm documentation](https://rocm.docs.amd.com/en/latest/)** · AMD, 2026 (intermédiaire, gratuit). La pile GPU d'AMD (HIP, RCCL, AMD SMI, ROCm Validation Suite, partitionnement GPU) ; la version affichée le 2026-10-25 est ROCm 10.1.0.
-   **[Effective Go](https://go.dev/doc/effective_go)** · Projet Go (go.dev), 2009 (intermédiaire, gratuit). Les idiomes du langage, dont la section Concurrency (goroutines, canaux) ; écrit pour la sortie de Go en 2009 et non mis à jour, il ne couvre ni les génériques ni les modules.
-   **[KubeVirt user guide](https://kubevirt.io/user-guide/)** · Projet KubeVirt, 2026 (intermédiaire, gratuit). Des machines virtuelles gérées comme des objets Kubernetes ; les pages Host Devices Assignment et Mediated devices and virtual GPUs traitent du passage d'un GPU à une VM.
-   **[Slurm — Fair Tree Fairshare Algorithm](https://slurm.schedmd.com/fair_tree.html)** · SchedMD, 2026 (intermédiaire, gratuit). Algorithme d'équité par défaut depuis 19.05 (module 5, chapitre 3).
-   **[Slurm — Generic Resource (GRES) Scheduling](https://slurm.schedmd.com/gres.html)** · SchedMD, 2026 (intermédiaire, gratuit). Déclaration des GPU et gestion de MIG (module 5, chapitre 5).
-   **[Slurm — Multifactor Priority Plugin](https://slurm.schedmd.com/priority_multifactor.html)** · SchedMD, 2026 (intermédiaire, gratuit). La formule de priorité d'un job et ses poids (module 5, chapitre 3).
-   **[Slurm — Preemption](https://slurm.schedmd.com/preempt.html)** · SchedMD, 2026 (intermédiaire, gratuit). PreemptType, PreemptMode, GraceTime (module 5, chapitre 4).
-   **[Slurm — Prolog and Epilog Guide](https://slurm.schedmd.com/prolog_epilog.html)** · SchedMD, 2026 (intermédiaire, gratuit). Sémantique des prologues et épilogues et conséquences de leurs échecs (module 5, chapitre 7).
-   **[Slurm — cgroup.conf](https://slurm.schedmd.com/cgroup.conf.html)** · SchedMD, 2026 (intermédiaire, gratuit). ConstrainDevices, ConstrainCores, ConstrainRAMSpace.
-   **[Writing exporters](https://prometheus.io/docs/instrumenting/writing_exporters/)** · Projet Prometheus, 2026 (intermédiaire, gratuit). Les règles de conception d'un exporter, quel que soit le langage : un collecteur qui lit l'état à chaque scrape, le nommage des métriques, les métriques sur le scrape lui-même.
-   **[nccl-tests — performance metrics](https://raw.githubusercontent.com/NVIDIA/nccl-tests/master/doc/PERFORMANCE.md)** · NVIDIA, 2026 (intermédiaire, gratuit). Définitions de algbw et busbw, base du module 7.
-   **[Slurm — sbatch](https://slurm.schedmd.com/sbatch.html)** · SchedMD, 2026 (introduction, gratuit). Toutes les options de soumission, dont --signal, --requeue et --gpus-per-node.
-   **[Slurm — sinfo](https://slurm.schedmd.com/sinfo.html)** · SchedMD, 2026 (introduction, gratuit). États de nœuds et sorties de sinfo.
-   **[Slurm — squeue](https://slurm.schedmd.com/squeue.html)** · SchedMD, 2026 (introduction, gratuit). Codes de raison d'attente d'un job.

## Communautés et conférences {#community}

-   **[ASC 世界大学生超级计算机竞赛](https://m.tech.china.com/article/20260521/202605211874155.html)** · 2026 (intermédiaire, coût non précisé). Teams build and tune a small cluster under a 5000 W power cap and run HPL, HPCG and scientific/AI applications: the closest hands-on training to cluster operations available to students of these universities; PKU, Tsinghua and ZJU teams appear in the 2026 results.
-   **[CC-FR](https://romeo.univ-reims.fr/16_cc-fr.html)** · 2026 (intermédiaire, coût non précisé). Point d'entrée français du programme EuroCC : formations de prise en main d'un supercalculateur et formations avancées (containers, LLM) sur le réseau des mésocentres MesoNET, utile pour pratiquer sur de vraies machines hors université.
-   **[Cemosis](https://www.cemosis.fr/en/)** · 2026 (intermédiaire, coût non précisé). Plateforme adossée au master CSMI, impliquée dans PEPR NumPEx (Exa-MA, SAGE-HPC) et le CoE EuroHPC HiDALGO2 : lien concret entre formation, HPC et projets exascale.
-   **[Hackathon TERATEC](https://romeo.univ-reims.fr/chps)** · 2026 (intermédiaire, coût non précisé). Compétition HPC française à laquelle participent des étudiants (une équipe de M2 CHPS Reims y a obtenu le prix du jury en janvier 2024) ; bon terrain pour pratiquer l'optimisation sur machine réelle.
-   **[IDRIS](http://www.idris.fr/docs/jean-zay/jean-zay/jean-zay-hardware)** · 2026 (intermédiaire, coût non précisé). Real national GPU supercomputer (CPU, V100, A100 and H100 partitions) operated with Slurm, a Lustre parallel file system and InfiniBand/Omni-Path networks: the closest public, documented example of the cluster stack a compute infrastructure engineer runs. The hardware, scheduler and filesystem pages are public documentation to read and reproduce in labs.
-   **[MesoNET](https://romeo.univ-reims.fr/16_cc-fr.html)** · 2026 (intermédiaire, coût non précisé). Réseau de centres de calcul régionaux donnant accès à des supercalculateurs, du stockage et des heures de calcul : base du paysage HPC académique français en dessous du niveau national (GENCI).
-   **[Réseau des Masters CHPS](https://master-chps.fr/about/)** · 2026 (intermédiaire, coût non précisé). National network of French state-recognised HPC and simulation degrees (Paris-Saclay, Bordeaux CISD, Toulouse ENSEEIHT, Perpignan, Reims) with joint seminars, shared internship offers and a student hackathon with Teratec; the entry point to compare French HPC curricula.
-   **[SC Student Cluster Competition](https://studentclustercompetition.us/)** · 2026 (intermédiaire, coût non précisé). Teams of students build, tune and run HPC applications on a cluster in a competition setting; the best hands-on route to cluster operation skills for a student, and a recruiting ground for HPC centres.
-   **[中国科学技术大学超级计算中心](http://scc.ustc.edu.cn/40970/list.htm)** · 2026 (intermédiaire, coût non précisé). A production university cluster documented in detail (A100 GPU nodes, GPFS, HDR InfiniBand, Slurm 24.11, module environment): a realistic reference of a campus HPC/AI cluster and a place where USTC students can get accounts via their supervisor.
-   **[国防科技大学](https://english.nudt.edu.cn/nav/About/AtAGlance/d9d8150917a24b18ba2089168ab6f43f.htm)** · 2026 (intermédiaire, coût non précisé). NUDT is the builder of the TianHe supercomputers; its computer college is therefore a major HPC training site in China, but no NUDT graduate curriculum page was reachable (see blocked_sources), so no programme entry is given.
-   **[清华大学学生超算团队](https://www.tsinghua.edu.cn/info/1175/111550.htm)** · 2026 (intermédiaire, coût non précisé). Student team organised with the HPC group of the CS department (coached by HPC faculty and supported by HPC-institute PhD students); wins in the three international student cluster competitions, including cluster power control, a core cluster-operations skill.

## Outils {#tool}

-   **[LBNL Node Health Check (NHC)](https://raw.githubusercontent.com/mej/nhc/master/README.md)** · Lawrence Berkeley National Laboratory, 2026 (intermédiaire, gratuit). Implémentation de référence d'un contrôle de santé de nœud pour Slurm et d'autres ordonnanceurs.
-   **[Prometheus Go client library (package prometheus)](https://pkg.go.dev/github.com/prometheus/client_golang/prometheus)** · Projet Prometheus, 2026 (intermédiaire, gratuit). La bibliothèque d'instrumentation Go de Prometheus (registre, collecteurs, exposition HTTP par promhttp) : la base d'un exporter de nœud ou de GPU écrit en Go.
-   **[Pyxis — Slurm container plugin](https://raw.githubusercontent.com/NVIDIA/pyxis/master/README.md)** · NVIDIA, 2026 (intermédiaire, gratuit). Plugin SPANK qui ajoute --container-image à srun.
-   **[Slinky — Slurm and Kubernetes](https://www.nvidia.com/en-us/software/slinky/)** · SchedMD / NVIDIA, 2026 (intermédiaire, gratuit). Projet ouvert pour exécuter des clusters Slurm dans Kubernetes (module 5, chapitre 8 ; module 12).

## Sources et portée {#sources}

**Documenté.** Ressources relues à leur source entre le 22 et le 25 octobre 2026 (outil `tools/verify_quotes.py`).

**Recommandé.** Le tri par type et le commentaire d'usage sont des choix de ce parcours.

**À vérifier.** Les offres de formation et de certification changent : confirmez sur la page officielle.
