#!/usr/bin/env bash
# Lab 14.2 check (about 1 minute, no GPU): generated files fresh, rules valid, tests green, lint clean, 12 mutants killed.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
command -v promtool >/dev/null || { echo "promtool missing: sudo apt-get install prometheus" >&2; exit 2; }
promtool --version | head -1

echo "--- 1. burn-rate table from the model, and generated files up to date"
"$PY" gen_rules.py --table
"$PY" gen_rules.py --check

echo "--- 2. promtool check rules"
promtool check rules rules/platform.rules.yml rules/slo.rules.yml

echo "--- 3. policy lint (severity, runbook, for, metrics really exposed)"
"$PY" lint_rules.py
if "$PY" lint_rules.py tests/bad.rules.yml > /tmp/lint_bad.$$ 2>&1; then echo "lint accepted a bad file" >&2; exit 1; fi
echo "lint rejects tests/bad.rules.yml, as it should:"; sed 's/^/    /' /tmp/lint_bad.$$; rm -f /tmp/lint_bad.$$

echo "--- 4. promtool test rules"
GOMAXPROCS=2 promtool test rules tests/platform.rules.test.yml
GOMAXPROCS=2 promtool test rules tests/slo.rules.test.yml
GOMAXPROCS=2 promtool test rules tests/wait_quantile.test.yml

echo "--- 5. mutation testing"
"$PY" mutate.py
echo "OK alert-rules"
