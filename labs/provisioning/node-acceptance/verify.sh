#!/usr/bin/env bash
# Lab 6.3 check, REPLAY BRANCH ONLY (about 5 s, no GPU): lints the runner, proves that the reference decision rules pass the
# tests and the starter does not, and replays recorded/synthetic evidence through acceptance.sh.
# NOT covered here: the live branch (nvidia-smi, dcgmi diag, gpu_burn, nccl-tests) needs a GPU node and has never been run.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1
"$PY" -c "import pytest" 2>/dev/null || { echo "FAIL: PYTHON needs pytest" >&2; exit 2; }
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "--- A. Lint"
bash -n acceptance.sh
bash -n verify.sh
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck acceptance.sh verify.sh
  echo "shellcheck: ok"
else
  echo "shellcheck: not installed (skipped)"
fi
"$PY" - <<'PYEOF'
import ast, glob
files = glob.glob("*.py") + glob.glob("lib/*.py") + glob.glob("reference/*.py") + glob.glob("starter/*.py") + glob.glob("tests/*.py")
for f in files:
    ast.parse(open(f, encoding="utf-8").read(), filename=f)
print(f"python syntax: ok ({len(files)} files)")
PYEOF

echo "--- B. Synthetic fixtures are reproducible"
"$PY" make_fixtures.py "$tmp/fixtures" >/dev/null
diff -r fixtures "$tmp/fixtures"
echo "OK fixtures: $(find fixtures -mindepth 1 -maxdepth 1 -type d | wc -l) scenarios, byte-identical to make_fixtures.py output"

echo "--- C. Reference rules pass the tests, the starter does not"
IMPL=reference "$PY" -m pytest -q -p no:cacheprovider tests | tail -n 1
if IMPL=starter "$PY" -m pytest -q -p no:cacheprovider tests > "$tmp/starter.log" 2>&1; then
  echo "FAIL: starter passes all tests, so the tests do not discriminate"; exit 1
fi
echo "starter (failures expected): $(tail -n 1 "$tmp/starter.log")"

echo "--- D. Replay through acceptance.sh: exit status 0 accept, 1 reject, 3 retest"
check() {
  local scenario="$1" want="$2" rc=0
  PYTHON="$PY" bash acceptance.sh --fixtures "fixtures/$scenario" --level full > "$tmp/out.json" || rc=$?
  if [ "$rc" -ne "$want" ]; then echo "FAIL: $scenario exited $rc, expected $want"; cat "$tmp/out.json"; exit 1; fi
  echo "  $scenario -> exit $rc ($("$PY" -c "import json,sys; print(json.load(open(sys.argv[1]))['verdict'])" "$tmp/out.json"))"
}
check good 0
check remap_failure 1
check dcgm_fail_rc0 1
check nccl_marginal 3
check xid79 1

echo "--- E. Live mode refuses to run without the tools"
if command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi present: live refusal check skipped (this machine has a GPU stack)"
else
  rc=0; bash acceptance.sh --level quick > /dev/null 2> "$tmp/live.err" || rc=$?
  test "$rc" -eq 2
  echo "OK live mode without GPU tools: exit 2 ($(cat "$tmp/live.err"))"
fi
echo "NOT EXECUTED: live branch on real GPUs (nvidia-smi / dcgmi diag / gpu_burn / nccl-tests); kind = gpu, badge = unverified."
echo "OK node-acceptance (replay branch): decision rules proven on synthetic evidence"
