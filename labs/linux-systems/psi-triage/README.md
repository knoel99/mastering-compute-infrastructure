# Lab 1.2 — Triage avec la méthode USE et la pression PSI

`triage.py` lit deux instantanés du noyau à quelques secondes d'écart et en tire, pour le processeur, la mémoire et
le disque, une **utilisation** et une **saturation** :

- processeur : part du temps occupé (`/proc/stat`) et pression PSI `cpu` (`/proc/pressure/cpu`) ;
- mémoire : pression PSI `memory` ;
- disque : occupation (`io_ticks` de `/proc/diskstats`), taille moyenne de file, pression PSI `io`.

`classify` en tire des conclusions lisibles. Le dernier cas est volontaire : avec des E/S asynchrones profondes, le disque
est occupé mais **PSI `io` reste à zéro** (angle mort constaté sur le disque virtuel du bac à sable).

```bash
python3 triage.py --seconds 5           # lecture lisible
python3 triage.py --seconds 5 --json    # pour un script
sudo apt-get install -y stress-ng fio   # nécessaires à verify.sh
PYTHON=python3 bash verify.sh           # tests, puis quatre charges réelles (~30 s)
```

Les erreurs (troisième lettre de USE) ne sont pas couvertes : elles demandent des compteurs matériels (chapitre 8).
