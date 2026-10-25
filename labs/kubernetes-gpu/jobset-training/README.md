# Lab 12.2 — JobSet : un entraînement multi-nœuds

Type : **cluster** (GPU, Kubernetes, JobSet ; Kueue et Kubeflow Trainer en option). **La partie cluster n'a pas été exécutée par l'auteur.** Ce qui l'a été, sans cluster, via `verify.sh` :

| Branche | Contenu | État |
|---|---|---|
| Lint | `bash -n`, `shellcheck`, `py_compile`, `yamllint` | exécutée |
| Schémas | JobSet v0.13.0 et TrainJob (Kubeflow Trainer v2.1.0) contre leurs CRD upstream (`schemas/crds.json`), avec le validateur du lab 12.1 ; quatre JobSet mutés sont rejetés | exécutée |
| Répétition locale | deux processus `torchrun` (gloo, CPU) avec **les mêmes options de rendez-vous que le manifeste** ; un échec est injecté au pas 30, une boucle de redémarrage tient le rôle de `failurePolicy.maxRestarts`, `train.py` reprend au pas 20 | exécutée (simulation de l'orchestration, pas Kubernetes) |
| Serveur d'API réel | les mêmes manifestes acceptés par un `kube-apiserver` 1.37.1 (lab 12.4, partie C) | exécutée dans le lab 12.4 |
| Exécution sur cluster | pods, GPU, NCCL, Kueue, redémarrage réel | **non exécutée** |

## Fichiers

- `manifests/20-jobset-torchrun.yaml` : 16 nœuds de 8 GPU, file Kueue, topologie exigée au niveau du bloc, `maxRestarts: 3`, volume de checkpoints.
- `manifests/30-trainjob.yaml` : le même entraînement pour Kubeflow Trainer v2 (le runtime `torch-distributed` fournit le gabarit).
- `train.py` : entraîneur DDP minimal avec checkpoints atomiques et reprise ; NCCL si CUDA est présent, sinon gloo.
- `local_two_nodes.sh` : la répétition locale.

## Sur un vrai cluster (non exécuté)

1. Installer JobSet (page d'installation de JobSet), Kueue, l'opérateur GPU ; appliquer les manifestes du lab 12.1 puis `10-checkpoint-volume.yaml` (classe de stockage à adapter, RWX).
2. Remplacer `registry.example/pretrain:7b` par une image contenant `train.py` et PyTorch ; adapter `--nnodes`, `--nproc_per_node` et le nombre de GPU à votre parc.
3. `kubectl apply -f manifests/20-jobset-torchrun.yaml` ; observer `kubectl get workloads -n research`, `kubectl get jobset,pods -n research -o wide`, puis supprimer un pod pour provoquer le redémarrage de l'ensemble.

**Critère de réussite sur cluster** : après la suppression d'un pod, tous les pods sont recréés et les journaux de rang 0 affichent `resuming_from_step=` avec un pas non nul.

## Lancer la branche hors cluster

```bash
python3 -m pip install torch pyyaml jsonschema kubernetes-validate    # torch CPU suffit
PYTHON=python3 bash verify.sh                                         # environ 20 s
```
