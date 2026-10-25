#!/usr/bin/env bash
# Stop everything started by setup.sh, in dependency order, and wipe job/node state.
#   --purge-db   also drop the accounting database (usage, accounts, QOS)
# Order matters: slurmctld flushes accounting records to slurmdbd while shutting down, so slurmdbd
# and MariaDB must outlive it. The accounting DB must be dropped with SQL while MariaDB runs:
# deleting its directory by hand corrupts InnoDB's data dictionary at the next slurmdbd start.
set +e
purge=0; [ "${1:-}" = "--purge-db" ] && purge=1

# On Ubuntu the daemons run as slurmctld-wlm and slurmd-wlm (slurmctld and slurmd are symlinks to them), so a
# process is looked up under "<name>" and "<name>-wlm": `pgrep -x slurmctld` alone never finds the controller.
# (pgrep -x refuses patterns longer than 15 characters, hence two plain names instead of one regular expression.)
alive() { pgrep -x "$1" >/dev/null 2>&1 || pgrep -x "$1-wlm" >/dev/null 2>&1; }
signal() { pkill "$1" -x "$2" 2>/dev/null; pkill "$1" -x "$2-wlm" 2>/dev/null; }
stop() {  # stop <process name> <seconds to wait before SIGKILL>
  alive "$1" || return 0
  signal -TERM "$1"
  for _ in $(seq 1 "$2"); do alive "$1" || return 0; sleep 1; done
  signal -KILL "$1"
  for _ in $(seq 1 10); do alive "$1" || return 0; sleep 1; done
}

squeue -h -o %i 2>/dev/null | xargs -r scancel >/dev/null 2>&1 || true   # scancel has no --all option
stop slurmd 30
stop slurmctld 60
signal -KILL slurmscriptd   # a leftover zombie of an earlier controller would make stop() wait for nothing
if [ "$purge" -eq 1 ]; then
  if ! pgrep -x mariadbd >/dev/null && [ -d /var/lib/mysql/mysql ]; then
    # An earlier teardown already stopped MariaDB: start it just long enough to drop the database with SQL
    # (otherwise the accounting records of that earlier run would survive a "--purge-db").
    mkdir -p /run/mysqld && chown mysql:mysql /run/mysqld
    nohup mariadbd --user=mysql --datadir=/var/lib/mysql --socket=/run/mysqld/mysqld.sock >/var/log/mariadb.out 2>&1 </dev/null &
    for _ in $(seq 1 40); do mariadb -e 'select 1' >/dev/null 2>&1 && break; sleep 1; done
  fi
  if pgrep -x mariadbd >/dev/null; then
    mariadb -e 'DROP DATABASE IF EXISTS slurm_acct_db' >/dev/null 2>&1
  fi
fi
stop slurmdbd 30
stop mariadbd 30
stop munged 10
rm -rf /var/spool/slurmctld/* /var/spool/slurmd/*
exit 0
