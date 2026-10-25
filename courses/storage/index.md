---
title: "Stockage et E/S pour l'entraînement"
subtitle: "Module 08 · Phase 2 · 24 h"
description: "Nourrir les GPU et sauvegarder sans les arrêter : systèmes de fichiers parallèles, objet, formats de données, chargeurs, checkpoints et caches, avec des mesures par compteurs."
module:
  id: storage
  number: 8
  phase: 2
  hours: 24
  level: 2
prerequisites: [linux-systems]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs vérifiés dans un bac à sable (disque local, pas de système de fichiers parallèle)", class: verified}
labs:
  - {id: loader-bottleneck, kind: sandbox}
  - {id: shard-format, kind: sandbox}
  - {id: checkpoint-io, kind: sandbox}
  - {id: io-sizing, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** votre entraînement de 256 GPU est-il lent parce que les GPU attendent leurs données, ou parce qu'un checkpoint arrête tout le monde toutes les demi-heures ? Dans les deux cas, la réponse tient dans trois nombres que l'on peut mesurer : un débit, une taille de requête et un nombre d'opérations de métadonnées.

Ce module vous apprend à **dimensionner** le stockage d'un entraînement (lecture du jeu de données, écriture et relecture des checkpoints), à **choisir** entre système de fichiers parallèle, NFS et stockage objet, à **diagnostiquer** un chargeur de données lent et à **concevoir** un cache. Les mesures viennent d'une machine Linux sans GPU, avec des compteurs du noyau plutôt qu'avec des chronomètres.

Ce module ne remplace pas le module 10 sur les pannes : le protocole d'un checkpoint correct (atomicité, intégrité, reprise) y est traité. Ici, on s'occupe de ce que le checkpoint **coûte au stockage** et de ce que le stockage **coûte à l'entraînement**.

::: key
[Règle de ce module]{.tag} Ne croyez aucun débit que vous n'avez pas mesuré avec un compteur, et ne changez pas de matériel avant d'avoir changé le motif d'accès. Passer de millions de petites lectures à quelques grosses lectures séquentielles rapporte plus qu'un stockage dix fois plus cher.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 24 h : environ 9,5 h de lecture, 9,25 h de labs, 3,5 h d'exercices et 0,5 h de bilan de sortie, soit 22,75 h, plus une marge d'environ 1 h répartie sur les séances |
| Niveau d'entrée | 2 : à l'aise avec Linux en ligne de commande (module 1) et avec PyTorch |
| Prérequis | [Module 1 — Linux, systèmes et diagnostic](../linux-systems/index.html), en particulier le chapitre 7 sur le cache de pages et `fio` |
| Statut pour le lecteur de référence | cœur : vous connaissez les chargeurs PyTorch, mais pas les systèmes de fichiers parallèles ni la dimension E/S d'un checkpoint à grande échelle |
| Livrable | un rapport de dimensionnement E/S d'un entraînement (lecture, checkpoint, cache, capacité) et la table de décision du chargeur appliquée à une mesure |
| Environnement | un portable ou une VM Linux sans GPU ; `fio`, PyTorch CPU et `pytest` ; `pyarrow` et `webdataset` en option. Les parties qui demandent un GPU (`pin_memory`, GPUDirect Storage) ou un vrai système de fichiers parallèle sont décrites, **pas exécutées** |
| Projets liés | [Projet 3 — Entraîneur tolérant aux pannes](../../projects/resilient-trainer/index.html), [Projet 6 — RFC de plateforme](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Estimer le débit de lecture d'un entraînement et le débit d'écriture d'un checkpoint à partir de la taille d'un échantillon, du nombre de GPU et de la période de sauvegarde (chapitre 1, lab 8.4).
-   Dire ce qu'est un système de fichiers parallèle, et régler le *striping* d'un fichier à partir d'un besoin de débit (chapitre 2).
-   Comparer NFS, stockage objet et passerelles FUSE sur la cohérence, la latence, les métadonnées et le coût, sans chiffre de fournisseur non sourcé (chapitre 3).
-   Chiffrer l'amplification de lecture d'un format de données (fichiers, shards, fichier empaqueté, Parquet) avec des compteurs (chapitre 4, lab 8.2).
-   Diagnostiquer un entraînement limité par ses données : part d'attente, workers, CPU, profileur (chapitre 5, lab 8.1).
-   Modéliser le coût bloquant d'un checkpoint synchrone et asynchrone, et dimensionner son débit (chapitre 6, lab 8.3).
-   Prévoir le taux de succès d'un cache et concevoir un cache à plusieurs niveaux (chapitre 7).
-   Planifier capacité, rétention, quotas et sauvegardes d'un programme d'entraînement (chapitre 8).

### Plan de séances {#seances}

Huit séances de 3 h, soit 24 h. Chaque séance contient ses chapitres, son lab (ou sa partie de lab) et ses exercices dans sa durée, avec une marge. Le niveau 1 correspond aux fondations, le niveau 2 aux méthodes de cœur, le niveau 3 à l'avancé : il ne diminue jamais.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 3 h | 1 | ch. 1 Besoins d'E/S d'un entraînement ; questions de positionnement | Lab 8.4 partie A ; Ex. 1, 2 |
| 2 | 3 h | 1 | ch. 2 Systèmes de fichiers parallèles ; ch. 3 NFS, objet, FUSE | Ex. 3, 4, 5 |
| 3 | 3 h | 2 | ch. 4 Formats de données | Lab 8.2 partie A ; Ex. 6 |
| 4 | 3 h | 2 | ch. 5 Chargeurs de données | Lab 8.2 partie B ; Ex. 7 |
| 5 | 3 h | 2 | révision des chapitres 4 et 5 | Lab 8.1 ; Ex. 8 |
| 6 | 3 h | 2 | ch. 6 E/S de checkpoint | Lab 8.3 parties A, B et D ; Ex. 9 |
| 7 | 3 h | 3 | ch. 7 Mise en cache | Lab 8.3 partie C ; Lab 8.4 partie B |
| 8 | 3 h | 3 | ch. 8 Capacité, durée de vie, coût ; checkpoint de sortie | Ex. 10, 11, 12 |

## Avant de commencer {#avant}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si elles vous semblent routinières, parcourez les exercices ★★★ et passez au module suivant.

1.  **Où est le débit ?** Un entraînement de texte déjà découpé en jetons de 2 octets tourne sur 256 GPU, chacun consommant 8 000 jetons par seconde. Quel débit de lecture cela représente-t-il ? Et le checkpoint d'un modèle de 70 milliards de paramètres, à 14 octets par paramètre ?

2.  **Petits fichiers.** Pourquoi lire 4 096 fichiers de 16 Kio est-il plus coûteux que lire une archive de 64 Mio qui contient les mêmes octets, même sur un disque rapide ?

3.  **Attente.** Un job laisse ses GPU inactifs 85 % du temps, en attente de données. Quelle est la première mesure à faire avant d'ajouter des workers au chargeur ?

::: sol
**Réponses.**

1.  Le texte demande $256 \times 8000 \times 2 = 4{,}1$ Mo/s, soit presque rien : la lecture d'un jeu de texte pré-tokenisé n'est pas le problème. Le checkpoint pèse $70 \cdot 10^{9} \times 14 = 980$ Go, qu'il faut écrire en rafale. C'est lui qui dimensionne le stockage (chapitres 1 et 6).

2.  Chaque fichier coûte au moins une ouverture, une lecture et une fermeture, soit des opérations de métadonnées et des requêtes de petite taille. Le temps d'une requête vaut $\alpha + n/B$ : pour $n$ petit, c'est la latence $\alpha$ qui domine (chapitres 3 et 4).

3.  Mesurer où le temps d'attente passe : la part d'attente (*stall*) de la boucle, puis le CPU réellement consommé par les workers. Des workers qui dorment sont limités par la latence ; des workers à 100 % de CPU sont limités par le calcul de prétraitement, et en ajouter ne sert à rien (chapitre 5).
:::

## 1. Besoins d'E/S d'un entraînement {#ch1}

Avant de choisir un système de fichiers, il faut savoir ce qui doit y passer. Ce chapitre découpe l'entraînement en quatre flux d'E/S, rappelle les trois grandeurs qui les décrivent et pose les deux formules de dimensionnement qui servent dans tout le module.

### 1.1. Quatre flux

Un entraînement n'a pas *une* charge de stockage, mais quatre, qui n'ont ni les mêmes motifs d'accès ni les mêmes victimes.

| Flux | Motif d'accès | Ce qui le rend difficile |
|---|---|---|
| Jeu de données | lecture, répétée à chaque époque, souvent dans un ordre aléatoire | latence par échantillon, nombre de fichiers, cache |
| Checkpoint | écriture en rafale par tous les rangs à la fois, relecture à la reprise | débit agrégé ; bloque l'entraînement |
| Journaux et métriques | petites écritures continues, parfois dans un fichier partagé | verrous, nombre de fichiers créés |
| Artefacts (code, conteneurs, environnements) | lecture simultanée par tous les nœuds au démarrage | tous les nœuds demandent les mêmes fichiers au même instant |

Le jeu de données est un flux **chronique** : il dure toute la campagne et son débit se lisse. Le checkpoint est un flux **aigu** : il est bref, synchronisé entre tous les rangs, et c'est son pic qui dimensionne le stockage. Les deux autres sont petits en octets mais grands en nombre d'opérations.

### 1.2. Trois grandeurs, un modèle

Trois grandeurs décrivent un accès au stockage : le **débit** $B$ en octets par seconde, la **latence** $\alpha$ du premier octet, et le **nombre d'opérations** par seconde (IOPS pour les blocs, opérations de métadonnées pour les fichiers). Le temps d'une requête de $n$ octets vaut

$$T(n) = \alpha + \frac{n}{B}$$

C'est le modèle α-β du [chapitre 6 du module 2](../perf-models/index.html#ch6) ; la loi de Little du [chapitre 7 du module 1](../linux-systems/index.html#ch7) relie le nombre de requêtes en vol au débit et à la latence. De ces formules sort la **taille de demi-performance** $n_{1/2} = \alpha B$ : une requête de cette taille n'atteint que la moitié du débit maximal, une requête dix fois plus petite en atteint moins de 10 %.

Retenez la conséquence : un système peut afficher un débit maximal élevé et délivrer très peu à qui lui envoie de petites requêtes. Le chapitre 4 mesure ce phénomène sur un disque.

### 1.3. Dimensionner la lecture

Le débit de lecture à fournir est le produit du nombre de consommateurs, du rythme de chacun et de la taille d'un échantillon :

$$B_{\text{lecture}} = N_{\text{GPU}} \times r_{\text{échantillons/s}} \times s_{\text{octets}}$$

::: ex
[Exemple 1.1 — Texte, images, vidéo sur 256 GPU]{.tag} Les entrées sont des **valeurs d'exemple**, pas des mesures de produits. Calculées avec `iosizing.py demo` (lab 8.4).

| Charge | Hypothèses par GPU | Débit agrégé |
|---|---|---|
| texte tokenisé | 8 000 jetons/s, 2 octets par jeton | 4,1 Mo/s |
| images | 3 000 images/s, 110 ko par image | 84,5 Go/s |
| clips vidéo | 20 clips/s, 2 Mo par clip | 10,2 Go/s |

Le texte pré-tokenisé demande un débit négligeable ; les images en demandent plus de vingt mille fois plus. Deux charges de « calcul d'IA » n'ont donc pas le même problème de stockage. Pour le texte, ce sont le nombre de fichiers et le checkpoint qui comptent ; pour les images et la vidéo, c'est aussi le débit.
:::

Le débit moyen ne dit rien du nombre de fichiers : 3 000 images par seconde sur 256 GPU, ce sont près de 770 000 ouvertures de fichier par seconde si chaque image est un fichier. Les chapitres 2 à 4 reviennent sur ce point.

### 1.4. Dimensionner le checkpoint

Pour un modèle de $\Psi$ paramètres entraîné avec Adam en précision mixte, le [papier ZeRO](https://arxiv.org/abs/1910.02054) compte 2 octets par paramètre pour les poids en demi-précision, 2 pour les gradients et 12 pour l'état de l'optimiseur. Un checkpoint n'a pas besoin des gradients : on retient ici $14\Psi$ octets, comme au [chapitre 2 du module 10](../fault-tolerance/index.html#ch2).

Si l'écriture doit tenir dans une fraction $f$ de la période $\tau$ entre deux checkpoints, le débit d'écriture agrégé requis est

$$B_{\text{écriture}} = \frac{S}{f \, \tau}$$

::: ex
[Exemple 1.2 — Un modèle de 70 milliards de paramètres]{.tag} L'état pèse $70 \cdot 10^{9} \times 14 = 980$ Go. Avec une période de 30 minutes et une écriture limitée à 10 % de la période (180 s), il faut $980 / 180 = 5{,}4$ Go/s en écriture agrégée. Pour relire tout l'état en 120 s à la reprise, il faut 8,2 Go/s en lecture. Calculé avec `iosizing.py demo`.

Comparez avec l'exemple 1.1 : pour du texte, le stockage est dimensionné par **un checkpoint toutes les demi-heures**, pas par la lecture du jeu de données.
:::

::: war
[Des écritures de checkpoint en rafale saturent le réseau de stockage]{.tag} Le rapport Llama 3 (section 3.3.1) décrit le stockage d'entraînement de Meta : le système de fichiers distribué Tectonic offre 240 Po sur 7 500 serveurs équipés de SSD, avec un débit soutenable de 2 To/s et un pic de 7 To/s. Les auteurs écrivent : « A major challenge is supporting the highly bursty checkpoint writes that saturate the storage fabric for short durations. » L'état de modèle par GPU va de 1 Mo à 4 Go. Source : [Dubey et al., 2024](https://arxiv.org/abs/2407.21783), lu le 24 octobre 2026.
:::

### 1.5. Journaux et artefacts

Les journaux ne dépendent pas du débit mais de la discipline : un fichier par rang évite les verrous d'un fichier partagé, au prix de nombreux fichiers. Les artefacts posent le problème inverse : tous les nœuds lisent le même conteneur ou le même environnement Python au démarrage, ce qui concentre la charge sur les mêmes fichiers. La parade est de copier une fois vers un stockage local ou un cache (chapitre 7), pas d'augmenter le débit du serveur.

Le lab 8.4 contient les fonctions de dimensionnement de ce chapitre sous forme de code testé. La partie A vous fait refaire les exemples 1.1 et 1.2 avec vos propres chiffres.

::: recap
Points clés — chapitre 1

-   Quatre flux : jeu de données (chronique), checkpoint (aigu), journaux, artefacts. Chacun a son motif d'accès.
-   Le temps d'une requête vaut $\alpha + n/B$ ; la taille de demi-performance $\alpha B$ dit à partir de quelle taille de requête le débit est bon.
-   Lecture : consommateurs × rythme × taille ; checkpoint : $S/(f\tau)$ avec $S = 14\Psi$ octets.
-   Pour du texte tokenisé, le checkpoint dimensionne le stockage ; pour des images ou de la vidéo, la lecture compte aussi.
-   Le débit moyen ne dit rien du nombre d'opérations de métadonnées.
:::

## 2. Systèmes de fichiers parallèles {#ch2}

Un seul serveur de fichiers plafonne en débit et en opérations. Un système de fichiers parallèle répartit les données sur de nombreux serveurs et les métadonnées sur d'autres, pour que des centaines de clients lisent et écrivent en même temps.

### 2.1. Le principe : séparer métadonnées et données

La documentation de BeeGFS l'énonce ainsi : le système « combines multiple storage servers to provide a highly scalable shared network file system with striped file contents », grâce à une séparation des métadonnées et du contenu. Les serveurs de stockage conservent des morceaux du contenu des fichiers ; les serveurs de métadonnées coordonnent le placement et informent les clients ; les clients contactent **directement** les serveurs de stockage pour les E/S.

Le [manuel de Lustre](https://doc.lustre.org/lustre_manual.xhtml) décrit la même architecture avec d'autres noms. Un serveur de métadonnées (MDS) gère les noms et les répertoires, stockés sur une ou plusieurs cibles de métadonnées (MDT). Un serveur de stockage d'objets (OSS) assure les E/S de fichiers pour une ou plusieurs cibles de stockage (OST) ; le manuel indique qu'un OSS sert en général de deux à huit OST de 16 Tio au plus.

<figure class="fig">
<svg viewBox="0 0 560 330" role="img" aria-labelledby="pfs-t pfs-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="pfs-t">Système de fichiers parallèle et striping</title>
<desc id="pfs-d">Des clients envoient les opérations de métadonnées au serveur de métadonnées et lisent ou écrivent les données directement sur plusieurs cibles de stockage. Un fichier est découpé en blocs répartis en tourniquet sur quatre cibles.</desc>
<rect x="20" y="14" width="100" height="40" fill="currentColor" fill-opacity=".10" stroke="currentColor" stroke-width="1.5"/>
<text x="70.0" y="39.0" text-anchor="middle" font-size="14" fill="currentColor">client 1</text>
<rect x="140" y="14" width="100" height="40" fill="currentColor" fill-opacity=".10" stroke="currentColor" stroke-width="1.5"/>
<text x="190.0" y="39.0" text-anchor="middle" font-size="14" fill="currentColor">client 2</text>
<rect x="260" y="14" width="100" height="40" fill="currentColor" fill-opacity=".10" stroke="currentColor" stroke-width="1.5"/>
<text x="310.0" y="39.0" text-anchor="middle" font-size="14" fill="currentColor">client 3</text>
<text x="390" y="39" font-size="14" fill="currentColor">… N clients</text>
<line x1="20" y1="80" x2="540" y2="80" stroke="currentColor" stroke-width="3"/>
<text x="280" y="74" text-anchor="middle" font-size="14" fill="currentColor">réseau</text>
<rect x="20" y="110" width="150" height="56" fill="var(--accent)" fill-opacity=".35" stroke="currentColor" stroke-width="1.5"/>
<text x="95.0" y="135.0" text-anchor="middle" font-size="14" fill="currentColor">serveur de</text>
<text x="95.0" y="152.0" text-anchor="middle" font-size="14" fill="currentColor">métadonnées</text>
<text x="95" y="188" text-anchor="middle" font-size="14" fill="currentColor">noms, répertoires,</text><text x="95" y="206" text-anchor="middle" font-size="14" fill="currentColor">placement des blocs</text>
<rect x="200" y="110" width="76" height="56" fill="currentColor" fill-opacity=".10" stroke="currentColor" stroke-width="1.5"/>
<text x="238.0" y="135.0" text-anchor="middle" font-size="14" fill="currentColor">cible 0</text>
<text x="238.0" y="152.0" text-anchor="middle" font-size="14" fill="currentColor">données</text>
<rect x="288" y="110" width="76" height="56" fill="currentColor" fill-opacity=".10" stroke="currentColor" stroke-width="1.5"/>
<text x="326.0" y="135.0" text-anchor="middle" font-size="14" fill="currentColor">cible 1</text>
<text x="326.0" y="152.0" text-anchor="middle" font-size="14" fill="currentColor">données</text>
<rect x="376" y="110" width="76" height="56" fill="currentColor" fill-opacity=".10" stroke="currentColor" stroke-width="1.5"/>
<text x="414.0" y="135.0" text-anchor="middle" font-size="14" fill="currentColor">cible 2</text>
<text x="414.0" y="152.0" text-anchor="middle" font-size="14" fill="currentColor">données</text>
<rect x="464" y="110" width="76" height="56" fill="currentColor" fill-opacity=".10" stroke="currentColor" stroke-width="1.5"/>
<text x="502.0" y="135.0" text-anchor="middle" font-size="14" fill="currentColor">cible 3</text>
<text x="502.0" y="152.0" text-anchor="middle" font-size="14" fill="currentColor">données</text>
<line x1="95" y1="54" x2="95" y2="110" stroke="currentColor" stroke-dasharray="5 4"/>
<line x1="238" y1="80" x2="238" y2="110" stroke="currentColor"/>
<line x1="326" y1="80" x2="326" y2="110" stroke="currentColor"/>
<line x1="414" y1="80" x2="414" y2="110" stroke="currentColor"/>
<line x1="502" y1="80" x2="502" y2="110" stroke="currentColor"/>
<text x="372" y="188" text-anchor="middle" font-size="14" fill="currentColor">les clients lisent et écrivent les données</text><text x="372" y="206" text-anchor="middle" font-size="14" fill="currentColor">directement sur les cibles</text>
<text x="20" y="250" font-size="14" font-weight="700" fill="currentColor">un fichier de 8 blocs, nombre de cibles = 4 :</text>
<rect x="20" y="262" width="62" height="30" fill="var(--accent)" fill-opacity="0.15" stroke="currentColor"/>
<text x="51" y="282" text-anchor="middle" font-size="14" fill="currentColor">b0 → c0</text>
<rect x="84" y="262" width="62" height="30" fill="var(--accent)" fill-opacity="0.3" stroke="currentColor"/>
<text x="115" y="282" text-anchor="middle" font-size="14" fill="currentColor">b1 → c1</text>
<rect x="148" y="262" width="62" height="30" fill="var(--accent)" fill-opacity="0.44999999999999996" stroke="currentColor"/>
<text x="179" y="282" text-anchor="middle" font-size="14" fill="currentColor">b2 → c2</text>
<rect x="212" y="262" width="62" height="30" fill="var(--accent)" fill-opacity="0.6" stroke="currentColor"/>
<text x="243" y="282" text-anchor="middle" font-size="14" fill="currentColor">b3 → c3</text>
<rect x="276" y="262" width="62" height="30" fill="var(--accent)" fill-opacity="0.15" stroke="currentColor"/>
<text x="307" y="282" text-anchor="middle" font-size="14" fill="currentColor">b4 → c0</text>
<rect x="340" y="262" width="62" height="30" fill="var(--accent)" fill-opacity="0.3" stroke="currentColor"/>
<text x="371" y="282" text-anchor="middle" font-size="14" fill="currentColor">b5 → c1</text>
<rect x="404" y="262" width="62" height="30" fill="var(--accent)" fill-opacity="0.44999999999999996" stroke="currentColor"/>
<text x="435" y="282" text-anchor="middle" font-size="14" fill="currentColor">b6 → c2</text>
<rect x="468" y="262" width="62" height="30" fill="var(--accent)" fill-opacity="0.6" stroke="currentColor"/>
<text x="499" y="282" text-anchor="middle" font-size="14" fill="currentColor">b7 → c3</text>
<text x="20" y="318" font-size="14" fill="currentColor">bloc k sur la cible k mod 4 : quatre cibles se partagent le débit du fichier</text>
</svg>
<figcaption>Architecture commune des systèmes de fichiers parallèles : les métadonnées passent par un serveur dédié, les données par les cibles de stockage. Ici un fichier de huit blocs est réparti en tourniquet sur quatre cibles (valeurs de l'illustration, pas d'un système réel).</figcaption>
</figure>

### 2.2. Le striping

Le **striping** découpe un fichier en blocs de taille fixe répartis en tourniquet sur plusieurs cibles. Deux paramètres le règlent : le nombre de cibles (*stripe count*) et la taille d'un bloc (*stripe size*). Le manuel de Lustre indique que les valeurs par défaut du système sont de **1** cible et de **1 Mo**, modifiables par répertoire ou par fichier avec `lfs setstripe -c`.

La documentation de BeeGFS donne un exemple de répertoire configuré en `RAID0` avec 4 cibles et des blocs de 1 Mio, modifiable avec `beegfs entry set --num-targets=… --chunk-size=…` ; ces réglages s'appliquent aux **nouveaux** fichiers du répertoire, pas à ceux qui existent déjà.

La règle de pouce du manuel de Lustre est de « stripe over as few objects as will meet those needs and no more ». Répartir sur plus de cibles accroît le débit possible d'**un** fichier, mais coûte ailleurs.

-   **Pour augmenter le striping :** un fichier très grand ou accédé par de nombreux nœuds à la fois a besoin de plus de bande passante que ne peut en fournir un seul OSS.
-   **Contre :** plus de verrous et d'opérations réseau pour `stat` et `unlink` ; plus de contention sur les serveurs ; un risque accru (la panne d'un serveur abîme une partie de *chaque* fichier réparti partout) ; aucun bénéfice pour les petits fichiers.

Un fichier écrit par plusieurs nœuds pose un problème de plus : si plus d'un client écrit dans un même bloc, ils se disputent le verrou, même quand leurs écritures ne se recouvrent pas. Le manuel recommande d'aligner les E/S sur les blocs, et depuis Lustre 2.13 de pouvoir placer plus d'un bloc par cible (*overstriping*).

### 2.3. Dimensionner le striping

Si un fichier doit être lu ou écrit à $B_{\text{req}}$ et qu'une cible délivre $b$, il faut au moins

$$k = \left\lceil \frac{B_{\text{req}}}{b} \right\rceil$$

cibles. Le manuel donne une borne voisine, raisonnée par serveur : le plus grand nombre de cibles utile est borné par le débit que demandent les clients divisé par la performance d'un OSS. Au-delà, on ajoute des coûts sans gain.

::: ex
[Exemple 2.1 — Combien de cibles pour un fichier de checkpoint ?]{.tag} Valeurs d'exemple. On veut écrire un fichier partagé à 6 Go/s ; une cible délivre 1,5 Go/s. Il faut $\lceil 6/1{,}5 \rceil = 4$ cibles. Avec le striping par défaut (1 cible), le fichier plafonne à 1,5 Go/s, soit quatre fois trop peu.

Le débit **agrégé** d'un système est borné par le côté le plus étroit : avec 64 clients de 2,5 Go/s et 12 serveurs de 15 Go/s, il vaut $\min(160, 180) = 160$ Go/s, limité par les clients. Calculé avec `iosizing.py demo`.
:::

### 2.4. Les métadonnées, goulot silencieux

Chaque `open`, `stat` ou `unlink` passe par le serveur de métadonnées. Un jeu de données de dix millions de fichiers, lu une fois par époque avec trois opérations par fichier (ouverture, lecture des attributs, fermeture), fait $3 \cdot 10^{7}$ opérations de métadonnées par époque. Le débit des données ne les accélère pas : c'est le rythme du serveur de métadonnées, exprimé en opérations par seconde, qui les borne.

Deux mécanismes atténuent le problème. Les métadonnées peuvent être **réparties** sur plusieurs serveurs (BeeGFS le permet, Lustre le fait avec plusieurs MDT). Et, depuis Lustre 2.11, la fonction *Data on MDT* place les petits fichiers directement sur la cible de métadonnées, ce qui « improves small file IO ». La vraie parade reste de ne pas créer des millions de petits fichiers (chapitre 4).

::: war
[Une configuration documentée : un seul OST par défaut, parce que les petits fichiers dominent]{.tag} La page du système de fichiers de travail de Perlmutter au NERSC décrit un système Lustre tout flash de 44 Po, d'un débit agrégé supérieur à 6 To/s et de 4 millions d'IOPS (accès aléatoires de 4 Kio), avec 16 serveurs de métadonnées et 370 OST. Elle précise : « By default files on Perlmutter are striped across a single OST. Given the large number of small files on our system, this is a compromise ». Source : [NERSC, Perlmutter scratch](https://docs.nersc.gov/filesystems/perlmutter-scratch/), lu le 24 octobre 2026.
:::

### 2.5. Quatre systèmes, honnêtement

Ce tableau ne contient que ce que ce module a **lu à la source** le 24 octobre 2026. Il ne classe pas les produits : aucun banc d'essai comparatif n'a été lu, et les chiffres de débit des fournisseurs ne se comparent pas d'une page à l'autre.

| Système | Ce que la documentation lue établit | Réglage de répartition |
|---|---|---|
| Lustre | clients, serveurs de métadonnées (MDS, MDT) et de stockage (OSS, OST) ; Data on MDT depuis 2.11 ; quotas utilisateur, groupe et projet | nombre et taille de blocs, par répertoire ou par fichier ; défaut 1 cible et 1 Mo |
| BeeGFS | services client, métadonnées, stockage et gestion ; clients en contact direct avec le stockage ; métadonnées répartissables ; module noyau côté client | nombre de cibles et taille de bloc par répertoire |
| GPFS / IBM Storage Scale | **non relu** : la documentation d'IBM a répondu HTTP 403 depuis le bac à sable | à vérifier à la source |
| WEKA | système de fichiers parallèle distribué (la page lue nomme le produit « NeuralMesh by WEKA »), exécuté dans l'espace utilisateur en conteneurs Linux, cohérence forte et compatibilité POSIX complète annoncées ; quotas, instantanés et hiérarchisation vers un stockage objet | non relu en détail |

Ce que ces systèmes ont en commun compte plus que ce qui les distingue : une séparation des métadonnées, un débit qui croît avec le nombre de serveurs, et un motif d'accès idéal fait de **gros** fichiers lus ou écrits par **gros** morceaux.

### 2.6. Comment choisir

Le choix se joue sur la charge, pas sur la marque. Posez cinq questions avant de comparer des offres : quel est le nombre de fichiers du jeu de données et leur taille médiane ? Quel pic de checkpoint (chapitre 1) ? Combien de clients simultanés ? Qui exploitera le système, avec quelle expérience ? Quel test de recette le fournisseur accepte-t-il de passer sur vos motifs d'accès (chapitre 6, section 6.7) ?

Un fournisseur qui répond par un débit maximal agrégé sans dire la taille de requête ni le nombre de clients ne répond pas à la question : l'exemple 1.1 montre pourquoi.

::: recap
Points clés — chapitre 2

-   Un système de fichiers parallèle sépare métadonnées et données ; les clients parlent directement aux serveurs de stockage.
-   Le striping répartit un fichier en tourniquet : règle de pouce de Lustre, « as few objects as will meet those needs and no more ».
-   Cibles nécessaires : $\lceil B_{\text{req}}/b \rceil$ ; débit agrégé : le minimum du côté clients et du côté serveurs.
-   Les métadonnées sont le goulot silencieux : des millions de petits fichiers coûtent en opérations, pas en octets.
-   Ce module n'a pas relu GPFS à la source ; ne comparez pas des chiffres de fournisseurs sans la taille de requête.
:::

## 3. NFS, objet (S3), FUSE et caches {#ch3}

Les systèmes parallèles du chapitre 2 ne sont pas le seul endroit où vivent les données. Les répertoires personnels, les environnements Python et souvent les jeux de données sont sur NFS ; les jeux de données massifs et les checkpoints archivés sont de plus en plus dans un stockage objet. Chacun offre des garanties différentes, et une erreur de garantie se paie en corruption silencieuse plus qu'en lenteur.

### 3.1. NFS et la cohérence à la fermeture

NFS expose à un client un répertoire exporté par un serveur. Sa garantie de cohérence est volontairement faible. La page `nfs(5)` la décrit comme la *close-to-open consistency* : à l'ouverture d'un fichier, le client envoie une requête `GETATTR` ou `ACCESS` « regardless of the freshness of the file's cached attributes » ; à la fermeture, il écrit au serveur les modifications en attente, pour que l'ouvreur suivant les voie. Le comportement se désactive avec l'option `nocto`.

Les conséquences sont concrètes. Un fichier écrit par un nœud puis fermé est visible d'un autre nœud qui l'ouvre ensuite : un checkpoint écrit puis relu est sûr. Un lecteur qui garde un fichier ouvert, ou un journal suivi en direct depuis un autre nœud, peut voir des données périmées. Le cache d'attributs (`acregmin`, `acregmax`, `acdirmin`, `acdirmax`, ou `actimeo` pour tous à la fois) ajoute une fenêtre de péremption sur les listages de répertoires.

Côté débit, un serveur NFS classique est un point unique : son réseau et ses disques bornent ce que tous les clients obtiennent ensemble. L'option `nconnect=n` ouvre plusieurs connexions TCP entre client et serveur, « up to a limit of 16 », ce qui aide quand le client dispose de plusieurs cartes réseau ; elle ne crée pas de bande passante serveur.

### 3.2. Le stockage objet

Un stockage objet range des objets entiers sous des clés. On lit un objet (ou une plage d'octets), on en écrit un nouveau, on le supprime ; on ne modifie pas un objet en place et il n'y a pas de renommage atomique. Amazon S3 fournit, selon son guide, « strong read-after-write consistency for PUT and DELETE requests of objects » dans toutes les régions ; les listages, métadonnées et étiquettes sont eux aussi fortement cohérents.

Le débit passe par le **parallélisme**. Le guide de performance indique qu'une application peut atteindre « at least 3,500 PUT/COPY/POST/DELETE or 5,500 GET/HEAD requests per second per partitioned Amazon S3 prefix », sans limite au nombre de préfixes, et que la montée en charge est progressive.

La latence du premier octet d'un GET est élevée devant celle d'un disque local, donc la taille de demi-performance $\alpha B$ est grande : on lit par **grandes plages** et on garde beaucoup de requêtes en vol. La loi de Little donne la concurrence nécessaire : requêtes en vol = débit de requêtes × latence moyenne.

::: ex
[Exemple 3.1 — 20 Go/s depuis un magasin d'objets]{.tag} Valeurs d'exemple pour la cible ; 5 500 GET/s par préfixe est le **minimum** documenté ci-dessus (« at least »), pas un plafond : on le prend ici comme hypothèse prudente. Calculé avec `iosizing.py`.

| Taille d'une requête | Requêtes par seconde pour 20 Go/s | Préfixes nécessaires |
|---|---|---|
| plages de 8 Mio | 2 384 | 1 |
| objets de 128 Kio | 152 588 | 28 |

La même charge demande soixante-quatre fois plus de requêtes quand les objets sont soixante-quatre fois plus petits. Le gain des gros objets ne vient pas du réseau : il vient de la réduction du nombre de requêtes, donc de la latence cumulée et du coût de facturation par requête.
:::

::: war
[Un stockage objet qui monte en charge renvoie des erreurs 503]{.tag} Le guide de performance d'Amazon S3 précise que la montée en charge « happens gradually and is not instantaneous » et que, pendant que S3 s'adapte à un débit de requêtes plus élevé, l'application peut voir des erreurs `503 (Slow Down)`. Un chargeur de données qui passe d'un coup de zéro à des dizaines de milliers de GET par seconde doit donc réessayer avec un délai croissant, pas échouer. Source : [guide de l'utilisateur d'Amazon S3, optimisation des performances](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html), lu le 24 octobre 2026.
:::

### 3.3. FUSE : un système de fichiers qui n'en est pas tout à fait un

FUSE permet à un processus utilisateur de répondre aux opérations de fichiers du noyau ; c'est ainsi qu'on monte un magasin d'objets comme un répertoire. Ce confort a un prix : la sémantique d'un magasin d'objets ne se laisse pas toute émuler.

Le dépôt de Mountpoint pour Amazon S3 documente ses choix. Le client est optimisé pour la lecture séquentielle de gros objets, avec plusieurs requêtes concurrentes quand la lecture est séquentielle ; il accepte les lectures aléatoires. Il crée de nouveaux objets par écritures séquentielles depuis le début du fichier. Il ne supporte pas `rename` sur un bucket général, car cela exigerait de nombreux appels ; il ne gère ni lien physique ni lien symbolique ; la suppression est désactivée par défaut (option `--allow-delete`).

::: war
[Le protocole « fichier temporaire puis renommage » ne fonctionne pas sur un montage objet]{.tag} Le [document de sémantique de Mountpoint](https://raw.githubusercontent.com/awslabs/mountpoint-s3/main/doc/SEMANTICS.md) (lu le 24 octobre 2026) indique que le renommage n'est pas émulé sur les buckets généraux. Un code de checkpoint qui écrit `ckpt.tmp` puis le renomme échoue ou se comporte autrement sur un tel montage. Le motif adapté est celui du [chapitre 3 du module 10](../fault-tolerance/index.html#ch3) : écrire le manifeste en dernier et n'accepter qu'une version dont le manifeste existe.
:::

### 3.4. Une comparaison honnête

Le tableau compare des **garanties**, pas des vitesses. Les vitesses se mesurent chez vous (section suivante) ; aucun chiffre de débit ou de latence de fournisseur n'est repris ici.

| Critère | NFS | Système de fichiers parallèle | Stockage objet | Objet monté par FUSE |
|---|---|---|---|---|
| Cohérence | à la fermeture (*close-to-open*), cache d'attributs | POSIX ; Lustre applique par défaut la cohérence POSIX | forte, lecture après écriture (S3) | celle de l'objet, avec des cas limites documentés |
| Renommage atomique | oui | oui | non | non sur un bucket général (Mountpoint) |
| Débit qui croît avec la taille | non : borné par le serveur | oui : plus de serveurs, plus de débit | oui : plus de préfixes et de connexions | dépend du client |
| Petits fichiers | un aller-retour par ouverture | métadonnées partagées, goulot du chapitre 2 | une requête par objet | une requête par objet, plus le coût FUSE |
| À mesurer d'abord | $\alpha$ et $B$ sur un montage | $\alpha$, $B$, opérations de métadonnées | latence du premier octet, requêtes par seconde | débit séquentiel du client |

### 3.5. Mesurer les trois nombres de votre stockage

La méthode est la même pour tout stockage : mesurer $\alpha$, $B$ et la taille de demi-performance avec des requêtes de taille croissante. Le lab 8.2 (partie B) le fait avec `fio` sur un fichier de 512 Mio en `O_DIRECT`, profondeur de file 1, et ajuste $T = \alpha + n/B$. Pour un autre système, lancez `python3 fio_gap.py --dir <point de montage>` ; un montage NFS n'a **pas** été testé ici.

::: ex
[Exemple 3.2 — Les trois nombres du disque du bac à sable]{.tag} Capturé sur la VM de test (4 vCPU, disque virtuel `virtio`, 2026-10-24), `fio_gap.py`, lectures aléatoires en `O_DIRECT` à profondeur de file 1 :

~~~text
pattern      bs      IOPS       MiB/s  mean lat us
read         1M      1692        1692        589.3
randread     1M      1568        1568        635.2
randread   128k      9605        1201        103.1
randread    16k     15162         237         64.9
randread     4k     17043          67         57.7
alpha-beta fit on random reads: alpha = 55 us, B = 1936 MiB/s, half-performance size = 109 KiB, median error 8 %
gap: sequential 1M reads give 25x the bandwidth of random 4k reads
~~~

Deux lectures. D'abord, des requêtes de 4 Kio donnent 67 Mio/s sur un disque capable de 1 700 Mio/s : un facteur 25 d'écart qui vient entièrement de la taille de la requête. Ensuite, la lecture aléatoire de 1 Mio vaut la séquentielle : ce disque virtuel n'a pas de pénalité de déplacement de tête. Sur un disque rotatif ou un système de fichiers réseau, il y en aurait une en plus.

Ces valeurs sont celles **de ce bac à sable**, pas celles d'un stockage de production, et elles bougent : sur huit exécutions du lab, $n_{1/2}$ a valu de 91 à 122 Kio et l'écart de 21 à 27 fois.
:::

### 3.6. Le coût d'un stockage

Le coût d'un stockage se décompose en trois lignes : la capacité (prix du To par mois, multiplié par le nombre de copies), les requêtes (surtout pour l'objet) et les sorties de données hors de la région ou du fournisseur. Ce module ne cite **aucun prix** : lisez la page de prix du fournisseur le jour de votre calcul, et relisez-la avant chaque engagement.

Ce qu'un module de stockage peut affirmer sans prix, c'est l'effet de vos choix sur le **nombre de requêtes**. Un téraoctet en objets de 100 ko se lit en $10^{7}$ requêtes ; le même téraoctet en plages de 16 Mio, en environ 59 600, soit près de 170 fois moins. Si votre facture contient un prix par requête, cet écart se retrouve sur la ligne correspondante.

::: key
[Lire la garantie avant d'y poser un protocole]{.tag} NFS garantit la cohérence à la fermeture, S3 la lecture après écriture, un montage FUSE moins que les deux. Un protocole de checkpoint qui suppose le renommage atomique ne tient pas sur tous.
:::

::: recap
Points clés — chapitre 3

-   NFS : cohérence à la fermeture (`nocto` la désactive), cache d'attributs, débit borné par le serveur ; `nconnect` jusqu'à 16 connexions.
-   S3 : cohérence forte lecture après écriture ; au moins 5 500 GET/s par préfixe (valeur documentée) ; erreurs 503 pendant la montée en charge.
-   La latence du premier octet impose de grandes plages et du parallélisme ; la concurrence vaut débit de requêtes × latence.
-   FUSE ne rend pas un magasin d'objets POSIX : pas de renommage sur un bucket général avec Mountpoint.
-   Mesurez $\alpha$, $B$ et $n_{1/2}$ sur votre stockage avec `fio_gap.py` ; ne comparez pas des chiffres de fournisseurs.
:::

## 4. Formats de données pour l'entraînement {#ch4}

Un jeu de données de texte ou d'images peut être rangé de bien des façons, et la façon change le nombre d'ouvertures, la taille des requêtes et la quantité d'octets lus pour rien. Ce chapitre les mesure avec des compteurs, sur le même jeu synthétique, dans quatre dispositions.

### 4.1. Pourquoi le format compte

Reprenons l'ajustement de l'exemple 3.2 : $\alpha = 55\ \mu$s, $B = 1\,936$ Mio/s, soit $n_{1/2} = 109$ Kio. L'efficacité d'une requête de $n$ octets, c'est-à-dire la part du débit maximal qu'elle atteint, vaut

$$\eta(n) = \frac{n/B}{\alpha + n/B}$$

::: ex
[Exemple 4.1 — Quelle part du disque un échantillon de 16 Kio utilise-t-il ?]{.tag} Calculé avec `request_efficiency` (lab 8.4), avec les $\alpha$ et $B$ de l'exemple 3.2.

| Taille de la requête | Efficacité |
|---|---|
| 4 Kio | 3,5 % |
| 16 Kio (un échantillon de notre jeu) | 12,8 % |
| 128 Kio | 54,0 % |
| 1 Mio | 90,4 % |
| 4 Mio | 97,4 % |

Lire chaque échantillon de 16 Kio comme une requête à part n'utilise que 13 % du disque. Lire des morceaux de 1 Mio qui contiennent soixante-quatre échantillons en utilise 90 %. C'est toute la justification des **shards** : regrouper les échantillons pour que chaque requête dépasse $n_{1/2}$.
:::

### 4.2. Le jeu et les dispositions

Le lab 8.2 écrit 4 096 échantillons de 16 Kio (64 Mio de jetons de 16 bits pseudo-aléatoires, graine fixe : des données **synthétiques**, seule la disposition compte) dans quatre dispositions. Un fichier par échantillon. Huit archives tar de 512 échantillons selon la convention WebDataset. Un fichier unique de jetons concaténés, lu avec `pread` (lecture à un décalage donné) ou avec `mmap` (le fichier est projeté en mémoire, ses pages se chargent à la demande). Un fichier Parquet à groupes de 256 lignes.

Pour chaque lecteur, le lab évince d'abord le cache de pages des fichiers du jeu, puis lit trois compteurs de `/proc/self/io` : `syscr` (nombre d'appels `read`), `rchar` (octets renvoyés par les appels de lecture) et `read_bytes` (octets réellement lus sur la couche de stockage, d'après `proc_pid_io(5)`). Le nombre d'ouvertures est compté par un crochet d'audit Python. Ces compteurs sont ceux de **ce processus** : un autre processus de la machine ne les fausse pas, à la différence de `/proc/diskstats`.

~~~python
def drop_cache(paths: list[str]) -> None:
    """Ask the kernel to evict the clean pages of these files (no root needed; dirty pages must be flushed first)."""
    for p in paths:
        fd = os.open(p, os.O_RDONLY)
        try:
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        finally:
            os.close(fd)
~~~

### 4.3. Lire le tableau

::: ex
[Exemple 4.2 — Quatre dispositions, neuf lectures]{.tag} Capturé sur la VM de test (noyau 6.18, lecture anticipée de 128 Kio, 2026-10-24), `run_shards.py`. Les opérations comptées par `opens` sont celles que Python demande ; la colonne est `n/a` pour Parquet, dont les ouvertures sont faites en C++.

~~~text
layout        pattern         n  opens read()/smp asked/pay device/pay   warm smp/s
files         sequential   4096   4096      2.00      1.00      1.00        24157
files         random       1024   1024      2.00      1.00      1.00        22771
tar shards    sequential   4096      8      1.75      1.09      1.10        11808
tar shards    random       1024      8      1.00      1.00      1.30        26742
packed pread  sequential   4096      1      1.00      1.00      1.00        31709
packed pread  random       1024      1      1.00      1.00      1.04        29318
packed mmap   random       1024      1      0.00      0.00      3.41        25199
parquet       sequential   4096    n/a      0.00      1.00      1.00        17868
parquet       random       1024    n/a      1.00    256.09      4.00          337
~~~

`asked/pay` est le rapport entre les octets lus par les appels `read` et les octets utiles ; `device/pay`, le rapport entre les octets réellement lus sur la couche de stockage et les octets utiles. La dernière colonne est un débit **à chaud, donné pour information** et jamais testé : sur cette machine, le chronomètre est peu fiable (chapitre 7 du module 1).
:::

Ligne par ligne :

-   **Un fichier par échantillon :** une ouverture par échantillon (4 096), et deux `read` (les données puis la fin de fichier). Par octet lu, rien d'amplifié (`device/pay` = 1,00) : le coût est dans les ouvertures, donc dans les métadonnées et la latence par fichier.
-   **Shards, lecture séquentielle :** 8 ouvertures pour 4 096 échantillons. `asked/pay` vaut 1,09 : les en-têtes tar et les membres `.json` ajoutent 9 % d'octets lus.
-   **Shards, lecture aléatoire par index :** 1,30 à la couche bloc. Une explication cohérente avec l'arithmétique, non vérifiée par ce lab : les charges utiles ne commencent pas sur une frontière de page, donc un échantillon de 16 Kio touche cinq pages au lieu de quatre.
-   **Fichier empaqueté :** `pread` reste à 1,04 ; `mmap` en lecture aléatoire monte à **3,41** : le noyau lit autour du défaut de page (hypothèse de lecture anticipée, non vérifiée ici). La lecture anticipée de 128 Kio du périphérique est affichée par le lab.
-   **Parquet aléatoire :** 256,09 octets lus par octet utile. Chaque échantillon relit son groupe de 256 lignes entier. La colonne `device/pay` n'affiche que 4,00 : le jeu (64 Mio) tient dans le cache de pages, donc chaque groupe n'est lu qu'une fois sur le disque ; sur un jeu plus grand que la mémoire, elle se rapprocherait de 256.

### 4.4. Les shards et WebDataset

Le format [WebDataset](https://raw.githubusercontent.com/webdataset/webdataset/main/README.md) est un ensemble de fichiers tar avec deux conventions : les fichiers qui forment un échantillon partagent le même nom de base, et les shards sont numérotés `quelquechose-000000.tar`, souvent écrits en notation à accolades. Le README affirme qu'il permet des « purely sequential I/O pipelines » et chiffre le gain à « 3x-10x for local drives compared to random access » : c'est une **affirmation du projet, non reproduite ici**.

Notre mesure dit autre chose, et c'est utile : elle ne montre pas de gain de débit à chaud (le jeu tient en mémoire), mais elle chiffre ce qui change à froid : 8 ouvertures contre 4 096, des requêtes séquentielles, et 10 % de surcoût d'octets. Les shards du lab sont lisibles par la vraie bibliothèque `webdataset` (test du lab).

Le prix des shards est le mélange. Un tirage aléatoire global sur un jeu en shards redevient un accès aléatoire. La pratique est de mélanger l'ordre des shards puis de mélanger dans un tampon en mémoire, ce qui donne un ordre moins aléatoire qu'un tirage global. Le README note aussi la limite : équilibrer exactement le nombre d'échantillons entre nœuds sur une époque est délicat, d'où le ré-échantillonnage des shards en multi-nœuds.

~~~python
def read_tar_sequential(ds: Dataset, order=None) -> int:
    acc = 0
    for path in ds.shard_paths:
        with tarfile.open(path, "r|") as tar:  # stream mode: strictly sequential, no seek
            for ti in tar:
                if ti.name.endswith(".bin"):
                    acc ^= digest(int(ti.name.split(".")[0]), tar.extractfile(ti).read())
    return acc
~~~

### 4.5. Jetons pré-empaquetés et `mmap`

Pour du texte, la disposition la plus simple est de concaténer tous les jetons dans un fichier unique. nanoGPT le fait : `train.bin` est ouvert avec `np.memmap(..., dtype=np.uint16, mode='r')` et chaque batch tire des positions aléatoires avec `torch.randint(len(data) - block_size, (batch_size,))`. Un échantillon est une tranche du fichier : pas de métadonnées, pas de remplissage, une seule ouverture.

Le coût caché est celui du motif : sur un jeu plus grand que la mémoire, chaque tirage aléatoire est une lecture de petite taille. L'exemple 4.2 montre que `pread` ne lit presque rien de trop (1,04), alors que `mmap` lit 3,4 fois les octets utiles à froid. Quand le jeu tient dans le cache de pages, `mmap` est excellent ; quand il ne tient pas, préférez `pread` ou des lectures par blocs.

### 4.6. Parquet et Arrow

La [spécification de Parquet](https://raw.githubusercontent.com/apache/parquet-format/master/README.md) définit un fichier comme une suite de **groupes de lignes** ; un groupe contient un **bloc de colonne** par colonne ; un bloc est découpé en **pages**, « conceptually an indivisible unit (in terms of compression and encoding) ». L'unité de lecture est donc le bloc de colonne d'un groupe, jamais une ligne.

D'où l'amplification mesurée : lire une ligne coûte un groupe entier. Pour un groupe de $g$ lignes, la lecture aléatoire d'un échantillon lit environ $g$ fois les octets utiles ; le lab mesure 256,09 avec $g = 256$. À l'inverse, des groupes trop petits ne passent pas $n_{1/2}$ en lecture séquentielle. La taille du groupe de lignes arbitre entre les deux ; l'exercice 6 le chiffre.

Arrow est le pendant en mémoire : un format colonnaire que Hugging Face Datasets utilise pour son cache local, « memory-mapped for fast lookup », ce qui permet de manipuler de grands jeux avec peu de mémoire vive selon leur documentation. Les mêmes réserves que pour `mmap` s'appliquent.

### 4.7. Choisir

| Disposition | Lecture séquentielle | Accès aléatoire à un échantillon | Ouvertures par époque | Quand l'utiliser |
|---|---|---|---|---|
| un fichier par échantillon | sans amplification, mais une requête par échantillon | idem | un par échantillon | prototypes et petits jeux |
| shards tar | bonne : 1,10 mesuré | par index : 1,30 ; sinon mélange par tampon | un par shard | pré-entraînement multi-nœuds, stockage objet |
| fichier de jetons | optimale : 1,00 mesuré | `pread` 1,04 ; `mmap` 3,41 à froid | un | texte pré-tokenisé |
| Parquet | bonne | amplifiée d'un facteur égal aux lignes par groupe | peu | données tabulaires, lecture de colonnes |

::: key
[Trois nombres par format]{.tag} Pour tout format, notez le nombre d'ouvertures par époque, la taille moyenne d'une requête et le rapport `device/pay`. Si vous ne les connaissez pas, vous ne savez pas ce que votre jeu de données demande au stockage.
:::

::: recap
Points clés — chapitre 4

-   Une requête de $n$ octets utilise $\eta = (n/B)/(\alpha + n/B)$ du débit : 16 Kio n'en utilisent que 13 % sur le disque du bac à sable, 1 Mio en utilise 90 %.
-   Un fichier par échantillon coûte une ouverture par échantillon ; les shards en coûtent une par shard (4 096 contre 8 mesurés).
-   `mmap` en accès aléatoire à froid a lu 3,4 fois les octets utiles contre 1,04 pour `pread` sur cette machine.
-   Une ligne Parquet coûte un groupe de lignes entier : 256,09 octets lus par octet utile avec 256 lignes par groupe.
-   Le mélange est le prix des shards : mélanger les shards puis un tampon, pas tout le jeu.
:::

## 5. Chargeurs de données {#ch5}

Un chargeur lent est la cause la plus fréquente d'un GPU qui attend, et la plus mal diagnostiquée : on ajoute des workers au hasard. Ce chapitre donne une définition mesurable du problème, un modèle du premier ordre, une table de décision et un profileur.

### 5.1. Anatomie du `DataLoader`

Le `DataLoader` de PyTorch lance `num_workers` processus qui exécutent `Dataset.__getitem__`, assemblent les batchs et les renvoient au processus principal par une file. Les paramètres qui comptent sont décrits dans la docstring du code source (lue le 24 octobre 2026).

-   `num_workers` : « how many subprocesses to use for data loading. `0` means that the data will be loaded in the main process ».
-   `prefetch_factor` : le nombre de batchs chargés à l'avance **par worker**. Avec 2, il y a au total `2 * num_workers` batchs préchargés ; le défaut est 2 dès que `num_workers > 0`.
-   `persistent_workers` : si vrai, les workers ne sont pas arrêtés après une passe complète sur le jeu, ce qui évite de les redémarrer à chaque époque.
-   `pin_memory` : copie les tenseurs dans de la mémoire épinglée (*pinned*) avant de les rendre, pour accélérer le transfert vers le GPU. Il n'a d'effet qu'avec un GPU : **non mesuré ici**.

Les résultats sont livrés **dans l'ordre**. Le code de l'itérateur multiprocessus garde `_rcvd_idx`, l'« idx of the next task to be returned in __next__ » : un batch lent retarde tous ceux qui le suivent, même s'ils sont prêts. C'est la première explication que l'on essaie pour un écart du modèle plus bas ; le paramètre `in_order=False` désactive cette propriété (docstring de la branche `main`, essayé avec PyTorch 2.14.1).

### 5.2. Mesurer la part d'attente

La grandeur à mesurer est la **part d'attente** (*stall*) : le temps passé à attendre le prochain batch, divisé par le temps total de la boucle.

$$\text{stall} = \frac{\sum t_{\text{attente}}}{\sum t_{\text{attente}} + \sum t_{\text{pas}}}$$

Le papier sur les *data stalls* (Mohan et coauteurs, VLDB 2021) distingue les **prep stalls** (temps de prétraitement) des **fetch stalls** (temps d'E/S) et mesure les premiers et les seconds par une technique différentielle : comparer le temps d'époque avec des données réelles et avec des données déjà prêtes en mémoire. Le lab 8.1 applique la même idée en simulant le GPU par une attente fixe. La boucle mesurée tient en dix lignes :

~~~python
    for _ in range(n_batches):
        t0 = time.perf_counter()
        next(it)
        t1 = time.perf_counter()
        time.sleep(step_s)  # the simulated GPU step
        t2 = time.perf_counter()
        wait += t1 - t0
        step += t2 - t1
~~~

### 5.3. Un modèle du premier ordre

Un échantillon coûte $c$ secondes à un worker : une attente d'E/S $t_{\text{io}}$ et un calcul $t_{\text{cpu}}$. Un batch de $B$ échantillons coûte donc $Bc$ à un worker.

Avec $W$ workers, le chargeur produit $W/(Bc)$ batchs par seconde.

Les cœurs plafonnent ce débit : avec $C$ cœurs, il ne dépasse pas $C/(B\,t_{\text{cpu}})$. Le pas GPU dure $t_{\text{pas}}$ ; la boucle attend dès que le chargeur produit moins vite qu'elle ne consomme.

$$\text{stall} = \max\Bigl(0,\; 1 - t_{\text{pas}} \cdot \min\bigl(\tfrac{W}{B c},\; \tfrac{C}{B\,t_{\text{cpu}}}\bigr)\Bigr)$$

Sans worker, le chargement et le pas s'enchaînent : le *stall* vaut $Bc/(Bc + t_{\text{pas}})$.

::: ex
[Exemple 5.1 — Combien de workers pour un pas de 12 ms ?]{.tag} Jeu **simulé** : lecture distante de 6 ms par échantillon dont 5 % dix fois plus lentes (donc $t_{\text{io}}$ moyen de $6 \times (1 + 0{,}05 \times 9) = 8{,}7$ ms), décodage de 1 ms, batch de 8, pas GPU de 12 ms (le GPU consommerait 83 batchs par seconde). Donc $c = 9{,}7$ ms et $Bc = 77{,}6$ ms. Capturé sur la VM de test à 4 vCPU (2026-10-24), `run_lab.py`, `DataLoader` réel :

~~~text
workers prefetch  batch/s     stall     model cpu/wkr
      0        -     10.2      88 %      87 %    0.00
      1        2     11.8      86 %      85 %    0.14
      2        2     21.5      74 %      69 %    0.12
      4        2     41.5      50 %      38 %    0.12
      8        2     71.1      14 %       0 %    0.10
~~~

Le modèle suit la mesure à 12 points près au plus jusqu'à 4 workers. À 8 workers il annonce 0 % alors qu'on mesure 14 % (de 13 % à 17 % selon les exécutions) : c'est un **modèle optimiste**, qui raisonne sur des taux moyens.

La première explication essayée, la livraison des batchs dans l'ordre (un échantillon lent retarde son batch et les suivants), **ne tient pas** : avec `in_order=False` (`python3 run_lab.py --no-in-order`), le *stall* à 8 workers reste de 16 % à 19 % sur six exécutions, contre 13 % à 17 % avec l'ordre imposé (mesuré le 2026-10-25). L'écart reste inexpliqué ; hypothèse non testée : la variabilité des temps de service et la file de taille finie, que des taux moyens ignorent.

La colonne `cpu/wkr` (CPU consommé par worker, de 0,10 à 0,14) montre des workers presque inactifs : ils attendent des lectures, ils ne calculent pas.
:::

<figure class="fig">
<svg viewBox="0 0 560 330" role="img" aria-labelledby="stall-t stall-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="stall-t">Temps perdu à attendre les données selon le nombre de workers</title>
<desc id="stall-d">Courbe mesurée et courbe du modèle : la part du temps où la boucle attend un batch passe de 88 pour cent sans worker à 14 pour cent avec huit workers ; le modèle est optimiste.</desc>
<line x1="70" y1="270.0" x2="530" y2="270.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="275.0" text-anchor="end" font-size="14" fill="currentColor">0 %</text>
<line x1="70" y1="210.0" x2="530" y2="210.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="215.0" text-anchor="end" font-size="14" fill="currentColor">25 %</text>
<line x1="70" y1="150.0" x2="530" y2="150.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="155.0" text-anchor="end" font-size="14" fill="currentColor">50 %</text>
<line x1="70" y1="90.0" x2="530" y2="90.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="95.0" text-anchor="end" font-size="14" fill="currentColor">75 %</text>
<line x1="70" y1="30.0" x2="530" y2="30.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="35.0" text-anchor="end" font-size="14" fill="currentColor">100 %</text>
<rect x="70" y="30" width="460" height="240" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="100.0" y="292" text-anchor="middle" font-size="14" fill="currentColor">0</text>
<text x="200.0" y="292" text-anchor="middle" font-size="14" fill="currentColor">1</text>
<text x="300.0" y="292" text-anchor="middle" font-size="14" fill="currentColor">2</text>
<text x="400.0" y="292" text-anchor="middle" font-size="14" fill="currentColor">4</text>
<text x="500.0" y="292" text-anchor="middle" font-size="14" fill="currentColor">8</text>
<text x="300.0" y="316" text-anchor="middle" font-size="14" fill="currentColor">nombre de workers</text>
<polyline points="100,61 200,66 300,104 400,179 500,270" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="6 4"/>
<polyline points="100,59 200,64 300,92 400,150 500,236" fill="none" stroke="var(--accent)" stroke-width="3.5"/>
<circle cx="100" cy="59" r="5" fill="var(--accent)" stroke="currentColor"/>
<circle cx="200" cy="64" r="5" fill="var(--accent)" stroke="currentColor"/>
<circle cx="300" cy="92" r="5" fill="var(--accent)" stroke="currentColor"/>
<circle cx="400" cy="150" r="5" fill="var(--accent)" stroke="currentColor"/>
<circle cx="500" cy="236" r="5" fill="var(--accent)" stroke="currentColor"/>
<line x1="86" y1="48" x2="126" y2="48" stroke="var(--accent)" stroke-width="3.5"/><text x="134" y="53" font-size="14" fill="currentColor">mesuré</text>
<line x1="220" y1="48" x2="260" y2="48" stroke="currentColor" stroke-width="2" stroke-dasharray="6 4"/><text x="268" y="53" font-size="14" fill="currentColor">modèle</text>
<text x="14" y="150.0" text-anchor="middle" font-size="14" fill="currentColor" transform="rotate(-90 14 150.0)">part d'attente (stall)</text>
</svg>
<figcaption>Part d'attente selon le nombre de workers, mesurée (trait plein) et prédite (tirets) pour l'exemple 5.1. Le modèle est optimiste à 8 workers : mesure 14 %, modèle 0 %. Jeu simulé, `DataLoader` réel.</figcaption>
</figure>

L'exemple porte aussi sur `prefetch_factor`. Avec 8 workers, passer de 1 à 2 batchs préchargés a fait passer le *stall* de 24 % à 15 % ; aller à 4 puis 8 ne l'a pas amélioré (17 % et 17 %). Une file plus profonde absorbe la gigue, pas un manque de débit. Ces écarts de quelques points sont du même ordre que le bruit : une de nos exécutions de contrôle a donné 31 % pour 2 batchs préchargés, visiblement perturbée par la charge de la machine.

### 5.4. Quand les workers ne servent plus : le goulot CPU

Si le prétraitement coûte du CPU (décodage d'images, tokenisation, augmentation), ajouter des workers cesse d'aider dès que les cœurs sont saturés. Le papier sur les *data stalls* conclut dans son tableau 1 que les réseaux étudiés ont besoin « anywhere between 3 – 24 CPU cores per GPU » pour le prétraitement et passent jusqu'à 65 % du temps d'époque dans le prétraitement des données.

::: ex
[Exemple 5.2 — Un chargeur CPU sature à 4 cœurs]{.tag} Jeu **simulé** : 8 ms de CPU par échantillon (du vrai CPU), aucune attente d'E/S. Capturé sur la même VM, `run_lab.py`. Le modèle utilise le CPU **mesuré** par échantillon (lu dans `/proc/<pid>/stat` des workers), calibré sur la ligne à 2 workers, pas les 8 ms nominaux.

~~~text
workers prefetch  batch/s     stall     model cpu/wkr    cpu/sample
      1        2     14.6      82 %      82 %    1.00     8.5 ms
      2        2     28.6      65 %      65 %    0.97     8.5 ms
      4        2     52.1      37 %      29 %    0.85     8.2 ms
      8        2     53.0      34 %      29 %    0.46     8.6 ms
~~~

De 1 à 2 workers, le débit double ; de 4 à 8 il passe de 52,1 à 53,0 batchs par seconde : la machine a 4 cœurs, ils sont pleins (4 workers à 0,85 cœur, soit 3,4 cœurs ; 8 workers à 0,46, soit 3,7 cœurs). Le CPU mesuré par échantillon (8,2 à 8,6 ms) est proche du coût nominal : le coût réel d'un échantillon est un compteur qu'on lit, il ne se devine pas.
:::

### 5.5. Une table de décision

Trois mesures suffisent à choisir l'action : le *stall*, le nombre de workers et le CPU consommé par worker. Le lab les réunit dans une fonction.

~~~python
def diagnose(stall: float, worker_cpu_util: float, workers: int, cores: int, threshold: float = 0.05) -> str:
    """The decision table of the lab, as code. Inputs are things you can measure on a real job."""
    if stall < threshold:
        return "GPU-bound: the loader keeps up; do not touch it"
    if workers == 0:
        return "serial loading: set num_workers > 0 first"
    if worker_cpu_util >= 0.7 or workers * worker_cpu_util >= 0.8 * cores:
        return "CPU-bound loader: cheaper transforms, pre-processed data, or more cores per GPU"
    return "latency-bound loader: more workers, deeper prefetch, bigger sequential reads (shards)"
~~~

Le CPU par worker suppose que les cœurs ne sont pas pris par d'autres processus : lors d'une exécution du lab sur une machine partagée, 8 workers à 0,36 cœur chacun ont été diagnostiqués « à latence » alors que le chargeur était limité par le CPU.

Les seuils (5 % de *stall*, 0,7 cœur par worker, 80 % des cœurs) sont un choix de ce parcours, pas une norme. Ils servent à rendre la décision explicite : un chargeur à latence se soigne par plus de parallélisme ou de plus grosses lectures (chapitre 4), un chargeur CPU par un prétraitement moins coûteux ou fait une fois pour toutes (jetons pré-empaquetés), jamais par plus de workers.

### 5.6. Le profileur

`torch.profiler` nomme l'attente du chargeur : une ligne `enumerate(DataLoader)#…__next__` apparaît dans la table, avec le nombre d'appels et le temps total. Si cette ligne dépasse nettement le temps du pas, la boucle est limitée par les données ; sur un GPU, on la compare aux plages vides de la ligne de temps CUDA (non exécuté ici).

::: ex
[Exemple 5.3 — Lire la ligne `enumerate(DataLoader)`]{.tag} Capturé sur la VM de test (12 batchs, pas simulé de 12 ms, même jeu que l'exemple 5.1), `run_lab.py`, partie C :

~~~text
workers=0  enumerate(DataLoader)#_SingleProcessDataLoaderIter.__next__    calls=12  total= 1051.8 ms  per call=  87.7 ms
workers=4  enumerate(DataLoader)#_MultiProcessingDataLoaderIter.__next__  calls=12  total=  245.2 ms  per call=  20.4 ms
~~~

Sans worker, le chargeur coûte 87,7 ms par batch dans le fil principal, plus de sept fois le pas de 12 ms : la boucle attend. Avec 4 workers, il tombe à 20,4 ms par appel, encore supérieur au pas : la boucle attend toujours. Les deux mesures (12 batchs ici, 40 dans l'exemple 5.1, échauffements différents) ne se comparent pas chiffre à chiffre. Le nom de la classe (`SingleProcess` ou `MultiProcessing`) vous dit aussi quel itérateur tourne vraiment.
:::

### 5.7. Épingler la mémoire, et un chargeur par machine

L'option `pin_memory` copie les batchs dans de la mémoire épinglée avant de les rendre : le transfert vers le GPU peut alors se faire par DMA, et en parallèle du calcul. Sa valeur se mesure sur un nœud GPU en comparant `True` et `False` avec un jeu synthétique : ce test n'est **pas** exécuté ici.

À grande échelle, le papier MegaScale décrit une autre économie : sur chaque machine, un chargeur dédié unique lit les données dans de la mémoire partagée, puis chaque processus GPU copie ce dont il a besoin vers sa mémoire. Les auteurs indiquent que cela supprime les lectures redondantes quand plusieurs processus du même nœud lisent les mêmes données.

::: war
[Les données dominent le temps d'époque dans de nombreux cas]{.tag} L'analyse de Mohan et coauteurs sur des serveurs d'un grand cluster de production de Microsoft conclut : « in many cases, DNN training time is dominated by data stall time », et leur bibliothèque CoorDL réduit le temps d'entraînement d'un facteur pouvant aller jusqu'à 5 sur un serveur par rapport à DALI. L'étude porte sur la vision et l'audio, avec un prétraitement lourd : pour du texte pré-tokenisé, le constat ne s'applique pas tel quel (exemple 1.1). Source : [arXiv:2007.06775](https://arxiv.org/abs/2007.06775), lu le 24 octobre 2026.
:::

::: key
[Mesurez, puis ajoutez]{.tag} Ajouter des workers sans avoir mesuré le CPU par worker est un pari. Un chargeur à latence se soigne avec du parallélisme ; un chargeur CPU, avec moins de calcul par échantillon.
:::

::: recap
Points clés — chapitre 5

-   Le *stall* est la part du temps de boucle passée à attendre un batch ; il se mesure autour de `next()`.
-   Modèle : le *stall* vaut un moins le produit du pas GPU par le débit du chargeur (workers sur coût d'un batch, plafonné par les cœurs) ; il est optimiste (14 % mesuré contre 0 % prédit à 8 workers), et la livraison dans l'ordre n'en est pas la cause (`in_order=False` ne change rien).
-   `prefetch_factor` au-delà de 2 n'a rien apporté sur nos mesures ; il lisse la gigue.
-   Un chargeur CPU sature quand les cœurs sont pleins : 52,1 contre 53,0 batchs par seconde entre 4 et 8 workers sur 4 cœurs.
-   La table de décision prend trois mesures : *stall*, workers, CPU par worker. `pin_memory` n'a pas été mesuré (pas de GPU).
:::

## 6. E/S de checkpoint {#ch6}

Le chapitre 1 a chiffré ce qu'un checkpoint doit écrire. Ce chapitre mesure ce qu'il coûte réellement : une écriture durable, la part qui bloque l'entraînement, et ce qui change quand plusieurs rangs écrivent à la fois. Le protocole complet (somme de contrôle, manifeste, reprise exacte) est celui du [module 10](../fault-tolerance/index.html#ch3) ; on ne le répète pas.

### 6.1. Ce qu'on écrit

Un checkpoint de $\Psi$ paramètres pèse $14\Psi$ octets (section 1.4). Dans un entraînement parallèle, chaque rang en détient une part, de 1 Mo à 4 Go par GPU dans le rapport Llama 3. Le choix entre un fichier par rang et un fichier partagé, et celui du format, relèvent du module 10 ; ce qui nous intéresse est le nombre d'octets, le nombre de fichiers et le moment où tous les rangs écrivent.

### 6.2. Le coût d'une écriture durable

Une écriture ordinaire (`write`) est absorbée par le cache de pages : elle est rapide et **pas durable**, car rien ne dit que les octets ont atteint le disque (chapitre 7 du module 1). Le protocole durable écrit un fichier temporaire, appelle `fsync`, renomme, puis synchronise le répertoire. `O_DIRECT` contourne le cache et exige des tampons, des décalages et des longueurs alignés : une écriture de 1 000 octets échoue avec `EINVAL` (test du lab).

~~~python
    tmp = path + ".tmp"
    mv = memoryview(buf)
    t0 = time.perf_counter()
    with open(tmp, "wb") as f:
        for off in range(0, len(buf), chunk):
            if fail_after is not None and off >= fail_after:
                raise OSError("injected failure")
            f.write(mv[off:off + chunk])
            _pace(min(off + chunk, len(buf)), t0, throttle_mbps)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    fsync_dir(os.path.dirname(os.path.abspath(path)))
~~~

::: ex
[Exemple 6.1 — Ce que coûte la durabilité sur un disque virtuel]{.tag} Capturé sur la VM de test (4 vCPU, ext4 sur disque virtuel, 2026-10-24), `bench_ckpt.py`, partie A : médiane de cinq exécutions après une exécution d'échauffement, état d'octets pseudo-aléatoires, durées en millisecondes.

~~~text
    size   buffered      fsync   O_DIRECT   snapshot
      16       12.0       27.9       49.6        2.5
      64       51.6      106.9      155.5        6.9
     128      102.1      283.3      356.4       12.0
fit T = alpha + S/B on fsync: alpha = 0.0 ms, B = 518 MiB/s, median error 13 %, leave-one-out 25 %
~~~

À 128 Mio, l'écriture ordinaire prend 102 ms (1,2 Gio/s) mais n'est pas durable. Le protocole avec `fsync` en prend 283 (452 Mio/s), soit 2,8 fois plus : c'est le prix de la durabilité. `O_DIRECT` en prend 356. L'ajustement $T = \alpha + S/B$ donne $B = 518$ Mio/s avec 13 % d'erreur médiane. Sur nos exécutions, $B$ a varié de 499 à 590 Mio/s et l'erreur médiane de 2 % à 13 % : rapportez des médianes et dites la dispersion.

Avec trois tailles seulement, l'ajustement avait donné un $\alpha$ négatif (−3,5 ms), ramené à 0 par le code, alors que d'autres exécutions ont donné +3,6 et +4,0 ms : $\alpha$ n'est pas identifiable ici, seul $B$ se lit.
:::

La colonne `snapshot` est la copie de l'état dans un tampon de l'hôte, **simulation** de la copie GPU vers hôte (il n'y a pas de GPU ici) : 12 ms pour 128 Mio, soit environ 10 Gio/s. Elle est près de vingt-quatre fois plus courte que l'écriture durable. C'est cet écart que le checkpoint asynchrone exploite.

### 6.3. Temps bloquant et temps de persistance

Soit $T_p$ la durée de la persistance, $s$ celle du snapshot et $I$ l'intervalle entre deux checkpoints. Un checkpoint synchrone bloque pendant $T_p$ ; un checkpoint asynchrone bloque pendant $s$, plus ce qui reste de l'écriture précédente si elle dépasse l'intervalle :

$$\text{sync} = \frac{T_p}{I} \qquad \text{async} = \frac{s + \max(0,\, T_p - I)}{I}$$

Le temps qui entre dans la formule de Young du module 10 est le temps **bloquant**, pas la durée totale. Mais si $T_p$ dépasse $I$, l'écriture ne tient plus dans l'intervalle et son reliquat bloque à son tour : l'asynchrone ne vaut plus rien.

::: ex
[Exemple 6.2 — Synchrone contre asynchrone, mesuré contre modèle]{.tag} Partie B du lab : un pas d'entraînement **simulé** de 20 ms, un stockage **simulé** à 200 Mio/s (l'écrivain se bride lui-même), un état de 32 Mio. Persistance mesurée : 206 ms ; snapshot : 3 ms. Capturé sur la VM de test.

~~~text
every N steps   sync meas.   sync model  async meas.  async model
          10        96.9%       102.8%         8.9%         4.3%
          40        28.3%        25.7%         1.4%         0.4%
~~~

Tous les 10 pas (200 ms), l'intervalle vaut presque la durée d'écriture : le synchrone double le temps (96,9 %), l'asynchrone coûte 8,9 %. Tous les 40 pas (800 ms), le synchrone coûte 28,3 % et l'asynchrone 1,4 %. Le modèle suit à quelques points près ; l'asynchrone est un peu plus coûteux que prévu (8,9 % contre 4,3 %), écart que nous n'avons pas cherché à expliquer. Le lab accepte 10 points d'écart.
:::

La figure applique les deux formules à l'exemple d'un état dont la persistance dure 240 s (exercice 9) avec un snapshot de 3 s. Le surcoût synchrone suit $240/I$ ; l'asynchrone reste de l'ordre du pour cent tant que $I > 240$ s, puis s'effondre. **Le coude se trouve à $I = T_p$.**

<figure class="fig">
<svg viewBox="0 0 560 330" role="img" aria-labelledby="ovh-t ovh-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="ovh-t">Surcoût d'un checkpoint selon l'intervalle</title>
<desc id="ovh-d">Pour une écriture de 240 secondes, le surcoût synchrone vaut 240 divisé par l'intervalle. Le surcoût asynchrone reste de l'ordre du pour cent tant que l'intervalle dépasse 240 secondes, puis remonte vite.</desc>
<line x1="70" y1="264.0" x2="530" y2="264.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="269.0" text-anchor="end" font-size="14" fill="currentColor">0 %</text>
<line x1="70" y1="204.0" x2="530" y2="204.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="209.0" text-anchor="end" font-size="14" fill="currentColor">25 %</text>
<line x1="70" y1="144.0" x2="530" y2="144.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="149.0" text-anchor="end" font-size="14" fill="currentColor">50 %</text>
<line x1="70" y1="84.0" x2="530" y2="84.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="89.0" text-anchor="end" font-size="14" fill="currentColor">75 %</text>
<line x1="70" y1="24.0" x2="530" y2="24.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="29.0" text-anchor="end" font-size="14" fill="currentColor">100 %</text>
<line x1="70" y1="24" x2="70" y2="264" stroke="currentColor" stroke-opacity=".2"/><text x="70" y="286" text-anchor="middle" font-size="14" fill="currentColor">1 min</text>
<line x1="226" y1="24" x2="226" y2="264" stroke="currentColor" stroke-opacity=".2"/><text x="226" y="286" text-anchor="middle" font-size="14" fill="currentColor">4 min</text>
<line x1="329" y1="24" x2="329" y2="264" stroke="currentColor" stroke-opacity=".2"/><text x="329" y="286" text-anchor="middle" font-size="14" fill="currentColor">10 min</text>
<line x1="452" y1="24" x2="452" y2="264" stroke="currentColor" stroke-opacity=".2"/><text x="452" y="286" text-anchor="middle" font-size="14" fill="currentColor">30 min</text>
<line x1="530" y1="24" x2="530" y2="264" stroke="currentColor" stroke-opacity=".2"/><text x="530" y="286" text-anchor="middle" font-size="14" fill="currentColor">1 h</text>
<rect x="70" y="24" width="460" height="240" fill="none" stroke="currentColor" stroke-width="1.5"/>
<polyline points="70.0,24.0 77.7,24.0 85.3,24.0 93.0,24.0 100.7,24.0 108.3,24.0 116.0,24.0 123.7,24.0 131.3,24.0 139.0,24.0 146.7,24.0 154.3,24.0 162.0,24.0 169.7,24.0 177.3,24.0 185.0,24.0 192.7,24.0 200.3,24.0 208.0,24.0 215.7,24.0 223.3,24.0 231.0,35.0 238.7,50.1 246.3,64.2 254.0,77.4 261.7,89.7 269.3,101.2 277.0,111.9 284.7,121.9 292.3,131.3 300.0,140.1 307.7,148.2 315.3,155.9 323.0,163.0 330.7,169.7 338.3,175.9 346.0,181.7 353.7,187.1 361.3,192.2 369.0,196.9 376.7,201.4 384.3,205.5 392.0,209.4 399.7,213.0 407.3,216.3 415.0,219.5 422.7,222.4 430.3,225.2 438.0,227.7 445.7,230.1 453.3,232.3 461.0,234.4 468.7,236.4 476.3,238.2 484.0,239.9 491.7,241.5 499.3,243.0 507.0,244.4 514.7,245.7 522.3,246.9 530.0,248.0" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="6 4"/>
<polyline points="70.0,24.0 77.7,24.0 85.3,24.0 93.0,24.0 100.7,24.0 108.3,24.0 116.0,24.0 123.7,24.0 131.3,24.0 139.0,24.0 146.7,24.0 154.3,45.1 162.0,75.4 169.7,103.7 177.3,130.1 185.0,154.8 192.7,177.8 200.3,199.3 208.0,219.4 215.7,238.2 223.3,255.7 231.0,261.1 238.7,261.3 246.3,261.5 254.0,261.7 261.7,261.8 269.3,262.0 277.0,262.1 284.7,262.2 292.3,262.3 300.0,262.5 307.7,262.6 315.3,262.6 323.0,262.7 330.7,262.8 338.3,262.9 346.0,263.0 353.7,263.0 361.3,263.1 369.0,263.2 376.7,263.2 384.3,263.3 392.0,263.3 399.7,263.4 407.3,263.4 415.0,263.4 422.7,263.5 430.3,263.5 438.0,263.5 445.7,263.6 453.3,263.6 461.0,263.6 468.7,263.7 476.3,263.7 484.0,263.7 491.7,263.7 499.3,263.7 507.0,263.8 514.7,263.8 522.3,263.8 530.0,263.8" fill="none" stroke="var(--accent)" stroke-width="3.5"/>
<line x1="226" y1="24" x2="226" y2="264" stroke="var(--accent)" stroke-dasharray="3 3"/>
<text x="234" y="60" font-size="14" fill="currentColor">intervalle = durée</text><text x="234" y="78" font-size="14" fill="currentColor">d'écriture (240 s)</text>
<line x1="370" y1="94" x2="410" y2="94" stroke="var(--accent)" stroke-width="3.5"/><text x="418" y="99" font-size="14" fill="currentColor">asynchrone</text>
<line x1="370" y1="120" x2="410" y2="120" stroke="currentColor" stroke-width="2" stroke-dasharray="6 4"/><text x="418" y="125" font-size="14" fill="currentColor">synchrone</text>
<text x="300.0" y="312" text-anchor="middle" font-size="14" fill="currentColor">intervalle entre checkpoints (échelle logarithmique)</text>
<text x="14" y="144.0" text-anchor="middle" font-size="14" fill="currentColor" transform="rotate(-90 14 144.0)">surcoût (plafonné à 100 %)</text>
</svg>
<figcaption>Surcoût d'un checkpoint selon l'intervalle, pour une persistance de 240 s et un snapshot de 3 s (formules de la section 6.3, tracées avec `sync_overhead` et `async_overhead` ; pas une mesure). Le coude de la courbe asynchrone est à l'intervalle égal à la durée d'écriture.</figcaption>
</figure>

### 6.4. Le tampon de préparation

Le snapshot copie l'état dans un tampon de l'hôte. Allouer ce tampon à chaque checkpoint est une erreur. La partie D du lab copie 256 Mio dans un tampon neuf, puis de nouveau dans le même.

::: ex
[Exemple 6.3 — Le premier accès à un tampon neuf]{.tag} Capturé sur la VM de test, `bench_ckpt.py`, partie D (indicatif, non testé) :

~~~text
Part D - informational: snapshot copy of 256 MiB, first into a new buffer, then into the same one
   first copy   1417 ms   second copy     25 ms   ratio 56.3
~~~

La première copie coûte cinquante fois la seconde. L'écart dépend de l'état de la mémoire de la machine (fautes de page ; sur une VM, peut-être l'attribution tardive de la mémoire par l'hôte, hypothèse non vérifiée) et varie d'une exécution à l'autre. Il justifie la règle d'ingénierie : allouer et toucher le tampon une fois (c'est le rôle de la mémoire épinglée réutilisée dans les vrais entraîneurs), puis le réutiliser.
:::

Cette réutilisation impose la règle du module 10 : **une seule persistance en vol**. Tant que l'écriture précédente lit le tampon, le snapshot suivant doit attendre. C'est ce que fait `AsyncCheckpointer.save`, et c'est là que se mesure le temps d'attente de l'exemple 6.2.

~~~python
        if self._stage is None or len(self._stage) != len(state):
            self.prepare(len(state))
        t0 = time.perf_counter()
        self.wait()  # the staging buffer is still being written: at most one persistence in flight
        t1 = time.perf_counter()
        np.copyto(self._stage, state)  # the consistent snapshot: the only part that must stop training
        t2 = time.perf_counter()
~~~

Le budget de mémoire d'hôte est la taille de l'état local par nœud : pour 980 Go répartis sur 1 024 GPU, 0,96 Go par GPU, soit 7,7 Go par nœud de 8 GPU pour un snapshot en vol. Ce n'est pas énorme ; c'est un budget à ne pas oublier quand le chargeur de données préalloue lui aussi de la mémoire partagée.

### 6.5. Plusieurs écrivains, un seul stockage

Quand les rangs écrivent chacun leur part, l'agrégat dépend de ce que le stockage peut absorber. La partie C du lab écrit 128 Mio au total, répartis sur 1, 2 puis 4 processus qui écrivent chacun leur fichier avec le protocole durable.

::: ex
[Exemple 6.4 — Des écrivains parallèles sur un seul disque]{.tag} Capturé sur la VM de test, `bench_ckpt.py`, partie C. Médiane de trois exécutions après deux exécutions d'échauffement ; chaque écrivain se chronomètre depuis une barrière.

~~~text
       1 writers  wall    164 ms  aggregate    781 MiB/s
       2 writers  wall    148 ms  aggregate    867 MiB/s
       4 writers  wall    136 ms  aggregate    944 MiB/s
~~~

Quadrupler le nombre d'écrivains n'a gagné que 21 % de débit agrégé : il n'y a qu'**un** disque virtuel. Ce que le lab mesure ici est la contention d'un seul périphérique, pas le passage à l'échelle d'un système de fichiers parallèle : sur un tel système, le débit agrégé suit $\min(\text{clients},\text{serveurs})$ (section 2.3), tant que les écrivains sont répartis sur des cibles différentes.

Un écrivain seul atteint ici 781 Mio/s, plus que les 518 Mio/s de l'ajustement de l'exemple 6.1, sans que nous l'expliquions. Hypothèse non testée : l'option de montage `discard`, qui pénaliserait le renommage par-dessus un fichier existant (partie A) mais pas la création d'un fichier neuf (partie C).
:::

Fichier par rang ou fichier partagé ? Un fichier par rang évite les verrous mais crée autant de fichiers que de rangs à chaque checkpoint : 1 024 créations simultanées sur le serveur de métadonnées, puis autant de fichiers à effacer à la rotation. Un fichier partagé demande un striping suffisant (section 2.3) et des écritures alignées sur les blocs : le manuel de Lustre explique que plus d'un client écrivant dans un même bloc provoque des échanges de verrous, même sans recouvrement.

### 6.6. La relecture

À la reprise, tous les rangs relisent leur part en même temps : c'est un pic de lecture, pas d'écriture. Le débit de lecture requis pour relire en $R$ secondes est $S/R$ (exemple 1.2 : 8,2 Go/s pour 120 s). Le module 10 décrit comment MegaScale réduit cette charge en faisant lire une partition par un rang du groupe de parallélisme de données, qui la diffuse ensuite.

Un checkpoint complet contient aussi **l'état du chargeur de données**. CheckFreq (Mohan et coauteurs, FAST 2021) l'énonce : le système maintient l'invariant selon lequel chaque élément du jeu est utilisé exactement une fois par époque « by checkpointing data loader state using a light-weight resumable iterator ». Sans cela, une reprise rejoue ou saute des échantillons.

### 6.7. La recette d'un stockage de checkpoint

Un fournisseur de stockage ou de cloud donne un débit maximal ; ce qui vous importe est le débit pour **votre** motif. Le critère « débit et latence d'écriture d'un checkpoint » figure déjà dans la matrice de décision du [module 15](../finops-capacity/index.html#ch8). Une recette utile contient cinq essais, chacun avec un critère de réussite tiré de vos formules, caches froids, trois répétitions, médiane rapportée.

1.  **Rafale d'écriture :** $N$ clients écrivent chacun $S/N$ avec le protocole durable ; temps jusqu'au dernier `fsync` ; critère : $S/(f\tau)$ du chapitre 1.
2.  **Rafale de lecture :** les mêmes clients relisent, caches froids ; critère : $S/R$.
3.  **Lecture séquentielle agrégée :** $N$ clients lisent de gros fichiers ; critère : le débit de lecture du chapitre 1.
4.  **Lecture aléatoire :** à la taille d'un échantillon ; critère : $\eta(n)$ du chapitre 4 sur $\alpha$ et $B$ mesurés.
5.  **Métadonnées :** créations et lectures d'attributs par seconde ; critère : les opérations par époque de l'exemple 2.1 divisées par la durée que vous acceptez.

`bench_ckpt.py --dir <point de montage>` et `fio_gap.py --dir <point de montage>` couvrent les essais 1 et 4 sur un seul client ; le test multi-clients et le test de métadonnées sont à écrire pour votre système et n'ont **pas** été exécutés ici.

::: key
[Le temps qui compte]{.tag} Pour l'entraînement, le coût d'un checkpoint est son temps **bloquant**, pas sa durée d'écriture, tant que l'écriture tient dans l'intervalle. Dès qu'elle ne tient plus, l'asynchrone ne protège plus.
:::

::: recap
Points clés — chapitre 6

-   Écriture ordinaire (non durable), protocole `fsync` + renommage et `O_DIRECT` n'ont pas le même coût : 102, 283 et 356 ms pour 128 Mio sur le disque du bac à sable.
-   Synchrone : $T_p/I$ ; asynchrone : $(s + \max(0, T_p - I))/I$ ; le coude est à $I = T_p$.
-   Allouer le tampon de snapshot une fois : sur la VM de test, la première copie de 256 Mio dans un tampon neuf a coûté 1 417 ms, la suivante 25 ms.
-   Plusieurs écrivains sur un seul disque ne passent pas à l'échelle ; sur un système parallèle, l'agrégat suit $\min(\text{clients},\text{serveurs})$.
-   Un checkpoint contient l'état du chargeur ; une recette de stockage teste vos motifs avec des critères chiffrés.
:::

## 7. Mise en cache : NVMe local, cache distribué, GPUDirect Storage {#ch7}

Un cache évite de relire plusieurs fois, depuis le stockage partagé, ce que l'entraînement relit à chaque époque. Il se juge à son taux de succès, et ce taux dépend d'une politique d'éviction que le noyau a choisie pour d'autres charges que la vôtre.

### 7.1. Les niveaux

Entre le GPU et le stockage partagé, il y a typiquement trois niveaux. La mémoire de l'hôte, où le cache de pages du noyau garde ce qui a été lu récemment. Le disque NVMe local du nœud. Et, parfois, un cache partagé entre nœuds.

Le guide utilisateur du DGX H100 de NVIDIA décrit deux volumes : un « Data Cache » de 8 disques NVMe de 3,84 To en RAID 0, soit $8 \times 3{,}84 = 30{,}72$ To par nœud, et un volume système de 2 disques de 1,92 To en RAID 1. Un volume en RAID 0 ne survit pas à la perte d'un disque : traitez-le comme un cache, jamais comme un stockage.

Un cache a deux nombres : sa capacité, comparée à celle du jeu de données, et le rapport entre sa vitesse et celle du stockage derrière. Le débit moyen d'une lecture dont une fraction $h$ des octets vient du cache est la moyenne **harmonique** des deux vitesses :

$$B_{\text{eff}} = \frac{1}{h/B_{\text{cache}} + (1-h)/B_{\text{stockage}}}$$

::: ex
[Exemple 7.1 — Pourquoi 50 % de succès ne donne pas la moyenne]{.tag} Valeurs d'exemple : cache à 6 Go/s, stockage à 1 Go/s. À $h = 0{,}5$, le débit effectif n'est pas $(6+1)/2 = 3{,}5$ Go/s mais 1,71 Go/s : les octets lents dominent le temps. Pour atteindre 3 Go/s, il faut $h = (1 - 1/3)/(1 - 1/6) = 0{,}80$ : 80 % de succès. Calculé avec `effective_read_bandwidth` (lab 8.4).
:::

### 7.2. Le piège du LRU en époques aléatoires

Le cache de pages du noyau évince en gros les pages les moins récemment utilisées (LRU). Or un entraînement relit tout le jeu à chaque époque, dans un ordre aléatoire différent. Si le jeu est plus grand que le cache, ce motif est le pire cas pour le LRU : ce qu'on vient de lire est évincé avant d'être relu.

Le papier sur les *data stalls* le constate (tableau 1) : « OS Page Cache is inefficient for DNN training due to thrashing ». Ses auteurs proposent un cache logiciel, MinIO, spécialisé pour l'entraînement : les éléments, une fois en cache, ne sont **jamais remplacés**. Quand le cache est plein, les autres requêtes vont au stockage. Avec $x = C/D$, le rapport de la taille du cache à celle du jeu, un tel cache a un taux de succès de $x$.

Pour le LRU, la dérivation de ce parcours (champ moyen, détaillée dans la docstring de `lru_epoch_hit_ratio`) donne

$$h_{\text{LRU}}(x) = x + (1 - x)\ln(1 - x)$$

Entre deux usages d'un échantillon, le cache voit la fin de l'époque précédente et le début de l'époque courante ; les deux groupes se recouvrent un peu, ce qui compte les échantillons en double une seule fois. C'est une **dérivation de ce cours**, pas un résultat publié : le lab la vérifie par simulation.

::: ex
[Exemple 7.2 — LRU contre cache sans éviction]{.tag} Calculé avec `iosizing.py demo` ; la simulation (2 000 échantillons, cache de 1 000, six époques, graine 0) donne 0,151 pour le LRU et 0,500 pour le cache sans éviction.

| Cache / jeu de données | Cache sans éviction | LRU (formule) |
|---|---|---|
| 25 % | 25 % | 3,4 % |
| 50 % | 50 % | 15,3 % |
| 75 % | 75 % | 40,3 % |

Avec un cache de la moitié du jeu, le LRU ne garde que 15 % de succès : le tiers de ce que garde un cache qui ne supprime jamais. Avec les vitesses de l'exemple 7.1, cela fait 1,15 Go/s au lieu de 1,71 Go/s.
:::

<figure class="fig">
<svg viewBox="0 0 560 330" role="img" aria-labelledby="lru-t lru-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="lru-t">Taux de succès d'un cache selon sa taille relative</title>
<desc id="lru-d">Un cache qui ne supprime jamais ses entrées suit la diagonale. Un cache LRU lu en époques d'ordre aléatoire reste très en dessous : 15 pour cent à la moitié du jeu de données.</desc>
<line x1="70" y1="264" x2="530" y2="264" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="269" text-anchor="end" font-size="14" fill="currentColor">0 %</text>
<text x="70" y="286" text-anchor="middle" font-size="14" fill="currentColor">0 %</text>
<line x1="70" y1="204.0" x2="530" y2="204.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="209.0" text-anchor="end" font-size="14" fill="currentColor">25 %</text>
<text x="185.0" y="286" text-anchor="middle" font-size="14" fill="currentColor">25 %</text>
<line x1="70" y1="144.0" x2="530" y2="144.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="149.0" text-anchor="end" font-size="14" fill="currentColor">50 %</text>
<text x="300.0" y="286" text-anchor="middle" font-size="14" fill="currentColor">50 %</text>
<line x1="70" y1="84.0" x2="530" y2="84.0" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="89.0" text-anchor="end" font-size="14" fill="currentColor">75 %</text>
<text x="415.0" y="286" text-anchor="middle" font-size="14" fill="currentColor">75 %</text>
<line x1="70" y1="24" x2="530" y2="24" stroke="currentColor" stroke-opacity=".2"/>
<text x="62" y="29" text-anchor="end" font-size="14" fill="currentColor">100 %</text>
<text x="530" y="286" text-anchor="middle" font-size="14" fill="currentColor">100 %</text>
<rect x="70" y="24" width="460" height="240" fill="none" stroke="currentColor" stroke-width="1.5"/>
<line x1="70" y1="264" x2="530" y2="24" stroke="currentColor" stroke-width="2" stroke-dasharray="6 4"/>
<polyline points="70.0,264.0 79.2,264.0 88.4,263.8 97.6,263.6 106.8,263.2 116.0,262.8 125.2,262.2 134.4,261.5 143.6,260.7 152.8,259.9 162.0,258.8 171.2,257.7 180.4,256.5 189.6,255.1 198.8,253.6 208.0,251.9 217.2,250.1 226.4,248.2 235.6,246.1 244.8,243.9 254.0,241.6 263.2,239.0 272.4,236.3 281.6,233.5 290.8,230.4 300.0,227.2 309.2,223.8 318.4,220.1 327.6,216.3 336.8,212.2 346.0,208.0 355.2,203.4 364.4,198.7 373.6,193.6 382.8,188.3 392.0,182.7 401.2,176.7 410.4,170.5 419.6,163.8 428.8,156.7 438.0,149.3 447.2,141.3 456.4,132.8 465.6,123.7 474.8,113.9 484.0,103.3 493.2,91.7 502.4,78.9 511.6,64.5 520.8,47.6 530.0,24.0" fill="none" stroke="var(--accent)" stroke-width="3.5"/>
<circle cx="300.0" cy="144.0" r="5" fill="var(--key-bar)" stroke="currentColor"/><circle cx="300.0" cy="227.17766166719343" r="5" fill="var(--accent)" stroke="currentColor"/>
<text x="312.0" y="168.0" font-size="14" fill="currentColor">50 %</text><text x="288.0" y="215" text-anchor="end" font-size="14" fill="currentColor">15 %</text>
<text x="125.19999999999999" y="163.2" font-size="14" fill="currentColor" transform="rotate(-30 125.19999999999999 163.2)">cache sans éviction : x</text>
<text x="323.0" y="244.8" font-size="14" fill="currentColor">LRU : x + (1 − x) ln(1 − x)</text>
<text x="300.0" y="312" text-anchor="middle" font-size="14" fill="currentColor">taille du cache / taille du jeu de données (x)</text>
<text x="14" y="144.0" text-anchor="middle" font-size="14" fill="currentColor" transform="rotate(-90 14 144.0)">taux de succès</text>
</svg>
<figcaption>Taux de succès selon la taille relative du cache pour des époques en ordre aléatoire : cache sans éviction (tirets) et LRU (trait plein). Formules du lab 8.4, vérifiées par simulation à 3 points près.</figcaption>
</figure>

~~~python
def effective_read_bandwidth(hit_ratio: float, cache_bw: float, backend_bw: float) -> float:
    """Average rate when a fraction `hit_ratio` of the bytes comes from the cache: harmonic mix of the two speeds."""
    return 1.0 / (hit_ratio / cache_bw + (1.0 - hit_ratio) / backend_bw)
~~~

### 7.3. Un cache par nœud : affecter les shards

Sur plusieurs nœuds en parallélisme de données, chaque nœud ne lit à chaque époque qu'une part $D/N$ du jeu. Si les shards sont réaffectés au hasard à chaque époque, un nœud a déjà vu un shard donné à l'époque $k$ avec la probabilité

$$p_k = 1 - \left(1 - \frac{1}{N}\right)^{k-1}$$

avec $N$ nœuds, tant que son cache peut tout contenir. Pour $N = 4$ nœuds et $k = 3$, $p_3 = 1 - (3/4)^2 = 43{,}75\ \%$. Pour $N = 32$, la probabilité à l'époque 2 est de 3 %, et à l'époque 10 de 25 % : le cache se remplit très lentement.

La vitesse d'un nœud dépend alors de ce qui manque. Soit $h$ la part déjà en cache, $b$ la part du débit du stockage partagé qui revient à un nœud (débit total divisé par $N$) et $r_{\text{besoin}}$ le débit que le nœud voudrait consommer.

Les octets qui manquent viennent du stockage : le nœud va donc à $r = \min\bigl(r_{\text{besoin}},\, b/(1-h)\bigr)$, et une époque dure $D/N$ divisé par $r$ (lab 8.4, `epoch_times`).

La parade est une affectation **collante** : chaque nœud reçoit toujours les mêmes shards. Dès l'époque 2, sa part tient dans son cache et tout est servi localement. Le papier CoorDL décrit une idée voisine, un cache partitionné coordonné entre les serveurs. Le prix est un mélange moins aléatoire : un nœud ne voit jamais les échantillons d'un autre. On le compense en changeant la partition rarement (toutes les $K$ époques) ou en mélangeant à l'intérieur de gros shards. L'exercice 10 chiffre l'écart.

### 7.4. Pré-chauffage et invalidation

Le **pré-chauffage** consiste à copier les shards vers le disque local avant que l'entraînement ne commence, par exemple dans l'étape d'initialisation d'un job Slurm ([module 5](../slurm/index.html)). Il transforme une première époque limitée par le stockage partagé en une copie dont on connaît la durée : octets locaux divisés par le débit du stockage.

Quant à l'**invalidation**, la parade la plus sûre est de l'éviter : traitez les shards comme immuables. Une nouvelle version du jeu est un nouveau répertoire (ou un nouveau préfixe) avec un manifeste qui liste les shards et leurs empreintes ; la clé du cache est le chemin plus l'empreinte. On supprime les anciennes versions après vérification. C'est une **recommandation de ce parcours**, pas une propriété d'un produit.

### 7.5. GPUDirect Storage

Le guide de [GPUDirect Storage](https://docs.nvidia.com/gpudirect-storage/overview-guide/index.html) (GDS) le décrit comme un chemin direct pour des transferts par accès direct à la mémoire entre la mémoire du GPU et le stockage, ce qui « avoids a bounce buffer through the CPU » et peut soulager la bande passante du système et la charge du CPU.

Il convient surtout aux gros transferts qui ne passent pas par le CPU : lecture et écriture d'un checkpoint depuis la mémoire GPU, ou lots déjà prêts. Il apporte peu si le CPU doit de toute façon décoder les données (inférence de ce parcours, pas une phrase du guide).

::: war
[GPUDirect Storage exige l'accès direct au fichier]{.tag} Le guide indique que, pour des transferts directs entre la mémoire du GPU et le stockage, « the file must be opened in O_DIRECT mode » ; sinon, le contenu peut être mis en tampon dans la mémoire du CPU, ce qui est incompatible avec le transfert direct.

Depuis CUDA 12.2 (GDS 1.7.x), la bibliothèque cuFile prend le chemin `O_DIRECT` pour des tampons, tailles et décalages alignés même si le fichier n'a pas été ouvert ainsi. Source : [NVIDIA, GDS Overview Guide](https://docs.nvidia.com/gpudirect-storage/overview-guide/index.html), lu le 24 octobre 2026. **Non exécuté ici : pas de GPU.**
:::

Côté CPU, le lab 8.3 illustre la contrainte d'alignement de `O_DIRECT` (ce n'est pas une mesure de GDS) : une écriture de 1 000 octets échoue avec `EINVAL`.

::: key
[Un cache se juge à son taux de succès]{.tag} Avant d'acheter du NVMe local, calculez $x = C/D$ et le taux de succès de votre politique. Un cache de la moitié du jeu qui évince en LRU ne rend que 15 % de succès.
:::

::: recap
Points clés — chapitre 7

-   Le débit effectif d'un cache est une moyenne harmonique : 50 % de succès entre 6 et 1 Go/s donne 1,71 Go/s, pas 3,5.
-   En époques aléatoires, un LRU rend $x + (1-x)\ln(1-x)$ de succès ; un cache sans éviction, $x$ (15 % contre 50 % à moitié du jeu).
-   Affectation collante des shards : à partir de l'époque 2, la part d'un nœud est locale ; au hasard, le cache se remplit à $1 - (1-1/N)^{k-1}$.
-   Traitez les shards comme immuables : l'invalidation se règle par un manifeste et des empreintes.
-   GPUDirect Storage évite le tampon CPU et exige `O_DIRECT` ; non exécuté sans GPU.
:::

## 8. Capacité, durée de vie des données, sauvegardes, quotas, coût au To {#ch8}

Un stockage qui tient le débit peut quand même s'arrêter parce qu'il est plein, parce qu'un quota refuse une écriture, ou parce qu'une purge a effacé un checkpoint. Ce chapitre traite de ce qui dure et de ce qu'il coûte.

### 8.1. Quatre classes de durée de vie

Toutes les données ne méritent pas le même traitement. Quatre classes suffisent à les ranger : l'**éphémère** (caches, fichiers temporaires), le **travail en cours** (jeu de données courant, checkpoints actifs), le **durable** (code, configurations, manifestes, checkpoints finaux) et l'**archive**. Les exploitants les distinguent aussi.

Le NERSC décrit le système de fichiers de travail de Perlmutter comme un stockage temporaire de gros fichiers, avec purge. Le centre IDRIS décrit Jean Zay avec un système de fichiers parallèle Lustre et trois dispositifs de stockage : 8,5 Po sur SSD, 44 Po sur disques rotatifs et 56 Po sur bandes (page de matériel, lue le 24 octobre 2026). Ce sont trois niveaux de coût et de vitesse.

::: war
[Une purge efface ce qui n'a pas été lu depuis huit semaines]{.tag} La page du NERSC sur Perlmutter scratch avertit : « The scratch file system is purged. Any file not accessed within 8 weeks is subject to deletion. » Le NERSC utilise la date d'accès (*atime*) et précise que, passé ce délai, un fichier « may be purged at any time » ; il ajoute que « Ultimately, it is the user's responsibility to prevent data loss ». Un checkpoint de sécurité écrit puis jamais relu est un candidat à la purge. Source : [NERSC, Perlmutter scratch](https://docs.nersc.gov/filesystems/perlmutter-scratch/), lu le 24 octobre 2026.
:::

### 8.2. La vie d'un checkpoint

Sans politique, les checkpoints s'accumulent. La rotation du module 10 garde les $K$ derniers et un checkpoint ancien « de sécurité » tous les $L$ checkpoints. Le stockage retenu en fin de campagne est donc $(K + \lfloor n/L \rfloor) \times S$ pour $n$ checkpoints écrits.

::: ex
[Exemple 8.1 — Rotation d'un modèle de 70 milliards de paramètres]{.tag} $S = 980$ Go ; 100 000 pas, un checkpoint tous les 500 pas, soit $n = 200$ ; $K = 3$ et $L = 10$. On retient $3 + 20 = 23$ checkpoints, soit **22,5 To**, contre 196 To sans rotation : 173,5 To économisés. Pendant la rotation, le nouveau checkpoint est écrit et validé **avant** que le plus ancien soit supprimé : le pic est de $(K+1) \times S = 3{,}92$ To. Calculé avec `iosizing.py demo`.
:::

Deux conséquences. D'abord, le quota doit couvrir le **pic**, pas le régime établi : un checkpoint qui échoue par manque de place au moment de la rotation est un échec de plus à gérer. Ensuite, les checkpoints de sécurité à long terme n'ont pas leur place sur un stockage purgé ; ils vont sur un niveau durable (section 8.1).

### 8.3. Les jeux de données et leurs copies

Chaque transformation d'un jeu de données en crée une copie : brut, filtré, tokenisé, découpé en shards. La capacité à prévoir est la somme des copies que vous gardez, pas la taille du jeu brut. Gardez pour chaque copie un manifeste (liste de fichiers, empreintes, version du code qui l'a produite) : c'est ce qui permet de supprimer une copie dérivée en sachant la régénérer, et d'expliquer un résultat plus tard.

### 8.4. Les sauvegardes

Une sauvegarde répond à deux questions : combien de données peut-on perdre (l'objectif de point de reprise, RPO) et combien de temps peut-on attendre pour les retrouver (l'objectif de temps de reprise, RTO). Les réponses diffèrent par classe. Le code, les configurations et les manifestes se sauvegardent toujours ; les checkpoints finaux et les résultats d'évaluation aussi ; les caches, le scratch et les checkpoints intermédiaires non.

Les outils existent : la documentation de WEKA liste des instantanés et une copie d'instantané vers un stockage objet ; le dépôt de Mountpoint recommande d'activer le versionnage du bucket quand on autorise la suppression. Quel que soit l'outil, **testez une restauration** : une sauvegarde jamais restaurée est une hypothèse.

### 8.5. Les quotas

Un quota limite l'espace, parfois le nombre de fichiers, par utilisateur, groupe ou projet. Le manuel de Lustre documente `lfs setquota` avec les options `-u`, `-g` et `-p`, et précise que les quotas de `root` ne sont **pas** appliqués. Le NERSC dit ce qui se passe quand un quota est dépassé : « you will not be able to write to the file system until you reduce your usage ».

Pour un entraînement, cela signifie qu'un checkpoint peut échouer **parce qu'un quota est atteint**, sans que le système de fichiers soit plein. La garde la plus simple est de vérifier l'espace libre avant d'écrire et de faire pivoter avant de manquer de place ; le lab 8.4 contient `free_space_ok` et `peak_checkpoint_bytes`. Pour les quotas de fichiers, un fichier par rang et par checkpoint les épuise vite : 1 024 rangs et 23 checkpoints retenus font 23 552 fichiers.

### 8.6. Le coût au To

Le coût mensuel d'un programme est la somme, sur les niveaux, de la capacité multipliée par le nombre de copies et par le prix du To-mois du niveau, plus les requêtes et les sorties de données :

$$C = \sum_{\text{niveaux}} T_i \times m_i \times p_i$$

La fonction `monthly_cost` du lab prend le prix en argument : **aucun prix n'est donné** dans ce module. Lisez la page de prix de votre fournisseur le jour de votre calcul, avec ses unités (To ou Tio, mois de 30 jours ou non) et ses lignes annexes.

::: ex
[Exemple 8.2 — Ce que change le niveau de stockage]{.tag} Même programme que l'exemple 8.1 : 22,5 To de checkpoints, 20 To de jeu tokenisé, 2 To de journaux et artefacts (le « chaud », 44,5 To), plus 60 To de données brutes. Si tout est au prix $p$ du niveau chaud : 104,5 To × $p$. Si les 60 To bruts sont dans un niveau **supposé** à un quart du prix : $(44{,}5 + 60/4) \times p = 59{,}5\ p$, soit 43 % de moins. Le quart est une hypothèse pour l'illustration, pas un prix. Calculé avec `iosizing.py exercises`.
:::

### 8.7. Observer le stockage

Quatre familles de métriques suffisent à un tableau de bord de stockage : l'espace et les fichiers consommés par rapport au quota, par équipe ; l'âge des fichiers par rapport à la politique de purge ; la durée et le volume de chaque checkpoint (médiane et queue de distribution, par campagne) ; et la part d'attente des chargeurs (*stall*) relevée dans les journaux d'entraînement. Le [module 14](../observability/index.html#ch3) montre comment les exposer à Prometheus.

::: recap
Points clés — chapitre 8

-   Quatre classes : éphémère, travail en cours, durable, archive ; une purge efface ce qui n'a pas été lu (huit semaines au NERSC).
-   Rotation : $(K + \lfloor n/L \rfloor) \times S$ retenus ; le quota doit couvrir le pic $(K+1) \times S$.
-   Chaque transformation d'un jeu de données crée une copie : prévoir la somme, garder un manifeste.
-   Une sauvegarde se juge à sa restauration ; un quota atteint fait échouer une écriture sans que le disque soit plein.
-   Le coût est $\sum T_i m_i p_i$ ; lisez le prix le jour même, ne figez aucun chiffre.
:::

## Labs {#labs}

Les quatre labs s'exécutent sur une machine Linux **sans GPU** et sans système de fichiers parallèle : ils mesurent un vrai `DataLoader` PyTorch, de vraies E/S sur le disque local et des compteurs du noyau. Les éléments simulés (lecture distante, décodage, pas GPU, stockage lent) sont étiquetés comme tels dans chaque `README.md` et dans les énoncés ci-dessous. Les durées (2,5 h, 2,5 h, 2,5 h et 1,75 h) font 9,25 h, comme dans la fiche. Installation préalable :

~~~bash
python3 -m venv venv && . venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install numpy pytest pyarrow webdataset
sudo apt-get install -y fio          # nécessaire au lab 8.2, partie B
export PYTHON="$PWD/venv/bin/python"  # honoré par chaque verify.sh
~~~

::: lab
[Lab 8.1 — Démasquer un chargeur de données lent]{.tag}

**Objectif.** Mesurer la part d'attente d'une boucle d'entraînement, la comparer à un modèle, distinguer un chargeur à latence d'un chargeur CPU et lire le profileur. **Durée.** 2,5 h (séance 5). **Prérequis matériels.** Un portable ou une VM Linux de 4 cœurs au moins, Python avec PyTorch CPU, `numpy` et `pytest` ; aucun GPU. **Simulé :** la lecture distante, le décodage et le pas GPU ; **réel :** le `DataLoader`, le temps d'attente, le CPU des workers, le profileur.

1.  Lisez `labs/storage/loader-bottleneck/loader_lab.py` : repérez où l'attente d'E/S, le décodage et le pas GPU sont simulés, et la mesure autour de `next()`.
2.  Lancez `bash verify.sh` (environ 30 s) et lisez les trois tableaux A, B et C.
3.  Refaites à la main la prédiction du modèle pour 2 workers (coût $c$, coût d'un batch, débit, *stall*) et comparez à la colonne `model`.
4.  Relancez `python3 run_lab.py --batches 100` : les mesures sont-elles plus stables ?
5.  Changez `STEP_S` dans `run_lab.py` (6 ms, puis 24 ms) : à partir de combien de workers le chargeur suit-il le GPU ? Prédisez avec `predict_stall` avant de mesurer.
6.  Appliquez `diagnose` à une ligne d'un job réel (*stall*, workers, CPU par worker).

**Critère de réussite.** `bash verify.sh` affiche `OK loader-bottleneck` : le *stall* mesuré reste à moins de 25 points du modèle pour le chargeur à latence (35 points pour le chargeur CPU à 4 et 8 workers, dont le modèle suppose 4 cœurs libres), il baisse quand les workers augmentent, et passer de 4 à 8 workers sur le chargeur CPU ne gagne pas plus de 50 % de débit (il doublerait si les cœurs ne limitaient pas).

Sur la VM de test (2026-10-24) : `OK loader-bottleneck: stall 0/1/2/4/8 workers = 88 % / 86 % / 74 % / 50 % / 14 %; CPU-bound ceiling 52.1 -> 53.0 batch/s (4 -> 8 workers)`. Vos valeurs seront différentes.

**Pour aller plus loin.** Lancez `python3 run_lab.py --no-in-order` et comparez le *stall* à 8 workers à celui du modèle : la livraison dans l'ordre explique-t-elle l'écart ? Sur un nœud GPU, comparez `pin_memory=True` et `False` avec le même jeu synthétique, et lisez la ligne de temps CUDA du profileur. **Non exécuté ici.**
:::

::: lab
[Lab 8.2 — Shards et lecture séquentielle]{.tag}

**Objectif.** Chiffrer, avec des compteurs du noyau, ce que quatre dispositions d'un même jeu coûtent en ouvertures, en appels `read` et en octets lus, puis mesurer l'effet de la taille de requête avec `fio`. **Durée.** 2,5 h : partie A (compteurs) 1,5 h en séance 3, partie B (`fio`) 1 h en séance 4. **Prérequis matériels.** Linux, Python avec `numpy` et `pytest`, `pyarrow` et `webdataset` recommandés, `fio`, environ 200 Mio de disque libre ; aucun GPU. **Simulé :** les données (graine fixe) ; **réel :** les fichiers, le noyau, `fio`.

1.  Lisez `labs/storage/shard-format/shard_lab.py` : les quatre dispositions, les lecteurs, `measure` et ses compteurs.
2.  Partie A : lancez `python3 run_shards.py` et recopiez le tableau (ouvertures, `read()` par échantillon, `asked/pay`, `device/pay`).
3.  Vérifiez que les ouvertures valent 4 096, 8 et 1 pour les trois dispositions, et expliquez pourquoi un fichier coûte deux `read()`.
4.  Relancez avec `--samples 8192` : quels compteurs changent, lesquels non ?
5.  Partie B : lancez `python3 fio_gap.py`, relevez $\alpha$, $B$ et $n_{1/2}$, et calculez l'efficacité d'une requête de 16 Kio avec la formule du chapitre 4.
6.  Lisez `read_ahead_kb` de votre disque et expliquez la ligne `mmap` aléatoire ; écrivez votre hypothèse avant de la tester.

**Critère de réussite.** `bash verify.sh` affiche `OK shard-format` : sommes de contrôle exactes ; 4 096, 8 et 1 ouvertures ; octets lus sur le périphérique entre 0,9 et 1,6 fois la charge utile pour les lectures séquentielles et `pread` ; `mmap` aléatoire au moins 1,5 fois plus que `pread` ; Parquet aléatoire entre 0,75 et 1,25 fois 256 octets lus par octet utile ; `fio` : 1 Mio donne plus de deux fois la bande passante de 4 Kio.

 Sur la VM de test : `OK shard-format: opens files/tar/packed = 4096/8/1; mmap random device/payload 3.4 vs pread 1.0; parquet asked/payload 256; fio gap 25x, n_1/2 = 109 KiB`. Si `pyarrow` ou `webdataset` manquent, `verify.sh` le dit et saute ces lignes.

**Pour aller plus loin.** Lancez `fio_gap.py --dir <point de montage>` sur un NFS ou un système parallèle, et comparez $\alpha$, $B$ et $n_{1/2}$ à ceux du disque local. **Non testé ici.**
:::

::: lab
[Lab 8.3 — Coût d'un checkpoint]{.tag}

**Objectif.** Mesurer le coût d'écritures durables, ajuster $T = \alpha + S/B$, et confronter le modèle de surcoût synchrone et asynchrone à une boucle d'entraînement simulée. **Durée.** 2,5 h : parties A, B et D 1,5 h en séance 6, partie C 1 h en séance 7. **Prérequis matériels.** Linux, Python avec `numpy` et `pytest`, un disque qui accepte `O_DIRECT` ; aucun GPU. **Simulé :** le pas d'entraînement, le stockage lent de la partie B (l'écrivain se bride) et la copie GPU vers hôte (une copie en mémoire) ; **réel :** les écritures, `fsync`, `rename`, `O_DIRECT`.

1.  Lisez `labs/storage/checkpoint-io/ckpt_io.py` : les trois écritures, `AsyncCheckpointer`, la boucle simulée.
2.  Partie A : lancez `python3 bench_ckpt.py`, relevez le rapport `fsync` sur écriture ordinaire, l'ajustement et son erreur médiane ; relancez trois fois et notez la dispersion.
3.  Partie B : calculez à la main le surcoût synchrone et asynchrone pour un checkpoint tous les 40 pas, puis comparez au tableau.
4.  Changez `--throttle-mbps` (50, puis 800) : prédisez où se trouve le coude ($I = T_p$), puis mesurez.
5.  Partie C : relevez le gain agrégé de 1 à 4 écrivains et expliquez pourquoi il est faible sur un seul disque.
6.  Partie D : relevez le rapport entre la première et la seconde copie dans un tampon.

**Critère de réussite.** `bash verify.sh` affiche `OK checkpoint-io` : relecture exacte des trois modes, erreur médiane de l'ajustement sous 60 %, protocole `fsync` plus de 1,2 fois plus lent qu'une écriture ordinaire à la plus grande taille, surcoût simulé synchrone à moins de 15 points (ou 35 % en relatif) du modèle, asynchrone à moins de 10 points, et asynchrone sous la moitié du synchrone.

 Sur la VM de test : `OK checkpoint-io: fit B = 518 MiB/s, error 13 %; sync 28.3 % vs model 25.7 %; async 1.4 % vs model 0.4 %`. Vos valeurs seront différentes ; les parties C et D n'ont pas de seuil.

**Pour aller plus loin.** Lancez `bench_ckpt.py --dir <point de montage>` sur le stockage de votre cluster. Un test multi-clients (section 6.7) reste à écrire. **Non testé ici.**
:::

::: lab
[Lab 8.4 — Dimensionner : lecture, checkpoint, striping, requêtes, cache, capacité]{.tag}

**Objectif.** Refaire chaque calcul du module avec du code testé, puis avec vos propres chiffres. **Durée.** 1,75 h : partie A 1 h en séance 1, partie B 0,75 h en séance 7. **Prérequis matériels.** Python et `pytest` ; aucun autre outil. **Simulé :** la simulation de cache est une simulation (graine fixe) ; les entrées des exemples sont des **valeurs d'exemple**.

1.  Partie A : lancez `python3 iosizing.py demo` et refaites les exemples 1.1 et 1.2 avec la taille d'échantillon, le nombre de GPU et la période de votre propre campagne. Les exemples 2.1 et 3.1 se refont de la même façon une fois les chapitres 2 et 3 lus (séance 2).
2.  Ajoutez à `test_iosizing.py` un test pour un cas que vous inventez (par exemple 9 Go/s sur des cibles de 2 Go/s) et faites-le passer.
3.  Partie B : comparez `lru_epoch_hit_ratio(0.5)` et `simulate_epoch_hit_ratio(2000, 1000, 6, "lru")`, puis essayez $x = 0{,}9$.
4.  Appelez `epoch_times` avec votre nombre de nœuds et vos débits, en affectation `sticky` puis `random`, et tracez la différence.
5.  Calculez la rétention et le pic de votre campagne avec `retained_checkpoint_bytes` et `peak_checkpoint_bytes` (en séance 8, après le chapitre 8).

**Critère de réussite.** `bash verify.sh` affiche `OK io-sizing` (16 tests fournis) : la simulation du LRU est à 3 points de la formule, le cache sans éviction à 3 points de $x$, et votre test passe. Sur la VM de test : `OK io-sizing: 70B checkpoint = 980 GB, LRU 15 % vs pinned 50 % hits at cache = 50 % of data`.

**Pour aller plus loin.** Ajoutez un modèle de coût avec le prix lu le jour même sur la page de votre fournisseur (`monthly_cost` le prend en argument).
:::

## Exercices {#ex}

::: exo
[Exercice 1 · ★ — Texte ou images : combien lit-on ?]{.tag} Un cluster de 512 GPU entraîne (a) un modèle de texte déjà découpé en jetons de 2 octets, à 12 000 jetons par seconde et par GPU ; (b) un modèle d'images, à 2 500 images par seconde et par GPU, chaque image pesant 120 ko (valeurs d'exemple). Calculez le débit de lecture agrégé de chaque charge, leur rapport, et le nombre d'ouvertures de fichier par seconde de la charge (b) si chaque image est un fichier.
:::

::: sol
(a) $512 \times 12\,000 \times 2 = 12\,288\,000$ octets par seconde, soit 12,3 Mo/s. (b) $512 \times 2\,500 \times 120\,000 = 153{,}6 \cdot 10^{9}$ octets par seconde, soit 153,6 Go/s. Le rapport est de 12 500.

Pour (b) en fichiers : $512 \times 2\,500 = 1\,280\,000$ ouvertures par seconde. Le texte ne pose pas de problème de débit ; pour les images, le débit **et** le nombre d'ouvertures posent problème, et c'est le second qui fait s'effondrer un serveur de métadonnées (chapitres 2 et 4). Attention aux unités : on utilise ici des octets décimaux (1 Go = $10^9$ octets), comme les fournisseurs.
:::

::: exo
[Exercice 2 · ★ — Checkpoint d'un modèle de 180 milliards de paramètres]{.tag} Un modèle de $180 \cdot 10^{9}$ paramètres est sauvegardé à raison de 14 octets par paramètre, toutes les 20 minutes. (a) Quelle est la taille d'un checkpoint ? (b) Quel débit d'écriture agrégé faut-il pour que l'écriture tienne dans 5 % de la période ? (c) Quel débit de lecture pour relire l'état en 300 s ? (d) Si le stockage délivre 25 Go/s en écriture, quelle fraction de la période occupe l'écriture ?
:::

::: sol
(a) $S = 180 \cdot 10^{9} \times 14 = 2{,}52$ To.

(b) Le débit d'écriture agrégé requis est

$$B = \frac{S}{f\tau} = \frac{2{,}52 \cdot 10^{12}}{0{,}05 \times 1\,200} = 42\ \text{Go/s}$$

(c) Pour la relecture : $2{,}52 \cdot 10^{12}/300 = 8{,}4$ Go/s.

(d) À 25 Go/s, l'écriture dure $100{,}8$ s, soit $100{,}8/1\,200 = 8{,}4$ % de la période : 1,7 fois la cible de 5 %. Commande : `python3 iosizing.py exercises` (valeurs `e2.*`).
:::

::: exo
[Exercice 3 · ★ — Lire un striping BeeGFS]{.tag} Voici un extrait de ce que la documentation de BeeGFS montre pour `beegfs entry info` sur un répertoire :

~~~text
Stripe pattern details:
+ Type: RAID0
+ Chunksize: 1M
+ Number of storage targets: desired: 4
~~~

(a) Un fichier de 10 Mio est créé dans ce répertoire. Combien de blocs, et combien sur chaque cible, en supposant une répartition en tourniquet ? (b) Même question pour un fichier de 300 Kio. (c) Quelle commande fait utiliser 8 cibles et des blocs de 4 Mio aux fichiers **futurs** de ce répertoire, et que devient un fichier existant ?
:::

::: sol
(a) 10 blocs de 1 Mio ; le bloc $k$ va sur la cible $k \bmod 4$ : les cibles 0 et 1 en reçoivent 3, les cibles 2 et 3 en reçoivent 2. (b) Un seul bloc (moins de 1 Mio), donc une seule cible : pas de parallélisme, comme pour tout petit fichier (chapitre 2). (c) `beegfs entry set --num-targets=8 --chunk-size=4MiB <répertoire>` ; la documentation précise que les paramètres s'appliquent aux **nouveaux** fichiers, pas aux existants, qui gardent leur répartition.
:::

::: exo
[Exercice 4 · ★★ — Combien de cibles pour un fichier partagé ?]{.tag} Un fichier de checkpoint partagé doit être écrit à 12 Go/s. Le système a 32 cibles de stockage qui délivrent chacune 2,5 Go/s, et 64 clients de 3 Go/s chacun. (a) Que donne le striping par défaut (1 cible) ? (b) Combien de cibles faut-il au minimum, et avec 20 % de marge ? (c) Combien de clients faut-il pour tenir 14,4 Go/s ? (d) Quel est le débit agrégé du système ? (e) Pourquoi ne pas régler 32 cibles pour tous les fichiers du répertoire ?
:::

::: sol
(a) 2,5 Go/s, soit 4,8 fois trop peu.

(b) $\lceil 12/2{,}5 \rceil = 5$ cibles ; avec 20 % de marge, $\lceil 14{,}4/2{,}5 \rceil = 6$ cibles.

(c) $\lceil 14{,}4/3 \rceil = 5$ clients au moins.

(d) $\min(64 \times 3,\; 32 \times 2{,}5) = \min(192, 80) = 80$ Go/s, limité par les cibles : l'écriture à 14,4 Go/s passe.

(e) Le manuel de Lustre donne les raisons : le striping ajoute des verrous et des opérations réseau pour `stat` et `unlink`, de la contention entre fichiers, un risque accru (une panne de serveur abîme une partie de chaque fichier) et aucun bénéfice pour les petits fichiers. On règle le striping **par répertoire**, pour les gros fichiers seulement. Commande : `python3 iosizing.py exercises` (valeurs `e4.*`).
:::

::: exo
[Exercice 5 · ★ — Combien de requêtes pour 20 Go/s ?]{.tag} Un chargeur doit lire 20 Go/s depuis un magasin d'objets dont le débit documenté est d'**au moins** 5 500 GET par seconde et par préfixe (on prend ce minimum comme hypothèse prudente). Calculez le nombre de GET par seconde et de préfixes nécessaires (a) pour des objets de 100 ko, (b) pour des plages de 8 Mio.
:::

::: sol
(a) $20 \cdot 10^{9} / 100\,000 = 200\,000$ GET/s, soit $\lceil 200\,000/5\,500 \rceil = 37$ préfixes. (b) $20 \cdot 10^{9} / (8 \times 2^{20}) = 2\,384$ GET/s, soit 1 préfixe. Même débit, 84 fois moins de requêtes : c'est l'argument des gros objets et des shards (chapitre 3).
:::

::: exo
[Exercice 6 · ★★ — Quelle taille de groupe de lignes Parquet ?]{.tag} Un jeu d'échantillons de 20 ko est stocké dans Parquet sur un magasin distant, de latence par requête $\alpha = 5$ ms et de débit $B = 1$ Go/s (valeurs d'exemple). Pour des groupes de 50, 1 000 et 100 000 lignes, calculez la taille du groupe, l'efficacité $\eta$ d'une lecture d'un groupe, l'amplification d'un accès aléatoire à un échantillon et le nombre d'échantillons par seconde qu'une connexion lit en accès aléatoire. Quelle taille choisissez-vous pour une lecture en flux avec mélange par tampon ? Pour de l'accès aléatoire ?
:::

::: sol
La taille de demi-performance est $n_{1/2} = \alpha B = 5$ Mo. Avec $\eta(n) = (n/B)/(\alpha + n/B)$ :

| Lignes par groupe | Taille du groupe | Efficacité | Amplification (accès aléatoire) | Échantillons/s par connexion (accès aléatoire) |
|---|---|---|---|---|
| 50 | 1 Mo | 16,7 % | 50 | 166,7 |
| 1 000 | 20 Mo | 80 % | 1 000 | 40 |
| 100 000 | 2 Go | 99,75 % | 100 000 | 0,5 |

Pour le flux avec mélange par tampon, 1 000 lignes (20 Mo, soit quatre fois $n_{1/2}$) donne 80 % d'efficacité sans granularité excessive ; 100 000 lignes gagne 20 points mais impose de lire des blocs de 2 Go. Pour l'accès aléatoire, **aucune** taille ne convient : 50 lignes amplifient déjà 50 fois et n'utilisent que 17 % du débit. Il faut sortir l'accès aléatoire de Parquet (fichier empaqueté avec index, chapitre 4). Commande : `python3 iosizing.py exercises` (valeurs `e6.*`).
:::

::: exo
[Exercice 7 · ★★ — Petits objets contre shards : la concurrence]{.tag} On veut lire 30 To par époque de 6 heures depuis un magasin d'objets. Chaque requête a une latence de 20 ms avant le premier octet, puis 100 Mo/s par connexion (valeurs d'exemple). Pour (a) des objets de 100 ko et (b) des plages de 16 Mio, calculez le débit d'une connexion, le nombre de connexions simultanées nécessaires (loi de Little : connexions = requêtes par seconde × durée d'une requête), les GET par seconde et les préfixes (5 500 GET/s chacun, minimum documenté pris comme hypothèse prudente). Que conclure ?
:::

::: sol
Le débit visé est $30 \cdot 10^{12}/21\,600 = 1{,}39$ Go/s. (a) Une requête de 100 ko dure $0{,}020 + 10^{5}/10^{8} = 0{,}021$ s : une connexion donne 4,76 Mo/s, donc il faut $1{,}39 \cdot 10^{9} / 4{,}76 \cdot 10^{6} = 292$ connexions, pour 13 889 GET/s et 3 préfixes. (b) Une plage de 16 Mio dure $0{,}020 + 16{,}78 \cdot 10^{6}/10^{8} = 0{,}188$ s : 89,3 Mo/s par connexion, donc 16 connexions suffisent (15,5 calculées), pour 83 GET/s et 1 préfixe.

Avec de petits objets, la latence domine : il faut près de dix-neuf fois plus de connexions et dépasser le minimum documenté d'un préfixe. Des shards lus par grandes plages ramènent le problème à une quinzaine de connexions. Commande : `python3 iosizing.py exercises` (valeurs `e7.*`).
:::

::: exo
[Exercice 8 · ★★ — Lire le tableau d'un chargeur]{.tag} Un job de 8 GPU sur un nœud de 32 cœurs donne le tableau suivant (**fictif**, pour l'exercice). Appliquez la table de décision de la section 5.5 (`diagnose`, seuils 5 % de *stall*, 0,7 cœur par worker, 80 % des cœurs) à chaque ligne, dites combien de cœurs sont occupés à 32 workers et quel est le nombre de cœurs par GPU, puis proposez deux actions pour la dernière ligne.

| Workers | *Stall* | CPU par worker |
|---|---|---|
| 0 | 62 % | n/a |
| 8 | 41 % | 0,18 |
| 24 | 19 % | 0,42 |
| 32 | 17 % | 0,86 |
:::

::: sol
Avec `loader_lab.diagnose(stall, util, workers, cores=32)` : 0 worker, chargement **en série** (activer `num_workers`) ; 8 workers, chargeur **à latence** (8 × 0,18 = 1,4 cœur seulement) ; 24 workers, encore **à latence** (24 × 0,42 = 10,1 cœurs, sous le seuil de 25,6) ; 32 workers, chargeur **CPU** (0,86 ≥ 0,7).

À 32 workers, $32 \times 0{,}86 = 27{,}5$ cœurs sont occupés sur 32 : les cœurs sont presque saturés, et passer de 24 à 32 workers n'a gagné que 2 points de *stall*. Il y a $32/8 = 4$ cœurs par GPU, dans la fourchette de 3 à 24 cœurs par GPU que l'étude sur les *data stalls* observe pour le prétraitement. Deux actions : réduire le coût par échantillon (prétraiter une fois, jetons ou images pré-empaquetés, chapitre 4) ; ajouter des cœurs ou déporter le décodage. Ajouter des workers ne sert à rien.
:::

::: exo
[Exercice 9 · ★★ — Un checkpoint qui arrête tout]{.tag} Un job de 512 GPU écrit un checkpoint de 1,2 To toutes les 30 minutes. Un horodatage autour de l'appel de sauvegarde mesure 240 s de blocage. (a) Quel débit effectif cela représente-t-il ? (b) Quel surcoût ? (c) On rend le checkpoint asynchrone, avec un snapshot de 3 s et la même durée de persistance : quel surcoût pour un intervalle de 30 minutes, de 5 minutes et de 3 minutes ? (d) Quel débit d'écriture faut-il pour tenir un intervalle de 3 minutes ? (e) Que concluez-vous sur la fréquence ?
:::

::: sol
(a) $1{,}2 \cdot 10^{12}/240 = 5$ Go/s.

(b) Synchrone : $240/1\,800 = 13{,}3$ %.

(c) Asynchrone, avec la formule de la section 6.3 : à 30 min, $3/1\,800 = 0{,}17$ % ; à 5 min, $3/300 = 1$ % ; à 3 min (180 s, moins que $T_p = 240$ s), $(3 + 60)/180 = 35$ %. Le synchrone à 5 min coûterait $240/300 = 80$ %.

(d) Pour que l'écriture tienne dans 180 s : $1{,}2 \cdot 10^{12}/180 = 6{,}7$ Go/s (sans marge).

(e) L'asynchrone permet de passer de 30 à 5 minutes pour 1 % de surcoût, mais il ne sert plus dès que $T_p > I$ : à 3 minutes, le surcoût remonte à 35 %. Descendre plus bas exige de réduire $T_p$ (plus de débit, un état plus petit, un niveau en mémoire du module 10), pas de rendre l'écriture « plus asynchrone ». Commande : `python3 iosizing.py exercises` (valeurs `e9.*`).
:::

::: exo
[Exercice 10 · ★★★ — Concevoir le cache d'un jeu de 40 To]{.tag} 32 nœuds de 8 GPU entraînent sur un jeu de 40 To découpé en shards. Chaque nœud dispose d'un cache NVMe local de $8 \times 3{,}84 = 30{,}72$ To (configuration documentée du DGX H100) et a besoin de 3 Go/s. Le stockage partagé délivre 40 Go/s au total (valeur d'exemple). Chaque nœud lit $D/N$ du jeu par époque. Le cache ne supprime jamais ses entrées.

 (a) Quelle fraction du jeu le cache d'un nœud représente-t-il, et quel serait le taux de succès d'un LRU si un seul nœud lisait tout le jeu ? (b) Quelle est la durée d'une époque à pleine vitesse, et de la première époque ? (c) Avec des shards réaffectés au hasard à chaque époque, calculez la durée des époques 2, 5, 10 et 20, et le total sur 20 époques. (d) Même question avec une affectation collante. (e) Que recommandez-vous, et quel en est le prix ?
:::

::: sol
(a) $x = 30{,}72/40 = 0{,}768$ ; un LRU rendrait $x + (1-x)\ln(1-x) = 0{,}429$ si un seul nœud lisait tout le jeu. (b) Chaque nœud lit $40/32 = 1{,}25$ To par époque. À 3 Go/s : 417 s. La première époque est limitée par le stockage partagé, soit $40/32 = 1{,}25$ Go/s par nœud : 1 000 s.

(c) Avec une affectation aléatoire, la probabilité qu'un shard soit déjà dans le cache de ce nœud à l'époque $k$ est $1 - (1 - 1/32)^{k-1}$ ; la vitesse est $\min(3,\; 1{,}25/(1 - h))$ Go/s. Durées : époque 2, 969 s ; époque 5, 881 s ; époque 10, 751 s ; époque 20, 547 s ; total sur 20 époques : **15 042 s**.

(d) Avec une affectation collante, l'époque 1 coûte 1 000 s, puis la part de 1,25 To de chaque nœud est locale : 417 s par époque, soit un total de **8 917 s**.

 (e) L'affectation collante, 1,69 fois plus rapide sur 20 époques, et elle ne charge plus le stockage partagé après l'époque 1. Le prix : un nœud ne voit toujours que sa partition, donc un mélange moins aléatoire ; on change la partition toutes les $K$ époques (chacune coûte alors une époque partiellement froide) ou on mélange à l'intérieur de gros shards. Commande : `python3 iosizing.py exercises` (valeurs `e10.*`).
:::

::: exo
[Exercice 11 · ★★★ — Une tempête de métadonnées]{.tag} Un jeu de 120 millions d'images de 110 ko est stocké sous forme de fichiers sur un système parallèle. Chaque époque lit chaque fichier une fois, avec 3 opérations de métadonnées par fichier. Le serveur de métadonnées soutient 50 000 opérations par seconde (**valeur supposée** ; à mesurer avec un outil de test de métadonnées).

 (a) Combien de temps de métadonnées par époque ? (b) Et si le jeu est converti en shards de 1 000 échantillons ? (c) Combien de temps coûte la conversion elle-même, sachant qu'elle lit chaque fichier une fois et que le stockage délivre 5 Go/s ? (d) Proposez un plan.
:::

::: sol
(a) $120 \cdot 10^{6} \times 3 = 3{,}6 \cdot 10^{8}$ opérations, soit $3{,}6 \cdot 10^{8}/50\,000 = 7\,200$ s : **2 heures de métadonnées par époque**, quelle que soit la vitesse des données. (b) 120 000 shards, donc $360\,000$ opérations, soit 7,2 s.

(c) La conversion lit 13,2 To ; à 5 Go/s, cela prend 44 minutes de données. Mais elle lit aussi 120 millions de fichiers : elle paie **une dernière fois** la facture de métadonnées de 2 heures. Le temps est donc borné par $\max(2\ \text{h},\, 0{,}73\ \text{h}) = 2$ h, et lancer plus de clients n'y change rien si le serveur de métadonnées est le goulot.

(d) Plan : convertir une fois en shards de 1 000 échantillons (environ 110 Mo, très au-dessus de $n_{1/2}$), les nommer avec un numéro et une version, mélanger l'ordre des shards et un tampon en mémoire (chapitre 4), vérifier par somme de contrôle et compter les échantillons avant de supprimer l'original. Commande : `python3 iosizing.py exercises` (valeurs `e11.*`).
:::

::: exo
[Exercice 12 · ★★★ — Le plan de capacité d'un programme de six mois]{.tag} Un modèle de 70 milliards de paramètres ($S = 980$ Go) s'entraîne 100 000 pas, avec un checkpoint tous les 500 pas. Rotation : les 3 derniers plus un sur 10 (retenus : $(K + \lfloor n/L \rfloor) S$ ; pic pendant la rotation : $(K+1) S$). Données : 60 To de brut, 20 To de jeu tokenisé en shards, 2 To de journaux et d'artefacts. Le système de travail purge les fichiers non lus depuis 8 semaines.

 (a) Quels volumes de checkpoints retenus et de pic ? (b) Quelle quotité demandez-vous sur le système de travail, avec 15 % de marge, en comptant un checkpoint de plus pour le pic ? (c) Où mettez-vous chaque classe de données au vu de la purge ? (d) Combien de fichiers de checkpoint avec 1 024 rangs et un fichier par rang ? (e) Coût relatif si le brut est au quart du prix du chaud (hypothèse) ?
:::

::: sol
(a) $n = 100\,000/500 = 200$ checkpoints écrits ; retenus : $3 + 20 = 23$, soit $23 \times 0{,}98 = 22{,}5$ To ; pic de la rotation : $4 \times 0{,}98 = 3{,}92$ To. Sans rotation : 196 To.

(b) Le chaud vaut $22{,}54 + 20 + 2 = 44{,}54$ To ; en ajoutant un checkpoint pour le pic, $(44{,}54 + 0{,}98) \times 1{,}15 = 52{,}3$ To. (c) Le brut (60 To, relu rarement) va en archive ou sur un niveau froid. Les shards tokenisés sont relus à chaque époque, donc leur date d'accès se renouvelle, mais gardez une copie sur un niveau durable. Les 20 checkpoints « un sur dix » vont sur un niveau durable **sans purge** : écrits puis jamais relus, ils seraient purgés au bout de 8 semaines. Les 3 derniers restent sur le système de travail. (d) $1\,024 \times 23 = 23\,552$ fichiers, à ajouter au quota de fichiers.

(e) Tout au prix chaud $p$ : $22{,}54 + 20 + 2 + 60 = 104{,}54$ To × $p$. Avec le brut au quart du prix : $44{,}54 + 15 = 59{,}54$ To × $p$, soit 43 % de moins. Le quart est une hypothèse. Commande : `python3 iosizing.py exercises` (valeurs `e12.*`).
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux estimer le débit de lecture et le débit de checkpoint d'un entraînement.** Preuve : les exercices 1 et 2 refaits avec les chiffres de votre cluster, via `iosizing.py`.
-   **Je peux régler un striping et dimensionner un système parallèle.** Preuve : l'exercice 4 refait pour votre débit visé, avec la règle « le moins de cibles possible ».
-   **Je peux choisir entre NFS, objet et FUSE pour un usage donné.** Preuve : un tableau des garanties de cohérence et de renommage de votre candidat, avec la source.
-   **Je peux chiffrer l'amplification d'un format de données.** Preuve : le tableau du lab 8.2 pour votre jeu, avec ouvertures, requêtes et octets lus.
-   **Je peux diagnostiquer un chargeur lent.** Preuve : le *stall*, les workers et le CPU par worker d'un job réel, et la ligne de la table de décision qui en découle (exercice 8).
-   **Je peux modéliser le coût d'un checkpoint.** Preuve : le lab 8.3 sur votre stockage et l'exercice 9 refait avec vos mesures.
-   **Je peux prévoir et concevoir un cache.** Preuve : l'exercice 10 refait avec vos tailles, y compris le choix de l'affectation des shards.
-   **Je peux planifier la capacité d'un programme.** Preuve : l'exercice 12 refait pour votre campagne, avec rétention, pic, quotas et coût sans prix figé.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Vos GPU sont à 60 % d'utilisation et le job charge des images depuis NFS. Que faites-vous ?* Réponse-type : mesurer d'abord la part d'attente autour du `next()` du chargeur, puis le CPU par worker pour distinguer latence et calcul ; compter les fichiers et les ouvertures par époque ; mesurer $\alpha$ et $B$ du montage ; passer à des shards lus par gros morceaux ; mettre en cache sur NVMe local avec une affectation collante ; ne pas ajouter de workers avant d'avoir lu le CPU.
2.  *Un checkpoint de 1,2 To arrête l'entraînement 4 minutes toutes les 30 minutes. Comment réduisez-vous le coût ?* Réponse-type : distinguer temps bloquant et temps de persistance ; passer en deux phases (snapshot puis écriture de fond, une seule persistance en vol) pour tomber de 13 % à moins de 1 % ; vérifier que la persistance tient dans l'intervalle ; augmenter le débit (striping, un fichier par rang) ou descendre la fréquence si elle ne tient plus.
3.  *Comment dimensionneriez-vous le stockage d'un cluster de 256 GPU pour un programme de six mois ?* Réponse-type : les quatre flux ; lecture = consommateurs × rythme × taille, checkpoint = $S/(f\tau)$ avec $S = 14\Psi$ ; rétention et pic de rotation ; quotas d'espace et de fichiers ; niveaux de durée de vie face à la purge ; une recette de stockage avec des critères chiffrés ; aucun prix figé, à relire le jour de l'engagement.

## Lectures et références {#refs}

-   Whamcloud et la communauté Lustre. [*Lustre Software Release 2.x Operations Manual*](https://doc.lustre.org/lustre_manual.xhtml), lu le 24 octobre 2026 : composants (§ 1.2.2), striping (chap. 19), Data on MDT (chap. 20), quotas (chap. 25), petits fichiers (§ 34.10) ; chapitres 2, 6 et 8.
-   ThinkParQ. [*BeeGFS documentation, Architecture*](https://doc.beegfs.io/latest/architecture/overview.html) et [*Striping*](https://doc.beegfs.io/latest/advanced_topics/striping.html) : séparation métadonnées et données, `beegfs entry set` ; chapitre 2 et exercice 3.
-   WEKA. [*Documentation, About*](https://docs.weka.io/weka-system-overview/about) : nature du système, conteneurs, quotas, instantanés ; chapitres 2 et 8.
-   NERSC. [*Perlmutter scratch*](https://docs.nersc.gov/filesystems/perlmutter-scratch/) et IDRIS. [*Jean Zay : matériel*](http://www.idris.fr/docs/jean-zay/jean-zay/jean-zay-hardware) : exemples d'exploitants (système tout flash, purge de huit semaines, trois niveaux de stockage) ; chapitres 2 et 8.
-   Linux man-pages. [*nfs(5)*](https://man7.org/linux/man-pages/man5/nfs.5.html) et [*proc_pid_io(5)*](https://man7.org/linux/man-pages/man5/proc_pid_io.5.html) : cohérence à la fermeture, `nconnect`, compteurs `rchar`, `syscr`, `read_bytes` ; chapitres 3 et 4.
-   Amazon Web Services. *Amazon S3 User Guide* : [modèle de cohérence](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) et [optimisation des performances](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html) : cohérence forte, requêtes par préfixe, erreurs 503 ; chapitre 3.
-   AWS Labs. [*Mountpoint for Amazon S3, SEMANTICS.md*](https://raw.githubusercontent.com/awslabs/mountpoint-s3/main/doc/SEMANTICS.md) : ce qu'un montage objet ne fait pas ; chapitre 3.
-   Breuel. [*WebDataset, README*](https://raw.githubusercontent.com/webdataset/webdataset/main/README.md) : format de shards tar et ses limites ; chapitre 4.
-   Apache. [*Parquet format*](https://raw.githubusercontent.com/apache/parquet-format/master/README.md), Hugging Face. [*Datasets : about Arrow*](https://huggingface.co/docs/datasets/about_arrow) et Karpathy. [*nanoGPT, train.py*](https://raw.githubusercontent.com/karpathy/nanoGPT/master/train.py) : groupes de lignes, mémoire projetée, jetons empaquetés ; chapitre 4.
-   PyTorch. [*Code source de `torch.utils.data.DataLoader`*](https://raw.githubusercontent.com/pytorch/pytorch/main/torch/utils/data/dataloader.py), docstring : paramètres et ordre de livraison ; chapitre 5. (La page de documentation HTML n'a pas livré de texte exploitable depuis le bac à sable.)
-   Mohan, Phanishayee, Raniwala, Chidambaram. [*Analyzing and Mitigating Data Stalls in DNN Training*](https://arxiv.org/abs/2007.06775), VLDB 2021 : *prep stalls* et *fetch stalls*, cache de pages, MinIO ; chapitres 5 et 7.
-   Mohan, Phanishayee, Chidambaram. [*CheckFreq: Frequent, Fine-Grained DNN Checkpointing*](https://www.usenix.org/conference/fast21/presentation/mohan), FAST 2021 : checkpoint en deux phases, état du chargeur ; chapitre 6.
-   Dubey et al. [*The Llama 3 Herd of Models*](https://arxiv.org/abs/2407.21783), 2024, § 3.3.1 : le stockage d'un entraînement à 16 000 GPU ; chapitre 1.
-   Jiang et al. [*MegaScale*](https://arxiv.org/abs/2402.15627), 2024, section 3 : un chargeur dédié par machine ; chapitre 5.
-   NVIDIA. [*GPUDirect Storage Overview Guide*](https://docs.nvidia.com/gpudirect-storage/overview-guide/index.html) et [*DGX H100 User Guide*](https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html) : chemin direct GPU-stockage, configuration NVMe d'un nœud ; chapitre 7.

## Sources et portée {#sources}

**Documenté.** Les faits attribués à une source dans le texte ont été relus à la source le 24 octobre 2026 : les composants, les valeurs par défaut et les limites de striping, Data on MDT, la règle « as few objects… » et les quotas de Lustre ; l'architecture et le striping de BeeGFS ; la description générale de WEKA ; les chiffres du système de travail de Perlmutter, sa politique de purge et le matériel de Jean Zay ; la cohérence à la fermeture, `nconnect` et les compteurs de `/proc/<pid>/io` ; la cohérence et les débits par préfixe de S3 ; la sémantique de Mountpoint ; le format WebDataset ; la définition de Parquet, le cache mémoire projeté de Hugging Face Datasets et le `train.bin` de nanoGPT ; la docstring de `DataLoader` ; les résultats et le cache MinIO de l'étude sur les *data stalls* ; le résumé de CheckFreq ; le paragraphe sur le stockage de Llama 3 ; le chargeur unique par machine de MegaScale ; le guide de GPUDirect Storage et la configuration NVMe du DGX H100. Tous les chiffres des exemples et des corrigés viennent de `iosizing.py` (commandes `demo` et `exercises`) ou des sorties des labs, exécutés dans le bac à sable le 24 octobre 2026 (noyau Linux 6.18, 4 vCPU, PyTorch 2.14.1 CPU, `fio` 3.36, `pyarrow` 26.0.0, `webdataset` 1.0.2).

**Recommandé.** L'ordre des chapitres ; les quatre flux d'E/S ; les seuils de la table de décision du chargeur (5 %, 0,7 cœur, 80 %) ; le protocole « shards immuables avec manifeste » pour l'invalidation ; l'affectation collante des shards ; la recette de stockage en cinq essais ; les quatre classes de durée de vie ; la politique de sauvegarde par classe ; la rotation $K$ derniers plus un sur $L$ avec un quota couvrant le pic. Ce sont des choix de ce parcours, pas des normes.

**À vérifier.** (1) La documentation de GPFS / IBM Storage Scale a répondu HTTP 403 : aucun fait sur ce système n'est avancé, et celle de WEKA n'a été lue que dans sa page de présentation. (2) La formule du taux de succès d'un LRU en époques aléatoires est une **dérivation de ce parcours** (champ moyen), vérifiée par simulation à 3 points près ; ce n'est pas un résultat publié. Le modèle d'affectation collante ou aléatoire est une simplification (cache sans éviction, parts égales). (3) L'écart entre le modèle du chargeur et la mesure à 8 workers n'est pas expliqué : la livraison dans l'ordre a été testée (`in_order=False`) et écartée. Plusieurs autres explications sont des **hypothèses non testées** : l'amplification de 3,4 de `mmap` (lecture autour de la faute de page), le 1,30 de la lecture aléatoire de shards (échantillons à cheval sur cinq pages), l'écart de l'asynchrone mesuré (8,9 %) et prédit (4,3 %), le coût de la première copie dans un tampon neuf (attribution tardive de la mémoire par l'hôte) et l'effet de l'option `discard` sur les écritures parallèles. (4) Les entrées des exemples (3 000 images par seconde, 110 ou 120 ko par image, 8 000 jetons par seconde, latences de 20 ms, 40 Go/s de débit partagé, 50 000 opérations de métadonnées par seconde, quart de prix) sont des **valeurs d'exemple**, pas des mesures de produits. (5) L'affirmation de WebDataset sur un gain de 3 à 10 fois n'a pas été reproduite. (6) Le manuel de Lustre lu est celui du site officiel ; vérifiez la version de votre déploiement pour les fonctions citées avec un numéro (2.11, 2.13). (7) `pin_memory` et GPUDirect Storage n'ont pas été exécutés (pas de GPU) ; `fio_gap.py` et `bench_ckpt.py` n'ont pas été lancés sur NFS, ni sur un système parallèle, ni sur un stockage objet monté. (8) La page de documentation HTML de `DataLoader` n'a pas livré de texte : les paramètres viennent de la docstring du code source (branche `main`, lue le 24 octobre 2026) ; relisez la documentation de votre version. (9) Aucun prix n'est cité.

**Hors périmètre.** La conception d'un système de fichiers parallèle ou d'un stockage Ceph ; les réseaux de stockage (RDMA, NVMe sur fabric : module 7) ; le protocole et le format d'un checkpoint (atomicité, sommes de contrôle, reprise : module 10) ; les volumes Kubernetes et leurs pilotes CSI (module 12) ; le chiffrement au repos et le contrôle d'accès (module 16) ; le décodage d'images sur GPU (DALI) ; les tarifs des fournisseurs ; l'exécution de GPUDirect Storage.
