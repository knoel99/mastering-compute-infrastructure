---
title: "Architecture matérielle et modèles de performance"
subtitle: "Module 02 · Phase 0 · 24 h"
description: "Prédire avant de mesurer : hiérarchie mémoire, roofline, lois d'Amdahl et de Gustafson, modèle α-β des communications et MFU."
module:
  id: perf-models
  number: 2
  phase: 0
  hours: 24
  level: 1
prerequisites: []
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs vérifiés dans un bac à sable", class: verified}
labs:
  - {id: stream-gemm, kind: sandbox}
  - {id: allreduce-model, kind: sandbox}
  - {id: mfu-calculator, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** avant de lancer un job sur 64 GPU, pouvez-vous dire combien de temps il devrait durer, et pourquoi il durera plus longtemps ? Un ingénieur d'infrastructure qui ne sait pas répondre dépend de la bonne volonté des chercheurs pour savoir si son cluster fonctionne correctement.

Ce module vous donne cinq outils de raisonnement : la hiérarchie mémoire, le modèle *roofline*, les lois d'Amdahl et de Gustafson, le modèle de communication α-β et le MFU (*model FLOPs utilization*). Il vous donne surtout la discipline de les confronter à des mesures.

Tout le reste du parcours en dépend. Dimensionner un réseau (module 7), choisir un parallélisme (module 9) ou chiffrer un achat de GPU (module 15) revient à poser un modèle, à le mesurer, puis à expliquer l'écart.

::: key
[Règle de ce module]{.tag} Un modèle n'est jamais « vrai » : il est utile tant que l'écart avec la mesure reste expliqué. Un écart inexpliqué est le signal qu'il faut chercher, pas un échec du modèle.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 24 h, dont environ 10 h de lecture, 8 h de labs et 6 h d'exercices |
| Niveau d'entrée | 1 : algèbre de lycée, Python de base, notion de processus |
| Prérequis | aucun |
| Pour qui | Cœur pour tous : c'est la grammaire commune du parcours (roofline, modèle α-β, MFU). |
| Livrable | un rapport de mesure reproductible (lab 2.1 à 2.3) et le calculateur de MFU testé |
| Environnement | un portable CPU suffit ; aucun GPU requis. La variante GPU de chaque lab est décrite en « Pour aller plus loin » |
| Projets liés | [Projet 2 — Étude de passage à l'échelle](../../projects/scaling-study/index.html), [Projet 6 — RFC de plateforme](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Calculer l'intensité arithmétique d'un noyau et le situer sur un roofline, puis dire s'il est limité par le calcul ou par la mémoire (chapitres 1, 2 et 4).
-   Lire une fiche technique de GPU sans confondre les chiffres « avec sparsité » et les chiffres denses (chapitre 2).
-   Prédire le gain maximal d'une parallélisation avec Amdahl et Gustafson, et estimer la part séquentielle à partir de mesures (chapitre 5).
-   Estimer le temps d'un all-reduce avec le modèle α-β, ajuster α et la bande passante sur des mesures, et comparer anneau et arbre (chapitre 6).
-   Calculer les FLOP d'un entraînement de transformeur et son MFU, et repérer un MFU mal calculé (chapitre 7).
-   Planifier une étude de passage à l'échelle dont les conclusions résistent à la critique (chapitre 8).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 0 — Fondations : machines et performance** (semaines 1-5) : lire une machine et prédire sa performance avant de la mesurer.
-   **S'appuie sur** : aucun module ; c'est un point d'entrée.
-   **Prépare** : [module 3 — Programmation parallèle : OpenMP, MPI et études de passage à l'échelle](../parallel-programming/index.html), [module 4 — Programmation GPU : CUDA, Triton et profilage](../gpu-programming/index.html), [module 7 — Réseaux haute performance : InfiniBand, RoCE et NCCL](../networking/index.html), [module 9 — Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline](../distributed-training/index.html), [module 15 — FinOps, capacité, énergie et achats de calcul](../finops-capacity/index.html).
-   **Projets qui s'en servent** : [Projet 2 — Étude de passage à l'échelle d'un entraînement](../../projects/scaling-study/index.html).
<!-- /gen:place -->

### Plan de séances {#seances}

Huit séances de 3 h, soit 24 h. Le niveau 1 correspond aux fondations, le niveau 2 aux méthodes de cœur, le niveau 3 à l'avancé. Il ne diminue jamais d'une séance à la suivante.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 3 h | 1 | ch. 1 Du transistor au nœud | Ex. 1 ; questions de positionnement |
| 2 | 3 h | 1 | ch. 2 Le GPU, machine à débit | Ex. 2, 3 ; lab 2.1 (installation, partie STREAM) |
| 3 | 3 h | 1 | ch. 3 Mesurer proprement | Lab 2.1 (partie GEMM), premières mesures |
| 4 | 3 h | 2 | ch. 4 Le modèle roofline | Ex. 4, 5 ; lab 2.1 (tracé du roofline) |
| 5 | 3 h | 2 | ch. 5 Amdahl, Gustafson, efficacité | Ex. 6 ; lab 2.2 (étapes 1 et 2 : lecture du code, mesures) |
| 6 | 3 h | 2 | ch. 6 Le modèle α-β et les collectives | Ex. 7, 8 ; lab 2.2 (étapes 3 à 5 : ajustement, analyse) |
| 7 | 3 h | 2 | ch. 7 FLOP, MFU et mémoire d'un entraînement | Ex. 9, 10 ; lab 2.3 (étapes 1 à 3) |
| 8 | 3 h | 3 | ch. 8 Études de passage à l'échelle ; checkpoint de sortie | Ex. 11 ; lab 2.3 (étapes 4 et 5) ; démarrage du Projet 2 |

<!-- gen:travailler -->
### Comment travailler ce module {#travailler}

Le parcours s'adresse à plusieurs profils d'entrée, décrits dans le [point de départ](../../profile/index.html). Le tableau donne la priorité conseillée pour ce module ; les questions de positionnement (section 0.1) la confirment ou la corrigent.

| Profil d'entrée | Priorité | Ce que cela veut dire ici |
|---|---|---|
| Ingénieur plateforme, SRE ou DevOps | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Administrateur ou ingénieur HPC | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Ingénieur ML ou chercheur | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Développeur logiciel ou systèmes | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Étudiant ou personne en reconversion | à fond | tous les chapitres, tous les labs et les exercices ★★★ |

**À ne pas survoler.** Le roofline, le modèle α-β et le MFU reviennent dans les modules 3, 4, 7, 9 et 15 : ne les survolez pas, même si les formules vous sont familières.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le checkpoint de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si les trois vous paraissent routinières, parcourez les exercices ★★★ et passez directement au module suivant.

1.  **Mémoire ou calcul.** Un noyau lit deux vecteurs de $2^{30}$ nombres FP32 et écrit leur somme dans un troisième. Combien d'octets traversent le lien mémoire, combien d'opérations flottantes sont faites, et ce noyau est-il plutôt limité par le calcul ou par la mémoire ?

2.  **Part séquentielle.** Un programme passe 5 % de son temps dans une partie strictement séquentielle. Quel gain maximal pouvez-vous espérer avec 1 000 cœurs ? Avec une infinité de cœurs ?

3.  **Données échangées.** Un all-reduce de 1 Gio sur 8 GPU prend 75 ms. Quelle quantité de données chaque GPU doit-il au minimum émettre ? Pourquoi n'est-ce pas simplement 1 Gio ?

::: sol
**Réponses.**

1.  Chaque vecteur occupe $4 \times 2^{30}$ octets, soit 4 Gio. Le noyau lit 8 Gio et écrit 4 Gio : 12 Gio de trafic pour $2^{30}$ additions. L'intensité arithmétique vaut $1/12 \approx 0{,}083$ FLOP par octet, très en dessous de ce que demande n'importe quel processeur moderne pour être limité par le calcul. Le noyau est limité par la mémoire. Voir le chapitre 4.

2.  Avec $f = 0{,}95$ de part parallélisable, $S(1000) = 1/(0{,}05 + 0{,}95/1000) \approx 19{,}6$. Avec une infinité de cœurs, la limite est $1/0{,}05 = 20$. Au-delà de quelques centaines de cœurs, ajouter des cœurs ne rapporte presque plus rien ($S(100) \approx 16{,}8$). Voir le chapitre 5.

3.  Dans un all-reduce en anneau, chaque rang émet $2\,\frac{p-1}{p}\,n$ octets, soit $2 \times 7/8 \times 1 = 1{,}75$ Gio pour $p=8$. Ce n'est pas 1 Gio parce que l'opération se fait en deux phases : un *reduce-scatter* puis un *all-gather*, qui émettent chacune $\frac{p-1}{p}\,n$. Cette quantité est aussi une borne inférieure : sans compression des données, au moins un rang doit émettre autant (Patarasuk et Yuan, 2009), et l'anneau l'atteint pour tous les rangs. Voir le chapitre 6.
:::

## 1. Du transistor au nœud : ce que le logiciel voit de la machine {#ch1}

Ce chapitre fixe le vocabulaire. Vous n'avez pas besoin de savoir dessiner un processeur ; vous avez besoin de savoir quelles grandeurs limitent un programme, et comment les relier entre elles.

### 1.1. Quatre grandeurs

Quatre grandeurs suffisent à décrire presque tout ce que le matériel impose à un programme.

-   **Le débit de calcul** $P$, en opérations flottantes par seconde (FLOP/s), pour une précision donnée.
-   **La bande passante** $B$, en octets par seconde, entre deux niveaux de la machine : mémoire principale et processeur, GPU et réseau, nœud et stockage.
-   **La latence** $\alpha$, en secondes : le temps de premier octet d'un transfert, indépendant de sa taille.
-   **La capacité**, en octets, de chaque niveau de mémoire.

Un transfert de $n$ octets prend donc environ $\alpha + n/B$ secondes. Cette formule, que nous retrouverons au chapitre 6, est la plus utile de tout le module : elle sépare ce qui coûte *par message* de ce qui coûte *par octet*.

### 1.2. La hiérarchie mémoire

Plus une mémoire est proche des unités de calcul, plus elle est rapide et plus elle est petite. Le tableau donne les ordres de grandeur d'un serveur récent.

| Niveau | Capacité typique | Latence typique | Ce qu'il faut en retenir |
|---|---|---|---|
| Registres | de quelques centaines d'octets à quelques Kio par cœur | moins d'1 ns | gratuits, mais en nombre fixe |
| Cache L1 | quelques dizaines de Kio par cœur | environ 1 ns | privé à chaque cœur |
| Cache L2 | de 0,5 à 2 Mio par cœur | quelques ns | privé ou partagé par un petit groupe |
| Cache L3 | de dizaines à centaines de Mio par socket | de 10 à 40 ns | partagé ; souvent découpé en tranches |
| Mémoire principale (DRAM) | de centaines de Gio à plusieurs Tio | de 70 à 120 ns | un à deux ordres de grandeur plus lente que les caches |
| Stockage NVMe local | de To à dizaines de To | de dizaines à centaines de µs | de l'ordre de cent à mille fois la DRAM |

::: note
[Des ordres de grandeur, pas des garanties]{.tag} Ces plages varient d'un facteur 2 à 3 entre générations et constructeurs. Elles servent à raisonner sur les rapports (la DRAM est cent fois plus lente qu'un cache L1), pas à prédire un chiffre. Le lab 2.1 mesure la bande passante de *votre* machine : c'est elle qui compte.
:::

Un programme qui réutilise ses données dans les caches se rapproche du pic de calcul ; un programme qui lit des données une seule fois est condamné à la bande passante de la mémoire principale. Cette distinction, la **réutilisation des données**, gouverne tout le chapitre 4.

### 1.3. Le pic de calcul d'un processeur

Le pic d'un processeur se calcule en multipliant trois facteurs :

$$P_{\text{pic}} = n_{\text{cœurs}} \times f_{\text{horloge}} \times \text{FLOP par cycle et par cœur}$$

Les FLOP par cycle dépendent des unités vectorielles. Un cœur muni de deux unités *fused multiply-add* (FMA) de 8 voies FP32 réalise $2 \times 8 \times 2 = 32$ FLOP par cycle : 8 voies, 2 opérations par FMA (une multiplication et une addition), 2 unités.

::: ex
[Exemple 1.1 — Pic et équilibre d'un processeur d'exemple]{.tag} Soit un processeur de 32 cœurs à 2,5 GHz avec 32 FLOP FP32 par cycle. Son pic vaut $32 \times 2{,}5 \cdot 10^9 \times 32 = 2{,}56 \cdot 10^{12}$ FLOP/s, soit 2,56 TFLOP/s. Si sa mémoire délivre 200 Go/s, son **équilibre machine** (*machine balance*), c'est-à-dire le rapport pic sur bande passante, vaut $2{,}56 \cdot 10^{12} / (200 \cdot 10^{9}) = 12{,}8$ FLOP par octet.

Ces valeurs sont des hypothèses d'exemple, pas celles d'un produit précis. Elles montrent comment un fabricant publie un pic et pourquoi ce pic n'est atteint que par des noyaux qui réutilisent massivement leurs données.
:::

L'équilibre machine est le chiffre à retenir de ce paragraphe. Il dit combien d'opérations il faut effectuer sur chaque octet lu pour que le calcul, et non la mémoire, devienne le facteur limitant.

### 1.4. Le nœud complet

Un nœud de calcul réunit plusieurs processeurs, chacun avec ses canaux mémoire. L'accès à la mémoire d'un autre socket coûte plus cher : c'est l'accès mémoire non uniforme, ou **NUMA**. Les GPU sont reliés au processeur par PCIe, ou par un lien spécifique sur certaines architectures, et les cartes réseau sont rattachées à l'un des sockets.

Pour un exploitant de cluster, la conséquence est concrète : un GPU qui communique avec une carte réseau rattachée à l'autre socket paie un détour. Le module 1 montre comment lire cette topologie ; le module 7 montre ce que NCCL en fait.

::: recap
Points clés — chapitre 1

-   Quatre grandeurs : débit de calcul, bande passante, latence, capacité.
-   Un transfert coûte $\alpha + n/B$ : un terme par message, un terme par octet.
-   Le pic d'un processeur est le produit des cœurs, de l'horloge et des FLOP par cycle.
-   L'équilibre machine (pic divisé par bande passante) dit combien d'opérations par octet il faut pour être limité par le calcul.
-   Les chiffres de capacité et de latence sont des ordres de grandeur : mesurez votre machine.
:::

## 2. Le GPU, machine à débit {#ch2}

Un GPU sacrifie la latence au profit du débit. Là où un cœur de processeur est conçu pour exécuter vite une suite d'instructions, un GPU est conçu pour exécuter une quantité énorme de calculs indépendants en même temps.

### 2.1. Une architecture pour le parallélisme massif

Un GPU NVIDIA est composé de dizaines à centaines de **multiprocesseurs de flux** (*streaming multiprocessors*, SM). Le blog d'architecture de NVIDIA indique 132 SM pour le H100 SXM5 contre 108 pour l'A100. Chaque SM exécute des **warps** de 32 threads qui avancent ensemble.

Quand un warp attend une donnée en mémoire, le SM bascule sur un autre warp prêt. La latence mémoire n'est pas réduite, elle est **masquée** par la quantité de travail disponible. C'est la raison pour laquelle un GPU exige des problèmes assez gros : avec trop peu de threads, la latence redevient visible et le GPU reste inactif.

La mémoire du GPU est de la **HBM** (*high bandwidth memory*), empilée à côté de la puce. Elle offre des bandes passantes de plusieurs To/s, pour une capacité de quelques dizaines de Gio. Les **cœurs tensoriels** réalisent le produit de petites matrices en une seule instruction ; ce sont eux qui fournissent l'essentiel du pic annoncé pour l'IA. Les GPU d'un même nœud communiquent entre eux par **NVLink**, un lien propre à NVIDIA dont la bande passante est, pour le H100, d'environ sept fois celle du PCIe de 5e génération d'après le [blog Hopper](https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth/).

### 2.2. Lire une fiche technique

Voici les chiffres que la page produit de NVIDIA publie pour le H100 SXM (consultée le 22 octobre 2026).

| Grandeur | H100 SXM |
|---|---|
| Mémoire GPU | 80 Go |
| Bande passante mémoire | 3,35 To/s |
| Bande passante NVLink | 900 Go/s |
| TF32, cœurs tensoriels | 989 TFLOPS (avec sparsité) |
| BF16 / FP16, cœurs tensoriels | 1 979 TFLOPS (avec sparsité) |
| FP8, cœurs tensoriels | 3 958 TFLOPS (avec sparsité) |
| Puissance maximale | jusqu'à 700 W |

::: war
[Le piège du chiffre « avec sparsité »]{.tag} Les trois lignes de cœurs tensoriels portent la note « *with sparsity* » sur la [page produit](https://www.nvidia.com/en-us/data-center/h100/). Elles supposent l'activation de la sparsité structurée des cœurs tensoriels, qui double leur débit annoncé mais qu'un calcul dense standard n'utilise pas. Le pic **dense** est la moitié, soit environ 989 TFLOPS en BF16.

Le [blog Hopper](https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth/) de NVIDIA présente d'ailleurs, sur des spécifications préliminaires, 1 000 TFLOPS en dense et 2 000 avec sparsité. Les 430 TFLOPs par GPU du tableau 4 de l'[article Llama 3](https://arxiv.org/abs/2407.21783) correspondent à 43 % du pic dense, ce qui est cohérent. Diviser une mesure par le chiffre « avec sparsité » fait paraître le matériel deux fois moins bien utilisé qu'il ne l'est.
:::

Les trois précisions suivent un rapport de 1 à 2 à 4 : TF32, puis BF16, puis FP8 doublent à chaque fois le débit annoncé. Choisir une précision plus basse double donc le pic, mais pas nécessairement la performance mesurée : le chapitre 4 explique pourquoi.

### 2.3. CPU et GPU face à face

| | Processeur serveur | GPU de centre de données |
|---|---|---|
| Objectif de conception | faible latence d'un fil d'exécution | débit global sur un grand nombre de fils |
| Pic de calcul | quelques TFLOP/s en FP32 | centaines de TFLOP/s avec cœurs tensoriels |
| Bande passante mémoire | centaines de Go/s | plusieurs To/s |
| Capacité mémoire | centaines de Gio à Tio | de dizaines à quelques centaines de Gio |
| Équilibre machine | de l'ordre de 10 FLOP/octet (exemple 1.1) | de 200 à 300 FLOP/octet en BF16 dense |

Dans cet exemple, le GPU offre environ 390 fois plus de pic de calcul (989 contre 2,56 TFLOP/s, précisions différentes) pour environ 17 fois plus de bande passante (3,35 To/s contre 200 Go/s). Son équilibre machine est donc bien plus élevé : il faut **beaucoup plus de réutilisation de données** pour l'alimenter.

::: ex
[Exemple 2.1 — L'équilibre machine du H100 et de l'A100]{.tag} Pour le H100 SXM, 989 TFLOP/s en BF16 dense et 3,35 To/s donnent $989 \cdot 10^{12} / (3{,}35 \cdot 10^{12}) \approx 295$ FLOP par octet. Pour l'A100 de 40 Go (312 TFLOPS en BF16 dense, 1 555 Go/s selon le blog Hopper), on trouve environ 201 FLOP par octet.

En passant de l'A100 au H100, le pic de calcul est multiplié par 3,2 mais la bande passante seulement par 2,2 : l'équilibre machine monte de 201 à 295 FLOP par octet. Chaque génération de GPU rend donc davantage de noyaux limités par la mémoire.
:::

::: recap
Points clés — chapitre 2

-   Un GPU masque la latence par le nombre de warps disponibles ; il lui faut des problèmes assez grands.
-   Les chiffres de précision basse (TF32, BF16, FP8) doublent à chaque marche, mais la fiche « avec sparsité » double encore une fois le pic réaliste.
-   Le pic dense BF16 du H100 SXM est d'environ 989 TFLOPS ; son équilibre machine, d'environ 295 FLOP par octet.
-   L'écart entre le pic de calcul et la bande passante se creuse à chaque génération.
:::

## 3. Mesurer proprement {#ch3}

Un modèle de performance ne vaut que par les mesures qui le contredisent ou le confirment. Mesurer mal est plus dangereux que ne pas mesurer : une mauvaise mesure donne une fausse confiance.

### 3.1. Les règles de base

Cinq règles évitent la majorité des erreurs.

1.  **Chauffer avant de mesurer.** Les premières exécutions paient le chargement des caches, la compilation à la volée et la montée en fréquence. Jetez-les.
2.  **Répéter.** Une mesure isolée n'a pas de sens ; sept à vingt répétitions donnent une distribution.
3.  **Choisir son estimateur.** Le *minimum* estime ce dont la machine est capable, car le bruit ne peut que ralentir ; la *médiane* estime ce qu'un utilisateur obtient typiquement. Annoncez lequel vous utilisez.
4.  **Contrôler l'environnement.** Nombre de threads, affinité, fréquence du processeur, autres charges sur la machine : notez-les, ou fixez-les.
5.  **Mesurer ce qu'on croit mesurer.** Sur un GPU, les appels sont asynchrones : sans synchronisation avant l'arrêt du chronomètre, vous mesurez le temps de lancement, pas d'exécution.

### 3.2. Deux benchmarks de référence

Le benchmark **STREAM**, créé par John McCalpin, mesure la bande passante mémoire soutenue avec des noyaux élémentaires comme la copie ($a = b$) et l'addition ($a = b + c$). Les tableaux doivent être beaucoup plus grands que le dernier niveau de cache, sinon vous mesurez le cache : le code source de référence (`stream.c`) demande des tableaux d'au moins quatre fois la taille du cache disponible.

Le **produit de matrices** (GEMM) mesure l'autre extrémité : un noyau très réutilisateur, qui approche le pic de calcul quand il est bien implémenté. La copie donne la bande passante, le GEMM donne le pic. Entre les deux, tous les autres programmes.

::: ex
[Exemple 3.1 — Compter honnêtement les octets de STREAM]{.tag} Pour l'addition $a = b + c$ en double précision, chaque élément implique deux lectures de 8 octets et une écriture de 8 octets : **24 octets par élément**. Pour la copie, 16 octets. Le lab 2.1 applique exactement ces comptes. Une bande passante calculée avec un mauvais compte d'octets est fausse d'un facteur 1,5.
:::

### 3.3. Rapporter honnêtement

Hoefler et Belli ont examiné 120 articles de trois grandes conférences de calcul haute performance et ont trouvé des pratiques de mesure insuffisantes, ce qui rend parfois impossible de savoir si un gain annoncé est réel. Ils en tirent des règles que nous reprendrons au chapitre 8 : intervalles de confiance, conditions expérimentales publiées, pas de moyenne arithmétique des rapports.

Pour l'instant, retenez une habitude : toute mesure que vous rapportez s'accompagne de la machine, des versions logicielles, du nombre de répétitions et de l'estimateur choisi.

::: recap
Points clés — chapitre 3

-   Chauffer, répéter, choisir et annoncer l'estimateur (minimum ou médiane), contrôler l'environnement.
-   STREAM mesure la bande passante, le GEMM mesure le pic : ensemble ils bornent votre machine.
-   Comptez les octets de chaque noyau ; une erreur de compte fausse la bande passante.
-   Sur GPU, synchronisez avant d'arrêter le chronomètre.
:::

## 4. Le modèle roofline {#ch4}

Le modèle *roofline*, proposé par Williams, Waterman et Patterson, répond à une question simple : étant donné une machine et un noyau, quelle performance peut-on au mieux espérer ? Sa force est de tenir sur un seul graphique.

### 4.1. Intensité arithmétique

L'**intensité arithmétique** $I$ d'un noyau est le nombre d'opérations flottantes qu'il effectue par octet échangé avec la mémoire principale :

$$I = \frac{\text{FLOP effectués}}{\text{octets transférés depuis et vers la mémoire}}$$

Elle ne dépend que de l'algorithme et de la taille du problème, pas de la machine. Le dénominateur compte le trafic **minimal** : chaque donnée lue ou écrite une seule fois, ce qui suppose une réutilisation parfaite des caches. C'est une borne optimiste sur $I$.

### 4.2. Les deux toits

Deux limites bornent la performance atteignable : le pic de calcul $P_{\text{pic}}$ et la bande passante $B$ multipliée par l'intensité. La performance atteignable est le minimum des deux :

$$P_{\text{atteignable}}(I) = \min\bigl(P_{\text{pic}},\; I \times B\bigr)$$

Sur un graphique à échelles logarithmiques, cela donne une pente (le toit mémoire) suivie d'un plateau (le toit de calcul). Le point où ils se rejoignent est le **point de rupture** : son abscisse est l'équilibre machine du chapitre 1. À gauche, le noyau est limité par la mémoire ; à droite, par le calcul.

<figure class="fig">
<svg viewBox="0 0 640 360" role="img" aria-labelledby="rf-t rf-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="rf-t">Roofline d'un GPU H100 SXM</title>
<desc id="rf-d">Graphe log-log : la performance atteignable est bornée par la bande passante mémoire à gauche du point de rupture, puis par le pic de calcul à droite. Trois noyaux sont placés.</desc>
<line x1="70.0" y1="20" x2="70.0" y2="300" stroke="currentColor" stroke-opacity=".18"/>
<text x="70.0" y="318" text-anchor="middle" font-size="12" fill="currentColor">10<tspan font-size="9" dy="-5">-1</tspan></text>
<line x1="192.7" y1="20" x2="192.7" y2="300" stroke="currentColor" stroke-opacity=".18"/>
<text x="192.7" y="318" text-anchor="middle" font-size="12" fill="currentColor">10<tspan font-size="9" dy="-5">0</tspan></text>
<line x1="315.5" y1="20" x2="315.5" y2="300" stroke="currentColor" stroke-opacity=".18"/>
<text x="315.5" y="318" text-anchor="middle" font-size="12" fill="currentColor">10<tspan font-size="9" dy="-5">1</tspan></text>
<line x1="438.2" y1="20" x2="438.2" y2="300" stroke="currentColor" stroke-opacity=".18"/>
<text x="438.2" y="318" text-anchor="middle" font-size="12" fill="currentColor">10<tspan font-size="9" dy="-5">2</tspan></text>
<line x1="560.9" y1="20" x2="560.9" y2="300" stroke="currentColor" stroke-opacity=".18"/>
<text x="560.9" y="318" text-anchor="middle" font-size="12" fill="currentColor">10<tspan font-size="9" dy="-5">3</tspan></text>
<line x1="70" y1="300.0" x2="610" y2="300.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="62" y="304.0" text-anchor="end" font-size="12" fill="currentColor">10<tspan font-size="9" dy="-5">11</tspan></text>
<line x1="70" y1="230.0" x2="610" y2="230.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="62" y="234.0" text-anchor="end" font-size="12" fill="currentColor">10<tspan font-size="9" dy="-5">12</tspan></text>
<line x1="70" y1="160.0" x2="610" y2="160.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="62" y="164.0" text-anchor="end" font-size="12" fill="currentColor">10<tspan font-size="9" dy="-5">13</tspan></text>
<line x1="70" y1="90.0" x2="610" y2="90.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="62" y="94.0" text-anchor="end" font-size="12" fill="currentColor">10<tspan font-size="9" dy="-5">14</tspan></text>
<line x1="70" y1="20.0" x2="610" y2="20.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="62" y="24.0" text-anchor="end" font-size="12" fill="currentColor">10<tspan font-size="9" dy="-5">15</tspan></text>
<rect x="70" y="20" width="540" height="280" fill="none" stroke="currentColor" stroke-width="1.5"/>
<polyline points="70.0,263.2 495.9,20.3 610.0,20.3" fill="none" stroke="var(--accent)" stroke-width="3.5"/>
<line x1="495.9" y1="20.3" x2="495.9" y2="300" stroke="var(--accent)" stroke-dasharray="5 4" stroke-width="1.5"/>
<text x="489.9" y="292" text-anchor="end" font-size="12" fill="currentColor">point de rupture ≈ 295 FLOP/octet</text>
<text x="78.0" y="233.2" font-size="12" fill="currentColor" transform="rotate(-27 78.0 233.2)">limite mémoire : 3,35 To/s</text>
<text x="487.9" y="12.3" text-anchor="end" font-size="12" fill="currentColor">limite calcul : 989 TFLOP/s (BF16 dense)</text>
<circle cx="60.3" cy="268.8" r="5.5" fill="var(--key-bar)" stroke="currentColor" stroke-width="1"/>
<text x="70.3" y="286.8" text-anchor="start" font-size="12" font-weight="700" fill="currentColor">addition de vecteurs</text>
<circle cx="429.7" cy="58.1" r="5.5" fill="var(--key-bar)" stroke="currentColor" stroke-width="1"/>
<text x="419.7" y="78.1" text-anchor="end" font-size="12" font-weight="700" fill="currentColor">GEMM n=256</text>
<circle cx="577.5" cy="20.3" r="5.5" fill="var(--key-bar)" stroke="currentColor" stroke-width="1"/>
<text x="567.5" y="42.3" text-anchor="end" font-size="12" font-weight="700" fill="currentColor">GEMM n=4096</text>
<text x="340.0" y="352" text-anchor="middle" font-size="13" fill="currentColor">intensité arithmétique (FLOP par octet de trafic mémoire)</text>
<text x="14" y="160.0" text-anchor="middle" font-size="13" fill="currentColor" transform="rotate(-90 14 160.0)">performance (FLOP/s)</text>
</svg>
<figcaption>Roofline d'un H100 SXM construit avec les valeurs de la page produit NVIDIA (pic dense BF16 de 989 TFLOP/s, bande passante de 3,35 To/s). Les trois points sont les noyaux des exemples 4.1 à 4.3.</figcaption>
</figure>

### 4.3. Quatre exemples sur le H100

::: ex
[Exemple 4.1 — Addition de vecteurs : limitée par la mémoire]{.tag} En FP32, $c = a + b$ lit 8 octets et en écrit 4 par élément, pour une addition : $I = 1/12 \approx 0{,}083$ FLOP par octet. Sur le H100, la performance atteignable est $0{,}083 \times 3{,}35 \cdot 10^{12} \approx 279$ GFLOP/s, soit 0,028 % du pic de 989 TFLOP/s. Aucune optimisation du calcul n'y changera rien : seul le trafic mémoire compte.

Précision : 989 TFLOP/s est le pic des cœurs tensoriels en BF16, dont une addition FP32 ne se sert pas. Son toit de calcul réel est le pic FP32 hors cœurs tensoriels (67 TFLOPS d'après la [page produit](https://www.nvidia.com/en-us/data-center/h100/)). La conclusion ne change pas : 279 GFLOP/s sont très loin des deux.
:::

::: ex
[Exemple 4.2 — GEMM carré en BF16]{.tag} Un produit de deux matrices $n \times n$ réalise $2n^3$ FLOP. Son trafic minimal est de $3n^2$ éléments de 2 octets : deux matrices lues, une écrite. L'intensité vaut donc $I = 2n^3/(6n^2) = n/3$ FLOP par octet. Elle croît avec $n$ : plus le problème est grand, plus chaque octet est réutilisé.
:::

La comparaison avec le point de rupture donne le résultat important. Pour atteindre 295 FLOP par octet, il faut $n/3 \geq 295$, soit $n \geq 886$ environ.

::: ex
[Exemple 4.3 — Un petit GEMM n'atteint pas le pic]{.tag} Pour $n = 256$, $I = 85$ FLOP par octet, inférieur au point de rupture : le toit mémoire donne $85 \times 3{,}35 \cdot 10^{12} \approx 286$ TFLOP/s, soit 29 % du pic. Pour $n = 4096$, $I \approx 1365$ : le noyau est à droite du point de rupture et peut espérer le pic de 989 TFLOP/s. **Un GPU est mal utilisé par les petits produits de matrices**, quel que soit le soin apporté au noyau.
:::

::: ex
[Exemple 4.4 — La génération de texte token par token]{.tag} Multiplier une matrice $d \times d$ par un seul vecteur (un produit matrice-vecteur) fait $2d^2$ FLOP en lisant $d^2$ coefficients de 2 octets : $I \approx 1$ FLOP par octet. La performance atteignable est de l'ordre de 3,35 TFLOP/s, soit 0,34 % du pic. C'est pourquoi la génération d'un token à la fois est limitée par la bande passante de la mémoire, et pourquoi regrouper des requêtes (augmenter le lot) est le levier principal.
:::

### 4.4. Limites du modèle

Le roofline est un **modèle optimiste** : il donne une borne supérieure, jamais une prédiction. Quatre limites doivent rester en tête.

-   Le trafic minimal suppose une réutilisation parfaite ; un noyau mal écrit lit plusieurs fois les mêmes données.
-   Il ignore la latence et les coûts fixes : lancer un noyau coûte quelques microsecondes, ce qui domine pour les très petits calculs.
-   Il suppose un seul goulot ; un programme réel mélange phases limitées par le calcul et phases limitées par la mémoire.
-   Le pic suppose que toutes les unités sont utilisées : un code sans FMA ou sans cœurs tensoriels a un toit de calcul plus bas.

### 4.5. Utiliser le roofline en pratique

La démarche est toujours la même. On mesure le temps et on compte les FLOP et les octets du noyau, ce qui donne un point $(I, P_{\text{mesurée}})$. On le compare à la droite : s'il est proche d'un toit, on a atteint la limite de la machine pour ce noyau, et il faut changer d'algorithme ; s'il en est loin, un défaut d'implémentation reste à trouver.

Le lab 2.1 construit **votre** roofline à partir de mesures sur votre machine, plutôt qu'à partir d'une fiche technique.

::: recap
Points clés — chapitre 4

-   Intensité arithmétique : FLOP par octet de trafic mémoire minimal ; elle ne dépend que du noyau.
-   Performance atteignable : $\min(P_{\text{pic}}, I \times B)$ ; le point de rupture est l'équilibre machine.
-   Un GEMM $n \times n$ en BF16 a $I = n/3$ ; sur H100 il faut $n \gtrsim 886$ pour dépasser le point de rupture.
-   Les opérations élémentaires et les produits matrice-vecteur sont limités par la mémoire ; fusionner les opérations et grossir les lots sont les leviers.
-   Le roofline est une borne optimiste, jamais une prédiction.
:::

## 5. Amdahl, Gustafson et l'efficacité parallèle {#ch5}

Le roofline dit ce qu'un seul noyau peut espérer. Ce chapitre répond à une autre question : que se passe-t-il quand on ajoute des processeurs ?

### 5.1. La loi d'Amdahl

Gene Amdahl a observé en 1967 qu'une partie séquentielle limite le gain de toute parallélisation. Si une fraction $f$ du temps d'exécution séquentiel peut être parallélisée parfaitement sur $p$ processeurs, et la fraction $1-f$ ne le peut pas, le gain (le *speedup*) vaut :

$$S(p) = \frac{1}{(1-f) + f/p}$$

Quand $p$ tend vers l'infini, le gain tend vers $1/(1-f)$. Avec 5 % de séquentiel, aucun nombre de processeurs ne dépassera 20 fois.

| Part parallélisable $f$ | $S(8)$ | $S(64)$ | $S(1024)$ | Limite |
|---|---|---|---|---|
| 0,90 | 4,71 | 8,77 | 9,91 | 10 |
| 0,95 | 5,93 | 15,42 | 19,64 | 20 |
| 0,99 | 7,48 | 39,26 | 91,18 | 100 |

L'**efficacité parallèle** est le gain divisé par le nombre de processeurs, $E = S/p$. Pour $f = 0{,}95$ et $p = 64$, le gain de 15,4 donne une efficacité de 24 % : les trois quarts des processeurs sont, en moyenne, inutiles.

### 5.2. La loi de Gustafson

John Gustafson a répondu en 1988 qu'on n'exécute pas le même problème sur 1 000 processeurs que sur un seul : on augmente la taille du problème. Si $s$ est la fraction séquentielle du temps d'exécution **sur la machine parallèle**, le gain dit *à l'échelle* vaut :

$$S_{\text{éch}}(p) = s + (1-s)\,p$$

Avec $s = 0{,}05$ et $p = 64$, on obtient 60,85. Les deux lois ne se contredisent pas : elles décrivent deux protocoles différents.

-   **Passage à l'échelle fort** (*strong scaling*) : le problème est fixe, on ajoute des processeurs. Amdahl s'applique. C'est le cas d'un entraînement dont la taille de lot global est fixée.
-   **Passage à l'échelle faible** (*weak scaling*) : le problème grandit avec le nombre de processeurs, par exemple avec une taille de lot par GPU fixe. Gustafson s'applique.

::: key
[Toujours dire quel passage à l'échelle]{.tag} Un graphique de scalabilité sans la mention « fort » ou « faible » est ininterprétable. Un passage à l'échelle faible est presque toujours plus flatteur : méfiez-vous d'une annonce qui ne dit pas lequel des deux elle mesure.
:::

### 5.3. Au-delà de la fraction séquentielle

Dans les systèmes réels, la limite n'est pas seulement une partie séquentielle : ce sont aussi les communications et les déséquilibres. Un modèle plus réaliste ajoute un terme de communication qui croît avec $p$ :

$$T(p) = T_1\,(1-f) + \frac{T_1\,f}{p} + T_{\text{comm}}(p)$$

Pour distinguer une vraie part séquentielle d'un coût qui croît avec $p$, la **métrique de Karp et Flatt** calcule, à partir d'un gain mesuré $S$ sur $p$ processeurs, une fraction séquentielle expérimentale :

$$e(p) = \frac{1/S - 1/p}{1 - 1/p}$$

Si $e$ reste constant quand $p$ augmente, le goulot est une vraie part séquentielle. Si $e$ croît, un coût de parallélisme (communication, synchronisation, déséquilibre) augmente avec $p$.

### 5.4. Les retardataires

Dans un entraînement synchrone, chaque étape attend le rang le plus lent. Si les temps de calcul des rangs sont des variables aléatoires de moyenne $\mu$ et d'écart-type $\sigma$, l'espérance du maximum de $p$ gaussiennes est bornée par $\mu + \sigma\sqrt{2\ln p}$.

Pour $p = 1024$, le facteur $\sqrt{2\ln p}$ vaut 3,72 : avec un écart-type de 2 % de la moyenne, l'étape dure en moyenne jusqu'à 7,4 % de plus que la moyenne des rangs. Un seul GPU légèrement dégradé, un *straggler*, suffit à ralentir tout le job. C'est la raison d'être de la supervision fine du module 14.

::: recap
Points clés — chapitre 5

-   Amdahl : $S(p) = 1/((1-f) + f/p)$ ; la partie séquentielle fixe un plafond de gain à $1/(1-f)$.
-   Gustafson : à problème croissant, le gain à l'échelle est $s + (1-s)\,p$.
-   Toujours préciser passage à l'échelle fort ou faible.
-   Karp-Flatt distingue une part séquentielle constante d'un coût de parallélisme croissant.
-   En synchrone, le rang le plus lent dicte l'étape : la dispersion compte autant que la moyenne.
:::

## 6. Le modèle α-β et les communications collectives {#ch6}

Entraîner sur plusieurs GPU, c'est échanger des gradients à chaque étape. Ce chapitre donne le modèle qui permet de chiffrer ces échanges avant de les mesurer.

### 6.1. Le modèle de Hockney

Roger Hockney a proposé de modéliser le temps d'un message de $n$ octets par une fonction affine :

$$T(n) = \alpha + \frac{n}{B}$$

Le terme $\alpha$ est la **latence** : ce que coûte un message, même vide. Le terme $n/B$ est le **temps de transfert**. Un petit message est dominé par $\alpha$, un gros par $n/B$. La taille qui sépare les deux régimes, atteinte quand le temps de transfert égale la latence, est $n_{1/2} = \alpha B$.

::: ex
[Exemple 6.1 — La taille de demi-performance]{.tag} Avec une latence $\alpha = 5\ \mu$s et une bande passante $B = 25$ Go/s, on obtient $n_{1/2} = 5 \cdot 10^{-6} \times 25 \cdot 10^9 = 125$ ko. En dessous de 125 ko, le débit effectif est inférieur à la moitié de la bande passante nominale. C'est pourquoi les bibliothèques regroupent les petits messages en gros.
:::

### 6.2. Le all-reduce

Dans un **all-reduce**, chacun des $p$ rangs (*ranks* : les processus qui participent à l'opération, en général un par GPU) détient un tableau de $n$ octets ; à la fin, chaque rang détient la somme élément par élément des $p$ tableaux. C'est l'opération centrale de l'entraînement en parallélisme de données : les gradients sont sommés entre les GPU.

Il existe une borne inférieure sur les données à émettre. Patarasuk et Yuan ont montré que, sans compression des données, les rangs doivent émettre en tout au moins $2n\,(p-1)$ octets. Au moins un rang en émet donc $2n\,(p-1)/p$, et l'anneau ci-dessous l'atteint pour chacun d'eux. Quand $p$ est grand, cela tend vers $2n$, **indépendamment de $p$** : c'est ce qui rend l'entraînement en parallélisme de données possible à grande échelle.

### 6.3. L'algorithme en anneau

L'algorithme en anneau atteint cette borne. Les rangs sont disposés en cercle ; le tableau est découpé en $p$ morceaux. La première phase, le *reduce-scatter*, fait circuler les morceaux pendant $p-1$ étapes en les additionnant au passage ; à la fin, chaque rang détient la somme complète d'un morceau. La seconde phase, l'*all-gather*, fait circuler ces sommes pendant $p-1$ étapes.

<figure class="fig">
<svg viewBox="0 0 640 300" role="img" aria-labelledby="ring-t ring-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="ring-t">All-reduce en anneau sur 4 rangs</title>
<desc id="ring-d">Quatre rangs disposés en anneau. Phase 1, reduce-scatter : chaque rang envoie un quart du tableau à son voisin pendant 3 étapes. Phase 2, all-gather : 3 étapes de plus. Au total 2(p-1) = 6 étapes.</desc>
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--accent)"/></marker></defs>
<line x1="341.2" y1="76.2" x2="391.0" y2="126.0" stroke="var(--accent)" stroke-width="3" marker-end="url(#arr)"/>
<line x1="393.8" y1="171.2" x2="344.0" y2="221.0" stroke="var(--accent)" stroke-width="3" marker-end="url(#arr)"/>
<line x1="298.8" y1="223.8" x2="249.0" y2="174.0" stroke="var(--accent)" stroke-width="3" marker-end="url(#arr)"/>
<line x1="246.2" y1="128.8" x2="296.0" y2="79.0" stroke="var(--accent)" stroke-width="3" marker-end="url(#arr)"/>
<circle cx="320" cy="55" r="28" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="320" y="60" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">rang 0</text>
<circle cx="415" cy="150" r="28" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="415" y="155" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">rang 1</text>
<circle cx="320" cy="245" r="28" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="320" y="250" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">rang 2</text>
<circle cx="225" cy="150" r="28" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="225" y="155" text-anchor="middle" font-size="15" font-weight="700" fill="currentColor">rang 3</text>
<text x="320" y="146" text-anchor="middle" font-size="13" fill="currentColor">chaque envoi = n/p octets</text>
<text x="320" y="164" text-anchor="middle" font-size="13" fill="currentColor">6 étapes = 2(p−1)</text>
<text x="18" y="40" font-size="13" font-weight="700" fill="currentColor">Phase 1 · reduce-scatter</text><text x="18" y="58" font-size="13" fill="currentColor">p−1 étapes : somme partielle</text>
<text x="18" y="90" font-size="13" font-weight="700" fill="currentColor">Phase 2 · all-gather</text><text x="18" y="108" font-size="13" fill="currentColor">p−1 étapes : diffusion du résultat</text>
</svg>
<figcaption>All-reduce en anneau sur quatre rangs : un reduce-scatter puis un all-gather, soit 2(p−1) étapes de n/p octets chacune.</figcaption>
</figure>

Chaque étape envoie $n/p$ octets, et il y a $2(p-1)$ étapes. Le temps de l'anneau est donc :

$$T_{\text{anneau}} = 2(p-1)\,\alpha + 2\,\frac{p-1}{p}\,\frac{n}{B}$$

Le premier terme est la latence, qui croît avec $p$ ; le second est le terme de bande passante, qui reste presque constant. L'anneau est excellent pour les gros messages et mauvais pour les petits.

### 6.4. Arbre contre anneau

Un autre algorithme combine les rangs le long d'un arbre binaire puis diffuse le résultat. Dans sa version naïve, il coûte :

$$T_{\text{arbre}} = 2\log_2 p\,\Bigl(\alpha + \frac{n}{B}\Bigr)$$

Il n'a que $\log_2 p$ termes de latence au lieu de $p-1$, mais son terme de bande passante est multiplié par $2\log_2 p$ au lieu de rester constant. L'arbre gagne donc pour les petits messages, l'anneau pour les gros. Les bibliothèques comme NCCL choisissent l'algorithme selon la taille du message et la topologie : vous les verrez agir au module 7.

::: ex
[Exemple 6.2 — Un all-reduce de 1 Gio sur 8 GPU]{.tag} Prenons $p = 8$, $\alpha = 5\ \mu$s et $B = 25$ Go/s. Le temps de l'anneau pour $n = 2^{30}$ octets vaut :

$$T = 14 \times 5\ \mu\text{s} + 2 \times \frac{7}{8} \times \frac{2^{30}}{25 \cdot 10^{9}} \approx 75{,}2\ \text{ms}$$

La latence ne pèse que 0,07 ms ; tout le temps est du transfert. À l'inverse, un message de 1 Kio coûte environ 70 µs, **entièrement de la latence**.

Pour les mêmes paramètres, l'arbre naïf prend 257,7 ms pour 1 Gio (3,4 fois plus) mais 30 µs pour 1 Kio (2,3 fois moins). Le point d'égalité se situe vers 235 ko.
:::

### 6.5. Débit algorithmique et débit de bus

Les outils de mesure comme `nccl-tests` rapportent deux débits. Le **débit algorithmique** (*algbw*) est la taille des données divisée par le temps, $S/t$. Le **débit de bus** (*busbw*) le multiplie par un facteur qui dépend de l'opération, pour obtenir un chiffre comparable à la bande passante matérielle quel que soit le nombre de rangs. Pour un all-reduce, la documentation de `nccl-tests` donne le facteur $2(p-1)/p$.

Dans l'exemple 6.2, le débit algorithmique vaut $2^{30}/0{,}0752 \approx 14{,}3$ Go/s ; le débit de bus vaut $14{,}3 \times 1{,}75 \approx 25$ Go/s, c'est-à-dire, à 0,1 % près, la bande passante $B$ du lien (la latence explique l'écart). Un débit de bus proche de la bande passante nominale signifie que le réseau est saturé : on ne peut plus rien gagner de ce côté.

### 6.6. Recouvrir calcul et communication

Si les gradients d'une couche peuvent être envoyés pendant que la couche précédente calcule encore sa rétropropagation, la communication est cachée derrière le calcul. Au mieux, le temps d'étape vaut le maximum des deux, et non leur somme :

$$T_{\text{étape}} \approx \max\bigl(T_{\text{calcul}},\; T_{\text{comm}}\bigr)$$

Au pire, sans recouvrement, c'est la somme. Les implémentations réelles tombent entre les deux ; mesurer où elles se situent est l'objet du module 9. Le modèle α-β donne seulement la valeur de $T_{\text{comm}}$ à mettre en regard du temps de calcul.

::: note
[Un modèle à deux niveaux]{.tag} Dans un nœud, les GPU communiquent par NVLink (900 Go/s sur H100 SXM d'après la page produit), bien plus vite qu'entre nœuds par le réseau. Un seul couple $(\alpha, B)$ ne suffit alors plus : on utilise un modèle hiérarchique, avec un all-reduce interne puis un all-reduce entre nœuds. Le module 7 détaille cette hiérarchie et ses effets de topologie.
:::

::: recap
Points clés — chapitre 6

-   $T(n) = \alpha + n/B$ : latence par message, transfert par octet ; la taille de demi-performance est $\alpha B$.
-   Un all-reduce exige que les rangs émettent au moins $2n(p-1)$ octets en tout, soit $2n(p-1)/p$ par rang en moyenne, presque indépendamment de $p$.
-   L'anneau est optimal en bande passante mais coûte $2(p-1)$ latences ; l'arbre fait l'inverse.
-   Le débit de bus de `nccl-tests` multiplie le débit algorithmique par $2(p-1)/p$ pour un all-reduce.
-   Le recouvrement fait passer le temps d'étape de la somme au maximum du calcul et de la communication.
:::

## 7. FLOP d'un transformeur, MFU et mémoire d'un entraînement {#ch7}

Le roofline et le modèle α-β décrivent la machine. Il reste à décrire la charge : combien de calcul demande un entraînement de modèle de langage, et quelle part du pic de la machine en fait-il un usage utile ?

### 7.1. Combien de FLOP par token

Pour un transformeur *decoder-only* de $N$ paramètres, l'entraînement d'un token demande environ $6N$ FLOP de produits de matrices : $2N$ pour la passe avant, $4N$ pour la passe arrière. Le calcul de l'attention ajoute un terme qui dépend de la longueur de séquence. L'annexe B de l'article PaLM donne le total par token :

$$F_{\text{token}} = 6N + 12\,L\,H\,Q\,T$$

avec $L$ le nombre de couches, $H$ le nombre de têtes d'attention, $Q$ la dimension d'une tête et $T$ la longueur de séquence.

::: ex
[Exemple 7.1 — Le terme d'attention pèse 15 % à 4 096 tokens]{.tag} Prenons un modèle de 7 milliards de paramètres avec $L = 32$, $H = 32$, $Q = 128$ et $T = 4096$. Le terme principal vaut $6N = 4{,}2 \cdot 10^{10}$ FLOP par token.

Le terme d'attention vaut :

$$12\,L\,H\,Q\,T = 12 \times 32 \times 32 \times 128 \times 4096 \approx 6{,}44 \cdot 10^{9}$$

Il ajoute donc 15,3 % aux FLOP. Il croît avec $T$ : à longue séquence il devient dominant, et l'ignorer sous-estime le travail réel.
:::

### 7.2. MFU et HFU

L'article PaLM définit le **MFU** (*model FLOPs utilization*) comme le rapport entre le débit observé, en tokens par seconde, et le débit théorique maximal d'une machine qui fonctionnerait au pic. Le dénominateur ne compte que les opérations *nécessaires* à la passe avant et arrière, pas celles qu'ajoute la recomputation des activations. Cela rend le MFU indépendant de l'implémentation :

$$\text{MFU} = \frac{\text{tokens/s} \times F_{\text{token}}}{n_{\text{GPU}} \times P_{\text{pic}}}$$

Le **HFU** (*hardware FLOPs utilization*) compte au contraire les FLOP réellement exécutés, recomputation comprise. Les auteurs de PaLM le jugent peu fiable pour comparer des systèmes : il dépend de choix d'implémentation et de la méthode de comptage. Pour PaLM 540B sur 6 144 puces TPU v4, ils rapportent un MFU de 46,2 % et un HFU de 57,8 %.

Le pic $P_{\text{pic}}$ doit être le pic **dense** de la précision utilisée pour l'entraînement : 989 TFLOP/s en BF16 sur H100 SXM, comme au chapitre 2.

::: ex
[Exemple 7.2 — MFU d'un entraînement de 7 milliards de paramètres]{.tag} Hypothèses d'exemple, non mesurées : un entraînement traite $2^{22} = 4\,194\,304$ tokens par étape sur 64 GPU H100 et une étape dure 7,0 s. Le débit est de 599 186 tokens/s. Avec $F_{\text{token}} = 4{,}84 \cdot 10^{10}$, les FLOP utiles par seconde valent $2{,}90 \cdot 10^{16}$, soit 29,0 PFLOP/s. Le pic agrégé vaut $64 \times 989 \cdot 10^{12} = 6{,}33 \cdot 10^{16}$. Le MFU est de **45,9 %**. Pour redescendre à 40 %, l'étape devrait durer 8,03 s.
:::

### 7.3. Quelles valeurs sont bonnes ?

Les publications donnent des repères. PaLM 540B atteint 46,2 % de MFU. L'article sur Llama 3 405B rapporte, dans son tableau 4, un MFU BF16 de 43 % sur 8 192 GPU, 41 % sur 16 384 GPU et 38 % avec une séquence de 131 072 tokens, soit 430, 400 et 380 TFLOPs par GPU. Autrement dit : **de 38 à 46 % est la fourchette publiée par des équipes très outillées à grande échelle** : un MFU de 40 % n'est pas un échec.

::: ex
[Exemple 7.3 — Retrouver un ordre de grandeur de durée d'étape]{.tag} Le tableau 4 de Llama 3 indique 16 M tokens par lot, soit environ $16 \times 2^{20}$. Pour $N = 405 \cdot 10^{9}$, $6N \times 1{,}68 \cdot 10^{7} \approx 4{,}08 \cdot 10^{19}$ FLOP par étape. À 400 TFLOPs par GPU sur 16 384 GPU, la machine délivre $6{,}55 \cdot 10^{18}$ FLOP/s : une étape dure de l'ordre de 6 secondes. C'est une estimation de l'auteur de ce module : l'article ne publie pas la durée d'étape.
:::

Le MFU est un rapport de débit. Il ne dit rien du temps perdu quand le job est arrêté, ce qui nous amène à la notion de **goodput** (débit utile) : ici, le MFU multiplié par la fraction du temps où le job progresse réellement.

::: war
[À 16 000 GPU, on s'arrête tous les jours]{.tag} Sur une période de 54 jours de pré-entraînement de Llama 3 405B, Meta a rapporté 466 interruptions de job, dont 47 planifiées et 419 imprévues. Environ 78 % des interruptions imprévues ont été attribuées à des problèmes matériels confirmés ou suspectés, les GPU représentant à eux seuls 58,7 % des causes. L'équipe a pourtant atteint plus de 90 % de temps d'entraînement effectif, grâce à l'automatisation : une intervention manuelle significative n'a été nécessaire que trois fois. Source : [article Llama 3](https://arxiv.org/abs/2407.21783), section 3.3.4.

Un MFU de 40 % associé à 90 % de temps effectif donne un usage utile de l'ordre de 36 % du pic ($0{,}9 \times 0{,}40$), un ordre de grandeur de calcul à retenir. Le module 10 traite cette perte.
:::

### 7.4. La mémoire d'un entraînement

Un entraînement en précision mixte avec l'optimiseur Adam stocke, par paramètre : 2 octets de poids en BF16, 2 octets de gradient, et 12 octets d'état d'optimiseur (copie des poids en FP32, moment, variance). L'article ZeRO l'écrit $2\Psi + 2\Psi + K\Psi = 16\Psi$ octets avec $K = 12$.

Pour 7 milliards de paramètres, cela représente $16 \times 7 \cdot 10^9 = 112$ Go, hors activations. C'est plus que les 80 Go d'un H100 : un modèle de 7 milliards de paramètres **ne tient pas** sur un GPU en entraînement complet. Il faut répartir ces états entre GPU, ce que font ZeRO et FSDP au module 9.

::: recap
Points clés — chapitre 7

-   Un token coûte environ $6N + 12LHQT$ FLOP à l'entraînement (PaLM, annexe B).
-   MFU : tokens/s × FLOP par token divisés par le pic dense agrégé ; HFU compte la recomputation.
-   De 38 à 46 % de MFU est la fourchette publiée à grande échelle (PaLM, Llama 3).
-   Le goodput est le MFU multiplié par la part de temps où le job tourne vraiment.
-   Adam en précision mixte coûte 16 octets par paramètre : 112 Go pour 7 milliards de paramètres.
:::

## 8. Mener une étude de passage à l'échelle {#ch8}

Une étude de passage à l'échelle n'est pas un graphique : c'est un argument. Elle doit permettre à un lecteur sceptique de refaire vos mesures et d'arriver à la même conclusion.

### 8.1. Le protocole en sept étapes

1.  **Poser la question.** Quel passage à l'échelle (fort ou faible), sur quelle plage, avec quelle métrique ?
2.  **Écrire la prédiction avant de mesurer.** Amdahl, α-β, roofline : quelles valeurs attendez-vous ?
3.  **Fixer le plan d'expérience.** Facteurs (nombre de processus, taille de message, taille de lot), nombre de répétitions, ordre aléatoire des essais.
4.  **Contrôler l'environnement.** Version logicielle, affinité, threads, autres charges ; tout est consigné.
5.  **Mesurer avec chauffe et répétitions.** Au moins dix répétitions ; estimateur annoncé.
6.  **Analyser avec incertitude.** Médiane, intervalle de confiance, efficacité et non seulement gain.
7.  **Conclure et nommer les menaces.** Ce que l'étude ne montre pas.

### 8.2. Statistiques minimales

Une moyenne sans dispersion n'est pas un résultat. Pour une médiane, un intervalle de confiance par rééchantillonnage (*bootstrap*) ne demande aucune hypothèse de distribution.

~~~python
import numpy as np

def median_ci(samples, n_boot=10_000, alpha=0.05, seed=0):
    """Median and bootstrap percentile confidence interval."""
    rng = np.random.default_rng(seed)
    x = np.asarray(samples, dtype=float)
    boots = np.median(rng.choice(x, size=(n_boot, x.size), replace=True), axis=1)
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return float(np.median(x)), float(lo), float(hi)
~~~

Hoefler et Belli recommandent aussi de ne jamais faire la moyenne arithmétique de rapports, comme des gains : calculez le gain à partir des temps médians, puis propagez l'incertitude des temps. Deux gains de 2 et de 0,5 ont une moyenne arithmétique de 1,25, alors que, sur deux charges de 100 s, le système passe de 200 s à 50 + 200 = 250 s : il est plus lent.

### 8.3. Lire un tableau de passage à l'échelle fort

::: ex
[Exemple 8.1 — Un jeu de mesures d'exemple]{.tag} Voici des temps d'exécution **fictifs**, choisis pour illustrer le calcul, pour un même problème sur $p$ processus.

| $p$ | Temps (s) | Gain $S$ | Efficacité $E = S/p$ |
|---|---|---|---|
| 1 | 100 | 1,00 | 100 % |
| 2 | 52 | 1,92 | 96 % |
| 4 | 28 | 3,57 | 89 % |
| 8 | 16,5 | 6,06 | 76 % |

La fraction séquentielle de Karp-Flatt vaut, pour $p = 8$, $e = (1/6{,}06 - 1/8)/(1 - 1/8) \approx 0{,}046$. Si ce coût était une vraie part séquentielle, Amdahl prédirait pour $p = 64$ un gain de $1/(0{,}046 + 0{,}954/64) \approx 16{,}5$, soit une efficacité de 26 %. La **prédiction** peut ensuite être comparée à une mesure : un écart important signale un coût qui croît avec $p$.
:::

### 8.4. Les pièges classiques

-   **Comparer à un code séquentiel affaibli.** Le gain se mesure par rapport au meilleur code séquentiel, pas à une version volontairement lente.
-   **Passer sous silence la taille du problème.** Un passage à l'échelle faible n'est pas un passage à l'échelle fort.
-   **Choisir la meilleure exécution.** Rapporter le meilleur de dix essais est un biais ; rapportez la médiane et la dispersion.
-   **Oublier la variabilité entre nœuds.** Deux nœuds nominalement identiques peuvent différer ; permutez l'affectation.
-   **Omettre l'environnement.** Sans version logicielle et matérielle, personne ne peut reproduire.

### 8.5. Le rapport

Un bon rapport tient sur deux pages : la question, la prédiction, le protocole, un graphique avec barres d'erreur, l'analyse de l'écart et les menaces à la validité. Une page de décision d'architecture (*ADR*) accompagne le rapport : elle consigne ce que l'étude a conduit à décider. Le [Projet 2](../../projects/scaling-study/index.html) applique ce format.

::: recap
Points clés — chapitre 8

-   Une étude est un argument : prédire avant de mesurer, annoncer le protocole, rapporter la dispersion.
-   Médiane et intervalle de confiance par bootstrap ; jamais de moyenne arithmétique de gains.
-   Efficacité plutôt que gain seul ; Karp-Flatt pour distinguer part séquentielle et coût de parallélisme.
-   Nommer les menaces à la validité fait la crédibilité d'un rapport.
:::

## Labs {#labs}

### Lab 2.1 — STREAM et GEMM : votre roofline {#lab-2-1}

::: lab

**Objectif.** Mesurer la bande passante mémoire et le débit de produit matriciel de votre machine, puis construire son roofline. **Durée.** 3 h. **Prérequis matériels.** Un portable CPU avec Python 3 et NumPy ; aucun GPU.

1.  Ouvrez `labs/perf-models/stream-gemm/` et lisez `stream_gemm.py` : repérez le compte d'octets de la copie (16 par élément) et de l'addition (24).
2.  Lancez `python3 stream_gemm.py` pour la mesure complète, puis `./verify.sh` pour le contrôle de cohérence rapide.
3.  Relevez dans `results.json` la bande passante `stream.add_gbs`, le débit `peak_gemm_gflops` et le point de rupture `ridge_flop_per_byte`.
4.  Pour chaque taille de GEMM, comparez le débit mesuré à la valeur du roofline (champ `measured_over_roofline`, affiché `ratio=`). Expliquez en cinq lignes pourquoi les petites tailles restent sous le toit.
5.  Relancez `python3 stream_gemm.py --quick` avec `OMP_NUM_THREADS` à 1, 2, puis au nombre de cœurs. Le débit du GEMM augmente avec les threads, mais la bande passante `add_gbs` ne bouge pas : les opérations élémentaires de NumPy sont mono-thread. Que devient le point de rupture, et pourquoi faut-il le lire avec prudence ?

**Critère de réussite.** `./verify.sh` affiche « OK roofline coherent » et vous pouvez donner, avec leurs unités, votre bande passante, votre pic GEMM et votre point de rupture. Sur la VM de test à 4 vCPU (relevé du 2026-10-25, une dizaine d'exécutions rapides), l'addition donne de 8 à 11 Go/s, le GEMM de 250 à 470 GFLOP/s et le point de rupture de 25 à 52 FLOP par octet ; la dispersion vient d'une machine partagée, et le GEMM peut tomber dix fois plus bas quand d'autres charges l'occupent. Vos valeurs seront différentes, c'est normal.

**Pour aller plus loin.** Sur un GPU, remplacez NumPy par PyTorch : mesurez l'addition de vecteurs sur le GPU, un GEMM en BF16, et comparez au pic **dense** de la fiche technique. Vous retrouverez qu'un petit GEMM est loin du pic (exemple 4.3).
:::

### Lab 2.2 — α-β : prédire puis mesurer un all-reduce {#lab-2-2}

::: lab

**Objectif.** Ajuster le modèle de l'anneau sur des mesures d'all-reduce et juger de sa qualité. **Durée.** 3 h. **Prérequis matériels.** Portable CPU, Python 3 et PyTorch (version CPU suffisante) ; 4 cœurs recommandés.

1.  Lisez `labs/perf-models/allreduce-model/bench_allreduce.py` : repérez la chauffe, la barrière avant chaque mesure et le maximum entre rangs.
2.  Lancez `OMP_NUM_THREADS=1 torchrun --nproc_per_node=4 bench_allreduce.py --out allreduce.json`.
3.  Lancez `python3 fit_alpha_beta.py allreduce.json` : il ajuste $\alpha$ et $B$ en minimisant l'erreur relative, sur les messages d'au moins 64 Kio.
4.  Comparez les temps mesurés et prédits pour chaque taille. Où le modèle se trompe-t-il le plus ? Reliez la réponse à la taille de demi-performance.
5.  Calculez le débit algorithmique et le débit de bus pour la plus grande taille, avec le facteur $2(p-1)/p$.

**Critère de réussite.** `./verify.sh` affiche « OK alpha-beta fit usable » avec une erreur relative médiane inférieure à 60 % sur la plage ajustée. Sur la VM de test (relevé du 2026-10-25, treize exécutions), l'ajustement donne $\alpha$ de 250 à 910 $\mu$s (les valeurs hautes quand la machine est chargée) et $B$ de 0,7 à 1,9 Go/s, avec une erreur médiane de 6 à 23 % : les processus `gloo` partagent les mêmes cœurs, ce n'est donc pas un réseau. Le but est la méthode, pas ces chiffres.

**Pour aller plus loin.** Sur un nœud multi-GPU, remplacez le backend par `nccl` et placez le tenseur sur GPU, puis comparez le débit de bus mesuré à la bande passante NVLink de la fiche technique.
:::

### Lab 2.3 — Un calculateur de MFU testé {#lab-2-3}

::: lab

**Objectif.** Maîtriser le calcul du MFU en le programmant avec ses cas limites. **Durée.** 2 h. **Prérequis matériels.** Portable, Python 3 et `pytest`.

1.  Lisez `labs/perf-models/mfu-calculator/mfu.py` : repérez la formule de PaLM (annexe B) et l'absence de comptage de la recomputation.
2.  Lancez `./verify.sh` : les seize tests doivent passer, puis la commande de l'étape 4 s'affiche.
3.  Lisez `test_mfu.py` : le test `test_llama3_table4_rows_with_dense_bf16_peak_989` retrouve les trois lignes du tableau 4 de Llama 3 (430, 400 et 380 TFLOPs par GPU sur un pic de 989). Pourquoi sa tolérance est-elle d'un point de pourcentage ?
4.  Appelez `mfu.py` avec les paramètres de l'exemple 7.2 et retrouvez 45,9 %.
5.  Écrivez un test qui compare le MFU de la première ligne du tableau 4 calculé avec le pic « avec sparsité » (1 979) aux 43 % publiés : il échoue, de combien ? Marquez-le `@pytest.mark.xfail(strict=True)` pour que `./verify.sh` reste vert.

**Critère de réussite.** Les tests passent et la commande de l'étape 4 affiche `MFU = 45.9 %` (un test le vérifie).

**Pour aller plus loin.** Ajoutez le comptage du HFU avec une recomputation complète des activations (8N au lieu de 6N par token) et comparez-le au MFU.
:::

## Exercices {#ex}

::: exo
[Exercice 1 · ★ — Équilibre machine et produit scalaire]{.tag} Soit un processeur de 2,56 TFLOP/s en FP32 et 200 Go/s de bande passante mémoire (exemple 1.1). Le produit scalaire de deux vecteurs FP32 de taille $n$ fait $2n$ FLOP et lit $8n$ octets. Calculez son intensité, sa performance atteignable et dites s'il est limité par le calcul ou la mémoire. Combien de fois chaque octet devrait-il être réutilisé pour que le calcul devienne limitant ?
:::

::: sol
L'intensité vaut $2n/(8n) = 0{,}25$ FLOP par octet. L'équilibre machine vaut :

$$\frac{2{,}56 \cdot 10^{12}}{200 \cdot 10^{9}} = 12{,}8\ \text{FLOP par octet}$$

Comme $0{,}25 < 12{,}8$, le noyau est limité par la mémoire. La performance atteignable est $0{,}25 \times 200 = 50$ GFLOP/s, soit 1,95 % du pic.

Pour devenir limité par le calcul, chaque octet devrait être réutilisé environ $12{,}8/0{,}25 \approx 51$ fois. C'est impossible pour un produit scalaire : chaque élément n'est utilisé qu'une fois.
:::

::: exo
[Exercice 2 · ★ — Pic d'un processeur et lecture d'une mesure]{.tag} (a) Calculez le pic FP32 d'un processeur de 64 cœurs à 2,0 GHz avec 32 FLOP par cycle et par cœur. (b) Un produit de matrices en BF16 (GEMM, voir le chapitre 3) mesuré sur un H100 SXM atteint 700 TFLOP/s. Quelle efficacité annoncez-vous ? Quelle valeur erronée obtiendriez-vous en divisant par le chiffre « avec sparsité » ?
:::

::: sol
(a) Le pic vaut :

$$64 \times 2{,}0 \cdot 10^{9} \times 32 = 4{,}096 \cdot 10^{12}\ \text{FLOP/s}$$

soit 4,10 TFLOP/s.

(b) Le pic dense BF16 est d'environ 989 TFLOP/s : l'efficacité est de $700/989 \approx 71$ %. En divisant par le chiffre « avec sparsité » de 1 979 TFLOP/s, on obtiendrait 35 %, une efficacité apparente deux fois trop faible. C'est l'erreur du chapitre 2.
:::

::: exo
[Exercice 3 · ★ — De l'A100 au H100]{.tag} L'A100 de 40 Go offre 312 TFLOP/s en BF16 dense et 1 555 Go/s ; le H100 SXM, 989 TFLOP/s et 3,35 To/s. Calculez les rapports de pic et de bande passante, l'équilibre machine de chaque GPU, et dites quel type de noyau profite le plus de la nouvelle génération.
:::

::: sol
Le rapport de pic vaut $989/312 \approx 3{,}17$ ; celui de bande passante, $3350/1555 \approx 2{,}15$. Les équilibres machine valent environ 201 FLOP par octet pour l'A100 et 295 pour le H100.

Un noyau limité par la mémoire gagne au plus le facteur de bande passante, soit 2,2. Un gros GEMM limité par le calcul peut gagner jusqu'à 3,2 : ce sont donc les noyaux limités par le calcul qui profitent le plus de la nouvelle génération.

Plus d'opérations deviennent limitées par la mémoire avec le H100 : fusionner les noyaux et réduire le trafic gagne en importance.
:::

::: exo
[Exercice 4 · ★★ — Normalisation de couche]{.tag} Une normalisation de couche lit un tenseur BF16 et en écrit un du même format. Supposez 8 FLOP par élément. Calculez son intensité, sa performance atteignable sur H100 (3,35 To/s, 989 TFLOP/s), et expliquez pourquoi la fusion avec les opérations voisines accélère le temps total.
:::

::: sol
Par élément : 2 octets lus et 2 octets écrits, soit 4 octets, pour 8 FLOP. L'intensité vaut $I = 2$ FLOP par octet.

La performance atteignable est $2 \times 3{,}35 = 6{,}7$ TFLOP/s, soit 0,68 % du pic. Le temps d'un tel noyau est celui de son trafic mémoire.

Fusionner la normalisation avec l'opération précédente ou suivante supprime une écriture suivie d'une relecture du tenseur intermédiaire. Le trafic, donc le temps, baisse en proportion, sans changer les FLOP.
:::

::: exo
[Exercice 5 · ★★ — Quelle taille de lot pour décoder ?]{.tag} On multiplie une matrice de poids carrée de côté $d = 8192$, en BF16, par $b$ vecteurs d'entrée. Comptez les poids lus une fois, et les entrées et sorties de taille $d \times b$ transférées.

Exprimez l'intensité en fonction de $b$. Trouvez le lot qui atteint le point de rupture du H100 (295,2 FLOP par octet). Donnez la performance atteignable pour un lot de 64.
:::

::: sol
Les FLOP valent $2d^2 b$ et les octets $2(d^2 + 2db)$. L'intensité s'écrit donc :

$$I(b) = \frac{b}{1 + 2b/d}$$

Pour $I = 295{,}2$, on résout $b\,(1 - 590{,}4/d) = 295{,}2$, ce qui donne $b \approx 318$ avec $d = 8192$.

Pour $b = 64$, $I \approx 63{,}0$, donc la performance atteignable est $63{,}0 \times 3{,}35 \approx 211$ TFLOP/s, soit 21 % du pic.

Il faut regrouper environ 300 requêtes pour qu'un décodage sature le calcul. Sans cela, le GPU attend sa mémoire.
:::

::: exo
[Exercice 6 · ★★ — Karp-Flatt]{.tag} On mesure les gains $S(2) = 1{,}8$, $S(4) = 3{,}1$ et $S(8) = 4{,}6$. Calculez $e(p)$ pour chaque $p$, interprétez, et prédisez le gain pour $p = 64$ en supposant le modèle d'Amdahl.
:::

::: sol
On applique $e(p) = (1/S - 1/p)/(1 - 1/p)$ à chaque mesure : $e(2) \approx 0{,}111$, $e(4) \approx 0{,}097$ et $e(8) \approx 0{,}106$.

Les valeurs sont presque constantes autour de 0,10. Il s'agit d'une vraie part séquentielle d'environ 10 %, et non d'un coût qui croît avec $p$. Le plafond d'Amdahl est donc 10.

La prédiction pour $p = 64$ est :

$$S(64) = \frac{1}{0{,}10 + 0{,}90/64} \approx 8{,}8$$

Si $e$ avait augmenté avec $p$, il aurait fallu chercher un surcoût de communication ou de synchronisation.
:::

::: exo
[Exercice 7 · ★★ — Retrouver α et B]{.tag} Un all-reduce en anneau sur $p = 4$ rangs prend 277,3 µs pour 1 Mio et 2 636,6 µs pour 16 Mio. Retrouvez $\alpha$ et $B$ avec le modèle de l'anneau.
:::

::: sol
Le modèle est affine : $T = a + b\,n$ avec $b = 2(p-1)/(p\,B)$ et $a = 2(p-1)\,\alpha$. La pente vaut :

$$b = \frac{(2636{,}6 - 277{,}3) \cdot 10^{-6}}{15 \times 2^{20}} = 1{,}5 \cdot 10^{-10}\ \text{s par octet}$$

On en tire $B = 2(p-1)/(p\,b) = 1{,}5 / (1{,}5 \cdot 10^{-10}) = 10$ Go/s.

L'ordonnée à l'origine vaut $a = 277{,}3\ \mu\text{s} - b \times 2^{20} \approx 120\ \mu$s, donc $\alpha = a/(2(p-1)) = 20\ \mu$s.
:::

::: exo
[Exercice 8 · ★★ — Anneau ou arbre]{.tag} Pour $p = 16$ rangs, $\alpha = 10\ \mu$s et $B = 50$ Go/s, calculez la taille de message à partir de laquelle l'anneau devient plus rapide que l'arbre naïf du chapitre 6, puis les deux temps pour 1 Mo et pour 100 Mo.
:::

::: sol
On égale le temps de l'anneau et celui de l'arbre naïf. Cela donne :

$$n^\star = \alpha B\,\frac{2(p-1) - 2\log_2 p}{2\log_2 p - 2(p-1)/p}$$

Avec $p = 16$, le numérateur vaut $30 - 8 = 22$ et le dénominateur $8 - 1{,}875 = 6{,}125$. Le rapport vaut 3,59.

Donc :

$$n^\star = \alpha B \times 3{,}59 = 10^{-5} \times 5 \cdot 10^{10} \times 3{,}59 \approx 1{,}8\ \text{Mo}$$

Pour 1 Mo, l'anneau prend 337,5 µs et l'arbre 240 µs : l'arbre gagne. Pour 100 Mo, l'anneau prend 4,05 ms et l'arbre 16,08 ms : l'anneau gagne, d'un facteur 4.
:::

::: exo
[Exercice 9 · ★★ — MFU d'un entraînement de 7 milliards de paramètres]{.tag} Un entraînement de $N = 7 \cdot 10^9$ paramètres ($L=32$, $H=32$, $Q=128$, $T=4096$) traite $2^{22}$ tokens par étape sur 64 H100 en 7,0 s. Calculez le MFU, puis la durée d'étape qui correspondrait à un MFU de 40 %. Vérifiez avec `mfu.py`.
:::

::: sol
Les FLOP par token valent :

$$6N + 12LHQT = 4{,}2 \cdot 10^{10} + 6{,}44 \cdot 10^{9} = 4{,}84 \cdot 10^{10}$$

Le débit est $2^{22}/7 = 599\,186$ tokens/s.

Les FLOP utiles par seconde valent :

$$599\,186 \times 4{,}84 \cdot 10^{10} = 2{,}90 \cdot 10^{16}$$

Le pic agrégé vaut $64 \times 989 \cdot 10^{12} = 6{,}33 \cdot 10^{16}$ FLOP/s, d'où un MFU de 45,9 %.

Pour 40 %, l'étape doit durer $7{,}0 \times 45{,}86/40 \approx 8{,}03$ s. La commande `python3 mfu.py ... --step-seconds 7.0` affiche bien 45,9 %.
:::

::: exo
[Exercice 10 · ★★★ — Un MFU de 72 % ?]{.tag} Un prestataire (scénario fictif) annonce un MFU de 72 % pour l'entraînement en BF16 d'un modèle de 70 milliards de paramètres sur 1 024 H100, à 868 000 tokens/s. Retrouvez au moins une manière d'obtenir 72 %, donnez le MFU correct (ignorez l'attention) et listez trois erreurs de définition fréquentes avec leur effet sur le chiffre.
:::

::: sol
Le MFU correct vaut :

$$\frac{868\,000 \times 6 \times 70 \cdot 10^{9}}{1024 \times 989 \cdot 10^{12}} \approx 36\ \%$$

En divisant par le pic TF32 **dense** (environ 494,5 TFLOP/s, la moitié du chiffre « avec sparsité » de 989) au lieu du pic BF16 dense, on obtient 72 %. Le dénominateur est deux fois trop petit.

Autres erreurs fréquentes :

-   Compter la recomputation des activations : 8N au lieu de 6N par token donne un HFU de 48 %, pas un MFU.
-   Utiliser, pour un entraînement en BF16, le pic « avec sparsité » ou le pic FP8 dense (tous deux 1 979 TFLOP/s) : on obtient alors 18 %, une erreur dans l'autre sens.
-   Ne compter que les paramètres hors embeddings sans le dire : les FLOP par token sont sous-estimés, donc le MFU aussi, de l'ordre de 1 à 3 % pour un modèle de 70 milliards selon la taille du vocabulaire.

La règle : le pic dense de la précision réellement utilisée, et les FLOP du modèle sans recomputation.
:::

::: exo
[Exercice 11 · ★★★ — La communication d'un DDP de 7 milliards de paramètres]{.tag} On entraîne un modèle de $7 \cdot 10^9$ paramètres en parallélisme de données pur sur 64 GPU, gradients en BF16, avec une étape de 7,0 s (exemple 7.2). Faites l'hypothèse d'une bande passante de 40 Go/s par GPU pour l'all-reduce en anneau, puis de 12,5 Go/s. Calculez le temps de communication, sa part de l'étape, et dites sous quelles conditions il est caché. Signalez une limite importante de ce scénario.
:::

::: sol
Les gradients occupent $2 \times 7 \cdot 10^9 = 14$ Go. Le temps de l'anneau, latence négligée, vaut :

$$T_{\text{comm}} = 2 \times \frac{63}{64} \times \frac{14}{40} \approx 0{,}69\ \text{s}$$

soit 9,8 % de l'étape à 40 Go/s. À 12,5 Go/s il vaut 2,2 s, soit 31,5 %.

Sans recouvrement, la communication s'ajoute au calcul. Avec recouvrement, elle disparaît tant qu'elle reste plus courte que la passe arrière, environ deux tiers du calcul, soit 4,7 s. À 40 Go/s elle est cachée avec de la marge. À 12,5 Go/s elle l'est encore sur le papier, mais avec peu de marge si le recouvrement est imparfait.

Limite importante : en entraînement complet, ce modèle occupe 112 Go d'états (chapitre 7). Il ne tient donc pas sur un GPU de 80 Go en DDP pur. L'exercice isole la communication ; le choix réel du parallélisme est l'objet du module 9. Les bandes passantes sont des hypothèses : il faut les mesurer.
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux situer un noyau sur un roofline.** Preuve : le roofline de votre machine (lab 2.1) et l'intensité de trois noyaux placés dessus.
-   **Je peux lire une fiche technique sans me tromper de pic.** Preuve : l'exercice 2 refait sur une fiche de votre choix.
-   **Je peux prédire un gain et son plafond.** Preuve : l'exercice 6 refait sur vos propres mesures de scalabilité.
-   **Je peux prédire le temps d'un all-reduce.** Preuve : l'ajustement α-β du lab 2.2 et son erreur relative.
-   **Je peux calculer un MFU et en contester un.** Preuve : le calculateur testé du lab 2.3 et l'exercice 10.
-   **Je peux écrire un plan d'étude de passage à l'échelle.** Preuve : une page avec question, prédiction, protocole et menaces.

Trois questions d'entretien à pouvoir traiter oralement en deux minutes chacune.

1.  *Notre job de 64 GPU affiche 30 % de MFU. Est-ce un problème ?* Réponse-type : comparer à des repères publiés (38 à 46 % à grande échelle), demander comment le MFU est calculé (pic dense de la bonne précision, FLOP sans recomputation), puis chercher où va le temps : communication non recouverte, déséquilibre, chargeur de données, coûts fixes.
2.  *Pourquoi un all-reduce de 1 Kio est-il plus lent que prévu par la bande passante du réseau ?* Réponse-type : le temps est dominé par la latence ($\alpha$), pas par la bande passante ; le débit effectif n'atteint la moitié du nominal qu'au-delà de $\alpha B$ ; on regroupe les petits messages.
3.  *Passer de 8 à 64 GPU divise le temps par 5 seulement. Que faites-vous ?* Réponse-type : calculer l'efficacité (62 %), appliquer Karp-Flatt pour savoir si c'est une part séquentielle constante ou un coût croissant, mesurer communication et recouvrement, puis traiter le premier goulot.

## Lectures et références {#refs}

-   NVIDIA. *NVIDIA H100 Tensor Core GPU* (page produit). Consultée le 22 octobre 2026. [nvidia.com](https://www.nvidia.com/en-us/data-center/h100/) : les chiffres du chapitre 2, y compris la note « with sparsity ».
-   NVIDIA. *NVIDIA Hopper Architecture In-Depth*, blog technique. [developer.nvidia.com](https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth/) : tableau comparatif A100 / H100 SXM5 avec valeurs denses et avec sparsité, nombre de SM.
-   Chowdhery et al. *PaLM: Scaling Language Modeling with Pathways*. 2022. [arXiv:2204.02311](https://arxiv.org/abs/2204.02311) : définition du MFU (section 4.1) et formule de l'annexe B.
-   Dubey et al. *The Llama 3 Herd of Models*. 2024. [arXiv:2407.21783](https://arxiv.org/abs/2407.21783) : tableau 4 (MFU par configuration) et section 3.3.4 (fiabilité).
-   Rajbhandari et al. *ZeRO: Memory Optimizations Toward Training Trillion Parameter Models*. 2020. [arXiv:1910.02054](https://arxiv.org/abs/1910.02054) : section 3.1 sur les 16 octets par paramètre.
-   NVIDIA. *nccl-tests, PERFORMANCE.md*. [github.com](https://github.com/NVIDIA/nccl-tests/blob/master/doc/PERFORMANCE.md) : définitions de algbw et busbw.
-   Williams, Waterman, Patterson. *Roofline: An Insightful Visual Performance Model for Multicore Architectures*. Communications of the ACM, 2009. [doi:10.1145/1498765.1498785](https://doi.org/10.1145/1498765.1498785).
-   McCalpin. *STREAM: Sustainable Memory Bandwidth in High Performance Computers*. [cs.virginia.edu/stream](https://www.cs.virginia.edu/stream/index.html) : comptes d'octets de la copie et de l'addition dans le code source [`stream.c`](https://raw.githubusercontent.com/jeffhammond/STREAM/master/stream.c).
-   Patarasuk, Yuan. *Bandwidth optimal all-reduce algorithms for clusters of workstations*. Journal of Parallel and Distributed Computing 69, 2009. [version de l'auteur](https://www.cs.fsu.edu/~xyuan/paper/09jpdc.pdf).
-   Hoefler, Belli. *Scientific Benchmarking of Parallel Computing Systems: Twelve Ways to Tell the Masses when Reporting Performance Results*. SC15, 2015. [doi:10.1145/2807591.2807644](https://doi.org/10.1145/2807591.2807644) : chapitres 3 et 8.

## Sources et portée {#sources}

### Documenté {#documente}

Les chiffres du H100 (page produit NVIDIA et blog Hopper), la définition et les valeurs de MFU de PaLM, le tableau 4 et la section 3.3.4 de Llama 3, la règle des 16 octets par paramètre de ZeRO, les définitions de débit algorithmique et de bus de `nccl-tests`, la borne inférieure de Patarasuk et Yuan, et l'étude de Hoefler et Belli ont été relus à la source le 22 octobre 2026, puis recontrôlés lors d'une relecture indépendante le 25 octobre 2026. Tous les calculs des exemples et des corrigés ont été refaits en Python. Les comptes d'octets de STREAM viennent du code source `stream.c`.

### Recommandé {#recommande}

L'ordre des chapitres, le choix de l'anneau et de l'arbre naïf comme modèles pédagogiques, le protocole en sept étapes et la discipline de prédire avant de mesurer sont des choix de ce parcours, pas des normes.

### À vérifier {#a-verifier}

Les références d'Amdahl (1967), de Gustafson (1988), de Hockney (1994) et de Karp et Flatt (1990), citées dans le texte, n'ont été confrontées qu'aux métadonnées Crossref (auteurs, année, revue) le 25 octobre 2026 ; les articles n'ont pas été relus. Le site officiel de STREAM n'a pas pu être rouvert (erreur de proxy). Les valeurs mesurées dans les labs viennent d'une VM partagée de 4 vCPU et varient d'un facteur 2 ou plus d'une exécution à l'autre. Les plages de capacité et de latence du tableau du chapitre 1 sont des ordres de grandeur non sourcés. Les chiffres des fiches techniques évoluent : relisez la page du fabricant avant toute décision d'achat.

### Hors périmètre {#hors-perimetre}

Les communications point à point sur réseau réel (module 7), le choix d'un parallélisme et ses effets sur la mémoire (module 9), la tolérance aux pannes (module 10) et le coût financier (module 15).
