---
title: "Pannes, checkpointing et reprise automatique"
subtitle: "Module 10 · Phase 3 · 28 h"
description: "Modéliser les pannes d'un entraînement à grande échelle, écrire des checkpoints corrects et rapides, détecter, isoler et reprendre sans intervention humaine, et tester tout cela par injection de pannes."
module:
  id: fault-tolerance
  number: 10
  phase: 3
  hours: 28
  level: 3
prerequisites: [distributed-training, storage]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs vérifiés dans un bac à sable (CPU, pannes simulées)", class: verified}
labs:
  - {id: young-daly, kind: sandbox}
  - {id: atomic-checkpoint, kind: sandbox}
  - {id: supervisor-loop, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** un entraînement de plusieurs semaines sur des milliers de GPU sera interrompu des dizaines, voire des centaines de fois. Comment faire pour que ces interruptions coûtent dix pour cent du temps de calcul plutôt que soixante, et pour que personne ne soit réveillé à trois heures du matin pour relancer un job ?

Ce module répond en six temps. Il **chiffre** la panne (taxonomie, données publiées, loi des grands nombres), **modélise** son coût (Young, Daly, goodput), apprend à **écrire** un checkpoint correct puis rapide, à **détecter** les pannes franches et silencieuses, à **reprendre** automatiquement en isolant le nœud fautif, et à **tester** le tout par injection de pannes. Les labs tournent sur un portable, sans GPU, avec des pannes simulées et signalées comme telles.

::: key
[Règle de ce module]{.tag} Une panne n'est pas un accident à éviter, c'est un paramètre de conception. La bonne question n'est pas « comment l'empêcher ? » mais « combien coûte-t-elle, en GPU-heures, et comment ce coût change-t-il quand je modifie la fréquence de checkpoint, le temps de détection ou le temps de relance ? »
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 28 h, dont environ 10 h de lecture, 10 h de labs et 8 h d'exercices |
| Niveau d'entrée | 3 : vous savez lancer un entraînement distribué avec `torchrun` et écrire un `state_dict` sur disque |
| Prérequis | [Module 9 — Entraînement distribué](../distributed-training/index.html), [Module 8 — Stockage](../storage/index.html) |
| Pour qui | Cœur : reprise après panne à grande échelle, coût des checkpoints et procédures d'exploitation. |
| Livrable | un entraîneur dont la reprise est prouvée identique à une exécution sans panne, son superviseur, et un tableau chiffré du coût des pannes |
| Environnement | un portable CPU suffit pour les trois labs ; aucun GPU. Les scripts Slurm et Kubernetes du chapitre 6 sont linté seulement |
| Projets liés | [Projet 3 — Entraîneur tolérant aux pannes](../../projects/resilient-trainer/index.html), [Projet 5 — Observabilité GPU](../../projects/gpu-observability/index.html), [Projet 6 — RFC de plateforme](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Estimer le temps moyen entre pannes d'un job à partir d'un taux de panne par nœud, et en déduire le temps perdu (chapitres 1 et 2).
-   Calculer l'intervalle de checkpoint de Young et de Daly, et dire quand ces formules cessent d'être fiables (chapitre 2, lab 10.1).
-   Écrire un checkpoint atomique et complet, et prouver par `kill -9` que la reprise est identique à une exécution sans panne (chapitre 3, lab 10.2).
-   Chiffrer le coût d'un checkpoint synchrone, asynchrone ou en mémoire, et choisir une architecture de stockage (chapitre 4).
-   Choisir des délais de détection et expliquer comment repérer un nœud lent ou silencieux (chapitre 5).
-   Concevoir une boucle de reprise qui isole le nœud fautif et ne boucle pas indéfiniment (chapitre 6, lab 10.3).
-   Lire un journal d'erreurs GPU (Xid, ECC) et décider : relancer le job, drainer le nœud ou ouvrir un dossier fournisseur (chapitre 7).
-   Préparer un test de chaos, un runbook et un post-mortem sans blâme (chapitre 8).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 3 — Systèmes d'entraînement distribué** (semaines 23-31) : faire tourner un entraînement multi-nœuds qui survit aux pannes.
-   **S'appuie sur** : [module 9 — Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline](../distributed-training/index.html), [module 8 — Stockage et E/S pour l'entraînement](../storage/index.html).
-   **Prépare** : [module 13 — Flotte multi-fournisseurs : SkyPilot, GPU clouds, hyperscalers et centres HPC](../multi-cloud/index.html).
-   **Projets qui s'en servent** : [Projet 3 — Entraîneur tolérant aux pannes](../../projects/resilient-trainer/index.html), [Projet 5 — Observabilité GPU et détection de pannes silencieuses](../../projects/gpu-observability/index.html), [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html).
<!-- /gen:place -->

### Plan de séances {#seances}

Dix séances, soit 28 h : six de 3 h et quatre de 2,5 h. Le niveau ne diminue jamais d'une séance à la suivante.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 3 h | 1 | ch. 1 Pannes à grande échelle | Ex. 1, 4 ; questions de positionnement |
| 2 | 3 h | 1 | ch. 2 Modèle de coût, première moitié (Young) | Ex. 2 |
| 3 | 3 h | 2 | ch. 2 seconde moitié (Daly, ETTR, dimensionnement) | Lab 10.1 ; Ex. 3 |
| 4 | 3 h | 2 | ch. 3 Checkpoint correct | Lab 10.2 partie A ; Ex. 12 |
| 5 | 2.5 h | 2 | ch. 3 suite (formats, reproductibilité), début du ch. 4 | Lab 10.2 partie B |
| 6 | 2.5 h | 2 | ch. 4 Checkpoints rapides | Ex. 6 |
| 7 | 2.5 h | 3 | ch. 5 Détection | Ex. 7 |
| 8 | 3 h | 3 | ch. 6 Reprise et élasticité | Lab 10.3 ; Ex. 5, 10 |
| 9 | 3 h | 3 | ch. 7 Erreurs GPU courantes | Ex. 8, 9 |
| 10 | 2.5 h | 3 | ch. 8 Chaos et procédures, synthèse | Ex. 11 ; checkpoint de sortie |

<!-- gen:travailler -->
### Comment travailler ce module {#travailler}

Le parcours s'adresse à plusieurs profils d'entrée, décrits dans le [point de départ](../../profile/index.html). Le tableau donne la priorité conseillée pour ce module ; les questions de positionnement (section 0.1) la confirment ou la corrigent.

| Profil d'entrée | Priorité | Ce que cela veut dire ici |
|---|---|---|
| Ingénieur plateforme, SRE ou DevOps | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Administrateur ou ingénieur HPC | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Ingénieur ML ou chercheur | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Développeur logiciel ou systèmes | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Étudiant ou personne en reconversion | à fond | tous les chapitres, tous les labs et les exercices ★★★ |

**À ne pas survoler.** Le modèle de Young et Daly et la détection des blocages reviennent dans les projets 3, 4 et 5.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le checkpoint de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si elles vous semblent routinières, lisez le chapitre 2 puis passez directement aux exercices ★★★.

1.  **Perte attendue.** Un job écrit un checkpoint toutes les 60 minutes. En moyenne, combien de travail perd-il à chaque panne, et pourquoi ?

2.  **Atomicité.** Un script appelle `torch.save(state, "ckpt.pt")` toutes les 10 minutes. Que contient `ckpt.pt` si la machine s'éteint pendant l'écriture ?

3.  **Échelle.** Si un nœud tombe en panne en moyenne tous les 150 jours, combien de pannes attendez-vous par jour sur 2 000 nœuds ?

::: sol
**Réponses.**

1.  En moyenne la moitié de l'intervalle, soit 30 minutes : la panne tombe n'importe où dans l'intervalle, de façon uniforme si les pannes sont indépendantes de la position dans le cycle. Voir le chapitre 2.

2.  Un fichier tronqué ou mélangé, sans que rien ne le signale, et l'ancien checkpoint a déjà été écrasé. Il faut écrire dans un fichier temporaire, forcer l'écriture sur disque (`fsync`), puis renommer. Voir le chapitre 3.

3.  $2000/150 \approx 13{,}3$ pannes par jour, soit une panne toutes les 1,8 heure environ. Voir le chapitre 1.
:::

## 1. Pannes à grande échelle {#ch1}

Un petit cluster tombe rarement en panne, un grand cluster tombe en panne tout le temps, et ce n'est pas une question de qualité du matériel : c'est de l'arithmétique. Ce chapitre donne la taxonomie des pannes, les ordres de grandeur publiés et le calcul qui relie le taux de panne d'un nœud au temps moyen entre pannes d'un job.

### 1.1. La loi des grands nombres appliquée aux GPU

Un entraînement synchrone est un **système en série** : tous les rangs doivent fonctionner pour que le pas avance. Si $N$ nœuds tombent en panne indépendamment, au taux $r$ pannes par nœud et par jour, le job subit $Nr$ pannes par jour et son temps moyen entre pannes (*MTBF*, *mean time between failures*) est l'inverse :

$$\text{MTBF}_{\text{job}} = \frac{1}{N\,r} = \frac{\text{MTBF}_{\text{nœud}}}{N}$$

Doubler la taille du job divise donc par deux le temps entre pannes. C'est la raison pour laquelle un job de 8 GPU sur un nœud peut tourner des mois sans incident, alors qu'un job de 16 000 GPU est interrompu plusieurs fois par jour.

::: ex
[Exemple 1.1 — De 6,5 pannes pour mille nœuds-jours au MTBF d'un job]{.tag} Kokolis et ses coauteurs ont mesuré, sur un cluster de recherche de 16 000 GPU, un taux de 6,50 pannes pour mille nœuds-jours ([Kokolis et al., 2024](https://arxiv.org/abs/2410.21680)). Un nœud tombe donc en moyenne tous les $1/0{,}0065 \approx 154$ jours. Avec 8 GPU par nœud, le calcul $24\,/\,(N \times 0{,}0065)$ donne, **calculé ici** :

| GPU | Nœuds | MTBF du job |
|---|---|---|
| 512 | 64 | 57,7 h |
| 1 024 | 128 | 28,8 h |
| 4 096 | 512 | 7,2 h |
| 16 384 | 2 048 | 1,80 h |
| 131 072 | 16 384 | 0,225 h |

Les deux dernières lignes reproduisent les projections de l'article (« 1.8 hours » pour 16 384 GPU, « 0.23 hours » pour 131 072 GPU) : le modèle en série à taux constant suffit pour le calcul d'ordre de grandeur.
:::

Deux réserves s'imposent. Le taux n'est pas constant : les mêmes auteurs observent des périodes à environ 2,5 pannes pour mille nœuds-jours et des pointes à environ 17,5, parce que les charges et les logiciels changent. Et l'indépendance est une hypothèse : un mauvais nœud réalloué à chaque relance, un commutateur défaillant ou une vague de chaleur créent des pannes corrélées. Nous y reviendrons avec le nœud défectueux qui revient à chaque relance (chapitre 5) et son exclusion par le superviseur (chapitre 6).

### 1.2. Une taxonomie utile à l'action

Classer les pannes par composant ne suffit pas : ce qui compte pour l'exploitant, c'est **ce qu'on fait ensuite**. Nous retiendrons quatre familles et un cas à part.

-   **Matériel.** GPU (erreurs ECC, du nom du code correcteur d'erreurs de la mémoire, mémoire HBM, processeur système du GPU, capteurs thermiques), hôte (processeur, mémoire, SSD, alimentation, châssis, carte d'extension). La réparation est un échange de composant ; l'action immédiate est de retirer le nœud.
-   **Réseau.** Câble ou commutateur, lien d'interconnexion qui flotte, carte réseau. Le symptôme est souvent un délai d'attente de collective qui n'indique pas la cause.
-   **Logiciel.** Pilote, bibliothèque de communication, bogue du *framework*, code utilisateur, dépendance externe (système de fichiers, service de métriques). La relance suffit parfois, parfois non : un bogue déterministe se reproduit à l'identique.
-   **Humaine et planifiée.** Mise à jour de micrologiciel, changement de configuration, mise à jour du jeu de données, erreur de commande. Ces interruptions se planifient, donc se réduisent.
-   **Silencieuse.** Le job continue mais le résultat est faux (corruption silencieuse de données) ou lent (nœud traînard). Aucun code d'erreur ne la signale : il faut la mesurer (chapitre 5).

### 1.3. Ce que disent les données publiées

Cinq sources décrivent des entraînements ou des clusters réels. Elles ne sont pas comparables entre elles (matériel, période, définition d'une « panne »), mais elles convergent sur l'ordre de grandeur.

| Source | Ce qui est mesuré | Chiffres cités |
|---|---|---|
| [Llama 3](https://arxiv.org/abs/2407.21783) (2024) | une fenêtre de 54 jours du pré-entraînement du 405B, sur jusqu'à 16 000 GPU H100 | 466 interruptions dont 47 prévues et 419 imprévues ; plus de 90 % de temps d'entraînement effectif |
| [Kokolis et al.](https://arxiv.org/abs/2410.21680) (2024) | onze mois sur deux clusters de recherche (RSC-1, RSC-2), 4 millions de jobs | 6,50 et 2,34 pannes pour mille nœuds-jours ; MTBF projeté de 1,8 h à 16 384 GPU |
| [OPT-175B](https://arxiv.org/abs/2205.01068) (2022) | deux mois d'entraînement | au moins 35 redémarrages manuels, plus de 100 hôtes remplacés, plus de 70 redémarrages automatiques estimés |
| [BLOOM](https://arxiv.org/abs/2211.05100) (2022) | l'entraînement du modèle de 176 milliards de paramètres | en moyenne 1 à 2 pannes de GPU par semaine |
| [Hu et al. (Acme)](https://arxiv.org/abs/2403.07648) (2024) | six mois (mars à août 2023) sur deux clusters totalisant 4 704 GPU A100 | les pannes d'infrastructure représentent 11 % des jobs en échec mais plus de 82 % du temps GPU des jobs en échec |

Le tableau 5 de l'article Llama 3 détaille les 419 interruptions imprévues. Nous l'avons regroupé par famille (chiffres de l'article, regroupement et divisions faits ici) :

| Famille | Interruptions | Part de 419 |
|---|---|---|
| GPU (défaut du GPU, HBM3, SRAM, processeur système, corruption silencieuse, capteur thermique) | 268 | 64,0 % |
| Logiciel (bogue, dépendance) | 56 | 13,4 % |
| Réseau (commutateur, câble) | 35 | 8,4 % |
| Maintenance imprévue d'un hôte | 32 | 7,6 % |
| Hôte (carte réseau, SSD, alimentation, châssis, carte d'extension, processeur, mémoire) | 21 | 5,0 % |
| Délai d'attente du *watchdog* NCCL (cause inconnue) | 7 | 1,7 % |

::: note
[Un chiffre de l'article qui ne se recalcule pas]{.tag} Le texte de l'article dit que les problèmes de GPU forment « 58.7% » des causes imprévues, et le tableau donne 30,1 % à la ligne « Faulty GPU ». Or les comptes du tableau somment bien à 419, et $148/419 = 35{,}3\ \%$, pas 30,1 %. Recalculée à partir des comptes, la part des GPU est de 64,0 %, pas 58,7 %. 

La colonne des pourcentages, elle, est cohérente avec le texte : $30{,}1 + 17{,}2 + 4{,}5 + 4{,}1 + 1{,}4 + 1{,}4 = 58{,}7$. Seule la ligne « Faulty GPU » est donc incohérente : avec 126 interruptions elle donnerait 30,1 %, mais les comptes ne sommeraient plus à 419. Nous ne pouvons pas trancher : l'exercice 4 vous demande de refaire ce calcul. La conclusion (les GPU forment de loin la première famille) ne change pas.
:::

La leçon opérationnelle la plus utile est ailleurs. Sur 419 interruptions imprévues en 54 jours, l'article indique que « significant manual intervention was required only three times during this period, with the rest of issues handled by automation ». L'écart entre 419 pannes et trois interventions humaines, c'est le contenu de ce module.

::: war
[Redémarrages manuels sur OPT-175B]{.tag} L'équipe d'OPT-175B rapporte que les pannes matérielles ont causé « at least 35 manual restarts » et le remplacement de plus de 100 hôtes sur deux mois, en plus d'environ 70 redémarrages automatiques estimés. Pendant un redémarrage manuel, l'entraînement était mis en pause et une série de tests de diagnostic était lancée avant la reprise. Source : [Zhang et al., 2022, section sur les pannes matérielles](https://arxiv.org/abs/2205.01068).
:::

### 1.4. Les pannes ne s'arrêtent pas au matériel

Hu et coauteurs notent que la plupart des erreurs de script surviennent au début des jobs et provoquent un arrêt rapide, alors que les pannes d'infrastructure frappent les longs pré-entraînements et coûtent cher. Ils relèvent aussi des pannes liées à la chaleur : sur leur cluster, l'entraînement de modèles de 7 milliards de paramètres, très bien optimisé pour la communication, laissait peu de temps d'inactivité aux GPU, la température de la salle montait d'environ 5 °C, et des erreurs NVLink ou ECC apparaissaient. Le refroidissement fut renforcé, et la fréquence de ces pannes baissa nettement.

Kokolis et coauteurs insistent sur une autre difficulté : le **diagnostic**. Un délai d'attente NCCL peut être attribué à tort au réseau alors qu'il s'agit d'un blocage logiciel ; ils formulent la leçon ainsi : « Beware of the red-herrings ». Nous verrons au chapitre 5 comment limiter ce risque.

### 1.5. Combien de temps un job survit-il sans reprise ?

Avec des pannes d'intervalle moyen $M$ réparties comme un processus de Poisson, la probabilité qu'un job de durée $T$ **ne subisse aucune panne** est $e^{-T/M}$. Pour Llama 3, 419 pannes imprévues en 1 296 heures donnent $M \approx 3{,}09$ h, soit 7,8 pannes par jour. Un job de 24 heures sans reprise a alors une chance sur 2 400 d'aller au bout ($e^{-7{,}77} \approx 4{,}2 \times 10^{-4}$, **calculé ici**). Sans tolérance aux pannes, l'entraînement ne finit jamais.

::: recap
Points clés — chapitre 1

-   Le MTBF d'un job en série est celui d'un nœud divisé par le nombre de nœuds : $1/(Nr)$.
-   Sur 16 000 GPU, les sources publiées montrent plusieurs pannes imprévues par jour ; l'automatisation, pas le matériel, fait la différence.
-   Classez les pannes par action à mener : retirer le nœud, relancer, corriger le code, planifier, mesurer.
-   Les taux varient dans le temps et les pannes sont corrélées : le modèle à taux constant donne un ordre de grandeur.
-   Un chiffre publié se recalcule : un tableau dont les parts ne se recoupent pas est une information, pas un détail.
:::

## 2. Modèle de coût : Young, Daly et goodput {#ch2}

Si les pannes sont inévitables, la seule décision qui reste est la fréquence des checkpoints : trop rares, on perd beaucoup de calcul à chaque panne ; trop fréquents, on passe son temps à écrire. Ce chapitre pose le modèle qui chiffre cet arbitrage, le vérifie par simulation et le confronte aux chiffres publiés.

### 2.1. Les quatre durées

Notons, en secondes :

-   $\delta$ le **coût d'un checkpoint** qui bloque la boucle d'entraînement ;
-   $M$ le **temps moyen entre pannes** du job entier (le MTBF du chapitre 1) ;
-   $R$ le **coût de redémarrage** : détection, relance, chargement du checkpoint, ré-initialisation ;
-   $\tau$ le **calcul utile** entre deux checkpoints.

Le **goodput** est la part du temps d'horloge consacrée à du calcul qui sera conservé. Son complément est le **temps perdu** (*waste*). L'article de Kokolis et coauteurs définit un indicateur voisin, l'*Effective Training Time Ratio* (ETTR) : le rapport entre le temps productif d'un job et le temps d'horloge disponible. Le MFU du [module 2](../perf-models/index.html) mesure autre chose : l'efficacité du calcul quand la machine travaille. Un job peut avoir un excellent MFU et un mauvais goodput.

### 2.2. Le modèle du premier ordre

Sur une période d'horloge, le checkpoint coûte $\delta$ pour $\tau$ secondes de calcul, soit une fraction $\delta/\tau$. Les pannes arrivent au rythme $1/M$ ; chacune fait perdre en moyenne la moitié d'une période de calcul, $\tau/2$ (la panne tombe au hasard dans la période), plus le redémarrage $R$. Le temps perdu vaut donc, au premier ordre :

$$W(\tau) \;\approx\; \frac{\delta}{\tau} + \frac{\tau/2 + R}{M}$$

Le premier terme décroît avec $\tau$, le second croît. En dérivant et en annulant la dérivée, $-\delta/\tau^2 + 1/(2M) = 0$, on obtient la formule de Young (1974) :

$$\tau^{\ast} = \sqrt{2\,\delta\,M} \qquad W^{\ast} = \sqrt{\frac{2\delta}{M}} + \frac{R}{M}$$

À l'optimum, le coût d'écriture $\delta/\tau$ est égal au coût moyen de recalcul $\tau/(2M)$ : on dépense autant à se protéger qu'à perdre. Les références originales sont Young, *A first order approximation to the optimum checkpoint interval*, Communications of the ACM 17(9), 1974, et Daly, *A higher order estimate of the optimum checkpoint interval for restart dumps*, Future Generation Computer Systems 22(3), 2006 (métadonnées vérifiées auprès de Crossref).

::: ex
[Exemple 2.1 — L'intervalle de Young pour un job « à la Llama 3 »]{.tag} Prenons $M = 3{,}09$ h $= 11\,124$ s (419 pannes en 54 jours), $\delta = 60$ s et $R = 300$ s. Alors $\tau^{\ast} = \sqrt{2 \times 60 \times 11124} \approx 1155$ s, soit 19,3 minutes. Le temps perdu vaut $W^{\ast} = 0{,}1038 + 0{,}0270 = 0{,}131$, un goodput de 86,9 %.

À l'optimum les deux termes sont égaux : $\delta/\tau = 0{,}0519$ et $\tau/(2M) = 0{,}0519$ (**calculé ici**). Si vous doublez la période à 2 311 s, le goodput du modèle exact passe de 87,6 % à 85,1 % ; si vous la divisez par deux, à 85,7 % : l'optimum est plat.
:::

### 2.3. Le modèle exact et la correction de Daly

Le premier ordre suppose $\delta \ll M$. Pour des pannes exponentielles, on peut écrire l'espérance exacte du temps d'horloge par seconde de calcul utile (résultat classique, repris de Daly 2006 et **vérifié numériquement** dans le lab 10.1) :

$$\frac{\mathbb{E}[\text{horloge}]}{\text{calcul utile}} = \frac{M\,e^{R/M}\left(e^{(\tau+\delta)/M} - 1\right)}{\tau}$$

Le goodput est son inverse. Daly propose aussi une estimation d'ordre supérieur de l'intervalle optimal, pour $\delta < 2M$ :

$$\tau_{\text{Daly}} = \sqrt{2\delta M}\left[1 + \tfrac{1}{3}\sqrt{\tfrac{\delta}{2M}} + \tfrac{1}{9}\,\tfrac{\delta}{2M}\right] - \delta$$

Nous n'avons pas pu relire l'article de Daly (accès payant) : cette formule est donnée comme implémentée dans `yd.py`, et le test `test_daly_high_matches_numerical_optimum` vérifie qu'elle coïncide à 0,5 % près avec le minimum numérique du modèle exact.

::: ex
[Exemple 2.2 — Formules contre simulation (lab 10.1)]{.tag} La commande `python3 sweep.py --delta 60 --mtbf-hours 3.09 --restart 300` simule 40 entraînements de 800 heures de calcul utile par période testée, avec des pannes exponentielles (sortie réelle du bac à sable, 2026-10-24) :

~~~text
Young   tau = sqrt(2*delta*M)        =   1155.4 s
Daly 2  higher-order estimate         =   1115.7 s
exact   argmin of E[wall] (numerical) =   1115.7 s
  tau (s)  1st-order    exact   MC exp     +-    MC wb
      289     0.7524   0.7935   0.7939 0.0004   0.7955
      578     0.8432   0.8568   0.8573 0.0006   0.8602
      867     0.8649   0.8730   0.8734 0.0007   0.8776
     1155     0.8692   0.8757   0.8767 0.0008   0.8818   <- Young
     1733     0.8605   0.8670   0.8686 0.0012   0.8761
     2311     0.8432   0.8512   0.8534 0.0013   0.8635
     3466     0.7999   0.8132   0.8141 0.0018   0.8328
     4621     0.7523   0.7729   0.7749 0.0024   0.7997
~~~

La colonne « MC exp » (Monte-Carlo, goodput moyen, erreur standard dans la colonne suivante) coïncide avec le modèle exact à moins de deux erreurs standard. Le premier ordre sous-estime le goodput d'environ 0,7 point à l'optimum, et de 1,3 à 4,1 points aux extrémités de la grille. La dernière colonne utilise des pannes en rafales (loi de Weibull de paramètre de forme 0,7, de même moyenne) : le goodput est un peu meilleur et l'optimum, sur cette grille, ne bouge pas.
:::

<figure class="fig">
<svg viewBox="0 0 640 340" xmlns="http://www.w3.org/2000/svg" font-family="inherit" font-size="12" role="img">
<title>Goodput en fonction de la période de checkpoint</title>
<rect x="56" y="16" width="568" height="280" fill="none" stroke="currentColor" stroke-opacity=".3"/>
<line x1="56" x2="624" y1="296.0" y2="296.0" stroke="currentColor" stroke-opacity=".12"/>
<text x="50" y="300.0" text-anchor="end" fill="currentColor">0.75</text>
<line x1="56" x2="624" y1="202.7" y2="202.7" stroke="currentColor" stroke-opacity=".12"/>
<text x="50" y="206.7" text-anchor="end" fill="currentColor">0.80</text>
<line x1="56" x2="624" y1="109.3" y2="109.3" stroke="currentColor" stroke-opacity=".12"/>
<text x="50" y="113.3" text-anchor="end" fill="currentColor">0.85</text>
<line x1="56" x2="624" y1="16.0" y2="16.0" stroke="currentColor" stroke-opacity=".12"/>
<text x="50" y="20.0" text-anchor="end" fill="currentColor">0.90</text>
<text x="56.0" y="312" text-anchor="middle" fill="currentColor">289</text>
<text x="198.0" y="312" text-anchor="middle" fill="currentColor">578</text>
<text x="281.1" y="312" text-anchor="middle" fill="currentColor">867</text>
<text x="339.9" y="312" text-anchor="middle" fill="currentColor">1155</text>
<text x="423.0" y="312" text-anchor="middle" fill="currentColor">1733</text>
<text x="482.0" y="312" text-anchor="middle" fill="currentColor">2311</text>
<text x="565.1" y="312" text-anchor="middle" fill="currentColor">3466</text>
<text x="624.0" y="312" text-anchor="middle" fill="currentColor">4621</text>
<text x="340.0" y="334" text-anchor="middle" fill="currentColor">période de calcul entre checkpoints (s), échelle log</text>
<line x1="340.0" x2="340.0" y1="16" y2="296" stroke="currentColor" stroke-dasharray="4 3"/>
<text x="344.0" y="290" fill="currentColor">Young</text>
<polyline points="56.0,291.5 198.0,121.9 281.1,81.6 339.9,73.6 423.0,89.7 482.0,122.0 565.1,202.8 624.0,291.6" fill="none" stroke-width="2" stroke="currentColor" stroke-opacity=".55" stroke-dasharray="6 4"/>
<polyline points="56.0,214.9 198.0,96.6 281.1,66.4 339.9,61.3 423.0,77.5 482.0,107.0 565.1,178.1 624.0,253.3" fill="none" stroke-width="2" stroke="currentColor"/>
<polyline points="56.0,211.1 198.0,90.2 281.1,57.7 339.9,50.0 423.0,60.6 482.0,84.2 565.1,141.4 624.0,203.2" fill="none" stroke-width="2" stroke="var(--accent)" stroke-opacity=".7"/>
<circle cx="56.0" cy="214.1" r="4" fill="var(--accent)"/>
<circle cx="198.0" cy="95.8" r="4" fill="var(--accent)"/>
<circle cx="281.1" cy="65.7" r="4" fill="var(--accent)"/>
<circle cx="339.9" cy="59.5" r="4" fill="var(--accent)"/>
<circle cx="423.0" cy="74.7" r="4" fill="var(--accent)"/>
<circle cx="482.0" cy="103.1" r="4" fill="var(--accent)"/>
<circle cx="565.1" cy="176.3" r="4" fill="var(--accent)"/>
<circle cx="624.0" cy="249.5" r="4" fill="var(--accent)"/>
<text x="64" y="32" fill="currentColor">trait plein : modèle exact · pointillé : premier ordre</text>
<text x="64" y="48" fill="currentColor">points : Monte-Carlo · orange fin : Weibull k=0.7</text>
</svg>
<figcaption>Goodput en fonction de la période de calcul entre checkpoints, pour les valeurs de l'exemple 2.2 (lab 10.1, <code>sweep.py --svg</code>). Trait plein : modèle exact ; pointillé : premier ordre ; points : Monte-Carlo ; trait fin orange : pannes en rafales. Le trait vertical marque la période de Young : l'optimum est plat.</figcaption>
</figure>

### 2.4. Là où les formules mentent

Quatre limites méritent d'être connues avant de s'appuyer sur un chiffre.

-   **Checkpoint long devant le MTBF.** Avec $\delta = 3000$ s et le même $M$, la formule de Young donne 8 170 s alors que le minimum exact est à 6 304 s, soit 30 % d'écart ; le goodput à l'optimum n'est plus que de 42 % (**calculé ici** avec `yd.py`, et vérifié par le test `test_first_order_breaks_when_checkpoint_is_not_small`). Dans ce régime, le problème n'est pas la période, c'est le checkpoint.
-   **Pannes non exponentielles.** Les pannes réelles viennent en rafales. Avec la loi de Weibull de forme 0,7, la période de Young reste à moins d'un point du meilleur goodput échantillonné, et le goodput est plus élevé que dans le cas exponentiel à $M$ égal. Le choix de la loi est une hypothèse du lab, pas une mesure.
-   **Coûts non constants.** $R$ dépend de la file d'attente, de l'état du cache de données, du nombre de nœuds de rechange. Mesurez-le sur vos relances (chapitre 6), ne le supposez pas.
-   **Checkpoints qui échouent.** Une écriture peut échouer ou être corrompue ; le modèle suppose qu'un checkpoint terminé est un checkpoint utilisable. Le chapitre 3 traite ce point.

### 2.5. Confrontation aux chiffres publiés

Kokolis et coauteurs donnent une approximation de l'ETTR pour un job long : en notant $N$ le nombre de nœuds, $r_f$ le taux de panne par nœud-jour, $u_0$ le temps de ré-initialisation et $\Delta t$ l'intervalle de checkpoint (checkpoints supposés non bloquants),

$$\mathbb{E}[\text{ETTR}] \;\approx\; 1 - N\,r_f\left(u_0 + \frac{\Delta t}{2}\right)$$

C'est la même structure que $W(\tau)$, sans le terme d'écriture. L'article en tire deux chiffres pour un hypothétique entraînement de 16 000 GPU occupant tout RSC-1 : « the expected ETTR would be 0.7 for a 60 minute checkpoint interval », et 0,93 pour un intervalle de 5 minutes.

::: ex
[Exemple 2.3 — Retrouver les 0,7 et 0,93 de l'article]{.tag} Avec $N = 2048$ nœuds, $r_f = 6{,}5 \times 10^{-3}$ par nœud-jour, donc $N r_f = 13{,}3$ pannes par jour, et $u_0 = 5$ minutes (valeur que l'article prend pour ses comparaisons), le calcul donne (**calculé ici**) :

| Intervalle $\Delta t$ | ETTR attendu |
|---|---|
| 60 min | 0,676 |
| 30 min | 0,815 |
| 10 min | 0,908 |
| 5 min | 0,931 |
| 2 min | 0,945 |

Les 60 minutes donnent 0,68, que l'article arrondit à 0,7 ; les 5 minutes donnent 0,93. La conclusion pratique : à cette échelle, un checkpoint horaire coûte un tiers du temps de calcul, et ce n'est qu'en rendant le checkpoint **non bloquant** que descendre à quelques minutes devient raisonnable. Le plancher (0,945 à 2 minutes) est fixé par $u_0$, d'où l'intérêt de réduire le temps de relance.
:::

### 2.6. Dimensionner le coût d'un checkpoint

Que contient le checkpoint, et combien pèse-t-il ? Pour l'optimiseur Adam en précision mixte, le papier [ZeRO](https://arxiv.org/abs/1910.02054) compte 2 octets par paramètre pour la copie en demi-précision, 2 pour les gradients et $K = 12$ pour l'état de l'optimiseur (copie maître en simple précision, deux moments), soit $16\Psi$ octets pour $\Psi$ paramètres. Un checkpoint n'a pas besoin des gradients : de $12\Psi$ à $14\Psi$ octets selon que l'on sauve ou non la copie en demi-précision (qui se reconstruit).

::: ex
[Exemple 2.4 — Un modèle de 70 milliards de paramètres]{.tag} Avec $14\Psi$ octets, $\Psi = 70 \times 10^9$ donne 980 Go. Sur un job de 1 024 GPU ($M = 28{,}85$ h au taux de RSC-1, $R = 600$ s supposé), le minimum exact du modèle donne (**calculé ici**, débits d'écriture agrégés **supposés**) :

| Débit d'écriture | $\delta$ bloquant | $\tau^{\ast}$ | Temps perdu |
|---|---|---|---|
| 5 Go/s | 196 s | 104 min | 6,6 % |
| 20 Go/s | 49 s | 52,6 min | 3,6 % |
| 100 Go/s | 9,8 s | 23,7 min | 1,9 % |

Si l'on rend le checkpoint asynchrone et que la partie bloquante se réduit à environ 1 s (copie du GPU vers la mémoire de l'hôte, **supposée**), la période optimale tombe à 7,6 minutes et le temps perdu à 1,0 %. Attention : l'écriture de fond de 49 s à 20 Go/s doit tenir dans la période, et elle concurrence l'entraînement pour la bande passante. Voir le chapitre 4.
:::

::: recap
Points clés — chapitre 2

-   Au premier ordre, $W(\tau) = \delta/\tau + (\tau/2 + R)/M$ et $\tau^{\ast} = \sqrt{2\delta M}$.
-   L'optimum est plat : un facteur 2 de part ou d'autre coûte quelques points de goodput, pas dix.
-   La formule de Young faiblit quand $\delta$ n'est plus petit devant $M$ ; le modèle exact et Daly corrigent.
-   À grande échelle, un checkpoint horaire est trop rare : l'ETTR attendu de 16 000 GPU passe de 0,68 à 0,93 en passant de 60 à 5 minutes.
-   Tout chiffre de $\delta$, $R$ et $M$ doit être mesuré sur votre système ; ceux du cours sont des exemples.
:::

## 3. Écrire un checkpoint correct {#ch3}

Un checkpoint est une promesse : « si le job meurt maintenant, je repars d'ici et le résultat sera celui que j'aurais eu sans panne ». Cette promesse repose sur trois propriétés qu'un `torch.save` naïf ne garantit pas : l'**atomicité** (jamais de demi-checkpoint visible), l'**intégrité** (on détecte un fichier abîmé) et la **complétude** (tout l'état nécessaire est là).

### 3.1. Quel état sauvegarder ?

Les poids ne suffisent pas. Un entraînement a de l'état caché, et chaque oubli se paie en divergence silencieuse.

-   Les **moments de l'optimiseur** (pour Adam, deux tenseurs par paramètre et un compteur de pas).
-   La **position de l'ordonnanceur** de taux d'apprentissage.
-   Les **états des générateurs aléatoires** : celui de PyTorch sur CPU, un par GPU pour CUDA, ceux de Python et de NumPy si votre code les utilise. Le *dropout* en consomme.
-   Le **curseur de données** : époque, position dans l'ordre mélangé, ou état du générateur qui le produit. CheckFreq en fait un invariant : chaque exemple doit servir une fois par époque, grâce à un itérateur reprenable léger.
-   Les compteurs (pas global, jetons vus), l'échelle de gradient en précision mixte, les moyennes mobiles de poids, tout état que votre boucle accumule.

::: ex
[Exemple 3.1 — Ce que protège chaque partie (lab 10.2)]{.tag} `ablate.py` entraîne 30 pas avec un checkpoint tous les 10, « plante », reprend au pas 30 et poursuit jusqu'à 60, en retirant une partie de l'état à la fois. La référence est un entraînement de 60 pas sans interruption. Sortie réelle du bac à sable (PyTorch 2.14.1 CPU, 2026-10-24) :

~~~text
omitted      first wrong step  max |dloss|  same final state
nothing                  None    0.000e+00              True
optimizer                  31    7.493e-02             False
scheduler                  32    9.814e-02             False
rng                        30    2.583e-02             False
cursor                     30    3.337e-01             False
~~~

La reprise complète est identique à l'exécution continue, au bit près (pertes et état final). Chaque omission fait diverger l'entraînement, à des pas différents : sans le générateur aléatoire ou le curseur, la perte est fausse dès le pas 30 (masques de *dropout* ou lot différents) ; sans l'optimiseur, la perte du pas 30 est encore juste (elle est calculée avant la mise à jour) et c'est celle du pas 31 qui est fausse ; sans l'ordonnanceur, c'est le taux d'apprentissage du pas suivant qui est faux, donc la perte du pas 32.
:::

Une conséquence pratique : un test de reprise qui ne compare que la perte au pas qui suit immédiatement la reprise laisse passer un oubli d'optimiseur. Comparez plusieurs pas, et l'état final.

### 3.2. Atomicité : le protocole en quatre temps

Sur un système de fichiers POSIX, une écriture n'est ni durable ni atomique : le noyau peut réordonner et retarder les écritures, et une coupure à mi-chemin laisse un fichier partiel. Le protocole standard :

1.  écrire dans un **fichier ou répertoire temporaire** dans le même système de fichiers ;
2.  appeler `fsync` sur chaque fichier, pour que les données soient durables avant la suite ;
3.  **renommer** vers le nom final (`rename` est atomique sur le même système de fichiers) ;
4.  appeler `fsync` sur le **répertoire parent**, pour que le renommage soit durable.

Un checkpoint réparti compte plusieurs fichiers : le lab écrit tout dans un répertoire `step-N.tmp`, puis un **manifeste** (tailles et empreintes SHA-256 de chaque fichier) en dernier, puis renomme le répertoire. Le renommage du répertoire est le point de validation : avant lui rien n'existe, après lui tout existe.

~~~python
# labs/fault-tolerance/atomic-checkpoint/ckpt.py (extrait de save)
with open(tmp / "MANIFEST.json", "w") as f:
    json.dump({"step": step, "files": files}, f, sort_keys=True)
    f.flush(); os.fsync(f.fileno())
_fsync_dir(tmp)
os.rename(tmp, final)   # the commit point
_fsync_dir(root)
~~~

Sur un stockage objet, il n'y a pas de renommage de répertoire atomique : le même motif s'applique avec le manifeste comme **dernier objet écrit**, et un lecteur qui n'accepte une version que si son manifeste existe et que toutes les empreintes concordent. C'est un choix de conception de ce parcours ; vérifiez les garanties de cohérence de votre stockage dans sa documentation.

::: ex
[Exemple 3.2 — Une campagne de kill -9 (lab 10.2)]{.tag} `chaos.py` lance l'entraîneur, le tue avec `SIGKILL` (groupe de processus entier) à un délai aléatoire après qu'il a annoncé `READY`, le relance, et recommence jusqu'à ce qu'il se termine. Pour que les coups tombent souvent pendant une écriture, le lab ralentit le stockage de façon **simulée** (15 ms par fichier). Résultat d'une exécution (bac à sable, 2026-10-24 ; les nombres varient d'une exécution à l'autre) :

~~~text
{'life': 5, 'resumed_from': '50', 'torn_tmp_found': '1', 'skipped': '0', 'outcome': 'killed after 0.92s'}
{'life': 6, 'resumed_from': '90', 'torn_tmp_found': '0', 'skipped': '0', 'outcome': 'completed'}
{"kills": 5, "lives": 6, "replayed_steps": 43, "torn_tmp_dirs_met": 2, "every_step_logged": true, "replayed_losses_identical": true, "final_digest_equal": true}
~~~

Six vies, cinq `kill -9`, deux répertoires temporaires abandonnés rencontrés au redémarrage (des écritures interrompues), 43 pas recalculés, et pourtant : chaque pas a été journalisé, toutes les pertes recalculées sont identiques à celles de la première fois, et l'empreinte de l'état final est celle de l'exécution sans panne.
:::

### 3.3. Intégrité : ne pas faire confiance à ce qui est sur disque

Un checkpoint peut être abîmé après son écriture : octet inversé, volume plein, copie interrompue. La règle : **vérifier avant d'utiliser, et savoir se replier**. Le chargeur du lab parcourt les répertoires du plus récent au plus ancien, rejette ceux dont le manifeste manque ou dont une empreinte ne concorde pas, et charge le premier qui est valide. Quatre tests le prouvent : écriture interrompue, octet inversé, manifeste absent, et reprise de l'entraîneur sur un checkpoint abîmé.

::: note
[Un bogue trouvé en écrivant le lab]{.tag} Notre première version de `save` échouait avec `OSError: Directory not empty` lorsqu'on reprenait sur le pas 20 après avoir rejeté un répertoire `step-30` abîmé : le pas 30, recalculé, voulait s'écrire sous un nom déjà occupé. La correction (déplacer le répertoire abîmé vers `step-30.corrupt` pour garder la preuve, puis écrire) est dans `ckpt.py` et testée par `test_trainer_resumes_from_latest_valid_checkpoint`. La leçon : le chemin « se replier sur l'ancien » est un chemin de code rare, donc rarement testé, donc bogué tant qu'on ne l'a pas fait tourner.
:::

### 3.4. Checkpoints répartis et formats

Quand le modèle est partitionné sur des centaines de GPU, personne ne veut rassembler tout l'état sur un seul rang. La documentation de PyTorch décrit ainsi le *Distributed Checkpoint* (DCP) : il « supports loading and saving models from multiple ranks in parallel » et « handles load-time resharding which enables saving in one cluster topology and loading into another ». C'est la propriété qui permet de reprendre sur un nombre de nœuds différent (chapitre 6).

::: ex
[Exemple 3.3 — Écrire sur 2 rangs, relire sur 4 (lab 10.2)]{.tag} `dcp_reshard.py` sauvegarde un tenseur de 8 lignes découpé en 2 morceaux par 2 processus (backend `gloo`, CPU, PyTorch 2.14.1), puis le recharge dans 4 processus. Sortie réelle (2026-10-24) :

~~~text
files written by 2 ranks: ['.metadata', '__0_0.distcp', '__1_0.distcp']
load rank 0/4: holds rows 0..1
load rank 1/4: holds rows 2..3
load rank 2/4: holds rows 4..5
load rank 3/4: holds rows 6..7
OK dcp: saved on 2 ranks, loaded on 4 ranks, tensor identical
~~~

Un fichier de données par rang écrivain et un fichier de métadonnées décrivant le découpage : chaque lecteur sait quels octets lire pour obtenir sa tranche. La reconstruction du tenseur complet vérifie l'égalité avec l'original.
:::

Le format compte aussi pour la sécurité et la portabilité. `torch.save` repose sur `pickle`, qui peut exécuter du code arbitraire à la lecture ; le [dépôt de `safetensors`](https://raw.githubusercontent.com/huggingface/safetensors/main/README.md) classe d'ailleurs le pickle « Unsafe, runs arbitrary code ». C'est pourquoi le lab charge avec `weights_only=True`. Le format `safetensors` est simple : 8 octets (entier non signé de 64 bits, petit-boutiste) donnant la taille $N$ d'un en-tête JSON, l'en-tête, puis les octets des tenseurs.

~~~text
file size 182 bytes; header length N = 144; data section = 30 bytes
{"__metadata__": {"step": "40"}, "b": {"data_offsets": [24, 30], "dtype": "BF16", "shape": [3]}, "w": {"data_offsets": [0, 24], "dtype": "F32", "shape": [2, 3]}}
~~~

Cette sortie, produite par `safetensors_peek.py`, montre le format : deux tenseurs, leurs décalages et un champ de métadonnées dont les valeurs doivent être des chaînes. Un format fait de tenseurs et de chaînes ne convient pas à l'état d'un entraînement (compteurs, états de générateurs, structures de l'optimiseur) : réservez `safetensors` à l'export des poids, et utilisez DCP ou `torch.save` pour reprendre un entraînement.

### 3.5. Reprise exacte, reprise équivalente

Le lab prouve une reprise **identique au bit près**, ce qui suppose un seul fil CPU, la même topologie et des algorithmes déterministes. Sur GPU, avec des réductions non déterministes, ou après un redimensionnement (autre nombre de rangs, donc autre ordre de sommation et autre découpage des données), l'identité au bit près n'est plus un objectif réaliste. On vise alors une reprise **statistiquement équivalente** : même courbe de perte à la tolérance près, pas de saut, pas de pic. Fixez le critère avant la panne, pas après. C'est une recommandation de ce parcours, pas une garantie de PyTorch.

::: recap
Points clés — chapitre 3

-   Sauvegardez poids, optimiseur, ordonnanceur, générateurs aléatoires, curseur de données et compteurs ; chaque oubli fait diverger, parfois quelques pas plus tard.
-   Écrire, `fsync`, renommer, `fsync` du répertoire ; pour plusieurs fichiers, un manifeste d'empreintes écrit en dernier.
-   Vérifiez les empreintes à la lecture et sachez vous replier ; testez ce chemin.
-   DCP écrit en parallèle et reshard à la lecture ; `safetensors` est un format de poids, pas d'état d'entraînement.
-   Visez la reprise identique quand c'est possible, l'équivalence statistique sinon, et fixez le critère à l'avance.
:::

## 4. Checkpoints rapides {#ch4}

Le chapitre 2 a montré que le coût bloquant $\delta$ fixe la fréquence de checkpoint raisonnable, donc le temps perdu. Pour un modèle dont l'état se compte en centaines de gigaoctets, écrire proprement et vite est un problème d'ingénierie à part entière : où va le temps, qu'est-ce qui peut se faire en arrière-plan, et quel stockage faut-il derrière.

### 4.1. Où va le temps d'un checkpoint

Un checkpoint synchrone enchaîne quatre phases, toutes bloquantes : copier l'état du GPU vers la mémoire de l'hôte (*snapshot*), le sérialiser, l'écrire sur le stockage, valider (manifeste, renommage). La seule phase qui doit absolument arrêter l'entraînement est la première, parce que l'état change à chaque pas. Les autres peuvent se faire pendant que les pas suivants calculent.

C'est l'idée du **checkpoint en deux phases** de CheckFreq (Mohan, Phanishayee et Chidambaram, FAST 2021) : une phase de *snapshot* rapide, puis une phase de persistance qui recouvre le calcul. Les auteurs rapportent que leur système peut ramener le temps de reprise « from hours to seconds while bounding the runtime overhead within 3.5% ». MegaScale (Jiang et al., 2024) décrit la même structure : chaque GPU copie son état vers la mémoire de l'hôte puis reprend l'entraînement, et un processus de fond transfère ensuite l'état vers un système de fichiers distribué. 

L'équipe d'Acme, de son côté, annonce un checkpoint accéléré de 3,6 à 58,7 fois par cette approche, en citant un ralentissement de l'entraînement pouvant atteindre 43 % avec des checkpoints synchrones de plusieurs téraoctets.

<figure class="fig">
<svg viewBox="0 0 640 190" role="img" aria-labelledby="ck-t ck-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="ck-t">Checkpoint en deux phases</title>
<desc id="ck-d">Deux voies parallèles. Sur la voie GPU, des pas d'entraînement séparés par un court snapshot bloquant. Sur la voie de fond, une longue écriture vers le stockage qui recouvre plusieurs pas.</desc>
<text x="8" y="58" font-size="12" fill="currentColor">GPU</text>
<text x="8" y="138" font-size="12" fill="currentColor">fond</text>
<line x1="50" y1="70" x2="630" y2="70" stroke="currentColor" stroke-opacity=".25"/>
<rect x="56" y="40" width="90" height="30" fill="currentColor" fill-opacity=".14" stroke="currentColor"/>
<rect x="146" y="40" width="22" height="30" fill="var(--accent)" stroke="currentColor"/>
<rect x="168" y="40" width="90" height="30" fill="currentColor" fill-opacity=".14" stroke="currentColor"/>
<rect x="258" y="40" width="90" height="30" fill="currentColor" fill-opacity=".14" stroke="currentColor"/>
<rect x="348" y="40" width="90" height="30" fill="currentColor" fill-opacity=".14" stroke="currentColor"/>
<rect x="438" y="40" width="22" height="30" fill="var(--accent)" stroke="currentColor"/>
<rect x="460" y="40" width="90" height="30" fill="currentColor" fill-opacity=".14" stroke="currentColor"/>
<text x="101" y="60" text-anchor="middle" font-size="11" fill="currentColor">pas n</text>
<text x="213" y="60" text-anchor="middle" font-size="11" fill="currentColor">pas n+1</text>
<text x="303" y="60" text-anchor="middle" font-size="11" fill="currentColor">pas n+2</text>
<text x="393" y="60" text-anchor="middle" font-size="11" fill="currentColor">pas n+3</text>
<text x="505" y="60" text-anchor="middle" font-size="11" fill="currentColor">pas n+4</text>
<text x="157" y="32" text-anchor="middle" font-size="11" font-weight="700" fill="currentColor">snapshot</text>
<text x="449" y="32" text-anchor="middle" font-size="11" font-weight="700" fill="currentColor">snapshot</text>
<rect x="168" y="118" width="270" height="30" fill="none" stroke="currentColor" stroke-dasharray="5 3"/>
<text x="303" y="138" text-anchor="middle" font-size="11" fill="currentColor">sérialiser, écrire, manifeste, renommer</text>
<line x1="157" y1="72" x2="168" y2="118" stroke="currentColor" stroke-opacity=".5"/>
<text x="320" y="176" text-anchor="middle" font-size="12" fill="currentColor">seul le snapshot (orange) bloque l'entraînement : δ bloquant ≪ durée totale d'écriture</text>
</svg>
<figcaption>Un checkpoint en deux phases. Le snapshot copie l'état vers la mémoire de l'hôte à un instant cohérent ; la persistance se déroule en arrière-plan pendant les pas suivants. Schéma : les durées ne sont pas à l'échelle.</figcaption>
</figure>

### 4.2. Les règles d'un checkpoint asynchrone correct

Rendre l'écriture asynchrone ajoute des modes de panne. Cinq règles les maîtrisent.

1.  **Un snapshot cohérent.** La copie vers l'hôte doit être terminée avant la mise à jour suivante des poids, sinon elle mélange deux pas. C'est la partie bloquante irréductible.
2.  **Une seule persistance en vol.** Si l'écriture précédente n'est pas finie quand le prochain intervalle arrive, on saute ce checkpoint ou on bloque ; sinon la mémoire de l'hôte et le stockage s'empilent.
3.  **Le même protocole de validation.** Une persistance qui meurt à mi-chemin ne doit rien laisser de visible (chapitre 3) : manifeste en dernier, renommage atomique.
4.  **Un budget de mémoire d'hôte.** Le snapshot occupe la taille de l'état local, par checkpoint en vol.
5.  **Une mesure du bon temps.** C'est le temps **bloquant** qui entre dans $\delta$, pas la durée totale. Mais si la persistance dure $P$ et dépasse la période $\tau$, la période effective devient $P$.

PyTorch fournit `torch.distributed.checkpoint.async_save`, dont la documentation décrit une version asynchrone de `save` qui commence par copier l'état vers un support intermédiaire. Elle renvoie un objet `Future` (ou, selon le mode, une réponse asynchrone) qu'il faut attendre avant le checkpoint suivant. Lisez la documentation de **votre** version : la signature de l'API a changé entre versions, et nous n'avons testé ici que `save` et `load` (PyTorch 2.14.1, CPU).

### 4.3. En mémoire et à plusieurs niveaux

La bande passante vers un stockage distant est le goulot. Le système Gemini (Wang et coauteurs, SOSP 2023) la contourne en écrivant les checkpoints dans la **mémoire CPU des machines hôtes**, dont la bande passante agrégée est beaucoup plus grande. L'article identifie deux difficultés : la disponibilité des checkpoints en mémoire au moment d'une panne n'est pas garantie, et le trafic de checkpoint partage le réseau avec le trafic d'entraînement. Il propose un placement des copies dont il prouve qu'il est proche de l'optimal, et une planification du trafic.

Cela conduit à un modèle à **deux niveaux** : un checkpoint rapide et fréquent (mémoire d'un pair) qui couvre la majorité des pannes, et un checkpoint durable et rare (stockage) pour le reste. Soit $p$ la fraction des pannes que le niveau 1 sait couvrir. Au premier ordre, chaque niveau suit la formule de Young avec un MTBF effectif $M/p$ ou $M/(1-p)$ :

$$\tau_1 = \sqrt{\frac{2\,\delta_1 M}{p}} \qquad \tau_2 = \sqrt{\frac{2\,\delta_2 M}{1-p}}$$

::: ex
[Exemple 4.1 — Un niveau ou deux ?]{.tag} Reprenons le job de 1 024 GPU ($M = 28{,}85$ h). Hypothèses **posées pour l'exemple**, à mesurer chez vous : niveau 1 avec $\delta_1 = 2$ s et $R_1 = 120$ s, niveau 2 avec $\delta_2 = 120$ s et $R_2 = 600$ s, et $p = 0{,}8$. 

Le calcul au premier ordre (**fait ici**, confirmé par minimisation numérique) donne 721 s (12 minutes) pour $\tau_1$ et 11 163 s (3,1 heures) pour $\tau_2$, soit un temps perdu de 2,9 %.

Avec le seul niveau 2, la période de Young serait de 4 992 s (83 minutes) et le temps perdu de 5,4 % (le modèle exact donne 5,3 %). Le second niveau divise presque par deux le temps perdu, à condition que $p = 0{,}8$ soit vrai : si le placement des copies fait qu'un nœud et son pair tombent ensemble, $p$ chute et le gain avec lui.
:::

### 4.4. La couche de stockage

Le rapport Llama 3 décrit ce que subit le stockage : « A major challenge is supporting the highly bursty checkpoint writes that saturate the storage fabric for short durations », avec un état de modèle par GPU « ranging from 1 MB to 4 GB ». Il note aussi que des dizaines de milliers de GPU qui attendent tous un checkpoint changent de consommation électrique au même instant. Un checkpoint synchrone arrête **tout** le cluster en même temps ; un checkpoint étalé lisse la charge.

Pour dimensionner, partez du chiffre voulu pour la persistance. Si l'état fait $S$ et que la persistance doit tenir dans une fraction $f$ de la période $\tau$, le débit d'écriture agrégé requis est $S/(f\tau)$.

Avec l'exemple 2.4 ($S = 980$ Go, $\tau = 455$ s, $f = 10$ %), il faut 21,5 Go/s (**calculé ici**). La lecture compte autant : à la relance, tous les rangs relisent en même temps, et ce débit entre dans $R$. MegaScale réduit la charge de lecture en faisant lire une partition par un rang du groupe de parallélisme de données, qui la diffuse ensuite aux autres rangs.

::: ex
[Exemple 4.2 — La borne supérieure de 65 To]{.tag} Avec 16 384 GPU et un état par GPU qui peut atteindre 4 Go (borne haute indiquée par le rapport Llama 3), un checkpoint complet pèse au plus $16\,384 \times 4$ Go $= 65{,}5$ To (**calcul de borne haute fait ici**, le rapport ne donne pas ce total). Écrire cela en 60 secondes demande plus d'un téraoctet par seconde en agrégé ; l'écrire en trente minutes en demande 36 Go/s. C'est l'argument pour étaler l'écriture sur la période plutôt que de la concentrer.
:::

### 4.5. Déduplication et rotation

Dans un entraînement parallèle en données, les réplicas contiennent des copies identiques des poids. Écrire $N$ copies est un gaspillage : un seul réplica par groupe doit écrire. Le planificateur par défaut de DCP expose un paramètre `dedup_replicated_tensors` ; lisez la documentation de votre version pour connaître son comportement par défaut. Entre deux checkpoints successifs, en revanche, presque tous les poids ont changé : la déduplication d'un checkpoint à l'autre rapporte peu, et c'est la **rotation** (garder les $K$ derniers checkpoints valides, un checkpoint plus ancien « de sécurité » tous les $L$ pas) qui borne le stockage.

::: recap
Points clés — chapitre 4

-   Seul le snapshot GPU vers hôte doit bloquer ; sérialisation et écriture se recouvrent avec le calcul.
-   Une persistance en vol à la fois, même protocole de validation, un budget de mémoire d'hôte.
-   $\delta$ dans la formule de Young est le temps **bloquant** ; la persistance doit tenir dans la période.
-   Deux niveaux (mémoire de pair, stockage durable) peuvent diviser le temps perdu, selon la part $p$ de pannes couvertes par le niveau rapide.
-   Dimensionnez le stockage sur l'état et la fraction de période acceptée, en écriture comme en lecture.
:::

## 5. Détecter : crashs, blocages, nœuds lents et silencieux {#ch5}

La reprise automatique commence par une question : **le job est-il en panne ?** Un processus qui s'arrête s'annonce lui-même. Un processus bloqué, un nœud lent ou un résultat faux ne s'annoncent pas, et ce sont eux qui coûtent le plus, parce que les GPU restent réservés pendant que rien d'utile ne se passe.

### 5.1. Quatre familles de symptômes

| Symptôme | Ce qu'on observe | Détecteur typique |
|---|---|---|
| Crash | un processus sort avec un code non nul ou un signal | l'agent de lancement (`torchrun`), l'ordonnanceur |
| Blocage | tous les processus sont vivants, aucun pas n'avance | compteur de progression, délai d'attente de collective |
| Lenteur | un rang ou un nœud ralentit tout le monde | temps de pas par rang, durée des collectives |
| Silence | le job avance, le résultat est faux | comparaison de répliques, tests à réponse connue, courbes de perte |

### 5.2. Les délais d'attente : un budget, pas une valeur par défaut

Une collective qui ne se termine pas laisse tous les rangs bloqués. PyTorch borne l'attente : la documentation de `init_process_group` indique un délai par défaut de 10 minutes pour NCCL et de 30 minutes pour les autres backends (vérifié aussi dans PyTorch 2.14.1 : `default_pg_timeout` vaut 0:30:00). Lu dans le code de l'agent élastique de la même version, `torchrun` positionne `TORCH_NCCL_ASYNC_ERROR_HANDLING` à 1 si vous ne l'avez pas fait.

Dix minutes de blocage sur un grand job se paient en GPU-heures.

::: ex
[Exemple 5.1 — Le prix d'un blocage détecté trop tard]{.tag} Un blocage sur 16 384 GPU, détecté par le délai NCCL de 10 minutes, laisse 16 384 GPU inactifs pendant 10 minutes : 2 731 GPU-heures (**calculé ici**). Avec un délai de 2 minutes, 546 GPU-heures. Sur 1 024 GPU, 171 GPU-heures pour 10 minutes. Un délai court détecte plus tôt mais risque de tuer un job sain pendant une phase légitimement lente (checkpoint synchrone, évaluation). Le bon délai est le plus court qui soit **plus long que la plus longue phase silencieuse légitime**, mesurée sur votre job.
:::

Au niveau du réseau, NCCL ajoute ses propres minuteries. Pour InfiniBand, la [documentation de NCCL](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html) précise que `NCCL_IB_TIMEOUT` fixe un délai de $4{,}096\ \mu s \times 2^{\text{valeur}}$, et que le temps total d'attente avant erreur est le produit de ce délai par `NCCL_IB_RETRY_CNT`. Avec la valeur 20 et 7 essais, la documentation indique environ 30 secondes (nous retrouvons $4{,}096\ \mu s \times 2^{20} = 4{,}29$ s, fois 7). Une valeur de 0, ou supérieure ou égale à 32, donne un délai infini.

Quand une erreur de communicateur NCCL est fatale, la documentation indique qu'il faut appeler `ncclCommAbort` puis recréer le communicateur : une collective bloquée ne se débloque pas d'elle-même.

### 5.3. Les pulsations

Un **watchdog** externe ne regarde pas si le processus vit, mais s'il **progresse**. Le motif du lab 10.3 : l'entraîneur touche un fichier de pulsation après chaque pas ; le superviseur compare l'âge de ce fichier à un délai. Trois choix de conception comptent.

-   **Progression, pas vivacité.** Un fil séparé qui envoie des pulsations tant que le processus est vivant masquera un blocage de la boucle principale. Placez la pulsation dans la boucle.
-   **Le démarrage compte comme une pulsation**, sans quoi un job lent à démarrer est tué en boucle.
-   **Le délai doit dépasser la plus longue phase légitime** sans pulsation (écriture synchrone, évaluation) : ajoutez une pulsation dans ces phases ou allongez le délai.

MegaScale décrit le même principe à grande échelle : des messages de pulsation envoyés régulièrement à un pilote, qui lance une série de tests de diagnostic quand une pulsation manque. Les auteurs rapportent que détection et diagnostic prennent en moyenne moins de 10 minutes.

Pour **injecter** un blocage dans un test, `kill -STOP <pid>` suspend un processus sans le tuer : à l'extérieur, c'est un blocage parfait. Le lab utilise un mode `hang` du faux entraîneur.

### 5.4. Les nœuds lents

Dans un entraînement synchrone, le temps de pas est le maximum des temps des rangs. Le rapport Llama 3 note : « Even a single straggler can slow down thousands of other GPUs, often appearing as functioning but slow communications ». MegaScale en donne un exemple chiffré : certains hôtes mettaient environ 10 % de plus pour les mêmes calculs, et leur retrait a amélioré le MFU d'environ 0,7 %.

::: ex
[Exemple 5.2 — Le prix d'un seul traînard]{.tag} Un rang 10 % plus lent allonge le pas de 10 % pour tout le job, soit un débit de $1/1{,}1 = 0{,}909$ : 9,1 % de perte. Sur 1 024 GPU, cela fait 2 234 GPU-heures par jour (**calculé ici**), soit l'équivalent de 93 GPU entièrement perdus, pour un seul nœud défectueux sur 128. Aucun code d'erreur ne se déclenche : seule la comparaison des temps de pas par rang le révèle.
:::

Le détecteur robuste compare chaque rang à la **médiane** de ses pairs avec une échelle fondée sur l'écart absolu médian (*MAD*) plutôt que sur l'écart-type, que le traînard lui-même déforme. Le [projet 5](../../projects/gpu-observability/index.html) construit ce détecteur et mesure son taux de fausses alertes et son délai de détection ; ne le réécrivez pas ici.

### 5.5. Le silence : résultats faux

Le rapport Llama 3 compte 6 cas de corruption silencieuse de données sur 419 interruptions imprévues (1,4 %) : rares, mais sans symptôme visible tant qu'on ne cherche pas. Le coût d'une telle erreur est un entraînement entier qui apprend de travers. Trois contrôles se recommandent, sans garantie d'exhaustivité : comparer périodiquement une somme de contrôle des poids entre répliques de données, qui doivent être identiques ; surveiller la norme des gradients et la perte pour repérer les sauts ; exécuter des tests à réponse connue dans le contrôle de santé des nœuds. Ce sont des recommandations de ce parcours.

::: war
[Un nœud défectueux qui revient]{.tag} Kokolis et coauteurs formulent une observation de leur étude : « One bad node spoils the bunch ». Sans contrôle de santé, un nœud défectueux revient dans l'allocation à chaque relance, et le job redémarre en boucle sur le même matériel. Ils notent aussi que le délai d'attente NCCL peut être attribué à tort au réseau alors que la cause est un blocage logiciel (« Beware of the red-herrings »). Source : [Kokolis et al., 2024, observations 2 et 3](https://arxiv.org/abs/2410.21680).
:::

::: recap
Points clés — chapitre 5

-   Quatre symptômes : crash, blocage, lenteur, silence ; seuls les crashs s'annoncent.
-   Le délai de détection est un budget : 10 minutes de blocage à 16 384 GPU coûtent 2 731 GPU-heures.
-   Une pulsation mesure la progression de la boucle principale, pas la vie du processus.
-   Un seul rang lent ralentit tout le job : comparez les rangs à la médiane, avec le MAD.
-   Les erreurs silencieuses se cherchent par comparaison de répliques et tests à réponse connue.
:::

## 6. Reprendre et redimensionner {#ch6}

Détecter ne sert à rien si la suite dépend d'un humain. Ce chapitre décompose le temps de relance, présente ce que fournit `torchrun` en mode élastique, la boucle d'un superviseur (lab 10.3) et sa traduction sous Slurm et sous Kubernetes.

### 6.1. Anatomie d'une reprise

Le coût de redémarrage $R$ du chapitre 2 est une somme de phases, dont chacune se mesure et se réduit séparément.

<figure class="fig">
<svg viewBox="0 0 640 150" role="img" aria-labelledby="rc-t rc-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="rc-t">Anatomie d'une reprise</title>
<desc id="rc-d">Six phases consécutives : détection, arrêt et nettoyage, réattribution des nœuds, initialisation distribuée, chargement du checkpoint, rattrapage du calcul perdu.</desc>
<rect x="20" y="40" width="130" height="34" fill="currentColor" fill-opacity=".30" stroke="currentColor"/>
<rect x="150" y="40" width="50" height="34" fill="currentColor" fill-opacity=".14" stroke="currentColor"/>
<rect x="200" y="40" width="110" height="34" fill="currentColor" fill-opacity=".30" stroke="currentColor"/>
<rect x="310" y="40" width="100" height="34" fill="currentColor" fill-opacity=".14" stroke="currentColor"/>
<rect x="410" y="40" width="80" height="34" fill="currentColor" fill-opacity=".30" stroke="currentColor"/>
<rect x="490" y="40" width="130" height="34" fill="var(--accent)" fill-opacity=".55" stroke="currentColor"/>
<text x="85" y="62" text-anchor="middle" font-size="11" fill="currentColor">1 détection</text>
<text x="175" y="62" text-anchor="middle" font-size="11" fill="currentColor">2</text>
<text x="255" y="62" text-anchor="middle" font-size="11" fill="currentColor">3 réattribution</text>
<text x="360" y="62" text-anchor="middle" font-size="11" fill="currentColor">4 init.</text>
<text x="450" y="62" text-anchor="middle" font-size="11" fill="currentColor">5 charge</text>
<text x="555" y="62" text-anchor="middle" font-size="11" fill="currentColor">6 rattrapage</text>
<text x="20" y="104" font-size="12" fill="currentColor">2 arrêt et nettoyage · 4 rendez-vous, communicateurs · 5 lecture du checkpoint · 6 pas recalculés</text>
<text x="20" y="128" font-size="12" fill="currentColor">R = 1 + 2 + 3 + 4 + 5 ; la phase 6 vaut en moyenne τ/2 : c'est le terme de la formule de Young</text>
</svg>
<figcaption>Les phases d'une reprise. Schéma : les largeurs ne sont pas des mesures. Les phases 1 à 5 forment le coût de redémarrage $R$ ; la phase 6 est le travail perdu.</figcaption>
</figure>

Les ordres de grandeur publiés : Kokolis et coauteurs prennent un temps d'initialisation $u_0$ de 5 à 20 minutes ; MegaScale indique moins de 10 minutes pour détecter et diagnostiquer, puis un rattrapage du calcul perdu en 15 minutes au plus depuis le dernier checkpoint. Ce sont leurs systèmes, pas le vôtre.

### 6.2. `torchrun` élastique

L'agent élastique de PyTorch (`torchrun`) lance les processus locaux, surveille leur état et gère un **rendez-vous** (*rendezvous*) entre nœuds. Selon la documentation (PyTorch 2.14) : si des travailleurs échouent, « all workers are stopped and restarted up to max_restarts » ; en cas de départ ou d'arrivée d'un nœud, un nouveau groupe de travailleurs est formé et tous reçoivent un nouveau `RANK` et un nouveau `WORLD_SIZE`. La syntaxe `--nnodes=1:4` autorise une taille variable entre 1 et 4 nœuds, et l'agent exporte `TORCHELASTIC_RESTART_COUNT` aux processus.

La documentation est explicite sur ce que cela ne fait pas : « On failures or membership changes ALL surviving workers are killed immediately. Make sure to checkpoint your progress. » Le redémarrage est donc un redémarrage complet depuis le dernier checkpoint, et le choix de sa fréquence reste le vôtre. Et l'agent ne sait pas remplacer un nœud : sa panne est traitée comme celle de ses travailleurs, et c'est au gestionnaire de jobs de faire échouer le job entier ou de remplacer le nœud.

::: ex
[Exemple 6.1 — Perdre un nœud quand le parallélisme est figé]{.tag} Un job de 64 nœuds de 8 GPU (512 GPU) avec parallélisme tensoriel de 8 et en pipeline de 4 a 32 GPU par réplica et donc 16 réplicas de données. Si un nœud disparaît, il reste 504 GPU ; $\lfloor 504/32 \rfloor = 15$ réplicas, soit 480 GPU utilisés et 24 inactifs (**calculé ici**). 

Le job perd donc 1/16 = 6,25 % de son débit pour 1/64 = 1,6 % de matériel perdu, et le lot global change (un réplica de moins) : il faut ajuster l'accumulation de gradients ou le taux d'apprentissage. Avec deux nœuds de rechange dans l'allocation, on remplace le nœud sans redimensionner. Le redimensionnement élastique n'est donc pas gratuit : il se décide par la taille des réplicas et par le nombre de rechanges.
:::

### 6.3. Un superviseur de relance

Sous Slurm comme sous Kubernetes, quelque chose doit décider « relancer ou abandonner ». Le lab 10.3 écrit ce composant sous forme d'un programme de quelques dizaines de lignes, testé. Sa politique :

1.  **Lancer** l'entraîneur dans son propre groupe de processus, avec le nom du nœud en variable d'environnement.
2.  **Surveiller** la pulsation ; au-delà du délai, tuer **tout le groupe** (un processus petit-fils survivant garderait un GPU).
3.  **Classer** l'issue : terminé, fatale (un code comme 2 qu'une relance ne corrigera pas), nœud auto-déclaré défectueux (code 42), blocage, autre.
4.  **Exclure** un nœud qui s'est déclaré défectueux, ou qui cause deux échecs.
5.  **Limiter** : un budget de relances, et une garde « aucun progrès » (deux tentatives de suite sans avancer le dernier checkpoint durable) qui arrête la boucle.

::: ex
[Exemple 6.2 — Journal d'une relance qui isole un nœud (lab 10.3)]{.tag} Plan de pannes **simulé** : `n0` plante une fois au pas 7, `n1` s'annonce défectueux (code 42) dès son démarrage. Journal réel de `supervisor.jsonl` (horodatages retirés, bac à sable, 2026-10-24) :

~~~text
{"event": "launch", "attempt": 1, "node": "n0", "resume_step": 0}
{"event": "exit", "attempt": 1, "node": "n0", "rc": 1, "kind": "retry", "step_before": 0, "step_after": 5}
{"event": "launch", "attempt": 2, "node": "n1", "resume_step": 5}
{"event": "exit", "attempt": 2, "node": "n1", "rc": 42, "kind": "node", "step_before": 5, "step_after": 5}
{"event": "exclude", "node": "n1", "why": "self-diagnosed"}
{"event": "launch", "attempt": 3, "node": "n2", "resume_step": 5}
{"event": "exit", "attempt": 3, "node": "n2", "rc": 0, "kind": "done", "step_before": 5, "step_after": 30}
{"event": "done", "attempts": 3}
~~~

La première tentative a progressé jusqu'au checkpoint du pas 5 puis a planté ; la deuxième, sur un autre nœud, a repris au pas 5 et s'est arrêtée aussitôt : `n1` est exclu ; la troisième termine à partir du même checkpoint. Aucun humain, trois lancements.
:::

La garde « aucun progrès » est la pièce que l'on oublie. Kokolis et coauteurs décrivent le pire cas, une boucle de plantage (*crash loop*) où un job est configuré pour se remettre en file à chaque échec : ils observent un job de 1 024 GPU qui a échoué en `NODE_FAIL` puis s'est remis en file 35 fois, causant 548 préemptions (sur plus de 7 000 GPU). Ils concluent que de telles situations doivent être évitées, parce qu'elles perturbent tout le cluster.

::: ex
[Exemple 6.3 — Une erreur de code ne doit pas brûler le cluster]{.tag} Même lab, plan de pannes où **tous** les nœuds échouent au pas 0 (un bogue logiciel). Journal réel :

~~~text
{"event": "launch", "attempt": 1, "node": "n0", "resume_step": 0}
{"event": "exit", "attempt": 1, "node": "n0", "rc": 1, "kind": "retry", "step_before": 0, "step_after": 0}
{"event": "launch", "attempt": 2, "node": "n1", "resume_step": 0}
{"event": "exit", "attempt": 2, "node": "n1", "rc": 1, "kind": "retry", "step_before": 0, "step_after": 0}
{"event": "give_up", "reason": "2 attempts without progress"}
~~~

Après deux tentatives sans progrès, le superviseur abandonne (statut 1) au lieu d'épuiser son budget de dix relances. La même panne partout n'est pas une panne de nœud : c'est le signal qu'un humain doit regarder.
:::

### 6.4. Sous Slurm

La documentation de `sbatch` précise que, avec `--requeue`, un job peut être remis en file ; « When a job is requeued, the batch script is initiated from its beginning with the same job ID ». 

Le script doit donc savoir reprendre (`--resume latest`). La variable `SLURM_RESTART_COUNT` indique le nombre de relances. `--signal=B:USR1@600` envoie un signal au script 600 secondes avant la limite de temps, pour déclencher un dernier checkpoint. 

Avec `--no-kill`, le job n'est pas tué si un nœud tombe, et la documentation précise que « The user will assume the responsibilities for fault-tolerance should a node fail ». `--exclude` écarte des nœuds.

Le script `examples/train.sbatch` du lab assemble ces options pour 4 nœuds ; il est linté, pas exécuté, faute de GPU. Il suppose un `train.py` à vous (non fourni) qui accepte `--resume latest` et teste un fichier de demande de checkpoint. En effet `torchrun` n'installe par défaut des gestionnaires que pour `SIGTERM`, `SIGINT`, `SIGHUP` et `SIGQUIT`, et ils arrêtent les processus (variable `TORCHELASTIC_SIGNALS_TO_HANDLE`, lue dans le code de PyTorch 2.14.1) : un `SIGUSR1` n'est pas relayé aux processus d'entraînement.

::: ex
[Exemple 6.4 — Ce que coûte une remise en file sous Slurm 23.11.4]{.tag} Le script `requeue_demo.sbatch` s'auto-remet en file deux fois puis se termine, sur le Slurm mono-nœud du module 5 (paquets Ubuntu 24.04, sans GPU). Sortie réelle (2026-10-24) :

~~~text
job=1 restart_count=0 node=vm
simulated node failure, requeueing
slurmstepd-vm: error: *** JOB 1 ON vm CANCELLED AT 2026-10-24T17:59:58 DUE TO JOB REQUEUE ***
job=1 restart_count=1 node=vm
simulated node failure, requeueing
slurmstepd-vm: error: *** JOB 1 ON vm CANCELLED AT 2026-10-24T18:02:55 DUE TO JOB REQUEUE ***
job=1 restart_count=2 node=vm
finished after 2 restarts
~~~

Entre les deux, `squeue` affichait l'état `PENDING` avec la raison `BeginTime`, et `scontrol show job` indiquait `Restarts=1`, puis `Restarts=2`. L'heure d'éligibilité était celle de la remise en file plus 121 secondes (17:59:58 devient 18:01:59, 18:02:55 devient 18:04:56), puis le job ne démarrait qu'au passage suivant de l'ordonnanceur. **Observation faite sur cette installation par défaut ; nous n'avons pas trouvé le paramètre en cause dans la documentation lue.** Retenez qu'un job remis en file n'est pas relancé immédiatement : ce délai entre dans $R$, et il faut le mesurer sur votre cluster.
:::

Le chapitre 7 du [module 5](../slurm/index.html) traite de l'autre moitié : le contrôle de santé et le drainage qui empêchent de retomber sur le nœud défectueux.

### 6.5. Sous Kubernetes

Un `Job` Kubernetes a un `backoffLimit` (6 par défaut d'après la documentation) et applique, entre les essais, un délai exponentiel « (10s, 20s, 40s ...) capped at ten minutes ». 

Six essais consomment donc 10 + 20 + 40 + 80 + 160 + 320 = 630 secondes de délai cumulé (**calculé ici**), à ajouter à $R$. La *pod failure policy* permet de distinguer les causes : une règle `FailJob` sur un code de sortie (« erreur de configuration, ne pas réessayer ») et une règle `Ignore` sur la condition `DisruptionTarget` (le nœud a été drainé ou le pod préempté, ce qui ne doit pas compter dans le budget). 

`examples/job.yaml` du lab montre les deux règles ; il est linté (`yamllint`), non appliqué à un cluster. Un entraînement multi-nœuds demande en plus une sémantique de gang, que ce module ne traite pas.

::: recap
Points clés — chapitre 6

-   $R$ est une somme de phases (détection, arrêt, réattribution, initialisation, chargement) ; mesurez chacune.
-   `torchrun` redémarre tout depuis le dernier checkpoint ; l'élasticité ne redimensionne pas votre parallélisme.
-   Un superviseur classe, exclut, limite ; sa garde « aucun progrès » évite la boucle de plantage.
-   Sous Slurm, `--requeue` relance le script depuis le début ; un délai de remise en file entre dans $R$.
-   Sous Kubernetes, `backoffLimit` et la pod failure policy séparent erreur de code et perturbation de nœud.
:::

## 7. Erreurs GPU courantes {#ch7}

Quand un GPU tombe en panne, le premier témoin est le journal du noyau. Ce chapitre apprend à le lire sans surinterpréter, à connaître les mécanismes de mémoire des GPU récents, et à poser une règle de conduite : relancer le job, drainer le nœud, ou ouvrir un dossier chez le fournisseur.

### 7.1. Lire un message Xid

La documentation de NVIDIA définit un message Xid comme un rapport d'erreur du pilote, écrit dans le journal du noyau : il peut révéler un problème matériel, un problème du pilote ou un problème de l'application. Sous Linux, on les trouve en cherchant `NVRM: Xid` dans le journal (`dmesg`, `journalctl -k`, `/var/log/syslog`). Le format donné en exemple par la documentation est :

~~~text
[...] NVRM: Xid (0000:03:00): 14, Channel 00000001
~~~

`0000:03:00` est l'adresse PCI du GPU, `14` le numéro d'Xid, `Channel 00000001` une donnée propre à cette erreur. La documentation insiste : ces messages sont des guides de débogage, pas des verdicts, parce qu'une corruption de la mémoire ou du bus peut faire apparaître presque n'importe quelle erreur. Utilisez-les comme point de départ.

Le catalogue des Xid (page « Analyzing Xid Errors with the Xid Catalog », mise à jour le 9 septembre 2026, lue le 24 octobre 2026) associe à chaque numéro un nom, une description, des architectures concernées et deux colonnes d'action : une **action immédiate** et une **action d'investigation**. Voici les entrées qui reviennent le plus, avec les libellés du catalogue :

| Xid | Nom du catalogue | Description | Action immédiate |
|---|---|---|---|
| 13 | `ROBUST_CHANNEL_GR_EXCEPTION` | exception du moteur graphique | `RESTART_APP` |
| 31 | `ROBUST_CHANNEL_FIFO_ERROR_MMU_ERR_FLT` | faute de page mémoire du GPU | `RESTART_APP` |
| 45 | `ROBUST_CHANNEL_PREEMPTIVE_REMOVAL` | nettoyage préventif après erreurs antérieures | `WORKFLOW_XID_45` |
| 48 | `ROBUST_CHANNEL_GPU_ECC_DBE` | erreur ECC à double bit | `WORKFLOW_XID_48` |
| 63 | `INFOROM_DRAM_RETIREMENT_EVENT` | événement de remappage mémoire | `IGNORE` |
| 64 | `INFOROM_DRAM_RETIREMENT_FAILURE` | échec du remappage mémoire | `RESET_GPU` |
| 74 | `NVLINK_ERROR` | erreur NVLink | `WORKFLOW_NVLINK_ERR` |
| 79 | `ROBUST_CHANNEL_GPU_HAS_FALLEN_OFF_THE_BUS` | le GPU est tombé du bus | `RESTART_BM` |
| 94 | `ROBUST_CHANNEL_CONTAINED_ERROR` | erreur mémoire contenue | `RESTART_APP` |
| 95 | `ROBUST_CHANNEL_UNCONTAINED_ERROR` | erreur mémoire non contenue | `RESET_GPU` |
| 119, 120 | `GSP_RPC_TIMEOUT`, `GSP_ERROR` | erreur ou délai du processeur GSP | `RESET_GPU` |
| 140 | `UNRECOVERABLE_ECC_ERROR_ESCAPE` | erreur ECC non récupérée | `RESET_GPU` |
| 154 | `GPU_RECOVERY_ACTION_CHANGED` | changement d'action de récupération | informatif |

Nous reproduisons les libellés tels quels : les sigles de la colonne d'action (`RESTART_APP`, `RESET_GPU`, `RESTART_BM`, `WORKFLOW_*`) ne sont pas définis dans la page lue, et nous ne les traduisons pas. Le catalogue précise que l'Xid 154 « summarizes the recovery action required for other Xids » : lisez-le avec l'Xid qu'il accompagne. Dans leurs clusters de recherche, Kokolis et coauteurs observent que 43 % des erreurs PCIe de RSC-1 (63 % pour RSC-2) coïncident avec l'Xid 79, ce qui rappelle qu'un symptôme peut venir d'un bus et pas du GPU.

### 7.2. Mémoire : ECC, confinement et remappage

La documentation de NVIDIA sur la gestion des erreurs mémoire des GPU Ampere et suivants décrit trois mécanismes. Le **confinement d'erreur** limite l'impact d'une erreur ECC non corrigeable aux applications qui la rencontrent : les autres continuent, et les GPU de ces générations ne demandent pas de réinitialisation à chaque erreur mémoire. La **mise hors service dynamique de pages** marque comme inutilisable la page où l'erreur est apparue. 

Le **remappage de lignes** remplace dans le matériel les cellules dégradées par des lignes de rechange ; selon la documentation, « The process of row-remapping requires a GPU reset to take effect ».

Les systèmes exposent aussi un **drapeau d'action de récupération**. Ses valeurs, dans la documentation : aucune, **réinitialisation du GPU**, **redémarrage du système**, **vidange du trafic pair-à-pair**, et **vidange puis réinitialisation**. Pour la dernière, le GPU fonctionne à capacité réduite : aucun nouveau travail ne doit y être placé, mais le travail non affecté peut continuer « until they finish or reach a good checkpoint ». C'est exactement la conduite à tenir pour un entraînement : demander un checkpoint, puis drainer le nœud.

### 7.3. Réseau et liens

Les erreurs NVLink (Xid 74) et les liens InfiniBand qui flottent donnent des blocages de collectives, c'est-à-dire des délais d'attente NCCL (chapitre 5). Le rapport Llama 3 note que des défaillances du GPU distant ou de NVLink se manifestent souvent comme des opérations de chargement ou de rangement bloquées dans des noyaux CUDA, sans code d'erreur. Pour isoler un lien suspect, lancez un test de communication (par exemple `nccl-tests`) entre le nœud et ses voisins, avant la remise en service. Le [module 7](../networking/index.html) approfondit le réseau.

### 7.4. Thermique

Les auteurs d'Acme décrivent des pannes liées à la chaleur : sur leur cluster, l'entraînement de modèles de 7 milliards de paramètres a fait monter la température de la salle d'environ 5 °C, avec des erreurs NVLink et ECC à la clé. Ils ont renforcé le refroidissement et la fréquence de ces pannes a nettement baissé.

::: war
[Une salle trop chaude]{.tag} Hu et coauteurs rapportent que l'entraînement de modèles de 7 milliards de paramètres sur le cluster Kalos, très optimisé pour la communication et donc presque sans temps mort pour les GPU, s'est accompagné d'une hausse de température de la salle d'environ 5 °C et d'erreurs NVLink et ECC, surtout en juillet 2023. Le refroidissement a été amélioré. Source : [Hu et al., 2024, section 5.2](https://arxiv.org/abs/2403.07648).
:::

### 7.5. La conduite à tenir

Une règle de décision courte vaut mieux qu'un catalogue. Le lab 10.3 contient `xid_triage.py`, qui lit un journal et classe chaque GPU. Les niveaux sont la **politique de ce cours** (une recommandation, pas une règle de NVIDIA) :

| Niveau | Quand | Action |
|---|---|---|
| 0, surveiller | Xid dont le catalogue dit d'ignorer l'action immédiate (43, 63) ou qui accompagne un autre (45, 154) | noter, ne rien faire |
| 1, relancer le job | erreurs d'application (13, 31, 94) | relancer ; si l'erreur se répète sur plusieurs nœuds, chercher dans le code |
| 2, drainer le nœud | erreurs ECC (48, 140), mémoire (64, 95), NVLink (74), bus (79), GSP (119, 120) | demander un checkpoint, drainer avec une raison, collecter les preuves, réinitialiser ou redémarrer, puis recette |

::: ex
[Exemple 7.1 — Triage d'un journal (lab 10.3)]{.tag} Sur la fixture **synthétique** `fixtures/kernel_log_sample.txt` (écrite à la main dans le format de la documentation, pas une capture d'une vraie machine), `xid_triage.py` donne :

~~~text
gpu 0000:3b:00  xid  45  x2  catalog=WORKFLOW_XID_45      course-level=watch
gpu 0000:3b:00  xid  48  x1  catalog=WORKFLOW_XID_48      course-level=drain-node
gpu 0000:3b:00  xid  63  x1  catalog=IGNORE               course-level=watch
gpu 0000:3b:00  xid 154  x1  catalog=XID_154              course-level=watch
gpu 0000:5e:00  xid  13  x1  catalog=RESTART_APP          course-level=restart-job
gpu 0000:86:00  xid  74  x3  catalog=WORKFLOW_NVLINK_ERR  course-level=drain-node
node verdict: drain-node
~~~

Le GPU `3b:00` porte une erreur ECC à double bit, dont les Xid 45 et 154 sont les échos : à drainer. Le GPU `86:00` cumule trois erreurs NVLink : à drainer aussi. Le GPU `5e:00` n'a qu'une exception d'application : à elle seule, elle ne justifie pas de retirer le nœud. Le verdict du nœud est le pire des niveaux.
:::

**Avant de réinitialiser, préservez les preuves.** La documentation indique que `nvidia-bug-report.sh` collecte les journaux et les sorties de commandes dans un fichier `nvidia-bug-report.log.gz`, qu'il faut lui laisser jusqu'à une heure dans de rares cas, et qu'il existe une variante `--safe-mode`. Ajoutez la sortie de `nvidia-smi -q`, le journal du noyau, l'identifiant du job et l'heure. Après réparation, une **recette** (diagnostic DCGM, test de communication) précède la remise en service, et la règle du module 5 s'applique : trois drains en sept jours sortent le nœud de la production.

::: recap
Points clés — chapitre 7

-   Un message Xid est un guide de débogage ; cherchez `NVRM: Xid` et lisez l'Xid 154 avec celui qu'il accompagne.
-   Le catalogue donne une action immédiate par Xid ; reprenez ses libellés, ne les inventez pas.
-   Confinement, mise hors service de pages et remappage (qui demande une réinitialisation) protègent la mémoire des GPU récents.
-   « Vidange puis réinitialisation » veut dire : checkpoint, puis drainage.
-   Drainez avec une raison, préservez les preuves avant de réinitialiser, validez avant de remettre en service.
:::

## 8. Tests de chaos, procédures et post-mortems {#ch8}

Un mécanisme de reprise que personne n'a jamais déclenché ne marche pas, il est seulement non testé. Ce chapitre organise les essais de pannes, les procédures écrites et l'apprentissage après incident.

### 8.1. L'ingénierie du chaos appliquée à l'entraînement

Le site des *Principles of Chaos Engineering* définit la discipline comme l'expérimentation sur un système pour établir la confiance dans sa capacité à résister à des conditions turbulentes. La méthode : définir un **état stable** (*steady state*), « some measurable output of a system that indicates normal behavior », formuler l'hypothèse qu'il persiste dans le groupe de contrôle comme dans le groupe expérimental, puis chercher à la réfuter en introduisant des événements du monde réel comme la mort d'un serveur.

Pour un entraînement, l'état stable se mesure : goodput, temps de pas, courbe de perte, nombre d'interventions humaines. L'hypothèse se chiffre : « si je tue un rang, le job repart seul en moins de $X$ minutes et perd moins de $Y$ pas ». Une expérience sans hypothèse chiffrée est une démonstration, pas un test.

### 8.2. Un catalogue d'injections

| Panne injectée | Comment | Ce qu'on vérifie | Dans ce module |
|---|---|---|---|
| Mort d'un processus | `kill -9` du groupe de processus | reprise, identité de l'état final | lab 10.2 |
| Écriture interrompue | arrêt brutal au milieu d'un `save` | aucun demi-checkpoint visible | lab 10.2 (tests) |
| Checkpoint abîmé | inverser un octet du plus récent | repli sur le précédent | lab 10.2 (tests) |
| Blocage | `kill -STOP`, ou mode `hang` du faux entraîneur | détection par pulsation, destruction du groupe | lab 10.3 |
| Nœud défectueux | plan de pannes lié à un nom de nœud | exclusion, absence de boucle | lab 10.3 |
| Stockage lent | latence artificielle par fichier | contre-pression, période effective | lab 10.2 |
| Nœud lent, coupure réseau, erreur GPU | `stress-ng` sur un nœud, règles de pare-feu, injection DCGM | détection, drainage | à vérifier sur votre infrastructure |

La dernière ligne reste hors des labs : nous n'avons pas testé ces outils ici, et une injection réseau ou GPU réelle demande des garde-fous (périmètre, durée, annulation) que seul votre environnement peut fournir.

### 8.3. Les journées d'exercice (*game days*)

Une journée d'exercice est une expérience de chaos planifiée, avec les personnes qui interviendraient en vrai. Préparez : l'hypothèse chiffrée, le périmètre (un job de 64 GPU, pas la production), les **critères d'arrêt** (« on interrompt si la perte dépasse $Z$ »), les rôles (qui injecte, qui observe, qui décide) et l'enregistrement du déroulé minute par minute.

::: ex
[Exemple 8.1 — Un budget de temps pour une expérience]{.tag} Pour un job de 1 024 GPU avec un checkpoint toutes les 455 s (exemple 2.4), une détection visée à 3 minutes et un redémarrage de 15 minutes (900 s, **hypothèses**), le pire cas d'un `kill -9` est : 180 + 900 + 455 = 1 535 s, soit 25,6 minutes, hors rattrapage. 

L'hypothèse de l'expérience s'écrit alors : « le job est de nouveau en train de calculer 26 minutes au plus après la mort du rang, sans intervention, et l'état final est celui d'une exécution sans panne ». Si la mesure dépasse le budget, l'expérience a trouvé une phase de la reprise (chapitre 6) à raccourcir : c'est son but.
:::

### 8.4. Les runbooks

Un runbook est la procédure écrite de quelqu'un qui n'a pas le temps de réfléchir : à trois heures du matin, on suit, on ne conçoit pas. Chaque entrée suit le même format : **symptôme**, **vérifications dans l'ordre**, **action**, **quand escalader**. Squelette pour « l'entraînement ne repart pas après une panne » :

1.  Le superviseur a-t-il abandonné ? Lire `supervisor.jsonl` : raison de l'abandon (budget, aucun progrès, aucun nœud sain).
2.  Aucun progrès : le dernier checkpoint valide est-il lisible ? Vérifier les empreintes ; essayer le précédent.
3.  Même échec sur plusieurs nœuds : chercher dans le code ou la configuration, pas dans le matériel.
4.  Échec sur un seul nœud : le drainer avec une raison, relancer ailleurs.
5.  Perte NaN après reprise : revenir à un checkpoint plus ancien (une empreinte correcte ne prouve pas que le contenu l'est).
6.  Escalade : si deux checkpoints successifs échouent ou si plus de $N$ nœuds sont drainés dans l'heure.

### 8.5. Le post-mortem sans blâme

Le livre *Site Reliability Engineering* de Google définit un post-mortem comme « a written record of an incident, its impact, the actions taken to mitigate or resolve it, the root cause(s), and the follow-up actions to prevent the incident from recurring », et pose que les post-mortems sans blâme sont un principe de la culture SRE.

Ils cherchent les causes contributives sans mettre en cause une personne ou une équipe, en supposant que chacun a fait de son mieux avec l'information dont il disposait. Pour un entraînement, ajoutez une ligne que tout le monde comprend : les **GPU-heures perdues**, avec leur décomposition.

::: ex
[Exemple 8.2 — Chiffrer un incident (scénario fictif)]{.tag} Sur un job de 1 024 GPU, un nœud tombe en panne à 03 h 02. **Scénario fictif, pour l'exercice** : la détection prend 12 minutes, la relance 18 minutes, le recalcul 14 minutes. Total 44 minutes, soit $1024 \times 44/60 = 751$ GPU-heures perdues (**calculé ici**). 

Le post-mortem identifie que 12 minutes de détection viennent d'un délai trop long : le ramener à 3 minutes économise $1024 \times 9/60 = 154$ GPU-heures **par incident**. Avec 0,83 incident par jour sur 128 nœuds (taux de l'exemple 1.1), l'action de suivi « raccourcir la détection » vaut environ 128 GPU-heures par jour, à comparer au risque de fausses alertes (exercice 7).
:::

Un bon post-mortem se termine par des actions **vérifiables** : un test qui échoue avant la correction et passe après, une alerte, une ligne de runbook. Le [projet 3](../../projects/resilient-trainer/index.html) vous demande un ADR et un runbook, et le [projet 6](../../projects/capstone-rfc/index.html) les réutilise.

::: recap
Points clés — chapitre 8

-   Un test de chaos part d'un état stable mesurable et d'une hypothèse chiffrée.
-   Injectez ce que vous savez injecter sans danger (mort, blocage, checkpoint abîmé, nœud défectueux, stockage lent) et gardez le reste pour une journée d'exercice encadrée.
-   Un budget de temps par expérience fait de la reprise un objet mesurable.
-   Un runbook se suit à trois heures du matin : symptôme, vérifications ordonnées, action, escalade.
-   Un post-mortem sans blâme chiffre l'incident en GPU-heures et finit par des actions vérifiables.
:::

## Labs {#labs}

Les trois labs tournent sur un portable Linux **sans GPU**, avec Python et PyTorch CPU (testés avec PyTorch 2.14.1 le 2026-10-24). Ils sont indépendants des modules 8 et 9 et utilisent des pannes **simulées**, signalées comme telles dans chaque `README.md`. Préparation :

~~~bash
python3 -m venv .venv && . .venv/bin/activate
pip install numpy scipy pytest pyyaml safetensors
pip install torch --index-url https://download.pytorch.org/whl/cpu
export PYTHON="$(command -v python)"
~~~

### Lab 10.1 — Intervalle de checkpoint optimal {#lab-10-1}

::: lab

**Objectif.** Comparer l'intervalle de Young, l'estimation de Daly et le minimum du modèle exact à une simulation de Monte-Carlo, et voir où le premier ordre cesse de valoir. **Durée.** 3 h. **Prérequis matériels.** Un portable, 1 cœur, quelques secondes de calcul ; aucun GPU.

1.  Lisez `labs/fault-tolerance/young-daly/yd.py` : repérez le simulateur (`simulate`) et le modèle exact (`wall_per_work_exact`).
2.  Lancez `python3 sweep.py --delta 60 --mtbf-hours 3.09 --restart 300 --svg yd.svg` et ouvrez le graphique.
3.  Modifiez `--delta` à 600 puis 3000 : à partir de quel rapport $\delta/M$ la formule de Young s'écarte-t-elle de plus de 10 % du minimum exact ?
4.  Relancez avec `--weibull-shape 0.5` : que devient le meilleur point échantillonné ?
5.  Lancez `bash verify.sh` et lisez les 9 tests.

**Critère de réussite.** `bash verify.sh` affiche « OK young-daly: Young T=1155 s, Daly T=1116 s, exact argmin T=1116 s; goodput at Young 0.8767 vs best sampled 0.8767 » (sortie réelle du bac à sable, 2026-10-24) après `9 passed`. Temps d'exécution : environ deux secondes.

**Pour aller plus loin.** Remplacez les pannes de Weibull par une trace de pannes réelle de votre cluster (rejouée), et ajoutez un second niveau de checkpoint au simulateur (exemple 4.1).
:::

### Lab 10.2 — Checkpoint atomique et reprise exacte {#lab-10-2}

::: lab

**Objectif.** Écrire et casser un checkpoint par répertoire, prouver qu'une reprise complète est identique à l'exécution continue, mesurer ce que chaque partie de l'état protège, et survivre à une campagne de `kill -9`. **Durée.** 4 h. **Prérequis matériels.** Un portable avec PyTorch CPU ; environ 50 secondes pour `verify.sh`.

1.  Lisez `ckpt.py` : repérez le répertoire temporaire, le manifeste écrit en dernier et le renommage.
2.  Lancez `python3 ablate.py` et expliquez, pour chaque ligne du tableau, pourquoi le premier pas faux est celui-là.
3.  Lancez `python3 chaos.py --out /tmp/chaos` plusieurs fois avec `--seed` différent : notez le nombre de pannes, de pas rejoués et de répertoires temporaires rencontrés.
4.  Lancez `python3 dcp_reshard.py` et `python3 safetensors_peek.py` ; retrouvez dans l'en-tête le décalage de chaque tenseur.
5.  Cassez le code : supprimez le `fsync` du fichier, ou écrivez le manifeste en premier. Quel test échoue, lequel ne détecte rien, et pourquoi (indice : une coupure de courant n'est pas un `kill -9`) ?

**Critère de réussite.** `bash verify.sh` passe 11 tests, affiche le tableau d'ablation, le résultat du DCP et du `safetensors`, puis « OK atomic-checkpoint: final state digest identical (948207a8778d...) after the kill campaign ». L'empreinte vue ci-dessus est celle de cette machine et de ce PyTorch ; la vôtre peut différer, **elle doit être identique entre la référence et la campagne**.

**Pour aller plus loin.** Ajoutez la reprise sur un nombre de rangs différent avec DCP, ou une persistance asynchrone dans un fil, avec une seule écriture en vol. **Limites.** Le `kill -9` n'efface pas le cache du noyau : il ne prouve pas la durabilité après une coupure de courant. Les délais (`--sleep-ms`, `--slow-ckpt-ms`) sont simulés.
:::

### Lab 10.3 — Superviseur de relance {#lab-10-3}

::: lab

**Objectif.** Écrire un superviseur qui détecte plantage et blocage, tue le groupe de processus, exclut un nœud fautif et s'arrête quand il ne progresse plus, et lire un journal d'erreurs GPU. **Durée.** 4 h. **Prérequis matériels.** Un portable ; aucun GPU, aucun Slurm requis pour la partie A.

1.  Partie A. Lancez `IMPL=starter python3 -m pytest -q test_supervisor.py` : 10 échecs. Lisez chaque message.
2.  Complétez `starter/supervisor.py` (`classify`, `kill_group`, `Supervisor.run`) sans lire `reference/` ; faites passer les tests un par un.
3.  Comparez avec `reference/supervisor.py` : la garde « aucun progrès », l'exclusion après deux échecs, le traitement de `SIGTERM`.
4.  Lancez `python3 xid_triage.py fixtures/kernel_log_sample.txt` ; ajoutez un Xid de votre choix à la table `CATALOG` avec sa source.
5.  Partie B, facultative (root et Slurm du module 5) : `sudo bash slurm_demo.sh`, environ cinq minutes à cause du délai de remise en file (exemple 6.4).

**Critère de réussite.** `bash verify.sh` affiche `13 passed` (10 tests du superviseur et 3 du triage Xid), puis `starter (failures expected): 10 failed`, puis « OK supervisor-loop: reference green, starter red; examples linted (not executed) ». **Branches.** La partie A et le triage Xid sont vérifiés dans le bac à sable ; `examples/train.sbatch` et `examples/job.yaml` sont seulement linté (`shellcheck`, `yamllint`) car ils demandent des GPU ou un cluster ; `slurm_demo.sh` (partie B, avec `requeue_demo.sbatch`) a été exécuté de bout en bout une fois sur Slurm 23.11.4 (5 min 44 s, le 2026-10-24) et n'est pas lancé par `verify.sh`.

**Pour aller plus loin.** Ajoutez une attente exponentielle entre relances (option `--backoff`), un mode « un nœud sur deux traînard » détecté par comparaison à la médiane, ou branchez le superviseur sur le vrai entraîneur du lab 10.2.
:::

## Exercices {#ex}

Les calculs des corrigés ont été refaits en Python (avec `yd.py` du lab 10.1 pour les modèles de checkpoint et `scipy.stats.poisson` pour l'exercice 9), et les commandes citées ont été exécutées dans le bac à sable.

::: exo
[Exercice 1 · ★ — MTBF d'un job]{.tag} Les nœuds d'un cluster tombent en panne au taux de 6,5 pannes pour mille nœuds-jours. Un job occupe 256 nœuds (2 048 GPU). (a) Quel est son MTBF ? (b) Quelle est la probabilité qu'il tourne 48 heures sans aucune panne ? (c) Combien de pannes attendez-vous en moyenne en 48 heures ?
:::

::: sol
(a) Le job subit $256 \times 0{,}0065 = 1{,}664$ pannes par jour, donc son MTBF est $24/1{,}664 = 14{,}4$ heures.

(b) Avec des pannes de Poisson, $P = e^{-48/14{,}42} = e^{-3{,}33} \approx 0{,}036$, soit 3,6 %, une chance sur 28.

(c) $48/14{,}42 = 3{,}33$ pannes. Sans checkpoint, ce job n'irait au bout de ses 48 heures qu'une fois sur 28 : la tolérance aux pannes n'est pas optionnelle à cette échelle.
:::

::: exo
[Exercice 2 · ★ — Young sur le job de l'exercice 1]{.tag} Le checkpoint bloque l'entraînement $\delta = 30$ s et le redémarrage coûte $R = 600$ s. (a) Calculez la période de Young. (b) Donnez le goodput du premier ordre à cette période. (c) Comparez avec un checkpoint toutes les heures, et exprimez la différence en GPU-heures par jour.
:::

::: sol
Avec $M = 14{,}42$ h $= 51\,923$ s :

(a) $\tau^{\ast} = \sqrt{2 \times 30 \times 51\,923} = 1765$ s, soit 29,4 minutes.

(b) Le temps perdu vaut :

$$W^{\ast} = \sqrt{\frac{2\delta}{M}} + \frac{R}{M} = 0{,}0340 + 0{,}0116 = 0{,}0455$$

Soit un goodput de 95,4 % (le modèle exact donne 95,5 %).

(c) À $\tau = 3600$ s :

$$W = \frac{30}{3600} + \frac{1800 + 600}{51\,923} = 0{,}0083 + 0{,}0462 = 0{,}0546$$

Soit 94,5 %. L'écart est de 0,90 point, soit $0{,}0090 \times 2048 \times 24 \approx 443$ GPU-heures par jour. Le checkpoint horaire coûte donc environ 443 GPU-heures quotidiennes de plus que l'optimum, pour ce job.
:::

::: exo
[Exercice 3 · ★ — Lire un balayage]{.tag} Avec le tableau de l'exemple 2.2 seulement : (a) quelle période choisissez-vous ? (b) Que perdez-vous en prenant 2 311 s ou 578 s ? (c) Un collègue propose « un checkpoint toutes les 5 minutes, par prudence » (289 s) : que répondez-vous ? (d) Pourquoi la colonne du premier ordre est-elle inférieure à celle du modèle exact ?
:::

::: sol
(a) 1 155 s : le goodput simulé y est maximal (0,8767).

(b) À 2 311 s, 0,8534, soit 2,3 points de moins ; à 578 s, 0,8573, soit 1,9 point de moins. L'optimum est plat.

(c) À 289 s, le goodput simulé tombe à 0,7939 : 8,3 points de moins qu'à l'optimum. « Par prudence » n'est pas gratuit : trop fréquent coûte autant que trop rare (à 4 621 s, 4 fois la période de Young, la perte est de 10,2 points).

(d) Le premier ordre approxime la perte de recalcul et néglige des termes d'ordre supérieur en $\tau/M$ et $\delta/M$ ; il sous-estime donc le goodput d'environ 0,7 point à l'optimum et de 1,3 à 4,1 points aux extrémités de la grille.
:::

::: exo
[Exercice 4 · ★★ — Recalculer un tableau publié]{.tag} Le tableau 5 de l'article Llama 3 donne, sur 419 interruptions imprévues : défaut du GPU 148 (30,1 %), mémoire HBM3 72, mémoire SRAM 19, processeur système du GPU 17, corruption silencieuse 6, capteur thermique 6. Le texte dit que les GPU forment 58,7 % des causes imprévues. (a) Quelle part obtenez-vous à partir des comptes ? (b) Que faudrait-il pour que 58,7 % soit juste ? (c) Que concluez-vous ?
:::

::: sol
(a) $148 + 72 + 19 + 17 + 6 + 6 = 268$, et $268/419 = 64{,}0\ \%$. Au passage, $148/419 = 35{,}3\ \%$, pas 30,1 %.

(b) 58,7 % de 419 font 246 interruptions de GPU. C'est ce qu'on obtient si « défaut du GPU » vaut 126, car $0{,}301 \times 419 = 126$ et $126 + 72 + 19 + 17 + 6 + 6 = 246$. Mais alors les comptes de tout le tableau ne somment plus à 419 mais à 397.

(c) Le tableau ne peut pas être cohérent avec ses deux colonnes à la fois. Les comptes somment exactement à 419, les pourcentages des autres lignes sont ceux de comptes divisés par 419 : la ligne « défaut du GPU » est la seule incohérente. Les pourcentages publiés des six lignes GPU (30,1 ; 17,2 ; 4,5 ; 4,1 ; 1,4 ; 1,4) additionnés donnent bien 58,7 %, ce qui montre d'où vient ce chiffre. Sans accès aux données, il faut signaler l'écart, citer les **comptes** et recalculer les parts. Dans les deux lectures, les GPU restent la première famille.
:::

::: exo
[Exercice 5 · ★★ — Lire le journal d'un superviseur]{.tag} Voici le `supervisor.jsonl` d'un job de 30 pas avec deux nœuds, `n0` et `n1`, un checkpoint tous les 5 pas et une politique d'exclusion à deux échecs (pannes simulées du lab 10.3).

~~~text
{"event": "launch", "attempt": 1, "node": "n0", "resume_step": 0}
{"event": "exit", "attempt": 1, "node": "n0", "rc": 1, "kind": "retry", "step_before": 0, "step_after": 5}
{"event": "launch", "attempt": 2, "node": "n1", "resume_step": 5}
{"event": "exit", "attempt": 2, "node": "n1", "rc": 1, "kind": "retry", "step_before": 5, "step_after": 5}
{"event": "launch", "attempt": 3, "node": "n0", "resume_step": 5}
{"event": "exit", "attempt": 3, "node": "n0", "rc": 1, "kind": "retry", "step_before": 5, "step_after": 10}
{"event": "exclude", "node": "n0", "why": "2 strikes"}
{"event": "launch", "attempt": 4, "node": "n1", "resume_step": 10}
{"event": "exit", "attempt": 4, "node": "n1", "rc": 0, "kind": "done", "step_before": 10, "step_after": 30}
{"event": "done", "attempts": 4}
~~~

(a) Pourquoi `n0` est-il exclu après la tentative 3 et pas `n1` après la tentative 2 ? (b) Quelle progression durable chaque tentative a-t-elle apportée ? (c) L'exclusion de `n0` est-elle prouvée par ce journal ? (d) Que se serait-il passé si la tentative 3 n'avait pas progressé ?
:::

::: sol
(a) `n0` a subi deux échecs (tentatives 1 et 3), ce qui atteint le seuil de deux de la politique ; `n1` n'en a subi qu'un à ce stade.

(b) Progressions durables (`step_after - step_before`) : +5, +0, +5, +20. La tentative 2 n'a rien rapporté : son travail et son redémarrage sont entièrement perdus.

(c) Non. Deux échecs ne sont pas une preuve : c'est une règle de politique, qui tolère de se tromper. `n1` a aussi échoué une fois. Pour confirmer, comparez les messages d'erreur (les mêmes sur les deux nœuds indiquent un bogue logiciel), cherchez des Xid dans le journal du noyau de `n0` et lancez le contrôle de santé.

(d) Deux tentatives consécutives sans progrès (2 et 3) auraient déclenché la garde : le superviseur aurait écrit `give_up` avec la raison `2 attempts without progress` et rendu le statut 1. Journal reproductible avec `FAULT_PLAN` comme dans le test `test_two_strikes_exclude_a_node`.
:::

::: exo
[Exercice 6 · ★★ — Dimensionner un checkpoint de 175 milliards de paramètres]{.tag} Un job de 2 048 GPU (256 nœuds) entraîne un modèle de 175 milliards de paramètres. Hypothèses : état de $14\Psi$ octets, débit d'écriture agrégé de 50 Go/s, $R = 900$ s, MTBF du job de l'exercice 1 (14,4 h). (a) Donnez la taille du checkpoint et le coût $\delta$ d'une écriture synchrone, la période optimale et le goodput. (b) Même question si la partie bloquante se réduit à 1 s. (c) Quelles conditions faut-il vérifier avant de choisir (b) ? Utilisez `yd.py`.
:::

::: sol
(a) $14 \times 175 \times 10^9 = 2450$ Go. À 50 Go/s, $\delta = 49$ s. Le minimum exact du modèle (`yd.argmin_exact`) donne $\tau^{\ast} = 2223$ s (37 minutes) et un goodput de 94,1 %.

(b) Avec $\delta = 1$ s, $\tau^{\ast} = 322$ s (5,4 minutes) et un goodput de 97,7 % : 3,6 points de mieux, soit environ 1 770 GPU-heures par jour sur 2 048 GPU ($0{,}036 \times 49\,152$).

(c) Trois vérifications. La persistance de fond (49 s) doit tenir dans la période (322 s), c'est le cas : 15 %. Le débit nécessaire pour la faire tenir dans 20 % de la période est $2450/(0{,}2 \times 322) = 38$ Go/s, inférieur aux 50 Go/s supposés, mais il faut le partager avec la lecture des données d'entraînement. Enfin la mémoire d'hôte doit contenir le snapshot : 9,6 Go par nœud (1,2 Go par GPU), à ajouter à tout ce qui y réside déjà. La concurrence avec le trafic d'entraînement doit se mesurer (chapitre 4).
:::

::: exo
[Exercice 7 · ★★ — Raccourcir le délai de détection]{.tag} Sur 1 024 GPU (128 nœuds au taux de 6,5 pannes pour mille nœuds-jours), on suppose que 30 % des pannes sont des blocages, que le délai passe de 10 à 3 minutes, que $R = 900$ s et que $\tau = 455$ s. Un délai de 3 minutes peut tuer à tort un job sain. (a) Combien de GPU-heures par jour économise-t-on ? (b) Combien coûte une fausse alerte ? (c) Quel taux de fausses alertes rend l'opération neutre ? (d) Que décidez-vous ?
:::

::: sol
(a) $128 \times 0{,}0065 = 0{,}832$ pannes par jour, dont $0{,}2496$ blocages. Chacun économise 7 minutes sur 1 024 GPU : $1024 \times 7/60 = 119{,}5$ GPU-heures. Total : $0{,}2496 \times 119{,}5 = 29{,}8$ GPU-heures par jour.

(b) Une fausse alerte tue un job sain : il perd le redémarrage et, en moyenne, la moitié d'une période, soit $900 + 455/2 = 1127{,}5$ s, c'est-à-dire $1024 \times 1127{,}5/3600 = 320{,}7$ GPU-heures.

(c) Neutre quand $29{,}8 = 320{,}7 \times f$, soit $f = 0{,}093$ par jour : une fausse alerte tous les 10,8 jours.

(d) On ne raccourcit le délai que si l'on peut garantir moins d'une fausse alerte tous les 11 jours environ. Cela passe par la mesure de la plus longue phase silencieuse légitime (checkpoint, évaluation) et par des pulsations dans ces phases. Les 30 % de blocages sont une hypothèse : mesurez la vôtre.
:::

::: exo
[Exercice 8 · ★★ — Lire un journal du noyau]{.tag} Voici un extrait de `fixtures/kernel_log_sample.txt` (fixture synthétique, une seule ligne par Xid répété) :

~~~text
[Sat Oct 24 02:14:37 2026] NVRM: Xid (0000:3b:00): 63, Row remapping event
[Sat Oct 24 02:51:12 2026] NVRM: Xid (0000:5e:00): 13, Graphics Engine Exception
[Sat Oct 24 03:02:44 2026] NVRM: Xid (0000:3b:00): 48, An uncorrectable double bit error (DBE) has been detected
[Sat Oct 24 03:02:44 2026] NVRM: Xid (0000:3b:00): 154, GPU recovery action changed
[Sat Oct 24 03:02:45 2026] NVRM: Xid (0000:3b:00): 45, Ch 00000012, Preemptive removal
[Sat Oct 24 04:40:19 2026] NVRM: Xid (0000:86:00): 74, NVLink error
~~~

(a) Reconstituez l'histoire du GPU `3b:00`. (b) Sur quels GPU agissez-vous, et comment ? (c) Que faites-vous du job en cours ? (d) Que conservez-vous avant toute réinitialisation ?
:::

::: sol
(a) À 02 h 14, un événement de remappage (Xid 63, dont le catalogue indique `IGNORE` comme action immédiate) : la mémoire a commencé à se dégrader. À 03 h 02, une erreur ECC à double bit (Xid 48) ; les Xid 154 (changement d'action de récupération) et 45 (nettoyage préventif) en sont les échos. Le remappage prend effet à la prochaine réinitialisation du GPU.

(b) `3b:00` (ECC à double bit) et `86:00` (NVLink) justifient de drainer le nœud (niveau 2 de la politique du chapitre 7). `5e:00` n'a qu'une exception d'application (Xid 13, `RESTART_APP`) : seule, elle ne justifie pas de retirer le nœud.

(c) Si le job n'est pas déjà tombé, demander un checkpoint puis drainer (« vidange puis réinitialisation ») ; sinon le superviseur relance le job sur d'autres nœuds en excluant celui-ci. `python3 xid_triage.py fixtures/kernel_log_sample.txt` affiche le verdict `drain-node`.

(d) La sortie de `nvidia-bug-report.sh`, celle de `nvidia-smi -q`, le journal du noyau complet, l'identifiant du job et l'heure, avant tout `nvidia-smi -r` ou redémarrage qui effacerait l'état.
:::

::: exo
[Exercice 9 · ★★★ — Combien de nœuds de rechange ?]{.tag} Un cluster alloue 2 048 nœuds à un job. Les nœuds tombent en panne indépendamment au taux de 6,5 pannes pour mille nœuds-jours et une réparation prend 2 jours (hypothèse), sans limite de capacité de réparation. (a) Combien de nœuds sont en réparation en moyenne ? (b) Combien de rechanges garantissent, avec une probabilité d'au moins 99 %, de remplacer sans redimensionner ? (c) Que devient ce nombre si la réparation prend 5 jours ou 1 jour ? (d) Combien coûtent les rechanges inactives, et comment réduire ce coût ?

*Indice* : le nombre moyen de nœuds en réparation est le taux de panne multiplié par la durée de réparation (loi de Little) ; sans limite de capacité de réparation, ce nombre suit une loi de Poisson.
:::

::: sol
(a) Régime permanent d'une file sans limite de serveurs : le nombre de nœuds en réparation suit une loi de Poisson de moyenne $2048 \times 0{,}0065 \times 2 = 26{,}6$.

(b) Le plus petit $k$ tel que $P(X \le k) \ge 0{,}99$ est 39 (calculé avec `scipy.stats.poisson.ppf`) : $P(X > 39) = 0{,}0092$. Il faut donc 39 nœuds de rechange, soit 1,9 % de l'allocation.

(c) À 5 jours, la moyenne est de 66,6 et le seuil de 86 (4,2 %) ; à 1 jour, la moyenne est de 13,3 et le seuil de 22. Le besoin est proportionnel au temps de réparation : le raccourcir est aussi efficace que de réduire le taux de panne.

(d) 39 nœuds de 8 GPU inactifs représentent $39 \times 8 \times 24 = 7488$ GPU-heures par jour. On réduit ce coût en faisant tourner sur les rechanges des jobs **préemptibles** (QOS du module 5), au prix d'un délai de libération qui s'ajoute à $R$, ou en mutualisant les rechanges entre plusieurs jobs. Le modèle suppose des pannes indépendantes et ne couvre ni les pannes corrélées (un commutateur) ni la contrainte de taille de réplica de l'exemple 6.1.
:::

::: exo
[Exercice 10 · ★★★ — Une boucle de relance toute la nuit]{.tag} Dans ce scénario fictif, un job de 1 024 GPU a redémarré 28 fois entre 1 h et 6 h 30. Le superviseur indique, pour chaque tentative : un nœud différent, un échec 90 secondes après le lancement, et `step_before = step_after = 18000`. $R$ vaut 600 s. (a) Qu'est-ce qui, dans ces données, écarte une panne de nœud ? (b) Combien de GPU-heures ont été perdues ? (c) Quelle garde aurait limité les dégâts, et combien aurait-elle économisé ? (d) Quelle cause expliquerait ce comportement quand les empreintes du checkpoint sont correctes ? (e) Quels changements proposez-vous ?
:::

::: sol
(a) Vingt-huit nœuds différents échouent au même instant relatif et au même pas : ce n'est pas le matériel. L'absence de progrès (`step_after = step_before`) montre que le problème survient dès la reprise.

(b) Chaque tentative coûte $(90 + 600)\ \text{s} = 690$ s, soit $1024 \times 690/3600 = 196{,}3$ GPU-heures ; 28 tentatives font 5 495 GPU-heures.

(c) La garde « aucun progrès » (deux tentatives de suite sans avancer) aurait arrêté la boucle après 2 tentatives, soit 393 GPU-heures : 5 103 GPU-heures économisées, sans parler du cluster qui n'a pas été perturbé (cf. les 35 remises en file et 548 préemptions décrites par Kokolis et coauteurs).

(d) Une empreinte correcte prouve l'**intégrité** (ce qui a été lu est ce qui a été écrit), pas l'**exactitude** : le checkpoint du pas 18 000 peut contenir des valeurs non finies, écrites juste après une divergence, que la reprise fait échouer aussitôt (par exemple une garde « perte non finie »).

(e) Valider le contenu à l'écriture (perte et norme de gradient finies) et à la lecture ; conserver plusieurs checkpoints et un point « sain » marqué tous les $L$ pas ; revenir automatiquement au précédent après un échec sans progrès ; alerter un humain à la deuxième tentative ; ajouter l'entrée 5 du runbook du chapitre 8.
:::

::: exo
[Exercice 11 · ★★★ — Un plan de tests de chaos]{.tag} Concevez la journée d'exercice d'un job de 1 024 GPU (128 nœuds) avec $\tau = 455$ s et $R = 900$ s visé. Listez six expériences, chacune avec son injection, son hypothèse **chiffrée**, ses critères d'arrêt, et la métrique de sortie. Précisez le périmètre et le rôle de chacun.
:::

::: sol
Une réponse défendable (les seuils découlent de l'exemple 8.1 et sont à recalibrer sur vos mesures) :

| Expérience | Hypothèse chiffrée |
|---|---|
| 1. `kill -9` d'un rang | reprise automatique en 1 535 s au plus (180 s de détection, 900 s de relance, 455 s de recalcul) ; état final sans écart |
| 2. `kill -STOP` d'un rang | blocage détecté en 180 s au plus, groupe de processus détruit, même budget total |
| 3. checkpoint le plus récent abîmé | repli sur le précédent ; perte au plus deux périodes (910 s) en plus de $R$ |
| 4. nœud auto-déclaré défectueux (code 42) | exclu à la première occurrence, aucune relance sur ce nœud ensuite |
| 5. stockage ralenti d'un facteur 5 | au plus une persistance en vol, aucun empilement de mémoire d'hôte, goodput mesuré |
| 6. échec partout au pas 0 (bogue) | arrêt après 2 tentatives sans progrès, alerte émise, aucune intervention nécessaire avant |

**Périmètre** : une allocation de test ou un job de 64 GPU, jamais la production. **Critères d'arrêt** : toute expérience dépassant trois fois son budget est interrompue par l'animateur. **Rôles** : un injecteur, un observateur du journal, un décideur qui peut arrêter. **Sortie** : le temps de reprise mesuré par phase, les GPU-heures perdues, et pour chaque écart une action de suivi vérifiable.

Une bonne réponse comporte : des hypothèses mesurables et pas seulement « le système se rétablit », un périmètre contenu, des critères d'arrêt, une métrique en GPU-heures, et le lien avec un runbook ou un test automatisé.
:::

::: exo
[Exercice 12 · ★ — Le `torch.save` de la veille]{.tag} Un script appelle `torch.save(state, "ckpt.pt")` toutes les dix minutes. Citez quatre défauts, puis écrivez une fonction `save_atomic(state, path)` qui en corrige deux. Que reste-t-il à corriger ?
:::

::: sol
**Défauts.** (1) L'écriture n'est pas atomique : une coupure laisse un fichier tronqué sous le nom final. (2) Le précédent checkpoint est écrasé : aucun repli possible. (3) Aucun `fsync` : le noyau peut avoir accepté l'écriture sans qu'elle soit durable. (4) Aucune empreinte : un fichier abîmé est chargé sans alerte. (5) Souvent, l'état est incomplet (optimiseur, générateurs aléatoires, curseur de données).

**Correction partielle** (exécutée dans le bac à sable : après deux sauvegardes successives, le répertoire ne contient que `ckpt.pt`, sans résidu `.tmp`) :

~~~python
import os
import torch

def save_atomic(state, path):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        torch.save(state, f)
        f.flush()
        os.fsync(f.fileno())          # data durable before the rename
    os.replace(tmp, path)             # atomic on the same file system
    fd = os.open(os.path.dirname(path) or ".", os.O_RDONLY)
    try:
        os.fsync(fd)                  # the rename itself durable
    finally:
        os.close(fd)
~~~

Cette version corrige (1) et (3). Il reste (2) et (4), et la complétude (5) : passez à un répertoire par pas avec manifeste d'empreintes et rotation, comme `ckpt.py` du lab 10.2.
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux chiffrer le coût des pannes d'un job.** Preuve : un tableau MTBF, période de Young et goodput pour un job de votre choix, avec les hypothèses étiquetées (exemples 1.1 et 2.1).
-   **Je peux écrire un checkpoint atomique, complet et vérifié.** Preuve : le lab 10.2 et un test qui échoue quand on retire le manifeste ou le `fsync`.
-   **Je peux prouver qu'une reprise est exacte.** Preuve : la sortie de `ablate.py` et de `chaos.py` appliqués à votre propre entraîneur.
-   **Je peux concevoir une boucle de reprise qui ne boucle pas.** Preuve : le lab 10.3, `starter` complété, et un journal où le superviseur exclut un nœud, puis un autre où il abandonne.
-   **Je peux régler un délai de détection avec des chiffres.** Preuve : l'exercice 7 refait avec vos taux de panne et votre plus longue phase silencieuse.
-   **Je peux lire un journal d'erreurs GPU et décider.** Preuve : les exercices 8 et 10 refaits sur un journal réel anonymisé.
-   **Je peux dimensionner les rechanges.** Preuve : l'exercice 9 avec votre temps de réparation.
-   **Je peux préparer un test de chaos et un post-mortem.** Preuve : le plan de l'exercice 11 et un post-mortem chiffré en GPU-heures.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Un job de 4 000 GPU perd un quart de son temps à cause des pannes. Que faites-vous ?* Réponse-type : décomposer d'abord la perte (détection, relance, recalcul, écriture de checkpoint, via l'ETTR) ; si le recalcul domine, des checkpoints plus fréquents et non bloquants ; si la relance domine, raccourcir $R$ (nœuds de rechange, délai de remise en file, temps de chargement) ; si la détection domine, des pulsations et des délais mesurés ; chercher les nœuds qui reviennent et les boucles ; chiffrer chaque levier en GPU-heures avant de choisir.
2.  *Comment savez-vous que votre reprise est correcte ?* Réponse-type : une reprise identique au bit près sur un cas de test CPU (pertes et état final), un état complet (optimiseur, générateurs, curseur), des empreintes vérifiées, un critère d'équivalence statistique fixé à l'avance pour la production, et des tests de chaos réguliers, pas un seul essai heureux.
3.  *Un job redémarre en boucle depuis deux heures. Que faites-vous ?* Réponse-type : arrêter la boucle (garde « aucun progrès »), lire le journal du superviseur : mêmes nœuds ou non, même pas ou non ; même échec partout veut dire code ou checkpoint, pas matériel ; vérifier le contenu du dernier checkpoint, revenir à un plus ancien, escalader, puis corriger la garde manquante.

## Lectures et références {#refs}

-   Dubey et al. (2024). [*The Llama 3 Herd of Models*](https://arxiv.org/abs/2407.21783), section 3.3.4 et tableau 5 : 466 interruptions en 54 jours et leurs causes (chapitres 1, 4, 5).
-   Kokolis et al. (2024). [*Revisiting Reliability in Large-Scale Machine Learning Research Clusters*](https://arxiv.org/abs/2410.21680) : taux de panne, MTTF, ETTR et formule de l'ETTR attendu (chapitres 1, 2, 5, 6).
-   Hu et al. (2024). [*Characterization of Large Language Model Development in the Datacenter*](https://arxiv.org/abs/2403.07648), sections 5 et 6.1 : pannes d'un datacenter de LLM, checkpoint asynchrone, thermique (chapitres 1, 4, 7).
-   Jiang et al. (2024). [*MegaScale*](https://arxiv.org/abs/2402.15627), sections 4 et 6.3 : pulsations, diagnostic, checkpoint en deux étapes (chapitres 4, 5).
-   Mohan, Phanishayee, Chidambaram (2021). [*CheckFreq: Frequent, Fine-Grained DNN Checkpointing*](https://www.usenix.org/conference/fast21/presentation/mohan), FAST : checkpoint en deux phases et curseur de données (chapitres 3, 4).
-   Wang et al. (2023). [*Gemini: Fast Failure Recovery in Distributed Training with In-Memory Checkpoints*](https://www.cs.rice.edu/~eugeneng/papers/SOSP23.pdf), SOSP : checkpoints en mémoire CPU (chapitre 4).
-   Young (1974), [*A first order approximation to the optimum checkpoint interval*](https://doi.org/10.1145/361147.361115), CACM ; Daly (2006), [*A higher order estimate of the optimum checkpoint interval for restart dumps*](https://doi.org/10.1016/j.future.2004.11.016), FGCS : les formules du chapitre 2 (accès payant).
-   PyTorch. [*Distributed Checkpoint (DCP)*](https://docs.pytorch.org/docs/2.14/distributed.checkpoint.html) : sauvegarde parallèle, redécoupage à la lecture, `async_save` (chapitres 3, 4).
-   PyTorch. [*torchrun (Elastic Launch)*](https://docs.pytorch.org/docs/2.14/elastic/run.html) : modes de panne, `--max-restarts`, `--nnodes=min:max` (chapitre 6).
-   NVIDIA. [*Xid Errors*](https://docs.nvidia.com/deploy/xid-errors/latest/index.html) : lecture des messages et catalogue des Xid (chapitre 7).
-   NVIDIA. [*GPU Memory Error Management*](https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/latest/index.html) : confinement, remappage de lignes, drapeaux de récupération (chapitre 7).
-   SchedMD. [*sbatch*](https://slurm.schedmd.com/sbatch.html) : `--requeue`, `--signal`, `--no-kill`, `SLURM_RESTART_COUNT` (chapitre 6).
-   Kubernetes. [*Jobs*](https://kubernetes.io/docs/concepts/workloads/controllers/job/) : `backoffLimit`, délai exponentiel, pod failure policy (chapitre 6).
-   Principles of Chaos Engineering. [*principlesofchaos.org*](https://principlesofchaos.org/) : état stable, hypothèse, événements réels (chapitre 8).
-   Google. [*Site Reliability Engineering, chapitre « Postmortem Culture »*](https://sre.google/sre-book/postmortem-culture/) : post-mortems sans blâme (chapitre 8).

## Sources et portée {#sources}

### Documenté {#documente}

Les chiffres de Llama 3 (466, 47, 419 interruptions, tableau 5, « plus de 90 % », trois interventions), de Kokolis et coauteurs (6,50 et 2,34 pannes pour mille nœuds-jours, projections de 1,8 h et 0,23 h, formule de l'ETTR, 0,7 et 0,93, 548 préemptions pour 35 remises en file), d'Acme (11 % et 82 %, thermique, checkpoint asynchrone), d'OPT-175B et de BLOOM ont été lus le 24 octobre 2026 dans le texte des articles. Les faits sur CheckFreq, Gemini (résumé et première page) et MegaScale (sections 4 et 6.3) viennent des articles ; les métadonnées de Young et de Daly ont été vérifiées auprès de Crossref. Les comportements de DCP et de `torchrun` viennent de la documentation de PyTorch 2.14 ; les valeurs par défaut des délais ont aussi été relues dans le code de PyTorch 2.14.1. Le catalogue des Xid (mis à jour le 9 septembre 2026), la gestion des erreurs mémoire, `NCCL_IB_TIMEOUT`, `sbatch`, les Jobs Kubernetes, les principes du chaos et le chapitre « Postmortem Culture » ont été relus sur leurs pages officielles. Les sorties « réelles » viennent du bac à sable (Linux 6.18, 4 vCPU, sans GPU, PyTorch 2.14.1 CPU, Slurm 23.11.4), et tous les calculs « faits ici » ont été refaits en Python.

### Recommandé {#recommande}

Les niveaux de triage Xid (surveiller, relancer, drainer), la règle « le délai de détection est plus long que la plus longue phase silencieuse », la garde « aucun progrès », l'exclusion après deux échecs, les cinq règles du checkpoint asynchrone, le modèle à deux niveaux du premier ordre (dérivé ici, vérifié par minimisation numérique), le calcul de rechanges par la loi de Poisson, la distinction reprise identique et reprise équivalente, le budget de temps d'une expérience de chaos : ce sont des choix de ce parcours, pas des règles de PyTorch, de NVIDIA, de Slurm ou de Kubernetes.

### À vérifier {#a-verifier}

(1) La formule d'ordre supérieur de Daly n'a pas été relue dans l'article (accès payant) ; elle est vérifiée numériquement contre le modèle exact. (2) Le tableau 5 de Llama 3 est incohérent dans le texte récupéré (148 sur 419 ne fait pas 30,1 %, et 268 sur 419 ne fait pas 58,7 %) : nous citons les comptes, pas les pourcentages. (3) Le texte de Kokolis et coauteurs cite un MTTF de 7,9 h pour des jobs de 1 024 GPU ; avec le taux de 6,50 pour mille nœuds-jours, nous obtenons 28,8 h : nous n'avons pas pu réconcilier les deux et n'utilisons que les projections à 16 384 et 131 072 GPU, que nous reproduisons. (4) Le délai de 121 secondes avant éligibilité d'un job remis en file a été observé sur Slurm 23.11.4 par défaut ; nous n'avons pas identifié le paramètre en cause. (5) Les libellés d'action du catalogue Xid (`RESTART_APP`, `RESET_GPU`, `RESTART_BM`, `WORKFLOW_*`) ne sont pas définis dans la page lue ; les Xid et leurs libellés évoluent avec les pilotes, relisez le catalogue de votre version. (6) Le comportement par défaut de `dedup_replicated_tensors` et la signature de `async_save` changent selon la version de PyTorch : seul `save`/`load` a été exécuté. (7) Les injections de pannes réseau, GPU (DCGM) et de nœud lent du chapitre 8 n'ont pas été testées. (8) Les garanties de cohérence d'un stockage objet pour le motif « manifeste en dernier » dépendent du fournisseur. (9) Les scripts `train.sbatch` et `job.yaml` sont linté, pas exécutés, faute de GPU et de cluster.

### Hors périmètre {#hors-perimetre}

Les bibliothèques de checkpoint multiniveau d'autres écosystèmes, le checkpoint/restauration au niveau du pilote GPU, les accélérateurs non NVIDIA, les stratégies de redimensionnement élastique qui préservent le lot global et la reproductibilité, l'orchestration de gang sous Kubernetes (JobSet et similaires), la détection matérielle de la corruption silencieuse, la résilience de l'inférence servie, et le dimensionnement financier des rechanges (module 15).
