#!/usr/bin/env bash
# Offline branch of the jobset-training lab. This lab is of kind "cluster": running the manifests needs Kubernetes
# with GPUs, JobSet and (optionally) Kueue and Kubeflow Trainer. What IS executed here, without a cluster:
#   1. lint: bash -n / shellcheck, py_compile, yamllint;
#   2. schema validation of the JobSet and TrainJob manifests against the vendored upstream CRDs
#      (and of the Kueue manifests of lab 12.1, whose queue the JobSet targets);
#   3. a rehearsal of the JobSet restart semantics with two local torchrun processes (gloo, CPU).
# Needs PYTHON with torch, pyyaml, jsonschema, kubernetes-validate; optional: shellcheck, yamllint.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import torch, yaml, jsonschema, kubernetes_validate" 2>/dev/null \
  || { echo "FAIL: PYTHON needs torch, pyyaml, jsonschema, kubernetes-validate" >&2; exit 2; }
echo "--- 1. lint"
bash -n local_two_nodes.sh verify.sh
if command -v shellcheck >/dev/null; then shellcheck local_two_nodes.sh verify.sh; else echo "shellcheck not installed: skipped"; fi
"$PY" -m py_compile train.py fetch_schemas.py
if command -v yamllint >/dev/null; then yamllint -c .yamllint.yaml manifests; else echo "yamllint not installed: skipped"; fi
echo "--- 2. schemas"
VAL=../kueue-manifests/validate_manifests.py
"$PY" "$VAL" --schemas schemas/crds.json manifests | tail -1
"$PY" - <<'PYEOF'
import copy, sys, yaml
sys.path.insert(0, "../kueue-manifests")
import validate_manifests as vm
vm.load_schemas("schemas/crds.json")
js = next(yaml.safe_load_all(open("manifests/20-jobset-torchrun.yaml")))
def bad(mut):
    d = copy.deepcopy(js); mut(d); return vm.validate_doc(d)
rj = lambda d: d["spec"]["replicatedJobs"][0]["template"]["spec"]
assert bad(lambda d: d["spec"]["failurePolicy"].update(maxRestart=3)), "typo in failurePolicy must be rejected"
assert bad(lambda d: rj(d).update(parallelism="16")), "string parallelism must be rejected"
assert bad(lambda d: rj(d)["template"]["spec"]["containers"][0].update(imagee="x")), "typo inside the pod template must be rejected"
assert bad(lambda d: d.update(apiVersion="jobset.x-k8s.io/v1beta1")), "unknown apiVersion must be rejected"
print("validator rejects 4 mutated JobSets")
PYEOF
echo "--- 3. local rehearsal of the restart semantics"
out="$(PYTHON="$PY" bash local_two_nodes.sh)"
echo "$out"
grep -q 'RESTARTS=1' <<<"$out" || { echo "FAIL: expected exactly one restart" >&2; exit 1; }
grep -q 'resuming_from_step=20' <<<"$out" || { echo "FAIL: the second attempt must resume from step 20" >&2; exit 1; }
grep -q 'done step=60' <<<"$out" || { echo "FAIL: training did not finish" >&2; exit 1; }
echo "OK jobset-training (offline branch): manifests valid, 1 restart, resumed from step 20, finished at step 60; cluster branch NOT executed"
