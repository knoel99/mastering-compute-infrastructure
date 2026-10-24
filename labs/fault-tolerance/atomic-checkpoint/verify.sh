#!/usr/bin/env bash
# Sandbox check: unit tests of the checkpoint protocol, the ablation table, then a real kill -9 campaign.
# Assertions are on equality of states and losses and on counters (kills, lives), never on durations.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import torch, pytest" 2>/dev/null || { echo "FAIL: PYTHON needs torch (CPU) and pytest" >&2; exit 2; }
"$PY" -m pytest -q -p no:cacheprovider test_ckpt.py
echo "--- ablation: what each part of the checkpoint protects"
"$PY" ablate.py
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
echo "--- sharded checkpoint written on 2 ranks, read on 4 (DCP, gloo, CPU)"
"$PY" dcp_reshard.py --dir "$tmp/dcp" 2>/dev/null | tail -3
echo "--- safetensors header"
if "$PY" -c "import safetensors" 2>/dev/null; then "$PY" safetensors_peek.py; else echo "SKIP (pip install safetensors to run this part)"; fi
echo "--- chaos: kill -9 at random moments"
"$PY" chaos.py --out "$tmp/chaos-run" | tail -3
"$PY" - "$tmp" <<'PYEOF'
import json, sys, pathlib
ref = json.loads((pathlib.Path(sys.argv[1]) / "chaos-run" / "ref" / "final.json").read_text())
cha = json.loads((pathlib.Path(sys.argv[1]) / "chaos-run" / "chaos" / "final.json").read_text())
assert ref["digest"] == cha["digest"], "final state differs from the uninterrupted run"
print("OK atomic-checkpoint: final state digest identical (%s...) after the kill campaign" % cha["digest"][:12])
PYEOF
