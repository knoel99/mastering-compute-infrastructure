#!/usr/bin/env bash
# GPU fragmentation by the default scoring: 4 single-GPU pods spread over 4 nodes, then a pod that needs a whole
# node stays Pending although 28 GPUs are free; with MostAllocated (bin packing) it fits. Requires up.sh.
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=lib.sh
. ./lib.sh
fail() { echo "FAIL: $*" >&2; exit 1; }
per_node() { kc get pods -l "job-name=$1" -o jsonpath='{range .items[*]}{.spec.nodeName}{"\n"}{end}' | sort | uniq -c | sed 's/^ */    /'; }
four_nodes() { for i in 1 2 3 4; do add_node "gpu-node-$i" "rack-0" 8; done; }

for mode in default binpack; do
  echo "== scheduler scoring: $([ "$mode" = default ] && echo 'LeastAllocated (default)' || echo 'MostAllocated, GPUs weigh 3')"
  reset_state; start_scheduler "$mode"; four_nodes
  kc apply -f manifests/job-small.yaml >/dev/null
  stable_bound eval-small 4 || fail "the 4 small pods should be bound"
  echo "  pods of eval-small per node (4 nodes x 8 GPUs, 4 GPUs requested in total):"; per_node eval-small
  kc apply -f manifests/job-big.yaml >/dev/null
  if [ "$mode" = default ]; then
    stable_bound train-whole-node 0 || fail "default scoring: the whole-node pod should stay Pending"
    pod="$(kc get pods -l job-name=train-whole-node -o name | head -1)"
    wait_for 30 "FailedScheduling" bash -c "$BIN/kubectl --request-timeout=10s get events --field-selector involvedObject.name=${pod#pod/},reason=FailedScheduling -o name | grep -q ."
    echo "  whole-node pod: Pending; free GPUs in the cluster: $((32 - 4)); scheduler says:"
    echo "    $(kc get events --field-selector "involvedObject.name=${pod#pod/},reason=FailedScheduling" -o jsonpath='{.items[0].message}')"
  else
    stable_bound train-whole-node 1 || fail "bin packing: the whole-node pod should be bound"
    echo "  whole-node pod: bound to $(kc get pods -l job-name=train-whole-node -o jsonpath='{.items[0].spec.nodeName}')"
  fi
done
reset_state; start_scheduler default
echo "OK fragmentation_demo: spread scoring left the whole-node pod Pending with 28 free GPUs; MostAllocated packed the small pods and let it run"
