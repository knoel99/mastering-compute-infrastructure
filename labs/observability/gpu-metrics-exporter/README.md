# Lab 14.1 — Un exportateur de métriques de nœud testé

Exportateur Prometheus en Python (`prometheus_client`) qui expose, derrière un seul `/metrics` :

- un **résumé de nœud GPU** calculé à partir du texte d'un dcgm-exporter : GPU chauds, GPU « occupés mais tensor au repos », dispersion des fréquences SM, dernier code XID ;
- l'**état de la file Slurm** (`squeue --json`, `sinfo --json`) avec des étiquettes à valeurs bornées (les raisons d'attente sont regroupées en classes) ;
- un **histogramme du délai d'attente** (`sacct`), chaque job compté une seule fois.

## Ce qui est réel, ce qui est simulé

| Fichier | Nature |
|---|---|
| `fixtures/dcgm_node.prom` | **SIMULÉ.** Un scrape d'un nœud de 8 GPU fictifs (`gen_fixture.py`, graine fixe). Noms, types et textes d'aide : ceux de `default-counters.csv` de dcgm-exporter. Les valeurs ne viennent d'aucun matériel. Trois pannes sont plantées (GPU 3 chaud et ralenti, GPU 5 « occupé mais tensor au repos », GPU 6 au repos avec XID 79). Le rapport de fréquences ne compte que les GPU occupés : un GPU au repos descend légitimement en fréquence. |
| `fixtures/slurm/*.json`, `sacct.txt` | **CAPTURÉS** sur le Slurm 23.11.4 du bac à sable (`labs/slurm/slurm-sandbox`), le 2026-10-24, puis réduits aux champs lus par l'exportateur. `sacct.txt` est la projection des colonnes `JobID,QOS,State,Submit,Start` d'une capture plus large. |
| `tests/`, `mutants.py` | Code testé sur ces fixtures. |

## Lancer

```bash
export PYTHON=/chemin/vers/python      # prometheus_client, pytest ; promtool (paquet apt "prometheus")
bash verify.sh                          # branche hors ligne : fixtures uniquement, ~10 s
LIVE_SLURM=1 bash verify.sh             # ajoute la branche « vrai Slurm » (bac à sable démarré avant)
python3 exporter.py --fixtures fixtures --once | head -30
```

## Branches vérifiées

- **Hors ligne (`verify.sh`)** : 14 tests, 6 mutants tous tués, `promtool check metrics` (2.45.3) accepte la sortie, un scrape HTTP réel. Exécutée par l'auteur le 2026-10-24.
- **En direct (`LIVE_SLURM=1`)** : `squeue --json`, `sinfo --json` et `sacct` d'un vrai Slurm 23.11.4 du bac à sable ; la partie GPU reste la fixture, servie par HTTP à la place de dcgm-exporter. Exécutée une fois par l'auteur le 2026-10-24 (avant un correctif de la gestion du processus du serveur HTTP de la fixture, testé séparément).
- **Non vérifié** : la lecture d'un vrai dcgm-exporter sur GPU (aucun GPU disponible).

## À savoir

`promtool check metrics` **refuse** le texte de dcgm-exporter lui-même (code de sortie 3) : ses étiquettes `modelName` et `Hostname` ne sont pas en `snake_case`. L'exportateur de ce lab n'utilise que des étiquettes conformes (`node`, `state`, `reason_class`, `partition`, `qos`).

## Pour aller plus loin

1. Ajoutez un mutant de votre invention et vérifiez qu'il est tué (sinon, écrivez le test manquant).
2. Calculez le nombre de séries pour 500 nœuds de 8 GPU : combien en économise-t-on en n'exposant que le résumé de nœud plutôt que les 7 métriques par GPU ?
3. Remplacez la lecture fixe du texte DCGM par un `GET` sur un vrai dcgm-exporter (`localhost:9400`) si vous avez un GPU.
