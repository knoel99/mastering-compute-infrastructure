---
title: "Flotte multi-fournisseurs : SkyPilot, GPU clouds, hyperscalers et centres HPC"
subtitle: "Module 13 · Phase 4 · 28 h"
description: "Placer, déborder et basculer des charges GPU entre fournisseurs sans réécrire les jobs : modèles de capacité, abstraction du fournisseur, gravité des données, préemption, réseau, identité, centres publics et gouvernance."
module:
  id: multi-cloud
  number: 13
  phase: 4
  hours: 28
  level: 3
prerequisites: [kubernetes-gpu, fault-tolerance]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs : 2 sur 3 vérifiés dans un bac à sable ; la branche cloud du lab 13.2 n'est pas exécutée", class: unverified}
labs:
  - {id: cost-aware-placement, kind: sandbox}
  - {id: skypilot-yaml, kind: cluster}
  - {id: egress-cost, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** votre équipe a besoin de 256 GPU pendant six semaines, aucun fournisseur n'en a autant de libres aujourd'hui au prix visé, et votre jeu de données de 60 To vit chez l'un d'eux. Où lancez-vous le job, que faites-vous quand on vous le reprend, et combien coûte réellement le déménagement ?

Ce module donne le vocabulaire et les calculs pour y répondre. Il couvre l'offre (les *hyperscalers*, très grands clouds publics ; les *GPU clouds*, fournisseurs spécialisés dans les GPU ; les centres publics), les modèles de capacité, les outils qui abstraient le fournisseur, la gravité des données, le placement avec préemption, le réseau et l'identité, l'accès aux centres nationaux et la gouvernance. Un simulateur de placement et un calculateur de coût de déménagement sont exécutés dans un bac à sable ; un lab de job SkyPilot est analysé hors ligne mais **jamais lancé sur un vrai cloud**.

::: key
[Règle de ce module]{.tag} Un job se place entier, sur un seul site. Ce qui voyage entre fournisseurs, ce sont des jobs, des checkpoints et des jeux de données, jamais le trafic d'un all-reduce. Le coût de ce voyage, en argent et en temps, fait partie de la décision de placement.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 28 h, dont 12 h de lecture, 9,5 h de labs et 6,5 h d'exercices (répartition estimée par l'auteur, non mesurée) |
| Niveau d'entrée | 3 : Kubernetes pour les GPU et la tolérance aux pannes sont acquis |
| Prérequis | [Module 12 — Kubernetes pour les GPU](../kubernetes-gpu/index.html), [Module 10 — Tolérance aux pannes](../fault-tolerance/index.html) |
| Pour qui | Cœur : la plateforme de calcul d'une organisation est presque toujours répartie entre plusieurs fournisseurs. |
| Livrable | un simulateur de placement testé, un calculateur de coût de déménagement de données testé, un job SkyPilot analysé hors ligne avec sa politique de gouvernance |
| Environnement | un portable CPU suffit pour les labs 13.1 et 13.3 et pour la branche hors ligne du lab 13.2. La branche cloud du lab 13.2 demande un compte cloud et du crédit : lancez de petits jobs de quelques minutes et vérifiez l'arrêt automatique |
| Projets liés | [Projet 4 — Placement multi-fournisseurs](../../projects/multi-provider-scheduler/index.html), [Projet 6 — RFC de plateforme](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Situer une offre de calcul (hyperscaler, GPU cloud, centre public, colocation) par ce qu'elle vend, son unité de facturation, son engagement et son réseau (chapitres 1 et 2).
-   Calculer le prix d'une heure de GPU **utile** sur une offre préemptible et dire à partir de quelle remise elle bat le prix à la demande (chapitre 2).
-   Lire un job SkyPilot, dire ce que l'outil garantit et ce qu'il ne vérifie pas, et le soumettre à une politique de gouvernance (chapitres 3 et 8).
-   Chiffrer un déménagement de données : sortie par tranches, stockage pendant le chevauchement, temps de copie, point d'équilibre (chapitre 4).
-   Décider si une bascule de fournisseur après une préemption vaut son coût de transfert, avec des chiffres (chapitre 5).
-   Expliquer pourquoi un entraînement ne se coupe pas entre fournisseurs et dimensionner quotas et identités (chapitre 6).
-   Choisir une voie d'accès à un centre national ou européen et convertir une demande d'heures GPU (chapitre 7).
-   Mettre en place inventaire, étiquetage et nettoyage automatique (chapitre 8).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 4 — Plateforme cloud-native et multi-fournisseurs** (semaines 32-41) : placer, observer et facturer des charges sur plusieurs fournisseurs.
-   **S'appuie sur** : [module 12 — Kubernetes pour l'IA : GPU, files d'attente et gang scheduling](../kubernetes-gpu/index.html), [module 10 — Pannes, checkpointing et reprise automatique](../fault-tolerance/index.html).
-   **Projets qui s'en servent** : [Projet 4 — Placement multi-fournisseurs sensible aux coûts](../../projects/multi-provider-scheduler/index.html), [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html).
<!-- /gen:place -->

### Plan de séances {#seances}

Dix séances, soit 28 h : sept de 3 h, deux de 2,5 h et une de 2 h. Le niveau 2 correspond aux méthodes de cœur, le niveau 3 à l'avancé ; il ne diminue jamais. Les durées de chaque séance additionnent exactement celles de ses chapitres, de ses parties de lab et de ses exercices.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 2.5 h | 2 | ch. 1 Le paysage de l'offre GPU (2,25 h, avec les questions de positionnement) | Ex. 3 (0,25 h) |
| 2 | 2 h | 2 | ch. 2 Modèles de capacité (1,5 h) | Ex. 4 (0,5 h) |
| 3 | 3 h | 2 | ch. 3 Abstraire le fournisseur (1,5 h) | Lab 13.2 partie A : lint, politique, analyse hors ligne (1,5 h) |
| 4 | 3 h | 2 | ch. 4 Données et gravité (1,75 h) | Lab 13.3 partie A : carte tarifaire et scénarios (1 h) ; Ex. 1 (0,25 h) |
| 5 | 3 h | 3 | ch. 5 §5.1 et §5.2 : objectifs et politiques de placement (0,5 h) | Lab 13.3 partie B : écrire le calculateur (2 h) ; Ex. 7 (0,5 h) |
| 6 | 3 h | 3 | ch. 5 §5.3 à §5.7 (1 h) ; ch. 6 Réseau et identité (1 h) | Lab 13.1 partie A : formules et moteur (1 h) |
| 7 | 3 h | 3 | Séance de lab | Lab 13.1 partie B : politiques, balayage, critère (3 h) |
| 8 | 3 h | 3 | ch. 7 Centres publics (1,5 h) | Ex. 6, 9, 10, 5 (1,5 h) |
| 9 | 3 h | 3 | ch. 8 Gouvernance (1 h) | Lab 13.2 partie B : résidence et jobs étendus (1 h) ; Ex. 11 (1 h) |
| 10 | 2.5 h | 3 | Synthèse et checkpoint de sortie | Ex. 8, 12, 2 (2,5 h) |

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

**À ne pas survoler.** La comparaison chiffrée d'offres de capacité et la reprise d'un job d'un fournisseur à l'autre servent au projet 4.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le checkpoint de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si elles vous semblent routinières, parcourez les exercices ★★★ et passez au module suivant.

1.  **Perdre un job.** Un job préemptible subit en moyenne 0,15 interruption par heure d'allocation. Un checkpoint prend 3 minutes et une reprise 10 minutes. Quelle période de checkpoint minimise le gaspillage, et quelle part du temps alloué est perdue ?

2.  **Déménager un jeu de données.** Vous déplacez 2 To d'un fournisseur A vers un fournisseur B. La sortie est facturée 0,09 USD par Go (sans franchise) et le lien soutient 10 Gbit/s à 80 % d'efficacité. Combien cela coûte-t-il en sortie et combien de temps dure la copie ?

3.  **Couper un entraînement.** Pourquoi ne répartit-on pas un entraînement de 64 GPU entre deux fournisseurs pour profiter de la capacité de chacun ?

::: sol
**Réponses.**

1.  Avec les formules du module 10, rappelées au chapitre 2, $M = 1/0{,}15 = 6{,}67$ h, $C = 0{,}05$ h et $R = 0{,}167$ h. La période optimale vaut $T^* = \sqrt{2CM} = 0{,}816$ h, soit 49 minutes. Le gaspillage vaut $W = C/T^* + (T^*/2 + R)/M = 14{,}7\ \%$ du temps alloué.

2.  2 000 Go à 0,09 USD font **180 USD**. La copie dure $2000 \times 8 / (10 \times 0{,}8) = 2000$ s, soit 33 minutes. Le calcul complet, avec tranches et franchise, est l'objet du chapitre 4.

3.  À chaque étape, les gradients sont échangés. Entre deux sites, le lien est une liaison longue distance de quelques Gbit/s, contre des centaines de Go/s dans un nœud. Le chapitre 6 chiffre l'écart : environ 20 fois plus de temps de communication pour un modèle de 7 milliards de paramètres.
:::

## 1. Le paysage de l'offre GPU {#ch1}

Ce chapitre fournit une grille de lecture, pas un annuaire. Les offres changent plus vite que ce cours : retenez les questions qui classent un fournisseur, et datez chaque réponse.

### 1.1. Quatre questions qui classent une offre

Toute offre de calcul GPU, quel que soit son nom commercial, se décrit par quatre réponses.

-   **Qui exploite le matériel ?** Un fournisseur public vous loue des machines ; un centre national vous alloue des heures ; vous exploitez vous-même un parc en colocation.
-   **Quelle est l'unité vendue ?** L'instance à l'heure, le nœud réservé pour des jours, un volume d'heures GPU attribué par un comité, ou une baie et sa puissance électrique.
-   **Quel engagement ?** Aucun, quelques semaines, un à trois ans, ou une durée de projet.
-   **Quel environnement autour du GPU ?** Interconnexion entre nœuds, stockage, réseau vers l'extérieur, identité, quotas.

La quatrième question est celle qu'on oublie. Un GPU identique ne donne pas le même entraînement derrière un réseau différent : le chapitre 3 y revient.

### 1.2. Les familles d'offre

Le tableau classe cinq familles. Il décrit des tendances à vérifier pour chaque fournisseur, pas des propriétés garanties.

| Famille | Ce qu'on achète | Unité et engagement typiques | Atout | Piège |
|---|---|---|---|---|
| Hyperscalers | instances et services gérés, régions mondiales | à la seconde ou à l'heure ; engagements d'usage de 1 à 3 ans ; réservations ciblées | écosystème complet, quotas et identités matures | capacité GPU parfois rare, sorties de données facturées |
| GPU clouds spécialisés | nœuds GPU, souvent avec réseau InfiniBand, parfois Kubernetes ou Slurm gérés | location à l'heure ou contrat de capacité de plusieurs mois | accès à du matériel récent, réseau pensé pour l'entraînement | services périphériques plus limités, contrats à lire (module 15) |
| Offres européennes | variantes des deux précédentes, avec une juridiction et des lieux européens | comme ci-dessus | résidence des données, cadre juridique européen | catalogue plus étroit, à vérifier fournisseur par fournisseur |
| Centres nationaux et européens | heures GPU attribuées sur dossier, via Slurm | allocation par projet, de quelques mois à un an | pas de facture à l'heure, matériel de recherche de pointe | files d'attente, règles d'accès, publication attendue (chapitre 7) |
| Colocation et parc propre | vos nœuds dans le centre de données d'un tiers | achat ou bail de plusieurs années | coût marginal bas à forte occupation, contrôle total | délai de livraison, exploitation à votre charge (module 15) |

Pour la famille « offres européennes », ce cours ne nomme pas de fournisseur : la liste, les lieux et les tarifs sont des informations datées. Elles relèvent de votre veille et de la section « À vérifier ».

### 1.3. Le réseau d'un nœud dépend du fournisseur

La page de référence du YAML de SkyPilot, lue le 24 octobre 2026, décrit l'option `network_tier: best` fournisseur par fournisseur. Chez AWS, elle active l'Elastic Fabric Adapter (EFA). Chez Google Cloud, elle active GPUDirect-TCPX, TCPXO ou RDMA selon la famille de machines. Chez Nebius, CoreWeave et Together AI, elle active InfiniBand ; sur les clusters Oracle OKE à serveurs nus, elle active RoCEv2.

Un même `torchrun` avec NCCL ne se comporte donc pas pareil d'une offre à l'autre. Les variables d'environnement, les images et les pilotes diffèrent. Le module 7 détaille NCCL ; ici, retenez que « indépendant du fournisseur » décrit le job, jamais la performance qu'il obtiendra.

### 1.4. Les centres publics, une famille à part

Un centre national ne vend pas des heures de GPU : il attribue des heures à un projet scientifique. Le Jean Zay de l'IDRIS, en France, en fournit un exemple documenté. Sa page matérielle, lue le 24 octobre 2026, liste une partition de 364 nœuds à quatre GPU NVIDIA H100 SXM5 80 Go et une partition de 52 nœuds à huit GPU A100 SXM4 80 Go. Les nœuds de l'extension Bull BullSequana XH3000 sont reliés en InfiniBand, les anciens nœuds en Omni-Path.

La demande d'heures passe par le portail eDARI de GENCI, qui exprime les seuils en heures de GPU V100 et donne les équivalences suivantes : 1 GPU H100 vaut 2 GPU A100 ou 4 GPU V100.

::: ex
[Exemple 1.1 — Que pèse un seuil d'allocation ?]{.tag} Le portail eDARI fixe à 50 kh GPU V100 (50 000 heures) le seuil entre allocation dynamique et allocation régulière. Convertissons-le en H100 puis en durée de calcul.

La partition H100 compte $364 \times 4 = 1456$ GPU, soit 5 824 équivalents V100. Le seuil de 50 000 h V100 équivaut à $50\,000 / 4 = 12\,500$ h H100. C'est 8,6 h de l'ensemble de la partition H100, ou 1 562 h (65 jours) pour un job de 8 GPU H100.

Un entraînement de 8 GPU H100 pendant moins de 65 jours reste donc sous le seuil de l'allocation dynamique, d'après les chiffres lus le 24 octobre 2026. Le chapitre 7 reprend cette conversion pour une demande réelle.
:::

### 1.5. Une fiche par fournisseur

Pour comparer, remplissez la même fiche pour chaque candidat et datez-la. Douze lignes suffisent pour commencer.

| Ligne | Question |
|---|---|
| Lieux | Quelles régions et quelles juridictions ? |
| Matériel | Quels GPU, combien par nœud, quelle mémoire ? |
| Interconnexion | EFA, InfiniBand, RoCE, Ethernet ? Quelle bande passante par nœud ? |
| Stockage | Système de fichiers parallèle, objet, local ? À quel débit ? |
| Modèle de capacité | À la demande, réservé, préemptible, contrat ? |
| Préavis de préemption | Combien de secondes, garanti ou au mieux ? |
| Quotas | Dans quelle unité, par quoi limités, en combien de jours obtenus ? |
| Sortie de données | Tarif par Go, franchise, exceptions ? |
| Identité | Fédération OIDC (*OpenID Connect* : jetons d'identité signés), clés longues, rôles ? |
| Support et SLA | Quel délai, quel crédit en cas de panne (SLA : engagement de niveau de service) ? |
| Conformité | Certifications, résidence, sous-traitants ? |
| Sortie du contrat | Préavis, frais, export des données ? |

::: recap
Points clés — chapitre 1

-   Quatre questions classent une offre : qui exploite, quelle unité, quel engagement, quel environnement.
-   Cinq familles : hyperscalers, GPU clouds, offres européennes, centres publics, colocation. Les tendances ne remplacent pas la fiche datée de chaque fournisseur.
-   Le réseau d'un nœud (EFA, GPUDirect, InfiniBand, RoCE) diffère selon le fournisseur : le job est portable, sa performance ne l'est pas.
-   Un centre public attribue des heures sur dossier ; il les exprime dans une unité de référence (ici le GPU V100) qu'on sait convertir.
-   Une fiche de douze lignes, datée et sourcée, rend deux offres comparables.
:::

## 2. Modèles de capacité {#ch2}

Un même GPU se vend de six manières. Ce chapitre les classe par ce qu'elles garantissent et par ce qu'elles coûtent réellement, une fois comptée la perte de travail.

### 2.1. Six modèles

La [documentation d'AWS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-purchasing-options.html) énumère, parmi ses options d'achat d'instances, la [facturation à la seconde](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-on-demand-instances.html) à la demande, les [Savings Plans](https://docs.aws.amazon.com/savingsplans/latest/userguide/what-is-savings-plans.html) (engagement d'un montant horaire pendant un à trois ans), les Reserved Instances (engagement sur une configuration), les Spot Instances et les Capacity Reservations. Les Capacity Blocks for ML s'y ajoutent pour réserver un groupe d'instances GPU sur une date future. Google Cloud distingue, sur la page de ses modèles de provisionnement, quatre modèles : standard (celui par défaut), Spot, Flex-start et lié à une réservation.

Les noms varient, la structure se retrouve partout.

| Modèle | Ce qu'il garantit | Ce qu'il ne garantit pas | Fait documenté |
|---|---|---|---|
| À la demande | une instance, payée à l'usage | qu'il y ait de la capacité au moment de la demande | facturation à la seconde chez AWS |
| Engagement d'usage | un prix réduit contre un volume sur 1 à 3 ans | de la capacité disponible | Savings Plans : montant horaire engagé |
| Réservation planifiée | de la capacité à une date et pour une durée | une annulation, un changement de date | Capacity Blocks AWS : départ jusqu'à 8 semaines à l'avance, annulation interdite |
| Capacité à attente (*flex-start*) | de la capacité obtenue après une attente | un délai | Flex-start Google : exécution ininterrompue jusqu'à 7 jours ([source](https://cloud.google.com/compute/docs/instances/about-flex-start-vms)) |
| Préemptible (*spot*) | un prix bas | de rester en vie | préavis : 2 min (AWS), 0 s par défaut (Google), 30 s au mieux (Azure) |
| Contrat de capacité | des nœuds sur des mois ou des années | une flexibilité de sortie | à lire clause par clause (module 15) |

Les Capacity Blocks d'AWS illustrent la réservation planifiée. La documentation indique qu'un bloc réserve jusqu'à 64 instances, avec 256 instances au plus au total, que les annulations ne sont pas permises, que le prix dépend de l'offre et de la demande au moment de l'achat et qu'il est facturé d'avance (page [tarification et facturation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/capacity-blocks-pricing-billing.html)).

### 2.2. Le préavis de préemption

Une préemption ne prévient pas toujours, et jamais longtemps. Les trois grands fournisseurs documentent des préavis très différents.

AWS émet un avertissement deux minutes avant l'interruption d'une instance Spot, « au mieux » (*best effort*). Azure tente de livrer l'événement planifié jusqu'à 30 secondes avant l'éviction. Google Cloud, dont le préavis de préemption vaut 0 seconde par défaut, laisse une période d'arrêt au mieux de 30 secondes au plus pour une VM Spot ; un préavis de 120 secondes se configure à la création.

::: war
[Préavis nul par défaut chez Google Cloud]{.tag} La documentation des VM Spot de Google Cloud indique que, si la durée du préavis n'est pas précisée ou vaut 0, il n'y a aucun délai dédié entre la détection de la préemption dans les métadonnées et le début de l'arrêt, et que la période d'arrêt est « au mieux » et d'au plus 30 secondes. Elle recommande 120 secondes pour toute charge qui a besoin de plus de 30 secondes. Source : [Spot VMs](https://cloud.google.com/compute/docs/instances/spot), lu le 24 octobre 2026.
:::

::: ex
[Exemple 2.1 — Le préavis ne suffit jamais à sauvegarder]{.tag} Un modèle de 7 milliards de paramètres occupe environ 16 octets par paramètre en entraînement mixte avec Adam (règle de [ZeRO](https://arxiv.org/abs/1910.02054), module 2), soit $7 \cdot 10^9 \times 16 = 112$ Go d'états.

Pour tout écrire dans un préavis de 30 s, il faut soutenir $112/30 = 3{,}7$ Go/s ; dans 120 s, $112/120 = 0{,}93$ Go/s, et seulement si tous les rangs écrivent en parallèle vers un stockage qui suit.

Le préavis sert donc à **vider proprement** (terminer l'étape, signaler la fin), pas à remplacer le checkpoint périodique. C'est ce que montre la répétition du lab 13.2 : un arrêt sans préavis perd les 12 étapes écoulées depuis le dernier checkpoint, un arrêt avec préavis traité par le job n'en perd aucune, et seul le premier cas est garanti partout.
:::

### 2.3. Le coût d'une heure utile

Une heure payée sur une offre préemptible n'est pas une heure de travail. Le module 10 établit la période de checkpoint optimale au premier ordre, avec $C$ le coût d'un checkpoint, $M$ le temps moyen entre interruptions et $R$ le temps de reprise :

$$T^* = \sqrt{2CM}, \qquad W(T) = \frac{C}{T} + \frac{T/2 + R}{M}$$

La fraction $W$ est la part du temps alloué qui ne produit pas de progrès. Au point optimal elle se simplifie en $W(T^*) = \sqrt{2C/M} + R/M$. Le prix d'une heure **utile** est alors le prix catalogue divisé par $1 - W$ :

$$p_{\text{utile}} = \frac{p}{1 - W(T^*)}$$

L'offre préemptible bat l'offre à la demande tant que $p_{\text{spot}} / (1 - W) < p_{\text{demande}}$. La remise minimale vaut donc exactement $W$.

::: ex
[Exemple 2.2 — La remise qui rembourse les interruptions]{.tag} Prenons un taux de 0,15 interruption par heure ($M = 6{,}67$ h), un checkpoint de 3 minutes ($C = 0{,}05$ h) et une reprise de 10 minutes ($R = 0{,}167$ h). Alors $T^* = 0{,}8165$ h, soit 49,0 minutes, et $W = 0{,}1225 + 0{,}0250 = 0{,}1475$.

Le spot bat l'offre à la demande dès que sa remise dépasse **14,7 %**. À 4,0 unités contre 10,0 à la demande, la remise est de 60 % et le prix de l'heure utile vaut $4{,}0 / (1 - 0{,}1475) = 4{,}69$ unités.

Ces taux d'interruption sont des hypothèses de l'exemple. Mesurez les vôtres sur au moins quelques semaines : ils changent selon la région, l'heure et le type d'instance.
:::

### 2.4. Capacité garantie et capacité bon marché

La réservation planifiée et la capacité à attente répondent à un autre problème que le spot : obtenir des GPU **à une date**, pour un entraînement qu'on ne peut pas faire attendre. On paie alors la garantie par un engagement de durée, un paiement anticipé ou un délai. Les deux ne sont pas exclusives : une flotte combine souvent une base réservée, une couche à la demande pour les pics et du préemptible pour les travaux qui savent reprendre.

Le module 15 donne le modèle de coût total qui tranche entre ces mélanges, ainsi que la lecture des contrats de capacité. Retenez ici le critère opérationnel : **un job qui ne sait pas reprendre n'a pas sa place sur du préemptible**, quelle que soit la remise.

### 2.5. Choisir un modèle par charge

| Charge | Modèle raisonnable | Condition |
|---|---|---|
| Expériences courtes, jobs réparables | préemptible avec reprise automatique | checkpoint périodique, stockage qui survit à la VM |
| Entraînement long sur date ferme | réservation planifiée ou contrat de capacité | budget engagé, plan B si le bloc est annulé par le fournisseur |
| Pics imprévus | à la demande | plafond de coût, quotas suffisants |
| Base permanente | engagement d'usage ou parc propre | taux d'occupation élevé et mesuré (module 15) |

::: recap
Points clés — chapitre 2

-   Six modèles : à la demande, engagement d'usage, réservation planifiée, capacité à attente, préemptible, contrat de capacité.
-   Les préavis de préemption documentés vont de 0 à 120 secondes, au mieux : ils ne remplacent pas le checkpoint périodique.
-   Prix d'une heure utile : $p / (1 - W)$ avec $W(T^*) = \sqrt{2C/M} + R/M$ ; la remise minimale du spot vaut $W$.
-   Un job qui ne sait pas reprendre n'a pas sa place sur du préemptible.
-   Les modèles se combinent : base réservée, pics à la demande, travaux reprenables en préemptible.
:::

## 3. Abstraire le fournisseur {#ch3}

« Sans réécrire les jobs » recouvre trois problèmes distincts. Chaque outil en résout un, et le confondre avec un autre est la première source de déception.

### 3.1. Trois problèmes, trois familles d'outils

-   **Provisionner** une infrastructure : réseaux, comptes, buckets, clusters Kubernetes. Terraform et ses *providers* décrivent cet état de façon déclarative.
-   **Placer un job** : choisir un lieu et une offre, obtenir la capacité, relancer ailleurs après une préemption. SkyPilot occupe cet espace.
-   **Répartir des jobs sur plusieurs clusters Kubernetes** : MultiKueue, dans l'écosystème de Kueue, envoie un workload vers l'un des clusters candidats.

Aucun des trois ne règle à votre place les données (chapitre 4), le réseau et l'identité (chapitre 6) ni la gouvernance (chapitre 8).

### 3.2. SkyPilot : un courtier entre les fournisseurs

SkyPilot a été présenté à NSDI 2023 comme un *intercloud broker* : un logiciel qui voit l'écosystème des clouds comme un ensemble plutôt que comme des silos. Les auteurs motivent ce courtier par les régulations sur l'emplacement des données et par la protection contre les pannes majeures. L'outil est ouvert.

Le job se décrit par un fichier YAML : ressources demandées, montages de fichiers, commandes `setup` et `run`. À partir de là, un optimiseur choisit le lieu le moins cher parmi ceux qui conviennent, et un *provisioner* obtient la capacité. L'article décrit un mécanisme de bascule : si l'allocation échoue par manque de capacité ou de quota, le lieu en échec est bloqué temporairement, l'optimiseur recalcule un plan sans lui et le *provisioner* réessaie.

Cette bascule sert surtout pour les ressources rares. Selon l'article, il a fallu 3 à 5 tentatives de lieu pour obtenir 8 GPU V100 chez AWS, et 2 à 7 pour 8 GPU T4, selon le moment de la demande.

### 3.3. Les jobs managés et la reprise

Pour un job qui doit survivre aux préemptions, SkyPilot propose les *managed jobs* (`sky jobs launch`). Un contrôleur surveille le job, le relance en cas de préemption, de panne de nœud ou de GPU, et nettoie à la fin. La documentation précise que le job doit enregistrer ses checkpoints sur un stockage persistant (volume ou bucket) pour reprendre sans repartir de zéro.

La stratégie de reprise se choisit dans `job_recovery`. Avec `FAILOVER`, le job redémarre dans la même région et passe à la suivante s'il n'y trouve pas de ressources. Avec `EAGER_NEXT_REGION`, valeur par défaut d'après la documentation, il passe directement à la région suivante. La documentation justifie ce défaut pour le spot : en pratique, une préemption dans une région signale souvent un manque de ressources dans cette région.

La documentation annonce aussi environ 70 % d'économie sur les coûts GPU avec des instances spot. C'est une affirmation du fournisseur de l'outil, sans conditions publiées sur cette page : traitez-la comme un ordre de grandeur à mesurer chez vous.

### 3.4. Lire un job, ligne à ligne

Le fichier `job.yaml` du lab 13.2 est l'exemple de ce chapitre. Voici ses ressources et ses montages.

~~~yaml
resources:
  accelerators: H100:8
  use_spot: true
  max_hourly_cost: 120.0          # per-instance price cap in USD, a budget guard (example value)
  any_of:                         # the optimizer tries the cheapest first and fails over to the next
    - infra: aws/us-east-1
    - infra: gcp/us-central1
    - infra: k8s/eu-gpu-cluster   # placeholder Kubernetes context
  job_recovery:
    strategy: EAGER_NEXT_REGION   # after a preemption go straight to another location
    max_restarts_on_errors: 2
file_mounts:
  /checkpoint:                    # survives the loss of the VM; its location decides where egress is paid
    source: r2://example-ckpt-bucket
    mode: MOUNT_CACHED
    type: MODEL_CHECKPOINT_RW
~~~

Trois lignes portent la politique. `any_of` donne trois lieux candidats, dont l'ordre de bascule est décidé par l'optimiseur ; `ordered` fixerait cet ordre. `job_recovery` choisit la stratégie de reprise. `file_mounts` place le checkpoint sur un bucket indépendant des trois lieux, ce qui évite qu'une bascule de AWS vers Google ne paie une sortie à chaque lecture (chapitre 4).

::: ex
[Exemple 3.1 — Ce que SkyPilot accepte, et ce qu'il laisse passer]{.tag} La branche hors ligne du lab 13.2 charge les fichiers avec le vrai code de SkyPilot 0.14.1 (`sky.Task.from_yaml`), sans compte cloud. Sortie capturée sur le bac à sable de l'auteur (Linux 6.18, 4 vCPU), le 24 octobre 2026 :

~~~text
skypilot 0.14.1
  job.yaml: parsed, num_nodes=2, candidates=["AWS([Spot], {'H100': 8}, max_cost=$120.0/hr)", "GCP([Spot], {'H100': 8}, max_cost=$120.0/hr)", "Kubernetes([Spot], {'H100': 8}, max_cost=$120.0/hr)"]
  rejected as expected: unknown key in resources (InvalidSkyPilotConfigError)
  rejected as expected: use_spot is not a boolean (InvalidSkyPilotConfigError)
  rejected as expected: unknown mount mode (InvalidSkyPilotConfigError)
  rejected as expected: malformed accelerators (ValueError)
  rejected as expected: unknown top-level key (InvalidSkyPilotConfigError)
~~~

L'analyse attrape les fautes de frappe, les mauvais types et les modes de montage invalides. Elle a aussi rejeté ma première version du fichier : `type:` n'est permis qu'avec `mode: MOUNT_CACHED`.

Elle **accepte** en revanche un nom de stratégie `job_recovery` invalide, et le fichier `bad-job.yaml`, qui n'a aucune reprise ni étiquette. Le chapitre 8 montre la politique qui comble ce trou. Rien de tout cela ne prouve qu'un lieu a de la capacité ou que votre quota l'autorise.

Lecture du code de SkyPilot 0.14.1 (`sky/clouds/kubernetes.py`), non exécutée : `use_spot` n'est admis sur un contexte Kubernetes que si ses nœuds portent une étiquette *spot*. Le troisième lieu de `job.yaml`, factice, pourrait donc être écarté au lancement alors que l'analyse l'accepte.
:::

### 3.5. Terraform multi-fournisseur

Terraform sait configurer plusieurs *providers*, y compris plusieurs configurations d'un même provider grâce à l'argument `alias`, que la documentation présente comme le moyen de définir plusieurs configurations pour un même fournisseur et de choisir laquelle utiliser pour chaque ressource ou module. Une flotte multi-fournisseurs l'utilise pour créer, de façon répétable, les comptes, les réseaux, les buckets et les clusters dans chaque lieu.

Ce que Terraform ne fait pas : il ne connaît ni la préemption, ni le placement d'un job, ni la file d'attente. L'abstraction du fournisseur y est celle des **modules que vous écrivez** : un module « cluster GPU » par fournisseur, avec la même interface. C'est un travail d'ingénierie à planifier, pas une propriété de l'outil. Le [module 6](../provisioning/index.html) traite le provisionnement en détail.

### 3.6. Kubernetes sur plusieurs clusters

MultiKueue est une extension de Kueue. La documentation la présente comme fonctionnalité bêta depuis Kueue v0.9, activée par défaut. Un dispositif MultiKueue comprend un cluster *manager* et au moins un cluster *worker*. Quand le workload d'un job obtient une réservation de quota sur le manager, un algorithme de dispatch (`AllAtOnce`, `Incremental` ou personnalisé) le crée sur tout ou partie des workers. Dès qu'un worker l'admet, le manager supprime les copies des autres.

::: war
[Le manager ne travaille pas pour lui-même]{.tag} La documentation de MultiKueue précise que le partage de rôle, où le cluster manager serait aussi l'un de ses propres workers, n'est pas supporté pour l'instant. Un cluster de contrôle dédié est donc une dépense à prévoir. Source : [MultiKueue](https://kueue.sigs.k8s.io/docs/concepts/multikueue/), lu le 24 octobre 2026. Le module 12 traite Kueue.
:::

### 3.7. Ce que l'abstraction ne cache pas

| Sujet | Ce que l'outil abstrait | Ce qui reste à vous |
|---|---|---|
| Lieu et capacité | la liste des lieux candidats et la bascule | les quotas, le compte, l'accès à la capacité |
| Image et pilotes | l'image par lieu peut se déclarer | construire et tester l'image sur chaque fournisseur |
| Interconnexion | une option `network_tier` | les variables NCCL, la performance mesurée (module 7) |
| Données | un montage de bucket | où vit le bucket, ce que coûte le lire depuis ailleurs |
| Identité | des identifiants par fournisseur | la fédération, la rotation, les droits minimaux (chapitre 6) |
| Coût | un plafond par instance, un classement par prix catalogue | l'allocation par équipe, l'imputation (chapitre 8) |

::: recap
Points clés — chapitre 3

-   Provisionner (Terraform), placer un job (SkyPilot) et répartir sur des clusters Kubernetes (MultiKueue) sont trois problèmes distincts.
-   SkyPilot calcule un placement par coût, bascule par lieu en cas d'échec d'allocation et relance les jobs managés après une préemption, à condition d'un checkpoint sur stockage persistant.
-   `EAGER_NEXT_REGION` est la valeur par défaut de reprise : une préemption signale souvent une pénurie dans la région.
-   Une analyse hors ligne attrape les fautes de syntaxe, pas les erreurs de politique ni les manques de capacité ou de quota.
-   Le job est portable ; l'image, l'interconnexion, les données et l'identité ne le sont pas.
:::

## 4. Données et gravité {#ch4}

Un GPU se loue à l'heure et se déplace en quelques minutes. Un jeu de données de dizaines de téraoctets se déplace en heures, coûte de l'argent à chaque sortie et laisse deux copies à gouverner. C'est ce qu'on appelle la **gravité des données** : plus un volume est gros, plus il attire les calculs vers l'endroit où il se trouve.

### 4.1. Trois coûts d'un déplacement

-   **L'argent.** La sortie de données est facturée à l'endroit qu'on quitte ; le stockage est facturé aux deux endroits pendant le chevauchement.
-   **Le temps.** Une copie de $D$ Go sur un lien de $B$ Gbit/s à l'efficacité $\eta$ dure $8D / (\eta B)$ secondes. Pendant ce temps, les GPU attendent ou ne démarrent pas.
-   **La cohérence.** Deux copies peuvent diverger ; savoir laquelle fait foi est une décision de gouvernance.

### 4.2. Anatomie d'une facture de sortie

Les fournisseurs facturent la sortie vers Internet par tranches mensuelles dégressives, après une franchise. Avec $f$ la franchise, $u_k$ les bornes cumulées des tranches (comptées après la franchise, $u_0 = 0$) et $r_k$ leurs tarifs par Go, le coût mensuel de $x$ Go vaut :

$$F(x) = \sum_k r_k \cdot \max\bigl(0,\ \min(x - f,\ u_k) - u_{k-1}\bigr)$$

Chez AWS, les tranches se cumulent sur le mois et sur plusieurs services du compte (EC2, S3, RDS et d'autres, d'après la [page de tarification EC2](https://aws.amazon.com/ec2/pricing/on-demand/)) : une franchise déjà consommée par d'autres usages n'est plus disponible. Le lab 13.3 gère ce cas avec le paramètre `used_gb`.

Le tableau donne les tarifs lus le 24 octobre 2026 à la source de chaque ligne. **Ne figez jamais ces valeurs** : relisez la page du fournisseur le jour de votre étude.

| Offre | Franchise mensuelle | Tarif par Go | Source |
|---|---|---|---|
| AWS, sortie Internet depuis us-east-1 | 100 Go | 0,09 USD jusqu'à 10 240 Go, 0,085 jusqu'à 51 200 Go, 0,07 jusqu'à 153 600 Go, 0,05 au-delà (volumes comptés après la franchise) | [liste de prix AWS](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSDataTransfer/current/index.json), publiée le 2026-09-16 |
| AWS, de us-east-1 vers une autre région | aucune | 0,02 USD (vers l'Irlande et l'Oregon) | même liste de prix |
| Azure, Europe de l'Ouest, *routing preference* Internet | 100 Go | 0,08 USD jusqu'à 10 100 Go au total, 0,065 jusqu'à 50 100, 0,06 jusqu'à 150 100, 0,04 au-delà | [API de prix Azure](https://prices.azure.com/api/retail/prices), tarif en vigueur depuis 2022-03-01 |
| Cloudflare R2, tous types de stockage | sans objet | 0 : pas de frais de sortie (la classe Infrequent Access a des frais de récupération) | [page de prix R2](https://developers.cloudflare.com/r2/pricing/), mise à jour le 1er octobre 2026 |
| Backblaze B2 | jusqu'à 3 fois le volume moyen stocké | 0,01 USD au-delà | [page de prix B2](https://www.backblaze.com/cloud-storage/pricing), lue le 2026-10-24 |

Google Cloud publie aussi ses tarifs de transfert, mais le tableau de la page lue est aplati et ses colonnes ne se rattachent pas aux en-têtes sans ambiguïté : ce cours ne cite aucun tarif Google et renvoie à la [page de prix du réseau](https://cloud.google.com/vpc/network-pricing).

### 4.3. Un exemple publié, avec des tarifs d'aujourd'hui

L'article SkyPilot offre un cas chiffré. Un pipeline entraîne un ResNet-50 sur ImageNet (150 Go, stocké sur AWS S3). Le plan « tout sur AWS » coûte 85 USD. Le plan choisi par l'optimiseur envoie les données chez Google, pour utiliser un TPU : 57 USD, dont 44 de calcul et 13 de sortie. L'article note en bas de page que, avec une entrée quatre fois plus grosse (600 Go), l'optimiseur renonce au transfert parce que la sortie domine.

::: ex
[Exemple 4.1 — À partir de quelle taille le déménagement perd-il ?]{.tag} La sortie de 13 USD pour 150 Go donne un tarif implicite de $13/150 = 0{,}0867$ USD par Go. En gardant fixes les coûts de calcul de l'article (44 et 85 USD), ce que suppose sa note, le déménagement reste avantageux tant que $44 + 0{,}0867\,D < 85$, soit $D < 41/0{,}0867 = 473$ Go. Les 150 Go sont sous ce seuil, les 600 Go le dépassent.

Avec la carte tarifaire d'aujourd'hui (AWS, franchise de 100 Go déjà consommée) le lab 13.3 calcule :

~~~text
[S1] 150 GB leaving AWS us-east-1 (volume of the dataset in the SkyPilot paper, section 5.1.1)
  free allowance still available :     4.50 USD
  free allowance already used up :    13.50 USD
[S2] same, dataset 4x larger (600 GB)
  free allowance already used up :    54.00 USD
~~~

Sortie capturée sur le bac à sable de l'auteur le 24 octobre 2026. Le tarif actuel de 0,09 USD par Go retrouve les 13 USD de l'article (13,50). Le seuil devient $41/0{,}09 = 456$ Go. Si la franchise est encore intacte, la sortie de 150 Go ne coûte que 4,50 USD : la franchise compte pour les petits volumes seulement. Les prix de calcul de l'article (2022-2023) ne sont pas ceux d'aujourd'hui, mais le raisonnement tient.
:::

<figure class="fig">
<svg viewBox="0 0 560 290" role="img" aria-labelledby="be-t be-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="be-t">Coût du plan qui reste sur AWS contre le plan qui déménage les données</title>
<desc id="be-d">Le coût du plan qui reste sur AWS est constant à 85 USD. Le coût du plan qui déménage vaut 44 USD plus 0,0867 USD par Go. Les deux droites se croisent à 473 Go. À 150 Go le déménagement coûte 57 USD, à 600 Go il en coûte 96.</desc>
<line x1="60" y1="240" x2="530" y2="240" stroke="currentColor" stroke-width="2"/>
<line x1="60" y1="240" x2="60" y2="24" stroke="currentColor" stroke-width="2"/>
<text x="295" y="276" text-anchor="middle" font-size="14" fill="currentColor">taille du jeu de données (Go)</text>
<text x="14" y="36" font-size="14" fill="currentColor">USD</text>
<text x="60" y="258" text-anchor="middle" font-size="14" fill="currentColor">0</text>
<text x="295" y="258" text-anchor="middle" font-size="14" fill="currentColor">350</text>
<text x="530" y="258" text-anchor="middle" font-size="14" fill="currentColor">700</text>
<text x="54" y="244" text-anchor="end" font-size="14" fill="currentColor">0</text>
<text x="54" y="84" text-anchor="end" font-size="14" fill="currentColor">85</text>
<line x1="60" y1="80" x2="530" y2="80" stroke="currentColor" stroke-width="3"/>
<line x1="60" y1="157" x2="530" y2="43" stroke="var(--accent)" stroke-width="3"/>
<circle cx="377" cy="80" r="6" fill="var(--accent)"/>
<text x="386" y="110" font-size="14" fill="currentColor">égalité à 473 Go</text>
<text x="70" y="72" font-size="14" fill="currentColor">rester sur AWS : 85</text>
<text x="70" y="188" font-size="14" fill="var(--accent)">déménager : 44 + 0,0867 par Go</text>
<circle cx="161" cy="133" r="4" fill="currentColor"/>
<text x="170" y="128" font-size="14" fill="currentColor">150 Go : 57</text>
<circle cx="463" cy="59" r="4" fill="currentColor"/>
<text x="400" y="52" font-size="14" fill="currentColor">600 Go : 96</text>
</svg>
<figcaption>Le plan qui déménage les données gagne tant que la sortie reste faible devant l'économie de calcul ; il perd au-delà de 473 Go. Chiffres de l'article SkyPilot (NSDI 2023, section 5.1.1), non actualisés.</figcaption>
</figure>

### 4.4. Étaler un déménagement ne le rend pas toujours moins cher

Puisque les tranches et la franchise repartent chaque mois, on pourrait croire qu'étaler un gros transfert sur plusieurs mois réduit la facture. Deux effets s'opposent. Étaler regagne la franchise chaque mois, ce qui compte pour les petits volumes. Étaler perd aussi les tranches dégressives, ce qui compte pour les gros.

::: ex
[Exemple 4.2 — 50 To et 200 To]{.tag} Le lab 13.3 calcule le déménagement de 50 To d'AWS S3 vers R2, avec un mois de stockage double, sur un lien de 10 Gbit/s à 80 % :

~~~text
[S3] 50 TB (50 000 GB) AWS S3 -> R2, one month of double storage, 10 Gbit/s link at 80 %
  egress   4292.70  dst storage   750.00  src storage  1150.00  TOTAL   6192.70 USD  in 13.9 h (0.58 d)
~~~

La sortie ne fait que 69 % de la facture : le stockage chevauché pèse 31 %. Pour 200 To sortant d'AWS us-east-1, étaler change le total ainsi :

~~~text
[S4] 200 TB (200 000 GB) leaving AWS us-east-1: one month vs split over several months
  split over 1 month(s):   13886.20 USD   (avg 0.0694 USD/GB)
  split over 2 month(s):   15624.40 USD   (avg 0.0781 USD/GB)
  split over 4 month(s):   17170.80 USD   (avg 0.0859 USD/GB)
~~~

Étaler sur deux mois coûte 12,5 % de plus. Pour 300 Go, au contraire, trois mois de 100 Go sortent entièrement dans la franchise : 0 USD contre 18 USD en un mois. Sortie capturée sur le bac à sable de l'auteur le 24 octobre 2026.
:::

### 4.5. Copier ou relire à distance ?

Un entraînement qui lit son jeu de données à chaque époque depuis un bucket d'un autre fournisseur paie la sortie à chaque lecture. Copier une fois coûte la sortie, plus le stockage du côté de l'entraînement.

Pour 150 Go, avec les tarifs de la carte, le lab 13.3 trouve : copie 6,75 USD (4,50 de sortie et 2,25 de stockage R2 sur un mois), contre 4,50 USD pour la première époque lue à distance (la franchise absorbe 100 Go), puis 13,50 USD par époque supplémentaire. La copie gagne dès la deuxième époque. À 90 époques, la relecture distante coûte 1 190 USD contre 6,75. Un cache local à la lecture (le mode `MOUNT_CACHED` de SkyPilot en est un) réduit le coût de la relecture, mais ne supprime pas la première lecture.

### 4.6. Les sorties « gratuites » ont des conditions

::: war
[Une sortie gratuite pour partir, pas pour exploiter]{.tag} AWS offre la sortie gratuite vers Internet aux clients qui déplacent **toutes** leurs données hors d'AWS, ou toutes celles d'un service donné, après demande au support. Google Cloud l'offre aux clients qui ont l'intention de résilier leur contrat pour le service concerné, avec un préavis et des délais documentés. Aucun de ces deux programmes ne couvre l'exploitation courante d'une flotte sur deux fournisseurs. Sources : [AWS](https://aws.amazon.com/blogs/aws/free-data-transfer-out-to-internet-when-moving-out-of-aws/), [Google Cloud](https://cloud.google.com/exit-cloud), lus le 24 octobre 2026.
:::

Pour les clients européens, le règlement européen sur les données (*Data Act*) encadre le changement de fournisseur. L'article d'AWS indique que sa dispense suit la direction fixée par ce règlement, et l'addendum contractuel d'AWS exige une demande de changement au moins deux mois avant la date prévue. Le texte du règlement n'a pas pu être relu à la source depuis le bac à sable (EUR-Lex et le site de la Commission refusent les accès) : les dates d'application exactes sont dans « À vérifier ».

Deux pratiques contournent le problème plutôt que de le payer. Stocker les jeux de données dans un **objet neutre à sortie gratuite**, comme le fait `job.yaml` avec un bucket R2 : les lectures depuis n'importe quel fournisseur ne paient pas de sortie du côté du stockage. Et **garder les gros jeux près des GPU les moins chers**, plutôt que de chasser le prix horaire.

### 4.7. Résidence et conformité

La résidence des données n'est pas un coût mais une contrainte dure : elle retire des candidats avant tout calcul d'optimisation. L'article SkyPilot cite parmi ses motivations les régulations sur l'emplacement et le traitement des données. Dans la pratique, la contrainte se traduit en liste de lieux autorisés, appliquée mécaniquement (la règle `--allow-prefix` de `policy_check.py` au chapitre 8) et revue avec le juriste de l'organisation. Ce cours ne donne pas d'avis juridique.

::: recap
Points clés — chapitre 4

-   Trois coûts de déplacement : argent (sortie et double stockage), temps ($8D/(\eta B)$) et cohérence des copies.
-   La sortie se facture par tranches mensuelles dégressives après une franchise, cumulées sur le compte ; les tarifs se relisent le jour de l'étude.
-   Un déménagement avantageux à 150 Go peut perdre à 600 Go : calculez le seuil (473 Go dans l'exemple publié, 456 Go avec le tarif actuel).
-   Étaler un transfert regagne la franchise mais perd les tranches dégressives ; selon le volume, c'est un gain ou une perte.
-   Les programmes de sortie gratuite supposent un départ complet ; un stockage neutre à sortie gratuite contourne la facture.
:::

## 5. Placement, files et reprise entre fournisseurs {#ch5}

Placer un job, c'est répondre à une question au démarrage et à chaque préemption : où repart-il ? Ce chapitre formule la réponse comme un score, la compare à trois politiques plus naïves sur des tirages communs, et en déduit un seuil de bascule.

### 5.1. Trois objectifs

Un placement équilibre trois objectifs qui se contredisent.

-   **Le coût**, compté en prix d'une heure **utile** (chapitre 2), plus les frais de déplacement (chapitre 4).
-   **La latence**, c'est-à-dire le délai avant que le job tourne : copie des données, attente de capacité, démarrage de la VM.
-   **La fiabilité**, qui est la fréquence des préemptions et la marge avant l'échéance.

Le lab 13.1 les réunit dans un score à minimiser pour chaque pool candidat. Soit $w$ le travail restant en heures, $n$ le nombre de GPU, $W$ le gaspillage du pool, $e$ le tarif de sortie par Go et $\lambda$ la valeur d'une heure de retard :

$$S = \frac{p}{1-W}\; n\, w \;+\; e\,(\text{Go à copier}) \;+\; \lambda\Bigl(t_{\text{copie}} + t_{\text{attente}} + t_{\text{démarrage}} + \frac{w}{1-W}\Bigr)$$

Le paramètre $\lambda$ vient de l'activité, pas du code : c'est ce que coûte un jour de retard (une échéance de conférence, une fenêtre de lancement). Le simulateur ne sait pas le choisir.

### 5.2. Quatre politiques

-   **`stay`** relance toujours dans le même pool et attend de la capacité. C'est la référence sans mouvement.
-   **`cheapest`**, le chasseur de prix, va toujours vers le prix catalogue le plus bas et attend sa capacité. Il ignore le gaspillage et le coût de déplacement.
-   **`failover`** prend le moins cher **parmi les pools qui accordent de la capacité maintenant**. C'est ce que fait une liste `any_of` avec bascule : le premier lieu qui répond gagne.
-   **`aware`** minimise le score $S$ du paragraphe précédent.

Dans SkyPilot, `ordered` fixe l'ordre d'essai et `any_of` le laisse à l'optimiseur ; `FAILOVER` et `EAGER_NEXT_REGION` règlent où repart un job managé après une panne (chapitre 3). Aucun ne calcule à votre place le seuil de la section 5.4.

### 5.3. Ce que donne le simulateur

Le scénario du lab 13.1 est entièrement **synthétique** : quatre pools de trois fournisseurs, un job de 64 GPU et 120 h de calcul utile, un checkpoint de 112 Go, un tarif de sortie de 0,09 u par Go et $\lambda = 40$ u par heure. Les lignes du tableau suivant donnent la moyenne sur 200 graines, les mêmes pour chaque politique.

~~~text
SYNTHETIC pools (u = arbitrary unit):
  a-od    provider A  price 10.00  hazard 0.00/h  p_avail 0.90  price per useful GPU-hour 10.000
  a-spot  provider A  price  4.00  hazard 0.15/h  p_avail 0.60  price per useful GPU-hour  4.695
  b-spot  provider B  price  3.00  hazard 0.30/h  p_avail 0.80  price per useful GPU-hour  3.867
  c-spot  provider C  price  3.40  hazard 0.10/h  p_avail 0.50  price per useful GPU-hour  3.851
job: 64 GPUs x 120 h of work, deadline 240 h, checkpoint 112 GB, home provider A; 200 seeds, lam = 40 u/h
 data GB    policy     cost u  finish h  late %  moves  preempt
       0      stay      36577     145.6     0.0   0.00    21.57
       0  cheapest      30285     159.5     0.0   1.00    46.95
       0  failover      53967     135.9     0.0   6.46    18.14
       0     aware      29785     139.4     0.0   1.04    13.29
         aware - stay:     -6791 u (+/- 175, paired over 200 seeds)
    1000      stay      36577     145.6     0.0   0.00    21.57
    1000  cheapest      30409     160.0     0.0   1.00    47.16
    1000  failover      51273     138.6     0.0   6.84    20.33
    1000     aware      29974     140.3     0.0   1.00    13.82
         aware - stay:     -6603 u (+/- 173, paired over 200 seeds)
   10000      stay      36577     145.6     0.0   0.00    21.57
   10000  cheapest      31180     162.3     0.0   1.00    47.23
   10000  failover      53457     142.5     0.0   6.71    20.09
   10000     aware      30815     143.0     0.0   1.00    13.93
         aware - stay:     -5761 u (+/- 173, paired over 200 seeds)
   30000      stay      36577     145.6     0.0   0.00    21.57
   30000  cheapest      32934     167.6     0.0   1.00    46.80
   30000  failover      57822     150.6     0.0   6.84    19.37
   30000     aware      32584     148.4     0.0   1.00    13.59
         aware - stay:     -3992 u (+/- 181, paired over 200 seeds)
   60000      stay      36577     145.6     0.0   0.00    21.57
   60000  cheapest      35621     175.7     0.0   1.00    46.56
   60000  failover      58942     167.1     0.0   7.30    21.14
   60000     aware      35251     156.5     0.0   1.00    13.72
         aware - stay:     -1326 u (+/- 173, paired over 200 seeds)
  100000      stay      36577     145.6     0.0   0.00    21.57
  100000  cheapest      39226     186.9     0.0   1.00    46.47
  100000  failover      66546     184.9     0.0   6.83    20.13
  100000     aware      36577     145.6     0.0   0.00    21.57
         aware - stay:        +0 u (+/- 0, paired over 200 seeds)
worst ratio aware / min(other policies) over the scan: 1.000
mean moves of 'aware' by dataset size: 0:1.04, 1000:1.00, 10000:1.00, 30000:1.00, 60000:1.00, 100000:0.00
smallest scanned dataset for which 'aware' (almost) never moves: 100000 GB
CRITERION (moves of 'aware' non-increasing with data size; cost <= 1.05 x the best other policy): OK
~~~

::: ex
[Exemple 5.1 — Lire le tableau]{.tag} Sortie capturée sur le bac à sable de l'auteur le 24 octobre 2026 (`python3 scenarios.py --seeds 200`, reproductible à l'identique). Colonnes : taille du jeu de données, politique, coût moyen en u, fin moyenne en heures, part en retard, déménagements, préemptions.

Sans donnée à déplacer, `cheapest` (30 285 u) et `aware` (29 785 u) battent `stay` (36 577 u). Mais `cheapest` subit 47 préemptions contre 13 et finit 20 h plus tard, parce qu'il vise le pool le moins cher au catalogue (b-spot) et non le moins cher par heure utile.

À 100 To, le chasseur de prix paie 39 226 u, 7,2 % de plus que `stay`, et finit 41 h plus tard. `aware` reste sur place (0 déménagement) et retrouve exactement le coût de `stay`. `failover` coûte 47,5 % de plus que `stay` dès 0 To : c'est le piège du paragraphe suivant.
:::

### 5.4. Le piège du pool à la demande

La politique `failover` atterrit chez le pool à la demande chaque fois que les pools spot refusent au moment de la demande. Ce pool n'est jamais préempté : rien ne ramène donc jamais le job sur du spot. Dans le tableau, le coût de 53 967 u contre 36 577 u pour `stay`, à 0 Go de données, le montre ; le test `test_on_demand_trap_costs_more_than_waiting_for_spot` reproduit le mécanisme sur un cas minimal.

Les 6,5 déménagements viennent d'un autre effet : à chaque préemption, `failover` reprend la décision et saute d'un fournisseur spot à l'autre (observé en journalisant les décisions du simulateur sur les mêmes 200 graines ; `scenarios.py` ne l'affiche pas).

Une liste `any_of` qui mélange spot et à la demande a ce comportement. Les parades sont de ne mettre à la demande dans la liste qu'en dernier recours explicite (`ordered`), de plafonner la durée d'un job sur du à-la-demande, ou de réévaluer le placement périodiquement. Le simulateur ne réévalue qu'à la préemption : c'est une limite assumée du lab.

### 5.5. Le seuil de bascule

Pour la politique `aware`, le seuil de taille de données au-delà duquel on ne bascule plus se calcule directement.

::: ex
[Exemple 5.2 — À partir de quel jeu de données reste-t-on ?]{.tag} Passer du pool a-spot (4,695 u par heure utile) au pool c-spot (3,851) économise $0{,}8442 \times 64 \times 120 = 6\,483$ u sur 120 h (valeurs non arrondies). Chaque Go déplacé coûte 0,09 u de sortie, plus le temps de copie valorisé : $\lambda \times 8/(10 \times 0{,}8)/3600 = 0{,}011$ u par Go, soit 0,101 u par Go au total.

Au premier ordre, le seuil vaut $6483/0{,}101 \approx 64\,000$ Go. Le calcul exact du score (`Aware.score` à l'instant 0, les deux pools refusant la capacité, avec le checkpoint, le démarrage et la durée de chaque pool) donne **65 931 Go** : un peu plus de 65 To. La commande `python3 threshold.py` du lab 13.1 le recalcule.

Ce seuil dépend de $\lambda$ : 71 925 Go si le temps ne vaut rien, 41 786 Go si une heure de retard vaut 400 u (même commande). Le balayage du tableau le confirme : `aware` déménage en moyenne une fois à 60 To, jamais à 100 To.
:::

<figure class="fig">
<svg viewBox="0 0 560 300" role="img" aria-labelledby="fl-t fl-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="fl-t">Décision après une préemption</title>
<desc id="fl-d">Après une préemption, le job perd le travail depuis le dernier checkpoint. Trois options : attendre le même pool, changer de pool chez le même fournisseur sans sortie de données, ou changer de fournisseur en payant la sortie du checkpoint et du jeu de données absent.</desc>
<defs><marker id="ar5" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--accent)"/></marker></defs>
<rect x="140" y="14" width="280" height="46" rx="6" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="280" y="34" text-anchor="middle" font-size="14" font-weight="700" fill="currentColor">Préemption</text>
<text x="280" y="52" text-anchor="middle" font-size="14" fill="currentColor">travail perdu : dernier checkpoint</text>
<line x1="280" y1="60" x2="280" y2="86" stroke="var(--accent)" stroke-width="3" marker-end="url(#ar5)"/>
<text x="280" y="106" text-anchor="middle" font-size="14" font-weight="700" fill="currentColor">Calculer le score S de chaque pool</text>
<line x1="150" y1="116" x2="80" y2="152" stroke="var(--accent)" stroke-width="3" marker-end="url(#ar5)"/>
<line x1="280" y1="114" x2="280" y2="152" stroke="var(--accent)" stroke-width="3" marker-end="url(#ar5)"/>
<line x1="410" y1="116" x2="480" y2="152" stroke="var(--accent)" stroke-width="3" marker-end="url(#ar5)"/>
<rect x="8" y="154" width="170" height="104" rx="6" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="93" y="176" text-anchor="middle" font-size="14" font-weight="700" fill="currentColor">Même pool</text>
<text x="93" y="198" text-anchor="middle" font-size="14" fill="currentColor">pas de sortie</text>
<text x="93" y="218" text-anchor="middle" font-size="14" fill="currentColor">attente de capacité</text>
<text x="93" y="238" text-anchor="middle" font-size="14" fill="currentColor">prix : le même</text>
<rect x="195" y="154" width="170" height="104" rx="6" fill="var(--side-bg)" stroke="currentColor" stroke-width="2"/>
<text x="280" y="176" text-anchor="middle" font-size="14" font-weight="700" fill="currentColor">Même fournisseur</text>
<text x="280" y="198" text-anchor="middle" font-size="14" fill="currentColor">autre pool, sans sortie</text>
<text x="280" y="218" text-anchor="middle" font-size="14" fill="currentColor">autre prix, autre taux</text>
<text x="280" y="238" text-anchor="middle" font-size="14" fill="currentColor">capacité différente</text>
<rect x="382" y="154" width="170" height="104" rx="6" fill="var(--side-bg)" stroke="var(--accent)" stroke-width="3"/>
<text x="467" y="176" text-anchor="middle" font-size="14" font-weight="700" fill="currentColor">Autre fournisseur</text>
<text x="467" y="198" text-anchor="middle" font-size="14" fill="currentColor">sortie : checkpoint</text>
<text x="467" y="218" text-anchor="middle" font-size="14" fill="currentColor">+ données absentes</text>
<text x="467" y="238" text-anchor="middle" font-size="14" fill="currentColor">+ temps de copie</text>
<text x="280" y="284" text-anchor="middle" font-size="14" fill="currentColor">on choisit le plus petit S, pas le plus bas prix</text>
</svg>
<figcaption>Trois issues après une préemption. Seule la troisième déclenche une sortie de données ; le score S les met toutes sur la même échelle de coût.</figcaption>
</figure>

### 5.6. Reprise entre fournisseurs

Une reprise ailleurs exige trois choses disponibles **depuis n'importe quel lieu candidat** : le dernier checkpoint, le jeu de données et l'image. Le plus simple est un stockage objet neutre pour les deux premiers (chapitre 4), et une image publiée dans un registre accessible partout.

L'article SkyPilot rapporte un cas favorable (ses auteurs écrivent *a good case*) sur une charge de bio-informatique. Le courtier a déplacé rapidement les 22 jobs préemptés vers une autre région, restée sans préemption pendant toute l'expérience. La région d'origine continuait de préempter dans toutes ses zones, ce qui causait beaucoup de traînards avec la stratégie à région unique. L'article présente aussi, sur une trace réelle de huit jours avec 24 VM spot de GCP, le cumul des préemptions au cours du temps.

Les auteurs précisent que cette politique n'est pas toujours meilleure que de rester dans la région : un job parti d'une région calme peut être déplacé vers une région plus agitée.

Une règle de sécurité complète le score : une **garde d'échéance**. Avant de choisir une offre préemptible, vérifiez que la fin attendue, $t_{\text{démarrage}} + t_{\text{attente}} + w/(1-W)$, laisse une marge avant l'échéance ; sinon retenez le pool fiable. La politique « couverte » du [projet 4](../../projects/multi-provider-scheduler/index.html) le fait pour une file de jobs, avec une capacité limitée par pool.

### 5.7. Les files

Le placement d'un job isolé ne dit rien de la file. Quand dix jobs veulent les mêmes GPU, l'ordre de service compte autant que le lieu. Sur Slurm, c'est la priorité, l'équité et la préemption par QOS du [module 5](../slurm/index.html) ; sur Kubernetes, ce sont les files et les quotas de Kueue du [module 12](../kubernetes-gpu/index.html), avec MultiKueue pour dispatcher vers plusieurs clusters. L'algorithme `Incremental` de MultiKueue évite de créer le workload partout en même temps, au prix d'un démarrage plus lent (par défaut, trois clusters par tour et cinq minutes avant le tour suivant).

::: recap
Points clés — chapitre 5

-   Un score de placement additionne le prix de l'heure utile, la sortie de données et la valeur du temps ; $\lambda$ vient de l'activité, pas du code.
-   Quatre politiques sur tirages communs : `stay`, `cheapest`, `failover` (piège du pool à la demande) et `aware`.
-   Sur le scénario synthétique, `aware` n'est jamais plus cher que les autres et reste sur place au-delà d'environ 66 To de données.
-   Le seuil de bascule se calcule : économie par heure utile fois travail restant, divisée par le coût par Go déplacé.
-   Une reprise entre fournisseurs suppose checkpoint, données et image accessibles de partout, et une garde d'échéance.
:::

## 6. Réseau et identité {#ch6}

Un job placé ailleurs doit pouvoir joindre ses données, s'authentifier et obtenir ses GPU. Ce chapitre traite ce qui circule entre les sites, ce qui les identifie et ce qui les limite.

### 6.1. Un job égale un site

Pourquoi ne pas coupler les GPU de deux fournisseurs pour un seul entraînement ? Parce que chaque étape échange les gradients, et que le lien entre sites est sans commune mesure avec celui d'un site.

::: ex
[Exemple 6.1 — Un all-reduce entre deux sites]{.tag} Un modèle de 7 milliards de paramètres a des gradients de $2 \times 7 \cdot 10^9 = 14$ Go en BF16. Reprenons le modèle du module 2 : chaque rang émet $2\,\frac{p-1}{p}\,n$ octets dans un anneau.

Dans un site, 64 GPU à 40 Go/s (valeurs de l'exercice 11 du module 2) échangent ces gradients en $2 \times \frac{63}{64} \times 14/40 = 0{,}69$ s.

Entre deux sites reliés à 10 Gbit/s à 80 % d'efficacité, soit 1 Go/s, avec $p = 2$ : $2 \times \frac{1}{2} \times 14/1 = 14$ s par étape. C'est **20 fois** plus long, avant tout recouvrement et en ignorant la latence de la liaison. Ces bandes passantes sont des hypothèses d'exemple.

Le job ne se coupe donc pas : il se place entier, et seuls ses checkpoints et ses données traversent la liaison.
:::

### 6.2. Ce qui traverse la liaison

Entre fournisseurs circulent le plan de contrôle (ordres de lancement, supervision), les checkpoints, les jeux de données et les journaux. Les options de connexion vont de l'Internet public avec chiffrement à un VPN de site à site, puis à une interconnexion privée ou un appairage (*peering*). Le choix dépend du volume et de la sensibilité.

Les liaisons privées ont leur propre tarif, parfois par port et par heure, parfois par volume : ce cours n'en cite aucun, car aucune page tarifaire n'a été relue pour ce module. Mesurez le débit réel **de bout en bout** avec `iperf3` entre deux VM des sites concernés avant de promettre un délai de copie.

### 6.3. Identités fédérées

Chaque fournisseur a son propre système d'identités. Mettre des clés d'accès longues dans un fichier de job ou dans une variable d'environnement est le chemin le plus court vers un incident. La documentation de Google Cloud présente la fédération d'identité de charge de travail (*Workload Identity Federation*) comme le moyen de donner à des charges hors Google, y compris sur AWS ou Azure, un accès à ses ressources au moyen d'identités fédérées plutôt que d'une clé de compte de service.

Le principe se généralise : un fournisseur d'identité de confiance délivre un jeton court à la charge, le fournisseur cible l'échange contre des droits limités, et rien de durable n'est stocké. Dans SkyPilot, les secrets se déclarent dans `secrets:` et se passent au lancement ; la règle E4 de `policy_check.py` refuse un secret placé dans `envs`.

### 6.4. Comptes, projets et quotas

La première cause d'échec d'un lancement est souvent le quota, avant même la capacité. L'article SkyPilot le dit : une allocation échoue soit par manque de capacité dans un lieu, soit par manque de quota du compte. La documentation d'AWS exprime les quotas d'instances en **nombre maximal de vCPU** par famille, avec des lignes distinctes comme « Running On-Demand P instances », et un tableau séparé pour les instances Spot et un autre pour les Capacity Blocks.

Deux conséquences. Le quota se calcule en vCPU, pas en GPU ou en nœuds, donc en nombre de nœuds fois le nombre de vCPU du type d'instance. Et un parc qui mélange à la demande et spot doit demander les deux quotas. Les délais d'obtention varient : demandez-les avant d'en avoir besoin.

### 6.5. Segmenter

Un compte ou un projet par équipe et par environnement limite les dégâts d'une erreur et rend les coûts lisibles (chapitre 8). Côté réseau, les nœuds d'entraînement n'ont besoin que de sortir vers les stockages et le plan de contrôle, pas de recevoir du trafic public. Le module 16 traite la sécurité d'une plateforme partagée.

::: recap
Points clés — chapitre 6

-   Un entraînement ne se coupe pas entre sites : 14 s contre 0,7 s par étape dans l'exemple, soit 20 fois plus.
-   Entre sites ne circulent que le contrôle, les checkpoints, les données et les journaux ; mesurez le débit de bout en bout.
-   Préférez des identités fédérées à jetons courts aux clés longues ; les secrets ne vont jamais dans `envs`.
-   Les quotas d'instances se comptent en vCPU, par famille, séparément pour le spot : demandez-les à l'avance.
-   Un compte ou un projet par équipe et par environnement rend dégâts et coûts lisibles.
:::

## 7. Centres publics de calcul : accès et articulation avec le cloud {#ch7}

Les centres nationaux et européens offrent des GPU sans facture à l'heure, à condition de passer par une procédure d'attribution. Pour une équipe d'infrastructure, ils sont une troisième source de capacité, avec leurs propres règles.

### 7.1. Un autre contrat : des heures attribuées

Dans un cloud, vous payez ce que vous allouez. Dans un centre public, un comité attribue un volume d'heures à un projet, vous le consommez par jobs soumis à Slurm, et vous rendez un rapport. L'unité n'est pas la monnaie mais l'heure de GPU d'un type donné ; la conversion entre types de GPU (section 1.4) fait partie de la demande.

Les dossiers répondent à des critères scientifiques et à une procédure : ce ne sont pas des commandes. Aucune garantie de délai n'existe, hors des voies rapides décrites plus bas.

### 7.2. En France : GENCI, IDRIS, eDARI

Le portail eDARI de GENCI reçoit les demandes d'heures sur les calculateurs nationaux, dont Jean Zay à l'IDRIS. La page lue le 24 octobre 2026 distingue l'accès **dynamique** et l'accès **régulier**. Le seuil entre les deux est fixé à 50 kh GPU V100, avec les équivalences 1 GPU H100 = 2 GPU A100 = 4 GPU V100. L'exemple donné par la page : une demande de 30 kh A100 est redirigée vers une allocation régulière.

La même page annonce la clôture de l'appel pour les accès réguliers le 8 février 2027 à 9 h. Les conditions affichées sont d'appartenir ou d'être associé à une structure de recherche française, de faire de la recherche donnant lieu à publication et de déposer un rapport d'activité à la fin de l'attribution. Elle précise aussi que les appels d'EuroHPC sont ouverts en permanence.

### 7.3. En Europe : EuroHPC et les usines d'IA

L'entreprise commune EuroHPC propose des appels à plusieurs échelles. Pour les *AI Factories*, la page lue le 24 octobre 2026 liste trois modes d'accès, tous marqués « ouverts » ce jour-là.

-   **Playground** s'adresse aux PME, aux jeunes entreprises et aux utilisateurs débutants. L'accès se fait en file FIFO (premier arrivé, premier servi), avec un démarrage sous deux jours ouvrés et un accompagnement d'intégration.
-   **Fast Lane** vise les PME et jeunes entreprises qui font de l'IA avec des allocations de taille moyenne.
-   **Large Scale** concerne les modèles et applications qui demandent plus de 50 000 heures de GPU, pour un an au maximum.

Pour les supercalculateurs, les appels portent sur les applications d'IA et à forte intensité de données, l'accès régulier, l'accès à très grande échelle et l'accès pour le développement. Ce dernier est un appel continuellement ouvert, avec un délai maximal de deux semaines avant le début d'accès après dépôt.

### 7.4. Aux États-Unis

Le programme [ACCESS](https://allocations.access-ci.org/project-types) de la NSF organise l'attribution en quatre types de projets, Explore, Discover, Accelerate et Maximize, selon l'ampleur des besoins. On peut démarrer par un projet Explore et monter en gamme. Le projet pilote [NAIRR](https://nairrpilot.org/) (*National AI Research Resource*) vise à relier chercheurs et enseignants américains à des ressources de calcul, de données et de formation ; sa page annonce que la NSF a désigné le 1er septembre 2026 un centre d'exploitation qui prolonge le pilote. Comme en Europe, les règles d'éligibilité varient et se lisent sur la page de chaque programme.

::: ex
[Exemple 7.1 — Quelle voie pour quelle demande ?]{.tag} Deux demandes converties avec les équivalences d'eDARI (1 H100 = 4 V100).

Un entraînement de 64 GPU H100 pendant 72 h consomme $64 \times 72 = 4\,608$ h H100, soit $4608 \times 4 = 18\,432$ h V100. C'est 37 % du seuil de 50 000 h : une allocation **dynamique** convient.

Un entraînement de 256 GPU H100 pendant 14 jours consomme $256 \times 14 \times 24 = 86\,016$ h H100, soit 344 064 h V100, 6,9 fois le seuil : il faut une allocation **régulière**, déposée avant la clôture de l'appel, avec un justificatif scientifique, ou une voie européenne comme Large Scale (au-dessus de 50 000 heures GPU, unité de type non précisée par la page).

Les dates et seuils sont ceux lus le 24 octobre 2026. Relisez les appels avant de planifier.
:::

### 7.5. Articuler un centre public et un cloud

Un centre public et un cloud ne se substituent pas, ils se complètent. Le tableau liste les différences qui comptent pour l'infrastructure.

| Aspect | Cloud | Centre public |
|---|---|---|
| Accès | compte et carte bancaire ou contrat | dossier scientifique, comité, rapport |
| Délai | minutes, si la capacité existe | dépend de l'appel ; ordre de grandeur, non sourcé : semaines à mois pour un appel à échéance, quelques jours pour une voie rapide |
| Unité | monnaie, à la seconde ou à l'heure | heures GPU attribuées, d'un type donné |
| Outil de soumission | API, SkyPilot, Kubernetes | Slurm (module 5) |
| Données | vos buckets | systèmes de fichiers du centre, soumis à ses règles |
| Reprise | à vous de la concevoir (chapitre 5) | à vous aussi : la préemption par QOS existe, et le checkpoint reste indispensable |
| Objectif | production, commercial possible | recherche, publication attendue |

SkyPilot sait cibler un cluster Slurm : la page de référence de son YAML mentionne `infra: slurm`, y compris pour des clusters AWS HyperPod. Un centre public précis reste un cas à tester, car les règles d'accès, d'installation d'outils et de réseau des nœuds varient d'un centre à l'autre.

La stratégie raisonnable est d'utiliser le centre pour le gros calcul de recherche qui entre dans son cadre, et le cloud pour ce qui demande de la souplesse ou de la confidentialité. La passerelle entre les deux est le checkpoint portable : un format que les deux environnements savent relire.

::: recap
Points clés — chapitre 7

-   Un centre public attribue des heures de GPU sur dossier ; l'unité est un type de GPU, convertible (1 H100 = 2 A100 = 4 V100 selon eDARI).
-   eDARI distingue accès dynamique et régulier autour de 50 kh V100 ; EuroHPC propose Playground, Fast Lane et Large Scale pour les usines d'IA.
-   ACCESS (États-Unis) organise quatre niveaux de projet ; le pilote NAIRR ouvre d'autres ressources.
-   Les appels, seuils et dates changent : citez-les datés et relisez-les avant de planifier.
-   Cloud et centre public se complètent : checkpoint portable et outils de soumission différents.
:::

## 8. Gouvernance : inventaire, étiquettes, coûts, nettoyage {#ch8}

Une flotte multi-fournisseurs multiplie les endroits où une ressource oubliée coûte de l'argent. La gouvernance est le travail qui rend chaque ressource attribuable à une équipe et supprimable sans enquête.

### 8.1. Inventaire et étiquetage

Un inventaire commence par une règle : toute ressource porte au moins une équipe, un projet et un responsable. SkyPilot les pose avec `resources.labels`, que sa documentation décrit comme des étiquettes appliquées aux instances. Chez AWS, une étiquette ne figure dans les rapports de facturation qu'après son **activation** dans la console de facturation, d'après la documentation sur les étiquettes d'allocation de coûts : une étiquette posée mais non activée n'imputera rien.

### 8.2. Des coûts comparables entre fournisseurs

Chaque fournisseur a son format de facture, ses noms et ses unités. FOCUS (*FinOps Open Cost and Usage Specification*), que la FinOps Foundation décrit comme un format unifié de données de facturation de sources multiples, normalise ces données pour réduire le travail de rapprochement. La page de présentation de la spécification renvoie aux notes de la version 1.4 (lue le 24 octobre 2026). L'allocation par équipe et le *showback* sont traités au [module 15](../finops-capacity/index.html), qui construit un rapport depuis les traces de l'ordonnanceur.

### 8.3. Nettoyer automatiquement

Le coût d'une ressource oubliée est proportionnel au temps. SkyPilot permet de déclarer `resources.autostop` avec `idle_minutes` et `down: true`, qui arrête et supprime le cluster inactif. Pour un job managé, le cluster temporaire est nettoyé à la fin par le contrôleur.

::: ex
[Exemple 8.1 — Le week-end d'un nœud oublié]{.tag} Un nœud de 8 GPU lancé le vendredi à 18 h et retrouvé le lundi à 8 h reste alloué 62 h. À un prix de 4 u par GPU-heure (valeur d'exemple), cela fait $8 \times 62 \times 4 = 1\,984$ u. Avec un arrêt automatique après 30 minutes d'inactivité, la perte maximale est de $8 \times 0{,}5 \times 4 = 16$ u, soit 124 fois moins.

Un `down: true` vaut mieux qu'un simple arrêt : une VM arrêtée garde en général ses disques, qui continuent d'être facturés. La règle E5 de `policy_check.py` l'exige pour un cluster interactif.
:::

### 8.4. La gouvernance comme code

Une règle écrite dans un wiki n'est pas appliquée. Le lab 13.2 propose `policy_check.py`, un lint des fichiers de job qui ne lit que le YAML. Les règles E sont des erreurs, les règles W des avertissements.

| Code | Règle |
|---|---|
| E1 | les étiquettes `team`, `project` et `owner` sont présentes |
| E2 | un job `use_spot` déclare `job_recovery` |
| E3 | un job `use_spot` monte un bucket en écriture pour reprendre |
| E4 | aucun secret n'est dans `envs` |
| E5 | un cluster interactif a `autostop` (au plus 60 minutes) avec `down: true` |
| E6 | avec `--allow-prefix`, tout lieu candidat est dans la liste autorisée |
| W1 à W4 | pas de plafond de coût ; un seul lieu candidat ; bucket d'un autre fournisseur ; lieu non vérifiable (contexte Kubernetes ou Slurm, avec `--allow-prefix`) |

::: ex
[Exemple 8.2 — Un job que SkyPilot accepte et que la politique refuse]{.tag} Sortie capturée sur le bac à sable de l'auteur le 24 octobre 2026, pour `bad-job.yaml` du lab 13.2 :

~~~text
bad-job.yaml: E1 error: label 'project' is missing
bad-job.yaml: E1 error: label 'owner' is missing
bad-job.yaml: E2 error: use_spot without job_recovery
bad-job.yaml: E3 error: use_spot without a writable mounted bucket to resume from
bad-job.yaml: E4 error: envs.HF_TOKEN looks like a credential: use secrets:
bad-job.yaml: W1 warning: no max_hourly_cost
bad-job.yaml: W2 warning: fewer than two candidate locations: nowhere to fail over
bad-job.yaml: 5 error(s), 2 warning(s)
~~~

Le même fichier est accepté par `sky.Task.from_yaml` (exemple 3.1). La politique et l'analyse de syntaxe sont deux contrôles différents ; il faut les deux. Lancée dans une intégration continue sur le dépôt des fichiers de job, la politique bloque ces fichiers avant tout lancement.
:::

### 8.5. Une revue périodique

Trois contrôles réguliers évitent la dérive.

-   **Inventaire contre facture.** Chaque ligne de facture d'un fournisseur se rattache à une étiquette ; la part sans étiquette est un indicateur à suivre.
-   **Orphelins.** Toute ressource sans job actif depuis une durée fixée est signalée, puis supprimée après préavis.
-   **Quotas et engagements.** Les quotas demandés, les engagements en cours et leurs dates de fin sont dans un tableau revu chaque trimestre avec la finance (module 15).

::: recap
Points clés — chapitre 8

-   Toute ressource porte équipe, projet et responsable ; chez AWS, les étiquettes d'allocation doivent être activées pour apparaître dans la facturation.
-   Un format commun (FOCUS) rend les coûts de plusieurs fournisseurs comparables.
-   L'arrêt automatique avec suppression borne la perte d'une ressource oubliée (124 fois moins dans l'exemple).
-   La gouvernance s'écrit en code, relue et testée comme le reste ; elle complète l'analyse de syntaxe de l'outil.
-   Trois revues régulières : inventaire contre facture, orphelins, quotas et engagements.
:::

## Labs {#labs}

Trois labs, 9,5 h au total : 4 h, 2,5 h et 3 h. Les labs 13.1 et 13.3 sont de type `sandbox` et ont été exécutés ; le lab 13.2 est de type `cluster` et sa branche cloud n'a **jamais été exécutée** (voir ci-dessous).

### Lab 13.1 — Simulateur de placement sensible aux coûts {#lab-13-1}

::: lab

**Objectif.** Comparer quatre politiques de placement d'un job préemptible sur des tirages communs, et trouver la taille de données au-delà de laquelle basculer ne vaut plus son coût. **Durée.** 4 h (partie A, 1 h : formules et moteur ; partie B, 3 h : politiques, balayage, critère). **Prérequis matériels.** Portable CPU, Python 3 avec `pytest` ; ni GPU ni compte cloud. Les données du scénario sont **synthétiques**.

1.  Lisez la docstring de `labs/multi-cloud/cost-aware-placement/reference/placement.py` : tirages communs, facturation d'une allocation, sémantique du checkpoint et de la copie.
2.  Dans `starter/placement.py`, écrivez `young_daly`, `waste`, `price_per_useful_hour` et `transfer_hours`. Lancez `IMPL=starter python -m pytest -q tests` : les tests de formules passent.
3.  Écrivez `move_cost`, `paired_diff` et `Aware.score`. Relisez la timeline exacte avec une préemption forcée dans `tests/test_placement.py` et refaites son calcul à la main.
4.  Lancez `python3 scenarios.py --seeds 200` avec la référence et reproduisez le tableau du chapitre 5, puis refaites-le avec `--impl starter` une fois vos fonctions écrites.
5.  Faites varier `--lam` (0, 40, 400) et relevez entre quelles deux tailles de la grille `aware` cesse de déménager, puis lancez `python3 threshold.py` pour le seuil exact et comparez à l'exemple 5.2.
6.  Changez `p_avail` du pool a-spot et le tarif de sortie : décrivez ce qui bascule en premier.

**Critère de réussite.** `verify.sh` affiche la ligne `CRITERION (moves of 'aware' non-increasing with data size; cost <= 1.05 x the best other policy): OK`, puis `CRITERION (threshold positive and non-increasing with lam): OK`, après des tests verts côté référence et rouges côté départ. Les critères sont **structurels**, pas des valeurs : le nombre de déménagements de `aware` ne croît pas avec la taille des données, son coût ne dépasse jamais de 5 % la meilleure des trois autres politiques, et le seuil de taille baisse quand `lam` monte. Aucun temps mesuré n'est testé.

**Pour aller plus loin.** Ajoutez une migration volontaire vers un pool devenu moins cher, ou reprenez le même scénario dans le [projet 4](../../projects/multi-provider-scheduler/index.html), qui gère plusieurs jobs et une capacité limitée.
:::

### Lab 13.2 — Un job SkyPilot indépendant du fournisseur {#lab-13-2}

::: lab

**Objectif.** Écrire et contrôler un job managé qui survit à la préemption, avec sa politique de gouvernance. **Durée.** 2,5 h (partie A, 1,5 h : étapes 1 à 5 ; partie B, 1 h : étapes 6 et 7 ; l'étape 8, facultative, s'ajoute). **Prérequis matériels.** Portable CPU, Python 3 avec `pytest` et `pyyaml`, `yamllint` et `shellcheck` recommandés ; la branche d'analyse de SkyPilot exige `pip install skypilot==0.14.1` dans un environnement à part. La branche cloud exige un compte et du crédit.

**Type `cluster`.** Ce qui a été exécuté : lint, règles de gouvernance, analyse hors ligne par SkyPilot 0.14.1 et répétition locale de la reprise. **Ce qui ne l'a pas été : tout lancement réel (`sky jobs launch`), toute bascule entre fournisseurs, toute préemption réelle.**

1.  Lisez `job.yaml` ligne à ligne et repérez où se décident le lieu, la reprise et le checkpoint.
2.  Lancez `bash verify.sh`. Sans SkyPilot, la section « 3. offline parse » du script affiche `SKIPPED` ; créez un environnement avec `skypilot==0.14.1` et relancez avec `SKY_PYTHON=…`.
3.  Lancez `python3 policy_check.py bad-job.yaml`, corrigez le fichier jusqu'à zéro erreur, puis refaites passer l'analyse SkyPilot.
4.  Lisez `train.py` (écriture atomique, reprise, gestionnaire de SIGTERM) et `rehearse_preemption.sh`.
5.  Lancez `rehearse_preemption.sh` et relevez les étapes perdues avec et sans préavis.
6.  Appliquez la règle de résidence : `python3 policy_check.py job.yaml --allow-prefix aws/eu- --allow-prefix gcp/europe-`, puis `job-eu.yaml`.
7.  Écrivez d'abord le test, puis la règle W5 : un job `use_spot` sans `max_restarts_on_errors` est signalé.
8.  Sur un vrai compte (non exécuté par l'auteur) : `sky check`, puis `sky jobs launch -n pretrain-demo job.yaml` avec de vrais buckets, et coupez la VM depuis la console.

**Critère de réussite hors ligne.** `verify.sh` affiche `OK skypilot parse: 4 files accepted (bad-job.yaml is valid for SkyPilot, only the policy refuses it), 5 mutations rejected`, `15 passed`, et `OK preemption rehearsal: resumed runs match the uninterrupted run exactly`. **Critère sur cluster (non vérifié)** : après la perte d'une VM, `sky jobs queue` montre au moins une reprise et le journal affiche un `resumed_from_step=` non nul.

**Pour aller plus loin.** Ajoutez un lieu Slurm (`infra: slurm`) à `any_of` et lisez ce que `policy_check.py --allow-prefix …` en dit (W4).
:::

### Lab 13.3 — Coût réel d'un déménagement de données {#lab-13-3}

::: lab

**Objectif.** Programmer et tester le calculateur du chapitre 4, puis l'appliquer à vos propres volumes. **Durée.** 3 h (partie A, 1 h : carte tarifaire, scénarios ; partie B, 2 h : écrire les fonctions). **Prérequis matériels.** Portable CPU, Python 3 avec `pytest` et `pyyaml`. Les tarifs de `rates.yaml` sont **réels et datés du 24 octobre 2026** ; relisez-les le jour de votre étude.

1.  Ouvrez `labs/multi-cloud/egress-cost/rates.yaml` : pour chaque entrée, retrouvez la source et la date. Ouvrez une source et vérifiez une valeur.
2.  Lancez `bash verify.sh` et lisez le tableau des scénarios S1 à S5.
3.  Dans `starter/egress.py`, écrivez `tiered_cost` : franchise, tranches, position de départ `used_gb`. Lancez les tests.
4.  Écrivez `split_cost`, `transfer_hours`, `storage_cost`, puis `move_cost`.
5.  Écrivez `breakeven_gpu_hours` et `copy_vs_remote_read`.
6.  Remplacez les tarifs par ceux d'un fournisseur de votre choix (page de prix lue aujourd'hui) et refaites S3 pour un volume qui vous concerne.

**Critère de réussite.** `verify.sh` affiche `18 passed` pour la référence et `18 failed` pour le départ, puis le tableau, dont `[S1] ... free allowance already used up : 13.50 USD`, et finit par `ok: egress-cost reference passes, starter fails as intended`. Les montants du tableau sont de l'arithmétique exacte à partir de la carte ; ils changeront avec **vos** tarifs, et c'est le but.

**Pour aller plus loin.** Ajoutez le coût des requêtes et des lectures de données froides, puis un second site de destination, et comparez l'étalement sur plusieurs mois.
:::

## Exercices {#ex}

Les tarifs et les paramètres sont donnés dans chaque énoncé : les corrigés ont été recalculés avec le code des labs, et les commandes citées ont été exécutées.

::: exo
[Exercice 1 · ★ — Une facture de sortie]{.tag} Un compte AWS sort 5 To (5 000 Go) en un mois depuis us-east-1. La franchise est de 100 Go, puis le tarif est de 0,09 USD par Go jusqu'à 10 240 Go (chapitre 4). Calculez la facture (a) si la franchise est intacte, (b) si d'autres usages du compte l'ont déjà consommée.
:::

::: sol
(a) Après la franchise, il reste $5000 - 100 = 4900$ Go à 0,09 USD : **441,00 USD**.

(b) La franchise étant consommée, les 5 000 Go sont tous facturés : $5000 \times 0{,}09 = $ **450,00 USD**.

Vérification avec le lab 13.3 : `tiered_cost(5000, tiers, 100)` rend 441,0 et `tiered_cost(5000, tiers, 100, used_gb=100)` rend 450,0. La franchise ne pèse que 9 USD sur ce volume ; elle domine seulement les petits transferts.
:::

::: exo
[Exercice 2 · ★ — Lire une sortie de politique]{.tag} Reprenez la sortie de l'exemple 8.2 pour `bad-job.yaml`. Pour chacune des cinq erreurs E1 à E4 et des deux avertissements, donnez la modification minimale du YAML qui la fait disparaître. Laquelle de ces erreurs SkyPilot détecterait-il seul à l'analyse ?
:::

::: sol
Corrections minimales, une par ligne.

-   **E1** : ajouter `project` et `owner` sous `resources.labels`.
-   **E2** : ajouter `job_recovery: {strategy: EAGER_NEXT_REGION}`.
-   **E3** : monter un bucket en écriture, par exemple `/checkpoint` avec `mode: MOUNT_CACHED`.
-   **E4** : déplacer `HF_TOKEN` de `envs` vers `secrets` et le passer au lancement.
-   **W1** : ajouter `max_hourly_cost`.
-   **W2** : remplacer `infra: aws` par une liste `any_of` de deux lieux au moins.

**Aucune** de ces erreurs n'est détectée par l'analyse de SkyPilot : le fichier est valide (exemple 3.1). Le fichier corrigé avec un lieu AWS et un lieu Google (`bad-job-fixed.yaml` dans le lab, à lire après l'essai) donne 0 erreur et un seul avertissement, W3 : le bucket `s3://` du jeu de données est lu depuis un lieu Google, donc avec une sortie de données. Avec deux lieux AWS, W3 ne se déclencherait pas. Cet avertissement est légitime et se traite au chapitre 4.
:::

::: exo
[Exercice 3 · ★ — Convertir une demande d'heures]{.tag} Avec les équivalences d'eDARI (1 H100 = 2 A100 = 4 V100) et le seuil de 50 kh V100 entre accès dynamique et régulier (chapitre 1 et chapitre 7), classez (a) une demande de 12 000 h H100, (b) une demande de 40 000 h A100. (c) Quelle est la plus grosse demande en h A100 qui reste dynamique ?
:::

::: sol
(a) $12\,000 \times 4 = 48\,000$ h V100, sous le seuil : **dynamique**.

(b) $40\,000 \times 2 = 80\,000$ h V100, au-dessus : **régulière**.

(c) $50\,000 / 2 = 25\,000$ h A100.

La page eDARI donne le même raisonnement pour 30 kh A100 (60 kh V100, donc régulier). Lue le 24 octobre 2026 : relisez le seuil avant de planifier.
:::

::: exo
[Exercice 4 · ★★ — La remise qui justifie le spot]{.tag} Un taux d'interruption de 0,2 par heure, un checkpoint de 2 minutes, une reprise de 12 minutes. Calculez $T^*$, $W$ et la remise minimale du spot. Le spot à 4,0 u bat-il une offre à la demande à 5,0 u ? À 4,5 u ? Utilisez les formules du chapitre 2.
:::

::: sol
Ici $M = 1/0{,}2 = 5$ h, $C = 2/60 = 0{,}0333$ h et $R = 0{,}2$ h. La période optimale vaut $T^* = \sqrt{2 \times 0{,}0333 \times 5} = 0{,}577$ h, soit **34,6 minutes**.

Le gaspillage vaut $W = \sqrt{2C/M} + R/M = 0{,}1155 + 0{,}04 = 0{,}1555$. La remise minimale est donc de **15,6 %**, et le prix de l'heure utile du spot à 4,0 u vaut $4{,}0/0{,}8445 = 4{,}74$ u.

Face à 5,0 u, la remise est de 20 % : le spot gagne (4,74 contre 5,0). Face à 4,5 u, la remise n'est que de 11,1 % : il perd (4,74 contre 4,5). Le gain dépend des taux que vous mesurez, pas du prix catalogue seul.
:::

::: exo
[Exercice 5 · ★★ — Combien coûte une préemption ?]{.tag} La répétition du lab 13.2 affiche : « kill : resumed from step 125, lost 12 steps ». Dans un vrai job de 64 GPU, une étape dure 90 s et un checkpoint a lieu toutes les 25 étapes. (a) Combien de GPU-heures cette préemption a-t-elle fait perdre ? (b) Quelle perte moyenne attendre par préemption si elle tombe à un instant uniforme ? (c) Quel intervalle de checkpoint, en étapes, garde cette perte moyenne sous 5 GPU-heures ? (d) Pourquoi ne pas descendre à une étape ?
:::

::: sol
(a) $12 \times 90 = 1080$ s, soit 0,30 h ; sur 64 GPU : **19,2 GPU-h**.

(b) La perte moyenne vaut la moitié de l'intervalle : $12{,}5$ étapes, soit $12{,}5 \times 90 / 3600 \times 64 = $ **20 GPU-h**.

(c) La perte moyenne $= (K/2) \times 90/3600 \times 64 = 0{,}8\,K$ GPU-h. Pour rester sous 5, il faut $K < 6{,}25$ étapes.

(d) Chaque checkpoint coûte du temps de GPU (le terme $C/T$ de $W$). La période optimale équilibre ce coût et la perte attendue ; elle se calcule avec Young et Daly, pas avec la seule perte moyenne.
:::

::: exo
[Exercice 6 · ★★ — Diagnostic : le job qui coûte 47 % de plus]{.tag} Dans le tableau de l'exemple 5.1, à 0 Go de données, la politique `failover` coûte 53 967 u contre 36 577 u pour `stay`, finit plus tôt (135,9 h contre 145,6 h) et déménage 6,46 fois en moyenne. Expliquez ces trois observations, proposez deux corrections pour un fichier `job.yaml` réel, et dites quel test du lab les couvre.
:::

::: sol
`failover` prend le moins cher **parmi les pools qui répondent maintenant**. Quand les pools spot refusent, il atterrit sur le pool à la demande à 10 u, qui n'est jamais préempté ; rien ne le ramène vers le spot. D'où le coût (+47,5 %) et la fin plus précoce : `failover` n'attend presque jamais de capacité et le pool à la demande ne subit pas de préemption.

Les nombreux déménagements ont une autre cause : la décision est reprise à chaque préemption, et le moins cher qui répond est souvent un spot d'un autre fournisseur (observé en journalisant les décisions du simulateur ; `scenarios.py` ne l'affiche pas).

Corrections : (1) retirer le pool à la demande de `any_of`, ou le placer en dernier dans une liste `ordered` ; (2) borner la durée sur le pool à la demande et réévaluer le placement périodiquement, ce que le lab ne fait pas.

Le test `test_on_demand_trap_costs_more_than_waiting_for_spot` du lab 13.1 reproduit le mécanisme sur un cas minimal.
:::

::: exo
[Exercice 7 · ★★ — Étaler ou non ?]{.tag} Comparez le coût d'un envoi unique, d'un envoi réparti en deux mois égaux et d'un envoi sur trois mois, avec les tarifs AWS du chapitre 4 (franchise de 100 Go par mois, 0,09 USD par Go jusqu'à 10 240 Go, puis 0,085), pour (a) 1 000 Go et (b) 20 000 Go. (c) À partir de quel volume l'étalement sur deux mois cesse-t-il d'être avantageux ?
:::

::: sol
(a) En un mois : $900 \times 0{,}09 = 81{,}00$ USD. En deux mois de 500 Go : $2 \times 400 \times 0{,}09 = 72{,}00$. En trois mois de 333,3 Go : $3 \times 233{,}3 \times 0{,}09 = 63{,}00$. L'étalement gagne : la franchise est regagnée chaque mois.

(b) En un mois :

$$10\,240 \times 0{,}09 + 9\,660 \times 0{,}085 = 1\,742{,}70\ \text{USD}$$

En deux mois de 10 000 Go : $2 \times 9\,900 \times 0{,}09 = 1\,782{,}00$. En trois mois : 1 773,00. L'étalement perd : la deuxième tranche à 0,085 n'est plus atteinte.

(c) Les coûts s'égalent là où $F(x) = 2F(x/2)$. Une recherche numérique avec `split_cost` du lab donne environ **12 140 Go**, où les deux plans coûtent 1 074,60 USD. Au-delà, l'étalement sur deux mois coûte plus.
:::

::: exo
[Exercice 8 · ★★★ — Déménager 40 To pour 0,8 u de moins ?]{.tag} Un job de 32 GPU doit faire 200 h de calcul utile. Un site B est moins cher de 0,8 u par GPU-heure **utile** que le site A où vivent les données : 40 To (40 000 Go) plus un checkpoint de 112 Go. La sortie coûte 0,09 u par Go, le lien soutient 10 Gbit/s à 80 % et une heure de retard vaut 100 u. (a) Faut-il déménager ? (b) À quel tarif de sortie la décision bascule-t-elle ? (c) Et si une heure de retard vaut 400 u ? (d) Que changeriez-vous dans l'architecture ?
:::

::: sol
(a) L'économie vaut $32 \times 200 \times 0{,}8 = 5\,120$ u. Le déplacement coûte $40\,112 \times 0{,}09 = 3\,610$ u de sortie, et la copie dure $40\,112 \times 8 / 8 / 3600 = 11{,}1$ h, valorisées $1\,114$ u. Le gain net est de **+396 u** : marginal, et sensible à toutes les hypothèses.

(b) La décision bascule quand le tarif de sortie atteint $(5120 - 1114)/40\,112 = $ **0,0999 u par Go**, c'est-à-dire presque le tarif de 0,09 u : une erreur de 11 % sur le tarif suffit.

(c) À 400 u par heure, le temps vaut 4 457 u et le gain net passe à **−2 947 u** : ne déménagez pas.

(d) Le vrai levier est de ne pas payer la sortie : un stockage objet à sortie gratuite pour les données fait passer le gain à $5\,120 - 1\,114 = +4\,006$ u. À défaut, il vaut mieux lancer le job là où vivent les données.
:::

::: exo
[Exercice 9 · ★★ — Un all-reduce entre deux sites]{.tag} Un modèle de 13 milliards de paramètres a des gradients de $2 \times 13 \cdot 10^9 = 26$ Go. Comparez le temps du all-reduce en anneau, $2\,\frac{p-1}{p}\,\frac{n}{B}$, (a) sur 64 GPU d'un site à 40 Go/s, (b) entre deux sites ($p = 2$) reliés à 5 Gbit/s à 80 % d'efficacité. Quelle part d'une étape de 8 s de calcul la communication occupe-t-elle dans chaque cas, sans recouvrement ?
:::

::: sol
(a) $2 \times \frac{63}{64} \times 26/40 = $ **1,28 s**.

(b) Le lien utile vaut $5 \times 0{,}8 / 8 = 0{,}5$ Go/s. Avec $p = 2$ : $2 \times \frac{1}{2} \times 26/0{,}5 = $ **52 s**, soit 40,6 fois plus que dans le cas (a).

Part de la communication dans l'étape : $1{,}28/(8+1{,}28) = 13{,}8\ \%$ dans un site, $52/(8+52) = 86{,}7\ \%$ entre deux sites. Entre sites, les GPU passent près de neuf dixièmes du temps à attendre : le job ne se coupe pas.
:::

::: exo
[Exercice 10 · ★ — Un quota en vCPU]{.tag} Vous voulez 16 nœuds de 8 GPU, 25 % à la demande et 75 % en spot. Le type d'instance expose 192 vCPU par nœud (valeur d'énoncé). (a) Quels quotas faut-il demander ? (b) Le quota spot accordé est de 2 000 vCPU : combien de nœuds spot peuvent démarrer, et que faites-vous des autres ?
:::

::: sol
(a) Les quotas se comptent en vCPU, séparément pour le à-la-demande et le spot (chapitre 6). Il faut $4 \times 192 = 768$ vCPU à la demande et $12 \times 192 = 2\,304$ vCPU en spot, soit 3 072 vCPU au total.

(b) $\lfloor 2000 / 192 \rfloor = 10$ nœuds spot, soit 1 920 vCPU. Les 2 nœuds restants se repositionnent ailleurs : à la demande si le quota le permet, sur un autre lieu ou un autre fournisseur, ou en attendant un relèvement du quota. C'est le rôle de la bascule de l'article SkyPilot : une allocation échoue par manque de capacité **ou** de quota.
:::

::: exo
[Exercice 11 · ★★★ — Résidence des données]{.tag} Le jeu de données du job de `job.yaml` ne peut pas quitter l'UE. Appliquez la règle de résidence du lab 13.2 (`--allow-prefix aws/eu- --allow-prefix gcp/europe-`) à `job.yaml` puis à `job-eu.yaml`. Interprétez les messages, listez ce que l'outil ne vérifie pas, et dites ce qui change pour la bascule et pour le coût.
:::

::: sol
Sortie capturée sur le bac à sable de l'auteur le 24 octobre 2026 :

~~~text
job.yaml: E6 error: aws/us-east-1 is outside the allowed locations ['aws/eu-', 'gcp/europe-']
job.yaml: E6 error: gcp/us-central1 is outside the allowed locations ['aws/eu-', 'gcp/europe-']
job.yaml: W4 warning: k8s/eu-gpu-cluster: a context name does not prove where the cluster runs
job.yaml: 2 error(s), 1 warning(s)
job-eu.yaml: W4 warning: k8s/eu-gpu-cluster: a context name does not prove where the cluster runs
job-eu.yaml: 0 error(s), 1 warning(s)
~~~

Deux lieux sont hors liste ; `job-eu.yaml` les remplace par `aws/eu-west-3` et `gcp/europe-west4`. L'outil **ne vérifie pas** : la région réelle du contexte Kubernetes (W4 le dit), la juridiction et l'emplacement du bucket de checkpoint (un bucket R2 n'a pas de préfixe de région dans ce YAML), ni les sauvegardes et les journaux.

Pour la bascule, les candidats restent trois, mais la liste est plus étroite : la probabilité de trouver de la capacité baisse, et la bascule vers un lieu hors UE est interdite même si elle serait moins chère. Le coût attendu se mesure en relançant le simulateur du lab 13.1 avec seulement les pools autorisés.
:::

::: exo
[Exercice 12 · ★★★ — Tempête de bascule]{.tag} Une région tombe et 40 jobs, qui utilisent tous le même jeu de données de 20 To (20 000 Go) et ont chacun un checkpoint de 112 Go, repartent en même temps chez un fournisseur B, sur une liaison partagée de 10 Gbit/s à 80 %. Avec les tarifs AWS du chapitre 4 (franchise intacte), calculez pour (a) une copie du jeu de données par job, (b) une copie partagée du jeu de données et un checkpoint par job, (c) les seuls checkpoints, le jeu étant déjà répliqué : le volume, la facture et la durée. Proposez une architecture.
:::

::: sol
(a) $40 \times (112 + 20\,000) = 804\,480$ Go. Avec les quatre tranches du tableau, $921{,}6 + 3\,481{,}6 + 7\,168 + 32\,539 = $ **44 110 USD**, et 223,5 h sur la liaison partagée.

(b) $20\,000 + 40 \times 112 = 24\,480$ Go : **2 124 USD** (2 123,50) et 6,8 h.

(c) $40 \times 112 = 4\,480$ Go : **394 USD** et 1,24 h.

Architecture : réplication continue du jeu de données vers un stockage neutre à sortie gratuite, ce qui amène le cas (c) ; ordre de reprise par priorité pour étaler les 1,24 h de copie ; plafond du nombre de transferts simultanés ; vérification que les images sont publiées chez le fournisseur B ; et un exercice de bascule régulier, comme un jeu de chaos. La liaison partagée est le goulot : la quarantième reprise attend la fin des 39 autres copies si on les sérialise.
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux classer une offre de calcul et la comparer à une autre.** Preuve : deux fiches de douze lignes (section 1.5), datées et sourcées, pour deux fournisseurs de votre choix.
-   **Je peux dire à partir de quelle remise le spot bat la demande.** Preuve : l'exercice 4 refait avec des taux d'interruption que vous avez mesurés.
-   **Je peux relire un job SkyPilot et dire ce que l'outil ne vérifie pas.** Preuve : la sortie de `verify.sh` du lab 13.2 et une correction de `bad-job.yaml`.
-   **Je peux chiffrer un déménagement de données.** Preuve : le calculateur testé du lab 13.3 appliqué à vos tarifs lus le jour même.
-   **Je peux décider d'une bascule avec des chiffres.** Preuve : le tableau du lab 13.1 et le seuil de l'exemple 5.2 recalculé pour vos paramètres.
-   **Je peux expliquer pourquoi un entraînement ne se coupe pas entre sites.** Preuve : l'exercice 9 refait avec vos débits mesurés.
-   **Je peux choisir une voie d'accès à un centre public.** Preuve : la conversion de l'exemple 7.1 pour une demande réelle, avec les appels relus.
-   **Je peux écrire une politique de gouvernance exécutable.** Preuve : une règle ajoutée à `policy_check.py` avec son test, lancée en intégration continue.

Trois questions d'entretien à pouvoir traiter oralement en deux minutes chacune.

1.  *Nous voulons utiliser du spot sur trois fournisseurs. Qu'est-ce qui peut mal tourner ?* Réponse-type : le préavis (0 à 120 s) ne suffit pas à sauvegarder, donc il faut un checkpoint périodique sur un stockage qui survit à la VM ; le piège du pool à la demande qui ne rend jamais la main ; les quotas, qui se comptent en vCPU et séparément pour le spot ; les sorties de données à chaque bascule ; la mesure des taux d'interruption réels.
2.  *Un jeu de données de 40 To est chez le fournisseur A, le fournisseur B est 20 % moins cher. Déménagez-vous ?* Réponse-type : calculer l'économie sur les heures utiles, la comparer au coût de sortie par tranches et au temps de copie valorisé ; vérifier la sensibilité au tarif et à la valeur du temps ; envisager un stockage neutre à sortie gratuite ou de lancer le job où vivent les données ; ne pas compter sur la sortie gratuite de départ, qui suppose de quitter le fournisseur.
3.  *Comment garder une flotte multi-fournisseurs sous contrôle ?* Réponse-type : étiquettes obligatoires (équipe, projet, responsable), politique de job exécutable en intégration continue, arrêt automatique avec suppression, coûts normalisés dans un format commun, revue périodique de l'inventaire, des orphelins et des quotas.

## Lectures et références {#refs}

Sauf mention contraire, les pages ci-dessous ont été lues le 24 octobre 2026 ; ce sont des pages vivantes, relisez-les avant de décider.

-   Yang et al. *SkyPilot: An Intercloud Broker for Sky Computing*. NSDI 2023. [usenix.org](https://www.usenix.org/conference/nsdi23/presentation/yang-zongheng), [texte](https://www.usenix.org/system/files/nsdi23-yang-zongheng.pdf) : §4 pour l'optimiseur et la bascule, §5.1 pour l'exemple de sortie de données du chapitre 4, §5.2 pour la bascule entre régions.
-   SkyPilot. *YAML specification*. Lue le 24 octobre 2026. [docs.skypilot.co](https://docs.skypilot.co/en/latest/reference/yaml-spec.html) : `any_of`, `ordered`, `job_recovery`, `file_mounts`, `autostop`, `labels`, `network_tier`.
-   SkyPilot. *Managed Jobs*. Lue le 24 octobre 2026. [docs.skypilot.co](https://docs.skypilot.co/en/latest/examples/managed-jobs.html) : reprise après préemption, checkpoints sur stockage persistant, jobs sur spot.
-   AWS. *Spot Instance interruption notices*. [docs.aws.amazon.com](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html) : le préavis de deux minutes, au mieux.
-   Google Cloud. *Spot VMs*. [cloud.google.com](https://cloud.google.com/compute/docs/instances/spot) : la durée de préavis configurable et la période d'arrêt au mieux.
-   Microsoft. *Azure Spot Virtual Machines*. [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/virtual-machines/spot-vms) : les événements planifiés, jusqu'à 30 secondes.
-   AWS. *Capacity Blocks for ML*. [docs.aws.amazon.com](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-capacity-blocks.html) : réservation planifiée de GPU, limites et annulation.
-   AWS. *Liste de prix AWSDataTransfer* (API de prix). [pricing.us-east-1.amazonaws.com](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSDataTransfer/current/index.json) : tarifs de sortie lus pour le lab 13.3.
-   Microsoft. *Azure Retail Prices API*. [prices.azure.com](https://prices.azure.com/api/retail/prices) : tarifs de bande passante de la région `westeurope`.
-   Cloudflare. *R2 pricing*. [developers.cloudflare.com](https://developers.cloudflare.com/r2/pricing/) : stockage et absence de frais de sortie.
-   Kueue. *MultiKueue*. [kueue.sigs.k8s.io](https://kueue.sigs.k8s.io/docs/concepts/multikueue/) : manager, workers, flux de dispatch et limites.
-   GENCI. *eDARI*. [edari.fr](https://www.edari.fr/) : seuils d'accès, équivalences de GPU, conditions et appels en cours.
-   IDRIS. *Jean Zay : matériel*. [idris.fr](http://www.idris.fr/docs/jean-zay/jean-zay/jean-zay-hardware) : partitions GPU et réseaux d'interconnexion.
-   EuroHPC JU. *AI Factories access calls*. [eurohpc-ju.europa.eu](https://eurohpc-ju.europa.eu/ai-factories/ai-factories-access-calls_en) : les trois modes d'accès aux usines d'IA.
-   FinOps Foundation. *What is FOCUS?* [focus.finops.org](https://focus.finops.org/what-is-focus/) : le format de données de facturation du chapitre 8.

## Sources et portée {#sources}

### Documenté {#documente}

Les préavis de préemption, les limites des Capacity Blocks, les modèles de provisionnement de Google Cloud, les champs du YAML de SkyPilot et le comportement de la reprise, l'exemple chiffré de sortie de données et les résultats de bascule de l'article SkyPilot, les statuts et le flux de MultiKueue, les alias de providers Terraform, la fédération d'identité de Google Cloud, les quotas d'instances en vCPU d'AWS, l'activation des étiquettes d'allocation, les conditions des sorties gratuites d'AWS et de Google Cloud, les seuils d'eDARI, le matériel de Jean Zay et les modes d'accès d'EuroHPC, d'ACCESS et du pilote NAIRR ont été relus à leur source le 24 octobre 2026. Les tarifs du lab 13.3 viennent de l'API de prix d'AWS (publications du 16 septembre 2026 pour le transfert et du 15 octobre 2026 pour le stockage S3), de l'API de prix d'Azure et des pages de Cloudflare R2 et de Backblaze B2. Les calculs des exemples et des corrigés ont été refaits avec le code des labs.

### Recommandé {#recommande}

Le score de placement du chapitre 5, la valeur $\lambda$ du temps comme paramètre d'activité, la garde d'échéance, la règle « un job égale un site », le stockage neutre à sortie gratuite pour les checkpoints, les règles E1 à E6 et W1 à W4 de `policy_check.py` et leur choix d'étiquettes sont des choix de ce parcours, pas des normes. Les trois politiques naïves du lab 13.1 sont des cas d'école volontairement simples.

### À vérifier {#a-verifier}

Tous les tarifs, franchises et dates d'appel cités changent : relisez la page du fournisseur le jour de la décision. Les tarifs de transfert de Google Cloud ne sont pas cités (tableau de la page aplati). Les règles exactes et les dates d'application du règlement européen sur les données (*Data Act*), notamment la fin des frais de changement de fournisseur, n'ont pas été relues à la source (EUR-Lex et le site de la Commission refusent l'accès depuis le bac à sable) ; le contrat de chaque fournisseur fait foi. L'annonce d'environ 70 % d'économie de la documentation SkyPilot est une affirmation du fournisseur de l'outil. Les offres et capacités des GPU clouds et des offres européennes, la liste des fournisseurs européens, les liaisons privées et leurs tarifs, la valeur de la préemption sur des GPU récents et l'état des appels d'EuroHPC, d'eDARI, d'ACCESS et du NAIRR sont instables et non documentés ici. Les règles d'installation d'outils et de réseau d'un centre public précis ne sont pas décrites.

### Mesuré dans le bac à sable, pas vérifié sur un cloud {#mesure-bac-a-sable}

SkyPilot 0.14.1 rejette `type:` avec `mode: MOUNT`, les fautes de frappe et les mauvais types, et accepte un nom de stratégie `job_recovery` invalide (observation du 24 octobre 2026). Lu dans le code de SkyPilot 0.14.1 sans l'exécuter : le spot sur un contexte Kubernetes exige une étiquette de nœud. Le job `job.yaml` n'a jamais été lancé sur un compte cloud ni sur un cluster Kubernetes. Les trois politiques et le scénario du lab 13.1 sont synthétiques, tout comme les taux d'interruption, de disponibilité et le tarif de sortie de 0,09 u par Go de ce lab.

### Hors périmètre {#hors-perimetre}

L'entraînement distribué entre fournisseurs, la négociation des contrats et le modèle de coût total (module 15), la sécurité d'une plateforme partagée (module 16), le provisionnement par Terraform en détail (module 6), la performance de NCCL sur chaque interconnexion (module 7), le droit des données et les certifications.
