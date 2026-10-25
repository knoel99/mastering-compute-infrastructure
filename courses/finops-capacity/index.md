---
title: "FinOps, capacité, énergie et achats de calcul"
subtitle: "Module 15 · Phase 4 · 24 h"
description: "Mesurer l'utilisation réelle, prévoir la demande, chiffrer le coût d'une GPU-heure utile, dimensionner puissance et refroidissement, lire et négocier un contrat de capacité."
module:
  id: finops-capacity
  number: 15
  phase: 4
  hours: 24
  level: 2
prerequisites: [perf-models]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs vérifiés dans un bac à sable", class: verified}
labs:
  - {id: usage-showback, kind: sandbox}
  - {id: demand-forecast, kind: sandbox}
  - {id: tco-model, kind: sandbox}
  - {id: contract-checklist, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** de combien de GPU votre équipe a-t-elle besoin l'an prochain, sous quelle forme (achat, location, réservation, à la demande), à quel coût par unité de travail *utile*, et comment le démontrer à une direction financière ou à un fournisseur ? Un ingénieur d'infrastructure qui ne sait pas chiffrer son cluster laisse d'autres décider à sa place, avec des hypothèses qu'il n'a pas vues.

Ce module est le volet technique de l'achat de calcul. Il part de l'utilisation réelle d'une flotte, construit une prévision de la demande avec ses incertitudes, en déduit une capacité à engager, la compare à d'autres régimes par un modèle de coût total, puis aborde ce que les fiches de prix cachent : la puissance et le refroidissement, les clauses d'un contrat de capacité et la façon de négocier.

::: key
[Règle de ce module]{.tag} Une GPU-heure n'a pas de prix : elle a un coût *par heure utile*, qui dépend de l'utilisation, du goodput et du contrat. Tout chiffre de ce module est donc accompagné de ses hypothèses, et tout exemple de prix est **fictif**, en unités arbitraires notées « u ».
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 24 h, dont environ 9 h de lecture, 9 h de labs et 6 h d'exercices |
| Niveau d'entrée | 2 : à l'aise avec Python (les labs s'écrivent et se testent avec `pytest`), la ligne de commande Linux et les coûts cloud ; avoir lu le module 2 |
| Prérequis | [Module 2 — Architecture matérielle et modèles de performance](../perf-models/index.html) |
| Pour qui | Cœur : contrats de capacité, énergie et prévision de la demande en GPU ; le FinOps cloud classique n'en couvre qu'une partie. |
| Livrable | un modèle de coût total testé, un plan de capacité chiffré avec ses risques et une revue de contrat appliquée à un contrat fictif |
| Environnement | un portable CPU suffit ; aucun GPU ni compte cloud. Un Slurm réel est optionnel (lab 15.1, branche « live ») |
| Projets liés | [Projet 4 — Placement multi-fournisseurs sensible aux coûts](../../projects/multi-provider-scheduler/index.html), [Projet 6 — RFC de plateforme](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Exprimer un coût en GPU-heure disponible, allouée et utile, et le convertir en coût par token ou par expérience (chapitres 1 et 2).
-   Produire un rapport de *showback* depuis l'export de l'ordonnanceur et répartir le coût de l'inactivité (chapitres 1 et 2).
-   Prévoir la demande d'une équipe de recherche, la tester sur le passé et en déduire la capacité à engager (chapitre 3).
-   Comparer achat, location, réservation, à la demande et spot par un modèle de coût total, et dire quelles hypothèses le font basculer (chapitre 4).
-   Estimer puissance, densité par baie et refroidissement d'un parc de GPU, et leur effet sur le calendrier (chapitre 5).
-   Lire un contrat de capacité GPU, repérer les clauses qui comptent pour un entraînement et chiffrer ce qu'elles valent (chapitres 6 et 7).
-   Construire une matrice de décision robuste, un appel d'offres technique et un tableau de pilotage trimestriel (chapitre 8).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 4 — Plateforme cloud-native et multi-fournisseurs** (semaines 32-41) : placer, observer et facturer des charges sur plusieurs fournisseurs.
-   **S'appuie sur** : [module 2 — Architecture matérielle et modèles de performance](../perf-models/index.html).
-   **Projets qui s'en servent** : [Projet 4 — Placement multi-fournisseurs sensible aux coûts](../../projects/multi-provider-scheduler/index.html), [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html).
-   **Compétences demandées dans les offres d'emploi et travaillées ici** : Python, Slurm, Clouds GPU spécialisés, FinOps, coûts, Achats, relation fournisseurs, Planification de capacité, Centre de données (énergie, refroidissement), Checkpoint, tolérance aux pannes, Conception d'ordonnanceur, Cloud hyperscaler (AWS, GCP, Azure…), Leadership, management (voir [l'analyse du marché](../../market/index.html#couverture)).
<!-- /gen:place -->

### Plan de séances {#seances}

Neuf séances, soit 24 h : six de 2,5 h et trois de 3 h. Le niveau 1 correspond aux fondations, le niveau 2 aux méthodes de cœur, le niveau 3 à l'avancé. Il ne diminue jamais d'une séance à la suivante.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 2.5 h | 1 | ch. 1 FinOps pour l'IA : cadre, unités, allocation | Ex. 1 ; questions de positionnement |
| 2 | 2.5 h | 1 | ch. 2 Utilisation réelle, goodput, files d'attente | Lab 15.1 (rapport de showback) ; Ex. 2, 3 |
| 3 | 2.5 h | 1 | ch. 3 Prévoir la demande, première moitié : modèle et backtest | Lab 15.1 branche « live » ; Ex. 4 |
| 4 | 3 h | 2 | ch. 3 seconde moitié : de la prévision à la capacité à engager | Lab 15.2 ; Ex. 5, 6 |
| 5 | 3 h | 2 | ch. 4 Modèle de coût total | Lab 15.3 ; Ex. 7 |
| 6 | 2.5 h | 2 | ch. 5 Énergie et datacenter | Ex. 8, 9 |
| 7 | 2.5 h | 2 | ch. 6 Lire un contrat de capacité | Lab 15.4 ; Ex. 10 |
| 8 | 3 h | 3 | ch. 7 Négocier | Ex. 11, 12 |
| 9 | 2.5 h | 3 | ch. 8 Matrices de décision, appel d'offres, pilotage ; checkpoint de sortie | Ex. 13 ; démarrage du Projet 6 |

<!-- gen:travailler -->
### Comment travailler ce module {#travailler}

Le parcours s'adresse à plusieurs profils d'entrée, décrits dans le [point de départ](../../profile/index.html). Le tableau donne la priorité conseillée pour ce module ; les questions de positionnement (section 0.1) la confirment ou la corrigent.

| Profil d'entrée | Priorité | Ce que cela veut dire ici |
|---|---|---|
| Ingénieur plateforme, SRE ou DevOps | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Administrateur ou ingénieur HPC | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Ingénieur ML ou chercheur | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Développeur logiciel ou systèmes | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Étudiant ou personne en reconversion | à fond | tous les chapitres, tous les labs et les exercices ★★★ |

**À ne pas survoler.** La prévision de demande et le coût par GPU-heure productive sont demandés par les offres de capacité et de direction.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le checkpoint de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Les prix sont fictifs, en unités arbitraires (u). Si elles vous semblent routinières, parcourez les exercices ★★★ et passez au chapitre 5.

1.  **Coût utile.** Une flotte de 64 GPU coûte, tout compris, 2,08 u par GPU-heure disponible. Elle est allouée 55 % du temps, et 90 % des heures allouées produisent un progrès utile. Combien coûte une GPU-heure utile ?

2.  **Engagement ou demande.** Une GPU-heure engagée sur un an coûte 2,6 u, qu'elle serve ou non. La même heure à la demande coûte 4,0 u. À partir de quel taux d'utilisation de la capacité engagée l'engagement est-il moins cher ?

3.  **Baie.** Quatre serveurs NVIDIA DGX H100 (10,2 kW maximum chacun, d'après le guide utilisateur de NVIDIA) sont posés dans une même baie. Quelle puissance la baie doit-elle recevoir, et pourquoi une salle « classique » ne convient-elle pas ?

::: sol
**Réponses.**

1.  $2{,}08 / (0{,}55 \times 0{,}90) = 4{,}20$ u, soit deux fois le coût par heure disponible. L'écart s'explique par l'utilisation et le goodput : voir les chapitres 2 et 4.

2.  Une heure engagée coûte 2,6 u, qu'on l'utilise ou non. Pour une heure réellement utilisée, elle coûte $2{,}6/u$ si la fraction utilisée est $u$. Elle bat la demande quand $2{,}6/u < 4{,}0$, soit $u > 0{,}65$. C'est le résultat central du chapitre 3 et du chapitre 4.

3.  $4 \times 10{,}2 = 40{,}8$ kW dans une baie. L'enquête 2020 de l'Uptime Institute observait que 71 % des répondants avaient une densité modale inférieure à 10 kW par baie : une salle de ce type reçoit un seul de ces serveurs par baie. Voir le chapitre 5.
:::

## 1. FinOps pour l'IA : cadre, unités, allocation {#ch1}

Ce chapitre fixe le vocabulaire financier et les unités du module. Vous n'avez pas besoin de devenir comptable ; vous avez besoin de savoir quelle question chaque chiffre permet de poser, et à qui.

### 1.1. Ce que la FinOps apporte

La FinOps Foundation définit la FinOps comme un cadre opérationnel et une pratique culturelle qui maximise la valeur métier de la technologie, accélère des décisions fondées sur les données et crée une responsabilité financière par la collaboration entre ingénierie, finance et métiers. Le cadre (*Framework*) repose sur six principes : collaborer, décider par la valeur, responsabiliser chacun sur son usage, rendre les données accessibles et exactes, piloter la pratique de façon centralisée, et tirer parti du modèle de coût variable du cloud.

Le cadre nomme quatre domaines : comprendre l'usage et le coût, quantifier la valeur métier, optimiser usage et coût, gérer la pratique. Chacun regroupe des capacités. Ce module en travaille six : l'allocation, la prévision, l'économie unitaire (*unit economics*), la planification, l'optimisation des tarifs (*rate optimization*) et la facturation interne (*invoicing and chargeback*). Les personas cités incluent l'ingénierie, la finance, la direction et les achats : vous parlerez aux quatre.

Le cadre élargit aussi les périmètres (*scopes*) au-delà du cloud public. La page du cadre y range l'IA, le cloud privé et le centre de données (consultée le 24 octobre 2026). C'est ce qui autorise à appliquer la même grille à un parc acheté, loué ou réservé.

### 1.2. Ce que l'IA change

Le document « FinOps for AI Overview » de la Fondation rappelle que l'équation de base reste « prix fois quantité » : on réduit le coût en baissant le prix payé ou la quantité consommée. Il liste ensuite ce qui est spécifique à l'IA. Les compteurs changent (les *tokens*). Les fournisseurs créent souvent de nouvelles références sans étiquetage natif. Et la rareté des GPU impose, selon le document, des « techniques de gestion de capacité » par le contrat, l'orchestration et les modes d'achat, ce qui est rare pour un cloud classique.

Le même document précise que le déploiement sur site ou hybride est hors de son périmètre. Ce module comble ce trou pour un lecteur qui doit comparer un parc maîtrisé avec du cloud : la méthode est celle de la FinOps, les ordres de grandeur et les contrats sont ceux du calcul GPU.

### 1.3. Trois GPU-heures et leurs coûts

Il faut distinguer trois quantités. Les confondre est l'erreur la plus fréquente des comparaisons de prix.

::: def
[GPU-heure disponible, allouée, utile]{.tag} La GPU-heure **disponible** existe dans la capacité que vous payez (achetée, louée ou engagée), qu'un job tourne ou non. Elle est **allouée** quand l'ordonnanceur la confie à un job. Elle est **utile** quand ce job produit du progrès conservé : on retire les redémarrages, le travail perdu après une panne et les attentes (le *goodput*, chapitre 2).
:::

Avec $c_{\text{dispo}}$ le coût plein d'une heure disponible, $u$ la part des heures allouées et $g$ le goodput des heures allouées, le coût d'une heure utile est :

$$c_{\text{utile}} = \frac{c_{\text{dispo}}}{u \times g}$$

C'est la formule de la question 1 de « Avant de commencer » : avec $u = 0{,}55$ et $g = 0{,}9$, un coût de 2,08 u devient 4,20 u. Les régimes à la demande se paient seulement quand on alloue : leur coût par heure utile vaut $c/g$, indépendamment de $u$ (chapitre 4).

Les équipes ne raisonnent pas en GPU-heures mais en unités métier. La Fondation propose, dans son document sur l'IA, des indicateurs comme le coût par inférence, le coût par token ($\text{coût total} / \text{tokens}$) et l'efficacité d'utilisation des ressources (utilisation réelle sur capacité provisionnée). Pour l'entraînement, le chapitre 7 du module 2 donne le pont : $6N$ FLOP par token pour un modèle de $N$ paramètres.

::: ex
[Exemple 1.1 — Coût d'un entraînement, par token]{.tag} Entraîner un modèle de $N = 7 \cdot 10^9$ paramètres sur $T = 10^{12}$ tokens demande $6NT = 4{,}2 \cdot 10^{22}$ FLOP. À un MFU de 40 % sur des GPU de 989 TFLOP/s dense (H100 SXM en BF16, module 2), un GPU délivre $0{,}4 \times 989 \cdot 10^{12} = 3{,}96 \cdot 10^{14}$ FLOP/s utiles.

Il faut donc :

$$\frac{4{,}2 \cdot 10^{22}}{3{,}96 \cdot 10^{14} \times 3600} \approx 29\,491 \text{ GPU-heures}$$

À un coût plein fictif de 2,08 u par GPU-heure disponible, cela fait environ 61 341 u, soit 0,061 u par million de tokens d'entraînement. Ce coût suppose que les 29 491 heures sont des heures *utiles* : chaque point de goodput perdu l'augmente d'autant.
:::

::: ex
[Exemple 1.2 — Coût par token servi : l'utilisation commande]{.tag} Un GPU qui sert 2 500 tokens par seconde (valeur d'exemple, à mesurer sur votre modèle) produit 9 millions de tokens par heure. À 2,08 u l'heure, un million de tokens coûte $2{,}08/9 = 0{,}231$ u si le GPU est saturé en permanence.

À 30 % d'utilisation moyenne, le même million coûte $0{,}231 / 0{,}3 = 0{,}770$ u : 3,3 fois plus, sans changer ni le matériel ni le modèle. Le coût par token d'un service est d'abord un coût d'utilisation.
:::

Un troisième regroupement parle aux chercheurs : le coût par expérience. Une exploration d'hyperparamètres sur 8 GPU pendant 6 heures représente 48 GPU-heures, soit environ 100 u au coût plein de 2,08 u. Le coût d'une expérience donne un budget lisible, et le premier levier d'un chercheur est souvent la taille de l'expérience, pas la plateforme.

### 1.4. Allocation et responsabilité

La Fondation décrit l'allocation comme la répartition du coût entre ceux qui en sont responsables, par comptes, étiquettes (*tags*) et métadonnées, y compris pour les coûts partagés. Son document sur l'IA recommande de commencer par du *showback* : montrer à chaque équipe ce qu'elle consomme, sans la facturer immédiatement (le *chargeback*, qui facture réellement).

Pour un parc GPU, la règle de comptabilité est simple à énoncer : **le coût plein doit être entièrement alloué**. La somme des coûts directs par équipe, plus la part de l'inactivité, plus ce que garde la plateforme, doit valoir ce que vous payez. Sinon, une partie du budget disparaît entre la facture et les équipes, et personne n'en répond. Le lab 15.1 teste cette conservation sur chaque rapport.

Reste à décider qui supporte l'inactivité. Trois politiques existent.

-   **Proportionnelle** : chaque équipe supporte l'inactivité au prorata de sa consommation. Elle est facile à défendre, mais elle fait payer le plus ceux qui utilisent le plus.
-   **Égale** : chaque équipe en supporte une part identique. Les petites équipes paient très cher ce qu'elles n'ont presque pas utilisé.
-   **Plateforme** : l'équipe plateforme garde l'inactivité et la montre comme sa propre ligne. Les factures des équipes restent propres, et l'inactivité devient un indicateur de la plateforme.

::: note
[Un choix de gouvernance]{.tag} Le chiffre d'une petite équipe change d'un facteur trois selon la politique (exercice 4). Il ne s'agit pas d'un détail de calcul : c'est ce qui décide qui est incité à libérer des GPU. Notre recommandation, un choix de ce parcours, est de laisser l'inactivité à la plateforme jusqu'à une cible fixée avec la finance, et de refacturer seulement le dépassement.
:::

::: recap
Points clés — chapitre 1

-   La FinOps est un cadre de collaboration entre ingénierie, finance et achats ; ses périmètres incluent le centre de données et le cloud privé.
-   Trois GPU-heures : disponible, allouée, utile. Le coût utile vaut $c_{\text{dispo}}/(u \times g)$.
-   Coût par token, par expérience, par heure utile : choisissez l'unité de celui qui décide.
-   Le coût plein doit être entièrement alloué ; la politique d'inactivité est un choix de gouvernance.
:::

## 2. Utilisation réelle : occupation, goodput, gaspillage et files d'attente {#ch2}

« Notre cluster est utilisé à 80 % » ne veut rien dire tant qu'on ne sait pas ce qui est compté. Ce chapitre décompose le rendement d'une flotte en facteurs mesurables, relève ce que des publications rapportent, et montre comment l'obtenir de l'ordonnanceur.

### 2.1. Une chaîne de rendements

Quatre facteurs se multiplient entre la capacité achetée et le calcul utile. Aucun n'est un défaut en soi ; chacun a un propriétaire différent.

-   **La disponibilité** : la part des GPU en état de servir (ni drainés, ni en réparation, ni en maintenance).
-   **L'allocation** : la part des heures disponibles confiées à un job ($u$ du chapitre 1). Elle dépend de la demande et de l'ordonnanceur.
-   **Le goodput** : la part des heures allouées qui produit du progrès conservé ($g$). Il dépend des pannes, des redémarrages, des checkpoints et des attentes.
-   **Le MFU** : la part du pic de calcul que le code exploite pendant qu'il tourne (module 2).

::: ex
[Exemple 2.1 — Un quart du pic seulement]{.tag} Prenons des valeurs d'exemple : disponibilité 0,97, allocation 0,70, goodput 0,90 et MFU 0,40. Leur produit vaut $0{,}97 \times 0{,}70 \times 0{,}90 \times 0{,}40 = 0{,}244$. Sur 100 GPU-heures achetées, environ 24 correspondent à du calcul au pic de la fiche technique.

Aucun des quatre facteurs n'est exceptionnel, et pourtant le produit l'est : c'est pourquoi on ne compare jamais des fournisseurs sur le seul prix de l'heure. Chaque facteur a un propriétaire : la plateforme pour les deux premiers, l'équipe d'entraînement pour les deux derniers.
:::

<figure class="fig">
<svg viewBox="0 0 640 250" role="img" aria-labelledby="chain-t chain-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="chain-t">De la capacité achetée au calcul utile</title>
<desc id="chain-d">Cinq barres horizontales : 100 % de la capacité, 97 % après la disponibilité, 67,9 % après l'allocation, 61,1 % après le goodput et 24,4 % après le MFU.</desc>
<text x="10" y="40" font-size="14" fill="currentColor">Capacité achetée</text>
<rect x="190" y="20" width="360.0" height="28" fill="var(--side-bg)" stroke="currentColor" stroke-width="1.5"/>
<text x="558.0" y="40" font-size="14" font-weight="700" fill="currentColor">100,0 %</text>
<text x="10" y="84" font-size="14" fill="currentColor">× disponibilité 0,97</text>
<rect x="190" y="64" width="349.2" height="28" fill="var(--side-bg)" stroke="currentColor" stroke-width="1.5"/>
<text x="547.2" y="84" font-size="14" font-weight="700" fill="currentColor">97,0 %</text>
<text x="10" y="128" font-size="14" fill="currentColor">× allocation 0,70</text>
<rect x="190" y="108" width="244.4" height="28" fill="var(--side-bg)" stroke="currentColor" stroke-width="1.5"/>
<text x="442.4" y="128" font-size="14" font-weight="700" fill="currentColor">67,9 %</text>
<text x="10" y="172" font-size="14" fill="currentColor">× goodput 0,90</text>
<rect x="190" y="152" width="220.0" height="28" fill="var(--side-bg)" stroke="currentColor" stroke-width="1.5"/>
<text x="418.0" y="172" font-size="14" font-weight="700" fill="currentColor">61,1 %</text>
<text x="10" y="216" font-size="14" fill="currentColor">× MFU 0,40</text>
<rect x="190" y="196" width="88.0" height="28" fill="var(--accent)" stroke="currentColor" stroke-width="1.5"/>
<text x="286.0" y="216" font-size="14" font-weight="700" fill="currentColor">24,4 %</text>
</svg>
<figcaption>Chaîne de rendements d'une flotte (valeurs de l'exemple 2.1, hypothèses d'exemple) : chaque facteur multiplie le précédent, et un quart seulement du pic achetable devient du calcul utile.</figcaption>
</figure>

### 2.2. Ce que des publications mesurent

Les équipes de recherche de Meta ont décrit deux clusters de recherche, RSC-1 (16 000 GPU) et RSC-2 (8 000 GPU). Leur article rapporte, pour ces deux clusters, une utilisation moyenne de 83 % et de 85 % (Kokolis et al., 2024). Il définit aussi le *Effective Training Time Ratio* (ETTR) d'un job : le rapport entre le temps de calcul productif et le temps d'horloge disponible du job, attente en file comprise.

L'ETTR joue le rôle d'un goodput par job (notre $g$ l'égale quand l'attente est nulle) ; l'article réserve le mot « goodput » à la production de travail utile de l'ensemble du cluster.

L'article de Llama 3 rapporte, lui, plus de 90 % de « temps d'entraînement effectif » pendant l'entraînement du modèle de 405 milliards de paramètres, tout en acceptant une maintenance automatisée du cluster. Sur 54 jours, l'équipe a compté 466 interruptions de jobs, dont 419 inattendues (Dubey et al., 2024).

::: war
[419 interruptions imprévues en 54 jours]{.tag} Selon le tableau 5 de [l'article de Llama 3](https://arxiv.org/abs/2407.21783), environ 78 % des interruptions inattendues sont attribuées à des problèmes matériels confirmés ou suspectés, sur une période de pré-entraînement du modèle de 405 milliards de paramètres. Le goodput est donc un chiffre d'exploitation, pas une propriété du code : il dépend de la fiabilité du matériel, de l'automatisation des reprises et du coût des checkpoints (projet [Entraîneur tolérant aux pannes](../../projects/resilient-trainer/index.html)).
:::

D'autres pertes sont moins spectaculaires. Hu et al. (2024) ont analysé les traces d'un centre de données qui développe des grands modèles de langage. Pour un job d'évaluation sur le jeu HumanEval, ils mesurent que 29,5 % du temps passent à charger le modèle et à préparer les données, et 19,0 % de plus à exécuter des tests de correction de programmes : environ la moitié du temps seulement est consacrée à l'inférence sur GPU.

Ces trois chiffres ne se comparent pas : ils portent sur des objets différents (cluster, job d'entraînement, job d'évaluation) et des définitions différentes. Retenez la leçon de méthode : avant de comparer deux utilisations, demandez ce qui est au numérateur et au dénominateur.

### 2.3. Mesurer depuis l'ordonnanceur

L'ordonnanceur sait quel compte a utilisé quelles ressources, pendant combien de temps, et comment le job s'est terminé. Avec Slurm (module 5), `sacct -X -P` produit cette comptabilité : l'option `-X` ne garde que l'allocation, `-P` sépare les champs par `|`. Les champs utiles sont `Account`, `State`, `Submit`, `Start`, `End`, `ElapsedRaw` (durée en secondes) et `AllocTRES` (ressources allouées, par exemple `gres/gpu=8`), d'après la documentation de `sacct`. Sans `--format`, `sacct` n'affiche pas ces champs : l'export du lab 15.1 les demande explicitement (voir `verify-live.sh`). Sur un vrai cluster, ajoutez `--allusers` pour voir tous les comptes et `--starttime`/`--endtime` pour borner la fenêtre.

~~~bash
sacct -X -P --format=JobID,Account,User,Partition,State,Submit,Start,End,ElapsedRaw,AllocTRES,NNodes,CPUTimeRAW
~~~

Le lab 15.1 transforme cet export en rapport de *showback*. Trois grandeurs en sortent. Les **heures allouées** par compte valent le nombre de GPU multiplié par la durée. L'**utilisation** est le rapport des heures allouées à la capacité multipliée par la durée de la fenêtre. Les **heures perdues candidates** sont celles des jobs terminés en `FAILED`, `TIMEOUT`, `NODE_FAIL`, `OUT_OF_MEMORY` ou `PREEMPTED` : c'est une borne supérieure de la perte évitable, car un job qui sauvegarde ses checkpoints ne perd que le travail depuis la dernière sauvegarde.

::: ex
[Exemple 2.2 — Un mois de trace synthétique]{.tag} Le lab fournit une trace **synthétique** (inventée par un générateur à graine fixe) de 28 jours sur 64 GPU et quatre équipes, soit 43 008 GPU-heures de capacité. Au coût plein fictif de 2,08 u par GPU-heure, le rapport affiche :

~~~text
unit=gres/gpu capacity=64 window=672.0 h  full cost=89457  idle cost=40372
utilization (allocated / capacity): 54.9 %
lost candidates: FAILED 1096, TIMEOUT 692, NODE_FAIL 693, PREEMPTED 138 = 11.1 % of allocated hours
fleet wait: p50 0.00 h, p90 10.41 h
~~~

Les heures allouées sont de 23 598 sur 43 008, soit 54,9 %. L'inactivité coûte 40 372 u, soit 45,1 % du coût plein. Environ 11 % des heures allouées (2 619 GPU-heures) se sont terminées en échec, délai dépassé, panne de nœud ou préemption.
:::

Le tableau par équipe montre qui consomme. La part d'inactivité est ici proportionnelle (politique du chapitre 1). Les valeurs viennent de la même trace synthétique.

| Équipe | Jobs | GPU-h allouées | Part | Coût direct (u) | Inactivité (u) | Total (u) | Attente p90 |
|---|---|---|---|---|---|---|---|
| nlp | 19 | 14 245 | 60,4 % | 29 630 | 24 371 | 54 001 | 6,6 h |
| vision | 78 | 7 475 | 31,7 % | 15 548 | 12 789 | 28 337 | 13,1 h |
| eval | 678 | 977 | 4,1 % | 2 033 | 1 672 | 3 705 | 10,1 h |
| dev | 346 | 901 | 3,8 % | 1 873 | 1 541 | 3 414 | 10,4 h |

Le même lab contient une capture **réelle** : le script `verify-live.sh` démarre le Slurm 23.11 du bac à sable (4 CPU, sans GPU : les CPU tiennent lieu de GPU), soumet sept jobs de deux comptes, exporte `sacct` et recalcule les heures allouées. Le résultat est comparé à la colonne `CPUTimeRAW` de Slurm lui-même : 28 CPU-secondes pour `teama`, 14 pour `teamb`, identiques aux nôtres.

Cette vérification contrôle l'arithmétique de base (lecture de `AllocTRES` et de `ElapsedRaw`) contre le calcul de Slurm lui-même ; elle ne valide ni l'allocation de l'inactivité ni les attentes, que seuls les tests du lab couvrent.

::: note
[Un blocage observé dans la capture réelle]{.tag} Dans cette capture, deux jobs de 2 CPU auraient pu cohabiter sur un nœud de 4 CPU. Ils se sont pourtant exécutés l'un après l'autre : chacun avait reçu `mem=12872M` dans `AllocTRES`, soit toute la mémoire déclarée du nœud (le script d'installation en déclare 80 % de celle de la machine, 12 872 Mo ici).

La documentation de `slurm.conf` indique que la mémoire par défaut par CPU (`DefMemPerCPU`) vaut 0, c'est-à-dire illimitée. L'observation est cohérente avec ce défaut, sans essai contraire : un job qui ne demande pas de mémoire peut immobiliser un nœud. Sur un nœud GPU, le même mécanisme laisse des GPU vides à cause de la mémoire ou des CPU.
:::

### 2.4. Files d'attente et coût de l'inactivité

Une utilisation de 55 % n'empêche pas d'attendre dix heures. Deux mécanismes l'expliquent. D'abord la fragmentation et le blocage en tête de file : dans la trace synthétique, un job de 32 GPU attend que 32 GPU se libèrent ensemble, pendant que de petits jobs pourraient passer (c'est ce que le *backfill* de Slurm corrige, module 5). Ensuite la statistique : plus l'utilisation monte, plus l'attente explose.

Le modèle le plus simple de file à $c$ serveurs identiques, appelé M/M/c, donne la probabilité d'attendre par la formule d'Erlang C et l'attente moyenne en multiples de la durée moyenne d'un job. Pour une charge offerte $a = \rho c$ (le nombre moyen d'emplacements demandés), la probabilité d'attendre $C(c,a)$ et l'attente moyenne $W_q$ (en durées moyennes de job) valent :

$$C(c,a) = \frac{\dfrac{a^{c}}{c!}\,\dfrac{c}{c-a}}{\displaystyle\sum_{k=0}^{c-1}\frac{a^{k}}{k!} + \dfrac{a^{c}}{c!}\,\dfrac{c}{c-a}} \qquad W_q = \frac{C(c,a)}{c\,(1-\rho)}$$

Pour 64 GPU en jobs de 8 GPU, soit $c = 8$ emplacements :

| Utilisation $\rho$ | Probabilité d'attendre | Attente moyenne / durée d'un job |
|---|---|---|
| 0,50 | 0,059 | 0,015 |
| 0,70 | 0,271 | 0,113 |
| 0,80 | 0,458 | 0,286 |
| 0,90 | 0,702 | 0,877 |
| 0,95 | 0,844 | 2,110 |

Pour des jobs de 10 heures, l'attente moyenne passe d'environ 1,1 heure à 70 % à 2,9 heures à 80 %, puis à 8,8 heures à 90 %. Le simulateur du projet 6, avec 200 000 jobs et trois graines (0 à 2), donne 0,28 à 0,29 (à 80 %) et 0,86 à 0,89 (à 90 %), proches des 0,286 et 0,877 de la formule. Ces résultats supposent des arrivées de Poisson, des durées exponentielles et une seule classe de jobs : la réalité attend davantage, car les durées ont des queues lourdes.

::: key
[Règle de ce chapitre]{.tag} Il n'existe pas d'utilisation « cible » universelle. La cible est le point où l'attente reste sous l'objectif de service (SLO) des utilisateurs, et ce point est plus bas pour les gros jobs et pour les petits pools. Un cluster à 95 % n'est pas bien géré : il est en train de faire attendre tout le monde.
:::

La **mise en commun** réduit l'attente. À 80 % d'utilisation, quatre équipes qui se partagent quatre pools de 2 emplacements attendent en moyenne 1,78 durée de job ; un pool commun de 8 emplacements, 0,29 : six fois moins. C'est l'argument technique pour un cluster partagé avec quotas et préemption (module 5), plutôt que des îlots par équipe. Le projet 6 fournit le simulateur M/M/c pour tester votre propre mélange de jobs.

::: recap
Points clés — chapitre 2

-   Le rendement d'une flotte est un produit : disponibilité, allocation, goodput, MFU. Chaque facteur a un propriétaire.
-   Ne comparez jamais deux « utilisations » sans connaître le numérateur et le dénominateur.
-   `sacct -X -P` suffit à produire heures allouées, heures perdues candidates et attentes ; vérifiez-le contre `CPUTimeRAW`.
-   L'attente explose avec l'utilisation (Erlang C) ; mettre les pools en commun la réduit fortement.
:::

## 3. Prévoir la demande et choisir la capacité à engager {#ch3}

Acheter ou engager du calcul, c'est parier sur la demande des mois ou des années à venir. Ce chapitre construit une prévision modeste mais testable, avec ses scénarios, puis en déduit une règle de décision chiffrée.

### 3.1. La demande n'est pas la consommation

Ce que l'ordonnanceur enregistre, c'est la consommation : les heures effectivement allouées, plafonnées par la capacité. La demande réelle est plus élevée dès que des jobs attendent, que des chercheurs renoncent à lancer une expérience ou la réduisent pour qu'elle passe. On dit que l'historique est *censuré*. Un historique à 95 % d'utilisation sous-estime la demande, d'un montant inconnu.

Deux précautions en découlent. Mesurez la demande à la soumission (taille et durée demandées) plutôt qu'à l'allocation. Et traitez toute prévision construite sur un cluster saturé comme une borne basse.

La demande d'une équipe de recherche se décompose en trois parts de nature différente.

-   **Un socle** : développement, évaluations, petites expériences. Il est régulier et croît avec les effectifs.
-   **Des campagnes** : pré-entraînements ou grosses reprises, de quelques semaines et de plusieurs dizaines de GPU. Elles arrivent par à-coups et se connaissent en partie à l'avance par la feuille de route.
-   **Une saisonnalité** : échéances de conférences, rythme de l'année universitaire. C'est une hypothèse à vérifier sur vos données.

### 3.2. Un modèle de départ

Le lab 15.2 part d'une série hebdomadaire de GPU demandés (**synthétique**, produite par un générateur qui combine croissance, saison, bruit et campagnes). Le modèle ajuste, par moindres carrés sur le logarithme de la demande, une tendance linéaire et une harmonique annuelle :

$$\ln D_t = \beta_0 + \beta_1 t + \beta_2 \sin\frac{2\pi t}{52} + \beta_3 \cos\frac{2\pi t}{52} + \varepsilon_t$$

Les résidus $\varepsilon_t$ sont ensuite rééchantillonnés par blocs de quatre semaines pour conserver leur autocorrélation, et chaque scénario reçoit une perturbation aléatoire de la croissance annuelle. On obtient ainsi 2 000 trajectoires plausibles de l'an prochain, pas une prévision unique.

::: ex
[Exemple 3.1 — La tendance ajustée dépasse la tendance injectée]{.tag} Le générateur injecte une croissance de 35 % par an. Sur l'historique de 104 semaines (graine 0), l'ajustement trouve +54 % par an. Sans campagnes, il retrouve +34,7 % : l'écart vient donc des campagnes. Cinq campagnes ont été tirées ; deux d'entre elles se terminent dans les douze dernières semaines de l'historique et tirent la droite vers le haut.

Les moyennes passent de 63 GPU (semaines 0 à 25) à 87,5 GPU (semaines 78 à 103). Sur l'an prochain, les 2 000 scénarios ont une moyenne de 135 GPU, une médiane de 122 et un intervalle de 82 à 207 GPU entre les déciles 10 et 90. L'incertitude pèse presque autant que la valeur centrale.
:::

### 3.3. Tester la prévision sur le passé

Une prévision qui n'a jamais été confrontée au passé n'est pas un plan. Le test (*backtest*) ajuste le modèle sur les 78 premières semaines, prévoit les 26 suivantes et compare à la réalité, avec deux repères : une prévision naïve (la moyenne des 8 dernières semaines) et la couverture de la bande entre les déciles 10 et 90, censée contenir 80 % des semaines.

Sur huit historiques synthétiques de graines différentes, le résultat est instructif (commande `demo.py --seeds 8` du lab) : le modèle bat la prévision naïve en erreur absolue moyenne dans cinq cas sur huit. La bande de 80 % couvre en réalité de 8 % à 77 % des semaines, avec une médiane de 65 %.

Trois enseignements à garder. Comparez toujours à une prévision naïve : si vous ne la battez pas, la complexité ne sert à rien. Les bandes de prévision sont souvent trop étroites (ici 65 % de couverture médiane pour 80 % visés) ; élargissez-les ou raisonnez par scénarios nommés. Enfin, les campagnes se connaissent mieux par la feuille de route que par la statistique : le socle se prévoit, les campagnes se planifient avec les chercheurs.

### 3.4. De la prévision à la capacité à engager

Supposons qu'on puisse engager $L$ GPU pour la période (au prix $r$ par GPU-heure, payé même sans usage) et acheter le reste à la demande au prix $o > r$. Le coût espéré vaut $rL + o\,\mathbb{E}[(D-L)^+]$ par heure. Sa dérivée en $L$ s'annule quand $r = o\,\mathbb{P}(D > L)$. C'est le problème classique du « vendeur de journaux » (*newsvendor*) : l'engagement optimal est un quantile de la demande.

$$\mathbb{P}(D > L^{*}) = \frac{r}{o} \quad\Longleftrightarrow\quad L^{*} = F^{-1}\!\left(1 - \frac{r}{o}\right)$$

Lisez-le à l'envers : on engage le niveau de demande qui est dépassé dans une fraction $r/o$ des semaines. Avec une remise faible ($r$ proche de $o$), ce niveau est bas. Avec une grosse remise, il monte. Le test `test_probability_of_exceeding_the_commitment_is_the_price_ratio` du lab vérifie ce résultat par simulation.

<figure class="fig">
<svg viewBox="0 0 640 290" role="img" aria-labelledby="ldc-t ldc-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="ldc-t">Courbe de durée de la demande et capacité à engager</title>
<desc id="ldc-d">Demande de GPU classée de la plus forte à la plus faible, en fonction de la part des semaines où elle est dépassée. La capacité optimale de 107 GPU coupe la courbe là où la probabilité de dépassement vaut 65 %.</desc>
<line x1="70" y1="220" x2="600" y2="220" stroke="currentColor" stroke-width="1.5"/>
<line x1="70" y1="220" x2="70" y2="20" stroke="currentColor" stroke-width="1.5"/>
<text x="64" y="224" font-size="12" text-anchor="end" fill="currentColor">0</text>
<text x="64" y="157" font-size="12" text-anchor="end" fill="currentColor">100</text>
<text x="64" y="90" font-size="12" text-anchor="end" fill="currentColor">200</text>
<text x="64" y="24" font-size="12" text-anchor="end" fill="currentColor">300</text>
<text x="70.0" y="238" font-size="12" text-anchor="middle" fill="currentColor">0 %</text>
<text x="202.5" y="238" font-size="12" text-anchor="middle" fill="currentColor">25 %</text>
<text x="335.0" y="238" font-size="12" text-anchor="middle" fill="currentColor">50 %</text>
<text x="467.5" y="238" font-size="12" text-anchor="middle" fill="currentColor">75 %</text>
<text x="600.0" y="238" font-size="12" text-anchor="middle" fill="currentColor">100 %</text>
<polyline points="70.0,20.0 80.6,33.3 91.2,49.8 101.8,62.8 112.4,74.3 123.0,82.2 133.6,89.2 144.2,94.6 154.8,99.4 165.4,104.0 176.0,108.0 186.6,111.3 197.2,114.3 207.8,116.9 218.4,119.2 229.0,121.4 239.6,123.5 250.2,125.5 260.8,127.1 271.4,128.8 282.0,130.5 292.6,132.2 303.2,133.9 313.8,135.5 324.4,137.0 335.0,138.4 345.6,139.7 356.2,141.1 366.8,142.4 377.4,143.7 388.0,145.0 398.6,146.4 409.2,147.7 419.8,149.0 430.4,150.3 441.0,151.6 451.6,153.0 462.2,154.3 472.8,155.6 483.4,156.9 494.0,158.2 504.6,159.6 515.2,161.0 525.8,162.4 536.4,163.9 547.0,165.6 557.6,167.4 568.2,169.4 578.8,172.0 589.4,176.4 600.0,190.1" fill="none" stroke="currentColor" stroke-width="2.5"/>
<line x1="70" y1="148.4" x2="600" y2="148.4" stroke="var(--accent)" stroke-width="3"/>
<line x1="414.5" y1="148.4" x2="414.5" y2="220" stroke="var(--accent)" stroke-width="2" stroke-dasharray="5 4"/>
<circle cx="414.5" cy="148.4" r="5" fill="var(--accent)" stroke="currentColor"/>
<text x="80" y="170.4" font-size="13" font-weight="700" fill="currentColor">engager 107 GPU : P(D &gt; L) = r/o = 0,65</text>
<text x="74" y="14" font-size="12" fill="currentColor">GPU demandés (semaine)</text>
<text x="600" y="258" font-size="12" text-anchor="end" fill="currentColor">part des semaines où la demande dépasse le niveau</text>
</svg>
<figcaption>Courbe de durée des 2 000 scénarios synthétiques du lab 15.2 (prix fictifs r = 2,6 et o = 4,0) : on engage le niveau de demande dépassé dans 65 % des semaines, pas la moyenne et encore moins le pic (axe vertical tronqué à 300 GPU).</figcaption>
</figure>

::: ex
[Exemple 3.2 — Combien engager, selon la remise]{.tag} Avec le prix à la demande fictif $o = 4{,}0$ u et les 2 000 scénarios de l'exemple 3.1, le lab donne ce tableau pour cinq niveaux de prix engagé. L'économie est calculée par rapport à un parc entièrement à la demande (4 702 537 u de coût moyen annuel).

| Prix engagé $r$ | $1 - r/o$ | GPU à engager | Part d'engagement inutilisée | Économie moyenne |
|---|---|---|---|---|
| 3,6 | 0,10 | 82 | 1,2 % | 5,4 % |
| 3,2 | 0,20 | 93 | 2,8 % | 11,9 % |
| 2,6 | 0,35 | 107 | 6,2 % | 23,0 % |
| 2,0 | 0,50 | 122 | 10,6 % | 35,8 % |
| 1,6 | 0,60 | 134 | 14,6 % | 45,3 % |

Pour $r = 2{,}6$, le coût moyen est de 3 620 507 u. Engager la demande moyenne (135 GPU) coûte 3 746 102 u, soit 3,5 % de plus ; engager le pic simulé (490 GPU) coûte 11 136 982 u, soit 3,1 fois plus ; engager le 90e centile (207 GPU) coûte 4 856 334 u, plus que de ne rien engager. L'optimum est plat autour de son minimum et très pentu du côté du sur-engagement.
:::

Le calcul suppose une offre à la demande illimitée. Or la rareté des GPU est précisément ce que la FinOps Foundation signale pour l'IA. Le lab permet de limiter les GPU obtenables à la demande (`cap`) et de pénaliser la demande non servie (`penalty`, coût d'une GPU-heure non satisfaite).

Avec au plus 20 GPU obtenables à la demande et une pénalité de 20 u par GPU-heure non servie (valeurs d'exemple), la commande `demo.py --cap 20 --penalty 20` fait passer l'engagement optimal de 107 à 177 GPU. La part d'engagement inutilisée monte à 28,8 %, et 95 % des scénarios contiennent au moins une semaine de demande non servie. Avec une pénalité de 8 u, l'optimum est de 135 GPU. **La rareté se paie en engagement.**

### 3.5. Un plan de capacité

Un plan de capacité utile tient en une page, révisée chaque trimestre.

1.  Les trois scénarios nommés (bas, central, haut), par exemple les déciles 10 et 90 et la médiane des trajectoires : ici 82, 122 et 207 GPU.
2.  La capacité engagée (le quantile du tableau précédent) et la façon de couvrir l'écart : à la demande, spot pour les travaux tolérants, partenaires.
3.  Les campagnes connues de la feuille de route, ajoutées au socle statistique.
4.  Les déclencheurs de révision : utilisation soutenue au-dessus d'un seuil, attente p90 au-dessus de l'objectif, erreur de prévision au-delà d'une marge.
5.  Le délai d'approvisionnement de chaque option : l'horizon de la prévision doit dépasser le délai de livraison, sinon la prévision ne sert à rien.

L'engagement n'est pas forcément plat sur l'année. Un engagement par paliers (une part ferme, une part optionnelle) suit mieux une croissance : c'est l'objet de la négociation du chapitre 7.

::: recap
Points clés — chapitre 3

-   L'historique est censuré par la capacité : mesurez la demande à la soumission et lisez une prévision sur cluster saturé comme une borne basse.
-   Un modèle simple (tendance, saison, résidus rééchantillonnés) suffit, à condition de le tester contre une prévision naïve et de vérifier la couverture de ses bandes.
-   L'engagement optimal est le quantile $1 - r/o$ de la demande, pas la moyenne ni le pic.
-   La rareté des GPU à la demande augmente l'engagement optimal ; un plan de capacité se révise chaque trimestre.
:::

## 4. Modèle de coût total : acheter, louer, réserver, payer à la demande {#ch4}

Comparer le prix d'une GPU-heure à la demande avec le « prix » d'un serveur acheté n'a pas de sens. Ce chapitre construit un modèle de coût total (*TCO*, *total cost of ownership*) qui ramène chaque régime à la même unité : le coût d'une GPU-heure utile. Le modèle est le lab 15.3.

::: key
[Prix fictifs]{.tag} Tous les prix, remises, durées de vie et tarifs d'énergie de ce chapitre sont des **valeurs d'exemple** en unités arbitraires (u), regroupées dans `assumptions.yaml`. Seule la puissance maximale d'un nœud de 8 GPU (10,2 kW, guide utilisateur du DGX H100) est une donnée publiée. Le chapitre vous donne la méthode ; les prix, vous les relevez le jour de la décision sur les pages des fournisseurs et dans les devis reçus.
:::

### 4.1. Les postes d'un parc possédé

Posséder un nœud coûte plus que son prix catalogue. Le modèle retient cinq postes, tous ramenés à une GPU et à une année.

-   **L'amortissement** du matériel (nœud, réseau, stockage), étalé sur la durée de vie économique, avec le coût du capital et la valeur de revente.
-   **Le support** : pièces de rechange et garantie étendue.
-   **Le personnel** d'exploitation, proportionnel au nombre de GPU.
-   **L'installation** : un prix par kW de puissance informatique réservée (salle dans un centre de colocation, ou amortissement d'un bâtiment sur site).
-   **L'énergie**, à la puissance moyenne réellement consommée, multipliée par le PUE (chapitre 5).

L'amortissement avec coût du capital se calcule comme une annuité. Avec $P$ le prix d'achat, $R$ la valeur de revente à la fin, $i$ le taux annuel du capital et $n$ la durée de vie en années, le coût annuel est :

$$A = \Bigl(P - \frac{R}{(1+i)^{n}}\Bigr)\,\frac{i}{1-(1+i)^{-n}}$$

::: ex
[Exemple 4.1 — Ce que coûte une GPU possédée]{.tag} Avec les hypothèses fictives du lab (nœud de 280 000 u, 25 % de plus pour réseau et stockage, 4 ans, 10 % de revente, capital à 8 %), l'investissement de 350 000 u par nœud donne $A = 97\,905$ u par an, contre 87 500 u par an en amortissement linéaire du prix, sans coût du capital ni revente : le coût du capital, net de la revente, ajoute 12 %. Par GPU (8 par nœud) et à 70 % d'utilisation, le tableau devient :

| Poste | u par GPU et par an | Part |
|---|---|---|
| Amortissement | 12 238 | 67,1 % |
| Support | 2 100 | 11,5 % |
| Installation (colocation) | 2 448 | 13,4 % |
| Énergie (PUE 1,4) | 1 154 | 6,3 % |
| Personnel | 300 | 1,6 % |
| **Total** | **18 240** | |

Divisé par 8 760 heures, le total donne 2,08 u par GPU-heure *disponible*, la valeur utilisée au chapitre 2 pour le rapport de showback.
:::

### 4.2. Le coût de la GPU-heure utile

Chaque régime se ramène au coût par heure utile, avec $u$ l'allocation et $g$ le goodput du chapitre 1. Les régimes à coût fixe (parc possédé, location, réservation) se paient toutes les heures, qu'on les utilise ou non. Les régimes à l'usage ne se paient que pendant l'allocation.

| Régime | Coût par GPU-heure utile |
|---|---|
| Possédé | coût annuel / $(8760 \cdot u \cdot g)$ |
| Location ou réservation | tarif engagé / $(u \cdot g)$ |
| À la demande | tarif / $g$ |
| Spot | tarif / $\bigl(g \cdot (1 - W)\bigr)$ |

Pour le spot, $W$ est la part de temps perdue à cause des interruptions. Au premier ordre et avec le meilleur intervalle de checkpoint, le modèle de Young et Daly (projet [Entraîneur tolérant aux pannes](../../projects/resilient-trainer/index.html)) donne :

$$W = \sqrt{\frac{2C}{M}} + \frac{R}{M}$$

avec $C$ le coût d'un checkpoint, $M$ le temps moyen entre interruptions et $R$ le coût d'un redémarrage.

Pour un checkpoint de 3 minutes et un redémarrage de 10 minutes, la perte vaut 7,9 % si une interruption survient en moyenne toutes les 20 heures. Elle monte à 30,7 % pour une interruption toutes les 2 heures et tombe à 2,3 % pour une toutes les 200 heures.

::: ex
[Exemple 4.2 — Où l'achat devient rentable]{.tag} Avec un goodput de 0,9, le lab calcule le coût par heure utile (en u) pour quatre niveaux d'utilisation.

| Utilisation | Possédé | Location 3 ans | Réservé 1 an | À la demande | Spot |
|---|---|---|---|---|---|
| 0,3 | 7,57 | 9,63 | 11,85 | 4,44 | 1,93 |
| 0,5 | 4,58 | 5,78 | 7,11 | 4,44 | 1,93 |
| 0,7 | 3,31 | 4,13 | 5,08 | 4,44 | 1,93 |
| 0,9 | 2,59 | 3,21 | 3,95 | 4,44 | 1,93 |

Le parc possédé bat la demande à partir d'une utilisation $u^{*} = 0{,}516$ (indépendante de $g$ : il se simplifie). La location à 2,6 u bat la demande à 4,0 u à partir de $r/o = 0{,}65$, et la réservation à 3,2 u à partir de 0,80. À 30 % d'utilisation, le parc possédé coûte 1,7 fois la demande ; à 90 %, il coûte 42 % de moins.
:::

<figure class="fig">
<svg viewBox="0 0 640 290" role="img" aria-labelledby="tco-t tco-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="tco-t">Coût de la GPU-heure utile selon l'utilisation</title>
<desc id="tco-d">Cinq courbes du coût par GPU-heure utile en fonction de l'utilisation de 30 à 100 %. Les options à coût fixe baissent quand l'utilisation monte ; la courbe de l'achat coupe celle de la demande à environ 52 % d'utilisation.</desc>
<line x1="70" y1="220" x2="600" y2="220" stroke="currentColor" stroke-width="1.5"/>
<line x1="70" y1="220" x2="70" y2="24" stroke="currentColor" stroke-width="1.5"/>
<text x="64" y="224" font-size="12" text-anchor="end" fill="currentColor">0</text>
<text x="64" y="175" font-size="12" text-anchor="end" fill="currentColor">3</text>
<text x="64" y="126" font-size="12" text-anchor="end" fill="currentColor">6</text>
<text x="64" y="77" font-size="12" text-anchor="end" fill="currentColor">9</text>
<text x="64" y="28" font-size="12" text-anchor="end" fill="currentColor">12</text>
<text x="70.0" y="238" font-size="12" text-anchor="middle" fill="currentColor">30 %</text>
<text x="145.7" y="238" font-size="12" text-anchor="middle" fill="currentColor">40 %</text>
<text x="221.4" y="238" font-size="12" text-anchor="middle" fill="currentColor">50 %</text>
<text x="297.1" y="238" font-size="12" text-anchor="middle" fill="currentColor">60 %</text>
<text x="372.9" y="238" font-size="12" text-anchor="middle" fill="currentColor">70 %</text>
<text x="448.6" y="238" font-size="12" text-anchor="middle" fill="currentColor">80 %</text>
<text x="524.3" y="238" font-size="12" text-anchor="middle" fill="currentColor">90 %</text>
<text x="600.0" y="238" font-size="12" text-anchor="middle" fill="currentColor">100 %</text>
<polyline points="70.0,96.4 88.9,105.7 107.9,113.8 126.8,120.7 145.7,126.8 164.6,132.2 183.6,137.0 202.5,141.3 221.4,145.1 240.4,148.6 259.3,151.8 278.2,154.7 297.1,157.3 316.1,159.7 335.0,162.0 353.9,164.1 372.9,166.0 391.8,167.8 410.7,169.5 429.6,171.1 448.6,172.5 467.5,173.9 486.4,175.2 505.4,176.5 524.3,177.6 543.2,178.7 562.1,179.8 581.1,180.7 600.0,181.7" fill="none" stroke="var(--accent)" stroke-width="3"/>
<polyline points="70.0,62.7 88.9,74.8 107.9,85.2 126.8,94.2 145.7,102.0 164.6,109.0 183.6,115.1 202.5,120.7 221.4,125.6 240.4,130.1 259.3,134.2 278.2,137.9 297.1,141.4 316.1,144.5 335.0,147.4 353.9,150.1 372.9,152.6 391.8,154.9 410.7,157.1 429.6,159.1 448.6,161.0 467.5,162.8 486.4,164.5 505.4,166.1 524.3,167.6 543.2,169.0 562.1,170.3 581.1,171.6 600.0,172.8" fill="none" stroke="currentColor" stroke-width="2"/>
<polyline points="70.0,26.4 88.9,41.3 107.9,54.1 126.8,65.1 145.7,74.8 164.6,83.4 183.6,90.9 202.5,97.7 221.4,103.9 240.4,109.4 259.3,114.4 278.2,119.0 297.1,123.2 316.1,127.1 335.0,130.7 353.9,134.0 372.9,137.0 391.8,139.9 410.7,142.6 429.6,145.1 448.6,147.4 467.5,149.6 486.4,151.7 505.4,153.6 524.3,155.5 543.2,157.2 562.1,158.9 581.1,160.4 600.0,161.9" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="6 4"/>
<polyline points="70.0,147.4 88.9,147.4 107.9,147.4 126.8,147.4 145.7,147.4 164.6,147.4 183.6,147.4 202.5,147.4 221.4,147.4 240.4,147.4 259.3,147.4 278.2,147.4 297.1,147.4 316.1,147.4 335.0,147.4 353.9,147.4 372.9,147.4 391.8,147.4 410.7,147.4 429.6,147.4 448.6,147.4 467.5,147.4 486.4,147.4 505.4,147.4 524.3,147.4 543.2,147.4 562.1,147.4 581.1,147.4 600.0,147.4" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="2 4"/>
<polyline points="70.0,188.5 88.9,188.5 107.9,188.5 126.8,188.5 145.7,188.5 164.6,188.5 183.6,188.5 202.5,188.5 221.4,188.5 240.4,188.5 259.3,188.5 278.2,188.5 297.1,188.5 316.1,188.5 335.0,188.5 353.9,188.5 372.9,188.5 391.8,188.5 410.7,188.5 429.6,188.5 448.6,188.5 467.5,188.5 486.4,188.5 505.4,188.5 524.3,188.5 543.2,188.5 562.1,188.5 581.1,188.5 600.0,188.5" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="10 3 2 3"/>
<circle cx="233.6" cy="147.4" r="5" fill="var(--accent)" stroke="currentColor"/>
<text x="223.6" y="177.4" font-size="13" font-weight="700" text-anchor="end" fill="currentColor">u* = 0,52</text>
<line x1="400" y1="34" x2="436" y2="34" stroke="var(--accent)" stroke-width="3"/>
<text x="444" y="38" font-size="13" fill="currentColor">achat (possédé)</text>
<line x1="400" y1="54" x2="436" y2="54" stroke="currentColor" stroke-width="2"/>
<text x="444" y="58" font-size="13" fill="currentColor">location 3 ans</text>
<line x1="400" y1="74" x2="436" y2="74" stroke="currentColor" stroke-width="2" stroke-dasharray="6 4"/>
<text x="444" y="78" font-size="13" fill="currentColor">réservé 1 an</text>
<line x1="400" y1="94" x2="436" y2="94" stroke="currentColor" stroke-width="2" stroke-dasharray="2 4"/>
<text x="444" y="98" font-size="13" fill="currentColor">à la demande</text>
<line x1="400" y1="114" x2="436" y2="114" stroke="currentColor" stroke-width="2" stroke-dasharray="10 3 2 3"/>
<text x="444" y="118" font-size="13" fill="currentColor">spot</text>
<text x="74" y="14" font-size="12" fill="currentColor">u par GPU-heure utile</text>
</svg>
<figcaption>Coût de la GPU-heure utile selon l'utilisation (goodput 0,9, données fictives du lab 15.3). Les options à coût fixe se paient à chaque heure et baissent avec l'utilisation ; la demande et le spot ne dépendent pas d'elle.</figcaption>
</figure>

Deux remarques sur ce tableau. Le spot est le moins cher à toute utilisation, mais ce chiffre est trompeur : il suppose qu'on puisse en obtenir autant qu'on veut, et que le travail tolère des interruptions. Ensuite, la comparaison de deux options à coût fixe (possédé contre location) ne dépend pas de l'utilisation, puisque les deux se divisent par le même $u$ : elle se joue sur le coût annuel par GPU, 18 240 u contre 22 776 u dans cet exemple.

### 4.3. Les régimes réels et leurs conditions

**Achat sur site ou en colocation.** L'installation en colocation se paie au kW réservé ; sur site, vous amortissez salle, alimentation et refroidissement. Avec les valeurs fictives du lab, le point mort contre la demande passe de 0,516 (colocation) à 0,485 (installation sur site à 90 u par kW et par mois) : la différence est réelle mais faible devant celle de l'utilisation.

**Réservations de courte durée.** AWS propose des *Capacity Blocks for ML* : on réserve des instances GPU pour une date future, avec un début jusqu'à huit semaines à l'avance, jusqu'à 64 instances par bloc et 256 au total, d'après la documentation d'AWS. Le prix dépend de l'offre et de la demande à l'achat, il est payé d'avance et ne change plus ensuite. Les remises des Savings Plans et des Reserved Instances ne s'y appliquent pas. Le temps non utilisé ne coûte rien de plus, mais il est déjà payé.

::: ex
[Exemple 4.3 — Un bloc réservé et payé d'avance]{.tag} Soit un bloc de 8 GPU sur 14 jours à un prix d'exemple de 3,0 u par GPU-heure : 8 064 u payés d'avance. Si le bloc n'est utilisé qu'à 60 %, le coût par heure réellement utilisée est $3{,}0/0{,}6 = 5{,}0$ u, plus que le tarif à la demande de 4,0 u. Un bloc payé d'avance ne vaut que si vous remplissez son calendrier : c'est l'argument pour caler les campagnes sur la réservation, pas l'inverse.
:::

**Spot.** AWS émet un avis d'interruption deux minutes avant d'arrêter ou de terminer une instance Spot, « au mieux » (*best effort*) d'après sa documentation. Un entraînement spot doit donc pouvoir sauvegarder un checkpoint en moins de deux minutes, ou accepter de perdre le travail depuis le dernier.

### 4.4. Sensibilité : ce qui fait basculer la décision

Un modèle sert surtout à savoir **quelles hypothèses comptent**. Le lab fait varier chaque paramètre de ±20 % autour de sa valeur et mesure l'écart sur le coût par heure utile du parc possédé, à 70 % d'utilisation :

| Paramètre | Coût à −20 % | Coût à +20 % | Écart |
|---|---|---|---|
| Prix du nœud | 2,79 | 3,82 | 1,04 |
| Durée de vie | 3,77 | 3,00 | 0,77 |
| Coût du capital | 3,22 | 3,39 | 0,18 |
| Réseau et stockage | 3,22 | 3,39 | 0,18 |
| Support | 3,23 | 3,38 | 0,15 |
| PUE | 3,26 | 3,35 | 0,08 |
| Prix de l'énergie | 3,26 | 3,35 | 0,08 |
| Valeur de revente | 3,34 | 3,27 | 0,07 |
| Personnel | 3,29 | 3,32 | 0,02 |

Le prix du matériel et la durée de vie dominent. L'énergie, souvent discutée, pèse peu dans le coût (6,3 % du total dans cet exemple) ; elle pèse davantage dans la capacité installable (chapitre 5). La valeur de revente, très incertaine, compte peu.

Passer la durée de vie de 3 à 6 ans fait baisser le coût par heure disponible de 2,47 à 1,70 u et le point mort de 0,615 à 0,418. **La durée de vie est une hypothèse de risque**, car elle dépend du rythme des générations de GPU, pas seulement de l'amortissement comptable. Fixez-la avec la finance, et testez un scénario où la revente est nulle.

### 4.5. Ce que le modèle ne dit pas

Le lab l'écrit dans son README : ni taxes, ni inflation, ni remises de volume, ni coût de transfert de données, ni limite de capacité sur le spot ou la demande, ni délai de livraison. Les trois derniers sont souvent décisifs. Un régime moins cher mais indisponible pendant six mois n'est pas une option.

En pratique, on compose les régimes : un socle engagé au niveau du chapitre 3, de la demande pour les pointes, du spot pour les travaux tolérants aux interruptions. Le projet « Placement multi-fournisseurs » prolonge ce chapitre en simulant cette composition sur des capacités et des taux d'interruption fictifs.

::: recap
Points clés — chapitre 4

-   Ramenez tout à la GPU-heure utile : coût fixe divisé par $u \cdot g$, tarif à l'usage divisé par $g$.
-   Un parc possédé ou engagé devient rentable au-delà d'un point mort d'utilisation ($0{,}516$ ici face à la demande) ; pour un engagement de tarif $r$ face à la demande $o$, ce point mort vaut $r/o$.
-   Prix du matériel et durée de vie dominent la sensibilité ; l'énergie pèse peu dans le coût.
-   Un bloc payé d'avance coûte $\text{prix}/\text{taux de remplissage}$ par heure utilisée.
-   Disponibilité, délais et limites de capacité ne sont pas dans le modèle : ajoutez-les par le contrat (chapitre 6).
:::

## 5. Énergie et datacenter : puissance, refroidissement, PUE, délais {#ch5}

Un GPU ne s'installe pas sans électricité ni évacuation de chaleur. Pour un ingénieur d'infrastructure, la puissance disponible est souvent la première contrainte de dimensionnement, avant le budget. Ce chapitre donne les ordres de grandeur publiés et le calcul qui relie kilowatts, baies et GPU.

### 5.1. Puissance d'un GPU, d'un nœud, d'une baie

La page produit du H100 de NVIDIA indique une puissance thermique maximale (TDP) « jusqu'à 700 W (configurable) » pour la version SXM (350 à 400 W pour la version NVL). Un nœud de 8 GPU consomme bien plus que 8 fois 700 W : processeurs, mémoire, commutateurs NVLink, cartes réseau, ventilateurs et stockage s'y ajoutent.

| Système | Puissance maximale | Refroidissement | Source |
|---|---|---|---|
| DGX H100 / H200 (8 GPU) | 10,2 kW, six alimentations de 3,3 kW en 4+2 | air | guide utilisateur NVIDIA |
| DGX B200 (8 GPU) | 14,3 kW, six alimentations de 3,3 kW en 5+1 | air | guide utilisateur NVIDIA |
| GB200 NVL72 (72 GPU, rack) | 120 kW de capacité de refroidissement requise | liquide direct | blog NVIDIA, 2024 |

Pour le DGX H100, les huit GPU représentent au plus $8 \times 0{,}7 = 5{,}6$ kW, soit 55 % de la puissance maximale du nœud. Chaque emplacement de GPU « coûte » donc 1,275 kW tout compris, et 1,79 kW pour le DGX B200 ($14{,}3 / 8$). Dans le rack NVL72, la capacité de 120 kW rapportée à 72 GPU donne 1,67 kW par GPU.

::: note
[Deux chiffres sur la même page]{.tag} Le guide du DGX H100 donne 10,2 kW de puissance maximale et, dans sa table des caractéristiques, une production de chaleur de 38 557 BTU par heure. Avec 1 W = 3,412 BTU/h, cela fait 11,3 kW, soit 11 % de plus. Nous n'avons pas d'explication documentée de l'écart. Pour dimensionner un refroidissement, prenez le plus grand des deux et demandez au constructeur de préciser les conditions de chaque mesure.
:::

### 5.2. Densité par baie et refroidissement

L'Uptime Institute rapportait en 2020 que, sur son échantillon, 71 % des répondants avaient une densité modale inférieure à 10 kW par baie, et que les baies les plus denses de la plupart des centres se situaient entre 10 et 19 kW. Il notait qu'au-delà de 20 à 25 kW par baie, le refroidissement liquide direct et l'air de précision deviennent plus économiques (enquête de 2020 : les ordres de grandeur ont évolué, mais ce sont les derniers chiffres que nous avons lus à la source).

Un seul DGX H100 occupe donc une baie entière d'une salle « classique », et quatre dans la même baie demandent 40,8 kW. Pour la ventilation, le guide du DGX H100 indique une température de fonctionnement de 5 à 30 °C et un débit d'air de 1 105 CFM à 80 % de la vitesse des ventilateurs.

::: ex
[Exemple 5.1 — L'air peut-il refroidir 120 kW ?]{.tag} L'élévation de température de l'air est donnée par $\Delta T = P / (\rho \, \dot V c_p)$. Avec 1 105 CFM, soit 0,522 m³/s, une masse volumique de 1,2 kg/m³ et une chaleur massique de 1 005 J/(kg·K), un nœud de 10,2 kW échauffe l'air de 16,2 K. C'est un ordre de grandeur, car le débit cité est à 80 % de la vitesse des ventilateurs et non à la charge maximale.

Pour évacuer 120 kW avec le même échauffement, il faudrait 6,14 m³/s, soit environ 13 000 CFM : l'équivalent du débit de 11,8 serveurs DGX H100 dans une seule baie. À l'eau, avec un échauffement de 10 K et une chaleur massique de 4 186 J/(kg·K), le même rack demande 2,87 kg/s, soit 172 litres par minute. C'est pour cela que les racks de cette densité sont conçus pour le refroidissement liquide direct.
:::

Le refroidissement liquide direct change l'exploitation : circuits d'eau, unités de distribution, détection de fuites, procédures de maintenance. Il se négocie aussi : qui est responsable d'une fuite, et dans quel délai le fournisseur la répare (chapitre 6).

### 5.3. Le PUE et le coût de l'énergie

Le PUE (*power usage effectiveness*) compare l'énergie totale d'une installation à celle qui alimente les équipements informatiques :

$$\text{PUE} = \frac{E_{\text{installation}}}{E_{\text{informatique}}}$$

Google le rappelle dans sa page sur l'efficacité de ses centres : un PUE de 2,0 signifie qu'à chaque watt informatique s'ajoute un watt pour le refroidissement et la distribution. Google rapporte un PUE moyen de 1,09 en 2025 sur sa flotte, et cite l'enquête 2025 de l'Uptime Institute pour une moyenne mondiale de 1,54. Ce sont deux populations différentes, à ne pas comparer à la légère.

L'effet sur le coût reste modeste. Un nœud DGX H100 qui tire en moyenne 75 % de sa puissance maximale (7,65 kW, valeur d'exemple) consomme, par GPU-heure et à 0,12 u le kWh (prix fictif), 0,126 u à PUE 1,1, 0,161 u à PUE 1,4 et 0,177 u à PUE 1,54. Cela fait de 6,1 % à 8,5 % du coût plein de 2,08 u. Mille GPU à PUE 1,4 consomment environ 11,7 GWh par an, dont 8,4 GWh pour l'informatique.

À l'échelle d'un pays, le Lawrence Berkeley National Laboratory estime que les centres de données américains ont consommé 176 TWh en 2023, soit 4,4 % de l'électricité du pays (rapport 2024). L'énergie est donc un sujet de politique publique, mais votre décision d'achat se joue sur la puissance installable plus que sur la facture d'énergie.

### 5.4. De la puissance disponible au nombre de GPU

La puissance se réserve en kW sur la valeur maximale, et se facture en kWh sur la consommation mesurée. Pour savoir combien de GPU tiennent dans une installation, on raisonne en puissance maximale informatique : le budget électrique de l'installation divisé par le PUE, puis par la puissance maximale d'un nœud.

::: ex
[Exemple 5.2 — Un mégawatt, combien de GPU ?]{.tag} Une installation dispose de 1 000 kW. À PUE 1,4, la part informatique est de $1000/1{,}4 = 714$ kW. Avec des nœuds DGX H100 de 10,2 kW, on installe $\lfloor 714/10{,}2 \rfloor = 70$ nœuds, soit 560 GPU, en 18 baies de quatre nœuds (40,8 kW chacune), dont la dernière est à moitié pleine.

Dimensionner sur la puissance *moyenne* (7,65 kW) conduirait à 93 nœuds, soit 744 GPU, un tiers de plus. C'est tentant et dangereux : disjoncteurs, onduleurs et refroidissement sont dimensionnés pour la pointe, et la charge d'un entraînement varie fortement à l'échelle de la salle. Notre recommandation est de dimensionner sur le maximum et d'utiliser la consommation moyenne pour le budget d'énergie seulement.
:::

::: war
[Des variations de puissance de l'ordre de dizaines de mégawatts]{.tag} Les auteurs de [l'article de Llama 3](https://arxiv.org/abs/2407.21783) notent que des dizaines de milliers de GPU peuvent augmenter ou réduire leur consommation en même temps, par exemple quand tous attendent la fin d'un checkpoint ou d'une communication collective, ou au démarrage ou à l'arrêt de tout le job.

Cela peut provoquer des fluctuations instantanées de consommation de l'ordre de dizaines de mégawatts dans le centre de données, aux limites du réseau électrique. Le même article relève une variation diurne de 1 à 2 % du débit d'entraînement, liée à la température. Demandez à l'exploitant de votre installation le profil de puissance qu'elle supporte avant de lancer une campagne.
:::

### 5.5. Délais et calendrier

Les délais de raccordement électrique, de fourniture des équipements de refroidissement et de livraison de GPU sont souvent plus longs que le délai de décision. Ce module ne cite aucune durée : nous n'avons pas lu de source primaire à jour qui en donne un ordre de grandeur fiable, et ces délais dépendent du site, du pays et du fournisseur.

La méthode, elle, est stable. Dressez le chemin critique : alimentation (raccordement et transformateurs), distribution (tableaux, PDU), refroidissement (unités de distribution, circuits), baies, réseau, recette. Demandez par écrit, pour chaque étape, une date et un responsable. Intégrez la date de « prêt pour le service » au contrat, avec une pénalité de retard (chapitre 6). Enfin, utilisez ce délai comme horizon minimal de votre prévision de demande (chapitre 3) : une capacité commandée aujourd'hui répond à la demande de dans plusieurs mois.

::: recap
Points clés — chapitre 5

-   Un nœud de 8 GPU tire 10,2 kW (DGX H100) ou 14,3 kW (DGX B200) au maximum ; un rack NVL72 demande 120 kW de refroidissement liquide.
-   À l'air, 120 kW demanderaient environ 13 000 CFM par baie ; l'eau n'en demande que 172 L/min pour un échauffement de 10 K.
-   Le PUE de l'ordre de 1,1 à 1,5 fait varier l'énergie de 6 à 9 % du coût plein ; il pèse davantage sur la puissance installable.
-   Dimensionnez en puissance maximale informatique divisée par le PUE ; ne vous fiez pas à la puissance moyenne.
-   Les délais d'alimentation et de refroidissement se demandent par écrit, étape par étape, et se contractualisent.
:::

## 6. Lire un contrat de capacité GPU {#ch6}

Le contrat est l'endroit où une promesse de capacité devient une obligation mesurable ou ne le devient pas. Ce chapitre apprend à lire un contrat de capacité avec un œil d'ingénieur : quelles clauses comptent pour un entraînement, comment les chiffrer, et lesquelles négocier. Il ne remplace pas un conseil juridique.

### 6.1. Anatomie d'un contrat de capacité

Un contrat de capacité GPU se découpe en neuf familles de clauses. Pour chacune, la question de l'ingénieur est la même : quel nombre, mesuré comment, avec quelle conséquence en cas de manquement ?

| Famille | Question à poser |
|---|---|
| Engagement | durée minimale, paiement à vide (*take-or-pay*), renouvellement, droit de sortie |
| Livraison | date de mise à disposition, livraison par tranches, recette, début de la facturation |
| Disponibilité (SLA) | cible, périmètre mesuré, exclusions, plafond et nature de la compensation |
| Remplacement | délai de remplacement d'un nœud, matériel de remplacement, pièces de rechange |
| Performance | réseau, stockage, fréquence : engagement ou « au mieux » |
| Support | horaires, délai de première réponse, interlocuteur nommé, escalade |
| Prix | indexation, augmentations, surcharges |
| Sortie et données | frais de transfert, restitution, suppression et certificat |
| Responsabilité | plafond, force majeure, suspension, résiliation par le fournisseur |

Pour chiffrer les clauses, ce chapitre suppose un contrat de 512 GPU (64 nœuds de 8) à un prix d'exemple de 3,0 u par GPU-heure, soit 1 105 920 u par mois de 30 jours.

### 6.2. Lire un SLA publié

Les grands fournisseurs publient leurs SLA ; ils servent d'étalon pour lire un SLA négocié. Le SLA d'Amazon EC2 (page « Last Updated: May 25, 2022 », lue le 24 octobre 2026) s'engage sur une disponibilité mensuelle d'au moins 99,99 % pour une région, à condition que toutes les instances soient déployées dans au moins deux zones.

En dessous, les crédits sont de 10 % de la facture mensuelle pour une disponibilité inférieure à 99,99 % et au moins égale à 99,0 %, de 30 % entre 99,0 % et 95,0 %, et de 100 % en dessous. Pour une instance isolée, la cible est de 99,5 %.

Plusieurs détails comptent plus que les pourcentages. Le crédit se calcule sur la facture mensuelle de l'offre concernée, hors paiements uniques d'avance. Il ne s'applique que sur des paiements futurs. Il faut le demander en ouvrant un dossier avant la fin du deuxième cycle de facturation suivant l'incident.

Le SLA précise qu'il constitue le recours unique et exclusif du client. Et pour une instance isolée, l'indisponibilité est définie comme l'absence de connectivité externe : une instance dont le GPU est défaillant mais qui répond au réseau est disponible au sens du SLA.

Le SLA de Google Compute Engine a la même structure au niveau régional : crédits de 10 %, 25 % puis 100 % selon la disponibilité mensuelle (entre 99,00 % et le seuil de la cible, entre 95,00 % et 99,00 %, puis en dessous de 95 %), versés sur les factures futures, avec le même recours unique et exclusif. Cette structure se retrouve dans la plupart des contrats : retenez-la comme grille de lecture.

| Disponibilité mensuelle | Minutes d'indisponibilité tolérées sur 30 jours |
|---|---|
| 99,99 % | 4,3 |
| 99,9 % | 43,2 |
| 99,5 % | 216 |
| 99,0 % | 432 |
| 95,0 % | 2 160 |

### 6.3. Pourquoi un crédit n'est pas une compensation

Un entraînement synchrone s'arrête dès qu'un nœud manque. Un SLA, lui, compte l'indisponibilité à une autre échelle, par instance ou par région, et seulement si le nœud est injoignable.

::: ex
[Exemple 6.1 — Un nœud sur 64 en panne]{.tag} Le module `sla.py` du lab 15.4 calcule la disponibilité par nœud-heure : $1 - \text{heures d'arrêt} / (\text{nœuds} \times 720)$. Un nœud en panne sur 64 pendant un mois de 30 jours donne :

| Nœud en panne | Disponibilité par nœud-heure | Crédit (cible 99,5 %) | Valeur du job de 512 GPU arrêté |
|---|---|---|---|
| 1 h | 99,9978 % | 0 | 1 536 u |
| 6 h | 99,9870 % | 0 | 9 216 u |
| 36 h | 99,9219 % | 0 | 55 296 u |
| 72 h | 99,8438 % | 0 | 110 592 u |

La dernière colonne suppose qu'un job de 512 GPU est arrêté pendant toute la panne (prix d'exemple 3,0 u). Le crédit est nul dans tous les cas : à 99,5 %, il faudrait 230 heures de panne d'un seul nœud sur 64 pour passer sous la cible par nœud-heure, alors que 3,6 heures d'arrêt de *tout le cluster* y suffiraient. Un SLA mesuré par cluster et sur la joignabilité du réseau ne protège pas un entraînement.
:::

L'inverse existe aussi : une panne totale courte donne un crédit généreux. Avec la grille d'AWS appliquée à 512 GPU, un mois à 99,7 % (130 minutes d'arrêt de tout le cluster) donne 10 % de crédit, soit 110 592 u, pour 3 318 u de GPU-heures perdues. Mais l'arrêt d'un job synchrone coûte plus que les heures d'arrêt (travail perdu depuis le dernier checkpoint), et aucun crédit ne couvre la dégradation silencieuse d'un GPU ou d'un lien. Le lien avec le chapitre 2 est direct : c'est un goodput que le SLA ne protège pas.

### 6.4. Les clauses propres aux GPU

**Remplacement.** Le contrat fictif du lab promet un remplacement « raisonnable » sans délai. Exigez un nombre d'heures, un stock de pièces dimensionné dans le contrat, et que le nœud compte comme indisponible jusqu'au remplacement. Sans quoi un nœud défaillant reste un nœud payé et inutilisable.

**Substitution.** Si le fournisseur peut remplacer un nœud par une « configuration équivalente », un nœud de génération différente peut entrer dans un job synchrone et le ralentir. Exigez le même modèle de GPU, la même mémoire et la même interconnexion, ou une validation par benchmark.

**Recette et performance.** Une recette (*acceptance*) décrit des tests passés avant la facturation : durée de rodage (*burn-in*), débit de bus d'un all-reduce comme celui de `nccl-tests` (module 2), débit de stockage, état de santé des GPU (projet [Observabilité des GPU](../../projects/gpu-observability/index.html)). Les valeurs mesurées à la recette deviennent un plancher pendant le contrat. Un contrat sans engagement de performance ne garantit qu'une présence.

**Maintenance et support.** Plafonnez les heures de maintenance planifiée, exigez un préavis, interdisez le redémarrage de nœuds en cours de job, et demandez un support 24 h sur 24 pour les incidents critiques avec un interlocuteur nommé.

**Relocalisation.** Le droit de déplacer votre capacité dans un autre centre peut dégrader la proximité du stockage et du réseau, et changer la localisation des données.

### 6.5. Engagement, prix et sortie

**Paiement à vide.** Dans le contrat fictif, vous payez les 512 GPU chaque heure dès la date de début, alors que seuls 25 % sont livrés au départ et que le reste l'est « selon disponibilité ». Si les 75 % restants arrivent après 90 jours, vous avez payé 2 488 320 u de capacité non livrée (à 3,0 u). Demandez de facturer la capacité livrée et recettée, avec un palier de souplesse de 10 à 20 %.

**Prix.** Une augmentation annuelle plafonnée à 8 % à partir de la deuxième année coûte, si elle s'applique deux fois (année 2 puis année 3, hausses composées), 3 269 984 u de plus sur 3 ans, soit 8,2 % du total. Les surcharges d'énergie « pour refléter les hausses de coûts » sans formule sont une augmentation sans plafond.

**Sortie et données.** Les frais de transfert au départ peuvent être un frein à la sortie. AWS décrit un programme de dérogation : sur demande auprès du support, les frais de transfert sortants sont supprimés pour un client qui quitte AWS. Le billet d'AWS précise que cette dérogation suit la direction du règlement européen sur les données (*Data Act*).

Une mise à jour datée du 8 octobre 2026 indique que les clients hors Union européenne disposent de 180 jours pour terminer leur départ. Ces conditions évoluent : relisez-les le jour de la décision, et obtenez leur équivalent par écrit dans votre contrat.

**Responsabilité.** Un plafond égal à trois mois de redevances (3 317 760 u dans notre exemple) représente 8,3 % des 39 813 120 u du contrat sur 36 mois. Combiné à l'exclusion de la « perte de progrès d'entraînement », il laisse l'essentiel du risque au client. La force majeure qui inclut « les pénuries de composants » ou « l'indisponibilité d'électricité » retire au fournisseur ses risques propres.

**Résiliation.** Un fournisseur qui peut résilier pour convenance avec 30 jours de préavis, sans remboursement des sommes payées d'avance, rend l'engagement unilatéral. Un client sans droit de résiliation, face à un fournisseur qui peut suspendre « sur soupçon raisonnable » et sans préavis, supporte tous les risques.

### 6.6. Une grille de revue, appliquée par un script

Le lab 15.4 fournit un contrat **fictif** de 26 clauses (fournisseur inventé, nombres inventés, problèmes plantés), une grille de 24 critères et un script qui les évalue par expressions régulières. Chaque critère est vert (1 point), orange (0,5) ou rouge (0), avec un poids ; quatre critères sont des *deal-breakers* (paiement à vide, livraison sans recours, périmètre de disponibilité, résiliation unilatérale par le fournisseur).

::: ex
[Exemple 6.2 — La revue du contrat fictif]{.tag} Sortie réelle du script sur le contrat fictif (premières lignes) :

~~~text
contract score 7/100  (0 green, 5 amber, 19 red)
by category: commitment 0  delivery 0  service 19  operations 10  price 0  exit_legal 8
deal-breakers red: take_or_pay, delivery_remedy, availability_scope, provider_exit
~~~

Après un tour de négociation fictif (version `fictional_contract_negotiated.md`), le score monte à 88/100 avec 18 critères verts, 6 oranges et aucun rouge. Les six oranges restants sont des compromis : délai de remplacement de 48 heures, disponibilité de 99,5 %, 24 heures de maintenance, engagement de 24 mois, recours exclusif et réponse critique en 4 heures ouvrées.
:::

Le score est une aide au tri, pas une mesure : poids et seuils sont les choix de ce parcours, et vous devez les adapter à votre charge et à vos alternatives.

Une limite importante : un critère de type indicateur (par exemple la substitution de matériel) devient rouge quand la formulation fautive *est présente*, et reste vert quand elle est absente. Un contrat muet sur un sujet peut donc paraître vert ; sur un contrat réel, faites un relevé manuel clause par clause. La vraie valeur du score est la liste ordonnée de ce qu'il faut négocier, avec pour chaque point la demande à formuler (chapitre 7).

::: recap
Points clés — chapitre 6

-   Un SLA publié a presque toujours la même structure : cible, périmètre, exclusions, crédits plafonnés, recours exclusif, réclamation dans un délai.
-   Un crédit n'est pas une compensation : un nœud en panne parmi 64 ne déclenche rien, alors qu'il arrête un job synchrone.
-   Les clauses propres aux GPU sont le remplacement, la substitution, la recette, le plancher de performance et la maintenance.
-   Paiement à vide, hausses de prix, frais de sortie, plafond de responsabilité et force majeure se chiffrent : faites-le avant de négocier.
:::

## 7. Négocier : leviers, alternatives, calendrier {#ch7}

La négociation d'un contrat de capacité se joue plus sur la préparation que sur le talent oratoire. L'ingénieur n'est pas celui qui signe, mais c'est lui qui sait ce que valent les clauses techniques. Ce chapitre donne une méthode et des chiffres ; les pratiques de négociation relèvent de ce parcours (« recommandé »), pas d'une norme.

### 7.1. Le rôle de l'ingénieur

La FinOps Foundation range les achats et la finance parmi les personas centraux d'une pratique FinOps, à côté de l'ingénierie. Dans un achat de calcul, chacun apporte une pièce que les autres n'ont pas : les achats connaissent les fournisseurs et les procédures, la finance les contraintes de trésorerie et de comptabilité, le juridique la portée des clauses. L'ingénieur apporte quatre choses.

1.  Une demande chiffrée et ses scénarios (chapitre 3), pour dimensionner l'engagement.
2.  Un coût par GPU-heure utile et sa sensibilité (chapitre 4), pour juger les prix.
3.  Des exigences mesurables : disponibilité par nœud-heure, délai de remplacement, tests de recette (chapitre 6).
4.  Un protocole de test que le fournisseur ne contrôle pas : vos propres charges de travail, pas ses démonstrations.

### 7.2. Mettre un prix sur chaque clause

On ne négocie pas tout. Le premier travail est de classer les demandes par valeur espérée, c'est-à-dire par montant en jeu multiplié par la probabilité que la clause joue. Pour le contrat fictif de 512 GPU à 3,0 u l'heure (mois de 720 heures, donc 36 mois = 39 813 120 u), voici quelques ordres de grandeur, recalculés en Python. Ce sont des montants en jeu, pas des espérances.

| Clause | Valeur en jeu (u) | Quand elle joue |
|---|---|---|
| 1 % de prix sur 36 mois | 398 131 | toujours |
| Facturation seulement de la capacité livrée (livraison sur 90 jours) | 2 488 320 | si la livraison est retardée |
| Plafond d'augmentation à 3 % au lieu de 8 % | 2 063 647 | si le fournisseur applique le plafond |
| Droit de sortie au mois 12 contre 3 mois de redevances | 3 317 760 payés au lieu de 26 542 080 | si la demande chute |
| Plafond de crédit à 30 % au lieu de 10 % | 221 184 par mois dégradé | si le service est mauvais |
| Responsabilité à 12 mois de redevances au lieu de 3 | 13 271 040 au lieu de 3 317 760 | si un incident grave survient |

La lecture est instructive. Un point de prix vaut moins que la souplesse sur la livraison ou que le droit de sortie. Et les clauses de protection (crédits, responsabilité) pèsent peu en espérance tant que le service est bon, mais décident de tout le jour où il ne l'est pas : on les négocie comme une assurance.

### 7.3. Une alternative crédible

Le levier le plus fort est de pouvoir partir. Fisher et Ury, dans *Getting to Yes*, appellent « BATNA » (*best alternative to a negotiated agreement*) ce que vous obtenez sans accord. Sa valeur fixe votre prix de réserve : le point au-delà duquel vous ne signez pas.

::: ex
[Exemple 7.1 — Le prix de réserve d'une location]{.tag} Reprenons les chiffres du chapitre 4. À une utilisation de 70 %, une location à $p$ u la GPU-heure bat la demande à 4,0 u tant que $p < u \times o = 0{,}7 \times 4{,}0 = 2{,}80$ u. Si l'achat est une alternative crédible, il fournit un second plafond : 2,08 u par heure disponible. Le prix de réserve est le plus bas des deux, donc 2,08 u, à condition que l'achat soit réalisable dans le délai.

Une offre à 2,6 u est donc acceptable face à la demande (2,6 < 2,8) mais pas face à un achat crédible (2,6 > 2,08). Obtenir 2,4 u au lieu de 2,6 u pour 512 GPU vaut 897 024 u par an, soit 2 691 072 u sur trois ans, mais ne change pas la conclusion face à l'achat : seul un levier de prix sous 2,08 u le ferait.
:::

Une alternative n'est crédible que si vous la remplissez : un devis écrit, un délai de livraison compatible avec votre besoin, et une charge de travail portable (le projet [Placement multi-fournisseurs](../../projects/multi-provider-scheduler/index.html) s'y exerce). Une alternative que vous ne pouvez pas exécuter dans le délai n'est pas une alternative, et le fournisseur le sent.

### 7.4. Calendrier et processus

Un achat de calcul se déroule en phases, chacune avec une sortie vérifiable.

| Phase | Sortie | Rôle de l'ingénieur |
|---|---|---|
| Besoin | plan de capacité chiffré (chapitre 3) | construit les scénarios et l'horizon |
| Consultation | réponses de plusieurs fournisseurs à un questionnaire technique | écrit les exigences mesurables |
| Essai | mesures sur vos charges de travail | conçoit et exécute les tests |
| Négociation | liste de demandes classées par valeur | traduit les résultats d'essai en clauses |
| Contrat | annexes techniques (recette, santé, performance) | relit les annexes |
| Recette | rapport de validation avant facturation | exécute la recette |

Menez au moins deux négociations en parallèle jusqu'à la fin : une négociation avec un seul interlocuteur n'a plus d'alternative. Gardez le calendrier réel pour vous : un délai que l'autre partie connaît est un levier pour elle. Prévoyez que l'essai et la recette prennent du temps de vos propres équipes, et comptez-le dans le coût.

### 7.5. Bonnes et mauvaises pratiques

Les pratiques ci-dessous sont des recommandations de ce parcours. Elles reposent sur la logique des chapitres précédents, pas sur une étude de marché.

**À faire.**

-   Séparer avant la discussion ce qui est indispensable de ce qui est souhaitable, et chiffrer chaque demande.
-   Échanger des éléments de valeur inégale : accepter une durée plus longue contre de la souplesse sur la livraison, ou une cible de 99,5 % contre une définition stricte de la disponibilité.
-   Transformer chaque promesse en nombre dans une annexe : délai, débit, durée.
-   Garder les tests sous votre contrôle et conserver les mesures de la recette.
-   Garder la sortie en vue : frais de transfert, restitution des données, certificat de suppression.

**À éviter.**

-   Négocier le prix seul et laisser « au mieux » sur le remplacement, la performance ou le support.
-   Engager le pic de la prévision plutôt que le quantile du chapitre 3.
-   Laisser le fournisseur choisir ou régler le benchmark.
-   Promettre des volumes ou des durées que votre prévision ne soutient pas : ces promesses se paient à vide.
-   Signer sans avoir regardé l'alternative la plus plausible.

::: recap
Points clés — chapitre 7

-   L'ingénieur apporte la demande chiffrée, le coût par heure utile, les exigences mesurables et les tests.
-   Classez les demandes par valeur en jeu : souplesse de livraison et droit de sortie valent souvent plus qu'un point de prix.
-   Le prix de réserve vient de l'alternative crédible : $u \times o$ face à la demande, coût disponible face à un achat réalisable.
-   Menez plusieurs négociations en parallèle, transformez chaque promesse en nombre dans une annexe, gardez les tests sous votre contrôle.
:::

## 8. Matrices de décision, appels d'offres techniques et pilotage trimestriel {#ch8}

Une fois les chiffres calculés et le contrat lu, il reste à décider, à consulter les fournisseurs de façon comparable et à suivre l'exécution. Ce chapitre donne les outils de ces trois étapes, avec leurs limites.

### 8.1. La matrice de décision pondérée

Une matrice de décision note chaque option sur plusieurs critères et pondère les notes. Elle sert à rendre un arbitrage explicite, pas à le calculer. Voici un exemple dont les notes (de 0 à 10) et les poids sont **inventés** pour l'illustration.

| Critère (poids) | Achat en colocation | Location 3 ans | Réservé 1 an | Demande et spot |
|---|---|---|---|---|
| Coût à forte utilisation (3) | 9 | 7 | 5 | 3 |
| Flexibilité (2) | 3 | 4 | 6 | 10 |
| Délai d'obtention (2) | 3 | 7 | 8 | 6 |
| Charge d'exploitation (1) | 3 | 7 | 8 | 9 |
| Risque d'approvisionnement (2) | 4 | 6 | 6 | 3 |
| **Total pondéré** | **5,0** | **6,2** | **6,3** | **5,6** |

La réservation sur un an arrive en tête avec 6,3, à une longueur de la location (6,2). Un écart de 0,1 point sur des notes subjectives ne constitue pas une décision : il faut tester la robustesse du classement.

::: ex
[Exemple 8.1 — Quelle confiance accorder au classement ?]{.tag} Le module `decision_matrix.py` du lab 15.3 tire 5 000 jeux de poids en multipliant chaque poids par un facteur uniforme entre 0,5 et 1,5. La réservation sur un an arrive première dans 63,4 % des tirages, la location sur 3 ans dans 34,4 %, la demande et le spot dans 2,2 % et l'achat dans aucun.

Le même module cherche le facteur qui renverse le classement. Il suffit de multiplier le poids du coût par 1,17 pour que la location passe devant, et celui de la flexibilité par 1,88 pour que la demande et le spot passent devant. Un classement qui bascule pour un changement de poids de 17 % n'est pas une conclusion : c'est une question à poser aux décideurs (« le coût compte-t-il vraiment 17 % de plus ? »).
:::

Trois règles de bonne hygiène. Dérivez les notes de mesures quand c'est possible (le coût vient du modèle du chapitre 4, le délai de devis écrits). Présentez des fourchettes plutôt que des notes uniques. Et montrez toujours l'analyse de robustesse à côté du classement.

### 8.2. L'appel d'offres technique

Un appel d'offres (*RFP*, *request for proposal*) technique permet de comparer des fournisseurs sur des bases identiques. Sa structure tient en sept blocs.

1.  Le besoin : plan de capacité et scénarios du chapitre 3, avec le calendrier souhaité.
2.  Les exigences, classées en obligatoires et souhaitables, chacune exprimée en nombre mesurable.
3.  Le protocole d'essai : vos charges de travail et vos outils de mesure, pas ceux du fournisseur.
4.  Le format de réponse : un tableau normalisé, pour que les réponses soient comparables ligne à ligne.
5.  Les critères d'évaluation et leur pondération, annoncés d'avance.
6.  Les références : des clients qui exploitent une configuration comparable.
7.  Les annexes contractuelles demandées : disponibilité, recette, performance, support.

Les exigences techniques se traduisent en tests de recette. Les seuils sont à fixer avec *vos* mesures ; le tableau donne les familles de tests et leur source dans ce parcours.

| Famille | Mesure | Où l'apprendre |
|---|---|---|
| Calcul | débit d'un GEMM en BF16 par rapport au pic dense | module 2, lab 2.1 |
| Réseau | débit de bus d'un all-reduce à plusieurs tailles de message | module 2, lab 2.2 ; module 7 |
| Stockage | débit et latence d'écriture d'un checkpoint | module 8 |
| Santé | diagnostics GPU et erreurs matérielles sur la durée du rodage | projet Observabilité des GPU |
| Ordonnancement | soumission, tableaux, préemption sous votre ordonnanceur | module 5 |
| Disponibilité | nombre de nœuds sains pendant la période d'essai | ce module, chapitre 6 |

### 8.3. Indicateurs de pilotage trimestriels

Un tableau de pilotage trimestriel tient en une page et sert à décider. Le document « FinOps for AI » de la Fondation propose, parmi ses indicateurs, l'efficacité d'utilisation des ressources : l'utilisation réelle divisée par la capacité provisionnée. Les indicateurs ci-dessous prolongent cette idée.

| Indicateur | Définition | Source | Propriétaire |
|---|---|---|---|
| Utilisation | GPU-heures allouées / GPU-heures disponibles | `sacct` (lab 15.1) | plateforme |
| Goodput | part des heures allouées qui produit du progrès (l'ETTR de Kokolis et al. compte en plus l'attente en file) | journaux d'entraînement, checkpoints | équipes d'entraînement |
| Attente p90 par classe | percentile 90 de (début − soumission) | `sacct` | plateforme |
| Coût par GPU-heure utile | coût plein / (heures disponibles × $u \times g$) | modèle du chapitre 4 | plateforme et finance |
| Couverture de l'engagement | heures engagées / heures totales | facturation | finance et achats |
| Utilisation de l'engagement | heures utilisées / heures engagées | facturation, `sacct` | plateforme |
| Erreur de prévision | biais et erreur absolue relative moyenne | lab 15.2 | ingénierie |
| Énergie | kWh par GPU-heure, PUE du site | relevés, fournisseur | exploitation |

Exemple de lecture de l'erreur de prévision. Sur quatre semaines, la demande observée est de 100, 110, 95 et 120 GPU et la prévision de 105, 100, 100 et 100. L'erreur absolue relative moyenne est de 9,0 % et le biais de −3,9 % (la prévision est en moyenne trop basse). Suivez les deux : le premier mesure l'imprécision, le second dit dans quel sens on se trompe.

### 8.4. La revue trimestrielle

La revue tient en trois questions. Les chiffres du trimestre sont-ils conformes au plan (écart de prévision, utilisation, attente) ? Qu'est-ce qui a changé dans les hypothèses (prix, délais, feuille de route) ? Quelle décision déclenche-t-on (commander, réduire, renégocier, ne rien faire) ?

Fixez à l'avance des seuils qui déclenchent des décisions. Par exemple (valeurs à fixer par vous) : une utilisation au-dessus de 85 % pendant quatre semaines avec une attente p90 au-dessus de l'objectif déclenche l'étude d'une extension ; une utilisation de l'engagement sous 60 % déclenche la renégociation ou la revente ; un biais de prévision supérieur à 15 % déclenche la révision du modèle. Le projet 6 vous fait rédiger une RFC qui rassemble ces éléments pour une plateforme de 8 à 256 GPU.

::: recap
Points clés — chapitre 8

-   Une matrice pondérée explicite un arbitrage ; testez toujours la robustesse du classement aux poids.
-   Un appel d'offres technique compare des fournisseurs sur des exigences mesurables, avec un protocole d'essai que vous contrôlez.
-   Un tableau de pilotage trimestriel suit l'utilisation, le goodput, l'attente, le coût par heure utile, l'engagement, l'erreur de prévision et l'énergie.
-   Fixez à l'avance les seuils qui déclenchent une décision.
:::

## Labs {#labs}

Les quatre labs s'exécutent sur un portable CPU avec Python 3, `pytest`, `numpy` et `pyyaml`, sans GPU ni compte cloud. Ils suivent le format des projets : un code de départ (`starter/`) dont les fonctions sont à écrire, une solution (`reference/`) à consulter après votre tentative, des tests partagés (la variable `IMPL=starter|reference` choisit le code testé) et un script `verify.sh` qui prouve que la référence passe et que le départ échoue. **Toutes les données sont étiquetées** : séries et traces synthétiques, prix fictifs, contrat fictif.

~~~bash
python3 -m venv .venv && . .venv/bin/activate
pip install pytest numpy pyyaml
export PYTHON="$(command -v python)"
~~~

### Lab 15.1 — Du sacct au rapport de showback {#lab-15-1}

::: lab

**Objectif.** Écrire l'outil qui transforme l'export de l'ordonnanceur en heures allouées par équipe, utilisation, heures perdues candidates, attentes et allocation du coût plein. **Durée.** 2,5 h. **Prérequis matériels.** Portable CPU, Python 3 et `pytest`. Pour la branche « live » : une machine Linux jetable avec accès root et le Slurm du module 5.

1.  Ouvrez `labs/finops-capacity/usage-showback/` et lisez `gen_trace.py` : ordonnancement FIFO strict, probabilités d'états finaux, en-tête `# SYNTHETIC` du fichier produit.
2.  Lancez `IMPL=starter python3 -m pytest -q tests` et repérez les tests qui échouent : ils décrivent les neuf fonctions de `starter/showback.py` à écrire.
3.  Écrivez-les une à une (`parse_tres`, `alloc_hours`, `usage_by_account`, `lost_candidates`, `utilization`, `percentile`, `wait_stats`, `allocate_idle`, `cost_report`), puis lancez `bash verify.sh`.
4.  Lancez le rapport avec `--idle proportional`, puis `equal`, puis `platform`, et comparez le total de l'équipe `eval`.
5.  Branche « live » : `sudo bash verify-live.sh` démarre le Slurm du bac à sable, soumet sept jobs, exporte `sacct` et compare vos heures à `CPUTimeRAW`.

**Critère de réussite.** `bash verify.sh` affiche `utilization (allocated / capacity): 54.9 %` puis « ok: usage-showback reference passes, starter fails as intended ». La branche live affiche `teama: showback 28 cpu-s, sacct CPUTimeRAW 28 cpu-s OK` (26 CPU-secondes à une autre exécution, les durées varient) puis « OK live: showback matches Slurm accounting ».

**Statut de vérification.** `verify.sh` a été exécuté deux fois avec succès (traces synthétique et réelle). `verify-live.sh` a été exécuté deux fois sur Slurm 23.11.4 le 24 octobre 2026 et la capture réelle est dans `fixtures/real_sandbox_sacct.txt`. Les CPU tiennent lieu de GPU : le format `gres/gpu` n'est testé que sur la trace synthétique.

**Pour aller plus loin.** Remplacez la trace synthétique par l'export de votre cluster. Ajoutez la lecture de `AllocTRES` avec plusieurs types de GPU et un coût par type.
:::

### Lab 15.2 — Prévision de la demande et capacité à engager {#lab-15-2}

::: lab

**Objectif.** Produire des scénarios de demande, en déduire la capacité à engager par la règle du quantile, mesurer le risque, et tester la prévision sur le passé. **Durée.** 2,5 h. **Prérequis matériels.** Portable CPU, Python 3, `numpy` et `pytest`.

1.  Ouvrez `labs/finops-capacity/demand-forecast/` et lisez `starter/forecast.py` (fourni) : générateur synthétique, ajustement tendance plus saison, scénarios par blocs, test sur le passé.
2.  Lancez `IMPL=starter python3 -m pytest -q tests` : dix échecs, tous dans `commit.py`.
3.  Écrivez `cost`, `optimal_commit`, `best_commit_grid` puis `risk_report` en suivant la formule du chapitre 3.
4.  Lancez `cd reference && python3 demo.py`, puis `demo.py --cap 20 --penalty 20`, puis `demo.py --seeds 8`.
5.  Variez le prix engagé de 3,6 à 1,6 et retrouvez le tableau de l'exemple 3.2.

**Critère de réussite.** `bash verify.sh` affiche `critical ratio 1-r/o = 0.350 -> commit 107 GPUs`, `mean yearly cost: 3620507 (all on-demand 4702537, saving 23.0 %)` et « ok: demand-forecast reference passes, starter fails as intended ». Les valeurs dépendent de la graine fixée (0) et de la version de `numpy` (testé avec Python 3.13 et numpy 2.5.4 le 24 octobre 2026) : avec une autre version, le flux aléatoire peut changer, et avec lui les chiffres exacts du chapitre 3 (les tests, eux, sont structurels et tolérants).

**Statut de vérification.** Deux exécutions réussies de `verify.sh` (17 tests verts pour la référence, 10 rouges au départ). Données entièrement synthétiques : seuls la méthode et les ordres de grandeur se transposent.

**Pour aller plus loin.** Branchez la sortie de `sacct` du lab 15.1 comme historique, ajoutez un engagement par paliers (deux niveaux, deux durées) et comparez-le au niveau unique.
:::

### Lab 15.3 — Modèle de coût total paramétrable {#lab-15-3}

::: lab

**Objectif.** Construire l'outil qui compare achat, location, réservation, demande et spot en coût par GPU-heure utile, trouve les points morts et classe les hypothèses par influence. **Durée.** 2,5 h. **Prérequis matériels.** Portable CPU, Python 3, `pyyaml` et `pytest`.

1.  Lisez `labs/finops-capacity/tco-model/assumptions.yaml` et classez chaque valeur : publiée (une seule : 10,2 kW) ou exemple.
2.  Lancez `IMPL=starter python3 -m pytest -q tests` : dix-huit échecs.
3.  Écrivez les sept fonctions de `starter/tco.py` : `annuity_factor`, `annualized_capex`, `owned_components`, `waste_fraction`, `cost_per_useful_hour`, `breakeven_utilization`, `sensitivity`.
4.  Lancez `python3 reference/tco.py assumptions.yaml --breakeven --sensitivity` et retrouvez les tableaux du chapitre 4.
5.  Remplacez trois valeurs de `assumptions.yaml` par des devis datés et sourcés, relancez, et notez le déplacement du point mort.
6.  Exécutez l'exemple de `decision_matrix.py` du chapitre 8 avec vos propres notes.

**Critère de réussite.** `bash verify.sh` affiche `breakeven owned vs on_demand   : u* = 0.516` et « ok: tco-model reference passes, starter fails as intended ».

**Statut de vérification.** Deux exécutions réussies de `verify.sh` (24 tests verts pour la référence, 18 rouges au départ). Les prix sont fictifs ; le modèle ignore taxes, inflation, remises de volume, limites de capacité et délais.

**Pour aller plus loin.** Ajoutez une capacité maximale au spot, un délai de livraison par option, ou un scénario où la revente est nulle.
:::

### Lab 15.4 — Revue d'un contrat de capacité fictif {#lab-15-4}

::: lab

**Objectif.** Appliquer une grille de revue à un contrat de capacité fictif, comprendre chaque clause rouge et chiffrer ce que vaut sa négociation. **Durée.** 1,5 h. **Prérequis matériels.** Portable CPU, Python 3, `pyyaml` et `pytest`.

1.  Lisez `labs/finops-capacity/contract-checklist/fictional_contract.md` **sans** lancer le script, et écrivez la liste des cinq clauses que vous refuseriez de signer.
2.  Lancez `python3 review.py fictional_contract.md rubric.yaml`. Comparez avec votre liste. Le code de sortie est 1 : au moins un *deal-breaker* est rouge.
3.  Lisez `answer_key.md` et le tableau des quatre *deal-breakers*, puis `sla.py` pour la mécanique des crédits.
4.  Lancez le script sur `fictional_contract_negotiated.md` et repérez les six clauses encore orange.
5.  Modifiez un seuil de `rubric.yaml` (par exemple la disponibilité verte à 99,5) et observez ce qui bouge.
6.  Rédigez une contre-proposition pour trois clauses rouges et relancez le script.

**Critère de réussite.** `bash verify.sh` affiche `contract score 7/100  (0 green, 5 amber, 19 red)` pour le contrat fictif et `contract score 88/100  (18 green, 6 amber, 0 red)` pour sa version négociée, puis « ok: contract-checklist agrees with the answer key ».

**Statut de vérification.** Deux exécutions réussies de `verify.sh` (12 tests). Le contrat est écrit pour le cours : ses nombres sont inventés et ses problèmes plantés. La grille est une aide au tri, pas un avis juridique.

**Pour aller plus loin.** Appliquez la même grille à un contrat réel dont vous avez le droit de lire le texte, en remplaçant les expressions régulières par un relevé manuel des clauses.
:::

## Exercices {#ex}

Les prix sont fictifs (unités arbitraires, notées « u »). Les corrigés ont été recalculés en Python ; les commandes qui y figurent ont été exécutées.

::: exo
[Exercice 1 · ★ — Coût d'un fine-tuning]{.tag} Un fine-tuning complet d'un modèle de $13 \cdot 10^9$ paramètres sur $2 \cdot 10^9$ tokens coûte $6NT$ FLOP. Le MFU est de 35 % sur des GPU de 989 TFLOP/s dense, et le coût plein est de 2,08 u par GPU-heure disponible. Calculez les GPU-heures, la durée sur 16 GPU, le coût, le coût par million de tokens, puis le coût si 10 % des heures allouées sont perdues.
:::

::: sol
Les FLOP valent $6NT = 1{,}56 \cdot 10^{20}$. Un GPU délivre $0{,}35 \times 989 \cdot 10^{12} = 3{,}46 \cdot 10^{14}$ FLOP/s utiles, d'où :

$$\frac{1{,}56 \cdot 10^{20}}{3{,}46 \cdot 10^{14} \times 3600} = 125{,}2 \text{ GPU-heures}$$

Sur 16 GPU, la durée est de $125{,}2 / 16 = 7{,}8$ h. Le coût est de $125{,}2 \times 2{,}08 \approx 260$ u, soit 0,13 u par million de tokens ($260/2000$). Si 10 % des heures allouées sont perdues, il faut allouer $125{,}2/0{,}9 = 139{,}1$ heures : le coût monte à 289 u (+11 %).
:::

::: exo
[Exercice 2 · ★ — Chaîne de rendements]{.tag} Une flotte a une disponibilité de 0,95, une allocation de 0,62, un goodput de 0,88 et un MFU de 0,38. Calculez la part du pic achetée qui devient du calcul utile et le coût d'une « GPU-heure équivalente au pic » au coût plein de 2,08 u. Si chaque facteur peut gagner 5 points absolus, lequel apporte le plus en valeur relative ?
:::

::: sol
Le produit vaut $0{,}95 \times 0{,}62 \times 0{,}88 \times 0{,}38 = 0{,}197$ : environ 20 % du pic acheté. Une heure équivalente au pic coûte $2{,}08 / 0{,}197 = 10{,}56$ u, cinq fois le coût disponible.

Cinq points de plus donnent un gain relatif de $0{,}05/0{,}95 = 5{,}3$ % pour la disponibilité, 8,1 % pour l'allocation, 5,7 % pour le goodput et 13,2 % pour le MFU. Le plus faible facteur gagne le plus en valeur relative. Mais les cinq points ne coûtent pas le même effort : monter le MFU de 0,38 à 0,43 est un travail d'ingénierie sur le code, alors que monter la disponibilité relève de l'exploitation.
:::

::: exo
[Exercice 3 · ★★ — Mettre les pools en commun]{.tag} Un cluster de 64 GPU sert des jobs de 8 GPU qui durent 10 heures en moyenne. Option A : quatre équipes ont chacune 16 GPU (deux emplacements). Option B : un pool commun de 64 GPU (huit emplacements). Avec le modèle M/M/c et la formule d'Erlang C, comparez la probabilité d'attendre et l'attente moyenne à 70 % puis à 80 % d'utilisation. Citez deux limites du modèle.
:::

::: sol
Avec $a = \rho c$ le trafic offert, la probabilité d'attendre est la formule d'Erlang C et l'attente moyenne vaut $C(c,a) / (c(1-\rho))$ durées de job. Le calcul :

~~~python
import math

def erlang_c(c, a):
    s = sum(a**k / math.factorial(k) for k in range(c))
    top = a**c / math.factorial(c) * c / (c - a)
    return top / (s + top)

def mean_wait(c, rho, service_h):
    return erlang_c(c, rho * c) / (c * (1 - rho)) * service_h

for rho in (0.7, 0.8):
    print(rho, mean_wait(2, rho, 10), mean_wait(8, rho, 10))
~~~

À 70 % : probabilité d'attendre 0,576 (A) contre 0,271 (B), attente moyenne de 9,6 h contre 1,1 h (8,5 fois moins). À 80 % : 0,711 contre 0,458, et 17,8 h contre 2,9 h (6,2 fois moins). Limites : arrivées de Poisson et durées exponentielles sont optimistes (les durées réelles ont des queues lourdes, et les jobs ont plusieurs tailles) ; la mise en commun suppose quotas et préemption pour protéger les petites équipes.
:::

::: exo
[Exercice 4 · ★★ — Lire un rapport de showback]{.tag} Voici la fin d'un rapport produit sur la trace synthétique du lab 15.1 (64 GPU, 28 jours, coût plein 2,08 u par GPU-heure, 89 457 u au total).

~~~text
account    jobs    alloc_h    direct      idle     total p50 wait p90 wait
nlp          19    14245.4     29630     24371     54001    0.00h    6.64h
vision       78     7475.2     15548     12789     28337    0.00h   13.11h
eval        678      977.3      2033      1672      3705    0.00h   10.12h
dev         346      900.5      1873      1541      3414    0.00h   10.38h
utilization (allocated / capacity): 54.9 %
lost candidates: FAILED 1096, TIMEOUT 692, NODE_FAIL 693, PREEMPTED 138 = 11.1 % of allocated hours
fleet wait: p50 0.00 h, p90 10.41 h
~~~

(a) Un directeur propose de réduire la flotte de moitié puisqu'elle est à 55 %. Quelle ligne du rapport vous fait hésiter ? (b) Combien paierait l'équipe `eval` avec les politiques « égale » et « plateforme » ? (c) Quelle part du coût plein représentent les heures perdues candidates ? (d) Quelle première action proposez-vous ?
:::

::: sol
(a) L'attente : malgré 55 % d'utilisation, le p90 est de 10,4 h pour la flotte, et de 16,2 h pour les jobs de 16 GPU ou plus (calcul sur la trace). L'attente vient de la fragmentation et du blocage en tête de file, pas du manque moyen de capacité ; réduire de moitié la flotte multiplierait l'attente (chapitre 2).

(b) Avec `--idle equal`, le coût d'inactivité se partage en quatre parts égales : `eval` paie 12 126 u, contre 3 705 u en proportionnel (3,3 fois plus). Avec `--idle platform`, `eval` paie son coût direct de 2 033 u et la plateforme porte 40 372 u d'inactivité. Dans les trois cas, la somme est de 89 457 u.

(c) Les 2 619 GPU-heures perdues candidates coûtent $2619 \times 2{,}08 \approx 5\,448$ u, soit 6,1 % du coût plein : une borne supérieure, puisque des checkpoints en récupèrent une partie.

(d) D'abord l'attente : vérifier le *backfill*, la précision des durées demandées et la politique de gros jobs (module 5). Ensuite les 693 GPU-heures perdues en `NODE_FAIL`, qui désignent une cause matérielle à instruire avec le module 14.
:::

::: exo
[Exercice 5 · ★★ — Quelle capacité engager, à la main]{.tag} La demande hebdomadaire d'une équipe vaut 40, 80 ou 120 GPU avec la même probabilité. Un GPU engagé coûte $r = 2{,}5$ u par heure, qu'il serve ou non ; un GPU à la demande coûte $o = 4{,}0$ u. (a) Quelle capacité $L$ minimise le coût moyen par heure ? (b) Même question avec $r = 1{,}2$ u. Vérifiez par le calcul direct du coût de chaque niveau possible.
:::

::: sol
(a) Le ratio critique vaut $1 - r/o = 0{,}375$. La fonction de répartition vaut $1/3$ en 40 et $2/3$ en 80 : le plus petit niveau où elle atteint 0,375 est $L^{*} = 80$.

Coût moyen par heure : $L=0$ : 320 ; $L=40$ : $100 + 4 \times (0+40+80)/3 = 260$ ; $L=80$ : $200 + 4 \times 40/3 = 253{,}3$ ; $L=120$ : 300. Le minimum est bien en 80.

(b) Le ratio critique vaut $1 - 1{,}2/4 = 0{,}7 > 2/3$, donc $L^{*} = 120$. Coûts : 320, 208, 149,3 et 144 pour $L = 0, 40, 80, 120$. Une remise plus forte pousse l'engagement vers le pic de la distribution.
:::

::: exo
[Exercice 6 · ★★★ — Diagnostic de deux prévisions ratées]{.tag} Le test du lab 15.2 sur huit historiques synthétiques donne, pour deux graines, ces résultats (erreur absolue moyenne en GPU, couverture de la bande entre déciles 10 et 90).

~~~text
seed 5  model MAE 73.2  naive MAE 11.7  coverage 0.08   fitted growth 93 %/year, forecast mean 132 vs actual 64
seed 7  model MAE 59.8  naive MAE 76.0  coverage 0.42   fitted growth 71 %/year, forecast mean  95 vs actual 132
~~~

Les campagnes tirées pour la graine 5 démarrent aux semaines 36, 45, 49, 66 et 77 (la dernière dure trois semaines, les autres de quatre à sept) ; pour la graine 7, certaines démarrent aux semaines 88, 90, 90, 94 et 99 (la fenêtre d'ajustement couvre les semaines 0 à 77, le test les semaines 78 à 103). Expliquez chaque échec, dites ce que vous changeriez dans la démarche, et ce que vous engageriez.
:::

::: sol
**Graine 5 : sur-prévision.** Les cinq campagnes démarrent dans la fenêtre d'ajustement et quatre y finissent ; la dernière (semaine 77, trois semaines) déborde de deux semaines sur le test. La droite log-linéaire les prend pour une croissance (+93 % par an), prolonge la pente, et prévoit 132 GPU alors que la demande de base est restée à 64. La prévision naïve (erreur de 11,7 GPU) bat le modèle (73,2) : la bande couvre 8 % des semaines.

**Graine 7 : sous-prévision.** Cinq campagnes arrivent après la fenêtre d'ajustement. Aucune méthode statistique ne les voit venir : la demande réelle moyenne est de 132 GPU pour une prévision de 95. Le modèle bat ici la prévision naïve (59,8 contre 76,0), mais la bande est trop étroite (couverture de 42 %).

Changements : séparer le socle des campagnes (ajuster le socle sur les semaines sans campagne, planifier les campagnes avec la feuille de route) ; comparer systématiquement à la prévision naïve ; élargir les bandes ou raisonner par scénarios nommés. Engagement : le quantile de la demande de *socle*, pas de la demande totale, le reste en capacité flexible, et révision trimestrielle (chapitre 3).
:::

::: exo
[Exercice 7 · ★ — Point mort entre achat et demande]{.tag} Un GPU possédé coûte 17 000 u par an, énergie comprise et constante. À la demande, une GPU-heure coûte 4,0 u. (a) Quelle utilisation minimale justifie l'achat ? (b) Quel est le coût par heure utile de chaque option à une utilisation de 40 % puis de 80 %, avec un goodput de 0,9 ?
:::

::: sol
(a) Le point mort est $u^{*} = 17\,000 / (8760 \times 4{,}0) = 0{,}485$ (le goodput se simplifie).

(b) À $u = 0{,}4$ : le parc possédé coûte $17\,000 / (8760 \times 0{,}4 \times 0{,}9) = 5{,}39$ u par heure utile, la demande $4{,}0/0{,}9 = 4{,}44$ u : l'achat coûte 21 % de plus. À $u = 0{,}8$ : le parc coûte 2,70 u, 39 % de moins que la demande. L'achat n'a de sens que si l'on sait remplir le parc.
:::

::: exo
[Exercice 8 · ★★ — Dimensionner puissance et baies]{.tag} Une salle compte 40 baies limitées à 20 kW chacune. Le budget électrique total de l'installation est de 1,2 MW et le PUE vaut 1,35. On y installe des nœuds de 10,2 kW. (a) Combien de nœuds permet la puissance ? Combien permettent les baies ? (b) Quelle puissance est inutilisée ? (c) Que se passe-t-il si la limite passe à 21 kW par baie, et que vérifier avant ?
:::

::: sol
(a) La puissance informatique disponible est $1200 / 1{,}35 = 888{,}9$ kW, soit $\lfloor 888{,}9/10{,}2 \rfloor = 87$ nœuds. Une baie de 20 kW ne reçoit qu'un nœud (deux demanderaient 20,4 kW) : 40 baies donnent 40 nœuds, soit 320 GPU. Les baies sont la contrainte.

(b) Chaque baie laisse 9,8 kW inutilisés ; la salle utilise 408 kW sur 888,9 disponibles (46 %).

(c) À 21 kW, une baie reçoit deux nœuds (20,4 kW) : 80 nœuds, soit 640 GPU, pour 816 kW informatiques et 1 101,6 kW avec le PUE, sous le budget de 1 200 kW. Les baies restent la contrainte (80 nœuds contre 87 permis par la puissance, soit une marge de 71 kW informatiques). À vérifier avant : les 21 kW par baie traversent la distribution électrique et le refroidissement ; au-delà de 20 à 25 kW, l'Uptime Institute note que le refroidissement liquide direct devient plus économique.
:::

::: exo
[Exercice 9 · ★ — Air ou liquide]{.tag} (a) Un rack de 120 kW est refroidi à l'eau avec un échauffement de 10 K. Quel débit en litres par minute ? Et avec 12 K ? (b) Quel débit d'air faudrait-il avec l'échauffement de 16,2 K du DGX H100, et à combien de ventilations de DGX H100 cela correspond-il ? (c) Convertissez les 38 557 BTU/h de la fiche du DGX H100 en kW et comparez aux 10,2 kW.
:::

::: sol
(a) Le débit massique vaut $P/(c_p \Delta T) = 120\,000 / (4186 \times 10) = 2{,}87$ kg/s, soit 172 L/min (environ 1 kg par litre). À 12 K : 143 L/min.

(b) Pour l'air ($\rho = 1{,}2$ kg/m³, $c_p = 1005$ J/(kg·K)) : $120\,000 / (1{,}2 \times 1005 \times 16{,}2) = 6{,}14$ m³/s, soit environ 13 000 CFM, ou 11,8 fois le débit de 1 105 CFM d'un DGX H100.

(c) $38\,557 / 3412{,}14 = 11{,}3$ kW, soit 10,8 % de plus que 10,2 kW. Les deux chiffres figurent sur la même page : dimensionnez sur le plus grand et demandez les conditions de mesure au constructeur.
:::

::: exo
[Exercice 10 · ★★ — Lire un SLA publié]{.tag} La facture mensuelle fictive d'un parc de 512 GPU est de 1 105 920 u (3,0 u par GPU-heure sur 720 h). Une région affiche 99,7 % de disponibilité mensuelle.

D'après la grille du SLA d'Amazon EC2 du 25 mai 2022 (99,99 % de cible régionale, crédits de 10 %, 30 % et 100 %), répondez. (a) Combien de minutes d'arrêt cela représente-t-il sur 30 jours ? (b) Quel crédit, et sous quelle forme ? (c) Que faut-il faire pour l'obtenir ? (d) Quel crédit si un GPU est défaillant sur une instance qui répond au réseau ? (e) Comment le crédit se compare-t-il à la valeur des GPU-heures perdues ?
:::

::: sol
(a) $0{,}003 \times 43\,200 = 129{,}6$ minutes.

(b) La disponibilité est inférieure à 99,99 % et supérieure à 99,0 % : crédit de 10 %, soit 110 592 u, déduit de paiements futurs et non remboursé.

(c) Ouvrir un dossier au support, avec les informations demandées, avant la fin du deuxième cycle de facturation qui suit l'incident ; le crédit est le recours exclusif.

(d) Aucun : pour une instance isolée, l'indisponibilité est l'absence de connectivité externe, et l'instance est donc disponible.

(e) Si tout le parc est arrêté pendant 129,6 minutes, les GPU-heures perdues valent $512 \times 129{,}6/60 \times 3{,}0 = 3\,318$ u : le crédit en vaut 33 fois plus. Ce rapport s'inverse pour une panne partielle ou une dégradation silencieuse, et il ne compte pas le travail perdu depuis le dernier checkpoint.
:::

::: exo
[Exercice 11 · ★★★ — Priorités d'une revue de contrat]{.tag} Voici le début de la sortie du script du lab 15.4 sur le contrat fictif.

~~~text
contract score 7/100  (0 green, 5 amber, 19 red)
deal-breakers red: take_or_pay, delivery_remedy, availability_scope, provider_exit
~~~

Le prix proposé est 3,0 u par GPU-heure pour 512 GPU ; une réservation d'un an à 3,4 u est disponible chez un autre fournisseur. (a) Classez les cinq demandes que vous formuleriez d'abord, avec leur valeur en jeu quand elle se chiffre. (b) Pour chacune, une position de repli. (c) Signez-vous le contrat en l'état ? Justifiez avec la prime de l'alternative.
:::

::: sol
(a) Ordre proposé : 1. périmètre de la disponibilité (clause 3.2 : sans définition par santé des GPU, l'ensemble du SLA est vide) ; 2. résiliation unilatérale par le fournisseur (9.4 : risque existentiel, 30 jours de préavis sans remboursement) ; 3. paiement à vide et livraison sans recours (1.2 et 2.2 : 2 488 320 u si 75 % de la capacité arrive après 90 jours).

La suite : 4. plafond d'augmentation de 8 % (3 269 984 u de plus sur 3 ans, contre 1 206 338 u à 3 %) ; 5. délai de remplacement et substitution (4.1 et 4.2), avec le plancher de performance.

(b) Replis : accepter 99,5 % si la définition est stricte ; accepter la livraison par tranches si la facturation suit la recette ; accepter une résiliation par le fournisseur seulement pour impayé ou abus, avec préavis ; accepter 5 % de hausse plafonnée ; accepter 48 h de remplacement si le nœud compte comme indisponible.

(c) Non. Quatre *deal-breakers* sont rouges. Renoncer coûte 1 794 048 u par an de plus ($0{,}4 \times 512 \times 8760$ pour la réservation à 3,4 u), soit 5,4 M u sur les trois ans du contrat à prix constant, à comparer aux expositions chiffrées (2,49 M u de paiement à vide, 3,3 M u de hausses). Ce sont des montants maximaux en jeu, pas des espérances : le chiffre ne tranche donc pas seul.

Ce qui tranche, c'est le risque que vous ne pouvez pas chiffrer (résiliation par le fournisseur, SLA vide), que la prime de l'alternative doit couvrir. Le raisonnement porte sur des prix fictifs, à refaire avec vos devis ; la version négociée du lab (88/100) montre où se situe une issue acceptable.
:::

::: exo
[Exercice 12 · ★★★ — Deux offres, un arbitrage chiffré]{.tag} Offre A : 512 GPU pendant 36 mois à 2,4 u par GPU-heure, paiement à vide, sans sortie. Offre B : même capacité à 3,2 u pour 12 mois renouvelables, avec ajustement annuel à la demande réelle (utilisation de 0,9 après ajustement). La demande de l'équipe est soit forte (utilisation de 0,9 de la capacité de A) avec une probabilité $p$, soit faible (0,45) avec une probabilité $1-p$, pour les trois années. Comparez le coût par heure utile, trouvez la probabilité qui rend A préférable, chiffrez le regret du cas défavorable, et proposez une clause.
:::

::: sol
Pour A, le coût par heure utile en espérance (coût total espéré divisé par les heures utiles espérées) est $2{,}4 / (0{,}9p + 0{,}45(1-p))$. Pour B, qui suit la demande, il est de $3{,}2/0{,}9 = 3{,}56$ u. À $p = 0{,}6$, A coûte $2{,}4/0{,}72 = 3{,}33$ u : A est moins cher en espérance.

A l'emporte quand cette espérance est inférieure à 3,56 u, soit pour $p > 0{,}5$. Le cas favorable donne 2,67 u pour A. Le cas défavorable donne $2{,}4/0{,}45 = 5{,}33$ u, plus que la demande à 4,0 u. Le regret annuel de A face à un achat à la demande des seules heures utiles vaut :

$$512 \times 8760 \times (2{,}4 - 4{,}0 \times 0{,}45) = 2\,691\,072 \text{ u}$$

Clause à demander : un droit de sortie au mois 12 contre trois mois de redevances, soit $3 \times 2{,}4 \times 512 \times 730 = 2\,691\,072$ u (un montant égal, par coïncidence, au regret d'une année). Dans le cas défavorable, la perte passe de trois années de regret (8 073 216 u) à une année de regret plus les frais de sortie (5 382 144 u). La décision dépend de $p$ : si vous ne pouvez pas affirmer qu'elle dépasse 50 %, préférez B ou négociez la sortie.
:::

::: exo
[Exercice 13 · ★★ — Robustesse d'une matrice]{.tag} Reprenez la matrice du chapitre 8 avec les poids : coût 3, flexibilité 4, délai 2, exploitation 1, approvisionnement 2. Calculez les totaux, le classement, la probabilité de gagner de chaque option quand chaque poids varie de ±50 %, et les multiplicateurs qui renversent le classement. Conclusion ?
:::

::: sol
Avec le module du lab (`python3` dans `labs/finops-capacity/tco-model`), les poids sont normalisés puis multipliés aux notes :

~~~python
import decision_matrix as dm
w = {"cost_at_high_util": 3, "flexibility": 4, "time_to_capacity": 2, "ops_load": 1, "risk_supply": 2}
print(dm.total_scores(dm.EXAMPLE_SCORES, w))
print(dm.win_probability(dm.EXAMPLE_SCORES, w, rel=0.5, draws=5000, seed=0))
~~~

Totaux : achat 4,67 ; location 5,83 ; réservé 6,25 ; demande et spot 6,33. La demande et le spot sont premiers, d'un cheveu devant le réservé. Sur 5 000 tirages : demande et spot 57,2 %, réservé 38,3 %, location 4,5 %, achat 0 %. Multiplier le poids du coût ou de l'approvisionnement par 1,17, ou celui du délai par 1,25, renverse le classement.

Conclusion : l'écart de 0,08 point ne fait pas une décision. Remplacez les notes subjectives par des mesures, ou retenez un mélange (socle réservé, pointes à la demande) au lieu d'un gagnant.
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux exprimer le coût d'un cluster en GPU-heure utile.** Preuve : l'exercice 2 refait avec vos propres mesures de disponibilité, d'allocation, de goodput et de MFU.
-   **Je peux produire un rapport de showback depuis l'ordonnanceur.** Preuve : le lab 15.1 appliqué à votre export `sacct`, avec la conservation du coût plein vérifiée.
-   **Je peux prévoir la demande et justifier une capacité à engager.** Preuve : le lab 15.2 avec son test sur le passé comparé à une prévision naïve, et le quantile retenu.
-   **Je peux comparer achat, location, réservation et demande par un modèle de coût total.** Preuve : le lab 15.3 avec trois devis datés et le classement des hypothèses par influence.
-   **Je peux dimensionner puissance, baies et refroidissement.** Preuve : l'exercice 8 refait pour une salle réelle ou une salle supposée, avec la contrainte qui lie.
-   **Je peux lire un contrat de capacité et chiffrer ses clauses.** Preuve : le lab 15.4 et la liste ordonnée de vos demandes, chacune avec sa valeur en jeu.
-   **Je peux préparer une négociation et un appel d'offres.** Preuve : un prix de réserve (exemple 7.1) et une annexe de recette avec des seuils mesurables.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Un fournisseur propose 99,9 % de disponibilité. Est-ce suffisant pour nos entraînements ?* Réponse-type : demander ce qui est mesuré (joignabilité du nœud ou état de santé des GPU et du réseau), à quelle échelle (cluster ou nœud-heure), avec quel recours (crédits plafonnés, recours exclusif). Un nœud en panne parmi 64 arrête un job synchrone sans déclencher de crédit. Exiger une définition par contrôles de santé, un délai de remplacement en heures, et suivre le goodput réel.
2.  *Combien de GPU faut-il engager pour l'an prochain ?* Réponse-type : ce n'est pas un nombre mais un quantile. Construire des scénarios à partir de la demande à la soumission, tester le modèle contre une prévision naïve, engager le niveau dépassé dans une fraction $r/o$ des semaines, raisonner sur la rareté des GPU à la demande, couvrir le reste de façon flexible et réviser chaque trimestre.
3.  *Faut-il acheter ou louer 256 GPU ?* Réponse-type : comparer le coût par heure utile à l'utilisation prévue et le point mort face à la demande, avec durée de vie, revente, personnel, puissance, baies, refroidissement et délais. Tester la sensibilité, confronter à une alternative crédible, et ne jamais décider sur le prix catalogue d'une GPU-heure.

## Lectures et références {#refs}

-   FinOps Foundation. *FinOps Framework* (principes, personas, domaines, capacités, périmètres) et *FOCUS*, la spécification ouverte de normalisation des données de facturation. [finops.org/framework](https://www.finops.org/framework/), [focus.finops.org](https://focus.finops.org/). Consultées le 24 octobre 2026 : chapitres 1 et 8.
-   FinOps Foundation. *FinOps for AI Overview*. [finops.org](https://www.finops.org/wg/finops-for-ai-overview/). Consulté le 24 octobre 2026 : rareté des GPU, showback, indicateurs (chapitres 1, 3 et 8).
-   NVIDIA. *DGX H100/H200 User Guide* et *DGX B200 User Guide*, chapitres d'introduction : puissance, alimentations, débit d'air, chaleur dégagée. [DGX H100](https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html), [DGX B200](https://docs.nvidia.com/dgx/dgxb200-user-guide/introduction-to-dgxb200.html) : chapitre 5.
-   NVIDIA. *NVIDIA Contributes NVIDIA GB200 NVL72 Designs to Open Compute Project*, blog technique, 2024. [developer.nvidia.com](https://developer.nvidia.com/blog/nvidia-contributes-nvidia-gb200-nvl72-designs-to-open-compute-project/) : les 120 kW de refroidissement requis par rack (chapitre 5).
-   Google. *Data Center Efficiency* (PUE). [datacenters.google/efficiency](https://datacenters.google/efficiency/) : définition du PUE et valeurs de 2025 (chapitre 5).
-   Uptime Institute. *Rack Density is Rising*, 2020. [journal.uptimeinstitute.com](https://journal.uptimeinstitute.com/rack-density-is-rising/) : densités par baie observées en 2020 (chapitre 5).
-   Shehabi et al. *2024 United States Data Center Energy Usage Report*, Lawrence Berkeley National Laboratory, 2024. [escholarship.org](https://escholarship.org/content/qt32d6m0d1/qt32d6m0d1.pdf), publié le 20 décembre 2024 : 176 TWh en 2023 (chapitre 5).
-   Amazon Web Services. *Amazon EC2 Service Level Agreement*. [aws.amazon.com](https://aws.amazon.com/compute/sla/). Google Cloud. *Compute Engine Service Level Agreement*. [cloud.google.com](https://cloud.google.com/compute/sla) : structure des SLA et des crédits, à relire le jour de la décision (chapitre 6).
-   Amazon Web Services. *Capacity Blocks for ML* et *Spot Instance interruption notices*. [Capacity Blocks](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-capacity-blocks.html) (prix et facturation : [page dédiée](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/capacity-blocks-pricing-billing.html)), [Spot](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html) : réservations de courte durée et préavis de deux minutes (chapitre 4).
-   Amazon Web Services. *Free data transfer out to internet when moving out of AWS*, billet de blog avec mises à jour. [aws.amazon.com](https://aws.amazon.com/blogs/aws/free-data-transfer-out-to-internet-when-moving-out-of-aws/) : dérogation aux frais de sortie (chapitre 6).
-   Kokolis et al. *Revisiting Reliability in Large-Scale Machine Learning Research Clusters*. 2024. [arXiv:2410.21680](https://arxiv.org/abs/2410.21680) : utilisation de 83 % et 85 %, définition de l'ETTR (chapitre 2).
-   Dubey et al. *The Llama 3 Herd of Models*. 2024. [arXiv:2407.21783](https://arxiv.org/abs/2407.21783) : temps d'entraînement effectif, interruptions, variations de puissance (chapitres 2 et 5).
-   Hu et al. *Characterization of Large Language Model Development in the Datacenter*. 2024. [arXiv:2403.07648](https://arxiv.org/abs/2403.07648) : temps perdu des jobs d'évaluation (chapitre 2).
-   SchedMD. [*sacct*](https://slurm.schedmd.com/sacct.html) et [*slurm.conf*](https://slurm.schedmd.com/slurm.conf.html) : champs `AllocTRES`, `ElapsedRaw`, `CPUTimeRAW` ; mémoire par défaut (chapitre 2).
-   Fisher, Ury. *Getting to Yes: Negotiating Agreement Without Giving In*. Houghton Mifflin, 1981. [notice](https://en.wikipedia.org/wiki/Getting_to_Yes) : la notion de BATNA (chapitre 7).

## Sources et portée {#sources}

### Documenté {#documente}

Les faits suivants ont été relus à la source le 24 octobre 2026 : les principes, personas, domaines, capacités et périmètres de la FinOps Foundation ; les indicateurs et les recommandations de showback du document « FinOps for AI » ; la puissance maximale de 10,2 kW du DGX H100, de 14,3 kW du DGX B200, les alimentations de 3,3 kW, le débit d'air, la température de fonctionnement et la chaleur dégagée de 38 557 BTU/h ; le TDP du H100 (page produit) et les 120 kW du rack GB200 NVL72 ; le PUE de Google et la moyenne de l'Uptime Institute citée par Google ; les densités de baie de l'enquête 2020 ; les 176 TWh du rapport du LBNL ; la structure et les crédits du SLA d'Amazon EC2 (page datée du 25 mai 2022) et de Google Compute Engine ; les conditions des Capacity Blocks et le préavis Spot d'AWS ; la dérogation aux frais de sortie d'AWS et sa mise à jour du 8 octobre 2026 ; les chiffres de Kokolis et al., Dubey et al. et Hu et al. ; les champs de `sacct` et le défaut de `DefMemPerCPU`. Tous les calculs des exemples et des corrigés ont été refaits en Python, les observations de Slurm ont été faites sur Slurm 23.11.4 (paquets Ubuntu 24.04) le 24 octobre 2026, et les quatre `verify.sh` ainsi que `verify-live.sh` ont été exécutés deux fois avec succès.

### Recommandé {#recommande}

Les politiques d'allocation de l'inactivité, la règle de dimensionner sur la puissance maximale, la grille de revue de contrat (poids et seuils), les seuils du tableau de pilotage, la marge de souplesse de 10 à 20 % sur un engagement, l'ordre des demandes de négociation, la matrice de décision et la plage de ±20 % de l'analyse de sensibilité sont des choix de ce parcours, pas des normes. La règle du quantile pour l'engagement est un résultat classique, présenté ici comme outil pédagogique.

### À vérifier {#a-verifier}

Tous les prix, remises, durées de vie, tarifs d'énergie, taux d'interruption et notes de la matrice de décision sont des valeurs d'exemple fictives. Les résultats d'Erlang C et du vendeur de journaux sont classiques et n'ont pas été rouverts dans un manuel : le premier a été confronté à la simulation à événements discrets du projet 6 (200 000 jobs, trois graines), le second à une minimisation numérique du coût (test `test_closed_form_matches_the_grid_minimizer` du lab 15.2). Le texte du règlement européen sur les données n'a pas pu être lu (le site officiel refuse l'accès automatisé depuis le bac à sable) : seule la mention qu'en fait AWS est citée. Aucun délai de raccordement ou de livraison n'est donné, faute de source primaire lue. Les chiffres de l'Uptime Institute sont ceux de 2020 pour les densités ; la moyenne de 2025 est citée d'après la note de Google, sans lecture de l'enquête. L'écart entre 38 557 BTU/h et 10,2 kW n'est pas expliqué par la documentation. L'effet de `DefMemPerCPU` sur la capture est cohérent avec la documentation mais n'a pas fait l'objet d'un essai contraire. Les SLA des fournisseurs changent et peuvent différer pour les instances GPU et les réservations : relisez le texte en vigueur. L'existence du livre de Fisher et Ury et le sens de BATNA ont été confirmés par une notice encyclopédique, le livre n'a pas été relu. Aucun lab n'utilise de GPU : le format `gres/gpu` n'est testé que sur la trace synthétique, la branche « live » utilise des CPU.

### Hors périmètre {#hors-perimetre}

Les contrats de colocation détaillés (alimentation, redondance, accès), le droit des contrats et de la souveraineté des données, la fiscalité et la comptabilité (amortissement fiscal, crédit-bail), l'empreinte carbone et la mesure des émissions, la conception des circuits de refroidissement, le marché secondaire des GPU, l'achat de réseau et de stockage, et la FinOps de l'inférence à grande échelle en production.
