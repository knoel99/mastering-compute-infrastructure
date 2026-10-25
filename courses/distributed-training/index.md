---
title: "Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline"
subtitle: "Module 09 · Phase 3 · 36 h"
description: "Choisir un parallélisme, estimer la mémoire et la communication d'un entraînement multi-GPU, lancer et déboguer un job multi-processus, et distinguer un bug de distribution d'une instabilité numérique."
module:
  id: distributed-training
  number: 9
  phase: 3
  hours: 36
  level: 3
prerequisites: [perf-models, gpu-programming, networking]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs vérifiés dans un bac à sable (CPU, gloo, sans GPU)", class: verified}
labs:
  - {id: ddp-gloo, kind: sandbox}
  - {id: fsdp-memory, kind: sandbox}
  - {id: hang-debug, kind: sandbox}
  - {id: parallelism-planner, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** un modèle de langage ne tient plus sur un GPU, ou l'entraîner sur un seul prendrait des années. Comment le découper sur des dizaines ou des milliers de GPU, quelle part du temps part en communication, et comment savoir qu'un découpage est bon ? Un ingénieur d'infrastructure qui ne sait pas répondre dépend des chercheurs pour dire si son cluster est bien utilisé.

Ce module donne un vocabulaire (données, tenseur, pipeline, experts, séquence), des formules de mémoire et de communication que vous refaites vous-même, un outil de calcul testé, et une méthode pour déboguer ce qui se passe quand plusieurs processus doivent rester d'accord. Les labs tournent sur CPU avec le backend `gloo` : la **méthode** est celle d'un cluster, pas les débits.

::: key
[Règle de ce module]{.tag} Chaque parallélisme est un choix de ce qu'on échange : gradients, paramètres, activations ou jetons. Choisir une disposition, c'est placer chaque échange sur le lien qui peut le porter. Un chiffre de mémoire ou de communication que vous ne pouvez pas recalculer à la main n'est pas une raison de décider.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 36 h, dont environ 14 h de lecture (chapitres, questions de positionnement, checkpoint de sortie), 13 h de labs et 9 h d'exercices |
| Niveau d'entrée | 3 : vous savez écrire une boucle d'entraînement PyTorch, lire un MFU et un modèle α-β (module 2), et vous connaissez le rôle de NCCL (module 7) |
| Prérequis | [Module 2 — Architecture et modèles de performance](../perf-models/index.html), [Module 4 — Programmation GPU](../gpu-programming/index.html), [Module 7 — Réseaux haute performance](../networking/index.html) |
| Statut pour le lecteur de référence | cœur : aucune expérience d'entraînement multi-nœuds dans le profil |
| Livrable | un planificateur de parallélisme testé, un DDP prouvé équivalent à un entraînement mono-processus, une mesure de mémoire FSDP comparée à sa prédiction, une procédure d'enquête sur un hang |
| Environnement | un portable CPU avec PyTorch suffit : les quatre labs tournent sur 4 processus `gloo`, sans GPU. Ce que seuls des GPU permettraient (NCCL, recouvrement réel, MFU mesuré) est décrit et sourcé, jamais présenté comme exécuté |
| Projets liés | [Projet 2 — Étude de passage à l'échelle](../../projects/scaling-study/index.html), [Projet 3 — Entraîneur tolérant aux pannes](../../projects/resilient-trainer/index.html), [Projet 6 — RFC de plateforme](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Décoder une configuration de parallélisme (par exemple celle de Llama 3 405B) : degrés, nombre de GPU, tokens par lot, groupes de communication (chapitre 1).
-   Lancer un job avec `torchrun`, prédire le découpage en seaux de DDP et reproduire puis corriger ses erreurs classiques (chapitre 2, lab 9.1).
-   Calculer la mémoire par GPU d'un entraînement pour ZeRO 0 à 3 et pour FSDP, et la comparer à une mesure (chapitre 3, lab 9.2).
-   Chiffrer la communication du parallélisme tensoriel, la bulle d'un pipeline et le trafic d'un parallélisme d'experts (chapitre 4, lab 9.4).
-   Choisir et justifier une disposition `(tp, pp, dp)` pour un modèle et un cluster donnés, en disant ce que le modèle de calcul ne voit pas (chapitre 5).
-   Décomposer l'écart entre un MFU mesuré et un MFU attendu, et choisir le levier le plus rentable (chapitre 6).
-   Séparer un bug de distribution d'une instabilité numérique, et dire ce qu'on peut exiger de la reproductibilité (chapitre 7).
-   Localiser un hang par une procédure reproductible et lire la configuration de Megatron-LM, DeepSpeed ou TorchTitan (chapitres 8 et 9, lab 9.3).

### Plan de séances {#seances}

Douze séances de 3 h, soit 36 h. Le niveau 1 correspond aux fondations, le niveau 2 aux méthodes de cœur, le niveau 3 à l'avancé ; il ne diminue jamais. Les durées entre parenthèses sont celles de la lecture, des labs et des exercices : leur somme vaut 14 h, 13 h et 9 h.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 3 h | 1 | Positionnement (15 min) ; ch. 1 (75 min) ; ch. 2 §2.1 à §2.3 (65 min) | Ex. 1 (25 min) |
| 2 | 3 h | 1 | ch. 2 fin (25 min) ; ch. 3 §3.1 (5 min) | Lab 9.1 partie A (90 min) ; Ex. 2 (25 min), Ex. 4 (35 min) |
| 3 | 3 h | 2 | ch. 3 §3.1 et §3.2 (55 min) | Lab 9.1 partie B (90 min) ; Ex. 5 (35 min) |
| 4 | 3 h | 2 | ch. 3 §3.3 à §3.5 (60 min) ; ch. 4 §4.1 (5 min) | Lab 9.2 partie A (90 min) ; Ex. 3 (25 min) |
| 5 | 3 h | 2 | ch. 4 §4.1 (20 min) | Lab 9.2 partie B (90 min) ; Ex. 6 (35 min), Ex. 13 (35 min) |
| 6 | 3 h | 2 | ch. 4 §4.2 à §4.4 (125 min) ; ch. 5 §5.1 (20 min) | Ex. 7 (35 min) |
| 7 | 3 h | 2 | ch. 5 §5.1 et §5.2 (25 min) | Lab 9.4 partie A (120 min) ; Ex. 8 (35 min) |
| 8 | 3 h | 2 | ch. 5 §5.3 à §5.5 (45 min) ; ch. 6 §6.1 (15 min) | Lab 9.4 partie B (120 min) |
| 9 | 3 h | 3 | ch. 6 (45 min) ; ch. 7 §7.1 (25 min) | Ex. 10 (55 min), Ex. 11 (55 min) |
| 10 | 3 h | 3 | ch. 7 (50 min) ; ch. 8 §8.1 à §8.3 (75 min) | Ex. 12 (55 min) |
| 11 | 3 h | 3 | ch. 8 fin (15 min) ; ch. 9 §9.1 et §9.2 (40 min) | Lab 9.3 partie A (90 min) ; Ex. 9 (35 min) |
| 12 | 3 h | 3 | ch. 9 fin (20 min) ; checkpoint de sortie (15 min) | Lab 9.3 partie B (90 min) ; Ex. 14 (55 min) |

## Avant de commencer {#avant}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si elles vous semblent routinières, lisez les chapitres 5 et 8, faites les exercices ★★★ et passez au module 10.

1.  **Tient-il sur un GPU ?** Un modèle de 7 milliards de paramètres est entraîné en précision mixte BF16 avec Adam. Tient-il sur un GPU de 80 Go ? Justifiez par un calcul.

2.  **Moyenne des moyennes.** Quatre processus calculent chacun la perte moyenne de 16 exemples, soit un lot global de 64. DDP fait la moyenne de leurs gradients. Obtient-on le gradient d'un seul processus sur les 64 exemples ? Et si les processus recevaient 20, 20, 20 et 4 exemples ?

3.  **Une collective sautée.** Quatre processus appellent chacun `dist.all_reduce` à chaque étape. L'un d'eux saute l'appel une seule fois, puis continue normalement. Que voyez-vous tout de suite, et que voyez-vous plus tard ?

::: sol
**Réponses.**

1.  Non. Il faut 2 octets de poids, 2 de gradient et 12 d'états d'optimiseur par paramètre, soit $16 \times 7 \cdot 10^{9} = 112$ Go avant les activations (module 2, chapitre 7). Chapitre 3.

2.  Avec des parts égales, oui : la moyenne de quatre moyennes de 16 exemples est la moyenne des 64, et le gradient est linéaire. Avec 20, 20, 20 et 4, non : les 4 exemples du dernier processus pèsent un quart du gradient au lieu d'un seizième. Le lab 9.1 mesure l'écart. Chapitre 2.

3.  Rien tout de suite. Les collectives s'apparient par **ordre d'appel**, pas par étape : les autres apparient leur étape $k$ avec l'étape $k+1$ du processus fautif, les gradients sont mélangés en silence, et le job ne se bloque qu'à la fin, loin du bug (lab 9.3). Chapitre 8.
:::

## 1. Panorama : données, tenseurs, pipeline, experts, séquence {#ch1}

Ce chapitre fixe le vocabulaire et la grille de lecture du module. Vous n'y apprenez aucun algorithme : vous apprenez à regarder une configuration de parallélisme et à dire ce que chaque nombre implique pour la mémoire, le réseau et le placement des processus.

### 1.1. Pourquoi découper un entraînement

Deux raisons, et il faut savoir laquelle est en cause. La **mémoire** : les états d'un entraînement ne tiennent pas dans les 80 Go d'un GPU (chapitre 3). Le **temps** : le calcul total, de l'ordre de $6\Psi D$ FLOP pour $\Psi$ paramètres et $D$ tokens, demande des milliers de GPU pour finir en semaines (module 2, chapitre 7).

Un modèle de 1 milliard de paramètres tient sur un GPU mais s'entraîne mieux sur huit ; un modèle de 70 milliards ne tient sur aucun, quel que soit le temps disponible. Les deux problèmes se traitent avec des outils différents.

### 1.2. Les cinq dimensions

On découpe le travail selon cinq axes. Chacun partage un objet différent, donc échange un objet différent.

| Dimension | Ce qui est découpé | Ce qui circule | Collective typique |
|---|---|---|---|
| **Données** (DP) | le lot ; le modèle est répliqué | gradients, une fois par étape | all-reduce |
| **Données partitionnées** (ZeRO, FSDP) | le lot et les états du modèle | paramètres avant chaque couche, gradients | all-gather, reduce-scatter |
| **Tenseur** (TP) | les matrices de chaque couche | activations, à chaque bloc | all-reduce, ou reduce-scatter et all-gather |
| **Pipeline** (PP) | les couches, en étages | activations entre étages | envoi et réception point à point |
| **Experts** (EP) | les experts d'un modèle MoE | jetons vers leur expert | all-to-all |
| **Séquence / contexte** (SP, CP) | la longueur de la séquence | clés et valeurs de l'attention | all-gather, point à point |

Le **parallélisme de séquence** (SP) de Megatron-LM et le **parallélisme de contexte** (CP) de Llama 3 sont deux choses différentes, souvent confondues. Le premier répartit sur la séquence les activations des couches de normalisation et de *dropout*, à l'intérieur d'un groupe de tenseurs ([Korthikanti et al., 2022](https://arxiv.org/abs/2205.05198)). Le second découpe la séquence d'entrée elle-même, pour que l'attention d'un contexte de 128 000 tokens tienne en mémoire ([Dubey et al., 2024](https://arxiv.org/abs/2407.21783), section 3.3.2).

### 1.3. La grille

Un GPU a une coordonnée dans chaque dimension, et le nombre de GPU est le produit des degrés. Pour $t$ en tenseur, $p$ en pipeline et $d$ en données :

$$N = t \times p \times d$$

C'est la grille « 3D » du papier Megatron-LM de 2021, appelée PTD-P (*pipeline, tensor, data*). Avec contexte et experts, elle passe à quatre ou cinq dimensions ; Megatron Core écrit le produit de tous les degrés, mais le chapitre 9 montre que son tableau d'exemples ne l'applique pas partout.

<figure class="fig">
<svg viewBox="0 0 560 360" role="img" aria-labelledby="grid-t grid-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="grid-t">Placer les dimensions du parallélisme sur la hiérarchie matérielle</title>
<desc id="grid-d">Un nœud de huit GPU porte le tenseur, quatre nœuds en série portent les étages d'un pipeline, trois répliques du pipeline portent les données.</desc>
<defs><marker id="arr1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--accent)"/></marker></defs>
<g fill="var(--side-bg)" stroke="currentColor" stroke-width="2"><rect x="20" y="30" width="520" height="92" rx="6"/>
<rect x="30" y="148" width="100" height="44" rx="4"/>
<rect x="160" y="148" width="100" height="44" rx="4"/>
<rect x="290" y="148" width="100" height="44" rx="4"/>
<rect x="420" y="148" width="100" height="44" rx="4"/>
</g>
<g fill="var(--side-bg)" stroke="currentColor"><rect x="30" y="238" width="360" height="22" rx="3"/><rect x="30" y="266" width="360" height="22" rx="3"/><rect x="30" y="294" width="360" height="22" rx="3"/></g>
<g fill="var(--accent)" fill-opacity="0.35" stroke="currentColor"><rect x="40" y="44" width="44" height="34"/><rect x="100" y="44" width="44" height="34"/><rect x="160" y="44" width="44" height="34"/><rect x="220" y="44" width="44" height="34"/><rect x="280" y="44" width="44" height="34"/><rect x="340" y="44" width="44" height="34"/><rect x="400" y="44" width="44" height="34"/><rect x="460" y="44" width="44" height="34"/></g>
<g stroke="var(--accent)" stroke-width="3" marker-end="url(#arr1)"><line x1="132" y1="170" x2="158" y2="170"/><line x1="262" y1="170" x2="288" y2="170"/><line x1="392" y1="170" x2="418" y2="170"/></g>
<line x1="404" y1="249" x2="404" y2="305" stroke="var(--accent)" stroke-width="3"/>
<g text-anchor="middle" font-size="14" fill="currentColor"><text x="62" y="66">G0</text><text x="122" y="66">G1</text><text x="182" y="66">G2</text><text x="242" y="66">G3</text><text x="302" y="66">G4</text><text x="362" y="66">G5</text><text x="422" y="66">G6</text><text x="482" y="66">G7</text><text x="80" y="176">étage 0</text><text x="210" y="176">étage 1</text><text x="340" y="176">étage 2</text><text x="470" y="176">étage 3</text></g>
<g text-anchor="middle" font-size="15" font-weight="700" fill="currentColor"><text x="280" y="108">TP = 8 · NVLink · all-reduce d'activations</text><text x="280" y="216">PP = 4 · un étage par nœud · activations point à point</text></g>
<g font-size="14" fill="currentColor"><text x="42" y="254">réplique 0 (pipeline complet)</text><text x="42" y="282">réplique 1</text><text x="42" y="310">réplique 2</text><text x="416" y="292">gradients</text></g>
<text x="416" y="272" font-size="15" font-weight="700" fill="currentColor">DP = 3</text>
<text x="280" y="346" text-anchor="middle" font-size="15" fill="currentColor">GPU au total : N = TP × PP × DP = 8 × 4 × 3 = 96</text>
</svg>
<figcaption>Une grille 3D de 96 GPU. Le parallélisme tensoriel occupe les huit GPU d'un nœud, le pipeline s'étend sur quatre nœuds, trois répliques de ce pipeline forment le parallélisme de données.</figcaption>
</figure>

L'**ordre** des dimensions décide quels GPU sont voisins. Llama 3 range ses groupes dans l'ordre [TP, CP, PP, DP], du plus interne au plus externe : les GPU d'un groupe de tenseurs sont consécutifs, donc dans le même nœud, et les groupes de données traversent le réseau. Le chapitre 5 y revient.

::: ex
[Exemple 1.1 — Décoder une ligne du tableau de Llama 3 405B]{.tag} Le tableau 4 de l'[article Llama 3](https://arxiv.org/abs/2407.21783) donne trois configurations. Première ligne : 8 192 GPU, TP 8, CP 1, PP 16, DP 64, séquences de 8 192 tokens, 32 séquences par groupe de données.

Le produit des degrés vaut $8 \times 1 \times 16 \times 64 = 8192$. Le lot global compte $64 \times 32 = 2048$ séquences, soit $2048 \times 8192 = 16\,777\,216$ tokens : les « 16M » de la colonne *Tokens/Batch*. La deuxième ligne double les GPU (DP 128) et divise par deux le lot par groupe (16) : le lot global reste de 2 048 séquences. Les auteurs attribuent la baisse de MFU (*model FLOPs utilization*, module 2) de 43 % à 41 % à ce lot plus petit par groupe.

La colonne *TFLOPs/GPU* est arrondie : 400 TFLOP/s sur 989 donneraient 40,4 %, et l'article annonce 41 %.
:::

::: ex
[Exemple 1.2 — Les groupes de communication d'un job à 16 GPU]{.tag} La figure 5 de l'article Llama 3 décrit 16 GPU avec 2 degrés partout. Le module `mesh.py` du lab 9.4 calcule les groupes (noms listés du plus externe au plus interne) ; sortie capturée sur la VM de rédaction :

~~~python
from mesh import Mesh
m = Mesh(("dp", "pp", "cp", "tp"), (2, 2, 2, 2))
print("rank 5 coords (dp, pp, cp, tp):", m.coords(5))
for name in m.names:
    print(f"group {name}:", m.group(5, name))
~~~

~~~text
rank 5 coords (dp, pp, cp, tp): (0, 1, 0, 1)
group dp: [5, 13]
group pp: [1, 5]
group cp: [5, 7]
group tp: [4, 5]
~~~

Pour le GPU 0, le code donne les groupes [0, 1] (tenseur), [0, 2] (contexte), [0, 4] (pipeline) et [0, 8] (données) : c'est le texte de la légende de la figure 5. Un GPU appartient à **un groupe par dimension**, et chaque collective ne concerne que son groupe.
:::

### 1.4. Les collectives dont vous aurez besoin

Une **collective** est une opération de communication à laquelle tous les membres d'un groupe participent. Le **rang** (*rank*) est le numéro d'un processus dans le groupe ; la **taille du monde** (*world size*) est le nombre de processus. Le tableau suppose l'anneau du module 2 et $n$ octets pour le tenseur complet.

| Collective | Avant → après, pour chaque rang | Octets émis par rang | Où la rencontre-t-on |
|---|---|---|---|
| *all-reduce* | un tableau de $n$ octets → la somme des $p$ tableaux | $2\,\frac{p-1}{p}\,n$ | gradients de DDP, sorties du TP |
| *reduce-scatter* | un tableau de $n$ → un morceau de $n/p$ de la somme | $\frac{p-1}{p}\,n$ | gradients de FSDP et de ZeRO |
| *all-gather* | un morceau de $n/p$ → le tableau complet | $\frac{p-1}{p}\,n$ | paramètres de FSDP et de ZeRO-3 |
| *all-to-all* | $p$ morceaux distincts → $p$ morceaux reçus | $\frac{p-1}{p}\,n$ | parallélisme d'experts |
| envoi / réception | un tableau → un voisin | $n$ | pipeline |
| *broadcast*, *barrier* | rang 0 → tous ; synchronisation | de l'ordre de $n$ ; aucun | initialisation de DDP ; débogage |

Un all-reduce est un reduce-scatter suivi d'un all-gather : sa charge est la somme des deux, ce qui permet à ZeRO (chapitre 3) de changer de forme sans changer le volume. Les collectives s'**apparient par ordre d'appel** : la $k$-ième collective d'un rang se joint à la $k$-ième des autres. C'est la source de la plupart des blocages du chapitre 8.

::: recap
Points clés — chapitre 1

-   On découpe pour deux raisons distinctes, la mémoire et le temps ; le diagnostic précède le choix.
-   Cinq dimensions, cinq objets échangés : gradients, paramètres, activations, jetons, clés et valeurs.
-   Le nombre de GPU est le produit des degrés ; l'ordre des dimensions décide quels GPU sont voisins.
-   Un GPU appartient à un groupe par dimension ; `mesh.py` et `DeviceMesh` calculent ces groupes.
-   Les collectives s'apparient par ordre d'appel, pas par étape ni par nom.
:::

## 2. DDP : seaux, recouvrement, torchrun et erreurs classiques {#ch2}

Le parallélisme de données est la brique de base : presque toute disposition en contient une. Ce chapitre explique ce que fait `DistributedDataParallel` (DDP) pendant la passe arrière, comment `torchrun` lance et relance les processus, et pourquoi les erreurs classiques sont presque toutes des erreurs d'accord entre rangs. Les mesures viennent du lab 9.1.

### 2.1. Ce que fait DDP

Chaque processus détient une copie complète du modèle et traite sa part du lot. Au moment de construire DDP, le rang 0 diffuse ses paramètres et ses *buffers* aux autres : toutes les copies démarrent identiques ([notes DDP de PyTorch](https://docs.pytorch.org/docs/2.14/notes/ddp.html)). Pendant la passe arrière, les gradients sont **moyennés** entre les processus ; chacun applique ensuite le même optimiseur au même gradient, et les copies restent égales sans autre échange.

Si les $p$ processus reçoivent des parts de taille égale et calculent une perte moyenne, la moyenne des gradients locaux $g_r$ est exactement le gradient de la perte moyenne sur le lot global :

$$g = \frac{1}{p}\sum_{r=1}^{p} g_r = \nabla \left( \frac{1}{B}\sum_{i=1}^{B} \ell_i \right) \quad \text{si chaque part compte } B/p \text{ exemples}$$

La condition « parts égales » est l'hypothèse cachée. Elle tombe dès que le dernier lot d'une époque est plus court sur certains rangs. Le lab 9.1 mesure l'équivalence, et ce qui se passe quand elle tombe.

::: ex
[Exemple 2.1 — DDP à quatre processus contre un seul processus]{.tag} Le script `train.py` du lab entraîne un MLP de 1 347 073 paramètres (5 388 292 octets en fp32) sur un lot global de 64 exemples seedés, soit 16 par processus, avec SGD. Un processus seul reçoit les 64 exemples. Après 12 étapes, sur la VM de rédaction (4 vCPU, PyTorch 2.14.1 CPU) :

~~~text
DDP(4) vs single process max|dw|=7.5e-09 (rel 6.0e-08); repeat run bitwise equal
ragged batch split: max|dw|=7.2e-03
~~~

Les deux entraînements ne sont **pas** identiques bit à bit, mais l'écart maximal des paramètres est de l'ordre de $10^{-8}$ : un arrondi flottant, pas une divergence (chapitre 7). Deux exécutions identiques de DDP, elles, donnent exactement les mêmes bits. Avec un découpage inégal (20, 20, 20 et 4 exemples) l'écart monte à $7 \cdot 10^{-3}$, près de six ordres de grandeur plus haut : ce n'est plus de l'arrondi, c'est un autre algorithme.
:::

### 2.2. Seaux et recouvrement

DDP n'attend pas la fin de la passe arrière pour communiquer : il regroupe les gradients en **seaux** (*buckets*) et lance un all-reduce asynchrone dès qu'un seau est complet. D'après la documentation, un crochet *autograd* par paramètre signale que son gradient est prêt ; les paramètres sont rangés dans les seaux dans l'ordre **inverse** de `model.parameters()`, car la passe arrière produit d'abord les gradients des dernières couches ; les all-reduce partent toujours dans l'ordre des indices de seaux, pour que tous les rangs lancent les mêmes dans le même ordre.

Le paramètre `bucket_cap_mb` fixe la taille limite d'un seau, 25 MiB par défaut ([documentation de DDP](https://docs.pytorch.org/docs/2.14/generated/torch.nn.parallel.DistributedDataParallel.html)). Le recouvrement en découle : pendant que les couches du début rétropropagent, les seaux des dernières couches voyagent. Le coût total de communication ne change pas ; ce qui change, c'est la part cachée derrière le calcul.

Le code source de la version testée (PyTorch 2.14.1) ajoute deux précisions absentes de la documentation. À la première itération, DDP n'utilise **qu'un seul seau**, car l'ordre réel de disponibilité des gradients est inconnu ; il **reconstruit** ensuite les seaux selon l'ordre observé. Et un seau se ferme dès que sa taille atteint la limite : il peut la dépasser du dernier tenseur ajouté.

::: ex
[Exemple 2.2 — Prédire les seaux de DDP]{.tag} Le module `buckets.py` applique cette règle aux tailles des paramètres du MLP, pris du dernier au premier : le premier seau est limité à 1 MiB quand `bucket_cap_mb` n'est pas fourni, et chaque seau se ferme dès qu'il atteint sa limite. Sa sortie, capturée sur la VM de rédaction :

~~~text
$ python3 buckets.py
2 buckets: 1052676, 4335616 (total 5388292 bytes)
$ python3 buckets.py --cap-mb 1
6 buckets: 1052676, 1050624, 1050624, 1050624, 1050624, 133120 (total 5388292 bytes)
~~~

`verify.sh` lance DDP avec ces deux réglages et exige que les tailles journalisées par DDP après reconstruction (`_get_ddp_logging_data()`, API privée) soient exactement celles-là. Avec le cap par défaut, le premier seau est la couche finale et les 4 335 616 octets restants forment un seau unique, très en dessous de 25 MiB. Avec 1 MiB, chaque couche de 1 050 624 octets referme un seau. Un crochet de communication Python compte les appels : `1 + (étapes - 1) × seaux`, soit 23 all-reduce pour 12 étapes et 2 seaux, et exactement `étapes × 5 388 292` octets.
:::

::: note
[Mesure du coût de communication sur CPU : pas de recouvrement utile]{.tag} Sur la VM de rédaction, le même pas dure de l'ordre de 22 à 28 ms avec synchronisation et de 4 à 7 ms sans (`no_sync`) ; l'all-reduce isolé des mêmes seaux dure de 11 à 13 ms (cinq exécutions). La communication exposée dépasse donc l'all-reduce isolé ; explication probable, non testée : sur 4 vCPU, les quatre rangs, leurs threads `gloo` et le calcul se disputent les mêmes cœurs. Ces temps sont informatifs, `verify.sh` n'en asserte aucun, et ils ne disent rien du recouvrement sur GPU (chapitre 6).
:::

### 2.3. torchrun et le rendez-vous

`torchrun` lance `--nproc-per-node` processus par nœud et leur fournit leur identité par des variables d'environnement. La documentation en liste treize ; les cinq que votre script lit sont `RANK` (rang global), `LOCAL_RANK` (rang dans le nœud, qui choisit le GPU), `WORLD_SIZE` (nombre total de processus), `MASTER_ADDR` et `MASTER_PORT` (où trouver le magasin clé-valeur du rendez-vous). `GROUP_RANK` est le rang du groupe de travail, c'est-à-dire du nœud quand il y a un groupe par nœud.

Le **rendez-vous** (*rendezvous*) est le mécanisme par lequel les processus de tous les nœuds se découvrent et se numérotent. Sur un seul nœud, `--standalone` suffit. Sur plusieurs, on donne un identifiant de job, un moteur (`c10d` est recommandé) et un point d'accès sur l'un des nœuds :

~~~bash
# one node, 4 processes (lab 9.1)
torchrun --standalone --nproc_per_node=4 train.py --out ddp.json

# two nodes of 8 GPU: the same command on both nodes (labs/.../configs/megatron_llama3_70b_64gpu.sh has a full one)
torchrun --nnodes=2 --nproc_per_node=8 --max-restarts=3 \
  --rdzv-id="$JOB_ID" --rdzv-backend=c10d --rdzv-endpoint="$HEAD_NODE:29500" train.py
~~~

Deux phrases de la documentation conditionnent la tolérance aux pannes (module 10). D'abord, « On failures or membership changes ALL surviving workers are killed immediately » : une panne tue tous les processus du groupe, qui sont relancés au plus `--max-restarts` fois, et ils doivent reprendre depuis un checkpoint. Ensuite, le rang n'est pas stable d'un redémarrage à l'autre : ne codez jamais en dur « le rang 3 fait ceci ». Sous Slurm, le lancement par nœud est décrit à l'[exemple 2.1 du module Slurm](../slurm/index.html#ch2).

~~~python
# lines of labs/distributed-training/ddp-gloo/train.py (abridged)
dist.init_process_group("gloo", timeout=timedelta(seconds=60))
rank = dist.get_rank() if distributed else 0
world = dist.get_world_size() if distributed else 1
...
model = DDP(model, **kw)
~~~

`init_process_group` lit `RANK`, `WORLD_SIZE` et `MASTER_*` dans l'environnement ; sur GPU, on ajoute `device_ids=[local_rank]`.

### 2.4. Erreurs classiques

| Erreur | Ce qu'on voit | Cause | Remède |
|---|---|---|---|
| Parts inégales d'un lot | aucun message ; résultat différent d'un entraînement mono-processus (lab : écart environ un million de fois plus grand) | la moyenne de moyennes pèse chaque rang pareillement | `drop_last`, ou pondérer par le nombre d'exemples |
| Paramètre sans gradient | `RuntimeError` à la **deuxième** itération | une branche du modèle n'entre pas dans la perte | utiliser toutes les sorties ; `find_unused_parameters=True` en dernier recours |
| Tous les rangs lisent les mêmes exemples | aucun message ; le lot effectif est $p$ fois trop petit | découpage des données oublié | découper par rang (`shard_bounds` dans le lab) |
| `RANK` au lieu de `LOCAL_RANK` pour choisir le GPU | erreur d'indice de périphérique sur le nœud 1 et suivants | le rang global dépasse le nombre de GPU du nœud | `torch.cuda.set_device(LOCAL_RANK)` |
| Collective sous condition locale | blocage, souvent loin du bug (chapitre 8) | un rang saute un appel que les autres font | décider collectivement (chapitre 7) |
| Deux jobs sur un même nœud | jobs fusionnés ou conflit de port | même point de rendez-vous | `--rdzv-endpoint=localhost:0`, un port libre par job |

::: ex
[Exemple 2.3 — Reproduire l'erreur du paramètre sans gradient]{.tag} `unused_param_demo.py` construit un modèle à deux têtes `a` et `b` dont la perte n'utilise que `b`. Avec `TORCH_DISTRIBUTED_DEBUG=INFO`, la sortie capturée sur la VM de rédaction est :

~~~text
rank 0: RuntimeError at step 1
    Expected to have finished reduction in the prior iteration before starting a new one. This error indicates that your module has parameters that were not used in producing loss. You can enable unused parameter detection by passing the keyword argument `find_unused_parameters=True` to `torch.nn.parallel.DistributedDataParallel`, and by making sure all `forward` function outputs participate in calculating loss.
    Parameters which did not receive grad for rank 0: a.weight
    Parameter indices which did not receive grad for rank 0: 0
~~~

L'erreur n'apparaît qu'à l'étape 1 : l'étape 0 se termine, mais le seau de `a.weight` n'a jamais été complété, et l'itération suivante le détecte. Avec `find_unused_parameters=True`, les trois étapes passent (code de sortie 0). Le coût de ce drapeau est un parcours du graphe autograd à chaque itération.
:::

::: note
[Un niveau de débogage qui plante, sur cette version]{.tag} Avec PyTorch 2.14.1 (CPU), `TORCH_DISTRIBUTED_DEBUG=DETAIL` combiné à DDP sur `gloo` a terminé par un `SIGSEGV` dès la construction de DDP dans nos essais, même pour un modèle d'une seule couche. `INFO` fonctionne avec DDP, et `DETAIL` fonctionne sur des collectives directes (lab 9.3). Observation de l'auteur sur un environnement, pas un défaut documenté : vérifiez sur votre version.
:::

### 2.5. Accumuler des gradients

Pour un lot global plus grand que la mémoire ne le permet, on accumule les gradients sur plusieurs micro-lots avant l'optimiseur. Avec DDP, les micro-lots intermédiaires s'exécutent dans `model.no_sync()`, qui supprime l'all-reduce ; le dernier le déclenche. DeepSpeed impose dans sa configuration l'identité qui en résulte :

$$B_{\text{global}} = b_{\text{micro}} \times a_{\text{accum}} \times p$$

L'accumulation réduit la fréquence de communication, pas le volume par étape, et ne remplace pas le parallélisme quand le problème est la mémoire des états.

::: recap
Points clés — chapitre 2

-   DDP réplique le modèle, moyenne les gradients par all-reduce et garde les copies égales ; l'équivalence avec un seul processus exige des parts égales.
-   Les gradients sont regroupés en seaux (25 MiB par défaut) et réduits dès qu'un seau est complet ; la première itération n'a qu'un seau, puis DDP reconstruit les seaux selon l'ordre réel.
-   `torchrun` fournit `RANK`, `LOCAL_RANK`, `WORLD_SIZE` et le rendez-vous ; une panne tue tout le groupe et le rang n'est pas stable.
-   Les erreurs classiques sont des désaccords entre rangs : parts inégales, paramètre sans gradient, collective conditionnelle.
-   Un lot global est le produit du micro-lot, des étapes d'accumulation et du nombre de rangs.
:::

## 3. Mémoire d'un entraînement : ZeRO, FSDP et activations {#ch3}

La mémoire décide de la première question : une disposition est-elle seulement possible ? Ce chapitre décompose la mémoire d'un GPU en quatre postes, montre comment ZeRO et FSDP en partitionnent trois, et donne la formule du quatrième, les activations. Tous les calculs sont refaits par le planificateur du lab 9.4 ; la mesure vient du lab 9.2.

### 3.1. Les quatre postes

L'entraînement d'un modèle de $\Psi$ paramètres avec Adam en précision mixte stocke, par paramètre : 2 octets de poids BF16, 2 octets de gradient BF16 et 12 octets d'**états d'optimiseur** (une copie FP32 des poids, le moment et la variance, 4 octets chacun). L'article ZeRO le résume par $2\Psi + 2\Psi + K\Psi$ avec $K = 12$ :

$$M_{\text{états}} = (2 + 2 + 12)\,\Psi = 16\,\Psi \ \text{octets}$$

À cela s'ajoutent les **activations** (ce que la passe avant garde pour la passe arrière), des tampons temporaires et la fragmentation de l'allocateur. Les trois premiers postes sont proportionnels à $\Psi$ et ne dépendent pas du lot ; les activations dépendent du lot, de la séquence et de la profondeur.

| Modèle | États à 16 octets par paramètre | Tient sur un GPU de 80 Go ? |
|---|---|---|
| 7 milliards de paramètres | 112 Go | non |
| 13 milliards | 208 Go | non |
| 70 milliards | 1 120 Go | non, ni sur 8 GPU sans partitionnement |

::: note
[Trois façons de compter les octets]{.tag} L'article ZeRO compte 16 octets (poids et gradients BF16, plus 12 octets FP32). *How to Scale Your Model* compte 10 octets par paramètre pour des poids BF16 et des états FP32 (2 + 8), sans copie maître ni gradients. Notre lab, en FP32 pur avec AdamW, compte 4 + 4 + 8 = 16, le même total que ZeRO mais pas la même composition. Demandez toujours ce qu'un chiffre de mémoire inclut.
:::

### 3.2. ZeRO : partitionner les états

L'idée de ZeRO (*Zero Redundancy Optimizer*) est que DDP stocke $p$ fois les mêmes états. On peut les partitionner entre les $p$ rangs de données en trois étapes cumulatives, chacune retirant un poste de la mémoire d'un rang. Avec $N_d$ rangs, l'article ZeRO donne :

$$M_1 = 4\Psi + \frac{12\,\Psi}{N_d} \qquad M_2 = 2\Psi + \frac{14\,\Psi}{N_d} \qquad M_3 = \frac{16\,\Psi}{N_d}$$

L'étape 1 partitionne l'état de l'optimiseur, l'étape 2 y ajoute les gradients, l'étape 3 y ajoute les paramètres. L'étape 3 est ce que PyTorch appelle FSDP (section suivante). Le coût est en communication : les étapes 1 et 2 gardent le volume de DDP, soit $2\Psi$ éléments par pas (un *reduce-scatter* des gradients puis un *all-gather* des paramètres) ; l'étape 3 y ajoute un second all-gather des paramètres, pour $3\Psi$, soit 1,5 fois le volume de DDP ([Rajbhandari et al., 2020](https://arxiv.org/abs/1910.02054), section 7).

<figure class="fig">
<svg viewBox="0 0 560 330" role="img" aria-labelledby="zero-t zero-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="zero-t">Mémoire du modèle par GPU selon l'étape ZeRO</title>
<desc id="zero-d">Barres empilées : étape 0, 120 Go ; étape 1, 31,4 Go ; étape 2, 16,6 Go ; étape 3, 1,9 Go.</desc>
<g fill="currentColor" fill-opacity="0.16" stroke="currentColor"><rect x="150.0" y="50" width="39.0" height="34"/><rect x="150.0" y="106" width="39.0" height="34"/><rect x="150.0" y="162" width="39.0" height="34"/><rect x="150.0" y="218" width="0.8" height="34"/><rect x="20" y="278" width="18" height="18"/></g>
<g fill="currentColor" fill-opacity="0.42" stroke="currentColor"><rect x="189.0" y="50" width="39.0" height="34"/><rect x="189.0" y="106" width="39.0" height="34"/><rect x="189.0" y="162" width="0.8" height="34"/><rect x="150.6" y="218" width="0.8" height="34"/><rect x="170" y="278" width="18" height="18"/></g>
<g fill="currentColor" fill-opacity="0.78" stroke="currentColor"><rect x="228.0" y="50" width="234.0" height="34"/><rect x="228.0" y="106" width="3.7" height="34"/><rect x="189.6" y="162" width="3.7" height="34"/><rect x="151.2" y="218" width="3.7" height="34"/><rect x="320" y="278" width="18" height="18"/></g>
<g font-size="15" fill="currentColor"><text x="138" y="72.0" text-anchor="end" font-weight="700">étape 0</text><text x="138" y="128.0" text-anchor="end" font-weight="700">étape 1</text><text x="138" y="184.0" text-anchor="end" font-weight="700">étape 2</text><text x="138" y="240.0" text-anchor="end" font-weight="700">étape 3</text><text x="470.0" y="72.0">120,0 Go</text><text x="239.7" y="128.0">31,4 Go</text><text x="201.3" y="184.0">16,6 Go</text><text x="162.9" y="240.0">1,9 Go</text><text x="20" y="28">7,5 milliards de paramètres, 64 rangs, précision mixte (2 + 2 + 12 octets)</text><text x="46" y="292">paramètres</text><text x="196" y="292">gradients</text><text x="346" y="292">optimiseur</text></g>
</svg>
<figcaption>Mémoire des états par GPU pour 7,5 milliards de paramètres sur 64 rangs : 120, 31,4, 16,6 puis 1,9 Go. Valeurs de la figure 1 de l'article ZeRO, retrouvées par le planificateur du lab 9.4 (tests `test_zero_figure_1_of_the_paper`).</figcaption>
</figure>

::: ex
[Exemple 3.1 — Un modèle de 7 milliards sur 8 GPU de 80 Go]{.tag} Avec $\Psi = 7 \cdot 10^{9}$ et $N_d = 8$, les formules donnent 112 Go (DDP), 38,5 Go (étape 1, soit $4 \times 7 + 12 \times 7 / 8$), 26,25 Go (étape 2) et 14 Go (étape 3). Les états seuls tiennent dans 80 Go dès l'étape 1, mais il ne reste alors que 41,5 Go pour les activations ; à l'étape 3, 66 Go. Le choix se fait avec **les deux** postes, ce que fait le planificateur du chapitre 5.
:::

### 3.3. FSDP et `fully_shard`

FSDP (*Fully Sharded Data Parallel*) est l'implémentation de PyTorch de l'étape 3. Sa deuxième version, `fully_shard`, représente chaque paramètre comme un `DTensor` (tenseur distribué) découpé sur la **dimension 0** (avec `torch.chunk`) entre les rangs. Avant la passe avant d'un module, un *all-gather* reconstitue ses paramètres complets ; après la passe arrière, un *reduce-scatter* renvoie à chaque rang la part de gradient qui lui revient ([documentation de `fully_shard`](https://docs.pytorch.org/docs/2.14/distributed.fsdp.fully_shard.html)).

Deux règles de la documentation structurent l'usage. D'abord, **le groupe de communication est le module** : chaque appel à `fully_shard` crée un groupe avec les paramètres du module qui n'appartiennent pas déjà à un sous-module traité. Il faut donc appeler `fully_shard` de bas en haut, couche par couche puis sur la racine. Il n'y a pas de `bucket_cap_mb` : n'appliquer `fully_shard` qu'à la racine donne deux grosses communications bloquantes, ce que la documentation déconseille presque toujours.

Ensuite, `reshard_after_forward` règle le compromis mémoire-communication. La valeur `True` libère les paramètres après la passe avant et les re-rassemble pour la passe arrière ; `False` les garde et évite le second all-gather ; `None`, la valeur par défaut, vaut `True` pour les modules non racines et `False` pour la racine.

L'article FSDP résume le coût mémoire ainsi : proportionnel à la taille du modèle partitionné **plus** celle de la plus grande unité reconstituée ([Zhao et al., 2023](https://arxiv.org/abs/2304.11277)). Un maillage à deux dimensions donne le *sharding* hybride (HSDP) : partitionné dans un groupe, répliqué entre les groupes. Les noms de stratégies correspondent à ceux de ZeRO : selon la documentation d'Accelerate, `FULL_SHARD` correspond à ZeRO-3, `SHARD_GRAD_OP` à ZeRO-2 et `NO_SHARD` à DDP.

::: ex
[Exemple 3.2 — Mesurer ce que chaque rang détient]{.tag} Le lab 9.2 construit un modèle de 16 802 826 paramètres (8 blocs `512 → 2048 → 512` et une tête à 10 classes) et mesure, sur 4 rangs `gloo`, les octets de paramètres, de gradients et d'états AdamW **détenus** par chaque rang, en lisant `DTensor.to_local()`. La prédiction n'utilise que les formes des tenseurs. Sortie de `verify.sh` sur la VM de rédaction :

~~~text
OK fsdp-memory: 16802826 parameters; per-rank persistent MiB: DDP 256.4, FSDP [64.1, 64.1, 64.1, 64.09] (measured = predicted, ratio 4.00)
   peak unsharded params MiB: DDP 64.1, FSDP reshard 8.0, FSDP no reshard 64.1
~~~

DDP détient $16 \times 16\,802\,826$ octets, soit 256,4 MiB, par rang. FSDP2 en détient le quart, 64,1 MiB : le dernier rang a un peu moins, parce que la tête de forme (10, 512) est découpée en lignes de 3, 3, 3 et 1. Le pic de paramètres non partitionnés, relevé à l'entrée de chaque bloc de la passe avant, vaut 8,0 MiB (un bloc plus la tête) avec `reshard_after_forward=True`. Il monte à 64,1 MiB quand les blocs ne sont pas re-partitionnés : tout le modèle est reconstitué.

Les égalités mesuré = prédit sont **exactes** : c'est de l'arithmétique entière sur des tailles de tenseurs.
:::

::: ex
[Exemple 3.3 — Le choix de Llama 3]{.tag} L'[article Llama 3](https://arxiv.org/abs/2407.21783) indique que sa dimension de données est un FSDP qui partitionne optimiseur et gradients mais ne re-partitionne pas les paramètres après la passe avant, afin d'éviter un all-gather supplémentaire en passe arrière : `reshard_after_forward=False`. Le prix est de la mémoire. C'est vraisemblablement supportable parce que le pipeline (PP 16) réduit déjà la taille de chaque étape, mais c'est une interprétation de l'auteur, l'article ne le dit pas. FSDP seul et FSDP dans une grille n'ont pas les mêmes bons réglages.
:::

### 3.4. Les activations

Les activations sont le poste qui dépend du lot. Pour une couche de transformeur sans parallélisme, avec des activations 16 bits, [Korthikanti et al.](https://arxiv.org/abs/2205.05198) donnent la mémoire stockée par couche :

$$A_{\text{couche}} = s\,b\,h\left(34 + 5\,\frac{a\,s}{h}\right) \ \text{octets}$$

où $s$ est la longueur de séquence, $b$ le micro-lot, $h$ la taille cachée et $a$ le nombre de têtes. Le terme en $a\,s/h$ vient des scores d'attention, de taille $s^2$ par tête : il croît **quadratiquement** avec la séquence. Le tableau 2 de l'article donne les variantes :

| Configuration | Activations par couche |
|---|---|
| sans parallélisme | $s b h\,(34 + 5as/h)$ |
| parallélisme tensoriel de degré $t$ | $s b h\,(10 + 24/t + 5as/(ht))$ |
| tensoriel + séquence | $s b h\,(34/t + 5as/(ht))$ |
| tensoriel + recalcul sélectif | $s b h\,(10 + 24/t)$ |
| tensoriel + séquence + recalcul sélectif | $s b h \cdot 34/t$ |
| recalcul complet | $s b h \cdot 2$ |

Le **recalcul** (*activation checkpointing*) troque du calcul contre de la mémoire : on ne garde que l'entrée de chaque couche et on refait la passe avant pendant la passe arrière. Chen et al. ont montré qu'on peut ainsi descendre à un coût mémoire en $O(\sqrt{n})$ pour $n$ couches avec une passe avant supplémentaire. Le recalcul **sélectif** ne refait que la partie la plus chère en mémoire et la moins chère en calcul, l'attention.

::: ex
[Exemple 3.4 — Les activations d'un modèle de 7 milliards de paramètres]{.tag} Prenons une séquence de 4 096 tokens, un micro-lot de 1, une taille cachée de 4 096, 32 têtes et 32 couches. Comme $s = h$, le facteur vaut $34 + 5 \times 32 = 194$ ; la base $s\,b\,h$ vaut 16,8 Mo. Résultats du planificateur (`activation_bytes_per_layer`, en Go de $10^{9}$ octets) :

| Variante | Par couche | Pour 32 couches |
|---|---|---|
| aucune optimisation | 3,25 Go | 104,2 Go |
| recalcul sélectif | 0,570 Go | 18,3 Go |
| recalcul complet | 0,034 Go | 1,07 Go |
| TP 8 + séquence + recalcul sélectif | 0,071 Go | 2,28 Go |

Sans optimisation, **les activations dépassent la mémoire du GPU** avant même les états : le terme d'attention pèse 160 sur 194. Le recalcul sélectif retire ce terme ; le recalcul complet n'en garde que le minimum. Selon le tableau 4 de l'article (une couche d'un modèle de 22 milliards sur A100), le recalcul complet coûte 39 % de temps de calcul en plus et le recalcul sélectif 7 % : ce sont **une** mesure d'un modèle et d'un GPU, à remplacer par les vôtres.
:::

Deux précisions. Avec un pipeline 1F1B, la première étape garde les activations de $p$ micro-lots pour ses $L/p$ couches, soit **$L$ couches d'activations quel que soit $p$** : le pipeline ne réduit pas ce poste (Korthikanti et al., équation 5). Et des noyaux d'attention qui ne matérialisent pas les scores jouent le rôle du recalcul sélectif sur le terme quadratique : selon l'[Ultra-Scale Playbook](https://nanotron-ultrascale-playbook.static.hf.space/index.html), FlashAttention recalcule les scores dans la passe arrière au lieu de les stocker. Llama 3 a entraîné sur des séquences de 8 000 tokens sans recalcul d'activations grâce à ses améliorations de pipeline.

::: recap
Points clés — chapitre 3

-   Les états coûtent 16 octets par paramètre en précision mixte (2 + 2 + 12), indépendamment du lot ; vérifiez toujours ce qu'un chiffre de mémoire inclut.
-   ZeRO partitionne l'optimiseur (étape 1), les gradients (étape 2) puis les paramètres (étape 3) ; le volume de communication reste celui de DDP jusqu'à l'étape 2 et monte à 1,5 fois à l'étape 3.
-   `fully_shard` partitionne chaque paramètre sur sa dimension 0 ; le groupe de communication est le module ; `reshard_after_forward` échange mémoire contre all-gather.
-   Les activations croissent avec le lot et, par le terme d'attention, avec le carré de la séquence ; recalcul complet, recalcul sélectif et parallélisme tensoriel avec séquence les réduisent, à des prix différents.
-   Un pipeline 1F1B laisse à la première étape les activations de toutes les couches ; seul le parallélisme tensoriel les divise.
:::

## 4. Tenseur, séquence, pipeline et experts {#ch4}

Les trois autres dimensions répondent à des problèmes que ZeRO ne résout pas : une couche trop grosse ou des activations trop lourdes (tenseur et séquence), un modèle trop profond pour un nœud (pipeline), un modèle à experts. Chacune a une charge de communication et une pénalité propres, que ce chapitre chiffre.

### 4.1. Parallélisme tensoriel

Le parallélisme tensoriel (TP) découpe les **matrices d'une couche** entre plusieurs GPU. Le bloc MLP d'un transformeur calcule $Y = \mathrm{GeLU}(XA)\,B$. Megatron-LM découpe $A$ par colonnes en $[A_1, A_2]$ et $B$ par lignes en $B_1$ et $B_2$. La non-linéarité s'applique colonne par colonne : chaque GPU calcule sa part sans rien échanger, et la sortie est une somme.

$$Y = \sum_{i=1}^{t} \mathrm{GeLU}(X A_i)\,B_i$$

Le seul échange est un **all-reduce** de cette somme. Un transformeur a deux blocs par couche (attention et MLP), donc deux all-reduce en passe avant et deux en passe arrière : quatre par couche et par micro-lot ([Narayanan et al., 2021](https://arxiv.org/abs/2104.04473), section 2.3). Chacun porte un tenseur d'activations de $s \times b \times h$ éléments.

Le lab 9.4 contient une vraie version de ce découpage, `tp_mlp_check.py`, sur deux processus `gloo`. Il écrit les deux opérateurs conjugués de Megatron et vérifie que sortie et gradients égalent ceux du MLP dense : `OK tp_mlp_check: 2-way tensor-parallel MLP equals the dense MLP (max error 2.1e-14, float64); collectives per block: 1 forward + 1 backward`.

::: ex
[Exemple 4.1 — Ce que coûte le parallélisme tensoriel, et pourquoi il reste dans le nœud]{.tag} Prenons une couche de modèle à 70 milliards de paramètres : taille cachée 8 192, séquence de 4 096 tokens, micro-lot de 1, activations BF16, degré 8. Un all-reduce porte $4096 \times 8192 \times 2 = 67{,}1$ Mo. Chaque GPU émet $2 \cdot \frac{7}{8} \cdot 67{,}1 = 117{,}4$ Mo par all-reduce, soit 470 Mo par couche pour les quatre.

À une **hypothèse** de 400 Go/s de débit de bus dans le nœud, les quatre durent 1,17 ms. Le calcul de la couche vaut environ $6 \times 12h^2 \times 4096 = 19{,}8$ TFLOP en passes avant et arrière, avec $12h^2$ paramètres par couche (approximation classique), soit 2,47 TFLOP par GPU après découpage en 8. À 40 % de MFU sur un pic dense de 989 TFLOP/s : 6,25 ms. La communication pèse **19 %** du calcul.

À 25 Go/s (une carte de 200 Gb/s par GPU, hypothèse), les quatre all-reduce dureraient 18,8 ms, soit **trois fois le calcul**. Ces débits sont des hypothèses, à mesurer avec `nccl-tests` ([module 7](../networking/index.html#ch8)) ; c'est leur rapport de 16 qui compte.
:::

::: war
[Le parallélisme tensoriel franchit mal la frontière du nœud]{.tag} Le premier enseignement de l'article Megatron-LM est d'utiliser le TP jusqu'à la taille du nœud, puis le pipeline au-delà. L'[Ultra-Scale Playbook](https://nanotron-ultrascale-playbook.static.hf.space/index.html) l'illustre sur H100 : baisses significatives de débit en passant de TP=8 à TP=16, parce que la communication quitte NVLink pour le réseau ; le TP, avec ou sans séquence, se recouvre mal avec le calcul.
:::

### 4.2. Parallélisme de séquence et de contexte

Dans un bloc de transformeur, le TP ne découpe pas les couches de normalisation ni le *dropout* : chaque GPU du groupe en garde les activations complètes. Le **parallélisme de séquence** (SP) les répartit sur la séquence. Les deux opérateurs deviennent un *all-gather* et un *reduce-scatter*, dont les volumes somment à celui d'un all-reduce : pas un octet de plus sur le réseau, mais des activations divisées par le degré du TP (tableau 2 du chapitre 3).

Le **parallélisme de contexte** (CP) est une autre idée : pour de très longues séquences, on découpe la séquence d'entrée entre GPU, et l'attention doit voir toutes les clés et valeurs. Llama 3 découpe la séquence en deux fois CP morceaux, deux par rang pour équilibrer l'attention causale, et rassemble les clés et valeurs par un *all-gather*. Sa latence reste sur le chemin critique mais elle est faible, car l'attention à groupes de requêtes (GQA) rend clés et valeurs bien plus petites que les requêtes. Megatron Core recommande le CP à partir de 8 000 tokens environ.

### 4.3. Parallélisme de pipeline

Le pipeline coupe les **couches** en $p$ étages et fait circuler les activations de l'un à l'autre. Pour que tous les étages travaillent ensemble, on découpe le lot en $m$ micro-lots qui entrent l'un derrière l'autre. Il reste un temps mort au début et à la fin : la **bulle**. Dans l'ordonnancement GPipe (toutes les passes avant, puis toutes les passes arrière, puis la mise à jour des poids, le *flush*), chaque étage reste inactif pendant $(p-1)(t_f + t_b)$ pour un calcul utile de $m\,(t_f + t_b)$ :

$$\text{bulle} = \frac{(p-1)\,(t_f + t_b)}{m\,(t_f + t_b)} = \frac{p-1}{m}$$

<figure class="fig">
<svg viewBox="0 0 560 298" role="img" aria-labelledby="pp-t pp-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="pp-t">Pipeline à 4 étages et 4 micro-lots : la bulle</title>
<desc id="pp-d">Chaque ligne est un étage ; passes avant et arrière en deux teintes ; les vides sont la bulle, 9 unités pour 12 de calcul utile.</desc>
<g fill="var(--accent)" fill-opacity="0.35" stroke="currentColor"><rect x="74" y="44" width="22" height="36"/><rect x="96" y="44" width="22" height="36"/><rect x="118" y="44" width="22" height="36"/><rect x="140" y="44" width="22" height="36"/><rect x="96" y="88" width="22" height="36"/><rect x="118" y="88" width="22" height="36"/><rect x="140" y="88" width="22" height="36"/><rect x="162" y="88" width="22" height="36"/><rect x="118" y="132" width="22" height="36"/><rect x="140" y="132" width="22" height="36"/><rect x="162" y="132" width="22" height="36"/><rect x="184" y="132" width="22" height="36"/><rect x="140" y="176" width="22" height="36"/><rect x="162" y="176" width="22" height="36"/><rect x="184" y="176" width="22" height="36"/><rect x="206" y="176" width="22" height="36"/><rect x="74" y="226" width="18" height="18"/></g>
<g fill="currentColor" fill-opacity="0.22" stroke="currentColor"><rect x="492" y="44" width="44" height="36"/><rect x="448" y="44" width="44" height="36"/><rect x="404" y="44" width="44" height="36"/><rect x="360" y="44" width="44" height="36"/><rect x="448" y="88" width="44" height="36"/><rect x="404" y="88" width="44" height="36"/><rect x="360" y="88" width="44" height="36"/><rect x="316" y="88" width="44" height="36"/><rect x="404" y="132" width="44" height="36"/><rect x="360" y="132" width="44" height="36"/><rect x="316" y="132" width="44" height="36"/><rect x="272" y="132" width="44" height="36"/><rect x="360" y="176" width="44" height="36"/><rect x="316" y="176" width="44" height="36"/><rect x="272" y="176" width="44" height="36"/><rect x="228" y="176" width="44" height="36"/><rect x="274" y="226" width="18" height="18"/></g>
<g text-anchor="middle" font-size="14" fill="currentColor"><text x="85.0" y="67.0">0</text><text x="107.0" y="67.0">1</text><text x="129.0" y="67.0">2</text><text x="151.0" y="67.0">3</text><text x="107.0" y="111.0">0</text><text x="129.0" y="111.0">1</text><text x="151.0" y="111.0">2</text><text x="173.0" y="111.0">3</text><text x="129.0" y="155.0">0</text><text x="151.0" y="155.0">1</text><text x="173.0" y="155.0">2</text><text x="195.0" y="155.0">3</text><text x="151.0" y="199.0">0</text><text x="173.0" y="199.0">1</text><text x="195.0" y="199.0">2</text><text x="217.0" y="199.0">3</text><text x="514" y="67.0">0</text><text x="470" y="67.0">1</text><text x="426" y="67.0">2</text><text x="382" y="67.0">3</text><text x="470" y="111.0">0</text><text x="426" y="111.0">1</text><text x="382" y="111.0">2</text><text x="338" y="111.0">3</text><text x="426" y="155.0">0</text><text x="382" y="155.0">1</text><text x="338" y="155.0">2</text><text x="294" y="155.0">3</text><text x="382" y="199.0">0</text><text x="338" y="199.0">1</text><text x="294" y="199.0">2</text><text x="250" y="199.0">3</text></g>
<g text-anchor="end" font-size="15" font-weight="700" fill="currentColor"><text x="64" y="67.0">étage 0</text><text x="64" y="111.0">étage 1</text><text x="64" y="155.0">étage 2</text><text x="64" y="199.0">étage 3</text></g>
<g font-size="15" fill="currentColor"><text x="100" y="240">passe avant (1 unité)</text><text x="300" y="240">passe arrière (2 unités)</text><text x="74" y="270">vide = bulle : (p−1)/m = 3/4 ici, avec m = 4 seulement</text></g>
</svg>
<figcaption>Ordonnancement GPipe à 4 étages et 4 micro-lots, passe arrière deux fois plus longue que la passe avant. Chaque étage calcule 12 unités sur 21 : la bulle est de 9 unités, soit 3/4 du calcul utile. Le schéma prend m = 4 pour rester lisible ; avec m = 64 la même formule donne 3/64.</figcaption>
</figure>

Pour une petite bulle, il faut beaucoup plus de micro-lots que d'étages ([Narayanan et al., 2021](https://arxiv.org/abs/2104.04473), section 2.2). L'ordonnancement **1F1B** (une passe avant, une passe arrière) ne réduit pas la bulle mais limite à $p$ les micro-lots en vol, donc la mémoire des activations. L'ordonnancement **entrelacé** donne à chaque GPU $v$ blocs de couches non contigus : bulle divisée par $v$, communication entre étages multipliée par $v$. Llama 3 écrit $(\mathrm{PP}-1)/(V \cdot M)$, avec $V$ étages virtuels par rang.

::: ex
[Exemple 4.2 — Dimensionner un pipeline]{.tag} Un pipeline de 8 étages reçoit 64 micro-lots : bulle de $7/64 = 10{,}9\ \%$. Avec 4 blocs entrelacés, $7/256 = 2{,}7\ \%$. Mais les communications entre étages sont multipliées par 4 et la mémoire d'activations de la première étape par $1 + 7/32 = 1{,}22$ (équation de Korthikanti et al. pour le schéma entrelacé).

Pour moins de 5 % sans entrelacement, il faut au moins $7 / 0{,}05 = 140$ micro-lots par pipeline. Avec 4 répliques de données et des micro-lots d'une séquence : un lot global d'au moins $140 \times 4 = 560$ séquences. **Le pipeline impose un lot global minimal** : si l'optimisation fixe le lot (chapitre 5), c'est la disposition qui doit s'y plier.

Dans le tableau 1 de Megatron-LM, le modèle de 1 008 milliards de paramètres utilise TP 8 et PP 64 sur 3 072 GPU : 6 répliques de données, 512 séquences par pipeline pour un lot de 3 072, 163 TFLOP/s par GPU, soit 52 % du pic.
:::

Le pipeline communique peu : une frontière d'étage ne reçoit qu'un tenseur d'activations par micro-lot et par sens, ce qui lui permet de traverser le réseau entre nœuds. Ses défauts sont le déséquilibre et la mémoire. Llama 3 note que la première étape consomme plus de mémoire (plongements, micro-lots en attente) et que la dernière est le goulot de latence (calcul de la perte) ; ses auteurs ont retiré une couche à chacune.

### 4.4. Parallélisme d'experts

Dans un modèle à mélange d'experts (MoE), chaque couche contient plusieurs sous-réseaux, les experts, et un routeur envoie chaque jeton vers un petit nombre d'entre eux (*top-k*). Le parallélisme d'experts (EP) place les experts sur des GPU différents. Il n'y a pas de matrice à découper : on **déplace les jetons** vers leur expert, puis on rapporte les résultats, deux déplacements qui sont des *all-to-all*.

::: ex
[Exemple 4.3 — Le trafic d'un all-to-all d'experts]{.tag} Prenons 8 192 jetons par GPU, taille cachée 4 096, BF16, top-2 (hypothèse) et 8 rangs d'experts. Chaque jeton part en 2 exemplaires : $8192 \times 2 \times 4096 \times 2 = 134{,}2$ Mo. Un rang garde en moyenne 1/8 de ses jetons ; il émet $\frac{7}{8} \times 134{,}2 = 117{,}4$ Mo par all-to-all.

La passe avant en fait deux (envoi, retour), la passe arrière autant : quatre par couche MoE. Le volume est du même ordre que celui du TP de l'exemple 4.1, avec un motif différent : un all-to-all vers tous les rangs, sensible aux déséquilibres de charge. Selon le Playbook, DeepSeek-V3 limite chaque jeton à au plus 4 nœuds pour garder le trafic dans les nœuds.
:::

Deux conséquences. Megatron Core exige d'activer le parallélisme de séquence quand on combine TP et EP. Et le Playbook note que certaines implémentations traitent l'EP comme un sous-ensemble de la dimension de données, ce qui change la façon de compter les GPU (chapitre 9).

::: recap
Points clés — chapitre 4

-   Le TP découpe les matrices (colonnes puis lignes) : quatre all-reduce d'activations par couche et par micro-lot ; il reste dans le nœud, où le débit est, dans notre exemple chiffré, 16 fois plus grand.
-   Le parallélisme de séquence divise les activations par le degré du TP pour le même volume de communication ; le contexte sert aux très longues séquences.
-   La bulle d'un pipeline vaut $(p-1)/m$, divisée par $v$ avec l'entrelacement ; elle impose un lot global minimal.
-   Le pipeline communique peu mais déséquilibre mémoire et calcul entre étages.
-   Le parallélisme d'experts est un all-to-all de jetons, quatre par couche MoE, sensible à l'équilibre de charge.
:::

## 5. Choisir et dimensionner une disposition {#ch5}

Les chapitres précédents donnent les pièces. Celui-ci donne la méthode pour les assembler : dans quel ordre poser les questions, où placer chaque dimension sur la topologie, et comment un calcul de mémoire et de communication sert de filtre avant les essais réels.

### 5.1. Une procédure en quatre temps

Les sources publiées convergent. L'article Megatron-LM énonce trois enseignements : le TP jusqu'à la taille du nœud puis le pipeline au-delà ; un degré de parallélisme du modèle (tenseur fois pipeline) qui fait tenir paramètres et activations, les données faisant monter en GPU ; un micro-lot réglé selon la mémoire, le débit et le lot global. Le guide de Megatron Core (section « Start Simple ») recommande de commencer simple : données seules, puis tenseur si le modèle ne tient pas, puis pipeline, puis contexte pour les longues séquences.

L'[Ultra-Scale Playbook](https://nanotron-ultrascale-playbook.static.hf.space/index.html) en fait une procédure, que nous complétons d'une quatrième étape :

1.  **Faire tenir un pas en mémoire.** Moins de 10 milliards de paramètres : une seule technique, par exemple ZeRO-3 sur 8 GPU. De 10 à 100 milliards : TP=8 avec pipeline, TP=8 avec ZeRO-3, ou ZeRO-3 seul. Au-delà de 512 GPU, ZeRO-3 pur devient inefficace ; à partir de 1 024, TP=8 avec ZeRO-2 et pipeline.
2.  **Atteindre le lot global voulu** : plus de données, d'accumulation, ou du contexte.
3.  **Optimiser le débit** : TP jusqu'à la taille du nœud, plus de données, pipeline quand la communication de données devient le goulot, essais de micro-lots.
4.  **Mesurer** chaque candidat sur quelques dizaines d'étapes. Les seuils du Playbook viennent de nœuds de 8 H100 : un point de départ, pas une loi.

::: key
[Règle de ce chapitre]{.tag} On ne choisit pas la disposition la plus rapide sur le papier : on élimine celles qui ne tiennent pas, on garde deux ou trois candidates dont le coût estimé est voisin, et on les mesure. Un modèle de calcul qui départage deux candidates à deux points près ne départage rien.
:::

### 5.2. Placer les dimensions sur la topologie

Chaque dimension demande un lien différent. Le TP échange des activations à chaque couche, avec une latence qui compte : il lui faut le lien le plus rapide, NVLink dans le nœud. Le pipeline échange peu, en point à point : il tolère le réseau entre nœuds.

Les données échangent le plus gros volume, mais une fois par étape, et le recouvrent avec la passe arrière : elles occupent la dimension la plus externe. D'où l'ordre [TP, PP, DP] du plus interne au plus externe, auquel Llama 3 ajoute le contexte entre le TP et le PP.

L'[article Llama 3](https://arxiv.org/abs/2407.21783) donne la même justification : la dimension la plus interne exige la plus forte bande passante et la plus faible latence, donc reste dans un serveur ; la plus externe traverse un réseau à plusieurs sauts et doit tolérer la latence. Les données, sous forme de FSDP, y parviennent en préchargeant les poids partitionnés et en réduisant les gradients de façon asynchrone.

::: ex
[Exemple 5.1 — Vérifier le placement avant de lancer]{.tag} Soit 64 GPU en 8 nœuds de 8, avec TP 4, PP 2 et DP 8. Le module `mesh.py` donne le nombre de nœuds traversés par le groupe de chaque dimension (`placement_demo.py` du lab 9.4, dont `verify.sh` compare la sortie). Sortie capturée sur la VM de rédaction :

~~~python
from mesh import Mesh
inner = Mesh(("dp", "pp", "tp"), (8, 2, 4))  # names from outermost to innermost
outer = Mesh(("tp", "pp", "dp"), (4, 2, 8))  # same degrees, tensor parallelism outermost
print(f"tp spans {inner.node_span('tp', 8)} node(s); dp spans {inner.node_span('dp', 8)} nodes")
print(f"same sizes, tp outermost: tp spans {outer.node_span('tp', 8)} nodes")
~~~

~~~text
tp spans 1 node(s); dp spans 8 nodes
same sizes, tp outermost: tp spans 4 nodes
~~~

Avec le TP en position la plus interne, un groupe de tenseurs tient dans un nœud et le groupe de données traverse les 8 nœuds, comme attendu. Avec les mêmes degrés dans l'ordre inverse (TP le plus externe), chaque groupe de tenseurs est réparti sur 4 nœuds : le job démarre, donne le bon résultat, et perd du débit sans qu'aucun message n'apparaisse. Un lanceur ou un ordonnanceur qui place mal les rangs produit exactement ce défaut ; le contrôle coûte une ligne de Python.
:::

Ce contrôle suppose que les rangs consécutifs sont dans le même nœud. C'est ce que `torchrun` fournit en pratique : la documentation parle d'une plage de rangs par nœud.

Sous un ordonnanceur topologique ([module Slurm, chapitre 5](../slurm/index.html#ch5)) ou Kubernetes, vérifiez-le. Une allocation qui disperse les nœuds d'un job sur plusieurs rails coûte autant qu'un mauvais ordre des dimensions ([module 7, chapitre 5](../networking/index.html#ch5)).

### 5.3. Le planificateur et ce qu'il ne voit pas

Les auteurs de Llama 3 disent avoir développé, pour choisir, un estimateur de consommation mémoire et un outil de projection de performance. Le lab 9.4 est une version pédagogique de cette idée : il combine les formules des chapitres 3 et 4.

Pour une disposition, il calcule la mémoire par GPU (états de ZeRO, activations de Korthikanti sur la première étape d'un pipeline), la bulle du pipeline, et les temps de communication du TP, du pipeline et des données, à partir de bandes passantes **que vous fournissez**. Il y ajoute le coût du recalcul d'activations (39 % ou 7 %, deux valeurs d'une même mesure publiée) et une marge de 10 % de la mémoire.

::: ex
[Exemple 5.2 — 70 milliards de paramètres sur 64 GPU]{.tag} Modèle : 70 milliards de paramètres, 80 couches, taille cachée 8 192, 64 têtes, séquence de 4 096 tokens (la forme d'un Llama 3 70B). Cluster : 8 nœuds de 8 GPU de 80 Go, pic dense de 989 TFLOP/s. Lot global de 512 séquences, micro-lot de 1. **Hypothèses** : 400 Go/s de débit de bus dans le nœud, 25 Go/s entre nœuds, 40 % de MFU pour dimensionner le calcul, soit 34,8 s par étape.

Le planificateur évalue 46 dispositions (degrés, étape ZeRO 1 ou 3, recalcul sélectif ou complet). 17 ne tiennent pas, 29 tiennent dans 90 % de 80 Go. Extrait de sa sortie (`scenario.py`), classé par surcoût sans recouvrement. Colonnes : `m` est le nombre de micro-lots par pipeline, `t_*_s` les secondes de communication par étape.

~~~text
tp pp dp zero recompute  m  state_GB  acts_GB  total_GB  bubble  t_tp_s  t_pp_s  t_dp_s  overhead: no-overlap / dp-hidden
 2 16  2    1 selective 256     21.9     45.6     67.5    5.9%    0.86    0.69    0.17     17.8%     17.3%
 4  8  2    1 selective 256     21.9     22.8     44.7    2.7%    2.58    0.34    0.17     18.6%     18.1%
 4  4  4    1 selective 128     30.6     22.8     53.4    2.3%    2.58    0.17    0.53     18.8%     17.2%
 4  1 16    3 selective  32     17.5     22.8     40.3    0.0%    2.58    0.00    3.94     25.7%     14.4%
 8  8  1    1 selective 512     17.5     11.4     28.9    1.4%    6.01    0.34    0.00     26.6%     26.6%
 8  1  8    1 selective  64     48.1     11.4     59.5    0.0%    6.01    0.00    1.23     27.8%     24.3%
 2  1 32    3 selective  16     17.5     45.6     63.1    0.0%    0.86    0.00    8.14     32.9%      9.5%
 1  1 64    3 full        8     17.5      5.4     22.9    0.0%    0.00    0.00   16.54     86.5%     39.0%
~~~
:::

Lisons ce tableau comme un ingénieur et non comme un classement.

-   **Trois dispositions sont dans un mouchoir** : les trois premières lignes sont à moins de deux points, avec TP de 2 à 4 et PP de 4 à 16. Le modèle ne les départage pas : il faut les mesurer.
-   **La mémoire est le vrai filtre.** Le ZeRO-3 pur à 64 rangs (dernière ligne) ne tient qu'avec un recalcul **complet** : en sélectif, il demande 108,8 Go. Même avec toute sa communication de données cachée, il garde 39 % de surcoût, qui est le recalcul. Un TP, même petit, aide parce qu'il divise les activations.
-   **Les bornes comptent.** « Sans recouvrement » est une borne haute, « données cachées » une borne basse. La ligne TP 2, ZeRO-3, DP 32 passe de 32,9 % à 9,5 % si les 8 secondes de communication de données se cachent derrière 35 secondes de calcul : plausible, pas garanti.
-   **Le TP de 8 coûte plus que le modèle ne le dit** : 26 à 28 %, auxquels s'ajoute l'efficacité perdue sur des matrices huit fois plus petites par GPU, que le modèle ignore.

Ce que le modèle **ne voit pas** : l'efficacité des noyaux sur de petites matrices, les activations transitoires de la couche en cours de recalcul, le déséquilibre entre étapes de pipeline, les termes de latence, la fragmentation, le recouvrement réel, l'écart entre débit nominal et mesuré. D'où la quatrième étape de la procédure : mesurer.

### 5.4. Le lot global comme contrainte

La disposition ne se choisit pas à lot libre : l'optimisation fixe le lot global, que la disposition doit produire.

$$B_{\text{global}} = b_{\text{micro}} \times a_{\text{accum}} \times d$$

Plus on ajoute de répliques de données à lot fixe, plus le lot par réplique diminue, jusqu'à ce que le calcul par GPU ne cache plus la communication (*How to Scale Your Model* en fait un seuil de lot par puce, calculé pour des TPU). Le pipeline impose de son côté un nombre minimal de micro-lots (exemple 4.2).

Pour plus de GPU à lot constant, il faut d'autres dimensions : tenseur, contexte, pipeline entrelacé. Au-delà d'un certain lot, l'entraînement a des rendements décroissants parce que les gradients deviennent presque sans bruit (même source) : le lot utile est une propriété de l'optimisation, pas de l'infrastructure. Llama 3 en donne une illustration (chapitre 1) : passer de 8 192 à 16 384 GPU à 16 M de tokens par lot a coûté deux points de MFU.

### 5.5. Une table de décision

| Contrainte observée | Dimension à ajouter | Pourquoi | Ce qu'elle coûte |
|---|---|---|---|
| Le modèle tient avec ses états sur un GPU, on veut aller plus vite | données (DDP) | aucune contrainte de mémoire | all-reduce des gradients, caché par le recouvrement |
| Les états ne tiennent pas, les couches tiennent | ZeRO-2 ou FSDP | les états sont divisés par $d$ | jusqu'à 1,5 fois le volume de DDP en ZeRO-3 |
| Les activations ne tiennent pas | recalcul sélectif, puis TP avec séquence, puis recalcul complet | divise ou supprime le poste | 7 %, communication du TP, ou 39 % de calcul en plus |
| Une couche ne tient pas, ou les matrices par GPU sont trop grosses | tenseur, dans le nœud | découpe les matrices | quatre all-reduce par couche : NVLink exigé |
| Le modèle dépasse un nœud | pipeline | peu de communication entre étages | bulle ; lot minimal ; déséquilibre |
| Séquences de 8 000 tokens ou plus | contexte | divise les activations de l'attention | all-gather des clés et valeurs |
| Modèle à experts | experts | place les experts sans découper les matrices | all-to-all de jetons ; déséquilibre de charge |

::: recap
Points clés — chapitre 5

-   La procédure est : faire tenir en mémoire, atteindre le lot, optimiser le débit, mesurer. Les seuils du Playbook partent de nœuds de 8 H100 ; ils ne sont pas universels.
-   TP au plus interne, pipeline au milieu, données au plus externe : un ordre inversé ne produit aucune erreur et coûte du débit.
-   Le planificateur filtre sur la mémoire et borne le surcoût de communication ; deux dispositions dans un mouchoir se mesurent.
-   À 70 milliards de paramètres et 4 096 tokens, ZeRO-3 pur ne tient qu'avec un recalcul complet à 39 % de surcoût ; un TP même petit change l'équilibre.
-   Le lot global est une contrainte de l'optimisation que la disposition doit produire ; le pipeline impose un lot minimal.
:::

## 6. Le MFU en pratique : mesurer, expliquer l'écart, agir {#ch6}

Le module 2 a défini le MFU. Ce chapitre l'utilise comme un outil de diagnostic : comment le mesurer sans se tromper, comment décomposer l'écart entre le MFU obtenu et celui qu'on attendait, et quels leviers ont du sens selon la cause. L'objectif est de pouvoir répondre à « pourquoi 33 % et pas 43 % ? » avec une liste de secondes, pas avec une impression.

### 6.1. Mesurer correctement

Rappel de la définition (module 2, chapitre 7), avec le nombre de FLOP par token de l'annexe B de PaLM :

$$\text{MFU} = \frac{\text{tokens/s} \times F_{\text{token}}}{N_{\text{GPU}} \times P_{\text{pic}}} \qquad F_{\text{token}} \approx 6\Psi + 12\,L\,H\,Q\,T$$

où $P_{\text{pic}}$ est le pic **dense** de la précision utilisée. Les sources d'erreur sont dans la mesure du temps et dans le dénominateur.

-   **Écartez les premières étapes** (un seul seau à la première itération de DDP, allocateur à chaud) : médiane d'une trentaine d'étapes après échauffement, comme dans le lab 9.1.
-   **Synchronisez avant de lire l'horloge.** Sur GPU, les noyaux sont asynchrones : sans synchronisation, vous chronométrez leur envoi.
-   **Comptez des tokens utiles** (pas le remplissage) et pas la recomputation (module 2, exercice 10).
-   **Prenez le pic dense** de la précision utilisée, jamais le chiffre « avec sparsité ».
-   **Notez la configuration** : degrés, lot, versions, topologie.

### 6.2. Décomposer l'écart

Une étape se décompose en temps qui s'additionnent :

$$T_{\text{étape}} = T_{\text{noyaux}} + T_{\text{comm exposée}} + T_{\text{bulle}} + T_{\text{recalcul}} + T_{\text{données}} + T_{\text{optimiseur}} + T_{\text{autres}}$$

Seul $T_{\text{noyaux}}$ est du calcul utile. Si les noyaux tournent à un MFU de $\mu$ et que le reste ajoute une fraction $\omega$ de ce temps, le MFU de l'étape vaut $\mu / (1 + \omega)$. C'est l'usage que fait ce chapitre des colonnes de surcoût du planificateur.

::: ex
[Exemple 6.1 — De 40 % de noyaux à un MFU d'étape]{.tag} Reprenons les dispositions de l'exemple 5.2 et supposons que les noyaux tournent à 40 % du pic. Avec les surcoûts sans recouvrement du planificateur, le MFU de l'étape vaut $0{,}40 / (1 + \omega)$ :

| Disposition (TP, PP, DP, ZeRO) | Surcoût $\omega$ | MFU d'étape estimé |
|---|---|---|
| 2, 16, 2, ZeRO-1 | 17,8 % | 34,0 % |
| 4, 4, 4, ZeRO-1 | 18,8 % | 33,7 % |
| 2, 1, 32, ZeRO-3 (communication non cachée) | 32,9 % | 30,1 % |
| 1, 1, 64, ZeRO-3, recalcul complet | 86,5 % | 21,4 % |

Ces valeurs sont des **sorties de modèle**, à partir d'hypothèses de bande passante. Elles donnent un ordre de grandeur de 30 à 34 % pour les bonnes dispositions, en dessous de l'intervalle de 38 à 43 % publié pour Llama 3 405B sur des GPU et un réseau réglés avec soin. L'écart avec le publié est une liste de choses à vérifier (recouvrement réel, noyaux fusionnés, équilibre du pipeline), pas une faute.
:::

Un exemple publié montre à quel point un seul choix pèse. [Korthikanti et al.](https://arxiv.org/abs/2205.05198) entraînent un modèle de 530 milliards de paramètres sur 2 240 GPU A100 : avec le recalcul complet des activations ils atteignent 42,1 % de MFU, avec le recalcul sélectif et le parallélisme de séquence 54,2 %, soit un entraînement 29 % plus rapide. Douze points de MFU viennent d'un réglage de mémoire.

::: ex
[Exemple 6.2 — Quand la communication de données n'est plus cachée]{.tag} Un modèle de 7 milliards de paramètres en DDP pur sur 64 GPU échange 14 Go de gradients BF16. Avec l'anneau et 25 Go/s par GPU (hypothèse), cela prend 1,10 s ($2 \times \frac{63}{64} \times 14 / 25$). Ce modèle ne tient pas en DDP pur (112 Go d'états) ; l'exemple isole la communication, comme l'exercice 11 du module 2.

La passe arrière dure environ les deux tiers du calcul. Avec 32 768 tokens par GPU, le calcul vaut :

$$\frac{6 \times 7 \cdot 10^{9} \times 32768}{989 \cdot 10^{12} \times 0{,}4} = 3{,}48\ \text{s}$$

La passe arrière dure donc 2,32 s et la communication (1,10 s) se cache entièrement.

Gardons le même lot global avec 4 fois plus de GPU : il ne reste que 8 192 tokens par GPU. Le calcul tombe à 0,87 s, la passe arrière à 0,58 s, et la communication reste à 1,10 s. Au moins **0,52 s** restent exposées, soit 60 % de la durée du calcul. À lot global fixe, ajouter des GPU divise le calcul, pas la communication.
:::

### 6.3. Les leviers

| Levier | Ce qu'il réduit | Limite ou risque |
|---|---|---|
| Plus gros micro-lot par GPU | communication exposée (amortie), bulle, intensité arithmétique des noyaux | mémoire d'activations ; lot global fixé par l'optimisation |
| Recouvrement | communication exposée | DDP : seaux et passe arrière ; FSDP2 : préchargement des all-gather (`set_modules_to_forward_prefetch`) ; le TP se recouvre mal |
| Recalcul sélectif plutôt que complet | calcul refait (7 % contre 39 % dans la mesure de Korthikanti et al.) | dépend de l'implémentation de l'attention |
| Noyaux fusionnés, `torch.compile` | temps des noyaux liés à la mémoire (module 2, roofline) | temps de compilation, ruptures de graphe |
| Précision plus basse | temps des noyaux | FP8 était qualifié d'expérimental début 2025 par le Playbook ; stabilité (chapitre 7) |
| Chasser les retardataires | tout : un GPU lent ralentit tous les autres | détection : chapitre 8 |
| Pipeline de données | attente de lots | stockage et prétraitement (module 8) |

Un seul GPU lent peut ralentir des milliers de GPU, ce qui se voit comme des communications lentes mais fonctionnelles : c'est l'un des constats de l'équipe Llama 3, qui a développé des outils pour repérer les communications suspectes parmi les groupes de processus.

### 6.4. Du MFU au rendement utile

Un MFU ne dit rien du temps où le job ne tourne pas. Sur 54 jours de pré-entraînement de [Llama 3 405B](https://arxiv.org/abs/2407.21783), l'équipe rapporte plus de 90 % de temps d'entraînement effectif malgré 466 interruptions. Un MFU de 40 % avec 90 % de temps effectif donne un usage utile de l'ordre de 36 % du pic ($0{,}9 \times 0{,}40$). Interruptions, checkpoints et reprises sont l'objet du [module 10](../fault-tolerance/index.html).

::: recap
Points clés — chapitre 6

-   Mesurez la médiane après échauffement, avec synchronisation, en tokens utiles, avec le pic dense de la bonne précision, et notez la configuration.
-   L'étape se décompose en secondes ; le MFU d'étape vaut le MFU des noyaux divisé par un plus le surcoût.
-   Un seul réglage mémoire (recalcul complet contre sélectif) a valu douze points de MFU dans une mesure publiée.
-   À lot global fixe, ajouter des GPU divise le calcul par GPU mais pas la communication de données : elle finit par être exposée.
-   Les leviers se choisissent selon la ligne de la décomposition qui pèse le plus ; le temps hors étape (pannes) se traite à part.
:::

## 7. Numérique et déterminisme {#ch7}

Un entraînement distribué ne donne pas les mêmes bits qu'un entraînement sur un seul processus, et ce n'est pas un bug. Mais un entraînement qui diverge, lui, est un problème, et les deux se ressemblent dans un journal. Ce chapitre donne les ordres de grandeur de l'un, les signatures de l'autre, et une procédure pour les séparer.

### 7.1. Les formats et ce qu'ils perdent

Un nombre flottant a un exposant (qui fixe l'étendue) et une mantisse (qui fixe la précision). Le **BF16** garde l'étendue du FP32 avec sept bits de mantisse ; le **FP16** a trois bits de mantisse de plus, mais une étendue bien plus petite. Sortie de `numerics_demo.py` (PyTorch 2.14.1, valeurs lues dans `torch.finfo`) :

~~~text
dtype      bits  eps         max         smallest normal
float32      32  1.192e-07  3.403e+38  1.175e-38
float16      16  9.766e-04  6.550e+04  6.104e-05
bfloat16     16  7.812e-03  3.390e+38  1.175e-38
~~~

La colonne `eps` est l'écart entre 1 et le nombre suivant : en BF16, ajouter moins d'environ 0,4 % à une valeur ne la change pas. La colonne `max` explique l'histoire du FP16 : au-delà de 65 504, c'est un dépassement. Le BF16 ne dépasse pas, mais il arrondit grossièrement.

::: ex
[Exemple 7.1 — Un accumulateur en BF16 cesse de croître]{.tag} Ajoutons $10^{-3}$ dix mille fois à un accumulateur. La somme exacte vaut 10. Sortie du même script :

~~~text
accumulating 1e-3 ten thousand times: expected 10.0, float32 10.000, bfloat16 0.500
~~~

Le résultat en BF16 est **0,5**. Quand l'accumulateur atteint 0,5, l'espacement des nombres représentables est d'environ 0,004 ; sa moitié (0,002) dépasse l'incrément, et chaque addition est arrondie à zéro. C'est la raison pour laquelle on accumule en FP32 : l'article Llama 3 précise que l'équipe utilise une accumulation des gradients en FP32 entre micro-lots, et réduit les gradients en FP32 entre les rangs de données de FSDP ([Dubey et al., 2024](https://arxiv.org/abs/2407.21783), section 3.3.2, paragraphe « Numerical stability »).
:::

### 7.2. Pourquoi un run distribué n'est pas bit-identique

L'addition flottante n'est pas associative : $(a + b) + c$ et $a + (b + c)$ peuvent différer d'un bit. Or l'ordre des additions change dès qu'on change le nombre de processus, le découpage en seaux ou l'algorithme de la collective. Le même script mesure l'effet.

::: ex
[Exemple 7.2 — Ordre des additions, et ce qu'il fait à un entraînement]{.tag} Sortie de `numerics_demo.py` (graines fixes) :

~~~text
sum of 1000000 float32 numbers in 20 orders: 6 distinct results, relative spread 4.69e-07, largest error vs float64 4.10e-04
elements that differ between ((a+b)+c)+d and (a+b)+(c+d): float32 29.8 %, bfloat16 29.7 %
~~~

Un million de nombres sommés dans 20 ordres donnent 6 résultats différents, avec un écart relatif de $5 \cdot 10^{-7}$. Quatre vecteurs de rangs sommés de gauche à droite ou deux à deux diffèrent sur près de 30 % de leurs éléments. Dans le lab 9.1, après 30 étapes de SGD, les paramètres de DDP à 4 processus et d'un processus seul diffèrent d'au plus $7{,}5 \cdot 10^{-9}$ ; avec AdamW, de $1{,}4 \cdot 10^{-6}$ (relatif : $7 \cdot 10^{-6}$). Adam divise par une racine de variance : les gradients minuscules, noyés dans l'arrondi, sont amplifiés.

Autre observation du lab, sur 12 étapes : le cap par défaut (2 seaux) et `--bucket-cap-mb 1` (6 seaux) donnent des paramètres qui diffèrent de $7{,}5 \cdot 10^{-9}$, alors que `--bucket-cap-mb 1` et `--bucket-cap-mb 0.25`, qui donnent les mêmes 6 seaux, sont identiques bit à bit. Les commandes sont dans le README du lab.
:::

Ce résultat fixe ce qu'on peut exiger. Deux exécutions avec la même configuration, le même matériel et les mêmes versions peuvent être **bit-identiques** : le lab le vérifie sur `gloo`. Une exécution avec un autre nombre de GPU, une autre taille de seau ou une autre version ne peut qu'être **statistiquement équivalente**. L'équivalence se juge sur la trajectoire de perte et des normes, avec une tolérance, jamais sur l'égalité.

### 7.3. Normes de gradient, pics de perte et NaN

La **norme globale du gradient** est le premier instrument de santé d'un entraînement : elle monte avant la plupart des pics de perte. Avec des gradients répartis entre rangs (FSDP), il faut la calculer sur l'**ensemble** des fragments. Le lab 9.2 compare DDP et FSDP2 sur les mêmes données.

::: ex
[Exemple 7.3 — La norme du fragment local n'est pas la norme globale]{.tag} Sortie de `verify.sh` du lab 9.2, étape 0 d'un entraînement à 4 rangs :

~~~text
FSDP vs DDP after 3 steps: max|dw|=2.2e-08; global grad norm step 0: DDP 5.8588, FSDP 5.8589, local shard of rank 0 2.9620
~~~

La norme globale vaut 5,8589 avec FSDP2 et 5,8588 avec DDP : l'écart relatif est de l'ordre de $10^{-5}$, du même ordre que l'arrondi de sommes de 17 millions de carrés. La norme du seul fragment du rang 0 vaut 2,96, environ la moitié. Écrêter à 0,5 avec cette norme locale appliquerait un facteur de 0,17 au lieu de 0,085 : un écrêtage deux fois trop faible. `clip_grad_norm_` appliqué à des `DTensor` calcule la norme globale. Le lab vérifie aussi que la racine de la somme des carrés des normes locales retrouve la norme globale.
:::

Les causes habituelles d'un NaN sont connues : dépassement en FP16, division par une quantité nulle dans une normalisation, donnée corrompue, gradient qui explose, et, à grande échelle, erreur matérielle silencieuse (l'article Llama 3 range la corruption silencieuse de données parmi les causes matérielles suspectées). Une règle de conception en découle : **la décision de sauter un pas doit être collective**. Un rang qui écarte son lot sur un NaN local, sans que les autres le sachent, saute une collective ; c'est exactement le bug `skip` du lab 9.3.

::: war
[Les pics de perte de PaLM 540B]{.tag} Les auteurs de PaLM rapportent environ 20 pics de perte pendant l'entraînement du plus grand modèle, malgré l'écrêtage des gradients, à des intervalles très irréguliers, et aucun sur les modèles plus petits. Ils n'ont pas trouvé de stratégie de fond. Leur remède : repartir d'un checkpoint situé environ 100 étapes avant le pic et sauter 200 à 500 lots de données. Ils ne pensent pas que les données soient en cause : reprises depuis un checkpoint plus ancien, les mêmes lots n'ont pas produit de pic. Source : [Chowdhery et al., 2022](https://arxiv.org/abs/2204.02311), section sur la stabilité de l'entraînement.
:::

### 7.4. La reproductibilité et ses limites

La documentation de PyTorch est explicite : des résultats complètement reproductibles ne sont pas garantis entre versions, entre commits ni entre plateformes. `torch.manual_seed` aide à reproduire d'une exécution à l'autre sur la même plateforme ; `torch.use_deterministic_algorithms(True)` force les algorithmes déterministes quand ils existent, ou lève une erreur, au prix de la vitesse.

PaLM a obtenu une reproductibilité bit à bit **depuis n'importe quel checkpoint** avec un framework déterministe (JAX, XLA, T5X) et un pipeline de données déterministe, où le contenu d'un lot ne dépend que du numéro d'étape. Avec PyTorch, les leviers sont les mêmes : algorithmes déterministes, graine par rang et par étape, ordre des données fonction de l'étape.

| On change… | Bit-identique ? | Ce qu'on vérifie à la place |
|---|---|---|
| rien (même configuration, matériel, versions) | oui, possible | égalité des paramètres (lab 9.1) |
| on redémarre depuis un checkpoint, même configuration | oui, si l'état du générateur et la position dans les données sont sauvegardés | égalité avec le run sans panne (module 10, [projet 3](../../projects/resilient-trainer/index.html)) |
| le nombre de GPU ou le découpage en seaux | non | écart de paramètres de l'ordre de l'arrondi ; trajectoires de perte superposées |
| la version de PyTorch, de CUDA ou le type de GPU | non | courbes de perte et normes dans la dispersion entre graines |

### 7.5. Bug de distribution ou instabilité numérique ?

Quand une courbe diverge, la première question est de savoir si le problème vient de la distribution ou de l'optimisation. L'équipe Llama 3 décrit la méthode de base : en comparant la perte entre différentes dispositions de parallélisme, elle a corrigé plusieurs problèmes numériques qui nuisaient à la stabilité. La procédure suivante la systématise en quelques essais.

| Essai | Résultat normal | Résultat anormal |
|---|---|---|
| Un processus, même lot global, mêmes graines : la trajectoire suit-elle le job distribué à l'arrondi près ? | pas la distribution | **bug de distribution** : parts inégales, graine de données, perte non normalisée, *buffers* non synchronisés |
| À l'étape 0 : perte, norme globale et somme de contrôle des paramètres identiques sur tous les rangs et au mono-processus ? | mise en route saine | désaccord d'initialisation ou de données |
| Le pic réapparaît-il sur un processus seul, mêmes lots ? | **instabilité numérique ou d'optimisation** | lié à la distribution, au matériel ou à un rang |
| Accumulation et réduction en FP32 : le résultat change-t-il ? | sommes hors de cause | précision des sommes trop basse |
| Redémarrer avant le pic en sautant des lots le supprime-t-il ? | combinaison lot-état fragile (comme PaLM) | cause persistante : taux d'apprentissage, données |

::: recap
Points clés — chapitre 7

-   Le BF16 a l'étendue du FP32 mais peu de précision ; les sommes longues se font en FP32 (Llama 3 accumule et réduit les gradients en FP32).
-   L'addition flottante n'est pas associative : un autre nombre de GPU ou de seaux change les derniers bits ; un entraînement correct s'en écarte de l'ordre de l'arrondi, pas plus.
-   La norme du gradient se lit sur l'ensemble des fragments ; celle d'un fragment local ne vaut presque rien.
-   La décision de sauter un pas doit être collective, sinon c'est un blocage en attente.
-   Exigez la reproductibilité bit à bit seulement à configuration égale ; sinon, comparez des trajectoires avec une tolérance.
:::

## 8. Déboguer le distribué : hangs, désaccords et divergences {#ch8}

Un job distribué tombe en panne de trois façons : il plante avec un message, il ralentit sans rien dire, ou il se bloque. Les deux premiers se lisent dans les journaux. Le troisième, le *hang*, est le plus coûteux : les GPU sont réservés, la facture court, et il n'y a rien à lire. Ce chapitre donne une procédure d'enquête que le lab 9.3 reproduit sur CPU.

::: key
[Règle de ce chapitre]{.tag} Un blocage est un désaccord entre rangs. La question n'est pas « pourquoi ça bloque ? » mais « quel rang n'est pas là où les autres l'attendent, et depuis quand ? ». Tant que vous n'avez pas l'état de **chaque** rang, vous ne savez rien. Ne tuez donc jamais le job avant d'avoir collecté de quoi répondre.
:::

### 8.1. Cinq familles de symptômes

| Symptôme | Famille probable | Premier outil |
|---|---|---|
| Tous les rangs sont dans la même collective, un rang est absent | un rang est bloqué **hors** des collectives (chargeur de données, E/S, plantage) | pile Python du rang absent |
| Les rangs sont dans des collectives différentes | **désaccord** de flot de contrôle : collective conditionnelle, boucle de longueur différente | vérification de cohérence (`DETAIL`), journal des collectives |
| Erreur de forme ou de type dans une collective | désaccord de tenseurs entre rangs | `DETAIL` (message explicite) |
| Le job avance mais lentement, sans erreur | retardataire (un GPU, un lien, un rang) | temps par rang, comparaison de rangs |
| Pas d'erreur, mais la perte diffère d'un run mono-processus | bug de distribution ou numérique | test d'équivalence (chapitre 7) |

### 8.2. Une procédure en cinq temps

1.  **Figer la preuve.** Ne redémarrez pas : les délais maximaux détruisent l'état (10 minutes par défaut pour NCCL, 30 pour les autres backends, d'après la documentation de `torch.distributed`). Collectez avant.
2.  **Lire l'état de chaque rang** : dernière collective terminée et collective en cours. C'est le rôle d'un journal des collectives.
3.  **Trouver la première divergence** : le premier numéro de séquence où les rangs ne font pas la même chose est plus informatif que le point où tout s'arrête.
4.  **Lire la pile du rang fautif** : est-il dans la collective suivante, ou hors de toute collective ?
5.  **Corriger, puis écrire le test qui reproduit le bug.** Le lab 9.3 est ce test pour deux bugs.

### 8.3. Les outils

-   **Le délai du groupe** : `init_process_group(timeout=...)`. Réduisez-le dans les jobs de test.
-   **`TORCH_DISTRIBUTED_DEBUG=DETAIL`** enveloppe chaque groupe d'un contrôle de cohérence : un `monitored_barrier` qui signale les rangs en retard, puis la vérification que opération et formes concordent. Il ralentit l'exécution : réservez-le au débogage.
-   **`monitored_barrier`** : barrière à délai, réservée à `gloo`, où le rang 0 nomme les rangs qui n'arrivent pas à temps.
-   **Le *flight recorder* de PyTorch, pour NCCL** : tampon circulaire des métadonnées de chaque collective, vidé sur disque au délai. On l'active avec `TORCH_NCCL_TRACE_BUFFER_SIZE` (entier positif) et `TORCH_NCCL_DUMP_ON_TIMEOUT=true`, puis `torchfrtrace <répertoire>` l'analyse ([tutoriel](https://docs.pytorch.org/tutorials/unstable/flight_recorder_tutorial.html)). Documenté ; **non exécuté ici**, faute de GPU.
-   **`faulthandler`** (bibliothèque standard) : `faulthandler.register(signal.SIGUSR1)` écrit la pile de tous les fils sur signal, même si le fil principal est bloqué dans du code C ; `dump_traceback_later` le fait après un délai.
-   **`NCCL_DEBUG=INFO`** : journal d'initialisation de NCCL, traité au [module 7](../networking/index.html#ch7).

### 8.4. Deux bugs, cinq outils

Le programme `train_hang.py` du lab 9.3 entraîne quatre rangs `gloo` avec une collective par étape. Le rang 2 y a un bug à l'étape 4, de deux sortes.

::: ex
[Exemple 8.1 — Le rang 2 saute une collective (`--bug skip`)]{.tag} Sans aucun outil, le journal du rang 0 donne l'impression d'une boucle saine :

~~~text
rank 0 step 7 done, reduced value 10
rank 0 step 8 done, reduced value 10
rank 0 FAILED RuntimeError: [.../gloo/transport/tcp/unbound_buffer.cc:78] Timed out waiting 5000ms for recv operation to complete
~~~

Les étapes 4 à 8 « réussissent » alors que les gradients sont décalés d'un rang : les collectives s'apparient par ordre. Le blocage n'arrive qu'à l'étape 9, quand le rang 2, à court de collectives, entre dans la barrière finale. Les quatre rangs expirent après le délai.

Avec `TORCH_DISTRIBUTED_DEBUG=DETAIL`, l'erreur est immédiate et nomme le désaccord (texte tel qu'imprimé par PyTorch 2.14.1) : `Rank 2 is running collective: CollectiveFingerPrint(SequenceNumber=9OpType=BARRIER), but Rank 0 is running collective: CollectiveFingerPrint(SequenceNumber=9, OpType=ALLREDUCE, TensorShape=[1000], ...`. C'est le **symptôme**, à la collective 9, pas la cause.

Le journal des collectives donne la cause. `analyze_journal.py` lit les fichiers de chaque rang :

~~~text
rank  last_completed  in_flight
   0               8  seq 9 all_reduce 'step=9' at train_hang.py:51
   1               8  seq 9 all_reduce 'step=9' at train_hang.py:51
   2               8  seq 9 barrier 'final' at train_hang.py:80
   3               8  seq 9 all_reduce 'step=9' at train_hang.py:51

findings:
  - first divergence at seq 4: majority did all_reduce shape=[1000] tag='step=4'; rank(s) [2] did all_reduce tag='step=5' at train_hang.py:51 -> they skipped the collective of the majority's tag
~~~

À la séquence 4, trois rangs exécutent la collective de l'étape 4 et le rang 2 celle de l'étape 5 : **le rang 2 a sauté l'étape 4**. Le correctif est de rendre collective toute décision de sauter (chapitre 7) ; `--bug none` est le programme corrigé.
:::

::: ex
[Exemple 8.2 — Le rang 2 est bloqué hors des collectives (`--bug stuck`)]{.tag} Ici le rang 2 reste dans `time.sleep` pendant le chargement de son lot (un chargeur de données qui ne revient pas). Le journal est différent :

~~~text
rank  last_completed  in_flight
   0               3  seq 4 all_reduce 'step=4' at train_hang.py:51
   1               3  seq 4 all_reduce 'step=4' at train_hang.py:51
   2               3  -
   3               3  seq 4 all_reduce 'step=4' at train_hang.py:51

findings:
  - ranks [0, 1, 3] wait in seq 4 (all_reduce, step=4); rank(s) [2] completed only up to seq 3 and have nothing in flight -> blocked outside the collectives: dump their Python stack
~~~

Rien n'est en cours sur le rang 2 : il n'est pas dans une collective, la pile Python dira où il est. Celle de `faulthandler`, prise après 3 s, place son fil principal à `train_hang.py`, ligne 65 : la ligne de `time.sleep`. Les piles des rangs 0, 1 et 3 contiennent `all_reduce`, pas celle du rang 2.

Deux autres outils nomment aussi le coupable. `DETAIL` donne `Ranks 2 failed to pass monitoredBarrier in 5000 ms`, car son enveloppe pose un `monitored_barrier` avant chaque collective. Un `monitored_barrier` placé par vous **avant** la collective, après le chargement du lot, donne `Rank 2 failed to pass monitoredBarrier in 3000 ms` au bout de 3 s, avant le délai de 5 s du groupe.
:::

| Outil | `skip` (désaccord) | `stuck` (rang absent) |
|---|---|---|
| Délai seul | tous expirent, après un déroulement apparemment sain | tous expirent |
| `DETAIL` | symptôme immédiat : `BARRIER` contre `ALLREDUCE` à la séquence 9 | nomme le rang 2 |
| `monitored_barrier` avant la collective | pas de coupable (`Connection closed by peer` sur le rang 0) | nomme le rang 2 |
| Journal des collectives | **cause** : le rang 2 saute l'étape 4 | rang 2 sans collective en cours |
| Pile Python (`faulthandler`) | non collectée | **ligne** où le rang 2 est bloqué |

Aucun outil ne suffit seul : la leçon est la complémentarité, et l'ordre de la procédure.

### 8.5. Un entraînement qui diverge d'un run mono-processus

Sans blocage mais avec une perte qui ne suit pas celle d'un entraînement mono-processus, la procédure est celle du §7.5. Le lab 9.1 en donne l'exemple le plus petit : `train.py` en mono-processus et en DDP, mêmes graines, même lot global, puis `compare.py`. Un écart de l'ordre de $10^{-8}$ est un arrondi ; un écart de $10^{-3}$ (lot découpé inégalement) est un bug.

Les causes à écarter, dans l'ordre : parts inégales ; graine de données identique ou différente sur tous les rangs ; perte non normalisée par le nombre d'exemples réels ; *buffers* (statistiques de normalisation) non synchronisés ; graine d'initialisation différente selon les rangs, sans diffusion depuis le rang 0.

::: war
[À 16 000 GPU, on lit le flight recorder avant de redémarrer]{.tag} L'article Llama 3 décrit l'outillage de diagnostic de 54 jours de pré-entraînement sur 16 000 GPU. Les auteurs utilisent largement le *flight recorder* NCCL de PyTorch pour diagnostiquer vite les blocages et les problèmes de performance, et déclenchent son vidage automatique sur délai ou absence de battement de cœur.

Ils notent aussi qu'un seul retardataire, un GPU encore fonctionnel mais lent, peut ralentir des milliers d'autres GPU et ressemble alors à des communications lentes. Ils ont développé des outils pour prioriser les communications suspectes. Source : [Dubey et al., 2024](https://arxiv.org/abs/2407.21783), section 3.3.4.
:::

::: recap
Points clés — chapitre 8

-   Un blocage est un désaccord entre rangs : collectez l'état de chaque rang avant de redémarrer.
-   Les collectives s'apparient par ordre : un rang qui en saute une provoque un blocage **loin** du bug, après des étapes qui semblent réussir.
-   Trois lectures complémentaires : la cohérence des collectives (`DETAIL`), le journal des collectives (première divergence), la pile Python du rang absent.
-   `monitored_barrier` nomme un rang absent quand on le place avant la collective ; il ne diagnostique pas un désaccord.
-   Le flight recorder NCCL est l'outil de production ; son principe est reproduit sur CPU dans le lab, ses commandes sont documentées mais non exécutées ici.
:::

## 9. L'écosystème : lire les configurations de Megatron-LM, DeepSpeed, TorchTitan et des surcouches {#ch9}

Vous ne programmerez presque jamais DDP à la main : vous opérerez des entraînements écrits avec l'un de quatre outils, et il faudra lire leurs configurations pour répondre à « combien de GPU, quelles dimensions, quel lot ? ». Ce chapitre ne compare pas les outils ; il donne une méthode de lecture et les noms des paramètres qui comptent.

Tout ce qui suit vient de la documentation lue le 25 octobre 2026. **Aucun de ces quatre outils n'est installé dans le bac à sable** : les exemples du dossier `configs/` du lab 9.4 sont analysés et leur arithmétique est vérifiée, jamais exécutés.

### 9.1. Megatron-LM et Megatron Core

Megatron-LM est le dépôt de référence de NVIDIA ; Megatron Core en est la bibliothèque de composants. Sa documentation décrit les dimensions TP, PP, DP, CP, EP et un FSDP propre. Les paramètres suivent les noms des dimensions :

| Dimension | Paramètre |
|---|---|
| tenseur | `--tensor-model-parallel-size` |
| séquence (avec le TP) | `--sequence-parallel` |
| pipeline | `--pipeline-model-parallel-size`, `--num-layers-per-virtual-pipeline-stage` (entrelacement) |
| contexte | `--context-parallel-size` |
| experts | `--expert-model-parallel-size` |
| optimiseur partitionné | `--use-distributed-optimizer` |
| FSDP de Megatron | `--use-megatron-fsdp`, `--data-parallel-sharding-strategy` (`no_shard` pour DDP, `optim_grads_params` pour l'étape 3) |
| lot | `--micro-batch-size`, `--global-batch-size` |

Le degré de **données** n'y est pas un paramètre : il se déduit du nombre de GPU lancés par `torchrun` et des autres degrés.

::: ex
[Exemple 9.1 — Lire la commande « Llama-3 70B sur 64 GPU » du guide de Megatron Core]{.tag} Le fichier `configs/megatron_llama3_70b_64gpu.sh` reprend l'exemple du guide, avec en plus `--sequence-parallel` et `--use-distributed-optimizer` que le guide recommande ailleurs : 8 nœuds de 8 GPU, TP 4, PP 4, CP 2, séquence de 8 192, micro-lot de 1, lot global de 512, BF16. `check_configs.py` l'analyse (`bash -n` puis lecture des arguments) et vérifie l'arithmétique :

~~~text
megatron: {'tp': 4, 'pp': 4, 'cp': 2, 'dp': 2, 'microbatches': 256, 'bubble': 0.01171875, 'tokens': 4194304}
~~~

Le degré de données vaut $64 / (4 \times 4 \times 2) = 2$. Chaque pipeline reçoit $512 / (2 \times 1) = 256$ micro-lots, soit une bulle de $3/256 = 1{,}2\ \%$. Le lot global fait $512 \times 8192 = 4\,194\,304$ tokens, soit $2^{22}$. Avec l'ordre [TP, CP, PP, DP] de Llama 3, `mesh.py` montre que le TP de 4 et le CP de 2 occupent ensemble un nœud de 8 GPU.
:::

::: note
[Une incohérence dans le guide : la formule et le tableau]{.tag} Le guide de Megatron Core écrit « Total GPUs = TP × PP × CP × EP × DP ». Son tableau d'exemples donne pourtant, pour DeepSeek-V3 (671 milliards de paramètres), 1 024 GPU avec TP 2, PP 16, CP 1 et EP 64. Le produit TP × PP × CP × EP vaut déjà 2 048, deux fois les GPU disponibles, ce qui laisserait un degré de données de 0,5. Les autres lignes sont compatibles avec la formule (Llama 3 70B : 4 × 4 × 2 × 1 × 2 = 64).

Deux lectures sont possibles. L'EP peut être découpé **dans** les rangs de données : le Playbook note que certaines implémentations le traitent comme un sous-ensemble du parallélisme de données. Ou bien la ligne suppose d'autres réglages que ceux du tableau. Le guide ne tranche pas : c'est un point **à vérifier** dans le code avant de dimensionner un MoE. L'exercice 14 vous le fait recalculer.
:::

### 9.2. DeepSpeed

DeepSpeed est configuré par un fichier JSON. Les deux blocs qui comptent pour ce module sont la partition des états et l'identité de lot. L'étape ZeRO se règle par `zero_optimization.stage` (0 à 3) ; les paramètres `overlap_comm` et `reduce_bucket_size` règlent le recouvrement et la taille des seaux. Pour le lot, la documentation impose que `train_batch_size` soit égal à `train_micro_batch_size_per_gpu` multiplié par `gradient_accumulation_steps` et par le nombre de GPU ; on peut n'en donner que deux, le troisième est déduit.

~~~json
{
  "train_batch_size": 512,
  "train_micro_batch_size_per_gpu": 2,
  "gradient_accumulation_steps": 4,
  "bf16": { "enabled": true },
  "zero_optimization": { "stage": 3, "overlap_comm": true }
}
~~~

Le fichier `configs/deepspeed_zero3.json` contient les mêmes clés et les mêmes valeurs ; `check_configs.py` vérifie qu'avec 64 GPU, $2 \times 4 \times 64 = 512$. Avec 32 GPU, le même fichier violerait l'identité exigée par la documentation : c'est une erreur de configuration à attendre après chaque changement de taille de job.

### 9.3. TorchTitan

TorchTitan est la plateforme de PyTorch pour le pré-entraînement. Ses composants s'empilent par `DeviceMesh` et `DTensor` : FSDP2, HSDP, parallélisme tensoriel (y compris asynchrone), pipeline (1F1B, entrelacé, GPipe), contexte, `torch.compile` régional, états d'optimiseur en BF16. Dans la version que nous avons lue, **une configuration est une fonction Python** qui retourne la configuration complète :

~~~python
def llama3_8b_fsdp8_tp2():
    config = llama3_8b()
    config.parallelism.data_parallel_shard_degree = 8
    config.parallelism.tensor_parallel_degree = 2
    return config  # NGPU must equal the product of the degrees: 8 x 2 = 16
~~~

La documentation précise : les degrés de parallélisme sont dans la configuration, mais pas la taille du monde ; la variable `NGPU` doit donc correspondre au produit des degrés. Les chemins de configuration changent vite : le fichier TOML que nous avons tenté de lire sur la branche principale (`llama3_8b.toml`) n'existe plus (erreur 404), et la documentation actuelle ne décrit que des recettes Python. Lisez la documentation de **votre** version.

### 9.4. Accelerate et Lightning

Accelerate et Lightning ne sont pas des moteurs de parallélisme : ce sont des surcouches qui configurent et lancent DDP, FSDP ou DeepSpeed. Avec Accelerate, `accelerate config` écrit un fichier, `accelerate launch` lance le script, et `fsdp_sharding_strategy` règle FSDP. Sa documentation fait la correspondance avec ZeRO : `FULL_SHARD` vaut l'étape 3, `SHARD_GRAD_OP` l'étape 2, `NO_SHARD` DDP, et `HYBRID_SHARD` partitionne dans chaque nœud en répliquant entre nœuds. Avec Lightning, `L.Trainer(accelerator="cuda", devices=2, strategy="fsdp")` active FSDP en une ligne.

Ces surcouches simplifient le lancement, pas les questions de ce module : elles ne choisissent pas vos degrés, ne vérifient pas le placement et ne diagnostiquent pas un blocage.

### 9.5. Lire une configuration en sept questions

1.  **Le produit des degrés égale-t-il le nombre de GPU ?** Calculez-le, y compris le degré de données déduit.
2.  **Le lot global est-il produit par la disposition ?** Micro-lot × accumulation × degré de données (chapitre 5).
3.  **Combien de micro-lots par pipeline, et quelle bulle ?** Le nombre doit dépasser largement le nombre d'étages (chapitre 4).
4.  **Quelle dimension est partitionnée, et jusqu'où ?** Étape ZeRO, `reshard_after_forward`, optimiseur distribué (chapitre 3).
5.  **Le TP tient-il dans le nœud ?** Degré de TP au plus égal au nombre de GPU par nœud, rangs consécutifs (chapitre 5).
6.  **Quelle précision pour les calculs, les sommes et les gradients réduits ?** (chapitre 7).
7.  **Quel recalcul d'activations ?** Aucun, sélectif ou complet (chapitre 3).

::: recap
Points clés — chapitre 9

-   Megatron-LM nomme les dimensions par paramètres ; le degré de données se déduit. DeepSpeed règle l'étape ZeRO et l'identité de lot dans un JSON. TorchTitan décrit une configuration par une fonction Python. Accelerate et Lightning enveloppent DDP, FSDP ou DeepSpeed.
-   Les noms diffèrent, les questions sont les mêmes : produit des degrés, lot global, micro-lots et bulle, partition des états, placement du TP, précision, recalcul.
-   Une documentation peut se contredire (formule et tableau du guide de Megatron Core) : recalculez les exemples avant de vous y fier.
-   Les formats de configuration évoluent vite ; datez ce que vous lisez et lisez la version que vous opérez.
:::

## Labs {#labs}

Les quatre labs tournent sur **CPU, avec le backend `gloo`**, dans `labs/distributed-training/`. Leurs `verify.sh` ont été exécutés avec PyTorch 2.14.1 (CPU) et Python 3.13 sur une VM Linux de 4 vCPU et 16 Go ; chacun honore la variable `PYTHON`. Le lab 9.2 lit `/proc` : Linux est requis. Aucun GPU n'est requis, mais quatre processus PyTorch occupent quatre cœurs : ne lancez pas deux labs à la fois sur une machine partagée. Installation préalable :

~~~bash
python3 -m venv .venv && . .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install numpy pytest
export PYTHON="$(command -v python)" OMP_NUM_THREADS=1 GLOO_SOCKET_IFNAME=lo
~~~

::: lab
[Lab 9.1 — DDP à quatre processus sur CPU]{.tag}

**Objectif.** Entraîner un MLP avec DDP sur quatre processus, prouver l'équivalence avec un processus seul à l'arrondi près, prédire les seaux, mesurer la communication, reproduire et corriger deux erreurs classiques. **Durée.** 3 h (partie A : 1,5 h, partie B : 1,5 h). **Prérequis matériels.** Un portable à 4 cœurs et 2 Go libres, sans GPU.

*Partie A.*

1.  Lisez `common.py` et `train.py` : lot global seedé, découpage par rang (`shard_bounds`), contexte `no_sync`.
2.  Lancez `train.py --steps 12 --out single.json` seul, puis avec `python3 -m torch.distributed.run --standalone --nproc_per_node=4 train.py --steps 12 --hook --timing --out ddp.json`.
3.  Comparez avec `compare.py single.json ddp.json`, puis comparez deux exécutions de DDP entre elles.
4.  Lancez `buckets.py` et `buckets.py --cap-mb 1` ; comparez à `ddp_rebuilt_bucket_sizes` de `ddp.json` et d'une exécution avec `--bucket-cap-mb 1`.

*Partie B.*

5.  Reliez `hook_calls` à `1 + (étapes - 1) × seaux` ; comparez le pas avec et sans synchronisation à l'all-reduce isolé.
6.  Lancez DDP avec `--uneven` : l'écart avec `single.json` est-il un arrondi ?
7.  Lancez `unused_param_demo.py` avec `TORCH_DISTRIBUTED_DEBUG=INFO` sur 2 processus, relevez le nom du paramètre, puis ajoutez `--fix`.
8.  Lancez `bash verify.sh`. Plus tard, en lisant le §7.2 (séance 9), lancez aussi `numerics_demo.py` (3 s).

**Critère de réussite.** `bash verify.sh` se termine par le code 0 et affiche, par exemple, `OK ddp-gloo: DDP(4) vs single process max|dw|=7.5e-09 (rel 6.0e-08); repeat run bitwise equal; buckets [1052676, 4335616] predicted = measured`. Vos derniers chiffres diffèrent.

Sont exigés : écart des paramètres inférieur à 1e-5 ; deux exécutions de DDP identiques bit à bit ; seaux prédits égaux aux seaux journalisés ; `1 + (étapes - 1) × seaux` appels ; écart du découpage inégal supérieur à 1e-4 ; erreur de paramètre inutilisé reproduite (code 1) puis corrigée (code 0). Les temps affichés ne sont jamais assertés.

**Pour aller plus loin.** Essayez `--optim adamw --lr 0.003` (écart de l'ordre de 1e-6). Sur un nœud à GPU : `nccl`, `device_ids=[local_rank]` et `Avg backward comm/comp overlap time` sous `TORCH_DISTRIBUTED_DEBUG=DETAIL` (documenté, **non exécuté ici**).
:::

::: lab
[Lab 9.2 — FSDP : mesurer la mémoire par rang]{.tag}

**Objectif.** Mesurer ce que chaque rang détient sous DDP et sous FSDP2, le comparer à une prédiction écrite à partir des formes des tenseurs, et montrer que FSDP2 et DDP calculent la même chose. **Durée.** 3 h (partie A : 1,5 h, partie B : 1,5 h). **Prérequis matériels.** Quatre cœurs, 3 Go libres, PyTorch 2.6 ou plus pour `fully_shard`.

*Partie A.*

1.  Lisez `fsdp_memory.py` : `fully_shard` bloc par bloc puis sur la racine, `DTensor.to_local()`, crochet de mesure des paramètres non partitionnés.
2.  Lisez `predict.py` et lancez `test_predict.py` : la règle de découpage est celle de `torch.chunk`.
3.  Lancez `--mode ddp` puis `--mode fsdp` (commandes dans le README) et ouvrez les deux JSON.
4.  Calculez le rapport entre DDP et FSDP pour un rang, et expliquez pourquoi le dernier rang détient un peu moins.

*Partie B.*

5.  Lancez `--mode fsdp --no-reshard` et comparez `peak_unsharded_param_bytes`.
6.  Lancez `equivalence.py` : normes globales de DDP et de FSDP2, norme du fragment local du rang 0, paramètres finaux (interprétation au §7.3).
7.  Modifiez `fsdp_memory.py` pour n'appeler `fully_shard` que sur la racine et relisez le pic.
8.  Lancez `bash verify.sh`.

**Critère de réussite.** `bash verify.sh` se termine par le code 0 et affiche, par exemple, `OK fsdp-memory: 16802826 parameters; per-rank persistent MiB: DDP 256.4, FSDP [64.1, 64.1, 64.1, 64.09] (measured = predicted, ratio 4.00)`.

Sont exigés : octets de paramètres, de gradients et d'états **exactement égaux** à la prédiction sur chaque rang ; rapport DDP sur FSDP entre 3,9 et 4 ; paramètres égaux à 1e-5 près après trois étapes ; norme de gradient égale à 1e-3 près (relatif) ; pic de mémoire résidente de DDP supérieur d'au moins 15 % à celui de FSDP2.

**Pour aller plus loin.** Mesurez le pic en passe arrière avec `torch.profiler` en mode mémoire. Sur GPU, ajoutez `MixedPrecisionPolicy(param_dtype=torch.bfloat16, reduce_dtype=torch.float32)` (**non testé ici**).
:::

::: lab
[Lab 9.3 — Reproduire et diagnostiquer un hang]{.tag}

**Objectif.** Reproduire deux blocages, un rang qui saute une collective et un rang bloqué hors des collectives, et les localiser avec le délai, `TORCH_DISTRIBUTED_DEBUG`, `monitored_barrier`, un journal des collectives et les piles Python. **Durée.** 3 h (partie A : 1,5 h, partie B : 1,5 h). **Prérequis matériels.** Quatre cœurs presque inactifs (les rangs attendent), sans GPU. Le journal est un **analogue écrit pour ce lab** du *flight recorder* NCCL, qui n'existe pas pour `gloo` : le README du lab distingue le réel du simulé.

*Partie A : le rang qui saute.*

1.  Lisez `train_hang.py` et repérez où le rang 2 saute la collective de l'étape 4 (`--bug skip`).
2.  Lancez `--bug skip --timeout 5` sans outil : combien d'étapes « réussissent » ?
3.  Relancez avec `TORCH_DISTRIBUTED_DEBUG=DETAIL --timeout 30`, puis avec `--journal-dir`, et lisez `analyze_journal.py` sur le résultat.
4.  Vérifiez que `--bug none` est la version corrigée et notez la phrase qui désigne le coupable et l'étape.

*Partie B : le rang absent.*

5.  Lancez `--bug stuck --timeout 5 --journal-dir J --stacks-dir S` ; lisez l'analyse, puis `S/rank2.txt` et `S/rank0.txt`.
6.  Relancez la commande avec `--timeout 60`, attendez 5 s, envoyez `kill -USR1` aux processus de **votre** `torchrun` (`pgrep -P <pid>`), puis arrêtez-le par son PID.
7.  Lancez `--bug stuck --monitored`, puis `TORCH_DISTRIBUTED_DEBUG=DETAIL --bug stuck` : quel rang est nommé, et quand ?
8.  Lancez `bash verify.sh` et remplissez à la main le tableau « outil contre bug » du chapitre 8.

**Critère de réussite.** `bash verify.sh` se termine par le code 0 après les lignes `OK 1` à `OK 6` (dont `4b` et `5b`) et `OK hang-debug`.

Sont exigés : progression apparente jusqu'à l'étape 8 puis expiration (`skip`) ; `Detected mismatch between collectives on ranks` avec `OpType=BARRIER` sous `DETAIL` ; première divergence à la séquence 4 avec le rang 2 sur l'étape 5 ; trois rangs en attente dans la séquence 4, le rang 2 sans collective en cours et sa pile hors de `all_reduce`, par le délai comme par `kill -USR1` (`stuck`) ; `Rank 2 failed to pass monitoredBarrier` ; programme corrigé en code 0. Aucune durée n'est assertée.

**Pour aller plus loin.** Sur GPU : `TORCH_NCCL_TRACE_BUFFER_SIZE=2000 TORCH_NCCL_DUMP_ON_TIMEOUT=true`, puis `torchfrtrace <répertoire>` (**documenté, non exécuté ici**). Ajoutez un bug où un rang fait une étape de moins et vérifiez que l'analyseur le nomme.
:::

::: lab
[Lab 9.4 — Un planificateur de parallélisme testé]{.tag}

**Objectif.** Écrire un calculateur de mémoire et de communication à partir des formules de ZeRO, de Korthikanti et al. et de Megatron-LM, le valider contre les figures des articles, l'appliquer à un job de 70 milliards de paramètres, puis le confronter à un vrai parallélisme tensoriel et à `DeviceMesh`. **Durée.** 4 h (partie A : 2 h, partie B : 2 h). **Prérequis matériels.** Un portable ; PyTorch CPU pour `mesh_check.py` et `tp_mlp_check.py`.

*Partie A : la mémoire.*

1.  Lisez `tests/test_planner.py` : les valeurs attendues viennent des articles (figure 1 de ZeRO, tableau 2 de Korthikanti et al.).
2.  Lancez `IMPL=starter python3 -m pytest -q tests` : 22 échecs par `NotImplementedError`, 6 réussites.
3.  Dans `starter/planner.py`, implémentez `zero_state_bytes`, `model_state_bytes`, `activation_bytes_per_layer`, `activation_bytes_first_stage` et `pipeline_bubble_fraction`, jusqu'à ce que leurs tests passent.

*Partie B : la communication et le choix.*

4.  Implémentez `dp_comm_seconds`, `tp_comm_seconds`, `pp_comm_seconds`, `feasible_layouts` et `evaluate`.
5.  Lancez `IMPL=starter python3 scenario.py --top 12` et comparez aux lignes de l'exemple 5.2, puis lancez la référence.
6.  Lancez `tp_mlp_check.py` sur 2 processus et `mesh_check.py` sur 4 ; lisez `check_configs.py` et les trois fichiers de `configs/`.
7.  Lancez `bash verify.sh`.

**Critère de réussite.** `IMPL=starter python3 -m pytest -q tests` donne 28 tests réussis sur 28 avec votre code, et `bash verify.sh` se termine par le code 0 après `ok: reference passes, starter fails as intended` et `OK parallelism-planner`.

Le tableau de `scenario.py` est identique à une décimale près avec votre code et avec la référence. Vous savez dire pourquoi trois dispositions voisines de la colonne « sans recouvrement » ne se départagent pas sans mesure.

**Pour aller plus loin.** Ajoutez un terme d'efficacité des noyaux qui baisse quand les matrices par GPU rapetissent (à ajuster sur vos mesures, sans source publiée ici). Branchez le planificateur sur vos bandes passantes mesurées avec `nccl-tests`.
:::

## Exercices {#ex}

Les corrigés sont complets ; les calculs ont été refaits en Python et les commandes exécutées sur la VM de rédaction. Les sorties marquées « fictive » sont inventées pour l'exercice, au format des outils du lab.

::: exo
[Exercice 1 · ★ — Décoder une ligne de Llama 3]{.tag} La troisième ligne du tableau 4 de l'article Llama 3 donne : 16 384 GPU, TP 8, CP 16, PP 16, DP 8, séquences de 131 072 tokens, 16 séquences par groupe de données, 380 TFLOP/s par GPU. (a) Le produit des degrés égale-t-il le nombre de GPU ? (b) Combien de séquences et de tokens par lot global ? (c) Quel MFU, avec un pic dense de 989 TFLOP/s ? (d) Avec 8 GPU par nœud et le TP le plus interne, combien de nœuds un groupe de contexte traverse-t-il ?
:::

::: sol
(a) $8 \times 16 \times 16 \times 8 = 16\,384$ : oui.

(b) $8 \times 16 = 128$ séquences, soit $128 \times 131\,072 = 16\,777\,216$ tokens : les mêmes « 16M » que les deux autres lignes.

(c) $380 / 989 = 38{,}4\ \%$, que l'article arrondit à 38 %.

(d) Le TP, le plus interne, occupe les 8 rangs consécutifs d'un nœud. Le CP vient ensuite, avec un pas de 8 : chacun de ses 16 membres est dans un nœud différent, donc **16** nœuds (`Mesh(("dp","pp","cp","tp"), (8,16,16,8)).node_span("cp", 8)` le confirme). Son all-gather de clés et valeurs traverse le réseau, ce que l'article accepte parce que ces tenseurs sont petits (GQA).
:::

::: exo
[Exercice 2 · ★ — Qui est qui avec torchrun ?]{.tag} Un job est lancé par `torchrun --nnodes=2 --nproc-per-node=8 …`. (a) Pour le processus de rang local 3 sur le nœud dont `GROUP_RANK` vaut 1, donnez `RANK`, `LOCAL_RANK`, `WORLD_SIZE` et `LOCAL_WORLD_SIZE` avec l'affectation habituelle. (b) Le script fait `torch.cuda.set_device(int(os.environ["RANK"]))` : que se passe-t-il sur le nœud 1 ? (c) Après un redémarrage, le même processus physique reçoit-il le même `RANK` ?
:::

::: sol
(a) `RANK` vaut $1 \times 8 + 3 = 11$, `LOCAL_RANK` 3, `WORLD_SIZE` 16, `LOCAL_WORLD_SIZE` 8.

(b) Sur le nœud 1, les rangs globaux vont de 8 à 15, mais le nœud n'a que les GPU 0 à 7 : `set_device(11)` échoue. Le GPU se choisit avec `LOCAL_RANK`.

(c) Pas forcément : la documentation dit que `RANK` n'est pas stable d'un redémarrage à l'autre et interdit d'en faire une hypothèse. Un checkpoint se retrouve par son contenu, pas par « le rang 3 ».
:::

::: exo
[Exercice 3 · ★ — Quelle étape ZeRO pour 13 milliards ?]{.tag} Un modèle de 13 milliards de paramètres est entraîné avec Adam en précision mixte (2 + 2 + 12 octets par paramètre) sur 16 rangs de données, avec des GPU de 80 Go. Donnez les états par GPU pour les étapes 0 à 3, puis la première étape qui laisse au moins 20 Go pour les activations et la marge.
:::

::: sol
Avec $\Psi = 13 \cdot 10^{9}$ et $N_d = 16$ : étape 0, $16\Psi = 208$ Go ; étape 1, $4\Psi + 12\Psi/16 = 61{,}75$ Go ; étape 2, $2\Psi + 14\Psi/16 = 37{,}375$ Go ; étape 3, $16\Psi/16 = 13$ Go.

Les états ne doivent pas dépasser $80 - 20 = 60$ Go. L'étape 1 laisse 18,25 Go : insuffisant. L'**étape 2** (reste 42,6 Go) est la première qui convient. L'étape 3 libérerait 67 Go mais coûte 1,5 fois le volume de DDP : inutile si l'étape 2 suffit.
:::

::: exo
[Exercice 4 · ★★ — Prévoir les seaux de DDP]{.tag} Les gradients deviennent disponibles dans l'ordre suivant, en MiB : 0,5 ; 0,6 ; 12 ; 14 ; 9 ; 30 ; 3.

Règle : on ajoute chaque tenseur au seau courant, qui se ferme dès que sa taille atteint la limite. La limite du premier seau est de 1 MiB si `bucket_cap_mb` n'est pas fourni, sinon celle des autres.

(a) Donnez les seaux avec le réglage par défaut (25 MiB). (b) Même question avec `bucket_cap_mb=25` fourni, puis 10. (c) Combien d'all-reduce à la première itération ? (d) Quel est l'intérêt d'un petit premier seau ?
:::

::: sol
(a) Le premier seau se ferme à $0{,}5 + 0{,}6 = 1{,}1$ MiB. Puis $12 + 14 = 26$ MiB ferme le deuxième, $9 + 30 = 39$ MiB le troisième, et 3 MiB forment le quatrième : **[1,1 ; 26 ; 39 ; 3]**, soit 4 all-reduce.

(b) Avec 25 fourni : **[27,1 ; 39 ; 3]**, 3 all-reduce. Avec 10 : **[13,1 ; 14 ; 39 ; 3]**, 4 all-reduce. `predict_buckets` de `buckets.py` le confirme.

(c) Un seul : à la première itération DDP n'utilise qu'un seau, l'ordre réel des gradients étant inconnu (code source de la version testée).

(d) Les gradients des dernières couches sont prêts les premiers : un petit premier seau lance la communication plus tôt pendant la passe arrière, pour un terme de latence de plus.
:::

::: exo
[Exercice 5 · ★★ — Lire une erreur de DDP]{.tag} Fin du message d'un job à 2 processus (capturé avec le lab 9.1 sous `TORCH_DISTRIBUTED_DEBUG=INFO`) :

~~~text
rank 0: RuntimeError at step 1
    Expected to have finished reduction in the prior iteration before starting a new one. [...]
    Parameters which did not receive grad for rank 0: a.weight
~~~

(a) Quel paramètre pose problème ? (b) Pourquoi l'erreur apparaît-elle à l'étape 1 et non à l'étape 0 ? (c) Donnez trois corrections et leur coût. (d) Que vérifiez-vous avant `find_unused_parameters=True` ?
:::

::: sol
(a) `a.weight` : la perte ne dépend pas de la tête `a`.

(b) À l'étape 0, le seau qui contient `a.weight` n'est jamais complet : la réduction reste inachevée. L'étape suivante, en voulant en démarrer une nouvelle, le constate et lève l'erreur.

(c) (1) Faire participer la sortie `a` à la perte, ou supprimer la tête : aucun coût. (2) `find_unused_parameters=True` : parcours du graphe autograd à chaque itération. (3) `static_graph=True` si les paramètres inutilisés sont toujours les mêmes : repérés une fois ; faux dès que le graphe change.

(d) Que l'inutilisation est voulue (branche réellement conditionnelle) et non un bug (branche oubliée, poids gelé par erreur). Ne payez le surcoût qu'après avoir écarté le bug.
:::

::: exo
[Exercice 6 · ★★ — Les activations d'un modèle de 13 milliards]{.tag} Un modèle a 40 couches, une taille cachée de 5 120 et 40 têtes ; séquence de 4 096 tokens, micro-lot de 2. L'activation d'une couche vaut $s\,b\,h\,(34 + 5\,a\,s/h)$ octets. (a) Calculez-la par couche et pour 40 couches. (b) Même question avec le recalcul sélectif (le terme en $5as/h$ disparaît). (c) Avec TP 8, parallélisme de séquence et recalcul sélectif (facteur $34/8$). (d) Les états occupent 30 Go sur un GPU de 80 Go utilisé à 90 % : quelles variantes tiennent ?
:::

::: sol
Ici $s\,b\,h = 4096 \times 2 \times 5120 = 41\,943\,040$ et $5as/h = 160$.

(a) Facteur 194 : 8,14 Go par couche, **325,5 Go** pour 40 couches. (b) Facteur 34 : 1,43 Go par couche, **57,0 Go**. (c) Facteur 4,25 : 0,178 Go par couche, **7,13 Go**.

(d) Le budget est $0{,}9 \times 80 - 30 = 42$ Go. Le recalcul sélectif seul (57,0 Go) ne tient pas ; TP 8 avec séquence et recalcul sélectif (7,1 Go) tient largement ; le recalcul complet ($2\,s\,b\,h$ par couche, 3,36 Go au total) tient aussi mais coûte 39 % de calcul en plus (mesure de Korthikanti et al.). Un pipeline 1F1B ne change pas ces totaux : la première étape garde les activations de toutes les couches.
:::

::: exo
[Exercice 7 · ★★ — Dimensionner un pipeline]{.tag} Un job utilise PP 8 et DP 4, avec un lot global de 256 séquences et des micro-lots d'une séquence. Bulle $= (p-1)/(v\,m)$ ; avec $v > 1$, la mémoire d'activations de la première étape est multipliée par $1 + (p-1)/(p\,v)$. (a) Combien de micro-lots par pipeline, et quelle bulle ? (b) Quelle bulle et quel prix en mémoire avec $v = 2$ et $v = 4$ ? (c) Quel lot global minimal pour une bulle d'au plus 5 % sans entrelacement ? (d) Pourquoi ne pas simplement augmenter le lot ?
:::

::: sol
(a) $m = 256 / 4 = 64$ ; bulle $7/64 = 10{,}9\ \%$.

(b) $v = 2$ : bulle de $7/128 = 5{,}5\ \%$, mémoire ×1,44. $v = 4$ : bulle de $7/256 = 2{,}7\ \%$, mémoire ×1,22. L'entrelacement multiplie aussi par $v$ les communications entre étages.

(c) $m \ge 7 / 0{,}05 = 140$, donc un lot global d'au moins $140 \times 4 = 560$ séquences.

(d) Le lot utile est une propriété de l'optimisation : au-delà d'un certain lot, les rendements décroissent (*How to Scale Your Model*). Remplir un pipeline en grossissant le lot peut dégrader la convergence : ce n'est pas une décision d'infrastructure seule.
:::

::: exo
[Exercice 8 · ★★ — Le TP à 4 : dans le nœud ou sur le réseau ?]{.tag} Une couche a une taille cachée de 6 144 ; séquence de 4 096 tokens, micro-lot de 2, BF16, TP 4. Une couche exécute 4 all-reduce de $s\,b\,h$ éléments ; un all-reduce en anneau émet $2\,\frac{t-1}{t}\,n$ octets ; une couche a environ $12h^2$ paramètres, son calcul vaut $6 \times 12h^2 \times s\,b$ FLOP répartis sur $t$ GPU. Hypothèses : 400 Go/s dans le nœud, 25 Go/s entre nœuds, MFU de 40 % sur 989 TFLOP/s. Calculez la communication par couche dans chaque cas, le calcul, et concluez.
:::

::: sol
Un all-reduce porte $4096 \times 2 \times 6144 \times 2 = 100{,}7$ Mo ; chaque GPU émet $2 \times \frac{3}{4} \times 100{,}7 = 151{,}0$ Mo, soit 604 Mo pour les quatre. Dans le nœud : $604 / 400\,000 = 1{,}51$ ms. Entre nœuds : **24,2 ms**.

Le calcul vaut $6 \times 12 \times 6144^2 \times 8192 / 4 = 5{,}57$ TFLOP par GPU, soit $14{,}1$ ms à 40 % de MFU.

La communication pèse 10,7 % du calcul dans le nœud et **172 %** entre nœuds : elle dépasse le calcul. Le TP reste dans le nœud ; au-delà, pipeline ou données. Ces débits sont des hypothèses : mesurez-les avec `nccl-tests`.
:::

::: exo
[Exercice 9 · ★★ — Diagnostiquer un hang à partir d'un journal]{.tag} Un job à 8 rangs est bloqué depuis 20 minutes. Analyse des journaux (sortie **fictive**) puis pile du rang 5 (extrait **fictif**) :

~~~text
rank  last_completed  in_flight
   0            1206  seq 1207 all_reduce 'step=412' at train.py:88
   ...             (rangs 1 à 4 et 6 à 7 identiques)
   5            1206  -
findings:
  - ranks [0, 1, 2, 3, 4, 6, 7] wait in seq 1207 (all_reduce, step=412); rank(s) [5] completed only up to seq 1206 and have nothing in flight

  File ".../queue.py", line 171 in get
  File ".../dataloader.py", line 1285 in _get_data
  File "train.py", line 61 in main
~~~

(a) Quelle famille de blocage, quel rang, quelle étape ? (b) Que dit la pile ? (c) Trois causes à vérifier côté infrastructure ? (d) Que faites-vous du job et de la suite ?
:::

::: sol
(a) Un rang **absent** : sept rangs attendent dans la collective 1207 de l'étape 412 ; le rang 5, sans rien en cours, s'est arrêté après la 1206. Les autres sont d'accord entre eux : ce n'est pas un désaccord de flot de contrôle.

(b) Le fil principal du rang 5 attend dans `queue.get` du chargeur de données : le chargeur ne livre plus de lot. La cause n'est pas dans les collectives.

(c) Le stockage vu par le nœud du rang 5 (E/S bloquées ou très lentes, module 8) ; un processus de chargement tué (manque de mémoire, `dmesg`) ; une contention de CPU ou un échantillon anormalement lourd.

(d) Conservez piles et journaux, vérifiez le nœud du rang 5, puis tuez le job et repartez du dernier checkpoint (on perd le travail depuis celui-ci). Pour la suite : un délai de récupération d'un lot qui nomme le rang, une métrique de temps par rang visible avant le blocage (module 14), des délais de groupe courts en test.
:::

::: exo
[Exercice 10 · ★★★ — Choisir une disposition pour 175 milliards de paramètres]{.tag} Un modèle de 175 milliards de paramètres (96 couches, taille cachée 12 288, 96 têtes, séquence de 4 096) s'entraîne sur 128 GPU de 80 Go (16 nœuds de 8), lot global de 1 024 séquences, micro-lot de 1. Lancez `scenario.py` du lab 9.4 avec les hypothèses du chapitre 5. (a) Combien de dispositions tiennent ? (b) Choisissez trois candidates à mesurer, avec leur mémoire et leur surcoût estimé. (c) Donnez un critère de décision chiffré. (d) Nommez une limite du modèle qui pourrait renverser le classement.
:::

::: sol
(a) Commande : `python3 scenario.py --psi 175e9 --layers 96 --h 12288 --heads 96 --seq 4096 --gpus 128 --batch 1024 --top 10`. Sortie : 54 dispositions évaluées, **24 tiennent** dans 72 Go, pour 87,0 s de calcul par étape. Trois premières lignes :

~~~text
tp pp dp zero recompute  m  state_GB  acts_GB  total_GB  bubble  t_tp_s  t_pp_s  t_dp_s  overhead: no-overlap / dp-hidden
 4 16  2    1 selective 512     27.3     41.1     68.4    2.9%    4.64    1.03    0.22     16.7%     16.4%
 4 32  1    1 selective 1024     21.9     41.1     62.9    3.0%    4.64    2.06    0.00     17.7%     17.7%
 8  8  2    1 selective 512     27.3     20.5     47.9    1.4%   10.82    0.52    0.22     21.7%     21.4%
~~~

(b) **A** (4, 16, 2, ZeRO-1) : 16,7 %, mais 68,4 Go, 3,6 Go sous la limite, donc fragile face à la fragmentation. **B** (4, 1, 32, ZeRO-3) : 24,0 % sans recouvrement, 12,3 % si les 10,2 s de communication de données se cachent derrière 87 s de calcul ; 62,9 Go, sans pipeline donc plus simple à exploiter. **C** (8, 8, 2, ZeRO-1) : 21,7 %, 47,9 Go, grande marge mémoire.

(c) Mesurer 50 étapes de chacune ; médiane de tokens par seconde après échauffement ; retenir la plus rapide dont le pic de mémoire reste sous 72 Go ; à moins de 3 % d'écart, la plus simple (B). Ce seuil est un choix de ce parcours.

(d) Le modèle ignore l'efficacité des noyaux sur de petites matrices (un TP ou un pipeline plus grand la dégrade, donc pénalise C), le recouvrement réel (B en dépend entièrement) et le déséquilibre entre étages.
:::

::: exo
[Exercice 11 · ★★★ — Expliquer un MFU de 35 %]{.tag} Un modèle de $8 \cdot 10^{9}$ paramètres s'entraîne sur 64 H100 (989 TFLOP/s) avec $2^{22}$ tokens par étape, en 9,0 s. Profil **fictif** : noyaux 6,1 s ; communication exposée 1,5 s ; attente de données 0,6 s ; optimiseur 0,5 s ; checkpoint amorti 0,3 s. (a) Calculez le MFU avec $6\Psi$ FLOP par token. (b) Quel MFU en supprimant chaque poste, et tous ensemble ? (c) Deux leviers : précharger les données (peu coûteux, supprime au mieux l'attente) ou recouvrir la communication (semaines d'ingénierie, supprime au mieux la moitié de la communication exposée). Lequel d'abord ?
:::

::: sol
(a) Le débit vaut $2^{22} / 9{,}0 = 466\,034$ tokens/s. Les FLOP utiles par seconde valent :

$$6 \times 8 \cdot 10^{9} \times 466\,034 = 2{,}237 \cdot 10^{16}$$

Le pic agrégé vaut $64 \times 989 \cdot 10^{12} = 6{,}33 \cdot 10^{16}$ FLOP/s : MFU $= 35{,}3\ \%$.

(b) Le MFU est inversement proportionnel à la durée. Sans l'attente (8,4 s) : **37,9 %**. Sans communication exposée (7,5 s) : **42,4 %**. Sans checkpoint amorti (8,7 s) : 36,6 %. Sans optimiseur (8,5 s) : 37,4 %. Sans attente ni communication (6,9 s) : **46,1 %**. Sans aucun poste hors noyaux (6,1 s) : 52,1 %, le plafond de ce profil.

(c) Le préchargement vise au mieux 2,5 points (35,3 → 37,9 %) pour un coût faible. Le recouvrement partiel vise 0,75 s, donc 35,3 → 38,6 % au mieux, pour des semaines. Gains du même ordre, coûts sans commune mesure : on commence par les données, puis on mesure à nouveau, car la communication devient alors le premier poste.
:::

::: exo
[Exercice 12 · ★★★ — Un pic de perte : bug ou numérique ?]{.tag} Un entraînement à 64 GPU (étape de 9,0 s, $2^{22}$ tokens par étape) affiche, d'après un journal **fictif**, ces valeurs ; la norme « locale » est celle du fragment FSDP du rang 0 (modèle partitionné sur 64 rangs), semblable à celle des autres rangs :

| Étape | Perte | Norme globale | Norme locale (rang 0) |
|---|---|---|---|
| 18 390 | 2,41 | 0,92 | 0,115 |
| 18 398 | 2,42 | 3,8 | 0,48 |
| 18 399 | 2,44 | 14,1 | 1,76 |
| 18 400 | 3,97 | 52,6 | 6,6 |
| 18 410 | 3,10 | 8,0 | 1,0 |

(a) Les rangs sont-ils d'accord ? (b) Quels essais du §7.5, dans quel ordre ? (c) Remède de PaLM : repartir 100 étapes avant le pic, sauter 300 lots. Coût en GPU-heures et en tokens écartés ? (d) Que changez-vous dans la surveillance ?
:::

::: sol
(a) Oui. La norme locale vaut environ un huitième de la norme globale (0,115 contre 0,92 ; 6,6 contre 52,6), soit $1/\sqrt{64}$, ce qu'on attend de 64 fragments de poids comparable. Aucun rang ne diverge.

(b) D'abord comparer, à l'étape 18 398, avec un processus seul sur les mêmes lots : même norme à l'arrondi près, donc pas de bug de distribution (sur un modèle réduit si le modèle complet ne tient pas sur un processus). Ensuite rejouer le pic sur un processus seul : s'il pique, l'instabilité est numérique ou d'optimisation. Puis contrôler la précision des sommes (FP32). Enfin redémarrer avant le pic en sautant des lots.

(c) 100 étapes de 9,0 s font 900 s, soit $900 \times 64 / 3600 = 16{,}0$ GPU-heures recalculées. 300 lots de $2^{22}$ tokens font $1{,}26 \cdot 10^{9}$ tokens écartés.

(d) Alerter sur la **norme globale** (de 0,9 à 3,8 en huit étapes, avant que la perte bouge) plutôt que sur la perte, et checkpointer assez souvent pour que la reprise coûte peu (module 10).
:::

::: exo
[Exercice 13 · ★★ — DDP ou FSDP entre nœuds ?]{.tag} Un modèle de $7 \cdot 10^{9}$ paramètres s'entraîne sur 32 GPU (4 nœuds de 8), gradients et paramètres BF16. Hypothèses : 25 Go/s par GPU entre nœuds, 8 séquences de 4 096 tokens par GPU, MFU de 40 % sur 989 TFLOP/s. DDP émet par GPU $2\,\frac{p-1}{p}\,n$ octets avec $n = 14$ Go ; FSDP (ZeRO-3) émet $\frac{p-1}{p}\,(2+2\times 2)\,\Psi$ octets. Calculez trafic et temps des deux options, le temps de calcul, et concluez.
:::

::: sol
DDP : $2 \times \frac{31}{32} \times 14 = 27{,}1$ Go, soit **1,09 s** à 25 Go/s. FSDP : $\frac{31}{32} \times 6 \times 7 = 40{,}7$ Go, soit **1,63 s** : rapport 1,5, comme dans l'article ZeRO.

Le calcul par étape, pour 32 768 tokens par GPU, vaut :

$$\frac{6 \times 7 \cdot 10^{9} \times 32768}{989 \cdot 10^{12} \times 0{,}4} = 3{,}48\ \text{s}$$

Avec un recouvrement parfait, les deux sont cachées (1,63 s = 47 % du calcul). La marge de FSDP est plus mince et dépend du préchargement des all-gather et de `fully_shard` couche par couche. Si la moitié seulement se cache, il reste 0,8 s exposées (23 %) contre 0,54 s pour DDP. Mais DDP ne tient pas en mémoire (112 Go d'états) : FSDP est ici une nécessité. Retenez le facteur 1,5.
:::

::: exo
[Exercice 14 · ★★★ — Vérifier une configuration publiée]{.tag} Le guide de Megatron Core donne « Total GPUs = TP × PP × CP × EP × DP » et un tableau MoE : Mixtral 8x7B (64 GPU, TP 1, PP 4, CP 1, EP 8) ; Mixtral 8x22B (256 GPU, TP 4, PP 4, CP 1, EP 8) ; DeepSeek-V3 (1 024 GPU, TP 2, PP 16, CP 1, EP 64).

(a) Pour chaque ligne, calculez le degré de données si l'EP est multiplicatif, puis s'il est découpé dans les rangs de données. (b) Quelle ligne contredit la première lecture ? (c) La seconde la sauve-t-elle ? (d) Que vérifiez-vous avant de dimensionner un MoE ?
:::

::: sol
(a) EP multiplicatif : Mixtral 8x7B, $64 / 32 = 2$ ; Mixtral 8x22B, $256 / 128 = 2$ ; DeepSeek-V3, $1024 / 2048 = 0{,}5$. EP dans les rangs de données (diviser par TP × PP × CP seulement) : $64 / 4 = 16$ ; $256 / 16 = 16$ ; $1024 / 32 = 32$.

(b) **DeepSeek-V3** : un degré de données de 0,5 n'existe pas.

(c) Non. Avec l'EP dans les rangs de données, DeepSeek-V3 a 32 rangs de données pour un EP de 64 : l'EP ne peut pas diviser 32. Les lignes Mixtral passent (8 divise 16). Les deux lectures échouent pour cette ligne.

(d) Une troisième lecture, **non confirmée** dans les sources lues : les couches d'experts utiliseraient un autre découpage que l'attention (par exemple un TP d'experts de 1), de sorte que $1024 / 16 = 64$ rangs forment l'EP. Avant de dimensionner un MoE, recalculez le produit sur chaque exemple publié et lisez le code de construction des groupes de votre version ; ne prenez pas un tableau de documentation pour une spécification.
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux décoder une configuration de parallélisme.** Preuve : l'exercice 1 refait sur une configuration publiée de votre choix, avec `mesh.py`.
-   **Je peux lancer un job multi-processus et expliquer ce que `torchrun` fournit.** Preuve : le lab 9.1 et l'exercice 2.
-   **Je peux prédire la mémoire par GPU et la mesurer.** Preuve : le lab 9.2 (mesuré = prédit) et l'exercice 3.
-   **Je peux chiffrer communication, bulle et activations de chaque dimension.** Preuve : les exercices 6, 7, 8 et 13 et le lab 9.4.
-   **Je peux choisir une disposition et dire ce que mon modèle ne voit pas.** Preuve : l'exercice 10 en une page, avec trois candidates, un critère chiffré et une limite du modèle.
-   **Je peux localiser un hang.** Preuve : le lab 9.3 et le tableau « outil contre bug » rempli de votre main.
-   **Je peux séparer un bug de distribution d'une instabilité numérique.** Preuve : l'exercice 12 et un test d'équivalence entre un et plusieurs processus sur vos données.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Notre job de 70 milliards de paramètres sur 64 GPU fait 25 % de MFU. Où cherchez-vous ?* Réponse-type : vérifier la mesure (échauffement, pic dense, tokens utiles), puis décomposer l'étape en secondes : communication exposée, bulle, recalcul, données, optimiseur, retardataires. Comparer aux repères publiés (38 à 43 % pour Llama 3), vérifier que le TP tient dans le nœud et que les rangs sont bien ordonnés, traiter le premier poste par rapport coût-gain.
2.  *Un entraînement à 128 GPU ne progresse plus depuis vingt minutes. Que faites-vous ?* Réponse-type : ne pas redémarrer avant d'avoir l'état de chaque rang (piles Python, journal des collectives ou flight recorder). Chercher si un rang est hors des collectives (chargeur, E/S, nœud défaillant) ou si les rangs sont dans des collectives différentes. Puis reprendre du dernier checkpoint et écrire le test qui reproduit le bug.
3.  *Pourquoi FSDP plutôt que DDP, et quand ajouter du parallélisme tensoriel ?* Réponse-type : les états coûtent 16 octets par paramètre, ce qui interdit DDP au-delà de quelques milliards de paramètres sur 80 Go ; FSDP les partitionne pour 1,5 fois le volume de DDP. On ajoute du TP, dans le nœud, quand activations ou matrices par GPU posent problème, sachant qu'il coûte quatre all-reduce par couche et se recouvre mal ; le pipeline prend le relais au-delà du nœud.

## Lectures et références {#refs}

-   Narayanan, Shoeybi, Casper et al. *Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM*. 2021. [arXiv:2104.04473](https://arxiv.org/abs/2104.04473) : sections 2 et 3 (tenseur, pipeline, bulle, trois enseignements), tableau 1.
-   Rajbhandari, Rasley, Ruwase, He. *ZeRO: Memory Optimizations Toward Training Trillion Parameter Models*. 2020. [arXiv:1910.02054](https://arxiv.org/abs/1910.02054) : figure 1 et section 7 (volume de communication).
-   Zhao et al. *PyTorch FSDP: Experiences on Scaling Fully Sharded Data Parallel*. 2023. [arXiv:2304.11277](https://arxiv.org/abs/2304.11277) : conception de FSDP et coût mémoire.
-   Korthikanti et al. *Reducing Activation Recomputation in Large Transformer Models*. 2022. [arXiv:2205.05198](https://arxiv.org/abs/2205.05198) : tableaux 2 et 4, équation 5.
-   Dubey et al. *The Llama 3 Herd of Models*. 2024. [arXiv:2407.21783](https://arxiv.org/abs/2407.21783) : tableau 4, sections 3.3.2 à 3.3.4 (grille 4D, stabilité numérique, flight recorder).
-   Chowdhery et al. *PaLM: Scaling Language Modeling with Pathways*. 2022. [arXiv:2204.02311](https://arxiv.org/abs/2204.02311) : pics de perte, reproductibilité bit à bit.
-   Tazi, Mom, Zhao, Nguyen, Mekkouri, von Werra, Wolf. *The Ultra-Scale Playbook: Training LLMs on GPU Clusters*. 2025. [version statique](https://nanotron-ultrascale-playbook.static.hf.space/index.html) : procédure de choix, TP, experts.
-   Austin et al. *How to Scale Your Model*. 2025. [chapitre Training](https://jax-ml.github.io/scaling-book/training/) : seuils de lot par puce (TPU).
-   PyTorch. *torchrun (Elastic Launch)*, documentation 2.14. [docs.pytorch.org](https://docs.pytorch.org/docs/2.14/elastic/run.html) : variables d'environnement, rendez-vous, redémarrages.
-   PyTorch. *DistributedDataParallel*, documentation 2.14 : [API](https://docs.pytorch.org/docs/2.14/generated/torch.nn.parallel.DistributedDataParallel.html) et [notes](https://docs.pytorch.org/docs/2.14/notes/ddp.html) : seaux, crochets, paramètres inutilisés.
-   PyTorch. *FSDP2 (`fully_shard`)*, documentation 2.14. [docs.pytorch.org](https://docs.pytorch.org/docs/2.14/distributed.fsdp.fully_shard.html) : groupes, `reshard_after_forward`, préchargement.
-   PyTorch. *torch.distributed* ([documentation 2.14](https://docs.pytorch.org/docs/2.14/distributed.html)) et [tutoriel Flight Recorder](https://docs.pytorch.org/tutorials/unstable/flight_recorder_tutorial.html) : délais, `TORCH_DISTRIBUTED_DEBUG`, `monitored_barrier`.
-   PyTorch. *Reproducibility*, documentation 2.14. [docs.pytorch.org](https://docs.pytorch.org/docs/2.14/notes/randomness.html) : ce que PyTorch garantit ou non.
-   Chen, Xu, Zhang, Guestrin. *Training Deep Nets with Sublinear Memory Cost*. 2016, [arXiv:1604.06174](https://arxiv.org/abs/1604.06174) ; Huang et al. *GPipe*. 2018, [arXiv:1811.06965](https://arxiv.org/abs/1811.06965) : recalcul d'activations et ordonnancement du pipeline.
-   Documentation des outils, lue le 25 octobre 2026 : [Megatron Core](https://docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/parallelism-guide.html), [DeepSpeed ZeRO](https://www.deepspeed.ai/tutorials/zero/) et [configuration](https://www.deepspeed.ai/docs/config-json/), [TorchTitan](https://raw.githubusercontent.com/pytorch/torchtitan/main/README.md), [Accelerate](https://huggingface.co/docs/accelerate/usage_guides/fsdp), [Lightning](https://lightning.ai/docs/pytorch/stable/advanced/model_parallel/fsdp.html) : noms de paramètres, identités de configuration (chapitre 9).

## Sources et portée {#sources}

**Documenté.** Relus le 25 octobre 2026 : la documentation de PyTorch 2.14 (torchrun, DDP et ses notes, `fully_shard`, `torch.distributed`, reproductibilité, tutoriel du flight recorder) ; les articles Megatron-LM (sections 2 et 3, tableau 1), ZeRO (figure 1, section 7), FSDP, Korthikanti et al. (tableaux 2 et 4, équation 5), Llama 3 (tableau 4, sections 3.3.2 à 3.3.4), PaLM, Chen et al., GPipe ; le Playbook et *How to Scale Your Model* ; les documentations de Megatron Core, DeepSpeed, TorchTitan, Accelerate et Lightning. Le comportement des seaux de DDP à la première itération vient du **code source** de PyTorch 2.14.1 installé. Tous les calculs ont été refaits en Python. Les mesures viennent d'une VM de 4 vCPU (PyTorch 2.14.1 CPU, Python 3.13) ; les quatre `verify.sh` ont été exécutés au moins deux fois.

**Recommandé.** L'ordre des chapitres, la quatrième étape « mesurer », la marge de 10 % de mémoire, le seuil de 3 % de l'exercice 10, la règle « la décision de sauter un pas doit être collective » et les exercices sont des choix de ce parcours. Les bandes passantes de 400 et 25 Go/s et le MFU de 40 % des exemples sont des **hypothèses** d'école, jamais des mesures.

**À vérifier.** (1) Rien n'a été exécuté sur GPU ni avec NCCL : commandes du flight recorder, recouvrement réel de DDP et de FSDP2, MFU mesuré sont documentés, pas observés ici. (2) `_get_ddp_logging_data()` est une API privée, et `TORCH_DISTRIBUTED_DEBUG=DETAIL` avec DDP sur `gloo` CPU a planté avec PyTorch 2.14.1 : observation de l'auteur, non investiguée, non signalée en amont. (3) Les surcoûts de recalcul (7 % et 39 %) viennent d'**une** mesure de Korthikanti et al. ; l'approximation de $12h^2$ paramètres par couche est classique mais non sourcée ici. (4) Le tableau du guide de Megatron Core contredit sa propre formule pour DeepSeek-V3 ; la correspondance entre `--use-distributed-optimizer` et ZeRO-1 n'est pas vérifiée. (5) Les formats de configuration de TorchTitan changent vite (le fichier TOML essayé renvoie une erreur 404). (6) Les seuils du Playbook viennent d'expériences sur H100 ; sa page est rendue par JavaScript, nous avons lu sa version statique. (7) Aucun outil du chapitre 9 n'est installé : les fichiers de `configs/` sont analysés, jamais exécutés.

**Hors périmètre.** La programmation des noyaux (module 4), le réglage de NCCL et la topologie réseau (module 7), la tolérance aux pannes et le checkpointing distribué (module 10), l'apprentissage par renforcement et Ray (module 11), le parallélisme pour l'inférence, le détail du FP8, ZeRO-Infinity et le déchargement vers CPU ou NVMe, le routage des modèles à experts, les ordonnancements de pipeline sans bulle, l'attention en anneau et `torch.compile`.
