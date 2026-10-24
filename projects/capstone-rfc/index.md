---
title: "Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU"
subtitle: "Projet 6 · 40 h · projet de synthèse, tous les modules d'infrastructure"
description: "Un document de conception complet pour une plateforme de calcul, un modèle de capacité et de coût exécutable dont les chiffres sont recoupés par le texte, une revue contradictoire par grille et une soutenance de vingt minutes."
project:
  id: capstone-rfc
  number: 6
  hours: 40
  modules: [slurm, provisioning, networking, storage, distributed-training, fault-tolerance, ray-rl-infra, kubernetes-gpu, multi-cloud, observability, finops-capacity, platform-leadership]
badges:
  - {label: "Projet de synthèse", class: core}
  - {label: "Modèle et vérificateur vérifiés (CPU) ; RFC jugée par grille humaine", class: verified}
---

## Contexte et objectif {#contexte}

Le métier de responsable d'infrastructure de calcul consiste moins à installer des machines qu'à **décider et à convaincre** : combien de GPU, de quel type, achetés comment, partagés selon quelle politique, supervisés par qui, avec quel plan si cela tourne mal. Ces décisions s'écrivent dans un document de conception (*RFC*, *request for comments*) que d'autres lisent, contestent et approuvent.

Ce projet de synthèse vous fait écrire une telle RFC pour une plateforme de 8 à 256 GPU, à partir d'un cahier des charges **fictif** fourni. Vous construisez le modèle de capacité et de coût qui étaye vos chiffres, un vérificateur qui contrôle que le texte et le modèle disent la même chose, puis vous soumettez le document à une revue contradictoire et vous le défendez à l'oral.

::: key
[Objectif du projet]{.tag} Produire un document qu'un lecteur sceptique peut vérifier : chaque chiffre vient d'un modèle exécutable que l'on peut relancer, chaque option a des inconvénients écrits, chaque risque a une mitigation, et les limites du modèle sont dites avant que quelqu'un ne les découvre.
:::

::: war
[Tout est fictif]{.tag} Le cahier des charges, les prix (en unités arbitraires), les taux de panne et d'interruption sont **inventés** pour l'exercice. La RFC de référence en tire des conclusions qui ne valent que pour ces données. Pour un usage réel, remplacez-les par vos mesures et par des prix relevés le jour de la décision.
:::

Le projet mobilise tout le parcours : la politique d'ordonnancement (module Slurm), le réseau et le stockage, la reprise après panne (projet 3), la mesure du passage à l'échelle (projet 2), la comparaison de politiques de placement (projet 4), l'observabilité (projet 5) et les arbitrages de coût. Il ne demande pas de tout refaire : il demande de **choisir, chiffrer et justifier**.

### Prérequis de connaissances {#pre}

Les projets 2 à 5 en sont les briques : relisez-les si besoin. Ce projet ajoute deux outils, la théorie des files d'attente pour estimer l'attente, et l'écriture technique. La théorie des files est rappelée dans les formules en fin de page ; l'écriture se travaille avec la grille de revue.

## Cahier des charges {#cahier}

Le dossier `labs/projects/capstone-rfc/` contient `starter/` (à compléter), `reference/` (modèle, vérificateur et une RFC complète à consulter **après** votre tentative), `tests/` (37 tests) et `verify.sh`. Le cahier des charges fictif est `requirements.yaml` : un groupe de recherche de 40 personnes, trois ingénieurs de plateforme, quatre classes de charge (pré-entraînement, réglage fin, évaluation, développement interactif), des objectifs d'attente, un budget mensuel.

| ID | Exigence | Test qui la vérifie |
|---|---|---|
| R1 | **Formule d'Erlang C** et statistiques d'attente d'une file M/M/c (probabilité d'attente, attente moyenne, 90e centile) | `test_erlang_c_exact_cases`, `test_wait_stats_mm1_closed_forms` |
| R2 | **Recoupement par simulation** : la formule et une simulation indépendante s'accordent à 5 % près | `test_formulas_agree_with_an_independent_simulation` |
| R3 | **Disponibilité utile** à la période de Young et Daly, avec une charge préemptible en plus | `test_goodput_closed_form_and_monotonicity` |
| R4 | **Évaluation d'une conception** : pools réservés (file, coût de la capacité), élastiques (coût à l'usage), verdict budget et SLO | `test_cost_accounting_*`, `test_candidate_designs_*` |
| R5 | **Vérificateur de RFC** : sections, options, tableau de décision, risques, bloc de conception, **coût du texte égal au coût du modèle** | `tests/test_rfc_lint.py` (28 tests) |
| R6 | **Votre RFC** passe le vérificateur | `test_my_rfc_passes_the_linter` |

Le vérificateur ne juge pas la qualité du raisonnement : il garantit la **cohérence mécanique** (le texte dit le coût que le modèle calcule) et la **présence** de ce qu'une revue exige. La qualité se juge avec la grille ci-dessous.

## Jalons {#jalons}

| N° | Jalon | Durée | Preuve |
|---|---|---|---|
| 1 | Modèle de capacité et de coût (`capacity.py`) | 8 h | les 9 tests de `test_capacity.py` passent, dont l'accord formule et simulation |
| 2 | Options et décision : au moins trois conceptions évaluées par le modèle | 6 h | un tableau d'options avec coût et verdict de SLO pour chacune |
| 3 | Rédaction de la RFC complète | 12 h | `rfc.md` de 1 500 mots au moins, toutes les sections |
| 4 | Vérificateur de RFC (`rfc_lint.py`) | 4 h | les 28 tests de `test_rfc_lint.py` passent et votre RFC passe |
| 5 | Revue contradictoire par grille | 4 h | la grille remplie par un relecteur autre que vous, et vos corrections |
| 6 | Soutenance de vingt minutes | 6 h | un support, la liste des questions préparées et leurs réponses |

~~~bash
cd labs/projects/capstone-rfc
export PYTHON=/chemin/vers/python           # pytest et pyyaml
IMPL=starter $PYTHON -m pytest -q tests     # 36 échecs sur 37 au départ
PYTHON=$PYTHON bash verify.sh                # référence verte, départ rouge
python3 starter/rfc_lint.py starter/rfc.md --requirements starter/requirements.yaml
~~~

Commencez par le modèle, pas par le texte : une RFC dont on ne peut pas relancer les chiffres est une opinion. Réécrivez ensuite la RFC en citant **seulement** ce que le modèle a calculé.

## Livrables {#livrables}

Votre dépôt public contient :

- `capacity.py`, `rfc_lint.py` et leurs tests, avec une commande unique qui les lance ;
- votre `rfc.md`, qui passe le vérificateur ;
- le tableau des conceptions évaluées, avec coût, verdict du budget et verdict de chaque objectif ;
- la **grille de revue** remplie par une autre personne, et la liste de ce que vous avez corrigé à sa suite ;
- le support de soutenance et vos réponses aux questions préparées ;
- une page « ce que ce modèle ne dit pas », qui reprend et complète les limites de la RFC.

Le document doit trancher, dans sa section « Décision », une option **et** dire à partir de quel signal on reviendrait dessus : une décision sans critère de révision n'est pas une décision, c'est une préférence.

## Critères de réussite {#criteres}

Chaque critère est mesurable ; la commande qui le montre est indiquée.

- **Modèle exact.** `erlang_c(2, 1.0)` vaut un tiers ; pour une file M/M/1 de charge 0,5 et de service 1, l'attente moyenne vaut 1,0 et le 90e centile $\ln 5 / 0{,}5 \approx 3{,}22$. Commande : `pytest tests/test_capacity.py -k "exact or closed_forms"`.
- **Modèle recoupé.** Formule et simulation s'accordent à 5 % près sur l'attente moyenne et le 90e centile, pour deux files, avec trois graines de 300 000 arrivées. Commande : `pytest -k independent_simulation`.
- **Verdicts.** Votre modèle donne, pour le cahier des charges fourni, les mêmes verdicts de budget et d'objectif que la solution de référence sur les cinq conceptions testées.
- **Vérificateur.** Chacune des treize sections manquantes, et chaque mutation (poids de somme différente de 100, total faux, note hors de 1 à 5, risque sans mitigation, coût du texte différent du modèle, conception hors budget, conception hors objectif, marqueur inachevé) est détectée. Commande : `pytest tests/test_rfc_lint.py`.
- **Cohérence texte et modèle.** `python3 rfc_lint.py rfc.md` affiche `rfc: ok` : le coût mensuel écrit dans votre RFC égale celui du modèle appliqué à **votre** bloc de conception, à 0,5 % près.
- **Revue.** La grille remplie par un autre relecteur ne contient aucune case « 0 » sur les critères éliminatoires, et chaque remarque est suivie d'une correction ou d'une réponse écrite.
- **Honnêteté.** La RFC dit quelles données sont inventées, quelles hypothèses sont les plus fragiles, et à quel seuil la décision serait révisée.

## Pistes et indices {#pistes}

Ces indices ne donnent pas la solution ; essayez d'abord sans.

**La file d'attente.** Un job de plusieurs GPU a besoin de tous ses GPU en même temps : on le modélise comme un client qui occupe un « serveur » de la taille du job. Le nombre de serveurs est le nombre de jobs qui tiennent dans le pool. Ce modèle ignore les rafales, les priorités entre classes et la fragmentation : ses attentes sont une **borne optimiste**, à dire dans la RFC.

**La formule d'Erlang C.** Calculez les termes $a^k/k!$ par récurrence plutôt qu'avec des factorielles, qui débordent pour de grands pools. La queue de la distribution d'attente est exponentielle : de là viennent la moyenne et le 90e centile. Vérifiez d'abord les deux cas à la main, une file à un serveur et la file à deux serveurs de charge 1.

**Valider par simulation.** Une simulation courte est bruitée : à des charges de 0,75 à 0,8, une seule exécution de 60 000 arrivées s'est écartée de la formule de 7 % à 18 % dans nos essais, alors que six exécutions de 600 000 arrivées retombent à moins de 1 %. Les attentes successives sont corrélées, donc la précision d'une moyenne est bien moindre que ne le suggère le nombre d'arrivées. Mesurez la dispersion entre graines avant de fixer une tolérance.

**Pool réservé ou élastique.** Un pool réservé se paie en permanence mais n'a pas de délai d'obtention. Un pool élastique se paie à l'usage mais impose un délai : il ne peut pas tenir un objectif plus court que ce délai. Ce simple fait explique pourquoi la plus petite classe, la plus exigeante en latence, est souvent la seule réservée.

**Le vérificateur.** Lisez le texte comme un programme : les sections sont des titres exacts, les tableaux ont un en-tête que l'on reconnaît, le coût est une phrase au format fixe. C'est volontairement rigide : la rigidité rend le document vérifiable, la grille humaine juge le reste.

**La décision.** Un tableau de critères pondérés n'est pas une mesure : les notes sont des jugements. Écrivez ce qui fonde chaque note avec un chiffre du modèle, faites relire les poids par quelqu'un d'autre, et vérifiez qu'un changement raisonnable des poids ne renverse pas le classement.

### Résultats de la solution de référence {#reference-results}

À lire **après** votre propre travail. Tout dépend des données inventées du cahier des charges.

::: sol
**Demande.** 53 740 GPU-heures de travail par mois, dont 46 080 pour le pré-entraînement (86 %).

**Quatre conceptions évaluées par le modèle** (coût mensuel en unités arbitraires) :

| Option | Description | Coût | Budget (450 000) | Objectifs |
|---|---|---|---|---|
| A | tout à la demande | 570 709 | dépassé | développement non tenu (15 min contre 5 min) |
| B | tout réservé, un pool par classe (256, 32, 16, 4 GPU) | 1 349 040 | dépassé | tous tenus |
| C | développement réservé (4 GPU), reste élastique, pré-entraînement préemptible | 317 161 | tenu, marge de 29,5 % | tous tenus |
| D | comme C, mais pré-entraînement à la demande | 580 388 | dépassé | tous tenus |

**Décision de la RFC de référence : l'option C**, avec le risque principal nommé (capacité préemptible de 128 GPU d'un seul tenant, hypothèse la plus fragile du modèle) et une règle de bascule vers la demande.

**Sensibilité.** Le pré-entraînement préemptible coûte autant que le pré-entraînement à la demande vers **1,0 interruption par heure de job** (valeur supposée : 0,15). À 0,60 le coût du pré-entraînement passe de 229 515 à 332 236 : la décision tient tant que le taux réel reste très en dessous de 1. Avec deux GPU réservés pour le développement au lieu de quatre, l'attente au 90e centile monte à 1,72 heure : quatre est le minimum.

**Ce que la référence dit mal ou ne dit pas.** Les notes de la décision sont des jugements ; les attentes sont une borne optimiste ; la capacité préemptible est supposée toujours disponible au volume demandé. La RFC les écrit dans « Hypothèses et limites ».
:::

## Extensions {#extensions}

- **Simulation de bout en bout.** Remplacez le modèle M/M/c par une simulation à événements discrets d'un pool partagé avec priorités entre classes (réutilisez le simulateur du projet 4) et mesurez de combien les attentes réelles dépassent la borne optimiste.
- **Réservation partagée.** Au lieu d'un pool réservé par classe, un pool commun avec files par équipe et préemption (module Slurm) : refaites l'évaluation et comparez.
- **Capacité qui fluctue.** Faites varier la disponibilité préemptible dans le temps et estimez la fréquence de bascule vers la demande qui ferait renverser la décision.
- **Données réelles.** Remplacez le cahier des charges fictif par les mesures de votre propre équipe (profil de charge, temps de service, taux de panne mesuré) et relancez tout.
- **RFC d'un pair.** Relisez la RFC d'une autre personne avec la grille et rédigez la revue : lire ce qu'on n'a pas écrit est la meilleure façon d'apprendre à écrire.

## Pour le portfolio {#portfolio}

**Structure du dépôt.** Un `README.md` d'un écran : la question, l'avertissement sur les données fictives, la commande qui lance les 37 tests et le vérificateur, la décision de la RFC en une phrase avec son signal de révision, et un lien vers la RFC.

**Ce qu'il faut montrer.** La RFC, la grille de revue remplie par un autre, le modèle et ses tests, et l'accord entre la formule et la simulation. La RFC est le livrable : le code n'est que ce qui la rend vérifiable.

**Ce qu'un recruteur d'infrastructure de calcul cherche.** Quelqu'un qui écrit une décision que l'on peut contester, qui chiffre au lieu d'affirmer, qui sépare le mesuré de l'hypothèse, et qui sait défendre une option devant des questions hostiles.

### Grille de revue contradictoire {#grille}

Un relecteur autre que l'auteur note chaque critère de 0 à 2 (0 absent ou faux, 1 partiel, 2 solide) et justifie chaque note. Les critères marqués ★ sont éliminatoires : un 0 sur l'un d'eux renvoie la RFC en réécriture.

| Critère | Question posée au relecteur |
|---|---|
| ★ Chiffres vérifiables | Chaque chiffre vient-il du modèle, et le modèle se relance-t-il ? |
| ★ Options réelles | Les options sont-elles des alternatives sérieuses, avec des inconvénients écrits ? |
| ★ Décision et signal de révision | La décision est-elle claire, et le texte dit-il à quel seuil on la révise ? |
| Hypothèses | Les plus fragiles sont-elles nommées et leur effet chiffré ? |
| Fiabilité | Les pannes sont-elles absorbées sans intervention humaine hors heures ouvrées ? |
| Observabilité | Détecte-t-on un job bloqué ou un exportateur muet, et en combien de temps ? |
| Migration | Chaque phase a-t-elle un critère de sortie et un retour arrière ? |
| Risques | Y a-t-il au moins cinq risques avec une mitigation concrète et un propriétaire ? |
| Lisibilité | Un lecteur pressé comprend-il la décision en deux minutes ? |

### Questions de soutenance {#soutenance}

La soutenance dure vingt minutes : cinq pour le problème et les options, cinq pour la décision et les chiffres, cinq pour la fiabilité et la migration, cinq pour les questions. Préparez ces questions, en sachant que le jury peut en poser d'autres :

1. Si le taux d'interruption réel était dix fois supérieur à votre hypothèse, que deviendrait la décision, et comment le sauriez-vous en deux semaines ?
2. Votre modèle ignore les rafales : de combien vos attentes sont-elles optimistes, et comment le mesureriez-vous ?
3. Pourquoi réserver exactement ce pool et pas un de moins ?
4. Que se passe-t-il si les trois ingénieurs de l'équipe sont absents un week-end ?
5. Quelle est l'option que vous avez écartée avec le plus de regret, et pourquoi ?
6. Quelle donnée réelle changerait le plus votre décision si elle était différente ?
7. Comment un chercheur voit-il ce que lui coûte son job, et qu'est-ce que cela change à son comportement ?
8. À quel moment cette plateforme cesse-t-elle d'être la bonne et que ferait-on alors ?

### Formules du projet {#formules}

Pour une file M/M/c avec un taux d'arrivée $\lambda$, un taux de service $\mu$, $c$ serveurs et une charge offerte $a = \lambda/\mu$, la probabilité qu'une arrivée doive attendre est la formule d'Erlang C :

$$P_{\text{attente}} = \frac{\dfrac{a^{c}}{c!}\cdot\dfrac{c}{c-a}}{\displaystyle\sum_{k=0}^{c-1}\frac{a^{k}}{k!} + \dfrac{a^{c}}{c!}\cdot\dfrac{c}{c-a}}$$

La queue de l'attente est exponentielle, d'où l'attente moyenne et le 90e centile :

$$W_q = \frac{P_{\text{attente}}}{c\mu - \lambda}, \qquad t_{90} = \frac{\ln\bigl(P_{\text{attente}}/0{,}1\bigr)}{c\mu - \lambda} \ \text{si } P_{\text{attente}} > 0{,}1, \text{ sinon } 0$$

Le coût d'un pool réservé de $N$ GPU est $N \times 730 \times p_{\text{réservé}}$ par mois. Celui d'un pool élastique est le nombre de GPU-heures utilisées, divisé par la disponibilité utile, multiplié par le prix. La disponibilité utile reprend le projet 3 :

$$g = 1 - \left(\frac{C}{T^{*}} + \frac{T^{*}/2 + R}{M}\right), \qquad T^{*} = \sqrt{2\,C\,M}$$

### Pour aller plus loin {#lectures}

- Le [projet 3](../resilient-trainer/index.html) pour la période de Young et Daly, le [projet 4](../multi-provider-scheduler/index.html) pour la comparaison de politiques de placement, le [projet 5](../gpu-observability/index.html) pour l'observabilité.
- Une RFC d'ingénierie lue en entier vaut dix conseils d'écriture : cherchez celles que publient des projets ouverts de votre domaine, et lisez-en une avec la grille ci-dessus.
