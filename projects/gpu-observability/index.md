---
title: "Projet 5 — Observabilité GPU et détection de pannes silencieuses"
subtitle: "Projet 5 · 20 h · modules : observability, slurm, fault-tolerance"
description: "Un exportateur au format dcgm-exporter, des règles d'alerte dont les tests résistent à la mutation, et des détecteurs de job bloqué et de traînard avec taux d'alarmes fausses et délai de détection mesurés."
project:
  id: gpu-observability
  number: 5
  hours: 20
  modules: [observability, slurm, fault-tolerance]
badges:
  - {label: "Portfolio", class: core}
  - {label: "Code de départ et solution vérifiés (promtool 2.45)", class: verified}
---

## Contexte et objectif {#contexte}

Les pannes qui font du bruit sont les moins chères : un nœud qui tombe, un code d'erreur dans les journaux, un job qui s'arrête. Les pannes **silencieuses** coûtent le plus, parce que les GPU restent réservés et facturés pendant que rien d'utile ne se passe. Le rapport technique de Llama 3 en décrit une classe : « Sometimes, hardware issues may cause still-functioning but slow stragglers that are hard to detect. Even a single straggler can slow down thousands of other GPUs, often appearing as functioning but slow communications » ([Llama Team, 2024](https://arxiv.org/abs/2407.21783)).

Ce projet vous fait construire la chaîne qui rend ces pannes visibles : un exportateur de métriques, des règles d'alerte **testées**, des détecteurs dont vous **mesurez** la qualité, et un tableau de bord. Tout est alimenté par un simulateur de cluster, car la matière première d'une alerte, ce sont des séries temporelles de pannes, et on ne peut pas les provoquer à la demande sur du vrai matériel.

::: key
[Objectif du projet]{.tag} Passer de « j'ai installé un exportateur et un tableau de bord » à « je sais dire en combien de temps mon dispositif détecte chaque panne, avec combien de fausses alertes, et j'ai prouvé que mes tests d'alertes les protègent contre une modification de la règle ».
:::

Trois pannes sont simulées. Un **job bloqué** : une collective ne se termine plus, tous les GPU du job tournent dans des noyaux d'attente. Un **traînard** : un GPU ralenti par la chauffe freine tout le job. Un **code XID** : le pilote signale une erreur matérielle. Une quatrième situation, l'**allocation inactive**, ressemble à un blocage mais n'en est pas un : rien ne tourne, l'utilisation est vraiment nulle.

::: war
[Hypothèse du simulateur, à valider sur matériel]{.tag} Le simulateur suppose qu'un job bloqué garde une utilisation GPU **élevée** (les noyaux d'attente tournent) alors que l'activité des unités tensorielles tombe à zéro et que la puissance baisse. Des rapports d'utilisateurs concordants décrivent ce profil ([forum PyTorch](https://discuss.pytorch.org/t/distributed-data-parallel-freezes-without-error-message/8009?page=2), [dépannage NCCL de la documentation d'Axolotl](https://docs.axolotl.ai/docs/nccl.html)), mais je ne les ai pas vérifiés mot à mot et je n'ai pas pu le mesurer sur un GPU. Si vous avez un GPU, refaites l'expérience avant de faire confiance à la leçon de ce projet.
:::

Les noms, types et textes d'aide des métriques sont ceux de la liste de compteurs par défaut de dcgm-exporter ([etc/default-counters.csv](https://github.com/NVIDIA/dcgm-exporter/blob/main/etc/default-counters.csv), lue à la rédaction). Notez le piège de `DCGM_FI_DEV_XID_ERRORS` : c'est une **jauge** qui porte « la valeur de la dernière erreur XID rencontrée », pas un compteur d'erreurs. Elle reste donc non nulle jusqu'à la réinitialisation du GPU, ce qui oriente la règle d'alerte.

### Prérequis de connaissances {#pre}

Vous devez savoir lire une métrique Prometheus (jauge, étiquettes, requête `avg by`) et écrire un peu de Python. Le [module Slurm](../../courses/slurm/index.html) donne le contexte d'exploitation, en particulier le chapitre sur la santé des nœuds. Le module « observabilité » du parcours approfondit Prometheus, Alertmanager et les tableaux de bord ; vous pouvez faire ce projet avant de le lire.

Installation de l'outil de test, sous Debian ou Ubuntu : `sudo apt-get install prometheus` fournit `promtool`. Les tests ont été exécutés avec la version 2.45.3.

## Cahier des charges {#cahier}

Le dossier `labs/projects/gpu-observability/` contient `starter/` (à compléter), `reference/` (à consulter **après** votre tentative), `tests/` (21 tests) et `verify.sh`. Le simulateur `sim.py` est fourni.

| ID | Exigence | Test qui la vérifie |
|---|---|---|
| R1 | **Exportateur** : texte au format d'exposition de Prometheus, six métriques aux noms de dcgm-exporter, une ligne par GPU, serveur HTTP `/metrics` | `tests/test_exporter.py` (5 tests) |
| R2 | **Jointure d'allocation** : métrique `slurm_job_gpu_allocated` pour relier un GPU à son job, car dcgm-exporter ne connaît pas Slurm | `test_labels_follow_dcgm_exporter_and_join_metric_*` |
| R3 | **Quatre alertes** : `GPUXidError`, `GPUThermalThrottle`, `JobStalled`, `GPUIdleAllocated`, chacune avec une sévérité et un résumé | `test_required_alerts_exist_*`, `test_rules_are_syntactically_valid` |
| R4 | **Tests d'alertes** avec `promtool test rules` : pour chaque alerte, au moins un cas qui la déclenche et un cas où elle reste silencieuse | `test_rule_unit_tests_pass`, `test_every_required_alert_has_*` |
| R5 | **Tests qui résistent à la mutation** : si l'on allonge la durée `for` d'une règle ou si l'on inverse sa comparaison, vos tests doivent échouer | `test_unit_tests_catch_mutated_rules` |
| R6 | **Détecteur de job bloqué** fondé sur l'activité tensorielle, qui ne se laisse pas tromper par une utilisation GPU élevée | `test_stalled_job_*`, `test_naive_utilisation_alert_is_blind_*` |
| R7 | **Détecteur de traînard** robuste (médiane et MAD) et mesure du taux d'alarmes fausses et du délai de détection | `test_straggler_*`, `test_no_false_alarm_*`, `test_detectors_do_not_confuse_*` |
| R8 | **Tableau de bord** généré (JSON Grafana) dont chaque expression est du PromQL valide et n'utilise que des métriques exposées | `tests/test_dashboard.py` (3 tests) |

Le code de départ contient un squelette de `exporter.py` (liste des métriques donnée), les aides de `detectors.py` avec le détecteur naïf **fondé sur l'utilisation GPU**, laissé en place pour démontrer son aveuglement, une règle `GPUXidError` et son test. Les trois autres alertes, leurs tests, les deux détecteurs et le tableau de bord sont à écrire.

## Jalons {#jalons}

| N° | Jalon | Durée | Preuve |
|---|---|---|---|
| 1 | Exportateur au format dcgm-exporter et serveur `/metrics` | 4 h | les 5 tests de `test_exporter.py` passent ; la sortie est lue par `promtool check metrics` |
| 2 | Règles d'alerte et tests `promtool` | 5 h | `promtool check rules` et `promtool test rules` passent ; `test_rules.py` passe, mutants compris |
| 3 | Détecteurs de job bloqué et de traînard, avec mesures | 5 h | les 8 tests de `test_detectors.py` passent ; un tableau seuil, délai, alarmes fausses |
| 4 | Tableau de bord généré | 3 h | les 3 tests de `test_dashboard.py` passent ; un `dashboard.json` joint |
| 5 | Mesures, runbook et ADR | 3 h | une page de résultats, un runbook d'une page par panne, un ADR |

~~~bash
cd labs/projects/gpu-observability
sudo apt-get install -y prometheus            # promtool
export PYTHON=/chemin/vers/python             # pytest et pyyaml suffisent
IMPL=starter $PYTHON -m pytest -q tests       # 19 échecs sur 21 au départ
PYTHON=$PYTHON bash verify.sh                  # référence verte, départ rouge
cd starter/rules && promtool test rules gpu.rules.test.yml
~~~

Le test de mutation vaut le détour. Il copie vos règles, en modifie une (durée `for` portée à 90 minutes, ou comparaison inversée), relance `promtool test rules` et exige un échec. Une suite de tests qui passe encore sur une règle cassée ne protège de rien : écrire des cas qui franchissent le seuil **et** qui restent en deçà, avec des instants d'évaluation de part et d'autre de la durée `for`, est la seule façon de réussir.

## Livrables {#livrables}

Votre dépôt public contient :

- le code complété, les règles, leurs tests `promtool` et la commande unique qui lance tout ;
- `dashboard.json` généré ;
- une page de **mesures** : pour chaque détecteur, le délai de détection et le taux d'alarmes fausses, avec les valeurs de seuil essayées ;
- un **runbook** d'une page par panne (job bloqué, traînard, XID) : ce que l'alerte signifie, ce qu'il faut vérifier, dans quel ordre, quand vider le nœud ;
- un **ADR** d'une page.

L'ADR tranche au moins quatre questions, en nommant l'alternative écartée :

1. Pourquoi détecter un job bloqué par l'activité tensorielle plutôt que par l'utilisation GPU, et quelle hypothèse cela suppose-t-il ?
2. Où placer la jointure avec l'allocation (dans la règle, dans un exportateur, dans une règle d'enregistrement) et que se passe-t-il quand la métrique d'allocation est absente ?
3. Comment avez-vous choisi les durées `for` et les seuils, et quel coût une alerte trop sensible fait-elle porter à la personne d'astreinte ?
4. Que se passe-t-il quand l'exportateur lui-même tombe, et comment le saurez-vous ?

## Critères de réussite {#criteres}

Chaque critère est mesurable ; la commande qui le montre est indiquée.

- **Format.** La sortie de l'exportateur est acceptée par `promtool check metrics` ; le seul avertissement toléré est celui de la casse des étiquettes `UUID`, `modelName` et `Hostname`, qui sont celles de dcgm-exporter.
- **Règles.** `promtool check rules gpu.rules.yml` réussit et `promtool test rules gpu.rules.test.yml` réussit pour les quatre alertes.
- **Mutation.** Les huit mutants (quatre durées allongées, quatre comparaisons inversées) font tous échouer vos tests. Commande : `pytest tests/test_rules.py -k mutated`.
- **Blocage.** Un job bloqué à t = 1 800 s est détecté en moins de 20 scrapes de 15 s plus un intervalle, alors que le détecteur naïf par utilisation GPU ne le détecte **jamais**. Commande : `pytest tests/test_detectors.py -k "stalled or naive"`.
- **Traînard.** Un GPU ralenti est signalé en moins de huit scrapes plus un intervalle, **lui seul** est signalé, et aucun traînard n'est déclaré sur un job bloqué (ni l'inverse).
- **Alarmes fausses.** Sur 1 024 GPU-heures sans panne, aucune alerte. Vous savez dire ce que cela prouve : le taux est inférieur à environ 3 divisés par 1 024, soit 0,3 %, avec 95 % de confiance, **si** les observations sont indépendantes, ce qu'elles ne sont pas tout à fait.
- **Tableau de bord.** Chaque expression passe `promtool check rules` et n'utilise que des métriques de l'exportateur. Commande : `pytest tests/test_dashboard.py`.

## Pistes et indices {#pistes}

Ces indices ne donnent pas la solution ; essayez d'abord sans.

**Jointure.** dcgm-exporter décrit des GPU, Slurm décrit des jobs. Pour agréger par job, multipliez la métrique du GPU par la métrique d'allocation, valeur 1, en associant sur `Hostname` et `gpu` et en ramenant l'étiquette du job avec `group_left`. Vérifiez ce qui arrive aux GPU sans allocation : la multiplication les fait disparaître, ce qui est voulu ici.

**Durée `for`.** Une alerte passe par l'état « en attente » avant de se déclencher. Pour la tester, évaluez avant et après la durée : l'état avant doit être silencieux, l'état après doit être actif. L'écriture `0.55x39` de `promtool` produit **quarante** échantillons, pas trente-neuf : la notation `axn` répète la valeur `n` fois après la première.

**XID.** Comme la jauge garde la dernière valeur, une règle `> 0` reste active jusqu'à la remise à zéro. C'est voulu ; décidez en revanche si le message doit nommer le code (`{{ $value }}`), et lisez le catalogue d'erreurs XID de NVIDIA avant d'écrire un runbook.

**Traînard.** Une valeur aberrante gonfle l'écart type : utilisez la médiane et l'écart absolu médian (MAD), multiplié par 1,4826 pour l'ajuster à un écart type gaussien. Un plancher sur l'échelle évite de diviser par un nombre minuscule sur une flotte très régulière ; choisissez-le d'après la **variabilité réelle** d'une flotte saine.

**Persistance.** Exiger que la condition dure plusieurs scrapes consécutifs divise fortement les alarmes fausses, au prix d'un délai. Mesurez ce compromis plutôt que de le supposer : c'est le tableau demandé dans les livrables.

**Mesurer sans se tromper.** Un dispositif qui ne déclenche jamais n'a ni fausse alerte ni bonne détection. Reportez toujours les deux, sur des pannes simulées **et** sur des exécutions saines.

### Résultats de la solution de référence {#reference-results}

À lire **après** votre propre travail. Le simulateur est déterministe, ces valeurs sont donc reproductibles ; elles dépendent de ses hypothèses, pas d'un matériel réel.

::: sol
**Délais de détection** (faute à t = 1 800 s, scrape de 15 s) :

| détecteur | panne | délai |
|---|---|---|
| `StalledJob` (20 scrapes) | job bloqué | 285 s |
| `NaiveUtilStall` (utilisation GPU) | job bloqué | jamais |
| `Straggler` (8 scrapes, z de 6) | GPU ralenti | 105 s |

Le délai est celui de la persistance : 19 intervalles de 15 s font 285 s, 7 intervalles font 105 s. Le détecteur naïf ne voit rien parce que, dans l'hypothèse du simulateur, l'utilisation reste à 98 % pendant le blocage.

**Alarmes fausses du détecteur de traînard**, sur 1 024 GPU-heures saines, **sans persistance** (un seul scrape suffit) :

| seuil z | alarmes par GPU-heure |
|---|---|
| 2 | 8,41 |
| 3 | 1,89 |
| 4 | 0,40 |
| 6 | 0,016 |

Avec la persistance de huit scrapes et z de 6, le nombre d'alarmes tombe à zéro. À z de 6 sans persistance il reste seize alarmes, bien plus que ne le prédit une loi gaussienne : le plancher d'échelle, de 5 MHz, est inférieur à la variabilité simulée de 10 MHz, donc le seuil effectif est proche de 3 écarts types. **Le plancher doit refléter le bruit réel d'une flotte saine.**

**Tests d'alertes.** Les quatre alertes de référence passent `promtool test rules` avec quatre scénarios, et les huit mutants sont tous détectés.

**Avertissement de format.** `promtool check metrics` signale les étiquettes `UUID`, `modelName` et `Hostname` comme non conformes à la convention snake_case : ce sont celles de dcgm-exporter lui-même. La solution les conserve, parce que les règles et les tableaux de bord réels s'en servent ; c'est une décision à consigner dans l'ADR.
:::

## Extensions {#extensions}

- **Alerter sur l'absence.** Ajoutez une alerte qui se déclenche quand l'exportateur ne répond plus, avec `up` ou `absent`, et testez-la avec `promtool`. Un exportateur mort ressemble à un cluster sain.
- **Vrai dcgm-exporter.** Sur une machine à GPU, lancez dcgm-exporter, comparez ses séries à celles du simulateur, et **mesurez** le profil d'un blocage (utilisation, puissance, activité tensorielle) en tuant un rang d'un entraînement. C'est la validation qui manque à ce projet.
- **Alertmanager.** Ajoutez regroupement, inhibition (un nœud en erreur XID masque les alertes de ses GPU) et silences, puis testez l'acheminement avec `amtool`.
- **Seuils appris.** Remplacez le plancher fixe du traînard par une estimation sur une fenêtre glissante de données saines et mesurez de nouveau délai et alarmes fausses.
- **Intégration Slurm.** Faites écrire la jointure d'allocation par un prolog et un épilog Slurm (module Slurm, chapitre sur la santé des nœuds) au lieu d'un fichier statique.

## Pour le portfolio {#portfolio}

**Structure du dépôt.** Un `README.md` d'un écran : les trois pannes, le schéma exportateur, règles, détecteurs et tableau de bord, la commande qui lance les 21 tests, le tableau des délais et des alarmes fausses, et un paragraphe « ce qui n'est pas validé sur matériel réel ».

**Ce qu'il faut montrer.** Les tests `promtool`, le test de mutation, le tableau seuil-délai-alarmes et le runbook. Le tableau de bord vient en dernier : il ne prouve rien tout seul.

**Ce qu'un recruteur d'infrastructure de calcul cherche.** Quelqu'un qui sait que l'utilisation GPU ne dit pas si le job travaille, qui chiffre ses détecteurs au lieu de les affirmer, qui teste ses alertes comme du code, et qui dit ce qu'il n'a pas pu valider.

::: note
[Zéro événement observé n'est pas zéro risque]{.tag} Voir aucune alarme fausse sur 1 024 GPU-heures permet seulement d'affirmer, avec 95 % de confiance, que le taux est inférieur à environ 3/1 024 par GPU-heure (règle des trois), si les observations sont indépendantes. Les GPU d'un même job ne le sont pas : l'incertitude réelle est plus grande. Écrivez la borne, pas « zéro ».
:::

Trois accroches **honnêtes**, à adapter à ce que vous avez réellement fait :

1. « J'ai écrit des règles d'alerte GPU dont les tests `promtool` échouent quand on casse la règle (mutation de la durée et de la comparaison), et un détecteur de job bloqué qu'une alerte fondée sur l'utilisation GPU ne voit pas. »
2. « J'ai mesuré délai de détection et alarmes fausses d'un détecteur de traînard pour plusieurs seuils sur un cluster simulé, et montré qu'un plancher d'échelle trop bas ramène le seuil réel à environ trois écarts types. »
3. « Je sais dire ce que ce projet ne valide pas : le profil réel d'un blocage sur GPU, et le comportement à grande échelle. »

### Formules du projet {#formules}

Le score robuste d'un GPU, avec x sa mesure, m la médiane de son job et MAD l'écart absolu médian :

$$z = \frac{x - m}{\max\bigl(1{,}4826\,\mathrm{MAD},\; \text{plancher}\bigr)}$$

Le délai de détection d'un détecteur à persistance k, avec un scrape toutes les Δ secondes, est de (k − 1)·Δ si la panne tombe sur un scrape, et d'au plus k·Δ sinon. La règle des trois borne le taux d'un événement non observé en n essais :

$$p < \frac{3}{n} \quad (95\ \%)$$

### Pour aller plus loin {#lectures}

- Llama Team, *The Llama 3 Herd of Models*, 2024 : section sur la fiabilité, le diagnostic des blocages et des traînards, [arxiv.org/abs/2407.21783](https://arxiv.org/abs/2407.21783).
- Documentation de Prometheus : tests unitaires de règles (`promtool test rules`) et règles d'alerte.
- Dépôt [NVIDIA/dcgm-exporter](https://github.com/NVIDIA/dcgm-exporter) : liste de compteurs par défaut.
