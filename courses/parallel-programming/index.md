---
title: "Programmation parallèle : OpenMP, MPI et études de passage à l'échelle"
subtitle: "Module 03 · Phase 1 · 30 h"
description: "Mémoire partagée avec OpenMP, passage de messages avec MPI, collectives, halos, reproductibilité numérique et une étude de passage à l'échelle mesurée sur un vrai Open MPI."
module:
  id: parallel-programming
  number: 3
  phase: 1
  hours: 30
  level: 2
prerequisites: [perf-models]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs vérifiés dans un bac à sable", class: verified}
labs:
  - {id: openmp-reduction, kind: sandbox}
  - {id: mpi-ring, kind: sandbox}
  - {id: jacobi-scaling, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** quand un calcul tient sur un cœur, il est simple ; comment le répartir sur quatre cœurs, puis sur quatre machines, sans changer son résultat et en sachant dire pourquoi il n'ira pas quatre fois plus vite ? C'est le noyau commun des formations en calcul haute performance, et c'est aussi le vocabulaire sur lequel se calquent NCCL et les frameworks d'entraînement distribué.

Vous allez écrire et mesurer de petits programmes OpenMP (mémoire partagée) et MPI (passage de messages), puis les assembler dans un solveur de Jacobi dont vous étudierez le passage à l'échelle. Les sorties et les chiffres de ce module viennent d'exécutions réelles sur une VM de 4 cœurs virtuels, avec Open MPI 4.1.6 et GCC 13.3, le 25 octobre 2026 ; les données fictives (exercices 1 et 12) et les paramètres d'exemple sont signalés comme tels. Les chiffres de votre machine seront différents ; la méthode, non.

Le module [Architecture matérielle et modèles de performance](../perf-models/index.html) vous a donné les modèles : Amdahl, Gustafson, α-β, roofline. Ici, vous les confrontez à des mesures et vous apprenez à expliquer l'écart. Le module [Slurm](../slurm/index.html) servira de lanceur pour la dernière partie.

::: key
[Règle de ce module]{.tag} Un programme parallèle correct donne le même résultat que le programme séquentiel, à une tolérance que vous avez choisie et écrite. Vérifiez cela avant de mesurer la moindre durée : un code rapide et faux ne vaut rien.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 30 h, dont environ 12 h de lecture (11,75 h), 12 h de labs (4 h, 4,5 h et 3,5 h), 6 h d'exercices (5,75 h : 15 min par ★, 30 min par ★★, 45 min par ★★★) et 30 min de bilan de sortie |
| Niveau d'entrée | 2 : lecture de C et de Python, ligne de commande Linux, modèles du module précédent |
| Prérequis | [Module 2 — Architecture matérielle et modèles de performance](../perf-models/index.html) |
| Pour qui | Cœur : rang, communicateur, collective et liaison aux cœurs reviennent dans NCCL, dans PyTorch distribué et dans les journaux de Slurm ; survol possible si vous pratiquez déjà MPI. |
| Livrable | une étude de passage à l'échelle reproductible d'un solveur MPI+OpenMP (lab 3.3), un all-reduce en anneau testé (lab 3.2) et un rapport d'une page |
| Environnement | un portable CPU de 4 cœurs ou plus, Linux, GCC, Open MPI et mpi4py ; aucun GPU. La partie facultative sous Slurm demande en plus un conteneur jetable avec accès root |
| Projets liés | [Projet 2 — Étude de passage à l'échelle d'un entraînement](../../projects/scaling-study/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Paralléliser une boucle avec OpenMP en justifiant le partage des variables, la réduction et l'ordonnancement, puis prédire l'effet de ce dernier (chapitre 2).
-   Reconnaître un faux partage dans un code et le corriger, en comptant les lignes de cache concernées (chapitre 2).
-   Écrire un échange MPI sans interblocage, et expliquer pourquoi un programme qui marche avec de petits messages peut se bloquer avec de gros (chapitre 3).
-   Chiffrer le coût d'une collective avec les formules de l'anneau et du doublement récursif, puis les relier à ce que fait NCCL (chapitre 4).
-   Décomposer un domaine, compter les octets de halo et décider si un recouvrement vaut la peine (chapitre 5).
-   Dire quand un résultat doit être identique bit à bit, et comment l'obtenir malgré une addition non associative (chapitre 6).
-   Lancer un job hybride MPI+OpenMP avec le bon placement, avec `mpirun` et sous Slurm (chapitre 7).
-   Mener une étude de passage à l'échelle, fort et faible, avec intervalles de confiance, et expliquer l'écart au modèle (chapitre 8).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 1 — Calcul parallèle et GPU** (semaines 5-9) : écrire, mesurer et expliquer un programme parallèle sur CPU et GPU.
-   **S'appuie sur** : [module 2 — Architecture matérielle et modèles de performance](../perf-models/index.html).
-   **Prépare** : [module 9 — Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline](../distributed-training/index.html).
-   **Projets qui s'en servent** : [Projet 2 — Étude de passage à l'échelle d'un entraînement](../../projects/scaling-study/index.html).
-   **Compétences demandées dans les offres d'emploi et travaillées ici** : Python, Slurm, Expérience HPC, Profilage, bancs d'essai, Langage système (Go, Rust, C++), Collectives (NCCL, RCCL, HCCL), Réseau (général), Systèmes distribués (voir [l'analyse du marché](../../market/index.html#couverture)).
<!-- /gen:place -->

### Plan de séances {#seances}

Onze séances, soit 30 h : sept de 3 h, deux de 2,5 h et deux de 2 h. Le contenu de chaque séance tient dans sa durée : par exemple la séance 1 compte 1 h de chapitre 1, 15 min de positionnement, 1 h de chapitre 2 et 15 min d'exercice. Le niveau ne diminue jamais.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 2.5 h | 1 | ch. 1 Parallélisme et modèles de mémoire ; ch. 2, sections 2.1 à 2.3 (régions, partage, réductions) | Questions de positionnement ; Ex. 1 |
| 2 | 3 h | 1 | ch. 2, sections 2.4 à 2.7 (ordonnancement, faux partage, tâches, ligne de base) | Lab 3.1 partie A ; Ex. 2, 4 |
| 3 | 3 h | 1 | pratique | Lab 3.1 parties B, C et D ; Ex. 3 |
| 4 | 3 h | 2 | ch. 3 MPI, les bases | Lab 3.2 partie B ; Ex. 5 |
| 5 | 3 h | 2 | ch. 4 MPI, les collectives | Lab 3.2 partie A |
| 6 | 3 h | 2 | ch. 5 Décomposition de domaine et halos | Lab 3.2 parties C et D |
| 7 | 3 h | 2 | ch. 6 E/S parallèles et reproductibilité numérique | Ex. 6, 8, 9 |
| 8 | 2.5 h | 3 | ch. 7 Hybride, placement et lancement sous Slurm | Lab 3.3 partie A |
| 9 | 3 h | 3 | ch. 8 Étudier le passage à l'échelle | Lab 3.3 partie B |
| 10 | 2 h | 3 | pratique | Lab 3.3 partie C (la partie D, facultative, est reportée après le module 5) ; Ex. 10, 11 |
| 11 | 2 h | 3 | bilan de sortie | Ex. 7, 12 |

<!-- gen:travailler -->
### Comment travailler ce module {#travailler}

Le parcours s'adresse à plusieurs profils d'entrée, décrits dans le [point de départ](../../profile/index.html). Le tableau donne la priorité conseillée pour ce module ; les questions de positionnement (section 0.1) la confirment ou la corrigent.

| Profil d'entrée | Priorité | Ce que cela veut dire ici |
|---|---|---|
| Ingénieur plateforme, SRE ou DevOps | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Administrateur ou ingénieur HPC | survol guidé | les questions de positionnement, les chapitres signalés ci-dessous, un lab et le checkpoint |
| Ingénieur ML ou chercheur | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Développeur logiciel ou systèmes | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Étudiant ou personne en reconversion | à fond | tous les chapitres, tous les labs et les exercices ★★★ |

**À ne pas survoler.** Si vous survolez, gardez l'étude de passage à l'échelle et la lecture des courbes : le projet 2 la reprend.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le bilan de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si les trois vous paraissent routinières, parcourez les exercices ★★★ et passez au module suivant.

1.  **Compteur partagé.** Deux threads exécutent chacun un million de fois `n++` sur le même entier, sans aucune protection. Quelle valeur finale peut-on observer ?

2.  **Messages croisés.** Deux processus MPI s'envoient mutuellement un message avec `MPI_Send`, puis reçoivent avec `MPI_Recv`. Que se passe-t-il pour 8 octets ? Pour 1 Mio ?

3.  **Efficacité.** Un solveur met 100 s sur un rang et 30 s sur quatre. Quel est le gain, quelle est l'efficacité, et que vous manque-t-il pour dire si c'est bon ?

::: sol
**Réponses.**

1.  Aucune valeur n'est garantie, et surtout pas 2 000 000. L'incrémentation est une lecture, une addition et une écriture : si deux threads lisent la même valeur, une des deux additions est perdue, donc on observe en général moins que le total attendu. Il n'existe pas de borne basse sûre : en C, une course de données est un comportement indéfini. Le lab 3.1 montre une somme de $2^{25}$ éléments qui rend 33 554 432 au lieu de 134 217 723. Voir le chapitre 2.

2.  Le standard MPI ne promet rien : un envoi standard peut être copié dans un tampon (et le programme passe) ou attendre que la réception soit postée (et les deux rangs attendent l'un l'autre). Avec Open MPI 4.1.6 sur une machine, 8 octets passent et 1 Mio se bloque, comme le lab 3.2 le constate. Voir le chapitre 3.

3.  Le gain vaut $100/30 \approx 3{,}33$ et l'efficacité $3{,}33/4 \approx 83\ \%$. Pour juger, il faut un modèle de ce qu'on attendait (Amdahl, coût de communication), la dispersion des mesures, et une ligne de base séquentielle honnête. Voir les chapitres 1 et 8.
:::

## 1. Parallélisme : tâches, données, pipeline, et deux modèles de mémoire {#ch1}

Ce chapitre fixe le vocabulaire et les deux modèles d'exécution qui structurent le reste du module. Il se termine par la lecture d'une vraie machine : combien de cœurs, quels caches, quels domaines mémoire.

### 1.1. Trois formes de parallélisme

Répartir un travail sur plusieurs unités de calcul peut se faire de trois façons, qui se combinent.

-   Le **parallélisme de données** applique la même opération à des morceaux différents des données. Un solveur sur une grille donne un bloc de lignes à chaque processus ; un entraînement en parallélisme de données donne un mini-lot à chaque GPU.
-   Le **parallélisme de tâches** exécute en même temps des opérations différentes, souvent indépendantes : un thread charge le lot suivant pendant que les autres calculent.
-   Le **pipeline** découpe le travail en étapes enchaînées ; chaque étape traite un lot différent au même instant, comme un entraînement dont les couches sont réparties sur plusieurs GPU.

Ce rapprochement avec l'entraînement est une analogie pédagogique, pas une équivalence : les frameworks combinent ces formes de façon plus fine. Il vous aide pourtant à lire un schéma de parallélisme de modèle avec les réflexes du calcul scientifique.

| Forme | Exemple en calcul scientifique | Exemple en entraînement | Ce qui la limite |
|---|---|---|---|
| Données | grille découpée en blocs | un lot par GPU, gradients sommés | l'échange des bords ou des gradients |
| Tâches | chargement pendant le calcul | prétraitement pendant le pas | le nombre de tâches indépendantes |
| Pipeline | étapes d'un traitement en chaîne | couches réparties sur des GPU | les « bulles » quand une étape attend |

### 1.2. Travail, profondeur et bornes

Deux grandeurs décrivent un calcul indépendamment de la machine. Le **travail** $W$ est le nombre total d'opérations. La **profondeur** $T_\infty$ (en anglais *span*) est la longueur de la plus longue chaîne d'opérations dépendantes entre elles : même avec autant de processeurs qu'on veut, on ne peut pas faire mieux, d'où la notation.

Sur $p$ processeurs, le temps est donc au moins $\max(W/p,\ T_\infty)$ en unités d'opération. Un ordonnanceur glouton, qui ne laisse jamais un processeur inactif tant qu'il reste du travail prêt, atteint $W/p + T_\infty$ au plus : cet encadrement de facteur deux suffit pour raisonner.

::: ex
[Exemple 1.1 — Travail et profondeur d'une somme]{.tag} Sommer $n = 2^{25} = 33\,554\,432$ nombres demande $W = n - 1 = 33\,554\,431$ additions. En les regroupant deux par deux, puis les résultats deux par deux, on obtient un arbre de $\log_2 n = 25$ niveaux : la profondeur vaut $T_\infty = 25$ additions.

Le parallélisme disponible, $W/T_\infty \approx 1{,}34$ million, dépasse de loin les 4 cœurs de la machine d'essai : la somme n'est pas limitée par sa structure, mais par la mémoire et par la façon de l'écrire (chapitre 2). À l'inverse, une boucle `s += a[i]` écrite telle quelle a une profondeur de $n-1$ : c'est la structure des dépendances, pas le nombre de cœurs, qui interdit de la paralléliser sans la réécrire en arbre.
:::

### 1.3. Mémoire partagée contre mémoire distribuée

Dans le modèle à **mémoire partagée**, des *threads* (flots d'exécution d'un même processus) voient les mêmes adresses. Ils communiquent en lisant et en écrivant des variables communes, et se synchronisent avec des verrous ou des barrières. OpenMP est l'interface qui en fait une affaire d'annotations sur du code séquentiel.

Dans le modèle à **mémoire distribuée**, des processus ont chacun leur espace d'adressage et ne communiquent que par messages. MPI (*Message Passing Interface*) est la bibliothèque de référence. Un processus MPI est appelé un **rang** (*rank*) : son numéro dans un groupe de processus, le communicateur.

<figure class="fig">
<svg viewBox="0 0 560 260" role="img" aria-labelledby="mem-t mem-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="mem-t">Mémoire partagée et mémoire distribuée</title>
<desc id="mem-d">À gauche, quatre threads accèdent à une même mémoire par lectures et écritures. À droite, quatre processus ont chacun leur mémoire et s'échangent des messages par un réseau.</desc>
<g fill="none" stroke="currentColor" stroke-width="2">
<rect x="20" y="40" width="46" height="34" rx="4"/><rect x="76" y="40" width="46" height="34" rx="4"/><rect x="132" y="40" width="46" height="34" rx="4"/><rect x="188" y="40" width="46" height="34" rx="4"/>
<rect x="20" y="150" width="214" height="52" rx="4" stroke="var(--accent)"/>
<rect x="318" y="40" width="46" height="34" rx="4"/><rect x="376" y="40" width="46" height="34" rx="4"/><rect x="434" y="40" width="46" height="34" rx="4"/><rect x="492" y="40" width="46" height="34" rx="4"/>
<rect x="318" y="110" width="46" height="34" rx="4" stroke="var(--accent)"/><rect x="376" y="110" width="46" height="34" rx="4" stroke="var(--accent)"/><rect x="434" y="110" width="46" height="34" rx="4" stroke="var(--accent)"/><rect x="492" y="110" width="46" height="34" rx="4" stroke="var(--accent)"/>
<line x1="43" y1="74" x2="43" y2="150"/><line x1="99" y1="74" x2="99" y2="150"/><line x1="155" y1="74" x2="155" y2="150"/><line x1="211" y1="74" x2="211" y2="150"/>
<line x1="341" y1="74" x2="341" y2="110"/><line x1="399" y1="74" x2="399" y2="110"/><line x1="457" y1="74" x2="457" y2="110"/><line x1="515" y1="74" x2="515" y2="110"/>
<line x1="341" y1="176" x2="515" y2="176" stroke-dasharray="6 5"/>
<line x1="341" y1="144" x2="341" y2="176" stroke-dasharray="6 5"/><line x1="399" y1="144" x2="399" y2="176" stroke-dasharray="6 5"/><line x1="457" y1="144" x2="457" y2="176" stroke-dasharray="6 5"/><line x1="515" y1="144" x2="515" y2="176" stroke-dasharray="6 5"/>
</g>
<g fill="currentColor" font-size="14" text-anchor="middle">
<text x="43" y="62">T0</text><text x="99" y="62">T1</text><text x="155" y="62">T2</text><text x="211" y="62">T3</text>
<text x="127" y="181">mémoire commune</text>
<text x="341" y="62">P0</text><text x="399" y="62">P1</text><text x="457" y="62">P2</text><text x="515" y="62">P3</text>
<text x="341" y="132">M0</text><text x="399" y="132">M1</text><text x="457" y="132">M2</text><text x="515" y="132">M3</text>
<text x="428" y="198">réseau : messages</text>
<text x="127" y="236" font-weight="700">OpenMP : load et store</text>
<text x="428" y="236" font-weight="700">MPI : send et recv</text>
</g>
</svg>
<figcaption>Deux modèles d'exécution : des threads qui partagent une mémoire (à gauche) et des processus à mémoires privées qui échangent des messages (à droite). Un nœud de calcul est partagé ; un cluster est distribué.</figcaption>
</figure>

| | Mémoire partagée (OpenMP) | Mémoire distribuée (MPI) |
|---|---|---|
| Unité d'exécution | thread | processus, appelé rang |
| Communication | lecture et écriture de variables communes | envoi et réception explicites |
| Erreur typique | course de données : résultat faux, non reproductible | interblocage : le programme attend pour toujours |
| Passage à l'échelle | un nœud (quelques dizaines de cœurs) | plusieurs nœuds, jusqu'à des milliers |
| Coût de communication | quasi nul en apparence, caché dans les caches | latence plus bande passante, mesurables (chapitre 4) |
| Équivalent en entraînement | threads d'un chargeur de données ; noyaux d'un GPU | un processus par GPU et NCCL entre eux |

Les deux modèles se combinent : un rang MPI par nœud ou par socket, des threads OpenMP à l'intérieur. C'est le sujet du chapitre 7.

::: def
[Vocabulaire]{.tag} Un **cœur** est une unité de calcul matérielle. Un **thread** est un flot d'exécution géré par le système ; plusieurs threads d'un même processus partagent sa mémoire. Un **rang** est l'identifiant d'un processus MPI dans un **communicateur**, groupe de processus qui peuvent communiquer. Les mots ne sont pas interchangeables : on lance autant de rangs que de processus, autant de threads que de flots d'exécution par rang.
:::

### 1.4. Deux standards, deux versions à distinguer

OpenMP et MPI sont des spécifications, mises en œuvre par des bibliothèques de versions plus anciennes. La page du consortium OpenMP annonce, lue le 25 octobre 2026, la version 6.0 de novembre 2024 ; celle du MPI Forum annonce MPI 5.0, approuvée le 5 juin 2025.

Ce que vous utiliserez est plus ancien. Le compilateur GCC 13.3 déclare `_OPENMP=201511`, c'est-à-dire OpenMP 4.5. L'Open MPI 4.1.6 du paquet Ubuntu 24.04 annonce, via mpi4py, la version 3.1 du standard (`MPI.Get_version()` rend `(3, 1)`). Lisez donc la spécification récente pour comprendre, et votre bibliothèque pour savoir ce qui marche.

### 1.5. Lire la machine

Avant de paralléliser, regardez ce que la machine offre. Voici la sortie de `lscpu` sur la VM utilisée dans ce module (filtrée).

~~~text
CPU(s):                                  4
Model name:                              Intel(R) Xeon(R) Processor @ 2.80GHz
Thread(s) per core:                      1
Core(s) per socket:                      4
Socket(s):                               1
L1d cache:                               128 KiB (4 instances)
L2 cache:                                4 MiB (4 instances)
L3 cache:                                33 MiB (1 instance)
NUMA node(s):                            1
~~~

::: ex
[Exemple 1.2 — Ce que dit `lscpu`]{.tag} Quatre instances de L1d pour 128 KiB font 32 KiB par cœur ; quatre instances de L2 pour 4 MiB font 1 MiB par cœur ; le L3 de 33 MiB est unique, donc partagé. Chaque cœur a un seul thread matériel et il n'y a qu'un domaine NUMA : tous les cœurs voient la mémoire à la même distance.

Conséquences pratiques : deux threads sur deux cœurs ont des caches L1 et L2 privés, donc une ligne de cache écrite par l'un doit être transférée à l'autre (chapitre 2, faux partage). `getconf LEVEL1_DCACHE_LINESIZE` rend 64 : c'est la taille de la ligne. Et comme il n'y a qu'un domaine NUMA, cette machine **ne peut pas** illustrer les effets de placement de la mémoire d'un serveur à deux sockets ; le chapitre 7 le dit.
:::

La machine n'est pas dédiée : d'autres charges peuvent tourner sur les mêmes cœurs virtuels. Les scripts de ce module n'affirment donc jamais une durée ; ils affirment des résultats, des compteurs et des propriétés de structure. Les durées sont affichées, avec leur dispersion.

::: recap
Points clés — chapitre 1

-   Données, tâches et pipeline sont trois façons de répartir un travail ; elles se combinent.
-   Le travail $W$ et la profondeur $T_\infty$ donnent le temps minimal $\max(W/p,\ T_\infty)$ sur $p$ processeurs.
-   Mémoire partagée : des threads, des courses de données. Mémoire distribuée : des rangs, des interblocages.
-   Les spécifications (OpenMP 6.0, MPI 5.0) sont plus récentes que les bibliothèques que vous utilisez (OpenMP 4.5 pour GCC 13.3, MPI 3.1 pour Open MPI 4.1.6).
-   Lisez la machine (`lscpu`, `getconf`) avant de choisir un schéma : caches privés ou partagés, nombre de domaines NUMA.
:::

## 2. OpenMP : régions parallèles, partage, réductions, ordonnancement, faux partage, tâches {#ch2}

OpenMP ajoute à du C, du C++ ou du Fortran des directives (`#pragma omp ...` en C) qui indiquent au compilateur comment répartir le travail sur des threads. Ce chapitre suit le lab 3.1 (`labs/parallel-programming/openmp-reduction/`) : chaque affirmation est suivie d'une sortie d'un programme que vous pouvez relancer.

### 2.1. Le modèle fork-join

Un programme OpenMP démarre avec un seul thread. À l'entrée d'une **région parallèle** (`#pragma omp parallel`), il crée une équipe de threads qui exécutent tous le même bloc ; à la sortie, une barrière les rassemble et un seul thread continue. La construction `omp for` répartit les itérations d'une boucle entre les threads de l'équipe.

Le nombre de threads vient de la variable d'environnement `OMP_NUM_THREADS`. La spécification 6.0 laisse sa valeur par défaut à l'implémentation ; avec `libgomp`, la bibliothèque de GCC, nous avons observé 4 threads quand la variable n'est pas définie, soit le nombre de processeurs de la machine. Lancez toujours vos mesures avec cette variable écrite explicitement.

### 2.2. Partager ou ne pas partager

Dans une région parallèle, une variable déclarée avant la région est **partagée** par défaut : tous les threads voient la même case mémoire. Une variable **privée** a une copie par thread. La plupart des bogues OpenMP sont des variables partagées qu'on voulait privées.

::: ex
[Exemple 2.1 — Une course de données, mesurée]{.tag} Le programme `sum_variants` additionne $2^{25}$ nombres entiers stockés en `double` (donc toute addition est exacte). La variante `race` écrit `sum += a[i]` dans une boucle `parallel for` sans protection. Résultat sur la VM d'essai, 4 threads, 7 répétitions :

~~~text
variant=race threads=4 n=33554432 repeat=7 wrong=7 result=33554432 expected=134217723 min_ms=14.672 median_ms=15.060
~~~

La somme obtenue vaut environ le quart de la somme attendue, dans les 7 répétitions sur 7. Une explication plausible, que nous n'avons pas vérifiée dans le code assembleur : le compilateur garde `sum` dans un registre pendant la boucle de chaque thread, chacun écrit ensuite son total partiel à l'adresse commune et le dernier écrase les autres. Avec un seul thread, la même boucle est exacte. Une course de données est un comportement indéfini selon le standard : ni ce résultat ni son contraire n'est garanti, et `verify.sh` n'affirme rien sur lui.
:::

### 2.3. Réductions

Une **réduction** combine les contributions de tous les threads avec un opérateur associatif (somme, produit, maximum). La clause `reduction(+ : sum)` donne à chaque thread une copie privée de `sum` initialisée à l'élément neutre, puis combine les copies à la fin.

~~~c
#pragma omp parallel for num_threads(nth) reduction(+ : sum)
        for (long i = 0; i < n; i++) sum += a[i];
~~~

La spécification 6.0 précise (section 7.6.7) que l'endroit et l'ordre de la combinaison ne sont pas spécifiés, et que des résultats identiques bit à bit ne sont donc pas garantis, y compris d'une exécution à l'autre avec le même nombre de threads. Pour des entiers, cela n'a aucune importance ; pour des flottants, c'est le sujet du chapitre 6.

Les alternatives correctes mais lentes protègent l'accumulateur commun : `critical` (une section à la fois) ou `atomic` (une instruction atomique). Le tableau compare les variantes du lab, médiane de 7 répétitions, machine au repos (charge moyenne 0,17 avant et 0,24 après).

| Variante | 1 thread (ms) | 4 threads (ms) | Résultat |
|---|---|---|---|
| séquentielle, scalaire | 53,0 | n.a. | exact |
| séquentielle, `omp simd` | 36,6 | n.a. | exact |
| `race` (course de données) | 56,3 | 15,1 | faux à 4 threads |
| `reduction(+ : sum)` | 51,9 | 14,3 | exact |
| réduction écrite à la main (`local`) | 51,6 | 13,8 | exact |
| `reduction` avec `parallel for simd` | 43,0 | 10,8 | exact |
| `critical` ($n = 2\cdot 10^6$) | 31,2 | 257,4 | exact |
| `atomic` ($n = 2\cdot 10^6$) | 27,3 | 149,5 | exact |

::: ex
[Exemple 2.2 — Lire le tableau]{.tag} Pour `critical`, le temps par élément passe de $31{,}2\ \text{ms}/2\cdot 10^6 = 15{,}6$ ns avec un thread à $257{,}4\ \text{ms}/2\cdot 10^6 = 128{,}7$ ns avec quatre : 8,2 fois plus lent avec quatre threads qu'avec un. Les threads se disputent le verrou, et chaque passage le fait circuler entre caches. `atomic` perd un facteur 5,5. La réduction, elle, coûte $14{,}3\ \text{ms}/2^{25} \approx 0{,}43$ ns par élément : une combinaison par thread, pas par élément.

Règle : ne synchronisez jamais à chaque itération ce que vous pouvez accumuler localement puis combiner une fois.
:::

### 2.4. Ordonnancement des itérations

La clause `schedule(kind[, chunk])` décide quel thread exécute quelle itération. La spécification 6.0 (section 13.6.3) définit les trois choix de base.

-   `static` : des paquets (*chunks*) d'itérations consécutives sont distribués aux threads en tourniquet, dans l'ordre des numéros de thread. Sans taille de paquet, l'espace d'itérations est coupé en blocs de tailles à peu près égales, au plus un par thread.
-   `dynamic` : chaque thread prend un paquet quand il est libre ; la taille par défaut est 1.
-   `guided` : comme `dynamic`, mais la taille du paquet est proportionnelle au nombre d'itérations restantes divisé par le nombre de threads, et décroît jusqu'à la taille minimale demandée.

Sans clause `schedule`, la spécification 6.0 dit que l'effet est celui de `auto`, c'est-à-dire un choix de l'implémentation. Avec `libgomp` 13.3, le programme `default_schedule` montre des blocs statiques : `threads=4 owner=0000111122223333`. La variable `OMP_SCHEDULE` ne s'applique qu'aux boucles écrites `schedule(runtime)`.

Le choix compte quand les itérations ne coûtent pas toutes pareil. Le programme `schedule_demo` enregistre le propriétaire de chaque itération, en déduit la charge de chaque thread, puis le **déséquilibre** : charge maximale divisée par charge moyenne. Le temps d'une boucle parallèle vaut alors à peu près la charge maximale multipliée par le temps d'une unité de travail.

$$T_{\text{boucle}} \approx t_{\text{unité}} \times \max_t \text{charge}_t \qquad \text{gain} \le \frac{p}{\text{déséquilibre}}$$

::: ex
[Exemple 2.3 — Une boucle triangulaire, six ordonnancements]{.tag} L'itération $i$ coûte $i+1$ unités, pour $N = 2000$ itérations, soit 2 001 000 unités, sur 4 threads. Temps séquentiel : de 292 à 302 ms selon la série. Les temps prédits viennent de la charge maximale et du temps par unité mesuré en séquentiel ; pour `dynamic` et `guided`, de l'assignation réellement observée.

| Ordonnancement | Paquets observés | Déséquilibre | Temps prédit (ms) | Temps mesuré (ms) | Gain mesuré |
|---|---|---|---|---|---|
| `static` | 4 | 1,750 | 129,1 | 137,7 | 2,14 |
| `static,1` | 2000 | 1,001 | 75,5 | 76,5 | 3,94 |
| `static,16` | 125 | 1,024 | 74,9 | 84,8 | 3,45 |
| `dynamic,1` | 2000 | 1,013 | 76,3 | 74,9 | 4,02 |
| `dynamic,16` | 125 | 1,017 | 74,2 | 75,7 | 3,85 |
| `guided` | 23 | 1,003 | 73,1 | 73,8 | 3,95 |

Le déséquilibre de `static` est exact et déterministe : le dernier thread reçoit les itérations 1500 à 1999, de coûts 1 501 à 2 000, soit 875 250 unités sur une moyenne de 500 250, donc 1,750. Les prédictions tombent à 7 % des mesures pour `static` et à 13 % pour `static,16`, le plus mauvais cas. Le modèle ne contient ni le coût d'obtention d'un paquet ni les effets de cache ; ce qu'il ne dit pas est la partie de l'écart que vous devez chercher.
:::

Sur une boucle uniforme, `static` suffit et coûte le moins. Dès que le coût dépend de l'indice ou des données, essayez `static` avec un petit paquet, puis `dynamic` ou `guided`, et mesurez avec `schedule(runtime)` et `OMP_SCHEDULE` sans recompiler.

### 2.5. Le faux partage

Un cœur ne lit pas la mémoire octet par octet mais par **lignes de cache** de 64 octets sur cette machine. Si deux threads écrivent des variables différentes situées dans la même ligne, la ligne fait des allers-retours entre leurs caches : c'est le **faux partage** (*false sharing*). Aucun octet n'est partagé, et pourtant tout se passe comme si l'on se disputait une même variable.

<figure class="fig">
<svg viewBox="0 0 560 250" role="img" aria-labelledby="fs-t fs-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="fs-t">Faux partage : quatre cases de 56 octets contre quatre cases alignées sur 64 octets</title>
<desc id="fs-d">En haut, quatre threads ont chacun une case de 56 octets rangées côte à côte sur quatre lignes de cache de 64 octets : les cases des threads 0 et 1, 1 et 2, 2 et 3 partagent une ligne. En bas, chaque case commence au début d'une ligne : aucune ligne n'est partagée.</desc>
<g fill="none" stroke="currentColor" stroke-width="2">
<rect x="20" y="50" width="520" height="40"/><line x1="150" y1="50" x2="150" y2="90"/><line x1="280" y1="50" x2="280" y2="90"/><line x1="410" y1="50" x2="410" y2="90"/>
<rect x="20" y="160" width="520" height="40"/><line x1="150" y1="160" x2="150" y2="200"/><line x1="280" y1="160" x2="280" y2="200"/><line x1="410" y1="160" x2="410" y2="200"/>
</g>
<g fill="var(--accent)" fill-opacity="0.35" stroke="var(--accent)" stroke-width="2">
<rect x="20" y="56" width="114" height="28"/><rect x="134" y="56" width="114" height="28"/><rect x="248" y="56" width="114" height="28"/><rect x="362" y="56" width="114" height="28"/>
<rect x="20" y="166" width="114" height="28"/><rect x="150" y="166" width="114" height="28"/><rect x="280" y="166" width="114" height="28"/><rect x="410" y="166" width="114" height="28"/>
</g>
<g fill="currentColor" font-size="14" text-anchor="middle">
<text x="77" y="76">T0</text><text x="191" y="76">T1</text><text x="305" y="76">T2</text><text x="419" y="76">T3</text>
<text x="77" y="186">T0</text><text x="207" y="186">T1</text><text x="337" y="186">T2</text><text x="467" y="186">T3</text>
<text x="85" y="42">ligne 0</text><text x="215" y="42">ligne 1</text><text x="345" y="42">ligne 2</text><text x="475" y="42">ligne 3</text>
<text x="280" y="116" font-weight="700">cases de 56 octets : 3 lignes partagées</text>
<text x="280" y="226" font-weight="700">cases alignées sur 64 octets : aucune</text>
</g>
</svg>
<figcaption>Quatre threads, une case de sept compteurs de 8 octets chacun. Rangées bout à bout (56 octets), les cases débordent d'une ligne de 64 octets sur la suivante ; alignées, chacune a sa ligne.</figcaption>
</figure>

Le lab construit un cas réaliste : un histogramme par thread, où l'indice du compteur incrémenté dépend de la donnée. Trois dispositions, mêmes résultats :

-   `packed` : chaque thread a 7 compteurs de 8 octets (56 octets), rangés bout à bout ;
-   `padded` : chaque thread a sa case alignée sur 64 octets, complétée par du remplissage (*padding*) ;
-   `private` : chaque thread compte dans un tableau local, fusionné une fois à la fin.

::: ex
[Exemple 2.4 — Mesurer un faux partage]{.tag} $10^8$ éléments, 7 répétitions, médiane en ms. La colonne « lignes partagées » est calculée par adresse, sans chronomètre : les cases de 56 octets partagent 1 ligne avec 2 threads, 3 avec 4 threads (`exercises/line_sharing.py` donne 7 pour 8 threads et 14 pour 16).

| Disposition | Lignes partagées | 1 thread | 2 threads | 4 threads |
|---|---|---|---|---|
| `packed` (56 octets) | 0 / 1 / 3 | 60,7 | 84,1 | 96,5 |
| `padded` (64 octets) | 0 | 56,3 | 44,6 | 29,4 |
| `private` | 0 | 52,7 | 29,9 | 27,2 |

Avec quatre threads, `packed` est 3,3 fois plus lent que `padded` et 1,6 fois plus lent qu'**un seul** thread. Ajouter des cœurs a rendu le programme plus lent. `private` est le meilleur et le plus simple : le remède du faux partage est presque toujours de ne pas écrire dans une zone commune pendant la boucle.
:::

::: note
[Un effet qui dépend du matériel]{.tag} Le programme `fs_counters` donne un compteur à chaque thread, rangé compact (8 octets d'écart) ou aligné (64 octets). Avec une incrémentation simple `volatile`, sur la VM d'essai, à 4 threads et $2\cdot 10^8$ incréments au total : 191,1 ms (compact) contre 191,2 ms (aligné), minimum de 5 répétitions, aucun écart. Avec une incrémentation atomique : 2 590 ms contre 469 ms, un facteur 5,5. La machine n'était pas tout à fait au repos (charge moyenne de 0,6).

Un essai de relecture à $10^8$ incréments a donné un facteur proche de 10 : l'ordre de grandeur est robuste, le facteur ne l'est pas.

Nous n'avons pas d'explication vérifiée à l'absence d'effet dans le premier cas (on peut supposer que le tampon d'écriture du cœur absorbe des écritures simples, hypothèse non testée). Retenez que le faux partage n'est pas une constante de la nature : mesurez-le sur votre matériel avant d'ajouter du remplissage partout.
:::

### 2.6. Les tâches

Quand le travail n'est pas une boucle (parcours d'arbre, récursion), OpenMP offre les **tâches** : `#pragma omp task` crée un travail que n'importe quel thread de l'équipe exécutera, `taskwait` attend ses enfants. Une tâche a un coût de création ; le remède est un **seuil de coupure** (*cutoff*) au-delà duquel on calcule séquentiellement.

::: ex
[Exemple 2.5 — Le prix d'une tâche]{.tag} `tasks_fib` calcule fib(32) = 2 178 309 par récursion. Les appels de profondeur inférieure au seuil créent une tâche ; le nombre de tâches est compté puis comparé à celui d'un parcours séquentiel de la récursion (le programme échoue s'ils diffèrent).

| Seuil | Tâches créées | Temps, 4 threads (ms) |
|---|---|---|
| 0 | 0 | 4,4 |
| 4 | 15 | 2,8 |
| 8 | 255 | 3,3 |
| 12 | 4 095 | 4,9 |
| 27 | 3 520 835 | 3 452 |

À 3,5 millions de tâches, le calcul est 780 fois plus lent que sans tâche : environ une microseconde de temps mur par tâche sur 4 threads. Aux seuils de 4 à 12, le calcul entier ne dure que quelques millisecondes et les temps sont dominés par le démarrage de l'équipe : ne tirez pas de conclusion de leurs écarts. La conclusion fiable est la dernière ligne, plus les comptes de tâches, qui sont exacts.
:::

### 2.7. Quelle ligne de base ?

Le tableau de la section 2.3 contient un piège. Le gain de `reduction` sur 4 threads semble excellent : $51{,}9/14{,}3 = 3{,}63$ par rapport à son propre temps sur un thread. Mais la version séquentielle scalaire, à 1,6 ns par élément (5,1 Go/s), est probablement limitée par la chaîne de dépendances des additions, chacune attendant la précédente, plutôt que par la mémoire : la version vectorisée, qui réordonne les additions, va 1,4 fois plus vite avec un seul thread.

La même boucle vectorisée (`omp simd`) tourne en 36,6 ms, soit 7,3 Go/s. Par rapport à **ce meilleur code séquentiel**, `reduction` sur 4 threads ne gagne que $36{,}6/14{,}3 = 2{,}56$. Et `parallel for simd` atteint $268{,}4\ \text{Mo}/10{,}8\ \text{ms} \approx 24{,}9$ Go/s, plus que quatre fois le débit d'un thread scalaire. C'est le piège du « code séquentiel affaibli » du module 2 : le gain se mesure contre le meilleur séquentiel, pas contre le plus lent.

::: recap
Points clés — chapitre 2

-   Une variable partagée écrite par plusieurs threads sans protection est une course de données : résultat indéfini.
-   `reduction` accumule localement et combine une fois ; `critical` et `atomic` à chaque itération coûtent 5 à 8 fois plus avec 4 threads qu'avec un.
-   Les ordonnancements `static`, `dynamic` et `guided` se jugent par le déséquilibre : temps $\approx$ charge maximale $\times$ temps par unité.
-   Le faux partage se prévoit par l'adresse (lignes de 64 octets partagées) et se vérifie par la mesure ; il dépend du matériel.
-   Une tâche coûte de l'ordre de la microseconde : coupez la récursion avec un seuil.
-   Comparez toujours au meilleur code séquentiel, pas à la première version.
:::

## 3. MPI, les bases : rangs, communicateurs, point-à-point, interblocages {#ch3}

MPI est une bibliothèque : vos processus s'y appellent les uns les autres par des fonctions. Ce chapitre suit le lab 3.2 (`labs/parallel-programming/mpi-ring/`), en Python avec mpi4py pour garder le code court. Les noms de fonctions sont ceux de la norme (`MPI_Send` devient `comm.Send`), donc ce que vous apprenez vaut pour le C et le Fortran.

### 3.1. Un programme, plusieurs processus

Un programme MPI est lancé en plusieurs exemplaires par `mpirun -np 4 python3 programme.py`. C'est le modèle **SPMD** (*single program, multiple data*) : tous les processus exécutent le même code et se distinguent par leur rang.

~~~python
comm = MPI.COMM_WORLD
rank, size = comm.Get_rank(), comm.Get_size()
~~~

`MPI_COMM_WORLD` est le communicateur qui contient tous les processus lancés ensemble. Deux options d'Open MPI servent dans un conteneur de test : `--oversubscribe` autorise plus de rangs que de cœurs (par défaut, le nombre de places est le nombre de cœurs détectés d'après la page de manuel de `mpirun`) et `--allow-run-as-root` accepte de tourner en root. Les scripts du lab les ajoutent quand il le faut.

### 3.2. Envoyer et recevoir

Un message est identifié par sa source, sa destination, une **étiquette** (*tag*) entière et le communicateur. Une réception ne retient que les messages dont la source, l'étiquette et le communicateur correspondent. Entre deux processus donnés, les messages ne se doublent pas : si un émetteur envoie deux messages qui correspondent à la même réception, le premier est reçu en premier (c'est la règle du « non-dépassement » de la norme, chapitre 3).

Avec mpi4py, les méthodes à initiale majuscule (`Send`, `Recv`) travaillent sur des tampons numpy, sans copie intermédiaire ; celles à initiale minuscule (`send`, `recv`) sérialisent des objets Python, plus pratiques et plus lentes. Tout le lab utilise la première famille.

### 3.3. Quatre modes d'envoi

La norme définit quatre modes d'envoi (section 3.4) : standard (`Send`), synchrone (`Ssend`), tamponné (`Bsend`) et prêt (`Rsend`). Les deux qui comptent pour la suite sont les premiers.

-   Un **envoi standard** laisse la bibliothèque choisir : copier le message dans un tampon interne et rendre la main, ou attendre que la réception soit postée. Le programme ne peut pas savoir lequel.
-   Un **envoi synchrone** ne se termine que lorsque la réception correspondante a commencé : il n'est jamais tamponné.

La norme en tire un conseil aux utilisateurs (section 3.5) : un programme portable qui utilise des envois standard ne doit pas compter sur la mise en tampon pour éviter l'interblocage. Tous ses envois doivent pouvoir être remplacés par des envois synchrones sans que le programme cesse de fonctionner.

::: key
[Le test du `Ssend`]{.tag} Remplacez `Send` par `Ssend` dans votre programme. S'il se bloque, il ne fonctionnait que grâce à la mise en tampon de la bibliothèque, donc par chance. C'est le moyen le plus rapide de débusquer un interblocage latent avant qu'il n'apparaisse avec de plus gros messages.
:::

### 3.4. L'interblocage

Un **interblocage** (*deadlock*) est un cycle d'attentes : A attend B qui attend A. Le cas d'école en MPI : deux rangs commencent tous deux par envoyer, puis par recevoir. Si les deux envois sont tamponnés, tout va bien ; s'ils attendent le récepteur, aucun ne reçoit jamais.

~~~python
if mode == "send_send":
    comm.Send(out, dest=other, tag=7)
    comm.Recv(inp, source=other, tag=7)
elif mode == "ssend_ssend":
    comm.Ssend(out, dest=other, tag=7)
    comm.Recv(inp, source=other, tag=7)
~~~

::: ex
[Exemple 3.1 — Qui se bloque, et à partir de quelle taille ?]{.tag} Le lab lance `deadlock_demo.py` sur 2 rangs sous `timeout` (5 s pour les cas qui doivent se bloquer, 30 s pour les autres) ; le code de sortie 124 signifie « toujours bloqué quand le délai a expiré ». Open MPI 4.1.6, transport mémoire partagée.

| Mode | Taille | Résultat |
|---|---|---|
| `send_send` | 8 octets | termine |
| `send_send` | 2 048 octets | termine |
| `send_send` | 1 048 576 octets | **bloqué** |
| `ssend_ssend` | 8 octets | **bloqué** |
| `recv_send` (un rang reçoit d'abord) | 1 048 576 octets | termine |
| `sendrecv` | 1 048 576 octets | termine |
| `isend_recv` | 1 048 576 octets | termine |

Le seuil vient de la **limite eager** (*eager limit*) du transport : sous une certaine taille, le message est copié tout de suite dans le tampon du destinataire. `ompi_info --param btl vader --level 9` rend `btl_vader_eager_limit` = 4096 octets, en-tête compris, et nous avons constaté que 2 048 passe.

La norme ne dit rien de tel : sur un autre transport ou une autre bibliothèque, le seuil change. Le test du `Ssend` bloque dès 8 octets, ce qui est son rôle. Relever la limite avec `--mca btl_vader_eager_limit 65536` fait passer 8 192 et 32 768 octets, mais pas 262 144 : le seuil se déplace, le risque reste.
:::

Un programme dont les petits tests passent et dont la production se bloque est le cas le plus coûteux : l'interblocage apparaît avec la taille réelle des données, sur le cluster, au bout d'une heure de file d'attente.

### 3.5. Trois façons de l'éviter

La norme cite les deux premiers dans la description de l'envoi-réception combiné (section 3.2.7).

1.  **Ordonner.** Les rangs pairs envoient puis reçoivent, les rangs impairs reçoivent puis envoient : le cycle disparaît. C'est ce que fait le mode `recv_send` de l'exemple 3.1.
2.  **Combiner.** `Sendrecv` exécute l'envoi et la réception en une seule opération que la bibliothèque sait ordonner. C'est l'outil de base des décalages et des échanges de halo.
3.  **Rendre non bloquant.** `Isend` et `Irecv` rendent la main immédiatement avec une requête ; `Wait` ou `Waitall` attend la fin. Il ne faut ni modifier le tampon d'envoi ni lire le tampon de réception avant la fin de la requête.

Le non-bloquant ouvre aussi la porte au **recouvrement** du calcul et de la communication (chapitre 5), à condition que la bibliothèque progresse pendant que vous calculez. La documentation de NCCL le rappelle à propos de MPI : « MPI operations need the program to call MPI functions (potentially multiple times) to make progress and eventually complete ».

::: note
[Les rangs aux extrémités]{.tag} Un rang qui n'a pas de voisin (le premier ou le dernier d'une chaîne) envoie ou reçoit avec le rang spécial `MPI.PROC_NULL`, ce qui ne fait rien et se termine tout de suite. Cela évite d'écrire un cas particulier pour les bords ; `halo_stencil.py` l'utilise.
:::

::: recap
Points clés — chapitre 3

-   SPMD : un programme, N rangs, distingués par `Get_rank()` dans un communicateur.
-   Un message est (source, destination, étiquette, communicateur) ; entre deux processus donnés, il ne se double pas.
-   `Send` peut ou non être tamponné ; ne comptez jamais dessus (norme, section 3.5).
-   Test du `Ssend` : si le programme se bloque avec des envois synchrones, il est fragile.
-   Remèdes : ordre pair-impair, `Sendrecv`, `Isend`/`Irecv` + `Waitall`.
:::

## 4. MPI, les collectives : broadcast, reduce, allreduce, alltoall ; algorithmes et coûts {#ch4}

Une **collective** est une opération à laquelle tous les rangs d'un communicateur participent. Elles remplacent des dizaines de lignes de `Send`/`Recv`, et surtout elles laissent la bibliothèque choisir l'algorithme en fonction du nombre de rangs et de la taille. C'est ce que fait NCCL pour les GPU.

### 4.1. Le catalogue

Le script `collectives_tour.py` appelle chaque collective sur 4 rangs. Le rang $r$ part avec les quatre entiers $[10r,\ 10r+1,\ 10r+2,\ 10r+3]$. Sortie réelle (Open MPI 4.1.6, mpi4py 4.1.2) :

~~~text
input          r0:[0, 1, 2, 3] r1:[10, 11, 12, 13] r2:[20, 21, 22, 23] r3:[30, 31, 32, 33]
bcast(root=0)   every rank: [0, 1, 2, 3]
reduce(root=0) r0:[60, 64, 68, 72] r1:[-1, -1, -1, -1] r2:[-1, -1, -1, -1] r3:[-1, -1, -1, -1]
allreduce       every rank: [60, 64, 68, 72]
reduce_scatter r0:[60] r1:[64] r2:[68] r3:[72]
allgather       every rank: [0, 1, 2, 3, 10, 11, 12, 13, 20, 21, 22, 23, 30, 31, 32, 33]
alltoall       r0:[0, 10, 20, 30] r1:[1, 11, 21, 31] r2:[2, 12, 22, 32] r3:[3, 13, 23, 33]
~~~

-   `Bcast` copie le tableau d'un rang racine vers tous les autres.
-   `Reduce` combine les tableaux élément par élément et laisse le résultat sur la racine (les autres rangs gardent ici la valeur $-1$ qui marque « non touché »).
-   `Allreduce` fait la même chose et laisse le résultat partout. C'est la somme des gradients de l'entraînement en parallélisme de données.
-   `Reduce_scatter_block` combine, puis découpe le résultat en blocs égaux, un par rang.
-   `Allgather` concatène les contributions de tous les rangs, dans l'ordre des rangs, chez tous.
-   `Alltoall` transpose : le bloc $j$ du rang $i$ devient le bloc $i$ du rang $j$.

Deux identités sont vérifiées par le script. `Allreduce` égale `Reduce_scatter_block` suivi d'`Allgather` ; `Alltoall` est la transposée de la matrice des blocs. La première est la clé des algorithmes de la section 4.3 et de NCCL (section 4.7).

### 4.2. Tous ou personne

Une collective doit être appelée par **tous** les rangs du communicateur, avec des arguments compatibles. Si un rang saute l'appel (parce qu'une condition a divergé, ou qu'il a planté), les autres attendent indéfiniment. Il n'y a pas d'étiquette pour distinguer deux collectives : c'est l'ordre des appels qui les apparie. Deux rangs qui appellent `Bcast` puis `Allreduce` dans des ordres différents se bloquent ou, pire, mélangent leurs données.

C'est une cause classique de job d'entraînement « figé » : un rang est tombé en panne ou a pris un autre chemin, et tous les autres attendent à la prochaine collective. Le module [Slurm](../slurm/index.html) en montre l'effet côté ordonnanceur, et le module sur la tolérance aux pannes le traite côté application.

### 4.3. Combien coûte un all-reduce

Le module 2 a donné le modèle de Hockney : un message de $n$ octets coûte $\alpha + n/B$. Pour un all-reduce sur $p$ rangs, deux algorithmes élémentaires s'écrivent avec cette seule formule.

L'**anneau** fait un *reduce-scatter* puis un *all-gather*. Le tableau est découpé en $p$ morceaux ; à chaque étape, chaque rang envoie un morceau à son voisin de droite et reçoit un morceau de celui de gauche. Il y a $2(p-1)$ étapes de $n/p$ octets.

Le **doublement récursif** échange le tableau entier entre rangs voisins à des distances $1, 2, 4, \dots$ : $\log_2 p$ étapes de $n$ octets (il suppose $p$ puissance de deux dans notre version).

$$T_{\text{anneau}} = 2(p-1)\,\alpha + \frac{2(p-1)}{p}\,\frac{n}{B} \qquad T_{\text{doublement}} = \log_2 p\,\Bigl(\alpha + \frac{n}{B}\Bigr)$$

L'anneau envoie moins d'octets et fait plus de messages ; le doublement récursif fait l'inverse. Patarasuk et Yuan ont démontré que l'anneau envoie le minimum d'octets possible pour un all-reduce, sous l'hypothèse que l'opérateur est associatif et commutatif : hypothèse qui reviendra au chapitre 6.

Voici la fonction du lab (`ringlib.py`), avec le compteur qui sert à vérifier les formules sans chronomètre.

~~~python
def ring_allreduce(comm, x, counter=None):
    """Sum-all-reduce x in place. 2(p-1) steps; each rank sends about n/p elements per step."""
    p, r = comm.Get_size(), comm.Get_rank()
    if p == 1:
        return
    b = chunk_bounds(x.size, p)
    right, left = (r + 1) % p, (r - 1) % p
    tmp = np.empty(int(np.diff(b).max()), dtype=x.dtype)
    # Phase 1, reduce-scatter. Step s: send chunk (r - s), receive chunk (r - s - 1) and add it.
    for s in range(p - 1):
        cs, cr = (r - s) % p, (r - s - 1) % p
        send = x[b[cs]:b[cs + 1]]
        recv = tmp[:b[cr + 1] - b[cr]]
        comm.Sendrecv(send, dest=right, recvbuf=recv, source=left)
        x[b[cr]:b[cr + 1]] += recv
        if counter:
            counter.add(send)
    # Rank r now owns the fully reduced chunk (r + 1) mod p.
    # Phase 2, all-gather. Step s: send chunk (r + 1 - s), receive chunk (r - s) and keep it.
    for s in range(p - 1):
        cs, cr = (r + 1 - s) % p, (r - s) % p
        send = x[b[cs]:b[cs + 1]]
        comm.Sendrecv(send, dest=right, recvbuf=x[b[cr]:b[cr + 1]], source=left)
        if counter:
            counter.add(send)
~~~

::: ex
[Exemple 4.1 — Compter plutôt que chronométrer]{.tag} `check_allreduce.py` exécute l'anneau et le doublement récursif sur $n = 1200$ doubles (9 600 octets), vérifie que le résultat entier égale celui de `MPI_Allreduce` exactement, et compare les compteurs de chaque rang aux formules. Sorties réelles :

~~~text
p=4 n=1200 int64: ring == MPI_Allreduce exactly; float64: max|ring - MPI_Allreduce| = 8.9e-16
  ring per rank: 6 messages, 14400 bytes (2(p-1)/p*n*8 = 14400 bytes)
  recursive doubling per rank: 2 messages, 19200 bytes (log2(p)*n*8 = 19200)
p=8 n=1200 int64: ring == MPI_Allreduce exactly; float64: max|ring - MPI_Allreduce| = 1.8e-15
  ring per rank: 14 messages, 16800 bytes (2(p-1)/p*n*8 = 16800 bytes)
  recursive doubling per rank: 3 messages, 28800 bytes (log2(p)*n*8 = 28800)
~~~

Avec $p = 8$, l'anneau émet $1{,}75\,n$ octets en 14 messages, le doublement récursif $3\,n$ octets en 3 messages. Les compteurs sont exacts, et le script échoue s'ils s'écartent des formules. Les écarts flottants de l'ordre de $10^{-15}$ entre l'anneau et `MPI_Allreduce` sont des erreurs d'arrondi dues à un autre ordre d'addition : le chapitre 6 y revient.
:::

En égalant les deux temps, on trouve la taille au-dessus de laquelle l'anneau gagne.

$$n^{*} = \alpha B\,\frac{2(p-1) - \log_2 p}{\log_2 p - 2(p-1)/p} \qquad (p \ge 4)$$

::: ex
[Exemple 4.2 — Où se croisent anneau et doublement récursif ?]{.tag} Avec les paramètres d'exemple du module 2 ($\alpha = 5\ \mu$s, $B = 25$ Go/s, donc $\alpha B = 125$ ko), `exercises/crossover.py` donne :

| $p$ | $n^{*}$ (octets) | en unités de $\alpha B$ |
|---|---|---|
| 4 | 1 000 000 | 8,00 |
| 8 | 1 100 000 | 8,80 |
| 16 | 1 529 412 | 12,24 |
| 64 | 3 720 930 | 29,77 |

Pour $p = 8$ à la moitié du seuil, l'anneau prend 108,5 µs et le doublement récursif 81,0 µs ; au double du seuil, 224 µs contre 279 µs. Plus $p$ grandit, plus le seuil monte : l'anneau paie $2(p-1)$ latences. Les valeurs de $\alpha$ et de $B$ sont des exemples du module 2, pas des mesures de cette VM.
:::

### 4.4. Ce que Open MPI propose vraiment

Une bibliothèque ne se contente pas de deux algorithmes. `ompi_info --param coll tuned --level 9` liste, pour `MPI_Allreduce`, les algorithmes que le composant `tuned` d'Open MPI 4.1.6 sait forcer : 1 `basic_linear`, 2 `nonoverlapping` (reduce puis bcast), 3 `recursive_doubling`, 4 `ring`, 5 `segmented_ring`, 6 `rabenseifner`. Par défaut, la bibliothèque choisit selon la taille et le nombre de rangs ; avec `--mca coll_tuned_use_dynamic_rules 1 --mca coll_tuned_allreduce_algorithm 4`, on force l'anneau.

::: ex
[Exemple 4.3 — Forcer l'algorithme, et mesurer honnêtement]{.tag} 4 rangs, `float64`, médiane de 7 répétitions par taille (en µs), plage sur 3 exécutions complètes pour le choix par défaut et sur 2 pour chaque algorithme forcé (`bench_allreduce.py --max-exp 22`, voir le README du lab).

| Taille | Défaut | Doublement récursif | Anneau | Rabenseifner |
|---|---|---|---|---|
| 8 octets | 2,7 à 4,4 | 3,9 à 5,3 | 2,9 à 4,2 | 4,0 à 4,7 |
| 4 Kio | 10,3 à 20,0 | 13,3 à 18,7 | 17,9 à 18,4 | 13,3 à 14,5 |
| 256 Kio | 120 à 216 | 287 à 409 | 230 à 254 | 196 à 237 |
| 2 Mio | 1 065 à 1 690 | 1 615 à 2 837 | 1 737 à 1 855 | 1 596 à 1 651 |

Les plages se recouvrent presque partout : la variation d'une exécution à l'autre est de l'ordre de l'écart entre algorithmes. Seul le doublement récursif à 256 Kio est plus lent dans les deux exécutions, et il faudrait plus de répétitions pour conclure. Surtout, ces quatre rangs partagent une mémoire : cette expérience n'apprend rien sur un réseau. Elle apprend qu'un classement d'algorithmes mesuré une fois est une anecdote.
:::

### 4.5. Le modèle face à la mesure

Le lab 3.2 mesure le ping-pong entre deux rangs, l'échange simultané de tous les rangs avec leur voisin (ce que fait une étape d'anneau), puis les deux all-reduce faits main et `MPI_Allreduce`. Il ajuste $\alpha$ et $B$ (erreur relative minimale) sur chaque micro-mesure, puis compare. Voici une exécution complète, 4 rangs, machine au repos au départ.

| Taille | Anneau mesuré (µs) | Modèle (ping-pong) | Mesure/modèle | Modèle (échange + boucle Python) | Mesure/modèle |
|---|---|---|---|---|---|
| 8 octets | 45,5 | 8,6 | 5,27 | 39,4 | 1,15 |
| 4 Kio | 50,5 | 9,6 | 5,24 | 37,3 | 1,36 |
| 256 Kio | 252,2 | 73,7 | 3,42 | 173,2 | 1,46 |
| 2 Mio | 1 894 | 529 | 3,58 | 1 079 | 1,76 |

Les ajustements de cette exécution : $\alpha = 1{,}4$ µs et $B = 6{,}0$ Go/s sur le ping-pong ; $\alpha = 2{,}1$ µs et $B = 7{,}3$ Go/s sur l'échange simultané. Le modèle du ping-pong sous-estime l'anneau d'un facteur 3,4 à 7,3 selon la taille (quatre tailles sur sept sont montrées). Sur trois exécutions complètes, le rapport médian mesure/modèle va de 3,9 à 5,4.

Deux corrections ramènent l'écart près de l'unité. Premièrement, calibrer sur la primitive qu'on utilise : un `Sendrecv` simultané n'est pas un ping-pong. Deuxièmement, mesurer le coût de la boucle Python elle-même, avec un communicateur factice dont `Sendrecv` ne fait rien (ligne `pyloop` du lab) : pour 8 octets, c'est la plus grande part des 45 µs. Avec ces deux corrections, le rapport médian pour l'anneau va de 1,2 à 1,4 sur les trois exécutions.

::: note
[Ce qui reste inexpliqué]{.tag} Pour les gros messages, il reste un facteur de 1,5 à 1,8 sur l'anneau, et le doublement récursif de 2 Mio est 7,4 fois plus lent que son modèle (5 157 µs mesurés contre 697 µs). Nous ne l'expliquons pas. Hypothèses non testées : le transport mémoire partagée copie en deux temps, et quatre rangs se partagent le bus mémoire. À titre de repère, `MPI_Allreduce` de la bibliothèque prend 2,7 µs pour 8 octets (17 fois moins que notre anneau en Python) et 1 065 µs pour 2 Mio.
:::

### 4.6. Deux niveaux : nœud, puis réseau

Dans un nœud à plusieurs GPU, les liens internes sont bien plus rapides que le réseau entre nœuds. Un anneau unique sur tous les rangs est limité par le lien le plus lent. L'alternative à deux niveaux est un modèle que nous dérivons ici (sans l'avoir mesuré) : *reduce-scatter* dans chaque nœud, all-reduce entre nœuds de la tranche $n/g$ de chaque rang, puis *all-gather* dans le nœud. Avec $m$ nœuds de $g$ rangs, des latences $\alpha_i, \alpha_o$ et des débits $B_i, B_o$ interne et externe :

$$T_{\text{2 niv.}} = 2\Bigl[(g-1)\alpha_i + \tfrac{g-1}{g}\tfrac{n}{B_i}\Bigr] + 2(m-1)\alpha_o + \tfrac{2(m-1)}{m}\,\tfrac{n/g}{B_o}$$

L'avantage vient du terme externe : chaque rang n'envoie que $n/g$ octets sur le réseau. L'exercice 7 le chiffre. Le module [Réseaux](../networking/index.html) traite les débits réels et la topologie.

### 4.7. De MPI à NCCL

NCCL, la bibliothèque de communication des GPU NVIDIA, reprend les noms et la sémantique des collectives MPI. Sa documentation (page de la version 2.32, lue le 25 octobre 2026) le dit ainsi : « The NCCL API and usage are similar to MPI but there are many minor differences ».

| MPI | NCCL | Remarque tirée de la documentation de NCCL |
|---|---|---|
| `MPI_Allreduce` | `ncclAllReduce` | chaque rang reçoit des résultats identiques |
| `MPI_Reduce_scatter_block` | `ncclReduceScatter` | NCCL suit le « block », pas `MPI_Reduce_scatter` |
| `MPI_Allgather` | `ncclAllGather` | sortie ordonnée par rang |
| `MPI_Bcast`, `MPI_Reduce` | `ncclBroadcast`, `ncclReduce` | « A Reduce, followed by a Broadcast, is equivalent to the AllReduce operation » |
| `MPI_Isend`/`MPI_Irecv` + `Waitall` | `ncclSend`/`ncclRecv` dans un groupe | pas de `MPI_ANY_SOURCE`, pas d'étiquettes |

La phrase de la documentation qui relie ce chapitre à l'entraînement est celle-ci : « Executing ReduceScatter, followed by AllGather, is equivalent to the AllReduce operation ». C'est exactement la décomposition en deux phases de l'anneau de la section 4.3 et du module 2. NCCL choisit lui aussi son algorithme : la variable `NCCL_ALGO` accepte, d'après la même documentation, `Ring` et `Tree` (depuis 2.5) ainsi que des algorithmes plus récents pour les réseaux et les liens NVLink de dernière génération.

Côté PyTorch, `torch.distributed` propose les backends `gloo`, `mpi`, `nccl` et `xccl`. La documentation de la version 2.14 précise que MPI est un backend optionnel, disponible seulement si l'on compile PyTorch depuis les sources, et conseille : « Use Gloo, unless you have specific reasons to use MPI ». Sur la VM d'essai, avec PyTorch 2.14.1 installé par `pip` pour CPU, `is_mpi_available()` rend `False`, `is_gloo_available()` rend `True` et `is_nccl_available()` rend `False`.

::: war
[Une collective NCCL peut interbloquer un programme MPI]{.tag} Documenté par NVIDIA (page « NCCL and MPI », NCCL 2.32) : bloquer sur une collective NCCL, par exemple avec `cudaStreamSynchronize`, peut créer un interblocage, parce que dans certaines implémentations MPI la progression d'un rang exige que MPI soit appelé sur un autre rang. De même, utiliser NCCL et un MPI sensible aux GPU en même temps sur les mêmes périphériques n'est pas garanti sûr. L'exemple de la page interroge le flux avec `cudaStreamQuery` et appelle `MPI_Iprobe` dans la boucle d'attente. Nous n'avons pas pu l'exécuter ici (pas de GPU) : la source est <https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/mpi.html>.
:::

::: recap
Points clés — chapitre 4

-   Une collective est appelée par tous les rangs, dans le même ordre ; sinon, blocage.
-   `Allreduce` = `Reduce_scatter_block` + `Allgather` : c'est la structure de l'anneau et de NCCL.
-   Anneau : $2(p-1)$ messages, $2(p-1)/p\cdot n$ octets. Doublement récursif : $\log_2 p$ messages, $\log_2 p \cdot n$ octets. Seuil de croisement $n^{*}$ au-dessus duquel l'anneau gagne.
-   Les compteurs de messages et d'octets se vérifient exactement ; les durées, jamais sans dispersion.
-   Calibrez le modèle sur la primitive que vous utilisez, et mesurez le coût de votre propre code.
-   NCCL reprend les noms et les identités des collectives MPI, sans étiquettes ni `MPI_ANY_SOURCE`.
:::

## 5. Décomposition de domaine, halos et recouvrement calcul/communication {#ch5}

La plupart des codes de simulation, et une partie des codes d'entraînement, reposent sur une idée : découper les données, faire calculer chaque morceau par un processus, et n'échanger que ce qui traverse les frontières. Ce chapitre suit le lab 3.2 (partie C) et le lab 3.3 (`jacobi.c`).

### 5.1. Le propriétaire calcule

Prenons la relaxation de Jacobi pour l'équation de Laplace sur une grille : à chaque balayage, chaque point intérieur prend la moyenne de ses quatre voisins.

$$u^{\text{nouveau}}_{i,j} = \tfrac{1}{4}\bigl(u_{i-1,j} + u_{i+1,j} + u_{i,j-1} + u_{i,j+1}\bigr)$$

On donne à chaque rang un bloc de la grille. Pour les points au bord de son bloc, un voisin appartient à un autre rang : on en garde une copie dans une rangée de **cellules fantômes** (le *halo*), rafraîchie par un échange avant chaque balayage. Le rang calcule uniquement les points qu'il possède.

Voici l'échange du lab sur une ligne de points (`halo_stencil.py`), dans ses deux versions : bloquante, puis avec recouvrement.

~~~python
if style == "blocking":
    comm.Sendrecv(u[1:2], dest=left, recvbuf=u[m + 1:m + 2], source=right)
    comm.Sendrecv(u[m:m + 1], dest=right, recvbuf=u[0:1], source=left)
    new[1:-1] = (u[:-2] + u[1:-1] + u[2:]) / 3.0
else:
    reqs = [comm.Irecv(u[0:1], source=left), comm.Irecv(u[m + 1:m + 2], source=right),
            comm.Isend(u[1:2], dest=left), comm.Isend(u[m:m + 1], dest=right)]
    if m > 2:  # interior points 2..m-1 need no ghost
        new[2:m] = (u[1:m - 1] + u[2:m] + u[3:m + 1]) / 3.0
    MPI.Request.Waitall(reqs)
    new[1] = (u[0] + u[1] + u[2]) / 3.0
    if m > 1:
        new[m] = (u[m - 1] + u[m] + u[m + 1]) / 3.0
~~~

Le script vérifie que les deux versions rendent exactement les mêmes nombres que le calcul séquentiel, bit pour bit, pour 1 à 4 rangs : chaque point est calculé par la même expression, dans le même ordre, quelle que soit la décomposition. Il compte aussi les octets envoyés : 8 octets par voisin et par pas, donc 240 octets sur 30 pas pour un rang aux extrémités et 480 pour un rang intérieur.

### 5.2. Une dimension ou deux

Le coût d'un balayage a deux parties : du calcul proportionnel au nombre de points du bloc (le **volume**) et des échanges proportionnels au périmètre du bloc (la **surface**). Sur une grille de $n_x \times n_y$ points, la découpe en bandes (1D) donne à chaque rang des frontières de longueur $n_x$, quel que soit le nombre de rangs. La découpe en blocs (2D) raccourcit les frontières quand $p$ augmente.

<figure class="fig">
<svg viewBox="0 0 560 250" role="img" aria-labelledby="dd-t dd-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="dd-t">Décomposition en bandes et en blocs</title>
<desc id="dd-d">À gauche, une grille découpée en quatre bandes horizontales : trois frontières de largeur n. À droite, la même grille découpée en quatre blocs 2 par 2 : deux frontières horizontales et verticales de longueur n au total chacune.</desc>
<g fill="none" stroke="currentColor" stroke-width="2">
<rect x="30" y="30" width="200" height="160"/><line x1="30" y1="70" x2="230" y2="70"/><line x1="30" y1="110" x2="230" y2="110"/><line x1="30" y1="150" x2="230" y2="150"/>
<rect x="330" y="30" width="200" height="160"/><line x1="330" y1="110" x2="530" y2="110" /><line x1="430" y1="30" x2="430" y2="190"/>
</g>
<g stroke="var(--accent)" stroke-width="4" fill="none"><line x1="30" y1="70" x2="230" y2="70"/><line x1="30" y1="110" x2="230" y2="110"/><line x1="30" y1="150" x2="230" y2="150"/>
<line x1="330" y1="110" x2="530" y2="110"/><line x1="430" y1="30" x2="430" y2="190"/></g>
<g fill="currentColor" font-size="14" text-anchor="middle">
<text x="130" y="55">rang 0</text><text x="130" y="95">rang 1</text><text x="130" y="135">rang 2</text><text x="130" y="175">rang 3</text>
<text x="380" y="75">rang 0</text><text x="480" y="75">rang 1</text><text x="380" y="155">rang 2</text><text x="480" y="155">rang 3</text>
<text x="130" y="216" font-weight="700">1D : 3 frontières de longueur n</text>
<text x="430" y="216" font-weight="700">2D : 2 frontières de longueur n</text>
<text x="130" y="238">par balayage, 16·3·n octets</text>
<text x="430" y="238">par balayage, 16·2·n octets</text>
</g>
</svg>
<figcaption>Quatre rangs sur une grille n × n. Les traits épais sont les frontières où des halos s'échangent : la découpe en bandes en a trois, la découpe en blocs deux. Chaque frontière transporte les deux sens, à 8 octets par point.</figcaption>
</figure>

Avec $p_y \times p_x$ rangs, chaque frontière interne transporte deux messages (un par sens) de 8 octets par point de frontière. Le total par balayage s'écrit :

$$\text{octets} = 16\,\bigl[(p_y-1)\,n_x + (p_x-1)\,n_y\bigr] \qquad \text{messages} = 2\,\bigl[(p_y-1)\,p_x + (p_x-1)\,p_y\bigr]$$

Ces deux formules sont **vérifiées par comptage** dans le lab : `jacobi.c` compte les octets et messages réellement envoyés, et `verify.sh` exige l'égalité exacte pour la découpe 1D à 1, 5 et 8 rangs et la découpe 2D à 4, 6 et 9 rangs (grille de 96 × 96, rangs sur-souscrits : on compte, on ne chronomètre pas).

::: ex
[Exemple 5.1 — Les formules face aux compteurs]{.tag} Grille de $1536 \times 1536$, 30 balayages. Compteurs relevés dans l'étude du lab 3.3, comparés aux formules :

| Découpe | $p$ | Octets comptés | Formule $30 \times 16 \times (\dots)$ | Messages comptés |
|---|---|---|---|---|
| 1D | 2 | 737 280 | $30 \cdot 16 \cdot 1 \cdot 1536$ = 737 280 | 60 |
| 1D | 4 | 2 211 840 | $30 \cdot 16 \cdot 3 \cdot 1536$ = 2 211 840 | 180 |
| 2D (2 × 2) | 4 | 1 474 560 | $30 \cdot 16 \cdot (1536+1536)$ = 1 474 560 | 240 |

La découpe 2D envoie un tiers d'octets de moins que la 1D à $p = 4$. L'écart croît avec $p$ : par balayage et pour cette grille, `exercises/halo_sizing.py` donne 73 728 octets en 1D contre 49 152 en 2D à $p = 4$, 368 640 contre 147 456 à $p = 16$, et 1 548 288 contre 344 064 à $p = 64$.

Le rang le plus chargé envoie 24 576 octets en 1D quel que soit $p$, mais 6 144 octets en 2D à $p = 64$ : le volume de calcul d'un rang diminue avec $p$, la frontière 1D ne diminue pas.
:::

Attention à ne pas en conclure que 2D est toujours plus rapide. Il y a quatre messages au lieu de deux, les colonnes ne sont pas contiguës en mémoire (il faut un type dérivé ou un empaquetage), et à petit $p$ le volume échangé est négligeable devant le calcul, comme la section 5.4 le montre.

### 5.3. Recouvrir le calcul et la communication

Les points intérieurs d'un bloc ne dépendent d'aucun halo. On peut donc poster les échanges avec `Isend`/`Irecv`, calculer l'intérieur pendant que les messages voyagent, attendre, puis calculer le bord. Si l'échange dure moins que le calcul de l'intérieur, il est « caché » :

$$T_{\text{balayage}} \approx T_{\text{bord}} + \max\bigl(T_{\text{intérieur}},\ T_{\text{échange}}\bigr) \quad\text{contre}\quad T_{\text{calcul}} + T_{\text{échange}} \text{ sans recouvrement}$$

Le gain maximal est donc $\min(T_{\text{intérieur}}, T_{\text{échange}})$. Il est nul si l'échange est négligeable, et il ne peut pas dépasser le temps d'échange. Deux conditions pratiques : la bibliothèque doit faire progresser le transfert pendant que vous calculez (rappel du chapitre 3), et le bord ne doit pas être si gros que le calcul séparé coûte plus que le gain.

### 5.4. Mesurer où passe le temps

Le temps d'échange pur se mesure en supprimant l'arithmétique : l'option `--skip-sweep` de `jacobi.c` garde les messages et enlève le calcul.

::: ex
[Exemple 5.2 — Transfert ou attente ?]{.tag} Grille $1536 \times 1536$, 30 balayages, médiane de 9 répétitions. « Halo » est le temps passé dans l'échange (le maximum sur les rangs) dans le vrai calcul ; « échange seul » est le même échange sans arithmétique.

| $p$ | Halo dans le calcul (ms) | Échange seul (ms) | Rapport | Déséquilibre du calcul |
|---|---|---|---|---|
| 2 | 6,65 | 0,17 | 39 | 1,06 |
| 4 | 9,41 | 0,41 | 23 | 1,31 |

Le transfert lui-même coûte 6 µs par balayage à $p = 2$ et 14 µs à $p = 4$. Le reste, de l'ordre de 200 à 300 µs par balayage, est de l'**attente** : un rang qui finit plus tôt que son voisin attend dans l'échange.

Le « déséquilibre » est le rapport entre le temps de calcul du rang le plus lent et celui du plus rapide, alors qu'ils ont exactement le même nombre de points : 1,31 à $p = 4$.

Nous n'avons pas isolé la cause de cette différence entre rangs (mémoire partagée, ordonnancement du système, voisins sur l'hôte de la VM) : c'est une hypothèse, que le chapitre 8 range parmi les menaces à la validité.
:::

Une conséquence vérifiée par une autre expérience : demander la norme du résidu après **chaque** balayage (`--check-every 1`) ajoute deux `MPI_Allreduce` d'un nombre de 8 octets par balayage : un maximum et une somme, un par norme du résidu.

::: ex
[Exemple 5.3 — Deux all-reduce de 8 octets qui coûtent 0,6 ms par balayage]{.tag} `compare_variants.py` lance les variantes dans un ordre aléatoire, 15 répétitions, 4 rangs, grille $1536 \times 1536$, 30 balayages ; la machine était au repos au départ. Médianes :

| Variante | Temps (ms) | Minimum (ms) | Halo (ms) | All-reduce (ms) |
|---|---|---|---|---|
| bandes, échange bloquant | 31,7 | 27,4 | 4,86 | 0,22 |
| bandes, recouvrement | 30,4 | 28,1 | 3,47 | 1,23 |
| blocs 2D | 32,3 | 22,2 | 8,02 | 0,41 |
| blocs 2D, recouvrement | 37,3 | 23,6 | 13,15 | 0,64 |
| résidu à chaque balayage | 53,4 | 34,9 | 0,86 | 17,71 |

Les quatre premières lignes ne se distinguent pas de façon fiable : 31,7 contre 30,4 ms n'est pas une différence, et le classement des médianes (30,4 à 37,3 ms) n'est pas celui des minimums (22,2 à 28,1 ms). Le recouvrement ne pouvait d'ailleurs pas aider, puisque le transfert est plus de soixante-dix fois plus court que le balayage.

En revanche, le résidu à chaque balayage ajoute 68 % au temps total : 17,7 ms d'all-reduce pour 30 balayages, soit 0,59 ms par balayage et 0,30 ms pour chacun des 60 appels, alors qu'un all-reduce de 8 octets entre processus d'une même machine coûte quelques microsecondes (exemple 4.3). Ce temps est encore de l'attente : l'all-reduce est un point de rendez-vous où le retard du plus lent est payé par tous. Un test de convergence tous les 10 ou 100 balayages suffit presque toujours.
:::

::: recap
Points clés — chapitre 5

-   Chaque rang calcule son bloc et garde des cellules fantômes rafraîchies par un échange de halo avant chaque balayage.
-   Octets par balayage : $16[(p_y-1)n_x + (p_x-1)n_y]$ ; la découpe 2D l'emporte sur la 1D quand $p$ croît, pas forcément à petit $p$.
-   Recouvrir ne gagne que $\min(T_{\text{intérieur}}, T_{\text{échange}})$ : vérifiez d'abord que l'échange pèse quelque chose.
-   Mesurez l'échange seul (`--skip-sweep`) : ce qui dépasse est de l'attente, pas du transfert.
-   Un test de convergence à chaque pas est un point de synchronisation coûteux ; espacez-le.
:::

## 6. E/S parallèles et reproductibilité numérique : MPI-IO, sommes non associatives, graines {#ch6}

Un programme parallèle qui donne un résultat un peu différent à chaque exécution est difficile à déboguer, à valider et à comparer à une référence. Ce chapitre explique pourquoi les sommes changent avec le nombre de rangs, ce qu'on peut exiger, et comment écrire les résultats d'un calcul parallèle dans un fichier qui ne dépend pas de la façon dont on l'a lancé.

### 6.1. L'addition n'est pas associative

En arithmétique flottante, $(a + b) + c$ n'est pas toujours $a + (b + c)$, parce que chaque addition arrondit. Le script `exercises/fp_assoc.py` le montre :

~~~text
(0.1 + 0.2) + 0.3 = 0.6000000000000001
0.1 + (0.2 + 0.3) = 0.6
equal: False
(1e16 + 1) - 1e16 = 0.0    (1e16 - 1e16) + 1 = 1.0
~~~

Une réduction parallèle regroupe les termes selon le nombre de threads ou de rangs, donc selon $p$. Les deux normes le disent.

-   Pour OpenMP 6.0 (section 7.6.7), l'endroit et l'ordre de la combinaison ne sont pas spécifiés, et des résultats identiques bit à bit ne sont pas garantis, même avec le même nombre de threads.
-   Pour MPI 5.0 (section 6.9.1), l'implémentation peut profiter de l'associativité pour changer l'ordre d'évaluation, ce qui peut modifier le résultat des opérations qui ne sont pas strictement associatives et commutatives, comme l'addition flottante.

La même section de MPI recommande vivement qu'un appel répété avec les mêmes arguments, dans le même ordre, rende le même résultat. Ce n'est pas la même chose qu'un résultat indépendant de $p$.

### 6.2. Mesurer le phénomène

Le script `repro_sum.py` génère $10^6$ valeurs flottantes de magnitudes très variées, bloc par bloc, avec une graine qui ne dépend que du numéro de bloc (et donc pas de $p$). Il les somme de deux façons : **naïve** (chaque rang somme sa part avec numpy, puis `MPI_Allreduce`) et **à ordre fixe** (la somme de chaque bloc de 1 000 valeurs est calculée entière, toutes les sommes de blocs sont rassemblées et additionnées dans l'ordre des blocs). La référence est `math.fsum`, la somme correctement arrondie.

::: ex
[Exemple 6.1 — Mêmes données, six nombres de rangs]{.tag} Le résultat est écrit en hexadécimal flottant, qui montre chaque bit de la mantisse. Le pas entre deux flottants consécutifs à cette magnitude (de l'ordre de $2^{27}$) vaut $2^{-25} \approx 2{,}98\cdot 10^{-8}$.

| $p$ | Naïve | Erreur | À ordre fixe | Erreur |
|---|---|---|---|---|
| 1 | `-0x1.3f93a486735dbp+27` | −2,98e−08 | `-0x1.3f93a486735d9p+27` | +2,98e−08 |
| 2 | `-0x1.3f93a486735dbp+27` | −2,98e−08 | `-0x1.3f93a486735d9p+27` | +2,98e−08 |
| 3 | `-0x1.3f93a486735d8p+27` | +5,96e−08 | `-0x1.3f93a486735d9p+27` | +2,98e−08 |
| 4 | `-0x1.3f93a486735dbp+27` | −2,98e−08 | `-0x1.3f93a486735d9p+27` | +2,98e−08 |
| 5 | `-0x1.3f93a486735d8p+27` | +5,96e−08 | `-0x1.3f93a486735d9p+27` | +2,98e−08 |
| 8 | `-0x1.3f93a486735dbp+27` | −2,98e−08 | `-0x1.3f93a486735d9p+27` | +2,98e−08 |

La référence exacte est `-0x1.3f93a486735dap+27`. La somme naïve prend deux valeurs différentes selon $p$ (3 et 5 donnent la même, les autres une autre) ; la somme à ordre fixe est identique pour tous les $p$. Aucune des deux n'est exacte : l'ordre fixe se trompe d'un pas de flottant, mais **toujours du même**. Reproductible n'est pas synonyme de précis.

Ces mots hexadécimaux sont ceux de notre installation : NumPy ne garantit le même flux de nombres aléatoires que pour une même construction de la bibliothèque, et la sommation dépend du processeur. Chez vous, les valeurs changeront ; `verify.sh` contrôle seulement qu'il n'y a qu'une valeur à ordre fixe pour tous les $p$, et affiche le nombre de valeurs naïves distinctes sans l'exiger.
:::

### 6.3. Que peut-on exiger ?

Quatre stratégies, par ordre croissant de coût.

1.  **Tolérance.** Comparer deux exécutions avec une tolérance relative choisie et écrite (par exemple $10^{-12}$ pour des sommes de $10^6$ termes en double précision, ce qui est large par rapport aux écarts de quelques pas de flottant ci-dessus). C'est le choix par défaut, et celui des tests du lab.
2.  **Normes exactes.** Préférer, pour un critère de convergence, une grandeur qui se calcule sans arrondi de somme. Dans le lab, le résidu en norme max est identique pour tous les $p$ et toutes les découpes, alors que celui en norme 2 ne l'est qu'à $1{,}6 \cdot 10^{-14}$ près (relatif, quatre valeurs distinctes sur dix exécutions).
3.  **Ordre fixe indépendant de $p$.** Le schéma « blocs » ci-dessus : on fixe l'arbre d'addition sur les données, pas sur les rangs. Il coûte plus de communication (ici 1 000 sommes de blocs au lieu d'une) et suppose de choisir la taille des blocs.
4.  **Arithmétique exacte ou entière.** Une somme en virgule fixe sur des entiers est associative : le résultat est indépendant de l'ordre. Elle impose de borner la plage des valeurs.

Un champ calculé par un schéma local, sans réduction, est bit-reproductible par construction : le solveur de Jacobi donne la même empreinte (somme des motifs binaires des cellules, modulo $2^{64}$) pour 1 à 4 rangs, en 1D et en 2D, avec ou sans recouvrement, avec 2 threads par rang. C'est le test central de `verify.sh`.

La sommation compensée de Kahan améliore la précision d'une somme, pas sa reproductibilité à elle seule. Pour l'entraînement, les mêmes raisons valent pour la somme des gradients : l'ordre des additions dépend du nombre de GPU et de l'algorithme de la collective, donc deux entraînements identiques sur des configurations différentes ne suivent pas la même trajectoire bit à bit. C'est une conséquence de la non-associativité, pas une mesure faite ici.

### 6.4. Les graines

Si les données aléatoires dépendent du nombre de rangs, comparer deux exécutions n'a plus de sens. Règle : **associer la graine aux données, pas au rang**. Dans `repro_sum.py`, le bloc $b$ utilise `np.random.default_rng([2024, b])` : quelle que soit la façon dont les blocs sont répartis entre rangs, le jeu de données est le même. En entraînement, la même règle donne une graine par échantillon ou par fragment de données, et non par processus.

### 6.5. Écrire un fichier partagé avec MPI-IO

MPI-IO est la partie de la norme dédiée aux fichiers (chapitre 14). Tous les rangs ouvrent le **même** fichier ; chacun écrit sa tranche à un décalage calculé, avec un appel collectif (`Write_at_all`) que la bibliothèque peut agréger. La norme définit des indications (*hints*) pour cela, comme `collective_buffering`, `cb_nodes` et `cb_buffer_size` (section 14.2.8). Le fichier obtenu ne dépend pas du nombre de rangs.

::: ex
[Exemple 6.2 — Le même fichier pour 1 à 5 rangs]{.tag} `mpiio_demo.py` écrit le tableau $f(i) = i^2 + 7$ pour $i < 100\,003$ (entiers de 64 bits, soit 800 024 octets) avec des tranches de tailles inégales, puis relit le fichier avec numpy et le compare. Empreinte SHA-256 (16 premiers chiffres) pour $p = 1, 2, 3, 4, 5$ : `92a17901207de737` dans les cinq cas. Pour $p = 3$ les tranches ont 33 335, 33 334 et 33 334 éléments.
:::

Nous ne mesurons aucun débit d'écriture : sur cette VM, le cache de pages et le disque virtuel mis en cache par l'hôte décideraient du résultat (voir le module [Linux](../linux-systems/index.html) pour la mesure par compteurs).

Le compromis de conception est le suivant, à titre de recommandation. Un fichier par rang est simple et rapide à écrire, mais il lie le format au nombre de rangs et multiplie les fichiers. Un fichier partagé unique permet de redémarrer avec un autre nombre de rangs, au prix d'une coordination avec le système de fichiers que nous n'avons pas chiffrée. Le module [Tolérance aux pannes](../fault-tolerance/index.html) reprend ce choix pour les points de reprise.

::: recap
Points clés — chapitre 6

-   L'addition flottante n'est pas associative : toute réduction parallèle dépend de $p$ et de l'algorithme.
-   Les normes OpenMP et MPI ne garantissent pas l'identité bit à bit d'une réduction.
-   Exigez d'abord une tolérance écrite ; utilisez des normes exactes (max) ou un ordre fixe indépendant de $p$ si le bit à bit est nécessaire.
-   Un schéma local sans réduction (Jacobi) est bit-reproductible ; vérifiez-le par une empreinte.
-   La graine appartient aux données, pas au rang.
-   MPI-IO collectif écrit un fichier unique dont le contenu ne dépend pas du nombre de rangs.
:::

## 7. Hybride MPI+OpenMP, placement et binding ; lancement sous Slurm {#ch7}

Un nœud de calcul a de nombreux cœurs. On peut y lancer un rang MPI par cœur, ou un seul rang avec autant de threads, ou un compromis. Ce chapitre explique les raisons de chaque choix, comment s'assurer que les processus et les threads sont aux endroits voulus, et comment lancer le tout sous Slurm. Il utilise le lab 3.3 (parties A et C).

### 7.1. Pourquoi mélanger les deux

Un rang MPI par cœur est simple, mais chaque rang a ses cellules fantômes et ses messages. Avec un rang par nœud et des threads à l'intérieur, il y a moins de rangs, donc moins de frontières, moins de messages et moins de mémoire de halos. Les threads partagent la mémoire du rang, et il n'y a pas de message entre eux.

Le compteur d'octets de `hybrid_compare.py` donne l'effet exact : pour le même champ final, les octets envoyés dans les halos sur 4 cœurs valent 2 211 840 avec 4 rangs d'un thread, 737 280 avec 2 rangs de 2 threads, et 0 avec 1 rang de 4 threads (pas de frontière).

MPI doit savoir que des threads existent. La norme définit quatre niveaux (section 11.6) : `MPI_THREAD_SINGLE` (un seul thread), `MPI_THREAD_FUNNELED` (le processus a plusieurs threads, mais seul le thread principal appelle MPI), `MPI_THREAD_SERIALIZED` (plusieurs threads peuvent appeler MPI, un à la fois) et `MPI_THREAD_MULTIPLE` (sans restriction). Le solveur du lab n'appelle MPI qu'en dehors des régions OpenMP : le niveau `FUNNELED` suffit.

~~~c
    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);
~~~

### 7.2. Qui est où ?

Un processus ou un thread non lié peut être déplacé par le système d'un cœur à l'autre, ce qui vide ses caches et le met en concurrence avec les autres. La **liaison** (*binding*) fixe un processus ou un thread sur un ensemble de cœurs. Deux niveaux la décident : le lanceur (Slurm ou `mpirun`) pour les rangs, la bibliothèque OpenMP pour les threads à l'intérieur de chaque rang.

Open MPI montre ce qu'il a fait avec `--report-bindings`. Voici trois cas sur la VM de 4 cœurs, en sortie réelle (abrégée) :

~~~text
### mpirun -np 2 (liaison par défaut)
MCW rank 0 bound to socket 0[core 0[hwt 0]]: [B/././.]
MCW rank 1 bound to socket 0[core 1[hwt 0]]: [./B/./.]
### mpirun -np 4 (liaison par défaut)
MCW rank 0 is not bound (or bound to all available processors)
...
### mpirun -np 2 --map-by slot:PE=2 --bind-to core
MCW rank 0 bound to socket 0[core 0[hwt 0]], socket 0[core 1[hwt 0]]: [B/B/./.]
MCW rank 1 bound to socket 0[core 2[hwt 0]], socket 0[core 3[hwt 0]]: [././B/B]
~~~

Le défaut d'Open MPI 4.1.6 n'est pas le même avec 2 et avec 4 rangs : liés à un cœur chacun dans le premier cas, non liés dans le second. Nous l'avons observé, sans en lire la règle dans la documentation : ne vous y fiez pas, écrivez la liaison que vous voulez. L'option `--map-by slot:PE=n` réserve $n$ cœurs par rang, ce qui est la forme actuelle de `--cpus-per-proc` d'après la page de manuel de `mpirun`.

Côté OpenMP, `OMP_PLACES=cores` définit les emplacements (un par cœur) et `OMP_PROC_BIND=close` y place les threads côte à côte. `OMP_DISPLAY_AFFINITY=TRUE`, pris en charge par `libgomp` d'après sa documentation, affiche la liaison de chaque thread :

~~~text
### OMP_PROC_BIND=close OMP_PLACES=cores, 4 threads
level 1 thread 0x… affinity 0
level 1 thread 0x… affinity 1
level 1 thread 0x… affinity 2
level 1 thread 0x… affinity 3
### sans liaison
level 1 thread 0x… affinity 0-3
~~~

::: ex
[Exemple 7.1 — Mêmes cœurs, trois répartitions, une erreur de liaison]{.tag} `hybrid_compare.py --misbound` lance, dans un ordre aléatoire, 9 répétitions de chaque répartition de 4 cœurs sur la grille $1536 \times 1536$ (30 balayages). Les trois premières lignes sont correctement liées (`--map-by slot:PE=T --bind-to core`) ; les deux dernières mettent les $T$ threads de chaque rang sur un seul cœur (`--bind-to core` sans `PE`).

| Rangs × threads | Liaison | Médiane (ms) | Minimum (ms) | Octets de halo |
|---|---|---|---|---|
| 4 × 1 | correcte | 43,4 | 36,6 | 2 211 840 |
| 2 × 2 | correcte | 44,9 | 38,5 | 737 280 |
| 1 × 4 | correcte | 42,2 | 31,9 | 0 |
| 2 × 2 | un seul cœur | 72,0 | 65,6 | 737 280 |
| 1 × 4 | un seul cœur | 152,7 | 141,2 | 0 |

Le champ final a la même empreinte (`fbac34e1ef941f16`) dans toutes les lignes : une mauvaise liaison ne change pas le résultat, seulement le temps. Les trois répartitions bien liées sont indiscernables (42 à 45 ms) ; la mauvaise liaison coûte un facteur 1,6 pour 2 threads par rang et 3,6 pour 4 threads sur un cœur. Aucune erreur, aucun avertissement : seul `--report-bindings` ou l'étude des temps le révèlent.
:::

### 7.3. Mémoire et NUMA : ce que la VM ne montre pas

Sur un serveur à deux sockets, chaque socket a sa mémoire (un domaine NUMA) et un accès à la mémoire de l'autre est plus lent. Le système place généralement une page près du cœur qui la touche en premier : initialisez donc vos tableaux avec la même répartition de threads que le calcul (*first touch*). La règle usuelle est un rang par domaine NUMA et des threads à l'intérieur.

Nous ne pouvons pas le démontrer ici : `lscpu` montre un seul domaine NUMA, donc aucune mesure de cette VM ne dit rien du placement de la mémoire. Ce que vous lisez dans ce paragraphe est une recommandation générale, non vérifiée par ce module. Les sorties de `numactl --hardware` et de `lscpu` sont les premières choses à relever sur un nœud réel.

### 7.4. Lancer sous Slurm

Le guide MPI de Slurm distingue trois façons de lancer un programme parallèle dans une allocation.

1.  **Lancement direct** : `srun` démarre les tâches et initialise les communications par l'interface PMI-1, PMI-2 ou PMIx.
2.  **`mpirun` dans l'allocation, via Slurm** : `mpirun` démarre les processus avec l'infrastructure de Slurm (`srun`).
3.  **`mpirun` avec un autre mécanisme** (SSH, RSH) : les processus échappent à Slurm.

::: war
[Le troisième mode contourne Slurm]{.tag} Documenté dans le guide MPI de Slurm : dans le troisième cas, Slurm ne lance pas directement l'application, ce qui peut empêcher la liaison des tâches aux cœurs et la comptabilité, et le guide indique que ce n'est pas une méthode recommandée. Il recommande aussi `pam_slurm_adopt` pour que les processus lancés ainsi soient rattachés au job. Source : <https://slurm.schedmd.com/mpi_guide.html>.
:::

Le lab 3.3 (partie D, facultative) exécute les deux premiers modes sur le Slurm mono-nœud du module 5, version 23.11.4. Elle se fait après le lab 5.1, qui installe ce bac à sable : revenez-y pendant la phase 2. Le script `slurm_hybrid.sbatch` demande 2 tâches de 2 cœurs, fixe le nombre de threads d'après ce que Slurm a alloué, et lance `mpirun` dans l'allocation.

~~~bash
#!/usr/bin/env bash
#SBATCH --job-name=jacobi-hybrid
#SBATCH --ntasks=2
#SBATCH --cpus-per-task=2
#SBATCH --time=00:02:00
# Hybrid MPI+OpenMP job: one MPI rank per task, one OpenMP thread per CPU given to the task.
# JACOBI must point to the binary (mpicc -O2 -fopenmp -o jacobi jacobi.c -lm); MPIRUN_EXTRA may hold
# extra mpirun options (for example --allow-run-as-root in a disposable root-only container).
set -euo pipefail
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export OMP_PROC_BIND=close OMP_PLACES=cores
echo "slurm: ntasks=${SLURM_NTASKS} cpus_per_task=${SLURM_CPUS_PER_TASK} omp_threads=${OMP_NUM_THREADS}"
# Mode 2 of the Slurm MPI guide: mpirun starts the ranks through Slurm's infrastructure inside the allocation.
# shellcheck disable=SC2086  # MPIRUN_EXTRA is meant to be word-split
mpirun ${MPIRUN_EXTRA:-} --report-bindings --map-by "slot:PE=${OMP_NUM_THREADS}" --bind-to core \
  -np "${SLURM_NTASKS}" "${JACOBI:?set JACOBI to the jacobi binary}" --nx 400 --ny 400 --iters 20
~~~

Résultat réel de l'exécution (`bash slurm_launch.sh`, 25 octobre 2026) :

~~~text
task=0 cpus_per_task=2 affinity=0-3
task=1 cpus_per_task=2 affinity=0-3
direct launch refused by this Open MPI build, as documented: use mpirun inside the allocation (mode 2)
slurm: ntasks=2 cpus_per_task=2 omp_threads=2
MCW rank 0 bound to socket 0[core 0[hwt 0]], socket 0[core 1[hwt 0]]: [B/B/./.]
MCW rank 1 bound to socket 0[core 2[hwt 0]], socket 0[core 3[hwt 0]]: [././B/B]
OK slurm launch: allocation variables, bindings and field checksum (checksum=de84404792261c00) as expected
~~~

Trois constats se lisent dans cette sortie.

-   `affinity=0-3` : le Slurm du bac à sable utilise `TaskPlugin=task/none`, donc il n'impose aucune liaison. La documentation de `srun` indique que `--cpu-bind` ne sert qu'avec le greffon `task/affinity` ; ici, c'est `mpirun` qui lie.
-   Le lancement direct par `srun --mpi=pmi2` est refusé par l'Open MPI d'Ubuntu, avec le message « The application appears to have been direct launched using "srun", but OMPI was not built with SLURM's PMI support ». Pour le mode 1, la bibliothèque doit être compilée avec le support PMI ou PMIx de Slurm.
-   Le champ calculé sous Slurm a la même empreinte que le calcul à un rang.

`exercises/slurm_hybrid_2nodes.sbatch` montre la forme d'un job de deux nœuds (huit rangs de huit threads par nœud). Il est **seulement linté** (`bash -n`, `shellcheck`) : il demande deux nœuds que nous n'avons pas.

::: recap
Points clés — chapitre 7

-   L'hybride réduit les frontières : 4×1 envoie 2 211 840 octets de halo, 2×2 en envoie 737 280, 1×4 aucun.
-   MPI a quatre niveaux de threads ; `FUNNELED` suffit si seul le thread principal appelle MPI.
-   Écrivez la liaison : `--map-by slot:PE=T --bind-to core` pour les rangs, `OMP_PLACES` et `OMP_PROC_BIND` pour les threads, et vérifiez avec `--report-bindings` et `OMP_DISPLAY_AFFINITY`.
-   Une mauvaise liaison ne change pas le résultat mais multiplie le temps (1,6 à 3,6 ici).
-   Sous Slurm, `OMP_NUM_THREADS` doit suivre `SLURM_CPUS_PER_TASK` ; vérifiez si l'Open MPI sait être lancé directement par `srun`.
-   La VM n'a qu'un domaine NUMA : le placement mémoire n'est ni mesuré ni démontré ici.
:::

## 8. Étudier le passage à l'échelle : plan d'expérience, efficacité, goulots, rapport {#ch8}

Le module 2 a posé le protocole en sept étapes, les statistiques minimales et les pièges classiques. Ce chapitre les applique à un vrai solveur, du plan à l'interprétation, en rapportant aussi ce qui ne marche pas bien. Il suit la partie B du lab 3.3 et prépare le [Projet 2](../../projects/scaling-study/index.html). Le protocole est dans le [module 2, chapitre 8](../perf-models/index.html#ch8) : nous ne le répétons pas.

### 8.1. Question et prédiction, avant toute mesure

**Question.** Le solveur de Jacobi sur une grille de $1536 \times 1536$ points, 30 balayages, passe-t-il à l'échelle jusqu'à 4 cœurs, en passage à l'échelle fort (même grille) et faible (1 536 lignes de travail par rang) ?

**Modèle.** Le temps sur $p$ rangs est le temps séquentiel divisé par $p$, plus le transfert des halos mesuré par l'échange seul (section 5.4).

$$T_p \approx \frac{T_1}{p} + T_{\text{échange}}(p)$$

Avec $T_1 = 143{,}2$ ms et les échanges seuls de 0,17 ms (deux rangs) et de 0,41 ms (quatre rangs), la prédiction est un gain de 1,995 à deux rangs et de 3,95 à quatre.

Ce modèle oublie la mémoire. Le noyau fait 4 opérations flottantes par cellule et déplace au moins 16 octets (une lecture, une écriture), soit une intensité d'au plus $0{,}25$ FLOP par octet : il est limité par la mémoire, comme au module 2. À 2,0 ns par cellule en séquentiel, il utilise au moins 7,9 Go/s, du même ordre que le débit d'un cœur au chapitre 2 (7,3 Go/s), alors que quatre cœurs en tirent 24,9 Go/s, soit 3,4 fois plus. Une deuxième prédiction plafonne donc le gain à environ 3,4.

### 8.2. Le plan

-   Facteurs : $p \in \{1, 2, 4\}$ ; découpe 1D, et 2D pour $p=4$ ; fort et faible ; échange seul pour chaque $p$.
-   Neuf répétitions de chaque configuration, une de moins que la règle du module 2 (au moins dix) : c'est une menace à la validité (section 8.5). Ordre aléatoire à graine fixe (0), un seul `mpirun` par mesure.
-   Environnement fixé : Open MPI 4.1.6, GCC 13.3, `--bind-to core`, `OMP_NUM_THREADS=1`, 4 cœurs virtuels d'un Xeon à 2,8 GHz. La charge moyenne à 1 minute valait 1,04 au début, tâches précédentes de l'auteur incluses.
-   Estimateur : médiane, avec un intervalle de confiance à 95 % obtenu par rééchantillonnage ; gain $S = T_1/T_p$, efficacité $E = S/p$ et fraction de Karp-Flatt $e(p) = (1/S - 1/p)/(1 - 1/p)$ calculés sur les médianes.
-   Vérification préalable : le champ final doit avoir la même empreinte pour tous les $p$ (chapitre 6). Sinon on ne compare pas la même chose.

### 8.3. Résultats

Sortie de `analyze_study.py`, 9 répétitions, le 25 octobre 2026. Les temps sont en ms ; l'intervalle est celui de la médiane. Gain, efficacité et $e(p)$ sont calculés sur les temps non arrondis du fichier de l'étude : avec les médianes arrondies du tableau, $e(2)$ vaut 0,008 (exercice 11).

| Découpe | $p$ | Temps médian | Intervalle à 95 % | Gain $S$ | Efficacité $E$ | $e(p)$ |
|---|---|---|---|---|---|---|
| 1D | 1 | 143,2 | 136,6 à 158,4 | 1,00 | 1,00 | |
| 1D | 2 | 72,2 | 66,7 à 89,1 | 1,98 | 0,99 | 0,009 |
| 1D | 4 | 40,8 | 30,4 à 46,0 | 3,51 | 0,88 | 0,047 |
| 2D | 4 | 37,5 | 30,2 à 44,6 | 3,82 | 0,95 | 0,016 |

Passage à l'échelle faible (1 536 lignes de 1 536 points par rang, donc le travail par rang est constant) : 144,6 ms à $p=1$, 156,5 ms à $p=2$ (efficacité 0,92) et 170,2 ms à $p=4$ (efficacité 0,85).

<figure class="fig">
<svg viewBox="0 0 560 330" role="img" aria-labelledby="sp-t" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="sp-t">Gain du solveur de Jacobi, passage à l’échelle fort</title>
<line x1="62" y1="278" x2="540" y2="278" stroke="currentColor" stroke-width="1.5"/>
<line x1="62" y1="24" x2="62" y2="278" stroke="currentColor" stroke-width="1.5"/>
<line x1="62.0" y1="227.20188760939442" x2="540.0" y2="74.80755043757762" stroke="currentColor" stroke-width="1.5" stroke-dasharray="6 5" opacity="0.6"/>
<text x="524.0" y="68.80755043757762" text-anchor="end" font-size="14" fill="currentColor">idéal S = p</text>
<line x1="62.0" y1="278" x2="62.0" y2="283" stroke="currentColor"/>
<text x="62.0" y="300" text-anchor="middle" font-size="14" fill="currentColor">1</text>
<line x1="221.33333333333331" y1="278" x2="221.33333333333331" y2="283" stroke="currentColor"/>
<text x="221.33333333333331" y="300" text-anchor="middle" font-size="14" fill="currentColor">2</text>
<line x1="380.66666666666663" y1="278" x2="380.66666666666663" y2="283" stroke="currentColor"/>
<text x="380.66666666666663" y="300" text-anchor="middle" font-size="14" fill="currentColor">3</text>
<line x1="540.0" y1="278" x2="540.0" y2="283" stroke="currentColor"/>
<text x="540.0" y="300" text-anchor="middle" font-size="14" fill="currentColor">4</text>
<line x1="57" y1="278.0" x2="62" y2="278.0" stroke="currentColor"/>
<text x="53" y="283.0" text-anchor="end" font-size="14" fill="currentColor">0</text>
<line x1="57" y1="227.20188760939442" x2="62" y2="227.20188760939442" stroke="currentColor"/>
<text x="53" y="232.20188760939442" text-anchor="end" font-size="14" fill="currentColor">1</text>
<line x1="57" y1="176.4037752187888" x2="62" y2="176.4037752187888" stroke="currentColor"/>
<text x="53" y="181.4037752187888" text-anchor="end" font-size="14" fill="currentColor">2</text>
<line x1="57" y1="125.60566282818323" x2="62" y2="125.60566282818323" stroke="currentColor"/>
<text x="53" y="130.60566282818323" text-anchor="end" font-size="14" fill="currentColor">3</text>
<line x1="57" y1="74.80755043757762" x2="62" y2="74.80755043757762" stroke="currentColor"/>
<text x="53" y="79.80755043757762" text-anchor="end" font-size="14" fill="currentColor">4</text>
<line x1="57" y1="24.009438046972036" x2="62" y2="24.009438046972036" stroke="currentColor"/>
<text x="53" y="29.009438046972036" text-anchor="end" font-size="14" fill="currentColor">5</text>
<line x1="62.0" y1="232.0882329193205" x2="62.0" y2="224.75715013533713" stroke="var(--accent)" stroke-width="2"/>
<line x1="221.33333333333331" y1="196.37072263875683" x2="221.33333333333331" y2="168.9218590759623" stroke="var(--accent)" stroke-width="2"/>
<line x1="540.0" y1="119.89738946138982" x2="540.0" y2="38.37735849056605" stroke="var(--accent)" stroke-width="2"/>
<polyline fill="none" stroke="var(--accent)" stroke-width="2.5" points="62.0,227.2 221.3,177.3 540.0,99.8"/>
<circle cx="62.0" cy="227.2" r="5" fill="var(--accent)"/>
<circle cx="221.3" cy="177.3" r="5" fill="var(--accent)"/>
<circle cx="540.0" cy="99.8" r="5" fill="var(--accent)"/>
<text x="301.0" y="318" text-anchor="middle" font-size="14" fill="currentColor">processus MPI p</text>
<text x="16" y="151.0" text-anchor="middle" font-size="14" fill="currentColor" transform="rotate(-90 16 151.0)">gain S = T1 / Tp</text>
</svg>
<figcaption>Gain du solveur de Jacobi en passage à l'échelle fort (grille 1536 × 1536, découpe 1D) : médiane et intervalle de confiance à 95 % de la médiane, contre la droite idéale S = p. Le point à 4 rangs a un intervalle large : 9 répétitions ne suffisent pas à le resserrer.</figcaption>
</figure>

::: ex
[Exemple 8.1 — Prédit, mesuré, expliqué]{.tag} À $p = 4$ le temps idéal est $143{,}2/4 = 35{,}8$ ms ; le temps mesuré est 40,8 ms, soit 5,0 ms ou 14 % de plus. Le transfert des halos (échange seul, 0,41 ms) n'explique que 8 % de cet écart. Le reste est de l'attente : le rang le plus lent calcule 31 % plus longtemps que le plus rapide (déséquilibre 1,31, section 5.4), alors qu'ils ont la même charge.

La mesure se place entre la prédiction idéale ($S = 3{,}95$) et celle plafonnée par la mémoire ($S \approx 3{,}4$) : son intervalle (3,1 à 4,7 en gain) contient les deux. **L'étude ne tranche donc pas** entre les deux explications. Pour trancher, il faudrait plus de répétitions, ou une expérience qui sépare les deux effets, par exemple mesurer le débit mémoire de 4 processus du même programme sans communication.
:::

### 8.4. Lire les chiffres

**Karp-Flatt.** La fraction $e(p)$ passe de 0,009 à $p=2$ à 0,047 à $p=4$. Une vraie part séquentielle resterait constante ; une fraction qui croît désigne un coût qui augmente avec $p$ (module 2, chapitre 5) : ici l'attente liée au déséquilibre et à la mémoire, pas un morceau de code séquentiel.

**1D contre 2D.** La découpe 2D envoie un tiers d'octets de moins et affiche un meilleur gain (3,82 contre 3,51), mais les intervalles de confiance se recouvrent presque entièrement (30,2 à 44,6 ms contre 30,4 à 46,0 ms). Cette étude ne démontre pas de différence, et la section 5.4 explique pourquoi on n'en attend pas à $p=4$ : le transfert est négligeable.

**Passage à l'échelle faible.** Le travail par rang est constant, mais l'efficacité tombe à 0,85 à $p=4$. À ce stade nous ne savons pas dire si c'est la mémoire (les deux tableaux totalisent 151 Mo à quatre rangs contre 38 Mo à un rang, deux tailles supérieures au cache L3 de 33 Mio, soit 34,6 Mo : l'argument de capacité de cache ne suffit donc pas) ou l'attente. Une efficacité faible n'est pas un échec de l'étude, c'est la question suivante.

::: note
[Variabilité entre séances]{.tag} La même configuration (4 rangs, 1D, $1536^2$, 30 balayages) a donné une médiane de 40,8 ms dans cette étude et de 31,7 ms dans `compare_variants.py` lancé quelques dizaines de minutes plus tard, soit 29 % d'écart entre médianes.

La seconde valeur tombe pourtant dans l'intervalle de confiance de la première (30,4 à 46,0 ms, large d'environ 38 % de la médiane) : les deux mesures ne se distinguent pas statistiquement, et l'écart montre surtout qu'une médiane de neuf répétitions est très incertaine. Nous n'avons pas pu séparer une dérive de la machine (VM partagée) du simple bruit d'échantillonnage. Conséquence pratique : ne comparez que des mesures entrelacées dans la même séance, et rapportez la date.
:::

### 8.5. Rapport et menaces à la validité

Un rapport d'une page suffit : la question, la prédiction (avant la mesure), le protocole, le graphique avec intervalles, l'analyse de l'écart, les menaces. Voici les menaces de cette étude.

-   **Machine partagée.** Des charges étrangères ont pu tourner pendant les mesures ; l'écart entre séances ci-dessus en est peut-être un signe.
-   **Peu de répétitions.** Neuf mesures par point, une de moins que la règle du module 2, donnent des intervalles larges, surtout à $p=4$.
-   **Un seul nœud.** Les rangs se partagent un bus mémoire : aucune conclusion sur un réseau, la latence ou la topologie.
-   **Un seul problème.** Une grille de $1536^2$ et 30 balayages : les effets de cache seraient différents pour une autre taille.
-   **Cause non isolée.** Le déséquilibre entre rangs est mesuré, pas expliqué.

Le [Projet 2](../../projects/scaling-study/index.html) reprend ce plan pour un entraînement, avec un ajustement α-β de l'all-reduce. Les deux études sont comparables : mêmes statistiques, mêmes menaces, même discipline.

::: recap
Points clés — chapitre 8

-   Écrivez la prédiction avant de mesurer : ici $S(4) \approx 3{,}95$ idéal ou 3,4 avec plafond mémoire.
-   Répétitions entrelacées dans un ordre aléatoire, médiane et intervalle ; gain, efficacité et Karp-Flatt calculés sur les médianes.
-   Décomposez l'écart : transfert (échange seul), attente (déséquilibre), calcul (mémoire).
-   Un intervalle qui recouvre deux hypothèses ne les départage pas ; dites-le.
-   Une médiane de neuf répétitions est très incertaine, et la machine dérive peut-être d'une séance à l'autre : rapportez la date et ne comparez que des mesures entrelacées dans la même séance.
-   Nommez les menaces : machine partagée, peu de répétitions, un seul nœud, un seul problème.
:::

## Labs {#labs}

Les trois labs s'exécutent sur un portable ou une VM Linux jetable, **sans GPU** : GCC pour OpenMP, Open MPI et mpi4py pour MPI. Installation testée sur Ubuntu 24.04 :

~~~bash
sudo apt-get install -y gcc openmpi-bin libopenmpi-dev python3-venv
# Ubuntu 24.04 refuses system-wide pip installs (PEP 668): use a virtual environment.
python3 -m venv ~/pp-venv && . ~/pp-venv/bin/activate
python3 -m pip install numpy mpi4py
cd labs/parallel-programming/openmp-reduction && bash verify.sh
~~~

Chaque `verify.sh` sort avec le code 0 quand ses vérifications passent. Il affirme des résultats exacts, des compteurs et des propriétés de structure, **jamais une durée** : la machine peut être partagée. Les durées sont affichées pour que vous les analysiez. Les trois scripts ont été exécutés plusieurs fois le 25 octobre 2026 sur la VM de 4 cœurs décrite au chapitre 1 ; la partie D du lab 3.3 (Slurm) est facultative et se lance à part.

### Lab 3.1 — OpenMP : réduction, ordonnancement, faux partage, tâches {#lab-3-1}

::: lab

**Objectif.** Mesurer sur votre machine ce que le chapitre 2 affirme : une course de données, le coût de `critical` et `atomic`, l'effet d'un ordonnancement prédit par la charge, un faux partage compté par adresse, le prix d'une tâche. **Durée.** 4 h : partie A 1 h 30, B 1 h, C 1 h, D 30 min. **Prérequis matériels.** Un portable CPU de 4 cœurs ou plus, GCC ; aucun GPU, aucun coût.

1.  Partie A. Lisez `sum_variants.c`, compilez-le (`gcc -O2 -fopenmp -Wall -Wextra`) et lancez les huit variantes avec 1 et 4 threads. Reconstituez le tableau de la section 2.3 et calculez le gain de `reduction` contre sa propre ligne à 1 thread, puis contre la meilleure variante séquentielle.
2.  Partie B. Avec `schedule_demo`, lancez les six ordonnancements de l'exemple 2.3 (`OMP_SCHEDULE=...`). Pour chacun, comparez le temps prédit au temps mesuré, et lisez la chaîne `owner=` pour $N = 32$.
3.  Partie C. Avec `false_sharing`, mesurez `packed`, `padded` et `private` pour 1, 2 et 4 threads ; avec `fs_counters`, comparez `volatile` et `atomic`, compact et aligné. Retrouvez le nombre de lignes partagées avec `exercises/line_sharing.py`.
4.  Partie D. Avec `tasks_fib 32`, faites varier le seuil de 0 à 27 et relevez le nombre de tâches et le temps.
5.  Lancez `bash verify.sh` et lisez ses lignes « OK ».

**Critère de réussite.** `bash verify.sh` se termine par « OK openmp-reduction: results exact, assignments as specified, no timing asserted », avec notamment la ligne « OK schedules: static blocks / round-robin verified; triangular loop imbalance 1.750 (static) vs 1.001 (static,1) ». Sur une machine au repos, le temps prédit de `static` sur la boucle triangulaire est à moins de 30 % du temps mesuré. Votre tableau de la partie A contient les ralentissements de l'exemple 2.2 et les deux gains de la section 2.7 (contre la ligne à 1 thread, puis contre le meilleur séquentiel), avec vos valeurs.

**Pour aller plus loin.** Ajoutez `schedule(nonmonotonic:dynamic)`, `collapse(2)` sur une double boucle ou `taskloop`. Si vous disposez d'un serveur à deux sockets, ajoutez `numactl --interleave=all` et un premier accès parallèle : la VM du bac à sable n'a qu'un domaine NUMA et ne peut pas montrer cet effet.
:::

### Lab 3.2 — MPI : collectives, anneau fait main, interblocages, halo {#lab-3-2}

::: lab

**Objectif.** Lire un all-reduce en anneau écrit avec `Sendrecv` et en réécrire vous-même la phase *reduce-scatter*, prouver que l'anneau est juste et que ses compteurs suivent les formules, déclencher puis corriger des interblocages, échanger un halo et confronter le modèle α-β à la mesure. **Durée.** 4,5 h : partie A 1 h 30, B 1 h, C 1 h, D 1 h. **Prérequis matériels.** Un portable CPU de 4 cœurs, Open MPI, mpi4py, numpy ; aucun GPU, aucun coût.

1.  Partie A. Lancez `collectives_tour.py` sur 4 rangs et retrouvez la sortie du chapitre 4. Lisez `ringlib.py`, puis lancez `check_allreduce.py 1200` pour $p = 2, 3, 4, 5, 8$. Écrivez une variante qui fait seulement le *reduce-scatter* et vérifiez-la contre `Reduce_scatter_block`.
2.  Partie B. Lancez `deadlock_demo.py` pour les sept cas de l'exemple 3.1, sous `timeout` (5 s pour les cas bloquants). Puis relevez la limite eager avec `--mca btl_vader_eager_limit 65536` et notez les tailles qui passent.
3.  Partie C. Lancez `halo_stencil.py 203 30` pour $p = 1, 2, 3, 4$ et lisez les octets envoyés. Ajoutez un troisième schéma qui échange deux cellules de halo au lieu d'une.
4.  Partie D. Lancez `bench_allreduce.py` (4 rangs, `--max-exp 22`) puis `model_vs_measure.py`. Répétez trois fois et notez la plage du rapport mesure/modèle. Forcez les algorithmes 3, 4 et 6 de `MPI_Allreduce`.
5.  Lancez `bash verify.sh` (environ 45 s).

**Critère de réussite.** `bash verify.sh` se termine par « OK mpi-ring: collectives, ring and recursive doubling exact, counters match formulas, halo bitwise equal, deadlocks as documented ». Pour $p = 4$ et $n = 1200$ doubles, `check_allreduce.py` affiche « ring per rank: 6 messages, 14400 bytes ». Après les deux corrections de la section 4.5 (calibrage sur l'échange simultané et coût de la boucle Python), le rapport mesure/modèle de l'anneau reste sous 3 sur toute la plage.

**Pour aller plus loin.** Remplacez les rangs locaux par deux nœuds (`mpirun --hostfile`) et ajustez deux jeux $(\alpha, B)$, intra et inter nœud, pour le modèle à deux niveaux. Sur une machine à GPU, écrivez le même anneau avec `torch.distributed` et le backend `nccl`, et comparez à `all_reduce` : ce chemin n'est pas exécuté dans ce module.
:::

### Lab 3.3 — Jacobi 2D : décomposition de domaine et étude de passage à l'échelle {#lab-3-3}

::: lab

**Objectif.** Prouver qu'un solveur MPI+OpenMP donne le même champ pour toute décomposition, puis mener et rapporter une étude de passage à l'échelle, fort et faible, avec intervalles de confiance, en séparant calcul, transfert et attente. **Durée.** 3,5 h : partie A 1 h, B 1 h 30, C 1 h. **Prérequis matériels.** Un portable CPU de 4 cœurs, Open MPI, GCC, mpi4py, numpy ; aucun GPU, aucun coût. La partie D facultative demande en plus un conteneur jetable avec accès root et le Slurm du module 5 : faites-la après le lab 5.1.

1.  Partie A. Compilez `jacobi.c` (`mpicc -O2 -fopenmp`), lancez-le sur 1 à 4 rangs, en 1D et 2D, avec et sans `--overlap`, et comparez les empreintes. Lancez `repro_sum.py` pour $p = 1, 2, 3, 4, 5, 8$ et `mpiio_demo.py` pour $p = 1$ à 5. Lisez `check_jacobi.py`.
2.  Partie B. **Écrivez d'abord votre prédiction** (une page : $T_1$ mesuré, modèle, gains attendus à 2 et 4 rangs). Lancez `run_study.py --reps 9`, puis `analyze_study.py --svg speedup.svg`. Décomposez l'écart à la prédiction en transfert, attente et calcul, et rédigez la page de rapport avec ses menaces.
3.  Partie C. Lancez `hybrid_compare.py --misbound`, et `compare_variants.py`. Lisez `mpirun --report-bindings` et `OMP_DISPLAY_AFFINITY=TRUE` pour chaque répartition.
4.  Lancez `bash verify.sh` (environ 1 min). Facultatif : `RUN_SLURM=1 bash verify.sh` pour la partie D (lancement sous un vrai Slurm).

**Critère de réussite.** `bash verify.sh` se termine par « OK jacobi-scaling: field independent of decomposition, counters match formulas, study pipeline runs » et affiche la même empreinte pour toutes les décompositions. Votre rapport donne, pour chaque point, une médiane et un intervalle, une prédiction écrite avant la mesure, et l'efficacité à 4 rangs ; sur une machine au repos de 4 cœurs elle doit se situer entre 0,6 et 1,1, et vous expliquez tout écart à la prédiction.

**Pour aller plus loin.** Répétez l'étude avec 2 rangs de 2 threads, puis 1 rang de 4 threads. Si vous disposez de deux nœuds, lancez `exercises/slurm_hybrid_2nodes.sbatch` (jamais exécuté dans ce module) et ajoutez la latence réseau à la décomposition du temps.
:::

## Exercices {#ex}

Les corrigés renvoient aux scripts des labs : relancez-les pour vérifier. Toutes les valeurs des corrigés ont été calculées ou lues dans une sortie réelle.

::: exo
[Exercice 1 · ★ — Lire un nœud avant de le programmer]{.tag} Voici la sortie filtrée de `lscpu` d'un nœud **fictif**.

~~~text
CPU(s):              64
Thread(s) per core:  2
Core(s) per socket:  16
Socket(s):           2
NUMA node(s):        2
NUMA node0 CPU(s):   0-15,32-47
NUMA node1 CPU(s):   16-31,48-63
~~~

(a) Combien de cœurs physiques ? (b) D'après la section 1.3 (un rang MPI par nœud ou par socket, des threads OpenMP à l'intérieur), combien de rangs et combien de threads par rang proposez-vous pour ce nœud ? (c) Quelle commande vous donne la taille de la ligne de cache (exemple 1.2) ?
:::

::: sol
(a) $2 \times 16 = 32$ cœurs physiques, 64 threads matériels (2 par cœur).

(b) Un rang par socket, soit 2 rangs, chacun avec 16 threads (un par cœur physique de son socket). Ici chaque socket est aussi un domaine NUMA, avec sa propre mémoire : un rang par domaine garde les accès dans le domaine et ne laisse qu'une frontière à échanger. Le chapitre 7 (section 7.3) reprend et justifie ce choix.

C'est la recommandation usuelle, que la VM de ce module (un seul domaine) ne permet pas de mesurer. On la vérifie par `--report-bindings`. L'alternative de 4 rangs de 8 threads est défendable : on la départage par la mesure.

(c) `getconf LEVEL1_DCACHE_LINESIZE` : il rend 64 sur la VM d'essai. `lscpu` ne donne pas la taille de ligne.
:::

::: exo
[Exercice 2 · ★ — Reconnaître un ordonnancement]{.tag} Le programme `schedule_demo` (4 threads, $N = 32$) a imprimé quatre chaînes `owner=` : le caractère $i$ est le numéro du thread qui a exécuté l'itération $i$.

~~~text
A  00000000111111112222222233333333
B  00112233001122330011223300112233
C  01230123012301230123012301230123
D  03120312013201320132013201320132
~~~

(a) Retrouvez `OMP_SCHEDULE` pour A, B, C et D. (b) Laquelle des quatre n'est pas reproductible d'une exécution à l'autre ? (c) Pour une boucle où l'itération $i$ coûte $i+1$ unités, calculez le déséquilibre de A.
:::

::: sol
(a) A : `static` sans paquet (un bloc de 8 itérations par thread). B : `static,2` (paquets de 2 en tourniquet). C : `static,1`. D : `dynamic,1`, les paquets étant pris à mesure que les threads se libèrent. Ces chaînes viennent de `OMP_SCHEDULE=static`, `static,2`, `static,1` et `dynamic,1` avec `schedule_demo 32 uniform 2000`.

(b) D. La spécification fixe l'assignation de `static` (tourniquet en ordre de thread), pas celle de `dynamic`, qui dépend du moment où chaque thread est libre ; deux exécutions donnent deux chaînes différentes (nous avons obtenu `02130213...` dans une autre).

(c) Charges des quatre threads : 36, 100, 164 et 228 unités sur 528, moyenne 132, donc un déséquilibre de $228/132 = 1{,}727$ (`imbalance.py 32 4 static`). Le gain est au plus $4/1{,}727 = 2{,}32$.
:::

::: exo
[Exercice 3 · ★★ — Ajouter du remplissage ou non]{.tag} Chaque thread possède 7 compteurs de 8 octets (56 octets), rangés bout à bout dans un tableau aligné sur 64 octets. (a) Combien de lignes de cache sont partagées avec 8 threads ? avec 16 ? (b) Quel est le surcoût mémoire d'un remplissage (*padding*) à 64 octets par thread, pour 64 threads ? (c) Si chaque thread avait 12 compteurs (96 octets), combien de lignes seraient partagées avec 4 threads, et quel remplissage faudrait-il ? (d) Pourquoi la variante `private` du lab n'a-t-elle besoin d'aucun remplissage ?
:::

::: sol
(a) `line_sharing.py 8 56` donne 7 lignes partagées ; `line_sharing.py 16 56` en donne 14 (les cases se recalent toutes les 8, soit 7 lignes partagées par tranche de 8 threads).

(b) 64 octets au lieu de 56 : $+8$ octets par thread, soit $8/56 = 14{,}3\ \%$ ; pour 64 threads, $64 \times 64 = 4\,096$ octets au lieu de $3\,584$, soit 512 octets de plus. Le prix est négligeable devant le facteur 3,3 mesuré à l'exemple 2.4.

(c) 96 octets : 2 lignes partagées avec 4 threads, et un remplissage à 128 octets (deux lignes par thread), soit $+33{,}3\ \%$ (`line_sharing.py 4 96`).

(d) Chaque thread écrit dans un tableau local, sur sa propre pile, pendant la boucle ; la zone commune n'est écrite qu'une fois par thread à la fin, sous `critical`. Il n'y a pas d'écritures concurrentes sur une même ligne pendant le calcul.
:::

::: exo
[Exercice 4 · ★★ — Choisir un ordonnancement par le calcul]{.tag} Une boucle de $N = 1000$ itérations coûte $i+1$ µs à l'itération $i$, sur 4 threads. Calculez, pour `static`, `static,1` et `static,50`, la charge maximale d'un thread, le temps de la boucle (en supposant aucun coût d'ordonnancement), et le gain par rapport au temps séquentiel. Lequel choisissez-vous, et que vérifiez-vous avant de généraliser ?
:::

::: sol
Le temps séquentiel est $\sum (i+1) = 500\,500$ µs. `exercises/imbalance.py` donne :

| Ordonnancement | Charge max (µs) | Temps de la boucle | Déséquilibre | Gain |
|---|---|---|---|---|
| `static` | 218 875 | 218,9 ms | 1,749 | 2,29 |
| `static,1` | 125 500 | 125,5 ms | 1,003 | 3,99 |
| `static,50` | 143 875 | 143,9 ms | 1,150 | 3,48 |

`static,1` est le meilleur sur le papier ; `dynamic` ou `guided` donneraient un résultat proche en s'adaptant à un coût qu'on ne connaît pas à l'avance. Avant de généraliser, vérifiez que le coût réel suit la loi supposée et que le coût d'obtention d'un paquet (qui pénalise `dynamic,1`) reste petit devant celui d'une itération, avec `schedule_demo`.
:::

::: exo
[Exercice 5 · ★★ — Un anneau qui se fige]{.tag} Un collègue écrit un décalage en anneau : chaque rang envoie un tampon à son voisin de droite puis reçoit de celui de gauche.

~~~python
if mode == "send_recv":
    comm.Send(out, dest=right, tag=0)
    comm.Recv(inp, source=left, tag=0)
~~~

Avec 4 rangs et 8 octets, le programme (`exercises/ring_shift.py`) affiche « ok » quatre fois ; avec 1 Mio, il ne termine jamais et `timeout 5` rend le code 124. (a) Expliquez la panne, avec la règle de la norme. (b) Donnez trois corrections et dites laquelle vous choisiriez pour un halo. (c) Comment auriez-vous détecté la panne avec des messages de 8 octets ?
:::

::: sol
(a) Chaque rang commence par un `Send` standard. Avec 8 octets, le message est copié dans un tampon interne (sous la limite eager de 4 096 octets d'Open MPI) et le `Send` rend la main. Avec 1 Mio, il faut que la réception soit postée : tous les rangs sont dans `Send`, aucun n'est dans `Recv`, le cycle d'attente est complet. La norme (section 3.5) déconseille de compter sur la mise en tampon pour éviter l'interblocage.

(b) Trois corrections, toutes terminant avec 1 Mio sur 4 rangs (`ring_shift.py`) : l'ordre pair-impair (`parity`) ; un seul `Sendrecv` ; `Isend` puis `Recv` puis `Wait`. Pour un halo, `Sendrecv`, ou `Irecv`/`Isend` + `Waitall` si l'on recouvre le calcul.

(c) Remplacer `Send` par `Ssend` : `mpirun -np 4 python3 exercises/ring_shift.py ssend_recv 8` se bloque aussi à 8 octets (code 124 sous `timeout`). C'est le test du `Ssend` de la section 3.3.
:::

::: exo
[Exercice 6 · ★★ — Anneau ou doublement récursif ?]{.tag} Un all-reduce sur $p = 16$ rangs, avec $\alpha = 5\ \mu$s et $B = 25$ Go/s. Les temps modélisés sont :

$$T_{\text{anneau}} = 2(p-1)\,\alpha + \frac{2(p-1)}{p}\,\frac{n}{B} \qquad T_{\text{dbl}} = \log_2 p\,\Bigl(\alpha + \frac{n}{B}\Bigr)$$

(a) Calculez la taille de croisement $n^{*}$ donnée par le chapitre 4. (b) Quel algorithme pour un tampon de 256 Kio ? de 8 Mio ? (c) Donnez les deux temps pour 8 Mio.
:::

::: sol
(a) $\alpha B = 125\,000$ octets. Numérateur de la formule : $2 \times 15 - 4 = 26$. Dénominateur : $4 - 30/16 = 2{,}125$. Donc $n^{*} = 125\,000 \times 26/2{,}125 \approx 1\,529\,412$ octets (`crossover.py 16 5e-6 25e9`).

(b) 256 Kio $= 262\,144 < n^{*}$ : doublement récursif (61,9 µs contre 169,7 µs pour l'anneau). 8 Mio $= 8\,388\,608 > n^{*}$ : anneau.

(c) Pour l'anneau : 150 µs de latence plus $1{,}875 \times 335{,}5$ µs de transfert, soit 779,1 µs. Pour le doublement récursif : $4 \times (5 + 335{,}5)$ µs, soit 1 362,2 µs, 1,75 fois plus.

Ce sont des valeurs d'exemple et un modèle : une bibliothèque choisit pour vous, et le chapitre 4 montre que la mesure s'écarte du modèle d'un facteur 1,2 à 7 selon le cas.
:::

::: exo
[Exercice 7 · ★★★ — Un niveau ou deux ?]{.tag} Un entraînement **fictif** en parallélisme de données sur 8 nœuds de 8 GPU somme 14 Go de gradients à chaque pas ; le calcul d'un pas dure 7,0 s.

Paramètres **d'exemple** : dans un nœud, une latence de 2 µs et 300 Go/s ; entre nœuds, 10 µs et 25 Go/s.

(a) Calculez le temps d'un anneau plat sur 64 rangs, limité par le lien externe, et celui du modèle à deux niveaux de la section 4.6. (b) Donnez la part de la communication dans le pas, sans et avec recouvrement parfait. (c) Que devient le rapport avec un seul rang par nœud ? (d) Quelle validation exigez-vous avant de décider ?
:::

::: sol
(a) `hier_allreduce.py 14e9 8 8` : anneau plat 1 103,8 ms ; deux niveaux 204,3 ms, soit un facteur 5,4. Le terme externe de l'anneau plat porte tout le tableau ; dans le modèle à deux niveaux, chaque rang n'envoie que $n/8$ sur le réseau.

(b) Sans recouvrement : $7{,}0 + 1{,}104 = 8{,}104$ s avec l'anneau plat (communication : 13,6 %) et $7{,}0 + 0{,}204 = 7{,}204$ s avec deux niveaux (2,8 %). Avec recouvrement parfait, les deux communications sont plus courtes que le calcul : le pas dure 7,0 s dans les deux cas, et la différence disparaît tant qu'il reste de la marge.

(c) Avec $g = 1$ le deuxième niveau n'existe plus : rapport 1,00 (`hier_allreduce.py 14e9 8 1`).

(d) Le modèle est dérivé, pas mesuré ; ses paramètres sont des exemples. Il faut mesurer $\alpha_i, B_i, \alpha_o, B_o$ avec un ping-pong (chapitre 4), puis comparer au débit d'une collective réelle sur le matériel (module Réseaux), et vérifier que le recouvrement est effectif avant de compter sur le résultat de la ligne « avec recouvrement ».
:::

::: exo
[Exercice 8 · ★★ — Dimensionner un halo]{.tag} Grille de $8192 \times 8192$ points, 64 rangs. (a) Calculez avec `halo_sizing.py` le trafic de halo par balayage en 1D et en 2D, et le rang le plus chargé. (b) Avec $\alpha = 2$ µs, $B = 12$ Go/s (valeurs d'exemple) et 2,02 ns de calcul par point (mesuré au lab 3.3 en séquentiel), quelle part du balayage représente l'échange ? (c) À partir de quel nombre de rangs l'échange 1D dépasse-t-il 10 % du calcul ? (d) Que dit le recouvrement à 4 096 rangs en 2D ?
:::

::: sol
(a) `halo_sizing.py 8192 8192 64 2e-6 12e9` : 1D (64×1) : 8 257 536 octets et 126 messages au total, rang le plus chargé 131 072 octets en 2 messages ; 2D (8×8) : 1 835 008 octets et 224 messages, rang le plus chargé 32 768 octets en 4 messages.

(b) Un rang a $8192^2/64 = 1\,048\,576$ points, soit $2{,}02\ \text{ns} \times 1\,048\,576 \approx 2{,}12$ ms de calcul. Chaque message coûte $\alpha + n/B$ et ceux du rang le plus chargé s'additionnent (2 messages de 65 536 octets en 1D, 4 messages de 8 192 octets en 2D) :

$$T_{\text{1D}} = 2\Bigl(2\ \mu\text{s} + \tfrac{65\,536}{12\cdot 10^{9}}\ \text{s}\Bigr) = 14{,}9\ \mu\text{s} \qquad T_{\text{2D}} = 4\Bigl(2\ \mu\text{s} + \tfrac{8\,192}{12\cdot 10^{9}}\ \text{s}\Bigr) = 10{,}7\ \mu\text{s}$$

Cela fait 0,70 % du balayage en 1D et 0,51 % en 2D. Le recouvrement gagnerait au plus ces 0,7 %.

(c) Le calcul par rang est $2{,}02\ \text{ns} \times 8192^2 / p$ ; le halo 1D ne dépend pas de $p$ : 14,9 µs. L'échange atteint 10 % du calcul quand $135{,}6\ \text{ms}/p = 149\ \mu\text{s}$, soit $p \approx 910$ rangs (908 avec les valeurs non arrondies).

(d) À 4 096 rangs en 2D (64×64), le calcul par rang tombe à 33,1 µs et l'échange du rang le plus chargé à 8,3 µs, soit 25 % : le recouvrement peut maintenant gagner jusqu'à ces 8,3 µs, et le bord (non recouvrable) représente une fraction importante du bloc de 128×128 points.
:::

::: exo
[Exercice 9 · ★ — Pourquoi les sommes diffèrent]{.tag} Voici la sortie de `exercises/fp_assoc.py`.

~~~text
(0.1 + 0.2) + 0.3 = 0.6000000000000001
0.1 + (0.2 + 0.3) = 0.6
equal: False
(1e16 + 1) - 1e16 = 0.0    (1e16 - 1e16) + 1 = 1.0
~~~

(a) Expliquez les deux lignes de résultat. (b) Si trois rangs détiennent 0,1, 0,2 et 0,3, comment un all-reduce sur $p = 1$ puis sur $p = 3$ peut-il rendre deux valeurs différentes ? (c) Dans un test automatique, comparez-vous les deux sommes avec `==` ? Quelle tolérance relative proposez-vous, et sur quelle observation ?
:::

::: sol
(a) Chaque addition arrondit au flottant le plus proche. $0{,}1 + 0{,}2$ arrondit à un nombre légèrement plus grand que 0,3 ; l'autre regroupement n'arrondit pas de la même façon. Dans la dernière ligne, $10^{16} + 1$ arrondit à $10^{16}$ (le pas entre flottants à cette magnitude vaut 2), donc le 1 est perdu dans le premier regroupement et conservé dans le second.

(b) Un seul rang calcule $(0{,}1 + 0{,}2) + 0{,}3 = 0{,}6000000000000001$ ; un arbre qui additionne d'abord les rangs 1 et 2 calcule $0{,}1 + (0{,}2 + 0{,}3) = 0{,}6$. L'écart relatif est $1{,}85 \cdot 10^{-16}$, un pas de flottant.

(c) Non : `==` serait faux un jour sur deux. Une tolérance relative de $10^{-12}$ est cohérente avec l'observation du chapitre 6, sur $10^6$ termes de magnitudes très variées.

Les sommes naïves de $p = 1$ à 8 y diffèrent au plus de 3 pas de flottant, soit $8{,}9 \cdot 10^{-8}$ sur une somme de $1{,}68 \cdot 10^{8}$, environ $5{,}3 \cdot 10^{-16}$ en relatif. La tolérance laisse donc une marge de trois ordres de grandeur. C'est un choix qui se documente, pas une constante.
:::

::: exo
[Exercice 10 · ★★★ — Un job hybride lent et sans erreur]{.tag} Un collègue lance le solveur hybride avec `OMP_NUM_THREADS=2` sur 4 cœurs : `mpirun -np 2 ./jacobi ...`. Le job est correct mais 1,6 fois plus lent que prévu (72,0 ms contre 44,9 ms pour la même répartition correctement liée, médianes de 9 répétitions). `--report-bindings` affiche :

~~~text
MCW rank 0 bound to socket 0[core 0[hwt 0]]: [B/././.]
MCW rank 1 bound to socket 0[core 1[hwt 0]]: [./B/./.]
~~~

(a) Qu'est-ce qui ne va pas ? (b) Donnez la ligne `mpirun` corrigée. (c) Écrivez les directives `#SBATCH` et la commande de lancement pour 2 nœuds de 64 cœurs en 2 domaines NUMA de 32, avec 8 rangs de 8 threads par nœud. (d) Quelles trois vérifications faites-vous avant de lancer à grande échelle ?
:::

::: sol
(a) Chaque rang est lié à **un** cœur alors qu'il lance 2 threads : les 2 threads de chaque rang se disputent un cœur, et deux cœurs restent inoccupés. Aucun message d'erreur : le résultat est identique (même empreinte), seul le temps change. Le facteur 1,6 est inférieur à 2 : un noyau limité par la mémoire ne perd pas tout le débit en partageant un cœur (hypothèse non testée).

(b) `OMP_NUM_THREADS=2 mpirun -np 2 --map-by slot:PE=2 --bind-to core ./jacobi ...` ; le rapport devient `[B/B/./.]` et `[././B/B]`, comme dans la sortie du chapitre 7.

(c) `exercises/slurm_hybrid_2nodes.sbatch` (linté, jamais exécuté) :

~~~bash
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=8
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export OMP_PROC_BIND=close OMP_PLACES=cores
srun --cpu-bind=cores "${JACOBI:?set JACOBI to the jacobi binary}" --nx 16384 --ny 16384 --iters 100 --decomp 2d
~~~

$8 \times 8 = 64$ cœurs par nœud, et 4 rangs par domaine de 32 cœurs.

(d) Relire `--report-bindings` ou `OMP_DISPLAY_AFFINITY=TRUE` sur un petit job ; contrôler que l'Open MPI sait être lancé directement par `srun` (sinon passer par `mpirun` dans l'allocation) ; vérifier que le greffon de tâche de Slurm applique `--cpu-bind` (il est sans effet avec `task/none`).
:::

::: exo
[Exercice 11 · ★ — Gain, efficacité, Karp-Flatt]{.tag} Les médianes de l'étude du chapitre 8 en découpe 1D sont $T_1 = 143{,}2$ ms, $T_2 = 72{,}2$ ms et $T_4 = 40{,}8$ ms. Calculez le gain et l'efficacité à 2 et 4 rangs, et la fraction de Karp-Flatt $e = (1/S - 1/p)/(1 - 1/p)$. Que dit l'évolution de $e$ ?
:::

::: sol
`scaling_table.py 1:143.2 2:72.2 4:40.8` :

| $p$ | $S$ | $E$ | $e(p)$ |
|---|---|---|---|
| 2 | 1,98 | 0,99 | 0,008 |
| 4 | 3,51 | 0,88 | 0,047 |

(avec les temps non arrondis du fichier de l'étude, $e(2)$ vaut 0,009.) La fraction passe de moins de 1 % à presque 5 % : elle croît avec $p$, donc la perte n'est pas une part séquentielle constante mais un coût qui augmente avec le nombre de rangs (ici l'attente et la mémoire, chapitre 8).
:::

::: exo
[Exercice 12 · ★★★ — Combien de rangs pour ce job ?]{.tag} Une étude de passage à l'échelle **fictive** d'un solveur donne, pour $p = 1, 2, 4, 8, 16, 32, 64$ : 100, 51, 27, 15,5, 10,1, 7,9 et 7,5 s. Le coût est proportionnel à $p \times T$ (en cœurs-secondes, sans prix). (a) Calculez gain, efficacité et $e(p)$. (b) Que conclure sur la nature de la perte ? Proposez deux expériences pour la caractériser. (c) Un résultat est attendu en 12 s au plus : quel $p$ choisissez-vous, et à quel coût relatif ? (d) Sans échéance, quel $p$ choisissez-vous si vous exigez $E \ge 0{,}7$ ?
:::

::: sol
(a) `scaling_table.py 1:100 2:51 4:27 8:15.5 16:10.1 32:7.9 64:7.5` :

| $p$ | $S$ | $E$ | $e(p)$ | $p \times T$ |
|---|---|---|---|---|
| 2 | 1,96 | 0,98 | 0,020 | 102,0 |
| 4 | 3,70 | 0,93 | 0,027 | 108,0 |
| 8 | 6,45 | 0,81 | 0,034 | 124,0 |
| 16 | 9,90 | 0,62 | 0,041 | 161,6 |
| 32 | 12,66 | 0,40 | 0,049 | 252,8 |
| 64 | 13,33 | 0,21 | 0,060 | 480,0 |

(b) $e(p)$ croît de 0,02 à 0,06 : ce n'est pas une part séquentielle constante, c'est un coût qui augmente avec $p$ (communication, synchronisation, déséquilibre). Deux expériences : (1) la même exécution sans calcul (échange seul) pour séparer le transfert de l'attente ; (2) les temps de calcul de chaque rang (maximum et minimum) pour mesurer le déséquilibre. On y ajoute un passage à l'échelle faible pour distinguer un effet de taille de cache d'un effet de communication.

(c) $p = 8$ prend 15,5 s : trop long. $p = 16$ prend 10,1 s, et coûte 161,6 cœurs-secondes, 1,62 fois le coût séquentiel. $p = 32$ gagne encore 22 % de temps (7,9 s) mais coûte 56 % de plus que $p = 16$ (252,8). Réponse : $p = 16$, sauf si l'échéance a une marge très faible, auquel cas la variabilité entre séances (chapitre 8) rend risquée une prévision à 10,1 s.

(d) $E \ge 0{,}7$ : $p = 8$ ($E = 0{,}81$) ; $p = 16$ ($E = 0{,}62$) est en dessous du seuil. Ce choix est un compromis (seuil arbitraire) qu'il faut écrire dans le rapport.
:::

## Bilan de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux paralléliser une boucle avec OpenMP et justifier chaque clause.** Preuve : le tableau de la partie A du lab 3.1, avec la ligne de base séquentielle correcte.
-   **Je peux prédire l'effet d'un ordonnancement.** Preuve : le temps prédit et mesuré des six ordonnancements (lab 3.1 partie B) et l'exercice 4.
-   **Je peux écrire un échange MPI sans interblocage et dire pourquoi.** Preuve : la matrice de l'exemple 3.1 refaite et l'exercice 5.
-   **Je peux chiffrer une collective et la relier à NCCL.** Preuve : le lab 3.2 partie A (compteurs exacts) et l'exercice 6.
-   **Je peux décomposer un domaine et compter son halo.** Preuve : l'exercice 8 et la vérification des compteurs de `jacobi.c`.
-   **Je peux dire ce qu'est un résultat reproductible et en fixer la tolérance.** Preuve : l'exercice 9 et le tableau de l'exemple 6.1 refait.
-   **Je peux lancer un job hybride bien placé, sous `mpirun` et sous Slurm.** Preuve : `--report-bindings` d'un job correct et l'exercice 10.
-   **Je peux mener et rapporter une étude de passage à l'échelle.** Preuve : la page de rapport du lab 3.3 partie B avec prédiction, intervalles et menaces.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Notre job MPI de 64 rangs est deux fois plus lent que prévu. Par où commencez-vous ?* Réponse-type : écrire ce qu'on attendait (modèle), mesurer le gain et l'efficacité avec des intervalles, séparer calcul, transfert et attente (échange seul, temps de chaque rang), vérifier la liaison des processus (`--report-bindings`) et la variabilité entre exécutions, puis traiter le premier goulot.
2.  *Un entraînement distribué se fige sans erreur. Quelles pistes ?* Réponse-type : une collective où un rang manque ou diverge (appels dans un ordre différent, rang planté), un `Send` standard qui se bloque avec de gros messages, un rang en retard ou un nœud dégradé ; on regarde où chaque rang attend, avec un délai d'expiration et le test du `Ssend`.
3.  *Deux exécutions donnent des pertes qui diffèrent à la sixième décimale. Est-ce un bogue ?* Réponse-type : pas nécessairement. L'addition flottante n'est pas associative et l'ordre d'une réduction dépend de la configuration ; on exige d'abord une tolérance écrite, puis un ordre fixe indépendant de $p$ si le bit à bit est nécessaire, en vérifiant par une empreinte du champ.

## Lectures et références {#refs}

-   OpenMP Architecture Review Board. *OpenMP Application Programming Interface, version 6.0*, novembre 2024. [PDF](https://www.openmp.org/wp-content/uploads/OpenMP-API-Specification-6-0.pdf) : section 7.6.7 (ordre des réductions), section 13.6.3 (clause `schedule`), tableau des variables de contrôle (chapitres 2 et 6).
-   MPI Forum. *MPI: A Message-Passing Interface Standard, version 5.0*, approuvée le 5 juin 2025. [PDF](https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report.pdf) : sections 3.2.7, 3.4, 3.5, 6.9.1, 11.6 et chapitre 14 (chapitres 3, 4, 6 et 7).
-   Patarasuk, Yuan. *Bandwidth optimal all-reduce algorithms for clusters of workstations*. Journal of Parallel and Distributed Computing 69, 2009. [version de l'auteur](https://www.cs.fsu.edu/~xyuan/paper/09jpdc.pdf) : borne inférieure et anneau, avec l'hypothèse d'associativité (chapitres 4 et 6).
-   NVIDIA. *NCCL User Guide* : [Collective Operations](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/collectives.html), [NCCL and MPI](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/mpi.html) et [Environment Variables](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html) : identités entre collectives, différences avec MPI, `NCCL_ALGO` (chapitre 4).
-   PyTorch. [*Distributed communication package — torch.distributed*](https://docs.pytorch.org/docs/2.14/distributed.html) (version 2.14) : les backends `gloo`, `mpi`, `nccl` (chapitre 4).
-   SchedMD. [*MPI Users Guide*](https://slurm.schedmd.com/mpi_guide.html) et [*srun*](https://slurm.schedmd.com/srun.html) : les trois modes de lancement, `--cpu-bind`, `--cpus-per-task` (chapitre 7).
-   Open MPI. [*mpirun(1)*](https://www.open-mpi.org/doc/v4.1/man1/mpirun.1.php) (page de manuel 4.1) : `--bind-to`, `--map-by`, `--oversubscribe`, `--report-bindings` (chapitres 3 et 7).
-   GNU. [*libgomp : variables d'environnement OpenMP*](https://gcc.gnu.org/onlinedocs/libgomp/Environment-Variables.html) : `OMP_SCHEDULE`, `OMP_PROC_BIND`, `OMP_PLACES`, `OMP_DISPLAY_AFFINITY` (chapitres 2 et 7).
-   Hoefler, Belli. *Scientific Benchmarking of Parallel Computing Systems: Twelve Ways to Tell the Masses when Reporting Performance Results*. SC15, 2015. [page de l'article](https://evaluate.inf.usi.ch/node/366) : le protocole de rapport du chapitre 8.
-   IDRIS (CNRS). Supports de cours [MPI](http://www.idris.fr/docs/formations/hpc/formation-mpi), [OpenMP](http://www.idris.fr/docs/formations/hpc/formation-openmp) et [hybride MPI/OpenMP](http://www.idris.fr/docs/formations/hpc/formation-hybride-mpi-openmp) : cours publics en français, avec travaux pratiques, pour approfondir chaque chapitre.
-   UC Berkeley. [*CS267, Applications of Parallel Computers*](https://sites.google.com/lbl.gov/cs267-spr2025) : cours de référence sur la programmation parallèle pour la science et l'ingénierie ; à lire après ce module pour les algorithmes denses et creux.

## Sources et portée {#sources}

### Documenté {#documente}

Les faits suivants ont été lus à la source le 25 octobre 2026. OpenMP 6.0 (novembre 2024) : la section 7.6.7 sur l'ordre non spécifié des combinaisons d'une réduction, la section 13.6.3 sur les clauses `schedule` et le comportement sans clause, le tableau des variables de contrôle (nombre de threads par défaut laissé à l'implémentation). MPI 5.0 (5 juin 2025) : le non-dépassement des messages, les modes d'envoi (3.4), la règle de la mise en tampon (3.5), l'envoi-réception combiné (3.2.7), l'avis sur la reproductibilité de `MPI_REDUCE` (6.9.1), les niveaux de threads (11.6), les indications `collective_buffering` et `cb_nodes` (14.2.8). Patarasuk et Yuan : borne inférieure et hypothèse d'associativité. NCCL : les équivalences de collectives, les différences avec MPI, la remarque sur la progression, les valeurs de `NCCL_ALGO`. PyTorch 2.14 : le backend MPI optionnel et le conseil d'utiliser Gloo. Slurm : les trois modes de lancement, la note sur `--cpu-bind`. Open MPI : `--map-by ...:PE=n` remplace `--cpus-per-proc`, `--oversubscribe`, nombre de places égal au nombre de cœurs. Les valeurs de `ompi_info` (limite eager de 4 096 octets, liste des six algorithmes d'all-reduce) viennent de la machine d'essai.

Tous les chiffres des exemples et des corrigés viennent d'une exécution des scripts des labs sur la VM décrite au chapitre 1 (4 cœurs virtuels d'un Xeon à 2,8 GHz, Linux 6.18, GCC 13.3, Open MPI 4.1.6, mpi4py 4.1.2, PyTorch 2.14.1 pour CPU), le 25 octobre 2026, ou d'un calcul refait en Python. Les trois `verify.sh` ont été exécutés plusieurs fois avec succès ; le script Slurm de la partie D l'a été avec Slurm 23.11.4.

### Recommandé {#recommande}

L'ordre des chapitres, les analogies avec l'entraînement (chapitre 1), le « test du `Ssend` » comme usage de la règle de la norme, la tolérance relative de $10^{-12}$ proposée, la règle « un rang par domaine NUMA », le choix entre fichier partagé et fichier par rang, le plan d'étude du chapitre 8 et les seuils des exercices sont des choix pédagogiques de ce parcours, pas des normes.

### À vérifier {#a-verifier}

(1) L'article de Thakur, Rabenseifner et Gropp (2005) sur les algorithmes de collectives de MPICH est cité de mémoire : l'éditeur et l'hébergeur ont répondu 403, il n'a pas été rouvert. Les algorithmes d'Open MPI ne sont donc que nommés d'après `ompi_info` (dont Rabenseifner), jamais décrits. (2) La borne $\max(W/p, T_\infty)$ et l'encadrement $W/p + T_\infty$ de l'ordonnancement glouton sont des résultats classiques non rouverts pour ce module. (3) Les explications suivantes sont des hypothèses non testées : le mécanisme exact de la course de données (registre du compilateur), l'absence de faux partage mesurable avec des écritures `volatile`, la cause du déséquilibre de 1,31 entre rangs, le facteur de 7,4 du doublement récursif sur 2 Mio, le facteur 1,6 d'une mauvaise liaison. (4) La règle de liaison par défaut d'Open MPI (liés à un cœur avec 2 rangs, non liés avec 4) est observée, non lue dans la documentation. (5) Le seuil eager de 4 096 octets et le blocage des envois croisés sont propres à Open MPI 4.1.6 et à son transport mémoire partagée. (6) Le modèle à deux niveaux est dérivé, ses paramètres sont des exemples. (7) Le placement NUMA et le *first touch* ne sont pas démontrés : la VM n'a qu'un domaine. (8) L'écart de 29 % entre deux médianes de la même configuration, mesurées à quelques dizaines de minutes d'intervalle, n'est pas expliqué (dérive de la machine ou bruit d'échantillonnage : les deux intervalles se recouvrent). (9) Les versions changent : relisez les pages des normes et des bibliothèques à la date de votre lecture.

### Hors périmètre {#hors-perimetre}

Les communications unilatérales (RMA), les communications partitionnées et les sessions de MPI 4 et 5 ; MPI sensible aux GPU et les noyaux GPU (module de programmation GPU) ; l'exécution multi-nœuds réelle, le réseau et la topologie (module Réseaux) ; les systèmes de fichiers parallèles et leur réglage (module Stockage) ; le parallélisme d'un modèle de langage, de données, de tenseurs et de pipeline (module d'entraînement distribué) ; le délestage OpenMP vers un GPU (`target`), les dépendances de tâches et `taskloop` au-delà de leur mention ; le Fortran ; l'hyperthreading ; les cours EPCC cités par le programme, non rouverts ici.
