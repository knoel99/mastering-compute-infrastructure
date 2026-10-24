#!/usr/bin/env bash
# Sandbox check: a real Kubernetes v1.37.1 control plane (etcd, apiserver, controller-manager, scheduler), fake GPU nodes.
#   part A: the same 8-pod x 8-GPU Job with and without native gang scheduling (gang_demo.sh);
#   part B: GPU fragmentation by the default scoring, and bin packing (fragmentation_demo.sh);
#   part C: server-side validation of the manifests of labs 12.1 and 12.2 against the upstream CRDs.
# First run downloads ~350 MB (dl.k8s.io, registry.k8s.io, raw.githubusercontent.com) into $K8S_MINI_CACHE.
# Never asserts on durations: it polls for states and stops every process it started, even on failure.
set -euo pipefail
cd "$(dirname "$0")"
bash -n lib.sh up.sh down.sh gang_demo.sh fragmentation_demo.sh validate_server_side.sh verify.sh
if command -v shellcheck >/dev/null; then shellcheck -x lib.sh up.sh down.sh gang_demo.sh fragmentation_demo.sh validate_server_side.sh verify.sh; fi
for tool in curl openssl python3; do command -v "$tool" >/dev/null || { echo "FAIL: $tool is required" >&2; exit 2; }; done
# shellcheck source=lib.sh
. ./lib.sh
trap cp_down EXIT
cp_up
echo "--- gang scheduling demo"
bash gang_demo.sh
echo "--- fragmentation demo"
bash fragmentation_demo.sh
echo "--- server-side validation"
bash validate_server_side.sh
echo "OK mini-control-plane: Kubernetes $K8S_VERSION control plane without kubelet; gang demo and server-side validation passed"
