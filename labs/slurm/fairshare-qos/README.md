# Lab 5.2 — Fairshare, QOS et préemption

Deux comptes concurrents (`teama`, `teamb`), un QOS `urgent` qui préempte `normal` avec remise en file. Observer `sshare`, `sprio`, `squeue`, `sacct`.

```bash
sudo bash verify.sh     # environ 4 minutes : le facteur de fairshare n'est recalculé qu'à chaque PriorityCalcPeriod (réglé à 1 minute)
```

`configure.sh` ajoute la politique à la configuration du bac à sable ; les noms de compte sont mis en minuscules par Slurm.
