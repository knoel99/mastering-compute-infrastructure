---
title: "Projet 4 — Placement multi-fournisseurs sensible aux coûts"
subtitle: "Projet 4 · 24 h · modules : multi-cloud, finops-capacity, kubernetes-gpu"
description: "Un simulateur de placement de jobs sur des offres à la demande et préemptibles, trois politiques comparées par différences appariées, et les manifestes SkyPilot et Kueue qui les matérialiseraient, validés hors ligne."
project:
  id: multi-provider-scheduler
  number: 4
  hours: 24
  modules: [multi-cloud, finops-capacity, kubernetes-gpu]
badges:
  - {label: "Portfolio", class: core}
  - {label: "Code de départ et solution vérifiés (CPU, sans cloud)", class: verified}
---

## Contexte et objectif {#contexte}

Un même GPU se vend sous plusieurs formes : à la demande, cher mais fiable, ou préemptible (*spot*), moins cher mais que le fournisseur peut reprendre à tout moment. Plusieurs fournisseurs et plusieurs régions multiplient les choix. La question de l'ingénieur d'infrastructure n'est pas « quelle offre est la moins chère par heure ? » mais **« où lancer ce job, avec quelle fréquence de checkpoint, et que faire quand on me le reprend ? »**.

Ce projet vous fait construire un simulateur qui répond à cette question par des chiffres reproductibles : des jobs arrivent, des politiques les placent, des interruptions détruisent le travail non sauvegardé, et l'on compare les coûts et les échéances manquées. Il se termine par la production des fichiers de configuration (tâches SkyPilot, files Kueue) qui appliqueraient la politique retenue.

::: war
[Toutes les données sont inventées]{.tag} Les prix sont en unités arbitraires, les capacités et les taux d'interruption sont fabriqués pour le projet. **Ne les lisez pas comme le marché.** Aucun prix de fournisseur n'est cité sur cette page : les tarifs changent, varient selon la région et la disponibilité. Pour une étude réelle, relevez vous-même les prix le jour de l'étude, sur les pages des fournisseurs.
:::

::: key
[Idée centrale du projet]{.tag} Le prix par heure n'est pas le coût d'une heure **utile**. Une offre à prix bas qui interrompt souvent fait perdre du travail et en fait refaire : son coût par heure productive peut dépasser celui d'une offre plus chère et plus stable. Le projet vous fait chiffrer cet écart, avec la formule de Young et Daly du [projet 3](../resilient-trainer/index.html) pour choisir la fréquence de checkpoint.
:::

### Prérequis de connaissances {#pre}

Vous devez savoir lire un code Python de deux cents lignes et écrire des tests. Les notions de checkpoint, de reprise et de période optimale viennent du projet 3 : relisez sa section sur Young et Daly. Les modules « multi-cloud », « FinOps et capacité » et « Kubernetes pour les GPU » du parcours approfondissent le contexte ; ils ne sont pas requis pour faire le projet, qui rappelle ce dont il a besoin.

## Cahier des charges {#cahier}

Le dossier `labs/projects/multi-provider-scheduler/` contient `starter/` (à compléter), `reference/` (à consulter **après** votre tentative), `tests/` (29 tests) et `verify.sh`. Les données (`data.py`) sont fournies : quatre offres synthétiques et un générateur de jobs.

| ID | Exigence | Test qui la vérifie |
|---|---|---|
| R1 | **Moteur** minute par minute, avec les règles de facturation, de checkpoint et d'interruption décrites dans `sim.py` ; la capacité n'est jamais dépassée | `tests/test_sim.py` (11 tests) |
| R2 | **Chronologie exacte** : sans interruption, un job de 300 min de travail, avec démarrage de 10 min et checkpoints de 5 min toutes les 60 min, finit à la minute 330 ; avec une interruption forcée à 100 min, à la minute 365 | `test_timeline_*`, `test_forced_interruption_*` |
| R3 | **Tirages communs** : la « chance » d'interruption d'une allocation ne dépend que de (graine, job, numéro d'allocation), jamais de la politique | `test_interruption_luck_is_common_*` |
| R4 | **Trois politiques** : moins cher par heure, à la demande seulement, et une politique « couverte » qui minimise le coût attendu par heure productive avec garde d'échéance | `tests/test_policies.py` (6 tests) |
| R5 | **Comparaison appariée** : mêmes jobs et mêmes interruptions pour chaque politique, différence par graine avec intervalle bootstrap | `tests/test_compare.py` (5 tests) |
| R6 | **Tâches SkyPilot** et **manifestes Kueue** générés, avec validation structurelle (références croisées, quotas entiers, version d'API) | `tests/test_manifests.py` (7 tests) |

Le moteur suit une sémantique précise, donnée dans la docstring de `sim.py`. Un job en attente est proposé à la politique au début de chaque minute, dans l'ordre d'arrivée. Une allocation est facturée dès sa première minute, démarrage et checkpoints compris. Une interruption fait perdre toute la progression non sauvegardée, et le job est reproposé la même minute. Le dernier segment de calcul n'est pas suivi d'un checkpoint.

## Jalons {#jalons}

| N° | Jalon | Durée | Preuve |
|---|---|---|---|
| 1 | Moteur de simulation (`sim.py`) | 6 h | les 11 tests de `test_sim.py` passent, dont les deux chronologies exactes |
| 2 | Les trois politiques (`policies.py`) | 5 h | les 6 tests de `test_policies.py` passent |
| 3 | Comparaison appariée (`compare.py`) | 5 h | les 5 tests de `test_compare.py` passent ; un tableau de résultats sur 20 graines |
| 4 | Tâches SkyPilot et manifestes Kueue (`manifests.py`) | 4 h | les 7 tests de `test_manifests.py` passent ; `yamllint` propre sur vos fichiers |
| 5 | ADR et lecture critique | 4 h | un ADR d'une page ; une page des limites de l'étude |

Commencez par le moteur et ses deux chronologies exactes : calculez-les **à la main** avant de coder, comme le fait le commentaire du test. Un moteur dont on ne sait pas prédire la sortie sur un cas à un job n'est pas fiable sur trente.

~~~bash
cd labs/projects/multi-provider-scheduler
export PYTHON=/chemin/vers/python           # pytest, pyyaml et yamllint
IMPL=starter $PYTHON -m pytest -q tests     # 28 échecs sur 29 au départ
PYTHON=$PYTHON bash verify.sh                # référence verte, départ rouge
~~~

## Livrables {#livrables}

Votre dépôt public contient :

- le code complété, les tests et la commande unique qui les lance ;
- le tableau comparatif des trois politiques sur 20 graines, avec moyennes, intervalles **et différences appariées** ;
- au moins une tâche SkyPilot et un jeu de manifestes Kueue générés par votre code, avec une phrase disant qu'ils n'ont **pas** été appliqués à un vrai compte ou cluster ;
- un **ADR** d'une page ;
- une page « lecture critique » : trois choses que votre simulation ne permet pas de conclure.

L'ADR tranche au moins quatre questions, en nommant l'alternative écartée :

1. Pourquoi des tirages communs aux politiques plutôt que des tirages indépendants, et qu'est-ce que cela change à la précision de la comparaison ?
2. Pourquoi un pas de une minute, et qu'est-ce qu'un événement discret changerait au résultat ou au temps de calcul ?
3. Que dit votre politique couverte quand toutes les offres préemptibles sont trop risquées pour l'échéance, et à quoi renonce-t-elle ?
4. Quelles données réelles faudrait-il collecter pour croire les conclusions, et comment les collecteriez-vous sans citer de prix périmés ?

## Critères de réussite {#criteres}

Chaque critère est mesurable ; la commande qui le montre est indiquée.

- **Chronologies exactes.** Job sans interruption : fin à la minute 330 et 330 minutes facturées ; avec interruption forcée à 100 min : fin à la minute 365, 25 minutes perdues. Commande : `pytest tests/test_sim.py -k "timeline or forced"`.
- **Capacité.** Sur les trois politiques, aucun pic de GPU simultanés ne dépasse la capacité d'une offre. Commande : `pytest -k capacity_and_cost`.
- **Comptabilité.** Le coût total est égal à la somme du grand livre des allocations et à la somme des coûts par job, à l'arrondi flottant près.
- **Politique couverte.** Sur 8 graines, elle coûte moins que chacune des deux autres **sur chaque graine** et manque moins d'échéances (différence appariée dont l'intervalle est entièrement négatif). Commande : `pytest tests/test_compare.py`.
- **Le moins cher par heure n'est pas le moins cher.** La politique « moins cher par heure » perd au moins cinq fois plus d'heures de progression que la politique couverte. Mesuré par `test_cheapest_per_hour_is_not_cheapest_overall`.
- **Manifestes.** Les cinq mutations testées (flavor inconnu, file inconnue, quota en texte, doublon, mauvaise version d'API) sont toutes rejetées. Commande : `pytest tests/test_manifests.py`.
- **Honnêteté.** Votre README dit que les données sont inventées et que les manifestes ne sont validés que structurellement.

## Pistes et indices {#pistes}

Ces indices ne donnent pas la solution ; essayez d'abord sans.

**Moteur.** Écrivez d'abord un job, une offre, aucune interruption, et prédisez la minute de fin. Le piège classique est un décalage d'une minute : une allocation est facturée dès la minute où elle commence, et la fin d'un job est la minute **suivant** sa dernière minute de calcul.

Vérifiez aussi que la capacité est restituée **avant** de proposer les jobs en attente, sinon un job attend une minute de trop.

**Tirages communs.** Tirer les interruptions dans un seul générateur global rend le résultat d'une politique dépendant de l'ordre dans lequel les autres jobs consomment des nombres : deux politiques ne rencontrent plus la même malchance. Un générateur propre à chaque allocation, initialisé par (graine, job, numéro), corrige cela et réduit la variance de la **différence** entre politiques.

**Temps d'interruption.** Pour une interruption de taux constant, le temps jusqu'à l'interruption suit une loi exponentielle : à partir d'un tirage uniforme $u$, il vaut $-\ln(1-u)$ divisé par le taux par minute. Arrondissez au-dessus et gardez au moins une minute.

**Politique couverte.** Le coût attendu par heure productive est le prix divisé par un moins la fraction de gaspillage, que la formule de Young et Daly de la section suivante fournit. Écrivez-la d'abord à la main pour deux offres, vérifiez que l'offre moins chère par heure peut perdre, puis codez. N'oubliez pas la garde d'échéance : une offre préemptible n'est admissible que s'il reste de la marge.

**Comparaison.** Deux intervalles de moyennes qui se recouvrent ne prouvent pas que deux politiques sont indiscernables : si les mêmes jobs et les mêmes interruptions sont rejoués, la **différence par graine** est bien plus précise. Calculez-la, avec son intervalle et le nombre de graines où chaque politique gagne.

**Manifestes.** Dans Kueue, un travail reçoit « the first flavor in the ClusterQueue's .spec.resourceGroups[*].flavors list that has enough unused nominalQuota » : l'**ordre** des flavors exprime la préférence. Dans SkyPilot, `ordered` fait basculer dans l'ordre indiqué, alors que pour `any_of` « the failover order will be decided by the optimizer ». Vérifiez les noms de champs dans la documentation de **votre** version.

### Résultats de la solution de référence {#reference-results}

À lire **après** votre propre travail. Le simulateur est déterministe : ces valeurs sont reproductibles, mais elles dépendent entièrement des données inventées du projet.

::: sol
**Scénario.** Trente jobs de 8, 16 ou 32 GPU, arrivant sur 3 jours, avec 6 à 48 heures de travail. Quatre offres : deux à la demande (64 GPU chacune), deux préemptibles (64 et 32 GPU, taux d'interruption de 0,15 et 0,60 par heure). 

La demande moyenne est de **14 617 GPU-heures** de travail (de 11 199 à 19 039 selon la graine), contre **9 216 GPU-heures** à la demande disponibles pendant les 72 heures d'arrivée : le scénario est contraint en capacité, ce qui explique que la politique « à la demande seulement » manque aussi des échéances (de l'attente, pas des pannes).

**Moyennes sur 20 graines.**

| politique | coût (u) | échéances manquées | interruptions | heures de progression perdues |
|---|---|---|---|---|
| moins cher par heure | 144 091 | 7,40 | 356 | 398 |
| à la demande seulement | 161 008 | 8,05 | 0 | 0 |
| couverte | 120 567 | 2,05 | 187 | 42 |

**Différences appariées** (a moins b, négatif = a meilleur ; intervalle bootstrap à 95 %) :

| comparaison | coût | échéances manquées |
|---|---|---|
| couverte moins moins-cher | −23 524 [−25 791 ; −21 226], meilleure sur 20/20 | −5,3 [−6,1 ; −4,6], 20/20 |
| couverte moins à-la-demande | −40 442 [−42 547 ; −38 583], 20/20 | −6,0 [−7,0 ; −5,0], 20/20 |
| moins-cher moins à-la-demande | −16 918 [−19 589 ; −14 464], 20/20 | −0,7 [−2,0 ; +0,8], 12/20 |

**Lecture.** La politique couverte gagne partout : l'offre préemptible la plus risquée (0,60 interruption par heure) est moins chère à l'heure, mais **plus chère par heure productive**, et la politique « moins cher par heure » y envoie ses jobs. Elle perd 398 heures de progression contre 42. Entre « moins cher » et « à la demande », le coût diffère nettement mais **les échéances ne se départagent pas** (l'intervalle contient zéro) : c'est exactement ce qu'un tableau de moyennes seul aurait caché.
:::

## Extensions {#extensions}

- **Interruptions corrélées.** Dans la réalité, une interruption préemptible dans une région signale souvent une pénurie dans cette région : la documentation de SkyPilot écrit « preemptions in a region usually indicate a shortage of resources in that region ». Modélisez des pannes simultanées par région et mesurez ce que cela fait à une politique qui se rabat dans la même région.
- **Capacité qui varie.** Remplacez les capacités constantes par des capacités qui fluctuent et mesurez l'effet sur les échéances.
- **Coûts cachés.** Ajoutez le coût de sortie de données entre régions et le coût du stockage des checkpoints ; qu'est-ce qui change dans le classement ?
- **Terraform.** Écrivez le module qui créerait les files de machines correspondantes et validez-le avec `terraform validate` ; c'est la validation que ce projet ne fait pas.
- **Compte réel.** Lancez une tâche SkyPilot sur un compte de test avec une limite de budget **créée avant** (voir la page [environnement de travail](../../lab-setup/index.html)) et comparez l'interruption observée à votre modèle.

## Pour le portfolio {#portfolio}

**Structure du dépôt.** Un `README.md` d'un écran : la question, l'avertissement sur les données inventées, le tableau comparatif avec les différences appariées, la commande qui lance les 29 tests, et un paragraphe « ce que cette simulation ne montre pas ».

**Ce qu'il faut montrer.** Les chronologies exactes testées, la comparaison appariée, les manifestes et l'ADR. Les noms de fournisseurs réels n'y ont pas leur place tant que vous n'avez pas collecté de vraies données.

**Ce qu'un recruteur d'infrastructure de calcul cherche.** Quelqu'un qui sait que le prix par heure n'est pas le coût d'une heure utile, qui compare des politiques avec des intervalles et des différences appariées plutôt qu'avec des moyennes seules, et qui sait dire à quel point une simulation sur données inventées engage ou n'engage pas.

::: note
[Pourquoi comparer par différences appariées]{.tag} Les intervalles des moyennes de coût de la politique couverte et de la politique « moins cher par heure » se recouvrent sur 12 graines ([109 547 ; 134 650] contre [132 100 ; 158 074] dans une première exécution) ; pourtant la couverte est moins chère sur **chaque** graine.

Rejouer les mêmes jobs et les mêmes interruptions élimine la variabilité commune, et la différence par graine devient précise. Les intervalles de moyennes mélangent la variabilité entre scénarios, qui n'a rien à voir avec la comparaison.
:::

Trois accroches **honnêtes**, à adapter à ce que vous avez réellement fait :

1. « J'ai écrit un simulateur de placement sur offres préemptibles et à la demande, avec une chronologie testée à la minute près, et montré que l'offre la moins chère par heure est la plus chère par heure productive. »
2. « J'ai comparé trois politiques par différences appariées sur 20 graines, et montré que deux intervalles de moyennes qui se recouvrent peuvent cacher une différence nette. »
3. « Je sais dire ce que ma simulation ne dit pas : les prix et les taux d'interruption y sont inventés, et mes manifestes ne sont validés que structurellement. »

### Formules du projet {#formules}

Avec C le coût d'un checkpoint, M le temps moyen entre interruptions (60 divisé par le taux par heure, en minutes), R le coût d'une reprise et T le temps de calcul entre deux checkpoints, la fraction de gaspillage au premier ordre est :

$$W(T) = \frac{C}{T} + \frac{T/2 + R}{M}, \qquad T^{*} = \sqrt{2\,C\,M}$$

Le coût attendu par heure productive d'une offre de prix $p$ est alors :

$$\text{coût attendu} = \frac{p}{1 - W(T^{*})}$$

Pour une offre à la demande, $W$ vaut zéro et le coût attendu égale le prix. 

Un exemple de lecture : avec C de 3 min et R de 10 min, une offre à 4 u et 0,15 interruption par heure (M de 400 min) a un $T^{*}$ d'environ 49 min, un $W$ d'environ 0,15 et un coût attendu d'environ 4,7 u ; une offre à 3 u et 1,5 interruption par heure (M de 40 min) a un $W$ d'environ 0,64 et un coût attendu d'environ 8,3 u. La moins chère à l'heure devient la plus chère par heure utile.

### Pour aller plus loin {#lectures}

- Documentation de SkyPilot, [spécification YAML](https://docs.skypilot.co/en/latest/reference/yaml-spec.html) : `accelerators`, `use_spot`, `any_of`, `ordered`, `job_recovery` (lue le 2026-10-24).
- Documentation de Kueue, pages [ClusterQueue](https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/), [ResourceFlavor](https://kueue.sigs.k8s.io/docs/concepts/resource_flavor/) et [LocalQueue](https://kueue.sigs.k8s.io/docs/concepts/local_queue/) : version d'API `kueue.x-k8s.io/v1beta2` à la date de lecture ; vérifiez la vôtre.
- Le [projet 3](../resilient-trainer/index.html) pour la formule de Young et Daly et son contrôle par simulation.
