#!/usr/bin/env bash
# Stop everything started by setup.sh and wipe job/node state so the next run starts clean.
#   --purge-db   also drop the accounting database (usage, accounts, QOS)
# The accounting DB must be dropped with SQL while MariaDB runs: deleting its directory by hand
# corrupts InnoDB's data dictionary ("Table ... already exists" at the next slurmdbd start).
set +e
purge=0; [ "${1:-}" = "--purge-db" ] && purge=1
scancel --all >/dev/null 2>&1
if [ "$purge" -eq 1 ] && pgrep -x mariadbd >/dev/null; then
  mariadb -e 'DROP DATABASE IF EXISTS slurm_acct_db' >/dev/null 2>&1
fi
pkill -x slurmd; pkill -x slurmctld; pkill -x slurmdbd
# slurmctld writes its state files while shutting down: wait for the exit BEFORE wiping them
for _ in $(seq 1 40); do
  pgrep -x slurmd >/dev/null || pgrep -x slurmctld >/dev/null || pgrep -x slurmdbd >/dev/null || break
  sleep 1
done
pkill -9 -x slurmd; pkill -9 -x slurmctld; pkill -9 -x slurmdbd
pkill -x mariadbd
for _ in $(seq 1 20); do pgrep -x mariadbd >/dev/null || break; sleep 1; done
pkill -x munged
rm -rf /var/spool/slurmctld/* /var/spool/slurmd/*
exit 0
