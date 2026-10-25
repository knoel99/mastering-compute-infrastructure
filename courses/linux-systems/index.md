---
title: "Linux, systèmes et diagnostic de performance"
subtitle: "Module 01 · Phase 0 · 24 h"
description: "Le socle commun à tout ce qui suit : processus, mémoire, cgroups, NUMA, systemd, réseau et stockage vus par un exploitant de cluster, avec la méthode USE et des compteurs noyau plutôt que des impressions."
module:
  id: linux-systems
  number: 1
  phase: 0
  hours: 24
  level: 1
prerequisites: []
status: skim
badges:
  - {label: "À survoler si Linux est acquis", class: skim}
  - {label: "Labs vérifiés dans le bac à sable (lab 1.4 : branche cgroup v1 seulement)", class: verified}
labs:
  - {id: machine-map, kind: sandbox}
  - {id: psi-triage, kind: sandbox}
  - {id: pagecache, kind: sandbox}
  - {id: cgroup-limits, kind: sandbox}
  - {id: ops-script, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** quand un job de calcul est lent, *qu'est-ce qui est lent*, et comment le prouver en cinq minutes avec des compteurs du noyau plutôt qu'avec une intuition ? Tout le reste du parcours (ordonnanceur, réseau, stockage, Kubernetes) repose sur quelques objets du système Linux : le processus, la mémoire virtuelle, le groupe de contrôle (*cgroup*), la topologie matérielle. Ce module les rend concrets.

Il ne cherche pas à faire de vous un administrateur système complet. Il vous donne un **vocabulaire exact** (« la mémoire est saturée » ne veut rien dire, « le noyau tue des processus de ce groupe de contrôle parce que sa limite est atteinte » est vérifiable), une **méthode de diagnostic** et cinq labs exécutés sur une vraie machine Linux.

::: key
[Règle de ce module]{.tag} Ne tirez jamais de conclusion d'un débit mesuré seul. Lisez ce que le noyau compte : octets réellement lus sur le périphérique, pages résidentes, temps pendant lequel des tâches attendent. Une machine virtuelle, un contrôleur de disque ou un agent de la plateforme peuvent cacher ou fausser un chronométrage ; ils ne faussent pas un compteur d'événements.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 24 h, dont environ 9 h de lecture, 8 h de labs et 7 h d'exercices, de synthèse et de checkpoint |
| Niveau d'entrée | 1 : à l'aise avec un terminal et capable de lire un script Python court |
| Prérequis | aucun |
| Pour qui | Fondation pour tous ; survol possible si vous administrez déjà des serveurs Linux en production. |
| Livrable | un rapport de triage reproductible de votre machine et un script d'exploitation idempotent avec tests |
| Environnement | une machine Linux sans GPU suffit. Lab 1.4 : accès root. Lab 1.2 : `stress-ng` et `fio`. Lab 1.3 : `fio` pour la partie B seulement. Lab 1.5 : `shellcheck` et `systemd-analyze`. Voir la page [environnement de travail](../../lab-setup/index.html) |
| Projets liés | [Projet 1 — Mini-cluster Slurm instrumenté](../../projects/homelab-slurm/index.html) |

### Ce que vous saurez vérifier {#acquis}

- Cartographier une machine (processeurs, nœuds NUMA, périphériques PCI, interfaces réseau, disques) et dire **quelle carte réseau est proche de quel GPU** (chapitre 3, lab 1.1).
- Expliquer ce que fait un cgroup d'une limite mémoire et d'un quota de processeur, et **provoquer et lire** une mise à mort par manque de mémoire (chapitre 2, lab 1.4).
- Mener un diagnostic de nœud lent avec la méthode USE, en distinguant processeur, mémoire et disque, et connaître l'angle mort de la pression PSI (chapitre 4, lab 1.2).
- Dire, pour une lecture ou une écriture de fichier, ce qui touche le cache de pages et ce qui touche le disque (chapitre 7, lab 1.3).
- Écrire un script d'exploitation **idempotent**, avec codes de retour et tests (chapitre 8, lab 1.5).
- Lire une unité systemd, des limites de ressources et un journal du noyau sans deviner (chapitres 5 et 8).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 0 — Fondations : machines et performance** (semaines 1-4) : lire une machine et prédire sa performance avant de la mesurer.
-   **S'appuie sur** : aucun module ; c'est un point d'entrée.
-   **Prépare** : [module 5 — Slurm et exploitation d'un cluster HPC](../slurm/index.html), [module 6 — Provisioning, images et santé des nœuds GPU](../provisioning/index.html), [module 7 — Réseaux haute performance : InfiniBand, RoCE et NCCL](../networking/index.html), [module 8 — Stockage et E/S pour l'entraînement](../storage/index.html), [module 12 — Kubernetes pour l'IA : GPU, files d'attente et gang scheduling](../kubernetes-gpu/index.html), [module 14 — Observabilité et fiabilité d'une flotte GPU](../observability/index.html).
-   **Projets qui s'en servent** : [Projet 1 — Mini-cluster Slurm instrumenté](../../projects/homelab-slurm/index.html).
-   **Compétences demandées dans les offres d'emploi et travaillées ici** : Python, Administration Linux, Astreinte, fiabilité (SRE), Réseau (général), Profilage, bancs d'essai, Conteneurs, Journaux, traces, Checkpoint, tolérance aux pannes, Planification de capacité, CI/CD, automatisation, Virtualisation (KVM, MIG, vGPU), Santé matérielle (burn-in, diagnostics, RMA) (voir [l'analyse du marché](../../market/index.html#couverture)).
<!-- /gen:place -->

### Plan de séances {#seances}

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 2.5 h | 1 | Chapitre 1 : processus, signaux, ordonnanceur, charge, mémoire virtuelle | exercice 1 |
| 2 | 3 h | 1 | Chapitre 1 (cache de pages, OOM) puis chapitre 2 : cgroups et espaces de noms | lab 1.4, exercice 3 |
| 3 | 2.5 h | 1 | Chapitre 3 : topologie matérielle et NUMA | lab 1.1, exercice 4 |
| 4 | 3 h | 1 | Chapitre 4 : mesurer avant d'optimiser, méthode USE, pression PSI | lab 1.2, exercices 2 et 5 |
| 5 | 2.5 h | 2 | Chapitre 5 : systemd, limites de ressources, pages énormes, paramètres noyau | exercice 9 |
| 6 | 2.5 h | 2 | Chapitre 6 : réseau Linux, MTU, premiers pas RDMA | exercice 10 |
| 7 | 3 h | 2 | Chapitre 7 : stockage, cache de pages, E/S directes, loi de Little | lab 1.3, exercice 6 |
| 8 | 2.5 h | 2 | Chapitre 8 : pannes matérielles vues du système, scripts d'exploitation robustes | lab 1.5 (qui inclut l'exercice 11) |
| 9 | 2.5 h | 3 | Synthèse : dimensionner, diagnostiquer un cas ouvert, bilan de sortie | exercices 7 et 8, checkpoint |

<!-- gen:travailler -->
### Comment travailler ce module {#travailler}

Le parcours s'adresse à plusieurs profils d'entrée, décrits dans le [point de départ](../../profile/index.html). Le tableau donne la priorité conseillée pour ce module ; les questions de positionnement (section 0.1) la confirment ou la corrigent.

| Profil d'entrée | Priorité | Ce que cela veut dire ici |
|---|---|---|
| Ingénieur plateforme, SRE ou DevOps | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Administrateur ou ingénieur HPC | survol guidé | les questions de positionnement, les chapitres signalés ci-dessous, un lab et le checkpoint |
| Ingénieur ML ou chercheur | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Développeur logiciel ou systèmes | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Étudiant ou personne en reconversion | à fond | tous les chapitres, tous les labs et les exercices ★★★ |

**À ne pas survoler.** Même en survol, lisez les chapitres sur les cgroups, la topologie (NUMA, PCIe) et la méthode de mesure : tout le parcours s'appuie dessus.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le bilan de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Trois questions pour situer votre niveau. Répondez sans chercher, puis ouvrez les réponses.

1.  Un programme demande 512 Mio de mémoire et le noyau l'accorde, mais `VmRSS` n'indique que 10 Mio. Où est passé le reste ?
2.  Un nœud de 32 cœurs affiche une charge moyenne de 40. Pouvez-vous conclure que le processeur est saturé ?
3.  Un entraînement doit écrire un checkpoint quand on le préempte. Pourquoi `kill -TERM` peut-il fonctionner et `kill -KILL` jamais ?

::: sol
**Réponses.**

1.  Rien n'a disparu : la mémoire est **virtuelle**. Le noyau réserve des adresses et ne fournit une page physique qu'au premier accès (chapitre 1, exemple 1.3). `VmSize` compte ce qui est réservé, `VmRSS` ce qui est réellement en mémoire.

2.  Non. La charge moyenne compte les tâches exécutables **et** celles en attente d'un disque (état D). Une charge de 40 peut venir d'un disque saturé. Utilisez la pression PSI du chapitre 4 pour le savoir.

3.  `SIGTERM` peut être intercepté par le programme, qui sauvegarde puis s'arrête. `SIGKILL` ne peut être ni intercepté, ni bloqué, ni ignoré : le noyau détruit le processus sans lui laisser la main (statut de sortie 137). C'est le signal de l'arrêt par manque de mémoire.
:::

## 1. Modèle d'exécution Linux {#ch1}

Ce chapitre fixe quatre idées que tout le module réutilise : un processus a un état et reçoit des signaux, l'ordonnanceur répartit les cœurs, la mémoire est virtuelle et allouée à la demande, et le cache de pages place les fichiers en mémoire.

### 1.1. Processus, états et signaux

Un *processus* est un programme en cours d'exécution, avec son espace d'adresses, ses descripteurs de fichiers et un identifiant (PID). À chaque instant, il est dans un état : `R` (exécutable), `S` (en sommeil, réveillable par un signal), `D` (sommeil ininterruptible, typiquement en attente d'une entrée-sortie), `T` (arrêté) ou `Z` (zombie : terminé, mais pas encore récolté par son parent).

Les *signaux* sont les messages que le noyau ou un autre processus envoie. `SIGTERM` (15) demande l'arrêt et peut être intercepté. `SIGKILL` (9) et `SIGSTOP` ne le peuvent pas : la page [signal(7)](https://man7.org/linux/man-pages/man7/signal.7.html) le dit en une phrase, « The signals SIGKILL and SIGSTOP cannot be caught, blocked, or ignored ». Un processus tué par un signal est rapporté par le shell avec le statut 128 plus le numéro du signal (convention des shells : le parent lit dans le statut d'attente que le fils est mort d'un signal et affiche 128 + n).

::: ex
[Exemple 1.1 — Les états d'un processus au fil des signaux]{.tag} Capturé dans le bac à sable (Linux 6.18). On lance `sleep 300`, puis on l'arrête, on le reprend, on le termine :

~~~text
  PID STAT WCHAN          CMD
20120 S    hrtimer_nanosl sleep 300      # en sommeil, attend un minuteur
20120 T    sleep 300                     # après kill -STOP
20120 S    sleep 300                     # après kill -CONT
exit status after SIGTERM: 143           # 128 + 15
~~~

La colonne `WCHAN` indique où le noyau attend : ici un minuteur à haute résolution. Sur un nœud lent, un processus bloqué en état `D` avec un `WCHAN` lié à un système de fichiers ou à un pilote est le premier indice d'une panne de stockage.
:::

Un *zombie* est un processus fini dont le parent n'a pas encore lu le statut de sortie. Il ne consomme presque rien, mais occupe une entrée de la table des processus tant qu'il n'est pas récolté. Un lanceur qui oublie d'attendre ses enfants en accumule.

~~~text
PID  PPID STAT CMD
20128 20127 Z    [python3] <defunct>      # fils terminé, parent n'a pas appelé wait
after waitpid: gone                       # une fois récolté, il disparaît
~~~

Le lien avec les entraînements est direct. Un job qui doit sauvegarder à la préemption intercepte `SIGTERM` (ou un signal choisi sous Slurm, voir le lab 5.1 du [module Slurm](../slurm/index.html)). Il n'a aucune chance face à `SIGKILL`, statut 137, qui est justement ce qu'envoie le noyau quand la mémoire manque (chapitre 2).

### 1.2. L'ordonnanceur et la charge moyenne

L'ordonnanceur du noyau décide quelle tâche exécutable occupe quel cœur. La documentation du noyau décrit le passage à l'algorithme EEVDF à partir de la version 6.6 ([sched-eevdf](https://docs.kernel.org/scheduler/sched-eevdf.html)) ; pour un exploitant, ce qui compte est qu'il partage équitablement les cœurs entre les tâches exécutables, pas qu'il prévoie leurs besoins.

La **charge moyenne** (*load average*) est ce que montrent `uptime` et `/proc/loadavg`. Selon [proc_loadavg(5)](https://man7.org/linux/man-pages/man5/proc_loadavg.5.html), ce sont « the number of jobs in the run queue (state R) or waiting for disk I/O (state D) », moyennés sur 1, 5 et 15 minutes. C'est donc une moyenne exponentielle du nombre de tâches qui veulent le processeur ou attendent un disque, pas un pourcentage.

Avec $n$ tâches constamment exécutables, une constante de temps $\tau$ de 60 secondes pour la moyenne à une minute et une mise à jour environ toutes les $\Delta$ = 5 secondes, la valeur suit :

$$L_{k+1} = L_k\, e^{-\Delta/\tau} + n\,\bigl(1 - e^{-\Delta/\tau}\bigr)$$

::: ex
[Exemple 1.2 — Huit tâches sur quatre cœurs]{.tag} On lance huit boucles actives (`stress-ng --cpu 8`) sur une machine de quatre cœurs et on lit `/proc/loadavg` après environ 62 secondes. La récurrence ci-dessus donne 5,06 après 60 s et 5,29 après 65 s (calcul Python). Capturé :

~~~text
5.58 1.82 0.88 9/119 20326       # charge à 1, 5 et 15 minutes
~~~

La valeur lue, 5,58, est un peu supérieure à la prédiction : la charge de départ n'était pas nulle et d'autres tâches du système étaient exécutables en même temps, deux choses que le modèle ignore (on suppose $L_0 = 0$). L'ordre de grandeur est le bon, et la leçon aussi : **la charge ne dit pas combien de cœurs sont saturés**, seulement combien de tâches sont en file. Le chapitre 4 la remplace par une mesure directe de l'attente.
:::

### 1.3. Mémoire virtuelle et allocation à la demande

Chaque processus voit un espace d'adresses virtuel que le noyau relie à des pages physiques de 4 Kio (`getconf PAGESIZE` renvoie 4096 sur la machine de test). Il ne fournit une page physique qu'au **premier accès** : c'est l'allocation à la demande. `VmSize` mesure ce qui est réservé, `VmRSS` ce qui est réellement présent en mémoire (*resident set size*).

::: ex
[Exemple 1.3 — Réserver n'est pas toucher]{.tag} Un programme Python réserve 512 Mio de mémoire anonyme, puis écrit un octet par page sur 128 Mio. Capturé, en Mio :

~~~text
start             {'VmSize': 15,  'VmRSS': 9}
mmap 512 MiB      {'VmSize': 527, 'VmRSS': 10}
touched 128 MiB   {'VmSize': 527, 'VmRSS': 138}
~~~

La réservation augmente `VmSize` de 512 Mio et `VmRSS` d'un seul Mio. Toucher 128 Mio, soit 32 768 pages de 4 Kio, augmente `VmRSS` de 128 Mio exactement (138 moins 10). Un programme qui « consomme 500 Go » selon `VmSize` peut très bien n'en occuper que 2.
:::

Le noyau accepte souvent de réserver plus que la mémoire disponible : le paramètre `vm.overcommit_memory` vaut 0 sur la machine de test, valeur par défaut qui active une heuristique ([documentation sysctl vm](https://docs.kernel.org/admin-guide/sysctl/vm.html)). La conséquence est que l'échec arrive plus tard, au moment de toucher les pages, sous la forme d'une mise à mort par le noyau et non d'un refus d'allocation.

### 1.4. Cache de pages et mise à mort par manque de mémoire

Le noyau garde en mémoire les pages des fichiers qu'il a lus ou écrits : c'est le **cache de pages**, que `/proc/meminfo` compte dans `Cached`. Une écriture reçue par `write()` ne va pas tout de suite sur le disque : les pages sont « sales » (*dirty*) jusqu'à ce que le noyau les écrive, ou que le programme appelle `fsync()`. Le chapitre 7 et le lab 1.3 mesurent ces états.

Quand la mémoire ne peut plus être libérée, le noyau choisit un processus et le tue avec `SIGKILL` : c'est l'*OOM killer* (*out of memory*). Le paramètre `oom_score_adj` de chaque processus, entre −1000 et 1000 selon [proc_pid_oom_score_adj(5)](https://man7.org/linux/man-pages/man5/proc_pid_oom_score_adj.5.html), pèse dans le choix. Les cgroups, objet du chapitre suivant, permettent de déclencher cette mise à mort **dans un groupe seulement**, sans toucher le reste de la machine.

::: recap
[Points clés]{.tag}

-   Un processus a un état (`R`, `S`, `D`, `T`, `Z`) ; `SIGKILL` et `SIGSTOP` ne s'interceptent pas ; un signal tue avec le statut 128 plus son numéro.
-   La charge moyenne compte les tâches exécutables **et** celles en attente de disque : ce n'est pas un taux d'occupation des cœurs.
-   `VmSize` est réservé, `VmRSS` est présent ; la page physique n'arrive qu'au premier accès.
-   Le cache de pages garde les fichiers en mémoire ; une écriture est « sale » jusqu'à son écriture sur disque ou son `fsync`.
-   Sans mémoire libérable, le noyau envoie `SIGKILL` à un processus choisi par score.
:::

## 2. cgroups et espaces de noms {#ch2}

Un conteneur n'est pas une machine virtuelle : c'est un processus ordinaire dont le noyau limite les ressources (cgroups) et restreint la vue du système (espaces de noms). Comprendre ces deux mécanismes explique ce que font Slurm et Kubernetes quand ils « allouent » des ressources.

### 2.1. Ce qu'est un cgroup, v1 et v2

Un *cgroup* (groupe de contrôle) est un ensemble de processus organisé en arbre, auquel des **contrôleurs** appliquent des limites ou de la comptabilité : `cpu`, `memory`, `io`, `pids`, `cpuset`. Le noyau en a connu deux générations. En v1, chaque contrôleur a sa propre hiérarchie. En v2, « all mounted controllers reside in a single unified hierarchy » ([cgroups(7)](https://man7.org/linux/man-pages/man7/cgroups.7.html)).

Les deux peuvent coexister, c'est le mode **hybride**, avec une contrainte : un contrôleur ne peut pas être utilisé simultanément dans une hiérarchie v1 et dans la hiérarchie v2. Le bac à sable de ce cours est dans ce cas, et c'est une bonne occasion d'apprendre à le détecter.

::: ex
[Exemple 2.1 — Quelle version de cgroup tourne ici ?]{.tag} Capturé dans le bac à sable :

~~~text
$ stat -fc %T /sys/fs/cgroup
tmpfs                                   # v1 ou hybride (en v2 pur : cgroup2fs)
$ mount | grep cgroup2
cgroup2 on /sys/fs/cgroup/unified type cgroup2 (rw,relatime)
$ cat /sys/fs/cgroup/unified/cgroup.controllers
hugetlb                                 # un seul contrôleur côté v2
~~~

Les contrôleurs `cpu`, `memory`, `blkio` et d'autres sont montés en v1, donc indisponibles en v2. **Conséquence pour le cours** : le lab 1.4 détecte la version et exécute la branche v1 ici ; la branche v2, qui suit la documentation du noyau, n'a pas pu être exécutée dans le bac à sable et est signalée comme telle. Sur une distribution récente en v2 pur, c'est l'inverse.
:::

### 2.2. Limiter la mémoire

En v2, `memory.max` est « the main mechanism to limit memory usage » : au-delà, et si la mémoire ne peut pas être récupérée, « the OOM killer is invoked in » le cgroup ([documentation cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)). `memory.high` est une limite douce : la documentation précise que dépasser `high` n'invoque jamais le tueur, le groupe est seulement ralenti pour récupérer de la mémoire. Le compteur `oom_kill` de `memory.events` totalise les mises à mort. En v1, l'équivalent est `memory.limit_in_bytes` et le compteur `oom_kill` de `memory.oom_control`.

::: ex
[Exemple 2.2 — Une mise à mort par manque de mémoire, lue de bout en bout]{.tag} Le lab 1.4 place un programme dans un cgroup limité à 100 Mio, puis lui fait allouer 300 Mio par blocs de 10 Mio. Capturé (cgroup v1) :

~~~text
allocated 90 MiB                           # dernier message affiché
exit status: 137, oom_kill counter: 1      # tué par SIGKILL
Memory cgroup out of memory: Killed process 28868 (python3) total-vm:116780kB, anon-rss:102016kB, file-rss:5836kB
~~~

Lecture : la limite est de 102 400 kB ; la mémoire anonyme au moment de la mise à mort est de 102 016 kB, soit 99,6 % de la limite. Les 90 Mio de blocs terminés valent 92 160 kB ; il reste 9 856 kB (environ 9,6 Mio).

Ils se partagent entre l'interpréteur (un Python 3.13 au repos a environ 2 880 kB, soit 2,8 Mio, de mémoire anonyme, `RssAnon` lu dans `/proc/self/status`) et la partie du dixième bloc déjà touchée quand le noyau a tué, soit environ 6 976 kB (6,8 Mio) par différence. Le dixième bloc n'a jamais fini d'être touché : « allocated 100 MiB » ne s'est jamais affiché.
:::

C'est la raison pour laquelle un job limité à 100 Go **meurt** au lieu d'être ralenti quand il dépasse : la limite mémoire est dure. Sous Slurm, cette limite est la mémoire demandée quand `ConstrainRAMSpace=yes` (section 2.6). Sous Kubernetes, c'est la limite (`limits.memory`) ; la requête sert surtout au placement ([Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)). Pour un entraînement, prévoir de la marge dans la limite et un `memory.high` en dessous de `memory.max` transforme une mise à mort en ralentissement visible.

### 2.3. Limiter le processeur

Une limite de processeur est un **quota par période** : en v2, `cpu.max` est de la forme `$MAX $PERIOD`, avec la valeur par défaut `max 100000` (aucune limite sur une période de 100 000 µs). `20000 100000` accorde 20 000 µs de processeur par période de 100 000 µs, soit 20 % d'un cœur. En v1, ce sont `cpu.cfs_quota_us` et `cpu.cfs_period_us`.

Un quota n'est pas une priorité : il plafonne même si la machine est vide. Pour répartir sans plafonner, on utilise des poids (`cpu.weight` en v2), qui n'agissent qu'en cas de concurrence.

::: ex
[Exemple 2.3 — Un quota de 20 % mesuré]{.tag} Le lab 1.4 lance une boucle active pendant 4 secondes dans un groupe limité à 20 % d'un cœur et mesure le temps processeur obtenu sur le temps écoulé. Capturé : `share of one CPU obtained: 0.197` (0,199 et 0,200 sur deux autres exécutions). C'est 98,5 % du quota (0,197 sur 0,20) ; le test accepte entre 0,10 et 0,35 pour tolérer le bruit d'une machine partagée.
:::

### 2.4. La règle des processus internes (v2)

En v2, un cgroup qui délègue des contrôleurs à ses enfants ne peut en principe pas contenir de processus lui-même : c'est la contrainte « no internal process ». La documentation précise que le cgroup racine en est exempté. C'est pourquoi un gestionnaire de services comme systemd place chaque service dans une feuille de l'arbre, et pourquoi un conteneur est une feuille sous un cgroup de pod.

### 2.5. Espaces de noms

Un *espace de noms* (*namespace*) donne à un processus une vue restreinte d'une ressource globale. [namespaces(7)](https://man7.org/linux/man-pages/man7/namespaces.7.html) en liste huit types : `cgroup`, `ipc`, `network`, `mount`, `pid`, `time`, `user` et `uts` (nom de machine). Un conteneur est un ensemble de processus placés dans plusieurs de ces espaces, dans des cgroups, avec un système de fichiers racine propre.

::: ex
[Exemple 2.4 — Le processus qui se croit seul]{.tag} Avec `unshare` (root), on lance `ps` dans un nouvel espace de noms de processus. Capturé :

~~~text
$ unshare --pid --fork --mount-proc ps -e -o pid,cmd
    PID CMD
      1 ps -e -o pid,cmd
~~~

Dans son espace de noms, `ps` est le PID 1 et ne voit aucun autre processus de la machine : c'est ce que voit un conteneur. Aucune ressource n'est limitée pour autant : l'isolation de **vue** (espaces de noms) et la limitation de **consommation** (cgroups) sont deux mécanismes distincts.
:::

### 2.6. Ce que Slurm et Kubernetes en font

Slurm applique ses limites de ressources aux jobs avec des cgroups. Le fichier `cgroup.conf` choisit le mécanisme avec `CgroupPlugin=<cgroup/v1|cgroup/v2|autodetect|disabled>`, et les options `ConstrainCores`, `ConstrainRAMSpace` et `ConstrainDevices` activent la restriction des cœurs, de la mémoire et des périphériques ([cgroup.conf](https://slurm.schedmd.com/cgroup.conf.html)). C'est la raison pour laquelle un job Slurm qui dépasse sa mémoire demandée est tué, comme à l'exemple 2.2.

Kubernetes traduit de même les requêtes et les limites d'un conteneur en réglages de cgroup, et documente le support de cgroup v2 sur sa page [À propos de cgroup v2](https://kubernetes.io/docs/concepts/architecture/cgroups/), qui précise aussi les versions de noyau requises. Retenez le principe commun : **un ordonnanceur de cluster est un générateur de cgroups**.

::: recap
[Points clés]{.tag}

-   Un cgroup regroupe des processus et applique des contrôleurs ; v1 a une hiérarchie par contrôleur, v2 une seule, et un contrôleur ne sert pas à la fois en v1 et en v2.
-   `stat -fc %T /sys/fs/cgroup` détecte la version : `cgroup2fs` en v2 pur, `tmpfs` en v1 ou hybride.
-   La limite mémoire est **dure** : dépassée, un processus du groupe est tué (statut 137, compteur `oom_kill`) ; `memory.high` ralentit sans tuer.
-   Un quota de processeur plafonne même sur machine vide ; un poids ne joue qu'en cas de concurrence.
-   Les espaces de noms isolent la **vue**, les cgroups limitent la **consommation** ; un conteneur combine les deux.
:::

## 3. Topologie matérielle et NUMA {#ch3}

Un serveur d'entraînement n'est pas une boîte homogène : plusieurs processeurs, chacun avec sa mémoire, des GPU et des cartes réseau rattachés à l'un ou à l'autre. Savoir **qui est proche de qui** décide si les données prennent le chemin court ou traversent la machine.

### 3.1. Lire les processeurs

`lscpu` résume ce que le noyau connaît : modèle, nombre de processeurs logiques, de sockets, de cœurs par socket, de fils par cœur, tailles de caches. Le produit sockets × cœurs par socket × fils par cœur doit égaler le nombre de processeurs logiques ; si ce n'est pas le cas, l'un des champs est faux ou une partie des processeurs est hors ligne.

::: ex
[Exemple 3.1 — Un serveur virtuel lu avec `lscpu`]{.tag} Extrait capturé dans le bac à sable :

~~~text
CPU(s):                  4
Thread(s) per core:      1
Core(s) per socket:      4
Socket(s):               1
Hypervisor vendor:       KVM
Virtualization type:     full
L1d cache:               128 KiB (4 instances)
L2 cache:                4 MiB (4 instances)
L3 cache:                33 MiB (1 instance)
NUMA node(s):            1
~~~

Le produit 1 × 4 × 1 donne bien 4. Les lignes `Hypervisor vendor` et `Virtualization type` disent que ces « cœurs » sont des fils d'un hôte : les mesures de performance faites ici ne se transposent pas telles quelles à une machine physique. Le cache L3 de 33 Mio est partagé, d'où `1 instance`.
:::

### 3.2. NUMA : la mémoire a une adresse

Sur une machine à plusieurs sockets, chaque processeur est relié à sa propre mémoire. L'accès à la mémoire d'un autre socket est possible mais passe par une liaison entre processeurs : c'est l'*accès mémoire non uniforme* (NUMA). Le noyau expose les **nœuds NUMA** et une politique d'allocation par défaut, décrite dans la [documentation des politiques mémoire NUMA](https://docs.kernel.org/admin-guide/mm/numa_memory_policy.html) : par défaut, une page est allouée sur le nœud de la tâche qui la touche en premier.

::: ex
[Exemple 3.2 — Deux sources, deux totaux de mémoire]{.tag} Sur la machine de test (un seul nœud), `numactl -H` et `/proc/meminfo` ne s'accordent pas. Capturé :

~~~text
$ numactl -H
available: 1 nodes (0)
node 0 cpus: 0 1 2 3
node 0 size: 7901 MB
node 0 free: 7391 MB
$ head -1 /proc/meminfo
MemTotal:       16477348 kB          # soit 16 091 Mio
~~~

`numactl` annonce 7 901 « MB » pour l'unique nœud, qui sont des Mio (comparez avec le `MemTotal` en kB de `/sys/devices/system/node/node0/meminfo`, divisé par 1 024), et `MemTotal` en annonce 16 091 : le nœud ne couvre que 49 % de la mémoire de la machine virtuelle (la taille du nœud varie dans ce bac à sable : une relecture, plus tard, a donné 7 773 Mio).

Sur une machine virtuelle, **ne supposez pas** que la somme des nœuds égale la mémoire totale. Sur une machine physique, un écart est un signal à expliquer (mémoire non attachée à un nœud, dispositif de mémoire particulier) avant de dimensionner quoi que ce soit.
:::

### 3.3. Qui est branché où : GPU, carte réseau, disque NVMe

Chaque périphérique PCI déclare dans `/sys/bus/pci/devices/<adresse>/numa_node` le nœud auquel il est rattaché, avec `-1` pour « aucune affinité déclarée ». Croiser cette information avec la classe du périphérique (3D controller pour un GPU, InfiniBand, NVMe ; le code de classe est lu dans `/sys/bus/pci/devices/<adresse>/class`) donne une **table de localité** : pour chaque nœud, les GPU, les cartes réseau et les disques qui y sont directement branchés. Le lab 1.1 la construit.

Il classe une carte d'après ce code : une carte RDMA configurée en Ethernet (RoCE) peut y apparaître comme `ethernet` plutôt qu'`infiniband` ; ce point n'a pas été vérifié (voir « À vérifier »).

::: ex
[Exemple 3.3 — Quelle carte réseau pour quel GPU ?]{.tag} Le lab 1.1 est exécuté sur un serveur à deux sockets et quatre GPU **fabriqué à la main** (ce n'est pas la capture d'une machine réelle : il sert à tester la logique). La section `locality` du rapport JSON, remise en forme à la main, donne :

~~~text
nœud  0 : GPU 0000:18:00.0, 0000:3b:00.0   InfiniBand 0000:5e:00.0   NVMe 0000:5f:00.0
nœud  1 : GPU 0000:86:00.0, 0000:af:00.0   InfiniBand 0000:c1:00.0   NVMe 0000:c2:00.0
nœud -1 : Ethernet 0000:00:1f.6                                       # aucune affinité déclarée
~~~

Un processus qui pilote le GPU `0000:86:00.0` doit être épinglé sur les cœurs du nœud 1 et utiliser la carte `0000:c1:00.0`. S'il utilise celle du nœud 0, chaque transfert réseau traverse la liaison entre sockets. Le rapport garde le nœud `-1` visible plutôt que de l'omettre : une information manquante est un fait, pas un détail.
:::

La bibliothèque *hwloc* (*Portable Hardware Locality*) donne la même information sous forme d'arbre, des cœurs aux périphériques : son [site](https://www.open-mpi.org/projects/hwloc/) indique qu'elle « can detect the locality PCI devices ». `lstopo-no-graphics --of console` en affiche un résumé texte. Extrait capturé dans le bac à sable le 2026-10-25 (hwloc 2.10.0) :

~~~text
Machine (6110MB total)
  Package L#0
    NUMANode L#0 (P#0 6110MB)
    L3 L#0 (33MB)
      L2 L#0 (1024KB) + L1d L#0 (32KB) + L1i L#0 (32KB) + Core L#0 + PU L#0 (P#0)
  HostBridge
    PCI 00:02.0 (Storage)
      Block "vda"
    PCI 00:08.0 (Ethernet)
      Net "eth0"
~~~

(les trois autres cœurs et cinq autres disques virtio sont omis.) Les caches confirment `lscpu` : 1 Mio de L2 par cœur, soit les 4 Mio des quatre instances. Le total de la machine est celui du nœud NUMA, comme chez `numactl`, et non `MemTotal` : l'écart de l'exemple 3.2 se retrouve ici. Un pont PCI (`HostBridge`) y est rattaché « below a normal object (usually the entire machine or a NUMA node) » ([hwloc, I/O Devices](https://www.open-mpi.org/projects/hwloc/doc/v2.10.0/a00339.php)) : sur un serveur à plusieurs sockets, l'arbre recoupe donc la table de localité du lab 1.1.

Sur une machine réelle à GPU, recoupez toujours ce rapport avec la matrice que produit `nvidia-smi topo -m`, qui décrit aussi les liens entre GPU (NVLink ou PCIe). Aucun GPU n'est disponible dans le bac à sable : ce recoupement n'a pas pu être fait ici.

### 3.4. Épingler un processus

`taskset` restreint les cœurs autorisés d'un processus ; `numactl --cpunodebind=N --membind=N` restreint aussi l'allocation mémoire au nœud N. Slurm fait la même chose avec le contrôleur `cpuset` quand `ConstrainCores=yes` (section 2.6). Kubernetes le fait avec la politique `static` de son gestionnaire de processeurs (*CPU Manager*), qui réserve des cœurs exclusifs aux conteneurs des pods *Guaranteed* demandant un nombre entier de processeurs ([CPU Management Policies](https://kubernetes.io/docs/tasks/administer-cluster/cpu-management-policies/)).

::: ex
[Exemple 3.4 — Affinité de processeur]{.tag} Capturé :

~~~text
$ python3 -c "import os; print(sorted(os.sched_getaffinity(0)))"
[0, 1, 2, 3]
$ taskset -c 0 python3 -c "import os; print(sorted(os.sched_getaffinity(0)))"
[0]
~~~

Sous `taskset -c 0`, le programme ne peut s'exécuter que sur le cœur 0, même s'il crée des fils. Épingler sans comprendre la topologie est la manière classique de **ralentir** un job : cinq fils épinglés sur un cœur se partagent ce cœur.
:::

::: recap
[Points clés]{.tag}

-   Sockets × cœurs × fils doit égaler les processeurs logiques ; une machine virtuelle le dit dans `lscpu`.
-   La mémoire est attachée à un nœud NUMA ; par défaut, la page est allouée sur le nœud de la tâche qui la touche en premier.
-   `numactl -H` et `/proc/meminfo` peuvent diverger, surtout en machine virtuelle : expliquez l'écart avant de dimensionner.
-   `numa_node` de chaque périphérique PCI relie GPU, carte réseau et NVMe aux nœuds ; `-1` signifie « aucune affinité déclarée ».
-   Épingler suppose de connaître la topologie ; `taskset` ne protège pas d'une mauvaise répartition.
:::

## 4. Mesurer avant d'optimiser {#ch4}

Optimiser sans mesurer, c'est choisir au hasard parmi quatre ressources. Ce chapitre donne une méthode qui épuise les ressources dans un ordre fixe et un compteur du noyau qui mesure l'attente directement.

### 4.1. La méthode USE

Brendan Gregg a formulé la méthode USE en une règle : « For every resource, check utilization, saturation, and errors » ([The USE Method](https://www.brendangregg.com/usemethod.html)). L'*utilisation* est la part du temps où la ressource est occupée. La *saturation* est le travail qui attend parce qu'elle est occupée. Les *erreurs* sont les événements d'échec. L'auteur affirme que la méthode « solves about 80% of server issues with 5% of the effort », une affirmation d'expérience, pas une mesure.

| Ressource | Utilisation | Saturation | Erreurs |
|---|---|---|---|
| Processeur | part du temps occupé (`/proc/stat`) | attente de cœur : pression PSI `cpu` | erreurs machine (journal du noyau) |
| Mémoire | mémoire non disponible (`MemAvailable`) | pression PSI `memory`, activité de swap | mises à mort par OOM, compteurs ECC |
| Disque | part du temps occupé (`io_ticks`) | taille moyenne de file, pression PSI `io` | erreurs d'E/S, attributs SMART |
| Réseau | débit sur capacité du lien | pertes en file, dépassements | erreurs de trame (`ethtool -S`) |

La discipline de la méthode est de **remplir la table** avant d'avancer : une case vide est une hypothèse non testée, pas une absence de problème.

### 4.2. La pression PSI

Le noyau mesure directement l'attente avec les *pressure stall information*. `/proc/pressure/cpu`, `memory` et `io` contiennent une ligne `some` et une ligne `full` (pour le processeur au niveau système, `full` n'a pas de sens et est laissée à zéro depuis le noyau 5.13, selon la documentation). La [documentation PSI](https://docs.kernel.org/accounting/psi.html) définit `some` ainsi : « the share of time in which at least some tasks are stalled on a given resource ». Le champ `total` est un cumul en microsecondes ; la différence de deux lectures divisée par le temps écoulé donne la **fraction du temps** passée à attendre.

::: ex
[Exemple 4.1 — Lire un compteur cumulatif]{.tag} Lecture capturée sur la machine de test :

~~~text
cpu:    some avg10=0.01 avg60=0.02 avg300=0.04 total=11715677
memory: some avg10=0.00 avg60=0.00 avg300=0.00 total=0
io:     some avg10=0.08 avg60=0.12 avg300=0.07 total=83469838
~~~

`total=83469838` pour `io` signifie environ 83,5 secondes de blocage cumulées depuis le démarrage, pas une valeur instantanée. Pour savoir ce qui se passe **maintenant**, lisez le compteur deux fois à quelques secondes d'écart et divisez la différence par la durée : c'est ce que fait `triage.py` du lab 1.2.
:::

### 4.3. Les outils standard

`vmstat` donne en quelques colonnes l'état global : `r` tâches exécutables, `b` tâches bloquées (état D), `us`, `sy`, `id`, `wa`, `st` et `gu` pour le temps utilisateur, système, inactif, d'attente disque, volé par l'hôte et passé dans des invités. `iostat -x` détaille chaque disque (taille de file, occupation) et `pidstat` chaque processus. `strace -c` compte les appels système d'un programme.

::: ex
[Exemple 4.2 — `vmstat` sur une machine au repos, `strace -c` sur une lecture de fichier]{.tag} Capturés :

~~~text
procs -----------memory---------- ---swap-- -----io---- -system-- -------cpu-------
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st gu
 0  0      0 15953544   4680 197732    0    0     0     4  211  162  0  0 100  0  0  0

% time     seconds  usecs/call     calls    errors syscall
 25.54    0.001116          13        82        28 newfstatat
 16.93    0.000740          11        66           rt_sigaction
 14.99    0.000655          18        35         7 openat
~~~

La première ligne de `vmstat` (non reproduite) est une moyenne depuis le démarrage : ignorez-la. Ici `id` vaut 100 : rien ne travaille. Dans `strace -c`, la colonne `errors` compte les appels qui ont échoué : 28 `newfstatat` et 7 `openat` en erreur sont normaux au démarrage de Python (recherche de modules) ; un grand nombre d'erreurs sur un programme de calcul serait un indice.
:::

`sar`, du même paquet sysstat que `iostat` et `pidstat`, affiche ces compteurs à intervalle fixe : `sar -u 1 3` pour le processeur, `sar -d 1 3` pour chaque disque. Il relit aussi les fichiers d'activité quotidiens qu'enregistre son collecteur `sadc` ([sar(1)](https://man7.org/linux/man-pages/man1/sar.1.html)) : c'est l'outil qui répond à « que s'est-il passé cette nuit ? ». Encore faut-il que la collecte tourne. Dans le bac à sable (sysstat 12.6.1, lu le 2026-10-25), `/etc/default/sysstat` contient `ENABLED="false"` et le dossier d'historique est vide : `sar` n'y a pas de passé à montrer.

Les outils de profilage d'échantillonnage, `perf` avec ses graphes de flammes et `bpftrace` pour tracer le noyau, complètent cette liste. Ils ne sont pas installés dans le bac à sable : ce cours les décrit sans en montrer de sortie. Pour les utiliser, partez d'une hypothèse issue de la table USE, pas de l'envie d'essayer.

### 4.4. Quatre charges, quatre lectures

Le lab 1.2 fait tourner `triage.py` pendant quatre situations réelles et vérifie que chacune est reconnue. Résultats d'une exécution (fractions du temps, sauf `aqu-sz`, la taille moyenne de file du disque, au nom de la colonne de `iostat -x`) :

| Situation | `cpu_util` | `cpu_psi` | `io_psi` | `disk_util` | `aqu-sz` | Conclusion de `classify` |
|---|---|---|---|---|---|---|
| machine au repos | 0,00 | 0,00 | 0,00 | 0,00 | 0,0 | rien ne ressort |
| 8 boucles actives sur 4 cœurs | 1,00 | 0,98 | 0,00 | 0,00 | 0,0 | processeur saturé |
| écritures synchrones avec `fsync` | 0,09 | 0,01 | 0,43 | 0,72 | 1,2 | tâches bloquées sur le disque |
| écritures asynchrones profondes (4 Kio aléatoires, `O_DIRECT`) | 0,34 | 0,02 | 0,00 | 0,93 | 6,3 | disque occupé, aucune tâche bloquée |

D'une exécution à l'autre, les chiffres bougent : deux autres exécutions ont donné, pour les écritures synchrones, `io_psi` de 0,19 et 0,28 et `disk_util` de 0,45 et 0,55. Seules les conclusions de `classify` et les ordres de grandeur sont reproductibles, et `verify.sh` ne vérifie que les conclusions.

::: war
[L'angle mort de la pression PSI]{.tag} La dernière ligne est la leçon du chapitre. Avec des entrées-sorties asynchrones (`libaio` et une file de 32 requêtes), le disque est occupé à 93 % mais **aucune tâche n'est bloquée** : la pression PSI `io` reste à zéro. Un diagnostic qui ne lirait que PSI conclurait « le disque va bien ». Il faut lire en plus l'occupation du disque et la taille de sa file dans `/proc/diskstats`.

Constaté sur ce disque virtuel, avec ce noyau ; reproduisez-le avec `verify.sh` avant de généraliser. Source : mesure de ce module (lab 1.2) ; la définition de `some` est celle de la [documentation PSI](https://docs.kernel.org/accounting/psi.html), qui ne parle pas de ce cas.
:::

::: recap
[Points clés]{.tag}

-   USE : pour chaque ressource, vérifier utilisation, saturation et erreurs ; remplir la table avant d'optimiser.
-   PSI mesure la part du temps où des tâches attendent ; le compteur `total` est cumulatif, donc lisez-le deux fois.
-   La charge moyenne mélange processeur et disque ; PSI les sépare.
-   `vmstat`, `iostat`, `pidstat` et `strace -c` couvrent l'essentiel ; `perf` et `bpftrace` sont décrits ici sans être exécutés.
-   PSI `io` est aveugle à une file profonde d'E/S asynchrones : lisez aussi l'occupation du disque.
:::

## 5. systemd, limites de ressources et paramètres noyau {#ch5}

Un nœud de calcul est configuré par des unités de service, des limites de processus et quelques paramètres du noyau. Chacun a une raison d'être pour un entraînement ; aucun n'a de valeur « magique ».

### 5.1. Unités systemd

*systemd* démarre et supervise les services. Une *unité* est un fichier qui décrit un service : quoi lancer (`ExecStart`), quand (`After=`), quoi faire en cas d'échec (`Restart=`) et quelles limites appliquer. Chaque service tourne dans son propre cgroup, ce qui relie ce chapitre au précédent ; `Delegate=` autorise un service à gérer lui-même les sous-cgroups, ce que font les gestionnaires de conteneurs.

~~~ini
[Service]
Type=simple
ExecStart=/usr/bin/python3 -m http.server 9400
Restart=on-failure
RestartSec=5s
LimitNOFILE=1048576
LimitMEMLOCK=infinity
MemoryMax=512M
Delegate=no
NoNewPrivileges=yes
~~~

Cet extrait est celui de `labs/linux-systems/ops-script/units/gpu-exporter.service`. `Restart=on-failure` relance le service s'il sort avec une erreur, `MemoryMax` pose une limite dure (c'est le `memory.max` du chapitre 2) et les deux `Limit…` règlent les limites de processus décrites plus bas.

::: ex
[Exemple 5.1 — `systemd-analyze verify` ne retourne pas 1 sur un avertissement]{.tag} Le bac à sable n'a pas systemd comme processus 1, mais `systemd-analyze verify` vérifie un fichier **hors ligne**. Sur l'unité propre : aucune sortie, statut 0. Sur une copie où l'on a écrit `Restart=sometimes` (valeur invalide) :

~~~text
units/bad.service:9: Failed to parse service restart specifier, ignoring: sometimes
rc=0
~~~

L'outil signale la valeur, l'ignore, **et retourne quand même 0**. Une intégration continue qui ne regarde que le code de retour accepte l'unité cassée. `check_unit.sh` (lab 1.5) traite toute sortie comme un échec, et son test vérifie qu'il rejette `bad.service`. Documentation : [systemd-analyze](https://www.freedesktop.org/software/systemd/man/latest/systemd-analyze.html).
:::

Les messages des services et du noyau sont rassemblés par *journald*, le journal de systemd. `journalctl -u slurmd` lit ceux d'une unité ; `journalctl -k` lit les messages du noyau du démarrage en cours (l'option « implies --boot=0 », selon [journalctl(1)](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html)), c'est-à-dire ce que `dmesg` montre au chapitre 8, avec des dates et des filtres. Dans le bac à sable, où systemd n'est pas le processus 1, les deux commandes affichent « No journal files were found. » et retournent 0 : comme à l'exemple 8.1, un outil muet n'est pas un nœud sain.

### 5.2. Limites de processus

Chaque processus a des limites (`ulimit`, `setrlimit`). `RLIMIT_NOFILE` borne le nombre de fichiers ouverts : un serveur de données ou un entraînement avec beaucoup de fragments de jeu de données l'atteint. `RLIMIT_MEMLOCK` borne la mémoire que le processus peut verrouiller en RAM ([getrlimit(2)](https://man7.org/linux/man-pages/man2/getrlimit.2.html)). La FAQ d'Open MPI sur InfiniBand en fait une cause classique d'échec d'initialisation et indique que, « for most HPC installations, the memlock limits should be set to "unlimited" » ([FAQ Open MPI](https://www.open-mpi.org/faq/?category=openfabrics)) : d'où le `LimitMEMLOCK=infinity` de l'unité ci-dessus. Dans une unité systemd, ces limites s'écrivent `LimitNOFILE=` et `LimitMEMLOCK=` ([systemd.exec](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)).

Sur la machine de test, `ulimit -n` donne 20 000 et `ulimit -l` donne 8 192 (en kio) : insuffisant pour de l'enregistrement RDMA de grande taille. Constater cette valeur sur un nœud avant de lancer un job est un contrôle d'une ligne.

### 5.3. Pages énormes

La mémoire virtuelle est gérée par pages de 4 Kio (chapitre 1). Des pages plus grandes réduisent le nombre d'entrées à gérer pour de grands tampons ; `Hugepagesize` de `/proc/meminfo` vaut 2 048 kio sur la machine de test. Le noyau les propose de deux façons : la *Transparent Huge Page* (THP), automatique, et des pages énormes réservées à l'avance. Le réglage de la THP est lisible dans `/sys/kernel/mm/transparent_hugepage/enabled`.

~~~text
$ cat /sys/kernel/mm/transparent_hugepage/enabled
always [madvise] never
~~~

La valeur entre crochets est le mode actif : ici `madvise`, c'est-à-dire que seules les régions qu'un programme marque avec `madvise(MADV_HUGEPAGE)` en bénéficient ([documentation THP](https://docs.kernel.org/admin-guide/mm/transhuge.html)). Ne changez ce mode qu'en mesurant la charge réelle : l'effet dépend du programme.

### 5.4. Quelques paramètres noyau

Les paramètres `vm.*` se lisent avec `sysctl`. Ceux qui reviennent le plus sur un nœud de calcul, avec leur valeur sur la machine de test (valeurs par défaut de cette distribution, pas des recommandations) :

| Paramètre | Valeur lue | Rôle |
|---|---|---|
| `vm.swappiness` | 60 | coût relatif estimé des E/S de swap par rapport aux E/S de fichiers, entre 0 et 200 ; à 100 le noyau les traite à égalité ; défaut 60 |
| `vm.overcommit_memory` | 0 | mode heuristique de réservation (voir 1.3) |
| `vm.dirty_ratio` | 20 | part de mémoire sale à partir de laquelle le processus qui écrit doit lui-même écrire des données sur disque |
| `vm.dirty_background_ratio` | 10 | part de mémoire sale à partir de laquelle les fils de vidage du noyau commencent à écrire |
| `vm.max_map_count` | 65530 | nombre maximal de zones de projection mémoire (*memory map areas*) d'un processus |

La [documentation sysctl vm](https://docs.kernel.org/admin-guide/sysctl/vm.html) décrit chacun. Le lab 1.5 vous fait écrire un script qui fixe ces valeurs **de façon idempotente** ; la valeur de `vm.max_map_count` qu'il utilise comme exemple n'est pas une recommandation.

::: recap
[Points clés]{.tag}

-   Une unité systemd décrit commande, dépendances, redémarrage et limites ; chaque service est un cgroup.
-   `systemd-analyze verify` marche hors ligne mais retourne 0 sur un avertissement : traitez toute sortie comme un échec.
-   `NOFILE` borne les fichiers ouverts, `MEMLOCK` la mémoire verrouillée dont le RDMA a besoin ; lisez-les avant un job.
-   La THP en mode `madvise` ne profite qu'aux régions marquées ; ne la changez pas sans mesure.
-   Les valeurs `vm.*` lues sont des défauts, pas des recommandations ; un script de configuration doit être idempotent.
:::

## 6. Réseau Linux {#ch6}

Pour un exploitant de cluster, le réseau Linux se résume à quatre questions : quelles interfaces existent, avec quelle MTU, à quel débit réel, et avec quels compteurs d'erreurs. Ce chapitre apprend à les poser et signale ce qu'une machine virtuelle ne permet pas de constater.

### 6.1. Voir les interfaces

`ip -br link` liste les interfaces en une ligne chacune ; `ip -d link show` détaille leurs paramètres, dont la MTU ; `ethtool -i` donne le pilote ; `ss -s` résume les connexions.

::: ex
[Exemple 6.1 — Une interface virtuelle lue de près]{.tag} Capturé dans le bac à sable :

~~~text
$ ip -br link
lo      UNKNOWN  00:00:00:00:00:00  <LOOPBACK,UP,LOWER_UP>
eth0    UP       02:fc:00:00:00:01  <BROADCAST,MULTICAST,UP,LOWER_UP>
$ ip -d link show eth0 | head -1
4: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1400 qdisc pfifo_fast state UP ...
$ ethtool -i eth0 | head -1
driver: virtio_net
$ ss -s | head -2
Total: 33
TCP:   19 (estab 15, closed 1, orphaned 0, timewait 1)
~~~

(deux interfaces `ifb` à l'état `DOWN` sont omises.) La MTU est de **1 400**, pas 1 500, et le pilote est `virtio_net`, c'est-à-dire une carte virtuelle : il n'y a ni vitesse de lien réelle ni compteurs matériels d'erreurs à lire. Sur du matériel, `ethtool -S` donne ces compteurs ; ici le constat est « non observable », pas « aucune erreur ».
:::

### 6.2. MTU et surcoût d'en-têtes

La *MTU* (*maximum transmission unit*) est la taille maximale d'un paquet sur un lien. Chaque segment TCP transporte au plus la MTU moins les en-têtes ; avec les en-têtes minimaux IPv4 et TCP de 20 octets chacun, la charge utile maximale est la MTU moins 40, et la part d'en-têtes est de 40 divisé par la MTU.

| MTU | Charge utile TCP maximale | Part d'en-têtes |
|---|---|---|
| 1 400 | 1 360 octets | 2,86 % |
| 1 500 | 1 460 octets | 2,67 % |
| 9 000 | 8 960 octets | 0,44 % |

Le gain d'une MTU de 9 000 (*jumbo frames*) est réel pour les gros transferts, mais **chaque équipement du chemin** doit l'accepter, sinon les paquets sont fragmentés ou perdus. Une MTU incohérente entre deux machines est une panne classique et silencieuse : les petits messages passent, les gros s'arrêtent.

### 6.3. La boucle locale n'est pas un réseau

`iperf3` mesure le débit TCP entre deux machines. Contre l'adresse locale, il mesure autre chose.

::: ex
[Exemple 6.2 — 11,5 Gbit/s sur une interface qui n'existe pas]{.tag} Capturé : `iperf3 -c 127.0.0.1 -t 3` renvoie

~~~text
[  5]   0.00-3.00   sec  4.01 GBytes  11.5 Gbits/sec    2   sender
[  5]   0.00-3.00   sec  4.01 GBytes  11.5 Gbits/sec        receiver
~~~

Ces 11,5 Gbit/s sont la vitesse à laquelle le noyau copie des données d'un processus à un autre dans la même machine : aucune carte réseau n'intervient. Citer ce chiffre comme « le débit du réseau » serait faux. La mesure utile se fait **entre deux nœuds**, avec un jeu de paramètres que le module réseau détaille.
:::

### 6.4. Regroupement, contrôle de trafic et ce qu'on ne peut pas tester ici

Le *bonding* regroupe plusieurs interfaces en une seule pour la redondance ou le débit. `tc` (*traffic control*) configure les files d'attente d'une interface, ce qui permet d'émuler un lien lent ou perdant avec le module `netem`. Dans le bac à sable, cette émulation n'est pas possible : le noyau répond `Error: Specified qdisc kind is unknown.` à `tc qdisc add dev lo root netem delay 20ms`. C'est un constat sur ce noyau précis ; sur une machine de laboratoire, ces tests d'impact d'un lien dégradé sont précieux pour vérifier que vos outils de supervision détectent le problème.

### 6.5. Premiers pas RDMA

Dans une communication TCP, le noyau copie les données entre le programme et la carte. Avec le *RDMA* (*remote direct memory access*), la carte lit et écrit directement la mémoire du programme, sans passer par le noyau pour chaque transfert : c'est ce qui permet les latences basses et les débits élevés des réseaux de calcul (InfiniBand, ou RoCE, c'est-à-dire du RDMA sur Ethernet). Le programme **enregistre** d'abord des zones mémoire auprès de la carte, ce qui explique les limites `memlock` du chapitre 5.

Le [module 7 — Réseaux haute performance](../networking/index.html) détaille les protocoles (chapitres 2 à 4), la topologie (chapitre 5) et la mesure (chapitre 8). Retenez ici deux choses : le chemin des données change, donc les outils de diagnostic aussi, et un nœud dont la limite `memlock` est basse peut échouer à initialiser sa communication.

::: recap
[Points clés]{.tag}

-   `ip -br link`, `ip -d link`, `ethtool -i` et `ss -s` répondent aux quatre premières questions ; en machine virtuelle, les compteurs matériels sont absents.
-   La MTU fixe la charge utile (MTU moins 40) ; une MTU incohérente sur le chemin casse les gros paquets sans casser les petits.
-   Un `iperf3` sur la boucle locale mesure la copie mémoire du noyau, pas un réseau.
-   `tc netem` permet d'émuler un lien dégradé quand le noyau le permet ; ici il ne le permet pas.
-   RDMA contourne le noyau pour les transferts et exige de la mémoire enregistrée, donc des limites `memlock` adaptées.
:::

## 7. Stockage Linux {#ch7}

Un entraînement lit son jeu de données et écrit ses checkpoints : le stockage est sur le chemin critique. Ce chapitre apprend à distinguer ce que fait le cache de pages de ce que fait le disque, avec des compteurs et non avec des chronomètres.

### 7.1. Périphériques de bloc et systèmes de fichiers

`lsblk` liste les disques et leurs partitions ; la colonne `ROTA` indique si le noyau croit le disque rotatif. Le système de fichiers de la machine de test est de l'ext4 sur `/dev/vda` (`findmnt`).

Le noyau documente plusieurs systèmes de fichiers locaux, dont ext4, « an advanced level of the ext3 filesystem » ([ext4](https://docs.kernel.org/admin-guide/ext4.html)), et XFS, « a high performance journaling filesystem » prévu pour les gros fichiers et les grands volumes ([XFS](https://docs.kernel.org/admin-guide/xfs.html)). `findmnt` dit lequel est monté ; les compteurs et la loi de Little de ce chapitre s'appliquent aux deux. XFS n'est pas outillé dans le bac à sable (ni `mkfs.xfs` ni `xfs_info`) : ce chapitre n'en montre pas de sortie.

::: ex
[Exemple 7.1 — Quand `ROTA` ment]{.tag} Capturé :

~~~text
$ lsblk -o NAME,TYPE,SIZE,ROTA,MOUNTPOINT
NAME  TYPE  SIZE ROTA MOUNTPOINT
vda   disk  256G    1 /
vdb   disk  9.6M    1 /opt/rclone
~~~

Tous les disques virtio annoncent `ROTA=1`, comme s'ils étaient des disques durs mécaniques. Un disque virtuel ne connaît pas la nature du support qui se trouve derrière lui sur l'hôte : le drapeau n'est pas une mesure. Un script qui choisirait un ordonnanceur d'E/S ou une stratégie de lecture d'après `ROTA` se tromperait ici : **vérifiez avec une mesure**, comme celle de la section suivante.
:::

### 7.2. Mesurer un disque avec `fio` : la loi de Little

`fio` génère des charges d'entrée-sortie contrôlées. La **loi de Little** relie trois quantités d'un système stable : le nombre moyen de requêtes en cours est le produit du débit par le temps moyen de traitement.

$$N = \lambda \, W$$

Avec une file de profondeur $N$ (le nombre de requêtes que `fio` garde en vol), un débit $\lambda$ en requêtes par seconde et une latence moyenne $W$, le produit doit valoir $N$. C'est un contrôle de cohérence de toute mesure d'E/S : un résultat qui s'en écarte est suspect.

::: ex
[Exemple 7.2 — Little vérifiée sur le disque virtuel du bac à sable]{.tag} Le lab 1.3 (partie B) lance des lectures aléatoires de 4 Kio en `O_DIRECT` à profondeur de file 1 puis 32. Capturé :

~~~text
iodepth=1   iops=   16992  mean latency=   57.8 us  iops x latency =  0.98
iodepth=32  iops=   60341  mean latency=  529.3 us  iops x latency = 31.94
~~~

Le produit vaut 0,98 pour une profondeur de 1 et 31,94 pour 32 : la loi tient à 2 % près. **Lecture utile** : passer de 1 à 32 requêtes en vol multiplie le débit par 3,6 (60 341 sur 16 992) mais la latence moyenne par 9,2 (529,3 sur 57,8). Au-delà d'un certain point, mettre plus de requêtes en file ne fait qu'allonger l'attente : c'est le compromis entre débit et latence, lisible dans la sortie.
:::

### 7.3. Cache de pages, `fsync` et `O_DIRECT`

Une lecture normale passe par le cache de pages ; l'indicateur `O_DIRECT` de [open(2)](https://man7.org/linux/man-pages/man2/open.2.html) demande de « minimize cache effects of the I/O to and from this file » et exige des tampons alignés. `posix_fadvise` avec `POSIX_FADV_DONTNEED` « attempts to free cached pages » d'un fichier ([posix_fadvise(2)](https://man7.org/linux/man-pages/man2/posix_fadvise.2.html)), et [mincore(2)](https://man7.org/linux/man-pages/man2/mincore.2.html) permet de « determine whether pages are resident in memory ». Avec ces trois appels, le lab 1.3 raconte l'histoire du cache avec des compteurs.

::: ex
[Exemple 7.3 — Ce que le noyau a fait de 256 Mio]{.tag} Résultat du lab 1.3, partie A (les colonnes « résident » et « lu sur le périphérique » ont été identiques sur trois exécutions ; `dirty KiB` varie de quelques centaines de kio, car c'est le compteur `Dirty` de **toute la machine**, pas celui du fichier) :

~~~text
stage                  dirty KiB  resident MiB  device read MiB
after write()             262540           256                -
after fsync()                404           256                -
after DONTNEED               404             0                -
cold buffered read           404           256              256
warm buffered read           408           256                0
O_DIRECT read                408             0              256
~~~

Lecture ligne à ligne : après `write()`, 262 540 kio de pages sont sales, c'est-à-dire pas encore sur le disque (256 Mio font 262 144 kio ; le reste est le bruit de fond de la machine), mais les 256 Mio sont déjà **résidents**. `fsync()` ramène les pages sales à 404 kio sans les évincer. `DONTNEED` vide le cache du fichier. La lecture à froid lit 256 Mio **sur le périphérique** ; la lecture à chaud n'en lit aucun ; la lecture `O_DIRECT` lit 256 Mio sur le périphérique et **ne remplit pas** le cache.
:::

::: war
[Pourquoi ce lab compte des octets et pas des secondes]{.tag} Dans le bac à sable, une lecture « à froid » de 256 Mio ne prend que 0,10 s (2,5 Gio/s) contre 0,04 s à chaud, soit un rapport de 2,5 seulement (trois mesures le 2026-10-24). Le chronomètre ne dit pas si ces octets viennent d'un disque rapide ou d'un cache de l'hôte sous le disque virtuel (hypothèse, non vérifiée).

Des processus de la plateforme écrivent aussi dans `drop_caches`, ce que le journal du noyau garde en mémoire au démarrage (`dmesg` : « process_api (1): drop_caches: 10 », « tokio-rt-worker (77): drop_caches: 3 »). Un chronomètre brouille donc la lecture.

Les compteurs d'octets lus sur le périphérique, eux, restent exacts, à une réserve près : ils comptent tout le disque, donc la lecture d'un autre processus les fausse (raisonnement sur le code, non provoqué en pratique : cause possible d'un échec de `verify.sh` sur une machine partagée). Même sur du matériel, préférez le compteur. Source : mesures de ce module et journal du noyau du bac à sable.
:::

### 7.4. Écrire un checkpoint

Pour écrire un état de plusieurs gigaoctets, trois choix s'offrent. Écrire normalement et laisser le cache de pages absorber l'écriture est rapide, mais laisse jusqu'à la taille du fichier en mémoire sale puis résidente : sur un nœud où le jeu de données est lui aussi en cache, elle peut le chasser. Appeler `fsync()` rend l'écriture **durable** avant de répondre. Écrire en `O_DIRECT` évite de polluer le cache, au prix d'alignements et de tailles de bloc à respecter.

L'enseignement du lab 1.3 est que ces choix se **lisent** dans des compteurs. Le [projet 3](../../projects/resilient-trainer/index.html) en tire les conséquences pour un checkpoint atomique : écrire dans un fichier temporaire, `fsync`, renommer, puis synchroniser le dossier.

::: recap
[Points clés]{.tag}

-   `ROTA` d'un disque virtuel ne dit rien du support ; mesurez.
-   Loi de Little : requêtes en vol = débit × latence moyenne ; elle valide toute mesure d'E/S.
-   Une écriture est sale puis durable après `fsync` ; une lecture à froid lit le périphérique, à chaud non, `O_DIRECT` contourne le cache.
-   Comptez des octets lus sur le périphérique, pas des secondes, quand un hôte peut cacher le disque.
-   Un checkpoint durable combine fichier temporaire, `fsync`, renommage atomique et synchronisation du dossier.
:::

## 8. Pannes matérielles vues du système, et scripts d'exploitation robustes {#ch8}

Sur une flotte de GPU, une partie des pannes vient du matériel. Ce chapitre apprend où le système les rend visibles et comment écrire les scripts d'exploitation qui réagissent sans aggraver la situation.

### 8.1. Où le système voit une panne matérielle

Le noyau journalise ce qu'il détecte : `dmesg` lit ce journal. Pour la mémoire, le sous-système **EDAC** expose par contrôleur des compteurs d'erreurs corrigées par le code correcteur (ECC) et non corrigées sous `/sys/devices/system/edac/mc/` ([documentation EDAC](https://docs.kernel.org/driver-api/edac.html)). Pour les disques, `smartctl` lit les attributs SMART (l'auto-surveillance intégrée au disque). Pour le serveur lui-même, le contrôleur de gestion (BMC) tient un journal d'événements que `ipmitool sel` affiche ; il répond aussi en réseau, par IPMI ou par l'API REST Redfish ([module 6, chapitre 8](../provisioning/index.html#ch8), et le [lab 6.4](../provisioning/index.html#lab-6-4)).

::: ex
[Exemple 8.1 — Quand l'instrument est absent]{.tag} Dans le bac à sable (machine virtuelle), les trois sources de panne matérielle sont **absentes**. Capturé :

~~~text
$ ls /sys/devices/system/edac
ls: cannot access '/sys/devices/system/edac': No such file or directory
$ smartctl -a /dev/vda
/dev/vda: Unable to detect device type
$ ipmitool mc info
Could not open device at /dev/ipmi0 or /dev/ipmi/0 or /dev/ipmidev/0: No such file or directory
~~~

La conséquence pour un script de supervision est capitale : « je n'ai trouvé aucune erreur » et « je n'ai pas pu regarder » sont **deux états différents**. Un contrôle qui retourne 0 dans les deux cas déclare sain un nœud qu'il ne sait pas observer. Retournez un code distinct (par exemple 3 pour « non observable ») et traitez-le comme une alerte de configuration.
:::

### 8.2. Les erreurs de GPU : les messages Xid

Le pilote NVIDIA journalise les erreurs de GPU sous forme de messages *Xid*. La documentation de NVIDIA indique : « Grep for "NVRM: Xid" to find all the Xid messages », qui sont écrits dans le journal du noyau ([Working with Xid Errors](https://docs.nvidia.com/deploy/xid-errors/working-with-xid-errors.html)). Son catalogue donne l'exemple `NVRM: Xid (PCI:0000:5a:00): 79, GPU has fallen off the bus.` ([catalogue Xid](https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html)).

Le nombre après les deux-points est le code Xid ; la signification de chaque code est dans le catalogue, qui est la référence. Le [lab 5.3 du module Slurm](../slurm/index.html) simule un Xid 79 pour mettre un nœud en quarantaine, et le [projet 5](../../projects/gpu-observability/index.html) lit la valeur du dernier Xid exposée par dcgm-exporter. Aucun GPU n'est disponible dans le bac à sable : ces deux labs simulent le Xid, et ce chapitre ne montre pas de sortie réelle de pilote.

### 8.3. Lire un journal du noyau

Un journal se lit champ par champ. Voici la mise à mort par manque de mémoire de l'exemple 2.2, telle que le noyau l'a journalisée dans le bac à sable :

::: ex
[Exemple 8.2 — Les lignes du noyau après une mise à mort par manque de mémoire]{.tag} Extrait capturé de `dmesg` :

~~~text
oom-kill:constraint=CONSTRAINT_MEMCG,nodemask=(null),cpuset=/,mems_allowed=0,oom_memcg=/mci-lab-28861,task_memcg=/mci-lab-28861,task=python3,pid=28868,uid=0
Memory cgroup out of memory: Killed process 28868 (python3) total-vm:116780kB, anon-rss:102016kB, file-rss:5836kB, shmem-rss:0kB, UID:0 pgtables:260kB oom_score_adj:0
~~~

`constraint=CONSTRAINT_MEMCG` dit que la mise à mort est due à la **limite d'un cgroup** et non à la mémoire de la machine entière ; `oom_memcg=/mci-lab-28861` nomme le groupe fautif (le lab le nomme `mci-lab-` suivi du PID du script). `anon-rss` est la mémoire anonyme (tas, piles) du processus tué : c'est elle qui a atteint la limite. Sans cette ligne, un job « disparu » sans message est un mystère ; avec elle, c'est un diagnostic.
:::

### 8.4. Écrire un script d'exploitation robuste

Un script d'exploitation tourne sans surveillance, souvent à un moment critique. Cinq règles lui évitent d'aggraver une panne.

1.  **Idempotent** : l'appliquer deux fois donne le même état qu'une fois. Il rapporte « inchangé » au lieu de recommencer.
2.  **Codes de retour qui veulent dire quelque chose** : 0 rien à faire, 10 modifié, 2 usage invalide, 1 échec, 3 non observable.
3.  **Mode « à blanc »** (`--dry-run`) qui dit ce qu'il ferait sans l'écrire.
4.  **Écriture atomique** : fichier temporaire puis renommage, pour ne jamais laisser un fichier à moitié écrit.
5.  **Journal sur la sortie d'erreur**, daté, d'une ligne par décision.

`ensure_sysctl.sh` du lab 1.5 applique ces cinq règles, avec les codes 0, 10, 2 et 1 : le code 3 sert aux contrôles d'un matériel (exemple 8.1), et le « Pour aller plus loin » du lab l'ajoute à un contrôle SMART. Le comportement de `set -e`, souvent invoqué comme garantie, a des angles morts qu'une exécution montre mieux qu'une description.

::: ex
[Exemple 8.3 — Ce que `set -e` ne rattrape pas]{.tag} Le script `errexit_demo.sh` du lab 1.5, capturé :

~~~text
1) function called as an if condition:
  check_disk went on after a failure
  -> condition true
2) the same function in a subshell on the left of ||:
  check_disk went on after a failure
3) pipeline without pipefail:
  status: 0
4) pipeline with pipefail:
  status: 1
~~~

Dans une condition `if` ou à gauche d'un `||` (cas 2, ici dans un sous-shell), `set -e` est **neutralisé** : la fonction continue après `false` ; dans le cas 1, la condition est vraie. Sans `set -o pipefail`, `false | cat` retourne 0 car seul le statut de la dernière commande compte. Un contrôle de santé écrit sans ces précautions peut donc déclarer sain un nœud qui ne l'est pas.
:::

::: ex
[Exemple 8.4 — Un script idempotent, appliqué deux fois]{.tag} Premier appel sur un fichier qui contient `vm.swappiness = 60`, puis le même appel, capturés :

~~~text
changed: vm.swappiness 60 -> 10          rc=10
changed: vm.max_map_count <unset> -> 1048576
unchanged: vm.swappiness = 10            rc=0
unchanged: vm.max_map_count = 1048576
~~~

(les horodatages sont omis.) Le premier appel modifie et retourne 10 ; le second ne change rien et retourne 0. Le fichier garde ses commentaires et ne contient qu'une ligne par clé. Un appelant qui ne recharge la configuration que sur le code 10 évite un rechargement inutile à chaque passage d'un outil d'orchestration.
:::

::: recap
[Points clés]{.tag}

-   EDAC, SMART et le BMC sont les sources de pannes matérielles ; en machine virtuelle elles sont absentes, et un script doit distinguer « aucune erreur » de « non observable ».
-   Les erreurs de GPU sont des messages `NVRM: Xid` dans le journal du noyau ; le catalogue de NVIDIA est la référence des codes.
-   Une ligne de journal se lit champ par champ ; `constraint=CONSTRAINT_MEMCG` désigne une limite de cgroup.
-   Un script d'exploitation est idempotent, a des codes de retour explicites, un mode à blanc, des écritures atomiques et un journal.
-   `set -e` est neutralisé dans les conditions et les listes `||`, et un pipeline demande `pipefail`.
:::

## Labs {#labs}

Cinq labs, tous exécutés dans le bac à sable (machine virtuelle Linux 6.18, 4 processeurs, sans GPU), le lab 1.4 dans sa branche cgroup v1 seulement. `verify.sh` de chaque lab sort avec le code 0 et affiche la valeur du critère de réussite. Le lab 1.4 exige root et un cgroup ; lisez ses avertissements avant de l'exécuter. Lancez chaque commande depuis le dossier du lab (`cd labs/linux-systems/<lab>`). Les durées de lab indiquées sont celles du travail guidé ; elles tiennent dans les séances du plan.

Installation préalable des outils des labs 1.2, 1.3 et 1.5 : `sudo apt-get install -y stress-ng fio shellcheck systemd` (le paquet `systemd` fournit `systemd-analyze` ; l'image de conteneur Ubuntu 24.04 ne contient que `libsystemd0`, selon son [manifeste](https://partner-images.canonical.com/oci/noble/current/ubuntu-noble-oci-amd64-root.manifest) lu le 2026-10-25).

### Lab 1.1 — Cartographier une machine {#lab-1-1}

::: lab

**Objectif.** Produire un rapport JSON de la machine (processeurs, NUMA, mémoire, PCI, interfaces, disques) et sa **table de localité** GPU, carte réseau et NVMe. **Durée.** 1.5 h. **Prérequis matériels.** Un portable Linux ; aucun GPU.

1.  Lisez `labs/linux-systems/machine-map/machine_map.py` : repérez comment `numa_node` et la classe PCI sont croisés.
2.  Lancez `python3 machine_map.py` sur votre machine et repérez ce qui est vide (nœuds NUMA, PCI) et pourquoi.
3.  Lancez-le sur le serveur à deux sockets **fabriqué à la main** : `--sysroot fixtures/sysroot-2socket`. Retrouvez la carte réseau du GPU `0000:86:00.0`.
4.  Ajoutez au rapport la somme de la mémoire des nœuds et comparez-la à `MemTotal` (exemple 3.2).
5.  Écrivez un test pour votre ajout et lancez `bash verify.sh`.

**Critère de réussite.** `bash verify.sh` affiche « fixture: 2 NUMA nodes, 4 GPUs, 2 InfiniBand NICs », puis « live: 4 logical CPUs, 1 NUMA node(s), 15.7 GiB (MemTotal) » sur le bac à sable, puis « OK machine-map ». Neuf tests unitaires passent.

**Pour aller plus loin.** Sur une machine à GPU, comparez `locality` avec `nvidia-smi topo -m` et signalez toute divergence.
:::

### Lab 1.2 — Triage avec la méthode USE et la pression PSI {#lab-1-2}

::: lab

**Objectif.** Reconnaître, avec des compteurs du noyau, quatre situations réelles : repos, processeur saturé, tâches bloquées sur le disque, et l'angle mort de PSI. **Durée.** 1.5 h. **Prérequis matériels.** Linux avec PSI, `stress-ng` et `fio`.

1.  Lisez `labs/linux-systems/psi-triage/triage.py` : `compute` transforme deux instantanés en fractions du temps, `classify` en conclusions.
2.  Lancez `python3 triage.py --seconds 5` sur votre machine au repos.
3.  Provoquez une charge de processeur avec `stress-ng --cpu 8 --timeout 10s` et relancez.
4.  Provoquez des écritures synchrones puis asynchrones avec `fio` (voir les deux commandes de `verify.sh`) et comparez `io_psi` et `disk_util`.
5.  Le seuil mémoire (`mem_psi`) et son test existent déjà : ajoutez à la place la détection d'une activité de swap (`pswpin` et `pswpout` de `/proc/vmstat`, lus deux fois) et écrivez son test.

**Critère de réussite.** `bash verify.sh` affiche quatre lignes JSON dont les conclusions sont « cpu: saturated (busy and tasks waiting) », « io: tasks are stalled waiting for the disk » et « disk: busy, but no task stalls », puis « OK psi-triage ». Durée d'exécution : environ 30 secondes.

**Pour aller plus loin.** Créez de la pression mémoire dans un cgroup (lab 1.4) et vérifiez que PSI `memory` la voit.
:::

### Lab 1.3 — Page cache : mesurer ce qui touche le disque {#lab-1-3}

::: lab

**Objectif.** Raconter, avec trois compteurs du noyau, ce que deviennent 256 Mio écrits puis relus, et vérifier la loi de Little. **Durée.** 1.5 h. **Prérequis matériels.** Linux avec un système de fichiers sur disque (pas `tmpfs`) ; `fio` pour la partie B.

1.  Lisez `pagecache.py` : `resident_bytes` (mincore), `parse_diskstats`, `drop_file_cache` (fadvise).
2.  Lancez `python3 pagecache.py` et expliquez chaque ligne avec le tableau de l'exemple 7.3.
3.  Remplacez `os.fsync` par rien et observez ce qui change dans la colonne `dirty KiB`.
4.  Lancez `bash littles_law.sh` et vérifiez le produit débit × latence pour deux profondeurs de file.
5.  Sur un autre disque local de votre choix (un disque USB par exemple, avec `--dir` et au besoin `--device`), refaites la partie A et comparez. Un partage NFS ne convient pas : ses lectures ne passent pas par un périphérique de bloc local et n'apparaissent pas dans `/proc/diskstats`.

**Critère de réussite.** `bash verify.sh` affiche le tableau (lecture à froid : 256 Mio lus sur le périphérique ; à chaud : 0 ; `O_DIRECT` : 256 Mio et 0 Mio résidents), « OK pagecache », puis « iodepth=32 … iops x latency » proche de 32 (31,9 dans nos exécutions) et « OK littles-law ». Les colonnes de comptage ont été identiques sur trois exécutions ; `iodepth=32` doit rester à 25 % près de 32.

**Pour aller plus loin.** Écrivez un checkpoint par blocs de 1 Gio avec `fsync` et `DONTNEED` après chaque bloc, et mesurez la mémoire résidente maximale.
:::

### Lab 1.4 — cgroups : limite mémoire, mise à mort, quota de processeur {#lab-1-4}

::: lab

**Objectif.** Mettre un programme dans un cgroup, constater sa mise à mort par manque de mémoire, mesurer un quota de processeur. **Durée.** 1.5 h. **Prérequis matériels.** Linux, **root**, une machine jetable. **Branche exécutée.** Le script détecte la version : la branche **cgroup v1** a été exécutée dans le bac à sable ; la branche **cgroup v2** suit la documentation du noyau et **n'a pas pu être exécutée** (le bac à sable est en v1, avec seulement `hugetlb` côté v2).

1.  Lisez `labs/linux-systems/cgroup-limits/cgroup_lab.sh` : repérez la détection de version (`stat -fc %T`) et les deux branches.
2.  Lancez `sudo bash verify.sh`. Le script alloue 300 Mio dans un cgroup limité à 100 Mio.
3.  Lisez ensuite `dmesg | tail` et retrouvez les champs de l'exemple 8.2.
4.  Changez la limite mémoire, relancez, et prédisez à quelle étape le programme est tué.
5.  Sur une machine en cgroup v2, exécutez la branche v2 et **signalez tout écart** avec la page.

**Critère de réussite.** `sudo bash verify.sh` affiche « exit status: 137, oom_kill counter: 1 », « share of one CPU obtained » proche de 0,20 (0,197 à 0,200 dans nos exécutions ; le script accepte de 0,10 à 0,35 pour un quota de 20 %, ce qui suppose une machine peu chargée) et « OK cgroup-limits (v1) ».

**Pour aller plus loin.** Ajoutez `memory.high` en v2 et montrez que le groupe est ralenti sans être tué.
:::

### Lab 1.5 — Un script d'exploitation idempotent {#lab-1-5}

::: lab

**Objectif.** Écrire et tester un script qui fixe des paramètres noyau de façon idempotente, vérifier une unité systemd hors ligne, et constater les angles morts de `set -e`. **Durée.** 2 h, exercice 11 compris. **Prérequis matériels.** Linux, `shellcheck` et `systemd-analyze` (paquet `systemd`) ; aucun accès root requis (le test `--apply` ne s'exécute qu'en root et sans effet).

1.  Lisez `ensure_sysctl.sh` : cinq règles du chapitre 8, dont les codes de retour 0, 10, 2 et 1.
2.  Exécutez-le deux fois de suite, par exemple `./ensure_sysctl.sh --conf /tmp/90-mci.conf vm.swappiness=10`, et comparez les codes de retour (`echo $?`).
3.  Lancez `bash test_ensure_sysctl.sh` ; cassez volontairement une ligne du script et vérifiez que le test échoue.
4.  Lancez `./check_unit.sh units/bad.service` et expliquez pourquoi `systemd-analyze verify` seul ne suffit pas.
5.  Écrivez `ensure_line.sh` (exercice 11) puis comparez avec `solutions/ensure_line.sh`.

**Critère de réussite.** `bash verify.sh` affiche « ALL OK » pour les contrôles de `ensure_sysctl.sh` (22 hors root, 24 en root), « ok: the broken unit is rejected although systemd-analyze itself exits 0 », les deux compteurs « check_disk went on after a failure », puis « OK ops-script ».

**Pour aller plus loin.** Ajoutez un code de retour 3 « non observable » à un contrôle SMART qui échoue sur un disque virtuel.
:::

## Exercices {#ex}

Les extraits marqués « fabriqués » sont écrits pour l'exercice ; ils imitent le format des vrais outils mais ne sont pas des captures.

::: exo
[Exercice 1 · ★ — Pages touchées]{.tag} Un programme réserve 2 Gio de mémoire anonyme sur une machine à pages de 4 Kio, puis écrit un octet par page sur les 512 premiers Mio. (a) Combien de pages sont touchées ? (b) De combien `VmSize` et `VmRSS` ont-ils augmenté à la fin, en Mio ?
:::

::: sol
(a) 512 Mio divisés par 4 Kio donnent 512 × 2^20 / 4096 = **131 072 pages** (calcul Python). (b) `VmSize` a augmenté de **2 048 Mio** dès la réservation ; `VmRSS` a augmenté d'environ **512 Mio**, les seules pages touchées. L'allocation est à la demande : réserver 2 Gio ne consomme pas 2 Gio. Même mécanisme qu'à l'exemple 1.3, où toucher 128 Mio avait fait passer `VmRSS` de 10 à 138.
:::

::: exo
[Exercice 2 · ★ — Lire un `vmstat`]{.tag} Extrait **fabriqué** sur un nœud d'entraînement lent :

~~~text
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1 14      0 210000   4000 500000    0    0 52000    80 1500 3000  3  2 10 85  0
 0 13      0 208000   4000 502000    0    0 49000   120 1400 2900  2  1 12 85  0
~~~

Quelle ressource est limitante ? Quelles colonnes le prouvent ? Quelle mesure ajoutez-vous ensuite ?
:::

::: sol
Le **disque** est limitant. `wa` vaut 85 % : les processeurs sont inactifs en attente d'entrées-sorties. `b` vaut 13 à 14 : des tâches sont bloquées en état D, alors que `r` est de 0 à 1, donc aucun processeur n'est demandé. `bi` autour de 50 000 blocs par seconde montre une lecture soutenue ; pas de swap (`si` et `so` à 0).

Ensuite : la pression PSI `io` pour confirmer, `iostat -x` pour l'occupation et la file du disque, et `pidstat -d` pour trouver **quel processus** lit. Attention à l'angle mort du chapitre 4 : si PSI `io` reste à zéro mais que le disque est occupé, la charge est asynchrone.
:::

::: exo
[Exercice 3 · ★★ — Lire une mise à mort et dimensionner la limite]{.tag} L'exemple 2.2 donne : limite de 100 Mio, dernier message « allocated 90 MiB », `anon-rss:102016kB`. (a) Quelle part de la limite représente `anon-rss` ? (b) Donnez un majorant de la mémoire anonyme de base de l'interpréteur. (c) Quelle limite `memory.max` donneriez-vous à un programme qui a besoin de 90 Mio de données, avec 20 % de marge ?
:::

::: sol
(a) 102 016 / 102 400 = **99,6 %** de la limite. (b) 90 Mio valent 92 160 kB ; 102 016 moins 92 160 donnent **9 856 kB, soit 9,6 Mio**. C'est un **majorant** de la base, pas la base : le dixième bloc était déjà en partie touché quand le noyau a tué (un Python au repos n'a qu'environ 2,8 Mio de mémoire anonyme, `RssAnon`).

(c) Par prudence, on prend le majorant : besoin total 90 + 9,6 = 99,6 Mio ; avec 20 % de marge : 99,6 × 1,2 ≈ 119,5, soit une limite d'environ **120 Mio**. Une limite à 100 Mio, juste au besoin, tue le programme à la moindre variation ; c'est exactement ce que le lab 1.4 provoque.
:::

::: exo
[Exercice 4 · ★★ — Épingler un job sur GPU]{.tag} Avec le serveur à deux sockets fabriqué du lab 1.1, un job utilise les GPU `0000:86:00.0` et `0000:af:00.0`. Les fichiers `cpulist` de ce serveur donnent `0-31,64-95` pour le nœud 0 et `32-63,96-127` pour le nœud 1. Sur quels cœurs doit-il être épinglé, quelle carte InfiniBand doit-il utiliser, et quelle commande l'épingle ? Que se passe-t-il s'il utilise la carte `0000:5e:00.0` ?
:::

::: sol
Les deux GPU sont sur le **nœud 1** (`locality`), dont les cœurs sont **32 à 63 et 96 à 127** (64 processeurs logiques). La carte du nœud 1 est **`0000:c1:00.0`**. Commande : `numactl --cpunodebind=1 --membind=1 python train.py`. Avec `0000:5e:00.0`, rattachée au nœud 0, chaque transfert réseau doit traverser la liaison entre sockets : latence et débit sont dégradés, sans erreur visible. Vérifiable avec `python3 machine_map.py --sysroot fixtures/sysroot-2socket`.
:::

::: exo
[Exercice 5 · ★★ — Huit tâches sur quatre cœurs]{.tag} Huit tâches de calcul pur tournent en permanence sur un nœud de quatre cœurs. (a) Quelle charge moyenne à une minute lit-on après cinq minutes ? (b) Une tâche qui demanderait 60 secondes de processeur seule dure combien ici ? (c) De la charge ou de la pression PSI `cpu`, laquelle dit combien de temps les tâches attendent ?
:::

::: sol
(a) $L = 8\,(1 - e^{-300/60}) = 8 \times 0{,}9933 \approx$ **7,95** (calcul Python) : elle tend vers 8. (b) Chaque tâche obtient 4 / 8 = 0,5 cœur : **120 secondes**. (c) La **pression PSI** : sa ligne `some` donne la part du temps où des tâches attendent un cœur (0,98 à l'exemple du lab 1.2). La charge dit seulement combien de tâches sont en file, sans distinguer processeur et disque.
:::

::: exo
[Exercice 6 · ★★ — Trois façons d'écrire un checkpoint]{.tag} Un nœud de 512 Gio de mémoire contient 300 Gio de jeu de données en cache de pages et 150 Gio occupés par les processus. Il doit écrire un checkpoint de 100 Gio. Option A : écriture normale puis `fsync` à la fin. Option B : écriture par blocs, avec `fsync` puis `DONTNEED` après chaque bloc. Option C : `O_DIRECT`. **Hypothèse de l'exercice** : le stockage relit à 2 Gio/s. Comparez la mémoire de cache évincée et le coût en relecture de A, puis dites laquelle vous choisissez et ce que vous mesureriez.
:::

::: sol
Mémoire libre : 512 − (300 + 150) = **62 Gio**. **A** : le checkpoint occupe 100 Gio de cache ; il en manque 38, donc au pire le noyau évince **38 Gio du jeu de données**. Relus à 2 Gio/s, ils coûtent 38 / 2 = **19 s** qui s'ajoutent à l'entraînement, sans compter l'effet sur l'écriture elle-même. C'est une borne haute : le noyau peut aussi évincer les pages déjà écrites du checkpoint, qu'on ne relira pas, avant celles du jeu de données relues souvent ; seule la mesure tranche.

**B** : l'empreinte du cache reste de l'ordre d'un bloc, aucune éviction notable. **C** : aucune empreinte, mais des tampons alignés et des tailles de bloc à respecter.

Choix : **B** si votre code d'écriture est simple et doit rester portable, **C** si vous maîtrisez l'alignement.

Mesure à faire : `resident MiB` et octets lus sur le périphérique avant et après (lab 1.3), car l'éviction se voit dans ces deux compteurs.
:::

::: exo
[Exercice 7 · ★★★ — Dimensionner les cgroups d'un nœud à huit GPU]{.tag} Un nœud a 1 Tio de mémoire, 128 processeurs logiques et 8 GPU. Huit jobs d'un GPU chacun s'y exécutent. Réservez 10 % de la mémoire au système et au cache de pages. Donnez pour chaque job `memory.max`, `memory.high` et `cpu.max` (cgroup v2), justifiez, et dites ce qui se passe si la somme des `memory.max` dépasse la mémoire disponible.
:::

::: sol
Mémoire des jobs : 1 024 × 0,9 = 921,6 Gio, soit 115,2 Gio par job ; on arrondit **à la baisse** à **115 Gio** (8 × 115 = 920 Gio, sous la réserve). `memory.max = 123480309760` octets (115 × 2^30). `memory.high` plus bas, par exemple **108 Gio** = `115964116992` octets, pour que le groupe soit **ralenti** avant d'être tué.

Processeurs : 128 / 8 = 16 par job, soit `cpu.max = 1600000 100000` (un quota de 1 600 000 µs par période de 100 000 µs, c'est-à-dire 16 cœurs) ; un `cpuset` épinglé sur le nœud NUMA du GPU (exercice 4) serait préférable pour la localité.

Si la somme des `memory.max` dépasse la mémoire disponible, les limites ne protègent plus : le noyau peut manquer de mémoire **avant** qu'un groupe n'atteigne la sienne, et l'OOM killer global choisira une victime parmi tous. Une limite n'est une garantie que si la somme des limites tient dans la machine.

Les valeurs de marge (10 %, 108 Gio) sont des choix d'exercice, à mesurer sur votre charge.
:::

::: exo
[Exercice 8 · ★★★ — Trois nœuds, une même plainte]{.tag} Trois nœuds exécutent le même job lent. `triage.py` renvoie (valeurs **fabriquées** au profil des mesures du lab 1.2). Nœud A : `cpu_util 0.97, cpu_psi 0.02, io_psi 0.00, disk_util 0.10`. Nœud B : `cpu_util 0.35, cpu_psi 0.01, io_psi 0.00, disk_util 0.93, disk_aqu_sz 6.3`. Nœud C : `cpu_util 0.12, cpu_psi 0.00, io_psi 0.43, disk_util 0.72, disk_aqu_sz 1.2`. Que conclut `classify` pour chacun, et quelle mesure ajoutez-vous à chacun pour trouver la cause du ralentissement ?
:::

::: sol
Exécution de `triage.classify` (lab 1.2) : **A** : « cpu: busy, but no task is waiting for a core ». **B** : « disk: busy, but no task stalls (asynchronous IO or a parallel device): look at latency ». **C** : « io: tasks are stalled waiting for the disk ».

Mesures suivantes. **A** : le processeur est occupé sans file ; le nœud n'est pas contendu, la question est l'efficacité du programme (profilage échantillonné, vitesse de pas comparée aux autres nœuds). 
**B** : la latence moyenne du disque (`iostat -x`, colonne d'attente) et la loi de Little, car PSI ne voit rien ; chercher des lectures ou écritures asynchrones profondes. 
**C** : lister les processus en état D (`ps -eo stat,wchan,cmd`) et chercher un écrivain synchrone, par exemple un checkpoint avec `fsync`.

Aucune de ces trois lectures ne prouve à elle seule quel nœud est « le lent » : comparez aussi le débit applicatif de chaque nœud.
:::

::: exo
[Exercice 9 · ★ — Une unité qui passe l'outil et échoue en production]{.tag} Le fichier `ex9.service` ci-dessous contient une valeur invalide pour `Restart=`. (a) Que renvoie `systemd-analyze verify ex9.service` ? (b) Quelle commande ou quel script mettez-vous en intégration continue pour la refuser ?

~~~ini
[Service]
ExecStart=/usr/bin/python3 -m http.server 9400
Restart=sometimes
~~~
:::

::: sol
(a) Il affiche `ex9.service:3: Failed to parse service restart specifier, ignoring: sometimes` et **retourne 0** (essayé avec systemd 255) : la valeur invalide est ignorée, le service serait lancé sans politique de redémarrage. (b) Le script `check_unit.sh` du lab 1.5 traite toute sortie comme un échec et retourne 1 ; équivalent en une ligne : `test -z "$(systemd-analyze verify unit.service 2>&1)"`. Le test du lab vérifie que `bad.service` est rejetée et `gpu-exporter.service` acceptée.
:::

::: exo
[Exercice 10 · ★ — Le coût d'une MTU basse]{.tag} On envoie 1 Gio (2^30 octets) de charge utile TCP, avec des en-têtes IPv4 et TCP de 20 octets chacun. Combien de segments et combien d'octets d'en-têtes pour une MTU de 1 400, puis de 9 000 ?
:::

::: sol
Charge utile par segment : 1 400 − 40 = 1 360 ; 9 000 − 40 = 8 960. Segments : $\lceil 2^{30} / 1360 \rceil =$ **789 517** et $\lceil 2^{30} / 8960 \rceil =$ **119 838** (calcul Python). En-têtes : 40 × 789 517 = **31 580 680 octets** (environ 30 Mio) contre 40 × 119 838 = **4 793 520 octets** (environ 4,6 Mio), soit 6,6 fois moins de segments à traiter. On ignore ici l'en-tête de trame de la couche liaison et les options TCP. Le gain n'existe que si **tout** le chemin accepte la grande MTU.
:::

::: exo
[Exercice 11 · ★★★ — Écrire `ensure_line.sh`]{.tag} Écrivez `ensure_line.sh FILE LINE` qui ajoute `LINE` à `FILE` si aucune ligne identique n'existe. Codes : 0 déjà présente, 10 ajoutée, 2 usage invalide. Contraintes : un fichier dont la dernière ligne n'a pas de retour à la ligne ne doit pas « avaler » la nouvelle ; une ligne plus longue qui **contient** `LINE` n'est pas une correspondance. Écrivez le test.
:::

::: sol
Solution de référence, fichier `labs/linux-systems/ops-script/solutions/ensure_line.sh` (testée, `shellcheck` propre) :

~~~bash
#!/usr/bin/env bash
set -euo pipefail
[ $# -eq 2 ] || { echo "usage: $0 FILE LINE" >&2; exit 2; }
file="$1"; line="$2"
if [ -e "$file" ] && grep -qxF -- "$line" "$file"; then
  exit 0
fi
if [ -s "$file" ] && [ "$(tail -c1 "$file" | wc -l)" -eq 0 ]; then
  printf '\n' >> "$file"
fi
printf '%s\n' "$line" >> "$file"
exit 10
~~~

`grep -x` impose la correspondance de ligne entière et `-F` désactive les expressions régulières ; `tail -c1 | wc -l` vaut 0 quand le dernier octet n'est pas un retour à la ligne. Le test `solutions/test_ensure_line.sh` couvre : fichier absent, second appel sans effet, ligne différente, une ligne par entrée, dernière ligne sans retour, ligne plus longue qui contient le texte, usage invalide : huit contrôles, tous « ok ».
:::

## Bilan de sortie {#exit}

Ce bilan n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux cartographier une machine.** Preuve : le rapport du lab 1.1 sur votre machine, avec la table de localité commentée.
-   **Je peux provoquer et lire une mise à mort par manque de mémoire.** Preuve : le lab 1.4 et l'explication de chaque champ de la ligne `oom-kill` (exemple 8.2).
-   **Je peux faire un triage USE.** Preuve : `triage.py` sur une charge de votre choix, avec la table USE remplie et l'angle mort de PSI expliqué.
-   **Je peux dire ce que touche une lecture ou une écriture.** Preuve : le tableau du lab 1.3 refait sur votre support, avec trois compteurs.
-   **Je peux vérifier une mesure d'E/S.** Preuve : la loi de Little appliquée à deux profondeurs de file (lab 1.3, partie B).
-   **Je peux écrire un script d'exploitation sûr.** Preuve : `ensure_line.sh` avec ses tests et ses codes de retour, `shellcheck` propre.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Un job d'entraînement est lent sur un nœud et pas sur les autres. Que faites-vous ?* Réponse-type : remplir la table USE du nœud (processeur, mémoire, disque, réseau, utilisation, saturation, erreurs) avec la pression PSI plutôt que la charge moyenne ; lire aussi l'occupation du disque pour ne pas tomber dans l'angle mort de PSI ; comparer le débit applicatif aux autres nœuds ; ne rien optimiser avant d'avoir une ressource désignée.
2.  *Un job disparaît sans message d'erreur. Comment trouvez-vous pourquoi ?* Réponse-type : le statut de sortie (137 indique `SIGKILL`) ; `dmesg` pour une ligne `oom-kill` dont `constraint=CONSTRAINT_MEMCG` désigne une limite de cgroup ; les compteurs `oom_kill` du cgroup ; ensuite seulement discuter la mémoire demandée et la marge.
3.  *Pourquoi un conteneur « n'a que 8 Go » mais un `VmSize` de 50 Go ?* Réponse-type : la mémoire virtuelle est réservée à la demande ; `VmRSS` et la limite du cgroup comptent la mémoire réellement présente ; une limite dure tue au lieu de ralentir, d'où `memory.high` plus bas que `memory.max`.

## Lectures et références {#refs}

Les pages web ci-dessous ont été consultées le 2026-10-24 ; la documentation du noyau et les pages man7 sont mises à jour en continu et n'ont donc pas d'année de publication propre.

-   Brendan Gregg. [*The USE Method*](https://www.brendangregg.com/usemethod.html) : la méthode du chapitre 4 ; du même auteur, *Systems Performance*, 2e édition, Addison-Wesley, 2020, ouvrage de référence sur le sujet.
-   Noyau Linux. [*PSI — Pressure Stall Information*](https://docs.kernel.org/accounting/psi.html) : les lignes `some` et `full` (chapitre 4).
-   Noyau Linux. [*Control Group v2*](https://docs.kernel.org/admin-guide/cgroup-v2.html) et [*Memory Resource Controller (v1)*](https://docs.kernel.org/admin-guide/cgroup-v1/memory.html) : limites, `memory.events`, `memory.oom_control` (chapitre 2).
-   man7. [*cgroups(7)*](https://man7.org/linux/man-pages/man7/cgroups.7.html) et [*namespaces(7)*](https://man7.org/linux/man-pages/man7/namespaces.7.html) : v1, v2, hybride, les huit espaces de noms (chapitre 2).
-   Noyau Linux. [*NUMA memory policy*](https://docs.kernel.org/admin-guide/mm/numa_memory_policy.html) : politique d'allocation par défaut (chapitre 3).
-   Noyau Linux. [*sysctl vm*](https://docs.kernel.org/admin-guide/sysctl/vm.html) et [*Transparent Hugepage Support*](https://docs.kernel.org/admin-guide/mm/transhuge.html) : paramètres `vm.*` et THP (chapitre 5).
-   freedesktop.org. [*systemd-analyze*](https://www.freedesktop.org/software/systemd/man/latest/systemd-analyze.html) et [*systemd.exec*](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html) : vérification hors ligne et limites (chapitre 5).
-   Open MPI. [*FAQ — OpenFabrics*](https://www.open-mpi.org/faq/?category=openfabrics) : limites `memlock` pour InfiniBand (chapitres 5 et 6).
-   man7. [*open(2)*](https://man7.org/linux/man-pages/man2/open.2.html), [*posix_fadvise(2)*](https://man7.org/linux/man-pages/man2/posix_fadvise.2.html), [*mincore(2)*](https://man7.org/linux/man-pages/man2/mincore.2.html) : `O_DIRECT`, `DONTNEED`, pages résidentes (chapitre 7).
-   Noyau Linux. [*EDAC*](https://docs.kernel.org/driver-api/edac.html) : compteurs d'erreurs mémoire (chapitre 8).
-   NVIDIA. [*XID Errors*](https://docs.nvidia.com/deploy/xid-errors/index.html) : format des messages et catalogue des codes (chapitre 8).
-   SchedMD. [*cgroup.conf*](https://slurm.schedmd.com/cgroup.conf.html) : Slurm et les cgroups (chapitre 2).

## Sources et portée {#sources}

### Documenté {#documente}

Les définitions de PSI, de la méthode USE, de `memory.max`, `memory.high` et `cpu.max`, des espaces de noms, de la charge moyenne, de `RLIMIT_MEMLOCK`, des paramètres `vm.*`, de `O_DIRECT`, `DONTNEED` et `mincore`, de la THP, du format des messages Xid, des options `cgroup.conf` de Slurm, des limites mémoire et du gestionnaire de processeurs de Kubernetes, de `journalctl -k`, de `sar`, des ponts PCI de hwloc, d'ext4 et de XFS viennent des pages citées, lues pour ce module. Toutes les sorties de commande marquées « capturé » viennent de la machine du bac à sable (machine virtuelle Linux 6.18.44, Ubuntu 24.04, 4 processeurs ; outils testés le 2026-10-24 : systemd 255, fio 3.36, stress-ng 0.17.06, iperf3 3.16, util-linux 2.39.3, procps-ng 4.0.4, ShellCheck 0.9.0 ; le 2026-10-25 : hwloc 2.10.0, sysstat 12.6.1, Python 3.13) ; les valeurs numériques des exemples et des exercices ont été recalculées en Python.

### Recommandé {#recommande}

La table USE du chapitre 4, le code de retour 3 pour « non observable », les cinq règles du script d'exploitation, le choix de `memory.high` sous `memory.max` et l'ordre des chapitres sont des choix de cours, pas des normes.

### À vérifier {#a-verifier}

Le comportement de PSI `io` sous E/S asynchrones profondes a été constaté **sur ce disque virtuel et ce noyau** seulement. La branche cgroup v2 du lab 1.4 n'a pas été exécutée. Le serveur à deux sockets du lab 1.1 est fabriqué. Les extraits `vmstat` de l'exercice 2 et les valeurs de l'exercice 8 sont fabriqués. La mise à jour de EEVDF depuis le noyau 6.6 est celle que décrit la documentation du noyau : lisez-la pour votre version. Que `systemd-analyze verify` retourne 0 sur un avertissement a été constaté avec systemd 255 seulement. L'écart de vitesse entre lecture à froid et à chaud du lab 1.3 (rapport 2,5) et son explication par un cache de l'hôte sont une hypothèse. Le code de classe PCI d'une carte RDMA configurée en Ethernet (RoCE), que le lab 1.1 classerait comme `ethernet`, n'a pas été vérifié. Les labs 1.2 et 1.3 lisent des compteurs de toute la machine ou de tout le disque : sur une machine partagée, une autre charge peut les faire échouer ; deux exécutions consécutives de chaque `verify.sh` ont réussi lors de la revue, ce qui ne prouve pas la robustesse.

### Hors périmètre {#hors-perimetre}

`perf`, les graphes de flammes et `bpftrace` (non installés dans le bac à sable, décrits sans sortie), XFS (non outillé, décrit sans sortie), l'historique de `sar` et le contenu du journal de systemd (collecte absente dans le bac à sable), `tc netem` (module absent de ce noyau), les lectures SMART, EDAC et BMC réelles (absentes en machine virtuelle), `nvidia-smi topo -m` et les messages Xid réels (aucun GPU), le réglage fin du noyau et l'administration d'un système de fichiers parallèle.
