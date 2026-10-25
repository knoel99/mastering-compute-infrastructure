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
numbered: true
---

## Contexte et objectif {#contexte}

Un même GPU se vend sous plusieurs formes : à la demande, cher mais fiable, ou préemptible (*spot*), moins cher mais que le fournisseur peut reprendre à tout moment. Plusieurs fournisseurs et plusieurs régions multiplient les choix. La question de l'ingénieur d'infrastructure n'est pas « quelle offre est la moins chère par heure ? » mais **« où lancer ce job, avec quelle fréquence de checkpoint, et que faire quand on me le reprend ? »**.

Ce projet vous fait construire un simulateur qui répond à cette question par des chiffres reproductibles : des jobs arrivent, des politiques les placent, des interruptions détruisent le travail non sauvegardé, et l'on compare les coûts et les échéances manquées. Il se termine par la production des fichiers de configuration (tâches SkyPilot, un lanceur de jobs multi-cloud, et files Kueue, le système de files de jobs de Kubernetes) qui appliqueraient la politique retenue.

::: war
[Toutes les données sont inventées]{.tag} Les prix sont en unités arbitraires, les capacités et les taux d'interruption sont fabriqués pour le projet. **Ne les lisez pas comme le marché.** Aucun prix de fournisseur n'est cité sur cette page : les tarifs changent, varient selon la région et la disponibilité. Pour une étude réelle, relevez vous-même les prix le jour de l'étude, sur les pages des fournisseurs.
:::

::: key
[Idée centrale du projet]{.tag} Le prix par heure n'est pas le coût d'une heure **utile**. Une offre à prix bas qui interrompt souvent fait perdre du travail et en fait refaire : son coût par heure productive peut dépasser celui d'une offre plus chère et plus stable. Le projet vous fait chiffrer cet écart, avec la formule de Young et Daly du [projet 3](../resilient-trainer/index.html) pour choisir la fréquence de checkpoint. Sur les données inventées du projet, une ablation (section « Résultats ») montre que la fréquence de checkpoint pèse plus que le choix de l'offre.
:::

### Prérequis de connaissances {#pre}

Vous devez savoir lire un code Python de deux cents lignes et écrire des tests. Les notions de checkpoint, de reprise et de période optimale viennent du projet 3 : relisez sa section sur Young et Daly. Les modules « multi-cloud », « FinOps et capacité » et « Kubernetes pour les GPU » du parcours approfondissent le contexte ; ils ne sont pas requis pour faire le projet, qui rappelle ce dont il a besoin.

## Cahier des charges {#cahier}

Le dossier `labs/projects/multi-provider-scheduler/` contient `starter/` (à compléter), `reference/` (à consulter **après** votre tentative), `tests/` (33 tests) et `verify.sh`. Les données (`data.py`) sont fournies : quatre offres synthétiques et un générateur de jobs.

| ID | Exigence | Test qui la vérifie |
|---|---|---|
| R1 | **Moteur** minute par minute, avec les règles de facturation, de checkpoint et d'interruption décrites dans `sim.py` ; la capacité n'est jamais dépassée | `tests/test_sim.py` (12 tests) |
| R2 | **Chronologie exacte** : sans interruption, un job de 300 min de travail, avec démarrage de 10 min et checkpoints de 5 min toutes les 60 min, finit 330 min après son arrivée ; avec une interruption forcée à 100 min (coût de reprise nul dans ce test), 365 min après | `test_timeline_*`, `test_forced_interruption_*` |
| R3 | **Tirages communs** : la « chance » d'interruption d'une allocation ne dépend que de (graine, job, numéro d'allocation), jamais de la politique | `test_interruption_luck_is_common_*` |
| R4 | **Trois politiques** : moins cher par heure, à la demande seulement, et une politique « couverte » qui minimise le coût attendu par heure productive avec garde d'échéance | `tests/test_policies.py` (8 tests) |
| R5 | **Comparaison appariée** : mêmes jobs et mêmes interruptions pour chaque politique, différence par graine avec intervalle bootstrap | `tests/test_compare.py` (6 tests) |
| R6 | **Tâches SkyPilot** et **manifestes Kueue** générés, avec validation structurelle (références croisées, quotas entiers, version d'API) | `tests/test_manifests.py` (7 tests) |

Le moteur suit une sémantique précise, donnée dans la docstring de `sim.py`. Un job en attente est proposé à la politique au début de chaque minute, dans l'ordre d'arrivée. Une allocation est facturée dès sa première minute, démarrage et checkpoints compris. Une interruption fait perdre toute la progression non sauvegardée, et le job est reproposé la même minute. Le dernier segment de calcul n'est pas suivi d'un checkpoint.

## Jalons {#jalons}

| N° | Jalon | Durée | Preuve |
|---|---|---|---|
| 1 | Moteur de simulation (`sim.py`) | 6 h | les 12 tests de `test_sim.py` passent, dont les deux chronologies exactes |
| 2 | Les trois politiques (`policies.py`) | 5 h | les 8 tests de `test_policies.py` passent |
| 3 | Comparaison appariée (`compare.py`) | 5 h | les 6 tests de `test_compare.py` passent ; un tableau de résultats sur 20 graines |
| 4 | Tâches SkyPilot et manifestes Kueue (`manifests.py`) | 4 h | les 7 tests de `test_manifests.py` passent ; `yamllint` propre sur vos fichiers |
| 5 | ADR et lecture critique | 4 h | un ADR d'une page ; une page des limites de l'étude |

Commencez par le moteur et ses deux chronologies exactes : calculez-les **à la main** avant de coder, comme le fait le commentaire du test. Un moteur dont on ne sait pas prédire la sortie sur un cas à un job n'est pas fiable sur trente.

~~~bash
cd labs/projects/multi-provider-scheduler
export PYTHON=/chemin/vers/python           # pytest, pyyaml et yamllint
IMPL=starter $PYTHON -m pytest -q tests     # 33 échecs sur 33 au départ
PYTHON=$PYTHON bash verify.sh                # référence verte, départ rouge
~~~

## Livrables {#livrables}

Votre dépôt public contient :

- le code complété, les tests et la commande unique qui les lance ;
- le tableau comparatif des trois politiques sur 20 graines, avec moyennes, intervalles **et différences appariées** ;
- au moins une tâche SkyPilot et un jeu de manifestes Kueue générés par votre code, avec une phrase disant qu'ils n'ont **pas** été appliqués à un vrai compte ou cluster ;
- un **ADR** (*Architecture Decision Record*, note qui consigne une décision et l'alternative écartée) d'une page ;
- une page « lecture critique » : trois choses que votre simulation ne permet pas de conclure.

L'ADR tranche au moins quatre questions, en nommant l'alternative écartée :

1. Pourquoi des tirages communs aux politiques plutôt que des tirages indépendants, et qu'est-ce que cela change à la précision de la comparaison ?
2. Pourquoi un pas de une minute, et qu'est-ce qu'un événement discret changerait au résultat ou au temps de calcul ?
3. Que dit votre politique couverte quand toutes les offres préemptibles sont trop risquées pour l'échéance, et à quoi renonce-t-elle ?
4. Quelles données réelles faudrait-il collecter pour croire les conclusions, et comment les collecteriez-vous sans citer de prix périmés ?

## Critères de réussite {#criteres}

Chaque critère est mesurable ; la commande qui le montre est indiquée.

- **Chronologies exactes.** Job sans interruption : fin 330 min après l'arrivée et 330 minutes facturées ; avec interruption forcée à 100 min (coût de reprise nul) : fin 365 min après l'arrivée, 25 minutes perdues. Commande : `pytest tests/test_sim.py -k "timeline or forced"`.
- **Capacité.** Sur les trois politiques, aucun pic de GPU simultanés ne dépasse la capacité d'une offre. Commande : `pytest -k capacity_and_cost`.
- **Comptabilité.** Le coût total est égal à la somme du grand livre des allocations et à la somme des coûts par job, à l'arrondi flottant près. Commande : `pytest -k capacity_and_cost`.
- **Politique couverte.** Sur 8 graines, elle coûte moins que chacune des deux autres **sur chaque graine** et manque moins d'échéances (différence appariée dont l'intervalle est entièrement négatif). Commande : `pytest tests/test_compare.py`.
- **Le moins cher par heure n'est pas le moins cher.** La politique « moins cher par heure » perd au moins cinq fois plus d'heures de progression que la politique couverte. Mesuré par `test_cheapest_per_hour_is_not_cheapest_overall`.
- **Manifestes.** Les huit mutations testées (flavor inconnu, file inconnue, quota en texte, doublon, mauvaise version d'API, quota négatif, quota booléen, ressource absente de `coveredResources`) sont toutes rejetées. Commande : `pytest tests/test_manifests.py`.
- **Honnêteté.** Votre README dit que les données sont inventées et que les manifestes ne sont validés que structurellement.

## Pistes et indices {#pistes}

Ces indices ne donnent pas la solution ; essayez d'abord sans.

**Moteur.** Écrivez d'abord un job, une offre, aucune interruption, et prédisez la minute de fin. Le piège classique est un décalage d'une minute : une allocation est facturée dès la minute où elle commence, et la fin d'un job est la minute **suivant** sa dernière minute de calcul.

Vérifiez aussi que la capacité est restituée **avant** de proposer les jobs en attente, sinon un job attend une minute de trop.

**Tirages communs.** (`_fail_after`, fournie dans `sim.py`, applique déjà ce principe ; à vous de l'appeler avec le bon numéro d'allocation.) Tirer les interruptions dans un seul générateur global rend le résultat d'une politique dépendant de l'ordre dans lequel les autres jobs consomment des nombres : deux politiques ne rencontrent plus la même malchance. Un générateur propre à chaque allocation, initialisé par (graine, job, numéro), corrige cela et réduit la variance de la **différence** entre politiques.

**Temps d'interruption.** Cette fonction vous est fournie ; voici pourquoi elle est écrite ainsi. Pour une interruption de taux constant, le temps jusqu'à l'interruption suit une loi exponentielle : à partir d'un tirage uniforme $u$, il vaut $-\ln(1-u)$ divisé par le taux par minute. Elle arrondit au-dessus et garde au moins une minute.

**Politique couverte.** Le coût attendu par heure productive est le prix divisé par un moins la fraction de gaspillage, que la formule de Young et Daly de la section « [Formules du projet](#formules) », plus bas, fournit. Écrivez-la d'abord à la main pour deux offres, vérifiez qu'une offre moins chère par heure peut perdre (essayez 1,5 interruption par heure ; avec les offres du projet, l'écart est plus fin), puis codez. N'oubliez pas la garde d'échéance : une offre préemptible n'est admissible que s'il reste de la marge.

**Comparaison.** Deux intervalles de moyennes qui se recouvrent ne prouvent pas que deux politiques sont indiscernables : si les mêmes jobs et les mêmes interruptions sont rejoués, la **différence par graine** est bien plus précise. Calculez-la, avec son intervalle et le nombre de graines où chaque politique gagne.

**Manifestes.** Dans Kueue, un travail reçoit « the first flavor in the ClusterQueue's .spec.resourceGroups[*].flavors list that has enough unused nominalQuota » : l'**ordre** des flavors exprime la préférence. Dans SkyPilot, `ordered` fait basculer dans l'ordre indiqué, alors que pour `any_of` « the failover order will be decided by the optimizer ». Vérifiez les noms de champs dans la documentation de **votre** version.

Une tâche SkyPilot peut aussi mélanger spot et à la demande : sa page sur les jobs gérés donne l'exemple `any_of: [{use_spot: true}, {use_spot: false}]`. Ce projet génère deux tâches, une par marché, pour garder des fichiers simples à valider.

### Résultats de la solution de référence {#reference-results}

À lire **après** votre propre travail. Le simulateur est déterministe : ces valeurs sont reproductibles, mais elles dépendent entièrement des données inventées du projet.

::: sol
**Scénario.** Trente jobs de 8, 16 ou 32 GPU, arrivant sur 3 jours, avec 6 à 48 heures de travail. Quatre offres : deux à la demande (64 GPU chacune), deux préemptibles (64 et 32 GPU, taux d'interruption de 0,15 et 0,60 par heure). 

La demande moyenne est de **14 617 GPU-heures** de travail (de 11 199 à 19 039 selon la graine), contre **9 216 GPU-heures** à la demande disponibles pendant les 72 heures d'arrivée : le scénario est contraint en capacité, ce qui explique que la politique « à la demande seulement » manque aussi des échéances (de l'attente, pas des pannes).

**Moyennes sur 20 graines.**

| politique | coût (u) | échéances manquées | interruptions | heures de progression perdues (heures-job) |
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

**Lecture.** La politique couverte gagne partout : la politique « moins cher par heure » perd 398 heures de progression, contre 42 pour la couverte. Entre « moins cher » et « à la demande », le coût diffère nettement mais **les échéances ne se départagent pas** (l'intervalle contient zéro) : c'est exactement ce qu'un tableau de moyennes seul aurait caché.

**Mais pas pour la raison que l'énoncé laisse attendre.** Avec C = 3 min et R = 10 min, l'offre préemptible risquée (3 u, 0,60 interruption par heure) n'est **pas** plus chère par heure productive que l'autre (4 u, 0,15 par heure) : 4,58 u contre 4,69 u (formules plus bas).

Elle ne devient ruineuse qu'avec l'intervalle fixe de 240 min de la politique « moins cher », pour lequel le modèle du premier ordre donne un gaspillage supérieur à 1 (il sort alors de son domaine : cela dit seulement que cet intervalle est très mauvais pour cette offre). Une ablation (`reference/ablation.py`, hors tests) sépare les deux leviers, le placement et l'intervalle de checkpoint :

| variante | coût (u) | échéances manquées | heures perdues |
|---|---|---|---|
| moins cher par heure (intervalle 240 min) | 144 091 | 7,40 | 398 |
| moins cher par heure + intervalle de Young et Daly | 120 631 | 2,55 | 42 |
| couverte avec intervalle 240 min | 142 746 | 4,15 | 228 |
| couverte (intervalle de Young et Daly) | 120 567 | 2,05 | 42 |

Changer **seulement** l'intervalle retire 23 459 u de coût [−25 721 ; −21 255], soit presque tout l'écart de 23 524 u.

Le placement par coût attendu et la garde d'échéance n'ajoutent que −64 u [−1 498 ; +1 265], indiscernables de zéro, et −0,5 échéance manquée [−0,9 ; −0,1]. Dans ce scénario inventé, c'est la fréquence de checkpoint qui compte ; l'offre à 0,60 interruption par heure reste à 4,58 u contre 4,69 u.

Le taux pour lequel les deux coûts attendus s'égalent est d'environ 0,64 interruption par heure : au-delà, l'offre à 3 u devient plus chère par heure utile et le placement par coût attendu devrait peser davantage. Cette simulation ne le teste pas (voir l'extension « Taux de l'offre risquée »).
:::

## Extensions {#extensions}

- **Interruptions corrélées.** Dans la réalité, une interruption préemptible dans une région signale souvent une pénurie dans cette région : la documentation de SkyPilot écrit « preemptions in a region usually indicate a shortage of resources in that region ». Modélisez des pannes simultanées par région et mesurez ce que cela fait à une politique qui se rabat dans la même région.
- **Taux de l'offre risquée.** Faites varier le taux d'interruption de l'offre à 3 u de 0,3 à 2 par heure et reprenez l'ablation : à partir de quel taux le placement par coût attendu, et non seulement l'intervalle de checkpoint, change-t-il le coût ? Comparez avec le croisement calculé à la main (environ 0,64).
- **Capacité qui varie.** Remplacez les capacités constantes par des capacités qui fluctuent et mesurez l'effet sur les échéances.
- **Coûts cachés.** Ajoutez le coût de sortie de données entre régions et le coût du stockage des checkpoints ; qu'est-ce qui change dans le classement ?
- **Terraform.** Écrivez le module qui créerait les files de machines correspondantes et validez-le avec `terraform validate` ; c'est la validation que ce projet ne fait pas.
- **Compte réel.** Lancez une tâche SkyPilot sur un compte de test avec une limite de budget **créée avant** (voir la page [environnement de travail](../../lab-setup/index.html)) et comparez l'interruption observée à votre modèle.

## Pour le portfolio {#portfolio}

**Structure du dépôt.** Un `README.md` d'un écran : la question, l'avertissement sur les données inventées, le tableau comparatif avec les différences appariées, la commande qui lance les 33 tests, et un paragraphe « ce que cette simulation ne montre pas ».

**Ce qu'il faut montrer.** Les chronologies exactes testées, la comparaison appariée, l'ablation, les manifestes et l'ADR. Les noms de fournisseurs réels n'y ont pas leur place tant que vous n'avez pas collecté de vraies données.

**Ce qu'un recruteur d'infrastructure de calcul cherche.** Quelqu'un qui sait que le prix par heure n'est pas le coût d'une heure utile, qui compare des politiques avec des intervalles et des différences appariées plutôt qu'avec des moyennes seules, et qui sait dire à quel point une simulation sur données inventées engage ou n'engage pas.

::: note
[Pourquoi comparer par différences appariées]{.tag} Les intervalles des moyennes de coût de la politique couverte et de la politique « moins cher par heure » se recouvrent sur 12 graines ([109 547 ; 134 650] contre [132 100 ; 158 074] avec `python3 compare.py --seeds 12`) ; pourtant la couverte est moins chère sur **chaque** graine, de −23 315 u en moyenne [−26 855 ; −19 941].

Rejouer les mêmes jobs et les mêmes interruptions élimine la variabilité commune, et la différence par graine devient précise. Les intervalles de moyennes mélangent la variabilité entre scénarios, qui n'a rien à voir avec la comparaison.
:::

Trois accroches **honnêtes**, à adapter à ce que vous avez réellement fait :

1. « J'ai écrit un simulateur de placement sur offres préemptibles et à la demande, avec une chronologie testée à la minute près, et mesuré par ablation que, dans mon scénario inventé, la fréquence de checkpoint pèse plus que le choix de l'offre. »
2. « J'ai comparé trois politiques par différences appariées sur 20 graines, et montré que deux intervalles de moyennes qui se recouvrent peuvent cacher une différence nette. »
3. « Je sais dire ce que ma simulation ne dit pas : les prix et les taux d'interruption y sont inventés, et mes manifestes ne sont validés que structurellement. »

### Formules du projet {#formules}

Avec C le coût d'un checkpoint, M le temps moyen entre interruptions (60 divisé par le taux par heure, en minutes), R le coût d'une reprise et T le temps de calcul entre deux checkpoints, la fraction de gaspillage au premier ordre est :

$$W(T) = \frac{C}{T} + \frac{T/2 + R}{M}, \qquad T^{*} = \sqrt{2\,C\,M}$$

Le coût attendu par heure productive d'une offre de prix $p$ est alors :

$$\text{coût attendu} = \frac{p}{1 - W(T^{*})}$$

Pour une offre à la demande, $W$ vaut zéro et le coût attendu égale le prix. 

Un exemple de lecture, avec deux offres hypothétiques (celles du test `test_hedged_prefers_lower_expected_cost_per_productive_hour_over_lower_price`) : avec C de 3 min et R de 10 min, une offre à 4 u et 0,15 interruption par heure (M de 400 min) a un $T^{*}$ d'environ 49 min, un $W$ d'environ 0,15 et un coût attendu d'environ 4,7 u ; une offre à 3 u et 1,5 interruption par heure (M de 40 min) a un $W$ d'environ 0,64 et un coût attendu d'environ 8,3 u. La moins chère à l'heure devient la plus chère par heure utile.

Pour les offres **du projet** (3 u à 0,60 par heure, M de 100 min, $T^{*}$ d'environ 24 min, $W$ d'environ 0,34) le coût attendu est de 4,58 u, **sous** les 4,69 u de l'offre à 4 u : le croisement se situe vers 0,64 interruption par heure.

### Pour aller plus loin {#lectures}

- Documentation de SkyPilot, [spécification YAML](https://docs.skypilot.co/en/latest/reference/yaml-spec.html) : `accelerators`, `use_spot`, `any_of`, `ordered`, `job_recovery` (lue le 2026-10-24).
- Documentation de Kueue, pages [ClusterQueue](https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/), [ResourceFlavor](https://kueue.sigs.k8s.io/docs/concepts/resource_flavor/) et [LocalQueue](https://kueue.sigs.k8s.io/docs/concepts/local_queue/) : version d'API `kueue.x-k8s.io/v1beta2` à la date de lecture ; vérifiez la vôtre.
- Documentation de SkyPilot, page [jobs gérés](https://docs.skypilot.co/en/latest/examples/managed-jobs.html) : `use_spot` et `any_of` combinés (lue le 2026-10-24).
- Le [projet 3](../resilient-trainer/index.html) pour la formule de Young et Daly et son contrôle par simulation.
