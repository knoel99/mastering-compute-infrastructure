# Lab 12.4 — Un plan de contrôle Kubernetes 1.37 sans kubelet

Type : **sandbox** (Linux x86_64, accès sortant HTTPS vers `dl.k8s.io`, `registry.k8s.io`, `raw.githubusercontent.com` ; environ 350 Mo téléchargés au premier lancement dans `$K8S_MINI_CACHE`, par défaut `~/.cache/mci-k8s-mini`). Aucun GPU, ni Docker.

Le lab démarre de **vrais** `etcd` 3.7.0, `kube-apiserver`, `kube-controller-manager` et `kube-scheduler` en v1.37.1, **sans kubelet** : les nœuds sont des objets `Node` que le script crée et dont il déclare la capacité (8 `nvidia.com/gpu` chacun). Les pods sont liés à un nœud par le vrai ordonnanceur mais ne s'exécutent jamais. Cela suffit pour observer l'ordonnancement et la validation d'API, pas l'exécution.

- **Partie A** (`gang_demo.sh`) : le même Job de 8 pods × 8 GPU, sans puis avec l'ordonnancement de groupe natif (portes `GenericWorkload` et `WorkloadWithJob`, désactivées par défaut), sur 6 puis 8 nœuds.
- **Partie B** (`fragmentation_demo.sh`) : quatre petits pods répartis par le score par défaut, puis un pod de nœud entier qui attend avec 28 GPU libres ; avec `MostAllocated`, il passe.
- **Partie C** (`validate_server_side.sh`) : les CRD upstream (Kueue v0.20.3, JobSet v0.13.0, Kubeflow Trainer v2.1.0) sont installées et le serveur d'API valide en `--dry-run=server` les manifestes des labs 12.1 et 12.2 et une réclamation DRA, puis refuse quatre manifestes mutés (règles CEL comprises).

## Intégrité et limites

Les binaires Kubernetes sont comparés à leur fichier `.sha256` publié au même endroit (cela détecte une corruption, pas une compromission de la source). `etcd` est extrait de l'image `registry.k8s.io/etcd` (étiquette donnée par `kubeadm config images list` pour v1.37.1, résumé du manifeste figé dans `lib.sh`, chaque couche vérifiée contre son résumé). Le contrôleur de cycle de vie des nœuds est désactivé, faute de kubelet pour envoyer des battements de cœur. Le lab ne démarre ni Kueue, ni JobSet, ni l'opérateur GPU : leurs contrôleurs ne tournent pas, seule leur API est validée.

## Lancer

```bash
bash up.sh                   # ~25 s la première fois
bash gang_demo.sh && bash fragmentation_demo.sh && bash validate_server_side.sh
bash down.sh                 # arrête tout (par nom exact de processus)
bash verify.sh               # le tout avec arrêt garanti, environ 1,5 à 2 minutes avec le cache chaud
```

**Attention.** `down.sh` et la fin de `verify.sh` arrêtent *tout* processus de la machine dont le nom exact est `etcd`, `kube-apiserver`, `kube-controller-manager` ou `kube-scheduler`, y compris ceux d'un autre cluster : n'exécutez pas ce lab sur une machine qui héberge un vrai plan de contrôle. Le jeton d'administration est tiré au hasard à chaque démarrage et n'écoute que sur `127.0.0.1`.

Variables : `K8S_MINI_CACHE`, `K8S_MINI_API_PORT` (16443), `K8S_MINI_ETCD_PORT` (12379), `K8S_VERSION`, `K8S_MINI_FEATURE_GATES`.

## Pour aller plus loin

Ajoutez `kubectl taint` sur un nœud pendant que le Job gang est lié et observez ce que fait (ou ne fait pas) le plan de contrôle ; activez la porte `TopologyAwareWorkloadScheduling` (alpha en 1.36 d'après la documentation) et ajoutez une contrainte de topologie au PodGroup.
