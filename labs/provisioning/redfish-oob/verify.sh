#!/usr/bin/env bash
# Lab 6.4 check (about 5 s, no root, no network beyond 127.0.0.1): tests the client against a SIMULATED Redfish service,
# then runs the command-line client against the mock started as a background process that this script owns.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1
"$PY" -c "import pytest" 2>/dev/null || { echo "FAIL: PYTHON needs pytest" >&2; exit 2; }
tmp="$(mktemp -d)"
bmc_pid=""
cleanup() { if [ -n "$bmc_pid" ]; then kill "$bmc_pid" 2>/dev/null || true; wait "$bmc_pid" 2>/dev/null || true; fi; rm -rf "$tmp"; }
trap cleanup EXIT

echo "--- A. Unit tests against the in-process mock"
"$PY" -m pytest -q -p no:cacheprovider tests | tail -n 1
if command -v shellcheck >/dev/null 2>&1; then shellcheck verify.sh ipmi_example.sh && echo "shellcheck: ok"; else echo "shellcheck: not installed (skipped)"; fi
bash -n ipmi_example.sh
echo "ipmi_example.sh: syntax ok (not executed: no BMC here)"

echo "--- B. Command-line client against a background mock (health=Critical)"
head -c 18 /dev/urandom | base64 > "$tmp/pw"
"$PY" mock_bmc.py --health Critical --port-file "$tmp/port" --password-file "$tmp/pw" 2> "$tmp/mock.log" &
bmc_pid=$!
for _ in $(seq 1 100); do [ -s "$tmp/port" ] && break; sleep 0.1; done
test -s "$tmp/port"
url="http://127.0.0.1:$(cat "$tmp/port")"
rc=0
BMC_PASSWORD="$(cat "$tmp/pw")" "$PY" redfish_client.py "$url" > "$tmp/client.out" || rc=$?
cat "$tmp/client.out"
test "$rc" -eq 1
grep -q '^worst=Critical action=drain$' "$tmp/client.out"
echo "OK exit status $rc = drain advised"
rc=0
BMC_PASSWORD="wrong-password" "$PY" redfish_client.py "$url" > /dev/null 2> "$tmp/err.out" || rc=$?
test "$rc" -eq 2
echo "OK wrong password: exit $rc ($(cat "$tmp/err.out"))"
rc=0
"$PY" redfish_client.py "$url" > /dev/null 2> "$tmp/err2.out" || rc=$?
test "$rc" -eq 2
grep -q 'BMC_PASSWORD' "$tmp/err2.out"
echo "OK no password in the environment: refused, and there is no --password option"
echo "OK redfish-oob: client logic proven against a SIMULATED service (never against a real BMC)"
