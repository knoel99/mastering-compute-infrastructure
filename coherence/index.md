---
title: "Cohérence du parcours"
subtitle: "Une revue croisée des seize modules et des six projets : méthode, constats, corrections et conventions communes"
description: "Comment les pages du parcours ont été relues ensemble pour éliminer les contradictions, les doublons, les prérequis manquants et les renvois cassés, et quelles conventions de notation en sont sorties."
numbered: true
---

## Ce que fait cette page {#objet}

Un parcours écrit module par module accumule des incohérences : deux définitions d'un même terme, un chiffre qui change d'une page à l'autre, un exercice qui suppose un chapitre placé plus loin, un projet qui annonce des modules qu'il n'utilise pas. Cette page décrit la revue croisée menée le 25 octobre 2026 sur les seize modules et les six projets, ce qu'elle a trouvé, ce qui a été corrigé, et les conventions qui valent désormais dans tout le parcours.

Elle complète l'[analyse du marché](../market/index.html), qui confronte le contenu du parcours aux offres d'emploi.

## Méthode {#methode}

### Quatre étapes {#etapes}

1.  **Extraction.** Chaque page a été lue en entier par un agent, qui en a relevé les concepts et leurs définitions, les notations, les chiffres réutilisables, les renvois vers d'autres pages, les prérequis supposés, la profondeur de couverture de chacune des 44 compétences de la taxonomie du marché et les défauts visibles dans la page.
2.  **Analyse croisée.** Quatre analyses ont comparé toutes les extractions, chacune sous un angle : contradictions de faits et de notations ; progression et prérequis ; doublons, lacunes et terminologie ; labs, projets et cohérence du parcours dans son ensemble. Chaque constat devait citer les passages en cause.
3.  **Vérification adversariale.** Un vérificateur par angle a rouvert les pages et tenté de réfuter chaque constat (citation absente, différence expliquée dans le texte, renvoi en fait correct, calcul juste). Faute de confirmation, le constat était réfuté.
4.  **Correction page par page.** Un agent par page a revérifié chaque constat confirmé sur le texte du jour, appliqué une correction minimale, vérifié chaque défaut local signalé avant d'y toucher, relancé deux fois les labs dont il changeait le code, puis les contrôles du dépôt. Les corrections qui touchaient une autre page ont été transmises à l'agent de cette page.

### Ce que la revue ne fait pas {#limites-methode}

Elle ne remplace pas une relecture humaine experte : elle détecte des incohérences entre pages et des erreurs vérifiables (calcul, citation, renvoi), pas la pertinence pédagogique d'un choix. Elle n'exécute rien sur un GPU, un cluster multi-nœuds ou un cloud : les parties qui en dépendent gardent leur badge « non vérifié ».

## Résultats {#resultats}

### Constats croisés {#constats}

| Angle d'analyse | Constats | Confirmés | En partie | Réfutés |
|---|---|---|---|---|
| Faits, définitions et notations | 32 | 21 | 9 | 2 |
| Progression et prérequis | 32 | 22 | 9 | 1 |
| Doublons, lacunes et terminologie | 33 | 18 | 15 | 0 |
| Labs, projets et parcours | 29 | 16 | 11 | 2 |
| **Total** | **126** | **77** | **44** | **5** |

Parmi les 121 constats retenus, 2 étaient graves (un apprenant aurait appris quelque chose de faux), 33 moyens (confusion ou heures perdues) et 86 mineurs.

### Défauts locaux {#defauts-locaux}

Les lecteurs ont aussi signalé 300 défauts internes aux pages (chiffre arrondi faux, exercice insoluble avec le texte, terme employé avant d'être défini, version d'outil non datée). Chacun a été vérifié avant correction : 210 ont été corrigés, 23 rejetés après vérification, les autres recoupaient un constat croisé ou ne s'appliquaient plus après une autre correction.

## Principaux constats et corrections {#corrections}

### Une seule définition par notion {#definitions}

-   **Goodput** (constat grave) : le module 2 le définissait comme MFU × part du temps utile, les modules 10, 14 et 15 comme une part du temps. Il désigne désormais partout la part du temps d'horloge consacrée à du calcul conservé ; le produit MFU × goodput s'appelle « usage utile du pic ».
-   **Calcul d'entraînement** : écrit 6N, 6ΨD, 6PD, 6NT ou 6Pb selon les pages ; c'est maintenant $C \approx 6ND$ partout, avec une glose quand une page reprend la notation Ψ de ZeRO.
-   **Coût d'une heure utile** : trois formules, et la lettre $u$ prenait trois sens ; $a$ désigne l'allocation et $u$ l'utilisation mesurée par DCGM dans les modules 5, 12 et 15.
-   **Formule de Young-Daly** : deux notations ($\tau$, $\delta$ contre $T$, $C$) ; le module 10 garde la sienne, les autres pages donnent la correspondance.
-   **SLO, budget d'erreur, post-mortem sans blâme** : définis deux fois chacun ; un module en est propriétaire, l'autre y renvoie.

### Des chiffres qui ne se contredisent plus {#chiffres}

-   **NVLink de la H100** : 900 Go/s utilisés comme un débit par sens ; c'est un total, soit 450 Go/s par sens, et les comparaisons de débit de bus en tiennent compte.
-   **Pannes de Llama 3** : le pourcentage du texte de l'article (58,7 %) ne correspond pas aux comptes de son tableau (268 sur 419, soit 64 %) ; les pages donnent les deux et le disent.
-   **Taux de panne d'un exercice** (0,0002 par GPU-heure) : six fois les taux publiés cités au module 10 ; il est présenté comme une hypothèse pessimiste.
-   **Diagnostics DCGM** : trois niveaux au module 14, quatre au module 6, avec des durées différentes ; alignés sur la documentation.

### Une progression qui tient {#progression}

-   **Prérequis** : plusieurs modules utilisaient le bac à sable Slurm ou le modèle α-β sans les avoir en prérequis ; les prérequis sont complétés, et les lignes « Prérequis » et « Projets liés » des fiches sont désormais générées depuis le plan du parcours.
-   **Semaines** : les pages de module et la feuille de route donnaient des semaines différentes ; elles sont calculées à partir des volumes horaires.
-   **Projets** : le projet 1, jalon de la phase 2, demandait des compétences de la phase 4 ; il est découpé (exigences R1 à R4 en phase 2, R5 à R7 après le module 14). Les projets déclarent les modules qu'ils utilisent vraiment, et la page d'accueil dit lequel n'est exercé que par ses labs.
-   **Renvois circulaires** : les compteurs InfiniBand étaient renvoyés du module 7 au module 14 et inversement ; le module 14 a maintenant une section qui les exporte et les surveille.

### Des labs et des projets alignés sur les cours {#labs-projets}

-   Le « MFU » du projet 2 n'était pas celui du module 2 ; le projet parle maintenant d'utilisation du pic mesuré.
-   Le coût attendu du projet 4 oubliait le démarrage facturé, ce qui inversait un classement : la formule de la page compte désormais le démarrage, ses chiffres sont recalculés par le modèle exact et par le simulateur, et la page dit que la politique de référence garde une version simplifiée.
-   Le lab 14.3 affichait « OK » sans sa partie C ; il dit désormais quelle partie a tourné.
-   La page [Environnement de travail](../lab-setup/index.html) dit enfin ce que chaque lab et chaque projet exige, et comment écrire un ADR et un runbook dès le premier projet.

## Conventions du parcours {#conventions}

| Notion | Notation ou terme | Sens | Page de référence |
|---|---|---|---|
| Goodput | $g$ | part du temps d'horloge consacrée à du calcul conservé | [module 10, chapitre 2](../courses/fault-tolerance/index.html#ch2) |
| Usage utile du pic | MFU × goodput | part du pic de calcul réellement transformée en entraînement conservé | [module 2, chapitre 7](../courses/perf-models/index.html#ch7) |
| Calcul d'entraînement | $C \approx 6ND$ | $N$ paramètres, $D$ tokens ; Ψ chez ZeRO désigne le même $N$ | [module 2, chapitre 7](../courses/perf-models/index.html#ch7) |
| Modèle α-β | $T(n) = \alpha + n/B$ | latence α et débit $B$ ; la littérature écrit souvent $\beta = 1/B$ | [module 2, chapitre 6](../courses/perf-models/index.html#ch6) |
| NVLink de la H100 | 900 Go/s | débit total, soit 450 Go/s par sens | [module 2, chapitre 2](../courses/perf-models/index.html#ch2) |
| Période de checkpoint | $\tau^\star \approx \sqrt{2\delta M}$ | $\delta$ coût bloquant d'un checkpoint, $M$ temps moyen entre pannes ; d'autres pages écrivent $T$ et $C$ | [module 10, chapitre 2](../courses/fault-tolerance/index.html#ch2) |
| Pannes d'un job | système en série | les taux de panne des nœuds s'additionnent | [module 10, chapitre 1](../courses/fault-tolerance/index.html#ch1) |
| Allocation et utilisation | $a$ et $u$ | part des heures allouées ; activité mesurée par DCGM | [module 15, chapitre 1](../courses/finops-capacity/index.html#ch1) |
| *Gang scheduling* | — | dans Slurm, partage par tranches de temps ; dans Kubernetes, démarrage tout ou rien d'un groupe | [module 5, chapitre 4](../courses/slurm/index.html#ch4), [module 12, chapitre 3](../courses/kubernetes-gpu/index.html#ch3) |
| *Straggler* | traînard | GPU ou rang plus lent qui retarde tout le job | [module 2, chapitre 5](../courses/perf-models/index.html#ch5) |
| *Pipeline stage* | étage | groupe de couches porté par un rang du parallélisme pipeline | [module 9, chapitre 1](../courses/distributed-training/index.html#ch1) |
| *Scaling* | passage à l'échelle | fort (taille fixe) ou faible (taille par rang fixe) | [module 3, chapitre 8](../courses/parallel-programming/index.html#ch8) |

## Les dépendances entre modules {#dependances}

Le tableau est généré depuis le plan du parcours (`data/curriculum.json`) : il est donc toujours d'accord avec les fiches des modules.

<!-- gen:dependencies -->
| Module | Phase | S'appuie sur | Prépare | Projets |
|---|---|---|---|---|
| [1. Linux, systèmes et diagnostic de performance](../courses/linux-systems/index.html) | 0 | — | 5, 6, 7, 8, 12, 14 | P1 |
| [2. Architecture matérielle et modèles de performance](../courses/perf-models/index.html) | 0 | — | 3, 4, 7, 8, 9, 15 | P2, P6 |
| [3. Programmation parallèle : OpenMP, MPI et études de passage à l'échelle](../courses/parallel-programming/index.html) | 1 | 2 | 9 | P2 |
| [4. Programmation GPU : CUDA, Triton et profilage](../courses/gpu-programming/index.html) | 1 | 2 | 9 | aucun (labs seulement) |
| [5. Slurm et exploitation d'un cluster HPC](../courses/slurm/index.html) | 2 | 1 | 6, 7, 10, 12, 14, 15, 16 | P1, P5, P6 |
| [6. Provisioning, images et santé des nœuds GPU](../courses/provisioning/index.html) | 2 | 1, 5 | 10 | P1, P6 |
| [7. Réseaux haute performance : InfiniBand, RoCE et NCCL](../courses/networking/index.html) | 2 | 1, 2, 5 | 9 | P6 |
| [8. Stockage et E/S pour l'entraînement](../courses/storage/index.html) | 2 | 1, 2 | 10 | P3, P6 |
| [9. Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline](../courses/distributed-training/index.html) | 3 | 2, 3, 4, 7 | 10, 11, 12 | P2, P3, P6 |
| [10. Pannes, checkpointing et reprise automatique](../courses/fault-tolerance/index.html) | 3 | 5, 6, 8, 9 | 13, 16 | P3, P4, P5, P6 |
| [11. Ray, infrastructure d'apprentissage par renforcement et boucles en ligne](../courses/ray-rl-infra/index.html) | 3 | 9 | — | P6 |
| [12. Kubernetes pour l'IA : GPU, files d'attente et gang scheduling](../courses/kubernetes-gpu/index.html) | 4 | 1, 5, 9 | 13, 16 | P4, P6 |
| [13. Flotte multi-fournisseurs : SkyPilot, GPU clouds, hyperscalers et centres HPC](../courses/multi-cloud/index.html) | 4 | 10, 12 | — | P4, P6 |
| [14. Observabilité et fiabilité d'une flotte GPU](../courses/observability/index.html) | 4 | 1, 5 | 16 | P1, P5, P6 |
| [15. FinOps, capacité, énergie et achats de calcul](../courses/finops-capacity/index.html) | 4 | 2, 5 | 16 | P4, P6 |
| [16. Plateforme interne, sécurité, production et leadership](../courses/platform-leadership/index.html) | 5 | 5, 10, 12, 14, 15 | — | P6 |
<!-- /gen:dependencies -->

## Ce qui reste à surveiller {#reste}

-   **Volumes de lecture.** Les heures de lecture de chaque module sont des estimations, pas des mesures ; les modules les plus denses (stockage, provisioning, FinOps) demandent sans doute plus que ce qu'annonce leur fiche.
-   **Parties non exécutées.** Ce qui demande un GPU, un cluster multi-nœuds ou un cloud n'a pas tourné ; les pages le disent dans leur badge et leur section « À vérifier ».
-   **Versions.** Les outils évoluent : chaque page date les versions testées, et la page Environnement de travail donne les versions de référence.
-   **Nouvelles pages, nouvelles incohérences.** Toute modification future d'une définition ou d'un chiffre de la table des conventions doit être faite dans la page de référence, puis répercutée.

## Sources et portée {#sources}

### Documenté {#documente}

Les constats, leurs verdicts et les corrections appliquées ont été produits par la revue décrite plus haut ; les contrôles mécaniques du dépôt (`tools/check_gates.py`, `tools/check_airiness.py`, `tools/build.py --check`) passent sur toutes les pages après correction.

### Recommandé {#recommande}

Les conventions de la table sont des choix de ce parcours, faits pour qu'un même mot garde un même sens ; d'autres ouvrages en font d'autres.

### Hors périmètre {#hors-perimetre}

La qualité pédagogique de chaque explication, qui relève d'une relecture humaine.
