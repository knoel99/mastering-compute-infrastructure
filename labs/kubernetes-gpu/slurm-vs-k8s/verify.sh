#!/usr/bin/env bash
# Sandbox check: the decision matrix is well formed, the scoring tool is correct (tests), the table is printed.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import pytest, yaml" 2>/dev/null || { echo "FAIL: PYTHON needs pytest and pyyaml" >&2; exit 2; }
"$PY" -m py_compile score.py
"$PY" -m pytest -q -p no:cacheprovider tests
"$PY" score.py --draws 2000 --seed 0
"$PY" - <<'PYEOF'
import score as sc
_, criteria, scenarios = sc.load()
table = sc.scores_of(criteria)
s = scenarios["enterprise-platform"]
w = sc.breakeven(table, s["weights"], s["must"], "ops_cost")
print(f"breakeven: in 'enterprise-platform' the winner changes when the weight of ops_cost goes from {s['weights']['ops_cost']} to {w}")
PYEOF
echo "OK slurm-vs-k8s: matrix well formed, tests green"
