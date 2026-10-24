# Lab 1.3 — Page cache : mesurer ce qui touche le disque

**Partie A — `pagecache.py`.** Écrit un fichier de 256 Mio puis le relit à froid, à chaud et en `O_DIRECT`, et
affiche pour chaque étape trois **compteurs du noyau** : pages sales (`Dirty` de `/proc/meminfo`), pages
résidentes du fichier (`mincore(2)`), octets lus sur le périphérique (`/proc/diskstats`). `posix_fadvise(DONTNEED)`
vide le cache d'un seul fichier **sans être root**.

```bash
python3 pagecache.py            # tableau lisible
python3 pagecache.py --json     # pour un script
```

Pourquoi des compteurs et pas des débits ? Dans le bac à sable, une lecture « à froid » de 256 Mio n'est que 2,5 fois plus
lente qu'une lecture « à chaud » (0,10 s contre 0,04 s) : le chronomètre ne dit pas si les octets viennent d'un disque
rapide ou d'un cache de l'hôte (hypothèse non vérifiée), et des processus de la plateforme écrivent dans `drop_caches`.
Les compteurs disent ce que le noyau a fait. Deux réserves : `Dirty` est le compteur de **toute la machine**, et les
octets lus sont ceux de **tout le périphérique** ; sur une machine partagée, l'activité d'un autre processus, ou un
`drop_caches` de la plateforme entre deux étapes, peut donc faire échouer `verify.sh` (raisonnement sur le code, non
provoqué en pratique ; deux exécutions consécutives ont réussi).

**Partie B — `littles_law.sh`** (nécessite `fio`). Lectures aléatoires de 4 Kio en `O_DIRECT`, profondeur de file 1
puis 32 : le produit débit × latence moyenne doit valoir environ la profondeur de file.

```bash
PYTHON=python3 bash verify.sh   # partie A, tests, partie B
```

`WORKDIR` doit être sur un système de fichiers qui accepte `O_DIRECT` (pas `tmpfs`).
