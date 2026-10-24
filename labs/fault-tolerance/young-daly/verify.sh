#!/usr/bin/env bash
# Sandbox check: tests of the formulas and of the simulator, then one sweep with the course's values.
# No assertion depends on wall-clock time: only on counters, ratios and statistical tolerances.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import numpy, pytest" 2>/dev/null || { echo "FAIL: PYTHON needs numpy and pytest" >&2; exit 2; }
"$PY" -m pytest -q -p no:cacheprovider test_yd.py
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
"$PY" sweep.py --delta 60 --mtbf-hours 3.09 --restart 300 --json "$tmp/sweep.json" --svg "$tmp/yd.svg" | tail -4
"$PY" - "$tmp/sweep.json" "$tmp/yd.svg" <<'PYEOF'
import json, sys
r = json.load(open(sys.argv[1]))
s = r["summary"]
gap = s["goodput_best_exp"] - s["goodput_at_young_exp"]
assert gap < 0.01, "Young's period should be within one point of the best sampled period"
assert abs(s["t_daly_high"] - s["t_exact"]) / s["t_exact"] < 0.005
assert open(sys.argv[2]).read().startswith("<svg")
print("OK young-daly: Young T=%.0f s, Daly T=%.0f s, exact argmin T=%.0f s; goodput at Young %.4f vs best sampled %.4f"
      % (s["t_young"], s["t_daly_high"], s["t_exact"], s["goodput_at_young_exp"], s["goodput_best_exp"]))
PYEOF
