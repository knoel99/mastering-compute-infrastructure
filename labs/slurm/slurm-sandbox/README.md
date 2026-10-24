# Lab 5.1 — Un Slurm réel dans le bac à sable

Démarre un Slurm mono-nœud **réel** (munge, MariaDB, `slurmdbd`, `slurmctld`, `slurmd`) avec comptabilité, sans systemd ni GPU, puis soumet un tableau de jobs et une dépendance.

```bash
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y munge slurm-wlm slurmdbd mariadb-server   # Ubuntu 24.04 : Slurm 23.11
sudo bash setup.sh        # idempotent, environ 15 s
sinfo ; sbatch --wrap='hostname' ; squeue ; sacct -X
sudo bash verify.sh       # contrôle complet puis arrêt propre
sudo bash teardown.sh     # arrête tout ce que setup.sh a démarré
```

**Constat de départ (important).** Sans `slurmdbd`, avec `AccountingStorageEnforce` vide, un job soumis par `root` reste en attente avec la raison `InvalidAccount` sur cette version. La solution est de fournir une vraie base de comptabilité, ce que fait `setup.sh`.

Ces scripts sont destinés à un conteneur ou une VM jetable : ils écrivent dans `/etc/slurm` et démarrent des démons en tant que `root`.
