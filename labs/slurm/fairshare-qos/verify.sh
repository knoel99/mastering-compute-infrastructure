#!/usr/bin/env bash
# Lab 5.2 check (a little over 2 minutes; the wait is dominated by PriorityCalcPeriod=1): fairshare orders pending jobs, a QOS preempts and requeues.
set -euo pipefail
cd "$(dirname "$0")"
trap 'bash ../slurm-sandbox/teardown.sh --purge-db >/dev/null 2>&1 || true' EXIT
bash ../slurm-sandbox/teardown.sh --purge-db >/dev/null 2>&1 || true   # clean accounting: usage from earlier runs would bias the test
bash ../slurm-sandbox/setup.sh >/dev/null
bash ./configure.sh
wait_until() {  # wait_until <seconds> <shell condition evaluated in this shell>
  local t=$1; shift; local end=$((SECONDS + t))
  until eval "$*"; do
    [ "$SECONDS" -ge "$end" ] && { echo "TIMEOUT waiting for: $*" >&2; return 1; }
    sleep 2
  done
}
fs() {  # sshare indents child accounts with spaces even in parsable mode: strip them before comparing
  sshare -n -a -P -o Account,User,FairShare | awk -F'|' -v a="$1" '{gsub(/ /,"",$1); gsub(/ /,"",$2)} $1==a && $2=="root" {print $3}'
}
fs_ready() { local a b; a=$(fs teama); b=$(fs teamb); [ -n "$a" ] && [ -n "$b" ] && awk -v a="$a" -v b="$b" 'BEGIN{exit !(a+0 < b+0)}'; }

echo "--- Part A: fairshare"
for _ in $(seq 1 8); do sbatch -A teama --cpus-per-task=1 --wrap='sleep 4' -o /dev/null >/dev/null; done
# shellcheck disable=SC2016  # the condition is evaluated later by wait_until, on purpose
wait_until 120 '[ -z "$(squeue -h)" ]'
echo "teama has consumed CPU time; waiting for slurmctld to recompute the fairshare factors (PriorityCalcPeriod=1 min)"
wait_until 240 fs_ready
sshare -a -l -o Account,User,NormShares,RawUsage,NormUsage,EffectvUsage,LevelFS,FairShare | grep -E 'Account|team'
# shellcheck disable=SC2034  # the blocker job only has to exist
blocker=$(sbatch --parsable -A teamb --cpus-per-task=4 --time=2 --wrap='sleep 25' -o /dev/null)
ja=$(sbatch --parsable -A teama --cpus-per-task=2 --wrap='sleep 2' -o /dev/null)
jb=$(sbatch --parsable -A teamb --cpus-per-task=2 --wrap='sleep 2' -o /dev/null)
sleep 2
sprio -o "%i %o %Y %f" -j "$ja,$jb"   # %o = account (%a would be the normalized age factor)
fa=$(sprio -h -o "%f" -j "$ja"); fb=$(sprio -h -o "%f" -j "$jb")
awk -v a="$fa" -v b="$fb" 'BEGIN{exit !(b>a)}' || { echo "FAIL: fairshare factor of teamb ($fb) should exceed teama ($fa)"; exit 1; }
# shellcheck disable=SC2016  # the condition is evaluated later by wait_until, on purpose
wait_until 120 '[ -z "$(squeue -h)" ]'
sa=$(sacct -X -n -j "$ja" --format=Start | head -1); sb=$(sacct -X -n -j "$jb" --format=Start | head -1)
sacct -X -j "$ja,$jb" --format=JobID,Account,Start%22
[[ "$sb" < "$sa" || "$sb" == "$sa" ]] || { echo "FAIL: teamb job should start no later than teama job"; exit 1; }
echo "OK part A: lighter user (fairshare $fb) was served before heavier user ($fa)"

echo "--- Part B: QOS preemption with requeue"
low=$(sbatch --parsable -A teama --qos=normal --cpus-per-task=4 --time=5 --requeue --wrap='sleep 120' -o /dev/null)
wait_until 30 "squeue -h -j $low -o %T | grep -q RUNNING"
hi=$(sbatch --parsable -A teamb --qos=urgent --cpus-per-task=1 --time=2 --wrap='sleep 6' -o /dev/null)
wait_until 30 "squeue -h -j $hi -o %T | grep -q RUNNING"
squeue -o "%i %q %T %r"
restarts=$(scontrol show job "$low" | sed -n 's/.*Restarts=\([0-9]*\).*/\1/p')
[ "$restarts" -ge 1 ] || { echo "FAIL: low-priority job was not requeued"; exit 1; }
wait_until 30 "sacct -X -n -j $low --format=JobID,State | grep -q PREEMPTED" || { echo "FAIL: no PREEMPTED record in the accounting"; exit 1; }   # slurmdbd gets the record a moment after the preemption
scancel "$low"
echo "OK part B: urgent job started, normal job preempted and requeued (Restarts=$restarts)"
echo "OK fairshare-qos"
