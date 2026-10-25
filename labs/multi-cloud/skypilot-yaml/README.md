# Lab 13.2 — Un job SkyPilot indépendant du fournisseur (module 13, `multi-cloud`)

Type : **cluster** (compte cloud ou contexte Kubernetes requis pour lancer réellement). **La partie cloud n'a jamais été
exécutée par l'auteur.** Ce qui a été exécuté, sans compte cloud, via `verify.sh` :

| Branche | Contenu | État |
|---|---|---|
| Lint | `bash -n`, `shellcheck`, compilation Python, `yamllint` | exécutée |
| Règles de gouvernance | `policy_check.py` (étiquettes, reprise, checkpoint, secrets, autostop, plafond de coût, résidence) et 15 tests | exécutée |
| Analyse par SkyPilot | `sky.Task.from_yaml` de SkyPilot **0.14.1** sur 4 fichiers et 5 mutations rejetées, hors ligne | exécutée si `SKY_PYTHON` (ou `PYTHON`) contient `skypilot`, sinon la ligne `SKIPPED` le dit |
| Répétition de la reprise | un « entraîneur » jouet, un « bucket » (un dossier), une « VM » neuve par tentative ; **simulation, pas SkyPilot** | exécutée |
| `sky jobs launch` réel | provisionnement, bascule entre fournisseurs, préemption réelle | **non exécutée** |

## Fichiers

```
job.yaml              job managé : H100:8 spot, any_of sur trois infras, job_recovery, checkpoint sur bucket, étiquettes
dev-cluster.yaml      cluster interactif avec autostop (down: true)
bad-job.yaml          valide pour SkyPilot, refusé par la politique (5 erreurs, 2 avertissements)
bad-job-fixed.yaml    la correction minimale de bad-job.yaml (exercice 2) : 0 erreur, 1 avertissement W3 ; à lire APRÈS l'essai
job-eu.yaml           le job restreint à l'UE (exercice 11)
policy_check.py       lint de gouvernance, du code et pas un wiki
test_policy_check.py  15 tests
parse_with_skypilot.py  analyse hors ligne par le vrai code de SkyPilot
train.py              entraîneur JOUET reprenable (un entier, mise à jour déterministe) : pas un entraînement
rehearse_preemption.sh  répétition : SIGKILL sans préavis, SIGTERM avec préavis, reprise depuis un autre « VM »
verify.sh
```

```bash
export PYTHON=/chemin/vers/python                  # pytest et pyyaml
python3 -m venv /tmp/sky && /tmp/sky/bin/pip install skypilot==0.14.1   # facultatif : branche d'analyse SkyPilot
SKY_PYTHON=/tmp/sky/bin/python PYTHON=$PYTHON bash verify.sh
```

## Sur un vrai compte (non exécuté par l'auteur)

1. `pip install "skypilot[aws,gcp]"`, puis `sky check` pour voir quelles infras sont utilisables avec vos identifiants.
2. Remplacez les buckets (`r2://example-...`), le contexte `k8s/eu-gpu-cluster` et le fichier `train.py` (un vrai).
3. `sky jobs launch -n pretrain-demo job.yaml`, puis `sky jobs queue` ; coupez la VM depuis la console du fournisseur pour
   voir la reprise.

**Critère de réussite hors ligne** : la ligne `OK skypilot parse: 4 files accepted (...), 5 mutations rejected`
(si SkyPilot est installé), `15 passed` pour les règles et `OK preemption rehearsal: resumed runs match the uninterrupted run exactly`.

**Critère de réussite sur cluster (non vérifié)** : après la perte d'une VM, `sky jobs queue` montre `#RECOVERIES` >= 1 et
le journal de rang 0 affiche `resumed_from_step=` avec un pas non nul.

## Ce que l'analyse hors ligne ne voit pas

Observé pendant l'écriture du lab : SkyPilot 0.14.1 rejette `type:` avec `mode: MOUNT` (il faut `MOUNT_CACHED`) et les fautes
de frappe, mais **accepte** un nom de stratégie `job_recovery` invalide. Aucune analyse hors ligne ne prouve qu'un lieu
a de la capacité, que votre quota l'autorise, ou que vos identifiants fonctionnent.

Lu dans le code de SkyPilot 0.14.1 (`sky/clouds/kubernetes.py`), **non exécuté** : `use_spot` n'est admis sur un contexte
Kubernetes que si les nœuds portent une étiquette *spot*. Le troisième lieu de `job.yaml` (un contexte factice) peut donc
être écarté au lancement sur un cluster sans cette étiquette, alors que l'analyse hors ligne l'accepte.
