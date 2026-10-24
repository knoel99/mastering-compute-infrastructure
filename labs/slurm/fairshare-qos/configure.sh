#!/usr/bin/env bash
# Add a fairshare / QOS / preemption policy to the sandbox Slurm (run after ../slurm-sandbox/setup.sh).
set -euo pipefail
conf=/etc/slurm/slurm.conf
grep -q '^PriorityCalcPeriod' "$conf" || cat >> "$conf" <<'CONF'
PriorityCalcPeriod=1
PriorityUsageResetPeriod=NONE
PreemptType=preempt/qos
PreemptMode=REQUEUE
CONF
scontrol reconfigure
sleep 2
# Slurm lower-cases account names: teama, teamb
sacctmgr -i add account teama parent=research fairshare=1 >/dev/null 2>&1 || true
sacctmgr -i add account teamb parent=research fairshare=1 >/dev/null 2>&1 || true
sacctmgr -i add user root account=teama >/dev/null 2>&1 || true
sacctmgr -i add user root account=teamb >/dev/null 2>&1 || true
sacctmgr -i add qos urgent Priority=1000 Preempt=normal >/dev/null 2>&1 || true
sacctmgr -i modify user root set qos+=urgent >/dev/null 2>&1 || true
