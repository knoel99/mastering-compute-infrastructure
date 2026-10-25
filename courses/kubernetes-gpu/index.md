---
title: "Kubernetes pour l'IA : GPU, files d'attente et gang scheduling"
subtitle: "Module 12 · Phase 4 · 28 h"
description: "Ce que Kubernetes sait et ne sait pas faire pour l'entraînement : GPU, MIG et DRA, Kueue et Volcano, JobSet et Kubeflow Trainer, topologie, et comparaison honnête avec Slurm."
module:
  id: kubernetes-gpu
  number: 12
  phase: 4
  hours: 28
  level: 2
prerequisites: [linux-systems, slurm, distributed-training]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs non tous vérifiés : le lab 12.2 exige un cluster GPU", class: unverified}
labs:
  - {id: kueue-manifests, kind: sandbox}
  - {id: jobset-training, kind: cluster}
  - {id: slurm-vs-k8s, kind: sandbox}
  - {id: mini-control-plane, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** votre cluster Kubernetes sait lancer des milliers de pods ; sait-il lancer un entraînement qui exige 128 GPU *ensemble ou pas du tout*, le mettre en file derrière d'autres équipes, le préempter proprement, et le replacer si un nœud meurt ? Et si oui, à quel prix d'exploitation par rapport à Slurm ?

Ce module ne réexplique pas Kubernetes : si vous ne l'avez jamais exploité, la section 1.1 en donne le minimum. Il se concentre sur ce qui change quand la ressource rare est un GPU et que la charge est un travail fini, parallèle et fragile. Les versions sont celles lues sur les sources officielles le 24 octobre 2026 ; les comportements annoncés comme « observés » viennent d'un vrai plan de contrôle Kubernetes 1.37.1 démarré dans le bac à sable du module.

::: key
[Règle de ce module]{.tag} Kubernetes décide **pod par pod** ; un entraînement est **un tout**. Chaque outil du module restaure une atomicité à un niveau différent : le quota (Kueue), le groupe de pods (ordonnancement de groupe, *gang scheduling*), le placement dans la topologie (TAS), le redémarrage (JobSet). Si vous ne savez pas dire de quel niveau parle un outil, vous ne savez pas encore ce qu'il garantit.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 28 h, dont environ 11 h de lecture, 10 h de labs et 7 h d'exercices |
| Niveau d'entrée | 2 : Linux, Slurm et entraînement distribué (modules 1, 5 et 9) ; pour Kubernetes, les notions de la section 1.1 suffisent, ou le tutoriel officiel [*Learn Kubernetes Basics*](https://kubernetes.io/docs/tutorials/kubernetes-basics/) avant de commencer |
| Prérequis | [Module 1 — Linux, systèmes et diagnostic de performance](../linux-systems/index.html), [Module 5 — Slurm et exploitation d'un cluster HPC](../slurm/index.html), [Module 9 — Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline](../distributed-training/index.html) |
| Pour qui | Cœur : la couche GPU de Kubernetes, la mise en file et le placement des entraînements ; si vous exploitez déjà Kubernetes, survolez les rappels et travaillez les chapitres sur les GPU, les files d'attente et le gang scheduling. |
| Livrable | un dossier de manifestes de files et de quotas validé, une trace de simulation commentée, une matrice de décision Slurm / Kubernetes défendue par écrit |
| Environnement | un portable Linux sans GPU suffit pour les labs 12.1, 12.3 et 12.4 (le lab 12.4 télécharge environ 350 Mo) ; le lab 12.2 ne s'exécute pour de bon que sur un cluster GPU, dont le coût dépend du fournisseur : lisez sa page de prix le jour même |
| Projets liés | [Projet 4 — Placement multi-fournisseurs sensible aux coûts](../../projects/multi-provider-scheduler/index.html), [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Dire ce que le plugin de périphériques, l'opérateur GPU, MIG, le partage par tranches de temps (*time-slicing*) et DRA permettent et interdisent (chapitre 2).
-   Écrire et valider des files, quotas, priorités et règles de préemption pour Kueue, et prédire qui est préempté (chapitre 3).
-   Expliquer pourquoi un ordonnancement pod par pod peut bloquer deux entraînements, et quelle couche y remédie (chapitres 1 et 3).
-   Lancer un entraînement multi-nœuds avec un Job indexé, JobSet ou Kubeflow Trainer, et décrire son redémarrage (chapitre 4).
-   Raisonner sur la topologie, la fragmentation des GPU et le coût d'une panne de nœud (chapitre 5).
-   Dimensionner les volumes de *checkpoints* (points de reprise) et l'effet d'un démarrage massif d'images (chapitre 6).
-   Choisir entre Slurm, Kubernetes et Slurm sur Kubernetes avec une grille explicite et sa robustesse (chapitre 7).
-   Planifier une mise à jour, un cloisonnement et un suivi de coût pour une flotte GPU sous Kubernetes (chapitre 8).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 4 — Plateforme cloud-native et multi-fournisseurs** (semaines 33-44) : placer, observer et facturer des charges sur plusieurs fournisseurs.
-   **S'appuie sur** : [module 1 — Linux, systèmes et diagnostic de performance](../linux-systems/index.html), [module 5 — Slurm et exploitation d'un cluster HPC](../slurm/index.html), [module 9 — Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline](../distributed-training/index.html).
-   **Prépare** : [module 13 — Flotte multi-fournisseurs : SkyPilot, GPU clouds, hyperscalers et centres HPC](../multi-cloud/index.html), [module 16 — Plateforme interne, sécurité, production et leadership](../platform-leadership/index.html).
-   **Projets qui s'en servent** : [Projet 4 — Placement multi-fournisseurs sensible aux coûts](../../projects/multi-provider-scheduler/index.html), [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html).
-   **Compétences demandées dans les offres d'emploi et travaillées ici** : Python, Kubernetes, Entraînement distribué (PyTorch, Megatron, DeepSpeed…), Checkpoint, tolérance aux pannes, Conception d'ordonnanceur, Slurm, Conteneurs, Systèmes de fichiers parallèles, FinOps, coûts, Planification de capacité, Sécurité, conformité, Systèmes distribués, Santé matérielle (burn-in, diagnostics, RMA) (voir [l'analyse du marché](../../market/index.html#couverture)).
<!-- /gen:place -->

### Plan de séances {#seances}

Onze séances, soit 28 h : cinq de 3 h, deux de 2,5 h et quatre de 2 h. Le niveau ne diminue jamais d'une séance à la suivante.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 2 h | 1 | ch. 1 Ce que Kubernetes apporte et ce qui change avec les GPU | Questions de positionnement ; lecture de l'exemple 1.1 |
| 2 | 3 h | 1 | ch. 2 §2.1 à §2.3 : plugin de périphériques, opérateur GPU, runtime | Lab 12.4 : lire `lib.sh`, démarrer le plan de contrôle, appliquer le pod GPU ; Ex. 1 |
| 3 | 2.5 h | 1 | ch. 2 §2.4 à §2.6 : MIG, *time-slicing*, DRA | Ex. 2, 3 |
| 4 | 3 h | 2 | ch. 3 §3.1 à §3.3 : Kueue, quotas, emprunt | Lab 12.1 partie A (manifestes) ; Ex. 4 |
| 5 | 3 h | 2 | ch. 3 §3.4 à §3.7 : préemption, Volcano, ordonnancement de groupe natif | Lab 12.1 partie B (modèle d'admission) ; Lab 12.4 partie A (ordonnancement de groupe natif) ; Ex. 5, 6 |
| 6 | 3 h | 2 | ch. 4 Charges d'entraînement : Jobs indexés, JobSet, Trainer, KubeRay, réseau | Lab 12.2 ; Ex. 7 |
| 7 | 2 h | 2 | ch. 5 Topologie, placement et pannes de nœud | Lab 12.4 partie B (fragmentation et *bin packing*) ; Ex. 8, 12 |
| 8 | 2 h | 2 | ch. 6 Stockage et données | Ex. 9 |
| 9 | 3 h | 3 | ch. 7 Slurm ou Kubernetes ? | Lab 12.3 ; Ex. 10 |
| 10 | 2.5 h | 3 | ch. 8 Exploitation : mises à jour, sécurité, multi-tenance, coûts | Lab 12.4 partie C (validation par un serveur d'API) ; Ex. 11, 13 |
| 11 | 2 h | 3 | Checkpoint de sortie, ouverture du Projet 4 | |

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

**À ne pas survoler.** Les files d'attente (Kueue), le gang scheduling et le partage des GPU sont ce qui distingue Kubernetes pour l'IA de Kubernetes pour des services.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le checkpoint de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si elles vous semblent routinières, lisez le chapitre 3 et le chapitre 7, puis passez aux exercices ★★★.

1.  **Pod par pod.** Un Job crée 8 pods qui demandent chacun un nœud entier de 8 GPU. Le cluster a 6 nœuds libres. Que fait l'ordonnanceur par défaut ?

2.  **Un demi-GPU.** Pourquoi `nvidia.com/gpu: 0.5` n'existe-t-il pas, et quelles sont les trois façons de partager un GPU entre pods ?

3.  **Quota et capacité.** Une file Kueue a un quota de 32 GPU et un Job de 32 GPU y est « admis ». Pourquoi ses pods peuvent-ils rester `Pending` ?

::: sol
**Réponses.**

1.  Il lie les pods un par un à tout nœud qui convient : 6 pods sont liés, 2 restent `Pending`, et les 48 GPU liés ne servent à rien tant que le Job est incomplet. Voir l'exemple 1.1, qui reproduit exactement ce cas sur un vrai plan de contrôle.

2.  Les ressources étendues d'un plugin de périphériques sont des **entiers** qu'on ne peut pas surallouer. Trois mécanismes partagent un GPU : MIG (partitions matérielles isolées), le partage par tranches de temps (*time-slicing* : réplicas sans isolation) et DRA (réclamations qui décrivent le partage). Voir le chapitre 2.

3.  Le quota de Kueue est une comptabilité : il décide quand un Job peut créer ses pods. Le placement reste fait par l'ordonnanceur de Kubernetes, qui peut échouer si les nœuds sont fragmentés, drainés ou occupés par autre chose. Voir les chapitres 3 et 5.
:::

## 1. Ce que Kubernetes apporte et ce qui change avec les GPU {#ch1}

Ce chapitre fait l'inventaire : ce que Kubernetes sait déjà faire et qui reste vrai, ce qui devient faux ou insuffisant dès que la ressource est un GPU et la charge un entraînement, et la correspondance avec les notions de Slurm du module 5.

### 1.1. Rappel : ce que Kubernetes sait déjà faire

Si vous exploitez déjà Kubernetes, survolez cette section ; sinon, elle donne le minimum pour la suite. Kubernetes repose sur une **boucle de réconciliation** ([*Controllers*](https://kubernetes.io/docs/concepts/architecture/controller/)) : un état désiré déclaré dans l'API, des contrôleurs qui le rapprochent de l'état observé, un ordonnanceur (*scheduler*) qui attribue les *pods* (un ou plusieurs conteneurs lancés ensemble sur un nœud) aux nœuds, un *kubelet* qui les exécute sur chaque nœud. Tout cela reste vrai pour l'IA, et c'est précisément l'argument en faveur de Kubernetes : une seule plateforme, une API unique, des opérateurs pour tout ce qui est spécifique.

Trois mécanismes comptent pour la suite. Les **opérateurs** (une ressource personnalisée plus un contrôleur) sont la forme standard d'extension : Kueue, JobSet, l'opérateur GPU et KubeRay en sont tous. Les **étiquettes, taints et sélecteurs** servent à diriger les pods vers des nœuds. Les **quotas par espace de noms** limitent la consommation. Aucun des trois ne sait, seul, exprimer « ces 16 pods ensemble ou aucun ».

### 1.2. L'unité d'ordonnancement est le pod

L'ordonnanceur par défaut traite **un pod à la fois** : il filtre les nœuds qui conviennent, les note, lie le pod au meilleur, puis passe au suivant. Un Job de 8 pods est, pour lui, 8 demandes indépendantes. Cela convient à un service web ; cela ne convient pas à un entraînement synchrone, dont chaque pas exige que tous les rangs soient présents.

::: ex
[Exemple 1.1 — Un Job de 64 GPU sur 6 nœuds de 8 GPU]{.tag} Le lab 12.4 démarre un vrai plan de contrôle Kubernetes v1.37.1 sans kubelet, avec 6 nœuds factices annonçant chacun 8 `nvidia.com/gpu`. Un Job indexé de 8 pods, chacun demandant 8 GPU, est créé sans option particulière. Sortie capturée le 24 octobre 2026 dans le bac à sable du module (Linux 6.18, 4 vCPU) :

~~~text
bound pods: 6 of 8 (the 2 others are Pending)
scheduler message for a pending pod:
0/6 nodes are available: 6 Insufficient nvidia.com/gpu.
~~~

Six pods sont liés, soit $6 \times 8 = 48$ GPU réservés ; deux restent en attente d'un nœud qui n'existera pas. Le Job ne progresse pas (un entraînement distribué ne démarre pas avec 6 rangs sur 8), mais ses 48 GPU sont inaccessibles aux autres. C'est le problème que tout le reste du module traite, à des niveaux différents.
:::

### 1.3. Les GPU sont des entiers, pas du CPU

Le CPU et la mémoire se décrivent en `requests` et `limits`, se surallouent, se partagent finement. Un GPU exposé par un plugin de périphériques est une **ressource étendue** : un entier, qui ne se suralloue pas et ne se partage pas entre conteneurs. Un pod qui demande 1 GPU en obtient un entier, avec ses 80 Go de mémoire, qu'il en ait besoin ou non. Le chapitre 2 présente les trois moyens de partager (MIG, *time-slicing*, DRA) et ce que chacun coûte.

Deuxième différence : un GPU est un composant **qui tombe en panne en cours de route** et dont la panne ne ressemble pas à celle d'un conteneur (erreur ECC, chute de débit NVLink, XID). Kubernetes sait remplacer un pod mort ; il ne sait pas, seul, qu'un nœud « sain » pour lui est devenu inutilisable pour l'entraînement. La santé GPU est un chantier propre (module 14 et [Projet 5](../../projects/gpu-observability/index.html)).

### 1.4. Correspondance avec Slurm

Le tableau suivant est un **jugement de ce parcours**, pas une équivalence exacte : chaque ligne cache des différences de sémantique, signalées au fil des chapitres.

| Notion Slurm (module 5) | Équivalent Kubernetes | Où le voir |
|---|---|---|
| Job `sbatch` multi-nœuds | Job indexé, JobSet, TrainJob | ch. 4 |
| Allocation atomique de N nœuds | ordonnancement de groupe : Kueue (quota), Volcano ou gang natif (placement) | ch. 3 |
| Partition | *flavor* de Kueue, groupe de nœuds, étiquettes | ch. 3 et 5 |
| Compte et association | espace de noms, LocalQueue, ClusterQueue | ch. 3 |
| QOS et préemption | WorkloadPriorityClass et politiques de préemption | ch. 3 |
| Équité (*fairshare*) | emprunt et récupération dans une cohorte ; *fair sharing* de Kueue | ch. 3 |
| GRES (`gpu:8`) | ressource étendue, MIG, DRA | ch. 2 |
| Topologie (`topology.conf`) | étiquettes de nœuds, TAS | ch. 5 |
| Prolog et contrôle de santé | validateurs de l'opérateur GPU, taints, réparation externe | ch. 5 et 8 |
| `sacct`, `sreport` | objets Workload, métriques Prometheus ; pas de base de comptabilité native | ch. 8 |

### 1.5. Trois niveaux d'atomicité

Ce qu'un entraînement attend de la plateforme se décompose en trois garanties, que des composants différents fournissent.

-   **Atomicité du quota.** Le Job n'est démarré que si la file a le droit à *tous* les GPU demandés. C'est le rôle de Kueue (chapitre 3) ou de Volcano.
-   **Atomicité du placement.** Les pods ne sont liés aux nœuds que si *tous* peuvent l'être. Un ordonnanceur de groupe l'assure : Volcano, KAI Scheduler, ou, depuis peu, l'ordonnanceur de Kubernetes lui-même.
-   **Atomicité du cycle de vie.** Si un pod meurt, tout le groupe redémarre ensemble. C'est le rôle de JobSet et de Trainer (chapitre 4).

État au 24 octobre 2026 d'après la documentation de Kubernetes : l'ordonnancement de groupe natif (API `Workload` et `PodGroup`, `scheduling.k8s.io/v1beta1`) est **bêta depuis la v1.37, désactivé par défaut** (porte `GenericWorkload`) ; son intégration au Job est **alpha depuis la v1.36**, et l'est toujours en v1.37 (porte `WorkloadWithJob`, d'après la [table des portes de fonctionnalités](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)). Le chapitre 3 le fait fonctionner dans le bac à sable.

### 1.6. L'échelle du plan de contrôle n'est pas le problème

La documentation de Kubernetes v1.37 annonce la prise en charge de clusters jusqu'à 5 000 nœuds, 110 pods par nœud, 150 000 pods et 300 000 conteneurs au total. Une flotte d'entraînement a peu de pods et beaucoup de GPU par pod.

::: ex
[Exemple 1.2 — Où se situe une flotte de 1 024 GPU]{.tag} Avec 8 GPU par nœud, 1 024 GPU font $1024 / 8 = 128$ nœuds, soit $128 / 5000 = 2{,}56\ \%$ de la limite documentée. Un Job par nœud donne quelques centaines de pods : la limite de pods n'est pas atteinte, et l'échelle du plan de contrôle ne décide pas du choix Kubernetes ou Slurm. Ce qui le décide, ce sont les sémantiques d'ordonnancement, objet de ce module. Le calcul a été refait par un script Python du module.
:::

::: recap
Points clés — chapitre 1

-   Kubernetes ordonnance **pod par pod** ; un entraînement est un groupe qui ne progresse qu'au complet.
-   Un GPU est une ressource étendue entière : ni surallocation, ni partage fin sans mécanisme dédié.
-   Trois atomicités à distinguer : quota (Kueue), placement (gang), cycle de vie (JobSet, Trainer).
-   Ordonnancement de groupe natif : bêta et désactivé par défaut en v1.37 ; intégration au Job : alpha depuis la v1.36, toujours alpha en v1.37.
-   À 1 024 GPU, le plan de contrôle est loin de ses limites documentées : le sujet est la sémantique.
:::

## 2. Exposer des GPU : plugin, opérateur, MIG, time-slicing, DRA {#ch2}

Ce chapitre suit le chemin d'un GPU depuis le pilote du nœud jusqu'au conteneur, puis présente les trois manières de le partager. Les noms de versions sont ceux de la documentation consultée le 24 octobre 2026.

### 2.1. Le plugin de périphériques

Le mécanisme historique est le **plugin de périphériques** (*device plugin*), stable depuis Kubernetes v1.26. Un processus du nœud s'enregistre auprès du kubelet par gRPC, annonce un nom de ressource de la forme `domaine/type` (par exemple `nvidia.com/gpu`) et la liste de ses périphériques. Le kubelet publie le décompte dans l'état du nœud ; l'ordonnanceur n'a plus qu'à comparer des entiers.

D'après la documentation, le plugin sert trois appels principaux : `ListAndWatch` pour signaler les périphériques et leur santé, `Allocate` au moment de créer le conteneur pour préparer l'accès, et `GetPreferredAllocation` pour suggérer un sous-ensemble préférable. Sa socket Unix vit sous `/var/lib/kubelet/device-plugins/`, chemin non configurable. Un plugin doit servir son gRPC *avant* de s'enregistrer.

::: def
[Ressource étendue]{.tag} Ressource dont le nom est de la forme `domaine/type`, annoncée par un plugin ou ajoutée par un administrateur. Elle n'existe que sous forme **entière**, ne peut pas être surallouée et ne se partage pas entre conteneurs. Pour un GPU, elle se déclare sous `limits` ; si `requests` est présent, il doit être égal à `limits`, et `requests` seul est refusé (documentation « Schedule GPUs »).
:::

Le fichier `manifests/pod-device-plugin.yaml` du lab 12.4 montre un pod qui demande un GPU et choisit un modèle par sélecteur de nœud ; le serveur d'API réel du lab l'accepte.

~~~yaml
spec:
  nodeSelector:
    nvidia.com/gpu.product: NVIDIA-H100-80GB-HBM3   # étiquette publiée par GPU Feature Discovery
  containers:
    - name: cuda
      resources:
        limits:
          nvidia.com/gpu: 1
~~~

### 2.2. L'opérateur GPU

Installer à la main le pilote, le plugin, le *runtime* et les étiquettes sur chaque nœud ne tient pas à l'échelle. L'**opérateur GPU de NVIDIA** (*GPU Operator*) automatise l'ensemble : d'après sa documentation, il gère les pilotes NVIDIA, le plugin de périphériques, le *NVIDIA Container Toolkit*, l'étiquetage automatique par GPU Feature Discovery (GFD), la supervision par DCGM, et d'autres composants. Au 24 octobre 2026, la page d'installation indique la version 26.7.2.

Deux points pratiques à retenir. Si le cluster applique Pod Security Admission, l'espace de noms de l'opérateur doit porter l'étiquette `pod-security.kubernetes.io/enforce=privileged` (page d'installation) : ses composants s'exécutent en mode privilégié (voir le chapitre 8). Et les étiquettes publiées par GFD, comme `nvidia.com/gpu.product` ou `nvidia.com/mig.config`, deviennent le vocabulaire de vos sélecteurs, de vos *flavors* Kueue et de vos règles de topologie.

### 2.3. Le runtime et CDI

Le conteneur doit voir les fichiers de périphériques et les bibliothèques du pilote. Le **NVIDIA Container Toolkit** s'en charge, de plus en plus via **CDI** (*Container Device Interface*), une spécification ouverte qui décrit ce que signifie « accéder à un périphérique » de façon identique pour tous les *runtimes*. D'après la documentation du toolkit, la génération de spécifications CDI existe depuis la version 1.12.0, et depuis la 1.18.0 un service systemd (`nvidia-cdi-refresh`) génère et met à jour la spécification dans `/var/run/cdi/nvidia.yaml`.

La documentation précise que ce service ne couvre pas certains cas, où la régénération doit être déclenchée à la main : vérifiez-le avant une mise à jour de pilote en production.

<figure class="fig">
<svg viewBox="0 0 640 250" role="img" aria-labelledby="gpt gpd" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit"><title id="gpt">Du pod au GPU</title><desc id="gpd">Un pod demande nvidia.com/gpu ; l'ordonnanceur compare des entiers ; le kubelet appelle le plugin, qui renvoie des instructions au runtime.</desc><style>.fb{fill:var(--side-bg);stroke:currentColor;stroke-width:2}.ft{fill:currentColor;font-size:12px;text-anchor:middle}.fh{font-size:14px;font-weight:700}.fa{stroke:var(--accent);stroke-width:2.5;fill:none}.fd{stroke-dasharray:5 4}.fz{fill:none;stroke:var(--accent);stroke-width:2;stroke-dasharray:6 4}.fx{fill:var(--accent);font-weight:700}.s1{fill:currentColor;fill-opacity:.35;stroke:currentColor}.s2{fill:var(--accent);stroke:currentColor}.s0{fill:none;stroke:currentColor}</style><defs><marker id="gpa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs><rect class="fb" x="10" y="20" width="130" height="60" rx="6"/><text class="ft fh" x="75" y="46">Pod</text><text class="ft" x="75" y="64">limits : gpu 1</text><rect class="fb" x="190" y="20" width="130" height="60" rx="6"/><text class="ft fh" x="255" y="46">Ordonnanceur</text><text class="ft" x="255" y="64">compare des entiers</text><rect class="fb" x="370" y="20" width="130" height="60" rx="6"/><text class="ft fh" x="435" y="46">Nœud</text><text class="ft" x="435" y="64">allocatable : gpu 8</text><rect class="fb" x="190" y="150" width="130" height="60" rx="6"/><text class="ft fh" x="255" y="176">Kubelet</text><text class="ft" x="255" y="194">appelle Allocate</text><rect class="fb" x="370" y="150" width="130" height="60" rx="6"/><text class="ft fh" x="435" y="176">Plugin GPU</text><text class="ft" x="435" y="194">ListAndWatch, santé</text><rect class="fb" x="520" y="85" width="115" height="60" rx="6"/><text class="ft fh" x="577.5" y="111">Runtime</text><text class="ft" x="577.5" y="129">CDI, /dev/nvidia*</text><path class="fa" d="M140 50L188 50" marker-end="url(#gpa)"/><path class="fa" d="M320 50L368 50" marker-end="url(#gpa)"/><path class="fa fd" d="M435 80L435 148" marker-end="url(#gpa)"/><path class="fa" d="M368 180L322 180" marker-end="url(#gpa)"/><path class="fa" d="M500 170L540 147" marker-end="url(#gpa)"/><text class="ft" x="320" y="238">Le plugin annonce des entiers au kubelet ; au démarrage du conteneur, il renvoie les périphériques à exposer.</text></svg>
<figcaption>Le chemin d'un GPU dans Kubernetes avec un plugin de périphériques : l'ordonnanceur ne voit que des entiers, le plugin et le runtime font le travail concret.</figcaption>
</figure>

::: note
[Un point de panne à connaître]{.tag} D'après la documentation du plugin de périphériques, quand un périphérique est déclaré défectueux, le kubelet diminue le décompte *allouable* de la ressource (la capacité ne change pas), mais les pods déjà affectés **restent affectés** à ce périphérique : leur code se met à échouer, et le pod passe en `Failed` ou en boucle de redémarrage. Depuis la v1.36 (bêta, activée par défaut, porte `ResourceHealthStatus`), le champ `allocatedResourcesStatus` du statut de conteneur indique la santé de chaque périphérique affecté. La réparation d'un nœud dont le GPU est dégradé reste une boucle d'exploitation à construire (chapitre 5).
:::

### 2.4. MIG : des partitions matérielles

Le [module 6, §9.3](../provisioning/index.html#partager-un-gpu-mig-time-slicing-mps-et-vgpu) est la référence du parcours sur les garanties d'un GPU partagé (passthrough, MIG, vGPU, MPS, *time-slicing*). Les sections 2.4 et 2.5 n'en reprennent que l'angle Kubernetes : ce que l'opérateur GPU configure, et ce que l'ordonnanceur voit.

Le **Multi-Instance GPU (MIG)** découpe un GPU de génération Ampere ou plus récente en instances isolées matériellement. L'opérateur déploie un *MIG Manager* qui applique la configuration voulue quand on change l'étiquette `nvidia.com/mig.config` du nœud (par exemple `all-1g.10gb`) ; l'état se lit dans `nvidia.com/mig.config.state` (`pending`, `success`, ou `rebooting` si l'option de redémarrage est activée). La documentation précise que le MIG Manager exige qu'aucune charge utilisateur ne tourne sur les GPU concernés, ce qui impose de vider le nœud avant de changer de profil.

Deux stratégies existent : `single`, où tous les GPU du nœud passent en MIG avec le même profil et restent annoncés comme `nvidia.com/gpu`, et `mixed`, où des profils différents coexistent et sont annoncés sous des noms de ressources distincts. Voici les profils du H100 80 Go (PCIe et SXM5) d'après le guide MIG de NVIDIA :

| Profil | Part de la mémoire | Part des SM | Instances au maximum |
|---|---|---|---|
| `1g.10gb` | 1/8 | 1/7 | 7 |
| `1g.20gb` | 1/4 | 1/7 | 4 |
| `2g.20gb` | 2/8 | 2/7 | 3 |
| `3g.40gb` | 4/8 | 3/7 | 2 |
| `4g.40gb` | 4/8 | 4/7 | 1 |
| `7g.80gb` | pleine | 7/7 | 1 |

::: ex
[Exemple 2.1 — Que perd-on en découpant ?]{.tag} Sept instances `1g.10gb` occupent $7/7$ des SM mais $7/8$ de la mémoire : 10 Go restent inutilisables. Deux instances `3g.40gb` occupent toute la mémoire ($2 \times 4/8$) mais seulement $6/7$ des SM ; trois `2g.20gb` occupent $6/7$ des SM et $6/8$ de la mémoire. Aucun découpage homogène en plusieurs instances ne remplit les deux axes : il reste toujours une part du GPU hors de portée (seul `7g.80gb`, le GPU entier, les remplit). Le calcul est fait par un script Python du module, à partir du tableau ci-dessus.
:::

Le prix de MIG est une **rigidité** : changer le profil d'un nœud suppose de le vider, et un mauvais découpage produit des fragments inutilisables. Son avantage est une isolation en mémoire, en bande passante et en défaut matériel : une instance qui plante n'affecte pas les autres.

### 2.5. Time-slicing : du partage sans isolation

Le **time-slicing** de l'opérateur GPU surannonce chaque GPU : avec `replicas: 4`, un nœud de 8 GPU annonce 32 `nvidia.com/gpu`, que l'ordonnanceur distribue comme des entiers. Les pods d'un même GPU alternent dans le temps. La documentation est explicite : contrairement à MIG, il n'y a **ni isolation mémoire ni isolation des défauts** entre réplicas.

Deux conséquences se lisent dans la documentation. Demander plusieurs réplicas ne donne pas une part proportionnelle de calcul : la demande garantit seulement l'accès à un GPU partagé, et le GPU donne une part de temps égale à chaque processus GPU, quel que soit le pod. Un pod qui demande 2 réplicas n'a donc pas plus de calcul qu'un pod qui en demande 1. L'option `failRequestsGreaterThanOne` existe pour refuser ces demandes trompeuses. Et DCGM-Exporter ne sait pas associer les métriques à des conteneurs quand le time-slicing est actif, ce qui prive votre observabilité de l'attribution par pod.

::: ex
[Exemple 2.2 — Les comptes du time-slicing]{.tag} Un nœud de 8 GPU avec `replicas: 4` annonce $8 \times 4 = 32$ ressources. Trois pods d'un seul processus GPU chacun, sur le même GPU, reçoivent chacun $1/3$ du temps, soit 33,3 %, que l'un d'eux ait demandé 1 ou 2 réplicas (la part est égale par processus, non par pod).

Il faut `replicas: 8` pour loger huit pods sur un même GPU (avec `replicas: 4`, il en reçoit au plus quatre). Huit pods de 10 Go sur un H100 de 80 Go remplissent alors la mémoire à 100 % : au moindre dépassement, les autres pods du GPU sont exposés, faute d'isolation. Le fichier `manifests/timeslicing-configmap.yaml` du lab 12.4 reprend la structure de configuration de la documentation ; le serveur d'API en valide le format, pas l'effet.
:::

### 2.6. DRA : décrire plutôt que compter

Le **Dynamic Resource Allocation (DRA)** remplace le décompte d'entiers par un modèle proche des volumes persistants. D'après la documentation de Kubernetes, il est **stable depuis la v1.35**, où la fonctionnalité ne peut plus être désactivée ; l'[annonce de la v1.34](https://kubernetes.io/blog/2025/08/27/kubernetes-v1-34-release/) (27 août 2025) le déclarait déjà GA (« The core of DRA is GA »), avec l'API `resource.k8s.io/v1` activée par défaut. Il est disponible depuis la v1.30.

Les pilotes publient des `ResourceSlice` décrivant les périphériques d'un nœud ; des `DeviceClass` les catégorisent ; une charge décrit son besoin dans un `ResourceClaim` ou un `ResourceClaimTemplate`, avec des filtres en CEL (*Common Expression Language*, le langage d'expressions des règles d'API) sur les attributs et capacités.

La documentation du pilote DRA de NVIDIA résume la rupture en une phrase : « The Kubernetes device plugin framework treats hardware resources as opaque countable integers. » Avec DRA, on demande « un GPU H100 » ou « une instance MIG de 20 Go » par attributs, on partage un même GPU entre conteneurs en référençant la même réclamation, et on attache une configuration par charge (par exemple le profil MIG). Le fichier `manifests/dra-claim.yaml` du lab 12.4 contient une réclamation de 8 GPU H100 ; le serveur d'API v1.37.1 du lab l'accepte, et refuse une valeur `allocationMode` inconnue.

~~~yaml
spec:
  devices:
    requests:
      - name: gpus
        exactly:
          deviceClassName: gpu.nvidia.com
          allocationMode: ExactCount
          count: 8
          selectors:
            - cel:
                expression: device.attributes['gpu.nvidia.com'].productName.matches('H100')
~~~

Trois réserves, toutes tirées de la documentation. Le pilote NVIDIA (version 0.5.1 dans la documentation de l'opérateur) a des fonctions encore **alpha**, comme la création dynamique de profils MIG. Un cluster peut avoir soit une ressource `GPUCluster` pour DRA, soit une `ClusterPolicy` pour le plugin de périphériques, **pas les deux**. Enfin, l'ordonnanceur de Kubernetes ne préempte pas les ressources DRA : un pod de forte priorité qui en a besoin reste en attente tant que le détenteur ne se termine pas.

::: war
[Une limite documentée : pas de préemption sur DRA]{.tag} La page « Dynamic Resource Allocation » de Kubernetes, rubrique *Limitations*, indique que le pod de plus forte priorité qui a besoin d'une ressource DRA détenue par un autre pod reste `Pending` jusqu'à ce que ce dernier se termine ou soit supprimé à la main. Conséquence : si vous comptez sur la préemption de pods pour reprendre des GPU, restez sur le plugin de périphériques ou faites préempter par la couche de file (Kueue, chapitre 3) ; sa préemption avec DRA est à vérifier pour votre version. Source : <https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/>.
:::

::: recap
Points clés — chapitre 2

-   Plugin de périphériques : des entiers sous `limits`, pas de surallocation, stable depuis la v1.26.
-   L'opérateur GPU installe pilote, plugin, toolkit, étiquettes et supervision ; son espace de noms est privilégié.
-   MIG : partitions isolées mais rigides, profils fixes, nœud à vider pour changer ; un découpage homogène laisse une part inutilisée.
-   Time-slicing : plus de pods par GPU sans isolation ; demander plus de réplicas ne donne pas plus de calcul.
-   DRA : GA en v1.34, verrouillé (non désactivable) en v1.35 ; décrit les besoins par attributs ; pas de préemption côté ordonnanceur, pilote NVIDIA partiellement alpha.
:::

## 3. Files d'attente et ordonnancement de groupe : Kueue, Volcano, natif {#ch3}

Ce chapitre est le cœur du module. Il explique comment faire attendre des entraînements, leur garantir une part, les préempter, et ne les démarrer que si tous leurs pods peuvent l'être. Les versions lues le 24 octobre 2026 : Kueue v0.20.3 (dernière entrée du fichier `CHANGELOG-0.20.md` de la branche principale), API `kueue.x-k8s.io/v1beta2`.

### 3.1. Une couche de file au-dessus de l'ordonnanceur

**Kueue** est un système natif de Kubernetes qui gère les quotas et la façon dont les Jobs les consomment. D'après sa documentation, il décide quand un Job doit attendre, quand il peut être admis (c'est-à-dire que ses pods peuvent être créés), et quand il doit être préempté (c'est-à-dire que ses pods actifs sont supprimés). Il ne remplace aucun composant : l'autoscaling, le placement des pods et la gestion du cycle de vie des Jobs restent aux composants existants.

Le fonctionnement tient en deux gestes. L'utilisateur crée un Job avec l'étiquette `kueue.x-k8s.io/queue-name` qui désigne une file locale ; Kueue le suspend (par un *webhook*) et crée un objet `Workload` qui représente la demande. Quand le quota le permet, il **admet** le Workload et lève la suspension ; l'ordonnanceur de Kubernetes place alors les pods. Voilà l'atomicité du **quota**, et seulement celle-là.

::: note
[Quelles charges Kueue sait gérer]{.tag} D'après sa page de présentation : Job, JobSet, MPIJob, RayJob et RayCluster sont « Stable » ; `TrainJob` (Trainer v2) est « Alpha » ; `PyTorchJob` et les autres opérateurs de Trainer v1 sont « Deprecated ». C'est un critère de choix pour le chapitre 4.
:::

### 3.2. Les objets de Kueue

<figure class="fig">
<svg viewBox="0 0 640 270" role="img" aria-labelledby="kqt kqd" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit"><title id="kqt">Les objets de Kueue</title><desc id="kqd">Un Job étiqueté vise une LocalQueue ; elle pointe vers une ClusterQueue ; trois ClusterQueue d'une cohorte partagent leur quota inutilisé ; chacune référence un ResourceFlavor.</desc><defs><marker id="kqa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs><rect class="fb" x="8" y="30" width="110" height="52" rx="6"/><text class="ft fh" x="63" y="52">Job</text><text class="ft" x="63" y="70">label queue-name</text><rect class="fb" x="165" y="30" width="105" height="52" rx="6"/><text class="ft fh" x="217.5" y="52">LocalQueue</text><text class="ft" x="217.5" y="70">espace de noms</text><path class="fa" d="M118 56L163 56" marker-end="url(#kqa)"/><rect class="fb" x="8" y="110" width="110" height="52" rx="6"/><text class="ft fh" x="63" y="132">Job</text><text class="ft" x="63" y="150">autre équipe</text><rect class="fb" x="165" y="110" width="105" height="52" rx="6"/><text class="ft fh" x="217.5" y="141">LocalQueue</text><path class="fa" d="M118 136L163 136" marker-end="url(#kqa)"/><rect class="fb" x="8" y="190" width="110" height="52" rx="6"/><text class="ft fh" x="63" y="212">Job</text><text class="ft" x="63" y="230">autre équipe</text><rect class="fb" x="165" y="190" width="105" height="52" rx="6"/><text class="ft fh" x="217.5" y="221">LocalQueue</text><path class="fa" d="M118 216L163 216" marker-end="url(#kqa)"/><rect class="fz" x="305" y="12" width="195" height="246" rx="10"/><text class="ft fx" x="402" y="30">cohorte : quota inutilisé partagé</text><rect class="fb" x="320" y="40" width="165" height="52" rx="6"/><text class="ft fh" x="402.5" y="62">ClusterQueue A</text><text class="ft" x="402.5" y="80">nominal, emprunt, prêt</text><rect class="fb" x="320" y="110" width="165" height="52" rx="6"/><text class="ft fh" x="402.5" y="141">ClusterQueue B</text><rect class="fb" x="320" y="190" width="165" height="52" rx="6"/><text class="ft fh" x="402.5" y="221">ClusterQueue C</text><rect class="fb" x="540" y="110" width="92" height="52" rx="6"/><text class="ft fh" x="586" y="132">Resource</text><text class="ft" x="586" y="150">Flavor</text><path class="fa" d="M270 56L318 66" marker-end="url(#kqa)"/><path class="fa" d="M270 136L318 136" marker-end="url(#kqa)"/><path class="fa" d="M270 216L318 214" marker-end="url(#kqa)"/><path class="fa" d="M485 136L538 136" marker-end="url(#kqa)"/></svg>
<figcaption>Les objets de Kueue : un Job étiqueté vise une LocalQueue, qui pointe vers une ClusterQueue ; les ClusterQueue d'une même cohorte se prêtent leur quota inutilisé ; chaque ClusterQueue référence des ResourceFlavor.</figcaption>
</figure>

-   Un **ResourceFlavor** décrit un type de nœuds (par ses étiquettes). Il peut référencer un objet `Topology` pour le placement (chapitre 5).
-   Une **ClusterQueue** (portée cluster) porte les quotas par *flavor* et par ressource, la stratégie de file, les règles de préemption, les espaces de noms autorisés et le nom de sa cohorte.
-   Une **LocalQueue** (portée espace de noms) est le point d'entrée de l'utilisateur ; elle pointe vers une ClusterQueue.
-   Une **WorkloadPriorityClass** donne une priorité au Workload sans toucher à la priorité des pods.
-   Une **cohorte** est un simple nom partagé : les ClusterQueue du même nom peuvent se prêter leur quota inutilisé.

Le lab 12.1 contient un jeu complet pour un pool de 64 GPU et trois équipes, que vous validez hors ligne. Voici la file de l'équipe de recherche (extrait de `manifests/30-clusterqueues.yaml`).

~~~yaml
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata: {name: research}
spec:
  cohortName: gpu-pool
  queueingStrategy: StrictFIFO
  preemption:
    withinClusterQueue: LowerPriority
    reclaimWithinCohort: Any
    borrowWithinCohort: {policy: Never}
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
      flavors:
        - name: h100-80gb
          resources:
            - {name: "nvidia.com/gpu", nominalQuota: 32, borrowingLimit: 8, lendingLimit: 16}
            # cpu et memory (mêmes principes) omis de l'extrait ; le fichier du lab est complet
~~~

### 3.3. Quotas, emprunt et prêt

Le `nominalQuota` est la quantité qu'une file peut consommer en propre. Dans une cohorte, d'après la documentation du champ, une file peut en outre **emprunter** le quota inutilisé des autres, jusqu'à `borrowingLimit` (sans limite si le champ est absent), et **prêter** au plus `lendingLimit` de son quota nominal : elle se réserve `nominalQuota - lendingLimit` pour son usage exclusif. Un `borrowingLimit` sans cohorte est une erreur de configuration, que la CRD interdit par une règle CEL.

Notons $n_i$ le quota nominal, $b_i$ la limite d'emprunt, $\ell_i$ la limite de prêt de la file $i$, $u_i$ sa consommation, et $g_i = n_i - \ell_i$ la part réservée. Une charge est admissible si deux conditions tiennent :

$$u_i \le n_i + b_i \qquad\text{et}\qquad \sum_j \max(0,\; u_j - g_j) \;\le\; \sum_j \ell_j .$$

La seconde ligne dit que ce qui dépasse la part réservée de chaque file puise dans un *pool* dont la capacité est la somme des quantités prêtables. Ce sont exactement les règles du modèle du lab 12.1.

::: ex
[Exemple 3.1 — Combien de GPU chaque équipe peut-elle obtenir ?]{.tag} Dans le jeu du lab, la recherche a un quota de 32, un emprunt limité à 8 et un prêt limité à 16 (donc 16 GPU réservés) ; le produit a 24 sans limite ; le développement a 8 avec un emprunt limité à 8. Capacité du pool : $16 + 24 + 8 = 48$.

Quand les autres files sont vides, le produit peut donc atteindre 48 GPU (24 en propre, 24 empruntés) mais pas 64 : les 16 GPU réservés de la recherche lui restent inaccessibles. La recherche est plafonnée à $32 + 8 = 40$ par sa limite d'emprunt, et le développement à $8 + 8 = 16$. Les tests `test_lending_limit_keeps_quota_for_the_owner` et `test_borrowing_limit_caps_a_queue` du lab vérifient ces plafonds sur le modèle.
:::

### 3.4. Ordre et stratégie de file

Dans une file, les Workloads sont ordonnés par priorité puis par date de création. La stratégie `StrictFIFO` fait bloquer un Workload ancien qui ne peut pas être admis **toute la file** derrière lui, même si de plus petits tiendraient ; `BestEffortFIFO` (défaut) laisse passer les suivants. Le choix est une politique : pour de gros entraînements qu'on ne veut pas voir doubler par une nuée de petits jobs, `StrictFIFO` ; pour une file d'expériences variées, `BestEffortFIFO`.

Une `WorkloadPriorityClass` se référence par l'étiquette `kueue.x-k8s.io/priority-class` du Job. Elle est cluster-scoped, donc utilisable depuis tous les espaces de noms ; sa valeur est un entier, et la page de documentation la distingue de la `PriorityClass` des pods.

### 3.5. Préempter : trois leviers

La préemption de Kueue est réglée sur la ClusterQueue du **demandeur** par trois champs, dont voici les sens d'après la CRD.

-   `withinClusterQueue` : le demandeur peut évincer des Workloads de **sa propre file** (`LowerPriority`, ou `LowerOrNewerEqualPriority` pour inclure les plus récents de même priorité).
-   `reclaimWithinCohort` : le demandeur dont la demande **tient dans son quota nominal** peut récupérer ce que d'autres files lui ont emprunté, quelle que soit leur priorité (`Any`) ou seulement si elle est plus basse (`LowerPriority`).
-   `borrowWithinCohort` : le demandeur qui doit *lui-même* emprunter peut tout de même évincer des Workloads d'autres files, de priorité plus basse et au plus égale à un seuil `maxPriorityThreshold`.

La documentation donne l'ordre des candidats : d'abord les Workloads des files qui empruntent, puis la priorité la plus basse, puis l'admission la plus récente. Kueue retient ensuite le plus petit ensemble de victimes en remettant en place, dans l'ordre inverse, celles dont l'éviction n'est pas nécessaire. Le *fair sharing* (stable depuis Kueue v0.7) est une alternative qui vise un partage équilibré du quota empruntable ; le modèle du lab ne l'implémente pas.

::: ex
[Exemple 3.2 — Une journée sur le pool de 64 GPU]{.tag} Le scénario `scenarios/platform-day.yaml` du lab 12.1 est rejoué sur le modèle ; il lit files et priorités dans les manifestes. Extrait de la trace (modèle de référence, 24 octobre 2026) ; l'étiquette `InCohort` est celle du modèle, Kueue publiant ses propres raisons de préemption (la page de documentation ne montre que `InClusterQueue`) :

~~~text
t= 10 min  submit pretrain-7b (32 GPU, priority normal=100) to research/main
            -> PREEMPT finetune-14b [product] InCohort by pretrain-7b
            -> ADMIT   pretrain-7b [research] nominal
t= 20 min  submit incident-eval (16 GPU, priority urgent=1000) to research/main
            -> PREEMPT pretrain-7b [research] InClusterQueue by incident-eval
            -> ADMIT   incident-eval [research] nominal
            -> ADMIT   finetune-14b [product] borrowing
t= 40 min  finish incident-eval
            -> PREEMPT ablation-sweep [research] InClusterQueue by pretrain-7b
            -> ADMIT   pretrain-7b [research] nominal
~~~

L'extrait omet les étapes sans préemption, dont trois comptent pour la suite. À $t=0$, des notebooks de développement prennent 8 GPU, rendus à $t=30$. À $t=5$, le fine-tuning du produit est admis avec 30 GPU, dont 6 empruntés. À $t=15$, le balayage d'ablation (8 GPU, priorité `preemptible`) est admis en empruntant.

À $t=10$, le produit puise 30 GPU dans le pool et le développement 8 ; la recherche y puiserait $32 - 16 = 16$, soit $54 > 48$. C'est ce pool partagé, développement compris, qui force une éviction : sans les notebooks, $16 + 30 = 46$ tiendrait. La demande de la recherche tient dans son quota nominal, et `reclaimWithinCohort: Any` l'autorise à évincer le fine-tuning.

À $t=20$, l'évaluation urgente (16 GPU) évince le pré-entraînement de 32 GPU plutôt que le balayage de 8 GPU de priorité plus basse : retirer le balayage seul ne libère pas assez, et une fois le pré-entraînement retiré le balayage peut être remis en place. Les GPU libérés permettent au fine-tuning de reprendre.

À $t=40$, le pré-entraînement ne peut pas revenir à côté du balayage : la recherche puiserait $40 - 16 = 24$ GPU dans le pool et le produit en puise déjà 30, soit $54 > 48$ ; c'est donc le balayage qui est évincé. Retrouvez ces trois décisions à la main avant d'ouvrir `reference/admission.py`.
:::

### 3.6. Admis ne veut pas dire placé

Le quota de Kueue est une **comptabilité virtuelle**. Si la capacité physique ne correspond pas au quota (nœuds drainés, GPU en panne, fragmentation, autre charge sur les mêmes nœuds), un Workload admis peut avoir des pods qui ne se placent pas. Deux Workloads admis qui se partagent mal le parc peuvent alors se bloquer.

::: war
[Un interblocage documenté par Kueue]{.tag} La page « Setup All-or-nothing with ready Pods » de la documentation de Kueue décrit le cas (traduction libre) : pour des Jobs dont tous les pods doivent tourner ensemble, une paire de tels Jobs peut s'interbloquer, sur une configuration par défaut, si la disponibilité physique ne correspond pas aux quotas de Kueue ; les mêmes Jobs iraient au bout ordonnancés en séquence. La parade historique est `waitForPodsReady` (depuis Kueue 0.3.0) : si tous les pods ne sont pas prêts dans un délai, le Workload est évincé et remis en file. Source : <https://kueue.sigs.k8s.io/docs/tasks/manage/setup_wait_for_pods_ready/>.
:::

Le même phénomène se produit sans Kueue, au niveau des pods, et il se chiffre. Le script `gang_deadlock.py` du lab 12.1 fait arriver dans un ordre aléatoire les pods de deux Jobs de 8 pods, chacun exigeant un nœud entier ; un ordonnanceur pod par pod lie chaque pod au premier nœud libre. Un Job ne progresse qu'au complet ; la grappe est bloquée si aucun des deux n'est complet une fois tous les pods arrivés.

$$P(\text{blocage}) \;=\; \sum_{k=m-p+1}^{p-1} \frac{\binom{m}{k}\binom{2p-m}{p-k}}{\binom{2p}{p}}$$

avec $m$ nœuds et $p$ pods par Job : $k$ est le nombre de pods du premier Job parmi les $m$ premiers arrivés, et le blocage survient quand chaque Job en a au plus $p-1$.

::: ex
[Exemple 3.3 — La probabilité de blocage de deux Jobs de 64 GPU]{.tag} Résultat de `python3 gang_deadlock.py` (20 000 tirages, graine 12, calcul exact et simulation) :

~~~text
nodes  GPUs held when deadlocked  P(deadlock) exact  simulated  with gang
    8                         64              1.000      1.000      0.000
   10                         80              0.993      0.992      0.000
   12                         96              0.923      0.919      0.000
   14                        112              0.533      0.537      0.000
   16                        128              0.000      0.000      0.000
~~~

Avec 12 nœuds (96 GPU) pour deux Jobs de 64 GPU, un ordonnancement pod par pod se bloque dans 92 % des ordres d'arrivée, en gardant 96 GPU liés sans qu'aucun Job ne progresse. Avec 16 nœuds, les deux tiennent et le risque disparaît ; avec ordonnancement de groupe, il est nul à toute taille. L'hypothèse (arrivée uniformément aléatoire) est celle de la simulation : la valeur réelle dépend de la façon dont vos pods sont créés.
:::

### 3.7. Volcano, KAI Scheduler et l'ordonnancement de groupe natif

Pour obtenir l'atomicité du **placement**, trois voies existent. **Volcano**, projet CNCF accepté en 2020 et passé au niveau *Incubating* le 21 mars 2022 d'après la page CNCF, apporte ses propres ressources : un `PodGroup` (dont `minMember` dit combien de pods doivent pouvoir être placés, sinon aucun ne l'est) et une `Queue` (champs `weight`, `capability`, `guarantee`, `deserved`, `reclaimable`). Son plugin de proportion calcule la part due à une file par la formule suivante.

$$\text{deserved} = \frac{\text{weight}}{\text{total-weight}} \times \text{total-resource}$$

**KAI Scheduler**, ordonnanceur open source orienté GPU, annonce dans son README de l'ordonnancement par lot, des files hiérarchiques et du *bin packing*, et peut cohabiter avec d'autres ordonnanceurs.

La troisième voie est l'ordonnanceur de Kubernetes lui-même. L'API `Workload` décrit une politique de planification de groupes de pods ; un `PodGroup` en est l'instance à l'exécution. Avec la politique `gang`, d'après la documentation de la v1.37, l'ordonnanceur retient les pods tant que le groupe n'existe pas et que `minCount` pods n'ont pas été créés, puis cherche un placement pour tous ; s'il n'en trouve pas pour au moins `minCount`, **aucun** n'est lié. Les pods vont alors dans la file des non-planifiables, laissant passer d'autres charges.

Le mot *gang* n'a pas ce sens dans Slurm. Son *gang scheduling* (option `GANG` de `PreemptMode`) est un partage par tranches de temps (*time slicing*) : des jobs alloués aux mêmes ressources sont suspendus et repris à tour de rôle, chacun pendant un intervalle configuré ([module 5, chapitre 4](../slurm/index.html#ch4)). Dans ce module, il désigne le démarrage tout ou rien d'un groupe de pods.

::: ex
[Exemple 3.4 — Le même Job de 64 GPU, avec ordonnancement de groupe natif]{.tag} Le lab 12.4 active les portes `GenericWorkload` et `WorkloadWithJob` sur un plan de contrôle v1.37.1 et ajoute `scheduling: {schedulingPolicy: {gang: {}}}` au Job de l'exemple 1.1. Sortie capturée le 24 octobre 2026 dans le bac à sable (6 puis 8 nœuds de 8 GPU) :

~~~text
== B. gang Job (native gang scheduling), same shape, still 6 nodes
bound pods: 0 of 8
PODGROUP                                           POLICY   REASON
train-gang-57b57577fc-train-gang-pgt-0-8ff484b67   8        Unschedulable
PodGroup message: minCount (8) cannot be satisfied: 6 scheduled, 1 remaining, pod group preemption: No preemption victims found for incoming preemptor

== C. two more nodes join: 8 x 8 GPUs
bound pods: 8 of 8
PodGroup reason after the join: Scheduled
~~~

Aucun des 8 pods n'est lié tant que 8 nœuds ne sont pas disponibles ; dès que les nœuds 7 et 8 apparaissent, les 8 pods sont liés d'un coup. `minCount` a pris la valeur de `parallelism` (8), comme le dit la documentation du Job. Rien n'a été installé en plus du plan de contrôle : mais la fonction est en bêta et **désactivée par défaut**, et elle ne fait ni file, ni quota, ni équité.
:::

| | Kueue | Volcano | Ordonnancement de groupe natif (v1.37) |
|---|---|---|---|
| Atomicité | quota (admission) | placement (et files) | placement |
| File, quotas, équité | oui (cohortes, préemption, *fair sharing*) | oui (files avec poids, `deserved`) | non |
| Ordonnanceur de pods | celui de Kubernetes | le sien (plugins et actions configurables) | celui de Kubernetes |
| Maturité (docs, 2026-10-24) | intégrations Job, JobSet, Ray « Stable » | CNCF Incubating | bêta, désactivée par défaut |
| À retenir | à combiner avec un gang de placement pour éviter l'interblocage | remplace plusieurs couches d'un coup | brique de fond, pas une plateforme |

Ce tableau est un jugement de ce parcours à date. Une combinaison courante en 2026 est Kueue pour les files et JobSet pour le groupe de pods ; vérifiez dans la documentation de votre version ce que Kueue délègue au placement natif.

::: recap
Points clés — chapitre 3

-   Kueue gère le **quota** et l'admission ; il ne place pas les pods et ne remplace pas l'ordonnanceur.
-   Quota nominal, emprunt, prêt : une file garde `nominalQuota - lendingLimit` pour elle ; le pool est la somme des quantités prêtables.
-   Préemption : `withinClusterQueue`, `reclaimWithinCohort`, `borrowWithinCohort` ; candidats par files qui empruntent, priorité croissante, admission récente ; victimes minimisées.
-   Admis ne veut pas dire placé : un interblocage est documenté par Kueue, `waitForPodsReady` en est la parade historique.
-   Deux Jobs de 64 GPU sur 96 GPU se bloquent dans 92 % des ordres d'arrivée avec un ordonnanceur pod par pod, jamais avec un gang.
-   Le gang natif existe (bêta, désactivé par défaut) mais n'offre ni file ni quota : il complète Kueue, il ne le remplace pas.
:::

## 4. Charges d'entraînement : Jobs indexés, JobSet, Trainer, KubeRay, réseau {#ch4}

Ce chapitre décrit comment lancer l'entraînement multi-nœuds lui-même : de la brique de base de Kubernetes jusqu'aux opérateurs spécialisés, avec ce que chacun apporte pour le rendez-vous des rangs, le redémarrage et le réseau.

### 4.1. Le Job indexé et le rendez-vous

Un entraînement `torchrun` sur plusieurs nœuds exige que chaque nœud connaisse un point de rendez-vous commun et, selon le mode, son propre numéro (lancement et rendez-vous de `torchrun` : [module 9, §2.3](../distributed-training/index.html#torchrun-et-le-rendez-vous)). Kubernetes fournit les briques. Un Job en mode `Indexed` donne à chaque pod un indice de 0 à `completions - 1`, exposé par l'annotation et l'étiquette `batch.kubernetes.io/job-completion-index` et par la variable d'environnement `JOB_COMPLETION_INDEX`. Combiné à un Service sans adresse (*headless*), il donne à chaque pod un nom DNS stable.

Avec le rendez-vous `c10d` de `torchrun`, un seul nom suffit : tous les pods se connectent à l'adresse du pod d'indice 0, et `torchrun` attribue lui-même les rangs. Il reste deux pièges propres au Job. Le champ `backoffLimitPerIndex` (stable depuis la v1.33) relance un seul indice défaillant : c'est la bonne option pour des tâches indépendantes, la mauvaise pour un collectif, où un rang relancé seul ne peut pas rejoindre une communication en cours. Et `podFailurePolicy` permet de ne pas gaspiller de tentatives sur des erreurs non récupérables, par code de sortie.

### 4.2. JobSet : un groupe de Jobs comme une unité

**JobSet** est décrit par sa documentation comme une API native de Kubernetes pour gérer un groupe de Jobs comme une unité, avec une API unifiée pour les charges HPC (MPI) et d'entraînement (PyTorch, JAX, TensorFlow). Ses apports pour l'entraînement, tous cités dans sa documentation, sont les suivants.

-   Plusieurs gabarits : un `replicatedJob` par rôle (meneur, travailleurs, serveurs de paramètres).
-   Un Service sans adresse créé et géré automatiquement, de sorte que chaque pod a un nom du type `<jobset>-<replicatedJob>-<indice du job>-<indice du pod>.<sous-domaine>` (exemple du dépôt : `network-jobset-leader-0-0.example`).
-   Une politique d'échec : si un Job échoue, **tout le JobSet est recréé**, ce qui permet de reprendre au dernier checkpoint (l'état d'entraînement sauvegardé : poids, optimiseur, pas courant) ; sans politique, le premier échec fait échouer le JobSet. `maxRestarts` borne les recréations.
-   Une politique de succès, un ordre de démarrage, et une annotation de **placement exclusif par domaine de topologie**.

L'API est `jobset.x-k8s.io/v1alpha2` ; la page d'installation indique la version v0.13.0 le 24 octobre 2026, et la documentation annonce le support des trois dernières versions mineures de Kubernetes. Son [README](https://github.com/kubernetes-sigs/jobset/blob/main/README.md) donne aussi un ordre de grandeur : un débit d'ordonnancement de 290 pods par seconde pendant la récupération après une défaillance, à l'échelle de 15 000 nœuds, mesuré par le projet (benchmark du projet, non reproduit ici).

C'est trois fois la limite de 5 000 nœuds que garantit la documentation de Kubernetes (§1.6), et le README ne dit pas sur quel cluster la mesure a été faite : lisez ce chiffre comme celui d'un cas extrême, pas d'un cluster standard.

<figure class="fig">
<svg viewBox="0 0 640 250" role="img" aria-labelledby="jst jsd" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit"><title id="jst">Rendez-vous d'un JobSet</title><desc id="jsd">Quatre pods d'un Job indexé ont des noms DNS stables ; les pods 1, 2 et 3 se connectent au pod 0, hôte du rendez-vous torchrun (port 29500).</desc><defs><marker id="jsa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs><rect class="fz" x="8" y="8" width="624" height="36" rx="6"/><text class="ft fx" x="320" y="31" style="font-size:13px">Service sans adresse « pretrain-7b » : un enregistrement DNS par pod</text><rect class="fb" x="200" y="80" width="240" height="62" rx="6" style="stroke-width:3"/><text class="ft fh" x="320" y="107">pod 0 : rendez-vous</text><text class="ft" x="320" y="127">pretrain-7b-workers-0-0:29500</text><rect class="fb" x="20" y="180" width="150" height="52" rx="6"/><text class="ft fh" x="95" y="202">pod 1</text><text class="ft" x="95" y="220">workers-0-1</text><rect class="fb" x="245" y="180" width="150" height="52" rx="6"/><text class="ft fh" x="320" y="202">pod 2</text><text class="ft" x="320" y="220">workers-0-2</text><rect class="fb" x="470" y="180" width="150" height="52" rx="6"/><text class="ft fh" x="545" y="202">pod 3 … 15</text><text class="ft" x="545" y="220">workers-0-3 … 0-15</text><path class="fa" d="M120 178L258 144" marker-end="url(#jsa)"/><path class="fa" d="M320 178L320 144" marker-end="url(#jsa)"/><path class="fa" d="M520 178L382 144" marker-end="url(#jsa)"/></svg>
<figcaption>Rendez-vous d'un JobSet de 16 pods : les noms DNS stables viennent du Service sans adresse ; tous les pods rejoignent le pod 0, qui héberge le rendez-vous c10d de torchrun.</figcaption>
</figure>

Le lab 12.2 fournit un JobSet complet pour 16 nœuds de 8 GPU (128 GPU), file Kueue, topologie exigée au niveau du bloc, volume de checkpoints partagé et `maxRestarts: 3`. Voici le cœur de la ligne de commande, qui reprend le modèle de l'exemple PyTorch du dépôt JobSet.

~~~yaml
args:
  - >-
    exec torchrun --nnodes=16 --nproc_per_node=8
    --rdzv_backend=c10d --rdzv_endpoint=pretrain-7b-workers-0-0.pretrain-7b:29500
    --rdzv_id=pretrain-7b
    train.py --steps 100000 --ckpt-dir /ckpt --ckpt-every 500
~~~

::: ex
[Exemple 4.1 — Répéter le redémarrage d'un JobSet sans cluster]{.tag} Le script `local_two_nodes.sh` du lab 12.2 lance deux processus `torchrun` (gloo, CPU) avec les mêmes options de rendez-vous que ci-dessus ; une boucle de redémarrage tient le rôle de `failurePolicy.maxRestarts`, et `train.py` injecte une panne du rang 1 au pas 30. Sortie capturée dans le bac à sable (Linux 6.18, 4 vCPU, PyTorch 2.14 CPU, 24 octobre 2026) :

~~~text
attempt 0: exit codes of the 2 pods = 1 1
    world_size=2 backend=gloo resuming_from_step=0
    checkpoint step=20 loss=0.12770
    rank 1: injected failure at step 30
  -> restarting the whole set (restart 1 of 3)
attempt 1: exit codes of the 2 pods = 0 0
    world_size=2 backend=gloo resuming_from_step=20
    checkpoint step=40 loss=0.00120
    checkpoint step=60 loss=0.00002
    done step=60 final_loss=0.000024
RESTARTS=1
~~~

Les deux « pods » échouent ensemble (le survivant perd son pair), le groupe est relancé en entier et reprend au pas 20, dernier checkpoint, non au pas 0. Les 10 pas calculés entre 20 et 30 sont perdus. Il s'agit d'une **répétition de la sémantique** et non de Kubernetes : seule l'exécution sur un cluster prouverait le comportement des pods et des volumes.
:::

### 4.3. Kubeflow Trainer v2

**Kubeflow Trainer** (ex Training Operator) propose une ressource unique, `TrainJob`, et des *runtimes* (`ClusterTrainingRuntime`, `TrainingRuntime`) qui portent le gabarit de lancement d'un framework. La documentation indique qu'il réutilise des briques natives comme JobSet et LeaderWorkerSet, que son installation (version v2.1.0) exige Kubernetes 1.31 ou plus, et qu'il s'intègre à Kueue, Volcano, KAI Scheduler, Coscheduling et Slurm Bridge. Pour PyTorch, il lance `torchrun` sur chaque nœud et configure l'environnement distribué (taille du monde, rang global, `LOCAL_RANK`).

Le fichier `manifests/30-trainjob.yaml` du lab 12.2 exprime le même entraînement : l'utilisateur ne donne que le nombre de nœuds, l'image, la commande et les ressources, et le runtime `torch-distributed` fournit le reste. Le schéma de l'API `trainer.kubeflow.org/v1alpha1` est vérifié hors ligne contre la CRD upstream et par un serveur d'API v1.37.1.

L'ancien *Training Operator* (v1) et ses opérateurs `PyTorchJob`, `TFJob`… sont qualifiés de « legacy » par la documentation de Trainer, et leurs intégrations Kueue de « Deprecated ». Pour un nouveau déploiement, le choix se fait entre JobSet (contrôle maximal, vous écrivez le lancement) et TrainJob (moins de YAML, au prix d'une couche d'abstraction encore en `v1alpha1`).

### 4.4. KubeRay

Pour les charges Ray, **KubeRay** est, d'après la documentation de Ray, la façon recommandée de l'exécuter sur Kubernetes ; le [module 11, §8.1](../ray-rl-infra/index.html#ray-sur-kubernetes-avec-kuberay) en détaille un manifeste, `deploy/raycluster.yaml`. Il introduit trois ressources, `RayCluster`, `RayJob` et `RayService` ; chaque nœud Ray est un pod, et un cluster est un pod de tête plus des pods de travail. Un autoscaling optionnel ajoute et retire des pods selon la charge. Les `RayJob` et `RayCluster` sont des intégrations « Stable » de Kueue, et la documentation de Ray décrit leur usage avec Kueue et avec KAI Scheduler pour l'ordonnancement de groupe et les priorités.

### 4.5. Réseau haute performance

Le réseau de pods par défaut n'est, en général, pas celui des collectifs d'entraînement. Les entraînements multi-nœuds exigeants utilisent un **second réseau** attaché au pod, avec RDMA. Les composants de l'écosystème NVIDIA l'organisent : un opérateur réseau, configuré par une ressource `NicClusterPolicy`, déploie les pilotes et les modules de réseau secondaire (Multus CNI, IPoIB, SR-IOV).

Côté GPU, la documentation de l'opérateur GPU explique que GPUDirect RDMA (accès direct entre la carte réseau et la mémoire GPU) s'appuie soit sur DMA-BUF du noyau Linux, soit sur le module historique `nvidia-peermem` ; NVIDIA recommande DMA-BUF. Le détail des débits à attendre et de la façon de les mesurer relève du module 7 (réseau) : un manifeste correct n'implique pas un débit correct, et c'est `nccl-tests` qui tranche.

### 4.6. Le coût d'un redémarrage

Quand un pod meurt, tout le JobSet est recréé. Le temps perdu a deux termes : la durée $R$ du redémarrage (recréation des pods, tirage des images, rendez-vous, reprise de lecture du checkpoint) et, en moyenne, la moitié de l'intervalle $\tau$ entre checkpoints, puisqu'une panne arrive à un instant uniforme.

$$T_{\text{perdu}} = R + \frac{\tau}{2}$$

::: ex
[Exemple 4.2 — Le prix d'une panne pour 128 GPU]{.tag} Hypothèses **illustratives** (à remplacer par vos mesures) : 6 s par pas, checkpoint tous les 500 pas (donc 3 000 s) et redémarrage de 300 s. Alors $T_{\text{perdu}} = 300 + 1500 = 1800$ s, soit 0,5 h par panne et $128 \times 0{,}5 = 64$ GPU·h.

Réduire l'intervalle à 1 000 s ramène la perte moyenne à $300 + 500 = 800$ s, mais coûte plus d'écritures de checkpoints : l'intervalle optimal du premier ordre, la formule de Young (souvent dite de Young-Daly ; Daly en donne une estimation d'ordre supérieur, module 10), équilibre les deux : $\tau^\star = \sqrt{2\,\delta\,M}$, où $\delta$ est la durée d'écriture d'un checkpoint et $M$ le temps moyen entre pannes du job (module 10 et [Projet 3](../../projects/resilient-trainer/index.html)).
:::

::: recap
Points clés — chapitre 4

-   Job indexé plus Service sans adresse : indice, noms DNS stables et rendez-vous `c10d` sur le pod 0.
-   `backoffLimitPerIndex` convient aux tâches indépendantes, pas aux collectifs.
-   JobSet recrée tout le groupe à la première défaillance (`maxRestarts`) : c'est le bon modèle pour un entraînement synchrone avec checkpoints.
-   Trainer v2 (`TrainJob`) réduit le YAML ; l'ancien Training Operator est déprécié côté Kueue.
-   Le réseau rapide est un second réseau (Multus, SR-IOV, IPoIB) géré par l'opérateur réseau ; GPUDirect RDMA par DMA-BUF.
-   Perte moyenne par panne : $R + \tau/2$ ; 64 GPU·h pour 128 GPU avec les hypothèses de l'exemple.
:::

## 5. Topologie, placement et pannes de nœud {#ch5}

Un entraînement ne demande pas seulement « 128 GPU » : il demande que ces GPU soient proches et sains. Ce chapitre traite du placement dans la topologie, de la fragmentation qui l'empêche, et du temps que Kubernetes met à réagir quand un nœud disparaît.

### 5.1. Pourquoi la topologie compte

La documentation de Kueue le dit simplement : la bande passante entre deux pods dépend de la position des nœuds dans le centre de données, qui a une structure hiérarchique (nœuds dans des racks, racks dans des blocs) ; des pods dans la même unité communiquent mieux que des pods dans des unités distinctes. Pour un collectif, la communication la plus lente impose le rythme à tous les rangs. Les modèles du module 2 chiffrent cet effet ; ici nous nous occupons de **la demander à la plateforme**.

Kubernetes ne connaît la topologie que par des **étiquettes de nœuds**. Les étiquettes de zone existent partout ; celles des racks et des blocs sont posées par le fournisseur de cloud ou par vous, sur site. Sans elles, aucun outil ne peut placer par proximité.

### 5.2. Les outils de placement

Du plus ancien au plus récent :

-   les affinités de pods et de nœuds, et les contraintes de répartition, génériques mais conçues pour des services : elles n'expriment pas « ce groupe entier dans un même rack » ;
-   l'annotation de **placement exclusif** de JobSet, qui associe un Job enfant à un domaine de topologie, de sorte que tous ses pods y soient colocalisés et qu'aucun autre Job ne s'y installe ;
-   le **TAS de Kueue** (*Topology-Aware Scheduling*), bêta depuis Kueue v0.14 et activé par défaut : un objet `Topology` liste les niveaux (blocs, racks), un `ResourceFlavor` le référence par `topologyName`, et le Job demande par annotation ;
-   le **TAS natif** de Kubernetes, qui fait partie de l'API `Workload` : alpha depuis la v1.36 et toujours alpha en v1.37 (porte `TopologyAwareWorkloadScheduling`), il colocalise un `PodGroup` dans un domaine désigné par une clé d'étiquette ; la documentation de la v1.37 n'admet toujours qu'une seule contrainte de topologie par `PodGroup`.

Les annotations du TAS de Kueue se placent sur le gabarit de pod. `podset-required-topology` exige un domaine du niveau indiqué, sinon le Workload attend. `podset-preferred-topology` essaie ce niveau puis remonte niveau par niveau, et en dernier recours admet le Workload réparti sur plusieurs domaines. `podset-unconstrained-topology` ne demande pas de proximité mais comble les trous pour limiter la fragmentation. Le calcul de capacité ne compte que les nœuds prêts et ordonnançables, moins les autres charges TAS et les pods hors TAS.

<figure class="fig">
<svg viewBox="0 0 640 280" role="img" aria-labelledby="tpt tpd" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit"><title id="tpt">Placer un groupe de 8 nœuds dans un bloc</title><desc id="tpd">Deux blocs de deux racks de 8 nœuds, certains occupés. Un groupe de 8 nœuds ne tient dans aucun rack mais tient dans le bloc 0 (5 + 3 nœuds libres).</desc><defs><marker id="tpa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs><rect class="s0" x="8" y="30" width="304" height="200" rx="8" style="stroke-opacity:.5"/><rect class="s0" x="328" y="30" width="304" height="200" rx="8" style="stroke-opacity:.5"/><text class="ft fh" x="160" y="22">bloc 0 : 8 nœuds libres</text><text class="ft fh" x="480" y="22">bloc 1 : 8 nœuds libres</text><text class="ft" x="84" y="52">rack 0 (5 libres)</text><path class="s1" d="M24 64h26v26h-26z M58 64h26v26h-26z M92 64h26v26h-26z"/><path class="s2" d="M126 64h26v26h-26z M24 98h26v26h-26z M58 98h26v26h-26z M92 98h26v26h-26z M126 98h26v26h-26z"/><text class="ft" x="236" y="52">rack 1 (3 libres)</text><path class="s1" d="M176 64h26v26h-26z M210 64h26v26h-26z M244 64h26v26h-26z M278 64h26v26h-26z M176 98h26v26h-26z"/><path class="s2" d="M210 98h26v26h-26z M244 98h26v26h-26z M278 98h26v26h-26z"/><text class="ft" x="404" y="52">rack 2 (6 libres)</text><path class="s1" d="M344 64h26v26h-26z M378 64h26v26h-26z"/><path class="s0" d="M412 64h26v26h-26z M446 64h26v26h-26z M344 98h26v26h-26z M378 98h26v26h-26z M412 98h26v26h-26z M446 98h26v26h-26z"/><text class="ft" x="556" y="52">rack 3 (2 libres)</text><path class="s1" d="M496 64h26v26h-26z M530 64h26v26h-26z M564 64h26v26h-26z M598 64h26v26h-26z M496 98h26v26h-26z M530 98h26v26h-26z"/><path class="s0" d="M564 98h26v26h-26z M598 98h26v26h-26z"/><text class="ft" x="160" y="160" style="font-size:13px">groupe de 8 nœuds : refusé au niveau rack</text><text class="ft fx" x="160" y="180" style="font-size:13px">accepté au niveau bloc (5 + 3)</text><text class="ft" x="480" y="160" style="font-size:13px">gris = occupé, plein = groupe, vide = libre</text><text class="ft" x="320" y="262">Résultat de topology_fit.py : required=rack attend ; preferred=rack va au bloc ; required=bloc va au bloc.</text></svg>
<figcaption>Un groupe de 8 nœuds ne tient dans aucun rack (au mieux 6 libres) mais tient dans un bloc : le niveau demandé décide si le Workload attend ou démarre.</figcaption>
</figure>

::: ex
[Exemple 5.1 — Où placer un groupe de $N$ nœuds ?]{.tag} Le script `topology_fit.py` du lab 12.1 reproduit la sémantique documentée des annotations sur le parc de la figure (racks de 5, 3, 6 et 2 nœuds libres, blocs de 8 et 8). Sortie, 24 octobre 2026 :

~~~text
need  6 nodes | required=rack: ('rack', 6) | preferred=rack: ('rack', 6) | required=block: ('block', 8)
need  8 nodes | required=rack: None | preferred=rack: ('block', 8) | required=block: ('block', 8)
need 12 nodes | required=rack: None | preferred=rack: ('cluster', 16) | required=block: None
need 17 nodes | required=rack: None | preferred=rack: None | required=block: None
~~~

Un groupe de 6 nœuds tient dans le rack 2 ; un groupe de 8 n'a aucun rack mais un bloc ; un groupe de 12 n'a aucun bloc, et ne démarre en `preferred` que réparti sur tout le parc. `None` signifie : attendre. Choisir `required` revient à échanger de l'attente contre de la bande passante ; `preferred` échange de la bande passante contre du temps de démarrage. C'est une décision de politique, pas de technique.
:::

### 5.3. Étiquettes et taints des nœuds GPU

Les étiquettes publiées par GFD (`nvidia.com/gpu.product`, `nvidia.com/gpu.count`, `nvidia.com/mig.config`…) et par NFD servent de vocabulaire de ciblage. La documentation de Kubernetes indique qu'on peut déployer NFD pour détecter et étiqueter automatiquement les nœuds GPU, et que NFD peut aussi poser des taints pour que seuls les pods qui demandent la fonction s'installent sur ces nœuds.

Réserver les nœuds GPU aux pods qui demandent des GPU par un taint est une pratique courante, que ce parcours recommande : sinon un pod de journalisation sans GPU peut occuper les cœurs d'un nœud à 8 GPU. Les DaemonSets système doivent alors porter la toleration correspondante.

### 5.4. La fragmentation des GPU

Le score par défaut de l'ordonnanceur répartit la charge. D'après la documentation, le plugin `NodeResourcesFit` note les nœuds selon trois stratégies, dont `LeastAllocated` est la valeur par défaut ; `MostAllocated` et `RequestedToCapacityRatio` font du *bin packing* (remplir un nœud avant d'en entamer un autre). Le point qui surprend : la référence de configuration précise que la stratégie par défaut est `LeastAllocated` avec un poids égal pour `cpu` et `memory`, et rien pour les GPU.

::: ex
[Exemple 5.2 — Quatre petits pods et un nœud entier]{.tag} Le script `fragmentation_demo.sh` du lab 12.4 crée 4 nœuds de 8 GPU et un Job de 4 pods d'un GPU (8 cœurs, 64 Gio chacun). Sortie capturée le 24 octobre 2026 (kube-scheduler v1.37.1, nœuds factices) :

~~~text
== scheduler scoring: LeastAllocated (default)
  pods of eval-small per node (4 nodes x 8 GPUs, 4 GPUs requested in total):
    1 gpu-node-1
    1 gpu-node-2
    1 gpu-node-3
    1 gpu-node-4
  whole-node pod: Pending; free GPUs in the cluster: 28; scheduler says:
    0/4 nodes are available: 4 Insufficient nvidia.com/gpu.
== scheduler scoring: MostAllocated, GPUs weigh 3
  pods of eval-small per node (4 nodes x 8 GPUs, 4 GPUs requested in total):
    4 gpu-node-1
  whole-node pod: bound to gpu-node-3
~~~

Avec le score par défaut, les quatre petits pods se répartissent un par nœud (leurs demandes de CPU et de mémoire poussent vers les nœuds les plus vides) : il reste 28 GPU libres, mais aucun nœud n'en a 8, et le pod qui exige un nœud entier attend. Avec `MostAllocated` et un poids de 3 sur `nvidia.com/gpu`, les quatre pods s'entassent sur un nœud et le pod suivant tient.

Le nom du nœud libre varie d'une exécution à l'autre (départage au hasard entre nœuds équivalents). La première exécution de ce lab, sans demandes de CPU, a placé les pods au hasard : sans signal, le score est neutre.
:::

Trois remèdes, à combiner. Configurer le *bin packing* sur la ressource GPU. Faire demander des nœuds entiers aux gros entraînements. Utiliser le TAS ou un ordonnanceur de groupe qui simule le placement de tout le groupe. Ne cherchez pas de remède dans le quota de Kueue : il ne voit pas les nœuds.

### 5.5. Quand un nœud disparaît

Le contrôleur de cycle de vie des nœuds marque un nœud injoignable après `--node-monitor-grace-period`, 50 secondes par défaut dans l'aide de `kube-controller-manager` v1.37.1. Il pose alors les taints `node.kubernetes.io/not-ready` ou `unreachable`. Mais la documentation précise que Kubernetes ajoute automatiquement à chaque pod une toleration de ces deux taints avec `tolerationSeconds=300`, de sorte que les pods restent liés au nœud **cinq minutes** après la détection. Le lab 12.4 le confirme sur un pod réel :

~~~text
tolerations injected by the DefaultTolerationSeconds admission plugin:
node.kubernetes.io/not-ready NoExecute tolerationSeconds=300
node.kubernetes.io/unreachable NoExecute tolerationSeconds=300
~~~

::: ex
[Exemple 5.3 — Le temps perdu avant l'éviction]{.tag} Pour un entraînement de 128 GPU dont un nœud tombe, avec les valeurs par défaut, les pods du groupe ne sont évincés qu'environ $50 + 300 = 350$ s après la dernière réponse du nœud. Si le collectif est bloqué pendant tout ce temps (borne haute, car le framework peut échouer plus tôt), le coût est $128 \times 350 / 3600 \approx 12{,}4$ GPU·h. Avec une toleration explicite de 30 s sur les pods d'entraînement, la borne tombe à $128 \times 80 / 3600 \approx 2{,}8$ GPU·h. Calcul fait par un script Python du module ; la valeur de 30 s est un exemple, pas une recommandation générale.
:::

En pratique, ce délai se réduit de trois façons : une toleration plus courte sur les pods d'entraînement, une détection par la couche applicative (délai d'expiration NCCL, surveillance de progression) qui fait échouer le groupe, et une boucle de réparation qui cordonne le nœud dès qu'un signal de santé GPU se dégrade, sur le modèle des contrôles de santé de Slurm (module 5, chapitre 7). Dans les trois cas, c'est JobSet ou Trainer qui relance le groupe sur d'autres nœuds.

::: recap
Points clés — chapitre 5

-   Kubernetes ne connaît la topologie que par des étiquettes de nœuds ; sans elles, aucun outil ne place par proximité.
-   Placement exclusif de JobSet, TAS de Kueue (bêta, activé par défaut) et TAS natif (alpha) : trois niveaux d'outillage.
-   `required` échange de l'attente contre de la bande passante, `preferred` l'inverse.
-   Le score par défaut répartit sur le CPU et la mémoire et fragmente les GPU ; `MostAllocated` pondéré sur la ressource GPU les regroupe.
-   Détection de nœud en panne : 50 s, puis 300 s de toleration par défaut ; réduire ce délai et détecter côté application.
:::

## 6. Stockage et données {#ch6}

Ce chapitre ne remplace pas le module 8 (stockage), qui traite des systèmes de fichiers parallèles. Il porte sur ce que Kubernetes ajoute : la façon d'exposer des volumes à un groupe de pods, et les chiffres à regarder avant de croire que « le stockage va suivre ».

### 6.1. Quatre usages, quatre profils

Un entraînement touche le stockage de quatre façons très différentes. L'**image** du conteneur est lue une fois par nœud au démarrage, en rafale. Les **données d'entraînement** sont lues en continu, souvent en petits accès. Les **checkpoints** sont écrits périodiquement en grosses rafales par tous les rangs, et relus au redémarrage. Les **fichiers temporaires et la mémoire partagée** (`/dev/shm`) sont locaux et sans durabilité. Chaque usage a son débit, sa durabilité et son point de défaillance ; les mélanger sur un seul volume est la source classique de surprises.

### 6.2. Les volumes Kubernetes

Un volume persistant (`PersistentVolume`) est demandé par une réclamation (`PersistentVolumeClaim`) qui indique une classe de stockage, une taille et un **mode d'accès**. D'après la documentation, les modes sont les suivants.

-   `ReadWriteOnce` : lecture et écriture par **un seul nœud** (plusieurs pods du même nœud peuvent y accéder).
-   `ReadOnlyMany` : lecture seule par plusieurs nœuds.
-   `ReadWriteMany` : lecture et écriture par plusieurs nœuds.
-   `ReadWriteOncePod` : lecture et écriture par **un seul pod** du cluster (stable depuis la v1.29).

Pour un volume partagé de checkpoints entre 16 pods répartis sur 16 nœuds, seul `ReadWriteMany` convient, ce qui impose une classe de stockage dont le pilote CSI le prend en charge, typiquement un système de fichiers partagé. La documentation prévient que `hostPath` est réservé aux tests sur un seul nœud et ne fonctionne pas sur un cluster multi-nœuds. La mémoire partagée se donne par un `emptyDir` de `medium: Memory`, comme dans le JobSet du lab 12.2 : `/dev/shm` par défaut est petit, et les chargeurs de données de PyTorch en ont besoin.

Les jeux de données massifs et les checkpoints archivés vivent souvent hors de tout volume, dans un stockage objet (compatible S3), que les pods lisent par le réseau. Le [module 8, chapitre 3](../storage/index.html#ch3) en donne les garanties et les caches : cohérence forte en lecture après écriture pour S3, mais pas de renommage atomique, même à travers un montage FUSE. Le protocole « fichier temporaire puis renommage » du §6.4 ne s'y applique donc pas tel quel.

### 6.3. Les données d'entraînement

::: ex
[Exemple 6.1 — Le débit de lecture d'un entraînement de texte est minuscule]{.tag} Avec la formule de PaLM de FLOP par token ($6N$ pour un modèle de $N$ paramètres, module 2), un H100 SXM à 40 % de MFU (*model FLOPs utilization*, part du pic réellement utilisée ; hypothèse) et un pic dense BF16 de 989 TFLOPS (la moitié de la valeur « avec sparsité » que la page produit NVIDIA donne pour la version SXM, voir le module 2 ; la version NVL a un pic plus bas), un modèle de 7 milliards de paramètres traite par GPU et par seconde :

$$\frac{0{,}4 \times 989 \cdot 10^{12}}{6 \times 7 \cdot 10^{9}} \approx 9\,400\ \text{tokens}$$

Pour 128 GPU : environ 1,2 million de tokens par seconde. À 2 octets par token (identifiants sur 16 bits ; 4 octets si le vocabulaire dépasse 65 536 entrées), la lecture demandée est de 2,4 Mo/s à 4,8 Mo/s. Calculs faits par un script Python du module.
:::

Cet ordre de grandeur change le regard : pour un entraînement de **texte tokenisé**, le débit de lecture est négligeable devant les capacités de n'importe quel stockage partagé, et la difficulté se trouve ailleurs (latence du premier accès, petits fichiers, métadonnées). Il en va autrement pour des images ou des vidéos brutes, où il faut refaire le calcul avec la taille réelle d'un échantillon.

Kubeflow Trainer propose de son côté un cache de données distribué, que sa documentation décrit comme conçu pour diffuser de gros volumes vers les nœuds GPU sans copie intermédiaire : c'est une option à évaluer, pas un prérequis.

### 6.4. Les checkpoints

C'est le vrai poids. Avec l'optimiseur Adam en précision mixte, l'état d'entraînement vaut 16 octets par paramètre (module 2, d'après ZeRO) ; un checkpoint omet les gradients et garde les poids en BF16 (2 octets) et l'état d'optimiseur (12 octets), soit environ 14 octets par paramètre dans ce modèle (le dimensionnement de référence du parcours est au [module 8, §1.4](../storage/index.html#dimensionner-le-checkpoint)). Selon le *framework*, ce chiffre peut aller de 12 à 14 octets : mesurez le vôtre.

::: ex
[Exemple 6.2 — Taille et durée d'un checkpoint]{.tag} Pour 7 milliards de paramètres : $14 \times 7 \cdot 10^9 = 98$ Go ; pour 70 milliards : 980 Go. Écrits à 10 Go/s agrégés, cela prend 9,8 s et 98 s ; à 2 Go/s, 49 s et 490 s. Avec un checkpoint toutes les 30 minutes (1 800 s), la part du temps passée à écrire est de 0,5 % et 5,4 % à 10 Go/s, de 2,7 % et 27,2 % à 2 Go/s. Les débits sont des hypothèses : c'est la méthode qui compte, et les chiffres de votre stockage se mesurent (module 8).
:::

Deux réserves. Le débit « agrégé » ne vaut que si **tous les rangs écrivent leur part** en parallèle ; un entraîneur où le rang 0 écrit seul (comme `train.py` du lab 12.2, volontairement simple) est limité par la carte réseau d'un seul nœud. Et l'écriture doit être **atomique** (fichier temporaire puis renommage), faute de quoi un redémarrage lit un checkpoint tronqué. La tolérance aux pannes est l'objet du module 10.

### 6.5. Le démarrage en rafale

Au redémarrage d'un groupe, tous les nœuds tirent la même image en même temps. La taille de l'image d'un framework d'entraînement est à mesurer pour la vôtre ; l'exemple suivant en suppose 20 Go.

::: ex
[Exemple 6.3 — Le tirage simultané d'une image]{.tag} Pour une image de 20 Go (valeur d'exemple) tirée par 128 nœuds, le registre sert $20 \times 128 = 2\,560$ Go. À 10 Go/s de débit de service, cela prend 256 s ; à 5 Go/s, 512 s. Ce temps entre directement dans le terme $R$ de la perte par panne du chapitre 4 : à 512 s, il dépasse à lui seul les 300 s supposés dans l'exemple 4.2.
:::

Les parades sont classiques : un miroir de registre local, un pré-tirage par DaemonSet sur les nœuds GPU, des images plus petites, un cache de nœud. Mesurez le temps de démarrage d'un groupe entier : c'est un indicateur de plateforme à suivre au même titre que l'utilisation des GPU.

::: recap
Points clés — chapitre 6

-   Quatre usages, quatre profils : image, données, checkpoints, fichiers temporaires.
-   Un volume partagé entre nœuds exige `ReadWriteMany` et un pilote CSI qui le prend en charge ; `hostPath` n'est que pour les tests.
-   Pour du texte tokenisé, la lecture se chiffre en Mo/s : négligeable ; les checkpoints sont le vrai poids.
-   Checkpoint : environ 14 octets par paramètre dans ce modèle, soit 98 Go pour 7 milliards ; le débit agrégé suppose que tous les rangs écrivent.
-   Le tirage simultané d'une image par 128 nœuds se compte en minutes et gonfle le coût de chaque redémarrage.
:::

## 7. Slurm ou Kubernetes ? {#ch7}

La question revient dans toute équipe qui monte une flotte GPU. Ce chapitre rassemble ce que les projets disent d'eux-mêmes, ce que montrent les retours publics, les modèles hybrides, et une méthode de décision dont on peut contester chaque ligne. Il évite volontairement de conclure en général : la bonne réponse dépend de l'équipe.

### 7.1. Ce que disent les deux projets

Slinky a été créé par SchedMD (les développeurs principaux de Slurm, désormais rattachés à NVIDIA d'après la [page de NVIDIA](https://www.nvidia.com/en-us/software/slinky/)) ; sa documentation le dit développé et soutenu par NVIDIA.

Ses concepteurs résument la différence dans leur documentation (résumé en français). Kubernetes excelle à ordonnancer des charges qui tournent pour une durée indéfinie, avec des besoins en ressources parfois vagues, sur un seul nœud, avec des règles souples, mais son parc de ressources peut croître sans limite pour suivre la demande. Slurm excelle à ordonnancer vite des charges de durée finie, avec des besoins et une topologie bien définis, sur plusieurs nœuds, avec des règles strictes, mais son parc est connu.

Cette phrase vient d'un projet qui vend un pont entre les deux, ce qui n'en fait pas une preuve ; mais elle recoupe ce que ce module a montré. Le chapitre 3 a vu que les fonctions de file et de gang sont natives dans Slurm et à assembler dans Kubernetes ; le chapitre 4 que le lancement d'un job multi-nœuds exige JobSet ou Trainer.

### 7.2. Ce que montrent les retours publics

Les retours publics détaillés sont rares et ne comparent pas. Deux sources lues pour ce module.

-   Hu et al. (2024) décrivent les clusters de développement de grands modèles d'un laboratoire d'IA, nommés Seren et Kalos, qui totalisent 4 704 GPU A100 (2 288 et 2 416 GPU) ; leur texte indique que l'ordonnanceur de Seren est construit sur Slurm et celui de Kalos sur Kubernetes : les deux technologies coexistent donc dans une même organisation, sur deux clusters de taille comparable.
-   Kokolis et al. (2024) analysent 11 mois de données de clusters de recherche, avec des jobs jusqu'à 4 000 GPU ; leur texte indique que ces clusters utilisent l'ordonnanceur Slurm, qui peut exécuter des contrôles avant et après un job.

Ces deux documents établissent qu'**on fait de l'entraînement à grande échelle avec les deux**. Ils n'établissent pas lequel est le meilleur, car leurs auteurs ne comparent pas à charge égale, et ils ne portent pas sur les outils de 2026 (Kueue, JobSet, ordonnancement de groupe natif) qui n'existaient pas ou étaient jeunes à l'époque. Méfiez-vous des affirmations tranchées qui s'appuient dessus.

### 7.3. Les modèles hybrides

Quatre modèles se rencontrent ; les deux premiers sont documentés par leurs projets. Ils répondent à des organisations qui veulent l'exploitation de Kubernetes **et** les habitudes de Slurm.

-   **Slurm sur Kubernetes, par opérateur.** Le projet Slinky fournit `slurm-operator`, qui déploie un cluster Slurm comme des ressources Kubernetes (des `NodeSet` dont les pods exécutent `slurmd`). La version 1.2 affichée le 24 octobre 2026 exige Kubernetes 1.29 au minimum et Slurm 25.11 au minimum. L'offre de CoreWeave, SUNK, suit le même principe d'après sa documentation : les nœuds Slurm sont des pods, et un « ordonnanceur de pods » arbitre entre Slurm et Kubernetes sur les mêmes nœuds.
-   **Un pont d'ordonnancement.** `slurm-bridge`, de Slinky, est un ordonnanceur Kubernetes qui confie à Slurm l'ordonnancement de charges choisies, pour faire cohabiter les deux types de charges dans le même cluster. Kubeflow Trainer documente une intégration « Slurm Bridge » pour que des `TrainJob` soient ordonnancés par Slurm.
-   **Deux clusters distincts**, comme le laboratoire d'IA ci-dessus : le plus simple à comprendre, avec le coût d'un parc partitionné.
-   **Un Kubernetes avec Kueue seul**, qui n'est pas un hybride mais la réponse sans Slurm.

Le coût d'un hybride est une **double compétence** et deux couches d'états à garder cohérentes (un pod non prêt doit apparaître comme un nœud drainé, et inversement). Slinky et SUNK ont des mécanismes pour cela ; vous les exploitez.

### 7.4. Une grille de décision défendable

Le lab 12.3 propose une grille de 12 critères, trois options (Slurm natif, Kubernetes avec Kueue et JobSet, Slurm sur Kubernetes), un score de 1 à 5 par case avec une phrase de justification, cinq profils d'équipe fictifs (poids de 0 à 5 et exigences éliminatoires) et un outil qui calcule

$$S_o \;=\; 100 \times \frac{\sum_c w_c\, s_{o,c}}{5\sum_c w_c},$$

c'est-à-dire la moyenne pondérée des scores ramenée à $[20, 100]$. Les scores sont **le jugement de ce parcours au 24 octobre 2026**, pas des mesures. L'outil ajoute ce qui manque aux grilles habituelles : il perturbe les poids (facteur aléatoire dans $[0{,}5 ;\, 1{,}5]$) et, une fois sur quatre, chaque score de $\pm 1$, et compte la fréquence de victoire de chaque option.

::: ex
[Exemple 7.1 — Cinq profils, une robustesse]{.tag} Sortie de `python3 score.py --draws 2000 --seed 0` (24 octobre 2026, 2 000 tirages ; `x` = exigence éliminatoire non satisfaite) :

~~~text
scenario                  slurm    k8s hybrid  winner   margin  stability
research-lab               87.4   66.9x   81.7  slurm       5.7  slurm 88%, hybrid 12%
inference-first-startup    59.4x   85.1   77.7  k8s         7.4  k8s 93%, hybrid 7%
enterprise-platform        73.3   75.7   80.5  hybrid      4.8  hybrid 82%, k8s 14%, slurm 4%
sovereign-hpc-center       85.5   68.0   82.0x  slurm      17.5  slurm 94%, hybrid 5%, k8s 0%
gpu-cloud-provider         70.0   77.0   81.7  hybrid      4.8  hybrid 86%, k8s 14%, slurm 0%
~~~

Le laboratoire de recherche choisit Slurm (écart de 5,7 points, victoire dans 88 % des perturbations), la start-up centrée sur l'inférence choisit Kubernetes, le centre de calcul à très grande échelle choisit Slurm avec une marge de 17,5 points. Les deux profils où l'hybride gagne ont des marges de 4,8 points : ce sont des débats, pas des évidences.
:::

::: ex
[Exemple 7.2 — Le biais de l'hybride]{.tag} L'option hybride reprend les points forts des deux autres et perd surtout sur la simplicité d'exploitation, où elle a 2 sur 5 (et un peu sur la maturité, 3 sur 5). Dans le profil d'entreprise, le poids de ce critère doit passer de 4 à **11,55** pour que le vainqueur change, ce qui sort de l'échelle de 0 à 5 : la pondération seule ne peut pas exprimer « nous n'avons que deux personnes pour exploiter ».

C'est le rôle des exigences éliminatoires. Avec un poids de 5 pour le critère de simplicité et une exigence « au moins 3 », l'hybride est éliminé et Kubernetes (75,3) devance Slurm (73,5) de 1,9 point, une marge que 54 % des perturbations seulement confirment. L'exercice 10 vous demande de le refaire.
:::

### 7.5. Ce que le choix coûte

Chaque option a un coût caché qu'il vaut mieux nommer avant de choisir.

-   **Slurm natif** : une pile d'exploitation spécifique (comptabilité, base de données, scripts de nœuds) à côté du reste de l'infrastructure, et peu de services permanents. Les utilisateurs, eux, ne changent pas.
-   **Kubernetes avec Kueue** : un assemblage de composants à maintenir à jour et à tester ensemble (plugin ou DRA, opérateur GPU, Kueue, JobSet ou Trainer, réseau secondaire), et des chercheurs à former aux manifestes et aux images. Le CNCF a lancé le 11 novembre 2025 un programme de conformité « AI Conformance » dont les premiers participants ont été certifiés en v1.0 ; le contenu précis des exigences est à lire à la source avant d'y compter.
-   **Hybride** : la somme des deux compétences, sur un projet plus jeune.

Trois questions suffisent souvent à orienter. **Qui sont les utilisateurs et que savent-ils faire ?** Une équipe qui écrit des `sbatch` depuis dix ans ne gagne rien à écrire des manifestes. **Quelle est la part de services permanents ?** Si elle est significative, Kubernetes devient l'évidence. **Combien de personnes exploitent, avec quelles compétences ?** Une plateforme assemblée coûte plus à tenir qu'un seul ordonnanceur.

::: recap
Points clés — chapitre 7

-   Slurm excelle à ordonnancer vite des jobs finis, multi-nœuds, sous règles strictes ; Kubernetes excelle aux services et à l'élasticité (d'après la documentation de Slinky).
-   Les retours publics lus montrent qu'on entraîne à grande échelle avec les deux, sans comparer les deux à charge égale.
-   Les hybrides (Slinky, SUNK) conservent les scripts Slurm au prix d'une double compétence.
-   Une grille pondérée est une aide à la discussion : exigez ses justifications, ses exigences éliminatoires et sa robustesse aux perturbations.
-   Les marges de moins de 5 points dans la grille du lab sont des débats, pas des décisions.
:::

## 8. Exploitation : mises à jour, sécurité, multi-tenance, coûts {#ch8}

Une plateforme d'entraînement se juge à ce qu'elle fait un mardi ordinaire : combien de temps prend une mise à jour de pilote, qui peut faire quoi, qui consomme quoi, et ce que coûte réellement une heure de GPU active. Ce chapitre donne la méthode, pas des prix.

### 8.1. Les mises à jour

Kubernetes maintient trois versions mineures et offre environ un an de correctifs par version. La page des versions, lue le 24 octobre 2026, donne pour fin de vie le 28 février 2027 pour la 1.35, le 28 juin 2027 pour la 1.36 et le 28 octobre 2027 pour la 1.37. Le décalage de version autorisé entre composants aide à étaler une mise à jour : d'après la politique de décalage, un kubelet peut avoir jusqu'à trois versions mineures de retard sur le serveur d'API.

La couche GPU a sa propre mise à jour. Pour les pilotes gérés par l'opérateur GPU, la documentation décrit une politique `upgradePolicy` avec, par défaut, `autoUpgrade: true`, `maxParallelUpgrades: 1` et `maxUnavailable: 25%`, plus des réglages d'attente des jobs en cours et de vidage du nœud. Une mise à jour de l'opérateur peut exiger des mises à jour de CRD.

::: ex
[Exemple 8.1 — Combien de temps pour changer de pilote sur 128 nœuds ?]{.tag} Avec le paramètre par défaut d'un nœud à la fois et 15 minutes par nœud (vidage, rechargement du pilote, validation : valeur d'exemple), $128 \times 15 = 1\,920$ minutes, soit 32 h. Avec 8 nœuds en parallèle, $\lceil 128/8 \rceil = 16$ vagues de 15 minutes, soit 4 h ; 8 nœuds de 8 GPU représentent 64 GPU sur 1 024, soit 6,25 % de la flotte hors service à tout instant. Le plafond `maxUnavailable: 25%` autoriserait jusqu'à 32 nœuds en parallèle. Calculs faits par un script Python du module.
:::

Deux règles de prudence en découlent. Une mise à jour de la couche GPU est une opération de flotte : elle se planifie avec les équipes d'entraînement, qui doivent pouvoir faire un checkpoint et relancer.

Et les API évoluent : dans la CRD de Kueue v0.20.3, la version `v1beta1` de chaque type est marquée dépréciée et **n'est plus servie** (`served: false`), seule `v1beta2` l'est. Des manifestes anciens cessent de s'appliquer à la mise à jour : validez-les contre les CRD de la version cible, comme le fait le lab 12.1.

### 8.2. La sécurité

Trois niveaux de contrôle, tous standards, ont une saveur particulière avec les GPU.

-   **Pod Security.** Les niveaux `privileged`, `baseline` et `restricted` s'appliquent par étiquette d'espace de noms. Là où Pod Security Admission est appliqué, l'opérateur GPU exige un espace de noms `privileged` : ses composants s'exécutent en mode privilégié, et sa [page sécurité](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/security.html) réserve l'accès de cet espace de noms à l'administrateur du cluster. Les espaces de noms des équipes, eux, ne devraient pas l'être ; les besoins particuliers (mémoire verrouillée pour RDMA, par exemple) se justifient au cas par cas.
-   **RBAC.** Les utilisateurs créent des Jobs, JobSets ou TrainJobs dans leur espace de noms ; les objets de cluster (ClusterQueue, ResourceFlavor, WorkloadPriorityClass, DeviceClass) sont réservés aux administrateurs. Un `namespaceSelector` de ClusterQueue défini à `null` n'autorise aucun espace de noms, et à `{}` les autorise tous : prenez le premier comme défaut.
-   **Réseau.** Un entraînement a besoin que ses pods se parlent (port de rendez-vous, ports NCCL, réseau secondaire) et de peu d'autre chose. Une `NetworkPolicy` qui n'autorise que les pods du même JobSet est un bon point de départ ; son effet dépend du plugin réseau, à tester.

La documentation de Kubernetes propose un guide de durcissement pour DRA, à lire avant d'activer DRA en production. Et la CRD de Kueue renvoie elle-même à un agent de politiques comme Gatekeeper pour les règles avancées : qui peut utiliser la priorité `urgent` n'est pas décidé par Kueue seul.

### 8.3. La multi-tenance

Deux mécanismes se superposent et ne se remplacent pas. Le `ResourceQuota` de Kubernetes plafonne la consommation d'un espace de noms ; pour une ressource étendue, la documentation indique que seul le préfixe `requests.` est permis, par exemple `requests.nvidia.com/gpu: 4`. Les quotas de **Kueue** s'appliquent à la file, avec prêt, emprunt et préemption entre files d'une cohorte.

Le montage que ce parcours recommande : un espace de noms par équipe, une `LocalQueue` par espace de noms, une `ClusterQueue` par équipe dans une cohorte commune, et un `ResourceQuota` large comme filet de sécurité contre une erreur de configuration (il ne remplace pas les quotas de file). L'exercice 11 vous fait concevoir ce montage pour un pool de 256 GPU et le valider avec les outils du lab 12.1.

### 8.4. Les coûts

On ne gère pas le coût d'une flotte GPU avec un prix de catalogue mais avec un **rendement**. Deux facteurs séparent le prix d'une heure de GPU du prix d'une heure de GPU *active* : la fraction $a$ du temps GPU acheté qui est allouée à des jobs (l'allocation), et l'activité moyenne $u$ de ces GPU alloués, telle que DCGM la mesure (l'utilisation). Le coût d'une heure active, rapporté au prix d'une heure de catalogue $c$, est :

$$c_{\text{actif}} = \frac{c}{a \times u}$$

Le [module 15](../finops-capacity/index.html#ch1) affine ce calcul pour obtenir le coût d'une heure *utile* : il remplace l'utilisation $u$, simple indice mesuré par DCGM, par le goodput $g$ du module 10, la part des heures allouées qui produit un calcul conservé.

::: ex
[Exemple 8.2 — Le multiplicateur de coût]{.tag} Avec des rendements **illustratifs** : si 85 % du temps GPU est alloué mais que les GPU alloués ne travaillent qu'à 55 %, l'heure active coûte $1/(0{,}85 \times 0{,}55) \approx 2{,}14$ fois le prix de catalogue. Avec 70 % d'allocation et 80 % d'utilisation, le multiplicateur est de 1,79.

La seconde flotte alloue moins mais utilise mieux : sa situation est meilleure. Le prix $c$ n'intervient pas dans la comparaison ; lisez la page de prix de votre fournisseur le jour où vous décidez.
:::

Les deux facteurs se mesurent. L'allocation vient des objets Kubernetes et de Kueue (pods ou Workloads admis rapportés à la capacité). L'utilisation vient de la supervision GPU (DCGM Exporter), dont la métrique d'utilisation est grossière et ne dit pas si le GPU calcule vraiment : voyez le module 14 et le [Projet 5](../../projects/gpu-observability/index.html).

Avec le *time-slicing*, la documentation de l'opérateur précise que DCGM Exporter ne peut pas associer les métriques à des conteneurs : l'attribution du coût par pod devient impossible, ce qui est une raison de plus de préférer MIG ou DRA pour de la refacturation. La suite de la méthode (capacité, engagement, refacturation) relève du [module 15](../finops-capacity/index.html).

::: recap
Points clés — chapitre 8

-   Trois versions mineures de Kubernetes sont maintenues ; la 1.35 sort du support le 28 février 2027, soit 127 jours après la date de rédaction.
-   La mise à jour de pilote GPU est une opération de flotte : 32 h à un nœud à la fois pour 128 nœuds, 4 h à 8 en parallèle.
-   Les API de Kueue changent (`v1beta1` n'est plus servie en v0.20.3) : validez vos manifestes contre la version cible.
-   L'opérateur GPU est privilégié, pas les espaces de noms d'équipe ; `namespaceSelector: null` est le bon défaut.
-   `ResourceQuota` (`requests.` seulement pour les ressources étendues) comme filet, Kueue pour le partage.
-   Le coût d'une heure active est le prix divisé par allocation × utilisation ; le module 15 remplace l'utilisation par le goodput pour l'heure utile ; le prix de catalogue se lit le jour même.
:::

## Labs {#labs}

Quatre labs, dans `labs/kubernetes-gpu/`. Trois sont de type **sandbox** : leur `verify.sh` a été exécuté deux fois avec succès dans le bac à sable du module (Linux 6.18, 4 vCPU, 16 Go, sans GPU) le 24 octobre 2026. Le lab 12.2 est de type **cluster** : sa partie hors cluster a été exécutée, sa partie cluster **ne l'a pas été**, d'où le badge « non vérifié ». Installation commune :

~~~bash
python3 -m pip install pytest pyyaml jsonschema kubernetes-validate torch
~~~

### Lab 12.1 — Kueue : files, quotas, préemption {#lab-12-1}

::: lab

**Objectif.** Valider hors ligne un jeu de manifestes Kueue (64 GPU, trois équipes), écrire le modèle d'admission qui prédit qui est admis et préempté, puis le confronter à des scénarios. **Durée.** 3 h. **Prérequis matériels.** Un portable Linux sans GPU, ni cluster, ni réseau une fois les paquets installés.

Les manifestes sont validés contre le schéma des CRD de Kueue v0.20.3 (copie élaguée, régénérable) et les schémas de Kubernetes 1.37. Le modèle d'admission est une **simulation écrite d'après la documentation**, pas le code de Kueue : il ignore le *fair sharing*, la fongibilité des *flavors* et la durée réelle d'une éviction.

1.  Lisez `manifests/30-clusterqueues.yaml` et retrouvez à la main la capacité du pool (48 GPU prêtables) et le plafond de chaque équipe (exemple 3.1).
2.  Lancez `python3 validate_manifests.py manifests`, puis cassez un manifeste (une coquille dans `queueingStrategy`, un `borrowingLimit` sans cohorte) et lisez le rejet.
3.  Dans `starter/admission.py`, écrivez l'emprunt et le prêt, la stratégie de file, puis la préemption : `IMPL=starter python3 -m pytest -q tests` doit passer de 11 échecs à zéro. Ne lisez `reference/` qu'après votre tentative.
4.  Rejouez `python3 run_scenario.py scenarios/platform-day.yaml` en prédisant chaque ligne (exemple 3.2), puis lancez `gang_deadlock.py` et `topology_fit.py` (exemples 3.3 et 5.1).

**Critère de réussite.** `bash verify.sh` se termine par `OK kueue-manifests`, après `16/16 documents valid`, `36 passed` pour la référence et `11 failed, 25 passed` pour le départ (sortie réelle, deux exécutions, environ 10 s).

**Pour aller plus loin.** Ajoutez le *fair sharing* au modèle, ou installez Kueue sur un cluster de test et comparez `kubectl get workloads` à la trace du modèle.
:::

### Lab 12.2 — JobSet : un entraînement multi-nœuds {#lab-12-2}

::: lab

**Objectif.** Lancer un entraînement `torchrun` sur 16 nœuds de 8 GPU, sous file Kueue, redémarré en bloc par JobSet, puis par Kubeflow Trainer. **Durée.** 2,5 h hors cluster, 2 h de plus sur un cluster. **Prérequis matériels.** Hors cluster : un portable Linux (PyTorch CPU suffit). Branche cluster : Kubernetes avec GPU, JobSet, Kueue et l'opérateur GPU ; le coût dépend du fournisseur, lisez sa page de prix le jour même.

*Exécuté :* lint, validation de schéma du JobSet (v0.13.0) et du TrainJob (Trainer v2.1.0) contre les CRD upstream avec rejet de quatre JobSet mutés, répétition locale du redémarrage avec deux processus `torchrun` (une simulation de l'orchestration), acceptation des manifestes par un `kube-apiserver` v1.37.1 réel (lab 12.4). *Non exécuté :* tout ce qui touche des pods, des GPU, NCCL, Kueue ou un redémarrage réel.

1.  Lisez `manifests/20-jobset-torchrun.yaml` : nom DNS du pod 0, rendez-vous, `maxRestarts`, annotation de topologie, file.
2.  Lancez `bash verify.sh`, lisez la répétition locale (exemple 4.1), changez `--die-at-step` et `--ckpt-every` et prédisez le pas de reprise.
3.  Comparez `30-trainjob.yaml` au JobSet : quelles lignes disparaissent, lesquelles sont portées par le runtime ?
4.  Sur un cluster (non exécuté par l'auteur) : remplacez l'image, appliquez les manifestes du lab 12.1 puis ceux-ci, supprimez un pod et observez la recréation du groupe.

**Critère de réussite.** Hors cluster : `OK jobset-training (offline branch): manifests valid, 1 restart, resumed from step 20, finished at step 60; cluster branch NOT executed` (sortie réelle, deux exécutions, environ 20 s). Sur cluster : après suppression d'un pod, tous les pods sont recréés et le journal du rang 0 affiche `resuming_from_step=` avec un pas non nul.

**Pour aller plus loin.** Ajoutez un meneur (second `replicatedJob`) et comparez le temps de redémarrage réel au terme $R$ de l'exemple 4.2.
:::

### Lab 12.3 — Matrice de décision Slurm / Kubernetes {#lab-12-3}

::: lab

**Objectif.** Défendre par écrit un choix Slurm, Kubernetes ou hybride avec une grille pondérée dont chaque score est justifié et dont la robustesse est mesurée. **Durée.** 1,5 h. **Prérequis matériels.** Un portable Linux sans GPU.

1.  Lisez `criteria.yaml` : pour trois critères, dites si vous changeriez le score, et pourquoi.
2.  Lancez `bash verify.sh` : neuf tests, le tableau des cinq profils, un point de bascule (exemples 7.1 et 7.2).
3.  Écrivez dans `scenarios.yaml` le profil de votre équipe (poids de 0 à 5, exigences éliminatoires) et relevez le vainqueur, la marge et la stabilité.
4.  Modifiez un score que vous contestez : le vainqueur change-t-il ? Rédigez en dix lignes la décision et ce qui la renverserait.

**Critère de réussite.** `bash verify.sh` se termine par `OK slurm-vs-k8s: matrix well formed, tests green` après `9 passed` (sortie réelle, deux exécutions, moins de 5 s), et votre note cite une marge et une stabilité.

**Pour aller plus loin.** Ajoutez un critère « taille de l'équipe d'exploitation » et une option « cloud géré ».
:::

### Lab 12.4 — Un plan de contrôle Kubernetes 1.37 sans kubelet {#lab-12-4}

::: lab

**Objectif.** Démarrer un vrai plan de contrôle (etcd, kube-apiserver, kube-controller-manager, kube-scheduler en v1.37.1) avec des nœuds GPU factices, observer l'ordonnancement de groupe natif et la fragmentation, et faire valider les manifestes du module par le serveur d'API. **Durée.** 3 h. **Prérequis matériels.** Linux x86_64, accès HTTPS vers `dl.k8s.io`, `registry.k8s.io` et `raw.githubusercontent.com` ; environ 350 Mo téléchargés au premier lancement ; ni Docker ni GPU.

Les nœuds sont des objets créés par le script, avec une capacité déclarée ; les pods sont liés par le vrai ordonnanceur mais ne s'exécutent jamais. On observe donc l'ordonnancement et la validation d'API, pas l'exécution, ni Kueue, ni JobSet, ni l'opérateur GPU (seules leurs CRD sont installées). Les binaires sont vérifiés contre leur `.sha256` et `etcd` contre les résumés des couches de l'image `registry.k8s.io/etcd`.

1.  Partie A : lisez `lib.sh`, lancez `bash up.sh` puis `bash gang_demo.sh` (exemples 1.1 et 3.4) et notez les portes de fonctionnalités activées.
2.  Partie B : lancez `bash fragmentation_demo.sh` (exemple 5.2) ; changez les demandes de CPU de `manifests/job-small.yaml` et observez le placement.
3.  Partie C : lancez `bash validate_server_side.sh` (il rejoue aussi les quatre variantes de l'exercice 1), puis écrivez votre propre manifeste invalide et lisez le rejet, règles CEL comprises.
4.  Terminez par `bash down.sh` et vérifiez qu'aucun processus ne reste (`pgrep -l kube`).

**Critère de réussite.** `bash verify.sh` se termine par `OK mini-control-plane: Kubernetes v1.37.1 control plane without kubelet; gang demo and server-side validation passed`, après `OK gang_demo: basic job bound 6/8 pods, gang job bound 0/8 on 6 nodes then 8/8 on 8 nodes` (sortie réelle, deux exécutions de 1,5 à 2 minutes avec le cache chaud ; aucun processus résiduel).

**Pour aller plus loin.** Cordonnez un nœud pendant que le Job gang est lié, ou activez la porte `TopologyAwareWorkloadScheduling` (alpha depuis la v1.36) et ajoutez une contrainte de topologie au `PodGroup`.
:::

## Exercices {#ex}

Les corrigés ont été vérifiés : les calculs refaits en Python, les réponses du serveur d'API et les traces reproduites avec les labs du module (24 octobre 2026).

::: exo
[Exercice 1 · ★ — Quatre pods de GPU, trois refus]{.tag} Voici quatre variantes de la section `resources` d'un conteneur, soumises à un serveur d'API Kubernetes v1.37.1 par `kubectl apply --dry-run=server`. Dites, sans les exécuter, lesquelles sont refusées et pourquoi.

~~~yaml
# a
resources: {requests: {nvidia.com/gpu: 2}}
# b
resources: {requests: {nvidia.com/gpu: 1}, limits: {nvidia.com/gpu: 2}}
# c
resources: {limits: {nvidia.com/gpu: 0.5}}
# d
resources: {requests: {nvidia.com/gpu: 2}, limits: {nvidia.com/gpu: 2}}
~~~
:::

::: sol
Seule la variante **d** est acceptée. Les réponses réelles du serveur, obtenues dans le lab 12.4 (partie C) :

~~~text
a: spec.containers[0].resources.limits: Required value: Limit must be set for non overcommitable resources
b: spec.containers[0].resources.requests: Invalid value: "1": must be equal to nvidia.com/gpu limit of 2
c: spec.containers[0].resources.limits[nvidia.com/gpu]: Invalid value: "500m": must be an integer
d: pod/t created (server dry run)
~~~

La règle : une ressource étendue est un entier, ne se suralloue pas, se déclare sous `limits`, et `requests` s'il est présent doit lui être égal (documentation « Schedule GPUs »). Pour obtenir « un demi-GPU », il faut un mécanisme de partage (exercice 2), pas une fraction dans le manifeste.
:::

::: exo
[Exercice 2 · ★ — Vingt réplicas d'inférence sur des H100]{.tag} Vous servez 20 réplicas d'un modèle qui tient dans 10 Go de mémoire GPU, sur des H100 de 80 Go. Combien de GPU faut-il avec MIG en `1g.10gb` ? avec le *time-slicing* à 8 réplicas par GPU ? Que garantit chaque option, et que risque-t-on ?
:::

::: sol
**MIG.** Le profil `1g.10gb` donne 7 instances par GPU : $\lceil 20/7 \rceil = 3$ GPU, soit 21 instances pour 20 réplicas. Chaque instance a sa mémoire, sa bande passante et son isolation de défaut. Il reste $1/8$ de la mémoire (10 Go) hors de portée sur chaque GPU.

**Time-slicing.** Avec 8 réplicas par GPU : $\lceil 20/8 \rceil = 3$ GPU aussi, soit 24 places. Mais huit pods de 10 Go occupent exactement les 80 Go : aucune marge, et aucune isolation. Un pod qui dépasse ses 10 Go ou qui plante peut faire échouer les sept autres. Aucune part de calcul n'est garantie non plus.

Même nombre de GPU, garanties très différentes : MIG est le bon choix si le niveau de service compte. Calcul vérifié par script.
:::

::: exo
[Exercice 3 · ★★ — MIG, time-slicing ou DRA ?]{.tag} Une petite flotte compte deux nœuds de 8 H100 de 80 Go. Elle doit héberger : (a) 14 réplicas d'inférence à latence contrôlée, 20 Go chacun ; (b) 6 notebooks de développement, 10 Go chacun, tolérants au bruit ; (c) un entraînement qui exige 4 GPU entiers. Proposez une répartition avec la stratégie MIG `single`, puis avec `mixed`, comptez les GPU, et dites ce que vous ne pouvez pas obtenir avec chacune.
:::

::: sol
**Besoins.** Le profil `1g.20gb` donne 4 instances par GPU : (a) demande $\lceil 14/4 \rceil = 4$ GPU. Le profil `1g.10gb` en donne 7 : (b) demande $\lceil 6/7 \rceil = 1$ GPU. (c) demande 4 GPU entiers. Au total 9 GPU sur 16.

**Stratégie `single`** (tous les GPU d'un nœud avec le même profil). Le nœud A passe tout en `1g.20gb` : 32 instances, dont 14 pour (a) et 6 pour (b) (une instance de 20 Go suffit à un notebook de 10 Go) ; les 12 restantes sont inutilisables comme GPU entiers. Le nœud B reste en GPU entiers pour (c). Deux nœuds suffisent.

**Stratégie `mixed`.** Quatre GPU en `1g.20gb`, un en `1g.10gb`, quatre entiers pour (c) : 9 GPU utilisés, **7 GPU entiers libres** pour d'autres entraînements. Mais reconfigurer un GPU exige de vider le nœud (documentation du MIG Manager).

**Ce qui manque à chacune.** Ni l'une ni l'autre ne suit une demande qui varie dans la journée sans vidage de nœud ; DRA vise à décrire le besoin par réclamation, avec des fonctions encore alpha dans le pilote NVIDIA 0.5.1. Le time-slicing conviendrait à (b), pas à (a) faute d'isolation.
:::

::: exo
[Exercice 4 · ★★ — Arithmétique de quotas]{.tag} Trois ClusterQueue d'une même cohorte, sur une seule ressource (GPU) : A a $n=40$, $b=8$ et $\ell=10$ ; B a $n=24$ sans limite ; C a $n=16$ avec $b=0$. (1) Quelle est la capacité du pool ? (2) Combien de GPU chaque file peut-elle obtenir quand les deux autres sont vides ? (3) A utilise 48 GPU : combien B peut-elle obtenir sans préemption ?
:::

::: sol
(1) La capacité du pool est la somme des quantités prêtables : $10 + 24 + 16 = 50$. A garde $40 - 10 = 30$ GPU pour elle.

(2) A est plafonnée par son emprunt : $40 + 8 = 48$ ; son usage dans le pool est $48 - 30 = 18 \le 50$. B n'a pas de limite d'emprunt mais le pool est de 50, et rien n'est réservé : **50** (les 30 GPU réservés d'A lui sont inaccessibles). C n'emprunte pas : **16**.

(3) Quand A utilise 48, son usage dans le pool est $48 - 30 = 18$, il reste $50 - 18 = 32$ pour les autres, donc B obtient **32** GPU.

Ces trois résultats (48, 50, 16, puis 32) ont été retrouvés par le modèle d'admission du lab 12.1 en soumettant des Workloads d'un GPU jusqu'au refus.
:::

::: exo
[Exercice 5 · ★★ — Lire une sortie de PodGroup]{.tag} Le Job gang de l'exemple 3.4 (8 pods de 8 GPU) tourne sur 6 nœuds de 8 GPU libres. La sortie est reproduite ci-dessous, capturée dans le lab 12.4. (a) Pourquoi aucun pod n'est-il lié ? (b) Que signifie « No preemption victims found » ? (c) Combien de GPU sont retenus inutilement, par comparaison avec l'exemple 1.1 ?

~~~text
bound pods: 0 of 8
PODGROUP                                           POLICY   REASON
train-gang-57b57577fc-train-gang-pgt-0-8ff484b67   8        Unschedulable
PodGroup message: minCount (8) cannot be satisfied: 6 scheduled, 1 remaining, pod group preemption: No preemption victims found for incoming preemptor
~~~
:::

::: sol
(a) La politique est `gang` avec `minCount` égal à `parallelism`, soit 8. Il n'y a que 6 nœuds de 8 GPU pour des pods qui demandent chacun 8 GPU : l'ordonnanceur ne trouve pas de placement pour 8 pods, donc il n'en lie **aucun**. Le décompte « 6 scheduled, 1 remaining » est celui de la tentative de placement du cycle (six placements provisoires, puis le septième pod ne trouve plus de nœud et le cycle s'arrête) : c'est une interprétation de l'auteur, la documentation ne détaille pas ce message.

(b) La préemption sensible aux groupes (bêta en v1.37) cherche, sur tout le cluster, des victimes de priorité plus basse dont l'éviction permettrait le placement. Ici il n'y en a aucune : aucun autre workload ne tourne. Le groupe attend.

(c) Dans l'exemple 1.1 (pods lus un par un) : 6 pods liés, soit 48 GPU retenus pour rien. Ici : 0. Les 48 GPU restent disponibles pour d'autres charges tant que le groupe attend.
:::

::: exo
[Exercice 6 · ★ — Les parts d'une file Volcano]{.tag} Trois files Volcano ont pour poids 1, 2 et 5 sur un parc de 128 GPU. Calculez la part due à chacune. La file de poids 5 n'utilise que 60 GPU et les deux autres veulent tout : que peut-il se passer, et à quelle condition ?
:::

::: sol
La documentation de Volcano donne la part due (*deserved*) d'une file, avec un poids total de 8 :

$$\text{deserved} = \frac{\text{weight}}{\text{total-weight}} \times \text{total-resource}$$

On obtient 16, 32 et 80 GPU ; la somme fait bien 128.

La file de poids 5 laisse $80 - 60 = 20$ GPU inutilisés. D'après la documentation, le poids est une contrainte **souple** : les autres files peuvent dépasser leur part en empruntant ces 20 GPU, mais doivent les rendre quand la file de poids 5 en a besoin, jusqu'à ce que leur usage retombe à leur part due. Condition : que les files qui ont dépassé leur part aient le champ `reclaimable` à vrai (c'est la valeur par défaut d'après la documentation) et que le plugin de proportion soit activé.
:::

::: exo
[Exercice 7 · ★★ — Dimensionner un JobSet pour 7 milliards de paramètres]{.tag} Un entraînement de 7 milliards de paramètres tourne sur 4 nœuds de 8 GPU pendant 200 h. Le MTBF mesuré de ce job de 4 nœuds est de 40 h ; un checkpoint pèse 98 Go et s'écrit à 10 Go/s agrégés ; le redémarrage d'un JobSet prend $R = 300$ s. Donnez : les options `torchrun` et le point de rendez-vous du JobSet nommé `pretrain-7b`, l'intervalle de checkpoints de Young-Daly (premier ordre), la perte moyenne par panne, et un `maxRestarts` défendable (on modélisera les pannes par un processus de Poisson, de taux $1/\text{MTBF}$).
:::

::: sol
**Lancement.** `--nnodes=4 --nproc_per_node=8`, rendez-vous `c10d` sur `pretrain-7b-workers-0-0.pretrain-7b:29500` (nom du pod 0 du Job `workers`, sous le sous-domaine du JobSet, selon le modèle `<jobset>-<replicatedJob>-<job>-<pod>.<sous-domaine>`), `--rdzv_id=pretrain-7b`, et `completionMode: Indexed` avec `backoffLimit: 0` : le Job échoue à la première panne et JobSet recrée le groupe entier.

**Intervalle.** Le temps d'écriture est $\delta = 98 / 10 = 9{,}8$ s. L'intervalle du premier ordre (Young-Daly) est

$$\tau^\star = \sqrt{2\,\delta\,M} = \sqrt{2 \times 9{,}8 \times 144\,000} = 1\,680\ \text{s} = 28\ \text{min},$$

soit 280 pas à 6 s par pas. **Perte moyenne** : $R + \tau^\star/2 = 300 + 840 = 1\,140$ s par panne.

**Redémarrages.** Sur 200 h, on attend $200/40 = 5$ pannes (modèle de Poisson). Avec `maxRestarts: 8`, la probabilité de dépasser (au moins 9 pannes) est de 6,8 % ; avec 10, de 1,4 % ; avec 12, de 0,2 %. Un `maxRestarts` de 10 à 12 est défendable ; au-delà, une panne qui se répète est probablement un défaut du nœud, pas de la malchance (module 10).
:::

::: exo
[Exercice 8 · ★★★ — 28 GPU libres et un pod qui attend]{.tag} Sur un cluster de 4 nœuds de 8 GPU, un Job de 4 pods d'un GPU (8 cœurs et 64 Gio chacun) tourne depuis une heure. Un pod qui exige un nœud entier (8 GPU) est créé : il reste `Pending` avec le message `0/4 nodes are available: 4 Insufficient nvidia.com/gpu.`, alors que `kubectl describe nodes` montre 28 GPU libres au total et que le quota Kueue de la file dit 28 GPU disponibles. Posez le diagnostic, donnez trois remèdes et leurs inconvénients, et dites ce que la file Kueue aurait fait de ce Workload.
:::

::: sol
**Diagnostic.** Les 4 petits pods sont répartis un par nœud : chaque nœud a 7 GPU libres, aucun n'en a 8 (sortie réelle du lab 12.4, partie B). La cause est le score par défaut `LeastAllocated`, qui pèse le CPU et la mémoire (poids égaux) et ignore les GPU : les petits pods vont vers les nœuds les moins chargés en CPU. La fragmentation est un phénomène de **placement**, que le quota ne voit pas.

**Remèdes.** (1) `NodeResourcesFit` en `MostAllocated` avec un poids sur `nvidia.com/gpu` : dans le lab, les quatre pods s'entassent sur un nœud et le pod suivant est lié ; inconvénient, la charge se concentre (nœud chaud, panne moins répartie). (2) Faire demander des nœuds entiers aux gros entraînements et réserver des nœuds par taint : simple, mais la capacité réservée peut rester inutilisée. (3) Le TAS de Kueue (`podset-unconstrained-topology` comble les trous) ou un ordonnanceur de groupe : plus complet, avec plus de pièces à maintenir.

**Kueue.** Il aurait **admis** le Workload (quota de 28 GPU disponibles, la demande de 8 y tient), puis le pod serait resté `Pending` : c'est l'écart entre « admis » et « placé » du chapitre 3. Surveillez la durée entre admission et pods prêts : c'est l'indicateur de ce défaut.
:::

::: exo
[Exercice 9 · ★★ — Un volume de checkpoints pour 70 milliards de paramètres]{.tag} Un entraînement de 70 milliards de paramètres écrit un checkpoint toutes les 20 minutes, à 14 octets par paramètre. Vous tolérez 5 % du temps en écriture. Quel débit agrégé faut-il ? Si seul le rang 0 écrit, à travers une carte réseau de 200 Gb/s, est-ce tenable ? Quelle taille de volume réserver pour garder 3 checkpoints plus celui en cours d'écriture ?
:::

::: sol
**Taille.** $14 \times 70 \cdot 10^9 = 980$ Go par checkpoint. **Débit.** Cinq pour cent de 1 200 s font 60 s : il faut $980 / 60 \approx 16{,}3$ Go/s agrégés.

**Rang 0 seul.** Une carte de 200 Gb/s offre au mieux 25 Go/s : $980 / 25 = 39{,}2$ s au minimum théorique, soit 3,3 % du temps, sans compter les protocoles de fichiers, le trafic NCCL qui partage la carte et le débit réel du stockage. Tenable en théorie, fragile en pratique : mieux vaut que **tous les rangs écrivent leur part**.

**Volume.** $4 \times 980 = 3\,920$ Go, soit environ $3{,}57$ Tio : il faut réserver **4 Tio** au minimum. Le volume de 2 Tio du JobSet du lab 12.2 convient pour 7 milliards de paramètres (98 Go par checkpoint), pas pour 70 milliards.
:::

::: exo
[Exercice 10 · ★★★ — Deux personnes pour exploiter : que conclure ?]{.tag} Dans le profil `enterprise-platform` du lab 12.3, l'équipe d'exploitation compte deux personnes sans expérience de Slurm. (a) Passez le poids de `ops_cost` à 5 : qui gagne ? (b) Ajoutez l'exigence `ops_cost >= 3` : qui gagne, de combien, et avec quelle stabilité sur 2 000 perturbations (graine 0) ? (c) Que concluez-vous, et quelle information demanderiez-vous avant de décider ?
:::

::: sol
Résultats obtenus avec `score.py` du lab 12.3.

(a) Poids de `ops_cost` à 5, sans exigence : hybride 79,5, Kubernetes 75,3, Slurm 73,5. L'hybride gagne encore : son score de simplicité (2 sur 5) est compensé par ses points forts ailleurs, et le point de bascule (11,55) est hors de l'échelle.

(b) Avec l'exigence `ops_cost >= 3`, l'hybride (score 2) est éliminé. Kubernetes (75,3) devance Slurm (73,5) de **1,9 point** (75,35 contre 73,49 avant arrondi) ; sur 2 000 perturbations, Kubernetes gagne dans 54 % des cas, Slurm dans 36 %, et l'hybride dans 10 % (quand une perturbation relève son score de simplicité à 3).

(c) Une marge de 1,9 point avec 54 % de stabilité est un **débat**, pas une décision. Avant de trancher, il faut connaître la part de services permanents, les compétences réelles des utilisateurs et un chiffre d'effort d'exploitation : un essai de deux semaines sur un échantillon réel de charges vaut mieux qu'un affinage de la grille.
:::

::: exo
[Exercice 11 · ★★★ — Concevoir un pool de 256 GPU pour trois équipes]{.tag} Concevez les ClusterQueue d'un pool de 256 GPU pour trois équipes. *Pretrain* a besoin de 128 GPU garantis pour de longs entraînements, accepte de prêter jusqu'à 64 GPU inactifs mais veut les reprendre aussitôt. *Finetune* a 96 GPU. *Eval* a 32 GPU, peut monter à 64, avec des jobs préemptibles. Écrivez quotas et politiques, validez-les avec le lab 12.1, et rejouez.

Scénario : eval soumet 64 GPU, finetune 96, puis pretrain 128 ; cinq minutes plus tard eval soumet aussi un petit job de 16 GPU, et finetune termine à la minute 60. Qui est préempté, et pourquoi eval ne reprend-il pas ses 64 GPU quand finetune termine ?
:::

::: sol
**Conception** (fichiers `exercises/ex11/` du lab 12.1, validés : `9/9 documents valid`). Pretrain : `nominalQuota: 128`, `lendingLimit: 64` (donc 64 réservés), `StrictFIFO` (les gros jobs ne se font pas doubler), `reclaimWithinCohort: Any` pour reprendre sans condition de priorité. Finetune : 96, `BestEffortFIFO`, `reclaimWithinCohort: LowerPriority`. Eval : 32 avec `borrowingLimit: 32`, aucune préemption à son profit (`Never`) : ses jobs sont `preemptible`.

**Rejeu** (sortie réelle) :

~~~text
-> ADMIT   eval-sweep [eval] borrowing
-> ADMIT   sft-70b [finetune] nominal
-> PREEMPT eval-sweep [eval] InCohort by pretrain-70b
-> ADMIT   pretrain-70b [pretrain] nominal
-> ADMIT   eval-small [eval] nominal
~~~

Au départ, eval emprunte 32 GPU. Pretrain arrive : son usage dans le pool serait $128 - 64 = 64$, avec 64 d'eval et 96 de finetune on dépasse la capacité (192), et sa demande tient dans son quota nominal : elle reprend les GPU prêtés en évinçant eval-sweep. À la fin de finetune, eval-sweep (64 GPU) ne revient pas : eval utilise déjà 16 GPU avec eval-small, et $16 + 64 = 80 > 32 + 32 = 64$, sa limite d'emprunt. Il faudrait terminer eval-small ou scinder le balayage en tâches de 32 GPU. Le modèle est une simulation, pas Kueue : à vérifier sur un vrai cluster.
:::

::: exo
[Exercice 12 · ★★ — Faut-il raccourcir la toleration d'une panne de nœud ?]{.tag} Un entraînement de 64 GPU subit 3 pannes de nœud par semaine. Avec les valeurs par défaut (détection à 50 s, toleration de 300 s), combien de GPU·h sont immobilisés avant éviction ? Avec une toleration de 30 s ? À partir de quel taux de fausses détections la toleration courte devient-elle perdante, sachant qu'un redémarrage coûte $R + \tau/2 = 1\,800$ s ?
:::

::: sol
**Par panne, par défaut.** $64 \times 350 / 3600 \approx 6{,}22$ GPU·h, soit **18,7 GPU·h** par semaine pour 3 pannes. **Avec 30 s** : $64 \times 80 / 3600 \approx 1{,}42$ GPU·h par panne, 4,3 par semaine. Le gain est de $64 \times 270 / 3600 = 4{,}8$ GPU·h par vraie panne.

**Coût d'une fausse détection.** Une éviction injustifiée (réseau instable pendant plus de 30 s) redémarre tout le groupe : $64 \times 1\,800 / 3600 = 32$ GPU·h.

**Point d'équilibre.** La toleration courte est perdante si le nombre de fausses détections par vraie panne dépasse $4{,}8 / 32 = 0{,}15$, soit environ une fausse alerte pour sept pannes réelles. Ce calcul est une borne : il suppose le collectif bloqué pendant toute la toleration, alors qu'une détection côté application (délai NCCL, surveillance de progression) peut échouer plus tôt, ce qui réduit le gain de la toleration courte.
:::

::: exo
[Exercice 13 · ★★★ — Changer de pilote GPU sans perdre deux jours]{.tag} Un cluster de 128 nœuds de 8 GPU héberge un entraînement de 64 nœuds (512 GPU) et des évaluations sur les 64 autres. Le changement de pilote prend 15 minutes par nœud. Un checkpoint de ce modèle prend 100 s et un redémarrage 300 s. Comparez trois plans en GPU·h perdus pour l'entraînement : (A) vider d'un coup les 64 nœuds du job, (B) mettre à jour d'abord les 64 nœuds libres, y basculer le job, puis mettre à jour les anciens nœuds, (C) mettre à jour en place par vagues de 8 nœuds. Recommandez.
:::

::: sol
**Plan A.** Le job s'arrête pendant tout le changement : checkpoint (100 s) + mise à jour (900 s) + redémarrage (300 s) = 1 300 s sur 512 GPU, soit $1\,300 \times 512 / 3600 \approx 184{,}9$ GPU·h.

**Plan B (rotation).** Les 64 nœuds libres sont mis à jour par vagues de 8 (8 vagues de 15 min, 2 h) sans toucher au job. Le job fait un checkpoint et redémarre sur les nœuds à jour : $(100 + 300) \times 512 / 3600 \approx 56{,}9$ GPU·h. Les anciens nœuds sont ensuite mis à jour en 2 h sans impact. Coût pour le job : une seule interruption.

**Plan C (en place par 8).** Chaque vague retire 8 nœuds au job, qui ne tourne pas à moins de 64 nœuds et doit donc s'arrêter, puis redémarrer : 8 vagues $\times$ 1 300 s $\times$ 512 GPU / 3600 $\approx$ 1 479 GPU·h, soit huit fois le plan A.

**Recommandation.** Plan B : environ 31 % du coût du plan A (56,9 contre 184,9 GPU·h), au prix de 64 nœuds de réserve libérés pendant environ 2 h (évaluations préemptées ou reportées) et de 4 h de calendrier. Il suppose que les 64 nœuds libres ont la même topologie que ceux du job (chapitre 5).
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux dire ce que garantit chaque moyen de partager un GPU.** Preuve : l'exercice 3 refait pour votre propre flotte, avec le décompte des GPU et ce que chaque stratégie interdit.
-   **Je peux écrire et valider des files et quotas Kueue.** Preuve : le lab 12.1, partie A, et l'exercice 11 sur un pool de votre taille, avec `validate_manifests.py` au vert.
-   **Je peux prédire une préemption avant de la lire.** Preuve : votre prédiction écrite de la trace de l'exemple 3.2, comparée à la sortie du modèle, et l'explication de chaque écart.
-   **Je peux lancer un entraînement multi-nœuds qui redémarre en bloc.** Preuve : le JobSet du lab 12.2 adapté à votre parc, la répétition locale au vert et, si un cluster est disponible, le journal de rang 0 après suppression d'un pod.
-   **Je peux diagnostiquer une fragmentation de GPU.** Preuve : le lab 12.4, partie B, rejoué avec vos propres tailles de pods, et l'exercice 8.
-   **Je peux chiffrer le coût d'une panne de nœud et d'une mise à jour de pilote.** Preuve : les exercices 12 et 13 refaits avec vos mesures de temps de redémarrage et de vidage.
-   **Je peux défendre un choix Slurm, Kubernetes ou hybride.** Preuve : la note de dix lignes du lab 12.3 avec une marge et une stabilité chiffrées.
-   **Je peux dire ce qui est stable, bêta ou alpha aujourd'hui.** Preuve : un tableau daté de l'état de DRA, du gang natif, du TAS de Kueue et de vos opérateurs, relu sur les pages officielles.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Kueue a admis un entraînement de 128 GPU mais il ne démarre pas. Que regardez-vous ?* Réponse-type : l'état du Workload ; les pods (`Pending` ?) et leurs événements (`Insufficient nvidia.com/gpu`, taints non tolérés) ; l'écart entre quota et capacité physique (nœuds drainés, GPU défectueux, autre charge) ; la fragmentation et le score de l'ordonnanceur ; une topologie `required` trop exigeante ; le gang ou `waitForPodsReady` qui évince et remet en file ; enfin le temps entre admission et pods prêts, à suivre comme indicateur.
2.  *Comment partager 256 GPU entre quatre équipes sans laisser de GPU inactifs ?* Réponse-type : une cohorte de ClusterQueue avec quotas nominaux, prêt et emprunt bornés ; des jobs préemptibles qui savent faire un checkpoint pour utiliser le quota prêté ; la récupération (`reclaimWithinCohort`) réglée par équipe ; un `ResourceQuota` comme filet ; la mesure hebdomadaire de l'allocation et de l'utilisation. Piège à citer : DRA ne permet pas la préemption par l'ordonnanceur.
3.  *Slurm ou Kubernetes pour 40 chercheurs et 200 GPU ?* Réponse-type : poser trois questions (compétences des utilisateurs, part de services permanents, équipe d'exploitation), puis une grille avec justifications, exigences éliminatoires et robustesse ; la marge dit s'il s'agit d'une décision ou d'un débat ; proposer un essai court sur des charges réelles et nommer le coût caché de l'option choisie.

## Lectures et références {#refs}

Toutes les pages ont été relues pour ce module le 24 octobre 2026, sauf mention contraire.

-   Kubernetes. [*Device Plugins*](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/) et [*Schedule GPUs*](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/) : ressources étendues, santé des périphériques, règles `limits` et `requests` (chapitre 2).
-   Kubernetes. [*Dynamic Resource Allocation*](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/) et [*Allocate Devices to Workloads with DRA*](https://kubernetes.io/docs/tasks/configure-pod-container/assign-resources/allocate-devices-dra/) : DRA stable et ses limites (chapitre 2).
-   Kubernetes. [*Gang Scheduling*](https://kubernetes.io/docs/concepts/scheduling-eviction/gang-scheduling/), [*Workload API*](https://kubernetes.io/docs/concepts/workloads/workload-api/) et [*Topology-Aware Workload Scheduling*](https://kubernetes.io/docs/concepts/workloads/workload-api/topology-aware-scheduling/) : ordonnancement de groupe natif et TAS (chapitres 3 et 5).
-   Kubernetes. [*Resource Bin Packing*](https://kubernetes.io/docs/concepts/scheduling-eviction/resource-bin-packing/) et [*Scheduler Configuration*](https://kubernetes.io/docs/reference/scheduling/config/) : stratégies de score `NodeResourcesFit` (chapitre 5).
-   NVIDIA. [*GPU Operator*](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/overview.html), pages [MIG](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-operator-mig.html), [*time-slicing*](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html) et [mises à jour de pilote](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-driver-upgrades.html) (chapitres 2 et 8). NVIDIA. [*MIG User Guide, profils pris en charge*](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/supported-mig-profiles.html) : tableau du H100 (chapitre 2).
-   NVIDIA. [*DRA Driver for NVIDIA GPUs*](https://dra-driver-nvidia-gpu.sigs.k8s.io/docs/) : le modèle DRA appliqué aux GPU (chapitre 2).
-   Kueue. [*Overview*](https://kueue.sigs.k8s.io/docs/overview/), [*Preemption*](https://kueue.sigs.k8s.io/docs/concepts/preemption/), [*ClusterQueue*](https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/), [*Topology-Aware Scheduling*](https://kueue.sigs.k8s.io/docs/concepts/topology_aware_scheduling/) et [*All-or-nothing with ready Pods*](https://kueue.sigs.k8s.io/docs/tasks/manage/setup_wait_for_pods_ready/) : le noyau du chapitre 3.
-   Volcano. [*PodGroup*](https://volcano.sh/docs/concepts/podgroup/) et [*Queue*](https://volcano.sh/docs/concepts/queue/) ; CNCF, [*page du projet Volcano*](https://www.cncf.io/projects/volcano/) (chapitre 3).
-   JobSet. [*Overview*](https://jobset.sigs.k8s.io/docs/overview/) et [*exemples de charges*](https://jobset.sigs.k8s.io/docs/tasks/workload_examples/) ; Kubeflow. [*Trainer*](https://trainer.kubeflow.org/en/latest/overview/index.html) et [*guide PyTorch*](https://trainer.kubeflow.org/en/latest/user-guides/pytorch.html) (chapitre 4).
-   Ray. [*Ray on Kubernetes*](https://docs.ray.io/en/latest/cluster/kubernetes/index.html) : KubeRay et ses trois ressources (chapitre 4). NVIDIA. [*Network Operator*](https://docs.nvidia.com/networking/display/COKAN10/Network+Operator) et [*GPUDirect RDMA*](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-operator-rdma.html) (chapitre 4).
-   SchedMD et NVIDIA. [*Slinky*](https://slinky.schedmd.com/docs/) et [*slurm-operator v1.2.0*](https://slinky.schedmd.com/slurm-operator/v1.2.0/) ; CoreWeave. [*About SUNK*](https://docs.coreweave.com/products/sunk) (chapitre 7).
-   Hu et al. [*Characterization of Large Language Model Development in the Datacenter*](https://arxiv.org/abs/2403.07648), 2024 : Seren sous Slurm, Kalos sous Kubernetes (chapitre 7). Kokolis et al. [*Revisiting Reliability in Large-Scale Machine Learning Research Clusters*](https://arxiv.org/abs/2410.21680), 2024 : clusters sous Slurm (chapitre 7).
-   CNCF. [*Certified Kubernetes AI Conformance Program*](https://www.cncf.io/announcements/2025/11/11/cncf-launches-certified-kubernetes-ai-conformance-program-to-standardize-ai-workloads-on-kubernetes/), 2025 : annonce du programme (chapitre 7).

## Sources et portée {#sources}

### Documenté {#documente}

Les faits attribués à une page officielle ont été relus à la source le 24 octobre 2026 : plugin de périphériques, DRA GA en v1.34 et verrouillé en v1.35 et ses limites, gang et API `Workload` en bêta en v1.37, intégration au Job et TAS natif en alpha depuis la v1.36 (toujours en v1.37), règles de `ResourceQuota`, tolérations par défaut de 300 s, politique de décalage de version, dates de fin de vie, profils MIG du H100, *time-slicing*, CDI, mises à jour de pilote, champs et règles de préemption de Kueue, ses intégrations et son TAS, l'interblocage et `waitForPodsReady`, PodGroup et Queue de Volcano, JobSet, Trainer v2, KubeRay, Slinky, SUNK, les études de Hu et al. et de Kokolis et al., le programme de conformité du CNCF. Versions : Kubernetes v1.37.1, GPU Operator 26.7.2, pilote DRA NVIDIA 0.5.1, Kueue v0.20.3, JobSet v0.13.0, Kubeflow Trainer v2.1.0, Slinky 1.2.0. **Observé** dans le bac à sable : les sorties des exemples 1.1, 3.4, 4.1 et 5.2, la liste des tolérances injectées du §5.5 et les sorties des exercices 1, 5 et 8 viennent de vraies exécutions (plan de contrôle v1.37.1 sans kubelet ; PyTorch CPU) ; les exemples 3.2, 3.3, 5.1 et 7.1 viennent des modèles et simulateurs des labs, décrits comme tels.

### Recommandé {#recommande}

Le découpage en trois atomicités, la correspondance Slurm / Kubernetes du chapitre 1, la réservation des nœuds GPU par taint, le montage « une ClusterQueue par équipe dans une cohorte plus un `ResourceQuota` large », le calcul du coût par heure active, la méthode de la grille de décision et tous ses scores, le plan de mise à jour par rotation, et les hypothèses chiffrées des exemples (6 s par pas, 40 % de MFU, 15 minutes par nœud, 20 Go d'image, débits de 2 à 10 Go/s, MTBF de 40 h, 14 octets par paramètre) sont des choix de ce parcours ou des valeurs d'exemple : remplacez-les par vos mesures.

### À vérifier {#a-verifier}

(1) Le modèle d'admission du lab 12.1 est une **simulation** d'après la documentation de Kueue v0.20 ; son comportement exact (ordre des têtes de file, sort d'une ressource non couverte par la file, étiquettes de raison de préemption hors `InClusterQueue`) n'a pas été comparé à un Kueue réel. (2) Les noms de portes (`GenericWorkload`, `WorkloadWithJob`, `TopologyAwareWorkloadScheduling`), les versions d'API et l'état bêta ou alpha de l'ordonnancement de groupe natif changent d'une version à l'autre : relisez la page de votre version. (3) Le pilote DRA de NVIDIA a des fonctions alpha. (4) La version de Kueue vient du fichier `CHANGELOG/CHANGELOG-0.20.md` de la branche principale, dont v0.20.3 est la dernière entrée, sans `CHANGELOG-0.21.md` (l'API GitHub des versions n'était pas joignable) ; Volcano affiche v1.16.0 comme dernière version de sa documentation, non testée ici. (5) Le délai de détection de 50 s de `kube-controller-manager` vient de l'aide du binaire v1.37.1, pas d'une page de documentation. (6) Les règles de sécurité des pods de RDMA (capacités, mémoire verrouillée) n'ont pas été testées. (7) Le contenu précis des exigences de la conformité IA du CNCF n'a pas été lu (le dépôt n'était pas accessible). (8) Le lab 12.2 n'a pas été exécuté sur un cluster GPU : comportement des pods, des volumes RWX, de NCCL et de Kueue non prouvé. (9) L'affirmation « 290 pods par seconde à 15 000 nœuds » est une mesure du projet JobSet, non reproduite. (10) Les binaires Kubernetes sont vérifiés contre un fichier `.sha256` publié au même endroit : la vérification détecte une corruption, pas une source compromise.

### Hors périmètre {#hors-perimetre}

L'installation d'un cluster avec kubelets et GPU réels, MultiKueue et les clusters multiples, l'autoscaling de nœuds (Karpenter, cluster-autoscaler), le service d'inférence (KServe, vLLM, LeaderWorkerSet), les accélérateurs non NVIDIA, les offres commerciales de gestion de flotte GPU, les maillages de services et le chiffrement des communications, et l'administration d'une base de comptabilité d'usage (voir le module 15).
