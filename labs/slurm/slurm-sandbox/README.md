# Lab 5.1 — Un Slurm réel dans le bac à sable

Démarre un Slurm mono-nœud **réel** (munge, MariaDB, `slurmdbd`, `slurmctld`, `slurmd`) avec comptabilité, sans systemd ni GPU, puis soumet un tableau de jobs et une dépendance.

```bash
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y munge slurm-wlm slurmdbd mariadb-server   # Ubuntu 24.04 : Slurm 23.11
sudo bash setup.sh        # idempotent, environ 15 s
sinfo ; sbatch --wrap='hostname' ; squeue ; sacct -X
sudo bash verify.sh       # contrôle complet puis arrêt propre
sudo bash teardown.sh     # arrête tout ce que setup.sh a démarré
```

**Constat de départ.** Avec `AccountingStorageEnforce=associations,limits,qos`, un utilisateur sans association est refusé par `sbatch` (« Invalid account or account/partition combination specified »). `setup.sh` fournit donc une vraie base de comptabilité, un compte `research` et l'association de `root`. Un essai du 25 octobre 2026 avec `AccountingStorageType=accounting_storage/none` et sans `AccountingStorageEnforce` a montré qu'un job s'exécute aussi sans base ; la raison d'attente `InvalidAccount` n'a pas pu être reproduite.

`teardown.sh --purge-db` efface aussi la comptabilité (les numéros de job repartent de 1 : sans cela, les anciens enregistrements `COMPLETED` d'une exécution précédente seraient pris pour ceux des nouveaux jobs). Le mot de passe de la base est aléatoire (ou `SANDBOX_DB_PASS`) : aucun secret n'est stocké dans le dépôt. `examples/wait_stats.py` calcule la médiane et le p90 de l'attente (chapitre 6).

Ces scripts sont destinés à un conteneur ou une VM jetable : ils écrivent dans `/etc/slurm` et démarrent des démons en tant que `root`.
