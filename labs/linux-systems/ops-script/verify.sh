#!/usr/bin/env bash
# Lint and behavioural tests of ensure_sysctl.sh. No root needed (the --apply test runs only as root).
set -euo pipefail
cd "$(dirname "$0")"
bash -n ensure_sysctl.sh test_ensure_sysctl.sh check_unit.sh errexit_demo.sh
command -v shellcheck >/dev/null && shellcheck ensure_sysctl.sh test_ensure_sysctl.sh check_unit.sh errexit_demo.sh || echo "shellcheck not installed: skipped"
bash test_ensure_sysctl.sh
echo "--- systemd units (offline verification, systemd need not be running)"
./check_unit.sh units/gpu-exporter.service
if ./check_unit.sh units/bad.service 2>/dev/null; then echo "FAIL: check_unit.sh accepted the broken unit" >&2; exit 1; fi
echo "ok: the broken unit is rejected although systemd-analyze itself exits 0"
echo "--- what set -e does NOT catch"
out="$(bash errexit_demo.sh)"
echo "$out"
[ "$(grep -c 'check_disk went on after a failure' <<<"$out")" = 2 ] || { echo "FAIL: set -e should be ignored in an if condition and in an || list" >&2; exit 1; }
grep -q '^  status: 0$' <<<"$out" || { echo "FAIL: pipeline without pipefail should report 0" >&2; exit 1; }
grep -q '^  status: 1$' <<<"$out" || { echo "FAIL: pipeline with pipefail should report 1" >&2; exit 1; }
echo "--- exercise 11 reference solution"
bash -n solutions/ensure_line.sh solutions/test_ensure_line.sh
command -v shellcheck >/dev/null && shellcheck solutions/ensure_line.sh solutions/test_ensure_line.sh || true
bash solutions/test_ensure_line.sh
echo "OK ops-script"
