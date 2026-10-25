# Lab 16.4 — Quorum d'un cluster de consensus et exercice de restauration

Deux parties, liées au chapitre 9 du module 16.

1. **`quorum.py`** calcule la probabilité qu'un cluster de consensus (Raft, etcd) de *n* membres garde sa majorité,
   avec la formule binomiale (membres indépendants) et avec des domaines de panne (racks, alimentations), puis
   vérifie la formule contre une simulation de Monte-Carlo à graine fixe. C'est ce que lance `verify.sh`.
2. **`etcd_drill.sh`** (facultatif) monte un vrai cluster etcd de trois membres sur `127.0.0.1`, prend un snapshot,
   arrête un membre puis deux, restaure le snapshot dans un nouveau répertoire et vérifie ce qui revient et ce qui est perdu.

```bash
python3 quorum.py table --a 0.99 0.999
python3 quorum.py racks --a 0.999 --r 0.9995 --layout 5 --layout 3,2 --layout 2,2,1 --layout 1,1,1
python3 quorum.py check --trials 100000 --seed 2026
PYTHON=python3 bash verify.sh                 # pytest requis : pip install pytest

ETCD_BIN=/chemin/vers/etcd-v3.x bash etcd_drill.sh   # facultatif : etcd, etcdctl et etcdutl (testé en v3.7.0)
```

## Ce qui est vérifié, et ce qui ne l'est pas

- `verify.sh` n'a besoin que de Python et de `pytest`. Il ne contient **aucune assertion de durée**. La simulation
  est comparée à la formule avec une tolérance de quatre écarts-types, sur des disponibilités assez basses (0,6 à 0,9)
  pour que des pannes s'observent : à 0,999, une simulation ne verrait presque aucune perte de quorum, alors que la
  formule est la même.
- `etcd_drill.sh` a été exécuté deux fois le 2026-10-25 avec etcd 3.7.0 (binaires `etcd`, `etcdctl`, `etcdutl` tirés de
  l'image `registry.k8s.io/etcd:3.7.0-0`, comme dans le lab 12.4). Il refuse de démarrer si ses ports (23791 à 23794
  par défaut, `DRILL_PORT_BASE` pour les changer) répondent déjà. Tout vit dans un répertoire temporaire supprimé à la fin.
- Les trois membres tournent sur **une seule machine** : la latence réseau et les pannes corrélées d'un vrai
  déploiement n'y existent pas. La durée de restauration affichée est une mesure locale, pas une prévision.
- Les disponibilités `a` et `r` sont des **hypothèses d'exercice**. L'indépendance des pannes est une hypothèse
  aussi : la commande `racks` montre ce qu'elle cache.

## Fichiers

| Fichier | Rôle |
|---|---|
| `quorum.py` | formule exacte, domaines de panne, simulation de Monte-Carlo (`table`, `racks`, `check`) |
| `test_quorum.py` | tailles de majorité de la FAQ d'etcd, valeurs de l'exemple 9.1 et de l'exercice 12, accord avec la simulation |
| `etcd_drill.sh` | exercice de restauration facultatif sur un cluster etcd local |
| `verify.sh` | tests, table de l'exemple 9.1, contrôle de Monte-Carlo, `bash -n etcd_drill.sh` |
