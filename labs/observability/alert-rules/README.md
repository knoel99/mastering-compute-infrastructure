# Lab 14.2 — Règles d'alerte testées avec promtool

Deux fichiers de règles, leurs tests, un lint de politique et un test de mutation.

| Fichier | Rôle |
|---|---|
| `rules/platform.rules.yml` | Écrit à la main : règles d'enregistrement (écart à la médiane du job) et quatre alertes : `GPUHot` (avec `keep_firing_for`), `NodeSlow`, `JobNoProgress`, `GpuTelemetryDown`. |
| `rules/slo.rules.yml` | **Généré** par `gen_rules.py` : SLO « 95 % des jobs démarrent en moins de 600 s », trois alertes de vitesse de consommation du budget (14,4 ; 6 ; 1) sur fenêtres longue et courte (rapport 1/12). |
| `tests/platform.rules.test.yml` | Écrit à la main : pour chaque alerte, un cas qui se déclenche et un cas silencieux, de part et d'autre de la durée `for`. |
| `tests/slo.rules.test.yml` | **Généré** : les minutes d'évaluation viennent d'une simulation des mêmes fenêtres sur des compteurs synthétiques. |
| `tests/wait_quantile.test.yml` | Ce que `histogram_quantile` répond sur les six délais d'attente réels capturés (médiane 7,5 s contre 6,5 s exact ; 90e centile 24 s contre 14,5 s exact) : l'erreur vient du découpage en seaux. |
| `lint_rules.py` | Politique : sévérité, résumé, runbook existant, `for` ≥ 2 min (sauf alertes de vitesse de consommation, qui n'en ont pas), et chaque métrique lue est réellement exposée par l'exportateur du lab 14.1, par la fixture dcgm ou par le contrat de l'entraîneur. |
| `mutate.py` | 12 mutants (durée changée, comparaison inversée, fenêtre courte supprimée…) : chacun doit faire échouer `promtool test rules`. |

## Ce qui est simulé

Toutes les séries des tests sont **synthétiques** (écrites à la main ou calculées). Les seuils (85 °C, rapport 1,3, 10 minutes sans progrès) sont **illustratifs** : à calibrer sur votre flotte. Le contrat de l'entraîneur (`train_steps_total`, `train_compute_seconds`) est une convention de ce cours, pas une métrique d'un outil existant.

## Lancer

```bash
export PYTHON=/chemin/vers/python      # pyyaml ; promtool (paquet apt "prometheus", testé : 2.45.3)
bash verify.sh                          # ~1 minute
python3 gen_rules.py --table            # tableau des vitesses de consommation du budget
```

`verify.sh` utilise `GOMAXPROCS=2` et `nice` pour les mutants : sur une machine partagée, ne le lancez pas en boucle.

## Branches vérifiées

Tout est exécutable sans GPU ni Slurm : `verify.sh` a été exécuté par l'auteur le 2026-10-24. Ce qui n'est **pas** vérifié : le comportement des règles sur un vrai Prometheus avec de vraies données (le moteur de `promtool` est celui de Prometheus, mais les tests ne couvrent que les séries qu'ils fournissent).

## Pour aller plus loin

1. Ajoutez un mutant qui survit (par exemple changer `severity: page` en `ticket`) et écrivez le test qui le tue.
2. Passez le SLO à 99 % : que deviennent les seuils et les minutes de déclenchement ? (`python3 gen_rules.py --table`)
3. Écrivez une règle `JobStuckPending` fondée sur `slurm_pending_oldest_age_seconds{reason_class="capacity"}` et testez-la.
