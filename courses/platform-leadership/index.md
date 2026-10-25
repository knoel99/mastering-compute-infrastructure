---
title: "Plateforme interne, sécurité, production et leadership"
subtitle: "Module 16 · Phase 5 · 30,5 h"
description: "Transformer un cluster en plateforme que des chercheurs adoptent : mesure de l'adoption, sessions interactives, sécurité multi-locataire, astreinte et post-mortems, migrations, direction d'équipe, plan de contrôle fiable et livraison continue, entretien."
module:
  id: platform-leadership
  number: 16
  phase: 5
  hours: 30.5
  level: 3
prerequisites: [slurm, kubernetes-gpu, observability, finops-capacity, fault-tolerance]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs vérifiés dans le bac à sable (données synthétiques ou fictives, étiquetées)", class: verified}
labs:
  - {id: rfc-template, kind: sandbox}
  - {id: incident-review, kind: sandbox}
  - {id: design-interview, kind: sandbox}
  - {id: quorum-drill, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** vous avez un cluster qui fonctionne. Comment en faire une **plateforme** que des chercheurs choisissent d'utiliser, que l'on peut exploiter à trois sans s'épuiser, qui résiste à un incident à deux heures du matin et dont vous pouvez défendre les choix devant un directeur ou un jury d'entretien ?

Les modules précédents donnent les briques (ordonnanceur, réseau, stockage, observabilité). Celui-ci traite ce qui reste quand les briques tournent : le produit, la sécurité d'un matériel partagé, la fiabilité en production, les migrations, l'équipe, la manière de décider par écrit, puis le plan de contrôle de la plateforme et la livraison de ses changements. Il s'appuie sur le [projet 6](../../projects/capstone-rfc/index.html), dont il donne les outils d'écriture et de revue.

::: key
[Règle de ce module]{.tag} Une décision de plateforme n'est solide que si elle est écrite, chiffrée, contestable et réversible : on peut dire quel chiffre la fonde, quelle alternative on a écartée et pourquoi, et quel signal la ferait rouvrir. Tout ce que ce module vous fait écrire est donc vérifié mécaniquement avant d'être relu par une personne.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 30,5 h, dont environ 11 h de lecture, 7,5 h de labs et 12 h d'exercices (estimations de l'auteur, non mesurées auprès d'un lecteur) |
| Niveau d'entrée | 3 : avoir suivi les phases 2 à 4 du parcours, ou avoir exploité un cluster ou une plateforme de calcul |
| Prérequis | [Module 5 — Slurm et exploitation d'un cluster HPC](../slurm/index.html), [Module 12 — Kubernetes pour l'IA : GPU, files d'attente et gang scheduling](../kubernetes-gpu/index.html), [Module 14 — Observabilité et fiabilité d'une flotte GPU](../observability/index.html), [Module 15 — FinOps, capacité, énergie et achats de calcul](../finops-capacity/index.html), [Module 10 — Pannes, checkpointing et reprise automatique](../fault-tolerance/index.html) |
| Pour qui | Cœur : écrire des décisions, gérer des incidents et diriger une équipe font partie du métier, au-delà de l'outillage. |
| Livrable | un ADR vérifié, un post-mortem cohérent avec son journal, un dimensionnement chiffré et défendu à l'oral |
| Environnement | un portable Linux avec Python, **sans GPU** ; aucun cloud ; les données des labs sont synthétiques ou fictives et étiquetées |
| Projets liés | [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html) |
### Ce que vous saurez vérifier {#acquis}

- Choisir quatre mesures d'adoption d'une plateforme et dire pourquoi une utilisation GPU élevée n'est pas un succès en soi (chapitre 1).
- Dimensionner des sessions interactives avec la loi de Little et décider entre un GPU entier, MIG et le partage par tranches de temps (chapitre 2).
- Dresser un modèle de menaces multi-locataire et nommer ce que chaque mécanisme isole, ou n'isole pas (chapitre 3).
- Calculer un budget d'erreur et la taille d'équipe qu'exige une astreinte, et écrire un post-mortem sans blâme dont les chiffres tiennent (chapitre 4).
- Planifier une migration par cohortes avec des critères d'entrée, de sortie et de retour arrière (chapitre 5).
- Fixer un budget de travail d'exploitation pour une petite équipe (chapitre 6).
- Conduire un exercice de conception d'entretien avec un calcul et ses hypothèses dites, et préparer une question de négociation (chapitre 8).
- Calculer la probabilité qu'un cluster de consensus garde son quorum selon le nombre et le placement de ses membres, conduire un exercice de restauration mesuré et livrer un changement d'infrastructure par canaris (chapitre 9).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 5 — Production et leadership** (semaines 45-50) : opérer en production, décider, négocier, diriger et passer l'entretien.
-   **S'appuie sur** : [module 5 — Slurm et exploitation d'un cluster HPC](../slurm/index.html), [module 12 — Kubernetes pour l'IA : GPU, files d'attente et gang scheduling](../kubernetes-gpu/index.html), [module 14 — Observabilité et fiabilité d'une flotte GPU](../observability/index.html), [module 15 — FinOps, capacité, énergie et achats de calcul](../finops-capacity/index.html), [module 10 — Pannes, checkpointing et reprise automatique](../fault-tolerance/index.html).
-   **Projets qui s'en servent** : [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html).
-   **Compétences demandées dans les offres d'emploi et travaillées ici** : Checkpoint, tolérance aux pannes, Planification de capacité, Sécurité, conformité, Astreinte, fiabilité (SRE), Leadership, management, Systèmes distribués, Slurm, Kubernetes, Conteneurs, Journaux, traces, Expérience d'entraînement ML, CI/CD, automatisation (voir [l'analyse du marché](../../market/index.html#couverture)).
<!-- /gen:place -->

### Plan de séances {#seances}

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 3 h | 2 | Chapitre 1 : la plateforme comme produit, quatre mesures d'adoption | exercice 3 |
| 2 | 3 h | 2 | Chapitre 2 : sessions interactives, MIG et partage de GPU | exercice 6 |
| 3 | 3 h | 2 | Chapitre 3 : sécurité d'une plateforme GPU partagée | exercice 8 |
| 4 | 3 h | 2 | Chapitre 4, première moitié (4.1 à 4.3) : SLO, budget d'erreur, astreinte, jalons d'un incident | exercices 1, 2 et 4, lab 16.2 (étapes 1 à 3) |
| 5 | 3 h | 3 | Chapitre 4, seconde moitié (4.4 et 4.5) : post-mortem, ADR et RFC | lab 16.2 (étapes 4 et 5), exercice 11 |
| 6 | 3 h | 3 | Chapitre 5 : évolutions et migrations | exercice 7, lab 16.1 (étapes 1 à 3) |
| 7 | 3 h | 3 | Chapitre 6 : diriger une petite équipe d'infrastructure | exercice 5, lab 16.1 (étapes 4 et 5) |
| 8 | 3 h | 3 | Chapitre 7 : contribuer et se rendre visible, puis chapitre 8 (début) | exercice 10 |
| 9 | 2 h | 3 | Chapitre 8 : exercice de conception | lab 16.3 (étapes 1 à 3) |
| 10 | 2.5 h | 3 | Chapitre 9 : plan de contrôle, consensus, haute disponibilité et livraison continue | lab 16.4, exercices 12 et 13 |
| 11 | 2 h | 3 | Synthèse et checkpoint de sortie | lab 16.3 (étapes 4 et 5), exercice 9, checkpoint |

<!-- gen:travailler -->
### Comment travailler ce module {#travailler}

Le parcours s'adresse à plusieurs profils d'entrée, décrits dans le [point de départ](../../profile/index.html). Le tableau donne la priorité conseillée pour ce module ; les questions de positionnement (section 0.1) la confirment ou la corrigent.

| Profil d'entrée | Priorité | Ce que cela veut dire ici |
|---|---|---|
| Ingénieur plateforme, SRE ou DevOps | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Administrateur ou ingénieur HPC | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Ingénieur ML ou chercheur | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Développeur logiciel ou systèmes | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Étudiant ou personne en reconversion | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |

**À ne pas survoler.** Le RFC et la revue d'incident servent au projet 6, quel que soit votre profil.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le checkpoint de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Trois questions pour situer votre niveau. Répondez sans chercher, puis ouvrez les réponses.

1.  Une plateforme de calcul affiche 98 % d'utilisation de ses GPU. Est-ce forcément un succès ?
2.  Un chercheur lance un notebook sur un GPU et l'oublie un week-end. Quelle mesure le détecte et quelle règle l'évite ?
3.  Pourquoi un incident de deux heures mérite-t-il un document écrit « sans blâme » plutôt qu'une réunion d'explications ?

::: sol
**Réponses.**

1.  Non. Une utilisation élevée peut venir d'une file d'attente interminable (les chercheurs attendent), de GPU occupés par des jobs bloqués ou inactifs (utilisation affichée mais aucun travail utile) ou d'une capacité mal dimensionnée. Il faut lire en plus l'attente par classe de charge et le *goodput*, la part du temps de calcul conservé (chapitre 1).

2.  L'alerte d'allocation inactive du projet 5 (utilisation proche de zéro pendant quinze minutes sur une allocation) la détecte ; une expiration automatique des sessions interactives l'évite (chapitre 2).

3.  Le SRE Book de Google le dit ainsi : un post-mortem sans blâme « assumes that everyone involved in an incident had good intentions and did the right thing with the information they had ». Si l'on punit, on cache les incidents ; si l'on cherche les causes du **système**, on peut les corriger (chapitre 4).
:::

## 1. La plateforme comme produit {#ch1}

Un cluster est une machine ; une plateforme est un **service que des gens choisissent ou subissent**. La différence se voit au premier jour d'un nouveau chercheur : combien de temps avant qu'il lance un premier job, et combien de messages à l'équipe pour y arriver ?

### 1.1. Qui sont vos utilisateurs

Dans un groupe de recherche, quatre profils reviennent : le chercheur qui développe en interactif, celui qui lance des évaluations par rafales, celui qui règle finement un modèle pendant quelques heures, et le petit nombre qui conduit un pré-entraînement de plusieurs jours. Leurs besoins s'opposent : le premier veut une réponse en minutes, le dernier veut une longue réservation fiable. Une plateforme qui n'a qu'une file pour tous les contente mal chacun.

Interrogez-les. Trois entretiens de vingt minutes avec des utilisateurs réels vous apprennent souvent plus qu'un tableau de bord : ce qui les bloque, ce qu'ils contournent, ce qu'ils copient d'un voisin faute de documentation.

### 1.2. Quatre mesures, pas quarante

Quatre mesures suffisent pour piloter, et chacune se calcule à partir des données que la plateforme produit déjà (comptabilité de l'ordonnanceur, métriques) :

1.  le **délai avant le premier job** d'un nouveau membre ;
2.  l'**attente au 90e centile** de chaque classe de charge, comparée à son objectif ;
3.  le ***goodput*** : la part du temps réservé qui sert à calculer ce qui sera conservé, au sens du [module 10, §2.1](../fault-tolerance/index.html#ch2) ;
4.  le **coût par GPU-heure utile**, et non par GPU-heure facturée.

::: ex
[Exemple 1.1 — Mesurer une classe de charge avec la loi de Little]{.tag} Dans le cahier des charges fictif du projet 6, 650 sessions interactives de 1,2 heure de travail arrivent chaque mois de 730 heures. Le taux d'arrivée est de 650 / 730 = 0,890 session par heure.

La loi de Little ([module 1, §7.2](../linux-systems/index.html#mesurer-un-disque-avec-fio-la-loi-de-little) : taux d'arrivée multiplié par durée moyenne) donne 0,890 × 1,2 = **1,07 session simultanée** en moyenne. Quatre GPU réservés l'absorbent à 26,7 % d'utilisation, avec une attente moyenne de 37 secondes (file M/M/c et formule d'Erlang C : [module 15, chapitre 2](../finops-capacity/index.html#ch2)).

Le modèle du projet 6 ajoute le surcoût des pannes et des reprises à la durée de service et publie **26,9 %** et **38 secondes**. À vue d'œil le pool est « sous-utilisé », et pourtant l'attente est justement dans l'objectif.

Une utilisation basse est ici le **prix d'une latence basse** : avec 2 GPU, l'attente au 90e centile monterait à 1,72 heure selon le projet 6 (1,69 heure sans le surcoût des pannes). Données fictives. Le modèle suppose des arrivées indépendantes et des durées exponentielles : il peut être optimiste pour des sessions à queue lourde (le notebook oublié), donc comparez-le à l'attente mesurée. La méthode est celle à appliquer à vos mesures.
:::

### 1.3. Mesurer sans se tromper de cible

Une mesure érigée en objectif cesse d'être une bonne mesure : si l'on récompense l'utilisation des GPU, les gens lanceront des jobs inutiles pour la faire monter. Associez toujours deux mesures qui se tirent dans des sens opposés (utilisation et attente, par exemple) et publiez-les ensemble.

### 1.4. Réduire le coût d'adoption

Les plateformes que l'on adopte ont un « chemin tout tracé » : un modèle de job qui marche, des valeurs par défaut sûres, une documentation courte et testée, un canal de support où l'on obtient une réponse. Écrivez le modèle de job avant le cinquantième utilisateur ; chaque chercheur qui copie le script d'un collègue copie aussi ses défauts.

::: recap
[Points clés]{.tag}

-   Une plateforme est un service : le premier job d'un nouveau membre est le test d'adoption.
-   Quatre mesures : délai avant le premier job, attente au 90e centile par classe, goodput, coût par GPU-heure utile.
-   La loi de Little dimensionne les classes interactives ; une utilisation basse peut être le prix d'une attente basse.
-   Associez deux mesures opposées pour qu'aucune ne devienne un objectif trompeur.
-   Un modèle de job testé réduit plus le coût d'adoption que n'importe quelle formation.
:::

## 2. Sessions interactives et environnements de développement {#ch2}

Le développement interactif est la classe qui exige la latence la plus basse et gaspille le plus : un notebook oublié garde un GPU. Deux familles d'outils l'organisent, et trois façons de partager un GPU se comparent.

### 2.1. Un portail HPC ou un hub multi-utilisateur

*Open OnDemand* se configure pour que des « interactive apps that run on compute nodes » soient lancées depuis un navigateur ([documentation](https://osc.github.io/ood-documentation/latest/how-tos/app-development/interactive/setup.html), version 4.2 lue le 2026-10-24), par des adaptateurs vers Slurm, LSF, PBS Professional, Grid Engine ou Kubernetes, entre autres ([liste des adaptateurs](https://osc.github.io/ood-documentation/latest/installation/resource-manager/slurm.html)) : une session interactive y est donc un job du gestionnaire de ressources. *JupyterHub*, de son côté, est « a multi-user Hub that spawns, manages, and proxies » des serveurs Jupyter mono-utilisateur, lancés par des *spawners* et déployables sur Kubernetes ([documentation](https://jupyterhub.readthedocs.io/en/stable/)).

Le choix dépend de l'ordonnanceur de la plateforme : si les sessions doivent entrer dans les files de Slurm, un portail qui lance des jobs est naturel ; si la plateforme est sur Kubernetes, un hub qui lance des pods l'est. Comme Open OnDemand dispose aussi d'un adaptateur Kubernetes, ce n'est pas une impossibilité technique qui tranche, mais le coût d'exploitation d'un composant de plus. Dans les deux cas, la question importante est la même : **qui arrête la session ?**

### 2.2. Trois façons de partager un GPU

Le [module 6, §9.3](../provisioning/index.html#partager-un-gpu-mig-time-slicing-mps-et-vgpu) est la référence du parcours sur les garanties d'un GPU partagé (MIG, *time-slicing*, MPS, vGPU), et le [module 12, §2.4 et 2.5](../kubernetes-gpu/index.html#ch2) en donne la configuration sous Kubernetes. On n'en retient ici que le choix et le dimensionnement pour des sessions interactives. Pour les machines virtuelles à GPU (passthrough VFIO, vGPU, KubeVirt) et leur recette, voir le [chapitre 9 du module 6](../provisioning/index.html#ch9).

Un GPU entier par session est simple et isolé, mais gaspille : une session de développement en occupe rarement la capacité. Deux mécanismes permettent de le partager.

La *MIG* (*Multi-Instance GPU*, à partir de l'architecture Ampere) partitionne un GPU en « up to seven separate GPU Instances », avec « separate and isolated paths through the entire memory system » et une isolation des pannes ([guide MIG](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/introduction.html)). Le partage par tranches de temps (*time-slicing*) fait alterner les charges sur un GPU surbooké ; la documentation du GPU Operator précise que, contrairement à MIG, « there is no memory or fault-isolation between replicas » ([partage de GPU](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html)).

| Mode | Isolation mémoire et pannes | Souplesse | Convient à |
|---|---|---|---|
| GPU entier | totale | aucune | entraînement, évaluation lourde |
| MIG | oui, au niveau matériel | 7 instances au plus par GPU, profils fixes | développement interactif de plusieurs utilisateurs non liés |
| Tranches de temps | non | nombre de partages choisi librement | charges de confiance mutuelle, démonstrations |

### 2.3. Les règles qui évitent le gaspillage

Trois règles suffisent : une **durée maximale** par session interactive, un **arrêt automatique après inactivité**, et une **alerte d'allocation inactive** pour ce qui échappe aux deux premières, comme l'alerte `GPUIdleAllocated` du [projet 5](../../projects/gpu-observability/index.html). Chacune est un compromis entre le confort de l'utilisateur et le coût : écrivez les valeurs dans une décision d'architecture (ADR, section 4.5), pas dans un message de messagerie.

::: ex
[Exemple 2.1 — Combien de sessions MIG pour 4 GPU ?]{.tag} Avec jusqu'à 7 instances par GPU, 4 GPU offrent au plus **28 sessions simultanées** (4 × 7). La demande moyenne de l'exemple 1.1 est de 1,07 session : la MIG n'est **pas nécessaire** pour la charge moyenne, qui tient sur 4 GPU entiers avec environ 2,5 % de probabilité d'attente. Elle ne se justifierait que si les pics, et non la moyenne, dépassaient 4 sessions simultanées de façon fréquente, ce que seule une mesure de l'attente réelle peut dire.
:::

::: recap
[Points clés]{.tag}

-   Open OnDemand lance des applications interactives comme des jobs ; JupyterHub lance des serveurs mono-utilisateur par des spawners.
-   Le vrai sujet est de savoir qui arrête la session : durée maximale, inactivité, alerte d'allocation inactive.
-   MIG isole mémoire et pannes, au plus sept instances par GPU ; le partage par tranches de temps n'isole ni l'un ni l'autre.
-   La loi de Little dit si le partage est utile avant de le mettre en place.
:::

## 3. Sécurité d'une plateforme GPU partagée {#ch3}

Un GPU partagé est un matériel que des personnes qui ne se connaissent pas utilisent en même temps. Ce chapitre ne remplace pas un cours de sécurité : il donne le **modèle de menaces** d'une plateforme de calcul et dit ce que chaque mécanisme protège réellement.

### 3.1. Qui est un locataire

La documentation de Kubernetes sur la [multi-location](https://kubernetes.io/docs/concepts/security/multi-tenancy/) le dit sans détour : « there is no single definition for a "tenant" ». Dans une plateforme de recherche, un locataire est typiquement une équipe, et parfois un utilisateur. Décidez-le **avant** de concevoir l'isolation : tout le reste (quotas, réseaux, secrets, audit) se rattache à cette unité.

### 3.2. Identité et moindre privilège

Chaque job doit s'exécuter avec l'identité de la personne ou de l'équipe qui l'a lancé, pas avec celle d'un compte de service partagé : sinon la comptabilité, l'audit et les quotas mentent. Le moindre privilège s'applique aux jetons d'accès au stockage (courte durée de vie, portée limitée) comme aux droits sur le cluster. Un compte de service partagé est le raccourci le plus tentant et le plus coûteux à défaire.

### 3.3. Isolation

Les conteneurs partagent le noyau de la machine : ils isolent la **vue** et limitent la **consommation** (module 1), ils ne constituent pas une barrière de sécurité de même force qu'une machine virtuelle. Kubernetes définit trois profils de sécurité de pods, *Privileged*, *Baseline* et *Restricted* ([Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)) : partez de *Restricted* pour les jobs des utilisateurs et n'ouvrez que ce qu'un cas précis exige (accès au GPU, réseau d'interconnexion). Pour le GPU lui-même, retenez la distinction du chapitre 2 : MIG isole mémoire et pannes, le partage par tranches de temps ne le fait pas.

Quand la frontière entre locataires est une machine virtuelle, c'est l'IOMMU qui empêche un GPU confié à un invité d'écrire dans la mémoire de l'hôte, et le groupe IOMMU est l'unité que l'on confie à un invité. Le [chapitre 9 du module 6](../provisioning/index.html#ch9) montre comment lire ces groupes et remettre un GPU en état entre deux locataires (§9.5).

Le réseau ne s'isole pas seul non plus : « By default, a pod is non-isolated for ingress; all inbound connections are allowed », et de même en sortie ([Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)). Une `NetworkPolicy` par locataire restreint ce trafic, à condition que le plugin réseau l'applique : « Creating a NetworkPolicy resource without a controller that implements it will have no effect ». Le [module 12, §8.2](../kubernetes-gpu/index.html#ch8) en donne un point de départ pour un entraînement.

### 3.4. Secrets

« Kubernetes Secrets are, by default, stored unencrypted in the API server's underlying data store » ([documentation des Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)). Un secret n'est donc pas protégé parce qu'il est dans un objet nommé `Secret` : activez le chiffrement au repos, limitez qui peut lire l'objet et ne mettez jamais un secret dans une image ni dans un dépôt.

::: ex
[Exemple 3.1 — Le base64 n'est pas du chiffrement]{.tag} Les valeurs d'un Secret Kubernetes sont encodées en base64 dans son manifeste. Exécuté :

~~~text
$ echo cGFzc3dvcmQ= | base64 -d
password
~~~

N'importe qui qui peut lire l'objet lit le secret. Le chiffrement au repos protège le disque du serveur de l'API ; le contrôle d'accès à l'objet protège sa lecture.
:::

### 3.5. Chaîne d'approvisionnement logicielle

Les utilisateurs lancent des images : une image modifiée est un chemin d'attaque et une source de non-reproductibilité. Épinglez par **empreinte** plutôt que par étiquette : d'après la documentation de Kubernetes, « Tags can be moved to point to different images, but digests are fixed » ([images](https://kubernetes.io/docs/concepts/containers/images/)). Construisez les images de base vous-même, dans un lieu contrôlé, et publiez la liste de celles que les utilisateurs ont le droit de lancer.

### 3.6. Audit

Sur Kubernetes, l'audit fournit « a security-relevant, chronological set of records » des appels à l'API ([audit](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)). Sur Slurm, la comptabilité (`sacct`) joue ce rôle pour les jobs. Dans les deux cas, conservez ces enregistrements assez longtemps pour reconstituer un incident, et assurez-vous qu'ils portent l'identité de la personne, pas celle d'un compte partagé.

::: recap
[Points clés]{.tag}

-   Décidez d'abord ce qu'est un locataire : équipe ou utilisateur.
-   Un job s'exécute avec l'identité de qui l'a lancé : sinon comptabilité, audit et quotas ne valent rien.
-   Les conteneurs isolent la vue, pas comme une machine virtuelle ; partez du profil Restricted.
-   Un pod accepte tout trafic tant qu'aucune `NetworkPolicy`, appliquée par le plugin réseau, ne le restreint.
-   Un Secret n'est pas chiffré par défaut ; base64 n'est pas du chiffrement.
-   Épinglez les images par empreinte, et gardez l'audit assez longtemps pour reconstituer un incident.
:::

## 4. Fiabilité de production {#ch4}

Opérer en production, c'est promettre un niveau de service, être joignable quand il se dégrade, et apprendre de chaque défaillance. Ce chapitre donne les outils et la limite humaine de cet exercice.

### 4.1. SLO et budget d'erreur

Le [module 14, §6.1](../observability/index.html#ch6) a défini SLI, SLO et **budget d'erreur** ; on les applique ici à la plateforme entière. Le SRE Book de Google rattache ce budget à l'objectif de niveau de service (*SLO*) : « the two teams jointly define a quarterly error budget based on the service's service level objective, or SLO » ([Embracing Risk](https://sre.google/sre-book/embracing-risk/)). Son exemple chiffré : un SLO de 99,999 % par trimestre donne un budget de 0,001 % ; un incident qui fait échouer 0,0002 % des requêtes en consomme 20 %.

::: ex
[Exemple 4.1 — Ce que coûte une heure d'incident]{.tag} Un SLO de disponibilité de 99,9 % sur 30 jours (43 200 minutes) autorise 0,001 × 43 200 = **43,2 minutes** de défaillance. Un SLO de 99,95 % n'en autorise que 21,6, un SLO de 99,99 % que 4,32. L'incident synthétique du lab 16.2 (un pré-entraînement sans progression pendant 1 h 58) dépasse à lui seul de 2,7 fois le budget de 99,9 % (118 / 43,2). Choisir un SLO, c'est donc choisir ce que l'on est prêt à investir pour ne pas dépasser ces minutes.
:::

### 4.2. Une astreinte soutenable

L'astreinte a une limite humaine que le SRE Book chiffre : investir « at least 50% of SRE time into engineering » et, sur le reste, ne pas passer plus de 25 % du temps total en astreinte (« no more than 25% can be spent on-call »), le dernier quart allant aux autres tâches d'exploitation.

Il en déduit que, pour une équipe sur un seul site assurant une rotation 24 heures sur 24 avec un titulaire et un second, « the minimum number of engineers needed for on-call duty from a single-site team is eight », et qu'une garde de 12 heures ne doit pas dépasser deux incidents ([Being On-Call](https://sre.google/sre-book/being-on-call/)).

::: ex
[Exemple 4.2 — Une équipe de trois ne tient pas une astreinte permanente]{.tag} Avec trois ingénieurs et une personne d'astreinte à la fois, en semaines alternées, chacun est d'astreinte un tiers du temps, soit **33,3 %**, au-dessus de la limite de 25 %. Pour qu'une seule personne d'astreinte à la fois ne dépasse pas 25 % du temps de chacun, il faut au moins 4 ingénieurs. C'est pourquoi la RFC de référence du projet 6 limite l'astreinte aux heures ouvrées et exige que chaque interruption soit absorbée **sans intervention humaine** : l'automatisation remplace des ingénieurs qu'on n'a pas.
:::

### 4.3. Gérer un incident

Un incident se gère avec des rôles et des jalons mesurés. Le lab 16.2 en donne la mécanique : un journal d'événements horodatés où l'on repère l'**anomalie** (début réel), la **détection** (premier signal humain ou automatique), l'**acquittement**, l'**atténuation** (le service repart) et la **résolution**. Les durées entre ces jalons sont les mesures à améliorer, en commençant par la plus longue. Sur beaucoup d'incidents c'est la détection, et détecter plus vite coûte souvent moins cher que réparer plus vite (règle de pratique, non chiffrée ici).

::: ex
[Exemple 4.3 — Lire les délais d'un incident synthétique]{.tag} Le journal inventé du lab 16.2 décrit un pré-entraînement de 128 GPU dont un rang s'arrête à 02:11. `timeline.py` donne :

~~~text
time to detect (anomaly to detection):   1 h 40 min
time to acknowledge (detection to ack):  4 min
time to mitigate (detection to fix):     18 min
anomaly to mitigation:                   1 h 58 min
anomaly to full resolution:              2 h 20 min
GPU-hours without progress (128 GPUs): 251.7
~~~

Une fois l'incident détecté, tout va vite : 4 minutes pour acquitter, 18 pour réparer. Les 100 minutes viennent de la **détection**, assurée par un chercheur parce que la supervision lisait une utilisation GPU rassurante et fausse. L'action utile est donc là, pas dans la vitesse de l'astreinte. Journal **synthétique** : ni système ni personne réels.

Le scénario suppose un délai d'attente des collectives allongé bien au-delà de la valeur par défaut de PyTorch, 10 minutes pour NCCL ([documentation de `torch.distributed`](https://docs.pytorch.org/docs/main/distributed.html)), ce que l'on fait pour ne pas tuer un job pendant une phase lente légitime. Avec la valeur par défaut, le job aurait échoué au bout de 10 minutes, et cet échec aurait servi de détection ([module 10, chapitre 5](../fault-tolerance/index.html#ch5)).
:::

### 4.4. Le post-mortem sans blâme

Un post-mortem est le document qui transforme un incident en actions. Le SRE Book pose la règle : il doit « focus on identifying the contributing causes of the incident without indicting any individual or team » ([Postmortem Culture](https://sre.google/sre-book/postmortem-culture/)).

Le [module 10, §8.5](../fault-tolerance/index.html#le-post-mortem-sans-blâme) en a donné la définition du SRE Book et la ligne des GPU-heures perdues ; on en fait ici un processus d'équipe, pratiqué au lab 16.2. Ce parcours en propose un plan **recommandé** : résumé, impact chiffré, chronologie, cause racine, facteurs contributifs, ce qui a bien et mal marché, et surtout des **actions** avec un propriétaire, une échéance et une vérification.

Le lab 16.2 fournit un vérificateur qui contrôle cette structure et, plus important, que **les durées écrites dans le texte égalent celles du journal** (détection, acquittement, atténuation, GPU-heures perdues ; pas chaque horodatage de la chronologie) : un post-mortem dont les chiffres ne tiennent pas est une opinion.

### 4.5. Écrire une décision : ADR et RFC

Une *ADR* (*architecture decision record*) est une décision d'une page : contexte, décision, alternatives écartées **avec une raison**, conséquences positives et négatives, et un **signal de révision** qui dit quelle mesure la ferait rouvrir. Une *RFC* est le document plus long qui précède les grandes décisions (projet 6). Le lab 16.1 vérifie mécaniquement la structure d'une ADR ; la qualité du raisonnement reste jugée par une personne.

::: recap
[Points clés]{.tag}

-   Le budget d'erreur est ce que l'objectif de service autorise de défaillance : 43,2 minutes par mois à 99,9 %.
-   Limite humaine de l'astreinte (SRE Book) : au plus 25 % du temps, au moins huit ingénieurs pour une rotation 24/7 à deux ; une petite équipe automatise ou limite l'astreinte aux heures ouvrées.
-   Un incident se mesure par des jalons ; la détection est souvent la durée la plus longue, et l'on commence par la plus longue.
-   Un post-mortem sans blâme cherche les causes du système et finit par des actions vérifiables ; ses chiffres doivent tenir.
-   Une ADR écrit l'alternative écartée et le signal qui rouvrirait la décision.
:::

## 5. Évolutions et migrations {#ch5}

Une plateforme qui ne change jamais devient obsolète ; une plateforme qui change sans méthode perd la confiance de ses utilisateurs. Ce chapitre traite deux cas : migrer des utilisateurs d'un système vers un autre, et mettre à jour un composant sans pouvoir revenir en arrière.

### 5.1. Migrer par cohortes

On ne bascule pas quarante personnes un lundi matin. On les répartit en **cohortes** de taille croissante et on ne passe à la suivante qu'après avoir atteint un **critère de sortie** mesuré. Chaque cohorte a trois éléments écrits avant de commencer :

1.  un **critère d'entrée** : ce qui doit être vrai pour que la cohorte démarre (documentation relue, support prêt) ;
2.  un **critère de sortie** : une mesure et une durée, par exemple « attente au 90e centile sous cinq minutes pendant deux semaines » ;
3.  un **déclencheur de retour arrière** et le délai pour l'exécuter.

La première cohorte est faite de volontaires qui tolèrent les défauts ; la dernière contient les utilisateurs aux besoins les plus exigeants, parce que la plateforme est alors rodée.

::: ex
[Exemple 5.1 — Trois cohortes pour quarante personnes]{.tag} Un groupe de 40 personnes passe de machines partagées à la plateforme. Plan : 5 pilotes, puis 15, puis 20. Les parts de chaque cohorte sont 5 / 40 = **12,5 %**, 15 / 40 = **37,5 %** et 20 / 40 = **50 %**, soit une part cumulée migrée de 12,5 %, **50 %** puis **100 %**.

Le point important est le deuxième palier : à 50 %, l'ancien système et le nouveau portent chacun la moitié de la charge, et tout incident doit pouvoir être imputé à l'un ou à l'autre. Un critère de sortie du pilote tel que « zéro incident de gravité 1 et délai moyen avant le premier job sous un jour » se vérifie avec les mesures du chapitre 1.
:::

### 5.2. Mettre à jour Slurm : l'ordre compte

La documentation de mise à jour de Slurm impose un ordre : sauvegardes, puis *slurmdbd* (la comptabilité), puis *slurmctld* (le contrôleur), puis *slurmd* (les démons des nœuds, de préférence avec le contrôleur), puis les nœuds de connexion et les commandes clientes ([guide de mise à jour](https://slurm.schedmd.com/upgrades.html)). Deux règles à retenir :

-   la mise à jour n'est possible que depuis les versions de la fenêtre de compatibilité de la version cible (les deux versions majeures précédentes, puis trois depuis Slurm 24.11, d'après le guide lu le 2026-10-24) : « Upgrades from incompatible versions will fail immediately upon startup », et il faut procéder par étapes entre versions compatibles ;
-   le retour arrière n'existe pas : « Reverting an upgrade (or downgrading) is not supported once any of the Slurm daemons have been started ».

Le numéro de version se lit ainsi : dans 23.11.4, « 23.11 » est la version majeure (année et mois de publication) et « .4 » la version de maintenance.

::: ex
[Exemple 5.2 — Ce que coûte un retour arrière]{.tag} Faute de retour arrière, la voie que décrit la documentation est de restaurer les sauvegardes de l'état du contrôleur et de la base de comptabilité, ce qui, selon la documentation, « will wipe out anything that happened after the backups were created ».

Avec les classes du cahier des charges fictif du projet 6 (1,5 + 26 + 170 + 650 = 847,5 jobs par mois de 730 heures), le taux d'arrivée est de 847,5 / 730 = 1,16 job par heure. Une fenêtre de trois heures entre la sauvegarde et la décision de revenir en arrière fait donc perdre la comptabilité d'environ **3,5 jobs** (1,16 × 3). C'est faible ici ; la même arithmétique appliquée à votre débit réel dit combien de comptabilité vous acceptez de perdre, et donc quand planifier la fenêtre.
:::

### 5.3. Changer la configuration comme du code

Une migration touche aussi la configuration : comptes, qualités de service, partages équitables. Le principe du [projet 1](../../projects/homelab-slurm/index.html) s'applique : décrire l'état voulu dans un fichier versionné, calculer un **plan** par différence avec l'état courant, ne jamais supprimer ce qui n'est pas dans le fichier, appliquer, puis vérifier qu'un second plan est vide. Un plan relu par une autre personne avant application est la meilleure protection contre l'erreur de frappe qui efface un compte.

### 5.4. Annoncer le changement

Un changement ne se termine pas quand il est déployé, mais quand les utilisateurs savent ce qui change pour eux. Quatre éléments suffisent : ce qui change et la date, ce que l'utilisateur doit faire, comment demander de l'aide, et la date à laquelle l'ancien système s'arrête. Une date de fin ferme est ce qui fait réellement migrer ; sans elle, l'ancien système survit indéfiniment à côté du nouveau.

::: recap
[Points clés]{.tag}

-   Migrez par cohortes de taille croissante, chacune avec critères d'entrée, de sortie et de retour arrière écrits d'avance.
-   Les volontaires d'abord ; les utilisateurs les plus exigeants en dernier.
-   Mise à jour de Slurm : sauvegardes, base de comptabilité, contrôleur, démons, clients, dans cet ordre ; aucune descente de version sans restauration.
-   La restauration efface ce qui s'est passé après la sauvegarde : chiffrez cette perte avant de planifier.
-   Plan par différence, relu, puis second plan vide : la configuration se traite comme du code.
-   Annoncez avec une date de fin ferme de l'ancien système.
:::

## 6. Diriger une petite équipe d'infrastructure {#ch6}

Diriger une équipe de trois personnes est un travail d'ingénierie : on décide quoi construire, quoi refuser et comment protéger le temps de chacun. Ce chapitre donne les mesures qui rendent ces choix discutables.

### 6.1. Le travail d'exploitation, ou *toil*

Le SRE Book définit le *toil* par un ensemble de traits : un travail « manual, repetitive, automatable, tactical, devoid of enduring value, and that scales linearly as a service grows » ([Eliminating Toil](https://sre.google/sre-book/eliminating-toil/)). Il fixe aussi une limite : le temps passé en travail purement opérationnel est plafonné à 50 % ([Being On-Call](https://sre.google/sre-book/being-on-call/)). Au-delà, l'équipe ne construit plus rien et le travail d'exploitation croît avec la plateforme.

Le toil se mesure en heures par mois : inventoriez chaque tâche répétitive, sa fréquence et sa durée. Une tâche qui prend trente minutes et revient 240 fois par mois pèse 120 heures.

::: ex
[Exemple 6.1 — Partager 480 heures entre trois personnes]{.tag} Trois ingénieurs à 160 heures par mois offrent 480 heures. Le plafond de 50 % de travail d'exploitation laisse au moins **240 heures** d'ingénierie. Sur le reste, l'astreinte ne devrait pas dépasser 25 % du temps total, soit **120 heures**, et les autres tâches d'exploitation 120 heures.

Or une astreinte permanente tenue à tour de rôle par trois personnes consomme un tiers du temps de chacune, soit 160 heures : elle dépasse son budget de 40 heures (160 − 120), qui sont prises sur l'ingénierie. La conclusion rejoint l'exemple 4.2 : une équipe de trois ne tient pas une astreinte permanente sans automatiser les reprises ou limiter l'astreinte aux heures ouvrées.
:::

### 6.2. Un point d'entrée unique pour les demandes

Une équipe qui reçoit des demandes par messagerie directe, par courriel et dans les couloirs ne peut ni les mesurer ni les prioriser. Imposez **un seul canal** et trois types de demandes : un incident (la plateforme est dégradée), une demande de service (un compte, un quota) et un projet (une évolution). Chaque type a un délai de première réponse annoncé. Les demandes de service les plus fréquentes sont les premières candidates à l'automatisation en libre-service.

### 6.3. Choisir quoi automatiser

Automatiser coûte de l'ingénierie maintenant pour économiser du toil plus tard. Deux nombres suffisent à comparer des options : le **coût de construction** en heures et le **gain mensuel** en heures. Leur rapport est le délai de retour en mois. À gain égal, on commence par ce qui se rembourse le plus vite ; sous une contrainte de temps de construction, on compare des *combinaisons* d'options, pas des options isolées (exercice 5).

### 6.4. Documenter l'exploitation

Chaque alerte qui réveille quelqu'un doit renvoyer à une fiche d'exploitation (*runbook*) qui dit quoi vérifier et quoi faire. Une fiche n'est vraie que si quelqu'un l'a suivie : faites-la exécuter une fois par une personne qui ne l'a pas écrite, et corrigez-la. C'est un choix de pratique de ce parcours (**recommandé**), pas une exigence d'un standard.

### 6.5. Réduire la dépendance à une seule personne

Le facteur de bus d'une équipe de trois est souvent un. Trois pratiques le relèvent à faible coût : une rotation des tâches d'astreinte pour que chacun sache faire le travail de l'autre, les décisions écrites en ADR plutôt que dans la mémoire de quelqu'un, et une revue systématique des changements d'infrastructure par une seconde personne.

::: recap
[Points clés]{.tag}

-   Le toil est un travail manuel, répétitif et automatisable qui croît avec la plateforme ; plafonnez-le à 50 % du temps.
-   Trois ingénieurs à 160 heures offrent 480 heures : 240 d'ingénierie au minimum, 120 d'astreinte au plus.
-   Un canal unique et trois types de demandes rendent le travail mesurable.
-   Comparez les automatisations par coût de construction, gain mensuel et délai de retour, en combinaisons sous contrainte.
-   Une fiche d'exploitation non exécutée par un tiers n'est pas encore vraie.
:::

## 7. Contribuer et se rendre visible {#ch7}

Un parcours d'apprentissage ne vaut que s'il laisse des traces que d'autres peuvent lire. Ce chapitre explique comment transformer votre travail en matière publiable sans exposer ce qui ne l'est pas.

### 7.1. Ce que lit quelqu'un qui évalue votre travail

Un relecteur ouvre le dépôt, lit le `README`, lance une commande et regarde si elle réussit. Les six projets de ce parcours sont construits pour cela : un `verify.sh` qui réussit sur l'implémentation de référence et échoue sur le gabarit, des badges qui disent honnêtement ce qui a été exécuté et ce qui ne l'a pas été, et des données fictives étiquetées comme telles. Reprenez ces règles pour tout ce que vous publiez.

### 7.2. Écrire en public sans rien exposer

Un post-mortem ou une décision tirés de votre travail réel sont précieux, mais ils contiennent presque toujours des noms de personnes, de clients, d'outils internes ou de chiffres confidentiels. Avant de publier : retirez les noms, remplacez les chiffres par des ordres de grandeur ou par des données synthétiques de même forme, et faites relire par la personne qui a la responsabilité du sujet. Le lab 16.2 donne un exemple : un journal **synthétique** qui reproduit la forme d'un incident sans en décrire aucun.

::: ex
[Exemple 7.1 — Vérifier mécaniquement le ton d'un post-mortem]{.tag} Le vérificateur du lab 16.2 contrôle la structure du post-mortem et que les durées écrites égalent celles du journal. Exécuté sur l'exemple fourni :

~~~text
$ python3 postmortem_lint.py postmortem_example.md --log incident.log --gpus 128
postmortem: ok
~~~

Il signale aussi un vocabulaire de blâme (« a oublié », « par négligence », « c'est la faute »…), mais ce contrôle est un indice, pas un verdict : un texte peut accuser sans employer un mot de la liste. La relecture par une personne reste nécessaire.
:::

### 7.3. Contribuer à un projet ouvert

Les projets ouverts du domaine (ordonnanceurs, opérateurs Kubernetes, outils d'observabilité) acceptent des contributions, et la plus utile pour débuter est modeste : reproduire un défaut avec une commande exacte, corriger une page de documentation, ajouter un test. Lisez d'abord le guide de contribution du projet et ses règles de licence de contribution, puis ouvrez une discussion avant un grand changement. Choisissez un projet que vous utilisez réellement dans un de vos labs : vous connaîtrez déjà son comportement.

### 7.4. Faire de chaque projet un récit

Pour chaque projet livré, préparez un court récit en quatre temps : le problème et ses contraintes, le choix fait et l'alternative écartée (une ADR), la mesure qui prouve que ça marche, et ce qui n'a pas marché. Ce dernier point est celui qui distingue un praticien d'un lecteur de documentation, et il sert directement à l'entretien du chapitre suivant.

::: recap
[Points clés]{.tag}

-   Un dépôt se juge à une commande qui réussit et à des badges honnêtes.
-   Publiez avec des données synthétiques ou anonymisées, relues par la personne responsable.
-   Les vérifications mécaniques de ton sont des indices, pas des verdicts.
-   Commencez à contribuer par une reproduction, un test ou une page de documentation.
-   Pour chaque projet, racontez le problème, le choix, la mesure et l'échec.
:::

## 8. Entretiens et exercices de conception {#ch8}

Un entretien de conception pour un poste d'infrastructure de calcul demande de dimensionner et de défendre une plateforme en trente minutes. Il ne teste pas la mémoire d'un chiffre mais la manière de raisonner, et ce que le candidat dit à voix haute.

### 8.1. Ce qui est évalué

La grille du lab 16.3 (`rubric.md`) retient sept critères notés de 0 à 2 : le **cadrage** (objectif, délai ferme ou souple, budget, autres utilisateurs), le **calcul de dimensionnement**, les **hypothèses** dites et chiffrées, la **fiabilité**, les **goulots**, les **compromis** et la **communication**. Les deux premiers sont éliminatoires. Cette grille est un outil d'entraînement de ce parcours, pas un standard de recrutement.

### 8.2. Le déroulé en trente minutes

Un découpage utile : cinq minutes de cadrage, dix de calcul, dix de conception (réseau, stockage, ordonnancement, fiabilité) et cinq de risques et de mesures à faire avant de s'engager. Écrivez les hypothèses au tableau dès que vous les posez.

### 8.3. Le calcul de tête

Pour un modèle dense de $N$ paramètres entraîné sur $D$ jetons, le calcul d'entraînement vaut environ $6ND$ opérations ([module 2, chapitre 7](../perf-models/index.html#ch7)). La durée sur $n_{\text{GPU}}$ GPU de pic $P_{\text{pic}}$ à une utilisation $\text{MFU}$ est :

$$ \text{jours} = \frac{6\,N\,D}{n_{\text{GPU}} \cdot P_{\text{pic}} \cdot \text{MFU} \cdot 86400} $$

où la MFU (*model FLOPs utilization*) est la part de la puissance crête réellement obtenue. Pour un délai donné, on inverse la formule pour obtenir $n_{\text{GPU}}$, qu'on arrondit **au nœud entier** supérieur.

::: ex
[Exemple 8.1 — Dimensionner 70 milliards de paramètres sur 2 000 milliards de jetons]{.tag} Le délai est de 100 jours au plus. Les hypothèses sont dites : pic de 989 TFLOP/s par GPU (un H100 SXM en BF16 dense, la moitié des 1 979 TFLOPS « with sparsity » de la [page produit](https://www.nvidia.com/en-us/data-center/h100/), voir le [module 2, chapitre 2](../perf-models/index.html#ch2)), MFU de 0,40, 14 octets par paramètre pour un checkpoint (poids en bf16, copie maîtresse et deux moments d'Adam en fp32), écriture à 50 Go/s au total, reprise de 15 minutes.

Le taux de 0,0002 panne par GPU-heure est une hypothèse **pessimiste** : environ six fois les 6,5 pannes pour mille nœuds-jours que [Kokolis et coauteurs](https://arxiv.org/abs/2410.21680) mesurent sur le cluster RSC-1, soit 3,4·10⁻⁵ par GPU-heure ([module 10, chapitre 1](../fault-tolerance/index.html#ch1)), qui donneraient un MTBF de job de 115 heures. Il est en revanche du même ordre que le MTTF de 7,9 heures que les mêmes auteurs mesurent pour les jobs de 1 024 GPU, soit 1,2·10⁻⁴. `sizing.py` donne, pour 256 GPU :

~~~text
training compute         : 8.40e+23 FLOP
nodes of 8 GPUs          : 32
ideal duration           : 96.0 days
checkpoint               : 980 GB, 20 s to write
job MTBF                 : 19.5 h
Young-Daly period        : 28 min, goodput 0.964
duration with failures   : 99.6 days
~~~

Le délai de 100 jours est tenu avec 0,4 jour de marge : la conclusion honnête est que 256 GPU suffisent à peine. Avec une MFU de 0,35 au lieu de 0,40, la durée idéale passe à 109,7 jours et il faut 288 GPU, avant même de compter les pannes. L'erreur sur une seule hypothèse décide du verdict, ce qui est exactement ce que l'on doit dire au jury.
:::

### 8.4. Fiabilité et goulots

Après le calcul de durée, trois chiffres montrent que vous pensez en production : le MTBF du job (ici 19,5 heures : un job de 256 GPU est interrompu en moyenne toutes les 19,5 heures), la taille et le temps d'écriture d'un checkpoint (980 Go en 20 secondes, ce qui suppose un stockage capable de 50 Go/s, à mesurer et non à supposer) et la période de checkpoint de Young et Daly, qui vaut ici 28 minutes. Nommez ensuite ce qui limiterait l'entraînement et comment vous le mesureriez *avant* de vous engager : réseau ([module 7](../networking/index.html)), stockage, fiabilité des nœuds.

La période de Young et Daly vaut $T^{\ast} = \sqrt{2CM}$, avec $C$ le temps d'écriture d'un checkpoint (le $\delta$ du module 10), $T$ la période (son $\tau$) et $M$ le temps moyen entre pannes du job ([module 10, chapitre 2](../fault-tolerance/index.html#ch2)).

Ici $C = 19{,}6$ s et $M = 70\,300$ s, d'où $T^{\ast} \approx 1\,660$ s, soit 28 minutes.

Le goodput s'en déduit au premier ordre, avec $R$ le temps de reprise (module 10, §2.2) :

$$ \text{goodput} \approx 1 - \left(\frac{C}{T} + \frac{T/2 + R}{M}\right) $$

Avec $R = 900$ s, le premier terme vaut 0,0118 et le second 0,0246 : le goodput est de 0,964, et la durée avec pannes de 96,0 / 0,964 = 99,6 jours. C'est le calcul de `sizing.py`, à refaire pour l'exercice 9.

### 8.5. Négocier, et poser vos propres questions

Diriger une plateforme, c'est aussi négocier une capacité ou un budget. Une question à préparer : *un fournisseur propose un engagement de trois ans sur votre capacité GPU ; comment préparez-vous la négociation ?* Réponse attendue : une demande chiffrée avec ses scénarios, le coût par GPU-heure utile, une alternative crédible qui fixe le prix de réserve, des clauses classées par valeur en jeu et deux négociations menées en parallèle. La méthode et ses chiffres sont au [module 15, chapitre 7](../finops-capacity/index.html#ch7).

En fin d'entretien, vos propres questions montrent ce que vous savez d'une plateforme, et leurs réponses disent si le poste est tenable. Cinq questions à poser (liste de ce parcours) :

1.  *Comment mesurez-vous l'adoption et le goodput de la plateforme ?* (chapitre 1)
2.  *Comment l'astreinte est-elle organisée : combien de personnes, quelles heures, combien d'incidents par garde ?* (chapitre 4)
3.  *Le dernier post-mortem a-t-il produit des actions avec un propriétaire, et ont-elles été faites ?* (chapitre 4)
4.  *Quelle part du temps de l'équipe va au travail d'exploitation, et qui décide de ce que l'on automatise ?* (chapitre 6)
5.  *Qui décide des achats de capacité, et quelle place l'équipe d'infrastructure y tient-elle ?* (module 15, chapitre 7)

::: recap
[Points clés]{.tag}

-   Sept critères : cadrage, calcul, hypothèses, fiabilité, goulots, compromis, communication.
-   Cadrer d'abord, calculer ensuite, dire chaque hypothèse à voix haute.
-   Durée = 6ND divisé par $n_{\text{GPU}}$, $P_{\text{pic}}$, MFU et 86 400 ; arrondir les GPU au nœud supérieur.
-   Goodput ≈ 1 − (C/T + (T/2 + R)/M) ; la durée avec pannes est la durée idéale divisée par le goodput.
-   Une hypothèse unique (la MFU) peut renverser la conclusion : chiffrez-en l'effet.
-   Montrez la fiabilité : MTBF du job, taille et temps du checkpoint, période de Young et Daly.
-   Préparez une question de négociation (module 15, chapitre 7) et vos propres questions sur l'astreinte, le toil et les post-mortems.
:::

## 9. Un plan de contrôle fiable : consensus, haute disponibilité et livraison continue {#ch9}

Les chapitres précédents supposent que le cœur de la plateforme répond : l'ordonnanceur accepte les jobs, le serveur d'API répond, la comptabilité enregistre. Ce chapitre traite ce cœur, le **plan de contrôle**, et la manière d'y livrer des changements sans l'abattre. La conception de systèmes distribués revient dans une large part des offres du [relevé du marché](../../market/index.html), la CI/CD dans une part notable, plus forte en Europe : c'est aussi un sujet d'entretien.

### 9.1. Ce qu'est le plan de contrôle d'une plateforme de calcul

::: def
[Plan de contrôle et plan de données]{.tag} Le *plan de contrôle* (*control plane*) regroupe les composants qui gardent l'état de la plateforme (files d'attente, allocations, objets déclarés) et prennent les décisions de placement. Le *plan de données* (*data plane*) exécute le travail : les nœuds et leurs jobs. Le plan de données peut survivre un moment sans plan de contrôle, mais il ne reçoit plus rien de neuf.
:::

Trois plans de contrôle reviennent dans ce parcours.

| Plateforme | Décide | Mémorise | Si le plan de contrôle tombe |
|---|---|---|---|
| Slurm ([module 5](../slurm/index.html#ch1)) | `slurmctld` | `StateSaveLocation` (état des jobs) ; base de `slurmdbd` (comptabilité) | plus de soumission ni de placement ; un contrôleur qui redémarre sans son état annule les jobs |
| Kubernetes ([module 12](../kubernetes-gpu/index.html#ch8)) | `kube-apiserver`, ordonnanceur, contrôleurs | etcd | les pods déjà placés peuvent continuer, aucun nouveau pod n'est placé |
| Ray ([module 11](../ray-rl-infra/index.html#ch2)) | GCS, sur le nœud de tête | mémoire du GCS, ou un stockage durable si on l'a configuré | sans tolérance aux pannes, tout le cluster Ray tombe |

Pour Slurm, `StateSaveLocation` contient « information about queued, running and recently completed jobs », et le guide d'administration prévient : « If a controller comes up without access to the state information, queued and running jobs will be cancelled » ([Quick Start Administrator Guide](https://slurm.schedmd.com/quickstart_admin.html), Slurm 26.05, lu le 2026-10-25). Le répertoire d'état vaut donc plus que la machine du contrôleur.

Pour Kubernetes, « All Kubernetes objects are stored in etcd » ; si la majorité des membres d'etcd est perdue, « Although the scheduled pods might continue to run, no new pods can be scheduled » ([Operating etcd clusters for Kubernetes](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)). Pour Ray, la page sur la tolérance aux pannes du GCS (*Global Control Service*) le dit sans nuance : par défaut, « If it fails, the entire Ray cluster fails » ([GCS fault tolerance](https://docs.ray.io/en/latest/ray-core/fault_tolerance/gcs.html)).

Le point commun : la panne du plan de contrôle n'arrête pas toujours les jobs en cours, mais elle arrête tout le **travail neuf**, y compris les reprises. Les reprises automatiques que l'exemple 4.2 exige (drainer un nœud, remettre un job en file) passent par lui : tant qu'il est absent, une panne de nœud n'est plus traitée.

::: war
[Décembre 2024 : un service de télémétrie sature les plans de contrôle Kubernetes]{.tag} D'après le post-mortem d'OpenAI, un nouveau service de télémétrie faisait exécuter à chaque nœud des appels coûteux à l'API Kubernetes, dont le coût croissait avec la taille du cluster ; les serveurs d'API des grands clusters ont cédé. Le plan de données devait tenir seul, mais « DNS relies on the control plane ».

Le test sur un cluster de préproduction n'avait rien montré, l'effet n'apparaissant qu'au-delà d'une certaine taille ; le cache DNS a retardé les symptômes pendant que le déploiement continuait ; et retirer le service fautif exigeait l'accès au plan de contrôle saturé ([post-mortem du 11 décembre 2024](https://status.openai.com/incidents/ctrsv3lwd797)).
:::

### 9.2. Consensus et quorum

Comment etcd garde-t-il un état cohérent sur plusieurs machines ? Par un algorithme de *consensus*, Raft, publié par Diego Ongaro et John Ousterhout à USENIX ATC 2014 ([article](https://www.usenix.org/conference/atc14/technical-sessions/presentation/ongaro)). Les membres élisent un *leader* qui reçoit les écritures et les réplique dans un journal ; une entrée est validée (*committed*) quand une **majorité** de membres l'a stockée. L'article donne l'ordre de grandeur courant : « five is a typical number, which allows the system to tolerate two failures ».

La majorité empêche le cerveau divisé (*split brain*). Chaque membre vote au plus une fois par mandat (*term*) et il faut une majorité pour être élu : deux leaders ne peuvent donc pas être élus pour le même mandat (propriété *Election Safety*, §5.2 de l'article). Après une coupure du réseau, au plus un des deux côtés a la majorité : celui-là continue, l'autre refuse les écritures.

::: thm
[Quorum et tolérance aux pannes]{.tag} Un cluster de $n$ membres a besoin d'un quorum de $q = \lfloor n/2 \rfloor + 1$ membres pour valider une écriture ; il tolère donc $f = \lfloor (n-1)/2 \rfloor$ pannes. Trois membres en tolèrent une, cinq en tolèrent deux, sept en tolèrent trois. Un quatrième ou un sixième membre n'ajoute aucune tolérance, puisque la majorité augmente avec lui ([FAQ d'etcd](https://etcd.io/docs/v3.7/faq/)).
:::

Pourquoi pas neuf membres ? Parce que chaque écriture attend la majorité. La FAQ d'etcd l'écrit : « Although larger clusters provide better fault tolerance, the write performance suffers because data must be replicated across more machines », et conseille de ne pas dépasser sept membres. La documentation de Kubernetes recommande cinq membres en production et décrit le passage de trois à cinq comme « A reasonable scaling ».

Éloigner les membres (plusieurs salles, plusieurs régions) les place dans des domaines de panne distincts, mais chaque écriture paie alors l'aller-retour vers la majorité : la FAQ d'etcd parle d'une latence « somewhat pronounced » entre centres de données. Le nombre de membres et leur distance se choisissent donc ensemble.

::: ex
[Exemple 9.1 — Garder le quorum avec 3 ou 5 membres]{.tag} Hypothèse à énoncer : chaque membre est disponible une fraction $a$ du temps, **indépendamment** des autres. La probabilité qu'au moins $q$ membres sur $n$ soient en service est une queue de loi binomiale :

$$ P(n, a) = \sum_{k=q}^{n} \binom{n}{k}\, a^{k}\, (1-a)^{n-k} $$

Pour trois membres, elle vaut $3a^2 - 2a^3$. La commande `python3 quorum.py table --a 0.99 0.999 --max-members 5` du lab 16.4 donne $P$ et l'indisponibilité $U = 1 - P$, convertie en minutes sur un mois de 30 jours (43 200 minutes, comme au chapitre 4) :

~~~text
members  quorum  tolerated  P(quorum) a=0.99    U (min/30 d)  P(quorum) a=0.999   U (min/30 d)
      1       1          0  0.990000000  1.00e-02 ( 432.0000)  0.999000000  1.00e-03 (  43.2000)
      2       2          0  0.980100000  1.99e-02 ( 859.6800)  0.998001000  2.00e-03 (  86.3568)
      3       2          1  0.999702000  2.98e-04 (  12.8736)  0.999997002  3.00e-06 (   0.1295)
      4       3          1  0.999407970  5.92e-04 (  25.5757)  0.999994008  5.99e-06 (   0.2589)
      5       3          2  0.999990149  9.85e-06 (   0.4255)  0.999999990  9.99e-09 (   0.0004)
~~~

Avec des membres à 99 %, un membre seul manque 432 minutes par mois, trois membres 12,9 minutes, cinq membres 0,43 minute. À 99,9 %, trois membres manquent 0,13 minute et cinq 0,0004. Quatre membres font pire que trois (25,6 contre 12,9 minutes à 99 %), comme l'annonce la FAQ d'etcd.

Tout repose sur l'indépendance. Si les cinq membres partagent un rack, une alimentation ou un commutateur, ce domaine les emporte ensemble, et le quorum ne peut être plus disponible que lui : $P = r \cdot P(5, a)$, où $r$ est la disponibilité du domaine. Avec un rack hypothétique à $r = 0{,}9995$, l'indisponibilité passe d'environ $10^{-8}$ à $5 \times 10^{-4}$ (21,6 minutes par mois), environ 50 000 fois plus. Placer les membres compte autant que les compter (exercice 12).
:::

### 9.3. La haute disponibilité en pratique

Slurm n'emploie pas de consensus pour son contrôleur : il fait du **basculement** (*failover*) entre un primaire et des secours. D'après la page `slurm.conf`, si `SlurmctldHost` est répété, « the first entry will run as the primary and all other entries as standby backups » ; un secours prend la main après `SlurmctldTimeout`, 120 secondes par défaut. Condition : `StateSaveLocation` doit être « readable and writable from the primary and all backup controllers at all times » ([slurm.conf](https://slurm.schedmd.com/slurm.conf.html), lu le 2026-10-25).

Ce répertoire partagé déplace le problème : il devient un point unique de défaillance, et sa latence ralentit le contrôleur. Le guide d'administration déconseille NFS et demande « a shared mount that is accessible to the two controllers and allows low-latency reads and writes ». Il prévient aussi qu'une panne avant l'écriture sur disque perd de l'état, écrit toutes les cinq secondes par défaut.

Pour la comptabilité, `AccountingStorageBackupHost` dans `slurm.conf` et `DbdBackupHost` dans [`slurmdbd.conf`](https://slurm.schedmd.com/slurmdbd.conf.html) déclarent un second `slurmdbd`. Les deux instances doivent accéder à la **même** base : la disponibilité de la base de données elle-même reste à assurer à part, et ce module ne la traite pas.

Kubernetes, avec kubeadm, propose deux topologies ([Options for Highly Available Topology](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/ha-topology/)). Dans la topologie **empilée** (*stacked*), celle par défaut, chaque nœud de plan de contrôle porte aussi un membre etcd : c'est plus simple, mais perdre un nœud fait perdre les deux, d'où « a minimum of three stacked control plane nodes ». Avec un etcd **externe**, etcd a ses propres machines : les pannes sont découplées, au prix de « twice the number of hosts », soit au moins trois plus trois.

Pour Ray, la tolérance aux pannes du GCS exige un stockage durable : un Redis hautement disponible (« officially supported », mais d'après une note de la page seulement avec KubeRay pour Ray Serve) ou un RocksDB embarqué, encore en alpha. Pendant la reprise, on ne crée plus d'acteurs ni de nœuds, mais « running Ray tasks and actors remain alive » ; un *raylet* qui ne retrouve pas le GCS en 60 secondes s'arrête (même page).

::: key
[Ce que la haute disponibilité ne protège pas]{.tag} La réplication copie tout, y compris les erreurs : un `kubectl delete` malheureux, une configuration fausse ou une donnée corrompue par un bogue se retrouvent aussitôt sur tous les membres. La haute disponibilité protège de la **perte d'une machine**. Elle ne protège ni d'une écriture fausse, ni d'un point unique caché (système de fichiers partagé, répartiteur de charge devant les serveurs d'API, DNS), ni d'un changement mal livré : pour cela, il faut des sauvegardes restaurées (9.4) et des changements progressifs (9.5).
:::

### 9.4. Sauvegarder, restaurer, et le prouver

Pour etcd, la documentation de Kubernetes décrit deux voies : le snapshot intégré et le snapshot de volume. Le snapshot intégré se prend sur un membre vivant avec `etcdctl snapshot save`. Sa vérification (`snapshot status`) et sa restauration (`snapshot restore`) passent par `etcdutl`, les commandes équivalentes d'`etcdctl` étant « deprecated since etcd v3.5.x ». Pour restaurer un cluster, la même page demande d'arrêter d'abord tous les serveurs d'API, puis de restaurer l'état dans chaque membre etcd.

Pour Slurm, le guide de mise à jour (section 5.2) nomme ce qu'il faut sauvegarder au minimum : le contenu de `StateSaveLocation`, tout le répertoire de configuration et, si `slurmdbd` est configuré, la base de comptabilité. Il ne donne pas la procédure, propre à chaque site. Pour une base MariaDB, l'outil de sauvegarde logique est `mariadb-dump`, anciennement `mysqldump` ([documentation MariaDB](https://mariadb.com/docs/server/clients-and-utilities/backup-restore-and-import-clients/mariadb-dump)). Rappelez-vous l'exemple 5.2 : restaurer efface tout ce qui a suivi la sauvegarde.

::: def
[RPO et RTO]{.tag} Le *RPO* (*recovery point objective*) est la perte de données acceptée, exprimée en temps : au pire, l'intervalle entre deux sauvegardes. Le *RTO* (*recovery time objective*) est la durée acceptée entre la panne et le service rétabli. Les deux se **mesurent** pendant un exercice de restauration ; ils ne se déduisent pas d'une fiche technique.
:::

::: key
[Une sauvegarde jamais restaurée n'est pas une sauvegarde]{.tag} Règle de ce parcours : chaque sauvegarde du plan de contrôle a sa procédure de restauration écrite dans une fiche d'exploitation (section 6.4). Une personne qui ne l'a pas écrite l'exécute à date fixe, dans un environnement jetable, et note deux mesures : la durée (RTO) et ce qui a été perdu (RPO).
:::

::: war
[Janvier 2017 : des sauvegardes que personne n'avait restaurées]{.tag} Pendant l'incident de base de données de GitLab.com, l'équipe constata que « the process of both finding and using backups failed completely ». Les dumps quotidiens échouaient sans bruit : `pg_dump` 9.2 face à une base PostgreSQL 9.6, et des courriels d'erreur rejetés par le serveur de réception. La restauration partit d'un snapshot LVM pris à la main six heures avant ; des heures de modifications (projets, commentaires, comptes) furent perdues ([post-mortem](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/)).
:::

::: ex
[Exemple 9.2 — Un exercice de restauration sur un etcd jetable]{.tag} Le script `etcd_drill.sh` du lab 16.4 démarre trois membres etcd 3.7.0 sur une seule machine, écrit 100 clés, prend un snapshot, écrit une clé de plus, arrête un membre, puis un deuxième, et restaure le snapshot dans un nouveau répertoire. Extraits de la sortie réelle, exécutée deux fois le 2026-10-25 :

~~~text
│   HASH   │ REVISION │ TOTAL KEYS │ TOTAL SIZE │ VERSION │
│ c5f8257a │      101 │        100 │      37 kB │   3.7.0 │
write with one member down: accepted
write with two members down: refused (Error: context deadline exceeded)
keys under /drill/job/ after restore: 100
key written after the snapshot: <absent>
restore and restart of one member: 1.2 s (measured on this machine)
RESTORE DRILL OK
~~~

Trois leçons. Avec un membre arrêté, le quorum de 2 sur 3 accepte encore les écritures ; avec deux, le membre restant les refuse, car il ne peut pas réunir de majorité. La clé écrite après le snapshot a disparu : c'est le RPO, rendu visible. Enfin, 1,2 seconde mesure la restauration de 37 ko sur une machine locale : la procédure est validée, pas sa durée sur une vraie base.
:::

### 9.5. Livrer l'infrastructure en continu

Le chapitre 5 traitait la configuration comme du code : un état voulu versionné, un plan par différence, une relecture. La pratique *GitOps* va plus loin. Ses quatre principes, publiés par le projet [OpenGitOps](https://opengitops.dev/), sont : un état voulu déclaratif, « Versioned and Immutable », tiré automatiquement par des agents (« Pulled Automatically »), et « Continuously Reconciled » : les agents observent sans cesse l'état réel et tentent d'y appliquer l'état voulu.

Sur Kubernetes, deux outils sont courants. Argo CD est « a declarative, GitOps continuous delivery tool for Kubernetes » qui marque *OutOfSync* une application dont l'état réel s'écarte du dépôt ([documentation](https://argo-cd.readthedocs.io/en/stable/)). Flux est « a tool for keeping Kubernetes clusters in sync with sources of configuration », projet diplômé de la CNCF ([documentation](https://fluxcd.io/flux/)). Plusieurs offres du relevé les citent nommément. Pour Slurm, ce parcours n'utilise pas d'agent : le plan par différence du [projet 1](../../projects/homelab-slurm/index.html), relu avant d'être appliqué, en tient lieu (le projet l'applique à la main ; le faire lancer par la CI après fusion est une extension).

Avec GitOps, tout changement passe par une demande de fusion : les contrôles automatiques avant fusion, tous déjà employés dans le parcours, deviennent la première protection du plan de contrôle.

| Ce qui change | Contrôle avant fusion | Où le parcours l'emploie |
|---|---|---|
| Scripts shell (drainage, recette, `verify.sh`) | `shellcheck` | modules 1, 5 et 6 |
| Règles d'alerte Prometheus | `promtool test rules` ([tests unitaires de règles](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/)) | module 14, projet 5 |
| Manifestes Kubernetes | validation contre les schémas de la version cible (par exemple `kubeconform`), puis `kubectl --dry-run=server` | module 12 (lab 12.4 pour le serveur d'API) |
| Infrastructure Terraform | `terraform plan -detailed-exitcode`, relu | [module 6, chapitre 4](../provisioning/index.html#ch4) |
| Comptes et QOS de Slurm | plan par différence, puis second plan vide | projet 1, section 5.3 |

`kubeval` n'est plus maintenu et renvoie vers `kubeconform` ([README de kubeval](https://github.com/instrumenta/kubeval)) ; celui-ci valide contre les spécifications OpenAPI, mais les validations faites côté serveur « are not covered », d'où `kubectl --dry-run=server` ([README de kubeconform](https://github.com/yannh/kubeconform)).

Les pilotes et les firmwares, eux, changent des nœuds. Le [module 6, chapitre 7](../provisioning/index.html#ch7) en donne la mécanique : drainer un lot, changer, redémarrer, vérifier par la recette rapide, remettre en service, avec un canari en premier lot, une taille de lot bornée et un arrêt au premier échec. Ce qui manque souvent, ce sont des critères de retour arrière **écrits avant** de commencer et évalués par la machine.

Le SRE Workbook définit le *canarying* comme « a partial and time-limited deployment of a change in a service and its evaluation ». On compare le canari à un groupe témoin (*control*) resté sur l'ancienne version, au même moment, plutôt qu'à la période précédente : « Before/After Evaluation Is Risky ». L'impact sur le budget d'erreur est proportionnel à la part exposée : 20 % d'erreurs sur 5 % du trafic donnent 1 % au total ([Canarying Releases](https://sre.google/workbook/canarying-releases/)).

Pour un lot de nœuds GPU, trois critères de retour arrière automatiques suffisent pour commencer (choix de ce parcours ; les seuils se fixent sur vos mesures) :

1.  un nœud canari échoue à la recette rapide après le changement ([module 6, chapitre 6](../provisioning/index.html#ch6)) ;
2.  le taux d'erreurs Xid ou de jobs en échec des canaris dépasse celui du groupe témoin sur la même fenêtre ;
3.  la santé du plan de contrôle se dégrade pendant le déploiement (latence du serveur d'API, changements de leader d'etcd) : c'est la leçon de l'incident de 2024 de la section 9.1.

Chaque critère a un propriétaire, un seuil et une action automatique : arrêter le déploiement et remettre l'image précédente sur le lot. Un humain décide de reprendre ; personne n'a à décider de s'arrêter.

### 9.6. Ce que les entretiens demandent sur les systèmes distribués

Dans le relevé, les offres parlent de systèmes distribués en termes généraux plutôt que d'algorithmes nommés ; certaines demandent de connaître les composants du plan de contrôle de Kubernetes, etcd compris. Les questions portent donc moins sur une preuve de Raft que sur ses conséquences d'exploitation. Cinq questions à préparer (liste de ce parcours) :

1.  *Pourquoi trois ou cinq membres, et jamais quatre ?* Majorité, tolérance, latence d'écriture (9.2).
2.  *Le contrôleur Slurm, etcd ou le GCS tombe : que deviennent les jobs ?* Jobs en cours contre travail neuf, contrôleur sans son état (9.1).
3.  *Comment éviter deux leaders après une coupure du réseau ?* Un vote par mandat et une majorité (9.2).
4.  *Trois membres etcd dans le même rack, est-ce de la haute disponibilité ?* Domaines de panne et indépendance (exemple 9.1, exercice 12).
5.  *Comment déployez-vous un nouveau pilote GPU sur mille nœuds ?* Canari, groupe témoin, lots bornés, retour arrière automatique (9.5).

Dans chaque réponse, donnez le chiffre et l'hypothèse qui le porte, comme au chapitre 8.

::: recap
[Points clés]{.tag}

-   Le plan de contrôle garde l'état et décide : `slurmctld` et son `StateSaveLocation`, `kube-apiserver` et etcd, le GCS de Ray. Sa panne arrête le travail neuf ; un contrôleur Slurm qui redémarre sans son état annule les jobs.
-   Un cluster de consensus de n membres a un quorum de ⌊n/2⌋ + 1 et tolère ⌊(n − 1)/2⌋ pannes : trois ou cinq membres, jamais un nombre pair.
-   La formule binomiale suppose des pannes indépendantes ; un rack ou une alimentation partagés plafonnent la disponibilité. Aucun domaine de panne ne doit porter plus de membres que le cluster ne tolère de pannes (2 sur 5).
-   La haute disponibilité protège de la perte d'une machine, pas d'une écriture fausse ni d'un changement mal livré.
-   Une sauvegarde n'existe que restaurée : procédure écrite, exercée à date fixe, RTO et RPO mesurés.
-   Livrez par un dépôt relu et testé avant fusion, puis par canaris comparés à un groupe témoin, avec des critères de retour arrière écrits d'avance.
:::

## Labs {#labs}

Quatre labs, tous exécutés dans le bac à sable (machine virtuelle Linux 6.18, 4 processeurs, sans GPU, sans cloud, Python 3.13 et pytest 9.1, le 2026-10-24, et le 2026-10-25 pour le lab 16.4). Chacun a un `verify.sh` qui sort avec le code 0 ; lancez les commandes depuis le dossier du lab (`labs/platform-leadership/<lab>/`), après `pip install pytest` si besoin, et choisissez l'interpréteur avec `PYTHON=python3 bash verify.sh`. **Aucun ne décrit un système ou une personne réels** : le journal d'incident, le cahier des charges et les réponses d'entretien sont inventés pour l'exercice.

### Lab 16.1 — Écrire une décision d'architecture vérifiable {#lab-16-1}

::: lab

**Objectif.** Écrire une ADR d'une page dont la structure est contrôlée mécaniquement : statut daté, contexte, décision, au moins deux alternatives écartées chacune avec une raison, conséquences positives **et** négatives, signal de révision. **Durée.** 2 h. **Prérequis matériels.** Un portable avec Python 3 et `pytest` ; aucun GPU.

1.  Lisez `labs/platform-leadership/rfc-template/example_adr.md`, qui reprend une décision de la RFC de référence du projet 6 (données fictives).
2.  Lancez `python3 adr_lint.py adr_template.md` : le gabarit vierge est refusé, lisez les messages.
3.  Écrivez une ADR sur une décision de votre propre parcours (par exemple le choix d'un ordonnanceur pour votre lab) en partant du gabarit.
4.  Lancez `adr_lint.py` sur votre texte jusqu'à « adr: ok », puis faites-le relire par une personne : le vérificateur ne juge pas le raisonnement.
5.  Lancez `bash verify.sh` et lisez les douze tests.

**Critère de réussite.** `bash verify.sh` affiche « 12 passed », « the blank template is refused, as it should be » et « OK rfc-template ».

**Pour aller plus loin.** Comparez votre ADR à `solutions/adr_jupyterhub.md` (exercice 10) ; passez à une RFC complète avec `labs/projects/capstone-rfc/reference/rfc_lint.py`.
:::

### Lab 16.2 — Post-mortem d'un incident simulé {#lab-16-2}

::: lab

**Objectif.** Reconstituer la chronologie d'un incident à partir d'un journal **synthétique**, mesurer ses jalons, puis écrire un post-mortem sans blâme dont les durées égalent celles du journal. **Durée.** 3 h. **Prérequis matériels.** Un portable avec Python 3 et `pytest` ; aucun GPU.

1.  Lisez `incident.log` **avant** `postmortem_example.md` : trouvez vous-même la cause (un rang silencieux sur un GPU tombé du bus) et les jalons.
2.  Lancez `python3 timeline.py incident.log 128` et comparez avec votre lecture : détection, acquittement, atténuation, résolution.
3.  Notez ce que la supervision affichait pendant l'incident (une utilisation GPU rassurante) et pourquoi c'est le facteur contributif principal.
4.  Rédigez votre propre post-mortem avec résumé, impact chiffré, chronologie, cause racine, facteurs contributifs, ce qui a bien et mal marché, et des actions avec propriétaire, échéance et vérification.
5.  Lancez `python3 postmortem_lint.py votre_fichier.md --log incident.log --gpus 128` jusqu'à « postmortem: ok », puis `bash verify.sh`.

**Critère de réussite.** `bash verify.sh` affiche « 20 passed », les cinq durées de l'exemple 4.3 (dont détection 1 h 40, acquittement 4 min, atténuation 18 min), « GPU-hours without progress (128 GPUs): 251.7 », « postmortem: ok » et « OK incident-review ».

**Pour aller plus loin.** Ajoutez au journal un événement de fausse alerte et mesurez son effet sur le temps de détection ; écrivez l'alerte qui aurait réduit la détection (projet 5).
:::

### Lab 16.3 — Exercice de conception : de 8 à 256 GPU {#lab-16-3}

::: lab

**Objectif.** Dimensionner l'entraînement d'un modèle dense avec un calculateur dont chaque hypothèse est explicite, puis comparer trois réponses d'entretien (insuffisante, solide, excellente) à la grille d'évaluation. **Durée.** 2 h. **Prérequis matériels.** Un portable avec Python 3 et `pytest` ; aucun GPU.

1.  Lisez l'énoncé et la grille dans `labs/platform-leadership/design-interview/rubric.md`.
2.  Répondez par écrit en trente minutes, **avant** de lire `answers/`.
3.  Lancez `python3 sizing.py` avec les paramètres de l'exemple 8.1 (la commande complète est dans `README.md`) et comparez sa sortie à vos chiffres.
4.  Changez la MFU à 0,35, le débit d'écriture à 10 Go/s, le taux de panne à 0,001, et notez ce qui bascule (avec les trois changements ensemble : 109,7 jours idéaux et 134,1 jours avec pannes).
5.  Notez votre réponse avec la grille, puis lisez les trois réponses de `answers/` et dites ce qui sépare chaque niveau du suivant. Lancez `bash verify.sh`.

**Critère de réussite.** `bash verify.sh` affiche « 8 passed » puis la sortie de l'exemple 8.1 (« duration with failures : 99.6 days ») et « OK design-interview ». Les tests vérifient que les chiffres des réponses « solide » et « excellente » sont ceux que reproduit le calculateur, et que la réponse « insuffisante » (« environ 25 jours ») est fausse selon lui (96,0 jours).

**Pour aller plus loin.** Refaites l'exercice pour 7 milliards de paramètres sur 1 000 milliards de jetons (exercice 9).
:::

### Lab 16.4 — Quorum d'un cluster de consensus et exercice de restauration {#lab-16-4}

::: lab

**Objectif.** Calculer la probabilité qu'un cluster de consensus garde son quorum, vérifier la formule contre une simulation de Monte-Carlo à graine fixe, puis mesurer l'effet des domaines de panne. **Durée.** 30 min, plus 30 min pour la partie facultative. **Prérequis matériels.** Un portable avec Python 3 et `pytest` ; aucun GPU. Partie facultative : les binaires `etcd`, `etcdctl` et `etcdutl` (testés en version 3.7.0 ; les versions 3.5 et 3.6 n'ont pas été essayées), sans privilège administrateur.

1.  Lisez `labs/platform-leadership/quorum-drill/quorum.py` : la formule binomiale, le modèle à domaines de panne et la simulation.
2.  Lancez `python3 quorum.py table --a 0.99 0.999` et retrouvez les valeurs de l'exemple 9.1.
3.  Lancez `python3 quorum.py check --trials 100000 --seed 2026` : la simulation est comparée à la formule avec une tolérance de quatre écarts-types, sur des disponibilités assez basses pour que des pertes de quorum s'observent.
4.  Lancez `python3 quorum.py racks` avec les dispositions de l'exercice 12 et expliquez pourquoi deux racks ne suffisent pas.
5.  Lancez `bash verify.sh` et lisez les quinze tests.

**Critère de réussite.** `bash verify.sh` affiche « 15 passed », la table de l'exemple 9.1 (dont « 0.999702000 » pour trois membres à 99 %), « formula and simulation agree » et « OK quorum-drill ».

**Pour aller plus loin.** Avec `ETCD_BIN=<dossier des binaires> bash etcd_drill.sh`, montez un vrai cluster etcd de trois membres sur `127.0.0.1`, prenez un snapshot, arrêtez un puis deux membres et restaurez (exemple 9.2) ; le script vérifie que les 100 clés reviennent et que la clé écrite après le snapshot est perdue. Il a été exécuté deux fois le 2026-10-25 avec etcd 3.7.0, mais `verify.sh` ne l'exige pas.
:::

## Exercices {#ex}

Les données des exercices sont **fictives**, de même que les journaux : les chiffres sont recalculés en Python, pas observés sur un système réel.

::: exo
[Exercice 1 · ★ — Budget d'erreur]{.tag} Un service vise un SLO de disponibilité sur 30 jours. (a) Calculez le budget d'erreur en minutes pour 99,5 %, 99,9 % et 99,99 %. (b) Un incident dure 140 minutes : quelle part du budget consomme-t-il pour chaque SLO ?
:::

::: sol
Un mois de 30 jours compte 43 200 minutes. (a) Budget = (1 − SLO) × 43 200 : **216 minutes** à 99,5 %, **43,2 minutes** à 99,9 % et **4,32 minutes** à 99,99 %. (b) 140 / 216 = **64,8 %** du budget à 99,5 %, 140 / 43,2 = **3,24 fois** le budget à 99,9 %, 140 / 4,32 = **32,4 fois** à 99,99 %. À 99,5 %, l'incident laisse 76 minutes (216 − 140) ; aux deux autres SLO, le budget est épuisé et les changements doivent ralentir (SRE Book, *Embracing Risk*).
:::

::: exo
[Exercice 2 · ★ — Astreinte et taille d'équipe]{.tag} Une équipe assure une astreinte permanente avec des semaines alternées. (a) Avec une seule personne d'astreinte à la fois, quelle part de son temps chacun passe-t-il d'astreinte pour 3, 4, 5, 6 ingénieurs ? (b) Avec un titulaire et un second en permanence, combien d'ingénieurs faut-il pour rester à 25 % ?
:::

::: sol
(a) Une personne sur N à la fois : 1 / N, soit **33,3 %**, **25 %**, **20 %** et **16,7 %**. L'équipe de 3 dépasse 25 %, celle de 4 est exactement à la limite. (b) Avec deux personnes en permanence, chacun passe 2 / N de son temps : 2 / N ≤ 25 % exige N ≥ **8**. On retrouve le minimum de huit ingénieurs du SRE Book pour une équipe sur un seul site, avec un tour d'astreinte (titulaire ou second) d'une semaine par mois.
:::

::: exo
[Exercice 3 · ★★ — Combien de GPU pour le développement ?]{.tag} 800 sessions interactives de 1,5 heure arrivent chaque mois de 730 heures. L'objectif est une attente au 90e centile d'au plus 5 minutes. (a) Quelle est la charge moyenne, en sessions simultanées ? (b) Pour 3, 4 et 5 GPU, donnez l'utilisation, la probabilité d'attente et l'attente moyenne avec le modèle de file M/M/c (formule d'Erlang C : [module 15, chapitre 2](../finops-capacity/index.html#ch2), ou fonction `erlang_c` de `labs/projects/capstone-rfc/reference/capacity.py`). (c) Que choisissez-vous, et que se passe-t-il si la demande augmente de 5 % ?
:::

::: sol
(a) Le taux d'arrivée est 800 / 730 = 1,096 session par heure ; par la loi de Little, la charge est 1,096 × 1,5 = **1,64 session simultanée**. (b) Formule d'Erlang C, calculée en Python : 3 GPU, utilisation 54,8 %, probabilité d'attente **29,1 %**, attente moyenne 1 158 secondes ; 4 GPU, 41,1 %, **9,83 %**, 225 secondes ; 5 GPU, 32,9 %, **2,87 %**, 46 secondes. Le 90e centile de l'attente est nul dès que la probabilité d'attente est sous 10 % : c'est le cas à 4 et 5 GPU, pas à 3 (71 minutes).

(c) **4 GPU** tiennent l'objectif, mais la marge est mince : à +5 % de demande, la probabilité d'attente passe à 11,4 % et l'attente au 90e centile à **5,07 minutes**, au-dessus de l'objectif. Choisissez 4 avec une alerte sur l'attente au 90e centile et un plan à 5 GPU, ou 5 GPU si l'objectif est contractuel.
:::

::: exo
[Exercice 4 · ★★ — Lire les jalons d'un incident]{.tag} Journal **fabriqué** d'un job de 64 GPU :

~~~text
14:00:00|gpu-03|ANOMALY|rank 17 stopped writing its log
14:06:00|alert|DETECT|alert: no progress for 5 minutes
14:09:00|on-call|ACK|acknowledged
14:24:00|on-call|MITIGATE|gpu-03 drained, job requeued from checkpoint
14:40:00|slurm|RESOLVE|job runs at full throughput again
~~~

(a) Calculez les durées de détection, d'acquittement, d'atténuation (depuis la détection) et de l'anomalie à l'atténuation. (b) Combien de GPU-heures sont perdues jusqu'à l'atténuation ? (c) Quelle durée améliorez-vous en premier, et comment ?
:::

::: sol
(a) Détection : 14:06 − 14:00 = **6 min**. Acquittement : 14:09 − 14:06 = **3 min**. Atténuation depuis la détection : 14:24 − 14:06 = **18 min**. De l'anomalie à l'atténuation : **24 min** ; jusqu'à la résolution complète : 40 min.

(b) 64 GPU × 24 min = 64 × 0,4 h = **25,6 GPU-heures**. (c) L'atténuation pèse 18 / 24 = **75 %** du temps sans progression : c'est la durée à réduire en premier, par un drainage et une remise en file automatiques sur erreur matérielle (projets 3 et 5), qui supprimeraient aussi la dépendance à l'astreinte. La détection, déjà à 6 minutes grâce à l'alerte, est correcte.
:::

::: exo
[Exercice 5 · ★★ — Choisir quoi automatiser]{.tag} Une équipe de trois ingénieurs (480 heures par mois) a 240 heures de toil par mois, réparties en quatre tâches. Elle dispose de **110 heures** de construction ce mois-ci.

| Tâche | Toil (h/mois) | Construction (h) | Part supprimée |
|---|---|---|---|
| A. Création de comptes et de quotas | 120 | 80 | 90 % |
| B. Drainage manuel de nœuds | 60 | 100 | 80 % |
| C. Rapports hebdomadaires | 45 | 30 | 100 % |
| D. Redémarrage de services | 15 | 40 | 100 % |

(a) Calculez le gain mensuel et le délai de retour de chaque tâche. (b) Quelle combinaison tenant dans 110 heures maximise le gain ? (c) Quelle part des 480 heures reste en toil, et que dit le plafond de 50 % ?
:::

::: sol
(a) Gains : A 120 × 0,9 = **108 h**, B 60 × 0,8 = **48 h**, C **45 h**, D **15 h** par mois. Délais de retour (construction ÷ gain) : A **0,74 mois**, B 2,08, C **0,67**, D 2,67.

(b) Les combinaisons de coût au plus 110 h sont A, B, C, D seules, A + C (110 h) et C + D (70 h) ; A + C donne **153 h** par mois, contre 108 h pour A seule et 60 h pour C + D. A + D (120 h) et B + C (130 h) dépassent le budget : le meilleur choix isolé (A) n'est donc pas la meilleure combinaison.

(c) Il reste 240 − 153 = **87 heures** de toil, soit 87 / 480 = **18,1 %** : l'équipe passe de 50 % (exactement au plafond, sans marge) à moins du quart du temps. Le plafond de 50 % était juste atteint avant l'automatisation, si l'équipe n'assure pas d'astreinte en plus : sinon ses heures s'ajoutent aux 240 heures, et le plafond était déjà dépassé (exemple 6.1).
:::

::: exo
[Exercice 6 · ★★ — MIG ou tranches de temps ?]{.tag} Dix-huit chercheurs qui ne se connaissent pas utilisent des notebooks de développement sur 3 GPU de 80 Go. Hypothèse de l'énoncé : un profil MIG offre environ 10 Go (à vérifier dans le guide MIG pour votre GPU). (a) Combien d'instances MIG au plus sont disponibles et quelle part sert-on ? (b) Avec 6 partages par GPU en tranches de temps, qu'arrive-t-il si un notebook alloue 60 Go ? (c) Que décidez-vous, et que faites-vous d'un chercheur qui a besoin de 40 Go ?
:::

::: sol
(a) Au plus sept instances par GPU : 3 × 7 = **21 instances**, dont 18 servies, soit **85,7 %**. (b) Avec les tranches de temps, il n'y a pas d'isolation de la mémoire ni des pannes entre les partages : un notebook qui alloue 60 Go laisse 80 − 60 = 20 Go aux cinq autres partages du GPU, soit **4 Go** chacun ; un dépassement ou une erreur fait échouer les voisins.

(c) **MIG** pour des utilisateurs qui ne se connaissent pas, parce qu'il isole mémoire et pannes. Le chercheur à 40 Go ne tient pas dans un profil de 10 Go : il passe sur un **GPU entier** réservé, dans une classe distincte de la file. Contrepartie de MIG : des profils fixes et une reconfiguration à planifier. Les tranches de temps ne conviennent qu'à des charges qui se font mutuellement confiance.
:::

::: exo
[Exercice 7 · ★★ — Plan de migration]{.tag} Quarante personnes passent de machines partagées à la plateforme. Vous proposez trois cohortes de 5, 15 et 20 personnes. (a) Donnez la part de chaque cohorte et la part cumulée migrée. (b) Écrivez pour chaque cohorte un critère d'entrée, un critère de sortie mesurable et un déclencheur de retour arrière. (c) Pourquoi ne pas mettre en premier les huit utilisateurs les plus gros ?
:::

::: sol
(a) 5 / 40 = **12,5 %**, 15 / 40 = **37,5 %**, 20 / 40 = **50 %** ; cumul **12,5 %**, **50 %**, **100 %**.

(b) **Cohorte 1 (5 volontaires).** Entrée : modèle de job et documentation relus par un tiers, canal de support ouvert. Sortie : zéro incident de gravité 1 et délai avant le premier job sous un jour pendant deux semaines. Retour arrière : un incident de gravité 1 non résolu en 4 heures ; les pilotes retrouvent l'ancien accès le jour même. 

**Cohorte 2 (15).** Entrée : critères de sortie précédents tenus. Sortie : attente au 90e centile de la classe interactive sous 5 minutes pendant deux semaines. Retour arrière : attente au 90e centile au-dessus de 10 minutes pendant trois jours. 

**Cohorte 3 (20).** Entrée : ancien système en lecture seule annoncé avec une date de fin. Sortie : arrêt de l'ancien système. Retour arrière : le même déclencheur, avec un délai de réactivation de l'ancien accès connu et testé.

(c) Les utilisateurs les plus gros révèlent les limites de capacité et de configuration au moment où la plateforme est la moins rodée ; leur échec coûte le plus et fait perdre la confiance du groupe. On les place en dernier, quand les défauts de la plateforme ont été corrigés sur des charges plus légères, tout en les associant tôt à la conception pour qu'ils ne découvrent pas la plateforme le jour de leur bascule.
:::

::: exo
[Exercice 8 · ★★★ — Modèle de menaces]{.tag} Deux équipes partagent 4 GPU en tranches de temps sur Kubernetes. Constats : tous les jobs s'exécutent avec un compte de service partagé dont le jeton de stockage vit un an ; les images sont référencées par `:latest` ; les Secrets sont ceux par défaut ; l'audit est désactivé. Dressez le modèle de menaces : cinq risques classés par gravité, avec pour chacun le contrôle que vous mettez et le risque résiduel.
:::

::: sol
Un classement défendable, du plus grave au moins grave :

| Risque | Contrôle | Risque résiduel |
|---|---|---|
| Jeton de stockage partagé et valable un an : une fuite donne accès aux données des deux équipes pendant un an | Identité par équipe ou par utilisateur ; jetons à courte durée de vie et à portée limitée | La compromission d'un jeton reste possible pendant sa durée de vie courte |
| Tranches de temps : aucune isolation mémoire ni des pannes entre partages | MIG pour des équipes non liées, ou GPU entiers par équipe | Profils MIG fixes, coût plus élevé |
| Image `:latest` : l'étiquette peut pointer ailleurs demain, donc code non reproductible ou altéré | Image épinglée par empreinte, construite et publiée par l'équipe | Il faut mettre à jour les empreintes (processus) |
| Secrets non chiffrés par défaut dans le magasin de l'API | Chiffrement au repos, droits de lecture restreints, aucun secret dans l'image ni le dépôt | Les administrateurs de l'API voient toujours les secrets |
| Audit désactivé : impossible de reconstituer qui a fait quoi | Audit activé et conservé assez longtemps, avec l'identité de la personne | Coût de stockage des journaux |

Le premier risque domine parce qu'il combine portée (les deux équipes), durée (un an) et facilité (un seul jeton). Sources : documentation Kubernetes (multi-location, Secrets, images, audit), citée au chapitre 3, et NVIDIA (MIG, partage de GPU), citée au chapitre 2.
:::

::: exo
[Exercice 9 · ★★★ — Dimensionner un entraînement de 7 milliards de paramètres]{.tag} On veut entraîner un modèle dense de 7 milliards de paramètres sur 1 000 milliards de jetons en 30 jours maximum, sur des GPU de 989 TFLOP/s crête. Hypothèses : MFU de 0,40, checkpoint de 14 octets par paramètre écrit à 20 Go/s au total, 0,0002 panne par GPU-heure (hypothèse pessimiste, voir l'exemple 8.1), reprise de 15 minutes.

(a) Combien de GPU, arrondis au nœud de 8 ? (b) Durée avec et sans pannes, MTBF, taille et temps du checkpoint, période de Young et Daly. (c) Que devient la réponse avec une MFU de 0,30 ? (d) Quelle mesure faites-vous avant de vous engager ?
:::

::: sol
Le calcul d'entraînement est 6 × 7e9 × 1e12 = **4,2e22 FLOP**. (a) Pour 30 jours : 4,2e22 / (30 × 86 400 × 989e12 × 0,40) = 40,96, soit 41 GPU, arrondis à **48 GPU** (6 nœuds).

(b) Sur 48 GPU : durée idéale **25,6 jours** ; checkpoint de 7e9 × 14 = **98 Go**, écrit en **4,9 secondes** à 20 Go/s ; MTBF du job 1 / (48 × 0,0002) = **104,2 heures** ; période de Young et Daly √(2CM) = **32 minutes** (31,95) avec un goodput de **0,992** ; durée avec pannes **25,8 jours**, soit 4,2 jours de marge sur les 30.

(c) À MFU 0,30 : 4,2e22 / (30 × 86 400 × 989e12 × 0,30) = 54,6, soit **56 GPU** ; à 48 GPU la durée idéale monte à **34,1 jours**, hors délai. (d) Avant de s'engager, mesurez la **MFU réelle** d'un nœud sur le modèle et la taille de lot visés, et le **débit d'écriture** du stockage sous charge : ce sont les deux hypothèses dont l'erreur renverse la conclusion.
:::

::: exo
[Exercice 10 · ★★★ — Écrire une décision]{.tag} Hypothèses de l'énoncé : la plateforme de la RFC de référence du projet 6 a un pool réservé de développement de 4 GPU ; elle n'exécute **pas** ses sessions sous Slurm (hypothèse propre à cet exercice) ; trois ingénieurs l'exploitent. 40 personnes lancent environ 650 sessions interactives par mois de 1,2 heure en moyenne, avec un objectif de démarrage sous 5 minutes. Rédigez l'ADR du choix du lanceur de sessions entre un JupyterHub, un portail de type Open OnDemand et un accès SSH direct. Validez-la avec `adr_lint.py`.
:::

::: sol
Une réponse qui passe le vérificateur (fichier `labs/platform-leadership/rfc-template/solutions/adr_jupyterhub.md`) :

~~~markdown
# ADR-002 — Les sessions interactives passent par un JupyterHub

## Statut

Proposé le 2026-04-06.

## Contexte

Le groupe de recherche (fictif) compte 40 personnes et lance environ 650 sessions interactives par mois, de 1,2 heure en moyenne : la demande moyenne est d'environ 1,07 GPU simultané. L'objectif de service est de démarrer une session en moins de 5 minutes. Les trois ingénieurs de plateforme ne peuvent pas exploiter un second système de lancement : la solution doit réutiliser la plateforme de la RFC-001 et s'arrêter seule quand elle est inactive.

## Décision

Nous déployons un JupyterHub qui lance un serveur mono-utilisateur par session sur le pool réservé de développement, avec un arrêt automatique après inactivité et une image de base épinglée par empreinte.

## Alternatives écartées

- **Portail de lancement de jobs de type Open OnDemand** : bonne intégration avec un ordonnanceur HPC et des applications interactives variées. Écartée parce que la plateforme retenue n'exécute pas les sessions sous Slurm ; Open OnDemand dispose d'un adaptateur Kubernetes, mais son coût d'exploitation face à celui d'un hub n'a pas été comparé, ce qui est le point à mesurer si le signal de révision se déclenche.
- **Accès SSH direct aux machines** : aucune infrastructure à écrire. Écartée parce qu'il n'y a ni isolation entre utilisateurs ni expiration automatique des sessions, donc des GPU réservés oubliés.

## Conséquences

**Positives**

- Une seule interface pour démarrer un environnement, avec des images contrôlées par l'équipe.
- L'arrêt après inactivité réduit les GPU réservés oubliés, que l'alerte d'allocation inactive du projet 5 surveille.

**Négatives**

- Un composant de plus à exploiter, avec ses mises à jour et sa sécurité.
- Le délai de démarrage dépend de la disponibilité du pool réservé : il n'est pas mesuré avant la mise en service.

Signal de révision : si le délai de démarrage au 90e centile dépasse 5 minutes pendant deux semaines consécutives, cette décision est rouverte.
~~~

Ce qui fait la qualité : le contexte chiffre la demande (650 × 1,2 / 730 = 1,07), chaque alternative a une raison qui s'appuie sur une contrainte du contexte, les conséquences négatives sont franches, et le signal de révision porte une mesure et un seuil. L'ADR ne prouve pas que JupyterHub est le bon choix ; elle rend le choix **contestable**.
:::

::: exo
[Exercice 11 · ★ — Quelle statistique rapporter ?]{.tag} Les délais de détection de sept incidents, en minutes, sont 5, 8, 12, 12, 14, 40 et 133. (a) Calculez la moyenne et la médiane. (b) Laquelle rapportez-vous à la direction, et que faites-vous du pire incident ?
:::

::: sol
(a) Somme 224 minutes ; moyenne 224 / 7 = **32 minutes** ; médiane (quatrième valeur triée) **12 minutes**. (b) La moyenne vaut 2,7 fois la médiane (32 / 12) parce qu'un incident de 133 minutes tire tout vers le haut. Rapportez la **médiane** pour le fonctionnement courant et le **maximum** à part, avec son post-mortem : c'est l'incident de 133 minutes qui montre où la supervision ne voit rien, et c'est lui qu'on étudie en premier. Avec sept valeurs, un 90e centile n'aurait pas de sens.
:::

::: exo
[Exercice 12 · ★★ — Placer cinq membres etcd]{.tag} Une plateforme Kubernetes a un etcd de cinq membres. Hypothèses de l'énoncé : un membre est disponible 99,9 % du temps quand son rack l'est ($a = 0{,}999$), et chaque rack (alimentation et commutateur de baie) l'est 99,95 % du temps ($r = 0{,}9995$), indépendamment des autres racks.

(a) Avec `quorum.py racks` (lab 16.4), calculez l'indisponibilité du quorum, en minutes par mois de 30 jours, pour : cinq membres dans un rack ; 3 + 2 sur deux racks ; 2 + 2 + 1 sur trois racks ; et, pour comparer, trois membres sur trois racks (1 + 1 + 1). (b) Pourquoi deux racks n'apportent-ils rien ? Énoncez la règle de placement. (c) Que donnerait l'hypothèse d'indépendance seule pour cinq membres, et qu'en concluez-vous ?
:::

::: sol
Commande : `python3 quorum.py racks --a 0.999 --r 0.9995 --layout 5 --layout 3,2 --layout 2,2,1 --layout 1,1,1`.

(a) Un seul rack : indisponibilité de 5,00e-4, soit **21,6 minutes** par mois. Deux racks (3 + 2) : 5,02e-4, soit **21,7 minutes**. Trois racks (2 + 2 + 1) : 3,76e-6, soit **0,16 minute**. Trois membres sur trois racks : 6,74e-6, soit **0,29 minute**.

(b) En 3 + 2, perdre le rack de trois membres suffit à perdre le quorum : il reste deux membres, il en faut trois. Ce rack coûte à lui seul 1 − r = 5e-4, autant qu'un rack unique, et le second rack ajoute un petit risque (s'il tombe, les trois autres membres doivent tous tenir).

Règle : **aucun domaine de panne ne porte plus de membres que le cluster ne tolère de pannes**, ici f = 2, donc au moins trois domaines pour cinq membres. En 2 + 2 + 1, la perte de n'importe quel rack laisse au moins trois membres.

(c) Membres indépendants seuls : 9,99e-9, soit 0,0004 minute par mois. Le modèle avec racks donne, en 2 + 2 + 1, une indisponibilité **376 fois** plus grande : un chiffre calculé sous l'hypothèse d'indépendance est optimiste. Surtout, trois membres bien placés (0,29 minute) font **74 fois** mieux que cinq membres dans un rack (21,6 minutes) : le placement compte plus que le nombre. Ces valeurs de a et r sont des hypothèses ; la méthode s'applique à vos disponibilités mesurées.
:::

::: exo
[Exercice 13 · ★★★ — Lire un exercice de restauration et décider]{.tag} Pendant un exercice sur un etcd de trois membres, `etcdctl endpoint health -w table` affiche (sortie réelle de `etcd_drill.sh`, lab 16.4, cluster jetable sur une seule machine) :

~~~text
┌────────────────────────┬────────┬──────────────┬───────────────────────────┐
│        ENDPOINT        │ HEALTH │     TOOK     │           ERROR           │
├────────────────────────┼────────┼──────────────┼───────────────────────────┤
│ http://127.0.0.1:23791 │   true │    6.04847ms │                           │
│ http://127.0.0.1:23792 │   true │   6.457915ms │                           │
│ http://127.0.0.1:23793 │  false │ 2.001054301s │ context deadline exceeded │
└────────────────────────┴────────┴──────────────┴───────────────────────────┘
~~~

(a) Combien de membres sont sains, combien de pannes supplémentaires le cluster tolère-t-il, et qu'arrive-t-il aux écritures si un autre membre tombe ? (b) Un collègue propose d'ajouter tout de suite un quatrième membre « pour regagner de la marge » avant de réparer le troisième. Que répondez-vous, et dans quel ordre opérez-vous ?

(c) La même plateforme sauvegarde la base de comptabilité de Slurm par un dump quotidien. Avec le débit de l'exemple 5.2 (847,5 jobs par mois de 730 heures), combien de jobs perdent leur comptabilité au pire et en moyenne en cas de restauration ? Et avec un dump toutes les 6 heures ? (d) L'exercice a restauré 100 clés en 1,2 seconde : que vaut cette mesure pour votre RTO ?
:::

::: sol
(a) Deux membres sur trois répondent en environ 6 ms ; le troisième dépasse le délai de 2 secondes (« context deadline exceeded »). Le quorum de 2 est atteint, mais le cluster ne tolère **plus aucune** panne : si un autre membre tombe, le dernier refuse les écritures, comme l'étape 4 du script le montre (« write with two members down: refused »). Dans ce cas, les pods déjà placés peuvent continuer, mais plus aucun nouveau pod n'est placé (section 9.1).

(b) Non. Un quatrième membre porte le quorum à 3 : avec un membre en panne, il faut que les deux sains et le nouveau soient tous en service. Si le nouveau ne rejoint pas le cluster (adresse fausse, disque lent), deux membres sur quatre tournent et le quorum est perdu sans retour : la [FAQ d'etcd](https://etcd.io/docs/v3.7/faq/) décrit ce cas, et etcd refuse par défaut un tel ajout (`strict-reconfig-check`).

L'ordre correct est celui de la FAQ, « remove the member first and then add its replacement » : `etcdctl member remove` du membre en panne (deux membres, quorum 2), puis `etcdctl member add` de son remplaçant (trois membres, quorum 2). Pendant toute l'opération, le quorum reste à 2.

(c) Le débit est de 847,5 / 730 = 1,16 job par heure. Avec un dump quotidien, la perte est au pire de 24 heures, soit 24 × 1,16 = **27,9 jobs** ; si la panne tombe au hasard entre deux dumps, elle vaut en moyenne la moitié, **13,9 jobs**. Avec un dump toutes les 6 heures : au pire **6,97 jobs**, en moyenne **3,48**.

L'arbitrage oppose la charge d'un dump sur la base à la valeur de la comptabilité pour l'équité et les rapports. Dans les deux cas, ce RPO ne vaut que si un dump a déjà été restauré.

(d) Presque rien : 37 ko, un seul membre, une machine locale, aucun réseau. La mesure valide la **procédure**, pas sa durée. Le RTO réel comprend la détection, la décision, l'arrêt des serveurs d'API, la copie du snapshot, la restauration de chaque membre à la taille réelle de la base, le redémarrage et la vérification. Mesurez-le sur un environnement jetable de taille réaliste, étape par étape, comme les jalons d'un incident du chapitre 4.
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux mesurer l'adoption d'une plateforme.** Preuve : les quatre mesures du chapitre 1 calculées sur des données (même synthétiques), avec la loi de Little appliquée à une classe de charge.
-   **Je peux choisir comment partager un GPU.** Preuve : l'exercice 6 refait pour votre cas, avec ce que chaque mécanisme isole ou n'isole pas.
-   **Je peux dresser un modèle de menaces.** Preuve : le tableau de l'exercice 8 refait sur votre propre plateforme, avec risque résiduel.
-   **Je peux chiffrer une astreinte et un budget d'erreur.** Preuve : les exercices 1 et 2 appliqués à votre équipe.
-   **Je peux écrire un post-mortem sans blâme dont les chiffres tiennent.** Preuve : le lab 16.2, avec `postmortem_lint.py` qui répond « ok ».
-   **Je peux écrire une décision contestable.** Preuve : l'ADR du lab 16.1, relue par une personne.
-   **Je peux dimensionner à voix haute.** Preuve : l'exercice 9 refait en trente minutes avec hypothèses dites et effet d'une erreur de MFU chiffré.
-   **Je peux dimensionner et éprouver un plan de contrôle.** Preuve : l'exercice 12 refait pour votre propre placement (membres, racks, alimentations), et un exercice de restauration exécuté (lab 16.4 ou votre plateforme) avec sa durée et ce qui a été perdu.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Votre plateforme affiche 95 % d'utilisation de GPU. Que répondez-vous au directeur qui veut en acheter moins ?* Réponse-type : l'utilisation seule ne dit rien ; il faut l'attente au 90e centile par classe et le goodput. Une utilisation haute avec une attente qui dépasse l'objectif signale un manque de capacité ; une utilisation haute faite de jobs bloqués signale un défaut de supervision. Je montre les quatre mesures avant de décider.
2.  *Votre équipe compte trois personnes et le service doit être disponible en permanence. Que faites-vous ?* Réponse-type : au plus 25 % du temps d'astreinte par personne, ce qui exige quatre personnes pour une seule personne d'astreinte à la fois et huit pour un titulaire et un second. À trois, je limite l'astreinte aux heures ouvrées, j'automatise les reprises sur panne matérielle pour que l'astreinte n'ait rien à faire la nuit, et je le dis au directeur avec le coût de l'alternative.
3.  *Un job de 256 GPU a stagné deux heures sans que personne ne le voie. Comment travaillez-vous ?* Réponse-type : je reconstitue les jalons (anomalie, détection, atténuation) dans un post-mortem sans blâme ; la durée de détection est la plus longue, donc l'action principale est une alerte sur l'absence de progrès plutôt que sur l'utilisation du GPU, avec un propriétaire et une échéance. Je vérifie que les chiffres du texte égalent ceux du journal.

## Lectures et références {#refs}

Le *SRE Book* (Beyer, Jones, Petoff et Murphy, dir., O'Reilly, 2016) est publié en ligne par Google ; les pages web ci-dessous ont été lues le 2026-10-24, et le 2026-10-25 pour celles du chapitre 9.

-   Google. [*Site Reliability Engineering*, chap. *Embracing Risk*](https://sre.google/sre-book/embracing-risk/) : budget d'erreur et SLO (chapitre 4).
-   Google. [*Site Reliability Engineering*, chap. *Being On-Call*](https://sre.google/sre-book/being-on-call/) : limites de l'astreinte et taille d'équipe (chapitres 4 et 6).
-   Google. [*Site Reliability Engineering*, chap. *Postmortem Culture*](https://sre.google/sre-book/postmortem-culture/) : le post-mortem sans blâme (chapitre 4).
-   Google. [*Site Reliability Engineering*, chap. *Eliminating Toil*](https://sre.google/sre-book/eliminating-toil/) : définition du toil (chapitre 6).
-   SchedMD. [*Slurm Upgrade Guide*](https://slurm.schedmd.com/upgrades.html) : ordre des mises à jour, fenêtre de compatibilité, retour arrière (chapitre 5).
-   JupyterHub. [*Documentation*](https://jupyterhub.readthedocs.io/en/stable/) : hub multi-utilisateur et *spawners* (chapitre 2).
-   Ohio Supercomputer Center. [*Open OnDemand — Setup Interactive Apps*](https://osc.github.io/ood-documentation/latest/how-tos/app-development/interactive/setup.html) : applications interactives sur les nœuds de calcul ; la [liste des adaptateurs](https://osc.github.io/ood-documentation/latest/installation/resource-manager/slurm.html) (Slurm, Kubernetes…) se trouve dans la même documentation (chapitre 2).
-   NVIDIA. [*MIG User Guide*](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/introduction.html) et [*GPU sharing, GPU Operator*](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html) : MIG et tranches de temps (chapitre 2).
-   Kubernetes. [*Multi-tenancy*](https://kubernetes.io/docs/concepts/security/multi-tenancy/) et [*Pod Security Standards*](https://kubernetes.io/docs/concepts/security/pod-security-standards/) : locataires et profils de sécurité (chapitre 3).
-   Kubernetes. [*Secrets*](https://kubernetes.io/docs/concepts/configuration/secret/), [*Images*](https://kubernetes.io/docs/concepts/containers/images/), [*Auditing*](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/) et [*Network Policies*](https://kubernetes.io/docs/concepts/services-networking/network-policies/) : secrets, empreintes d'images, audit, isolation réseau des pods (chapitre 3 ; *Network Policies* lue le 2026-10-25).
-   NVIDIA. [*XID Errors, Xid catalog*](https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html) : sens de l'Xid 79 (« GPU has fallen off the bus ») que montre le journal synthétique du lab 16.2.
-   Ongaro, D. et Ousterhout, J. [*In Search of an Understandable Consensus Algorithm*](https://www.usenix.org/conference/atc14/technical-sessions/presentation/ongaro), USENIX ATC, 2014 : lire §5.2 (élection d'un leader) et §5.3 (réplication du journal) pour la majorité et l'unicité du leader par mandat (chapitre 9).
-   etcd. [*Frequently Asked Questions*](https://etcd.io/docs/v3.7/faq/), documentation v3.7 : taille des majorités, tolérance aux pannes, taille maximale d'un cluster, ordre de remplacement d'un membre (chapitre 9).
-   Kubernetes. [*Operating etcd clusters for Kubernetes*](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/) et [*Options for Highly Available Topology*](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/ha-topology/) : sauvegarde et restauration d'etcd, cinq membres en production, topologies empilée et externe (chapitre 9).

## Sources et portée {#sources}

### Documenté {#documente}

Les définitions du budget d'erreur, les limites de 50 % et 25 %, le minimum de huit ingénieurs, le plafond de deux incidents par garde de 12 heures, la définition du toil et du post-mortem sans blâme viennent du SRE Book ; l'ordre de mise à jour de Slurm, l'absence de retour arrière et la fenêtre de compatibilité viennent du guide de mise à jour de SchedMD ; les propriétés de MIG et des tranches de temps, de la multi-location, des Secrets, des empreintes d'images, de l'audit et des `NetworkPolicy`, ainsi que le sens de l'Xid 79, viennent des pages citées, lues pour ce module. Les citations en anglais sont reproduites telles que ces pages les contiennent (texte lu le 2026-10-24, conservé par `tools/fetch_text.py`). Ont été lus le 2026-10-25 : la page *Network Policies* de Kubernetes, le délai par défaut des collectives NCCL dans la documentation de `torch.distributed`, le pic BF16 de la page produit du H100 et les taux de panne de Kokolis et coauteurs (6,5 pannes pour mille nœuds-jours, MTTF de 7,9 heures à 1 024 GPU).

Pour le chapitre 9 (pages lues le 2026-10-25) : la règle de majorité et l'unicité du leader par mandat viennent de l'article de Raft ; les tailles de majorité, la tolérance aux pannes, la limite de sept membres, l'effet de la taille sur les écritures et l'ordre de remplacement d'un membre, de la FAQ d'etcd v3.7 ; les cinq membres en production, la sauvegarde et la restauration d'etcd, l'arrêt des serveurs d'API avant restauration et les deux topologies, de la documentation de Kubernetes. Le basculement de `slurmctld`, `SlurmctldTimeout`, `StateSaveLocation` et le secours de `slurmdbd` viennent de `slurm.conf`, de `slurmdbd.conf` et du guide d'administration de Slurm 26.05, la liste minimale des sauvegardes, du guide de mise à jour ; la tolérance aux pannes du GCS, de la documentation de Ray ; `mariadb-dump`, de la documentation MariaDB. Les principes GitOps, Argo CD, Flux, `promtool test rules`, l'abandon de kubeval, les limites de kubeconform et la définition du canarying viennent des pages citées. Les deux incidents viennent de leurs post-mortems publics. La part des offres qui citent les systèmes distribués, la CI/CD, GitOps ou les composants de Kubernetes vient du [relevé du marché](../../market/index.html).

### Recommandé {#recommande}

Les quatre mesures d'adoption, la répartition en cohortes, l'obligation d'un signal de révision dans une ADR, le canal unique de demandes, la fiche d'exploitation exécutée par un tiers, la grille d'entretien et les questions à poser en fin d'entretien sont des choix de ce parcours, pas des normes. Le taux de 0,0002 panne par GPU-heure de l'exemple 8.1 et de l'exercice 9 est une hypothèse d'exercice, volontairement pessimiste. Il en va de même, au chapitre 9, de la règle de placement (aucun domaine de panne ne porte plus de membres que le cluster ne tolère de pannes), de l'exercice de restauration à date fixe avec RTO et RPO mesurés, de la liste des contrôles avant fusion, des trois critères de retour arrière et des cinq questions d'entretien.

### À vérifier {#a-verifier}

Le journal d'incident, le cahier des charges du projet 6, les données des exercices et les réponses d'entretien sont **fictifs ou synthétiques**. Les profils MIG (taille des instances) dépendent du GPU : l'hypothèse de 10 Go de l'exercice 6 est à vérifier dans le guide MIG de votre matériel. Les seuils de la grille d'entretien sont un repère d'entraînement. Les durées des séances et des labs sont des estimations de l'auteur, non mesurées auprès d'un lecteur. La fenêtre de compatibilité de Slurm change d'une version à l'autre (deux, puis trois versions majeures précédentes) : relisez le guide pour votre version cible. La liste des adaptateurs d'Open OnDemand est celle de la documentation 4.2, lue le 2026-10-24 à une adresse `latest/` qui suivra les versions suivantes. Le comportement du lanceur interactif sur votre ordonnanceur n'a pas été exécuté dans le bac à sable (aucun JupyterHub ni Open OnDemand n'y est installé).

Pour le chapitre 9 : les disponibilités de membre et de rack de l'exemple 9.1 et de l'exercice 12 sont des **hypothèses**, et l'indépendance des pannes en est une autre. L'exercice de restauration a tourné avec etcd 3.7.0 sur une seule machine, sans réseau ni base de taille réelle : sa durée n'est pas un RTO. La répartition des commandes entre `etcdctl` et `etcdutl` change d'une version d'etcd à l'autre, et le stockage RocksDB du GCS de Ray est en alpha : relisez la documentation de votre version. La haute disponibilité de Slurm, les topologies de Kubernetes, Argo CD, Flux et kubeconform n'ont pas été exécutés dans le bac à sable.

### Hors périmètre {#hors-perimetre}

La conformité réglementaire (RGPD, certifications), la gestion des ressources humaines, le recrutement, la négociation budgétaire détaillée (leviers et calendrier : [module 15, chapitre 7](../finops-capacity/index.html#ch7)), la sécurité du noyau et des hyperviseurs, et l'exploitation réelle d'un JupyterHub ou d'Open OnDemand. Pour le chapitre 9 : les preuves formelles de Raft ou de Paxos, les pannes byzantines, la réplication de la base de comptabilité elle-même (MariaDB), l'installation et l'exploitation d'Argo CD ou de Flux, et la livraison progressive des applications servies aux utilisateurs.
