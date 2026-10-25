---
title: "Enquête sur les masters HPC"
subtitle: "36 programmes en France, aux États-Unis, en Chine et dans le monde, comparés à 96 offres d'emploi"
description: "Ce que les masters de calcul haute performance enseignent, ce qu'ils n'enseignent presque pas, et ce que demandent les offres d'ingénieur d'infrastructure de calcul."
numbered: true
---

## Résumé {#resume}

-   **Les masters forment des programmeurs de calcul parallèle et de simulation, pas des opérateurs de plateformes.** MPI, GPU, architecture et numérique y ont souvent un cours dédié ; l'ordonnancement, le réseau d'interconnexion, la résilience et l'observabilité presque jamais.
-   **L'écart se chiffre.** Un cours dédié à l'interconnexion existe dans 1 programme sur 21 dont le syllabus est connu, alors que 41 offres sur 96 demandent InfiniBand ou RoCE. L'ordonnancement : 1 programme sur 8 contre 21 offres sur 96 pour Slurm et 50 offres sur 96 pour Kubernetes.
-   **Les programmes qui s'en approchent sont rares et orientés exploitation** : le diplôme d'administration de systèmes HPC du C-DAC (Inde), le master HPC de l'ICTP-SISSA (Italie) et certaines spécialisations d'EUMaster4HPC.
-   **En France, un réseau de masters dédiés** (CHPS) donne une base solide en parallélisme ; **aux États-Unis, le HPC vit dans des cours** plus que dans des diplômes ; **en Chine, il vit dans des centres de supercalcul et des compétitions** plus que dans les maquettes de master.
-   **Conséquence pour le parcours** : MPI, GPU et performance sont des fondations communes, que les masters enseignent bien ; l'essentiel de l'effort va aux sujets que les masters traitent peu et que les offres demandent.

## Méthode et limites {#methode}

L'enquête repose sur des pages officielles de programmes et de catalogues de cours, lues le 22 octobre 2026, et sur des offres d'emploi publiques. Pour chaque programme, un outil a relevé la durée, les crédits, la structure, les cours et leur couverture de 26 thèmes. Chaque fait porte une citation de la page source ; **un contrôle mécanique a vérifié mot pour mot 1437 citations sur 1438** (programmes, offres d'emploi et ressources) dans le texte des pages. Le détail des données est dans le dossier `data/` du dépôt.

Cinq limites à garder en tête.

-   **Échantillon non exhaustif.** Plusieurs programmes notables n'ont pas été étudiés faute de budget de recherche : en Europe, TUM, FAU, Stuttgart, RWTH, USI et Cambridge ; en France, Sorbonne et Ensimag ; à l'international, Tsukuba, KAIST et NUS (aucun programme lisible trouvé pour ces trois derniers).
-   **Inconnu n'est pas absent.** Quand un syllabus n'était pas lisible, le thème est marqué *inconnu*. Les proportions ci-dessous sont calculées sur les seuls programmes dont la valeur est connue, et leur effectif est toujours indiqué.
-   **Un cours dédié n'est pas un cours bien fait.** Le critère « cours dédié » signifie qu'un intitulé de cours ou de module nomme le thème ; il ne dit rien de la qualité ni de la profondeur.
-   **Les offres d'emploi ont leur propre page.** 96 offres publiques des États-Unis, d'Europe et de Chine sont analysées dans [Ce que demande le marché](../market/index.html) ; cette page n'en reprend que les compétences qui correspondent à un thème de master.
-   **Des informations changent.** Les programmes évoluent chaque année : consultez la page officielle avant toute décision.

## Ce que l'échantillon couvre {#echantillon}

| Zone | Programmes étudiés | Où se trouve le HPC |
|---|---|---|
| France | 13 | des masters dédiés (réseau CHPS) et des parcours d'écoles d'ingénieurs |
| États-Unis | 6 | des cours isolés dans des masters de science computationnelle ou d'informatique |
| Chine | 6 | des masters d'informatique généralistes, adossés à des centres de supercalcul et à des compétitions |
| Reste du monde | 11 | des masters dédiés (Édimbourg, Trieste, Milan) et un diplôme d'exploitation en Inde |

Chaque zone a sa page, avec les fiches détaillées : [France](france/index.html), [États-Unis](usa/index.html), [Chine](china/index.html), [reste du monde](world/index.html).

## Ce que les masters enseignent {#enseigne}

Le graphique montre, pour chaque thème, le nombre de programmes dont un cours ou un module **dédié** nomme le thème, sur les programmes dont la couverture est connue (le dénominateur varie donc d'un thème à l'autre).

<div class="bars" role="list">
<div class="bar" role="listitem"><span class="blab">Mémoire, stage</span><span class="track"><span class="fill two" style="width:94%"></span></span><span class="val">29/31</span></div>
<div class="bar" role="listitem"><span class="blab">Apprentissage automatique et profond</span><span class="track"><span class="fill two" style="width:81%"></span></span><span class="val">22/27</span></div>
<div class="bar" role="listitem"><span class="blab">Méthodes numériques</span><span class="track"><span class="fill two" style="width:77%"></span></span><span class="val">20/26</span></div>
<div class="bar" role="listitem"><span class="blab">Architecture des ordinateurs</span><span class="track"><span class="fill two" style="width:66%"></span></span><span class="val">19/29</span></div>
<div class="bar" role="listitem"><span class="blab">Systèmes distribués</span><span class="track"><span class="fill two" style="width:64%"></span></span><span class="val">14/22</span></div>
<div class="bar" role="listitem"><span class="blab">Algorithmique parallèle</span><span class="track"><span class="fill two" style="width:58%"></span></span><span class="val">15/26</span></div>
<div class="bar" role="listitem"><span class="blab">Cloud et multi-fournisseurs</span><span class="track"><span class="fill two" style="width:58%"></span></span><span class="val">11/19</span></div>
<div class="bar" role="listitem"><span class="blab">Programmation GPU</span><span class="track"><span class="fill two" style="width:57%"></span></span><span class="val">12/21</span></div>
<div class="bar" role="listitem"><span class="blab">Simulation et applications</span><span class="track"><span class="fill two" style="width:57%"></span></span><span class="val">13/23</span></div>
<div class="bar" role="listitem"><span class="blab">Données massives</span><span class="track"><span class="fill two" style="width:56%"></span></span><span class="val">10/18</span></div>
<div class="bar" role="listitem"><span class="blab">Quantique, architectures émergentes</span><span class="track"><span class="fill two" style="width:56%"></span></span><span class="val">10/18</span></div>
<div class="bar" role="listitem"><span class="blab">Passage de messages (MPI)</span><span class="track"><span class="fill two" style="width:48%"></span></span><span class="val">10/21</span></div>
<div class="bar" role="listitem"><span class="blab">Visualisation</span><span class="track"><span class="fill two" style="width:44%"></span></span><span class="val">7/16</span></div>
<div class="bar" role="listitem"><span class="blab">Génie logiciel HPC</span><span class="track"><span class="fill two" style="width:42%"></span></span><span class="val">5/12</span></div>
<div class="bar" role="listitem"><span class="blab">Mémoire partagée (OpenMP)</span><span class="track"><span class="fill two" style="width:39%"></span></span><span class="val">9/23</span></div>
<div class="bar" role="listitem"><span class="blab">Conteneurs, Kubernetes</span><span class="track"><span class="fill two" style="width:38%"></span></span><span class="val">5/13</span></div>
<div class="bar" role="listitem"><span class="blab">Gestion de projet, éthique</span><span class="track"><span class="fill two" style="width:35%"></span></span><span class="val">7/20</span></div>
<div class="bar" role="listitem"><span class="blab">Modèles de performance, profilage</span><span class="track"><span class="fill two" style="width:34%"></span></span><span class="val">10/29</span></div>
<div class="bar" role="listitem"><span class="blab">Administration de clusters</span><span class="track"><span class="fill two" style="width:30%"></span></span><span class="val">3/10</span></div>
<div class="bar" role="listitem"><span class="blab">Stockage et E/S parallèles</span><span class="track"><span class="fill two" style="width:27%"></span></span><span class="val">4/15</span></div>
<div class="bar" role="listitem"><span class="blab">Systèmes pour l'IA (entraînement distribué)</span><span class="track"><span class="fill two" style="width:21%"></span></span><span class="val">3/14</span></div>
<div class="bar" role="listitem"><span class="blab">Ordonnancement de jobs</span><span class="track"><span class="fill two" style="width:12%"></span></span><span class="val">1/8</span></div>
<div class="bar" role="listitem"><span class="blab">Efficacité énergétique</span><span class="track"><span class="fill two" style="width:8%"></span></span><span class="val">1/13</span></div>
<div class="bar" role="listitem"><span class="blab">Réseaux et interconnexions</span><span class="track"><span class="fill two" style="width:5%"></span></span><span class="val">1/21</span></div>
<div class="bar" role="listitem"><span class="blab">Résilience, checkpointing</span><span class="track"><span class="fill two" style="width:0%"></span></span><span class="val">0/12</span></div>
<div class="bar" role="listitem"><span class="blab">Supervision, observabilité, SRE</span><span class="track"><span class="fill two" style="width:0%"></span></span><span class="val">0/4</span></div>
</div>

Trois lectures.

-   Les thèmes **scientifiques et de programmation** dominent : mémoire de fin d'études (29 sur 31), apprentissage profond (22 sur 27), méthodes numériques (20 sur 26), architecture des ordinateurs (19 sur 29), GPU (12 sur 21), MPI (10 sur 21).
-   L'**exploitation** est à peine représentée : administration de clusters (3 sur 10), stockage (4 sur 15), conteneurs et Kubernetes (5 sur 13).
-   Quatre thèmes d'exploitation n'ont **presque aucun cours dédié** : ordonnancement (1 sur 8), interconnexion (1 sur 21), résilience (0 sur 12) et observabilité (0 sur 4, dont le syllabus n'est connu que pour quatre programmes).

## Ce que demandent les offres {#demande}

Sur les 96 offres de postes d'infrastructure de calcul relevées (détail dans [Ce que demande le marché](../market/index.html)), voici les compétences les plus citées, mises en regard du nombre de programmes qui leur consacrent un cours.

| Compétence demandée | Offres qui la citent | Thème de master correspondant | Programmes avec un cours dédié |
|---|---|---|---|
| Administration Linux | 54 sur 96 (50 exigées) | Administration de clusters | 3 sur 10 |
| Astreinte, fiabilité (SRE) | 52 sur 96 (49 exigées) | Supervision, observabilité, SRE | 0 sur 4 |
| Kubernetes | 50 sur 96 (37 exigées) | Conteneurs, Kubernetes | 5 sur 13 |
| Expérience HPC | 49 sur 96 (29 exigées) | Passage de messages (MPI) | 10 sur 21 |
| Expérience d'entraînement ML | 44 sur 96 (27 exigées) | Systèmes pour l'IA (entraînement distribué) | 3 sur 14 |
| InfiniBand / RoCE | 41 sur 96 (26 exigées) | Réseaux et interconnexions | 1 sur 21 |
| Prometheus / Grafana | 35 sur 96 (25 exigées) | Supervision, observabilité, SRE | 0 sur 4 |
| Stockage parallèle | 29 sur 96 (18 exigées) | Stockage et E/S parallèles | 4 sur 15 |
| Provisioning bare-metal | 28 sur 96 (20 exigées) | Administration de clusters | 3 sur 10 |
| Planification de capacité | 27 sur 96 (22 exigées) | Cloud et multi-fournisseurs | 11 sur 19 |
| Conteneurs | 26 sur 96 (17 exigées) | Conteneurs, Kubernetes | 5 sur 13 |
| Cloud hyperscaler | 26 sur 96 (18 exigées) | Cloud et multi-fournisseurs | 11 sur 19 |
| NCCL / collectives | 25 sur 96 (15 exigées) | Systèmes pour l'IA (entraînement distribué) | 3 sur 14 |
| Terraform / IaC | 25 sur 96 (16 exigées) | Cloud et multi-fournisseurs | 11 sur 19 |

Les nombres de programmes sont petits : lisez-les comme des ordres de grandeur. Trois constats tiennent néanmoins :

-   **Kubernetes** est cité par 50 offres sur 96 (dont 37 l'exigent), loin devant Slurm (21 offres sur 96, dont 12 l'exigent), que demandent surtout les centres HPC. Les masters, eux, n'enseignent presque ni l'un ni l'autre.
-   **L'astreinte et la fiabilité** figurent dans 52 offres sur 96 (dont 49 en exigence), alors que l'observabilité n'a aucun cours dédié dans les programmes dont le contenu est connu.
-   **La planification de capacité** est citée par 27 offres sur 96. Elle relève d'un métier que les masters n'enseignent pas : les thèmes de cloud qu'ils proposent portent sur la technique, pas sur l'achat ni la prévision.

## Les programmes les plus proches du métier {#proches}

Aucun programme ne couvre à lui seul le métier. Quatre s'en rapprochent par leur contenu d'exploitation :

-   **[C-DAC, diplôme d'administration de systèmes HPC](world/index.html#in-cdac-pg-dhpcsa)** (Inde) : 900 heures sur 24 semaines, avec Slurm et PBS Pro, Lustre et BeeGFS, InfiniBand, supervision, étalonnage (HPL, HPCG), conception de centre de données, Docker et Kubernetes. C'est le seul programme de l'échantillon à avoir un cours dédié à l'ordonnancement et à l'interconnexion.
-   **[ICTP-SISSA, master en calcul haute performance](world/index.html#it-sissa-ictp-mhpc)** (Italie) : un module où les étudiants installent et configurent un cluster Linux, des cours sur le stockage et le cloud pour le HPC, un mémoire réalisé avec une équipe de recherche ou un partenaire industriel.
-   **[EUMaster4HPC](world/index.html#eu-eumaster4hpc)** (consortium européen) : une seconde année avec les spécialisations « développement et support de systèmes » et « architecte de systèmes ».
-   **[Master DiPaC de Paris-Saclay](france/index.html#fr-saclay-dipac)** (France, en anglais) : ordonnancement et équilibrage de charge sur clusters et clouds, génie logiciel HPC, programmation GPU.

## Ce que cela change pour le parcours {#implications}

| Constat de l'enquête | Module du parcours | Décision |
|---|---|---|
| Interconnexion : 1 programme sur 21, 41 offres sur 96 | Module 7 | module long (28 h) et labs de dimensionnement |
| Ordonnancement : 1 programme sur 8 ; Slurm 21 offres sur 96 | Module 5 | 32 h, labs sur un vrai Slurm |
| Résilience : 0 sur 12, 19 offres sur 96 | Modules 9 et 10 | 28 h et un projet dédié |
| Observabilité et astreinte : 0 sur 4, 52 offres sur 96 | Modules 14 et 16 | 24 h, plus les pratiques de production |
| Kubernetes : 5 sur 13, 50 offres sur 96 | Module 12 | 28 h, centrés sur les GPU, les files d'attente et le placement |
| MPI : 10 sur 21 ; GPU : 12 sur 21 | Modules 3 et 4 | fondations communes, volume standard |
| Capacité et achats : 27 offres sur 96 | Module 15 | 24 h, avec l'énergie et les contrats |
| Méthodes numériques : 20 sur 26, aucune offre | aucun | hors parcours, avec des renvois |

L'enquête **confirme** le plan initial plutôt qu'elle ne le modifie : **les modules les plus longs du parcours portent sur les thèmes que les masters traitent le moins**, à savoir l'ordonnancement, le réseau, le stockage (phase 2) et la résilience (phase 3).

## Autres voies d'apprentissage {#voies}

Les diplômes ne sont pas la seule voie. L'enquête a recensé des ressources de pratique, détaillées sur les pages de zone :

-   **Les compétitions de clusters étudiants** : le Student Cluster Competition de la conférence SC, l'ASC Student Supercomputer Challenge en Chine, les équipes qui participent à l'ISC (l'équipe de l'EPCC, issue de ses masters, en fait partie). Elles donnent accès à de vraies machines et à une exploitation sous contrainte.
-   **Les centres de calcul et leurs formations** : la documentation de Jean Zay (IDRIS), les catalogues de formation de l'IDRIS, du NERSC, du réseau CHPS, le certificat HPC de SciNet à Toronto.
-   **Les cours ouverts** : Stanford CS149 et CS336, CMU 15-418, Deep Learning Systems et Machine Learning Systems, Berkeley CS267 ; voir la page [Ressources](../resources/index.html).

## Sources et portée {#sources}

**Documenté.** Les fiches par programme, avec leurs sources, sont sur les pages de zone ; les chiffres de cette page sont calculés par `tools/synthesize_research.py` à partir des fichiers du dossier `data/`, sans intervention d'un modèle.

**Recommandé.** Le regroupement par thèmes de la taxonomie et la lecture des proportions sont des jugements de ce parcours. La correspondance entre une compétence demandée et un thème de master est approximative.

**À vérifier.** Les programmes changent chaque année, les offres expirent, et la couverture de plusieurs programmes reste inconnue : traitez les proportions comme des ordres de grandeur.

**Hors périmètre.** Le classement des programmes par qualité, les frais d'inscription et les modalités d'admission.
