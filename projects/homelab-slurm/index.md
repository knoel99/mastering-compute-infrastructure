---
title: "Projet 1 — Mini-cluster Slurm instrumenté"
subtitle: "Projet 1 · 24 h · modules : linux-systems, provisioning, slurm, observability"
description: "La comptabilité d'un cluster Slurm décrite en code et appliquée de façon idempotente par différence, un exportateur de métriques, des alertes testées par promtool, et une vérification en direct sur un vrai Slurm."
project:
  id: homelab-slurm
  number: 1
  hours: 24
  modules: [linux-systems, provisioning, slurm, observability]
badges:
  - {label: "Portfolio", class: core}
  - {label: "Tests hors ligne et vérification en direct sur Slurm 23.11.4", class: verified}
numbered: true
---

## Contexte et objectif {#contexte}

Un cluster Slurm est un **état** : comptes, QOS, parts d'équité, utilisateurs, partitions. Tant que cet état n'existe que dans l'historique d'un terminal, personne ne peut le relire, le revoir ni le reconstruire. Ce projet vous fait décrire l'état voulu dans un fichier, calculer **ce qui manque** par rapport à l'état réel, l'appliquer, puis observer le cluster avec des métriques et des alertes que vous avez testées.

Le point de départ est un constat fait en écrivant le [module Slurm](../../courses/slurm/index.html). Ses scripts de lab ajoutent `|| true` à chaque `sacctmgr`, ce qui les rend « idempotents » mais **cache aussi les vraies erreurs**. En effet, `sacctmgr add` sur un objet qui existe déjà se termine avec le code 1, exactement comme une faute de frappe. La bonne méthode est d'**observer l'état réel et de n'ajouter que la différence**, comme le fait `terraform plan` : lire l'état réel, afficher l'écart, ne l'appliquer qu'ensuite.

::: key
[Objectif du projet]{.tag} Un cluster que l'on sait décrire (`cluster.yml`), converger vers cette description sans jamais rien supprimer, et surveiller avec des alertes dont on a prouvé qu'elles se déclenchent, qu'elles se taisent quand il le faut, et que les tests qui les protègent détectent une règle modifiée.
:::

Le projet se vérifie de deux façons. Hors ligne, avec des sorties **réelles** de Slurm 23.11.4 enregistrées dans `fixtures/` : aucun Slurm n'est nécessaire pour faire passer les tests. En direct, avec `verify-live.sh`, qui monte le Slurm du bac à sable du module 5, applique votre configuration deux fois et lit de vraies métriques.

**État de la vérification en direct.** Le 2026-10-24, `verify-live.sh` a été exécuté avec succès de bout en bout plusieurs fois sur le code de référence (dont deux fois sur la version finale), avec le Slurm 23.11.4 du bac à sable du module 5 (machine virtuelle Linux 6.18, 4 processeurs, sans GPU). Il applique 6 commandes `sacctmgr`, constate qu'un second passage n'en émet aucune, lit des métriques réelles (1 job en cours, 3 en attente, acceptées par `promtool`) et voit un nœud drainé devenir `slurm_node_unhealthy{reason="gpu_xid"} 1`.

Limites : le drainage est provoqué à la main avec `scontrol update … reason=gpu_xid:79`, sans panne de GPU réelle, et les jobs sont des `sleep` sur processeur. L'exportateur lit `sshare` sans `-a` : il ne voit que les associations de l'utilisateur qui le lance (ici `root`), pas celles des autres utilisateurs.

### Prérequis de connaissances {#pre}

Le [module Slurm](../../courses/slurm/index.html) (comptes, QOS, états de nœud, raisons d'attente) est le prérequis direct ; le chapitre sur la comptabilité explique ce que vous allez décrire en code. Les règles d'alerte et leurs tests reprennent la méthode du [projet 5](../gpu-observability/index.html), appliquée ici aux métriques d'un ordonnanceur et non d'un GPU. Ce projet vous fournit le test de mutation déjà écrit ; le projet 5 l'explique en détail.

## Cahier des charges {#cahier}

Le dossier `labs/projects/homelab-slurm/` contient `starter/` (à compléter), `reference/` (à consulter **après** votre tentative), `fixtures/` (sorties réelles de Slurm), `tests/` (24 tests), `verify.sh` (hors ligne) et `verify-live.sh` (sur un vrai Slurm).

| ID | Exigence | Test qui la vérifie |
|---|---|---|
| R1 | **Validation** de `cluster.yml` : parents inconnus, cycles, parts invalides, QOS ou comptes inconnus, noms en majuscules, tous signalés ensemble | `test_validate_reports_every_kind_of_mistake` |
| R2 | **Lecture de l'état réel** à partir des sorties `-nP` de `sacctmgr show assoc` et `show qos` | `test_parse_state_reads_the_real_sacctmgr_output` |
| R3 | **Plan par différence**, dans l'ordre (QOS, comptes parents d'abord, utilisateurs), avec la syntaxe vérifiée sur Slurm ; jamais destructif ; l'état réel capturé est déjà convergé | `test_plan_*`, `test_the_real_captured_state_is_already_converged` |
| R4 | **Convergence** : appliquer le plan puis recalculer donne un plan vide ; l'application s'arrête à la première erreur et la nomme | `test_applying_the_plan_converges_*`, `test_apply_stops_*` |
| R5 | **Exportateur** : métriques sur nœuds, jobs, raisons d'attente, âge du plus vieux job en attente, parts d'équité ; étiquettes **bornées** ; séries à zéro ; `slurm_scrape_ok` | `tests/test_exporter.py` (9 tests) |
| R6 | **Quatre alertes** avec tests `promtool`, chacune avec un cas qui se déclenche et un cas silencieux, et des tests qui détectent une règle mutée | `tests/test_rules.py` (5 tests) |
| R7 | **Vérification en direct** : le second passage ne change rien, les métriques lues sur un vrai Slurm sont acceptées par `promtool`, un nœud drainé devient « mal portant » | `verify-live.sh` |

Les quatre alertes sont `SlurmExporterStale` (métriques absentes ou périmées), `SlurmNodeUnhealthy` (nœud drainé ou en panne), `SlurmJobsPendingTooLong` (le plus vieux job attend depuis plus d'une heure) et `SlurmSchedulerStuck` (des jobs attendent, aucun ne tourne et des nœuds sont libres). La dernière est la panne classique du module 5 : un job qui attend à jamais avec la raison `InvalidAccount` alors que le nœud est libre.

## Jalons {#jalons}

| N° | Jalon | Durée | Preuve |
|---|---|---|---|
| 1 | Validation et lecture de l'état (`config.py`, première moitié) | 4 h | `test_validate_*` et `test_parse_state_*` passent |
| 2 | Plan, application, dérive et convergence | 6 h | les 10 tests de `test_config.py` passent ; l'état réel capturé donne un plan vide |
| 3 | Exportateur de métriques | 6 h | les 9 tests de `test_exporter.py` passent, dont l'acceptation par `promtool check metrics` |
| 4 | Règles d'alerte et leurs tests | 4 h | `promtool test rules` passe et le test de mutation aussi |
| 5 | Exécution en direct, runbook et ADR | 4 h | la sortie de `verify-live.sh`, un runbook d'une page, un ADR |

~~~bash
cd labs/projects/homelab-slurm
sudo apt-get install -y prometheus            # promtool
export PYTHON=/chemin/vers/python             # pytest et pyyaml
IMPL=starter $PYTHON -m pytest -q tests       # 22 échecs sur 24 au départ
PYTHON=$PYTHON bash verify.sh                  # référence verte, départ rouge
sudo PYTHON=$PYTHON IMPL=starter bash verify-live.sh   # votre code sur un vrai Slurm (root, bac à sable jetable)
~~~

Commencez par **regarder** les fixtures : ouvrez `fixtures/assoc.txt` et `fixtures/sshare.txt` et décrivez ce que vous voyez avant d'écrire un analyseur. L'indentation de `sshare`, par exemple, existe même avec l'option de sortie parsable ; on ne la découvre qu'en regardant.

## Livrables {#livrables}

Votre dépôt public contient :

- `cluster.yml`, `config.py` et `exporter.py` complétés, les règles et leurs tests, avec la commande unique qui lance tout ;
- la sortie de `verify-live.sh` sur votre machine, ou la mention honnête qu'elle n'a pas pu être exécutée ;
- un **runbook** d'une page : « des jobs attendent, des nœuds sont libres, que vérifier et dans quel ordre » ;
- un **ADR** d'une page.

L'ADR tranche au moins quatre questions, en nommant l'alternative écartée :

1. Pourquoi calculer une différence plutôt qu'ignorer les erreurs avec `|| true`, et que perd-on quand la différence est calculée sur un état qui change pendant l'exécution ?
2. Pourquoi le plan n'a-t-il aucune commande de suppression, et que faites-vous des objets qui ont dérivé ?
3. Comment avez-vous borné les étiquettes de l'exportateur, et quelle série aurait explosé sans cela ?
4. Pourquoi une alerte sur « rien ne tourne » exige-t-elle une série à zéro plutôt qu'une série absente ?

## Critères de réussite {#criteres}

Chaque critère est mesurable ; la commande qui le montre est indiquée.

- **État réel converge.** Pour `cluster.yml` et les sorties capturées dans `fixtures/`, `plan` renvoie une liste vide et `drift` ne signale rien. Commande : `pytest -k real_captured_state`.
- **Syntaxe vérifiée.** Sur un cluster vierge, le plan est exactement : une QOS, deux comptes, deux utilisateurs et un `modify user … qos+=urgent`, dans l'ordre du test. Commande : `pytest -k plan_from_an_empty`.
- **Idempotence.** Après application, un second plan est vide, avec un faux `sacctmgr` qui répond 1 sur un objet existant ; et en direct, le second passage de `config.py` n'affiche aucune commande. Commandes : `pytest -k converges` et `verify-live.sh`.
- **Jamais destructif.** Aucune commande du plan ne contient `delete`, `remove` ni `-=`, et les objets en trop sont rapportés par `drift`.
- **Exportateur.** Les sorties réelles donnent 4 jobs en attente dont 3 `Priority` et 1 `Resources`, et un nœud `drng` avec la raison bornée `gpu_xid`. L'exposition passe `promtool check metrics`.
- **Série à zéro.** Un cluster au repos expose `slurm_jobs{state="RUNNING"} 0` et `PENDING 0`. Commande : `pytest -k zero_valued`.
- **Alertes.** Chacune des six mutations (durée `for` portée à 90 minutes, comparaison inversée) fait échouer vos tests. Commande : `pytest tests/test_rules.py -k mutated`.

## Pistes et indices {#pistes}

Ces indices ne donnent pas la solution ; essayez d'abord sans.

**Syntaxe de `sacctmgr`.** Ne la devinez pas : testez-la sur le Slurm du bac à sable. Les formes qui ont été exécutées avec succès sont `add account NOM parent=P fairshare=N`, `modify account where name=NOM set fairshare=N`, `add user NOM account=A`, `add qos NOM Priority=N Preempt=autre`, `modify qos where name=NOM set Priority=N Preempt=a,b`, `modify user where name=NOM set qos+=Q` et `add user NOM account=A` pour un utilisateur déjà présent dans un autre compte.

**Lire l'état.** `sacctmgr -nP show assoc` mêle deux sortes de lignes : celles dont la colonne utilisateur est vide décrivent un compte (parent, part), les autres décrivent un utilisateur dans un compte (avec la liste de ses QOS). Un même utilisateur peut apparaître dans plusieurs comptes, comme `root` dans les fixtures.

**Idempotence par différence.** Deux idées distinctes : ne **proposer** que ce qui manque, et **s'arrêter** au premier échec avec un message qui nomme la commande. Un échec silencieux est exactement ce que `|| true` produisait.

**Étiquettes bornées.** Le texte libre d'une raison de nœud (`gpu_xid:79`, `health: …`) donnerait une série par message distinct. Gardez la partie avant le premier deux-points ou espace. De même, regroupez les raisons d'attente inconnues sous `other`.

**Fuseau horaire.** `squeue` écrit l'heure de soumission (`%V`) dans le fuseau **local** de la machine. L'analyseur la lit comme de l'UTC : lancez donc les commandes avec `TZ=UTC`, sinon l'âge de chaque job en attente est faux du décalage horaire (observé : `TZ=America/New_York` donnait 14402 s pour un job soumis 2 s plus tôt, de quoi déclencher `SlurmJobsPendingTooLong` aussitôt).

**Absence et zéro.** Une alerte « des jobs attendent et aucun ne tourne » compare le nombre de jobs en cours à zéro. Si l'exportateur n'émet que les états qui existent, la série `RUNNING` **n'existe pas** quand rien ne tourne, et la comparaison ne donne rien : l'alerte ne se déclenche jamais, précisément dans le cas qu'elle doit couvrir. Émettez des zéros explicites.

**États de nœud.** `sinfo` affiche `drng` (en cours de drainage, des jobs tournent encore) puis `drain`. Les deux sont « mal portants » ; un suffixe comme `*` ou `~` doit disparaître avant de comparer.

### Résultats de la solution de référence {#reference-results}

À lire **après** votre propre travail.

::: sol
**Observé sur Slurm 23.11.4 (bac à sable, 2026-10-24).**

~~~text
$ sacctmgr -i add account teama parent=research fairshare=1     # deuxième fois
 Already existing account teama on cluster sandbox              # code de retour 1
$ sacctmgr -i add qos urgent Priority=1000 Preempt=normal       # deuxième fois
 Nothing new added.                                             # code de retour 1
~~~

Les deux commandes se terminent avec le code 1, comme n'importe quelle erreur : c'est la raison de calculer une différence plutôt que d'ignorer les échecs. La commande `modify … set` réussit avec le code 0.

**Formats lus.** `sshare -n -P` indente la première colonne (` root|root|1|0.5…`) ; `sinfo -N -o "%E"` écrit `none` quand il n'y a pas de raison ; un nœud qui draine alors qu'un job tourne est `drng`, puis `drain` quand le job est parti ; `squeue` donne la raison `None` pour un job qui tourne.

**Résultat des tests.** La référence passe 24 tests ; le code de départ en échoue 22 (seuls passent les deux tests qui vérifient la règle et son test fournis). Le test de mutation génère six mutants de la règle et les détecte tous.

**Ce que les tests ne couvrent pas.**

- Le test de mutation ne produit que deux sortes de mutants (durée `for` à 90 minutes, première comparaison inversée). Un seuil ou une durée légèrement décalés, comme `> 3500` au lieu de `> 3600`, ne sont attrapés que par les cas ajoutés à la main dans `slurm.rules.test.yml`.
- `modify qos … Preempt=` **remplace** toute la liste (vérifié sur Slurm 23.11.4). Si le cluster préempte une QOS de plus que le fichier, le plan la retire, ce qui contredit « jamais destructif ».
- Si `preempt` est absent du fichier alors que le cluster en a un, le plan émet un `modify` qui ne change rien et ne converge jamais. Ces deux cas ne sont pas testés.
:::

## Extensions {#extensions}

- **Contrôle de santé.** Ajoutez la configuration `HealthCheckProgram` du lab 5.3 à `cluster.yml` et faites décrire par le code le nœud mis en quarantaine ; mesurez le délai entre la panne et l'alerte.
- **Plusieurs nœuds.** Étendez le cluster à plusieurs `slurmd` et vérifiez que les métriques par nœud et les alertes se comportent de même.
- **API plutôt que lignes de commande.** Remplacez les appels à `sinfo` et `squeue` par l'API REST `slurmrestd` et comparez la robustesse de l'analyse.
- **Tableau de bord.** Générez un tableau de bord Grafana comme au projet 5, avec les quatre alertes en annotations.
- **Dérive.** Faites supprimer, avec confirmation explicite, un objet signalé par `drift` ; décidez qui a le droit de lancer cette commande et comment le tracer.

## Pour le portfolio {#portfolio}

**Structure du dépôt.** Un `README.md` d'un écran : le problème (état du cluster non reproductible), le schéma description, plan, application, exportateur, alertes, la commande qui lance les 24 tests, la sortie de `verify-live.sh`, et un paragraphe sur ce que le projet ne couvre pas.

**Ce qu'il faut montrer.** Le plan vide au second passage, les alertes testées et le test de mutation, et le runbook. Le recruteur lira d'abord ce que vous faites des erreurs de `sacctmgr`.

**Ce qu'un recruteur d'infrastructure de calcul cherche.** Quelqu'un qui décrit un cluster comme du code, qui sait pourquoi `|| true` est un défaut, qui sépare l'absence d'une mesure de sa valeur zéro, et qui teste ses alertes comme du code.

::: note
[Pourquoi une différence plutôt qu'un script « rejouable »]{.tag} Un script qui rejoue tout en ignorant les échecs réussit dans tous les cas, y compris quand il n'a rien fait de ce qu'on voulait. Une différence calculée sur l'état réel dit ce qu'elle va faire **avant** de le faire, peut être relue, et devient vide quand le but est atteint : une liste vide est un résultat vérifiable.
:::

Trois accroches **honnêtes**, à adapter à ce que vous avez réellement fait :

1. « J'ai décrit la comptabilité d'un cluster Slurm dans un fichier et écrit un outil qui n'ajoute que la différence avec l'état réel, avec un second passage vide, vérifié sur un vrai Slurm. »
2. « J'ai écrit des alertes sur les files d'attente de Slurm dont les tests échouent quand on modifie la règle, dont une qui détecte des jobs en attente avec des nœuds libres. »
3. « Je sais dire ce que ce projet ne couvre pas : un cluster multi-nœuds, l'API REST et la suppression d'objets. »

### Formules du projet {#formules}

Ce projet n'introduit pas de formule nouvelle. L'âge du plus vieux job en attente, métrique de `SlurmJobsPendingTooLong`, est la différence entre l'instant de lecture et l'instant de soumission le plus ancien parmi les jobs en attente :

$$\text{âge}_{\max} = t_{\text{lecture}} - \min_{j \in \text{PENDING}} t_{\text{soumission}}(j)$$

### Pour aller plus loin {#lectures}

- SchedMD, documentation de [`sacctmgr`](https://slurm.schedmd.com/sacctmgr.html), [`sinfo`](https://slurm.schedmd.com/sinfo.html), [`squeue`](https://slurm.schedmd.com/squeue.html) et [`sshare`](https://slurm.schedmd.com/sshare.html).
- Le [projet 5](../gpu-observability/index.html) pour la méthode des règles testées par mutation.
