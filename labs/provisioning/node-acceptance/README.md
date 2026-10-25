# Lab 6.3 — Recette d'un nœud GPU (type `gpu` : branche de rejeu vérifiée, branche réelle non exécutée)

`acceptance.sh` enchaîne `nvidia-smi`, `dcgmi diag`, `gpu_burn` et `all_reduce_perf` (nccl-tests) sur un vrai nœud, range les preuves dans un répertoire et demande un verdict à `run_decision.py` : code 0 *accept*, 1 *reject*, 3 *retest*, 2 erreur d'usage ou outil absent.

```bash
PYTHON=/chemin/vers/venv/bin/python bash verify.sh      # environ 5 s, sans GPU
```

## Ce qui est vérifié ici, et ce qui ne l'est pas

* **Vérifié (branche de rejeu).** Lint (`bash -n`, `shellcheck`, syntaxe Python), 22 répertoires de preuves **synthétiques** reproductibles (`make_fixtures.py`), 30 tests : les règles de `reference/decide.py` les passent, le squelette `starter/decide.py` en échoue 24 (c'est voulu), et `acceptance.sh --fixtures` rend les codes 0, 1 et 3 attendus.
* **Non exécuté (branche réelle).** Aucune ligne de la collecte réelle n'a tourné : ni `nvidia-smi`, ni `dcgmi`, ni `gpu_burn`, ni `all_reduce_perf`. La liste de champs de `nvidia-smi --query-gpu` est **non vérifiée** sur un GPU réel : contrôlez-la avec `nvidia-smi --help-query-gpu`. `CUDA_RUNTIME_VERSION` et `NVSWITCH_GENERATION` sont lues dans l'environnement : sans elles, la version de CUDA vaut `unknown` (verdict *retest*) et le contrôle de Fabric Manager est ignoré. Le lab porte donc le badge *non vérifié*.
* **Synthétique.** Aucun nombre des fixtures n'a été mesuré. Les valeurs sont rondes à dessein (référence 100 GB/s, 98 observés…). L'enveloppe du JSON de `dcgmi diag` est une **hypothèse** : la documentation DCGM ne montre qu'un fragment (`category`, `tests`, `results`, `status`), l'analyseur parcourt donc toute imbrication.

## Sources lues le 2026-10-24

* DCGM Diagnostics (niveaux `-r 1..4`, `-j`, codes de sortie 226 `DCGM_ST_NVVS_ERROR` et 205 `DCGM_ST_NVVS_ISOLATE_ERROR`) : https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/dcgm-diagnostics.html
* Table de compatibilité mineure CUDA (CUDA 13.x >= 580, 12.x >= 525, 11.x >= 450) : https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html
* Fabric Manager : version égale à celle du pilote avant NVLink 5, service à démarrer à la main : https://docs.nvidia.com/datacenter/tesla/fabric-manager-user-guide/index.html
* Remappage de lignes (drapeaux *pending* et *failure*, seuils d'ouverture de RMA) : https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/latest/rma-policy-thresholds-for-row-remapping.html
* XID 79 « GPU has fallen off the bus » : https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html
* nccl-tests : `busbw`, `-J`, `NCCL_TESTS_MIN_BW` (échec sous 0,9 x la valeur) : https://github.com/NVIDIA/nccl-tests (`doc/PERFORMANCE.md`, `src/util.cu`, `src/common.cu`)
* gpu-burn : résumé final `GPU i: OK|FAULTY` : https://github.com/wilicc/gpu-burn (`gpu_burn-drv.cpp`)

## Ce que vous complétez

`starter/decide.py` contient sept fonctions vides. `IMPL=starter python -m pytest tests` échoue ; remplissez-les jusqu'à `IMPL=reference`-parité. Les seuils (`policy.json`) sont des **choix de site**, à étalonner sur un nœud de référence : ce ne sont pas des valeurs constructeur.
