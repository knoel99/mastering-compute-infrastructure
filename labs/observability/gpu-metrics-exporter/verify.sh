#!/usr/bin/env bash
# Lab 14.1 check (about 10 s, no GPU, no Slurm needed). LIVE_SLURM=1 adds a branch that talks to a running Slurm.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
command -v promtool >/dev/null || { echo "promtool missing: sudo apt-get install prometheus" >&2; exit 2; }

echo "--- 1. unit tests (fixtures: simulated dcgm text, real Slurm 23.11.4 captures)"
"$PY" -m pytest -q -p no:cacheprovider tests

echo "--- 2. mutation check"
"$PY" mutants.py

echo "--- 3. promtool check metrics on one offline scrape"
"$PY" exporter.py --fixtures fixtures --once > "${TMPDIR:-/tmp}/exp14_1.$$.prom"
promtool check metrics < "${TMPDIR:-/tmp}/exp14_1.$$.prom"
grep -E '^(gpu_node_(hot|xid|busy_but_tensor_idle)_gpus|slurm_jobs\{reason_class="capacity")' "${TMPDIR:-/tmp}/exp14_1.$$.prom"
rm -f "${TMPDIR:-/tmp}/exp14_1.$$.prom"

echo "--- 4. real HTTP scrape of the running exporter"
PORT=$("$PY" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')
"$PY" exporter.py --fixtures fixtures --port "$PORT" & PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT
for _ in $(seq 1 50); do curl -sf "http://127.0.0.1:$PORT/metrics" >/dev/null 2>&1 && break; sleep 0.2; done
curl -sf "http://127.0.0.1:$PORT/metrics" | grep -E '^gpu_node_hot_gpus|^slurm_job_wait_seconds_count'
kill $PID; trap - EXIT

if [ "${LIVE_SLURM:-0}" = "1" ]; then
  echo "--- 5. LIVE branch: real squeue/sinfo/sacct (needs a running Slurm, e.g. labs/slurm/slurm-sandbox/setup.sh)"
  sbatch --wrap='sleep 2' >/dev/null
  DPORT=$("$PY" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')
  (cd fixtures && exec "$PY" -m http.server "$DPORT" --bind 127.0.0.1 >/dev/null 2>&1) & HPID=$!
  trap 'kill $HPID 2>/dev/null || true' EXIT
  sleep 1
  "$PY" exporter.py --dcgm-url "http://127.0.0.1:$DPORT/dcgm_node.prom" --once | grep -E '^(slurm_scrape_success|slurm_nodes|slurm_jobs|gpu_node_scrape_success)'
  "$PY" exporter.py --dcgm-url "http://127.0.0.1:$DPORT/dcgm_node.prom" --once | grep -q '^slurm_scrape_success 1.0'
  kill $HPID; trap - EXIT
  echo "live branch: ran (the GPU side was a fixture served over HTTP, standing in for dcgm-exporter)"
else
  echo "live branch: skipped (set LIVE_SLURM=1 with a running Slurm to run it)"
fi
echo "OK gpu-metrics-exporter"
