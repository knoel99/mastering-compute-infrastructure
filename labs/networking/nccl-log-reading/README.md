# Lab 7.2 — Lire un journal NCCL

Analyseur de journaux `NCCL_DEBUG=INFO` (`nccl_log.py`) : version, rangs, nœuds, plugin réseau, cartes RDMA et GPUDirect, anneaux (fermeture de chaque anneau en un seul cycle), canaux, transports, rangs sans `Init COMPLETE`, avertissements. Chaque anomalie reçoit un code (`socket_network`, `hca_mismatch`, `init_incomplete`, `ring_broken`, `gdr_disabled`, `warnings`…).

```bash
python3 nccl_log.py fixtures/healthy_2node_ib.log
python3 nccl_log.py fixtures/socket_fallback.log --expect socket_network
PYTHON=/chemin/vers/python ./verify.sh       # 11 tests + 5 analyses
python3 make_fixtures.py                     # régénère fixtures/ à l'identique
```

## Données : tout est étiqueté

- `healthy_2node_ib.log`, `socket_fallback.log`, `degraded_rail.log`, `hang_in_init.log`, `healthy_with_warning.log` : **SYNTHÉTIQUES**. Ils sont générés par `make_fixtures.py` ; les formats de message ont été relus dans le code source de NCCL (`init.cc`, `search.cc`, `topo.cc`, `p2p.cc`, `net.cc`, `bootstrap.cc`, branche `master`, lecture du 2026-10-24) et sont listés dans l'en-tête du script. Les valeurs (pointeurs, pid, bandes passantes, identifiants de bus) sont inventées. Aucun GPU, aucune exécution de NCCL.
- Dans `degraded_rail.log`, les lignes `Channel` suivent les lignes de cartes : la carte 3 du premier nœud, sans GPUDirect, est citée sans le suffixe `/GDRDMA`, et le GPU 5 du second nœud, dont la carte 5 manque, passe par la carte 4 (règle **inventée** du générateur, pas le comportement de NCCL).
- `public_nccl_docs.log` : **PUBLIC**, neuf lignes copiées de la page « Logging » du guide d'utilisation de NCCL (URL dans le fichier, lue le 2026-10-24). Il teste le format avec horodatage, `file:line` et niveaux `WARN`/`ATTN`.
- Les formats changent d'une version de NCCL à l'autre. Une ligne inconnue est ignorée, jamais une erreur. L'analyseur n'a **pas** été essayé sur un vrai journal de cluster.
- Le test `test_fixtures_are_reproducible` garantit que les fichiers committés sont exactement ce que génère le script.

Testé le 2026-10-24 (Python 3.13, pytest). Exécution : moins d'une seconde.
