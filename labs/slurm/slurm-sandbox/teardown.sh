#!/usr/bin/env bash
# Stop everything started by setup.sh, in dependency order, and wipe job/node state.
#   --purge-db   also drop the accounting database (usage, accounts, QOS)
# Order matters: slurmctld flushes accounting records to slurmdbd while shutting down, so slurmdbd
# and MariaDB must outlive it. The accounting DB must be dropped with SQL while MariaDB runs:
# deleting its directory by hand corrupts InnoDB's data dictionary at the next slurmdbd start.
set +e
purge=0; [ "${1:-}" = "--purge-db" ] && purge=1

stop() {  # stop <process name> <seconds to wait before SIGKILL>
  pgrep -x "$1" >/dev/null || return 0
  pkill -x "$1"
  for _ in $(seq 1 "$2"); do pgrep -x "$1" >/dev/null || return 0; sleep 1; done
  pkill -9 -x "$1"
  for _ in $(seq 1 10); do pgrep -x "$1" >/dev/null || return 0; sleep 1; done
}

scancel --all >/dev/null 2>&1
stop slurmd 30
stop slurmctld 60
stop slurmscriptd 5
if [ "$purge" -eq 1 ] && pgrep -x mariadbd >/dev/null; then
  mariadb -e 'DROP DATABASE IF EXISTS slurm_acct_db' >/dev/null 2>&1
fi
stop slurmdbd 30
stop mariadbd 30
stop munged 10
rm -rf /var/spool/slurmctld/* /var/spool/slurmd/*
exit 0
