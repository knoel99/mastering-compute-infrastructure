#!/usr/bin/env bash
# Same 8-pod x 8-GPU Job, with and without native gang scheduling, on 6 then 8 fake GPU nodes.
# Requires a running control plane (up.sh). Prints a table and exits non-zero if an expectation fails.
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=lib.sh
. ./lib.sh

fail() { echo "FAIL: $*" >&2; exit 1; }
clean_jobs() {
  kc delete job --all --cascade=background --wait=false >/dev/null 2>&1 || true
  kc delete pods --all --force --grace-period=0 >/dev/null 2>&1 || true
  kc delete workloads.scheduling.k8s.io --all >/dev/null 2>&1 || true
  kc delete podgroups.scheduling.k8s.io --all >/dev/null 2>&1 || true
  sleep 2
}

reset_state
echo "== fake nodes: 6 x 8 GPUs"
for i in 1 2 3 4 5 6; do add_node "gpu-node-$i" "rack-$(( (i - 1) / 3 ))" 8; done
kc get nodes -o custom-columns='NODE:.metadata.name,GPUS:.status.allocatable.nvidia\.com/gpu,RACK:.metadata.labels.topology\.example\.com/rack'

echo; echo "== A. basic Job (pod-by-pod scheduling), 8 pods x 8 GPUs, 6 nodes"
kc apply -f manifests/job-basic.yaml >/dev/null
stable_bound train-basic 6 || fail "expected 6 bound pods for the basic job"
echo "bound pods: $(bound_count train-basic) of 8 (the 2 others are Pending)"
pending_pod="$(kc get pods -l job-name=train-basic -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.spec.nodeName}{"\n"}{end}' | awk 'NF==1{print $1; exit}')"
[ -n "$pending_pod" ] || fail "no pending pod found"
echo "scheduler message for a pending pod:"
wait_for 30 "FailedScheduling event" bash -c "$BIN/kubectl --request-timeout=10s get events --field-selector involvedObject.name=$pending_pod,reason=FailedScheduling -o name | grep -q ."
kc get events --field-selector "involvedObject.name=$pending_pod,reason=FailedScheduling" -o jsonpath='{.items[0].message}'; echo
echo "tolerations injected by the DefaultTolerationSeconds admission plugin:"
kc get pod "$pending_pod" -o jsonpath='{range .spec.tolerations[*]}{.key}{" "}{.effect}{" tolerationSeconds="}{.tolerationSeconds}{"\n"}{end}'
clean_jobs

echo; echo "== B. gang Job (native gang scheduling), same shape, still 6 nodes"
kc apply -f manifests/job-gang.yaml >/dev/null
stable_bound train-gang 0 || fail "expected 0 bound pods for the gang job on 6 nodes"
echo "bound pods: $(bound_count train-gang) of 8"
wait_for 60 "PodGroup Unschedulable" bash -c "$BIN/kubectl --request-timeout=10s get podgroups.scheduling.k8s.io -o jsonpath='{.items[0].status.conditions[0].reason}' | grep -q Unschedulable"
kc get podgroups.scheduling.k8s.io -o custom-columns='PODGROUP:.metadata.name,POLICY:.spec.schedulingPolicy.gang.minCount,REASON:.status.conditions[0].reason'
echo "PodGroup message: $(kc get podgroups.scheduling.k8s.io -o jsonpath='{.items[0].status.conditions[0].message}')"
[ "$(kc get podgroups.scheduling.k8s.io -o jsonpath='{.items[0].status.conditions[0].reason}')" = "Unschedulable" ] || fail "PodGroup should be Unschedulable"

echo; echo "== C. two more nodes join: 8 x 8 GPUs"
add_node gpu-node-7 rack-2 8
add_node gpu-node-8 rack-2 8
stable_bound train-gang 8 || fail "expected 8 bound pods once 8 nodes are available"
echo "bound pods: $(bound_count train-gang) of 8"
kc get pods -l job-name=train-gang -o custom-columns='POD:.metadata.name,NODE:.spec.nodeName' | sort
wait_for 30 "PodGroup scheduled" bash -c "$BIN/kubectl --request-timeout=10s get podgroups.scheduling.k8s.io -o jsonpath='{.items[0].status.conditions[0].reason}' | grep -q Scheduled"
echo "PodGroup reason after the join: $(kc get podgroups.scheduling.k8s.io -o jsonpath='{.items[0].status.conditions[0].reason}')"
clean_jobs
echo "OK gang_demo: basic job bound 6/8 pods, gang job bound 0/8 on 6 nodes then 8/8 on 8 nodes"
