---
title: "Mastering Compute Infrastructure"
subtitle: "Un parcours pour devenir compute infrastructure engineer : cours, labs vérifiés, projets de portfolio et enquête sur les masters HPC"
description: "Parcours d'apprentissage en français pour opérer des clusters GPU, ordonnancer, entraîner à grande échelle et piloter la capacité multi-fournisseurs."
numbered: true
toc-inline: false
---

<p class="lead">Un <em>compute infrastructure engineer</em> fait tourner les machines sur lesquelles on entraîne les modèles d'IA : clusters GPU, ordonnanceurs, réseaux, stockage, fiabilité, coût. Ce site rassemble de quoi apprendre ce métier de manière structurée : 16 modules en 6 phases, 6 projets de portfolio, des labs exécutables et une enquête sourcée sur les masters HPC en France, aux États-Unis, en Chine et dans le monde.</p>

<div class="hero-actions">
<a class="cta" href="#cours">Voir les cours</a>
<a class="cta cta-ghost" href="path/index.html">Feuille de route</a>
<a class="cta cta-ghost" href="syllabus/index.html">Plans détaillés</a>
<a class="cta cta-ghost" href="profile/index.html">Point de départ</a>
<a class="cta cta-ghost" href="market/index.html">Analyse du marché</a>
<a class="cta cta-ghost" href="masters/index.html">Enquête sur les masters HPC</a>
</div>

## État du chantier {#etat}

Ce site est construit module par module, et chaque page est vérifiée avant d'être publiée. **16 module(s) sur 16 et 6 projet(s) sur 6 sont publiés**.

-   **Documenté** : chaque chiffre sur un système réel renvoie à sa source ; sinon il est présenté comme un ordre de grandeur.
-   **Vérifié** : les calculs des exemples et des corrigés sont refaits en Python, les labs « bac à sable » s'exécutent sans GPU (`verify.sh`), les pages passent des contrôles mécaniques (`tools/check_gates.py`).
-   **Honnête** : un lab non exécuté porte le badge « non vérifié » ; une valeur incertaine est signalée « à vérifier ».

## Le parcours en un coup d'œil {#parcours}

Volume total : **440 h de modules et 152 h de projets**, soit environ 49 semaines à 12 h par semaine. Le détail, les jalons et les parcours courts sont dans la [feuille de route](path/index.html).

| Phase | Modules | Volume |
|---|---|---|
| 0 — Fondations : machines et performance | 1, 2 | 48 h |
| 1 — Calcul parallèle et GPU | 3, 4 | 60 h |
| 2 — Exploiter un cluster | 5, 6, 7, 8 | 108 h |
| 3 — Systèmes d'entraînement distribué | 9, 10, 11 | 92 h |
| 4 — Plateforme cloud-native et multi-fournisseurs | 12, 13, 14, 15 | 104 h |
| 5 — Production et leadership | 16 | 28 h |

## Cours {#cours}

Chaque cours est une longue page unique : fiche, plan de séances, chapitres avec exemples chiffrés, labs, exercices corrigés, checkpoint de sortie et références. Le badge **Cœur** signale un module indispensable à tous ; **Fondation** un module de base que vous pouvez survoler si vous le pratiquez déjà. La section « Comment travailler ce module » de chaque cours donne la priorité selon votre profil d'entrée.

### Phase 0 — Fondations : machines et performance {#phase0 .phase .unnumbered}


<p class="sub-line">Lire une machine et prédire sa performance avant de la mesurer.</p>

<div class="cards">
<a class="card" href="courses/linux-systems/index.html"><h4>Linux, systèmes et diagnostic de performance</h4><p class="meta">Module 01 · 24 h · Fondation</p><p>Le socle commun à tout ce qui suit : processus, mémoire, cgroups, NUMA, systemd, réseau et stockage vus par un exploitant de cluster.</p></a>
<a class="card" href="courses/perf-models/index.html"><h4>Architecture matérielle et modèles de performance</h4><p class="meta">Module 02 · 24 h · Cœur</p><p>Prédire avant de mesurer : hiérarchie mémoire, roofline, Amdahl/Gustafson, modèle α-β des communications et MFU.</p></a>
</div>

### Phase 1 — Calcul parallèle et GPU {#phase1 .phase .unnumbered}


<p class="sub-line">Écrire, mesurer et expliquer un programme parallèle sur CPU et GPU.</p>

<div class="cards">
<a class="card" href="courses/parallel-programming/index.html"><h4>Programmation parallèle : OpenMP, MPI et études de passage à l'échelle</h4><p class="meta">Module 03 · 30 h · Cœur</p><p>Le noyau commun de tous les masters HPC : mémoire partagée, passage de messages, collectives, et la discipline d'une étude de scalabilité.</p></a>
<a class="card" href="courses/gpu-programming/index.html"><h4>Programmation GPU : CUDA, Triton et profilage</h4><p class="meta">Module 04 · 30 h · Cœur</p><p>Comprendre un noyau GPU assez pour juger un profil : hiérarchie mémoire, occupation, coalescence, streams, puis Triton et Nsight.</p></a>
</div>

### Phase 2 — Exploiter un cluster {#phase2 .phase .unnumbered}


<p class="sub-line">Provisionner, ordonnancer, relier et alimenter en données un cluster GPU.</p>

<div class="cards">
<a class="card" href="courses/slurm/index.html"><h4>Slurm et exploitation d'un cluster HPC</h4><p class="meta">Module 05 · 32 h · Cœur</p><p>L'ordonnanceur de référence du calcul scientifique et de l'entraînement : partitions, QOS, fairshare, GRES, préemption, comptabilité, santé des nœuds.</p></a>
<a class="card" href="courses/provisioning/index.html"><h4>Provisioning, images et santé des nœuds GPU</h4><p class="meta">Module 06 · 24 h · Cœur</p><p>Du châssis nu au nœud en production : installation, images, configuration, pilotes, tests de recette et supervision matérielle.</p></a>
<a class="card" href="courses/networking/index.html"><h4>Réseaux haute performance : InfiniBand, RoCE et NCCL</h4><p class="meta">Module 07 · 28 h · Cœur</p><p>Pourquoi un entraînement multi-nœuds est limité par le réseau : topologies, RDMA, NVLink, NCCL, mesures et diagnostic.</p></a>
<a class="card" href="courses/storage/index.html"><h4>Stockage et E/S pour l'entraînement</h4><p class="meta">Module 08 · 24 h · Cœur</p><p>Nourrir les GPU et sauvegarder sans les arrêter : systèmes de fichiers parallèles, objet, cache, chargeurs de données et E/S de checkpoint.</p></a>
</div>

### Phase 3 — Systèmes d'entraînement distribué {#phase3 .phase .unnumbered}


<p class="sub-line">Faire tourner un entraînement multi-nœuds qui survit aux pannes.</p>

<div class="cards">
<a class="card" href="courses/distributed-training/index.html"><h4>Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline</h4><p class="meta">Module 09 · 36 h · Cœur</p><p>Le cœur du métier côté entraînement : choisir un parallélisme, estimer mémoire et communication, atteindre un bon MFU et déboguer l'instabilité numérique.</p></a>
<a class="card" href="courses/fault-tolerance/index.html"><h4>Pannes, checkpointing et reprise automatique</h4><p class="meta">Module 10 · 28 h · Cœur</p><p>À grande échelle les pannes sont la norme : modèle de panne, checkpoints rapides et corrects, entraînement élastique, reprise sans intervention humaine.</p></a>
<a class="card" href="courses/ray-rl-infra/index.html"><h4>Ray, infrastructure d'apprentissage par renforcement et boucles en ligne</h4><p class="meta">Module 11 · 28 h · Cœur</p><p>Les charges qui ne sont pas un simple gros job : acteurs, rollouts distribués, apprenant et acteurs, synchronisation de politique, tampons de rejeu, traitement de données orchestré.</p></a>
</div>

### Phase 4 — Plateforme cloud-native et multi-fournisseurs {#phase4 .phase .unnumbered}


<p class="sub-line">Placer, observer et facturer des charges sur plusieurs fournisseurs.</p>

<div class="cards">
<a class="card" href="courses/kubernetes-gpu/index.html"><h4>Kubernetes pour l'IA : GPU, files d'attente et gang scheduling</h4><p class="meta">Module 12 · 28 h · Cœur</p><p>Ce que Kubernetes sait et ne sait pas faire pour l'entraînement : GPU Operator, MIG, Kueue, Volcano, JobSet, KubeRay, topologie et comparaison honnête avec Slurm.</p></a>
<a class="card" href="courses/multi-cloud/index.html"><h4>Flotte multi-fournisseurs : SkyPilot, GPU clouds, hyperscalers et centres HPC</h4><p class="meta">Module 13 · 28 h · Cœur</p><p>Placer, déborder et basculer des charges entre fournisseurs sans réécrire les jobs : abstraction de la capacité, bascule, préemption et paysage de l'offre.</p></a>
<a class="card" href="courses/observability/index.html"><h4>Observabilité et fiabilité d'une flotte GPU</h4><p class="meta">Module 14 · 24 h · Cœur</p><p>Diagnostiquer en minutes un job bloqué, un GPU silencieux ou une courbe cassée : métriques GPU, journaux, traces, SLO de jobs et goodput.</p></a>
<a class="card" href="courses/finops-capacity/index.html"><h4>FinOps, capacité, énergie et achats de calcul</h4><p class="meta">Module 15 · 24 h · Cœur</p><p>Prévoir la demande, choisir le bon mélange de matériel et de contrats, lire un contrat GPU et négocier : le volet technique de l'achat de calcul.</p></a>
</div>

### Phase 5 — Production et leadership {#phase5 .phase .unnumbered}


<p class="sub-line">Opérer en production, décider, négocier, diriger et passer l'entretien.</p>

<div class="cards">
<a class="card" href="courses/platform-leadership/index.html"><h4>Plateforme interne, sécurité, production et leadership</h4><p class="meta">Module 16 · 28 h · Cœur</p><p>Transformer un cluster en plateforme que des chercheurs adoptent : expérience développeur, sécurité multi-locataire, fiabilité de production, direction d'équipe et entretien.</p></a>
</div>

## Projets de portfolio {#projets}

Chaque projet mobilise plusieurs modules et produit un dépôt que vous pouvez publier et présenter en entretien. Ils sont réalisables sans GPU dans leur version de base.

<div class="cards">
<a class="card" href="projects/homelab-slurm/index.html"><h4>Mini-cluster Slurm instrumenté</h4><p class="meta">Projet 1 · 24 h</p><p>Un cluster Slurm de test reproductible par script, avec comptabilité, politique d'équité et tableau de bord de supervision.</p></a>
<a class="card" href="projects/scaling-study/index.html"><h4>Étude de passage à l'échelle d'un entraînement</h4><p class="meta">Projet 2 · 20 h</p><p>Mesurer, modéliser et expliquer comment un entraînement distribué passe à l'échelle, avec un rapport honnête.</p></a>
<a class="card" href="projects/resilient-trainer/index.html"><h4>Entraîneur tolérant aux pannes</h4><p class="meta">Projet 3 · 24 h</p><p>Un entraînement qui survit à kill -9, aux blocages et aux checkpoints corrompus, avec preuves automatisées.</p></a>
<a class="card" href="projects/multi-provider-scheduler/index.html"><h4>Placement multi-fournisseurs sensible aux coûts</h4><p class="meta">Projet 4 · 24 h</p><p>Un simulateur et une politique de placement/bascule, avec les manifestes qui la matérialiseraient sur de vrais fournisseurs.</p></a>
<a class="card" href="projects/gpu-observability/index.html"><h4>Observabilité GPU et détection de pannes silencieuses</h4><p class="meta">Projet 5 · 20 h</p><p>Exportateurs, règles d'alerte testées et détecteurs qui trouvent un job bloqué ou un GPU dégradé en quelques minutes.</p></a>
<a class="card" href="projects/capstone-rfc/index.html"><h4>RFC et prototype : une plateforme de calcul de 8 à 256 GPU</h4><p class="meta">Projet 6 · 40 h</p><p>Le projet de synthèse : un document de conception complet, un modèle de capacité et de coût exécutable dont un vérificateur recoupe les chiffres, une revue contradictoire par grille et une soutenance.</p></a>
</div>

## Ce que demande le marché {#marche}

Une analyse sourcée d'offres d'emploi d'infrastructure de calcul publiées aux États-Unis, en Europe et en Chine, dans les laboratoires d'IA, les grands groupes, les clouds GPU et les centres HPC : les compétences demandées, ce qui change d'une région à l'autre, et ce que le parcours couvre. <a href="market/index.html">Lire l'analyse</a>.

## Enquête sur les masters HPC {#masters}

Une analyse sourcée des masters orientés calcul haute performance en France, aux États-Unis, en Chine et dans le reste du monde, croisée avec les offres d'emploi de compute infrastructure : ce que les masters enseignent, ce qu'ils n'enseignent presque pas, et ce que ce parcours ajoute. <a href="masters/index.html">Lire l'enquête</a>.

## Comment utiliser ce site {#usage}

1.  Lisez le [point de départ](profile/index.html) : il décrit le métier et cinq profils d'entrée, et propose une grille d'autodiagnostic pour choisir quels modules travailler à fond et lesquels survoler.
2.  Préparez votre [environnement de travail](lab-setup/index.html) si la page est publiée : un portable CPU suffit pour la base.
3.  Suivez les phases dans l'ordre. Dans chaque module, faites les trois questions de positionnement avant de lire.
4.  Faites les labs et lancez leur `verify.sh` : un lab compte quand sa vérification passe.
5.  Terminez chaque phase par son jalon (voir la feuille de route), puis par le projet associé.

## Sources et portée {#sources}

Ce site est un ensemble de notes d'étude indépendantes, rédigées à partir de documentations officielles, d'articles publiés et de fiches de formation publiques. Il n'est affilié à aucun établissement, éditeur ou employeur et ne remplace ni un diplôme ni une certification. Les contrats de contenu et les contrôles qui encadrent chaque page sont dans le dossier `specs/` et `tools/` du dépôt.
