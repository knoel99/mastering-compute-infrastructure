# RFC-001 — Une plateforme de calcul GPU de 8 à 256 GPU

**Statut :** brouillon soumis à revue. **Équipe :** plateforme (3 ingénieurs), groupe de recherche fictif de 40 personnes. **Portée du document :** tous les chiffres viennent d'un cahier des charges **inventé** (`requirements.yaml`) et d'un modèle de capacité exécutable ; aucun prix réel n'y figure. Remplacez-les par vos mesures avant toute décision réelle.

## Contexte

Le groupe entraîne et évalue des modèles de langage. Quatre classes de charge se partagent la plateforme : le **pré-entraînement** (128 GPU par job, environ 240 heures de calcul, 1,5 job par mois), le **réglage fin** (16 GPU, 10 heures, 26 jobs par mois), l'**évaluation** (8 GPU, 2 heures, 170 jobs par mois) et le **développement interactif** (1 GPU, 1,2 heure, 650 sessions par mois).

La demande de calcul est de 53 740 GPU-heures de travail par mois : 46 080 pour le pré-entraînement, 4 160 pour le réglage fin, 2 720 pour l'évaluation et 780 pour le développement. Le pré-entraînement représente 86 % de la demande mais seulement 1,5 job par mois : c'est la classe qui détermine le coût, et la plus exposée aux pannes.

Aujourd'hui il n'existe pas de plateforme commune. Chaque équipe réserve ses machines à sa manière, les files d'attente sont informelles et personne ne sait ce que coûte une heure de calcul utile.

## Objectifs et non-objectifs

**Objectifs.** Tenir les quatre objectifs de niveau de service ci-dessous pour un coût mensuel inférieur à 450 000 u (unités arbitraires). Être exploitable par trois ingénieurs avec une astreinte en heures ouvrées seulement. Rendre le coût d'une heure de calcul **utile**, et non d'une heure facturée, visible par équipe.

**Non-objectifs.** Pas de reprise sur sinistre multi-région, pas de plateforme au-delà de 256 GPU, pas d'entraînement sur du matériel propre, pas d'optimisation du code des modèles. Ces sujets sont repoussés à un document ultérieur.

## Exigences

| Classe | Mesure | Seuil |
|---|---|---|
| pré-entraînement | attente avant démarrage, 90e centile | 48 h |
| réglage fin | attente avant démarrage, 90e centile | 4 h |
| évaluation | attente avant démarrage, 90e centile | 1 h |
| développement | attente avant démarrage, 90e centile | 5 min |

Contraintes : budget mensuel de 450 000 u ; équipe de trois ingénieurs ; astreinte en heures ouvrées ; une seule région. **Hypothèses inventées** : un GPU tombe en panne tous les 5 000 heures en moyenne, un checkpoint dure 4 minutes, une reprise 15 minutes, l'obtention de capacité à la demande prend 15 minutes, une allocation préemptible est interrompue 0,15 fois par heure de job.

## Options considérées

Quatre options sont comparées avec le modèle de capacité. Le coût est mensuel, en unités arbitraires.

### Option A — Tout à la demande

Toutes les classes tournent sur de la capacité à la demande. Avantages : aucun engagement, mise en place immédiate, réversible. Inconvénients : coût de **570 709 u**, au-dessus du budget, et le développement interactif ne tient pas son objectif de 5 minutes, car obtenir de la capacité prend 15 minutes.

### Option B — Tout réservé, un pool par classe

Pools réservés de 256, 32, 16 et 4 GPU. Avantages : tous les objectifs sont tenus, attente nulle ou faible, comportement prévisible. Inconvénients : coût de **1 349 040 u**, soit trois fois le budget, avec une utilisation très basse de tous les pools (de 18 à 27 %) ; 308 GPU au total, au-delà du plafond de 256 GPU fixé par les non-objectifs ; engagement de durée difficile à défaire.

### Option C — Hybride : développement réservé, reste élastique, pré-entraînement préemptible

Quatre GPU réservés pour le développement ; réglage fin et évaluation à la demande ; pré-entraînement sur capacité préemptible avec checkpoints et reprise automatique. Avantages : tous les objectifs tenus pour **317 161 u**, soit 29,5 % sous le budget ; seul le pool qui exige une latence de quelques minutes est réservé. Inconvénients : le pré-entraînement subit environ 52 incidents par job, dont environ 45 interruptions de la capacité préemptible ; le modèle suppose qu'un job de 128 GPU trouve de la capacité préemptible d'un seul tenant, ce qui est l'hypothèse la plus fragile ; deux modes d'exploitation à maintenir.

### Option D — Hybride avec pré-entraînement à la demande

Comme l'option C, mais le pré-entraînement tourne à la demande. Avantages : peu d'interruptions (une panne matérielle environ toutes les 39 heures de job) et exploitation plus simple. Inconvénients : coût de **580 388 u**, au-dessus du budget de 130 388 u.

## Décision

Les critères et leurs poids sont ceux du groupe ; les notes de 1 à 5 sont un **jugement** étayé par les chiffres des options, pas une mesure.

| Critère | Poids | Option A | Option B | Option C | Option D |
|---|---|---|---|---|---|
| Coût | 30 | 1 | 1 | 5 | 1 |
| Respect des SLO | 30 | 2 | 5 | 5 | 5 |
| Risque opérationnel | 20 | 4 | 4 | 3 | 5 |
| Complexité | 10 | 5 | 3 | 3 | 4 |
| Réversibilité | 10 | 5 | 1 | 4 | 5 |
| Total | 100 | 2,7 | 3,0 | 4,3 | 3,7 |

**Décision : option C.** Elle est la seule qui tient le budget **et** les objectifs de niveau de service. Son principal risque, l'indisponibilité de capacité préemptible pour 128 GPU, est traité par une règle de bascule vers la capacité à la demande, voir « Migration » et « Risques ». Si ce risque se réalise souvent, la décision se rapproche de l'option D et dépasse le budget : c'est un seuil à surveiller, pas une certitude. La décision dépend aussi des poids : avec cinq poids égaux de 20, les options C et D sont à égalité à 4,0 ; C reste la seule qui tient le budget, ce qui est une contrainte avant d'être un critère.

## Capacité et coûts

Conception retenue, au format que lit `rfc_lint.py` :

```json
{"pools": {"pretrain": {"market": "spot"}, "finetune": {"market": "on_demand"}, "eval": {"market": "on_demand"}, "dev": {"market": "reserved", "gpus": 4}}}
```

Résultat du modèle pour cette conception :

| Classe | Marché | Disponibilité utile | GPU-heures utilisées | Attente p90 | Coût (u) |
|---|---|---|---|---|---|
| pré-entraînement | préemptible | 0,803 | 57 379 | 0,25 h | 229 515 |
| réglage fin | à la demande | 0,979 | 4 251 | 0,25 h | 42 512 |
| évaluation | à la demande | 0,985 | 2 761 | 0,25 h | 27 614 |
| développement | réservé (4 GPU) | 0,995 | 784 | 0 | 17 520 |

Coût mensuel total : 317 161 u. Budget : 450 000 u. Marge : 29,5 %.

Le pool de développement de quatre GPU a une utilisation de 26,9 %, une probabilité d'attente de 2,6 % et une attente moyenne de 38 secondes. Avec deux GPU réservés au lieu de quatre, l'attente au 90e centile monte à 1,72 heure et l'objectif de 5 minutes n'est plus tenu : quatre est le minimum de cette conception.

### Sensibilité au taux d'interruption préemptible

Seul le coût du pré-entraînement dépend de ce paramètre. Les valeurs ci-dessous sont celles du modèle, pour des taux d'interruption par heure de job autour de la valeur supposée de 0,15.

| Interruptions par heure de job | Disponibilité utile | Coût du pré-entraînement (u) |
|---|---|---|
| 0,05 | 0,881 | 209 288 |
| 0,15 | 0,803 | 229 515 |
| 0,30 | 0,710 | 259 517 |
| 0,60 | 0,555 | 332 236 |
| 1,00 | 0,374 | 493 088 |

À partir d'environ **1,0 interruption par heure de job**, le pré-entraînement préemptible coûte autant que le pré-entraînement à la demande (492 741 u). Tant que le taux réel reste très en dessous, l'option C est la moins chère. Ce seuil vient du modèle du premier ordre, qui devient pessimiste quand les pannes sont fréquentes (voir « Hypothèses et limites ») : le seuil du modèle exact du projet 3 est plus élevé, donc 1,0 est une valeur prudente.

### Hypothèses et limites

- Le modèle suppose des arrivées de Poisson et des durées exponentielles par classe ; il ignore les rafales, les priorités et la fragmentation entre pools : les attentes sont **probablement optimistes** (l'attente croît avec la variabilité des arrivées et des durées), sans être une borne garantie.
- Il suppose que la capacité à la demande et préemptible est toujours disponible au volume demandé, après 15 minutes. C'est l'hypothèse la plus forte.
- Prix, taux de panne et taux d'interruption sont inventés. Aucune de ces valeurs n'est une donnée de marché.
- La disponibilité utile suppose un checkpoint à la période de Young et Daly, sans perte liée à l'écriture sur le stockage partagé. Elle vient du modèle du premier ordre, fiable tant que la période de checkpoint reste petite devant le temps moyen entre incidents (ce rapport vaut 0,15 au taux supposé de 0,15 interruption par heure de job, et 0,37 à 1,0). Le modèle exact du projet 3 donne une disponibilité un peu plus haute au taux supposé et beaucoup plus haute à 1,0.

## Fiabilité

Sur capacité préemptible, un job de 128 GPU subit un taux d'incident de 0,1756 par heure (matériel : 128 × 0,0002, plus 0,15 d'interruptions), soit un temps moyen entre incidents de 342 minutes. La période de checkpoint de Young et Daly est d'environ 52 minutes ; sur un job de 240 heures de calcul, la durée réelle est d'environ 299 heures et l'on attend environ 52 incidents, dont environ 45 interruptions de la capacité préemptible.

Chaque interruption doit être absorbée **sans intervention humaine**, l'astreinte étant limitée aux heures ouvrées : écriture atomique des checkpoints avec somme de contrôle et repli sur le précédent, relance automatique avec détection de blocage, reprise à l'identique vérifiée par des tests. Ces mécanismes sont ceux du projet 3 ; l'objectif de disponibilité utile du pré-entraînement est de 80 %.

Règle de bascule : si la capacité préemptible n'est pas obtenue en 30 minutes pour un job de pré-entraînement, il est relancé à la demande, avec une alerte au responsable du budget.

## Observabilité

Les métriques de GPU sont exposées au format de dcgm-exporter et jointes à l'allocation par job. Deux alertes sont des **pages** (erreur Xid, job bloqué) et deux des **tickets** (GPU qui chauffe, allocation inactive), avec des règles testées par des tests unitaires qui résistent à la mutation (projet 5) ; une cinquième alerte, d'absence de l'exportateur, est ajoutée pour qu'un exportateur muet ne ressemble pas à une plateforme saine. Un tableau de bord par classe affiche attente, coût et disponibilité utile.

Un indicateur de coût par équipe est publié chaque semaine : GPU-heures utilisées, coût, et part du coût perdue en reprises. Sans cet indicateur, le coût d'une heure utile reste invisible.

## Sécurité

Une seule région et un seul réseau privé ; aucun jeu de données ne quitte la région. Les accès sont attribués par équipe avec le moindre privilège ; les jetons d'accès au stockage ont une durée de vie courte. Les images de conteneur sont construites par l'équipe plateforme, signées et épinglées par empreinte. Aucun secret n'est stocké dans les dépôts ni dans les définitions de jobs.

## Migration

**Phase 0 (semaines 0 à 2).** Réserver les 4 GPU de développement, déployer l'exportateur, les alertes et le tableau de bord. Critère de sortie : les cinq alertes ont été déclenchées volontairement sur un nœud d'essai.

**Phase 1 (semaines 3 à 6).** Basculer le réglage fin et l'évaluation sur capacité à la demande, avec files par équipe. Critère de sortie : attente p90 sous 4 h pour le réglage fin et sous 1 h pour l'évaluation pendant deux semaines.

**Phase 2 (semaines 7 à 12).** Pré-entraînement sur capacité préemptible avec l'entraîneur tolérant aux pannes, d'abord sur un job de 16 GPU puis de 128. Critère de sortie : un job complet de 128 GPU avec une disponibilité utile d'au moins 80 %.

Retour arrière : chaque phase peut revenir à la précédente en changeant le marché d'une classe dans la configuration ; les réservations sont limitées aux 4 GPU de développement, donc rien n'est difficile à défaire.

## Risques

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Capacité préemptible indisponible pour 128 GPU d'un seul tenant | moyenne | élevée | règle de bascule à 30 minutes vers la demande ; surveiller la fréquence des bascules ; revoir la décision si elle dépasse une fois sur quatre |
| Taux d'interruption réel très supérieur à 0,15 par heure | moyenne | élevée | mesurer le taux dès la phase 2 ; le seuil d'indifférence est d'environ 1,0 (valeur prudente du modèle) |
| Corruption silencieuse d'un checkpoint | faible | élevée | somme de contrôle, repli sur le précédent, test de reprise exacte en intégration continue |
| Dépassement du budget par des jobs inactifs | moyenne | moyenne | alerte d'allocation inactive, expiration automatique des sessions interactives |
| Perte de la seule personne qui connaît la plateforme | moyenne | élevée | runbooks relus par un second ingénieur, exercice de panne trimestriel |
| Les prix réels diffèrent des prix inventés du modèle | élevée | moyenne | refaire le calcul avec des prix relevés le jour de la décision |

## Questions ouvertes

Quelle part du pré-entraînement peut tolérer une interruption sans checkpoint intermédiaire ? Quelle capacité préemptible est réellement obtenable d'un seul tenant, et à quel moment de la journée ? L'équipe de recherche accepte-t-elle de lancer ses évaluations avec 15 minutes de délai ? À partir de quel taux de bascule vers la demande revoit-on la décision ?

## Annexes

Reproduire les chiffres : `python3 rfc_lint.py rfc.md --requirements requirements.yaml` évalue la conception du bloc JSON de la section « Capacité et coûts » et refuse un coût différent de celui du modèle. Briques utilisées : projet 2 pour la mesure de passage à l'échelle, projet 3 pour la reprise après panne, projet 4 pour la comparaison de politiques de placement, projet 5 pour l'observabilité. Vérification croisée de la formule d'attente : `mmc_sim.py` simule la file et retrouve la formule d'Erlang à moins de 1 % en moyenne sur six graines de 600 000 arrivées (sur une seule graine de 60 000 arrivées, l'écart va de 2 à 22 % selon la graine : les attentes sont corrélées).
