---
title: "Feuille de route"
subtitle: "6 phases, 592 h au total, jalons et parcours courts"
description: "Séquence des phases, volumes horaires, jalons de validation et parcours accélérés."
---

## Comment lire cette feuille de route {#lecture}

Le volume total est de **440 h de modules et 152 h de projets**, soit **592 h**. À titre de repère, 12 h par semaine donnent environ 49 semaines ; 25 h par semaine, environ 24 semaines ; un temps plein de 35 h, environ 17 semaines. Ce sont des ordres de grandeur : un module que vous maîtrisez déjà se parcourt en deux ou trois heures grâce à ses questions de positionnement.

Un rythme hebdomadaire type de 12 h : deux séances de lecture de 3 h, une séance de lab de 3 h, et 3 h d'exercices et de relecture. Tenez un journal d'apprentissage dans un dépôt public : c'est aussi une pièce de portfolio.

## Les six phases {#phases}

| Phase | Modules | Volume | Projets | Durée à 12 h/sem. | Jalon de validation |
|---|---|---|---|---|---|
| 0 — Fondations : machines et performance | linux-systems, perf-models | 48 h | — (0 h) | 4 sem. | Rapport de mesure reproductible (roofline, α-β) et calculateur de MFU testé. |
| 1 — Calcul parallèle et GPU | parallel-programming, gpu-programming | 60 h | — (0 h) | 5 sem. | Étude de scalabilité d'un solveur MPI et noyaux GPU validés par leurs tests. |
| 2 — Exploiter un cluster | slurm, provisioning, networking, storage | 108 h | 1 (24 h) | 11 sem. | Projet 1 : un mini-cluster Slurm reproductible, instrumenté, avec politique d'équité. |
| 3 — Systèmes d'entraînement distribué | distributed-training, fault-tolerance, ray-rl-infra | 92 h | 2, 3 (44 h) | 11 sem. | Projets 2 et 3 : étude de passage à l'échelle et entraîneur tolérant aux pannes. |
| 4 — Plateforme cloud-native et multi-fournisseurs | kubernetes-gpu, multi-cloud, observability, finops-capacity | 104 h | 4, 5 (44 h) | 12 sem. | Projets 4 et 5 : placement multi-fournisseurs et observabilité GPU. |
| 5 — Production et leadership | platform-leadership | 28 h | 6 (40 h) | 6 sem. | Projet 6 : RFC de plateforme de 8 à 256 GPU et soutenance de 20 minutes. |

Chaque phase se termine par son jalon : tant que le livrable n'existe pas et que ses vérifications ne passent pas, la phase n'est pas terminée, quel que soit le temps passé.

## Pourquoi cet ordre {#ordre}

-   **Phase 0 d'abord**, parce que tout le reste consiste à poser un modèle de performance, à le mesurer et à expliquer l'écart.
-   **Calcul parallèle et GPU avant l'ordonnancement**, parce qu'on ne règle pas un ordonnanceur pour des charges qu'on ne sait pas décrire.
-   **L'exploitation du cluster avant l'entraînement distribué**, parce que les pannes et les goulots d'un entraînement se situent presque toujours dans le réseau, le stockage ou l'ordonnanceur.
-   **Le multi-fournisseurs en phase 4**, parce qu'il suppose de savoir reprendre un job après une panne (phase 3).
-   **Le leadership en dernier**, parce qu'on dirige mieux ce qu'on a opéré soi-même.

## Parcours court : l'essentiel en 192 h {#court}

Si vous n'avez pas le temps de tout suivre, ce sous-ensemble couvre le noyau technique de l'entraînement à grande échelle : Architecture matérielle et modèles de performance, Slurm et exploitation d'un cluster HPC, Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline, Pannes, checkpointing et reprise automatique, Flotte multi-fournisseurs : SkyPilot, GPU clouds, hyperscalers et centres HPC, plus les projets Projet 2, Projet 3. Il ne remplace pas le parcours complet : l'exploitation du réseau, du stockage, de Kubernetes et de la capacité manque.

## Parcours pour le lecteur de référence {#reference}

Le [point de départ](../profile/index.html) compare un profil de référence au métier visé. Il en déduit un parcours ajusté : survol des modules proches de l'expérience existante, travail à fond sur ceux où aucun appui n'existe.

## Suivre sa progression {#suivi}

-   Après chaque module : cochez son checkpoint de sortie, produit pour chaque capacité la preuve demandée.
-   Après chaque phase : publiez le livrable du jalon dans un dépôt, avec un fichier `README.md` et une décision d'architecture d'une page.
-   Tous les deux mois : relisez l'enquête sur les masters et les offres d'emploi, et notez ce qui a changé.
