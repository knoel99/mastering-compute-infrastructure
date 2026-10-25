# Lab 13.3 — Coût réel d'un déménagement de données (module 13, `multi-cloud`)

Un calculateur testé : sortie de données par tranches mensuelles dégressives avec franchise, stockage pendant le
chevauchement des deux copies, temps de transfert, point d'équilibre en heures de GPU, copie contre relecture distante.

**Tarifs** : `rates.yaml` contient uniquement des tarifs lus le **2026-10-24** à la source indiquée pour chaque entrée
(API de liste de prix d'AWS, API de prix de détail d'Azure, page de prix de Cloudflare R2). Les tarifs changent :
relisez la page du fournisseur le jour de votre étude et remplacez les valeurs. Le code ne contient aucun prix.
Les volumes de GPU et les écarts de prix entre sites utilisés par `scenarios.py` sont des **entrées d'exemple**, pas
des prix de marché.

```
rates.yaml            cartes tarifaires sourcées et datées (aucun prix dans le code)
reference/egress.py   solution de référence
starter/egress.py     sept fonctions à écrire (tiered_cost, split_cost, transfer_hours, storage_cost, move_cost,
                      breakeven_gpu_hours, copy_vs_remote_read)
tests/                18 tests ; IMPL=starter|reference choisit le code testé
scenarios.py          le tableau du chapitre 4 du cours
verify.sh             prouve : référence verte, départ rouge, scénarios
```

```bash
export PYTHON=/chemin/vers/python            # pytest et pyyaml
IMPL=starter $PYTHON -m pytest -q tests       # votre travail : 18 échecs sur 18 au départ
PYTHON=$PYTHON bash verify.sh                 # référence verte (18), départ rouge, scénarios
```

**Critère de réussite** : `verify.sh` affiche la fin du tableau, dont par exemple
`[S1] ... free allowance already used up : 13.50 USD` pour 150 Go sortant d'AWS us-east-1 une fois la franchise de
100 Go consommée, et se termine par `ok: egress-cost reference passes, starter fails as intended`. Les montants du
calculateur sont de l'arithmétique exacte à partir de la carte : les tests les épinglent, mais vous les recalculerez
avec **vos** tarifs.

Limites, volontaires : un seul mois de facturation par appel (l'étalement sur plusieurs mois est un calcul à part,
`split_cost`), pas de taxes, pas de remises négociées, pas de frais de requête ni de frais de lecture
de données froides, pas de coût des liaisons privées. Les programmes de sortie gratuite lors d'un départ complet d'un
fournisseur (AWS, Google Cloud) ne concernent pas l'exploitation multi-fournisseurs courante et ne sont pas modélisés.
