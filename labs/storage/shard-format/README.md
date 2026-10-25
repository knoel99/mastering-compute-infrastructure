# Lab 8.2 — Shards et lecture séquentielle

Le même jeu synthétique de 4 096 échantillons de 16 Kio (64 Mio, jetons de 16 bits pseudo-aléatoires, graine fixe) est écrit dans
quatre dispositions, puis lu dans l'ordre et au hasard. Tout est mesuré avec des **compteurs**, pas des chronomètres.

| Disposition | Détail |
|---|---|
| un fichier par échantillon | 4 096 fichiers de 16 Kio |
| shards tar (convention WebDataset) | 8 archives de 512 échantillons, deux membres par échantillon (`.bin`, `.json`) ; lisibles par la vraie bibliothèque `webdataset` (testé) |
| fichier empaqueté | un seul fichier `packed.bin`, lu avec `pread` ou `mmap` (comme `train.bin` de nanoGPT) |
| Parquet | une colonne binaire, groupes de 256 lignes (4 Mio), sans compression (`pyarrow`) |

## Compteurs

Pour chaque lecteur : les pages des fichiers sont d'abord évincées (`posix_fadvise(DONTNEED)`, sans root), puis on lit
`/proc/self/io` avant et après : `syscr` (appels `read`), `rchar` (octets renvoyés par les appels de lecture), `read_bytes` (octets réellement lus sur la couche de stockage, d'après proc_pid_io(5)).
Le nombre d'ouvertures est compté par un crochet d'audit Python (`sys.addaudithook`), donc il ne voit pas les ouvertures faites par `pyarrow`
(colonne `n/a`). Pourquoi pas des débits ? Voir le lab 1.3 : sur ce bac à sable, l'hôte met le disque en cache et la plateforme vide le cache de pages.
Les débits « à chaud » sont affichés **à titre indicatif** et ne sont jamais testés.

## Partie B : l'écart en chiffres avec `fio`

`fio_gap.py` lit un fichier de 512 Mio en `O_DIRECT`, profondeur de file 1 : 1 Mio séquentiel et aléatoire, puis 128 Kio, 16 Kio et 4 Kio aléatoires. Il ajuste
$T = \alpha + n/B$ sur le temps moyen par requête et en déduit la taille de demi-performance $n_{1/2} = \alpha B$. **Nécessite `fio`.**

```bash
export PYTHON=/chemin/vers/python   # numpy, pytest ; pyarrow et webdataset optionnels (pip install pyarrow webdataset)
bash verify.sh                      # environ 40 s
python3 run_shards.py               # partie A seule
python3 fio_gap.py                  # partie B seule
```

Sortie réelle (VM de test à 4 vCPU, readahead de 128 Kio, 2026-10-24) :

```
OK shard-format: opens files/tar/packed = 4096/8/1; mmap random device/payload 3.4 vs pread 1.0; parquet asked/payload 256; fio gap 25x, n_1/2 = 109 KiB
```

## Ce que `verify.sh` affirme

Sommes de contrôle exactes de chaque lecteur ; nombre d'ouvertures (4 096, 8, 1) ; octets venus du périphérique proches de la charge utile pour les lectures séquentielles et `pread` (entre 0,9 et 1,6) ;
`mmap` aléatoire lit au moins 1,5 fois plus que `pread` (lecture autour de la faute de page) ; une lecture aléatoire Parquet demande un groupe de lignes entier (entre 0,75 et 1,25 fois 256) ; `fio` : 1 Mio donne plus de 2 fois la bande passante de 4 Kio.
Si `pyarrow` ou `webdataset` manquent, `verify.sh` le dit et saute ces lignes ou ce test, sans les compter comme réussis.

## Réserves

- `verify.sh` écrit le jeu dans `$HOME` si le répertoire temporaire est en mémoire (`tmpfs`) : sur de la mémoire, `read_bytes` reste à 0 et les rapports `device/pay` n'ont pas de sens. Le `read_ahead_kb` affiché est celui de `vda` ; sur un autre disque, lisez `/sys/block/<disque>/queue/read_ahead_kb`.

- Les données sont synthétiques et le jeu (64 Mio) tient dans la mémoire : le compteur `device/pay` d'une lecture aléatoire Parquet vaut 4 (et non 256) parce que chaque groupe n'est lu qu'une fois sur le disque puis servi par le cache ; sur un jeu plus grand que la mémoire, il tendrait vers 256.
- L'amplification de `mmap` dépend du `read_ahead_kb` du périphérique (128 ici) et du noyau (6.18) ; elle est mesurée, pas déduite d'une documentation.
- `fio` : sur ce disque virtuel il n'y a pas de pénalité de déplacement de tête, la lecture aléatoire de 1 Mio vaut la séquentielle ; l'écart vient entièrement de la taille de la requête ($\alpha$). Sur un disque rotatif ou un système de fichiers réseau, il y a un coût en plus.
- Le lecteur Parquet aléatoire relit volontairement un groupe entier par échantillon (pire cas, sans cache du dernier groupe).
