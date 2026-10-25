# Lab 7.1 — Dimensionner un fat-tree

Calculateur Python testé (`fabric.py`) pour dimensionner un fat-tree à 1, 2 ou 3 niveaux : commutateurs, câbles, émetteurs-récepteurs optiques, sur-souscription, bande passante de bissection. Il est confronté aux comptes publiés du DGX SuperPOD H100, puis (partie B) à un **vrai** OpenSM sur un fabric InfiniBand **simulé**.

```bash
python3 fabric.py --endpoints 2048 --radix 64 --leaf-down 48   # 3:1 -> 54 commutateurs
python3 fabric.py --compare                                     # 7 lignes sur 8 du SuperPOD retrouvées
python3 fabric.py --goodput 1024 2048 4096                      # débit utile RoCE v2 selon la MTU
python3 ibsim_check.py --iblinkinfo                             # partie B + une ligne d'iblinkinfo (exemple 3.1 du cours)
PYTHON=/chemin/vers/python ./verify.sh                          # tests + parties A et B
```

## Ce qui est vérifié, et ce qui ne l'est pas

- **Partie A (toujours)** : 12 tests `pytest` (formules d'Al-Fares, capacité, budget de ports par propriété avec graine fixe, débit utile) et comparaison à `published.json`.
- **Partie B (si `ibsim-utils`, `opensm`, `infiniband-diags` sont installés)** : `ibsim_check.py` génère un fabric à deux niveaux, le fait découvrir par OpenSM (`-R ftree`), relit les compteurs avec `ibnetdiscover` et les tables de transfert avec `ibroute`. Il vérifie que (1) `ftree` accepte les fabrics sains (1:1 et 3:1), (2) les nombres de commutateurs, hôtes et câbles égalent ceux du calculateur, (3) le déséquilibre des liens montants d'une feuille est d'au plus 1, (4) un fabric amputé d'un câble est rejeté (`Fabric topology is not a fat-tree`, repli sur Min Hop). Sans ces paquets, `verify.sh` écrit `SKIP part B` et termine par `OK topology-sizing (part A only)` : seule la partie A est alors vérifiée.
- **Simulé** : `ibsim` ne transporte aucun paquet. Rien ici ne mesure un débit. Les GUID et LID du fichier de topologie sont réattribués par le simulateur.
- **Données publiques transcrites à la main** : `published.json` reprend les tableaux 3 et 4 du guide d'architecture du DGX SuperPOD H100 (lus le 2026-10-24). Deux anomalies de la source y sont notées : la ligne à 3 SU (16 colonnes au lieu de 12) et la ligne « 56 SU » dont les 2 048 nœuds ne correspondent pas à 56 × 32. L'explication du premier écart est une **hypothèse**.
- **Constantes** : tailles d'en-têtes du noyau Linux (`ib_pack.h`), MTU de `verbs.h`. Les 24 octets de trame Ethernet sur le fil sont une valeur standard **non relue** dans la norme.

Testé le 2026-10-24 sur Ubuntu 24.04 (noyau 6.18, 4 vCPU), ibsim 0.10, OpenSM 3.3.23, infiniband-diags 50.0, en tant que root. `ibsim_check.py` n'écrit que dans un dossier temporaire (supprimé à la fin) et arrête le simulateur par son PID.
