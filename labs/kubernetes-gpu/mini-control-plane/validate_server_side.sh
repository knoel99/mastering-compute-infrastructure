#!/usr/bin/env bash
# Part C: ask a REAL API server (v1.37.1) to validate the manifests of the other labs, CRD rules (CEL) included.
# The CRDs are the upstream ones, downloaded at pinned tags; no controller runs, so only API validation is exercised
# (no Kueue admission, no JobSet pods). Requires a running control plane (up.sh).
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=lib.sh
. ./lib.sh

CRD_DIR="$CACHE/crds"; mkdir -p "$CRD_DIR"
fetch_crd() {   # fetch_crd FILE URL
  [ -s "$CRD_DIR/$1" ] || curl -fsSL --retry 3 -o "$CRD_DIR/$1" "$2"
}
KUEUE=https://raw.githubusercontent.com/kubernetes-sigs/kueue/v0.20.3/config/components/crd/bases
for k in clusterqueues localqueues resourceflavors workloadpriorityclasses cohorts topologies; do
  fetch_crd "kueue_$k.yaml" "$KUEUE/kueue.x-k8s.io_$k.yaml"
done
fetch_crd jobset.yaml https://raw.githubusercontent.com/kubernetes-sigs/jobset/v0.13.0/config/components/crd/bases/jobset.x-k8s.io_jobsets.yaml
fetch_crd trainjobs.yaml https://raw.githubusercontent.com/kubeflow/trainer/v2.1.0/manifests/base/crds/trainer.kubeflow.org_trainjobs.yaml

echo "== CRDs applied (server-side apply)"
for f in "$CRD_DIR"/*.yaml; do kc apply --server-side -f "$f" >/dev/null; done
wait_for 60 "CRDs established" bash -c "[ \"\$($BIN/kubectl --request-timeout=10s get crd -o jsonpath='{range .items[*]}{.status.conditions[?(@.type==\"Established\")].status}{\"\\n\"}{end}' | grep -c True)\" -ge 8 ]"
kc get crd -o custom-columns='CRD:.metadata.name' --no-headers | sort | tr '\n' ' '; echo

kc apply -f ../kueue-manifests/manifests/00-namespaces.yaml >/dev/null    # real objects: namespaced kinds need them

echo; echo "== dry-run=server of lab 12.1 manifests (Kueue)"
kc apply --dry-run=server -f ../kueue-manifests/manifests | sed 's/^/  /'
echo; echo "== dry-run=server of lab 12.2 manifests (JobSet, TrainJob, PVC)"
kc apply --dry-run=server -f ../jobset-training/manifests | sed 's/^/  /'
echo; echo "== dry-run=server of this lab's manifests (jobs, device-plugin pod, time-slicing ConfigMap, DRA claim)"
kc create namespace gpu-operator >/dev/null 2>&1 || true
kc apply --dry-run=server -f manifests | sed 's/^/  /'

echo; echo "== the server rejects what the CRD forbids"
reject() {   # reject DESCRIPTION SED_EXPRESSION FILE : the mutated manifest must be refused by the API server
  local what="$1" expr="$2" file="$3" out
  if out="$(sed "$expr" "$file" | kc apply --dry-run=server -f - 2>&1)"; then
    echo "FAIL: the server accepted: $what" >&2; exit 1
  fi
  echo "  [$what]"; echo "$out" | grep -E 'is invalid|^\* ' | head -2 | cut -c1-230 | sed 's/^/      /'
}
Q=../kueue-manifests/manifests/30-clusterqueues.yaml
reject "borrowingLimit without cohort (CEL rule)" '/cohortName: gpu-pool/d' "$Q"
reject "unknown queueingStrategy" 's/queueingStrategy: StrictFIFO/queueingStrategy: FIFO/' "$Q"
reject "reclaimWithinCohort Never with borrowWithinCohort (CEL rule)" '0,/reclaimWithinCohort: Any/s//reclaimWithinCohort: Never/;0,/borrowWithinCohort: {policy: Never}/s//borrowWithinCohort: {policy: LowerPriority}/' "$Q"
reject "JobSet with a string parallelism" 's/parallelism: 16/parallelism: "sixteen"/' ../jobset-training/manifests/20-jobset-torchrun.yaml

echo; echo "== extended resource rules for GPUs (answers quoted in exercise 1 of the module)"
expect_gpu() {   # expect_gpu LABEL "RESOURCES (flow mapping)" EXPECTED_SUBSTRING : the server must answer with that text
  local label="$1" res="$2" want="$3" out
  out="$(printf 'apiVersion: v1\nkind: Pod\nmetadata: {name: gpu-rules}\nspec:\n  containers:\n    - name: c\n      image: registry.example/x:1\n      resources: {%s}\n' "$res" \
    | kc apply --dry-run=server -f - 2>&1 || true)"
  grep -q -- "$want" <<<"$out" || { echo "FAIL: variant $label: expected '$want', got: $out" >&2; exit 1; }
  echo "  $label: $(grep -m1 -E 'Required value|Invalid value|created' <<<"$out" | sed 's/^The Pod "gpu-rules" is invalid: //; s/^\* //' | cut -c1-200)"
}
expect_gpu a 'requests: {nvidia.com/gpu: 2}' 'Limit must be set'
expect_gpu b 'requests: {nvidia.com/gpu: 1}, limits: {nvidia.com/gpu: 2}' 'must be equal to nvidia.com/gpu limit of 2'
expect_gpu c 'limits: {nvidia.com/gpu: 0.5}' 'must be an integer'
expect_gpu d 'requests: {nvidia.com/gpu: 2}, limits: {nvidia.com/gpu: 2}' 'created (server dry run)'
echo "OK server-side validation"
