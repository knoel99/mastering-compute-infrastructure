# Lab 13.1 — Simulateur de placement sensible aux coûts (module 13, `multi-cloud`)

Un simulateur **événementiel** d'un seul job long (64 GPU, 120 h de calcul utile) placé sur plusieurs offres de plusieurs
fournisseurs, avec préemption, disponibilité aléatoire de la capacité et **gravité des données** : changer de
fournisseur coûte une sortie de données (checkpoint et jeu de données) et du temps de copie. Quatre politiques sont
comparées sur les **mêmes tirages** (graines communes) : `stay`, `cheapest` (prix catalogue le plus bas),
`failover` (premier pool qui accorde de la capacité, ce que fait un `any_of` avec bascule) et `aware` (coût attendu,
copie et valeur du temps compris).

**Toutes les données du scénario sont SYNTHÉTIQUES** (prix en unités arbitraires `u`, disponibilités et taux de
préemption inventés, tarif de sortie de 0,09 u/Go inventé). Seule la taille du checkpoint est dérivée : 7e9 paramètres
x 16 octets par paramètre = 112 Go (règle ZeRO du module 2). Ne lisez pas ces chiffres comme le marché. Pour des
tarifs réels de sortie de données, voir le lab 13.3.

```
reference/placement.py   moteur, tirages communs, politiques, comparaison appariée (solution de référence)
starter/placement.py     même fichier avec 7 fonctions à écrire (young_daly, waste, price_per_useful_hour,
                         transfer_hours, move_cost, Aware.score, paired_diff) ; le moteur est fourni
tests/                   25 tests ; IMPL=starter|reference choisit le code testé
scenarios.py             balayage de la taille du jeu de données, tableau et critère de réussite
threshold.py             seuil exact de taille de données au-delà duquel `aware` ne déménage plus (exemple 5.2)
verify.sh                prouve : référence verte, départ rouge, critère structurel du balayage
```

```bash
export PYTHON=/chemin/vers/python            # pytest suffit, aucune autre dépendance
IMPL=starter $PYTHON -m pytest -q tests       # votre travail : 22 échecs sur 25 au départ (3 tests ne touchent pas vos fonctions)
PYTHON=$PYTHON bash verify.sh                 # référence verte (25), départ rouge, balayage
$PYTHON scenarios.py --seeds 200              # le tableau du cours (chapitre 5)
$PYTHON scenarios.py --seeds 200 --lam 400    # étape 5 : la grille de tailles est fixe, le seuil se lit entre deux points
$PYTHON threshold.py                          # seuils exacts pour lam = 0, 40, 400 (exemple 5.2)
```

**Critère de réussite (structurel, sans durée mesurée)** : la ligne finale
`CRITERION (moves of 'aware' non-increasing with data size; cost <= 1.05 x the best other policy): OK`. Les tirages
sont graînés : deux exécutions donnent exactement la même sortie. Les tests épinglent des valeurs exactes seulement pour
du code déterministe (chronologies avec préemption forcée) et utilisent des tolérances pour le reste (par exemple 15 %
entre le moteur et le modèle de gaspillage au premier ordre). `threshold.py` évalue `Aware.score` à l'instant 0 avec une
graine où les deux pools refusent la capacité (chacun paie alors son attente moyenne) : le seuil ne dépend pas d'un
tirage particulier, et son critère est structurel (positif, non croissant avec `lam`).

Limites, volontaires : un seul job (pas de file ni de capacité partagée, voir le projet 4), une re-décision seulement à
la préemption (jamais de migration volontaire vers un pool devenu moins cher), une seule valeur de tarif de sortie et
de débit entre tous les fournisseurs, `lam` (la valeur d'une heure de retard) est un paramètre que le code ne sait pas
choisir, une politique `aware` myope (elle suppose finir le job sur le pool choisi).

Le projet [Placement multi-fournisseurs](../../projects/multi-provider-scheduler/) construit la version à plusieurs
jobs et capacité limitée ; ce lab isole l'effet de la gravité des données sur la décision de bascule.
