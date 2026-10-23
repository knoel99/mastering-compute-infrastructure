#!/usr/bin/env bash
# Bring up a real single-node Slurm with accounting (munge + MariaDB + slurmdbd + slurmctld + slurmd).
# Idempotent. Needs root and apt packages: munge slurm-wlm slurmdbd mariadb-server
#   (DEBIAN_FRONTEND=noninteractive apt-get install -y munge slurm-wlm slurmdbd mariadb-server)
# Tested with Slurm 23.11.4 (Ubuntu 24.04 packages) in a container without systemd.
set -euo pipefail

HOST="$(hostname -s)"
CPUS="${SANDBOX_CPUS:-$(nproc)}"
MEM_MB="${SANDBOX_MEM_MB:-$(awk '/MemTotal/ {printf "%d", $2/1024*0.8}' /proc/meminfo)}"

command -v slurmctld >/dev/null || { echo "install slurm-wlm first" >&2; exit 2; }

mkdir -p /etc/slurm /var/spool/slurmctld /var/spool/slurmd /var/log/slurm /run/munge /var/lib/munge /var/log/munge /etc/munge /run/mysqld /var/lib/mysql
[ -f /etc/munge/munge.key ] || dd if=/dev/urandom bs=1 count=1024 of=/etc/munge/munge.key 2>/dev/null
chown -R munge:munge /etc/munge /var/lib/munge /var/log/munge /run/munge
chmod 700 /etc/munge /var/lib/munge /var/log/munge
chmod 400 /etc/munge/munge.key
pgrep -x munged >/dev/null || su -s /bin/sh munge -c /usr/sbin/munged

chown mysql:mysql /run/mysqld /var/lib/mysql
[ -d /var/lib/mysql/mysql ] || mariadb-install-db --user=mysql --datadir=/var/lib/mysql >/dev/null 2>&1
if ! pgrep -x mariadbd >/dev/null; then
  nohup mariadbd --user=mysql --datadir=/var/lib/mysql --socket=/run/mysqld/mysqld.sock >/var/log/mariadb.out 2>&1 &
fi
for _ in $(seq 1 40); do mariadb -e 'select 1' >/dev/null 2>&1 && break; sleep 1; done
mariadb -e "CREATE DATABASE IF NOT EXISTS slurm_acct_db;
            CREATE USER IF NOT EXISTS 'slurm'@'localhost' IDENTIFIED BY 'slurmpw';
            GRANT ALL ON slurm_acct_db.* TO 'slurm'@'localhost'; FLUSH PRIVILEGES;"

cat > /etc/slurm/slurmdbd.conf <<CONF
AuthType=auth/munge
DbdHost=localhost
SlurmUser=root
StorageType=accounting_storage/mysql
StorageHost=localhost
StorageUser=slurm
StoragePass=slurmpw
StorageLoc=slurm_acct_db
LogFile=/var/log/slurm/slurmdbd.log
PidFile=/run/slurmdbd.pid
CONF
chmod 600 /etc/slurm/slurmdbd.conf

cat > /etc/slurm/slurm.conf <<CONF
ClusterName=sandbox
SlurmctldHost=${HOST}
SlurmUser=root
AuthType=auth/munge
StateSaveLocation=/var/spool/slurmctld
SlurmdSpoolDir=/var/spool/slurmd
SlurmctldPidFile=/run/slurmctld.pid
SlurmdPidFile=/run/slurmd.pid
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
SelectType=select/cons_tres
SelectTypeParameters=CR_Core_Memory
SchedulerType=sched/backfill
PriorityType=priority/multifactor
PriorityWeightFairshare=10000
PriorityWeightQOS=1000
AccountingStorageType=accounting_storage/slurmdbd
AccountingStorageHost=localhost
AccountingStorageEnforce=associations,limits,qos
JobAcctGatherType=jobacct_gather/linux
JobCompType=jobcomp/none
NodeName=${HOST} CPUs=${CPUS} RealMemory=${MEM_MB} State=UNKNOWN
PartitionName=debug Nodes=${HOST} Default=YES MaxTime=INFINITE State=UP
CONF

pgrep -x slurmdbd >/dev/null || { nohup slurmdbd -D >/var/log/slurm/dbd.out 2>&1 & sleep 4; }
pgrep -x slurmctld >/dev/null || { nohup slurmctld -D >/var/log/slurm/ctld.out 2>&1 & sleep 3; }
pgrep -x slurmd >/dev/null || { nohup slurmd -D >/var/log/slurm/d.out 2>&1 & sleep 3; }

sacctmgr -i add cluster sandbox >/dev/null 2>&1 || true
sacctmgr -i add account research Description=research Organization=lab >/dev/null 2>&1 || true
sacctmgr -i add user root Account=research DefaultAccount=research >/dev/null 2>&1 || true
for _ in $(seq 1 20); do sinfo -h -o '%T' 2>/dev/null | grep -q idle && break; sleep 1; done
sinfo
