# Lab 1.1 — Cartographier une machine

`machine_map.py` produit un rapport JSON (CPU, NUMA, mémoire, périphériques PCI, interfaces réseau, disques) et
une table de **localité** : pour chaque nœud NUMA, quels GPU, cartes InfiniBand et disques NVMe y sont rattachés.

```bash
python3 machine_map.py                                   # cette machine
python3 machine_map.py --sysroot fixtures/sysroot-2socket --lscpu-json fixtures/lscpu-sandbox.json
PYTHON=python3 bash verify.sh
```

`fixtures/sysroot-2socket/` est un serveur à deux sockets et quatre GPU **fabriqué à la main** pour tester la
logique de localité : ce n'est pas la capture d'une machine réelle. `lscpu-sandbox.json` et `lsblk-sandbox.json`
sont, eux, des captures de la machine du bac à sable (Xeon virtualisé, 4 vCPU, un seul nœud NUMA).

Sur une vraie machine à GPU, comparez `locality` avec `nvidia-smi topo -m`.
