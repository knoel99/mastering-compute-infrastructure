# Lab 11.1 — Tâches et acteurs Ray : efficacité et pannes

Un vrai Ray local (CPU, 4 CPU logiques) fait tourner un petit pipeline (génération, prétraitement par **tâches** sans état, notation par un **groupe d'acteurs** qui gardent un « modèle » en mémoire), puis on mesure ce que coûte la granularité et on tue des processus pour voir ce que Ray en fait.

```
pipeline.py     documents synthétiques déterministes ; version série, version tâches, version acteurs (ActorPool)
granularity.py  efficacité en fonction de la durée d'une tâche ; surcoût d'un appel (tâche ou acteur)
fault.py        pannes injectées par os._exit(1) : acteur, redémarrage, état, nouvelles tentatives
test_ray_actors.py  8 tests (valeurs, compteurs, rapports ; jamais une durée)
run_demo.py     rapport complet dont les chiffres sont cités dans le cours
resources_demo.py   ressources logiques, acteurs par défaut ou explicites, pools hétérogènes, `ray status`, placement groups
data_demo.py    Ray Data en flux : étape à état sur une ressource logique `eval_gpu`
train_demo.py   Ray Train sur CPU (2 travailleurs, gloo) : un travailleur tué une fois, reprise sur point de reprise
deploy/         ray_slurm.sbatch et raycluster.yaml : LINTÉS seulement (shellcheck, yamllint), jamais exécutés
verify.sh       tout ce qui précède, puis « OK ray-actors »
```

```bash
python3 -m pip install "ray[data,train]" numpy pytest torch   # testé avec ray 2.59.0 (2026-10-25)
export PYTHON=/chemin/vers/python   # Python avec les paquets ci-dessus
PYTHON=$PYTHON bash verify.sh       # environ 2 minutes
```

## Ce qui est simulé, et ce qui ne l'est pas

- **Simulé** : `load_s` (50 ms) imite le chargement d'un modèle depuis un disque ; `granularity.py` remplace le travail par des `time.sleep`. Un sommeil ne consomme pas de CPU : la mesure isole le coût d'ordonnancement de Ray, et ne dépend pas de la charge d'une machine partagée. Ce n'est pas une mesure de calcul.
- **Simulé aussi** : les « GPU » de `resources_demo.py` et la ressource `eval_gpu` de `data_demo.py` sont des **ressources logiques** déclarées sur une machine sans GPU ; elles exercent l'ordonnanceur de Ray, pas un GPU. `train_demo.py` entraîne une couche linéaire sur CPU.
- **Réel** : Ray 2.59.0 (installé avec `pip install ray` le 2026-10-25), ses processus de travail, son magasin d'objets, ses redémarrages d'acteurs. Les pannes sont de vrais `os._exit(1)` dans de vrais processus.

## Sortie réelle (VM de test, 4 vCPU, Python 3.13, 2026-10-25)

```
model builds for 40 documents: tasks=40  actors=4  (simulated load 50 ms per build)
  d=   1.0 ms  chunk=  1  tasks= 1600  wall=1.14 s  efficiency=0.35
  d=  10.0 ms  chunk=  1  tasks=  160  wall=0.50 s  efficiency=0.80
  d= 100.0 ms  chunk=  1  tasks=   16  wall=0.41 s  efficiency=0.97
  d=   1.0 ms  chunk=100  tasks=   16  wall=0.46 s  efficiency=0.87
median round trip: empty task 2.06 ms, empty actor call 1.07 ms
max_restarts=0: next call -> RayActorError
max_restarts=1, no checkpoint: counter was 3, next inc -> 1
max_restarts=1, checkpoint   : counter was 3, next inc -> 4
max_task_retries= 0: result=RayActorError  side effects of call 7: ['7']
max_task_retries=-1: result=7              side effects of call 7: ['7', '7']
```

Sortie de `resources_demo.py` (ressources logiques, `ray status` réel) :

```
2 actors, default options         -> free CPU = 8 of 8
2 actors, num_gpus=1 only         -> free CPU = 6 of 8
2 actors, num_gpus=1, num_cpus=0  -> free CPU = 8 of 8
PACK group ready: True ; STRICT_SPREAD group ready on one node: False ; free CPU = 6 of 8
...
Pending Demands:
 {'CPU': 1.0, 'GPU': 2.0}: 1+ pending tasks/actors
```

Sortie de `data_demo.py` et `train_demo.py` :

```
rows=4000 scorer processes=2 (concurrency=2, eval_gpu=2)
first batch after 2.30 s, whole stream after 3.33 s
final metrics: {'epoch': 5, 'start': 2} error: None
```

Les durées varient d'une exécution à l'autre (le rapport est volontairement le seul endroit où elles s'affichent). Les tests, eux, n'affirment que des ordres : l'efficacité des tâches de 100 ms dépasse celle des tâches de 1 ms, le regroupement par 100 la fait remonter, un acteur construit son modèle une fois, une tâche à chaque appel.

## Limites

- `deploy/ray_slurm.sbatch` et `deploy/raycluster.yaml` ne sont **pas** exécutés : ils demandent un Slurm et un Kubernetes avec GPU. Le YAML n'est pas validé contre le schéma de la CRD KubeRay de votre version.
- `train_demo.py` : `start` vaut 2 dans la sortie ci-dessus (reprise au point de reprise de l'époque 1) ; la valeur exacte dépend de l'instant de la panne, le test affirme seulement qu'il y a eu reprise.
- Un seul nœud : l'ordonnancement entre nœuds, le transfert d'objets par le réseau et la perte d'un nœud entier ne sont pas observés ici.
- `max_task_retries=-1` rejoue l'appel interrompu : l'effet de bord de l'appel 7 apparaît deux fois (« au moins une fois »). Une méthode d'acteur qui n'est pas idempotente doit être protégée.
- Le point de reprise de `fault.py` est un petit JSON écrit par `write + fsync + rename`. Pour un état de plusieurs gigaoctets, voir le laboratoire [`labs/fault-tolerance/atomic-checkpoint`](../../fault-tolerance/atomic-checkpoint/) (module 10).
