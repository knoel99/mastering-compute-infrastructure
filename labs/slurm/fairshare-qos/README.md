# Lab 5.2 — Fairshare, QOS et préemption

Deux comptes concurrents (`teama`, `teamb`), un QOS `urgent` qui préempte `normal` avec remise en file. Observer `sshare`, `sprio`, `squeue`, `sacct`.

```bash
sudo bash verify.sh     # un peu plus de 2 minutes (123 s mesurées) : le facteur de fairshare n'est recalculé qu'à chaque PriorityCalcPeriod (réglé à 1 minute)
```

`configure.sh` ajoute la politique à la configuration du bac à sable ; les noms de compte sont mis en minuscules par Slurm.

Un job préempté puis remis en file a plusieurs enregistrements de comptabilité : `sacct` n'affiche que le dernier, sauf avec `-D` (`--duplicates`). C'est pourquoi `verify.sh` cherche l'état `PREEMPTED` du premier passage avec `sacct -D` (vérifié trois fois le 2026-10-25 sur Slurm 23.11.4).
