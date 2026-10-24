#!/usr/bin/env bash
# Sandbox check for the kueue-manifests lab (no cluster, no network, no GPU).
# 1. the manifests are valid against the Kueue v0.20.3 CRD schemas and Kubernetes 1.37 core schemas;
# 2. the validator rejects nine mutated ClusterQueues (tests/test_manifests.py);
# 3. the reference admission model passes every test, the starter does not;
# 4. the scenario trace and the gang-deadlock table are printed from the reference model.
# Needs: PYTHON with pytest, pyyaml, jsonschema, kubernetes-validate  (pip install pytest pyyaml jsonschema kubernetes-validate)
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import pytest, yaml, jsonschema, kubernetes_validate" 2>/dev/null \
  || { echo "FAIL: PYTHON needs pytest, pyyaml, jsonschema, kubernetes-validate" >&2; exit 2; }
"$PY" -m py_compile model.py validate_manifests.py run_scenario.py gang_deadlock.py topology_fit.py fetch_schemas.py \
  reference/admission.py starter/admission.py
echo "--- 1. manifests"
"$PY" validate_manifests.py manifests | tail -1
echo "--- 2. + 3. tests on the reference implementation"
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests
echo "--- starter (failures expected)"
log="$(mktemp)"
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests >"$log" 2>&1; then
  echo "starter passes all tests: the tests do not discriminate"; exit 1
fi
tail -1 "$log"
echo "--- 4. scenario (reference model), last state"
"$PY" run_scenario.py scenarios/platform-day.yaml | tail -4
"$PY" gang_deadlock.py --trials 5000 | sed -n 1,4p
echo "--- 5. exercise 11 solution (256-GPU pool for three teams)"
"$PY" validate_manifests.py exercises/ex11 | tail -1
"$PY" run_scenario.py exercises/ex11-scenario.yaml --manifests exercises/ex11 | grep -E 'PREEMPT|ADMIT' | head -5
"$PY" run_scenario.py exercises/ex11-scenario.yaml --manifests exercises/ex11 | grep -q 'PREEMPT eval-sweep' || { echo "FAIL: expected eval-sweep to be preempted" >&2; exit 1; }
echo "OK kueue-manifests: manifests valid, validator rejects mutants, reference green, starter red"
