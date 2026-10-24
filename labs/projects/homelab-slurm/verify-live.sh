#!/usr/bin/env bash
# Live proof on a REAL single-node Slurm (the sandbox of the Slurm module): apply cluster.yml twice, check that the
# second run changes nothing, scrape real metrics, check them with promtool, drain a node and see it. Needs root.
# IMPL=reference (default) or IMPL=starter to test your own code. Always purges the accounting database at the end.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
IMPL="${IMPL:-reference}"
SANDBOX=../../slurm/slurm-sandbox
[ "$(id -u)" = 0 ] || { echo "FAIL: root is required (the sandbox writes /etc/slurm)" >&2; exit 2; }
command -v promtool >/dev/null || { echo "FAIL: promtool not found" >&2; exit 2; }
cleanup() { scancel --all >/dev/null 2>&1 || true; bash "$SANDBOX/teardown.sh" --purge-db >/dev/null 2>&1 || true; }
trap cleanup EXIT
bash "$SANDBOX/teardown.sh" --purge-db >/dev/null 2>&1 || true   # start from an empty accounting database
bash "$SANDBOX/setup.sh" >/dev/null
node="$(sinfo -h -N -o %N | head -1)"

echo "--- 1. plan on a fresh cluster, then apply"
plan="$("$PY" "$IMPL/config.py" "$IMPL/cluster.yml")"
echo "$plan"
[ "$(wc -l <<<"$plan")" -ge 5 ] || { echo "FAIL: expected a plan of at least 5 commands" >&2; exit 1; }
"$PY" "$IMPL/config.py" "$IMPL/cluster.yml" --apply >/dev/null

echo "--- 2. the second run must be empty (convergence)"
again="$("$PY" "$IMPL/config.py" "$IMPL/cluster.yml")"
[ -z "$again" ] || { echo "FAIL: second plan is not empty:" >&2; echo "$again" >&2; exit 1; }
echo "converged: 0 commands"
sacctmgr -nP show assoc format=Account,User,Share,QOS | grep -E '^teama\|alice\|' || { echo "FAIL: alice not in teama" >&2; exit 1; }

echo "--- 3. real metrics from a real queue"
sacctmgr -i add user root account=teama >/dev/null 2>&1 || true
for i in 1 2 3 4; do sbatch -J lv$i -A teama -N1 -n4 --wrap 'sleep 300' >/dev/null; done
for _ in $(seq 1 30); do squeue -h -t R | grep -q . && break; sleep 1; done
metrics="$("$PY" "$IMPL/exporter.py" --once)"
echo "$metrics" | grep -E '^slurm_(scrape_ok|jobs)\{?' | head -8
grep -qx 'slurm_scrape_ok 1' <<<"$metrics" || { echo "FAIL: scrape not ok" >&2; exit 1; }
running="$(sed -n 's/^slurm_jobs{partition="[^"]*",state="RUNNING"} //p' <<<"$metrics" | head -1)"
pending="$(sed -n 's/^slurm_jobs{partition="[^"]*",state="PENDING"} //p' <<<"$metrics" | head -1)"
if [ "${running:-0}" -lt 1 ] || [ "${pending:-0}" -lt 2 ]; then echo "FAIL: RUNNING=$running PENDING=$pending" >&2; exit 1; fi
grep -q '^slurm_account_norm_shares{account="teama"}' <<<"$metrics" || { echo "FAIL: no share for teama" >&2; exit 1; }
promtool check metrics <<<"$metrics" >/dev/null || { echo "FAIL: promtool rejects the exposition" >&2; exit 1; }
echo "RUNNING=$running PENDING=$pending, promtool accepts the exposition"

echo "--- 4. a drained node becomes slurm_node_unhealthy"
scontrol update nodename="$node" state=drain reason="gpu_xid:79"
sleep 1
"$PY" "$IMPL/exporter.py" --once | grep -E '^slurm_node_unhealthy\{' | tee /dev/stderr | grep -q 'reason="gpu_xid"} 1' \
  || { echo "FAIL: the drained node is not reported unhealthy" >&2; exit 1; }
scontrol update nodename="$node" state=resume
echo "OK homelab-slurm (live)"
