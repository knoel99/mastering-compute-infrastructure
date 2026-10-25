---
title: "Slurm et exploitation d'un cluster HPC"
subtitle: "Module 05 · Phase 2 · 32 h"
description: "L'ordonnanceur de référence du calcul scientifique et de l'entraînement : jobs, politique d'équité, préemption, GPU et topologie, comptabilité, santé des nœuds."
module:
  id: slurm
  number: 5
  phase: 2
  hours: 32
  level: 2
prerequisites: [linux-systems]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs vérifiés sur un vrai Slurm 23.11", class: verified}
labs:
  - {id: slurm-sandbox, kind: sandbox}
  - {id: fairshare-qos, kind: sandbox}
  - {id: node-health, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** comment partager équitablement et efficacement quelques centaines de GPU entre des équipes qui ne s'entendent pas toujours, sans qu'un job oublié ne bloque un entraînement de deux semaines ? Slurm est la réponse la plus répandue dans les centres de calcul et chez de nombreux fournisseurs de GPU.

Ce module vous apprend à **lire** un cluster Slurm (états, raisons d'attente, comptabilité), à **écrire** des jobs corrects, à **configurer** une politique (partitions, équité, préemption) et à **exploiter** les nœuds (GPU, santé, conteneurs). Tout est vérifié sur un vrai Slurm 23.11 lancé dans un bac à sable, pas sur des exemples écrits de mémoire.

::: key
[Règle de ce module]{.tag} Un ordonnanceur est un contrat social écrit en configuration. Chaque paramètre répond à la question « qui passe en premier quand tout le monde veut la même chose ? ». Si vous ne savez pas formuler la réponse en une phrase, ne touchez pas au paramètre.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 32 h, dont environ 12 h de lecture, 10 h de labs et 10 h d'exercices, de synthèse et de checkpoint |
| Niveau d'entrée | 2 : à l'aise avec Linux en ligne de commande (module 1) |
| Prérequis | [Module 1 — Linux, systèmes et diagnostic](../linux-systems/index.html) |
| Statut pour le lecteur de référence | cœur : aucune expérience de Slurm dans le profil, écart de 3 sur 4 |
| Livrable | un Slurm de test reproductible par script, avec comptes, QOS, préemption et vérification de santé |
| Environnement | une VM ou un conteneur Linux jetable avec accès root ; aucun GPU |
| Projets liés | [Projet 1 — Mini-cluster Slurm instrumenté](../../projects/homelab-slurm/index.html), [Projet 6 — RFC de plateforme](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Écrire et soumettre des jobs en lot, des tableaux et des chaînes de dépendances avec des ressources GPU (chapitres 1 et 2).
-   Lire une file d'attente et expliquer pourquoi un job attend (chapitres 1 et 3).
-   Configurer partitions, comptes, QOS, équité et préemption pour une politique donnée (chapitres 3 et 4).
-   Décrire la configuration d'un nœud GPU et une topologie réseau pour le placement (chapitre 5).
-   Mesurer l'utilisation d'un cluster avec `sacct` et `sreport` (chapitre 6), et lire l'équité avec `sshare` (chapitre 3).
-   Diagnostiquer et mettre en quarantaine un nœud défaillant, automatiquement (chapitre 7).
-   Situer Slurm face aux conteneurs et à Kubernetes (chapitre 8).

### Plan de séances {#seances}

Douze séances, soit 32 h : huit de 3 h et quatre de 2 h. Le niveau ne diminue jamais d'une séance à la suivante.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 3 h | 1 | ch. 1 Architecture et vie d'un job | Ex. 1 ; questions de positionnement |
| 2 | 3 h | 1 | ch. 2 Soumettre des jobs, première moitié | Lab 5.1 partie A |
| 3 | 2 h | 1 | ch. 2 Tableaux, dépendances, scripts robustes | Lab 5.1 partie B ; Ex. 2, 3 |
| 4 | 3 h | 2 | ch. 3 Partitions, associations, QOS, priorité | Ex. 4 |
| 5 | 3 h | 2 | ch. 3 Équité (Fair Tree) et backfill | Lab 5.2 partie A ; Ex. 5, 6 |
| 6 | 2 h | 2 | ch. 4 Préemption, réservations, limites | Lab 5.2 partie B |
| 7 | 3 h | 2 | ch. 5 GPU et topologie | Ex. 7 |
| 8 | 2 h | 2 | ch. 6 Comptabilité et reporting | Ex. 8 |
| 9 | 3 h | 3 | ch. 7 Santé des nœuds | Lab 5.3 partie A |
| 10 | 3 h | 3 | ch. 7 suite, ch. 8 Conteneurs | Lab 5.3 partie B ; Ex. 9 |
| 11 | 3 h | 3 | ch. 8 Slurm sur Kubernetes, synthèse | Ex. 10 |
| 12 | 2 h | 3 | Checkpoint de sortie, démarrage du Projet 1 | |

## Avant de commencer {#avant}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si elles vous semblent routinières, parcourez les exercices ★★★ et passez au module 6.

1.  **Trois commandes.** Quelle différence entre `sbatch`, `srun` et `salloc` ?

2.  **Équité.** Deux équipes partagent un cluster. L'équipe A a consommé beaucoup de GPU-heures ce mois-ci, l'équipe B presque rien. Quel mécanisme de Slurm fait passer B devant A, et de quelles données dépend-il ?

3.  **Durée déclarée.** Pourquoi faut-il déclarer pour chaque job une durée limite réaliste plutôt que la plus grande possible ?

::: sol
**Réponses.**

1.  `sbatch` dépose un script qui s'exécutera plus tard, quand les ressources seront libres. `srun` lance une commande en parallèle ; dans une allocation existante elle crée une *étape* du job, en dehors elle demande une allocation puis attend. `salloc` obtient une allocation et ouvre un shell dans celle-ci. Voir les chapitres 1 et 2.

2.  Le mécanisme est l'**équité** (*fairshare*) : la priorité d'un job dépend de la part de ressources promise à son compte et de la consommation récente de ce compte, mesurée par la comptabilité et atténuée au cours du temps. Voir le chapitre 3.

3.  Le *backfill* fait passer devant un petit job seulement s'il ne retarde pas le job prioritaire, ce qu'il juge sur la durée déclarée. Une limite trop grande empêche le comblement des trous ; une limite trop petite fait tuer le job. Voir le chapitre 3 et l'exercice 6.
:::

## 1. Architecture et vie d'un job {#ch1}

Avant de configurer quoi que ce soit, il faut pouvoir lire l'état d'un cluster. Ce chapitre présente les pièces de Slurm et le cycle de vie d'un job, avec des sorties réelles du bac à sable du module.

### 1.1. Les démons

Un cluster Slurm est fait de quelques démons qui se parlent par un canal authentifié.

-   **`slurmctld`** est le contrôleur : il tient l'état de tous les nœuds et jobs, décide de l'ordonnancement et répond aux commandes des utilisateurs.
-   **`slurmd`** tourne sur chaque nœud de calcul : il lance les jobs, les surveille et rapporte l'état du nœud.
-   **`slurmdbd`** écrit la comptabilité dans une base de données (MariaDB dans notre bac à sable). Il est facultatif pour exécuter des jobs, mais indispensable à l'équité, aux limites par compte et aux rapports.
-   **`munge`** authentifie les échanges : tous les nœuds partagent une clé secrète.

Un démon de plus, `slurmrestd`, expose une API REST ; nous ne l'utiliserons pas ici.

::: note
[Un constat de ce module : sans association, le job est refusé]{.tag} Dans le bac à sable (Slurm 23.11.4), avec `AccountingStorageEnforce=associations,limits,qos`, un utilisateur sans association est refusé dès la soumission :

~~~text
$ sbatch --wrap='hostname'
sbatch: error: Batch job submission failed: Invalid account or account/partition combination specified
~~~

C'est pourquoi `labs/slurm/slurm-sandbox/setup.sh` installe MariaDB et `slurmdbd`, puis crée un compte et y rattache `root`. La base n'est pourtant pas indispensable pour *exécuter* un job : avec `AccountingStorageType=accounting_storage/none` et sans `AccountingStorageEnforce`, un job soumis par `root` s'exécute aussitôt. Ces deux essais datent du 25 octobre 2026. La raison d'attente `InvalidAccount` du tableau ci-dessous, documentée dans `squeue`, n'a pas pu être reproduite sur ce bac à sable : elle figure dans les points à vérifier.
:::

### 1.2. Les entités

-   Un **cluster** regroupe des nœuds sous un contrôleur.
-   Une **partition** est un groupe de nœuds avec des limites et une politique propres, qu'on peut voir comme une file d'attente.
-   Un **job** est une demande de ressources suivie d'un programme à exécuter. Une **étape** (*step*) est un lancement parallèle dans un job, créé par `srun`.
-   Les ressources suivies s'appellent des **TRES** (*trackable resources*) : processeurs, mémoire, nœuds, et GRES (*generic resources*) comme les GPU.
-   Une **association** relie un cluster, un compte, un utilisateur et éventuellement une partition ; c'est sur elle que portent les parts d'équité et les limites.

### 1.3. Le cycle de vie d'un job

Un job passe par des états que `squeue` et `sacct` affichent. Les principaux : `PENDING` (en attente), `RUNNING`, `COMPLETING` (en nettoyage), puis un état final comme `COMPLETED`, `FAILED`, `CANCELLED`, `TIMEOUT`, `NODE_FAIL`, `PREEMPTED` ou `OUT_OF_MEMORY`.

Un job en `PENDING` porte une **raison**, la clé du diagnostic. La documentation de `squeue` en donne la liste ; les plus utiles à connaître :

| Raison | Sens |
|---|---|
| `Priority` | un ou plusieurs jobs de priorité supérieure existent pour cette partition ou cette réservation |
| `Resources` | le job attend que les ressources demandées se libèrent |
| `Dependency` | le job dépend d'un autre job qui n'a pas terminé comme demandé |
| `BeginTime` | l'heure de début au plus tôt n'est pas atteinte (observé aussi sur un job remis en file, exemple 4.1) |
| `ReqNodeNotAvail` | un nœud explicitement demandé n'est pas disponible |
| `PartitionTimeLimit` | la durée demandée dépasse la limite de la partition |
| `JobHeldUser` | le job est retenu par son propriétaire |
| `InvalidAccount` | le compte du job n'est pas valide |

Une raison de la famille `Assoc…Limit` (par exemple `AssocGrpCpuLimit`, observée dans le bac à sable avec un quota `GrpTRES=cpu=2` et un job de 3 processeurs) signale qu'une limite attachée à l'association du job est atteinte : la file n'est pas pleine, c'est la politique qui retient.

::: ex
[Exemple 1.1 — Lire l'état d'un nœud et d'un job]{.tag} Voici les sorties réelles du bac à sable après le démarrage de `setup.sh` (une machine à 4 processeurs) puis l'exécution du lab 5.1.

~~~text
$ sinfo
PARTITION AVAIL  TIMELIMIT  NODES  STATE NODELIST
debug*       up   infinite      1   idle vm

$ sacct -X --format=JobID%14,JobName%10,State%10,Elapsed
         JobID    JobName      State    Elapsed
-------------- ---------- ---------- ----------
             2       wrap  COMPLETED   00:00:00
           1_1      hello  COMPLETED   00:00:01
           1_2      hello  COMPLETED   00:00:01
           1_3      hello  COMPLETED   00:00:02
~~~

La partition `debug` (l'étoile signale la partition par défaut) a une limite de temps infinie et un nœud `idle`. Les trois jobs `1_1` à `1_3` sont les tâches d'un **tableau** (`--array`), le job `2` est un job isolé. `sacct` lit la base de comptabilité : il retrace les jobs même après leur disparition de `squeue`.
:::

::: recap
Points clés — chapitre 1

-   `slurmctld` décide, `slurmd` exécute, `slurmdbd` mémorise, `munge` authentifie.
-   Un cluster se lit par partitions, nœuds, jobs, étapes et associations ; les ressources suivies sont des TRES.
-   Un job `PENDING` a toujours une raison : c'est le premier réflexe de diagnostic.
-   Sans `slurmdbd`, un job s'exécute mais il n'y a ni équité, ni limites par compte, ni rapports ; avec `AccountingStorageEnforce=associations`, un utilisateur sans association est refusé.
:::

## 2. Soumettre des jobs {#ch2}

Écrire un script de soumission paraît trivial. Les jobs qui coûtent cher en pratique sont pourtant ceux dont le script ignore la façon dont l'ordonnanceur les arrête et les relance.

### 2.1. Les trois commandes

-   **`sbatch script`** dépose un script ; les options `#SBATCH` du script sont les options de la ligne de commande. Le job tourne plus tard, sa sortie va dans un fichier.
-   **`srun commande`** lance une commande en parallèle. Dans un script `sbatch`, chaque `srun` crée une étape ; seul, il demande une allocation et attend.
-   **`salloc`** obtient une allocation interactive et ouvre un shell dedans, utile pour déboguer sur les mêmes machines que l'entraînement.

### 2.2. Demander des ressources

Les options de ressources les plus utiles à retenir sont celles de la documentation de `sbatch` :

-   `--nodes=N` et `--ntasks-per-node=M` : nombre de nœuds et de tâches par nœud ;
-   `--cpus-per-task=C` : processeurs par tâche, à fixer pour les chargeurs de données multi-processus ;
-   `--mem=M` : mémoire par nœud (`--mem=0` demande toute la mémoire du nœud) ;
-   `--gpus-per-node=[type:]N` ou `--gres=gpu:[type:]N` : GPU par nœud ; `-G` / `--gpus` compte à l'échelle du job ;
-   `--exclusive` : le job ne partage pas ses nœuds ;
-   `--time=D-HH:MM:SS` : durée limite, dont le chapitre 3 explique l'importance.

Pour un entraînement distribué, la règle est de **demander des nœuds entiers**, avec toutes leurs ressources, plutôt que des fractions : le réseau, le NUMA et le bruit des voisins rendent les placements partiels imprévisibles.

::: ex
[Exemple 2.1 — Un entraînement sur deux nœuds de huit GPU]{.tag} Le script `labs/slurm/slurm-sandbox/examples/train_multinode.sbatch` demande deux nœuds exclusifs de huit GPU, lance un `torchrun` par nœud avec un point de rendez-vous sur le premier nœud, et prévoit la reprise :

~~~bash
#!/usr/bin/env bash
#SBATCH --job-name=train-70b
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --cpus-per-task=96
#SBATCH --mem=0
#SBATCH --exclusive
#SBATCH --time=12:00:00
#SBATCH --signal=B:USR1@300
#SBATCH --requeue
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
head_node="$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)"
export OMP_NUM_THREADS=8
srun --kill-on-bad-exit=1 \
  torchrun --nnodes="$SLURM_NNODES" --nproc_per_node=8 \
           --rdzv_backend=c10d --rdzv_endpoint="${head_node}:29500" --rdzv_id="$SLURM_JOB_ID" \
           train.py --config config.yaml --resume-latest
~~~

Ce script a passé `shellcheck` mais n'a **pas** été exécuté ici : il demande des GPU. Les valeurs (96 processeurs par tâche, huit threads OpenMP, port 29500) sont des exemples à adapter. L'option `--kill-on-bad-exit=1` fait arrêter tout le job quand un rang tombe, plutôt que de laisser les autres bloqués dans une collective.
:::

### 2.3. Tableaux et dépendances

Un **tableau de jobs** (`--array=1-100`) soumet cent jobs presque identiques d'un coup ; chacun lit sa variable `SLURM_ARRAY_TASK_ID`. Le suffixe `%10` limite la concurrence : `--array=1-100%10` n'en laisse jamais plus de dix en cours. Les tableaux sont le bon outil pour un balayage d'hyperparamètres ou le traitement de milliers de fichiers, et un mauvais outil pour un job unique long.

Les **dépendances** chaînent des jobs : `--dependency=afterok:ID` attend que le job `ID` se soit terminé avec succès, `afterany` attend sa fin quelle qu'elle soit, `singleton` n'autorise qu'un job du même nom à la fois. Le lab 5.1 chaîne ainsi un traitement final après un tableau.

### 2.4. Écrire un script qui survit à Slurm

Slurm arrête les jobs : dépassement de durée, préemption, panne de nœud, annulation. Un script robuste prévoit ces cas.

1.  **Mettez `set -euo pipefail`** en tête : une erreur silencieuse en milieu de script ne doit pas produire un succès apparent.
2.  **Demandez un signal avant la fin.** `--signal=B:USR1@300` envoie `SIGUSR1` au shell du script environ 300 secondes avant la limite de durée (`B:` limite l'envoi au shell du script ; la documentation précise que le signal peut partir jusqu'à 60 secondes plus tôt). Le script le transmet au programme, qui sauvegarde son état.
3.  **Autorisez la remise en file** avec `--requeue` : Slurm relance alors le job depuis le début de son script, et c'est votre programme qui doit reprendre à son dernier point de sauvegarde.
4.  **Écrivez de façon atomique.** Un checkpoint écrit dans un fichier temporaire puis renommé ne laisse jamais un fichier à moitié écrit.

::: ex
[Exemple 2.2 — Un entraîneur qui sauvegarde sur signal et reprend]{.tag} Le script `examples/trainer.py` du lab 5.1 simule un entraînement : il compte des étapes, sauvegarde dans un fichier JSON quand il reçoit `SIGUSR1`, et reprend depuis ce fichier au démarrage suivant.

~~~python
def save(step):
    tmp = CKPT + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"step": step}, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, CKPT)  # atomic: a crash never leaves a half-written checkpoint
~~~

Le script `checkpoint_on_signal.sbatch` transmet le signal du shell au programme et attend vraiment la fin de celui-ci : `wait` revient dès qu'un signal intercepté arrive (avec un statut supérieur à 128), d'où la boucle qui vérifie avec `kill -0` que le programme a bien disparu, puis la sortie avec **son** code de retour.

Deux pièges réels, tous deux rencontrés en écrivant ce lab. Premier piège : Slurm exécute une **copie** du script depuis son répertoire d'attente, de sorte que `${BASH_SOURCE[0]}` ne désigne plus votre dépôt ; on utilise `SLURM_SUBMIT_DIR`, qui est le répertoire d'où `sbatch` a été lancé (et non celui de `--chdir`). Second piège : une première version du script avalait le code de retour, et le job affichait `COMPLETED 0:0` alors que Python n'avait même pas trouvé son fichier. Un job qui échoue doit finir en échec.

`verify.sh` le contrôle en lançant le script depuis un répertoire sans `trainer.py` : l'état attendu est `FAILED` avec `ExitCode 2:0`.

Le lab 5.1 envoie `scancel --signal=USR1 --batch` et vérifie que le checkpoint existe, puis que le job suivant reprend à l'étape sauvegardée.
:::

::: recap
Points clés — chapitre 2

-   `sbatch` dépose, `srun` lance une étape, `salloc` ouvre une allocation interactive.
-   Un entraînement distribué demande des nœuds entiers, exclusifs, avec leurs GPU et leur mémoire.
-   Tableaux (`--array`, `%N` pour limiter) et dépendances (`afterok`, `afterany`) chaînent les jobs.
-   Un script robuste : `set -euo pipefail`, `--signal` avant la fin, `--requeue`, checkpoint atomique.
:::

## 3. Partitions, comptes, QOS et priorité {#ch3}

Ce chapitre répond à la question centrale d'un ordonnanceur : quand tout le monde veut la même chose, qui passe en premier ? La réponse se construit en quatre couches : où tourne un job (partition), pour qui il tourne (association), selon quelles règles (QOS) et avec quelle priorité.

### 3.1. Partitions

Une **partition** est un groupe de nœuds avec ses propres limites, notamment une durée maximale. Les utilisateurs soumettent à une partition, et un nœud peut appartenir à plusieurs. Une partition d'entraînement et une partition de développement n'ont pas les mêmes limites de durée : une heure pour le développement garantit que quelqu'un peut déboguer sans attendre une semaine.

Une règle d'exploitation, issue de l'expérience et non de la documentation : **évitez de multiplier les partitions**. Chaque partition est une file séparée et morcelle la capacité : des nœuds libres dans l'une ne servent pas une demande bloquée dans l'autre. Préférez des QOS pour distinguer les politiques, et réservez les partitions aux différences matérielles (types de GPU).

### 3.2. Associations : l'organigramme dans la base

La comptabilité organise les utilisateurs en arbre : un **cluster** contient des **comptes**, qui contiennent des sous-comptes et des **utilisateurs**. Chaque feuille est une *association*, c'est elle qui porte les parts d'équité et les limites. On gère l'arbre avec `sacctmgr`.

~~~bash
sacctmgr -i add account teama parent=research fairshare=1
sacctmgr -i add account teamb parent=research fairshare=1
sacctmgr -i add user alice account=teama
~~~

La valeur `fairshare=N` est le nombre de **parts** promises au compte, relativement à ses frères. Le paramètre `AccountingStorageEnforce=associations,limits,qos` rend ces règles obligatoires : sans lui, qui est la valeur par défaut, la documentation précise que les limites ne sont pas appliquées. C'est le piège classique d'un cluster où « les limites ne marchent pas » : on les a déclarées sans les faire respecter.

::: note
[Slurm met les noms de compte en minuscules]{.tag} En créant un compte `TeamA` dans le lab 5.2, on constate que Slurm l'enregistre sous le nom `teama`. Notez-le dans vos scripts : une comparaison de chaînes sensible à la casse sur un nom de compte échoue silencieusement.
:::

### 3.3. QOS : un jeu de règles nommé

Une **QOS** (*quality of service*) regroupe une priorité, des limites et une règle de préemption sous un nom, qu'un job réclame avec `--qos=` et qu'un utilisateur n'obtient que si son association l'y autorise.

~~~bash
sacctmgr -i add qos urgent Priority=1000 Preempt=normal
sacctmgr -i modify user alice set qos+=urgent
~~~

Cette QOS `urgent` a une priorité élevée et peut préempter les jobs de la QOS `normal` (chapitre 4). Les limites s'expriment par des paramètres comme `GrpTRES`, `MaxTRESPerUser`, `MaxJobs` ou `MaxWall`, que la page « Resource Limits » de la documentation décrit en détail.

### 3.4. La priorité multifactorielle

Avec `PriorityType=priority/multifactor`, la priorité d'un job est une somme pondérée de facteurs, chacun compris entre 0 et 1. La documentation donne la formule :

$$\text{priorité} = \text{site} + W_{\text{âge}}\,f_{\text{âge}} + W_{\text{assoc}}\,f_{\text{assoc}} + W_{\text{équité}}\,f_{\text{équité}} + W_{\text{taille}}\,f_{\text{taille}} + W_{\text{partition}}\,f_{\text{partition}} + W_{\text{QOS}}\,f_{\text{QOS}} + \text{TRES} - \text{nice}$$

Chaque poids $W$ se règle par un paramètre `PriorityWeight…` de `slurm.conf`. La commande `sprio -w` affiche les poids en vigueur, `sprio -j ID` les facteurs d'un job donné. Le choix des poids **est** la politique : mettre un poids énorme sur l'équité rend le cluster équitable mais impatient, un poids sur l'âge évite qu'un job attende indéfiniment.

::: ex
[Exemple 3.1 — De l'équité à la priorité]{.tag} Dans le lab 5.2, le poids de l'équité est $W_{\text{équité}} = 10\,000$. Un job du compte peu actif obtient un facteur d'équité de 0,75 et un job du compte gros consommateur 0,25. Leurs priorités sont donc $10\,000 \times 0{,}75 = 7500$ et $10\,000 \times 0{,}25 = 2500$, ce que `sprio` affiche :

~~~text
$ sprio -o "%i %o %Y %f" -j 10,11
JOBID ACCOUNT PRIORITY FAIRSHARE
10    teama   2500     0.2500000
11    teamb   7500     0.7500000
~~~

Quand un nœud se libère, c'est le job 11, de priorité 7 500, qui démarre en premier, bien qu'il ait été soumis après le job 10.
:::

### 3.5. L'équité : Fair Tree

Pour chaque association, Slurm suit la consommation de ressources (en CPU-secondes ou en TRES), **atténuée dans le temps** : la demi-vie `PriorityDecayHalfLife` vaut 7 jours par défaut, de sorte que la consommation d'il y a une semaine compte moitié moins. Le contrôleur recalcule ces valeurs toutes les `PriorityCalcPeriod` minutes, 5 par défaut.

Depuis Slurm 19.05, l'algorithme par défaut est **Fair Tree**. Au lieu de calculer un facteur pour chaque utilisateur isolément, il compare des frères entre eux : si le compte A a un meilleur *Level FS* que son frère B, tous les enfants de A passent devant tous les enfants de B, à chaque niveau de l'arbre. Un *Level FS* supérieur à 1 signale une association sous-servie, entre 0 et 1 une association sur-servie ; il est infini pour une association sans consommation.

::: ex
[Exemple 3.2 — Lire sshare]{.tag} Après que huit jobs de 4 secondes du compte `teama` ont consommé 36 secondes de CPU (38 dans une autre exécution : le décompte varie de quelques secondes) et ceux de `teamb` rien, `sshare -l` affiche (extrait réel du lab 5.2, deux comptes de parts égales sous un même parent) :

~~~text
Account   User  NormShares  RawUsage  NormUsage  EffectvUsage  LevelFS  FairShare
teama           0.333333        36   1.000000      1.000000  0.333333
 teama  root    1.000000        36   1.000000      1.000000  1.000000  0.250000
teamb           0.333333         0   0.000000      0.000000       inf
 teamb  root    1.000000         0   0.000000      0.000000       inf  0.750000
~~~

`RawUsage` est la consommation en CPU-secondes, `NormUsage` sa part normalisée parmi les frères : `teama` en a consommé 100 %.

Les parts normalisées valent 0,333 et non 0,5 parce que le compte parent `research` a un troisième enfant, l'utilisateur `root` que `setup.sh` y rattache avec la même part par défaut (1) : `sacctmgr show assoc format=cluster,account,user,share` le montre.

Le *Level FS* d'une association vaut ici sa part normalisée divisée par sa consommation normalisée : $0{,}333/1{,}0 = 0{,}333$ pour le compte `teama`, supérieur à 1 pour une association sous-servie, et infini pour `teamb` qui n'a rien consommé, comme l'annonce la documentation. Le facteur d'équité est un **classement** : `teamb` obtient 0,75 et `teama` 0,25, d'où les priorités de l'exemple précédent.

Le lab 5.2 attend que `PriorityCalcPeriod` (réglé à une minute) rafraîchisse ces chiffres avant de soumettre ses jobs de comparaison.
:::

### 3.6. Le backfill

Sans *backfill*, chaque partition est servie strictement par ordre de priorité : si le premier job attend 64 nœuds, les petits jobs derrière lui attendent aussi, même si des nœuds restent libres. Le plugin `sched/backfill`, chargé par défaut d'après la documentation, démarre des jobs de moindre priorité **si cela ne retarde pas la date de début prévue des jobs plus prioritaires**.

Il ne peut le juger que sur les durées déclarées : « des limites de temps raisonnablement exactes sont importantes pour que le backfill fonctionne bien », dit la documentation. Un job sans durée précise ne peut pas combler un trou, un job avec une durée trop courte est tué.

::: key
[Déclarez la durée la plus juste, pas la plus grande]{.tag} Une durée gonflée « pour être tranquille » retarde votre propre job (il ne peut combler aucun trou) et les autres. Une durée trop serrée le fait tuer. Mesurez la durée réelle de vos jobs avec `sacct`, ajoutez 20 à 30 % de marge, et utilisez `--signal` (chapitre 2) pour sauvegarder avant la limite.
:::

::: recap
Points clés — chapitre 3

-   Partition : où et avec quelles limites ; peu de partitions, plusieurs QOS.
-   Association : l'arbre cluster, compte, utilisateur porte les parts et les limites ; `AccountingStorageEnforce` les rend effectives.
-   QOS : priorité, limites et préemption sous un nom.
-   Priorité : somme pondérée de facteurs entre 0 et 1 ; les poids sont la politique.
-   Équité Fair Tree : classement par parts et consommation atténuée ; `sshare` et `sprio` la montrent.
-   Backfill : comble les trous sans retarder le prioritaire, à condition de déclarer des durées justes.
:::

## 4. Préemption, réservations et limites {#ch4}

Ce chapitre traite les cas où la politique « premier par priorité » ne suffit pas : une urgence qui doit passer maintenant, une maintenance planifiée, un compte qui ne doit pas dépasser un quota.

### 4.1. La préemption par QOS

La **préemption** libère des ressources en interrompant un job moins prioritaire. Deux paramètres de `slurm.conf` la configurent : `PreemptType` choisit le critère (ici `preempt/qos`, la QOS d'un job décide s'il peut en préempter un autre) et `PreemptMode` choisit le mécanisme.

| `PreemptMode` | Ce qui arrive au job préempté |
|---|---|
| `REQUEUE` | il est remis en file s'il est « requeueable », annulé sinon |
| `CANCEL` | il est annulé |
| `SUSPEND,GANG` | il est suspendu puis repris, en partageant les ressources par tranches de temps |

Avec `preempt/qos`, `PreemptMode` peut aussi se fixer par QOS. Le paramètre `GraceTime` d'une QOS ou d'une partition donne au job préempté un délai pour finir proprement : c'est le moment de sauvegarder (voir le chapitre 2). Retenez la règle de fond : **la préemption n'a de sens que si les jobs préemptibles savent reprendre**. Un entraînement qui ne sait pas reprendre depuis un checkpoint perd tout son travail à chaque préemption.

::: ex
[Exemple 4.1 — Un job urgent préempte un job normal]{.tag} Le lab 5.2, partie B, occupe les quatre processeurs avec un job `normal` de 120 secondes, puis soumet un job `urgent` d'un processeur. Observation réelle sur Slurm 23.11 :

~~~text
$ squeue -o "%i %q %T %r"
JOBID QOS    STATE   REASON
12    normal PENDING BeginTime
13    urgent RUNNING None

$ scontrol show job 12 | grep -E 'JobState|Restarts'
   JobState=PENDING Reason=BeginTime Dependency=(null)
   Requeue=1 Restarts=1 BatchFlag=1 Reboot=0 ExitCode=0:0
$ sacct -X -n -j 12 --format=JobID,State
12            PREEMPTED
~~~

Le job urgent a démarré aussitôt. Le job normal a été **préempté puis remis en file** : `sacct` garde la trace `PREEMPTED` de son premier passage, `Restarts=1` compte la remise en file, et sa raison d'attente `BeginTime` s'explique par un délai avant la reprise. Si ce job ne savait pas reprendre depuis un checkpoint, il repartirait de zéro.
:::

### 4.2. Les réservations

Une **réservation** retire des nœuds du pool pour une période donnée : maintenance planifiée, démonstration, fenêtre dédiée à une équipe. La documentation donne l'exemple d'une maintenance de deux heures sur tous les nœuds :

~~~bash
scontrol create reservation starttime=2026-11-06T16:00:00 \
  duration=120 user=root flags=maint,ignore_jobs nodes=ALL
~~~

La durée est en minutes. Par construction, Slurm ne lance pas un job dont la durée déclarée chevaucherait le début de la réservation : c'est la même logique que le backfill du chapitre 3, et la raison pour laquelle des jobs « en attente avec des nœuds libres » avant une maintenance sont normaux (comportement usuel, non relu sur la page « Reservations » : voir les points à vérifier).

### 4.3. Les limites

Les limites s'attachent aux associations et aux QOS : nombre de jobs en cours ou soumis par utilisateur (`MaxJobs`, `MaxSubmitJobs`), durée maximale (`MaxWall`), ressources totales d'un groupe (`GrpTRES`) ou par utilisateur (`MaxTRESPerUser`). Si une limite est définie à plusieurs niveaux, la documentation de « Resource Limits » retient le premier niveau où elle est définie, dans cet ordre : QOS de la partition, QOS du job, association de l'utilisateur, associations des comptes en remontant l'arbre, racine du cluster, puis partition. Les limites `Grp*` font exception : celle du compte, si elle est plus stricte, s'applique avant celle de l'utilisateur.

Un job retenu par une limite porte une raison `Assoc…Limit` ou `QOS…Limit`, qu'on lit dans `squeue` (chapitre 1). Rappelez-vous la condition du chapitre 3 : sans `AccountingStorageEnforce=…limits`, ces limites sont lisibles dans la base mais **jamais appliquées**.

### 4.4. Gros jobs et fragmentation

Un job de 64 nœuds exclusifs peut attendre longtemps : les petits jobs qui passent devant occupent des nœuds épars, et les 64 nœuds ne sont jamais libres ensemble. Le backfill réserve en principe les ressources du job prioritaire dans le futur, mais seulement tant que les durées déclarées sont justes. Trois leviers d'exploitation :

-   **Des durées maximales par partition ou QOS**, pour que les petits jobs finissent en un temps prévisible.
-   **Une QOS « gros jobs »** avec un poids de priorité plus élevé et une limite minimale de nœuds.
-   **Des fenêtres réservées** (réservations récurrentes) pour les gros entraînements, quand la politique de l'organisation l'exige.

Le réglage fin du backfill passe par des paramètres `SchedulerParameters` de la forme `bf_…` (par exemple `bf_continue`, `bf_max_job_test`), dont les valeurs dépendent de la taille de la file : consultez la documentation de votre version avant de les modifier.

### 4.5. Une politique pour trois équipes

Voici l'architecture d'une politique cohérente, à titre d'exemple. Trois équipes partagent un cluster : la recherche (gros entraînements), les applications (expériences moyennes) et le développement (jobs courts interactifs).

| Besoin | Mécanisme |
|---|---|
| Chaque équipe obtient une part garantie à long terme | une association par équipe avec des parts d'équité proportionnelles |
| Un job interactif court démarre en moins d'une minute | QOS `interactive`, priorité élevée, `MaxWall=04:00:00`, `MaxTRESPerUser=gres/gpu=2` |
| Les gros entraînements ne sont pas bloqués par les petits | QOS `large` avec priorité suffisante et durée longue |
| Les jobs de reprise peu coûteuse utilisent les GPU inactifs | QOS `scavenger` préemptible, `PreemptMode=REQUEUE` |
| Personne ne dépasse un quota | `GrpTRES` par compte, appliqué grâce à `AccountingStorageEnforce` |

L'exercice 7 vous demande de traduire cette table en commandes `sacctmgr` et de les valider.

::: recap
Points clés — chapitre 4

-   `preempt/qos` et `PreemptMode=REQUEUE` : un job urgent préempte un job normal, qui est remis en file ; il faut qu'il sache reprendre.
-   Une réservation retire des nœuds pour une période ; les jobs trop longs n'y entrent pas avant elle.
-   Les limites ne sont appliquées que si `AccountingStorageEnforce` inclut `limits`.
-   Les gros jobs souffrent de la fragmentation : durées justes, QOS dédiée, fenêtres réservées.
-   Une politique complète combine parts d'équité, QOS, préemption et quotas, sans multiplier les partitions.
:::

## 5. GPU et topologie {#ch5}

Un nœud GPU n'est pas un sac de GPU : processeurs, GPU et cartes réseau y ont une géographie, et un placement ignorant cette géographie ralentit l'entraînement sans produire la moindre erreur. Ce chapitre montre comment Slurm la décrit et comment la demander.

### 5.1. Déclarer les GPU à Slurm

Trois fichiers de configuration décrivent un nœud GPU. Les extraits suivants sont des **exemples non exécutés** (ils exigent des GPU NVIDIA) ; les noms de fichiers et les clés viennent de la documentation de Slurm.

~~~text
# slurm.conf (extrait)
GresTypes=gpu
AccountingStorageTRES=gres/gpu
SelectType=select/cons_tres
ProctrackType=proctrack/cgroup
TaskPlugin=task/cgroup,task/affinity
NodeName=gpu[001-016] Sockets=2 CoresPerSocket=48 RealMemory=2000000 Gres=gpu:h100:8
PartitionName=train Nodes=gpu[001-016] MaxTime=7-00:00:00 State=UP

# gres.conf
AutoDetect=nvml

# cgroup.conf
ConstrainCores=yes
ConstrainRAMSpace=yes
ConstrainDevices=yes
~~~

-   `GresTypes=gpu` déclare la ressource générique ; `Gres=gpu:h100:8` annonce huit GPU de type `h100` sur chaque nœud.
-   `AccountingStorageTRES=gres/gpu` fait suivre les GPU par la comptabilité : sans cette ligne, `sreport` ne sait pas compter des GPU-heures.
-   `AutoDetect=nvml` demande à `slurmd` de détecter les GPU NVIDIA par la bibliothèque NVML, avec leurs fichiers de périphérique, leurs cœurs voisins et leurs liens. Sans détection, `gres.conf` liste à la main chaque `File=/dev/nvidia0` et son affinité.
-   `proctrack/cgroup` est « fortement recommandé » par la documentation pour suivre tous les processus d'un job.
-   La documentation recommande d'empiler `task/cgroup,task/affinity` pour contraindre les cœurs et fixer l'affinité.
-   `ConstrainDevices=yes` limite les périphériques visibles d'un job à ses GRES alloués : un job qui a demandé deux GPU ne voit que deux GPU.

Les valeurs de mémoire, de cœurs et de durée sont celles d'un exemple : relevez les vôtres avec `slurmd -C`, qui affiche la configuration détectée d'un nœud.

### 5.2. Demander des GPU et les lier correctement

La demande se fait par `--gpus-per-node=[type:]N`, `--gpus-per-task=[type:]N` ou `--gres=gpu:[type:]N`. Pour un entraînement multi-nœuds, `--gpus-per-node` avec `--exclusive` est la forme la plus lisible.

Reste la **liaison**. Deux options de la documentation comptent.

-   `--gres-flags=enforce-binding` restreint les processeurs d'un job à ceux qui sont liés aux GPU alloués : le job ne reçoit plus des cœurs du mauvais socket.
-   `--gpu-bind=closest` (avec `srun`) attache chaque tâche au GPU le plus proche d'elle.

::: ex
[Exemple 5.1 — Huit tâches, un GPU chacune, le plus proche]{.tag} Pour lancer huit processus par nœud, chacun avec son GPU voisin :

~~~bash
srun --nodes=1 --ntasks=8 --gpus-per-task=1 --gpu-bind=closest \
     --cpus-per-task=12 python worker.py
~~~

Sans `--gpu-bind=closest`, la répartition peut envoyer une tâche vers un GPU rattaché à l'autre socket, ce qui ajoute un détour par le lien inter-socket à chaque transfert. Cette commande est un exemple non exécuté : elle demande des GPU.
:::

### 5.3. Partager un GPU

Un GPU entier pour une petite expérience est du gaspillage. NVIDIA propose le partitionnement matériel **MIG** (*Multi-Instance GPU*) sur certains modèles ; la page « GRES » de la documentation de Slurm contient une section « MIG Management ». Elle précise qu'avec la détection `nvidia`, Slurm ne détecte pas les instances MIG ni les liens NVLink, et que NVML ne fournit pas de métriques d'utilisation pour les instances MIG : la comptabilité de la mémoire et de l'utilisation GPU n'existe donc pas pour elles.

Avec `AutoDetect=nvml`, en revanche, Slurm traite chaque instance MIG comme un GPU distinct. La conséquence pour l'exploitation : MIG convient aux petites charges d'inférence ou de développement, pas à l'entraînement multi-GPU. Le partage par tranches de temps (*time-slicing*) relève plutôt de Kubernetes (module 12).

### 5.4. Topologie du réseau

Si deux nœuds d'un même commutateur de bordure communiquent plus vite qu'à travers deux niveaux de commutateurs, un job de huit nœuds a intérêt à tenir sous le même commutateur. Slurm le sait avec le plugin `topology/tree` et un fichier `topology.conf` qui décrit les commutateurs. L'exemple de la documentation :

~~~text
SwitchName=s0 Nodes=tux[0-1]
SwitchName=s1 Nodes=tux[2-3]
SwitchName=s2 Nodes=tux[4-5]
SwitchName=s3 Nodes=tux[6-7]
SwitchName=s4 Switches=s[0-1]
SwitchName=s5 Switches=s[2-3]
SwitchName=s6 Switches=s[4-5]
~~~

Les commutateurs de feuille (`s0` à `s3`) listent leurs nœuds, ceux des niveaux supérieurs listent leurs sous-commutateurs. Selon la documentation, l'algorithme identifie le commutateur de plus bas niveau qui peut contenir l'allocation, puis choisit les nœuds sur ses commutateurs de feuille avec un algorithme de meilleur ajustement (*best fit*).

L'option `--switches=N@durée` d'un job fixe le nombre maximal de commutateurs de feuille souhaité et la durée d'attente maximale pour l'obtenir. La durée suit les formats de `--time` (`minutes`, `minutes:secondes`, `heures:minutes:secondes`) : `01:00` vaut donc **une minute**, pas une heure.

Un job qui préfère attendre une heure plutôt que de s'étaler sur deux commutateurs écrit `--switches=1@01:00:00`. L'administrateur peut plafonner cette attente avec le paramètre `max_switch_wait` de `SchedulerParameters` (300 secondes par défaut d'après le guide de configuration de l'ordonnancement).

::: ex
[Exemple 5.2 — Choisir entre attendre et s'étaler]{.tag} Sur les huit nœuds de la topologie ci-dessus, un job demande quatre nœuds. Seuls `tux0` (sous `s0`), `tux2` (sous `s1`), `tux4` et `tux5` (sous `s2`) sont libres. Quatre nœuds libres existent donc, mais sur trois commutateurs de feuille.

Avec `--switches=2@30` (30 minutes), Slurm attendra jusqu'à 30 minutes, sous réserve du plafond `max_switch_wait`, une allocation sur au plus deux commutateurs de feuille avant de céder et d'accepter ce qu'il trouve. Le compromis est classique : attendre améliore la communication mais retarde le démarrage ; pour un job de plusieurs jours, 30 minutes d'attente sont négligeables, pour un job d'une heure elles sont prohibitives.
:::

Les versions récentes de la documentation décrivent aussi un plugin `topology/block`, qui impose une structure hiérarchique de blocs pour que les jobs restent dans un bloc : il cherche à limiter la fragmentation de la grappe, là où `topology/tree` place d'abord le job sur les premières ressources disponibles. Ses détails et sa disponibilité dépendent de votre version : voir la page « Topology » de la documentation de la version installée.

::: recap
Points clés — chapitre 5

-   Un nœud GPU se déclare dans `slurm.conf` (`Gres=`), `gres.conf` (`AutoDetect=nvml`) et `cgroup.conf` (`ConstrainDevices=yes`).
-   `--gpus-per-node`, `--gres-flags=enforce-binding` et `--gpu-bind=closest` décrivent la demande et la liaison CPU-GPU.
-   MIG partage un GPU sans comptabilité d'utilisation GPU : réservez-le aux petites charges.
-   `topology/tree` et `--switches=N@durée` (attention : `01:00` vaut une minute) arbitrent entre attente et étalement sur le réseau.
:::

## 6. Comptabilité et reporting {#ch6}

Ce qui ne se mesure pas ne se pilote pas : l'utilisation d'un cluster, le temps d'attente des utilisateurs et la part de calcul perdue se lisent dans la comptabilité. Ce chapitre apprend à les extraire sans se tromper de commande.

### 6.1. Ce que la comptabilité enregistre

`slurmdbd` enregistre, pour chaque job, les ressources allouées et la durée, ainsi que l'état final. La comptabilité fonctionne en deux temps : les **enregistrements bruts** par job (lus par `sacct`) et des **agrégats** par heure, jour et mois calculés par `slurmdbd` (lus par `sreport`). La différence est essentielle, comme on le verra plus bas.

La commande de base est `sacct`. L'option `-X` n'affiche que l'allocation du job et non chacune de ses étapes, ce qui suffit presque toujours ; `--format` choisit les colonnes ; `-S` et `-E` bornent la période.

::: ex
[Exemple 6.1 — Lire sacct]{.tag} Trois petits jobs, un job qui échoue volontairement avec le code 3 et un job encore en cours, sur le bac à sable (extrait réel) :

~~~text
$ sacct -X --format=JobID,JobName%10,Account,AllocCPUS,State%12,ExitCode,Elapsed,CPUTimeRAW
JobID           JobName    Account  AllocCPUS        State ExitCode    Elapsed CPUTimeRAW
------------ ---------- ---------- ---------- ------------ -------- ---------- ----------
22                 wrap   research          2    COMPLETED      0:0   00:00:03          6
23                 wrap   research          2    COMPLETED      0:0   00:00:04          8
24                 wrap   research          2    COMPLETED      0:0   00:00:04          8
25                 wrap   research          1       FAILED      3:0   00:00:03          3
26                 wrap   research          1      RUNNING      0:0   00:00:02          2
~~~

`ExitCode` s'écrit `code:signal` : d'après la documentation, c'est le code de sortie renvoyé par le script du job, suivi après les deux-points du signal qui a éventuellement terminé le processus (`DerivedExitCode`, lui, est le code le plus élevé des étapes). Le job 25 s'est donc terminé avec le code 3 et sans signal. `CPUTimeRAW` est le produit du nombre de processeurs alloués par la durée, en secondes : $2 \times 3 = 6$ pour le job 22. C'est cette quantité, sommée par compte, qui alimente l'équité du chapitre 3.
:::

### 6.2. sreport et ses agrégats

`sreport` produit des rapports par cluster, compte, utilisateur ou QOS. Sa documentation précise que les données viennent de **cumuls horaires, quotidiens et mensuels** de la base, et que le rapport choisit la table de cumul la plus longue qui permet de répondre à la période demandée. L'option `-T` (`--tres`) choisit les ressources à rapporter, par exemple `-T gres/gpu` pour des GPU-heures, à condition que `AccountingStorageTRES=gres/gpu` soit configuré (chapitre 5).

~~~bash
sreport -t hours cluster utilization start=2026-10-17 end=2026-10-24 -T gres/gpu
sreport -t hours cluster AccountUtilizationByUser start=2026-10-01 -T gres/gpu
~~~

::: note
[Un cluster neuf affiche des rapports vides]{.tag} Sur le bac à sable, juste après les jobs de l'exemple 6.1, `sreport cluster utilization` et `sreport cluster AccountUtilizationByUser` n'affichent que leurs en-têtes : aucune ligne de données. Les agrégats ne sont pas encore calculés, alors que `sacct` voit déjà tous les jobs. Conséquence pratique : pour une vérification immédiate (« mon job a-t-il compté ? »), utilisez `sacct` ; pour un suivi de période, `sreport`, en sachant que les chiffres de l'heure en cours manquent. Cette observation a été faite sur Slurm 23.11 ; elle est cohérente avec le fonctionnement par cumuls décrit dans la documentation.
:::

### 6.3. Les trois indicateurs à suivre

Trois grandeurs répondent à trois questions différentes. Ne les mélangez pas.

1.  **L'utilisation** répond à « les machines sont-elles occupées ? ». Elle se calcule sur une période :

$$U = \frac{\text{GPU-heures allouées}}{\text{GPU-heures totales}}$$

Variante utile : rapporter l'allocation à la capacité *disponible*, c'est-à-dire sans les nœuds drainés. Le calcul est celui de l'exercice 8.

2.  **L'attente** répond à « les utilisateurs sont-ils servis rapidement ? ». Pour chaque job, c'est l'écart entre sa soumission et son démarrage ; on suit la médiane et un percentile élevé par QOS, car une moyenne cache les jobs qui attendent des jours.

3.  **Le gaspillage** répond à « combien de calcul est perdu ? ». Il se mesure par la part des GPU-heures allouées consommée par des jobs qui échouent, sont préemptés sans checkpoint ou sont tués pour dépassement de durée (états `FAILED`, `TIMEOUT`, `NODE_FAIL`, `PREEMPTED`).

Un script court suffit pour la deuxième : il lit la sortie de `sacct` au format parsable et calcule les percentiles.

~~~python
import subprocess
import sys
from datetime import datetime
from statistics import median, quantiles

out = subprocess.run(["sacct", "-X", "-P", "-n", "--format=Submit,Start", "-S", "now-7days"],
                     capture_output=True, text=True, check=True).stdout
waits = []
for line in out.splitlines():
    submit, start = line.split("|")
    if start not in ("Unknown", "None", ""):  # a job that has not started yet has no wait to measure
        waits.append((datetime.fromisoformat(start) - datetime.fromisoformat(submit)).total_seconds())
if len(waits) < 2:
    sys.exit("need at least two started jobs to compute a percentile")
# method="inclusive" never goes beyond the largest observed wait; the default "exclusive" does on small samples
p90 = quantiles(waits, n=10, method="inclusive")[-1]
print(f"jobs: {len(waits)}  median wait: {median(waits):.0f} s  p90: {p90:.0f} s")
~~~

Ce script est `labs/slurm/slurm-sandbox/examples/wait_stats.py`.

Lancé sur le bac à sable après quatre jobs d'une seconde soumis ensemble, il affiche `jobs: 4  median wait: 6 s  p90: 10 s` (mesure du 25 octobre 2026, à quelques secondes près d'une exécution à l'autre). Même sur un cluster vide, l'attente n'est pas nulle : ces jobs ont démarré à environ 3 secondes d'intervalle.

Avec quatre jobs, le p90 n'a aucune valeur statistique : l'exemple ne montre que la mécanique. L'option `method="inclusive"` évite de dépasser la plus grande attente observée, ce que fait la méthode par défaut sur un petit échantillon. Le script exige au moins deux jobs démarrés, car `quantiles` demande deux valeurs.

### 6.4. Du rapport au pilotage

Une revue hebdomadaire d'un cluster tient en quatre chiffres : utilisation brute, utilisation rapportée à la capacité disponible, médiane et percentile 90 de l'attente par QOS, part de GPU-heures perdues. Comparer deux semaines vaut mieux que lire une semaine seule. Le module 14 branche ces mêmes grandeurs sur Prometheus et Grafana ; le module 15 les convertit en coûts.

::: recap
Points clés — chapitre 6

-   `sacct` lit les jobs enregistrés ; `sreport` lit des cumuls horaires, quotidiens et mensuels : un cluster neuf ou l'heure en cours y est absent.
-   `ExitCode` s'écrit `code:signal` ; `CPUTimeRAW` est le produit processeurs par durée en secondes.
-   Pour compter des GPU, `AccountingStorageTRES=gres/gpu` est indispensable.
-   Trois indicateurs distincts : utilisation, attente, gaspillage.
:::

## 7. Santé des nœuds {#ch7}

Sur un cluster de plusieurs centaines de GPU, des nœuds tombent tous les jours. La question n'est pas d'éviter les pannes mais de **ne pas y envoyer de jobs** : un job lancé sur un nœud défaillant coûte des heures de GPU puis une enquête.

### 7.1. Les états d'un nœud

`sinfo` affiche l'état de chaque nœud. Les états de la documentation que vous rencontrerez le plus :

| État | Sens | Action typique |
|---|---|---|
| `idle` | libre | rien |
| `mixed` | partiellement alloué | rien |
| `allocated` | entièrement alloué | rien |
| `draining` | marqué *drain* mais des jobs tournent encore | attendre la fin des jobs |
| `drained` | marqué *drain*, plus aucun job | enquêter, réparer, remettre en service |
| `down` | indisponible ; Slurm y place parfois un nœud de lui-même après une défaillance | enquêter en priorité |
| `fail` / `failing` | une défaillance est annoncée mais les jobs en cours peuvent finir | traiter avant la fin des jobs |

Un nœud *drained* ne reçoit aucun nouveau job mais n'interrompt pas les jobs en cours : c'est la mise en quarantaine douce. Le mettre en `down` est plus radical. Les commandes :

~~~bash
scontrol update nodename=gpu007 state=drain reason="gpu_ecc_errors"
sinfo -R                                  # liste les nœuds retirés et leur raison
scontrol update nodename=gpu007 state=resume
~~~

Donner une **raison** est la règle : sans elle, le nœud devient un mystère pour l'équipe suivante.

### 7.2. Le contrôle de santé périodique

Slurm exécute périodiquement, sur chaque nœud, un programme de votre choix. Trois paramètres de `slurm.conf` : `HealthCheckProgram` (le chemin), `HealthCheckInterval` (la période en secondes) et `HealthCheckNodeState` (les états de nœud concernés). Le projet ouvert **LBNL Node Health Check** (NHC) en est une implémentation : il fournit une bibliothèque de tests (processeurs, mémoire, systèmes de fichiers, réseau, GPU) conçue pour Slurm et d'autres ordonnanceurs.

Quelle que soit l'implémentation, un bon contrôle :

1.  **est rapide** : quelques secondes au plus, car il tourne à intervalle fixe sur tous les nœuds ;
2.  **est idempotent** : le relancer ne change rien tant que rien n'a changé ;
3.  **draine avec une raison** qui identifie le contrôle qui a échoué ;
4.  **ne remet en service que ce qu'il a drainé lui-même** : un nœud mis en quarantaine par un humain doit le rester.

::: ex
[Exemple 7.1 — Un contrôle qui draine et remet en service]{.tag} Le script `labs/slurm/node-health/node_check.sh` vérifie l'espace libre dans `/tmp`, la présence de `python3` et un compteur d'erreurs GPU **simulé** par un fichier. Sa logique de décision tient en quelques lignes :

~~~bash
if [ "${#reasons[@]}" -gt 0 ]; then
  case "$state" in
    *DRAIN*) ;;  # already drained: keep the first reason
    *) scontrol update nodename="$node" state=drain reason="health: ${reasons[*]}" ;;
  esac
  exit 1
fi
case "$current_reason" in
  health:*) scontrol update nodename="$node" state=resume ;;
esac
~~~

Le préfixe `health:` de la raison est la signature du script : lui seul peut remettre le nœud en service. Le lab 5.3 écrit un faux compteur d'erreurs, attend que `sinfo -R` affiche `health: gpu_xid:79` (valeur simulée), supprime le fichier et attend que le nœud redevienne `idle`.
:::

### 7.3. Prolog et epilog

Un **prolog** est un script exécuté sur le nœud avant un job, un **epilog** après. La page « Prolog and Epilog Guide » de la documentation précise deux points qui surprennent.

-   Par défaut, le prolog ne s'exécute sur un nœud que lorsqu'il voit **la première étape d'une nouvelle allocation**. Un job qui n'a lancé aucune étape ne déclenche jamais le prolog, sauf si `PrologFlags=Alloc` force l'exécution dès l'allocation. L'epilog, lui, s'exécute toujours.
-   Si le **prolog échoue** (code de sortie non nul), le nœud passe en état `DRAIN` et le job est remis en file ; si l'**epilog échoue**, le nœud passe aussi en `DRAIN`. D'après la documentation, le job est alors retenu (*held*), sauf si `nohold_on_prolog_fail` figure dans `SchedulerParameters`.

Un prolog est donc une barrière : un job ne démarre pas sur un nœud qui échoue au contrôle.

::: ex
[Exemple 7.2 — Ce que fait un prolog qui échoue]{.tag} Le lab 5.3 configure `Prolog=prolog_gate.sh`, qui échoue quand le compteur d'erreurs simulé est non nul, puis soumet un job. Observation sur Slurm 23.11 :

~~~text
$ squeue -o "%i %T %r"
JOBID STATE REASON
15 PENDING launch failed requeued held
$ sinfo -R -h -o "%E | %N"
Prolog error | vm
~~~

Le nœud est drainé avec la raison `Prolog error` et le job repart en attente dans l'état **retenu** (*held*) : même une fois le nœud réparé, il faut le libérer avec `scontrol release`. C'est une surprise fréquente de l'exploitation : le job ne repart pas tout seul.
:::

### 7.4. Remettre un nœud en service

Une procédure écrite évite les remises en service précipitées.

1.  **Drainer** avec une raison précise.
2.  **Enquêter** sur la cause : journaux du noyau, erreurs ECC, état des liens, compteurs GPU (modules 6 et 14).
3.  **Réparer ou remplacer** : redémarrage, mise à jour de micrologiciel, échange de composant chez le fournisseur.
4.  **Valider** par un test de recette court : un test GPU et un test de communication (module 6).
5.  **Remettre en service** avec `state=resume`, et surveiller le nœud pendant les premières heures.

Un nœud qui est drainé plusieurs fois en peu de temps est un nœud à retirer pour réparation plutôt qu'à remettre en service : fixez une règle, par exemple trois drains en sept jours. C'est un choix de politique de ce parcours, pas une règle de Slurm.

::: war
[À grande échelle, la santé des nœuds est un travail d'automatisation]{.tag} Sur une période de 54 jours de pré-entraînement de Llama 3 405B, Meta a rapporté 419 interruptions imprévues de job, attribuées à environ 78 % à des problèmes matériels confirmés ou suspectés ; les GPU représentaient 58,7 % de toutes les causes imprévues. L'équipe n'a eu besoin d'une intervention manuelle significative que trois fois : le reste a été traité par l'automatisation. Source : [article Llama 3, section 3.3.4](https://arxiv.org/abs/2407.21783).
:::

::: recap
Points clés — chapitre 7

-   Drainer avec une raison : le nœud reçoit plus de jobs, les jobs en cours finissent.
-   `HealthCheckProgram` exécute un contrôle périodique ; NHC (LBNL) en est une implémentation ouverte.
-   Un bon contrôle est rapide, idempotent, drainé avec raison, et ne remet en service que ses propres drains.
-   Un prolog en échec draine le nœud et retient le job : il faut le libérer.
-   La remise en service suit une procédure écrite ; un nœud qui flotte doit sortir de la production.
:::

## 8. Conteneurs, environnements et Slurm sur Kubernetes {#ch8}

Les chercheurs veulent *leur* environnement logiciel, et pas celui de l'administrateur. Ce chapitre montre comment Slurm l'accueille et ce qu'on obtient quand on le place sur Kubernetes.

### 8.1. Environnements logiciels

Les centres de calcul gèrent classiquement des piles logicielles multiples avec des gestionnaires d'environnement (Environment Modules ou Lmod, qui modifient le `PATH` à la demande) et des outils de compilation de piles comme Spack. C'est une pratique courante du calcul scientifique : elle donne la reproductibilité de la compilation mais pas l'isolation des dépendances Python d'un entraînement.

### 8.2. Conteneurs sous Slurm

Pour l'entraînement, l'unité de livraison est de plus en plus une image de conteneur. **Pyxis** est un plugin SPANK de Slurm qui ajoute à `srun` les options `--container-image` et `--container-mounts`, et **Enroot** est l'exécuteur sans privilèges qui les prend en charge. D'après le dépôt de Pyxis :

~~~bash
srun --container-image=almalinux:9 grep PRETTY /etc/os-release
srun --container-image=almalinux:9 --container-mounts=/etc/os-release:/host/os-release grep PRETTY /host/os-release
~~~

Une contrainte d'exploitation à retenir : depuis Slurm 21.08, Pyxis doit être **compilé contre la version de Slurm déployée** sur le cluster, sinon Slurm refuse de le charger avec l'erreur `Incompatible plugin version`. Chaque mise à jour de Slurm entraîne donc une recompilation de Pyxis : c'est une ligne de votre procédure de mise à jour.

### 8.3. Slurm sur Kubernetes

Beaucoup d'organisations ont des années d'investissement dans des scripts Slurm et veulent pourtant la gestion d'infrastructure de Kubernetes. **Slinky** est un projet ouvert développé par SchedMD (désormais rattaché à NVIDIA) qui permet d'exécuter et de gérer des clusters Slurm à l'intérieur de Kubernetes. Il comprend notamment un opérateur (`slurm-operator`) qui déploie les démons Slurm comme des ressources Kubernetes. Le module 12 reprend cette comparaison.

### 8.4. Slurm, Kubernetes ou les deux ?

| Critère | Slurm natif | Kubernetes | Slurm sur Kubernetes |
|---|---|---|---|
| Modèle de charge | jobs finis, gros jobs parallèles | services et jobs | jobs finis dans une plateforme de services |
| File d'attente, équité, préemption | natifs et matures | à ajouter (Kueue, Volcano) | natifs de Slurm |
| *Gang scheduling* (tous les processus d'un job démarrent ensemble, ou aucun) | natif | à ajouter | natif de Slurm |
| Outillage des utilisateurs | scripts `sbatch`, familiers aux chercheurs | manifestes et images | scripts `sbatch` conservés |
| Exploitation de l'infrastructure | spécialisée HPC | commune avec les services | double compétence |

Ce tableau est un jugement de ce parcours, pas une mesure. Le bon choix dépend surtout de l'équipe qui opère et des habitudes des utilisateurs.

::: recap
Points clés — chapitre 8

-   Pyxis et Enroot lancent des conteneurs avec `srun --container-image` ; Pyxis doit être compilé contre la version de Slurm déployée.
-   Environment Modules, Lmod et Spack gèrent les piles logicielles des centres de calcul.
-   Slinky exécute des clusters Slurm dans Kubernetes pour concilier habitudes HPC et exploitation cloud-native.
-   Le choix Slurm, Kubernetes ou hybride dépend de l'équipe d'exploitation et des utilisateurs avant la technique.
:::

## Labs {#labs}

Les trois labs s'exécutent sur un **vrai Slurm 23.11** (paquets Ubuntu 24.04) dans une machine ou un conteneur Linux **jetable** avec accès root : les scripts écrivent dans `/etc/slurm` et démarrent des démons en `root`. Aucun GPU n'est requis. Installation préalable :

~~~bash
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y munge slurm-wlm slurmdbd mariadb-server
~~~

::: lab
[Lab 5.1 — Un Slurm réel dans le bac à sable]{.tag}

**Objectif.** Démarrer un Slurm mono-nœud avec comptabilité, soumettre un tableau et une dépendance, puis faire sauvegarder et reprendre un entraîneur sur signal. **Durée.** 3 h. **Prérequis matériels.** Une VM ou un conteneur Linux jetable, 2 processeurs et 4 Go de mémoire au minimum, accès root.

1.  Lisez `labs/slurm/slurm-sandbox/setup.sh` : repérez la clé `munge`, la base MariaDB, `slurmdbd.conf`, `slurm.conf` et la création du compte `research`.
2.  Lancez `sudo bash setup.sh`, puis `sinfo`, `sbatch --wrap='hostname'`, `squeue` et `sacct -X`.
3.  Soumettez le tableau et la dépendance de la partie A de `verify.sh` en les écrivant vous-même, puis comparez.
4.  Lisez `examples/trainer.py` et `examples/checkpoint_on_signal.sbatch` ; lancez la partie B : un `scancel --signal=USR1 --batch` déclenche le checkpoint, le job suivant reprend à l'étape sauvegardée.
5.  Terminez par `sudo bash teardown.sh` (avec `--purge-db`, la comptabilité est aussi effacée).

**Critère de réussite.** `sudo bash verify.sh` affiche « OK part A », la ligne `start at step N` de la reprise (où `N` est l'étape sauvegardée), « OK failure propagation » puis « OK slurm-sandbox: parts A and B ». Temps d'exécution : de 40 à 50 secondes mesurées.

**Pour aller plus loin.** Supprimez l'association de `root` (`sacctmgr -i remove user root`) et constatez le refus de `sbatch` du chapitre 1, puis essayez `AccountingStorageType=accounting_storage/none` sans `AccountingStorageEnforce` pour voir un job s'exécuter sans comptabilité. Ajouter un deuxième nœud simulé (plusieurs `slurmd` sur une machine) n'a pas été essayé ici.
:::

::: lab
[Lab 5.2 — Fairshare, QOS et préemption]{.tag}

**Objectif.** Constater qu'un compte peu actif passe devant un compte gros consommateur, et qu'une QOS urgente préempte une QOS normale. **Durée.** 4 h. **Prérequis matériels.** Ceux du lab 5.1.

1.  Lisez `labs/slurm/fairshare-qos/configure.sh` : `PriorityCalcPeriod=1`, `PreemptType=preempt/qos`, `PreemptMode=REQUEUE`, comptes, QOS `urgent`.
2.  Partie A : huit jobs courts du compte `teama` créent de la consommation ; attendez que `sshare` affiche un facteur d'équité inférieur à celui de `teamb`.
3.  Soumettez un job bloqueur, puis un job de chaque compte ; lisez `sprio` et vérifiez l'ordre de démarrage dans `sacct`.
4.  Partie B : lancez un job `normal` de quatre processeurs, puis un job `urgent` ; vérifiez `Restarts=1` et l'état `PREEMPTED`.
5.  Changez les poids (`PriorityWeightFairshare`, `PriorityWeightAge`) et relisez `sprio -w`.

**Critère de réussite.** `sudo bash verify.sh` affiche « OK part A » et « OK part B ». Comptez un peu plus de deux minutes (123 s mesurées) : le facteur d'équité n'est recalculé qu'à chaque `PriorityCalcPeriod`, réglé ici à une minute.

**Pour aller plus loin.** Ajoutez un `GraceTime` à la QOS `normal` et vérifiez que le job reçoit un signal avant d'être préempté.
:::

::: lab
[Lab 5.3 — Drain, prolog et vérification de santé]{.tag}

**Objectif.** Automatiser la mise en quarantaine d'un nœud défaillant et observer le comportement d'un prolog qui échoue. **Durée.** 3 h. **Prérequis matériels.** Ceux du lab 5.1.

1.  Lisez `labs/slurm/node-health/node_check.sh` : repérez les trois contrôles, le préfixe `health:` et la règle de remise en service.
2.  Partie A : configurez `HealthCheckProgram`, simulez une erreur GPU avec `echo 79 > /tmp/fake_gpu_xid`, attendez que `sinfo -R` affiche `health: gpu_xid:79`, supprimez le fichier, attendez le retour à `idle`. Drainez ensuite vous-même le nœud avec une raison sans préfixe `health:` et vérifiez, après quelques périodes du contrôle, qu'il reste drainé.
3.  Partie B : configurez `Prolog=prolog_gate.sh`, recréez l'erreur, soumettez un job et observez `launch failed requeued held` et la raison `Prolog error`.
4.  Libérez le job avec `scontrol release` après avoir remis le nœud en service.
5.  Ajoutez un contrôle de votre choix (par exemple l'espace libre d'un volume) et testez-le.

**Critère de réussite.** `sudo bash verify.sh` affiche « OK part A », « OK part A2 », « OK part B » et « OK node-health ». Durée d'exécution : environ 80 secondes mesurées.

**Pour aller plus loin.** Remplacez le compteur simulé par une vraie lecture : `dmesg` pour des erreurs matérielles, ou `nvidia-smi` sur un nœud GPU (module 14).
:::

## Exercices {#ex}

::: exo
[Exercice 1 · ★ — Lire une file d'attente]{.tag} Voici la file d'un cluster, **fictive**. Expliquez en une phrase la raison de chaque job en attente et dites lequel nécessite une action de l'utilisateur ou de l'administrateur.

~~~text
JOBID PARTITION NAME  USER  ST TIME NODES NODELIST(REASON)
8841  train     big   alice PD 0:00 16    (Resources)
8842  train     small bob   PD 0:00 1     (Priority)
8843  train     post  alice PD 0:00 1     (Dependency)
8844  dev       test  carol PD 0:00 1     (PartitionTimeLimit)
8845  train     tune  dave  PD 0:00 1     (JobHeldUser)
~~~
:::

::: sol
`8841` attend que 16 nœuds se libèrent : rien à faire, c'est de la file normale. `8842` est derrière des jobs de priorité supérieure : à vérifier avec `sprio` si l'attente s'éternise. `8843` attend la fin du job dont il dépend, vraisemblablement `8841` : rien à faire. `8844` demande une durée supérieure à la limite de la partition `dev` : **action de l'utilisateur**, réduire `--time` ou changer de partition, car il n'ira jamais plus loin sinon. `8845` est retenu par son propriétaire : **action de l'utilisateur**, `scontrol release 8845`.
:::

::: exo
[Exercice 2 · ★ — Écrire une soumission]{.tag} Écrivez le script `sbatch` d'un entraînement sur 4 nœuds de 8 GPU, 6 jours maximum, nœuds exclusifs, qui reçoit un signal 10 minutes avant la fin, peut être remis en file et lance `torchrun` sur chaque nœud avec rendez-vous sur le premier. Quelle erreur de chemin guette un script lancé depuis un dépôt ?
:::

::: sol
Les options clés sont `--nodes=4`, `--gpus-per-node=8`, `--exclusive`, `--time=6-00:00:00`, `--signal=B:USR1@600` et `--requeue`. Le lancement reprend la structure de l'exemple 2.1, avec le nombre de nœuds alloués passé à `torchrun`. L'erreur de chemin est celle du lab 5.1 : Slurm exécute une **copie** du script depuis son répertoire d'attente, de sorte que `${BASH_SOURCE[0]}` ne désigne plus votre dépôt. Utilisez `SLURM_SUBMIT_DIR` (le répertoire d'où `sbatch` a été lancé) ou un chemin absolu, et lancez `sbatch` depuis le répertoire du projet.
:::

::: exo
[Exercice 3 · ★ — Un tableau avec limite de concurrence]{.tag} Vous devez évaluer 100 points de contrôle. Chaque évaluation dure 12 minutes sur un GPU et vous n'avez le droit d'en occuper que 10 à la fois. Écrivez l'option de tableau et calculez le temps total en supposant que la file ne vous retarde pas.
:::

::: sol
L'option est `--array=1-100%10`. Dix tâches tournent en parallèle, donc il faut $\lceil 100/10 \rceil = 10$ vagues de 12 minutes, soit 120 minutes. Sans la limite `%10`, les 100 tâches pourraient occuper 100 GPU à la fois : l'équité envers les autres équipes se jouerait alors sur la priorité seule.
:::

::: exo
[Exercice 4 · ★★ — Calculer une priorité]{.tag} Avec $W_{\text{âge}} = 1000$, $W_{\text{équité}} = 10\,000$ et $W_{\text{QOS}} = 2000$ (les autres poids sont nuls), le job A a un facteur d'âge de 0,4, d'équité de 0,3 et de QOS de 0,5. Le job B a un âge de 1,0, une équité de 0,1 et une QOS de 0. Calculez les deux priorités et dites lequel démarre en premier. Que feriez-vous pour que l'attente prolongée finisse par l'emporter sur l'équité ?
:::

::: sol
Pour A, la priorité vaut :

$$1000 \times 0{,}4 + 10\,000 \times 0{,}3 + 2000 \times 0{,}5 = 4400$$

Pour B :

$$1000 \times 1{,}0 + 10\,000 \times 0{,}1 + 0 = 2000$$

A démarre en premier. Dans cette configuration, l'âge (au plus 1000 points) ne peut jamais compenser un écart d'équité de plus de 0,1 ($10\,000 \times 0{,}1$) : pour qu'une longue attente finisse par gagner, il faut augmenter $W_{\text{âge}}$ ou réduire $W_{\text{équité}}$. C'est un choix de politique : plus d'impatience tolérée ou plus d'équité garantie.
:::

::: exo
[Exercice 5 · ★★ — Qui est sous-servi ?]{.tag} Deux comptes frères A et B ont des parts de 3 et de 1. Leurs consommations normalisées parmi les frères sont de 0,8 pour A et de 0,2 pour B. Calculez, pour chaque compte, le rapport entre sa part normalisée et sa consommation normalisée, dites lequel est sous-servi, et lequel passera devant selon Fair Tree.
:::

::: sol
Les parts normalisées sont 0,75 pour A ($3/4$) et 0,25 pour B ($1/4$). Les rapports valent $0{,}75/0{,}8 = 0{,}9375$ pour A et $0{,}25/0{,}2 = 1{,}25$ pour B. Selon la documentation, une valeur supérieure à 1 désigne une association sous-servie et une valeur entre 0 et 1 une association sur-servie : B est sous-servi, A légèrement sur-servi. Fair Tree classe les frères par cette valeur : tous les enfants de B passent devant tous ceux de A, quelle que soit leur propre consommation.
:::

::: exo
[Exercice 6 · ★★ — Qui peut combler un trou ?]{.tag} Un nœud de 8 GPU exécute un job qui en occupe 4 et se termine dans 1 h. Le job prioritaire X demande les 8 GPU pour 4 h : il démarrera donc dans 1 h. Trois jobs plus petits attendent : (a) 4 GPU, limite de 50 min ; (b) 4 GPU, limite de 90 min ; (c) 2 GPU, sans limite déclarée. Lesquels le backfill peut-il lancer maintenant, et pourquoi ?
:::

::: sol
Seul (a) peut démarrer : il termine en 50 min, avant l'heure de début prévue de X, donc il ne retarde pas X. Le job (b) occuperait ses 4 GPU 30 minutes de plus que l'heure de début de X et le retarderait : refusé. Le job (c) n'a aucune durée déclarée, donc la durée maximale de la partition s'applique, sans doute très longue : le backfill ne peut pas garantir qu'il libère ses GPU à temps, il est refusé. La documentation insiste sur ce point : des limites de temps raisonnablement exactes sont importantes pour que le backfill fonctionne.
:::

::: exo
[Exercice 7 · ★★★ — Traduire une politique en commandes]{.tag} Traduisez la table du paragraphe 4.5 en commandes `sacctmgr` : trois comptes de parts 5, 3 et 2 sous un compte parent, une QOS `interactive` (priorité 2000, 4 h au plus, 2 GPU par utilisateur au plus), une QOS `scavenger` (priorité 10) que la QOS `normal` peut préempter, et un quota total de 64 GPU pour le compte de la recherche. Précisez deux paramètres de `slurm.conf` indispensables à son application, puis dites comment vous vérifieriez chaque règle.
:::

::: sol
Les commandes, **exécutées avec succès dans le bac à sable** (le 25 octobre 2026) en remplaçant `gres/gpu` par `cpu`, faute de GPU. `research` est le compte parent du bac à sable ; `recherche` désigne ici l'équipe :

~~~bash
sacctmgr -i add account recherche parent=research fairshare=5
sacctmgr -i add account applis parent=research fairshare=3
sacctmgr -i add account dev parent=research fairshare=2
sacctmgr -i add qos interactive Priority=2000 MaxWall=04:00:00 MaxTRESPerUser=gres/gpu=2
sacctmgr -i add qos scavenger Priority=10
sacctmgr -i modify qos normal set Preempt+=scavenger
sacctmgr -i modify account recherche set GrpTRES=gres/gpu=64
~~~

Deux paramètres sont indispensables : `AccountingStorageEnforce=associations,limits,qos` (sans lui les limites ne sont pas appliquées) et `AccountingStorageTRES=gres/gpu` (pour que les GPU soient suivis). La préemption exige aussi `PreemptType=preempt/qos` et un `PreemptMode`. On vérifie : les parts avec `sshare`, la QOS interactive en soumettant trois GPU pour un utilisateur (le job doit être retenu par une raison de limite ; avec des processeurs au lieu de GPU, le bac à sable a donné `QOSMaxCpuPerUserLimit`), le quota en soumettant au-delà de 64 GPU (`AssocGrpCpuLimit` avec des processeurs), et la préemption comme au lab 5.2.
:::

::: exo
[Exercice 8 · ★★ — Mesurer l'utilisation d'un cluster]{.tag} Un cluster compte 16 nœuds de 8 GPU. Sur une semaine, `sreport` donne 11 200 GPU-heures allouées. Cinq nœuds ont été drainés pendant 12 heures chacun. Calculez l'utilisation brute, l'utilisation rapportée à la capacité disponible, et le temps de GPU réellement productif si 20 % des GPU-heures allouées ont été perdues en redémarrages.
:::

::: sol
Capacité totale : $16 \times 8 \times 168 = 21\,504$ GPU-heures. Utilisation brute : $11\,200/21\,504 \approx 52{,}1$ %. Capacité retirée par les drains : $5 \times 8 \times 12 = 480$ GPU-heures, donc disponible $21\,024$ et utilisation rapportée à la disponibilité $11\,200/21\,024 \approx 53{,}3$ %. Avec 20 % de pertes, le travail productif est $0{,}8 \times 11\,200 = 8960$ GPU-heures, soit 41,7 % de la capacité totale. Ces trois chiffres répondent à trois questions différentes (occupation, qualité du service, efficacité), et un rapport honnête les distingue.
:::

::: exo
[Exercice 9 · ★★★ — Un nœud qui draine toutes les nuits]{.tag} Le nœud `gpu-n07` est drainé chaque nuit vers 3 h avec la raison `health: gpu_xid:79` (valeur simulée), puis remis en service par le contrôle de santé le matin, car l'erreur disparaît. Trois jobs ont été perdus cette semaine. Proposez une démarche d'enquête, une décision de remise en service, et deux changements de politique.
:::

::: sol
**Enquête.** Corréler les drains avec la charge : quels jobs tournaient à 3 h, y a-t-il une tâche planifiée (sauvegarde, mise à jour) à cette heure ? Lire les journaux du noyau et l'état des GPU autour de l'incident (module 14), comparer avec les nœuds voisins.

**Décision.** Un nœud qui draine plusieurs fois en peu de temps n'est pas « réparé » parce que l'erreur a disparu. Il faut le sortir de la production par un drainage manuel dont la raison n'a pas le préfixe `health:` (il ne sera donc pas remis en service automatiquement), le faire passer en recette complète, et ouvrir un dossier fournisseur si la panne se répète.

**Politique.** Compter les drains par nœud sur sept jours et retirer automatiquement au troisième. Ne remettre en service automatiquement que les raisons que le contrôle sait clore sans ambiguïté.
:::

::: exo
[Exercice 10 · ★★★ — Slurm, Kubernetes ou les deux ?]{.tag} Pour chacun des trois cas, recommandez Slurm natif, Kubernetes ou Slurm sur Kubernetes et justifiez en trois critères. (a) Un laboratoire de 40 chercheurs qui entraînent des modèles sur 200 GPU et connaissent `sbatch`. (b) Une start-up dont l'essentiel de la charge est de l'inférence servie 24 h sur 24, avec quelques entraînements. (c) Une grande entreprise avec une plateforme Kubernetes existante et une équipe de recherche qui exige ses scripts Slurm.
:::

::: sol
Il n'y a pas de réponse unique ; voici une réponse défendable.

(a) **Slurm natif.** Charge de jobs finis, utilisateurs formés, besoin d'équité et de préemption natifs, une seule technologie à exploiter.

(b) **Kubernetes.** L'inférence est un service, qu'on déploie, met à l'échelle et supervise comme tel ; les rares entraînements se traitent avec une file (Kueue) plutôt qu'avec un second ordonnanceur.

(c) **Slurm sur Kubernetes** (par exemple avec Slinky). La plateforme existante reste l'infrastructure commune, les scripts de la recherche sont conservés ; le coût est une double compétence d'exploitation.

Une bonne réponse nomme le coût caché de chaque choix.
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux lire un cluster Slurm.** Preuve : un compte rendu de `sinfo`, `squeue` et `sacct` du bac à sable qui explique chaque état et chaque raison.
-   **Je peux écrire un job qui survit à Slurm.** Preuve : le lab 5.1, partie B, refait avec votre propre script.
-   **Je peux configurer une politique d'équité et de préemption.** Preuve : le lab 5.2 et les commandes de l'exercice 7.
-   **Je peux décrire un nœud GPU et une topologie.** Preuve : un `slurm.conf` et un `gres.conf` commentés pour un nœud de votre choix, avec leurs sources.
-   **Je peux mesurer l'utilisation d'un cluster honnêtement.** Preuve : l'exercice 8 refait sur les chiffres d'un cluster réel ou simulé.
-   **Je peux automatiser la quarantaine d'un nœud.** Preuve : le lab 5.3 et un contrôle de votre choix.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Un job de 64 GPU attend depuis trois jours. Que regardez-vous ?* Réponse-type : la raison dans `squeue`, la priorité et ses facteurs avec `sprio`, l'équité de son compte avec `sshare`, sa durée déclarée (backfill), les réservations, les nœuds drainés qui retirent de la capacité, et la fragmentation due aux petits jobs.
2.  *Comment partager 256 GPU entre quatre équipes sans gaspiller les GPU inactifs ?* Réponse-type : parts d'équité par équipe, une QOS préemptible pour utiliser la capacité inactive à condition que ces jobs sachent reprendre, des quotas de groupe et une mesure d'utilisation hebdomadaire.
3.  *Un nœud draine toutes les nuits puis revient seul. Que faites-vous ?* Réponse-type : ne pas se fier au retour spontané, enquêter sur les causes corrélées, sortir le nœud de la production après plusieurs drains, le valider par une recette complète.

## Lectures et références {#refs}

-   SchedMD. [*Multifactor Priority Plugin*](https://slurm.schedmd.com/priority_multifactor.html) : la formule de priorité et les poids (chapitre 3).
-   SchedMD. [*Fair Tree Fairshare Algorithm*](https://slurm.schedmd.com/fair_tree.html) : l'algorithme d'équité par défaut (chapitre 3).
-   SchedMD. [*Scheduling Configuration Guide*](https://slurm.schedmd.com/sched_config.html) : le backfill et l'importance des durées (chapitre 3).
-   SchedMD. [*Resource Limits*](https://slurm.schedmd.com/resource_limits.html) et [*Preemption*](https://slurm.schedmd.com/preempt.html) : limites, `AccountingStorageEnforce`, `PreemptMode` (chapitre 4).
-   SchedMD. [*Reservations*](https://slurm.schedmd.com/reservations.html) : syntaxe des réservations (chapitre 4).
-   SchedMD. [*Generic Resource (GRES) Scheduling*](https://slurm.schedmd.com/gres.html), [*cgroup.conf*](https://slurm.schedmd.com/cgroup.conf.html) et [*Topology Guide*](https://slurm.schedmd.com/topology.html) : GPU, isolation, topologie (chapitre 5).
-   SchedMD. [*Prolog and Epilog Guide*](https://slurm.schedmd.com/prolog_epilog.html) et [*sbatch*](https://slurm.schedmd.com/sbatch.html) : prolog, signaux, remise en file (chapitres 2 et 7).
-   SchedMD. [*sinfo*](https://slurm.schedmd.com/sinfo.html) et [*squeue*](https://slurm.schedmd.com/squeue.html) : états de nœud et raisons d'attente (chapitres 1 et 7).
-   NVIDIA. [*Pyxis*](https://raw.githubusercontent.com/NVIDIA/pyxis/master/README.md) : conteneurs sous `srun` (chapitre 8).
-   LBNL. [*Node Health Check (NHC)*](https://raw.githubusercontent.com/mej/nhc/master/README.md) : bibliothèque ouverte de contrôles de santé de nœuds (chapitre 7).
-   SchedMD et NVIDIA. [*Slinky*](https://www.nvidia.com/en-us/software/slinky/) : Slurm dans Kubernetes (chapitre 8).
-   Grattafiori et al. (Meta). [*The Llama 3 Herd of Models*](https://arxiv.org/abs/2407.21783), section 3.3.4 : interruptions et automatisation à 16 000 GPU (chapitre 7).

## Sources et portée {#sources}

**Documenté.** Les formules, paramètres, options et comportements attribués à la documentation de Slurm (priorité multifactorielle, Fair Tree, backfill, préemption, réservations, limites, GRES, cgroup, topologie, prologues, `sbatch`, `sinfo`, `squeue`) ont été relus sur les pages officielles de SchedMD, qui affichent la documentation de la version 26.05, lors de la relecture du 25 octobre 2026. Les faits sur Pyxis, NHC et Slinky ont été relus sur leurs pages. Tous les comportements décrits comme « observés » ont été reproduits sur Slurm 23.11.4 dans le bac à sable ; les sorties citées en viennent, parfois abrégées ; les numéros de job, les durées et les décomptes de CPU-secondes varient d'une exécution à l'autre.

**Recommandé.** L'ordre des chapitres, la règle « peu de partitions, plusieurs QOS », le seuil de trois drains en sept jours, la marge de 20 à 30 % sur les durées et le tableau comparatif Slurm, Kubernetes et hybride sont des choix de ce parcours, pas des règles de Slurm.

**À vérifier.** La version testée est la 23.11.4 des paquets Ubuntu 24.04 : le comportement et les noms de paramètres évoluent, notamment pour les topologies (`topology/block`) et la préemption ; lisez la documentation de votre version. La raison d'attente `InvalidAccount` n'a pas été reproduite sur ce bac à sable (voir le chapitre 1), et le refus d'une réservation avant ses jobs trop longs (chapitre 4) n'a pas été relu sur la page « Reservations ». Les extraits de `slurm.conf`, `gres.conf` et les scripts GPU des chapitres 2 et 5 n'ont **pas** été exécutés (ils demandent des GPU) ; les scripts ont seulement passé `shellcheck`.

**Hors périmètre.** L'installation d'un cluster multi-nœuds réel et du réseau d'interconnexion (modules 6 et 7), Slurm en mode cloud avec nœuds éphémères, l'API REST `slurmrestd`, les accélérateurs non NVIDIA, et l'administration de la base de comptabilité en production (sauvegardes, purge).
