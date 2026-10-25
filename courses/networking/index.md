---
title: "Réseaux haute performance : InfiniBand, RoCE et NCCL"
subtitle: "Module 07 · Phase 2 · 28 h"
description: "Pourquoi un entraînement multi-nœuds est limité par le réseau : RDMA, InfiniBand, RoCE v2, topologies fat-tree, NVLink, NCCL, mesure et diagnostic."
module:
  id: networking
  number: 7
  phase: 2
  hours: 28
  level: 2
prerequisites: [linux-systems, perf-models]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs 7.1 et 7.2 vérifiés dans un bac à sable ; lab 7.3 (GPU) non exécuté", class: unverified}
labs:
  - {id: topology-sizing, kind: sandbox}
  - {id: nccl-log-reading, kind: sandbox}
  - {id: nccl-tests-run, kind: gpu}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** pourquoi un job qui tourne bien sur un nœud ralentit-il dès qu'il en occupe deux, et comment le démontrer avec des mesures plutôt qu'avec des soupçons ? Dans un entraînement multi-nœuds, chaque étape se termine par un échange de gradients. Le réseau décide alors si les GPU calculent ou s'ils attendent.

Ce module vous apprend à **choisir** une technologie (InfiniBand ou RoCE), à **dimensionner** une topologie, à **lire** le journal d'initialisation de NCCL et à **mesurer** un réseau avec `nccl-tests` et `perftest`. Les calculs sont refaits par un calculateur testé. Une partie des commandes est exécutée pour de vrai, dans un bac à sable, sur un simulateur InfiniBand et le gestionnaire de sous-réseau réel OpenSM. Rien n'est exécuté sur des GPU : le lab 7.3 le dit.

::: key
[Règle de ce module]{.tag} Un réseau d'entraînement se juge en débit de bus mesuré, comparé à ce que le matériel promet. Un écart se cherche couche par couche, du câble jusqu'au framework, en commençant par la couche la plus basse qui peut l'expliquer.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 28 h, dont 10,5 h de lecture (positionnement compris), 9 h de labs, 8 h d'exercices et 0,5 h de checkpoint |
| Niveau d'entrée | 2 : à l'aise avec Linux (module 1) et avec le modèle α-β (module 2) |
| Prérequis | [Module 1 — Linux, systèmes et diagnostic](../linux-systems/index.html), [Module 2 — Architecture matérielle et modèles de performance](../perf-models/index.html) |
| Pour qui | Cœur pour tous : InfiniBand, RoCE et NCCL ; un administrateur HPC qui connaît InfiniBand y trouvera NCCL et le dimensionnement pour l'entraînement. |
| Livrable | un calculateur de topologie testé, un analyseur de journaux NCCL testé et un script de recette `nccl-tests` linté |
| Environnement | un portable Linux avec Python 3 suffit pour les labs 7.1 et 7.2 ; la partie B du lab 7.1 utilise trois paquets Ubuntu. Le lab 7.3 demande deux nœuds GPU : consultez la page tarifaire de votre fournisseur le jour même |
| Projets liés | [Projet 2 — Étude de passage à l'échelle](../../projects/scaling-study/index.html), [Projet 6 — RFC de plateforme](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Convertir un débit de lien en débit utile et dire pourquoi la MTU compte (chapitre 1).
-   Expliquer ce que fait RDMA et ce que change GPUDirect (chapitre 2).
-   Lire l'état d'un sous-réseau InfiniBand et dire ce que fait son gestionnaire de sous-réseau (chapitre 3).
-   Comparer InfiniBand et RoCE v2 sur la perte, le contrôle de congestion et la configuration, en citant des déploiements documentés (chapitres 3 et 4).
-   Dimensionner un fat-tree, calculer sa sur-souscription et justifier un choix (chapitre 5).
-   Lire la topologie vue par un nœud GPU et vérifier l'affinité GPU-carte réseau (chapitre 6).
-   Expliquer comment NCCL choisit un algorithme et lire son journal `NCCL_DEBUG=INFO` (chapitre 7).
-   Mesurer avec `nccl-tests` et `perftest`, interpréter un écart et isoler une panne par bissection (chapitre 8).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 2 — Exploiter un cluster** (semaines 12-22) : provisionner, ordonnancer, relier et alimenter en données un cluster GPU.
-   **S'appuie sur** : [module 1 — Linux, systèmes et diagnostic de performance](../linux-systems/index.html), [module 2 — Architecture matérielle et modèles de performance](../perf-models/index.html).
-   **Prépare** : [module 9 — Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline](../distributed-training/index.html).
-   **Projets qui s'en servent** : [Projet 2 — Étude de passage à l'échelle d'un entraînement](../../projects/scaling-study/index.html), [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html).
-   **Compétences demandées dans les offres d'emploi et travaillées ici** : Python, Collectives (NCCL, RCCL, HCCL), InfiniBand, RoCE, Réseau (général), Santé matérielle (burn-in, diagnostics, RMA), Administration Linux, Slurm, Journaux, traces, FinOps, coûts, Planification de capacité, Astreinte, fiabilité (SRE), Expérience HPC, Profilage, bancs d'essai (voir [l'analyse du marché](../../market/index.html#couverture)).
<!-- /gen:place -->

### Plan de séances {#seances}

Onze séances, soit 28 h : trois de 3 h, six de 2,5 h et deux de 2 h. Le niveau ne diminue jamais. Chaque séance tient dans sa durée : lecture, lab et exercices compris, avec les estimations de 30 minutes par exercice ★, 1 h par ★★ et 1 h 30 par ★★★.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 3 h | 1 | ch. 1 Rappels réseau (1 h avec le positionnement), ch. 2 RDMA et GPUDirect (1,5 h) | Questions de positionnement ; Ex. 1 (0,5 h) |
| 2 | 2.5 h | 1 | ch. 3 InfiniBand (1,5 h) | Ex. 2 et 3 (1 h) |
| 3 | 2.5 h | 2 | ch. 4 Ethernet pour l'IA : RoCE v2 (1,5 h) | Ex. 4 (1 h) |
| 4 | 2 h | 2 | ch. 5 Topologies (1,5 h) | Ex. 5 (0,5 h) |
| 5 | 2.5 h | 2 | ch. 6 Dans le nœud (1 h) | Lab 7.1 partie A (1,5 h) |
| 6 | 2.5 h | 2 | ch. 3 et 5 en pratique : OpenSM sur un fabric simulé | Lab 7.1 partie B (1,5 h) ; Ex. 6 (1 h) |
| 7 | 2.5 h | 2 | ch. 7 NCCL (1,5 h) | Ex. 7 (1 h) |
| 8 | 3 h | 2 | Lab 7.2 en entier | Lab 7.2 (3 h) |
| 9 | 2.5 h | 3 | ch. 8 Mesure et diagnostic (1 h) | Ex. 8 (1,5 h) |
| 10 | 3 h | 3 | ch. 8 en pratique : recette `nccl-tests`, partie A | Lab 7.3 partie A (1,5 h) ; Ex. 9 (1,5 h) |
| 11 | 2 h | 3 | ch. 8 en pratique : recette sur cluster, partie B | Lab 7.3 partie B (1,5 h) ; Checkpoint de sortie (0,5 h) ; démarrage du Projet 2 |

<!-- gen:travailler -->
### Comment travailler ce module {#travailler}

Le parcours s'adresse à plusieurs profils d'entrée, décrits dans le [point de départ](../../profile/index.html). Le tableau donne la priorité conseillée pour ce module ; les questions de positionnement (section 0.1) la confirment ou la corrigent.

| Profil d'entrée | Priorité | Ce que cela veut dire ici |
|---|---|---|
| Ingénieur plateforme, SRE ou DevOps | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Administrateur ou ingénieur HPC | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Ingénieur ML ou chercheur | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Développeur logiciel ou systèmes | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Étudiant ou personne en reconversion | à fond | tous les chapitres, tous les labs et les exercices ★★★ |

**À ne pas survoler.** Le diagnostic NCCL et le modèle de coût des collectives sont ce qui manque le plus souvent, quel que soit le profil d'entrée.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le checkpoint de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si elles vous semblent routinières, parcourez les exercices ★★★ et passez directement au module suivant.

1.  **Un lien de 400 Gb/s.** Combien cela fait-il en Go/s ? Avec un temps d'aller-retour supposé de 5 µs, combien d'octets faut-il garder « en vol » pour saturer ce lien ?

2.  **Lire un débit de bus.** Un all-reduce de 1 Gio sur 16 GPU affiche un débit de bus de 40 Go/s. Quels sont son débit algorithmique et son temps ?

3.  **Compter les commutateurs.** Vous devez relier 1 024 GPU, un lien de 400 Gb/s chacun, avec des commutateurs de 64 ports et sans sur-souscription. Combien de niveaux et combien de commutateurs ?

::: sol
**Réponses.**

1.  Un octet fait 8 bits : $400 / 8 = 50$ Go/s. Le produit bande passante-délai vaut $50 \cdot 10^{9} \times 5 \cdot 10^{-6} = 250\,000$ octets, soit environ 244 Kio. Voir le chapitre 1.

2.  Pour un all-reduce, le débit de bus vaut le débit algorithmique multiplié par $2(p-1)/p$ (module 2, chapitre 6). Ici $2 \times 15/16 = 1{,}875$, donc le débit algorithmique vaut $40/1{,}875 \approx 21{,}3$ Go/s et le temps $2^{30} / 21{,}3 \cdot 10^{9} \approx 50{,}3$ ms. Voir le chapitre 8.

3.  Avec 64 ports, un commutateur relie au plus 64 GPU. Deux niveaux sans sur-souscription (32 ports vers les GPU, 32 vers le haut) donnent $32 \times 64 = 2\,048$ GPU au maximum : deux niveaux suffisent. Il faut $1024/32 = 32$ commutateurs de feuille et $1024/64 = 16$ commutateurs de colonne, soit 48. Voir le chapitre 5 et la commande `python3 fabric.py --endpoints 1024` du lab 7.1.
:::

## 1. Rappels : latence, débit utile, MTU, flux et congestion {#ch1}

Ce chapitre fixe le vocabulaire réseau dont les autres ont besoin. Vous connaissez déjà TCP/IP ; l'objectif est de savoir convertir un chiffre de fiche technique en débit réellement disponible pour un all-reduce.

### 1.1. Latence, débit nominal et débit utile

Un lien se décrit par trois chiffres. Son **débit nominal** est le nombre de bits que le matériel émet par seconde : 400 Gb/s pour une carte récente. Sa **latence** est le temps de premier octet. Son **débit utile** (*goodput*) est la part du débit nominal qui transporte vos données, une fois retirés les en-têtes et les trames de contrôle.

Les fiches annoncent des bits par seconde, les outils de mesure des octets par seconde. La conversion est une simple division par huit : 400 Gb/s font 50 Go/s. Cette division est la source d'erreur la plus fréquente des premières recettes réseau.

Le **produit bande passante-délai** (*bandwidth-delay product*, BDP) donne la quantité de données qu'un émetteur doit garder « en vol » pour que le lien ne reste pas vide en attendant les accusés de réception :

$$\text{BDP} = B \times \text{RTT}$$

::: ex
[Exemple 1.1 — Combien d'octets en vol pour un lien de 400 Gb/s ?]{.tag} Avec $B = 50$ Go/s et un temps d'aller-retour supposé de 5 µs (une hypothèse d'école, pas une mesure), le BDP vaut $50 \cdot 10^{9} \times 5 \cdot 10^{-6} = 250\,000$ octets, soit 244 Kio ou environ 61 paquets de 4 096 octets.

Un émetteur qui n'a que 64 Kio en vol ne peut utiliser qu'un quart du lien. C'est l'une des raisons pour lesquelles une carte RDMA suit elle-même, dans son matériel, les opérations en vol, plutôt que de laisser un noyau les compter.
:::

### 1.2. En-têtes, MTU et débit utile

Chaque paquet porte des en-têtes qui ne transportent pas vos données. Pour RoCE v2 (chapitre 4), le noyau Linux définit les tailles suivantes dans `include/rdma/ib_pack.h` : en-tête Ethernet 14 octets, IPv4 20, UDP 8, *Base Transport Header* (BTH) 12 et contrôle d'intégrité (ICRC) 4. Les en-têtes étendus de certaines opérations s'ajoutent ; nous les négligeons.

La **MTU InfiniBand** est la taille maximale de la charge utile d'un paquet. La bibliothèque `libibverbs` n'accepte que cinq valeurs : 256, 512, 1 024, 2 048 et 4 096 octets (énumération `ibv_mtu` de `verbs.h`). Sur Ethernet, la MTU IP doit contenir la charge utile plus 44 octets (IP, UDP, BTH, ICRC).

Sur le fil s'ajoutent la séquence de contrôle de trame, le préambule et l'espace inter-trame : 24 octets, valeur standard d'Ethernet que ce module n'a pas relue à la source (voir « À vérifier »). Le débit utile d'un paquet de charge $m$ vaut alors :

$$\eta(m) = \frac{m}{m + 14 + 44 + 24}$$

::: ex
[Exemple 1.2 — Pourquoi la MTU de 1 500 octets coûte cher]{.tag} Pour $m = 1\,024$, $\eta = 1024/1106 = 92{,}6\ \%$, soit 46,3 Go/s sur 50. Pour $m = 4\,096$, $\eta = 4096/4178 = 98{,}0\ \%$, soit 49,0 Go/s.

Avec la MTU Ethernet classique de 1 500 octets, la charge utile ne peut dépasser $1500 - 44 = 1456$ octets : la plus grande MTU InfiniBand utilisable est 1 024. Passer aux trames jumbo (MTU IP d'au moins 4 140 octets pour $m = 4096$) rend 2,7 Go/s par lien. Ces valeurs sortent de la commande `python3 fabric.py --goodput 1024 2048 4096` du lab 7.1.
:::

### 1.3. Contrôle de flux et contrôle de congestion

Deux mécanismes distincts protègent un réseau, et on les confond souvent. Le **contrôle de flux** empêche un émetteur de submerger **un récepteur** : fenêtre de réception de TCP, crédits d'InfiniBand, trames de pause d'Ethernet. Le **contrôle de congestion** empêche un ensemble d'émetteurs de submerger **le réseau** : perte de paquets pour TCP, marquage ECN (notification explicite de congestion, section 4.4), algorithmes à débit réglé.

Le premier est local à un lien ; le second est de bout en bout. Un réseau « sans perte » est un réseau où le contrôle de flux s'applique lien par lien, de sorte que les tampons ne débordent jamais. Il évite les pertes mais déplace le problème : une pause se propage de proche en proche. Les chapitres 3 et 4 détaillent les deux solutions d'InfiniBand et d'Ethernet.

### 1.4. Pourquoi l'entraînement est un trafic difficile

Un entraînement en parallélisme de données émet, à chaque étape, des échanges synchrones de très gros messages : peu de flux, tous démarrant en même temps, chacun capable de saturer une carte. Le réseau d'un fournisseur de cloud voit au contraire des millions de petits flux sans corrélation.

Cette différence a des conséquences documentées. Les concepteurs du réseau HPN d'Alibaba constatent que ces flux peu nombreux et très gros favorisent la polarisation du hachage d'ECMP (*Equal-Cost Multi-Path*), qui répartit mal le trafic. Nous y reviendrons aux chapitres 4 et 5. Retenez pour l'instant le modèle du module 2 : $T(n) = \alpha + n/B$, avec un débit de bus qui se compare à la bande passante du lien (voir [le chapitre 6 du module 2](../perf-models/index.html#ch6)).

::: recap
Points clés — chapitre 1

-   Bits par seconde sur les fiches, octets par seconde dans les outils : divisez par huit.
-   Le BDP donne les octets à garder en vol : 250 000 octets pour 400 Gb/s et 5 µs.
-   Le débit utile dépend de la MTU : 92,6 % à 1 024 octets, 98,0 % à 4 096 sur RoCE v2.
-   Contrôle de flux : protéger un récepteur. Contrôle de congestion : protéger le réseau.
:::

## 2. RDMA, verbs et GPUDirect {#ch2}

Ce chapitre explique pourquoi les réseaux d'entraînement n'utilisent pas TCP pour les gros transferts et ce que « RDMA » change concrètement pour un GPU.

### 2.1. Pourquoi contourner le noyau

Avec TCP, chaque transfert traverse le noyau : appels système, copies entre tampons, interruptions. À haut débit, ce coût devient important. Les auteurs de DCQCN (un protocole de contrôle de congestion pour RoCE, chapitre 4 ; Microsoft et Mellanox, 2015) mesurent le surcoût de TCP en processeur et le comparent à RDMA dans leur figure 1, sur des cartes de 40 Gb/s.

RDMA (*Remote Direct Memory Access*) déplace la copie vers la carte réseau. Le programme enregistre une zone de mémoire auprès de la carte, puis lui confie des opérations : la carte lit ou écrit directement cette mémoire, sans passer par le noyau sur le chemin des données. Des opérations « unilatérales » écrivent même dans la mémoire du pair sans réveiller son processeur.

### 2.2. Les objets des verbs

L'interface de programmation s'appelle *verbs* ; la bibliothèque est `libibverbs`, du projet `rdma-core`. Six objets suffisent pour comprendre les journaux et les outils.

-   Le **contexte de périphérique** désigne la carte (`mlx5_0` par exemple).
-   Le **domaine de protection** regroupe les ressources qui peuvent s'utiliser ensemble.
-   La **région mémoire** est une zone enregistrée : la carte obtient ses adresses physiques et des clés d'accès. Les pages sont épinglées.
-   La **paire de files** (*queue pair*, QP) est le canal : une file d'émission et une de réception.
-   La **file de complétion** (CQ) signale la fin des opérations.
-   La **requête de travail** décrit une opération : envoi, réception, écriture RDMA, lecture RDMA, opération atomique.

Le type de transport d'une QP règle la fiabilité. `ib_write_bw` accepte `RC`, `XRC`, `UC` et `DC` pour `--connection`, avec `RC` (connexion fiable) par défaut, comme le montre l'exemple suivant.

::: ex
[Exemple 2.1 — Ce que le bac à sable n'a pas]{.tag} Les commandes suivantes ont été exécutées le 2026-10-24 sur la VM Linux 6.18 du bac à sable, avec les paquets Ubuntu 24.04 `perftest` 24.01.0 et `rdma-core` 50.0.

~~~text
$ ibv_devinfo
Failed to get IB devices list: Function not implemented
$ ib_write_bw --help | grep -E '^ +-(a|c|q|s|m),'
  -a, --all  Run sizes from 2 till 2^23
  -c, --connection=<RC/XRC/UC/DC>  Connection type RC/XRC/UC/DC (default RC)
  -m, --mtu=<mtu>  MTU size : 256 - 4096 (default port mtu)
  -q, --qp=<num of qp's>  Num of qp's(default 1)
  -s, --size=<size>  Size of message to exchange (default 65536)
~~~

Le noyau du bac à sable est compilé sans la pile InfiniBand (`CONFIG_INFINIBAND` absent), et aucune carte n'existe : aucun transfert RDMA ne peut y être mesuré. Les labs 7.1 et 7.2 contournent cette limite sans la cacher : ils testent des calculs et des analyseurs, et un simulateur qui parle seulement le plan de gestion (chapitre 3).
:::

### 2.3. Les coûts cachés

RDMA n'est pas gratuit. L'enregistrement d'une région épingle des pages et programme la carte : on enregistre une fois, puis on réutilise. Les bibliothèques comme NCCL conservent donc des tampons enregistrés et des connexions ouvertes ; la documentation de NCCL consacre une section à l'enregistrement de tampons.

Chaque QP consomme des ressources de la carte. Un job de plusieurs milliers de rangs ouvre beaucoup de connexions. Les paramètres comme `NCCL_IB_QPS_PER_CONNECTION` existent pour arbitrer entre un meilleur étalement du trafic et ce coût.

### 2.4. GPUDirect RDMA

Sans aide, les données d'un GPU doivent d'abord être copiées dans la mémoire de l'hôte, puis lues par la carte réseau : deux traversées de PCIe et deux accès à la mémoire de l'hôte. **GPUDirect RDMA** ouvre un chemin direct. D'après la documentation CUDA, c'est un chemin direct d'échange de données entre le GPU et un périphérique tiers (carte réseau, carte d'acquisition, adaptateur de stockage), qui utilise des fonctions standard de PCI Express.

<figure class="fig">
<svg viewBox="0 0 560 250" role="img" aria-labelledby="gdr-t gdr-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="gdr-t">Chemin des données avec et sans GPUDirect RDMA</title>
<desc id="gdr-d">En haut, sans GPUDirect : le GPU copie vers la mémoire de l'hôte, puis la carte réseau lit cette mémoire. En bas, avec GPUDirect RDMA : la carte réseau lit directement la mémoire du GPU.</desc>
<defs><marker id="gdr-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--accent)"/></marker></defs>
<text x="10" y="24" font-size="15" font-weight="700" fill="currentColor">Sans GPUDirect : 2 traversées de PCIe</text>
<rect x="10" y="40" width="110" height="50" rx="6" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="65" y="70" text-anchor="middle" font-size="15" fill="currentColor">GPU</text>
<rect x="225" y="40" width="130" height="50" rx="6" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="290" y="70" text-anchor="middle" font-size="15" fill="currentColor">mémoire hôte</text>
<rect x="440" y="40" width="110" height="50" rx="6" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="495" y="70" text-anchor="middle" font-size="15" fill="currentColor">carte réseau</text>
<line x1="122" y1="65" x2="222" y2="65" stroke="var(--accent)" stroke-width="3" marker-end="url(#gdr-a)"/>
<line x1="357" y1="65" x2="437" y2="65" stroke="var(--accent)" stroke-width="3" marker-end="url(#gdr-a)"/>
<text x="10" y="150" font-size="15" font-weight="700" fill="currentColor">Avec GPUDirect RDMA : 1 traversée</text>
<rect x="10" y="166" width="110" height="50" rx="6" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="65" y="196" text-anchor="middle" font-size="15" fill="currentColor">GPU</text>
<rect x="440" y="166" width="110" height="50" rx="6" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="495" y="196" text-anchor="middle" font-size="15" fill="currentColor">carte réseau</text>
<line x1="122" y1="191" x2="437" y2="191" stroke="var(--accent)" stroke-width="3" marker-end="url(#gdr-a)"/>
<text x="280" y="182" text-anchor="middle" font-size="14" fill="currentColor">PCIe, sans copie par l'hôte</text>
</svg>
<figcaption>Chemin d'un tampon GPU vers le réseau, sans puis avec GPUDirect RDMA. Schéma pédagogique, pas une mesure.</figcaption>
</figure>

Trois conditions pratiques, toutes tirées de la documentation de NCCL et de CUDA. Le module noyau `nvidia-peermem` doit être chargé à chaque démarrage (aucun service ne le charge automatiquement) ; avec le pilote NVIDIA ouvert et un noyau récent, NCCL peut utiliser la fonction DMA-BUF à la place. Enfin, le GPU et la carte réseau doivent se trouver assez « près » l'un de l'autre sur le bus PCIe (chapitre 6).

::: ex
[Exemple 2.2 — Le trafic mémoire que GPUDirect épargne]{.tag} Un GPU envoie 1 Gio par étape. Sans GPUDirect, l'hôte écrit 1 Gio dans sa mémoire puis le relit : 2 Gio de trafic mémoire pour 1 Gio sur le réseau, auxquels s'ajoute le même coût à la réception. Avec GPUDirect RDMA, ce trafic disparaît.

À huit cartes de 400 Gb/s saturées dans un sens, cela représente 400 Go/s de réseau, donc 800 Go/s de trafic mémoire dans l'hôte à l'émission. Comparez ce chiffre à la bande passante mémoire de la fiche de votre serveur : la lecture est instructive, mais cette bande passante n'est pas citée ici faute de source relue.
:::

::: war
[Une option de BIOS qui casse GPUDirect]{.tag} La documentation de NCCL signale que la virtualisation des entrées-sorties (VT-d, IOMMU) et les services de contrôle d'accès PCI (ACS) peuvent rediriger tout le trafic pair-à-pair vers le contrôleur racine du processeur, avec une chute de performance notable, voire un blocage. Le remède documenté consiste à les désactiver sur les ponts PCI concernés. Source : [NCCL, « GPU troubleshooting »](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting/gpu_troubleshooting.html).
:::

### 2.5. GPUDirect Storage

Le même principe s'applique au stockage. **GPUDirect Storage** (GDS) offre un chemin de transfert direct entre la mémoire du GPU et le stockage, qui évite un tampon intermédiaire dans la mémoire du processeur, d'après le guide de NVIDIA. L'intérêt pour vous : la lecture des jeux de données et l'écriture des *checkpoints* (module 10, [tolérance aux pannes](../fault-tolerance/index.html)) chargent moins le processeur et la mémoire de l'hôte.

::: recap
Points clés — chapitre 2

-   RDMA sort le noyau du chemin des données ; la carte lit et écrit une mémoire enregistrée.
-   Six objets de verbs : contexte, domaine de protection, région mémoire, paire de files, file de complétion, requête.
-   Le bac à sable n'a ni pile InfiniBand ni carte : aucun transfert RDMA n'y est mesuré.
-   GPUDirect RDMA supprime deux accès mémoire de l'hôte par transfert ; il exige `nvidia-peermem` ou DMA-BUF, et des ACS désactivés.
-   GPUDirect Storage évite le tampon intermédiaire pour le stockage.
:::

## 3. InfiniBand : un réseau géré {#ch3}

InfiniBand n'est pas « de l'Ethernet plus rapide » : c'est une architecture complète, avec son transport, son routage et son gestionnaire central. Ce chapitre montre ce qu'il faut savoir pour l'exploiter, avec des sorties réellement capturées sur un simulateur.

### 3.1. Un sous-réseau, un gestionnaire

Un **sous-réseau** InfiniBand regroupe des commutateurs et des adaptateurs de canal d'hôte (HCA). Chaque port reçoit un **LID** (*local identifier*), adresse de niveau 2 attribuée par le **gestionnaire de sous-réseau** (*subnet manager*, SM). Chaque matériel porte aussi un identifiant mondial, le **GUID**.

Le SM découvre la topologie par des balayages (*sweeps*), attribue les LID et calcule les **tables de transfert linéaires** (LFT) de chaque commutateur : pour chaque LID de destination, le port de sortie. Les commutateurs n'exécutent pas de protocole de routage : ils appliquent les tables du SM. À l'inverse, un réseau Ethernet routé repose sur des protocoles distribués.

L'implémentation libre est **OpenSM** (paquet `opensm`). Les journaux du SM du bac à sable montrent ses états : `Entering DISCOVERING state`, puis `Entering MASTER state`. En production, plusieurs SM tournent : un maître et des veilleurs.

### 3.2. Débits et générations

La carte ConnectX-7 d'InfiniBand offre des ports de 400 Gb/s, d'après la page NVIDIA Quantum-2. Cette génération s'appelle **NDR** ; sa famille de commutateurs Quantum-2 compte 64 ports de 400 Gb/s ou 128 ports de 200 Gb/s sur 32 connecteurs OSFP, pour 51,2 Tb/s de débit agrégé bidirectionnel. La plateforme suivante, Quantum-X800, annonce du 800 Gb/s de bout en bout d'après [sa page produit](https://www.nvidia.com/en-us/networking/products/infiniband/quantum-x800/) (génération XDR, appellation non relue).

::: ex
[Exemple 3.1 — Lire une ligne d'`iblinkinfo`]{.tag} Voici une ligne capturée le 2026-10-24 avec `iblinkinfo` (infiniband-diags 50.0) sur un fabric **simulé** par `ibsim` 0.10, dont les liens sont déclarés « 4xEDR ». Elle sort de la commande `python3 ibsim_check.py --iblinkinfo` du lab 7.1 (les LID sont ceux que le gestionnaire de sous-réseau a attribués) :

~~~text
0x000000000010003f     44    1[  ] ==( 4X      25.78125 Gbps Active/  LinkUp)==>      18    4[  ] "leaf7" (Could be 12X )
~~~

Le suffixe `(Could be 12X)` n'entre pas dans le calcul. Le débit est celui d'une **voie** : 25,78125 Gb/s. Le lien en a quatre (`4X`), soit 103,125 Gb/s bruts. Avec l'encodage de ligne 64b/66b, le débit de données vaut $103{,}125 \times 64/66 = 100$ Gb/s, c'est-à-dire un lien EDR. L'encodage 64b/66b n'a pas été relu dans la spécification (voir « À vérifier ») ; le rapport exact de 100 est cependant un bon signe de cohérence.

Les états à surveiller sont `Active` et `LinkUp`, puis le débit attendu : la documentation de NCCL demande que le débit affiché corresponde à celui du réseau, sans « baisse inattendue » (*downshift*).
:::

### 3.3. OpenSM et ses moteurs de routage

Le SM choisit un **moteur de routage**. L'aide d'OpenSM 3.3.23 (paquet Ubuntu 24.04) liste : `updn`, `dnup`, `file`, `ftree`, `lash`, `dor`, `torus-2QoS`, `nue`, `dfsssp` et `sssp`. Le moteur par défaut est *Min Hop*. Plusieurs moteurs peuvent être donnés, séparés par des virgules : OpenSM essaie le suivant si le précédent échoue, et se rabat toujours sur *Min Hop* sauf si `no_fallback` figure dans la liste.

Le moteur `ftree` est conçu pour les fat-trees (chapitre 5) ; `dor` et `torus-2QoS` visent les tores ; `lash` évite les interblocages par des voies virtuelles. Le choix dépend de la topologie. Un moteur qui ne reconnaît pas la topologie échoue, ce qu'il faut savoir diagnostiquer.

::: ex
[Exemple 3.2 — `ftree` accepte un fat-tree sain et refuse un fat-tree amputé]{.tag} Le lab 7.1 (partie B) génère des fabrics à deux niveaux, les fait découvrir par OpenSM 3.3.23 (`-R ftree`) sur `ibsim` 0.10, puis lit la table de transfert d'une feuille avec `ibroute`. Trois fabrics, sorties capturées le 2026-10-24 :

| Fabric | Moteur retenu | Câbles feuille-colonne | Destinations distantes de `leaf0` par lien montant |
|---|---|---|---|
| 8 feuilles × 4 GPU, 4 colonnes (1:1) | `ftree` | 32 sur 32 attendus | 7, 7, 7, 7 |
| 8 feuilles × 6 GPU, 2 colonnes (3:1) | `ftree` | 16 sur 16 attendus | 21, 21 |
| Idem au premier, avec 1 câble retiré | `minhop` | 31 sur 32 | 8, 7, 7, 6 |

Dans les deux premiers cas, `ftree` répartit les destinations de façon égale sur les liens montants. Dans le troisième, OpenSM écrit `Fabric topology is not a fat-tree`, puis `ftree: cannot build lid matrices`, puis `minhop tables configured on all switches`. Un seul câble manquant a suffi à désactiver le moteur prévu, et la répartition devient inégale.
:::

### 3.4. Routage statique, routage adaptatif, calcul dans le réseau

Les LFT associent une destination à un port, pas un flux. Le routage est donc **statique** : deux flux vers des destinations différentes peuvent emprunter le même lien montant, sans que le SM le sache. L'équilibre de l'exemple 3.2 est un équilibre par destination, pas par trafic.

La page produit de NVIDIA pour Quantum-2 annonce du routage adaptatif avancé et SHARPv3. Le routage adaptatif choisit dynamiquement le chemin selon l'état du réseau, au lieu d'appliquer une table fixe ; SHARP déporte des réductions dans les commutateurs. NCCL sait l'exploiter : la documentation indique que `NVLS` et `NVLSTree` activent le délestage NVLink SHARP, et NCCL propose aussi des algorithmes `CollnetDirect` et `CollnetChain`, destinés à la réduction dans le réseau. Le détail des mécanismes dépend de votre version : voir « À vérifier ».

### 3.5. Opérations quotidiennes

Une exploitation InfiniBand repose sur quelques contrôles réguliers, tous disponibles dans le paquet `infiniband-diags`.

-   `ibstat` et `ibstatus` : état du port (`Active`), état physique (`LinkUp`), type de lien, débit. À lancer sur chaque nœud avant un job.
-   `iblinkinfo` : tous les liens du sous-réseau, avec largeur et débit. Un lien qui négocie moins de voies ou un débit inférieur se voit ici.
-   `ibnetdiscover` : la topologie découverte. Comparez-la à la topologie attendue : une différence signale un câble manquant ou croisé.
-   `ibroute` et `ibtracert` : tables de transfert et chemin d'un paquet.
-   Les compteurs d'erreurs de port, lus par `perfquery`, signalent un câble qui se dégrade avant qu'il ne tombe (voir « À vérifier » pour les noms exacts).

La comparaison de la topologie découverte avec la topologie attendue est justement ce que fait la partie B du lab 7.1, avec des compteurs de commutateurs, de nœuds et de liens.

::: recap
Points clés — chapitre 3

-   Le SM attribue les LID et calcule les tables de chaque commutateur ; il se surveille comme un service critique.
-   NDR = 400 Gb/s par port (ConnectX-7, Quantum-2) ; Quantum-X800 vise 800 Gb/s.
-   Les voies s'additionnent : 4 × 25,78125 Gb/s × 64/66 = 100 Gb/s.
-   `ftree` demande un vrai fat-tree : un câble manquant suffit pour retomber sur *Min Hop* et déséquilibrer les liens.
-   Le routage par tables est statique ; routage adaptatif et SHARP sont des options matérielles à valider.
:::

## 4. Ethernet pour l'IA : RoCE v2, PFC, ECN et DCQCN {#ch4}

Ce chapitre présente la voie Ethernet vers le RDMA. Elle est plus flexible que la voie InfiniBand, mais elle déplace vers l'exploitant des réglages que le SM d'InfiniBand cache. Il s'appuie sur des articles de déploiements réels, cités avec leurs limites.

### 4.1. RoCE v2 : le transport InfiniBand dans des paquets UDP

**RoCE v2** (*RDMA over Converged Ethernet*, version 2) encapsule le transport InfiniBand dans UDP, lui-même dans IP. Le paquet est donc routable. Le registre de l'IANA attribue le port UDP 4791 au service `roce` (« IP Routable RocE » dans le registre), à la demande de l'InfiniBand Trade Association (entrée du 2014-10-17).

Le port UDP source varie d'un flux à l'autre. Les auteurs de DCQCN notent que l'en-tête UDP sert justement à l'ECMP : les commutateurs hachent les champs IP et UDP pour répartir les flux sur les chemins équivalents. Ce hachage est la source de beaucoup de problèmes de performance, comme le chapitre 5 le montrera.

Côté NCCL, deux variables concernent spécifiquement RoCE. `NCCL_IB_GID_INDEX` choisit l'indice d'identifiant global utilisé en mode RoCE ; la documentation renvoie à la commande `show_gids` pour le trouver. `NCCL_IB_TC` fixe le champ de classe de trafic, ce qui permet d'aiguiller le trafic vers la file que le réseau protège.

### 4.2. Pourquoi RoCE veut un réseau sans perte

Les cartes RoCE implémentent le transport fiable en matériel, avec une reprise sur perte simple. D'après l'article de DCQCN, RoCE v2 a besoin du contrôle de flux par priorité (PFC, section 4.3) pour obtenir un réseau Ethernet sans perte. Sans cela, la moindre perte coûte cher.

Avec une reprise de type *go-back-N*, le récepteur écarte les paquets suivant le paquet perdu et l'émetteur retransmet tout depuis ce paquet. Au pire, cela retransmet une fenêtre entière. Si la perte n'est pas détectée par un accusé négatif, c'est un délai de garde qui règle la reprise, et un délai de garde se compte en centaines de millisecondes, voire en secondes : le défaut documenté de NCCL est de 4,3 s par tentative.

::: ex
[Exemple 4.1 — Le prix d'une perte]{.tag} Reprenons le BDP de l'exemple 1.1 : 250 000 octets en vol, soit 61 paquets de 4 096 octets. Une perte peut donc forcer jusqu'à 61 retransmissions pour un seul paquet perdu.

Si la reprise passe par le délai de garde, la documentation de NCCL donne la règle : le délai vaut $4{,}096\ \mu\text{s} \times 2^{t}$ pour la valeur `NCCL_IB_TIMEOUT` $= t$. Pour $t = 17$, le délai vaut 536,9 ms, et avec 7 tentatives le temps total avant erreur atteint 3,8 s. À 5 µs d'aller-retour, 536,9 ms représentent 107 374 allers-retours.

Une perte isolée ne se « voit » pas dans la moyenne d'un débit ; elle se voit dans le temps de l'étape la plus lente, puisque l'all-reduce attend le dernier rang.
:::

### 4.3. PFC : sans perte, mais avec des effets de bord

Le *Priority-based Flow Control* (PFC) de l'IEEE 802.1Qbb suspend l'émission d'une file de priorité quand le tampon du récepteur approche de la saturation. Le mécanisme est local à un lien et agit par port et par priorité, pas par flux. Les auteurs de DCQCN en tirent trois défauts : blocage en tête de file, injustice entre flux et « flux victime » pénalisé par une congestion qui n'est pas la sienne.

Le blocage se propage : un récepteur lent suspend le commutateur en amont, qui suspend ses propres voisins, de proche en proche. Un incident local peut devenir un incident de tout le réseau. Une étude de Microsoft sur RDMA déployé à grande échelle documente trois cas concrets.

::: war
[Trois pannes d'un RDMA Ethernet à grande échelle]{.tag} Guo et al. (SIGCOMM 2016) décrivent trois pannes de déploiements RoCE v2 en production.

-   Un **livelock** du transport, causé par une reprise de type *go-back-0* qui réémet tout le message depuis le début. La correction recommandée est *go-back-N*.
-   Un **interblocage PFC** (*deadlock*), provoqué par des paquets inondés vers tous les ports parce que leur destination manquait dans la table d'adresses d'un commutateur.
-   Une **tempête de trames de pause** (*PFC pause frame storm*), causée par une carte réseau défaillante qui émet des pauses sans fin et finit par paralyser tout le réseau.

Source : [RDMA over Commodity Ethernet at Scale](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/11/rdma_sigcomm2016.pdf), sections 4.1 à 4.3. Ces pannes ont été observées avant 2016 sur du matériel de l'époque ; les produits ont changé, les familles de pannes restent à connaître.
:::

### 4.4. ECN et DCQCN

La **notification explicite de congestion** (ECN, RFC 3168) permet à un routeur de marquer un paquet au lieu de le jeter : il positionne le codepoint *Congestion Experienced* (CE) dans l'en-tête IP. Le récepteur renvoie l'information à l'émetteur, qui réduit son débit.

**DCQCN** (*Data Center Quantized Congestion Notification*) applique cette idée à RoCE v2. L'article le décrit comme « a rate-based, end-to-end congestion protocol » qui s'appuie sur QCN et DCTCP. Il comprend trois acteurs. Le commutateur (*congestion point*) marque les paquets avec une probabilité qui monte entre deux seuils de file, $K_{\min}$ et $K_{\max}$, grâce à la fonction RED standard. Le récepteur (*notification point*) renvoie des paquets de notification de congestion (CNP) au plus une fois par intervalle. L'émetteur (*reaction point*) réduit son débit à la réception d'un CNP, puis le remonte avec des minuteurs et des compteurs.

DCQCN n'a donc besoin que des fonctions RED et ECN standard des commutateurs, mais du matériel de la carte. Il ne supprime pas PFC : les flux démarrent à plein débit, et sans PFC cela peut provoquer des pertes (§6 de l'article). L'idée est de déclencher le marquage ECN avant que PFC n'intervienne, de sorte que PFC reste un filet de sécurité.

### 4.5. Ce que disent trois déploiements documentés

Trois publications décrivent un réseau Ethernet pour de gros entraînements. Elles divergent sur la congestion, ce qui est la meilleure raison de ne pas considérer DCQCN comme un réglage « par défaut ».

-   **Llama 3** (Meta, 2024). Le modèle de 405 milliards de paramètres a été entraîné sur un réseau RoCE (commutateurs Arista 7800 et Minipack2 OCP) ; les petits modèles l'ont été sur Quantum-2 InfiniBand. Les deux réseaux sont à 400 Gb/s et réglés pour des performances équivalentes, d'après l'article. Meta fait tourner un cluster de 24 000 GPU sans DCQCN (16 000 au plus pour le préentraînement, dit une note de l'article), grâce à des commutateurs à grands tampons dans la couche de colonne, à un équilibrage de charge amélioré (*E-ECMP*) et à 16 flux entre deux GPU plutôt qu'un.
-   **MegaScale** (ByteDance, 2024). Les commutateurs sont à base de puces Tomahawk 4 (64 ports de 400 Gb/s) en trois couches. Les auteurs constatent qu'avec DCQCN par défaut, l'all-to-all peut provoquer des niveaux élevés de PFC et un blocage en tête de file ; ils conçoivent un algorithme qui combine Swift et DCQCN, et règlent les minuteries de retransmission de NCCL.
-   **HPN** (Alibaba Cloud, 2024). Le réseau a deux niveaux et deux plans, relie 15 000 GPU par *pod* et remplace le commutateur de baie unique par deux, pour supprimer le point de défaillance unique. Il vise la polarisation du hachage d'ECMP plus que la congestion.

Le tableau résume les différences entre les deux technologies, uniquement avec des éléments relus pour ce module. Il ne désigne pas de vainqueur : il montre les questions à poser.

| Question | InfiniBand | RoCE v2 |
|---|---|---|
| Qui calcule les routes ? | Le SM, centralement, avec des tables par destination | Le routage IP des commutateurs, avec hachage ECMP des flux |
| Qui évite la perte ? | Le niveau 2 sans perte de l'architecture (à vérifier dans la spécification) | À construire : PFC, ECN, DCQCN ou, chez Meta, tampons profonds et équilibrage |
| Réglages côté NCCL | Peu | `NCCL_IB_GID_INDEX`, `NCCL_IB_TC`, délais de garde |
| Pannes typiques | Moteur de routage, SM, câbles | Interblocage PFC, tempêtes de pause, hachage polarisé |
| Fournisseurs | Un seul écosystème de commutateurs | Plusieurs, dont des commutateurs ouverts (OCP) |

::: key
[Choisir]{.tag} Les deux réseaux de Llama 3 ont été réglés pour des performances équivalentes : le choix se fait sur le coût, les compétences de l'équipe et le fournisseur, pas sur une supériorité technique. Demandez toujours à qui appartiendra le réglage de la congestion.
:::

::: recap
Points clés — chapitre 4

-   RoCE v2 est le transport InfiniBand sur UDP (port 4791) : routable, mais exigeant en réglages.
-   Il suppose un réseau sans perte ; une perte coûte jusqu'à une fenêtre, un délai de garde coûte des centaines de millisecondes.
-   PFC évite la perte mais propage les pauses ; Guo et al. documentent livelock, interblocage et tempête de pause.
-   DCQCN combine marquage ECN, CNP et réduction de débit ; PFC reste un filet de sécurité.
-   Meta (sans DCQCN), ByteDance (Swift et DCQCN) et Alibaba (deux plans) ont fait trois choix différents.
:::

## 5. Topologies : fat-tree, rails et sur-souscription {#ch5}

La topologie fixe le débit que le réseau peut tenir quand tous les GPU parlent en même temps. Ce chapitre donne les formules qui se refont à la main, vérifiées par un calculateur testé et comparées à des configurations publiées.

### 5.1. Le fat-tree

Un **fat-tree** est un arbre où les liens deviennent plus gros (ou plus nombreux) en montant vers la racine, de sorte que la capacité ne se réduit pas. Al-Fares, Loukissas et Vahdat (SIGCOMM 2008) le construisent avec des commutateurs identiques de $k$ ports. Il y a $k$ *pods* de deux couches de $k/2$ commutateurs, et chaque commutateur de bordure dessert $k/2$ hôtes.

Le cœur compte $(k/2)^2$ commutateurs. Le résultat : $k^3/4$ hôtes et $5k^2/4$ commutateurs. Pour $k = 48$, l'article cite 27 648 hôtes ; la formule donne 2 880 commutateurs.

Avec des commutateurs de $r$ ports sans sur-souscription, deux niveaux (feuilles et colonnes) desservent au plus $r^2/2$ points d'accès ; trois niveaux, $r^3/4$. Pour $N$ points d'accès, le nombre de commutateurs vaut $3N/r$ à deux niveaux et $5N/r$ à trois :

$$N_{\max}^{(2)} = \frac{r^2}{2}, \qquad N_{\max}^{(3)} = \frac{r^3}{4}, \qquad S^{(2)} = \frac{3N}{r}, \qquad S^{(3)} = \frac{5N}{r}$$

<figure class="fig">
<svg viewBox="0 0 560 300" role="img" aria-labelledby="ft-t ft-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="ft-t">Fat-tree à deux niveaux</title>
<desc id="ft-d">Deux commutateurs de colonne reliés chacun aux quatre commutateurs de feuille ; chaque feuille dessert deux GPU. Aucune sur-souscription : autant de liens montants que de liens vers les GPU.</desc>
<g stroke="var(--accent)" stroke-width="2">
<line x1="170" y1="70" x2="75" y2="150"/><line x1="170" y1="70" x2="205" y2="150"/><line x1="170" y1="70" x2="345" y2="150"/><line x1="170" y1="70" x2="475" y2="150"/>
<line x1="390" y1="70" x2="75" y2="150"/><line x1="390" y1="70" x2="205" y2="150"/><line x1="390" y1="70" x2="345" y2="150"/><line x1="390" y1="70" x2="475" y2="150"/>
</g>
<g stroke="currentColor" stroke-width="2">
<line x1="75" y1="170" x2="45" y2="240"/><line x1="75" y1="170" x2="105" y2="240"/>
<line x1="205" y1="170" x2="175" y2="240"/><line x1="205" y1="170" x2="235" y2="240"/>
<line x1="345" y1="170" x2="315" y2="240"/><line x1="345" y1="170" x2="375" y2="240"/>
<line x1="475" y1="170" x2="445" y2="240"/><line x1="475" y1="170" x2="505" y2="240"/>
</g>
<g fill="var(--side-bg)" stroke="currentColor" stroke-width="2">
<rect x="120" y="45" width="100" height="40" rx="6"/><rect x="340" y="45" width="100" height="40" rx="6"/>
<rect x="30" y="150" width="90" height="36" rx="6"/><rect x="160" y="150" width="90" height="36" rx="6"/><rect x="300" y="150" width="90" height="36" rx="6"/><rect x="430" y="150" width="90" height="36" rx="6"/>
<circle cx="45" cy="250" r="12"/><circle cx="105" cy="250" r="12"/><circle cx="175" cy="250" r="12"/><circle cx="235" cy="250" r="12"/><circle cx="315" cy="250" r="12"/><circle cx="375" cy="250" r="12"/><circle cx="445" cy="250" r="12"/><circle cx="505" cy="250" r="12"/>
</g>
<g font-size="15" text-anchor="middle" fill="currentColor">
<text x="170" y="71">colonne 0</text><text x="390" y="71">colonne 1</text>
<text x="75" y="173">feuille 0</text><text x="205" y="173">feuille 1</text><text x="345" y="173">feuille 2</text><text x="475" y="173">feuille 3</text>
<text x="280" y="285" font-size="14">GPU (un port de carte réseau chacun)</text>
</g>
</svg>
<figcaption>Fat-tree à deux niveaux : 4 feuilles, 2 colonnes, 8 GPU. Chaque feuille offre autant de ports montants (2) que de ports vers les GPU (2) : sur-souscription 1:1.</figcaption>
</figure>

::: ex
[Exemple 5.1 — Retrouver les chiffres d'une architecture de référence]{.tag} Le guide d'architecture du DGX SuperPOD H100 publie, pour des commutateurs InfiniBand de 64 ports, le nombre de feuilles, de colonnes et de cœurs selon la taille, en unités évolutives (*scalable units*, SU) de 32 nœuds. La commande `python3 fabric.py --compare` du lab 7.1 recalcule ces nombres avec les formules ci-dessus (sortie capturée le 2026-10-24, quatre lignes sur huit, notes de fin de ligne omises) :

~~~text
OK   SU= 1 gpus=   248 published={'leaf': 8, 'spine': 4, 'core': 0} computed={'leaf': 8, 'spine': 4, 'core': 0}
DIFF SU= 3 gpus=   760 published={'leaf': 24, 'spine': 16, 'core': 0} computed={'leaf': 24, 'spine': 12, 'core': 0}
OK   SU=16 gpus=  4096 published={'leaf': 128, 'spine': 128, 'core': 64} computed={'leaf': 128, 'spine': 128, 'core': 64}
OK   SU=56 gpus= 16384 published={'leaf': 512, 'spine': 512, 'core': 256} computed={'leaf': 512, 'spine': 512, 'core': 256}
~~~

Sept lignes sur huit concordent. La différence pour 3 SU tient à la conception : le tableau garde 16 colonnes avec 768 câbles, soit 48 ports utilisés sur 64 par colonne, ce qui laisse penser (hypothèse) que le nombre de colonnes est conservé pour passer à 4 SU sans recâbler.

La ligne « 56 » est incohérente dans la source : 56 SU de 32 nœuds font 1 792 nœuds, alors que le tableau indique 2 048 nœuds et 16 384 GPU. Le calculateur utilise le nombre de GPU, pas l'étiquette.
:::

### 5.2. La sur-souscription

Le **taux de sur-souscription** compare ce que les points d'accès peuvent émettre à la capacité qui monte. Al-Fares et ses coauteurs l'expriment par un rapport : 1:1 signifie que tous les hôtes peuvent parler à n'importe quel autre à pleine vitesse ; 5:1 ne laisse disponible que 20 % de la bande passante des hôtes pour certains motifs de trafic.

Une feuille de 64 ports qui réserve 48 ports aux GPU et 16 aux colonnes affiche 3:1. L'intérêt est le coût : moins de commutateurs et surtout moins de câbles optiques. Le tableau suivant est calculé par le lab 7.1 (`--endpoints N --radix 64 --leaf-down D`), en comptant deux émetteurs-récepteurs optiques par lien entre commutateurs.

| GPU | Ports bas/haut | Niveaux | Feuilles | Colonnes | Cœurs | Commutateurs | Émetteurs-récepteurs |
|---|---|---|---|---|---|---|---|
| 2 048 | 32/32 (1:1) | 2 | 64 | 32 | 0 | 96 | 4 096 |
| 2 048 | 48/16 (≈3:1) | 2 | 43 | 11 | 0 | 54 | 1 376 |
| 4 096 | 32/32 (1:1) | 3 | 128 | 128 | 64 | 320 | 16 384 |
| 4 096 | 48/16 (≈3:1) | 3 | 86 | 48 | 24 | 158 | 5 824 |

Le prix des économies est le débit quand le trafic traverse le niveau sur-souscrit. Un modèle jouet suffit pour raisonner : une fraction $f$ des octets traverse le niveau au débit $B/o$, le reste va à $B$. Le temps par octet vaut $\big((1-f)+f\,o\big)/B$, donc :

$$B_{\text{eff}} = \frac{B}{1 + f\,(o-1)}$$

::: ex
[Exemple 5.2 — Le 1:7 de Llama 3]{.tag} L'article de Llama 3 décrit des baies de 16 GPU, 192 baies par *pod* soit 3 072 GPU en bande passante de bissection complète, et huit *pods* soit 24 576 GPU ; la couche d'agrégation a un taux de sur-souscription de « 1:7 ». Nous lisons cette notation comme « un septième de la bande passante complète » (à vérifier).

Dans cette lecture, un GPU dispose de $400/7 \approx 57$ Gb/s, soit 7,1 Go/s, vers un autre *pod*, contre 50 Go/s dans son *pod*. L'article précise que le parallélisme et l'ordonnanceur sont conçus pour minimiser les communications entre *pods* : c'est précisément ce que le modèle jouet recommande, en réduisant $f$.
:::

### 5.3. Topologies à rails

Dans un nœud GPU, chaque GPU possède sa propre carte réseau (chapitre 6). Une topologie **à rails** (*rail-optimized*) relie la carte numéro $k$ de tous les nœuds à un même ensemble de feuilles, le rail $k$. Le guide du DGX SuperPOD H100 l'énonce ainsi : « Each group of 32 nodes is rail-aligned. Traffic per rail of the DGX H100 systems is always one hop away from the other 31 nodes in a SU. »

L'avantage est que les cartes de même numéro local se parlent en un saut, sous une même feuille. NCCL aligne son choix de carte sur le GPU : dans les journaux synthétiques du lab 7.2, le GPU local 3 sort par la carte 3. Le coût de comptage est nul : huit rails de 128 nœuds utilisent autant de commutateurs qu'un fabric plat de 1 024 points d'accès (48, test du lab 7.1). L'inconvénient est un domaine de panne plus étendu : une feuille tombée prive un rail de tous les nœuds.

MegaScale relie les huit cartes de 200 Gb/s d'un serveur à huit commutateurs différents (en multi-rails), divise un port de 400 Gb/s de baie en deux ports de 200 Gb/s pour réduire les conflits de hachage, et place les nœuds gourmands sous un même commutateur de baie. HPN adopte deux plans et deux commutateurs de baie par serveur. Trois constructions différentes, une même idée : réduire le nombre de chemins sur lesquels le hachage peut se tromper.

### 5.4. Dragonfly et au-delà

À très grande échelle, un fat-tree à trois niveaux coûte beaucoup de câbles. Une topologie **dragonfly** regroupe des commutateurs en groupes entièrement connectés, reliés entre eux par un petit nombre de liens globaux ; elle réduit le nombre de câbles longs au prix d'un routage plus subtil, qui exige du routage adaptatif. La page de NVIDIA pour Quantum-2 annonce plus d'un million de nœuds de 400 Gb/s avec un DragonFly+ à quatre niveaux de commutateurs (trois sauts).

OpenSM propose des moteurs dédiés aux topologies non arborescentes (`dor`, `lash`, `torus-2QoS`, voir le chapitre 3). L'article fondateur du dragonfly n'a pas été relu pour ce module (voir « À vérifier »), et la plupart des entraînements décrits dans ce cours tiennent dans un fat-tree.

### 5.5. Placement sensible à la topologie

La topologie n'a de valeur que si l'ordonnanceur la connaît. Slurm la décrit par `topology/tree` et l'option `--switches` (voir [le chapitre 5 du module 5](../slurm/index.html#ch5)) ; sur Kubernetes, on étiquette les nœuds par feuille et par bloc (module 12). Le coût d'une allocation éparpillée est celui de l'exemple 5.2 : plus de trafic qui traverse les niveaux hauts.

Dans le sens inverse, NCCL lit la topologie du nœud et en déduit ses anneaux et ses arbres (chapitre 7). Une topologie fausse, une allocation éparpillée ou une affinité mal réglée donnent le même symptôme : un débit de bus en dessous de l'attendu, sans erreur.

::: recap
Points clés — chapitre 5

-   Un fat-tree de commutateurs à $r$ ports dessert $r^2/2$ points d'accès en 2 niveaux, $r^3/4$ en 3.
-   Sans sur-souscription : $3N/r$ commutateurs à 2 niveaux, $5N/r$ à 3. Le calculateur reproduit sept des huit lignes du DGX SuperPOD H100.
-   La sur-souscription économise des commutateurs et des émetteurs-récepteurs ; elle coûte du débit pour le trafic qui traverse le niveau.
-   Les topologies à rails gardent le trafic de même rang local à un saut.
-   Le placement par l'ordonnanceur compte autant que la topologie.
:::

## 6. Dans le nœud : NVLink, NVSwitch, PCIe et affinité {#ch6}

Avant de sortir du serveur, un octet traverse plusieurs liens de vitesses très différentes. Ce chapitre donne l'ordre de grandeur de chacun et la grammaire que NCCL utilise pour décrire la distance entre un GPU, un autre GPU et une carte réseau.

### 6.1. Une hiérarchie de liens

Dans un serveur GPU récent, quatre familles de liens coexistent. **NVLink** relie les GPU entre eux, par l'intermédiaire de **NVSwitch** quand le serveur en contient. **PCIe** relie les GPU, les cartes réseau, le stockage et les processeurs. Les **cartes réseau** quittent le serveur. Entre processeurs, un lien d'interconnexion (QPI ou UPI, d'après la documentation de NCCL) joint les sockets.

La page produit du H100 de NVIDIA annonce une quatrième génération de NVLink à 900 Go/s d'interconnexion GPU-GPU, avec PCIe Gen5. Le guide utilisateur du DGX H100 décrit huit cartes ConnectX-7 à un port, jusqu'à 400 Gb/s chacune, pour le réseau de calcul, et deux cartes ConnectX-7 à deux ports Ethernet pour le stockage et l'administration. Le stockage a donc ses propres cartes, distinctes des huit cartes du réseau de calcul.

::: ex
[Exemple 6.1 — NVLink contre carte réseau]{.tag} Huit cartes de 400 Gb/s font 3 200 Gb/s, soit 400 Go/s par sens et par serveur, à raison de 50 Go/s par GPU. Le rapport de 900 Go/s (NVLink) à 50 Go/s (une carte) vaut 18.

NVIDIA ne précise pas, dans la page citée, si les 900 Go/s se comptent par sens ou en bidirectionnel. En divisant par deux, le rapport tombe à 9 : l'ordre de grandeur reste celui d'un facteur dix. La conséquence est structurante : les collectives doivent faire le plus de travail possible à l'intérieur du nœud avant de toucher le réseau.
:::

### 6.2. La grammaire des chemins

NCCL détecte la topologie du nœud et classe chaque paire de composants selon un **type de chemin**. Le code source de NCCL (`src/graph/topo.cc`) en liste douze : `LOC`, `NVL`, `NVB`, `C2C`, `PIX`, `PXB`, `P2C`, `PXN`, `PHB`, `SYS`, `NET` et `DIS`. La documentation des variables d'environnement définit les types qui concernent le PCIe :

| Type | Sens (documentation de NCCL) |
|---|---|
| `NVL` | les GPU sont reliés par NVLink |
| `PIX` | sur le même commutateur PCI |
| `PXB` | à travers un ou plusieurs commutateurs PCI |
| `PHB` | sur le même nœud NUMA (même socket, module 1), le trafic traverse le processeur |
| `SYS` | entre nœuds NUMA, par l'interconnexion entre sockets |

Deux variables règlent la distance maximale tolérée. `NCCL_P2P_LEVEL` fixe la distance au-delà de laquelle NCCL n'utilise plus le transport pair-à-pair entre GPU ; `NCCL_NET_GDR_LEVEL` fixe la distance maximale entre carte réseau et GPU pour GPUDirect RDMA. La documentation déconseille d'écrire les valeurs sous forme d'entiers (les valeurs numériques changent d'une version à l'autre) et recommande les noms de types.

### 6.3. L'affinité GPU-carte réseau

La règle pratique est simple : chaque GPU doit trouver, sous le même commutateur PCI (type `PIX`), la carte réseau qui lui sert de sortie. Alors GPUDirect RDMA est actif, et le trafic ne remonte pas au processeur. Si la carte est à distance `PHB` ou `SYS` et que `NCCL_NET_GDR_LEVEL` est inférieur, NCCL désactive GPUDirect pour cette paire et passe par la mémoire de l'hôte (chapitre 2).

Trois contrôles de routine : lire la matrice de topologie du nœud (`nvidia-smi topo -m`) ; faire écrire à NCCL sa vision avec `NCCL_TOPO_DUMP_FILE` (disponible depuis la version 2.6) ; vérifier que les services de contrôle d'accès PCI (ACS) sont désactivés (chapitre 2). Côté ordonnanceur, `--gpu-bind=closest` rapproche chaque tâche de son GPU (voir [le chapitre 5 du module 5](../slurm/index.html#ch5)).

NCCL connaît aussi un type de chemin `PXN` et une variable `NCCL_PXN_DISABLE`. L'idée, détaillée dans le blog de NVIDIA sur NCCL 2.12 (non relu ici), est qu'un GPU peut envoyer par la carte réseau d'un GPU voisin relié en NVLink ; le comportement exact est à vérifier dans votre version.

::: ex
[Exemple 6.2 — Qui sort par quelle carte ?]{.tag} Un serveur à huit GPU et huit cartes montre, dans le journal synthétique du lab 7.2, des lignes de la forme `Channel 00/0 : 7[7] -> 8[0] [send] via NET/IB/7/GDRDMA`. Lisez-la ainsi : le rang 7, sur le GPU 7, envoie au rang 8, GPU 0 de l'autre nœud, par la carte numéro 7 du plugin IB, avec GPUDirect RDMA.

Si la ligne se terminait par `NET/IB/7` sans `/GDRDMA`, la carte 7 passerait par la mémoire de l'hôte : un indice de ACS, de `nvidia-peermem` absent ou d'une distance trop grande. C'est le genre de lecture que l'analyseur du lab 7.2 automatise.
:::

::: recap
Points clés — chapitre 6

-   Dans un nœud, NVLink dépasse la carte réseau d'au moins un ordre de grandeur (900 Go/s contre 50 Go/s par GPU, selon la convention de comptage).
-   NCCL classe les distances en types de chemin : `NVL`, `PIX`, `PXB`, `PHB`, `SYS`, `NET`…
-   `NCCL_P2P_LEVEL` et `NCCL_NET_GDR_LEVEL` fixent la distance maximale pour le pair-à-pair et GPUDirect.
-   Visez un GPU et une carte réseau sous le même commutateur PCI ; contrôlez ACS.
-   Le réseau de stockage est séparé du réseau de calcul sur les serveurs de référence.
:::

## 7. NCCL : algorithmes, protocoles et journaux {#ch7}

NCCL (*NVIDIA Collective Communications Library*) est la bibliothèque qui transforme un `all_reduce` de PyTorch en transferts sur NVLink et sur le réseau. Elle choisit seule des algorithmes et des chemins ; vous devez savoir lire ses choix.

### 7.1. Ce que NCCL fait pour vous

Une application crée un **communicateur** qui regroupe des rangs, puis appelle des collectives : all-reduce, all-gather, reduce-scatter, broadcast, reduce, all-to-all. À l'initialisation, NCCL amorce une connexion entre les rangs (*bootstrap*), détecte la topologie, cherche des anneaux et des arbres, ouvre des connexions réseau et réserve des tampons. Ensuite chaque collective découpe les données en **canaux** qui avancent en parallèle.

Tout se passe de façon asynchrone sur un flux CUDA : une collective qui ne se termine jamais ne produit aucune erreur immédiate, elle bloque le flux. C'est pourquoi les journaux, les délais de garde et les outils de diagnostic du chapitre 8 comptent.

### 7.2. Les algorithmes

La documentation de `NCCL_ALGO` liste les algorithmes avec la version qui les introduit : `Ring` et `Tree` (depuis 2.5), `CollnetDirect` et `CollnetChain` (2.14 et suivantes, réduction dans le réseau), `NVLS` (2.17) et `NVLSTree` (2.18), qui utilisent la réduction dans les commutateurs NVLink, et `PAT` (2.23). Sans réglage, NCCL choisit selon la topologie et l'architecture.

Les formules du module 2 donnent l'idée. L'anneau coûte $2(p-1)$ latences ; un arbre, de l'ordre de $\log_2 p$. Le blog de NVIDIA sur NCCL 2.4 explique que l'anneau fait croître la latence linéairement avec le nombre de GPU, ce qui empêche de dépasser quelques centaines de GPU, et présente les **arbres binaires doubles** : bande passante complète et latence logarithmique. Sur le supercalculateur Summit, jusqu'à 24 576 GPU, le gain de latence atteint 180 fois par rapport à l'anneau.

$$T_{\text{anneau}} = 2(p-1)\,\alpha + 2\,\frac{p-1}{p}\,\frac{n}{B} \qquad T_{\text{arbre}} \approx 2\log_2 p\;\alpha + 2\,\frac{n}{B}$$

::: ex
[Exemple 7.1 — 1 024 rangs : l'anneau face à l'arbre, en latence]{.tag} Prenons 128 nœuds de 8 GPU. Hypothèses d'école : 1 µs de latence entre GPU d'un même nœud, 5 µs entre nœuds. Un anneau qui traverse tous les GPU paie $2\big[(1024-128)\times 1 + 128 \times 5\big] = 3\,072$ µs de latence pure.

Un arbre sur les nœuds, avec une chaîne dans chaque nœud, paie $2\times 7 \times 5 + 2 \times 7 \times 1 = 84$ µs. Le rapport est d'environ 37. Ce n'est qu'un modèle jouet, avec des latences supposées ; l'ordre de grandeur est conforme à celui du blog (jusqu'à 180× à 24 576 GPU) sans le démontrer.

Pour un message de 1 Gio sur le même réseau, le terme de bande passante domine (de l'ordre de 40 ms à 50 Go/s) et l'écart de latence (3 ms contre 0,08 ms) pèse peu. C'est pourquoi NCCL choisit selon la taille.
:::

### 7.3. Les protocoles

NCCL propose trois protocoles : `LL`, `LL128` et `Simple`. La documentation décourage de fixer `NCCL_PROTO`, sauf pour désactiver un protocole en cas de bug suspecté. Elle avertit que forcer `LL128` sur une plate-forme qui ne le supporte pas peut corrompre des données. Par défaut, `LL`, `LL128` et `Simple` sont actifs sur les plates-formes qui acceptent `LL128`, et `LL` et `Simple` ailleurs.

### 7.4. Les variables d'environnement utiles

NCCL a des dizaines de variables. Le tableau liste celles dont vous aurez besoin pour diagnostiquer. Les descriptions viennent du guide d'utilisation de NCCL (page « Environment Variables », en-tête version 2.32, lue le 2026-10-24).

| Variable | Rôle |
|---|---|
| `NCCL_DEBUG` | niveau de journal : `VERSION`, `WARN`, `INFO`, `TRACE` (et `ATTN` depuis 2.32) |
| `NCCL_DEBUG_SUBSYS` | filtre par sous-système (`INIT`, `NET`, `GRAPH`, `TUNING`…) ; défaut `INIT,BOOTSTRAP,ENV` |
| `NCCL_DEBUG_FILE` | fichier de journal ; `%h` et `%p` insèrent le nom d'hôte et le PID |
| `NCCL_SOCKET_IFNAME` | interfaces IP utilisées, par préfixes ; `=eth0` pour un nom exact |
| `NCCL_IB_HCA` | cartes RDMA à utiliser ; `=mlx5_0:1` pour un nom exact |
| `NCCL_IB_GID_INDEX`, `NCCL_IB_TC` | indice GID (mode RoCE) et classe de trafic |
| `NCCL_IB_TIMEOUT`, `NCCL_IB_RETRY_CNT` | délai de garde de bas niveau et nombre de tentatives |
| `NCCL_NET_GDR_LEVEL`, `NCCL_P2P_LEVEL` | distance maximale pour GPUDirect et le pair-à-pair |
| `NCCL_ALGO`, `NCCL_PROTO` | restreindre les algorithmes et protocoles (à manier avec prudence) |
| `NCCL_TOPO_DUMP_FILE` | écrit la topologie détectée (depuis 2.6) |

Une variable posée « au cas où » est une dette : documentez qui l'a posée, pourquoi, et avec quelle mesure avant et après.

### 7.5. Lire un journal `NCCL_DEBUG=INFO`

Chaque ligne du journal commence par `hôte:pid:tid [GPU] NCCL INFO`. L'ordre des lignes suit l'initialisation. Tous les formats ci-dessous ont été relus dans le code de NCCL (`init.cc`, `search.cc`, `topo.cc`, `p2p.cc`, `net.cc`, `bootstrap.cc`, lecture du 2026-10-24) ; ils changent d'une version à l'autre, d'où la tolérance de l'analyseur du lab 7.2.

| Ligne (extrait) | Ce qu'elle dit | Anomalie typique |
|---|---|---|
| `Bootstrap: Using eth0:…` | interface IP du *bootstrap* | mauvaise interface (`docker0`, `lo`) |
| `Using network IB` | plugin réseau retenu | `Socket` : retour au TCP, aucun RDMA |
| `NET/IB : GPU Direct RDMA Enabled for HCA 3 'mlx5_3'` | une ligne par carte vue | moins de cartes que de GPU ; `Disabled` |
| `comm … rank 11 nRanks 16 nNodes 2 localRanks 8 …` | identité du rang | rangs absents |
| `Pattern 4, crossNic 0, nChannels 4, bw …, type NVL/PIX` | résultat de la recherche de graphe | `type …/SYS` : chemin lointain |
| `Ring 00 : 10 -> 11 -> 12` | voisins de ce rang dans l'anneau | anneau non fermé |
| `Channel 00/0 : 7[7] -> 8[0] [send] via NET/IB/7/GDRDMA` | transport d'un lien | `via NET/IB/7` sans `/GDRDMA` |
| `… - Init COMPLETE` | fin de l'initialisation du rang | absent : rang bloqué |

::: ex
[Exemple 7.2 — Lire un journal sain, puis un journal cassé]{.tag} L'analyseur du lab 7.2 lit des journaux **synthétiques** (générés par `make_fixtures.py` d'après les formats ci-dessus, avec des valeurs inventées). Sorties capturées le 2026-10-24 (lignes raccourcies par « ... ») :

~~~text
healthy_2node_ib.log: NCCL 2.30.3+cuda13.0; 16/16 ranks on 2 nodes; network IB; HCAs per host {'node-01': 8, 'node-02': 8}; channels [4]; init complete on 16 ranks
  [INFO ] rails_used: NICs carrying ring traffic per host: {'node-01': 4, 'node-02': 4} out of {'node-01': 8, 'node-02': 8}
socket_fallback.log: ...
  [ERROR] socket_network: NCCL uses the Socket (TCP) transport between nodes: no RDMA network was selected
degraded_rail.log: ...
  [ERROR] hca_mismatch: hosts see different numbers of HCAs: {'node-01': 8, 'node-02': 7}
hang_in_init.log: ...
  [ERROR] init_incomplete: ranks without 'Init COMPLETE': [11] (stuck in initialisation or log truncated)
~~~

Dans le journal sain, seules 4 cartes sur 8 portent du trafic d'anneau : il n'y a que 4 canaux. Rien ne dit que c'est un défaut ; cela se lit et se compare avec le nombre de canaux que NCCL ouvrirait dans votre version. Les trois autres journaux montrent un retour au TCP, une carte manquante sur le nœud 2 et un rang qui n'a jamais fini son initialisation.
:::

::: recap
Points clés — chapitre 7

-   NCCL détecte la topologie, cherche anneaux et arbres, ouvre des canaux et des connexions, puis choisit algorithme et protocole selon la taille.
-   Anneau : $2(p-1)$ latences ; arbre binaire double : latence logarithmique, bande passante complète (NCCL 2.4).
-   Ne fixez `NCCL_ALGO` et `NCCL_PROTO` que pour isoler un bug ; `LL128` forcé sur une plate-forme non supportée peut corrompre des données.
-   `NCCL_DEBUG=INFO` plus `NCCL_DEBUG_SUBSYS` filtrent le journal ; `Using network`, `GPU Direct RDMA`, `Ring`, `Channel` et `Init COMPLETE` sont les lignes à lire.
-   Mesurez avant et après toute variable.
:::

## 8. Mesure et diagnostic : nccl-tests, perftest, hangs et liens dégradés {#ch8}

Un réseau d'entraînement se recette comme un équipement : avec un protocole, des chiffres attendus et un rapport. Ce chapitre donne les outils, une méthode par couches et la façon d'isoler un composant défaillant.

### 8.1. nccl-tests et le débit de bus

Le dépôt `nccl-tests` de NVIDIA fournit un programme par collective (`all_reduce_perf`, `all_gather_perf`…). Chaque programme balaie des tailles de message et affiche, pour chaque taille, le temps, le débit algorithmique et le débit de bus, en place et hors place, plus une colonne `#wrong` qui compte les éléments faux. Les options utiles : `-b` et `-e` (tailles minimale et maximale), `-f` (facteur multiplicatif), `-g` (GPU par processus), `-n` (itérations), `-w` (itérations de chauffe), `-c` (vérification des résultats).

Le **débit algorithmique** est $S/t$. Le **débit de bus** le multiplie par un facteur qui dépend de l'opération et du nombre de rangs $n$, pour obtenir un chiffre comparable à la bande passante matérielle. Facteurs de la page `PERFORMANCE.md` : all-reduce $2(n-1)/n$ ; reduce-scatter, all-gather et all-to-all $(n-1)/n$ ; broadcast et reduce 1. La page résume : « The bus bandwidth should reflect the speed of the hardware bottleneck : NVLink, PCI, QPI, or network. »

Deux détails sauvent des heures. D'abord, la variable `NCCL_TESTS_MIN_BW` fait échouer le programme quand le débit de bus moyen tombe sous 0,9 fois sa valeur (code source de `common.cu`). Ce « moyen » est la moyenne de toutes les tailles du balayage, petites comprises : 17 Go/s pour un plateau de 48 Go/s sur la table synthétique de l'exemple 8.1.

Fixez donc la valeur d'après la moyenne imprimée par un essai antérieur du même balayage, ou limitez le test à une grande taille (`-b 4G -e 4G`). Une valeur de fiche technique ferait échouer un réseau sain.

Ensuite, `NCCL_TESTS_SPLIT` découpe les GPU en groupes qui exécutent la même opération en parallèle : avec `MOD 8` sur des nœuds de 8 GPU, on obtient huit opérations, chacune avec un GPU par nœud, donc uniquement sur le réseau inter-nœuds. Le débit affiché est celui d'un groupe, moyenné sur les rangs par défaut ; l'option `-a 3` retient le rang le plus lent. Un seul tableau sort : il révèle un rail lent sans le nommer.

::: ex
[Exemple 8.1 — Lire une table `nccl-tests` avec l'analyseur du lab 7.3]{.tag} Le lab 7.3 fournit des tables **synthétiques** (modèle d'anneau α-β, bruit de 1,5 %, jamais mesurées sur GPU) au format de `nccl-tests`. Sortie capturée le 2026-10-24 sur la table « saine » (16 rangs, débit de bus attendu de 48 Go/s) :

~~~text
all_reduce_synthetic_ok.txt: 32 sizes; plateau busbw 48.5 GB/s; 90% of it reached at 134217728 B; smallest-size time 356.1 us; fit {'B_gbs': 47.914, 'alpha_us': 12.049, 'intercept_us': 361.46}
OK nccl-tests output
~~~

Lecture : le plateau du débit de bus (48,5 Go/s) correspond à l'attendu ; il est atteint à 128 Mio ; le temps au plus petit message (356 µs) est un temps de latence, pas de bande passante. L'ajustement du modèle du module 2 retrouve $B \approx 48$ Go/s et $\alpha \approx 12$ µs, les paramètres du générateur. Sur une vraie mesure, le désaccord entre le modèle et la table est l'information utile.
:::

### 8.2. Les outils de bas niveau

Quand `nccl-tests` est mauvais, descendez d'une couche. La documentation de dépannage de NCCL recommande dans l'ordre :

-   `ibstat` et `ibstatus` : port `Active`, état physique `LinkUp`, bon type de lien, bon débit sans baisse inattendue.
-   `ib_write_bw -d <carte> -a` sur un serveur, puis `ib_write_bw -d <carte> <serveur> -a` sur le client : bande passante point à point sur toutes les tailles. Les variantes `--use_cuda=<gpu>` testent la mémoire GPU, donc GPUDirect.
-   `ib_write_lat` : la latence ; une bande passante correcte peut cacher des queues de latence mauvaises.
-   `rdma statistic` : compteurs du transport. Surveillez `rnr_nak_retry_err`, `packet_seq_err`, `implied_nak_seq_err` et `local_ack_timeout_err` pendant un test : des valeurs croissantes indiquent perte, reprises ou autres problèmes de transport.

La comparaison entre mémoire de l'hôte et mémoire GPU, pour la même paire de cartes, est un test rapide de GPUDirect : si le chemin GPU est nettement plus lent, cherchez ACS, `nvidia-peermem` ou la distance PCIe (chapitres 2 et 6).

### 8.3. Une méthode par couches

Un symptôme « lent » ou « bloqué » a de nombreuses causes. Le tableau associe des symptômes à une couche et à un premier outil, du plus bas au plus haut.

| Symptôme | Couche soupçonnée | Premier contrôle |
|---|---|---|
| Blocage à l'initialisation | amorçage, interface IP, pare-feu | `NCCL_SOCKET_IFNAME`, `NCCL_DEBUG_SUBSYS=INIT,BOOTSTRAP`, rangs sans `Init COMPLETE` |
| Débit bas partout | débit du lien, GPUDirect, PCIe | `ibstat` (débit), lignes `GPU Direct RDMA`, ACS |
| Débit bas sur un seul rail | câble, port, carte | `NCCL_TESTS_SPLIT="MOD 8"` avec `-a 3`, puis `ibstat` carte par carte |
| Arrêts intermittents | pertes, congestion, retransmissions | `rdma statistic`, `ib_write_lat`, compteurs de commutateur |
| Résultats faux | transport ou matériel | colonne `#wrong` de `nccl-tests` |
| Bon test, job lent | recouvrement, placement | module 9 ; topologie des nœuds alloués |

### 8.4. Isoler un composant par bissection

Sur un parc de $N$ nœuds avec un nœud défaillant, tester les nœuds un par un coûte $N$ essais. Une bissection coupe l'ensemble en deux moitiés, teste chacune avec `nccl-tests`, garde la moitié mauvaise et recommence : $\lceil \log_2 N \rceil$ essais suffisent. Pour 128 nœuds, 7 essais au lieu de 128.

La méthode suppose qu'une moitié contenant le nœud défaillant est reconnaissable, donc un test stable et un seuil fixé à l'avance (`--expect-busbw` de l'analyseur du lab 7.3). Elle ne marche pas pour une panne qui n'apparaît qu'à l'échelle (par exemple un lien de commutateur surchargé par plusieurs groupes) : dans ce cas, testez par rail et par feuille.

### 8.5. Blocages, délais de garde et observabilité

Un blocage est le pire symptôme : aucune erreur, des GPU à 100 % puis à 0 %. Trois pratiques documentées. D'abord, NCCL contient un sous-système RAS pour diagnostiquer les blocages et les arrêts brutaux, avec ses propres variables (`NCCL_RAS_ENABLE`, `NCCL_RAS_ADDR`, `NCCL_RAS_TIMEOUT_FACTOR`). Ensuite, Meta décrit, pour Llama 3, une version de NCCL (NCCLX) qui vide ses traces quand un chien de garde ou un battement de cœur expire, avec l'état des transferts en cours entre tous les rangs. Enfin, l'article MegaScale décrit l'analyse des dépassements de délai de NCCL pour désigner le nœud défaillant.

Le délai de garde lui-même est un compromis. Avec `NCCL_IB_TIMEOUT` $= t$, le délai de bas niveau vaut $4{,}096\ \mu\text{s} \times 2^t$, et le temps avant erreur vaut ce délai multiplié par `NCCL_IB_RETRY_CNT`. Le tableau de la documentation, recalculé par nos soins : pour 7 tentatives, $t = 17$ donne 3,8 s, $t = 20$ donne 30 s et $t = 22$ donne 120 s. Un délai long évite les fausses alertes sur un grand réseau, mais retarde la détection d'un vrai blocage de la durée correspondante.

Les compteurs de ports InfiniBand, les compteurs `rdma statistic` et les métriques GPU gagnent à être exportés vers votre supervision pour détecter une dégradation avant le job : voir [le module 14, observabilité](../observability/index.html), et [le module 10, tolérance aux pannes](../fault-tolerance/index.html) pour la reprise.

### 8.6. Le rapport de recette

Une recette réseau ne se résume pas à « ça marche ». Le rapport consigne : les versions (NCCL, pilote, micrologiciel des cartes, `nccl-tests`), les variables d'environnement, la commande exacte, le débit de bus attendu avec sa source (fiche, calcul du chapitre 1), le plateau mesuré, les résultats par rail, et les écarts expliqués. C'est la discipline du [module 2](../perf-models/index.html#ch8), appliquée au réseau, et le point d'entrée du [Projet 2](../../projects/scaling-study/index.html).

::: ex
[Exemple 8.2 — Quel débit attendre sur un lien de 400 Gb/s ?]{.tag} Avec 50 Go/s nominaux et un débit utile de 98,0 % pour une MTU InfiniBand de 4 096 (chapitre 1), le plafond d'un all-reduce multi-nœuds limité par la carte est de $50 \times 0{,}9804 = 49{,}0$ Go/s par GPU. Un plateau mesuré à 45 Go/s représente 92 % de ce plafond ; à 26 Go/s, 53 %.

Ce plafond est un majorant, pas une promesse : les protocoles de NCCL et le recouvrement avec le calcul font baisser le débit réel. Prenez l'attendu dans une fiche ou une mesure antérieure de la même configuration, et utilisez ce calcul pour juger si l'attendu est plausible.
:::

::: recap
Points clés — chapitre 8

-   Débit de bus = débit algorithmique × facteur (2(n−1)/n pour all-reduce) ; il se compare à la bande passante du matériel.
-   `NCCL_TESTS_MIN_BW` transforme la mesure en test d'acceptation ; `NCCL_TESTS_SPLIT` isole les rails.
-   Descendez d'une couche à la fois : `nccl-tests`, `ib_write_bw` et `ib_write_lat`, `ibstat`, `rdma statistic`.
-   Une bissection trouve un nœud défaillant parmi $N$ en $\lceil\log_2 N\rceil$ essais.
-   Les délais de garde (`NCCL_IB_TIMEOUT`) arbitrent entre fausses alertes et détection tardive.
:::

## Labs {#labs}

Trois labs, 9 h au total. Les labs 7.1 et 7.2 s'exécutent dans un bac à sable Linux sans GPU et ont été exécutés par l'auteur (Ubuntu 24.04, 4 vCPU, le 2026-10-24). Le lab 7.3 demande des GPU : il est **linté et testé sur des tables synthétiques**, mais son exécution réelle n'a pas été faite ; c'est pourquoi le badge du module est « non vérifié ». Les scripts `verify.sh` honorent `PYTHON=/chemin/vers/python`.

### Lab 7.1 — Dimensionner un fat-tree {#lab-7-1}

::: lab

**Objectif.** Dimensionner des fat-trees avec un calculateur testé, le confronter aux chiffres publiés du DGX SuperPOD H100, puis vérifier avec le **vrai** gestionnaire de sous-réseau OpenSM, sur un fabric simulé, qu'un fabric généré par le calculateur est reconnu comme un fat-tree. **Durée.** 3 h (partie A : 1,5 h, partie B : 1,5 h). **Prérequis matériels.** Un portable Linux avec Python 3 et `pytest`. Partie B : `sudo apt-get install -y ibsim-utils opensm infiniband-diags` (testé sur Ubuntu 24.04 : ibsim 0.10, OpenSM 3.3.23, infiniband-diags 50.0, en tant que root). Aucun GPU, aucun coût.

1.  Lisez `labs/networking/topology-sizing/fabric.py` : repérez `size_fabric`, la formule `5N/r` à trois niveaux, `effective_bandwidth` et `goodput_fraction`.
2.  Partie A. Lancez `python3 fabric.py --compare` : sept lignes sur huit du DGX SuperPOD H100 doivent concorder ; lisez la note de `published.json` sur la ligne à 3 SU et sur l'incohérence de la ligne « 56 ».
3.  Lancez `python3 fabric.py --endpoints 2048 --radix 64 --leaf-down 48` et retrouvez la ligne 54 commutateurs du tableau du chapitre 5. Puis `python3 fabric.py --goodput 1024 2048 4096`.
4.  Partie B. Lisez `ibsim_check.py` : il écrit un fabric pour `ibsim`, lance OpenSM avec `-R ftree`, relit la topologie avec `ibnetdiscover` et les tables avec `ibroute`. Lancez-le trois fois : `python3 ibsim_check.py`, `python3 ibsim_check.py --radix 8 --down 6 --leaves 8` et `python3 ibsim_check.py --drop-link`.
5.  Expliquez pourquoi le troisième fabric échoue : relisez les trois lignes d'OpenSM affichées par `OpenSM said:`.
6.  Lancez `./verify.sh`.

**Critère de réussite.** `./verify.sh` affiche « OK part A » (12 tests, sept lignes publiées retrouvées), puis « OK part B », puis `OK topology-sizing (parts A and B)`.

Propriétés structurelles vérifiées : les compteurs de commutateurs, d'hôtes et de câbles découverts égalent ceux du calculateur, le déséquilibre des liens montants d'une feuille est d'au plus 1 pour les fabrics sains, et le fabric amputé est rejeté par `ftree`.

Ligne capturée : `radix=8 down=6 up=2 leaves=8: engine=ftree switches=10/10 hosts=48/48 host_links=48/48 switch_links=16/16 max_uplink_imbalance=0`.

Sans les paquets de la partie B, le script affiche `SKIP part B` et se termine par `OK topology-sizing (part A only)` : dans ce cas, seule la partie A est vérifiée.

**Pour aller plus loin.** Étendez `ibsim_check.py` à trois niveaux. Ajoutez une quatrième configuration où une colonne entière est retirée, et observez le moteur retenu. Le simulateur ne transporte aucun paquet : ne mesurez pas de débit avec lui.
:::

### Lab 7.2 — Lire un journal NCCL {#lab-7-2}

::: lab

**Objectif.** Écrire et tester un analyseur de journaux `NCCL_DEBUG=INFO` qui extrait la topologie, le réseau, les cartes, les anneaux et le moment où un rang cesse de progresser. **Durée.** 3 h. **Prérequis matériels.** Un portable Linux avec Python 3 et `pytest`. Aucun GPU. **Données :** les journaux du dossier `fixtures/` sont **synthétiques** (générés par `make_fixtures.py` avec des formats relus dans le code de NCCL, des valeurs inventées), sauf `public_nccl_docs.log`, un extrait de neuf lignes de la documentation de NCCL, avec sa source.

1.  Lisez `make_fixtures.py` : l'en-tête cite le fichier source de NCCL pour chaque format de message. Relancez-le et constatez que les fichiers committés sont reproduits à l'identique.
2.  Lancez `python3 nccl_log.py fixtures/healthy_2node_ib.log`, puis les trois journaux cassés avec `--expect` pour le code d'erreur attendu.
3.  Lisez `nccl_log.py` : repérez `ring_is_single_cycle`, la reconnaissance des lignes et la tolérance aux lignes inconnues.
4.  Ajoutez une règle de votre choix, par exemple un avertissement quand un rang passe par `via NET/IB/…` sans `/GDRDMA`, avec un test et un journal synthétique qui la déclenche.
5.  Lancez `./verify.sh`.

**Critère de réussite.** `./verify.sh` passe 11 tests et se termine par `OK nccl-log-reading: healthy log clean, 3 broken logs diagnosed with the expected code`. Le journal sain ne produit aucune erreur ; chaque journal cassé produit exactement l'erreur attendue (`socket_network`, `hca_mismatch`, `init_incomplete`).

**Pour aller plus loin.** Lancez l'analyseur sur un vrai journal de votre cluster (`NCCL_DEBUG=INFO NCCL_DEBUG_FILE=nccl.%h.%p.log`), et notez les lignes dont le format a changé. Ajoutez les lignes de la famille `TUNING` pour extraire l'algorithme et le protocole retenus.
:::

### Lab 7.3 — nccl-tests sur un vrai cluster {#lab-7-3}

::: lab

**Objectif.** Préparer et interpréter une recette `all_reduce_perf` sous Slurm sur deux nœuds de huit GPU. **Durée.** 3 h (partie A : 1,5 h, partie B : 1,5 h).

**Prérequis matériels.** Partie A : un portable Linux avec Python 3, `pytest` et `shellcheck` (optionnel). Partie B : deux nœuds de huit GPU avec Slurm, `nccl-tests` compilé avec `MPI=1` et un `srun` capable de lancer des rangs MPI ; coût indicatif : voir la page tarifaire de votre fournisseur le jour même.

**État de vérification.** La partie A est exécutée par `verify.sh` ; la partie B n'a **pas** été exécutée par l'auteur.

1.  Partie A. Lisez `run_all_reduce.sbatch` : repérez `NCCL_DEBUG_FILE` avec `%h` et `%p`, la conversion de `MIN_BUSBW_GBS` en `NCCL_TESTS_MIN_BW`, et `--gpu-bind=closest`.
2.  Lancez `./verify.sh` : `bash -n`, `shellcheck`, les neuf tests de l'analyseur et l'analyse de deux tables synthétiques (une saine, une dégradée).
3.  Lisez `parse_nccl_tests.py` : l'ajustement du modèle α-β du module 2 (moindres carrés pondérés par $1/T^2$) et les seuils.
4.  Partie B. Exportez `NCCL_TESTS_DIR` et `MIN_BUSBW_GBS` (le plateau attendu, tiré de la fiche ou d'une mesure antérieure, voir l'exemple 8.2 ; seul l'analyseur l'utilise), puis `sbatch run_all_reduce.sbatch`. Pour que `nccl-tests` fasse lui-même échouer le job, exportez aussi `MIN_AVG_BUSBW_GBS`, la moyenne « Avg bus bandwidth » d'un essai antérieur du même balayage (section 8.1).
5.  Lancez `python3 parse_nccl_tests.py nccl-allreduce-<jobid>.out --expect-busbw "$MIN_BUSBW_GBS"`, puis relancez le test avec `NCCL_TESTS_SPLIT="MOD 8"` : `sbatch run_all_reduce.sbatch -a 3` rapporte le rail le plus lent.
6.  Rédigez la recette (exemple 8.2 et section 8.6) : versions, variables, commande, plateau, écarts.

**Critère de réussite.** Partie A : `./verify.sh` se termine par `OK nccl-tests-run (lint and parser only): the GPU run itself is NOT verified here`. Partie B : l'analyseur affiche `OK nccl-tests output`, c'est-à-dire un plateau de débit de bus d'au moins 80 % du débit attendu et aucune erreur `#wrong`, et le rapport explique tout écart par rail.

**Pour aller plus loin.** Ajoutez `all_gather_perf` et `reduce_scatter_perf` et vérifiez leurs facteurs de débit de bus. Si vous avez un cluster InfiniBand, comparez `ib_write_bw` entre deux cartes (mémoire hôte puis `--use_cuda`) au résultat de NCCL.
:::

## Exercices {#ex}

Neuf exercices : quatre ★ (environ 30 minutes), trois ★★ (1 h) et deux ★★★ (1 h 30). Les constantes de débit utile (en-têtes 14 + 44 octets, 24 octets sur le fil) sont celles du chapitre 1. Les valeurs marquées « hypothèse » sont des données d'énoncé, pas des mesures.

::: exo
[Exercice 1 · ★ — Débit utile et MTU]{.tag} Un serveur envoie en RoCE v2 sur un lien de 400 Gb/s. (a) Avec une MTU IP de 1 500 octets, quelle est la plus grande MTU InfiniBand utilisable ? (b) Quel débit utile, en Go/s, obtient-on avec cette MTU, puis avec une MTU InfiniBand de 4 096 sur des trames jumbo ? (c) Combien de Go/s et quel pourcentage perd-on avec la première ?
:::

::: sol
(a) La MTU IP doit contenir la charge utile plus 44 octets : $1500 - 44 = 1456$. Parmi 256, 512, 1 024, 2 048 et 4 096, la plus grande valeur qui tient est 1 024.

(b) Le débit utile vaut $m/(m + 14 + 44 + 24)$. Pour 1 024 : $1024/1106 = 0{,}9259$, soit 46,29 Go/s sur 50. Pour 4 096 : $4096/4178 = 0{,}9804$, soit 49,02 Go/s.

(c) La perte est de $49{,}02 - 46{,}29 = 2{,}73$ Go/s, soit 5,6 % du débit utile à 4 096. Vérification : `python3 fabric.py --goodput 1024 4096`.
:::

::: exo
[Exercice 2 · ★ — Le trafic mémoire que GPUDirect épargne]{.tag} Un serveur de 8 GPU envoie 4 Gio par GPU et par étape, et en reçoit autant. Sans GPUDirect RDMA, chaque octet émis est écrit puis relu dans la mémoire de l'hôte, et chaque octet reçu aussi. (a) Quel volume de trafic mémoire par étape ? (b) La carte de chaque GPU tient 49,0 Go/s (chapitre 1) : quelle durée de réseau et quel débit mémoire cela exige-t-il ? (c) Si la mémoire de l'hôte soutient 500 Go/s (hypothèse), de combien l'étape est-elle ralentie ?
:::

::: sol
(a) Par GPU : $4 \times 2$ Gio à l'émission et $4 \times 2$ Gio à la réception, soit 16 Gio ; pour 8 GPU, 128 Gio.

(b) Quatre Gio à 49,02 Go/s durent $4 \times 2^{30} / 49{,}02 \cdot 10^{9} = 0{,}0876$ s. Le débit mémoire requis vaut $128 \times 2^{30} / 0{,}0876 \approx 1\,569$ Go/s, soit 1,6 To/s.

(c) À 500 Go/s, la mémoire met $128 \times 2^{30} / 500 \cdot 10^{9} = 0{,}275$ s : 3,1 fois plus que le réseau. La mémoire de l'hôte devient le goulot, ce qui justifie GPUDirect RDMA (chapitre 2).
:::

::: exo
[Exercice 3 · ★ — Lire `ibstat`]{.tag} Voici trois extraits **fictifs** de `ibstat`, sur un nœud de 8 cartes de 400 Gb/s.

~~~text
CA 'mlx5_2'   Port 1: State: Active   Physical state: LinkUp   Rate: 400  Link layer: InfiniBand
CA 'mlx5_5'   Port 1: State: Active   Physical state: LinkUp   Rate: 100  Link layer: InfiniBand
CA 'mlx5_6'   Port 1: State: Init     Physical state: LinkUp   Rate: 400  Link layer: InfiniBand
~~~

(a) Appliquez la liste de contrôle du chapitre 3 : quelles cartes sont en défaut, et pourquoi ? (b) Dans un modèle où NCCL répartit les données à parts égales entre 8 canaux, un canal par carte, quel est l'effet de la carte `mlx5_5` sur le débit de bus du nœud, avec 49,0 Go/s par carte saine ?
:::

::: sol
(a) `mlx5_2` est saine : `Active`, `LinkUp`, 400. `mlx5_5` est `Active` mais négocie 100 au lieu de 400 : c'est la baisse de débit inattendue (*downshift*) que la documentation de NCCL demande de détecter ; cherchez câble, émetteur-récepteur ou port du commutateur. `mlx5_6` est en `Init` : le lien est physiquement monté mais le port n'est pas configuré, ce qui pointe vers le gestionnaire de sous-réseau (injoignable ou arrêté, ou balayage pas encore passé).

(b) Chaque canal porte un huitième des données. Le canal de `mlx5_5` va quatre fois moins vite, donc l'opération dure quatre fois plus : le débit de bus tombe à un quart, environ $49{,}0/4 = 12{,}3$ Go/s au lieu de 49,0. Ce résultat vient du modèle à parts égales, qui est une hypothèse ; un autre partage donnerait un autre chiffre, mais jamais le débit d'une carte saine.
:::

::: exo
[Exercice 4 · ★★ — La réserve de tampon de PFC]{.tag} Pour qu'un PFC suffise, le tampon d'un port doit pouvoir absorber ce qui arrive pendant que la pause se propage : $B \times (2 t_{\text{prop}} + t_{\text{réaction}})$ plus deux trames maximales. C'est un modèle simplifié, un ordre de grandeur et non la formule d'un constructeur.

Hypothèses : lien de 50 Go/s, 5 ns par mètre de fibre, réaction de 1 µs, trame de 4 096 + 82 octets, commutateur de 64 ports, tampon partagé de 64 Mo.

(a) Calculez la réserve par port et par priorité pour des câbles de 100 m, puis 500 m. (b) Quelle part du tampon prennent 2 priorités sans perte sur 64 ports, dans chaque cas ? (c) Combien de priorités tiennent dans 25 % du tampon à 100 m ? Concluez.
:::

::: sol
(a) À 100 m, le délai vaut :

$$2 \times 100 \times 5\ \text{ns} + 1\ \mu\text{s} = 2\ \mu\text{s}$$

Les octets en vol valent $50 \cdot 10^{9} \times 2 \cdot 10^{-6} = 100\,000$ ; deux trames ajoutent $2 \times 4178 = 8\,356$ : 108 356 octets. À 500 m, le délai vaut 6 µs : 300 000 + 8 356 = 308 356 octets.

(b) Pour $64 \times 2 = 128$ réserves : 13,87 Mo à 100 m, soit 21,7 % de 64 Mo ; 39,47 Mo à 500 m, soit 61,7 %.

(c) Dans 25 % de 64 Mo, soit 16 Mo : $16 \cdot 10^{6} / (64 \times 108\,356) = 2{,}3$ : 2 priorités à 100 m. À 500 m, le même calcul donne 0,81 : aucune priorité n'y tient.

Conclusion : plus les câbles s'allongent, plus la réserve consomme le tampon qui sert aussi à absorber les rafales. Un PFC sûr se limite à des liaisons courtes et à peu de priorités ; c'est un argument pour le DCQCN de Meta ou de ByteDance (chapitre 4) qui cherche à déclencher le marquage avant la pause.
:::

::: exo
[Exercice 5 · ★ — Sur-souscription et placement des rangs]{.tag} Un fabric de 2 048 GPU est sur-souscrit à 3:1 : 43 feuilles de 48 GPU ; une carte débite 50 Go/s. Utilisez $B_{\text{eff}} = B/(1 + f(o-1))$. (a) Quelle fraction $f$ du trafic d'un anneau traverse les feuilles si les rangs consécutifs partagent la feuille ? (b) Et si l'ordre des rangs est aléatoire ? (c) Donnez $B_{\text{eff}}$ dans les deux cas, et la fraction maximale $f$ qui conserve 80 % de $B$.
:::

::: sol
(a) Dans un anneau de 2 048 rangs, il y a 2 048 liens ; avec un ordre par feuille, seul le passage d'une feuille à la suivante traverse : 43 liens, donc $f = 43/2048 = 0{,}021$.

(b) Avec un ordre aléatoire, le rang suivant est dans une autre feuille avec la probabilité $1 - 47/2047 = 0{,}977$ : $f \approx 0{,}977$.

(c) Cas (a) : $50/(1 + 0{,}021 \times 2) = 48{,}0$ Go/s. Cas (b) : $50/(1 + 0{,}977 \times 2) = 16{,}9$ Go/s. Pour 80 % : $1/(1+2f) \ge 0{,}8$ donne $f \le 0{,}125$. L'ordre des rangs, donc le placement, change le débit d'un facteur près de 3 sur un fabric sur-souscrit.

Limite du modèle : c'est une moyenne, alors qu'un anneau est borné par son lien le plus lent. En (a), chaque feuille ne fait monter qu'un flux, qui tient dans un seul de ses 16 liens montants : le débit réel est plus proche de 50 que de 48 Go/s. En (b), jusqu'à 48 flux se partagent 16 liens montants, au mieux un tiers de $B$ (16,7 Go/s) : le modèle y est presque exact.
:::

::: exo
[Exercice 6 · ★★ — Lire une matrice de chemins]{.tag} Voici la distance, **fictive**, que NCCL pourrait détecter dans un serveur à 4 GPU (G0 à G3) et 2 cartes (N0, N1), avec les types de chemin du chapitre 6. G0 et G1 sont sur le socket 0, G2 et G3 sur le socket 1.

| | G1 | G2 | G3 | N0 | N1 |
|---|---|---|---|---|---|
| G0 | NVL | NVL | NVL | PIX | SYS |
| G1 | | NVL | NVL | PXB | SYS |
| G2 | | | NVL | SYS | PIX |
| G3 | | | | SYS | PXB |

(a) Avec `NCCL_P2P_LEVEL=PIX`, G0 et G3 utilisent-ils le pair-à-pair ? (b) Avec `NCCL_NET_GDR_LEVEL=PIX`, quels GPU gardent GPUDirect RDMA ? Et avec `PXB` ? (c) Quelle carte chaque GPU doit-il utiliser, et combien de GPU partagent chaque carte ? (d) Avec `NCCL_NET_GDR_LEVEL=LOC`, que devient le trafic réseau ?
:::

::: sol
(a) Oui. Le type `NVL` est plus proche que `PIX` ; la distance maximale autorisée est donc respectée. Le pair-à-pair reste actif entre GPU reliés en NVLink.

(b) Avec `PIX` : seuls G0 (avec N0) et G2 (avec N1), dont les chemins vers leur carte sont de type `PIX`. G1 et G3 sont à distance `PXB` de leur carte et perdent GPUDirect : leur trafic passe par la mémoire de l'hôte. Avec `PXB`, les quatre GPU le gardent.

(c) G0 et G1 utilisent N0 (même socket), G2 et G3 utilisent N1 : deux GPU par carte. Si la carte est de 50 Go/s, chaque GPU dispose de 25 Go/s au plus quand les deux émettent ensemble ; le serveur n'a que deux « rails » pour quatre GPU.

(d) `LOC` interdit toujours GPUDirect : tout le trafic réseau est transféré via la mémoire de l'hôte (chapitre 2), avec le surcoût de l'exercice 2.
:::

::: exo
[Exercice 7 · ★★ — Faut-il sur-souscrire ?]{.tag} Vous dimensionnez le réseau d'un cluster de 2 048 GPU, un port de 400 Gb/s par GPU, commutateurs de 64 ports. Option A : 1:1. Option B : 48 ports vers les GPU et 16 vers les colonnes (≈ 3:1).

(a) Donnez commutateurs et émetteurs-récepteurs inter-commutateurs de chaque option, et les économies de B. Rappel : feuilles = ⌈GPU / ports bas⌉ ; liens montants = feuilles × ports hauts ; colonnes = ⌈liens montants / 64⌉ ; deux émetteurs-récepteurs par lien.

(b) Les gradients de 7 milliards de paramètres en BF16 (14 Go) sont réduits par un anneau de 2 048 rangs, de durée $2\,\frac{p-1}{p}\,\frac{n}{B}$ (latence négligée, module 2) : calculez le temps de communication sans sur-souscription, puis avec $o = 3$ pour $f = 0{,}1$ et $f = 0{,}25$.

(c) Sur une étape de 5,0 s (hypothèse) dont cette communication n'est pas recouverte, quel surcoût de temps et quel seuil de rentabilité en part du coût total du cluster ?
:::

::: sol
(a) A : 64 feuilles et 32 colonnes, soit 96 commutateurs et 4 096 émetteurs-récepteurs. B : 43 feuilles et 11 colonnes, soit 54 commutateurs et 1 376 émetteurs-récepteurs (`python3 fabric.py --endpoints 2048 --radix 64 --leaf-down 48`). Économies : $1 - 54/96 = 43{,}8$ % des commutateurs et $1 - 1376/4096 = 66{,}4$ % des émetteurs-récepteurs.

(b) Avec le temps de l'anneau, latence négligée :

$$T = 2\,\frac{p-1}{p}\,\frac{n}{B}$$

On obtient 0,560 s à 50 Go/s. Avec $f = 0{,}1$, le débit effectif vaut 41,7 Go/s et $T = 0{,}672$ s. Avec $f = 0{,}25$, il vaut 33,3 Go/s et $T = 0{,}840$ s.

(c) Le surcoût vaut 0,112 s (2,2 % de 5,0 s) pour $f = 0{,}1$, et 0,280 s (5,6 %) pour $f = 0{,}25$. Un temps d'étape plus long de 2,2 % revient à 2,2 % d'heures-GPU en plus.

B est rentable si ses économies dépassent environ 2,2 % du coût total du cluster, à $f = 0{,}1$ ; 5,6 % si le placement est moins bon. Sans les prix réels (consultez les devis du jour), on ne peut pas conclure ; on sait en revanche que la décision dépend de $f$, donc du placement et de la parallélisation choisie, et qu'un recouvrement du calcul et de la communication réduirait le surcoût.
:::

::: exo
[Exercice 8 · ★★★ — Un rang qui ne finit jamais son initialisation]{.tag} Le job de 16 rangs sur 2 nœuds se bloque au démarrage, sans erreur. L'analyseur du lab 7.2 affiche (journal **synthétique** `hang_in_init.log`) :

~~~text
hang_in_init.log: NCCL 2.30.3+cuda13.0; 16/16 ranks on 2 nodes; network IB; HCAs per host {'node-01': 8, 'node-02': 8}; channels [4]; init complete on 15 ranks
  [ERROR] init_incomplete: ranks without 'Init COMPLETE': [11] (stuck in initialisation or log truncated)
~~~

Les lignes des rangs voisins sont `node-02:4010 [2] … Channel 00/0 : 10[2] -> 11[3] via P2P/CUMEM` puis `… Init COMPLETE` pour le rang 10 ; pour le rang 11 (`node-02:4011 [3]`), la dernière ligne est `Channel 03/0 : 11[3] -> 12[4] via P2P/CUMEM` : les quatre canaux sont décrits, mais `Init COMPLETE` manque. (a) Que peut-on établir avec certitude, et que ne peut-on pas ? (b) Donnez cinq vérifications ordonnées, avec les commandes. (c) Quel changement de journalisation évite l'ambiguïté « journal tronqué » ?
:::

::: sol
(a) Établi : les 16 rangs ont écrit leur ligne de communicateur ; 15 ont terminé ; le rang 11 est celui du GPU local 3 du second nœud ; le réseau retenu est IB sur les deux nœuds et les 8 cartes y sont vues. Non établi : la cause. Le journal montre où le rang s'arrête, pas pourquoi ; et rien ne distingue un processus bloqué d'un journal tronqué ou d'une sortie non vidée.

(b) Dans l'ordre : 1) le processus 11 est-il vivant (`ps`, `nvidia-smi`) et que fait-il (`py-spy dump` ou `strace -p`) ? 2) le noyau du nœud 2 signale-t-il une erreur de GPU ou de carte (`dmesg`) ? 3) la carte de ce rail est-elle saine (`ibstat`, état et débit de `mlx5_3`) ? 4) la connectivité réseau est-elle bonne entre les deux nœuds (`ib_write_bw` sur `mlx5_3`) ? 5) un `all_reduce_perf` à deux nœuds hors du nœud 2 passe-t-il (bissection du chapitre 8) ?

(c) Un fichier de journal par processus, avec `NCCL_DEBUG_FILE=nccl.%h.%p.log`, et `NCCL_DEBUG_SUBSYS=INIT,NET` pour avoir les lignes de connexion. La documentation précise que, si le nom de fichier n'est pas unique entre processus, la sortie peut être perdue ou corrompue. Avec un fichier par processus, l'absence de `Init COMPLETE` devient un fait, pas un doute.
:::

::: exo
[Exercice 9 · ★★★ — Diagnostic intégré : table et journal]{.tag} Sur un cluster de 16 GPU sur 2 nœuds, la recette donne (tables et journaux **synthétiques**, supposés issus du même cluster) :

~~~text
all_reduce_synthetic_degraded.txt: 32 sizes; plateau busbw 26.2 GB/s; 90% of it reached at 67108864 B; smallest-size time 364.9 us; fit {'B_gbs': 25.951, 'alpha_us': 12.129, 'intercept_us': 363.885}
  PROBLEM: plateau busbw 26.2 GB/s is 55% of the expected 48 GB/s (tolerance 80%)
degraded_rail.log:  HCAs per host {'node-01': 8, 'node-02': 7}
  [ERROR] hca_mismatch: hosts see different numbers of HCAs: {'node-01': 8, 'node-02': 7}
  [WARN ] gdr_disabled: GPU Direct RDMA disabled for ['node-01:mlx5_3']
~~~

(a) Quel rapport plateau/attendu, et que prédit l'hypothèse « un rail à moitié de sa capacité, parts égales » ? (b) Le journal propose deux causes ; lesquelles, et comment les séparer ? (c) Proposez le plan d'essais pour un parc de 128 nœuds, avec le nombre maximal d'essais. (d) Que mettez-vous dans le rapport d'incident ?
:::

::: sol
(a) $26{,}2/48 = 0{,}546$, soit 55 %. Avec huit canaux à parts égales dont un à moitié de débit, le temps double et le plateau vaut $48/2 = 24$ Go/s ; l'écart avec 26,2 est de 9 %, cohérent avec le modèle. Attention : le générateur de la table a simplement fixé $B = 26$ Go/s ; la lecture « un rail à moitié » est une hypothèse d'exercice, pas une propriété de la table.

L'ajustement α-β retrouve la même bande passante effective (25,95 Go/s) et un α inchangé (12,1 µs) : la latence n'a pas bougé, c'est la bande passante qui a chuté. Cela exclut un problème de petits messages.

(b) Cause 1 : sur le nœud 2, il manque la carte 5 (7 cartes pour 8 GPU) ; deux GPU doivent partager une carte, soit un rail à moitié de capacité. Cause 2 : sur le nœud 1, GPUDirect RDMA est désactivé pour `mlx5_3` ; le trafic de ce rail transite par la mémoire de l'hôte.

Pour les séparer : `NCCL_TESTS_SPLIT="MOD 8"` avec `-a 3` confirme qu'un rail est lent mais ne le nomme pas ; `ibstat` sur chaque carte, puis un essai à deux nœuds avec un seul GPU par nœud (le GPU 5, puis le GPU 3) désignent le coupable. Un essai lent avec le GPU 5 désigne la cause 1, avec le GPU 3 la cause 2 ; si les deux le sont, les deux causes existent.

(c) Un premier essai par rail identifie le rail. Ensuite une bissection sur les 128 nœuds : $\lceil \log_2 128 \rceil = 7$ essais pour isoler un nœud. Au plus 8 essais, contre 128 un par un. Seuil fixé à l'avance : 80 % du plateau attendu, avec `--expect-busbw 48` de l'analyseur (tolérance par défaut 0,8).

(d) Les versions de NCCL et du pilote, les variables posées, la commande exacte, le plateau attendu et sa source, la table par rail, la liste des nœuds exclus, la cause trouvée, la correction et la table de contrôle après correction. Mention explicite : les chiffres de cet exercice sont synthétiques.
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux convertir un débit de fiche en débit attendu.** Preuve : l'exercice 1 refait pour votre carte et votre MTU, avec le débit utile en Go/s.
-   **Je peux expliquer RDMA et GPUDirect.** Preuve : le schéma du chapitre 2 redessiné pour votre serveur, avec le trafic mémoire de l'exercice 2.
-   **Je peux lire l'état d'un sous-réseau InfiniBand.** Preuve : l'exercice 3 refait sur la sortie réelle de `ibstat` d'un de vos nœuds, ou sur la sortie du lab 7.1 partie B.
-   **Je peux comparer InfiniBand et RoCE v2 avec des sources.** Preuve : le tableau du chapitre 4 complété pour votre contexte, avec une source par ligne.
-   **Je peux dimensionner un fat-tree.** Preuve : le calculateur du lab 7.1 et l'arbitrage chiffré de l'exercice 7.
-   **Je peux lire un journal NCCL.** Preuve : l'analyseur du lab 7.2 et le diagnostic de l'exercice 8.
-   **Je peux recetter un réseau d'entraînement.** Preuve : le script du lab 7.3 et un rapport de recette au format de la section 8.6.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Notre job de 128 GPU atteint la moitié du débit de bus attendu. Par où commencez-vous ?* Réponse-type : fixer l'attendu et sa source, puis descendre par couches : `ibstat` (débit, état), journal NCCL (réseau, GPUDirect, nombre de cartes), `nccl-tests` par rail avec `NCCL_TESTS_SPLIT`, `ib_write_bw` entre paires, compteurs `rdma statistic`. Isoler par bissection, écrire les mesures dans un rapport.
2.  *InfiniBand ou RoCE pour 4 096 GPU ?* Réponse-type : les deux ont servi à des entraînements de grande taille (Llama 3 sur les deux, réglés pour des performances équivalentes) ; décider sur le coût, les compétences, le fournisseur et le propriétaire du réglage de la congestion. Citer les risques de RoCE (PFC, hachage ECMP) et ceux d'InfiniBand (SM, écosystème fermé), puis demander un essai de recette sur chaque option.
3.  *Pourquoi ne pas sur-souscrire à 3:1 pour économiser ?* Réponse-type : cela dépend de la fraction du trafic qui traverse le niveau. Avec un placement sensible à la topologie, le surcoût peut être faible ; avec un placement quelconque, le débit est divisé par le taux. Chiffrer les deux cas, comparer au coût du réseau, et prévoir comment l'ordonnanceur garantit le placement.

## Lectures et références {#refs}

-   NVIDIA. *NCCL User Guide* : [Environment Variables](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html), [Troubleshooting](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting.html), [Logging](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting/logging.html). Consulté le 24 octobre 2026 (version 2.32 en en-tête). Chapitres 6 à 8 : variables, formats de journal, dépannage.
-   NVIDIA. *nccl-tests* : [README](https://raw.githubusercontent.com/NVIDIA/nccl-tests/master/README.md) et [PERFORMANCE.md](https://raw.githubusercontent.com/NVIDIA/nccl-tests/master/doc/PERFORMANCE.md). Chapitre 8 : options, débit algorithmique et de bus.
-   Zhu et al. *Congestion Control for Large-Scale RDMA Deployments* (DCQCN). SIGCOMM 2015. [PDF](https://conferences.sigcomm.org/sigcomm/2015/pdf/papers/p523.pdf). Chapitre 4, sections 2 et 3.
-   Guo et al. *RDMA over Commodity Ethernet at Scale*. SIGCOMM 2016. [PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/11/rdma_sigcomm2016.pdf). Chapitre 4, section 4 : livelock, interblocage, tempête de pause.
-   Al-Fares, Loukissas, Vahdat. *A Scalable, Commodity Data Center Network Architecture*. SIGCOMM 2008. [PDF](http://ccr.sigcomm.org/online/files/p63-alfares.pdf). Chapitre 5, section 3.
-   Dubey et al. [*The Llama 3 Herd of Models*](https://arxiv.org/abs/2407.21783). 2024. Section 3.3 : réseau RoCE de 24 000 GPU, sur-souscription, équilibrage, journalisation de NCCLX.
-   Jiang et al. [*MegaScale*](https://arxiv.org/abs/2402.15627). 2024. Section 3.6 : topologie, conflits ECMP, contrôle de congestion, délais de retransmission.
-   Qian et al. *Alibaba HPN: A Data Center Network for Large Language Model Training*. SIGCOMM 2024. [PDF](https://ennanzhai.github.io/pub/sigcomm24-hpn.pdf). Chapitre 5 : deux plans, deux commutateurs de baie.
-   NVIDIA. [*DGX SuperPOD H100 Reference Architecture*](https://docs.nvidia.com/dgx-superpod/reference-architecture-scalable-infrastructure-h100/latest/network-fabrics.html), pages « DGX SuperPOD Architecture » et « Network Fabrics » ; [*DGX H100 User Guide*](https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html). Chapitres 5 et 6 : comptes de composants, cartes du serveur.
-   NVIDIA. [*NVIDIA H100*](https://www.nvidia.com/en-us/data-center/h100/) et [*Quantum-2 InfiniBand*](https://www.nvidia.com/en-us/networking/quantum2/), pages produit consultées le 24 octobre 2026. Chapitres 3 et 6 : NVLink, ConnectX-7, 64 ports de 400 Gb/s.
-   NVIDIA. [*Massively Scale Your Deep Learning Training with NCCL 2.4*](https://developer.nvidia.com/blog/massively-scale-deep-learning-training-nccl-2-4/). Chapitre 7 : arbres binaires doubles.
-   NVIDIA. [*GPUDirect RDMA*](https://docs.nvidia.com/cuda/gpudirect-rdma/) et [*GPUDirect Storage*](https://docs.nvidia.com/gpudirect-storage/overview-guide/index.html). Chapitre 2.
-   Patarasuk, Yuan. [*Bandwidth optimal all-reduce algorithms for clusters of workstations*](https://www.cs.fsu.edu/~xyuan/paper/09jpdc.pdf). JPDC 69, 2009. Origine de la borne $2n(p-1)/p$ du module 2.
-   SchedMD. [*Topology Guide*](https://slurm.schedmd.com/topology.html). Chapitre 5, placement : voir aussi le [chapitre 5 du module 5](../slurm/index.html#ch5).

## Sources et portée {#sources}

### Documenté {#documente}

Les noms, versions d'introduction et comportements des variables et algorithmes de NCCL (guide d'utilisation, pages « Environment Variables », « Troubleshooting », « Logging »), les formules de débit de bus et les options de `nccl-tests`, la variable `NCCL_TESTS_MIN_BW` et la structure du tableau de sortie (code source de `nccl-tests`), les formats des messages de journal de NCCL (code source de `init.cc`, `search.cc`, `topo.cc`, `p2p.cc`, `net.cc` et `bootstrap.cc`), les tailles d'en-têtes (`ib_pack.h` du noyau Linux) et les valeurs de MTU (`verbs.h`), le port UDP 4791 (registre de l'IANA), les affirmations sur DCQCN, PFC et ECN (article de DCQCN, RFC 3168), les trois pannes de Guo et al., les formules du fat-tree (Al-Fares et al.), les comptes du DGX SuperPOD H100, les débits des cartes et commutateurs (pages NVIDIA), les réseaux de Llama 3, MegaScale et HPN, et la latence logarithmique des arbres binaires doubles ont été relus à la source le 24 octobre 2026. Les sorties d'OpenSM 3.3.23, `ibsim` 0.10, `infiniband-diags` 50.0 et `perftest` 24.01.0 sont celles du bac à sable ; les calculs des exemples et des corrigés sont refaits par `labs/networking/topology-sizing/fabric.py` ou par un script Python.

### Recommandé {#recommande}

L'ordre des chapitres, le modèle jouet de sur-souscription, la réserve de tampon PFC de l'exercice 4, le modèle à parts égales entre canaux, la bissection, le seuil de 80 % du plateau attendu et la liste de contrôle en couches sont des choix pédagogiques de ce parcours, pas des normes. Les valeurs de latence de l'exemple 7.1 et tous les chiffres « hypothèse » sont des données d'école.

### À vérifier {#a-verifier}

(1) Les 24 octets de trame Ethernet sur le fil (séquence de contrôle, préambule, espace inter-trame), l'encodage 64b/66b, la norme IEEE 802.1Qbb de PFC, la correspondance XDR = 800 Gb/s, les noms exacts des compteurs de port InfiniBand et le niveau 2 sans perte avec contrôle de flux par crédits d'InfiniBand sont des connaissances courantes **non relues** dans la spécification (payante ou inaccessible depuis le bac à sable). (2) Les mécanismes du routage adaptatif, de SHARP, de `PXN` et des algorithmes CollNet dépendent de la version et n'ont pas été relus. (3) L'article fondateur du dragonfly et le fat-tree de Leiserson (1985) n'ont pas été relus. (4) La lecture du « 1:7 » de Llama 3 comme « un septième de la bande passante » est une interprétation. (5) Les journaux NCCL et les tables `nccl-tests` du module sont **synthétiques** : les formats changent d'une version à l'autre et aucune exécution sur GPU n'a eu lieu. (6) Les pages produit de NVIDIA ne précisent pas si les 900 Go/s de NVLink se comptent par sens ou en bidirectionnel. (7) Plusieurs éditeurs (ACM, IEEE Xplore) répondent 403 aux outils automatiques : les articles sont lus sur les copies d'auteur citées.

### Hors périmètre {#hors-perimetre}

L'architecture interne des commutateurs, Ultra Ethernet, les réseaux d'inférence, le réseau de stockage (module 8), le choix d'un parallélisme et son recouvrement (module 9), la supervision (module 14) et le coût des réseaux, dont les prix changent chaque trimestre : consultez les devis du jour.
