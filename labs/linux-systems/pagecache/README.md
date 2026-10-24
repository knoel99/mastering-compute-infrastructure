# Lab 1.3 — Page cache : mesurer ce qui touche le disque

**Partie A — `pagecache.py`.** Écrit un fichier de 256 Mio puis le relit à froid, à chaud et en `O_DIRECT`, et
affiche pour chaque étape trois **compteurs du noyau** : pages sales (`Dirty` de `/proc/meminfo`), pages
résidentes du fichier (`mincore(2)`), octets lus sur le périphérique (`/proc/diskstats`). `posix_fadvise(DONTNEED)`
vide le cache d'un seul fichier **sans être root**.

```bash
python3 pagecache.py            # tableau lisible
python3 pagecache.py --json     # pour un script
```

Pourquoi des compteurs et pas des débits ? Dans le bac à sable, le disque virtuel est mis en cache par l'hôte et des
processus de la plateforme écrivent dans `drop_caches` : lecture « à froid » et « à chaud » vont à la même vitesse.
Les compteurs, eux, disent la vérité sur ce que le noyau a fait.

**Partie B — `littles_law.sh`** (nécessite `fio`). Lectures aléatoires de 4 Kio en `O_DIRECT`, profondeur de file 1
puis 32 : le produit débit × latence moyenne doit valoir environ la profondeur de file.

```bash
PYTHON=python3 bash verify.sh   # partie A, tests, partie B
```

`WORKDIR` doit être sur un système de fichiers qui accepte `O_DIRECT` (pas `tmpfs`).
