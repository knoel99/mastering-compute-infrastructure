---
title: "Point de départ : un profil de référence face au métier"
subtitle: "Écart par domaine, priorités de travail et lecture honnête des limites d'un parcours"
description: "Comparaison d'un profil de référence (CAREER.md) au métier de compute infrastructure engineer, domaine par domaine, avec le parcours ajusté qui en découle."
---

## Ce que fait cette page {#objet}

Cette page part d'un document réel : le `CAREER.md` du dépôt [Certifications](https://github.com/knoel99/Certifications), un résumé de carrière structuré pour être lu par des humains et par des assistants. Elle le compare à ce que demande le métier de *compute infrastructure engineer* et en déduit **où travailler à fond, où survoler**.

Le profil de référence est celui d'un ingénieur IA et LLM de douze ans d'expérience, venu des géosciences et de la simulation numérique, devenu consultant en données massives puis en IA générative. Les noms de clients n'apparaissent pas ici ; seules les compétences comptent.

::: note
[Une estimation, pas un verdict]{.tag} Les niveaux ci-dessous sont déduits d'un document écrit. Une compétence absente du document peut exister ; une compétence présente peut être superficielle. Les questions de positionnement de chaque module servent à corriger cette estimation : faites-les honnêtement avant de décider de survoler un module.
:::

## Le métier visé en une page {#metier}

Un *compute infrastructure engineer* possède la plateforme de calcul d'une organisation qui entraîne des modèles : il provisionne la capacité GPU, ordonnance les jobs, relie les machines, nourrit les GPU en données, garde les entraînements en vie malgré les pannes, observe, facture, et négocie avec les fournisseurs. La version « lead » ajoute la responsabilité d'une équipe et des relations avec les fournisseurs.

Le métier se distingue de deux voisins. L'**ingénieur d'entraînement à grande échelle** travaille *dans* le job : parallélisme, MFU, numérique. L'**ingénieur plateforme classique** exploite des services, rarement des machines dont la performance dépend du réseau et de la mémoire. L'ingénieur de calcul fait le pont : il doit comprendre assez le job pour diagnostiquer, et assez la machine pour la faire tenir.

Les deux premiers modules (performance, systèmes) donnent le langage commun ; les phases suivantes construisent chacune une couche.

## Échelle d'évaluation {#echelle}

| Niveau | Signification |
|---|---|
| 0 | Aucune trace dans le profil |
| 1 | Notion : lu, vu, utilisé ponctuellement |
| 2 | Pratique : utilisé en projet, mais dans un autre contexte |
| 3 | Responsabilité : opéré en production, avec astreinte ou comptes à rendre |
| 4 | Référence : sait former, arbitrer et trancher |

## L'écart, domaine par domaine {#ecart}

Le niveau visé est celui que décrit une offre de *lead* en infrastructure de calcul pour l'entraînement (relevé d'octobre 2026, voir [Ce que demandent les offres](#offres)). Il est de 3 presque partout, car un lead doit pouvoir opérer lui-même ce qu'il dirige.

| Domaine | Ce que le profil documente | Estimé | Visé | Écart | Module |
|---|---|---|---|---|---|
| Linux et exploitation | Bash, certificats d'administration système, serveurs GPU gérés en interne, réglage de JVM | 2 | 3 | 1 | [1](../courses/linux-systems/index.html) |
| Modèles de performance | Simulation numérique, benchmark de GPU ; pas de trace de roofline ni de MFU | 1 | 3 | 2 | [2](../courses/perf-models/index.html) |
| Programmation parallèle (MPI, OpenMP) | Aucune trace | 1 | 2 | 1 | 3 |
| Programmation GPU | Utilisation de GPU pour l'inférence ; pas de noyaux | 1 | 2 | 1 | 4 |
| Ordonnanceurs HPC (Slurm) | Aucune trace | 0 | 3 | 3 | 5 |
| Provisioning et santé des nœuds | Benchmark GPU (DCGM, gpu-burn), Terraform côté cloud | 2 | 3 | 1 | 6 |
| Réseaux haute performance et NCCL | Aucune trace | 0 | 3 | 3 | 7 |
| Stockage pour l'entraînement | HDFS, Cassandra, Elasticsearch (autre contexte) | 1 | 3 | 2 | 8 |
| Entraînement distribué | Cours sur les réseaux de neurones et le matériel d'inférence ; pas de DDP ni FSDP | 1 | 3 | 2 | 9 |
| Pannes et checkpointing d'entraînement | Réduction de 94 % des incidents critiques sur une plateforme d'événements ; pas d'entraînement | 1 | 3 | 2 | 10 |
| Ray et infrastructure d'apprentissage par renforcement | Aucune trace | 0 | 2 | 2 | 11 |
| Langages de systèmes (Go, Rust, C++) | Python, Java, Bash, Fortran ; ni Go, ni Rust, ni C++ | 1 | 2 | 1 | aucun module dédié : C++ et Python dans les modules 3 et 4 |
| Kubernetes pour l'IA | Kubernetes, OpenShift, Helm en production ; inférence GPU ; pas d'ordonnancement d'entraînement | 2 | 3 | 1 | 12 |
| Multi-cloud et fournisseurs GPU | Déploiements sur trois hyperscalers, Terraform ; pas de capacité GPU négociée | 2 | 3 | 1 | 13 |
| Observabilité et fiabilité | Prometheus, Grafana, Loki, SLI/SLO, astreinte, gestion d'incident | 3 | 3 | 0 | 14 |
| FinOps, capacité, achats | Certification FinOps pour l'IA, suivi de coûts GPU et de jetons ; pas d'achat de capacité | 2 | 3 | 1 | 15 |
| Plateforme, sécurité, leadership | Rôles de lead, atelier avec les métiers, sécurité (Zero Trust, Kerberos), prise de parole | 3 | 3 | 0 | 16 |

## Ce que demandent les offres {#offres}

Pour fonder le niveau visé sur autre chose qu'une impression, douze offres publiques de postes d'infrastructure de calcul ont été lues en octobre 2026 : six chez des fournisseurs de GPU, trois dans des laboratoires d'IA, une dans un centre de calcul et deux d'une même start-up. Chaque compétence relevée est appuyée par une citation vérifiée dans le texte de l'offre. L'échantillon est petit : lisez les nombres comme des ordres de grandeur.

| Compétence | Offres qui la citent (sur 12) | Dont exigées | Niveau estimé du profil |
|---|---|---|---|
| Kubernetes | 10 | 8 | 2 à 3 : un atout |
| Python | 9 | 9 | 3 : un atout |
| Astreinte et fiabilité (SRE) | 9 | 9 | 3 : un atout |
| Langages de systèmes (Go, Rust, C++) | 8 | 7 | 1 : un écart |
| Expérience HPC | 8 | 6 | 1 : un écart |
| Administration Linux | 7 | 7 | 2 |
| InfiniBand et RoCE | 7 | 4 | 0 : un écart |
| Planification de capacité | 6 | 6 | 2 |
| Slurm | 5 | 2 | 0 : un écart |
| Prometheus et Grafana | 5 | 4 | 3 : un atout |
| Conception d'ordonnanceur | 5 | 4 | 0 à 1 : un écart |
| Provisioning bare-metal | 5 | 4 | 2 |

Deux lectures. D'abord, **les compétences les plus citées (Kubernetes, Python, fiabilité) sont celles où le profil est déjà fort** : il est proche des postes de fournisseurs de GPU, où l'infrastructure ressemble à celle du cloud. Ensuite, **les compétences propres au calcul haute performance (HPC, InfiniBand, Slurm, ordonnanceurs) sont celles où le profil est vide**, et ce sont aussi celles que les masters enseignent le moins (voir l'[enquête](../masters/index.html)).

Sept offres indiquent un nombre d'années d'expérience : de 3 à 15 ans, avec une médiane de 8. Aucune de ces années ne se remplace par un parcours d'apprentissage ; elles se remplacent en partie par des preuves publiques (voir plus bas).

## Ce que cet écart dit {#lecture}

**Le cœur du parcours est exactement là où le profil est le plus vide.** Les écarts de 2 ou 3 se concentrent sur l'ordonnancement HPC, le réseau d'entraînement, l'entraînement distribué, les pannes d'entraînement, le stockage, les modèles de performance et Ray : c'est le noyau technique qu'aucune expérience de plateforme classique ne remplace.

**Les appuis sont réels.** Kubernetes en production, observabilité, FinOps, certifications cloud, expérience de lead et goût de la communication sont des atouts rares chez les candidats venus du calcul scientifique. Ils réduisent le temps nécessaire sur les modules 12, 14, 15 et 16, mais ne les rendent pas superflus : ils portent surtout sur les services, pas sur les machines.

**Le parcours ajusté.** Priorité A (écart de 2 ou 3, à travailler à fond avec tous les labs) : modules 2, 5, 7, 8, 9, 10 et 11. Priorité B (écart de 1, parcours normal, en s'appuyant sur l'existant) : modules 3, 4, 6, 12, 13 et 15. Priorité C (écart de 0, survol guidé par les questions de positionnement) : modules 14 et 16, hors parties propres au GPU et à la sécurité. Le module 1, déjà proche du profil, se parcourt en survol.

## Ce qu'un parcours peut changer, et ce qu'il ne peut pas changer {#limites}

Les offres de *lead* en infrastructure de calcul demandent de l'**expérience prouvée** sur l'entraînement à grande échelle, de l'ordre de huit ans dans le domaine. Un parcours d'apprentissage donne des compétences, des projets publics et un vocabulaire ; il ne crée pas des années d'exploitation de clusters en production.

Trois conséquences pratiques.

-   **Viser une marche réaliste d'abord.** Un poste d'ingénieur senior en plateforme d'IA ou en infrastructure d'entraînement valorise déjà fortement Kubernetes en production, l'observabilité et le FinOps. Le poste de lead vient ensuite, avec l'expérience.
-   **Fabriquer des preuves publiques.** Les six projets du parcours, un journal d'apprentissage, des contributions à des outils ouverts (ordonnanceurs, files d'attente, exportateurs) et des post-mortems écrits remplacent en partie ce qu'on ne peut pas citer d'un employeur.
-   **Chercher l'exposition réelle.** Un stage de courte durée dans un centre de calcul, la participation à une compétition de clusters étudiants ou à un projet de recherche donnent un accès à de vraies machines. L'enquête sur les masters recense ces voies.

::: key
[Règle d'honnêteté]{.tag} Ne présentez jamais un projet de portfolio comme une expérience de production, et dites toujours ce qui a été exécuté sur quelle machine. Un recruteur compétent vérifie, et la franchise est un signal de fiabilité, qualité centrale du métier.
:::

## Deux postes voisins, 30 à 40 % de recouvrement {#postes}

Deux annonces publiées en septembre et octobre 2026 par une même start-up parisienne de robotique illustrent la différence entre les deux métiers voisins. Leur comparaison, requis par requis, donne un recouvrement estimé au jugé à 30 à 40 %.

| | Ingénieur d'entraînement à grande échelle | Lead de l'infrastructure de calcul |
|---|---|---|
| Couche | Ce qui tourne dans le job d'entraînement | La plateforme sur laquelle tournent les jobs |
| Cœur | Parallélisme (DDP, FSDP, tensoriel, pipeline, experts), MFU, noyaux, débogage numérique, déterminisme | Capacité GPU multi-fournisseurs, ordonnanceur, Ray, traitement de données orchestré, observabilité |
| Infrastructure d'apprentissage par renforcement | Rollouts distribués, acteur-apprenant, tampons de rejeu | Boucle d'apprentissage en ligne vue sous l'angle de la capacité |
| Aspect commercial | Aucun | Coûts, prévision de capacité, négociation avec les fournisseurs |
| Séniorité demandée | Pas d'années exigées | Huit ans et plus, niveau senior, lead ou staff |
| Modules les plus proches | 2, 3, 4, 9, 10, 11 | 5, 6, 7, 8, 12, 13, 14, 15, 16 |

Les deux postes partagent Python, PyTorch distribué, NCCL, la reprise des jobs longs et le diagnostic. Ce parcours couvre les deux : les phases 0 à 3 servent surtout le premier, les phases 2, 4 et 5 le second.

## Comment utiliser ce diagnostic {#usage}

1.  Refaites ce tableau vous-même, avec vos propres niveaux, avant de commencer.
2.  Pour chaque module, faites les questions de positionnement : elles confirment ou corrigent votre estimation.
3.  Refaites le tableau à la fin de chaque phase. L'écart doit diminuer là où vous avez travaillé ; sinon, refaites les labs.
4.  Gardez le tableau dans votre journal d'apprentissage : il documente votre progression de façon vérifiable.

## Sources et portée {#sources}

**Documenté.** Les compétences listées dans la colonne « profil » proviennent du `CAREER.md` du dépôt Certifications (version d'octobre 2026) ; les fréquences de compétences viennent de douze offres publiques, relevées le 22 octobre 2026 et citées dans le dossier `data/jobs/`.

**Recommandé.** Les niveaux estimés et visés, les priorités A, B et C, et l'ordre de travail sont des choix de ce parcours. Ils ne sont ni mesurés, ni validés par un tiers.

**À vérifier.** Les niveaux de chaque domaine pour une autre personne que le profil de référence : refaites le diagnostic.

**Hors périmètre.** Les aspects contractuels d'un recrutement, les salaires et toute promesse d'embauche.
