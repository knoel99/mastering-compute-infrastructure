---
title: "Ray, infrastructure d'apprentissage par renforcement et boucles en ligne"
subtitle: "Module 11 · Phase 3 · 30,5 h"
description: "Les charges qui ne sont pas un simple gros job : tâches et acteurs Ray, boucles acteurs-apprenant, obsolescence des politiques, contre-pression, pools hétérogènes et moteurs d'inférence."
module:
  id: ray-rl-infra
  number: 11
  phase: 3
  hours: 30.5
  level: 3
prerequisites: [distributed-training]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs vérifiés en local sur CPU (Ray 2.59)", class: verified}
labs:
  - {id: ray-actors, kind: sandbox}
  - {id: actor-learner-toy, kind: sandbox}
  - {id: throughput-model, kind: sandbox}
  - {id: batching-sim, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** que faire quand la charge n'est pas un job SPMD (*single program, multiple data* : tous les processus exécutent le même programme sur des données différentes) de 512 GPU, mais une application faite de rôles différents qui s'échangent des données en continu ? Un entraînement par renforcement d'un modèle de langage en est l'exemple type : des moteurs de génération produisent des trajectoires (ici, des réponses complètes), un évaluateur les note, un apprenant met à jour la politique (le modèle qui choisit les actions), puis les nouveaux poids retournent aux générateurs.

Les modules précédents traitaient un job : le placer, le faire survivre, le mesurer. Ici, la charge est un petit système distribué avec ses files, ses états et ses pannes partielles. Le module vous donne quatre outils : le modèle de programmation de Ray (tâches, acteurs, objets), un vocabulaire d'architectures acteur-apprenant, un modèle de files d'attente qui permet de dimensionner la boucle avant de la construire, et le dimensionnement d'un moteur d'inférence (cache KV, batching, goodput), celui qui produit les rollouts et sert aussi les utilisateurs.

Le fil rouge est une grandeur discrète, **l'obsolescence** : de combien de versions de la politique une trajectoire a-t-elle de retard quand l'apprenant l'utilise ? Elle relie des choix d'infrastructure (nombre d'acteurs, taille de file, fréquence de synchronisation) à la qualité de l'apprentissage.

::: key
[Règle de ce module]{.tag} Dans une boucle en ligne, ce qui n'est pas borné se paie en obsolescence. Une file, un tampon ou un nombre de trajectoires en vol sans limite finit par faire apprendre l'apprenant sur le passé. Dimensionnez d'abord le débit, puis bornez ce qui circule.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 30,5 h, dont 11,25 h de lecture, 13,5 h de labs et 5,75 h d'exercices |
| Niveau d'entrée | 3 : à l'aise avec l'entraînement distribué (module 9). Les *checkpoints* (points de reprise) du module 10 sont un plus : le chapitre 2 en rappelle l'essentiel |
| Prérequis | [Module 9 — Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline](../distributed-training/index.html) |
| Pour qui | Cœur : les charges de post-entraînement par renforcement sont l'une des raisons d'être d'une plateforme GPU. |
| Livrable | un modèle de débit validé par simulation, une boucle acteur-apprenant mesurée sur des acteurs Ray réels, une note de dimensionnement d'une boucle en ligne et le dimensionnement d'un moteur d'inférence (cache KV, goodput sous SLO) |
| Environnement | un portable CPU suffit (4 cœurs ; 8 Go recommandés, les labs ont été exécutés avec 16 Go) ; aucun GPU. Les GPU sont des **ressources logiques** simulées, et c'est écrit chaque fois |
| Projets liés | [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Expliquer le modèle de Ray (tâches, acteurs, objets, ressources logiques), prédire l'efficacité d'une tâche courte et dire quand Ray n'est pas l'outil (chapitres 1 et 2).
-   Prévoir ce qui arrive à un acteur, à une tâche et à leur état quand un processus meurt, et choisir `max_restarts` et `max_task_retries` en connaissance de cause (chapitre 2).
-   Situer Ray Train et Ray Data dans une chaîne d'entraînement et d'ingestion, et équilibrer les étapes d'un flux (chapitre 3).
-   Lire un pipeline de post-entraînement par renforcement comme une charge d'infrastructure : rôles, modèles en mémoire, part de la génération (chapitre 4).
-   Concevoir une boucle acteur-apprenant, mesurer son obsolescence et son débit, et choisir entre file, crédits et tampon de rejeu (chapitres 5 et 6).
-   Dimensionner le nombre d'acteurs, la taille d'une file et le coût par million de pas, avec des pools de types différents (chapitres 6 et 7).
-   Choisir et exploiter Ray sur Kubernetes ou Slurm, l'observer, et le comparer à Dask, Spark ou Kubeflow Trainer (chapitre 8).
-   Dimensionner le cache KV d'un moteur d'inférence à partir du `config.json` d'un modèle, expliquer batching continu, PagedAttention et cache de préfixes, et choisir les signaux d'autoscaling et les priorités d'une flotte partagée entre service, rollouts et entraînement (chapitre 9).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 3 — Systèmes d'entraînement distribué** (semaines 21-32) : faire tourner un entraînement multi-nœuds qui survit aux pannes.
-   **S'appuie sur** : [module 9 — Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline](../distributed-training/index.html).
-   **Projets qui s'en servent** : [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html).
-   **Compétences demandées dans les offres d'emploi et travaillées ici** : Python, Ray, Checkpoint, tolérance aux pannes, FinOps, coûts, Planification de capacité, Infrastructure de RL, Chaînes de données, Service d'inférence, Systèmes distribués, Slurm, Kubernetes, Prometheus, Grafana, Conception d'ordonnanceur, Expérience d'entraînement ML, Réseau (général), Profilage, bancs d'essai (voir [l'analyse du marché](../../market/index.html#couverture)).
<!-- /gen:place -->

### Plan de séances {#seances}

Onze séances, soit 30,5 h : sept de 3 h, trois de 2,5 h et une de 2 h. Chaque séance tient dans sa durée avec ses chapitres, sa part de lab et ses exercices, et un exercice n'apparaît qu'après la séance qui enseigne ce qu'il demande. Le niveau ne diminue jamais.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 3 h | 2 | ch. 1 Tâches, acteurs, ressources (1 h) ; questions de positionnement (0,25 h) | Lab 11.1 partie A, granularité (1,5 h) ; Ex. 1 (0,25 h) |
| 2 | 3 h | 2 | ch. 2 Ray en pratique : objets, placement, pannes, autoscaling (1,5 h) | Lab 11.1 partie B, pannes (1,25 h) ; Ex. 2 (0,25 h) |
| 3 | 2.5 h | 2 | ch. 3 Ray Train et Ray Data (1 h) | Lab 11.1 partie B, suite et démonstrations (1,25 h) ; Ex. 3 (0,25 h) |
| 4 | 2 h | 2 | ch. 4 Le renforcement vu de l'infrastructure (1,25 h) | Ex. 4, 5 (0,75 h) |
| 5 | 3 h | 3 | ch. 5 Architectures acteur-apprenant (1,5 h) | Lab 11.2 partie A, obsolescence contrôlée (1,5 h) |
| 6 | 3 h | 3 | ch. 6 Boucles en ligne, files et contre-pression (1,5 h) | Lab 11.3 partie 1, formules (1 h) ; Ex. 6 (0,5 h) |
| 7 | 3 h | 3 | Lab 11.3 partie 2 | Simulation à événements discrets et tests (2 h) ; Ex. 7, 8 (1 h) |
| 8 | 3 h | 3 | ch. 7 Hétérogénéité (0,75 h) | Lab 11.2 partie A, fin (0,5 h), puis partie B, acteurs Ray réels (1,75 h) |
| 9 | 3 h | 3 | ch. 8 Kubernetes, Slurm, observabilité, alternatives (0,75 h) | Lab 11.2 partie B, suite (2,25 h) |
| 10 | 2.5 h | 3 | ch. 9 Inférence : moteurs, cache KV, batching continu (1,25 h) | Lab 11.4, batching simulé (0,5 h) ; Ex. 13, 14 (0,75 h) |
| 11 | 2.5 h | 3 | Bilan de sortie (0,5 h) | Ex. 9, 10 (1 h) ; Ex. 11, 12 (1 h) |

<!-- gen:travailler -->
### Comment travailler ce module {#travailler}

Le parcours s'adresse à plusieurs profils d'entrée, décrits dans le [point de départ](../../profile/index.html). Le tableau donne la priorité conseillée pour ce module ; les questions de positionnement (section 0.1) la confirment ou la corrigent.

| Profil d'entrée | Priorité | Ce que cela veut dire ici |
|---|---|---|
| Ingénieur plateforme, SRE ou DevOps | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Administrateur ou ingénieur HPC | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Ingénieur ML ou chercheur | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Développeur logiciel ou systèmes | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Étudiant ou personne en reconversion | à fond | tous les chapitres, tous les labs et les exercices ★★★ |

**À ne pas survoler.** Les boucles acteur-apprenant et leur dimensionnement sont nouveaux pour presque tous les profils.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le bilan de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si elles vous semblent routinières, parcourez les exercices ★★★ et passez au module 12.

1.  **Tâche ou acteur.** Une fonction doit charger un modèle de 14 Go, puis noter 10 000 documents. L'écrivez-vous comme une tâche Ray ou comme un acteur Ray, et pourquoi ?

2.  **File qui grossit.** Dix acteurs produisent chacun 20 trajectoires par minute. L'apprenant en consomme 120 par minute, dans l'ordre d'arrivée. Que devient la file, et que disent les trajectoires que l'apprenant lit au bout de dix minutes ?

3.  **PPO et GRPO.** Un entraînement PPO manipule quatre modèles : la politique, un modèle de référence, un modèle de récompense et un critique. Lequel disparaît avec GRPO, et quel gain mémoire en attendez-vous pour des modèles de même taille ?

::: sol
**Réponses.**

1.  Un acteur. Une tâche n'a pas d'état : elle reconstruirait le modèle à chaque appel, soit 10 000 chargements. Un acteur le charge une fois dans son constructeur et sert ensuite les appels. Le lab 11.1 le mesure : 40 chargements en mode tâches contre 4 en mode acteurs. Voir le chapitre 1.

2.  Les acteurs produisent $10 \times 20 = 200$ trajectoires par minute pour 120 consommées : la file grossit de 80 par minute, soit 800 trajectoires après dix minutes. Lue dans l'ordre d'arrivée, la trajectoire suivante a attendu $800/120 \approx 6{,}7$ minutes : l'apprenant apprend sur du passé. Voir les chapitres 5 et 6.

3.  Le critique. GRPO estime la ligne de base à partir des récompenses d'un groupe de sorties et supprime ce modèle (Shao et al., 2024). Pour quatre modèles de même taille dont deux entraînés, retirer le critique libère son état d'entraînement, la part la plus lourde : à 16 octets par paramètre pour un modèle entraîné et 2 pour un modèle évalué, on passe de $16+16+2+2 = 36$ à $16+2+2 = 20$, soit 44 % de mémoire en moins (exemple 4.1). Voir le chapitre 4 et l'exercice 5.
:::

## 1. Pourquoi un framework distribué général : tâches, acteurs, ressources {#ch1}

Un ordonnanceur (*scheduler*) de cluster comme Slurm ou Kubernetes place des **jobs** : un ensemble fixe de processus, décrit à l'avance, qui démarre ensemble. Une boucle de renforcement ne ressemble pas à cela. Ce chapitre explique pourquoi un framework distribué général a sa place au-dessus de l'ordonnanceur, et ce qu'il coûte.

### 1.1. Ce qui n'est plus un gros job

Trois propriétés distinguent une boucle de renforcement d'un entraînement classique. Les rôles sont différents : un simulateur sur CPU, un moteur de génération sur GPU, un apprenant sur d'autres GPU. Le graphe de calcul est dynamique : on lance une simulation de plus quand une autre se termine, pas selon un plan écrit d'avance. Enfin, des états vivent longtemps : un modèle chargé, un environnement, un tampon.

Les auteurs de Ray (Moritz et al., 2018) partent de ce constat. Ils proposent une seule interface qui exprime le calcul parallèle de tâches et le calcul à base d'acteurs, sur un moteur d'exécution dynamique, et annoncent, dans leurs expériences, un passage à l'échelle au-delà de 1,8 million de tâches par seconde.

### 1.2. Trois objets : tâche, acteur, objet

Chaque nœud exécute un démon Ray, le *raylet*, qui héberge entre autres le moniteur de mémoire (section 2.3). Le modèle de Ray tient en trois objets, que le tableau compare. Une **tâche** est une fonction sans état exécutée à distance. Un **acteur** est une instance de classe qui vit dans son propre processus, garde un état, et exécute ses méthodes une à une. Un **objet** est une valeur immuable rangée dans un magasin partagé par nœud, désignée par une référence (*ObjectRef*).

| | Tâche | Acteur | Objet |
|---|---|---|---|
| État | aucun | oui, dans le processus | immuable |
| Appel | `f.remote(x)` | `a.m.remote(x)` | `ray.put(v)`, `ray.get(ref)` |
| Mise à jour fine | coûteuse (tout repasse par les objets) | peu coûteuse | impossible (on crée un nouvel objet) |
| Reprise après panne | simple : on rejoue la fonction | il faut restaurer l'état | reconstruit par rejeu si possible |
| Pour quoi faire | simulations courtes, prétraitement | modèle chargé, environnement, apprenant | poids, lots, trajectoires |

Cette comparaison reprend le tableau 2 de l'article de Ray, qui oppose le bon équilibrage de charge et la reprise peu coûteuse des tâches aux mises à jour fines efficaces des acteurs, au prix d'un coût de checkpoint.

<figure class="fig">
<svg viewBox="0 0 560 300" role="img" aria-labelledby="f1-t f1-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="f1-t">Tâches, acteurs et objets dans Ray</title>
<desc id="f1-d">Le pilote soumet des tâches sans état et des appels d'acteur. Sur chaque nœud, un raylet les exécute dans des processus de travail ; les valeurs passent par un magasin d'objets partagé.</desc>
<defs><marker id="a1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--accent)"/></marker></defs>
<rect x="12" y="110" width="120" height="70" rx="8" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="72" y="140" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">Pilote</text>
<text x="72" y="162" text-anchor="middle" font-size="14" fill="currentColor">(driver)</text>
<rect x="190" y="14" width="358" height="272" rx="10" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="6 5"/>
<text x="204" y="38" font-size="15" font-weight="700" fill="currentColor">Un nœud (raylet)</text>
<rect x="206" y="52" width="150" height="62" rx="8" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="281" y="78" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">Tâches</text>
<text x="281" y="99" text-anchor="middle" font-size="14" fill="currentColor">sans état</text>
<rect x="378" y="52" width="156" height="62" rx="8" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="456" y="78" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">Acteur</text>
<text x="456" y="99" text-anchor="middle" font-size="14" fill="currentColor">état + appels en file</text>
<rect x="206" y="170" width="328" height="56" rx="8" fill="var(--side-bg)" stroke="var(--accent)" stroke-width="3"/>
<text x="370" y="195" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">Magasin d'objets</text>
<text x="370" y="214" text-anchor="middle" font-size="14" fill="currentColor">valeurs immuables, mémoire partagée</text>
<text x="204" y="262" font-size="14" fill="currentColor">ressources logiques : CPU, GPU, mémoire, personnalisées</text>
<line x1="134" y1="132" x2="204" y2="86" stroke="var(--accent)" stroke-width="3" marker-end="url(#a1)"/>
<line x1="134" y1="160" x2="206" y2="196" stroke="var(--accent)" stroke-width="3" marker-end="url(#a1)"/>
<line x1="281" y1="116" x2="281" y2="168" stroke="currentColor" stroke-width="2" marker-end="url(#a1)"/>
<line x1="456" y1="116" x2="456" y2="168" stroke="currentColor" stroke-width="2" marker-end="url(#a1)"/>
</svg>
<figcaption>Les trois objets de Ray. Le pilote soumet des tâches et des appels d'acteur ; les valeurs échangées vivent dans le magasin d'objets du nœud.</figcaption>
</figure>

### 1.3. Des ressources logiques, pas des garanties

Ray raisonne en **ressources logiques**. La documentation précise que Ray ne fournit pas d'isolation CPU aux tâches ni aux acteurs. Un nœud déclare un nombre de CPU, de GPU et de mémoire, par défaut ceux qu'il détecte, et une tâche ou un acteur ne s'exécute que si ces quantités sont libres. Rien n'empêche une tâche déclarée à 1 CPU d'en consommer quatre. Ray fixe en revanche `CUDA_VISIBLE_DEVICES` pour isoler les GPU et `OMP_NUM_THREADS` selon `num_cpus`.

Conséquence pratique : une ressource logique est une **monnaie de comptage**, pas un cgroup. Vous pouvez donc déclarer des « GPU » sur une machine qui n'en a pas, pour tester un placement. C'est ce que font les labs de ce module, et ils le disent chaque fois.

Les valeurs par défaut réservent des surprises. D'après la documentation de Ray 2.59, une tâche utilise 1 CPU logique, et un acteur « 1 logical CPU for scheduling, and 0 logical CPU for running » ; dès que des ressources sont demandées explicitement, elles sont exigées au placement comme à l'exécution.

::: ex
[Exemple 1.1 — Ce que retient un acteur]{.tag} Voici la sortie réelle de `resources_demo.py` (lab 11.1, Ray 2.59.0, VM de test à 4 vCPU, nœud déclaré avec 8 CPU et 2 GPU logiques, 2026-10-25). Deux acteurs sont créés, puis on lit les CPU libres.

~~~text
2 actors, default options         -> free CPU = 8 of 8
2 actors, num_gpus=1 only         -> free CPU = 6 of 8
2 actors, num_gpus=1, num_cpus=0  -> free CPU = 8 of 8
~~~

Sans option, les acteurs ne retiennent aucun CPU. Avec `num_gpus=1` seul, chacun en retient un : 2 CPU de moins. Pour un apprenant qui n'a besoin que de son GPU, il faut écrire `num_cpus=0`. La documentation recommande de toujours fixer `num_cpus` pour les acteurs, justement pour éviter cette surprise.
:::

### 1.4. Le coût d'une tâche

Chaque appel à distance coûte un temps fixe $o$ : soumission, location d'un processus, retour du résultat. Pour une tâche utile de durée $d$ sur des processus en nombre suffisant, l'efficacité vaut

$$E(d) = \frac{d}{d + o}$$

et ne dépend ni du nombre de processus ni du total à calculer. Deux conséquences. Une tâche ne vaut le coup que si $d \gg o$. Et le remède aux tâches trop fines est de les **regrouper** : un lot de $k$ tâches de durée $d$ devient une tâche de durée $kd$.

::: ex
[Exemple 1.2 — Mesurer o, puis prédire]{.tag} Le lab 11.1 lance des tâches qui dorment $d$ secondes (une charge **simulée**, pour que la mesure ne dépende pas de la charge de la machine) sur 4 emplacements, avec 1,6 s de travail utile au total. Avec $d = 1$ ms, 1 600 tâches prennent 1,14 s : l'efficacité vaut $1{,}6/(4 \times 1{,}14) = 0{,}35$. On en tire $o = d\,(1/E - 1) \approx 1{,}85$ ms.

Le modèle prédit alors $E(10\ \text{ms}) = 0{,}84$ et $E(100\ \text{ms}) = 0{,}98$. On mesure 0,80 et 0,97 (VM de test, 2026-10-25). Regrouper les 1 600 tâches de 1 ms par paquets de 100 donne 16 tâches de 100 ms et une efficacité mesurée de 0,87 : le modèle prévoit 0,98, l'écart vient du démarrage des processus, qui pèse davantage sur un total de 0,4 s. Pour atteindre 90 %, il faut $d \ge 9\,o \approx 17$ ms.

Le coût $o$ n'est pas une constante : cinq exécutions ont donné de 0,32 à 0,41 pour $E(1\ \text{ms})$ (0,41 avec deux CPU occupés par un autre processus), soit $o$ entre 1,4 et 2,1 ms. Mesurez-le sur votre machine, plusieurs fois.
:::

Le même lab mesure la médiane d'un aller-retour : 2,06 ms pour une tâche vide et 1,07 ms pour un appel d'acteur vide. Un appel d'acteur coûte donc environ deux fois moins qu'un lancement de tâche sur cette machine. L'explication vraisemblable est qu'il n'y a ni location de processus ni reconstruction d'état, mais le lab ne l'isole pas.

### 1.5. Quand Ray, quand pas

Ray est un second ordonnanceur, posé sur le premier. Slurm ou Kubernetes vous donnent des nœuds ; Ray répartit des tâches et des acteurs sur ces nœuds. Ce niveau supplémentaire doit gagner sa place.

::: key
[Quand choisir Ray]{.tag} Choisissez Ray quand la charge a des **rôles hétérogènes**, un **graphe dynamique** ou des **états de longue durée** qu'il faut placer sur des ressources différentes (simulateurs, générateurs, apprenant). Restez sur un job classique quand tous les processus font la même chose, démarrent ensemble et ne s'échangent que des collectives : c'est un entraînement SPMD, et `torchrun` sous Slurm ou Kubernetes suffit.
:::

Un test rapide : dessinez les processus de votre application. S'il y a plus d'un type de processus, ou si leur nombre change pendant l'exécution, Ray devient candidat. Sinon, il ajoute un composant à exploiter sans rien apporter.

::: recap
Points clés — chapitre 1

-   Tâche : fonction sans état. Acteur : instance avec état dans son propre processus. Objet : valeur immuable dans un magasin partagé.
-   Les ressources de Ray sont logiques : pas d'isolation CPU, isolation GPU par `CUDA_VISIBLE_DEVICES`.
-   Fixez `num_cpus` explicitement pour les acteurs : sur Ray 2.59, `num_gpus=1` seul retient aussi 1 CPU.
-   Efficacité d'une tâche : $E = d/(d+o)$ ; sur la VM de test, $o$ vaut de 1,4 à 2,1 ms selon l'exécution. Regroupez les tâches fines.
-   Ray vaut le coup pour des rôles hétérogènes, un graphe dynamique ou des états longs ; pas pour un SPMD.
:::

## 2. Ray en pratique : objets, placement, mémoire, pannes, autoscaling {#ch2}

Le chapitre 1 a posé le modèle. Celui-ci regarde ce qui se passe quand l'application devient réelle : des gros objets à partager, des ressources à réserver ensemble, de la mémoire qui manque, des processus qui meurent et des nœuds qui apparaissent. Chaque section se termine par une règle d'exploitation.

### 2.1. Objets partagés et mémoire

`ray.put(v)` range une valeur dans le magasin d'objets du nœud et renvoie une référence. Les tâches et les acteurs qui reçoivent la référence en argument la résolvent sans copie supplémentaire sur le même nœud : un tableau NumPy est lu en place dans la mémoire partagée. Pour des poids de modèle, la bonne pratique est de faire **un** `ray.put` par version, puis de passer la référence à tous les acteurs, et non de repasser le tableau lui-même à chaque appel.

Les objets sont comptés par référence : un objet reste épinglé tant qu'une référence existe quelque part dans le cluster. Quand le magasin est plein, Ray déverse (*spill*) les objets sur le disque local, par défaut dans le répertoire temporaire de la session (`/tmp/ray/...`) ; le paramètre `object_spilling_directory` le change. Le magasin occupe par défaut 30 % de la mémoire disponible au démarrage.

::: ex
[Exemple 2.1 — Le magasin d'objets de la VM de test]{.tag} Sur la VM à 16 Go, `ray.cluster_resources()` renvoie `memory: 11402949018` et `object_store_memory: 4886978150` (octets, Ray 2.59.0, 2026-10-25). Le magasin représente la fraction suivante de la somme des deux valeurs :

$$\frac{4\,886\,978\,150}{11\,402\,949\,018 + 4\,886\,978\,150} = 0{,}300$$

C'est bien la règle des 30 %, appliquée à la mémoire disponible au démarrage.

Conséquence pour une boucle de renforcement : si les poids pèsent 14 Go et que vous en gardez trois versions vivantes, le magasin d'un nœud de 256 Go (donc environ 77 Go par défaut) en porte déjà 42 Go. Surveillez `object_store_memory` dans les métriques (chapitre 8) avant d'augmenter le nombre d'acteurs.
:::

### 2.2. Placement groups : réserver ensemble

Un **placement group** réserve atomiquement un ensemble de *bundles* (des lots de ressources) sur un ou plusieurs nœuds. La documentation de Ray y voit le *gang scheduling*, c'est-à-dire le tout ou rien : si un bundle ne tient nulle part, aucune ressource n'est réservée. Ray Train s'en sert pour son groupe de travailleurs.

Quatre stratégies existent. `PACK` et `SPREAD` sont des préférences ; `STRICT_PACK` et `STRICT_SPREAD` sont des obligations. Un bundle doit tenir sur un seul nœud : une demande de 9 CPU ne passe pas sur des nœuds de 8 et de 1.

::: ex
[Exemple 2.2 — Un groupe impossible ne réserve rien]{.tag} Sur le nœud unique du lab (8 CPU logiques), `resources_demo.py` crée un groupe `PACK` de deux bundles d'un CPU : il est prêt. Il crée ensuite un groupe `STRICT_SPREAD` de deux bundles, qui exige deux nœuds distincts. Il reste en attente, et les CPU libres sont 6 sur 8 : seuls les 2 CPU du groupe `PACK` sont réservés.

~~~text
PACK group ready: True ; STRICT_SPREAD group ready on one node: False ; free CPU = 6 of 8
~~~

C'est exactement la propriété d'atomicité de la documentation, vérifiée sur un vrai Ray 2.59.0. Sur un cluster réel à autoscaler, un groupe en attente déclenche l'ajout de nœuds, car l'autoscaler connaît les placement groups.
:::

Règle d'usage : `PACK` pour un apprenant dont les travailleurs communiquent beaucoup (même nœud, donc NVLink), `SPREAD` pour des réplicas dont on veut qu'un seul nœud perdu ne les emporte pas tous.

### 2.3. La mémoire qui manque

Quand la mémoire d'un nœud est épuisée, l'OOM killer du noyau choisit une victime selon son score (`oom_score`, que `oom_score_adj` pondère, [module 1](../linux-systems/index.html#cache-de-pages-et-mise-à-mort-par-manque-de-mémoire)), sans rien savoir de vos tâches. Ray préfère décider lui-même, avant lui : un moniteur de mémoire, dans le *raylet* de chaque nœud, compare l'utilisation totale (tas des travailleurs, magasin d'objets, raylet) à un seuil. Par défaut, il vérifie toutes les 250 ms (`RAY_memory_monitor_refresh_ms`) et agit au-delà de 95 % (`RAY_memory_usage_threshold`). Il tue alors un travailleur à la fois, en préférant les tâches qui peuvent être rejouées et les plus récentes.

::: war
[Une tâche tuée par le moniteur ignore max_retries]{.tag} D'après la [documentation de Ray](https://docs.ray.io/en/latest/ray-core/scheduling/ray-oom-prevention.html), une tâche tuée par le moniteur de mémoire est rejouée avec un délai exponentiel plafonné à 60 s, et sans respecter `max_retries` (rejeu infini), sauf si `max_retries=0`. Un acteur tué respecte en revanche `max_restarts`, qui vaut 0 par défaut. Le moniteur garantit qu'au moins une tâche par appelant et par nœud peut s'exécuter, faute de quoi la charge échoue avec une erreur de mémoire. Une tâche trop gourmande peut donc rebondir longtemps avant d'échouer ; déclarez sa mémoire (`memory=`) pour que l'ordonnanceur la place correctement.
:::

### 2.4. Pannes : ce que Ray rejoue, et ce qu'il ne sait pas

Ray règle la reprise à quatre endroits. Pour une **tâche**, le défaut est `max_retries=3`, et les exceptions applicatives ne sont pas rejouées (`retry_exceptions=False`). Pour un **acteur**, `max_restarts=0` : un acteur qui meurt reste mort, et ses appels suivants lèvent `RayActorError`. Pour les **appels** d'acteur, `max_task_retries=0` donne une sémantique « au plus une fois » ; `-1` ou une valeur positive donne « au moins une fois », et la documentation prévient qu'un appel rejoué peut s'exécuter deux fois.

Enfin, un **objet** perdu est reconstruit en rejouant la tâche qui l'a produit, tant que son propriétaire vit encore ; ceux que produisent des appels d'acteur ne le sont pas par défaut.

| Réglage | Défaut | Effet à la panne |
|---|---|---|
| `max_retries` (tâche) | 3 | la tâche est rejouée ; `-1` sans limite, `0` jamais |
| `max_restarts` (acteur) | 0 | 0 : l'acteur reste mort ; positif ou `-1` : il redémarre en rejouant son constructeur, sans l'état accumulé depuis |
| `max_task_retries` (acteur) | 0 | 0 : au plus une fois ; `-1` : au moins une fois |
| reconstruction d'un objet | active pour les tâches | par rejeu de la tâche qui l'a produit, si son propriétaire vit encore ; pas pour les résultats d'appels d'acteur par défaut |

::: ex
[Exemple 2.3 — Un acteur qui meurt trois fois sur le même appel]{.tag} Le lab 11.1 tue de vrais processus avec `os._exit(1)`. Voici sa sortie sur la VM de test (Ray 2.59.0, 2026-10-25), pour un compteur qui vaut 3 avant la panne.

~~~text
max_restarts=0: next call -> RayActorError
max_restarts=1, no checkpoint: counter was 3, next inc -> 1
max_restarts=1, checkpoint   : counter was 3, next inc -> 4
max_task_retries= 0: result=RayActorError  side effects of call 7: ['7']
max_task_retries=-1: result=7              side effects of call 7: ['7', '7']
~~~

Trois leçons. Sans `max_restarts`, l'acteur est perdu. Avec `max_restarts=1`, il revient mais **sans son état** (le compteur repart de 1) tant qu'on ne l'a pas écrit dans un checkpoint (un état sauvegardé hors du processus, d'où l'on peut repartir) : c'est le sujet du [module 10](../fault-tolerance/index.html). Avec `max_task_retries=-1`, l'appel interrompu est rejoué et son effet de bord (une ligne écrite dans un journal) apparaît **deux fois**.
:::

La conséquence est une règle de conception : tout appel d'acteur rejouable doit être **idempotent**, c'est-à-dire pouvoir s'exécuter deux fois sans changer le résultat. L'écriture d'un résultat sous une clé déterministe (l'identifiant de la trajectoire, pas un compteur) le garantit.

::: war
[Le GCS n'est pas tolérant aux pannes par défaut]{.tag} La [documentation de Ray](https://docs.ray.io/en/latest/ray-core/fault_tolerance/gcs.html) l'écrit : le GCS (*Global Control Service*, qui gère les métadonnées du cluster) garde tout en mémoire, et « If it fails, the entire Ray cluster fails ». Pour le rendre tolérant, il faut le sauvegarder dans un Redis hautement disponible, l'option officiellement supportée (RocksDB embarqué est annoncé en alpha). Sans cela, la perte du GCS emporte l'application.
:::

### 2.5. Autoscaling

L'autoscaler ajoute et retire des nœuds. Il raisonne sur les **demandes de ressources logiques** (tâches, acteurs, placement groups en attente), jamais sur l'utilisation physique : un GPU à 5 % d'utilisation mais réservé reste un GPU occupé. Il met la demande en file, ajuste le nombre de nœuds et retire les nœuds inactifs (sans tâche, acteur ni objet référencé) après un délai. Sur KubeRay, ce délai, `idleTimeoutSeconds`, vaut 60 s par défaut.

Deux pièges en découlent. Une demande dont la forme n'existe dans aucun type de nœud (par exemple 2 GPU sur des nœuds à 1 GPU) reste en attente, car l'autoscaler n'a aucun nœud à ajouter pour elle ; il faut changer la demande. Et un nœud qui porte un objet encore référencé ne descend pas à zéro, même sans calcul.

::: recap
Points clés — chapitre 2

-   Un `ray.put` par version de poids ; le magasin occupe 30 % de la mémoire disponible par défaut.
-   Un placement group est atomique : tout est réservé, ou rien.
-   Le moniteur de mémoire ne respecte pas `max_retries` pour une tâche qu'il tue (rejeu infini), sauf `max_retries=0`.
-   Défauts : `max_retries=3` pour une tâche, `max_restarts=0` et `max_task_retries=0` pour un acteur.
-   Un acteur redémarré perd son état ; un appel rejoué peut s'exécuter deux fois. Écrivez des appels idempotents et des checkpoints.
-   L'autoscaler suit les demandes logiques ; une forme de demande introuvable reste en attente.
:::

## 3. Ray Train et Ray Data : entraînement, ingestion, flux {#ch3}

Ray n'est pas qu'un modèle d'acteurs : il vient avec des bibliothèques qui encapsulent deux besoins fréquents autour de la boucle, entraîner à plusieurs travailleurs et nourrir ces travailleurs en données. Les connaître évite de les réécrire, et permet de savoir quand s'en passer.

### 3.1. Ray Train : un groupe de travailleurs

Ray Train lance un **groupe de travailleurs**, des acteurs Ray placés par un placement group, qui exécutent chacun la même fonction d'entraînement. Le `ScalingConfig` fixe le nombre de travailleurs, la présence de GPU, les ressources par travailleur et la stratégie de placement (`PACK` par défaut). `FailureConfig(max_failures=n)` autorise `n` reprises : chaque récupération après une panne de processus ou de nœud en consomme une, et les travailleurs relancés reprennent au dernier checkpoint.

Pour un ingénieur d'infrastructure, c'est un second chemin vers l'entraînement distribué, à côté de `torchrun` sous Slurm (module 9). Il est utile quand l'entraînement est une étape d'un pipeline Ray plus large. Il n'apporte pas de collectives plus rapides : dans la démonstration ci-dessous, les gradients passent par le `DistributedDataParallel` de PyTorch.

::: ex
[Exemple 3.1 — Une panne de travailleur dans Ray Train]{.tag} `train_demo.py` entraîne une couche linéaire sur 2 travailleurs CPU (backend `gloo`, `use_gpu=False` : aucun GPU, même logique), tue le rang 1 une fois à l'époque 3, avec `max_failures=2`. Sortie sur la VM de test (Ray 2.59.0, 2026-10-25) :

~~~text
final metrics: {'epoch': 5, 'start': 2} error: None
~~~

L'entraînement va au bout (époque 5), sans erreur. `start: 2` signifie que la boucle relancée a repris à l'époque 2, donc depuis le checkpoint de l'époque 1 : celui de l'époque 2 n'était pas encore écrit quand le rang 1 est mort. La valeur exacte dépend de l'instant de la panne ; le test n'exige que la reprise (`start ≥ 1`). Un checkpoint rare coûte du travail rejoué.
:::

### 3.2. Ray Data : un flux de blocs

Ray Data représente un jeu de données comme une suite de **blocs** (tables Arrow ou DataFrames) rangés dans le magasin d'objets. La documentation indique qu'elle cherche à borner leur taille entre 1 Mio et 128 Mio : les petits blocs favorisent la latence et le flux, les gros réduisent le coût d'ordonnancement.

L'exécution se fait en **flux** (*streaming*) : chaque opérateur produit et consomme des blocs sans attendre la fin du précédent, ce qui permet de traiter des jeux plus grands que la mémoire du cluster. Un opérateur n'est ordonnancé que s'il a des entrées, des ressources et s'il n'est pas sous **contre-pression** (*backpressure*) : un budget de ressources empêche un étage rapide d'inonder un étage lent.

`map_batches` applique une transformation. Avec une fonction, Ray Data lance des tâches ; avec une **classe**, il lance un pool d'acteurs, ce qui permet de charger un modèle une fois. `concurrency` fixe la taille du pool, `num_gpus` ou `resources` les ressources par travailleur.

~~~python
ds = (ray.data.range(rows, override_num_blocks=blocks)
      .map_batches(preprocess, batch_format="numpy")
      .map_batches(Scorer, batch_format="numpy", batch_size=100, concurrency=2,
                   num_cpus=0, resources={"eval_gpu": 1}))
~~~

Cet extrait vient de `data_demo.py` (lab 11.1). L'étape `Scorer` est un pool de deux acteurs, chacun exigeant une unité d'une ressource logique `eval_gpu` : le pool ne peut donc pas dépasser deux acteurs, même si des CPU restent libres.

::: ex
[Exemple 3.2 — Équilibrer deux étages d'un flux]{.tag} Dans un flux à deux étages, le débit de chaque étage vaut $n_i / t_i$ (travailleurs divisés par le temps par lot). Le flux est équilibré quand $n_1/t_1 = n_2/t_2$. Si un étage CPU met $t_1 = 40$ ms par lot et alimente 4 étages GPU qui mettent chacun $t_2 = 80$ ms, il faut $n_1 = n_2\,t_1/t_2 = 4 \times 40/80 = 2$ travailleurs CPU. Avec un seul, les GPU attendent la moitié du temps ; avec 4, deux CPU restent inactifs.

Dans `data_demo.py` (étage GPU **simulé** par un `sleep` de 20 ms), le premier lot sort après 2,30 s et le flux entier après 3,33 s (deux autres exécutions : 2,65 s et 3,64 s, puis 2,20 s et 4,35 s) : on reçoit des résultats avant la fin du traitement, signe d'un vrai flux. La sortie de journal de Ray Data y affiche `backpressured:tasks(ResourceBudget)`, la contre-pression en action.
:::

::: recap
Points clés — chapitre 3

-   Ray Train = groupe de travailleurs (acteurs) en placement group ; `FailureConfig` autorise les reprises, au dernier checkpoint.
-   Ray Train orchestre l'entraînement ; les gradients restent échangés par `torch.distributed`.
-   Ray Data traite des blocs de 1 à 128 Mio en flux, avec contre-pression par budget de ressources.
-   `map_batches` avec une fonction lance des tâches, avec une classe un pool d'acteurs.
-   Équilibre d'un flux : $n_1/t_1 = n_2/t_2$ ; sinon l'étage le plus lent borne le débit.
:::

## 4. Le renforcement vu de l'infrastructure : PPO, GRPO et post-entraînement {#ch4}

Ce chapitre n'est pas un cours de renforcement. Il donne le minimum pour lire une charge de post-entraînement comme un ingénieur d'infrastructure : quels rôles, quels modèles en mémoire, quelles données entre quels étages, et pourquoi la fraîcheur des données compte.

### 4.1. La boucle observation-action-récompense

Un agent observe un état, choisit une action avec sa **politique** $\pi_\theta$, reçoit une récompense, et recommence. Une **trajectoire** est la suite des états, actions et récompenses d'un épisode. Le but est de maximiser le retour espéré. Pour un modèle de langage, l'état est le prompt suivi des jetons déjà produits, l'action est le jeton suivant, la trajectoire est une réponse complète et la récompense est le plus souvent un score unique donné à la fin, par un modèle de récompense ou par un vérificateur à règles.

La méthode du gradient de politique pousse la probabilité d'une action vers le haut quand son **avantage** $\hat A_t$ est positif (mieux que prévu) et vers le bas sinon. L'avantage est un retour moins une ligne de base : toute la différence entre algorithmes tient à la façon de la calculer.

### 4.2. PPO en une page

PPO (*proximal policy optimization*, Schulman et al., 2017) alterne deux phases. Chaque itération, « each of N (parallel) actors collect T timesteps of data » ; l'apprenant optimise ensuite un objectif de substitution sur ces $NT$ pas, pendant quelques époques de descente par mini-lots (notées $K$ dans l'article ; ici, $K$ désigne les crédits du chapitre 6). Le rapport $r_t(\theta) = \pi_\theta / \pi_{\text{old}}$ compare la politique courante à celle qui a produit les données, et l'objectif écrête ce rapport hors de l'intervalle $[1-\varepsilon,\ 1+\varepsilon]$, où $\varepsilon$ est un petit seuil fixé :

$$L^{\text{CLIP}}(\theta) = \hat{\mathbb{E}}_t\bigl[\min\bigl(r_t\,\hat A_t,\ \text{clip}(r_t,\, 1-\varepsilon,\, 1+\varepsilon)\,\hat A_t\bigr)\bigr]$$

Lecture d'infrastructure : le rapport $r_t$ n'a de sens que si les données viennent d'une politique proche de la courante. PPO tolère donc une obsolescence **bornée** (celle de ces quelques époques) mais pas une obsolescence qui grandit. Et l'avantage vient en général d'un **critique** $V_\psi$ appris, un modèle de la taille de la politique.

### 4.3. GRPO : supprimer le critique

GRPO (*group relative policy optimization*, Shao et al., 2024) enlève ce modèle. Pour chaque question, il échantillonne un groupe de $G$ sorties, les note, puis normalise chaque récompense par la moyenne et l'écart-type du groupe :

$$\hat A_{i} = \frac{r_i - \text{mean}(\mathbf r)}{\text{std}(\mathbf r)}$$

Les auteurs écrivent que GRPO « foregoes the critic model, instead estimating the baseline from group scores, significantly reducing training resources ». Pour l'infrastructure, deux conséquences : un modèle de moins à placer et à entraîner, et $G$ générations par prompt au lieu d'une, donc une charge de génération multipliée d'autant. Si toutes les récompenses d'un groupe sont égales, l'avantage est nul : la génération correspondante n'apporte aucun gradient.

### 4.4. Le pipeline de post-entraînement

Un pas de post-entraînement enchaîne quatre étages, que la littérature d'outils décrit de façon cohérente.

1.  **Génération** (*rollout* : exécuter la politique jusqu'à une trajectoire complète) : la politique courante produit des réponses, sur un moteur d'inférence. C'est l'étage où les réponses longues dominent : avec des chaînes de raisonnement (*chain of thought*, CoT), OpenRLHF note que « CoT generation can dominate training time ».
2.  **Évaluation** : un modèle de récompense ou un vérificateur note les réponses ; un modèle de référence fournit les log-probabilités pour la pénalité de divergence.
3.  **Entraînement** : l'apprenant met à jour les poids.
4.  **Synchronisation** : les nouveaux poids retournent au moteur de génération.

Deux architectures publiques illustrent les choix. OpenRLHF, bâti sur Ray, vLLM, DeepSpeed et Hugging Face Transformers, attribue des lots de GPU à deux rôles, des moteurs de génération (*rollout engines*) et des moteurs ZeRO, qui calculent les log-probabilités et entraînent, et orchestre les flux avec l'ordonnancement de Ray. HybridFlow combine un contrôleur unique, qui coordonne les nœuds, et des contrôleurs multiples pour le calcul à l'intérieur d'un nœud ; il propose aussi un moteur qui redécoupe les poids de l'acteur entre l'entraînement et la génération (Sheng et al., 2024).

::: note
[Deux layouts, un coût de resharding]{.tag} Entraînement et génération n'ont pas le même parallélisme optimal. Les faire partager les mêmes GPU économise du matériel mais impose de **redécouper les poids** à chaque changement de phase ; les séparer sur deux pools supprime ce coût mais demande un transfert de poids et laisse chaque pool inactif une partie du temps. Le chapitre 5 chiffre le second cas.
:::

::: ex
[Exemple 4.1 — La mémoire de quatre modèles, puis de trois]{.tag} Prenons quatre modèles de 7 milliards de paramètres. Un modèle entraîné occupe 16 octets par paramètre (poids et gradients en BF16 à 2 octets chacun, plus 12 octets d'états d'optimiseur en FP32 : une copie des poids et les deux moments d'Adam, règle du module 9) ; un modèle seulement évalué en occupe 2. Pour PPO, la politique et le critique sont entraînés, la référence et le modèle de récompense évalués :

$$7 \cdot 10^{9} \times (16 + 16 + 2 + 2) = 252\ \text{Go}$$

Avec GRPO sans critique, le total passe à $7 \cdot 10^{9} \times (16 + 2 + 2) = 140$ Go : 112 Go libérés, soit 44 %. Si la récompense vient d'un vérificateur à règles et non d'un modèle, le total tombe à 126 Go. Ces chiffres sont l'**agrégat** sur tous les GPU, hors activations et hors cache KV (chapitre 9), et ils supposent que l'état est réparti entre les GPU (ZeRO) : un ordre de grandeur de placement, pas un plan.
:::

::: ex
[Exemple 4.2 — Avantages d'un groupe, et part de la génération]{.tag} Un groupe de $G = 8$ sorties reçoit les récompenses 1, 0, 0, 1, 1, 0, 0, 0. La moyenne vaut 0,375 et l'écart-type (population) 0,484. Les sorties réussies reçoivent l'avantage $+1{,}29$, les échouées $-0{,}77$. Si les huit récompenses valent 0, l'écart-type est nul : il n'y a pas d'avantage, et huit générations ont été payées pour rien.

Si la génération occupe 70 % d'une itération, l'évaluation 5 % et l'entraînement 25 % (hypothèse d'exemple), doubler le débit de génération ramène l'itération à $0{,}35 + 0{,}05 + 0{,}25 = 0{,}65$ de sa durée : un gain de $1/0{,}65 = 1{,}54$. Même une génération instantanée plafonnerait à $1/0{,}30 = 3{,}3$ : c'est la loi d'Amdahl ([module 2, §5.1](../perf-models/index.html#la-loi-damdahl)). Mesurez la part de chaque étage avant d'optimiser l'un d'eux.
:::

::: recap
Points clés — chapitre 4

-   Une trajectoire est une réponse complète ; l'avantage est un retour moins une ligne de base.
-   PPO : $N$ acteurs, $T$ pas, quelques époques par itération ; l'objectif borné suppose des données proches de la politique courante ; un critique de la taille de la politique.
-   GRPO supprime le critique et normalise par groupe ; il multiplie la génération par $G$.
-   Quatre étages : génération, évaluation, entraînement, synchronisation. La génération longue peut dominer.
-   Mesurez la part de chaque étage : la loi d'Amdahl borne le gain d'une accélération locale.
:::

## 5. Architectures acteur-apprenant : rollouts, poids, obsolescence, rejeu {#ch5}

Une architecture acteur-apprenant sépare ceux qui produisent des données (les acteurs) de celui qui apprend. Cette séparation donne du débit et pose un problème : les données arrivent avec une politique qui n'est plus tout à fait la bonne.

### 5.1. Synchrone ou asynchrone

Dans le schéma synchrone, tous les acteurs produisent avec les mêmes poids, une barrière attend le plus lent, l'apprenant met à jour, puis on rediffuse. La fraîcheur est parfaite et le coût est la barrière : un seul rollout lent bloque tous les GPU. OpenRLHF le dit pour les chaînes de raisonnement : dans un cadre synchrone, « the slowest CoT generation can bottleneck the whole pipeline ».

IMPALA (Espeholt et al., 2018) découple les deux. Les acteurs envoient des **trajectoires** (pas des gradients) à l'apprenant par une file ; l'apprenant, sur GPU, met à jour sur des lots de trajectoires venues de nombreux acteurs ; au début de chaque trajectoire, un acteur recopie la dernière politique de l'apprenant. Les auteurs rapportent 250 000 images par seconde, soit plus de 30 fois un A3C sur une seule machine.

<figure class="fig">
<svg viewBox="0 0 560 300" role="img" aria-labelledby="f2-t f2-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="f2-t">Boucle acteurs-apprenant avec file, version et poids</title>
<desc id="f2-d">Des acteurs envoient des trajectoires étiquetées de la version de leurs poids vers une file ou un tampon de rejeu, que l'apprenant consomme. L'apprenant publie les nouveaux poids vers les acteurs.</desc>
<defs><marker id="a2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--accent)"/></marker></defs>
<rect x="12" y="30" width="130" height="44" rx="8" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="77" y="58" text-anchor="middle" font-size="15" fill="currentColor">Acteur 1</text>
<rect x="12" y="92" width="130" height="44" rx="8" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="77" y="120" text-anchor="middle" font-size="15" fill="currentColor">Acteur 2</text>
<rect x="12" y="154" width="130" height="44" rx="8" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="77" y="182" text-anchor="middle" font-size="15" fill="currentColor">Acteur N</text>
<rect x="212" y="62" width="130" height="110" rx="8" fill="var(--side-bg)" stroke="var(--accent)" stroke-width="3"/>
<text x="277" y="94" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">File ou</text>
<text x="277" y="114" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">tampon de rejeu</text>
<text x="277" y="150" text-anchor="middle" font-size="14" fill="currentColor">trajectoire + version</text>
<rect x="412" y="62" width="136" height="110" rx="8" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="480" y="104" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">Apprenant</text>
<text x="480" y="128" text-anchor="middle" font-size="14" fill="currentColor">version v → v+1</text>
<line x1="144" y1="52" x2="210" y2="90" stroke="var(--accent)" stroke-width="3" marker-end="url(#a2)"/>
<line x1="144" y1="114" x2="210" y2="117" stroke="var(--accent)" stroke-width="3" marker-end="url(#a2)"/>
<line x1="144" y1="176" x2="210" y2="146" stroke="var(--accent)" stroke-width="3" marker-end="url(#a2)"/>
<line x1="344" y1="117" x2="410" y2="117" stroke="var(--accent)" stroke-width="3" marker-end="url(#a2)"/>
<path d="M480 174 L480 252 L77 252 L77 202" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="6 5" marker-end="url(#a2)"/>
<text x="278" y="244" text-anchor="middle" font-size="14" fill="currentColor">poids de la version v+1 (un ray.put)</text>
<text x="278" y="282" text-anchor="middle" font-size="14" fill="currentColor">obsolescence = version de l'apprenant − version de la trajectoire</text>
</svg>
<figcaption>Boucle acteurs-apprenant. Chaque trajectoire porte la version des poids qui l'ont produite ; l'obsolescence se lit à la consommation.</figcaption>
</figure>

### 5.2. L'obsolescence

L'**obsolescence** (*policy lag*) d'une trajectoire est le nombre de mises à jour effectuées entre le moment où l'acteur a lu ses poids et le moment où l'apprenant s'en sert. Elle ne se déduit pas de l'architecture : elle se mesure, version par version, en étiquetant chaque trajectoire. Les auteurs d'IMPALA décrivent le même phénomène : la politique de l'apprenant peut avoir plusieurs mises à jour d'avance sur celle des acteurs, d'où un « policy-lag » entre eux.

Pour corriger l'écart, IMPALA introduit V-trace, qui pondère chaque pas par un rapport d'importance tronqué :

$$\rho_t = \min\Bigl(\bar\rho,\ \frac{\pi(a_t \mid x_t)}{\mu(a_t \mid x_t)}\Bigr)$$

où $\pi$ est la politique de l'apprenant, $\mu$ celle de l'acteur au moment de la génération et $\bar\rho$ un seuil de troncature (1 dans le lab 11.2). L'acteur doit donc **enregistrer $\mu(a\mid x)$** avec chaque pas : une exigence de format de données, qui concerne l'infrastructure.

### 5.3. Tampon de rejeu

Ape-X (Horgan et al., 2018) range les expériences de tous les acteurs dans une mémoire de rejeu partagée ; l'apprenant y tire des échantillons, souvent selon une priorité. Un tampon FIFO de capacité $c$ trajectoires, alimenté de $f$ trajectoires fraîches par mise à jour et échantillonné uniformément, contient des données d'âge moyen

$$\bar a \approx \frac{c/2}{f} \quad\text{mises à jour,}\qquad f = \frac{b}{R}$$

où $b$ est le nombre de trajectoires par mise à jour et $R$ le **taux de rejeu**, le nombre moyen d'utilisations de chaque trajectoire. Réutiliser les données ($R > 1$) économise de la génération, mais vieillit l'échantillon proportionnellement.

### 5.4. Synchroniser les poids

Publier une version coûte au moins $\alpha + n/B$ (module 2). Pour des poids de 14 Go (7 milliards de paramètres en BF16) sur un lien de 25 Go/s, un transfert prend 0,56 s. Le coût de la diffusion vers $r$ nœuds dépend de la topologie : en étoile, la source envoie $r$ fois (modèle $\alpha + r\,n/B$) ; en arbre binomial (chaque nœud qui a reçu les poids les renvoie à un autre à chaque tour, comme le doublement récursif du [module 3](../parallel-programming/index.html#ch4)), $\lceil \log_2(r+1) \rceil$ tours de $\alpha + n/B$.

::: ex
[Exemple 5.1 — Diffuser 14 Go à 8 nœuds]{.tag} Avec $\alpha = 1$ ms, $n = 14$ Go et $B = 25$ Go/s (hypothèses d'exemple), `model.broadcast_time` (lab 11.3) donne 4,48 s en étoile et 2,24 s en arbre pour 8 nœuds : quatre tours de 0,56 s. Si l'apprenant fait une mise à jour par minute, l'étoile occupe 7,5 % du temps de la source, l'arbre 3,7 %. Ce calcul ne dit rien de l'algorithme réel de Ray pour les gros objets : mesurez-le sur votre réseau.
:::

Une règle découle de la structure de la boucle : un acteur lit ses poids **au début** d'un rollout. Si un rollout dure 120 s, synchroniser toutes les 2 s est inutile : la version lue ne change pas pendant la génération. La période de synchronisation utile est la durée d'un rollout, pas plus petite.

::: ex
[Exemple 5.2 — Ce que coûte l'obsolescence dans un jouet]{.tag} Le lab 11.2, partie A, entraîne un apprenant à gradient de politique sur un couloir de 16 cases, avec une obsolescence **imposée** de 0, 32 ou 128 mises à jour (8 graines, 400 mises à jour, 4 trajectoires par mise à jour). « Naïf » utilise les données telles quelles, « IS tronqué » applique le poids $\rho_t$ avec $\bar\rho = 1$. Sortie reproductible à chaque exécution (VM de test, 2026-10-25) :

~~~text
 lag  update rule  mean final  worst run  runs < 0.75
   0        naive       0.811      0.810         0/8
   0   clipped IS       0.811      0.810         0/8
  32        naive       0.705      0.490         6/8
  32   clipped IS       0.798      0.692         1/8
 128        naive       0.602     -0.232         7/8
 128   clipped IS       0.802      0.697         1/8
~~~

La colonne « runs < 0.75 » compte les graines dont le retour final reste sous 0,75. Le retour espéré optimal vaut environ 0,82 et une politique aléatoire −0,49. Sans obsolescence, les deux règles sont identiques (le rapport vaut 1). Avec 32 ou 128 mises à jour de retard, la règle naïve plafonne ou s'effondre, la règle tronquée tient. Attention : c'est un résultat **de ce jouet, avec ces réglages**. Il montre que l'obsolescence se mesure et se corrige ; il ne dit rien du réglage d'un entraînement de grand modèle.
:::

::: key
[Deux jauges à surveiller]{.tag} Suivez l'obsolescence en **versions** (un entier, facile à tracer) et l'écart des politiques en **rapport d'importance** (la part des pas où $\pi/\mu$ sort de $[0{,}8;\ 1{,}25]$, par exemple). La première dit ce que l'infrastructure produit, la seconde ce que l'algorithme en souffre.
:::

::: recap
Points clés — chapitre 5

-   Synchrone : fraîcheur parfaite, barrière sur le plus lent. Asynchrone : débit, mais trajectoires périmées.
-   L'obsolescence est un entier par trajectoire : versions de l'apprenant moins version de l'acteur. Étiquetez et mesurez.
-   L'acteur doit enregistrer la probabilité $\mu(a\mid x)$ du pas pour permettre une correction par poids d'importance tronqué.
-   Âge moyen d'un tampon FIFO : $\bar a \approx (c/2)/(b/R)$ ; réutiliser coûte de l'âge.
-   La synchronisation coûte $\alpha + n/B$ par lien ; la topologie de diffusion décide du total.
:::

## 6. Boucles en ligne et temps réel : latence, files, contre-pression {#ch6}

Une boucle en ligne apprend pendant qu'elle collecte. Ce chapitre construit le modèle qui permet de la dimensionner : combien d'acteurs pour saturer l'apprenant, ce que devient l'obsolescence quand on en ajoute, et où mettre la limite pour que la file ne dérive pas. Le modèle est celui du lab 11.3, validé contre une simulation à événements discrets.

### 6.1. La latence de bout en bout d'une donnée

Une donnée suit un chemin : lecture des poids, rollout, attente dans la file, mise à jour, publication des nouveaux poids. Sa **latence de bout en bout** est la somme de ces temps, et l'obsolescence en est la traduction en nombre de versions. Pour la réduire, on raccourcit le rollout (trajectoires plus courtes), on vide la file plus vite (apprenant plus rapide) ou on borne ce qui attend (crédits). On ne la réduit pas en ajoutant des acteurs : au-delà du point de saturation, ils ne font que remplir la file.

### 6.2. Deux régimes et un point de saturation

Notons $N$ le nombre d'acteurs, $m$ le nombre de pas d'environnement par trajectoire, $t_{\text{roll}}$ la durée d'un rollout, $t_{\text{sync}}$ celle de la lecture des poids, $b$ le nombre de trajectoires par mise à jour et $s_L$ la durée d'une mise à jour. La production et la capacité de l'apprenant valent

$$P(N) = \frac{N\,m}{t_{\text{roll}} + t_{\text{sync}}} \qquad C = \frac{b\,m}{s_L}$$

en pas par seconde, et le débit en régime permanent est $X = \min(P, C)$. Le point de saturation, au-delà duquel un acteur de plus n'apporte rien, est

$$N^{\star} = \frac{C\,(t_{\text{roll}} + t_{\text{sync}})}{m}$$

Sous $N^\star$, la boucle est **limitée par les acteurs** : l'apprenant attend ses données. Au-dessus, elle est **limitée par l'apprenant** : les acteurs attendent leur tour. Avec un taux de rejeu $R$, la capacité utile en données fraîches tombe à $C/R$.

::: ex
[Exemple 6.1 — Dimensionner avec plan.py]{.tag} Soit une boucle **illustrative** : trajectoires de $m = 200$ pas, rollout de 2,0 s, lecture des poids de 0,2 s, lots de $b = 4$ trajectoires, mise à jour de 1,0 s. Alors $C = 4 \times 200 / 1{,}0 = 800$ pas/s et $N^\star = 800 \times 2{,}2 / 200 = 8{,}8$. La commande `python3 plan.py --m 200 --t-roll 2.0 --t-sync 0.2 --b 4 --s-l 1.0 --queue-cap 8` (lab 11.3) répond 9 acteurs, un débit de 800 pas/s, un apprenant utilisé à 100 % et des acteurs utilisés à 97,8 %. Avec 8 acteurs, le débit serait $P = 727$ pas/s et l'apprenant serait inactif 9 % du temps.
:::

### 6.3. La loi de Little et l'obsolescence

La loi de Little ([module 1, §7.2](../linux-systems/index.html#mesurer-un-disque-avec-fio-la-loi-de-little)) s'écrit $L = \lambda W$ pour un système stable : $L$ éléments présents en moyenne, un débit d'arrivée $\lambda$, un temps moyen de séjour $W$. Appliquée à la boucle, elle donne une lecture simple de l'obsolescence : une trajectoire a l'âge de **tout ce qui circule devant elle**, divisé par ce qu'une mise à jour consomme.

$$\text{obsolescence} \approx \frac{\text{trajectoires en circulation}}{b}$$

Quand la boucle est limitée par l'apprenant, le nombre de trajectoires en circulation est $N + Q$ si chaque acteur garde sa trajectoire terminée en attendant une place dans une file de capacité $Q$ (politique « bloquer »), et $K$ si un acteur doit obtenir l'un des $K$ **crédits** avant de commencer (politique « crédit »). Quand elle est limitée par les acteurs, la file est presque vide et l'âge vient surtout du rollout. Le modèle du lab compte alors les rollouts en cours, plus en moyenne la moitié d'un lot qui attend d'être complet :

$$n_{\text{roll}} = \frac{N\,t_{\text{roll}}}{t_{\text{roll}}+t_{\text{sync}}}, \qquad \text{obsolescence} \approx \frac{n_{\text{roll}}}{b} + \frac{b-1}{2b}$$

### 6.4. Où placer la contre-pression

Trois politiques coexistent. Sans borne, la file grossit à la vitesse $(P - C)/m$ trajectoires par seconde et l'obsolescence croît sans limite. En « bloquant », l'acteur termine son rollout puis attend une place : la file est bornée mais l'acteur retient une trajectoire qui vieillit, et l'obsolescence atteint $(N+Q)/b$, proportionnelle au nombre d'acteurs. Avec des **crédits**, la limite est posée **avant** la production : l'obsolescence vaut $K/b$ quel que soit $N$.

Le tableau suivant vient de `report.py` (lab 11.3, temps simulé, durées lognormales de coefficient de variation 0,3, graine 1), pour la boucle de l'exemple 6.1, avec $Q = 8$ et $K = 8$.

| $N$ | $P$ | $X$ modèle | $X$ simulé | obsolescence modèle | obsolescence simulée | acteurs bloqués | $X$ avec $K=8$ | obsolescence avec $K=8$ |
|---|---|---|---|---|---|---|---|---|
| 2 | 182 | 182 | 182 | 0,83 | 0,59 | 0,0 | 182 | 0,59 |
| 4 | 364 | 364 | 365 | 1,28 | 1,28 | 0,0 | 365 | 1,27 |
| 6 | 545 | 545 | 547 | 1,74 | 1,99 | 0,0 | 516 | 1,85 |
| 8 | 727 | 727 | 725 | 2,19 | 2,94 | 0,0 | 577 | 2,00 |
| 10 | 909 | 800 | 794 | 4,50 | 4,41 | 1,3 | 577 | 2,00 |
| 12 | 1091 | 800 | 803 | 5,00 | 4,99 | 3,2 | 577 | 2,00 |
| 16 | 1455 | 800 | 805 | 6,00 | 6,00 | 7,2 | 577 | 2,00 |
| 24 | 2182 | 800 | 804 | 8,00 | 8,00 | 15,2 | 577 | 2,00 |

Lisez-le en trois temps. Le débit simulé suit le modèle à 0,7 % près sur toute la table. Au-delà de $N^\star$, l'obsolescence « bloquer » croît avec $N$ (de 4,4 à 8,0), tandis que les crédits la figent à 2,0. Le prix est visible : avec $K = 8$, le débit plafonne à 577 pas/s, soit 72 % de la capacité.

::: ex
[Exemple 6.2 — Combien de crédits ?]{.tag} Avec $N = 24$ acteurs, le même programme balaie $K$. Sortie de `report.py` :

~~~text
  K   X sim  learner util  lag model  lag sim  p95 lag
  8     577          0.72       2.00     2.00        3
 10     700          0.88       2.50     2.50        4
 12     772          0.96       3.00     3.00        4
 14     799          0.99       3.50     3.50        5
 16     800          1.00       4.00     4.00        5
 24     805          1.00       6.00     6.00        7
~~~

Le débit revient à moins de 1 % de la capacité dès $K = 14$ (graine 1), avec une obsolescence de 3,5 contre 8,0 en mode « bloquer ». La règle pratique de **cette** boucle : $K$ de l'ordre de $1{,}6\,N^\star$, soit $3{,}5\,b$ (le facteur dépend de $b$ et de la variabilité des durées : l'exercice 11 en trouve un autre). Si votre cible d'obsolescence est de 2, vous perdez 28 % de débit ; si elle est de 3,5, presque rien. L'arbitrage est un chiffre, pas une opinion.
:::

<figure class="fig">
<svg viewBox="0 0 560 470" role="img" aria-labelledby="f3-t f3-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="f3-t">Débit et obsolescence en fonction du nombre d'acteurs</title>
<desc id="f3-d">Haut : le débit simulé monte avec le nombre d'acteurs puis plafonne à 800 pas par seconde au-delà de N* égal à 8,8. Bas : l'obsolescence croît avec N en politique bloquer et reste à 2 avec 8 crédits.</desc>
<line x1="70" y1="205" x2="540" y2="205" stroke="currentColor" stroke-width="2"/><line x1="70" y1="30" x2="70" y2="205" stroke="currentColor" stroke-width="2"/>
<text x="62" y="210" text-anchor="end" font-size="14" fill="currentColor">0</text>
<text x="62" y="132" text-anchor="end" font-size="14" fill="currentColor">400</text>
<text x="62" y="54" text-anchor="end" font-size="14" fill="currentColor">800</text>
<text x="12" y="22" font-size="14" font-weight="700" fill="currentColor">pas/s</text>
<line x1="229.1" y1="30" x2="229.1" y2="205" stroke="currentColor" stroke-width="1.5" stroke-dasharray="5 4"/>
<text x="235" y="122" font-size="14" fill="currentColor">N* = 8,8</text>
<polyline points="70.0,205.0 88.1,187.3 106.2,169.6 124.2,152.0 142.3,134.3 160.4,116.6 178.5,98.9 196.5,81.3 214.6,63.6 232.7,49.4 250.8,49.4 268.8,49.4 286.9,49.4 305.0,49.4 323.1,49.4 341.2,49.4 359.2,49.4 377.3,49.4 395.4,49.4 413.5,49.4 431.5,49.4 449.6,49.4 467.7,49.4 485.8,49.4 503.8,49.4 521.9,49.4 540.0,49.4" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="6 4"/>
<circle cx="106.2" cy="169.6" r="5" fill="var(--accent)"/>
<circle cx="142.3" cy="134.1" r="5" fill="var(--accent)"/>
<circle cx="178.5" cy="98.6" r="5" fill="var(--accent)"/>
<circle cx="214.6" cy="64.0" r="5" fill="var(--accent)"/>
<circle cx="250.8" cy="50.6" r="5" fill="var(--accent)"/>
<circle cx="286.9" cy="48.9" r="5" fill="var(--accent)"/>
<circle cx="359.2" cy="48.6" r="5" fill="var(--accent)"/>
<circle cx="503.8" cy="48.8" r="5" fill="var(--accent)"/>
<text x="540" y="22" text-anchor="end" font-size="14" fill="currentColor">C = 800 ; tirets : modèle</text>
<line x1="70" y1="445" x2="540" y2="445" stroke="currentColor" stroke-width="2"/><line x1="70" y1="290" x2="70" y2="445" stroke="currentColor" stroke-width="2"/>
<text x="62" y="450" text-anchor="end" font-size="14" fill="currentColor">0</text>
<text x="62" y="381" text-anchor="end" font-size="14" fill="currentColor">4</text>
<text x="62" y="312" text-anchor="end" font-size="14" fill="currentColor">8</text>
<text x="12" y="276" font-size="14" font-weight="700" fill="currentColor">obsolescence (mises à jour)</text>
<text x="70" y="465" text-anchor="middle" font-size="14" fill="currentColor">0</text>
<text x="215" y="465" text-anchor="middle" font-size="14" fill="currentColor">8</text>
<text x="359" y="465" text-anchor="middle" font-size="14" fill="currentColor">16</text>
<text x="504" y="465" text-anchor="middle" font-size="14" fill="currentColor">24</text>
<text x="540" y="439" text-anchor="end" font-size="14" fill="currentColor">N (acteurs)</text>
<polyline points="106.2,434.8 142.3,423.0 178.5,410.7 214.6,394.3 250.8,369.1 286.9,359.0 359.2,341.7 503.8,307.2" fill="none" stroke="var(--accent)" stroke-width="3"/>
<polyline points="106.2,434.8 142.3,423.1 178.5,413.2 214.6,410.6 250.8,410.6 286.9,410.6 359.2,410.6 503.8,410.6" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="2 4"/>
<text x="90" y="318" font-size="14" fill="currentColor">bloquer : (N+Q)/b</text>
<text x="300" y="434" font-size="14" fill="currentColor">8 crédits : K/b = 2</text>
</svg>
<figcaption>Débit (haut) et obsolescence (bas) de la boucle de l'exemple 6.1, en temps simulé. Les points sont la simulation, les tirets le modèle ; les crédits figent l'obsolescence au prix du débit.</figcaption>
</figure>

### 6.5. Ce que le modèle ne dit pas, et ce que Ray montre

Le modèle d'obsolescence est une estimation de champ moyen. Près de la saturation, la variabilité des durées remplit la file avant que le débit n'atteigne le plafond : pour $N = 8$, le modèle prédit 2,19 et la simulation donne 2,94. Loin de la saturation il se trompe dans l'autre sens : pour $N = 2$, 0,83 prédit contre 0,59 simulé. Mesurez plutôt que de vous fier à la formule. Et une boucle réelle ajoute ce que le modèle ignore : pannes, acteurs de vitesses différentes, coût variable de la mise à jour.

Le lab 11.2, partie B, fait tourner une boucle sur de vrais acteurs Ray, avec un simulateur et un apprenant dont les durées sont **simulées** par des `sleep` (0,3 ms par pas, 10 ou 30 ms par mise à jour). L'obsolescence y suit la même lecture :

~~~text
 N  steps/s  upd/s  mean lag  p95  learner wait  final return
 1     2075   19.1      0.25    1          0.72          0.79
 2     3723   31.6      0.49    1          0.54          0.79
 4     4733   41.5      0.99    1          0.39          0.78
 8     3132   27.9      1.95    5          0.59          0.80

  K  steps/s  mean lag  p95   K/b       (N = 16, mise à jour simulée de 30 ms)
None     2418      3.72   10   nan
   8     1578      1.89    8   2.0
   4     1883      0.99    1   1.0
~~~

Dans ce tableau, « learner wait » est la fraction du temps que le pilote passe à attendre un résultat. Sans crédit, chaque acteur y a toujours une trajectoire en cours, et le pilote prend chaque lot dès qu'il est complet : à chaque mise à jour, $N$ trajectoires circulent et aucune n'attend dans la file. La lecture de la section 6.3 donne donc une obsolescence proche de $N/b$ ; avec des crédits, il en circule au plus $K$, d'où $K/b$.

Sur la VM de test (Ray 2.59.0, 2026-10-25), l'obsolescence moyenne est proche de $N/b$ : 1,95 pour 8 acteurs ($N/b = 2$), 3,72 pour 16 acteurs sans crédit ($N/b = 4$). Deux autres exécutions ont donné 1,94 et 3,61 : les valeurs bougent un peu d'une fois à l'autre. Avec des crédits, l'obsolescence vaut environ $K/b$ : 1,89 et 0,99. Le débit n'est pas monotone en $K$ (1 578 puis 1 883) : c'est du bruit d'une machine partagée, pas une propriété, et les tests n'affirment rien là-dessus. Le point à retenir est l'ordre de grandeur de l'obsolescence, et il est stable.

::: note
[Le débit baisse à 8 acteurs]{.tag} Dans ce lab, l'apprenant tourne dans le processus du pilote : à 8 acteurs, le débit baisse (3 132 pas/s) par rapport à 4 acteurs (4 733 ; deux autres exécutions ont donné la même baisse). Deux causes sont vraisemblables et le lab ne les sépare pas : le pilote reçoit et ordonnance tous les résultats, et les 4 vCPU de la VM sont déjà saturés par 8 acteurs, le pilote et les processus de Ray. Pour alléger le pilote, l'apprenant devient un acteur dédié, et la collecte de trajectoires se fait par lots ; mesurez avant de conclure.
:::

::: recap
Points clés — chapitre 6

-   $X = \min(P, C)$ avec $P = Nm/(t_{\text{roll}}+t_{\text{sync}})$ et $C = bm/s_L$ ; le point de saturation est $N^\star = C(t_{\text{roll}}+t_{\text{sync}})/m$.
-   Obsolescence $\approx$ trajectoires en circulation divisées par $b$ (loi de Little).
-   Sans borne, la file grossit à $(P-C)/m$ ; en « bloquant », $(N+Q)/b$ ; avec des crédits, $K/b$.
-   Les crédits figent l'obsolescence mais coûtent du débit si $K$ est trop petit : $K \approx 1{,}6\,N^\star$ dans l'exemple.
-   Le modèle de champ moyen sous-estime près de la saturation ; mesurez dans cette zone.
:::

## 7. Hétérogénéité : GPU d'entraînement, GPU d'évaluation, CPU {#ch7}

Une flotte réelle mélange des GPU chers pour l'apprenant, des GPU moins chers pour la génération ou l'évaluation, et des CPU pour les simulateurs. Ce chapitre pose comment placer chaque rôle sur le bon type de nœud, et comment choisir un type par un calcul de coût et non par habitude.

### 7.1. Un pool par rôle et par type

Chaque rôle de la boucle a son profil. Le simulateur d'environnement est souvent limité par le CPU. La génération est limitée par la bande passante mémoire du GPU et par la taille du cache KV (chapitre 9). L'évaluation par un modèle de récompense est un calcul d'inférence plus régulier. L'apprentissage est limité par le calcul et par les collectives. Ces profils ne demandent pas le même matériel.

Dans Ray, on exprime la contrainte par des **ressources personnalisées** déclarées sur les nœuds (`resources={"eval_gpu": 1}`), par les ressources standard (`num_gpus`), ou par des étiquettes de nœud et par le type d'accélérateur (`accelerator_type`) quand la distinction existe dans l'inventaire. Le gestionnaire de cluster fournit les types de nœuds : groupes de travailleurs de KubeRay, partitions et GRES de Slurm.

::: ex
[Exemple 7.1 — Trois pools sur un nœud, vus par ray status]{.tag} `resources_demo.py` déclare un nœud à 8 CPU, 2 « GPU » et 2 `eval_gpu` (ressources **logiques**, sans GPU réel) et place un apprenant sur un GPU, deux évaluateurs sur `eval_gpu` et quatre simulateurs sur CPU. Il demande ensuite un acteur à 2 GPU alors qu'un seul est libre. Extrait de `ray status` (Ray 2.59.0, VM de test, 2026-10-25) :

~~~text
Total Usage:
 4.0/8.0 CPU
 1.0/2.0 GPU
 2.0/2.0 eval_gpu
Pending Demands:
 {'CPU': 1.0, 'GPU': 2.0}: 1+ pending tasks/actors
~~~

Les trois pools sont placés ; la demande d'un acteur à 2 GPU reste en attente. Remarquez qu'elle porte aussi `'CPU': 1.0`, le CPU par défaut ajouté par Ray quand une ressource est demandée sans `num_cpus` (section 1.3).
:::

### 7.2. Une file par type, pas une file pour tous

Quand un seul pool alimente un seul apprenant, une file suffit. Avec plusieurs pools de vitesses différentes, une file unique mélange des trajectoires d'âges très différents : celles du pool lent sont plus périmées à l'arrivée. Deux précautions. Étiquetez chaque trajectoire du pool qui l'a produite, et suivez l'obsolescence par pool. Et donnez à chaque pool sa propre borne (crédits) : sinon le pool rapide occupe toute la file et prive l'apprenant de la diversité des autres.

### 7.3. Le coût par million de pas

Un type de nœud est meilleur s'il produit un million de pas pour moins d'argent, pas s'il est plus rapide ou moins cher pris isolément. Avec $N$ acteurs au prix horaire $p$ chacun et un apprenant au prix horaire $p_L$, pour un débit $X$ en pas par seconde :

$$\text{coût par million de pas} = \frac{N\,p + p_L}{3600\,X} \times 10^{6}$$

Comme le débit est plafonné par l'apprenant ($X = C$ dès que $N \ge N^\star$), comparer deux types d'acteurs revient à comparer $N_i\,p_i$, avec $N_i$ proportionnel à $t_i + t_{\text{sync}}$. Un type B moins rapide l'emporte donc quand

$$p_B\,(t_B + t_{\text{sync}}) < p_A\,(t_A + t_{\text{sync}})$$

Les prix sont des **entrées** : lisez la page de prix du fournisseur le jour même, et ne figez jamais un prix dans un document.

::: ex
[Exemple 7.2 — Simulateurs sur CPU ou sur GPU]{.tag} Boucle de l'exemple 6.1 ($C = 800$ pas/s, apprenant à 30 unités par heure, unités **fictives**). Un simulateur CPU met 6,0 s par trajectoire pour 0,5 unité par heure ; un simulateur accéléré par GPU met 1,0 s pour 4,0 unités. `plan.py` donne :

-   CPU : $N^\star = 800 \times 6{,}2 / 200 = 24{,}8$, soit 25 acteurs, $25 \times 0{,}5 + 30 = 42{,}5$ unités par heure, 14,76 unités par million de pas ;
-   GPU : $N^\star = 800 \times 1{,}2 / 200 = 4{,}8$, soit 5 acteurs, $5 \times 4{,}0 + 30 = 50$ unités par heure, 17,36 unités par million de pas.

Le CPU gagne de 15 %. Le prix d'équilibre du simulateur GPU est $25 \times 0{,}5 / 5 = 2{,}5$ unités : en dessous, il l'emporterait. Le raisonnement tient tant que le débit est plafonné par l'apprenant ; si ce n'est pas le cas, le calcul change.
:::

### 7.4. Hétérogénéité et obsolescence

Un pool plus lent produit des trajectoires plus longues à générer, donc plus de trajectoires « en vol » pour le même débit. L'obsolescence croît avec le nombre moyen de rollouts en cours $n_{\text{roll}}$ (section 6.3) quand la boucle est limitée par les acteurs, et avec $(N+Q)/b$ quand elle l'est par l'apprenant : dans les deux cas, avec le nombre d'acteurs.

Dans l'exemple 7.2, l'obsolescence en mode « bloquer » (file de 8) vaut 3,25 avec le pool de simulateurs GPU et 8,25 avec le pool CPU, parce qu'il faut 25 acteurs au lieu de 5 pour le même débit. C'est une raison de plus de la suivre par pool.

::: recap
Points clés — chapitre 7

-   Un pool par rôle (simulateur, génération, évaluation, apprentissage), exprimé par des ressources logiques, personnalisées ou standard.
-   `ray status` affiche l'usage par ressource et les demandes en attente : c'est le premier outil de diagnostic.
-   Étiquetez les trajectoires par pool, suivez l'obsolescence par pool, bornez chaque pool.
-   Coût par million de pas $= (Np + p_L)/(3600X) \times 10^6$ ; comparez des types à débit égal.
-   Un type moins cher et plus lent peut perdre : le calcul décide, avec des prix lus le jour même.
:::

## 8. Ray sur Kubernetes et sur Slurm, observabilité, alternatives {#ch8}

Ray ne remplace pas votre ordonnanceur de cluster : il s'installe dessus. Ce chapitre montre les deux installations courantes, ce qu'il faut observer, et les situations où un autre outil est un meilleur choix.

### 8.1. Ray sur Kubernetes avec KubeRay

Les objets Kubernetes employés ici (pod, opérateur, ressource personnalisée, Kueue) sont présentés au [module 12](../kubernetes-gpu/index.html#ch1) ; si vous ne les connaissez pas, lisez cette section après lui.

KubeRay est un opérateur Kubernetes qui fournit trois ressources personnalisées : `RayCluster`, qui gère le cycle de vie d'un cluster (création, suppression, autoscaling, tolérance aux pannes), `RayJob`, qui crée un cluster, y soumet un job et peut le supprimer à la fin, et `RayService`, qui ajoute un déploiement Ray Serve avec mises à jour sans interruption (README de KubeRay).

L'autoscaling s'active par `enableInTreeAutoscaling: true` : l'opérateur ajoute un conteneur annexe (*sidecar*) d'autoscaler au Pod de tête. Ce dernier lit les demandes de ressources logiques, ajuste `replicas` dans les limites `minReplicas` et `maxReplicas`, et retire les Pods inactifs après `idleTimeoutSeconds`, 60 s par défaut. Placer `num-cpus: "0"` dans les `rayStartParams` de la tête empêche d'y exécuter les tâches des utilisateurs. Depuis Ray 2.41, l'autoscaler lit les ressources d'un travailleur dans ses `rayStartParams` ou dans les limites et requêtes du conteneur.

Le fichier `deploy/raycluster.yaml` du lab 11.1 réunit ces champs pour un groupe CPU de rollouts (0 à 32 réplicas) et un groupe GPU d'apprenant. Il est **linté et analysé comme YAML, jamais appliqué** : vérifiez chaque champ contre la version de KubeRay que vous installez. La tolérance aux pannes du GCS demande un Redis externe (chapitre 2). L'ordonnancement en groupe (*gang scheduling*) d'un `RayJob` passe par un outil de file comme Kueue : la documentation de Ray liste un guide dédié, que ce module n'a pas relu.

::: ex
[Exemple 8.1 — Le plancher de gaspillage de l'autoscaler]{.tag} Quand une vague de 32 nœuds CPU de rollouts se termine, chaque nœud reste facturé au moins `idleTimeoutSeconds` = 60 s avant retrait : $32 \times 60 / 3600 = 0{,}53$ nœud-heure par vague, sans compter la détection. À une vague par heure sur 24 h, c'est $24 \times 0{,}53 = 12{,}8$ nœuds-heures, soit 1,7 % des 768 nœuds-heures d'une allocation statique de 32 nœuds. Réduire le délai à 30 s divise ce plancher par deux, au risque de retirer un nœud juste avant la vague suivante : le bon réglage dépend de l'intervalle entre vagues.
:::

### 8.2. Ray sur Slurm

Slurm lance N copies d'un programme, adapté au MPI ; Ray attend une tête, des travailleurs et un point d'entrée unique. Depuis Ray 2.49, la commande `ray symmetric-run` comble l'écart : exécutée sur tous les nœuds de l'allocation, elle démarre Ray partout et lance le programme d'entrée **sur la tête seulement**. Le script `deploy/ray_slurm.sbatch` suit l'exemple de la documentation : `--nodes`, `--exclusive`, `--tasks-per-node=1` (un runtime Ray par nœud), puis un `srun` de `ray symmetric-run` avec `--min-nodes` pour attendre que tous les nœuds aient rejoint.

~~~bash
srun --nodes="$SLURM_JOB_NUM_NODES" --ntasks="$SLURM_JOB_NUM_NODES" \
  ray symmetric-run \
  --address "$ip_head" \
  --min-nodes "$SLURM_JOB_NUM_NODES" \
  --num-cpus="${SLURM_CPUS_PER_TASK}" \
  --num-gpus="${SLURM_GPUS_PER_TASK}" \
  -- \
  python -u rl_driver.py
~~~

Conséquences d'exploitation : la durée de vie du cluster Ray est celle du job Slurm, l'allocation est statique (pas d'autoscaling), et un nœud perdu emporte le job sauf si l'application sait reprendre (module 10). En contrepartie, vous gardez la comptabilité, l'équité et la préemption de Slurm (module 5). Le script est **linté avec shellcheck, jamais exécuté** : il demande un Slurm à GPU.

### 8.3. Observer une application Ray

Ray émet des métriques au format Prometheus, mais ne les stocke pas : vous hébergez Prometheus et vous le configurez pour les collecter. Le port d'export se fixe avec `--metrics-export-port` (la documentation utilise 8080) et l'export suppose l'installation avec le composant de tableau de bord (`ray[default]`). Les métriques système utiles à une boucle sont `ray_tasks` et `ray_actors` (par nom et état), `ray_resources`, `ray_object_store_memory` et `ray_node_cpu_utilization`, avec des équivalents `ray_node_gpus_utilization` pour les GPU.

La documentation prévient qu'il faut **sommer** `ray_tasks` et `ray_actors` (par exemple `sum(ray_tasks) by (Name, State)`), car ces métriques sont émises par plusieurs composants distribués, avec des points parfois négatifs. En ligne de commande, l'API d'état donne `ray status`, `ray list actors` et `ray summary tasks`.

Ces métriques disent comment va Ray, pas comment va votre boucle. Ajoutez trois jauges applicatives, émises par le pilote : l'obsolescence (moyenne et p95), la longueur de la file, et la fraction du temps que l'apprenant passe à attendre. Ce sont les trois colonnes du tableau du lab 11.2, et elles se branchent sur l'observabilité du [module 14](../observability/index.html).

### 8.4. Alternatives : Dask, Spark, Kubeflow Trainer

Ray n'est pas la réponse à tout. Les pages d'accueil des projets suffisent à situer les alternatives.

| Outil | Ce qu'il dit être | Quand le préférer à Ray |
|---|---|---|
| Dask | une bibliothèque Python de calcul parallèle et distribué | analyse de tableaux et de DataFrames déjà écrite en NumPy ou pandas |
| Apache Spark | un moteur d'analyse unifié pour le traitement de données à grande échelle | ETL et SQL massifs, écosystème de données existant |
| Kubeflow Trainer | une plateforme d'IA distribuée native de Kubernetes pour l'entraînement et le réglage fin de modèles (ressources `TrainJob`) | un job d'entraînement distribué sur Kubernetes, sans rôles hétérogènes |
| Ray | un moteur de tâches et d'acteurs avec des bibliothèques d'entraînement, d'ingestion, de service | rôles hétérogènes, graphe dynamique, états longs (chapitre 1) |

La dernière colonne est un choix pédagogique de ce parcours, pas un classement des outils : chacun a des usages où il est excellent, et plusieurs se combinent (Ray sur Kubernetes via KubeRay, par exemple).

::: ex
[Exemple 8.2 — Trois charges, trois choix]{.tag} (1) Un ETL nocturne de 10 To de fichiers Parquet vers des tables : Spark, car la charge est un graphe de données statique. (2) Un réglage fin supervisé sur 64 GPU, identique sur tous les rangs : un job `torchrun` sous Slurm, ou un `TrainJob` sous Kubernetes, car c'est du SPMD. (3) Une boucle de renforcement avec des simulateurs CPU, un évaluateur et un apprenant GPU : Ray, car les rôles diffèrent et le graphe change. Le critère de décision est la **forme** de la charge, pas la popularité de l'outil.
:::

::: recap
Points clés — chapitre 8

-   KubeRay : `RayCluster`, `RayJob`, `RayService` ; autoscaler en sidecar ; `idleTimeoutSeconds` à 60 s ; GCS tolérant avec Redis.
-   Sur Slurm : `ray symmetric-run` (Ray 2.49 et plus) ; cluster Ray = durée du job ; pas d'autoscaling.
-   Ray exporte du Prometheus sans le stocker ; sommez `ray_tasks` et `ray_actors` ; ajoutez trois jauges de boucle (obsolescence, file, attente de l'apprenant).
-   Dask, Spark, Kubeflow Trainer couvrent d'autres formes de charge ; choisissez par la forme de la charge.
:::

## 9. Inférence pour les rollouts et pour le service : moteurs, cache KV et batching continu {#ch9}

Le chapitre 4 a laissé une boîte fermée : l'étage de génération tourne « sur un moteur d'inférence », et c'est souvent lui qui domine l'itération. Ce chapitre ouvre cette boîte. Le même moteur sert aussi les utilisateurs d'un modèle en production, et les deux charges se disputent les GPU de l'entraînement. Plusieurs offres du [relevé du parcours](../../market/index.html) citent des moteurs de service comme vLLM ou SGLang, et l'une demande d'optimiser les accès au stockage du prefill, du decode et du cache de préfixes : ce chapitre en donne les mécanismes.

### 9.1. Deux charges d'inférence sur une même flotte

Une génération de rollouts et un service en ligne exécutent le même calcul : un modèle produit des jetons un à un à partir d'un prompt. OpenRLHF génère ses rollouts avec vLLM (section 4.4), un moteur conçu pour le service de modèles. Les deux charges ne poursuivent pourtant pas le même objectif, et l'infrastructure doit savoir laquelle elle sert.

| | Rollouts de post-entraînement | Service en ligne |
|---|---|---|
| Objectif | débit en jetons par seconde, pour le lot entier | latence de chaque requête, sous un objectif de service (SLO) |
| Arrivées | par vagues, au rythme de l'apprenant | continues, variables dans la journée |
| Poids | changent à chaque version (section 5.4) | fixes entre deux déploiements |
| Ce qui coûte | la génération la plus lente, en mode synchrone (section 5.1) | la queue de la distribution des latences |
| Préemption | possible, au prix du travail en vol | à éviter : elle dégrade le SLO |

Les deux charges partagent souvent les GPU de l'entraînement. Le [mode veille de vLLM](https://docs.vllm.ai/en/latest/features/sleep_mode.html), « especially useful for RLHF, training, or cost-saving scenarios » selon sa documentation, libère la mémoire sans arrêter le serveur. Au niveau 1, les poids partent en mémoire CPU et le cache KV est effacé ; au niveau 2, les deux sont effacés, ce qui convient à une mise à jour des poids. C'est un moyen de partager les mêmes GPU entre entraînement et génération (note de la section 4.4).

### 9.2. Ce que fait un moteur : prefill, decode et cache KV

Une requête passe par deux phases, que l'article de PagedAttention ([Kwon et al., SOSP 2023](https://arxiv.org/abs/2309.06180)) décrit. Le **prefill** (*prompt phase*) traite tout le prompt d'un coup, par des produits de matrices qui exploitent bien le parallélisme du GPU ; pour un prompt qui n'est pas court, il tend à être limité par le calcul (DistServe, section 9.5). Il produit le premier jeton. Le **decode** produit ensuite un jeton par itération et par séquence ; il sous-utilise le calcul et devient limité par la bande passante mémoire. C'est l'exemple 4.4 du [module 2](../perf-models/index.html#ch4), à l'échelle d'un modèle entier.

::: def
[Cache KV]{.tag} Pour produire le jeton suivant, l'attention a besoin des clés et des valeurs de tous les jetons précédents, dans chaque couche. Le moteur les garde en mémoire GPU au lieu de les recalculer : c'est le **cache KV** (*key-value cache*). Il grandit d'une entrée par jeton et par séquence, et il est libéré à la fin de la requête, sauf si le moteur le garde pour un préfixe commun (section 9.4).
:::

Deux moteurs ouverts sont cités par des offres du relevé : vLLM, né de l'article de PagedAttention, et SGLang ([Zheng et al., 2023](https://arxiv.org/abs/2312.07104)), dont le moteur d'exécution introduit RadixAttention pour réutiliser le cache KV. Les mécanismes qui suivent leur sont communs ; les options citées sont celles de vLLM.

### 9.3. Dimensionner le cache KV

::: thm
[Taille du cache KV par jeton]{.tag} Pour un modèle à $n_L$ couches et $n_{KV}$ têtes de clés-valeurs de dimension $d_h$, stockées sur $e$ octets par élément :

$$k = 2 \times n_L \times n_{KV} \times d_h \times e \quad \text{octets par jeton}$$

Le facteur 2 compte la clé et la valeur. L'article de PagedAttention fait le calcul pour OPT-13B, sans têtes groupées : 2 × 5 120 (taille cachée) × 40 couches × 2 octets, soit 800 Ko par jeton. Avec l'attention à têtes groupées (*grouped-query attention*, GQA), seules les têtes de clés-valeurs comptent, pas les têtes de requête.
:::

::: ex
[Exemple 9.1 — Combien de séquences de 8 192 jetons sur un GPU de 80 Go ?]{.tag} Le [`config.json` de Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json) (lu le 2026-10-25) donne 36 couches, 8 têtes de clés-valeurs, `head_dim` = 128 et `torch_dtype` = `bfloat16`. D'où $k = 2 \times 36 \times 8 \times 128 \times 2 = 147\,456$ octets (144 Kio) par jeton, et 1,208 Go par séquence de 8 192 jetons. Les dimensions du même fichier donnent 8,19 milliards de paramètres (la [fiche du modèle](https://huggingface.co/Qwen/Qwen3-8B) annonce 8,2), soit $W = 16{,}38$ Go de poids en BF16.

Sur un GPU de 80 Go (H100 SXM, module 2), vLLM n'utilise par défaut que 92 % de la mémoire (`--gpu-memory-utilization`, [documentation](https://docs.vllm.ai/en/latest/configuration/engine_args.html) lue le 2026-10-25). Restent $0{,}92 \times 80 - 16{,}38 = 57{,}22$ Go, soit 47 séquences de 8 192 jetons ; 52 si l'on prenait toute la mémoire. C'est un plafond : les activations et les graphes CUDA en prennent une part, que seul un démarrage réel mesure.

Deux leviers changent ce nombre. Sans GQA (32 têtes de clés-valeurs au lieu de 8), le cache passerait à 576 Kio par jeton, soit 11 séquences. Un cache en FP8 (`--kv-cache-dtype fp8`) divise $e$ par deux : 94 séquences, si la qualité des réponses le permet.
:::

::: key
[Le cache KV fixe la taille du lot]{.tag} Le nombre de séquences simultanées, donc le débit du decode, est borné par la mémoire laissée au cache KV après les poids, bien avant le calcul. Dimensionnez un moteur en jetons de cache disponibles, puis divisez par la longueur des contextes.
:::

À chaque itération de decode, le GPU relit tous les poids et le cache KV de tout le lot, pour un jeton par séquence. Le coût fixe des poids se partage entre les séquences, d'où l'intérêt d'en faire tourner beaucoup à la fois. Le modèle roofline borne la durée d'une itération, pour $B$ séquences de contexte $L$ et une bande passante mémoire $\beta$ :

$$t_{\text{step}} \ge \frac{W + B\,L\,k}{\beta}$$

::: ex
[Exemple 9.2 — Ce que coûte une itération de decode]{.tag} Avec les valeurs de l'exemple 9.1, des contextes de 8 192 jetons et $\beta = 3{,}35$ To/s (H100 SXM), la borne donne :

| Séquences $B$ | Itération (borne basse) | Jetons/s (borne haute) | Part du cache KV dans les octets lus |
|---|---|---|---|
| 1 | 5,25 ms | 190 | 7 % |
| 16 | 10,66 ms | 1 501 | 54 % |
| 47 | 21,84 ms | 2 152 | 78 % |

Passer de 1 à 47 séquences multiplie le débit par 11,3 et la durée d'une itération par 4,2 : chaque séquence reçoit ses jetons plus lentement. Lot plein, le cache KV domine les octets lus : GQA et FP8 accélèrent aussi le decode. Un moteur réel reste en deçà de ces bornes ; mesurez-le.
:::

### 9.4. PagedAttention, batching continu et cache de préfixes

Les systèmes antérieurs réservaient pour chaque requête une zone contiguë à la longueur maximale possible. Les auteurs de PagedAttention mesurent que seuls 20,4 % à 38,2 % de la mémoire du cache KV y stockaient réellement des jetons ; le reste était perdu en réservation et en fragmentation. PagedAttention découpe le cache en **blocs** d'un nombre fixe de jetons, alloués à la demande et non contigus, comme les pages de la mémoire virtuelle. vLLM annonce un gaspillage presque nul et un débit multiplié par 2 à 4 à latence égale.

Le second mécanisme vient d'Orca ([Yu et al., OSDI 2022](https://www.usenix.org/conference/osdi22/presentation/yu)) : l'ordonnancement **par itération** (*iteration-level scheduling*), aujourd'hui appelé **batching continu**. L'ordonnanceur lance le modèle une itération à la fois ; une séquence terminée libère sa place aussitôt, et une requête en attente la prend. Orca rapporte un débit multiplié par 36,9 à latence égale face à FasterTransformer, sur GPT-3 175B. Pour des rollouts de longueurs très variables, c'est décisif : en lot statique, chaque place attend la plus longue réponse du lot.

::: ex
[Exemple 9.3 — Lot statique, lot continu, cache paginé]{.tag} Le lab 11.4 simule un moteur sur 64 requêtes arrivées ensemble, comme une vague de rollouts : réponses de 18 à 982 jetons (médiane 95), 32 places, cache de 16 384 jetons. Une itération dure la borne de l'exemple 9.2, plus le prefill des prompts admis. Le temps est **simulé**. Sortie de `sim.py` :

~~~text
    policy       kv  steps  time s   tok/s slot use mean run max run preempt
    static  reserve   4967   25.00     627     0.10      3.2      12       0
continuous  reserve   1889    9.95    1575     0.26      8.3      12       0
continuous    paged   1114    6.16    2544     0.44     14.1      32       0
~~~

À mémoire réservée égale, le lot continu produit les mêmes 15 679 jetons en 2,63 fois moins d'itérations : seule l'admission a changé. Réserver le prompt plus 1 024 jetons plafonne le lot à 12 séquences ; le cache paginé en admet 32 et divise encore les itérations par 1,70. Le temps baisse un peu moins (2,51 puis 1,62) : une itération plus chargée lit plus de cache KV.
:::

Le troisième mécanisme évite de refaire un calcul déjà fait. Le **cache de préfixes** garde les blocs KV d'une requête terminée et les réutilise quand une nouvelle requête commence par les mêmes jetons. vLLM identifie chaque bloc par un hachage de ses jetons et de tous ceux qui le précèdent, et évince les blocs inutilisés selon une politique LRU ([conception du cache de préfixes](https://docs.vllm.ai/en/latest/design/prefix_caching.html)) ; SGLang range les préfixes dans un arbre radix. Le prefill d'un long préfixe commun est évité, et avec lui une partie du délai avant le premier jeton.

::: ex
[Exemple 9.4 — Le préfixe partagé d'un groupe GRPO]{.tag} GRPO produit $G$ réponses par prompt (section 4.3). Avec $G = 8$, un prompt de 1 000 jetons et des réponses de 2 000 jetons en moyenne (hypothèses d'exemple), sur Qwen3-8B : sans partage, le moteur fait le prefill de 8 000 jetons ; avec, de 1 000, soit 87,5 % de moins. Le cache KV du groupe passe de 3,54 Go à 2,51 Go (29 % de moins), car le prompt n'est stocké qu'une fois.

PagedAttention partage déjà le prompt entre les échantillons d'une même requête ; le cache de préfixes étend ce partage à des requêtes distinctes, si elles arrivent sur le **même** moteur. Un répartiteur qui disperse les huit requêtes d'un groupe annule le gain : routez par prompt.
:::

### 9.5. Mesurer un service : TTFT, TPOT et goodput

::: def
[TTFT, TPOT et goodput]{.tag} Le **TTFT** (*time to first token*) est le délai entre l'arrivée d'une requête et son premier jeton : attente plus prefill. Le **TPOT** (*time per output token*) est la durée moyenne entre deux jetons suivants : le rythme du decode. Une réponse de $n$ jetons dure environ $\text{TTFT} + (n-1)\,\text{TPOT}$. Le **goodput** par GPU, au sens de DistServe ([Zhong et al., OSDI 2024](https://arxiv.org/abs/2401.09670)), est le plus grand taux de requêtes qu'un GPU sert en tenant à la fois les objectifs de TTFT et de TPOT pour une part fixée des requêtes, par exemple 90 %.
:::

Au [module 10](../fault-tolerance/index.html#ch2), le *goodput* d'un entraînement est la part du temps d'horloge consacrée à du calcul conservé : précisez toujours lequel des deux sens vous employez. Le débit seul ne suffit pas, car un moteur saturé produit beaucoup de jetons par seconde avec des TTFT de plusieurs secondes. vLLM exporte pour Prometheus ([métriques](https://docs.vllm.ai/en/latest/usage/metrics.html), lues le 2026-10-25) les histogrammes `vllm:time_to_first_token_seconds` et `vllm:inter_token_latency_seconds`, et les jauges `vllm:num_requests_waiting` et `vllm:kv_cache_usage_perc`.

::: ex
[Exemple 9.5 — Le goodput d'un GPU simulé]{.tag} `sim.py --sweep` (lab 11.4) envoie 400 requêtes à des taux croissants, arrivées de Poisson, et compte la part qui tient un TTFT de 500 ms et un TPOT de 20 ms. Extrait, en temps simulé :

~~~text
 rate     policy       kv   tok/s  TTFT p95  TPOT p95  attain
   16 continuous    paged    3202      60ms     6.5ms    0.99
   20 continuous    paged    3518    1809ms     9.2ms    0.40
   24 continuous    paged    3569    4108ms     8.8ms    0.25
~~~

À 16 requêtes par seconde, 99 % des requêtes tiennent l'objectif. À 20, le débit monte encore de 10 %, mais 40 % seulement le tiennent : la file fait exploser le TTFT. Au pas de 4 du balayage, le goodput est donc de 16 requêtes par seconde, et non 24, où le débit est le plus haut. En lot statique, aucun taux n'atteint 90 % : le TTFT p95 dépasse 29 s dès 4 requêtes par seconde. Le TPOT p95 passe de 6,5 à 9,2 ms : plus de séquences et de prefills par itération ralentissent tout le monde.
:::

Ce dernier effet est l'**interférence** entre prefill et decode. DistServe la supprime en plaçant les deux phases sur des GPU différents, chacune avec son parallélisme, et annonce 7,4 fois plus de requêtes servies ou un SLO 12,6 fois plus serré, pour plus de 90 % des requêtes dans les contraintes. vLLM propose cette séparation comme fonction [expérimentale](https://docs.vllm.ai/en/latest/features/disagg_prefill.html), qui « DOES NOT improve throughput » : elle règle séparément TTFT et latence entre jetons. SGLang la [documente](https://docs.sglang.io/docs/advanced_features/pd_disaggregation) aussi. L'autre réponse, active par défaut dans vLLM lorsque c'est possible ([guide d'optimisation](https://docs.vllm.ai/en/latest/configuration/optimization.html)), est le prefill découpé (*chunked prefill*) en morceaux mêlés au decode.

La séparation a un prix : le cache KV du prompt passe du GPU de prefill au GPU de decode. Pour Qwen3-8B et un prompt de 2 000 jetons, c'est 295 Mo : 11,8 ms sur un lien de 25 Go/s (hypothèse de la section 5.4), et sur le NVLink du H100, dont les 900 Go/s sont une bande passante totale ([blog Hopper](https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth/)), 0,33 ms à ce débit et 0,66 ms à sa moitié. À 10 requêtes par seconde, ce transfert demande 2,95 Go/s : c'est aussi un problème de réseau ([module 7](../networking/index.html)).

### 9.6. Autoscaling et cohabitation avec l'entraînement

Un service suit sa charge en ajoutant des réplicas, et le signal compte. L'utilisation du GPU est trompeuse : elle mesure la présence de noyaux ([module 14](../observability/index.html#ch2)), et un moteur en batching continu en exécute en permanence, avec 2 séquences comme avec 40. Les bons signaux sont la file et la mémoire : `vllm:num_requests_waiting` et `vllm:kv_cache_usage_perc`. Ray Serve règle son autoscaler sur le nombre moyen de requêtes en cours par réplica (`target_ongoing_requests`, [guide d'autoscaling](https://docs.ray.io/en/latest/serve/autoscaling-guide.html)) ; sur Kubernetes, un HPA peut lire une [métrique personnalisée](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/).

Un réplica neuf lit ses poids, puis initialise le moteur. Pour 16,4 Go, la lecture prend 16,4 s à 1 Go/s et 3,3 s à 5 Go/s (débits d'hypothèse, à mesurer sur votre stockage, [module 8](../storage/index.html)) ; l'initialisation s'y ajoute, et ce cours ne l'a pas mesurée. Gardez assez de réplicas chauds pour absorber la croissance du trafic pendant un démarrage (exercice 14). Le mode veille raccourcit ce délai, car le moteur reste initialisé.

Sur une flotte partagée, les coûts de préemption diffèrent. Le service a un SLO : il passe en premier. Un rollout préempté perd sa génération en cours ; avec des crédits (section 6.4), le nombre de trajectoires en vol borne cette perte. Un apprenant préempté repart de son dernier checkpoint ([module 10](../fault-tolerance/index.html)). Kueue exprime ces priorités entre charges ([module 12, chapitre 3](../kubernetes-gpu/index.html#ch3)) ; dans un moteur, vLLM sert par arrivée ou par priorité (`--scheduling-policy`) et compte dans `vllm:num_preemptions` les séquences évincées faute de cache KV.

Enfin, le coût par jeton suit l'utilisation (exemple 1.2 du [module 15](../finops-capacity/index.html#ch1)) : les réplicas chauds gardés pour le SLO coûtent sans servir. Prêter leurs GPU aux rollouts pendant les creux, par le mode veille ou par une préemption au bord d'une trajectoire, récupère une partie de ce coût ; l'exercice 14 chiffre cet arbitrage.

::: recap
Points clés — chapitre 9

-   Rollouts et service partagent les moteurs : les premiers visent le débit, le second une latence sous SLO.
-   Prefill souvent limité par le calcul ; decode, un jeton par itération, limité par la bande passante mémoire.
-   Cache KV : $k = 2\,n_L\,n_{KV}\,d_h\,e$ octets par jeton ; la mémoire laissée après les poids borne le lot.
-   PagedAttention pagine le cache, le batching continu remplit chaque place libérée, le cache de préfixes évite un prefill commun.
-   Mesurez TTFT, TPOT et goodput sous SLO ; séparer prefill et decode coûte un transfert de cache KV.
-   Autoscalez sur la file et le cache KV, comptez le démarrage à froid, préemptez d'abord ce qui coûte le moins à refaire.
:::

## Labs {#labs}

Les labs 11.1 à 11.3 tournent sur un **Ray réel, local, sans GPU** (testé avec Ray 2.59.0, PyTorch 2.14.1 pour CPU et Python 3.13, le 2026-10-25) ; le lab 11.4 est un simulateur en Python standard, sans Ray. Installation préalable, dans l'environnement virtuel de la [page d'installation](../../lab-setup/index.html) :

~~~bash
python3 -m pip install "ray[data,train]==2.59.0" numpy pytest pyyaml
python3 -m pip install "torch==2.14.1" --index-url https://download.pytorch.org/whl/cpu   # PyTorch for CPU
~~~

Ce que les labs **simulent** est dit dans chaque README et ici : les « GPU » sont des ressources logiques ; les durées de simulateur et de mise à jour du lab 11.2 sont des `sleep` ; le temps des labs 11.3 et 11.4 est simulé, et le moteur d'inférence du lab 11.4 aussi. Ce qu'ils exécutent pour de vrai : l'ordonnanceur, les acteurs, le magasin d'objets, les pannes (processus tués), Ray Data et Ray Train. Les fichiers `deploy/` du lab 11.1 (Slurm, KubeRay) sont **lintés seulement** : ils demandent un cluster.

### Lab 11.1 — Tâches, acteurs, ressources et pannes {#lab-11-1}

::: lab

**Objectif.** Mesurer le coût d'une tâche, comparer tâches et acteurs sur un pipeline, observer ce que Ray fait quand un processus meurt, et lire des ressources logiques. **Durée.** 4 h. **Prérequis matériels.** Un portable CPU, 4 cœurs, 8 Go recommandés (testé avec 16 Go) ; aucun GPU.

1.  Lisez `labs/ray-rl-infra/ray-actors/pipeline.py` : repérez `score_with_rebuild` (tâche, reconstruit le modèle à chaque appel) et `Scorer` (acteur, le construit une fois).
2.  Lancez `PYTHON=... bash verify.sh` (environ 2 minutes) et lisez la sortie complète de `run_demo.py`.
3.  Partie A : avec `granularity.efficiency(d)` (appelée par `run_demo.py`), mesurez $o$ avec $d = 1$ ms, prédisez $E(10\ \text{ms})$ par $d/(d+o)$, puis mesurez ; regroupez par 100 et expliquez l'écart au modèle.
4.  Partie B : dans `fault.py` (appelé par `run_demo.py`), retrouvez les cinq lignes de l'exemple 2.3 ; ajoutez un test où l'on tue un acteur du `ActorPool` en plein pipeline et où l'on rend l'appel idempotent.
5.  Lancez `resources_demo.py`, `data_demo.py` et `train_demo.py` ; changez `concurrency`, `max_failures` et l'instant de la panne, et expliquez chaque changement de sortie.

**Critère de réussite.** `verify.sh` s'arrête avec le code 0 et affiche « OK ray-actors » : 8 tests passent, `data_demo.py` compte 2 processus de notation, `train_demo.py` finit sans erreur. Votre $o$ mesuré est positif et votre prédiction de $E(10\ \text{ms})$ est à 0,15 près de la mesure. Sur la VM de l'auteur : $o \approx 1{,}85$ ms et 40 chargements de modèle en mode tâches contre 4 en mode acteurs ; vos valeurs seront différentes.

**Pour aller plus loin.** Démarrez un cluster Ray à deux machines (`ray start --head`, puis `--address`) et refaites la partie B en tuant un nœud ; limitez les CPU d'un travailleur avec un cgroup et constatez que Ray ne le fait pas à votre place. Après le chapitre 8 (séance 9), lisez `deploy/ray_slurm.sbatch` et `deploy/raycluster.yaml` à côté de la documentation de Ray, puis passez-les à `shellcheck` et `yamllint`.
:::

### Lab 11.2 — Boucle acteur-apprenant minimale {#lab-11-2}

::: lab

**Objectif.** Construire une boucle acteurs, tampon, apprenant et synchronisation de politique, mesurer son obsolescence et son débit, et observer l'effet d'une obsolescence imposée sur l'apprentissage. **Durée.** 6 h. **Prérequis matériels.** Ceux du lab 11.1.

1.  Partie A (2 h) : lisez `toy_env.py`, `learner.py`, `replay.py` et `loop_sim.py`. Lancez `pytest -q test_toy.py` (15 tests) puis `python3 report.py` ; vérifiez que la table A est **identique** sur deux exécutions.
2.  Tracez la courbe d'apprentissage de la graine 0 pour `lag=32` en règle naïve et en règle tronquée (`report.curve_demo()`), puis faites varier `lr` et `lag` : à partir de quel retard la règle naïve échoue-t-elle ?
3.  Partie B (4 h) : lancez `loop_ray.py` pour $N \in \{1, 2, 4, 8\}$ en mode `queue`. Comparez l'obsolescence moyenne à $N/b$ et le débit à $\min(P, C)$ du lab 11.3.
4.  Ajoutez des crédits ($K = 8$ puis $4$ avec 16 acteurs) et vérifiez que l'obsolescence vaut environ $K/b$. Passez en mode `replay` avec un tampon de 64 trajectoires et des taux de rejeu 1 et 2 : comparez l'âge moyen à $(c/2)/(b/R)$.
5.  Rendez l'apprenant asynchrone du pilote (un acteur Ray dédié) et dites ce que cela change au plafond de débit.

**Critère de réussite.** `verify.sh` affiche « OK actor-learner-toy » (15 tests, code 0). La table A est identique d'une exécution à l'autre. En partie B, l'obsolescence moyenne vaut $N/b$ à 25 % près pour $N = 4$ et $N = 8$, et les crédits la réduisent d'au moins 40 % à $N = 16$. Sur la VM de l'auteur : 0,99 et 1,95 pour $N/b$ = 1 et 2 ; 3,72 sans crédit contre 1,89 avec $K=8$.

**Pour aller plus loin.** Remplacez le couloir par un petit réseau PyTorch CPU ; implémentez la V-trace complète ; ajoutez un deuxième pool d'acteurs plus lent et suivez l'obsolescence par pool.
:::

### Lab 11.3 — Modèle de débit d'une boucle en ligne {#lab-11-3}

::: lab

**Objectif.** Écrire un modèle analytique d'une boucle acteurs-apprenant, le confronter à une simulation à événements discrets, et en tirer le nombre d'acteurs et de crédits. **Durée.** 3 h. **Prérequis matériels.** Ceux du lab 11.1 (seuls `numpy` et `pytest` servent ici) ; le temps est simulé.

1.  Partie 1 (1 h) : lisez `model.py`. Calculez à la main la capacité $C$ et le point $N^\star$ pour `m=128`, `t_roll=1.5`, `t_sync=0.1`, `b=8` et `s_L=0.8`, puis vérifiez avec `plan.py`.
2.  Partie 2 (2 h) : lisez `des.py` (deux politiques, `block` et `credit`), lancez `pytest -q test_throughput.py` (20 tests), puis `report.py` et `sweep.py`.
3.  Écrivez un test supplémentaire de votre choix (par exemple : la file non bornée grossit à $(P-C)/m$) et un mutant qui le casse.
4.  Comparez la table de `report.py` à la formule $(N+Q)/b$ pour $N$ entre 10 et 24, puis à $K/b$ pour les crédits ; expliquez l'écart près de $N^\star$.

**Critère de réussite.** `verify.sh` affiche « OK throughput-model » : 20 tests passent, l'écart de débit entre modèle et simulation reste sous 6 % sur toute la table de `report.py` (0,7 % sur la VM de l'auteur), et la loi de Little tient à moins de 3 % sur la file. Le résultat ne dépend d'aucune horloge : il est identique d'une machine à l'autre.

**Pour aller plus loin.** Ajoutez un mode « rejeu » à la simulation ; modélisez deux pools d'acteurs de vitesses différentes ; réinjectez dans le modèle les paramètres mesurés au lab 11.2 (temps de rollout par acteur, durée de mise à jour du pilote) et comparez le débit prédit au débit mesuré.
:::

### Lab 11.4 — Batching statique, batching continu et cache KV paginé {#lab-11-4}

::: lab

**Objectif.** Mesurer, sur un moteur d'inférence simulé, ce que changent le batching continu et la pagination du cache KV, puis tirer un goodput sous SLO d'un balayage de charge. **Durée.** 0,5 h dans la séance 10, davantage pour « Pour aller plus loin ». **Prérequis matériels.** Un portable CPU et Python 3 (bibliothèque standard seule) ; ni GPU, ni Ray. Le temps est simulé.

1.  Lisez `labs/ray-rl-infra/batching-sim/sim.py` : repérez la durée d'une itération (la borne de l'exemple 9.2), la règle d'admission des deux politiques et la préemption du mode `paged`.
2.  Lancez `PYTHON=... bash verify.sh` (quelques secondes) : 11 tests passent, puis s'affichent la table de l'exemple 9.3 et le balayage de l'exemple 9.5.
3.  Refaites à la main le calcul de `test_static_steps_equal_the_sum_of_batch_maxima` : pourquoi les itérations d'un lot statique sont-elles la somme des maxima de chaque lot ?
4.  Faites varier `--kv-budget` (8192, 32768, 65536) : à partir de quelle taille la pagination ne change-t-elle plus rien, et pourquoi des préemptions apparaissent-elles à 8 192 ?
5.  Resserrez le SLO avec `python3 sim.py --sweep --tpot-slo-ms 6` : quelle contrainte devient active, et que devient le goodput ?

**Critère de réussite.** `verify.sh` s'arrête avec le code 0 et affiche « OK batching-sim » : 11 tests passent, et le lot continu termine les 64 requêtes en moins d'itérations que le lot statique (1 889 contre 4 967 à mémoire réservée égale). La sortie est identique d'une exécution et d'une machine à l'autre.

**Pour aller plus loin.** Ajoutez un cache de préfixes : des groupes de $G$ requêtes qui partagent leur prompt, routées au hasard ou par prompt entre deux moteurs, et comparez les jetons de prefill. Ajoutez un prefill découpé et mesurez son effet sur le TPOT p95.
:::

## Exercices {#ex}

::: exo
[Exercice 1 · ★ — Combien de tâches en parallèle ?]{.tag} Un nœud déclare 8 CPU et 2 GPU logiques. On crée deux acteurs `@ray.remote(num_gpus=1)` sans autre option, puis on soumet beaucoup de tâches de 1 CPU. (a) Combien de tâches s'exécutent en parallèle ? (b) Même question si les acteurs sont créés avec `num_gpus=1, num_cpus=0`. (c) Les CPU sont-ils réservés physiquement ?
:::

::: sol
(a) Six. Dès qu'une ressource est demandée explicitement, les acteurs exigent leur CPU par défaut au placement comme à l'exécution : chacun en retient un, et $8 - 2 = 6$ CPU restent libres. (b) Huit, puisque les acteurs ne retiennent plus de CPU. (c) Non : les ressources sont logiques, et Ray n'isole pas les CPU. `resources_demo.py` (lab 11.1) l'a exécuté : « free CPU = 6 of 8 » puis « free CPU = 8 of 8 ».
:::

::: exo
[Exercice 2 · ★ — Lire une demande en attente]{.tag} Voici un extrait de `ray status` d'un cluster **fictif** à autoscaler, dont les nœuds de travail ont 4 GPU chacun et dont le groupe peut grandir jusqu'à 3 nœuds.

~~~text
Total Usage:
 30.0/32.0 CPU
 4.0/4.0 GPU
Pending Demands:
 {'CPU': 1.0, 'GPU': 1.0}: 3+ pending tasks/actors
 {'CPU': 1.0, 'GPU': 8.0}: 1+ pending tasks/actors
~~~

Dites pourquoi chaque demande attend et ce que fera l'autoscaler.
:::

::: sol
Les quatre GPU sont occupés (4,0/4,0) : les trois acteurs à 1 GPU attendent. L'autoscaler peut ajouter un nœud à 4 GPU, ce qui les débloque, tant que `maxReplicas` n'est pas atteint. La demande à 8 GPU, elle, ne sera jamais satisfaite : une tâche ou un acteur doit tenir sur un seul nœud, et aucun type de nœud n'en offre 8. L'autoscaler n'ajoutera rien pour elle. Il faut changer la demande : 4 GPU par acteur, ou un placement group de deux bundles de 4 GPU.
:::

::: exo
[Exercice 3 · ★ — Dimensionner un groupe de travailleurs]{.tag} Un `ScalingConfig(num_workers=16, use_gpu=True, resources_per_worker={"CPU": 8, "GPU": 1})` de Ray Train (configuration d'exercice, non exécutée : elle demande des GPU) doit tourner sur des nœuds de 8 GPU et 64 CPU. Combien de nœuds faut-il ? Et si les nœuds n'ont que 48 CPU ? Quelle fraction des GPU reste alors inutilisée ?
:::

::: sol
Avec 64 CPU, un nœud porte $\min(8, \lfloor 64/8 \rfloor) = 8$ travailleurs : $16/8 = 2$ nœuds, tous les GPU servent. Avec 48 CPU, un nœud n'en porte que $\lfloor 48/8 \rfloor = 6$ : il faut $\lceil 16/6 \rceil = 3$ nœuds, soit 24 GPU pour 16 utilisés. Huit GPU, soit un tiers, restent inutilisés : les CPU, pas les GPU, bornent le placement. La stratégie par défaut est `PACK` : Ray remplit un nœud avant d'en ouvrir un autre.

Ce calcul suppose que le coordinateur de Ray Train ne retient aucun CPU de plus ; la page de `ScalingConfig` lue pour ce module ne le précise pas, donc vérifiez `trainer_resources` avant de dimensionner pour de bon.
:::

::: exo
[Exercice 4 · ★ — Avantages d'un groupe GRPO]{.tag} Un groupe de $G = 6$ sorties reçoit les récompenses 1, 1, 0, 0, 0, 0. Calculez l'avantage de chaque sortie avec la normalisation par la moyenne et l'écart-type (population) du groupe, vérifiez que la somme des avantages est nulle, et dites ce qui se passe si les six récompenses sont égales.
:::

::: sol
La moyenne vaut $1/3$ et l'écart-type $\sqrt{2/9} = 0{,}4714$. Les deux sorties réussies reçoivent $(1 - 1/3)/0{,}4714 = +1{,}414$, les quatre autres $-0{,}707$. La somme vaut $2 \times 1{,}414 - 4 \times 0{,}707 = 0$. Si les six récompenses sont égales, l'écart-type est nul : il n'y a aucun avantage (en pratique on ajoute un epsilon au dénominateur), donc aucun gradient. Les six générations ont été payées pour rien, ce qui coûte cher quand les réponses sont longues.
:::

::: exo
[Exercice 5 · ★★ — Mémoire de PPO et de GRPO]{.tag} Une politique de 13 milliards de paramètres est entraînée avec un critique de 7 milliards (PPO). La référence est une copie de la politique, évaluée seulement ; le modèle de récompense a 7 milliards de paramètres, évalué seulement. Un modèle entraîné coûte 16 octets par paramètre (2 + 2 + 12), un modèle évalué 2 octets. Calculez la mémoire agrégée de PPO, de GRPO avec le même modèle de récompense, puis de GRPO avec un vérificateur à règles. Combien de GPU de 80 Go au minimum pour l'état seul ?
:::

::: sol
PPO : politique entraînée, critique entraîné, référence et récompense évaluées.

$$13\cdot10^9 \times 16 + 7\cdot10^9 \times 16 + 13\cdot10^9 \times 2 + 7\cdot10^9 \times 2 = 208 + 112 + 26 + 14 = 360\ \text{Go}$$

Il faut donc $\lceil 360/80 \rceil = 5$ GPU.

GRPO supprime le critique (112 Go) : 248 Go, soit 4 GPU. Avec un vérificateur à règles, le modèle de récompense disparaît aussi : 234 Go, soit 3 GPU. Le gain du critique est de 31 %.

Ces totaux excluent les activations et le cache KV, et supposent l'état réparti entre GPU : ils donnent un plancher, pas un plan.
:::

::: exo
[Exercice 6 · ★★ — Une cible d'obsolescence]{.tag} Dans la boucle de l'exemple 6.1 (`m=200`, `t_roll=2.0`, `t_sync=0.2`, `b=4`, `s_L=1.0`, capacité 800 pas/s), 24 acteurs tournent avec une file de capacité 8 en mode « bloquer ». (a) Quelle obsolescence moyenne attendez-vous ? (b) L'algorithme tolère 3 mises à jour de retard. Quel nombre de crédits $K$ choisissez-vous et que devient le débit ? (c) Et pour une cible de 3,5 ?
:::

::: sol
(a) $(N + Q)/b = (24 + 8)/4 = 8$ mises à jour (la simulation en donne 8,00). (b) L'obsolescence avec crédits vaut $K/b$ : $K = 3 \times 4 = 12$. La table de `report.py` (balayage de $K$ à $N=24$) donne alors un débit de 772 pas/s, soit 96,5 % de 800 : la cible coûte 3,5 % de débit. (c) $K = 14$ donne une obsolescence de 3,5 pour 799 pas/s, soit 99,9 % sur cette graine : la cible de 3,5 est presque gratuite. On voit que la cible 3 est un peu en dessous du point où la boucle est saturée.
:::

::: exo
[Exercice 7 · ★★ — Lire les compteurs d'une boucle]{.tag} Voici deux relevés d'une boucle **simulée** (sortie de `python3 make_log.py`, lab 11.3 ; boucle illustrative, durées lognormales).

~~~text
# m=256 steps/traj  b=4 traj/update  queue capacity=16  policy=block
N=16  steps/s=  1279  learner_busy=0.62  queue_len_mean=  1.7/16  actors_blocked_mean=  0.0  lag_mean= 4.38  lag_p95=   7
N=32  steps/s=  2049  learner_busy=1.00  queue_len_mean= 15.9/16  actors_blocked_mean=  6.4  lag_mean=11.98  lag_p95=  15
~~~

Pour chaque ligne, dites si la boucle est limitée par les acteurs ou par l'apprenant. Estimez la capacité $C$ de l'apprenant et le nombre $N^\star$. Quelle obsolescence moyenne attend-on pour $N=32$ ? Que coûte de la ramener à 6 ?
:::

::: sol
$N=16$ : apprenant occupé à 62 %, file presque vide, aucun acteur bloqué : la boucle est limitée par les acteurs ; le débit de 1 279 pas/s est la production $P = 16 \times 256/3{,}2 = 1\,280$ (soit 80 pas/s par acteur, pour un cycle de 3,2 s). $N=32$ : apprenant à 100 %, file pleine (15,9 sur 16), 6,4 acteurs bloqués : limitée par l'apprenant ; le débit de 2 049 pas/s est la capacité $C = 4 \times 256/0{,}5 = 2\,048$.

Le point de saturation vaut $N^\star = 2\,048/80 = 25{,}6$, soit 26 acteurs ; les 6,4 acteurs bloqués sont les $32 - 25{,}6$ en trop. L'obsolescence attendue est $(N+Q)/b = (32+16)/4 = 12$, mesurée 11,98.

Pour la ramener à 6, il faut des crédits $K = 24$, puisque l'obsolescence vaut $K/b$. La commande suivante balaie $K$ :

~~~bash
python3 sweep.py --m 256 --t-roll 3.0 --t-sync 0.2 --b 4 --s-l 0.5 \
    --queue-cap 16 --n 28 32 --credits 16 24 32 --horizon 3000 --seed 7
~~~

Pour 32 acteurs, $K = 24$ donne 0,839 de la capacité (16 % perdus) et $K = 16$ donne 0,561 (obsolescence 4, 44 % perdus). Le meilleur compromis est $K = 32$ : obsolescence 8,0 pour 0,987 de la capacité. Passer de 32 à 28 acteurs en mode « bloquer » ne change presque rien (10,8 pour 1,005).
:::

::: exo
[Exercice 8 · ★★ — Acteurs, taux de rejeu et âge du tampon]{.tag} Une boucle a 128 pas par trajectoire, un rollout de 1,5 s, une lecture des poids de 0,1 s, 8 trajectoires par mise à jour et une mise à jour de 0,8 s (`m=128`, `t_roll=1.5`, `t_sync=0.1`, `b=8`, `s_L=0.8`). (a) Calculez la capacité $C$ et $N^\star$. (b) Avec un taux de rejeu $R = 2$, combien d'acteurs suffisent ? (c) Avec 12 acteurs et $R=1$, quelle est l'utilisation de l'apprenant ? (d) Un tampon FIFO de 64 trajectoires : quel âge moyen en mises à jour pour $R = 1$ et $R = 2$ ?
:::

::: sol
(a) $C = 8 \times 128/0{,}8 = 1\,280$ pas/s et $N^\star = 1\,280 \times 1{,}6/128 = 16$ acteurs.

(b) Avec $R = 2$, la capacité en données fraîches est $C/R = 640$ pas/s, donc $N^\star = 8$ acteurs (`plan.py --replay-ratio 2` répond 8).

(c) 12 acteurs produisent $12 \times 128/1{,}6 = 960$ pas/s : l'apprenant est utilisé à 75 %, ce qui autoriserait un taux de rejeu de $1\,280/960 = 1{,}33$.

(d) Le flux frais vaut $f = b/R$. Pour $R=1$, $f = 8$ et l'âge vaut $(64/2)/8 = 4$ ; pour $R=2$, $f = 4$ et l'âge vaut 8. Réutiliser deux fois économise la moitié des acteurs, au prix d'un âge doublé.
:::

::: exo
[Exercice 9 · ★★★ — GPU de rollout : cher et rapide, ou bon marché et lent ?]{.tag} Boucle de l'exemple 6.1 ($C = 800$ pas/s), apprenant à 30 unités par heure (unités **fictives**). Le type A met 2,0 s par rollout pour 4,0 unités par heure et par acteur ; le type B met 3,4 s pour 1,9. (a) Dimensionnez chaque pool et calculez le coût par million de pas. (b) Quel prix du type B ferait l'égalité ? (c) Que devient l'avantage si l'apprenant coûte 60 unités ? (d) Quelle obsolescence « bloquer » ($Q=8$) pour chaque type ?
:::

::: sol
(a) A : $N^\star = 800 \times 2{,}2/200 = 8{,}8$, soit 9 acteurs ; $9 \times 4{,}0 + 30 = 66$ unités par heure ; coût $66/(3600 \times 800) \times 10^6 = 22{,}92$ par million de pas. B : $N^\star = 800 \times 3{,}6/200 = 14{,}4$, soit 15 acteurs ; $15 \times 1{,}9 + 30 = 58{,}5$ ; coût 20,31. B est moins cher de 11,4 %.

(b) À débit égal, on compare les pools : $9 \times 4{,}0 = 15\,p_B$ donne $p_B = 2{,}4$ unités. (c) Avec 60 unités pour l'apprenant : A coûte 33,33 et B 30,73 ; l'avantage de B tombe à 7,8 % : un coût fixe élevé dilue l'écart entre pools. (d) $(N+Q)/b$ donne $(9+8)/4 = 4{,}25$ pour A et $(15+8)/4 = 5{,}75$ pour B. Le type B coûte 1,5 mise à jour de retard de plus. Si l'algorithme tolère 5, choisissez A ; s'il tolère 6, B économise 11 %. Vérifiez avec `plan.py --t-roll 3.4 --actor-price-h 1.9 --learner-price-h 30`.
:::

::: exo
[Exercice 10 · ★★★ — Des lignes en double après une panne]{.tag} Une équipe constate que chaque panne de nœud duplique des lignes dans sa table de sortie. Son acteur `Writer` est déclaré avec `max_restarts=-1` et `max_task_retries=-1`, et sa méthode `write(row)` ajoute une ligne à un fichier. Le journal du raylet contient, à chaque panne, une ligne comme celle-ci (réelle, produite par le lab 11.1) :

~~~text
Task Counter.work failed. There are infinite retries remaining, so the task will be retried. Error: The actor is temporarily unavailable: RpcError: RPC error: Socket closed rpc_code: 14
~~~

Diagnostiquez, proposez deux corrections, et décrivez un test qui prouve la correction.
:::

::: sol
Le diagnostic est la sémantique « au moins une fois » : avec `max_task_retries=-1`, l'appel interrompu par la panne est rejoué sur l'acteur redémarré, et son effet de bord a déjà eu lieu en partie. Le lab 11.1 le reproduit : avec `max_task_retries=-1`, le résultat est 7 et le journal contient `['7', '7']`. Avec `0`, l'appel est perdu (`RayActorError`) mais ne s'exécute qu'une fois.

Première correction : rendre `write` idempotent, en écrivant sous une clé déterministe (l'identifiant de la trajectoire, pas un compteur), par écriture temporaire puis renommage. Un rejeu réécrit alors le même contenu au même endroit. Seconde correction : `max_task_retries=0` et un rejeu piloté par l'appelant, qui connaît les identifiants à écrire et déduplique à la relecture.

Test : reprendre `fault.Counter.work`, tuer le processus une fois, et vérifier qu'après correction le journal contient exactement une entrée par identifiant. Le test de non-régression est celui de `test_actor_task_semantics_at_most_once_vs_at_least_once`.
:::

::: exo
[Exercice 11 · ★★★ — Concevoir la boucle d'un post-entraînement]{.tag} Un post-entraînement génère des trajectoires de $m = 4096$ jetons en 120 s en moyenne par réplica de génération, qui produit une séquence à la fois : un réplica est un acteur du modèle du chapitre 6. L'apprenant traite $b = 64$ trajectoires en 90 s. Les poids (14 Go) sont diffusés en arbre binomial vers 4 nœuds de génération sur un lien de 25 Go/s, $\alpha = 1$ ms.

Cible : obsolescence moyenne d'au plus 3,2 mises à jour, perte de débit d'au plus 3 %. Dimensionnez $N$ et $K$ avec le simulateur (durées lognormales, coefficient de variation 0,3, file de 128) et justifiez. La topologie de diffusion change-t-elle $N^\star$ ?
:::

::: sol
Diffusion : un arbre binomial sur 4 nœuds fait $\lceil \log_2 5 \rceil = 3$ tours de $0{,}001 + 14/25 = 0{,}561$ s, soit $t_{\text{sync}} = 1{,}683$ s (2,241 s en étoile). C'est la durée de la diffusion entière, celle que voit le dernier nœud servi : la prendre pour chaque acteur est une borne haute. Capacité : $C = 64 \times 4096/90 = 2\,913$ jetons/s. $N^\star = 2\,913 \times 121{,}68/4096 = 86{,}5$ ; avec l'étoile, 86,9 : 87 dans les deux cas, la topologie ne change rien, car 2 s pèsent peu devant 120 s.

Au plus juste (87 acteurs), le bruit des durées fait perdre du débit. Le balayage ci-dessous (graine 2) donne :

-   87 acteurs : sans crédit (« bloquer »), 0,970 de la capacité et une obsolescence de 3,01 ; $K = 192$, 0,975 et 2,69 ;
-   104 acteurs ($1{,}2\,N^\star$) : sans crédit, 0,983 et 3,61 ; $K = 128$, 0,918 et 2,00 ; $K = 192$, 1,002 et 2,99.

~~~bash
python3 sweep.py --m 4096 --t-roll 120 --t-sync 1.683 --b 64 --s-l 90 \
    --queue-cap 128 --n 87 104 --credits 128 192 --horizon 60000 --seed 2
~~~

Avec 87 acteurs et $K = 192$, les deux cibles tiennent sur cette graine, de justesse : sur les graines 1 à 5, le débit varie de 0,960 à 0,975 et la perte dépasse 3 % dans trois cas sur cinq. Avec 104 acteurs et $K = 192$, il varie de 0,978 à 1,015 (perte d'au plus 2,2 %) et l'obsolescence reste à 2,99. Sans crédit, 104 acteurs dépassent la cible d'obsolescence (3,61).

Choix : $N = 104$ et $K = 192 = 3\,b$. $K = 128$ perdrait 8 %. Sur 4 nœuds, 104 réplicas font 26 séquences simultanées par nœud, qu'un moteur en batching continu sert ensemble (chapitre 9). Le prix est 17 acteurs de plus que le minimum : si leur coût compte, simulez davantage de graines avant de descendre vers 90 ou 95 acteurs. Pour cette boucle, la règle est de l'ordre de $2{,}2\,N^\star$ crédits, plus que les $1{,}6\,N^\star$ de l'exemple 6.2 : le facteur dépend de $b$.
:::

::: exo
[Exercice 12 · ★★★ — Allocation statique ou autoscaling ?]{.tag} Une charge réclame 32 nœuds CPU de rollouts pendant 20 min chaque heure, rien le reste du temps. Le démarrage d'un nœud prend 3 min (hypothèse), `idleTimeoutSeconds` vaut 60 s. Comparez en nœuds-heures par heure : (A) une allocation statique de 32 nœuds ; (B) un autoscaling pur ; (C) un autoscaling avec `minReplicas = 8`. Donnez aussi la capacité manquante pendant le démarrage, et recommandez selon deux profils de charge.
:::

::: sol
(A) $32 \times 1 = 32$ nœuds-heures par heure.

(B) Chaque nœud est facturé $3 + 20 + 1 = 24$ min, soit 0,4 h : $32 \times 0{,}4 = 12{,}8$, c'est-à-dire 60 % d'économie. Pendant les 3 min de démarrage, il manque 32 nœuds : $32 \times 3/60 = 1{,}6$ nœud-heure de capacité par vague.

(C) 8 nœuds toujours présents (8 nœuds-heures) et 24 démarrés à la demande ($24 \times 0{,}4 = 9{,}6$) : 17,6, soit 45 % d'économie. Il manque $24 \times 3/60 = 1{,}2$ nœud-heure par vague, et 25 % de la capacité est disponible dès la première seconde.

Recommandation : si le travail peut glisser de quelques minutes (un jeu de rollouts à produire avant une échéance lointaine), (B) économise le plus. Si la boucle doit repartir sans délai (apprenant qui attend les données), (C) paie 4,8 nœuds-heures de plus pour réduire de 25 % le creux. Toute la décision tient à la valeur de ces 3 minutes. Tous ces chiffres sont des hypothèses d'exemple ; seul `idleTimeoutSeconds` à 60 s est un défaut documenté de KubeRay.
:::

::: exo
[Exercice 13 · ★★ — Servir Qwen3-32B : un GPU ou deux ?]{.tag} Le [`config.json` de Qwen3-32B](https://huggingface.co/Qwen/Qwen3-32B/blob/main/config.json) (lu le 2026-10-25) donne 64 couches, 8 têtes de clés-valeurs, `head_dim` = 128, en `bfloat16` ; on en compte 32,76 milliards de paramètres (la fiche annonce 32,8). Le modèle est servi par vLLM sur des GPU de 80 Go, avec la fraction de mémoire par défaut de 92 %.

(a) Calculez le cache KV par jeton et par séquence de 8 192 jetons. (b) Combien de séquences de 8 192 jetons tiennent sur un seul GPU ? (c) Et en parallélisme tensoriel sur deux GPU, chacun portant la moitié des poids et la moitié des têtes de clés-valeurs ? Comparez par GPU.

(d) Un post-entraînement GRPO envoie des groupes de $G = 16$ réponses, sur des prompts de 1 500 jetons, pour des réponses de 3 000 jetons en moyenne. Combien de groupes complets tiennent dans le cache de la configuration (c), avec et sans partage du préfixe ? Quelle part du prefill le partage évite-t-il ?
:::

::: sol
(a) $k = 2 \times 64 \times 8 \times 128 \times 2 = 262\,144$ octets, soit 256 Kio par jeton, et 2,147 Go par séquence de 8 192 jetons. Les poids pèsent $2 \times 32{,}76 = 65{,}5$ Go en BF16.

(b) Il reste $0{,}92 \times 80 - 65{,}5 = 8{,}08$ Go pour le cache, soit 3,76 séquences : **3**.

(c) Chaque GPU porte 32,76 Go de poids et garde $73{,}6 - 32{,}76 = 40{,}84$ Go de cache, à 128 Kio par jeton (4 têtes sur 8). La paire tient $40{,}84 \cdot 10^9 / (8\,192 \times 131\,072) = 38{,}03$, soit **38** séquences : 19 par GPU contre 3, soit 6,3 fois plus. Le second GPU ne double pas seulement la mémoire : il libère la place des poids.

(d) Sans partage, un groupe occupe $16 \times 4\,500 \times 256$ Kio = 18,87 Go ; avec partage, $(1\,500 + 16 \times 3\,000) \times 256$ Kio = 12,98 Go, soit 31,25 % de moins. Dans les $2 \times 40{,}84 = 81{,}7$ Go de la paire tiennent **4** groupes sans partage et **6** avec. Le prefill passe de 24 000 à 1 500 jetons par groupe : 93,8 % évités, si les 16 requêtes arrivent sur ce moteur.

Ces calculs ignorent les activations, les graphes CUDA et les tampons de communication : un démarrage réel donne le vrai nombre de blocs.
:::

::: exo
[Exercice 14 · ★★★ — Une flotte partagée entre service et rollouts]{.tag} Une flotte de 32 GPU sert Qwen3-8B en ligne, un réplica par GPU, et prête le reste à des rollouts. Supposez qu'une mesure réelle confirme le goodput du lab 11.4 : 16 requêtes par seconde par réplica sous le SLO (TTFT de 500 ms, TPOT de 20 ms). Le trafic, **fictif**, vaut 200 requêtes par seconde pendant 10 h et 40 le reste de la journée ; au matin, il monte de 30 requêtes par seconde chaque minute.

Un réplica neuf lit 16,38 Go de poids à 2 Go/s, puis s'initialise en 60 s (hypothèse). Un matin, avant que l'autoscaler ne réagisse, le tableau de bord (fictif) d'un réplica affiche :

~~~text
vllm:num_requests_running                     47
vllm:num_requests_waiting                     38
vllm:kv_cache_usage_perc                      0.99
rate(vllm:num_preemptions)                    3.1 /s
p95 of vllm:time_to_first_token_seconds       2.4 s
DCGM_FI_DEV_GPU_UTIL                          100
~~~

(a) Diagnostiquez. Quel signal d'autoscaling aurait dû agir ? Augmenter `--max-num-seqs` aide-t-il ? (b) Combien de réplicas chauds faut-il au-delà du besoin pour absorber la montée pendant un démarrage ? Combien de réplicas au pic et au creux ? (c) Combien de GPU-heures par jour reviennent aux rollouts, contre une allocation fixe dimensionnée pour le pic ? (d) Quand le service reprend des GPU, quel ordre de préemption proposez-vous, et comment bornez-vous le travail perdu ?
:::

::: sol
(a) Le cache KV est plein (0,99) avec 47 séquences, le plafond de l'exemple 9.1 pour des contextes longs. 38 requêtes attendent, et le moteur évince des séquences qu'il devra recalculer : le TTFT p95 de 2,4 s vaut 4,8 fois l'objectif. L'utilisation du GPU à 100 % ne dit rien, elle y était déjà à faible charge (section 9.6). Le signal utile est `vllm:num_requests_waiting` durablement positif, ou `vllm:kv_cache_usage_perc` au-dessus d'un seuil (0,9 par exemple).

Augmenter `--max-num-seqs` n'aide pas : la limite est le cache, pas le nombre de places, et l'on ajouterait des préemptions ; le [guide d'optimisation](https://docs.vllm.ai/en/latest/configuration/optimization.html) conseille au contraire de le réduire contre les préemptions. Les leviers sont un cache FP8 (deux fois plus de séquences, si la qualité tient) et, surtout, un réplica de plus.

(b) Un démarrage dure $16{,}38/2 + 60 = 68{,}2$ s. Le trafic gagne pendant ce temps $0{,}5 \times 68{,}2 = 34{,}1$ requêtes par seconde, soit 2,1 réplicas : il en faut **3** chauds en réserve. Au pic, $200/16 = 12{,}5$ donne 13 réplicas, plus 3 : **16**. Au creux, $40/16 = 2{,}5$ donne 3, plus 3 : **6**.

(c) Avec l'autoscaling, les rollouts reçoivent $(32 - 16) \times 10 + (32 - 6) \times 14 = 160 + 364 = 524$ GPU-heures par jour. Une allocation fixe pour le pic n'a pas besoin de réserve de démarrage : 13 réplicas, qui laissent $19 \times 24 = 456$ GPU-heures aux rollouts. L'autoscaling leur en rend 68 de plus par jour (15 %). Les GPU du service servent alors en moyenne 66 % de leur goodput, contre 51 % en allocation fixe ; l'écart avec 100 % est le prix des réplicas chauds et des creux.

(d) Le service passe en premier : il a un SLO, et Kueue l'exprime par une priorité de charge (module 12). Viennent ensuite les rollouts, qu'on préempte au bord d'une trajectoire. Avec, par hypothèse, $K = 64$ crédits et des trajectoires de 120 s par réplica (comme à l'exercice 11), une préemption perd au plus 64 trajectoires, soit 2,1 heures-réplica de génération. L'apprenant passe en dernier : préempté, il repart d'un checkpoint et bloque toute la boucle (module 10).

Mettez le moteur de rollouts en veille de niveau 1 plutôt que de le détruire. À son retour, il recopie ses poids depuis la mémoire CPU, 0,66 s à 25 Go/s (hypothèse), au lieu des 68 s d'un démarrage à froid. Toutes les valeurs de trafic et de durée sont des hypothèses d'exemple.
:::

## Bilan de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux dire quand utiliser Ray et quand ne pas l'utiliser.** Preuve : un tableau de trois charges de votre choix, avec la forme de chacune et le choix motivé (exemple 8.2).
-   **Je peux prédire l'efficacité d'une tâche et choisir sa granularité.** Preuve : le $o$ mesuré au lab 11.1 et la prédiction de $E(d)$ à trois tailles.
-   **Je peux dire ce qui survit à une panne.** Preuve : le tableau de l'exemple 2.3 refait avec vos réglages, et un appel d'acteur rendu idempotent (exercice 10).
-   **Je peux mesurer l'obsolescence d'une boucle.** Preuve : la table A du lab 11.2, identique à chaque exécution, et la partie B comparée à $N/b$.
-   **Je peux dimensionner acteurs et crédits.** Preuve : une note de dimensionnement d'une boucle en ligne, qui donne `plan.py` et `sweep.py` sur votre boucle et l'arbitrage chiffré entre obsolescence et débit (exercices 6, 8, 11).
-   **Je peux comparer deux types de nœuds au coût par million de pas.** Preuve : l'exercice 9 refait avec les prix lus sur une page fournisseur le jour même.
-   **Je peux dimensionner un moteur d'inférence.** Preuve : le cache KV d'un modèle dont vous avez lu le `config.json`, le nombre de séquences qui tiennent sur un GPU, et un goodput sous SLO tiré du lab 11.4 (exemples 9.1 et 9.5, exercices 13 et 14).

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Nos acteurs de rollout sont à 40 % d'utilisation et l'apprenant à 100 %. Que faites-vous ?* Réponse-type : la boucle est limitée par l'apprenant, donc ajouter des acteurs ne sert à rien ; calculer $N^\star$ et retirer l'excédent ; borner ce qui circule par des crédits pour limiter l'obsolescence ; accélérer l'apprenant seulement si la mesure montre qu'il est le goulot.
2.  *Un acteur Ray redémarre et le job continue, mais les résultats sont faux. Où cherchez-vous ?* Réponse-type : l'état de l'acteur est perdu au redémarrage (`max_restarts` ne restaure rien) ; un appel rejoué (`max_task_retries`) peut dupliquer un effet de bord ; vérifier les checkpoints et l'idempotence, et comparer les compteurs avant et après la panne.
3.  *Pourquoi ne pas lancer toute la boucle de renforcement comme un gros job Slurm ?* Réponse-type : on le peut (`ray symmetric-run`), au prix d'une allocation statique sans autoscaling et d'un cluster Ray lié à la durée du job ; Kubernetes avec KubeRay apporte l'autoscaling et, avec un Redis externe, la tolérance aux pannes de la tête, au prix d'un autre opérateur à exploiter ; le choix dépend de l'existant et de la forme de la charge.

## Lectures et références {#refs}

-   Moritz, Nishihara, Wang, Tumanov, Liaw, Liang, Elibol, Yang, Paul, Jordan, Stoica. *Ray: A Distributed Framework for Emerging AI Applications*. OSDI 2018. [arXiv:1712.05889](https://arxiv.org/abs/1712.05889) : le modèle tâches-acteurs et le tableau 2 (chapitre 1). L'architecture décrite (ordonnanceur global) a évolué depuis.
-   Espeholt et al. *IMPALA: Scalable Distributed Deep-RL with Importance Weighted Actor-Learner Architectures*. 2018. [arXiv:1802.01561](https://arxiv.org/abs/1802.01561) : figure 1, politique en retard et V-trace (chapitre 5).
-   Horgan et al. *Distributed Prioritized Experience Replay* (Ape-X). 2018. [arXiv:1803.00933](https://arxiv.org/abs/1803.00933) : tampon de rejeu partagé (chapitre 5).
-   Schulman, Wolski, Dhariwal, Radford, Klimov. *Proximal Policy Optimization Algorithms*. 2017. [arXiv:1707.06347](https://arxiv.org/abs/1707.06347) : objectif borné et algorithme à $N$ acteurs (chapitre 4).
-   Shao et al. *DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models*. 2024. [arXiv:2402.03300](https://arxiv.org/abs/2402.03300) : section 4.1, GRPO (chapitre 4).
-   Hu et al. *OpenRLHF: An Easy-to-use, Scalable and High-performance RLHF Framework*. 2024 (version 6, octobre 2025, relue). [arXiv:2405.11143](https://arxiv.org/abs/2405.11143) : rôles de GPU et génération asynchrone, sections 1 et 3.1 (chapitres 4 et 5).
-   Sheng et al. *HybridFlow: A Flexible and Efficient RLHF Framework*. 2024. [arXiv:2409.19256](https://arxiv.org/abs/2409.19256) : contrôleur unique et multiple, redécoupage des poids (chapitre 4).
-   Ray. [*Resources*](https://docs.ray.io/en/latest/ray-core/scheduling/resources.html), [*Placement Groups*](https://docs.ray.io/en/latest/ray-core/scheduling/placement-group.html), [*Memory management*](https://docs.ray.io/en/latest/ray-core/scheduling/memory-management.html), [*Out-of-memory prevention*](https://docs.ray.io/en/latest/ray-core/scheduling/ray-oom-prevention.html), puis [*Task*](https://docs.ray.io/en/latest/ray-core/fault_tolerance/tasks.html), [*Actor*](https://docs.ray.io/en/latest/ray-core/fault_tolerance/actors.html), [*Object*](https://docs.ray.io/en/latest/ray-core/fault_tolerance/objects.html) et [*GCS fault tolerance*](https://docs.ray.io/en/latest/ray-core/fault_tolerance/gcs.html) : ressources logiques, groupes, magasin d'objets, moniteur de mémoire, réglages et limites de reprise (chapitres 1 et 2).
-   Ray. [*Ray Data internals*](https://docs.ray.io/en/latest/data/data-internals.html), [*Dataset.map_batches*](https://docs.ray.io/en/latest/data/api/doc/ray.data.Dataset.map_batches.html) et [*Ray Train fault tolerance*](https://docs.ray.io/en/latest/train/user-guides/fault-tolerance.html) : blocs, flux, contre-pression, reprises (chapitre 3).
-   Ray. [*KubeRay autoscaling*](https://docs.ray.io/en/latest/cluster/kubernetes/user-guides/configuring-autoscaling.html), [*README de KubeRay*](https://raw.githubusercontent.com/ray-project/kuberay/master/README.md) et [*Deploying on Slurm*](https://docs.ray.io/en/latest/cluster/vms/user-guides/community/slurm.html) : `RayCluster`, `RayJob`, `RayService`, autoscaler, `ray symmetric-run` (chapitre 8).
-   Ray. [*Metrics*](https://docs.ray.io/en/latest/cluster/metrics.html), [*System metrics*](https://docs.ray.io/en/latest/ray-observability/reference/system-metrics.html) et [*State API et CLI*](https://docs.ray.io/en/latest/ray-observability/user-guides/cli-sdk.html) : export Prometheus, noms de métriques (chapitre 8).
-   [*Dask*](https://docs.dask.org/en/stable/), [*Apache Spark*](https://spark.apache.org/docs/latest/) et [*Kubeflow Trainer*](https://www.kubeflow.org/docs/components/trainer/overview/) : pages d'accueil des alternatives (chapitre 8).
-   Kwon, Li, Zhuang, Sheng, Zheng, Yu, Gonzalez, Zhang, Stoica. *Efficient Memory Management for Large Language Model Serving with PagedAttention*. SOSP 2023. [arXiv:2309.06180](https://arxiv.org/abs/2309.06180) : sections 2 et 3 pour prefill, decode et taille du cache KV, section 4 pour les blocs (chapitre 9).
-   Zhong, Liu, Chen, Hu, Zhu, Liu, Jin, Zhang. *DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving*. OSDI 2024. [arXiv:2401.09670](https://arxiv.org/abs/2401.09670) : TTFT, TPOT, goodput par GPU et séparation des phases (chapitre 9).
-   vLLM. [*Engine arguments*](https://docs.vllm.ai/en/latest/configuration/engine_args.html), [*Metrics*](https://docs.vllm.ai/en/latest/usage/metrics.html), [*Automatic prefix caching*](https://docs.vllm.ai/en/latest/design/prefix_caching.html), [*Disaggregated prefilling*](https://docs.vllm.ai/en/latest/features/disagg_prefill.html), [*Optimization and Tuning*](https://docs.vllm.ai/en/latest/configuration/optimization.html) et [*Sleep mode*](https://docs.vllm.ai/en/latest/features/sleep_mode.html), lus le 2026-10-25 : réglages par défaut, métriques et mécanismes actuels (chapitre 9).

## Sources et portée {#sources}

### Documenté {#documente}

Les faits attribués à la documentation de Ray (ressources logiques et valeurs par défaut, placement groups, magasin d'objets à 30 %, moniteur de mémoire à 95 % et 250 ms, réglages de reprise, GCS, blocs de 1 à 128 Mio, flux et contre-pression, `FailureConfig`, autoscaler et `idleTimeoutSeconds` à 60 s, `ray symmetric-run` depuis Ray 2.49, export Prometheus) ont été relus sur docs.ray.io le 25 octobre 2026. Les faits sur Ray (tableau 2, 1,8 million de tâches par seconde), IMPALA (file de trajectoires, « policy-lag », V-trace, 250 000 images par seconde), PPO, GRPO, OpenRLHF, HybridFlow et Ape-X ont été relus dans le texte des articles. Les descriptions de Dask, Spark et Kubeflow Trainer viennent de leurs pages d'accueil. Tous les comportements décrits comme observés ont été reproduits avec Ray 2.59.0 dans le bac à sable ; les sorties citées en viennent. Les tableaux du modèle viennent de `report.py`, `plan.py`, `sweep.py` et `make_log.py`, relancés avant la dernière édition. Pour le chapitre 9, ont été relus le 25 octobre 2026 : les résumés et le texte de PagedAttention (phases, 800 Ko par jeton pour OPT-13B, 20,4 % à 38,2 %, gain de 2 à 4), de DistServe (TTFT, TPOT, goodput, 7,4 et 12,6), d'Orca (36,9) et de SGLang ; la documentation stable de vLLM (version 0.32.0 sur PyPI ce jour-là : 0,92 par défaut, FP8, prefill découpé, politiques d'ordonnancement, métriques, cache de préfixes, séparation expérimentale, mode veille) ; le guide d'autoscaling de Ray Serve ; la page HPA de Kubernetes ; les `config.json` et fiches de Qwen3-8B et Qwen3-32B ; la page produit du H100 (80 Go, 3,35 To/s, NVLink 900 Go/s) et le blog Hopper (900 Go/s de bande passante totale) ; les offres du relevé qui citent vLLM, SGLang ou le cache de préfixes (`data/jobs/`). Les sorties du lab 11.4 viennent de `sim.py`, exécuté deux fois à l'identique.

### Recommandé {#recommande}

L'ordre des chapitres, le critère « forme de la charge » du chapitre 1 et du tableau 8.4, la règle de crédits $K \approx 1{,}6\,N^\star$ de l'exemple 6.2 (valable pour cette boucle seulement), les trois jauges de boucle du chapitre 8 et le calcul du coût par million de pas sont des choix de ce parcours, pas des règles de Ray. Les prix, les unités de coût, les durées de démarrage et les tailles de boucle des exemples et des exercices sont **fictifs** : lisez la page de prix de votre fournisseur le jour même. Au chapitre 9, le routage par prompt, le choix des signaux d'autoscaling, la règle des réplicas chauds, l'ordre de préemption (service, rollouts, apprenant) et le modèle d'itération du lab 11.4 sont des choix de ce parcours ; le trafic et les débits de stockage y sont des hypothèses.

### À vérifier {#a-verifier}

(1) L'article de Ray décrit un ordonnanceur global et des ordonnanceurs locaux (2018) ; l'architecture actuelle a évolué et sa description n'a pas été relue pour ce module. (2) La documentation affiche, sur Ray 2.59, un bandeau annonçant l'authentification par jeton activée par défaut pour les clusters locaux et étendue à tous les clusters en 2.61 ; les labs tournent sans changement sur 2.59.0, mais ce changement n'a pas été étudié. (3) `deploy/raycluster.yaml` n'est pas validé contre le schéma de la CRD KubeRay, ni appliqué ; `deploy/ray_slurm.sbatch` est linté, pas exécuté. (4) Le guide Ray « Gang Scheduling with RayJob and Kueue » et la section « SLURM networking caveats » sont listés dans la documentation et n'ont pas été relus. (5) La correction du lab 11.2 n'est pas V-trace : c'est un poids d'importance tronqué sur des retours de Monte-Carlo, et l'effet observé vaut pour ce jouet seulement. (6) Le modèle d'obsolescence est une estimation de champ moyen, qui sous-estime l'obsolescence près de la saturation et la surestime loin d'elle (section 6.5). (7) Les chiffres de débit annoncés par IMPALA, OpenRLHF et HybridFlow n'ont pas été reproduits. (8) Les ressources que le coordinateur de Ray Train retient par défaut ne sont pas établies par la page de `ScalingConfig` lue : l'exercice 3 suppose qu'il n'en retient aucune. (9) Le rejeu infini d'une tâche tuée par le moniteur de mémoire est documenté, mais son interaction avec la garantie « au moins une tâche par appelant et par nœud » n'a pas été observée. (10) Les défauts de vLLM changent d'une version à l'autre : relisez `--gpu-memory-utilization` pour la vôtre. (11) Les nombres de séquences des exemples 9.1 et de l'exercice 13 ignorent activations, graphes CUDA et tampons ; la durée d'initialisation d'un moteur n'a pas été mesurée ; le partage des têtes de clés-valeurs entre deux GPU en parallélisme tensoriel n'a pas été vérifié sur vLLM. (12) Les gains annoncés par PagedAttention, Orca, DistServe et SGLang n'ont pas été reproduits ; aucun moteur n'a tourné sur GPU, et le lab 11.4 donne des bornes, pas des mesures.

### Hors périmètre {#hors-perimetre}

Les algorithmes de renforcement au-delà de PPO et de GRPO (DPO, méthodes hors-ligne), la conception d'une fonction de récompense, l'API de Ray Serve et les plateformes de service (KServe, LeaderWorkerSet), TensorRT-LLM, la quantification des poids, le décodage spéculatif et le service multi-nœuds de grands modèles, l'entraînement sur GPU réel avec Ray (aucun GPU n'était disponible), le réseau d'un cluster multi-nœuds (module 7), le coût financier d'une flotte (module 15) et l'exploitation de KubeRay en production (mise à jour de l'opérateur, sécurité des jetons).
