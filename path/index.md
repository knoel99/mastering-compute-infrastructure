---
title: "Feuille de route"
subtitle: "6 phases, 602 h au total, jalons et parcours courts"
description: "Séquence des phases, volumes horaires, jalons de validation et parcours accélérés."
numbered: true
---

## Comment lire cette feuille de route {#lecture}

Le volume total est de **450 h de modules et 152 h de projets**, soit **602 h**. À titre de repère, 12 h par semaine donnent environ 50 semaines (les numéros de semaine des pages de module supposent ce rythme) ; 25 h par semaine, environ 24 semaines ; un temps plein de 35 h, environ 17 semaines. Ce sont des ordres de grandeur : un module que vous maîtrisez déjà se parcourt en deux ou trois heures grâce à ses questions de positionnement.

Un rythme hebdomadaire type de 12 h : deux séances de lecture de 3 h, une séance de lab de 3 h, et 3 h d'exercices et de relecture. Tenez un journal d'apprentissage dans un dépôt public : c'est aussi une pièce de portfolio.

## Les six phases {#phases}

| Phase | Modules | Volume | Projets | Durée à 12 h/sem. | Jalon de validation |
|---|---|---|---|---|---|
| 0 — Fondations : machines et performance | linux-systems, perf-models | 48 h | — (0 h) | 4 sem. | Rapport de mesure reproductible (roofline, α-β) et calculateur de MFU testé. |
| 1 — Calcul parallèle et GPU | parallel-programming, gpu-programming | 62,5 h | — (0 h) | 5 sem. | Étude de scalabilité d'un solveur MPI et noyaux GPU validés par leurs tests. |
| 2 — Exploiter un cluster | slurm, provisioning, networking, storage | 110,5 h | 1 (24 h) | 11 sem. | Projet 1, exigences R1 à R4 : la comptabilité Slurm décrite en code, appliquée par différence, convergente. R5 à R7 (exportateur, alertes, vérification en direct) se terminent en phase 4, après le module 14. |
| 3 — Systèmes d'entraînement distribué | distributed-training, fault-tolerance, ray-rl-infra | 94,5 h | 2, 3 (44 h) | 12 sem. | Projets 2 et 3 : étude de passage à l'échelle et entraîneur tolérant aux pannes. |
| 4 — Plateforme cloud-native et multi-fournisseurs | kubernetes-gpu, multi-cloud, observability, finops-capacity | 104 h | 4, 5 (44 h) | 12 sem. | Projets 4 et 5 : placement multi-fournisseurs et observabilité GPU. |
| 5 — Production et leadership | platform-leadership | 30,5 h | 6 (40 h) | 6 sem. | Projet 6 : RFC de plateforme de 8 à 256 GPU et soutenance de 20 minutes. |

Chaque phase se termine par son jalon : tant que le livrable n'existe pas et que ses vérifications ne passent pas, la phase n'est pas terminée, quel que soit le temps passé.

## Pourquoi cet ordre {#ordre}

-   **Phase 0 d'abord**, parce que tout le reste consiste à poser un modèle de performance, à le mesurer et à expliquer l'écart.
-   **Calcul parallèle et GPU avant l'ordonnancement**, parce qu'on ne règle pas un ordonnanceur pour des charges qu'on ne sait pas décrire.
-   **L'exploitation du cluster avant l'entraînement distribué**, parce que les pannes et les goulots d'un entraînement se situent presque toujours dans le réseau, le stockage ou l'ordonnanceur.
-   **Le multi-fournisseurs en phase 4**, parce qu'il suppose de savoir reprendre un job après une panne (phase 3).
-   **Le leadership en dernier**, parce qu'on dirige mieux ce qu'on a opéré soi-même.

## Parcours court : l'essentiel en 192 h {#court}

Si vous n'avez pas le temps de tout suivre, ce sous-ensemble couvre le noyau technique de l'entraînement à grande échelle : Architecture matérielle et modèles de performance, Slurm et exploitation d'un cluster HPC, Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline, Pannes, checkpointing et reprise automatique, Flotte multi-fournisseurs : SkyPilot, GPU clouds, hyperscalers et centres HPC, plus les projets Projet 2, Projet 3. Il ne remplace pas le parcours complet : l'exploitation du réseau, du stockage, de Kubernetes et de la capacité manque.

Ces modules supposent des bases à survoler : module 1, chapitres 1 et 5, pour Slurm ; module 4, chapitres 1, 2 et 7, et module 7, chapitres 1 et 7, pour l'entraînement distribué ; module 8, chapitre 6 (E/S de checkpoint), pour les pannes et le projet 3 ; module 12, chapitre 3 (Kueue), pour le multi-fournisseurs.

## Parcours selon votre profil d'entrée {#profils}

Le [point de départ](../profile/index.html) décrit cinq profils d'entrée et leurs priorités module par module. Le tableau en déduit un volume d'étude indicatif : les modules à fond et normaux comptent pour leur volume, les modules survolés pour un quart, les projets pour leur volume. C'est un ordre de grandeur, à corriger avec les questions de positionnement.

| Profil d'entrée | À fond (A) | Survol guidé (C) | Volume indicatif |
|---|---|---|---|
| Ingénieur plateforme, SRE ou DevOps | 2, 3, 4, 5, 7, 8, 9, 11 | 14 | 580 h |
| Administrateur ou ingénieur HPC | 9, 10, 11, 12, 13, 15 | 1, 3, 5, 6 | 520 h |
| Ingénieur ML ou chercheur | 6, 7, 10, 12, 13, 14, 15, 16 | — | 600 h |
| Développeur logiciel ou systèmes | 5, 6, 7, 8, 9, 15 | — | 600 h |
| Étudiant ou personne en reconversion | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 | — | 600 h |

## Suivre sa progression {#suivi}

-   Après chaque module : cochez son bilan de sortie, produit pour chaque capacité la preuve demandée.
-   Après chaque phase : publiez le livrable du jalon dans un dépôt, avec un fichier `README.md` et une décision d'architecture d'une page.
-   Tous les deux mois : relisez l'enquête sur les masters et les offres d'emploi, et notez ce qui a changé.
