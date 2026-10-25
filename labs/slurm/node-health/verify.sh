#!/usr/bin/env bash
# Lab 5.3 check (about 80 seconds): health check drains/resumes the node; a failing prolog drains it and holds the job.
set -euo pipefail
cd "$(dirname "$0")"
here="$PWD"
trap 'rm -f /tmp/fake_gpu_xid; bash ../slurm-sandbox/teardown.sh --purge-db >/dev/null 2>&1 || true' EXIT
bash ../slurm-sandbox/teardown.sh --purge-db >/dev/null 2>&1 || true
bash ../slurm-sandbox/setup.sh >/dev/null
wait_until() { local t=$1; shift; timeout "$t" bash -c "until $*; do sleep 2; done"; }
rm -f /tmp/fake_gpu_xid

echo "--- Part A: HealthCheckProgram"
sed -i '/^HealthCheck/d;/^Prolog=/d' /etc/slurm/slurm.conf
cat >> /etc/slurm/slurm.conf <<CONF
HealthCheckProgram=$here/node_check.sh
HealthCheckInterval=10
HealthCheckNodeState=ANY
CONF
scontrol reconfigure; sleep 3
echo 79 > /tmp/fake_gpu_xid
wait_until 60 'sinfo -h -o "%T" | grep -q drain'
sinfo -R -h -o "%E | %N"
sinfo -R -h -o "%E" | grep -q 'health: gpu_xid:79'
rm -f /tmp/fake_gpu_xid
wait_until 60 'sinfo -h -o "%T" | grep -q "^idle"'
echo "OK part A: node drained with the right reason, then resumed by itself"

echo "--- Part A2: an operator's drain must never be undone by the health check"
node="$(hostname -s)"
scontrol update nodename="$node" state=drain reason="operator: planned maintenance"
sleep 25   # two and a half HealthCheckInterval periods: the node is healthy, yet it must stay drained
sinfo -R -h -o "%E" | grep -q 'operator: planned maintenance' || { echo "FAIL: the health check undid an operator's drain"; exit 1; }
sinfo -h -o "%T" | grep -q drain || { echo "FAIL: node is no longer drained"; exit 1; }
scontrol update nodename="$node" state=resume
wait_until 30 'sinfo -h -o "%T" | grep -q "^idle"'
echo "OK part A2: operator drain left alone by the health check"

echo "--- Part B: failing Prolog"
sed -i '/^HealthCheck/d' /etc/slurm/slurm.conf
echo "Prolog=$here/prolog_gate.sh" >> /etc/slurm/slurm.conf
scontrol reconfigure; sleep 3
echo 79 > /tmp/fake_gpu_xid
job=$(sbatch --parsable --wrap='echo should-not-run' -o /dev/null)
wait_until 40 "squeue -h -j $job -o %r | grep -qi 'launch.failed'"
squeue -o "%i %T %r"; sinfo -R -h -o "%E | %N"
sinfo -R -h -o "%E" | grep -q 'Prolog error'
echo "OK part B: node drained ('Prolog error') and job held after requeue (needs scontrol release once the node is fixed)"
echo "OK node-health"
