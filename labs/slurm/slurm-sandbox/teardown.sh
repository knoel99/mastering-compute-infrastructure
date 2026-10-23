#!/usr/bin/env bash
# Stop everything started by setup.sh and wipe job state so the next run starts clean.
set +e
scancel --all 2>/dev/null
pkill -x slurmd; pkill -x slurmctld; pkill -x slurmdbd; pkill -x mariadbd; pkill -x munged
sleep 2
rm -rf /var/spool/slurmctld/* /var/spool/slurmd/* /tmp/slurm-*.out
if [ "${1:-}" = "--purge-db" ]; then rm -rf /var/lib/mysql/slurm_acct_db; fi
exit 0
