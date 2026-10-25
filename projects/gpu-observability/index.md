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
numbered: true
---

## Contexte et objectif {#contexte}

Les pannes qui font du bruit sont les moins chères : un nœud qui tombe, un code d'erreur dans les journaux, un job qui s'arrête. Les pannes **silencieuses** coûtent souvent le plus, parce que les GPU restent réservés et facturés pendant que rien d'utile ne se passe. Le rapport technique de Llama 3 en décrit une classe : « Sometimes, hardware issues may cause still-functioning but slow stragglers that are hard to detect. Even a single straggler can slow down thousands of other GPUs, often appearing as functioning but slow communications » ([Llama Team, 2024](https://arxiv.org/abs/2407.21783)).

Ce projet vous fait construire la chaîne qui rend ces pannes visibles : un exportateur de métriques, des règles d'alerte **testées**, des détecteurs dont vous **mesurez** la qualité, et un tableau de bord. Tout est alimenté par un simulateur de cluster, car la matière première d'une alerte, ce sont des séries temporelles de pannes, et on ne peut pas les provoquer à la demande sur du vrai matériel.

::: key
[Objectif du projet]{.tag} Passer de « j'ai installé un exportateur et un tableau de bord » à « je sais dire en combien de temps mon dispositif détecte chaque panne, avec combien de fausses alertes, et j'ai prouvé que mes tests d'alertes les protègent contre une modification de la règle ».
:::

Trois pannes sont simulées. Un **job bloqué** : une collective ne se termine plus, tous les GPU du job tournent dans des noyaux d'attente. Un **traînard** : un GPU ralenti par la chauffe freine tout le job. Un **code XID** : le pilote journalise un code d'erreur (certains codes viennent du matériel, d'autres d'un bogue de l'application). Une quatrième situation, l'**allocation inactive**, ressemble à un blocage mais n'en est pas un : rien ne tourne, l'utilisation est vraiment nulle.

::: war
[Hypothèse du simulateur, à valider sur matériel]{.tag} Le simulateur suppose qu'un job bloqué garde une utilisation GPU **élevée** (les noyaux d'attente tournent), que la puissance baisse et que l'activité des unités tensorielles tombe à zéro. Les sources lues n'appuient que les deux premiers points, et pas de façon uniforme.

La documentation d'Axolotl écrit que le délai NCCL est « accompanied by below-average power consumption with near 100% GPU utilization » ([dépannage NCCL de la documentation d'Axolotl](https://docs.axolotl.ai/docs/nccl.html)). Dans un [fil du forum PyTorch](https://discuss.pytorch.org/t/distributed-data-parallel-freezes-without-error-message/8009?page=2), un utilisateur écrit « the GPU hangs at 100% utilization », mais un autre rapporte « the GPU utilization is 0% and stays at 0% for a long time » : le profil n'est donc pas universel.

Aucune source lue ne mentionne l'activité des unités tensorielles : c'est une déduction du projet, que je n'ai pas pu mesurer sur un GPU. Elle a un avantage de conception : un détecteur fondé sur l'activité tensorielle attrape les deux profils (utilisation haute ou nulle), le détecteur naïf un seul. Si vous avez un GPU, refaites l'expérience avant de faire confiance à la leçon de ce projet.
:::

Le [module 14, § 7.2](../../courses/observability/index.html#les-blocages-progrès-pas-activité) détecte un blocage par le compteur de pas, seule preuve de progrès : c'est l'alerte `JobNoProgress` du lab 14.2, fondée sur `train_steps_total`. Ce projet n'instrumente pas l'entraîneur : il ne dispose que des métriques DCGM, et l'activité tensorielle y sert d'indice, à croiser avec le compteur de pas quand il existe. `JobStalled`, l'alerte de blocage de ce projet, complète donc `JobNoProgress` sans la remplacer.

dcgm-exporter sait aussi lire des fichiers de correspondance GPU-job (option `--hpc-job-mapping-dir`, étiquette `hpc_job`, d'après son code source) ; ce projet n'utilise pas cette option et écrit sa propre métrique de jointure, ce qui garde les règles lisibles et testables avec `promtool`.

Les noms, types et textes d'aide des métriques sont ceux de la liste de compteurs par défaut de dcgm-exporter ([etc/default-counters.csv](https://github.com/NVIDIA/dcgm-exporter/blob/main/etc/default-counters.csv), lue à la rédaction). Notez le piège de `DCGM_FI_DEV_XID_ERRORS` : c'est une **jauge** dont le texte d'aide est « Value of the last XID error encountered. » (la dernière valeur, pas un compteur d'erreurs). Elle reste donc non nulle tant qu'aucune autre valeur ne la remplace (les sources lues ne disent pas quand elle retombe à zéro : à vérifier sur matériel), ce qui oriente la règle d'alerte.

Le dépôt propose aussi, commentés par défaut, `DCGM_EXP_XID_ERRORS_COUNT` (jauge sur une fenêtre) et `DCGM_EXP_XID_ERRORS_TOTAL` (compteur depuis le démarrage de l'exportateur) ; ce projet s'en tient à la jauge historique.

### Prérequis de connaissances {#pre}

Ce projet suppose que vous savez lire une métrique Prometheus (jauge, étiquettes, requête `avg by`) et écrire un peu de Python. Il rappelle ce dont il a besoin : vous pouvez le faire avant de lire les modules ci-dessous, quitte à y revenir ensuite.

Le [module 14](../../courses/observability/index.html) approfondit Prometheus, Alertmanager et les tableaux de bord : métriques DCGM au [chapitre 2](../../courses/observability/index.html#ch2), jointure d'allocation et règles d'enregistrement au [chapitre 3](../../courses/observability/index.html#ch3), pannes silencieuses au [chapitre 7](../../courses/observability/index.html#ch7). Le [module 10](../../courses/fault-tolerance/index.html) traite de la détection des blocages et des nœuds lents ([chapitre 5](../../courses/fault-tolerance/index.html#ch5)) et des erreurs Xid ([chapitre 7](../../courses/fault-tolerance/index.html#ch7)). Le [module 5](../../courses/slurm/index.html) donne le contexte d'exploitation de Slurm, en particulier son [chapitre 7](../../courses/slurm/index.html#ch7) sur la santé des nœuds.

Installation de l'outil de test, sous Debian ou Ubuntu : `sudo apt-get install prometheus` fournit `promtool`. Les tests ont été exécutés avec `promtool` 2.45.3, paquet d'Ubuntu 24.04, alors que la documentation citée est celle de la branche 3.x : vérifiez vos règles avec le `promtool` de la version de votre serveur Prometheus.

## Cahier des charges {#cahier}

Le dossier `labs/projects/gpu-observability/` contient `starter/` (à compléter), `reference/` (à consulter **après** votre tentative), `tests/` (28 tests) et `verify.sh`. Le simulateur `sim.py` est fourni.

| ID | Exigence | Test qui la vérifie |
|---|---|---|
| R1 | **Exportateur** : texte au format d'exposition de Prometheus, six métriques aux noms de dcgm-exporter, une ligne par GPU, serveur HTTP `/metrics` | `tests/test_exporter.py` (5 tests) |
| R2 | **Jointure d'allocation** : métrique `slurm_job_gpu_allocated` pour relier un GPU à son job, car dcgm-exporter, tel que ce projet l'utilise, ne relie pas un GPU à un job Slurm | `test_labels_follow_dcgm_exporter_and_join_metric_*` |
| R3 | **Quatre alertes** : `GPUXidError`, `GPUThermalThrottle`, `JobStalled`, `GPUIdleAllocated`, chacune avec une sévérité et un résumé | `test_required_alerts_exist_*`, `test_rules_are_syntactically_valid` |
| R4 | **Tests d'alertes** avec `promtool test rules` : pour chaque alerte, au moins un cas qui la déclenche et un cas où elle reste silencieuse | `test_rule_unit_tests_pass`, `test_every_required_alert_has_*` |
| R5 | **Tests qui résistent à la mutation** : si l'on allonge la durée `for` d'une règle ou si l'on inverse sa comparaison, vos tests doivent échouer | `test_unit_tests_catch_mutated_rules` |
| R6 | **Détecteur de job bloqué** fondé sur l'activité tensorielle (médiane du job sous 0,05 pendant 20 scrapes consécutifs), qui ne se laisse pas tromper par une utilisation GPU élevée | `test_stalled_job_*`, `test_naive_utilisation_alert_is_blind_*` |
| R7 | **Détecteur de traînard** fondé sur l'horloge SM (`DCGM_FI_DEV_SM_CLOCK`, en MHz) de chaque GPU comparée à la médiane de son job, robuste (médiane et écart absolu médian, MAD ; z de 6, persistance de 8 scrapes, plancher de 5 MHz), et mesure du taux d'alarmes fausses et du délai de détection | `test_straggler_*`, `test_no_false_alarm_*`, `test_detectors_do_not_confuse_*` |
| R8 | **Tableau de bord** généré (JSON Grafana) dont chaque expression est du PromQL valide, n'utilise que des métriques exposées et joint l'allocation pour les panneaux par job | `tests/test_dashboard.py` (3 tests) |

Le code de départ contient un squelette de `exporter.py` (liste des métriques donnée), les aides de `detectors.py` avec le détecteur naïf **fondé sur l'utilisation GPU**, laissé en place pour démontrer son aveuglement, une règle `GPUXidError` et son test. Les trois autres alertes, leurs tests, les deux détecteurs (avec `run`, `false_alarm_rate` et `detection_delay`) et le tableau de bord sont à écrire.

**Ce qui est exécuté, et ce qui ne l'est pas.** Les tests tournent sur un simulateur, sans GPU, avec `promtool` pour la syntaxe des métriques, des règles et des expressions du tableau de bord. L'exportateur n'a jamais été scruté par un vrai Prometheus (un client HTTP de test lit `/metrics`), et `dashboard.json` n'a pas été importé dans Grafana : ses tests vérifient le PromQL et les noms de métriques, pas le rendu.

## Jalons {#jalons}

| N° | Jalon | Durée | Preuve |
|---|---|---|---|
| 1 | Exportateur au format dcgm-exporter et serveur `/metrics` | 4 h | les 5 tests de `test_exporter.py` passent ; la sortie est lue par `promtool check metrics` |
| 2 | Règles d'alerte et tests `promtool` | 5 h | `promtool check rules` et `promtool test rules` passent ; `test_rules.py` passe, mutants compris |
| 3 | Détecteurs de job bloqué et de traînard, avec mesures | 5 h | les 15 tests de `test_detectors.py` passent ; un tableau seuil, délai, alarmes fausses |
| 4 | Tableau de bord généré | 3 h | les 3 tests de `test_dashboard.py` passent ; un `dashboard.json` joint |
| 5 | Mesures, runbook et ADR | 3 h | une page de résultats, un runbook d'une page par panne, un ADR |

~~~bash
cd labs/projects/gpu-observability
sudo apt-get install -y prometheus            # promtool
export PYTHON=/chemin/vers/python             # pytest et pyyaml suffisent
IMPL=starter $PYTHON -m pytest -q tests       # 26 échecs sur 28 au départ
PYTHON=$PYTHON bash verify.sh                  # référence verte, départ rouge
cd starter/rules && promtool test rules gpu.rules.test.yml
~~~

Le test de mutation vaut le détour. Il copie vos règles, en modifie une (durée `for` portée à 90 minutes, ou comparaison inversée), relance `promtool test rules` et exige un échec. Une suite de tests qui passe encore sur une règle cassée ne protège de rien.

Un cas qui franchit le seuil après la durée `for` suffit à tuer ces huit mutants ; des cas qui restent en deçà et des instants d'évaluation encore *en attente* (avant la fin de `for`) tuent aussi des mutants plus fins, comme une durée raccourcie.

Copiez dans vos séries de test les étiquettes que l'exportateur ajoute (`UUID`, `modelName`) : sans elles, une jointure qui échouerait sur les vraies séries passe quand même vos tests.

## Livrables {#livrables}

Votre dépôt public contient :

- le code complété, les règles, leurs tests `promtool` et la commande unique qui lance tout ;
- `dashboard.json` généré ;
- une page de **mesures** : pour chaque détecteur, le délai de détection et le taux d'alarmes fausses, avec les valeurs de seuil essayées ;
- un **runbook** d'une page par panne (job bloqué, traînard, XID) : ce que l'alerte signifie, ce qu'il faut vérifier, dans quel ordre, quand vider le nœud, avec la structure donnée dans [Écrire un ADR et un runbook](../../lab-setup/index.html#adr-runbook) ;
- un **ADR** d'une page au format de `adr_template.md`, vérifié par `adr_lint.py` (même section).

L'ADR tranche au moins quatre questions, en nommant l'alternative écartée :

1. Pourquoi détecter un job bloqué par l'activité tensorielle plutôt que par l'utilisation GPU, et quelle hypothèse cela suppose-t-il ?
2. Où placer la jointure avec l'allocation (dans la règle, dans un exportateur, dans une [règle d'enregistrement](../../courses/observability/index.html#règles-denregistrement)) et que se passe-t-il quand la métrique d'allocation est absente ?
3. Comment avez-vous choisi les durées `for` et les seuils, et quel coût une alerte trop sensible fait-elle porter à la personne d'astreinte ?
4. Que se passe-t-il quand l'exportateur lui-même tombe, et comment le saurez-vous ?

## Critères de réussite {#criteres}

Chaque critère est mesurable ; la commande qui le montre est indiquée.

- **Format.** `promtool check metrics` lit la sortie de l'exportateur sans erreur d'analyse et ne signale que la casse des étiquettes `UUID`, `modelName` et `Hostname`, qui sont celles de dcgm-exporter. Il sort donc avec le code 3 (problèmes de style seulement), et non 0 ; le code 1 signalerait une erreur d'analyse. Commande : `pytest tests/test_exporter.py -k exposition`.
- **Règles.** `promtool check rules gpu.rules.yml` réussit et `promtool test rules gpu.rules.test.yml` réussit pour les quatre alertes.
- **Mutation.** Les huit mutants (quatre durées allongées, quatre comparaisons inversées) font tous échouer vos tests. Commande : `pytest tests/test_rules.py -k mutated`.
- **Blocage.** Un job bloqué est détecté en au plus k·Δ = 300 s (persistance k = 20 scrapes, Δ = 15 s), alors que le détecteur naïf par utilisation GPU ne le détecte **jamais**. Le test place la panne sur un scrape, à t = 1 800 s : le délai y vaut exactement (k − 1)·Δ, soit 285 s. Commande : `pytest tests/test_detectors.py -k "stalled or naive"`.
- **Traînard.** Un GPU ralenti est signalé après exactement sept intervalles (k = 8, soit 105 s), **lui seul** est signalé, et aucun traînard n'est déclaré sur un job bloqué (ni l'inverse). Commande : `pytest tests/test_detectors.py -k "straggler or confuse"`.
- **Alarmes fausses.** Sur 1 024 GPU-heures sans panne, aucune alerte des deux détecteurs. Commande : `pytest tests/test_detectors.py -k no_false_alarm`. Vous savez dire ce que cela prouve : le taux est inférieur à environ 3 divisés par 1 024, soit 0,003 alarme par GPU-heure (0,3 pour 100 GPU-heures), avec 95 % de confiance, **si** les observations sont indépendantes, ce qu'elles ne sont pas tout à fait.
- **Limite de ce zéro.** Le simulateur ne contient aucune phase légitimement creuse : chargement des données, écriture d'un checkpoint (point de reprise), évaluation. Sur un vrai cluster, ce sont elles qui feront les fausses alertes de `JobStalled` (voir le [module de tolérance aux pannes](../../courses/fault-tolerance/index.html)).
- **Tableau de bord.** Chaque expression passe `promtool check rules`, n'utilise que des métriques de l'exportateur et, pour les panneaux par job, joint l'allocation. Commande : `pytest tests/test_dashboard.py`.

## Pistes et indices {#pistes}

Ces indices ne donnent pas la solution ; essayez d'abord sans.

**Jointure.** dcgm-exporter décrit des GPU, Slurm décrit des jobs. Pour agréger par job, multipliez la métrique du GPU par la métrique d'allocation, valeur 1, en associant sur `Hostname` et `gpu` et en ramenant l'étiquette du job avec `group_left`. Vérifiez ce qui arrive aux GPU sans allocation : la multiplication les fait disparaître, ce qui est voulu ici.

**Moyenne ou médiane.** Une règle `JobStalled` écrite avec `avg by (job)`, comme celle du [module 14, § 3.2](../../courses/observability/index.html#la-cardinalité-et-le-piège-de-létiquette-job), et le détecteur Python, dont un test impose la médiane (R6), ne disent pas la même chose. Sur un job de huit GPU dont cinq sont à 0 et trois à 0,9, la médiane vaut 0 (alerte) et la moyenne 0,34 (silence). PromQL calcule aussi une médiane, `quantile by (job) (0.5, …)` : consignez dans l'ADR la statistique que porte votre règle, et pourquoi.

**Durée `for`.** Une alerte passe par l'état « en attente » avant de se déclencher. Pour la tester, évaluez avant et après la durée : l'état avant doit être silencieux, l'état après doit être actif. L'écriture `0.55x39` de `promtool` produit **quarante** échantillons, pas trente-neuf : la notation `axn` répète la valeur `n` fois après la première.

**XID.** Comme la jauge garde la dernière valeur, une règle `> 0` reste active jusqu'à la remise à zéro. C'est voulu ; décidez en revanche si le message doit nommer le code (`{{ $value }}`), et lisez le catalogue d'erreurs XID de NVIDIA avant d'écrire un runbook : il indique que certains codes sont journalisés pour des fautes de l'application, de sorte qu'une alerte de niveau `page` sur toute valeur non nulle est un choix à justifier dans l'ADR (le code 79 du simulateur est décrit comme « GPU has fallen off the bus »).

**Thermique.** L'alerte `GPUThermalThrottle` mesure une température (80 °C, valeur du simulateur, pas une limite constructeur) et non la cause du ralentissement ; le ralentissement lui-même se lit sur l'horloge SM, ce que regarde le détecteur de traînard.

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

Avec la persistance de huit scrapes et z de 6, le nombre d'alarmes tombe à zéro. À z de 6 sans persistance il reste seize alarmes, bien plus que ne le prédit une loi gaussienne (environ 10⁻⁹ par échantillon).

Mesure : l'échelle estimée par la MAD sur seulement 16 GPU sous-évalue parfois le bruit simulé de 10 MHz (elle tombe sous 5 MHz dans 3,8 % des scrapes de job), et le plancher de 5 MHz vaut la moitié de ce bruit ; les seize alarmes correspondent à des écarts de 3,0 à 4,3 écarts types réels. En changeant seulement le plancher, le même essai donne 61 alarmes à 0 MHz, 16 à 5 MHz, puis aucune à 8 MHz ou plus. **Le plancher doit refléter le bruit d'une flotte saine.**

Ces zéros valent pour le simulateur, qui n'a aucune phase légitimement creuse ni aucune dérive lente d'horloge.

**Tests d'alertes.** Les quatre alertes de référence passent `promtool test rules` avec quatre scénarios, et les huit mutants sont tous détectés ; un seuil déplacé de peu (par exemple 84,9 °C au lieu de 80, ou 0,5 au lieu de 0,05 pour `JobStalled`) survit, parce que les séries de test sont loin des seuils.

**Avertissement de format.** `promtool check metrics` signale les étiquettes `UUID`, `modelName` et `Hostname` comme non conformes à la convention snake_case : ce sont celles de dcgm-exporter lui-même. La solution les conserve, parce que les règles et les tableaux de bord réels s'en servent ; c'est une décision à consigner dans l'ADR.
:::

## Extensions {#extensions}

- **Mutants plus fins.** Ajoutez des séries proches des seuils (79 °C et 81 °C, 0,04 et 0,06) jusqu'à tuer les mutants « seuil déplacé de peu » et « durée `for` raccourcie ».
- **Alerter sur l'absence.** Ajoutez une alerte qui se déclenche quand l'exportateur ne répond plus, avec `up` ou `absent`, et testez-la avec `promtool`. Un exportateur mort ressemble à un cluster sain.
- **Vrai dcgm-exporter.** Il faut une machine Linux avec deux GPU NVIDIA de centre de données de génération Volta ou plus récente : `default-counters.csv` réserve à ces GPU les métriques de profil comme `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`. Lancez dcgm-exporter, comparez ses séries à celles du simulateur, et **mesurez** le profil d'un blocage (utilisation, puissance, activité tensorielle) en tuant l'un des deux rangs d'un entraînement, un par GPU. C'est la validation qui manque à ce projet. Chiffrez la location avec la méthode de la page [Environnement de travail](../../lab-setup/index.html#budget).
- **Alertmanager.** Ajoutez regroupement, inhibition (un nœud en erreur XID masque les alertes de ses GPU) et silences, puis testez l'acheminement avec `amtool`.
- **Seuils appris.** Remplacez le plancher fixe du traînard par une estimation sur une fenêtre glissante de données saines et mesurez de nouveau délai et alarmes fausses.
- **Intégration Slurm.** Faites écrire la jointure d'allocation par un prolog et un épilog Slurm (module Slurm, chapitre sur la santé des nœuds) au lieu d'un fichier statique, ou comparez avec l'option `--hpc-job-mapping-dir` de dcgm-exporter.
- **Détecteur en Go ou en Rust.** Portez `StalledJob` et `Straggler` de `detectors.py` dans un service qui lit les échantillons ligne à ligne. Mêmes paramètres : activité tensorielle médiane sous 0,05 pendant 20 scrapes ; z de 6 sur l'échelle max(1,4826 × MAD ; 5 MHz), 8 scrapes ; médiane d'un nombre pair de valeurs égale à la moyenne des deux centrales (`statistics.median`). Le simulateur reste en Python : faites-lui écrire en JSON Lines les échantillons de quelques graines et pannes, et les alertes du code Python. La preuve : mêmes alertes au même scrape, même tableau délai / alarmes fausses.

## Pour le portfolio {#portfolio}

**Structure du dépôt.** Un `README.md` d'un écran : les trois pannes, le schéma exportateur, règles, détecteurs et tableau de bord, la commande qui lance les 28 tests, le tableau des délais et des alarmes fausses, et un paragraphe « ce qui n'est pas validé sur matériel réel ».

**Ce qu'il faut montrer.** Les tests `promtool`, le test de mutation, le tableau seuil-délai-alarmes et le runbook. Le tableau de bord vient en dernier : il ne prouve rien tout seul.

**Ce qu'un recruteur d'infrastructure de calcul cherche.** Quelqu'un qui sait que l'utilisation GPU ne dit pas si le job travaille, qui chiffre ses détecteurs au lieu de les affirmer, qui teste ses alertes comme du code, et qui dit ce qu'il n'a pas pu valider.

::: note
[Zéro événement observé n'est pas zéro risque]{.tag} Voir aucune alarme fausse sur 1 024 GPU-heures permet seulement d'affirmer, avec 95 % de confiance, que le taux est inférieur à environ 3/1 024 par GPU-heure (règle des trois), si les observations sont indépendantes. Les GPU d'un même job ne le sont pas : l'incertitude réelle est plus grande. Écrivez la borne, pas « zéro ».
:::

Trois accroches **honnêtes**, à adapter à ce que vous avez réellement fait :

1. « J'ai écrit des règles d'alerte GPU dont les tests `promtool` échouent quand on casse la règle (mutation de la durée et de la comparaison), et un détecteur de job bloqué qu'une alerte fondée sur l'utilisation GPU ne voit pas. »
2. « J'ai mesuré délai de détection et alarmes fausses d'un détecteur de traînard pour plusieurs seuils sur un cluster simulé, et montré qu'un plancher d'échelle inférieur au bruit laisse passer des alarmes fausses (16 en 1 024 GPU-heures à z de 6 sans persistance, 0 avec un plancher de 8 MHz). »
3. « Je sais dire ce que ce projet ne valide pas : le profil réel d'un blocage sur GPU, et le comportement à grande échelle. »

### Formules du projet {#formules}

Le score robuste d'un GPU, avec x sa mesure, m la médiane de son job et MAD l'écart absolu médian :

$$z = \frac{x - m}{\max\bigl(1{,}4826\,\mathrm{MAD},\; \text{plancher}\bigr)}$$

Le délai de détection d'un détecteur à persistance k, avec un scrape toutes les Δ secondes, est de (k − 1)·Δ si la panne tombe sur un scrape, et d'au plus k·Δ sinon. La règle des trois borne le taux d'un événement non observé en n essais :

$$p < \frac{3}{n} \quad (95\ \%)$$

### Pour aller plus loin {#lectures}

- Llama Team, *The Llama 3 Herd of Models*, 2024 : section sur la fiabilité, le diagnostic des blocages et des traînards, [arxiv.org/abs/2407.21783](https://arxiv.org/abs/2407.21783).
- Documentation de Prometheus, branche 3.x : [tests unitaires de règles](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/) (`promtool test rules`) et [règles d'alerte](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/).
- Dépôt [NVIDIA/dcgm-exporter](https://github.com/NVIDIA/dcgm-exporter) : liste de compteurs par défaut.
