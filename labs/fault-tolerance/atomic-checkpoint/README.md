# Lab 10.2 — Checkpoint atomique et reprise exacte

Un petit entraîneur PyTorch **CPU** déterministe (MLP, Adam, ordonnanceur de taux d'apprentissage, *dropout*, itérateur de données avec époques mélangées). Son checkpoint est un **répertoire** validé par un seul `rename`, avec un manifeste écrit en dernier (idée de base d'un checkpoint réparti).

```
ckpt.py             save (fichiers fsync, manifeste en dernier, rename, rotation), verify, load_latest
trainer.py          l'entraîneur ; --omit {optimizer,scheduler,rng,cursor} retire une partie de l'état
ablate.py           retire une partie à la fois et donne le premier pas faux
chaos.py            campagne de kill -9 au hasard sur un vrai processus, puis comparaison avec la référence
dcp_reshard.py      torch.distributed.checkpoint : écrit sur 2 rangs (gloo, CPU), relit sur 4
safetensors_peek.py écrit un fichier .safetensors et lit son en-tête à la main
test_ckpt.py        11 tests (écriture interrompue, octet inversé, manifeste absent, rotation, reprise exacte, ablations)
verify.sh           tout ce qui précède, avec une ligne finale « OK atomic-checkpoint »
```

```bash
export PYTHON=/chemin/vers/python   # PyTorch CPU, pytest ; safetensors est facultatif
PYTHON=$PYTHON bash verify.sh       # environ 50 s
```

Simulations, à dire clairement : `--sleep-ms` simule le temps de calcul d'un pas et `--slow-ckpt-ms` simule la latence d'un stockage lent, pour que les `kill -9` tombent souvent pendant une écriture. Ce ne sont pas des mesures d'un système réel. Les assertions portent sur l'égalité des états et des pertes, et sur des compteurs (au moins 3 pannes), jamais sur des durées.

Sortie réelle du bac à sable (2026-10-24), tableau d'ablation :

```
omitted      first wrong step  max |dloss|  same final state
nothing                  None    0.000e+00              True
optimizer                  31    7.493e-02             False
scheduler                  32    9.814e-02             False
rng                        30    2.583e-02             False
cursor                     30    3.337e-01             False
```

Limites : le déterminisme bit à bit tient ici parce que tout tourne sur un seul fil CPU avec la même topologie. Sur GPU, ou avec un nombre de rangs différent après un redimensionnement, on ne peut attendre qu'une équivalence statistique. `dcp_reshard.py` montre le redécoupage à la lecture, pas la reprise d'un entraînement complet.
