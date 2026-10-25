#!/usr/bin/env bash
# Lab 6.1 check (about 40 s, no root needed): the role converges, is idempotent, reports drift in
# check mode, fixes it, rolls out in batches with an abort path, and never leaks a vaulted secret.
# Every assertion is on counters or file content, never on timing.
set -euo pipefail
cd "$(dirname "$0")"
here="$PWD"
PY="${PYTHON:-python3}"
bindir="$(dirname "$(command -v "$PY")")"
find_tool() {
  if [ -x "$bindir/$1" ]; then echo "$bindir/$1"; elif command -v "$1" >/dev/null 2>&1; then command -v "$1"; else
    echo "FAIL: $1 not found (pip install ansible-core ansible-lint yamllint)" >&2; exit 2; fi
}
PLAYBOOK="$(find_tool ansible-playbook)"
VAULT="$(find_tool ansible-vault)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export ANSIBLE_CONFIG="$here/ansible.cfg" ANSIBLE_HOME="$tmp/ansible-home" ANSIBLE_LOCAL_TEMP="$tmp/ansible-tmp"
export ANSIBLE_NOCOLOR=1 ANSIBLE_FORCE_COLOR=0
root="$tmp/fleet"
mkdir -p "$root"
run() { "$PLAYBOOK" -e "lab_root=$root" "$@"; }
recap() { "$PY" tests/recap.py "$1" "$2"; }
# absent PATTERN FILE: fail when the fixed string occurs (a bare "! grep" would not trip errexit).
absent() { if grep -qF -- "$1" "$2"; then echo "FAIL: '$1' found in $2" >&2; exit 1; fi; }

echo "--- Lint"
run --syntax-check playbooks/site.yml playbooks/rolling.yml playbooks/secrets.yml playbooks/production_update.yml -e bmc_user=x -e bmc_password=x >/dev/null
echo "syntax-check: ok"
if command -v "$bindir/yamllint" >/dev/null 2>&1 || command -v yamllint >/dev/null 2>&1; then
  "$(find_tool yamllint)" -c .yamllint . && echo "yamllint: ok"
else
  echo "yamllint: not installed (skipped)"
fi
if [ -x "$bindir/ansible-lint" ] || command -v ansible-lint >/dev/null 2>&1; then
  (cd "$here" && "$(find_tool ansible-lint)" --offline -q playbooks roles) && echo "ansible-lint: ok"
else
  echo "ansible-lint: not installed (skipped)"
fi

echo "--- A. First run converges: every node changes"
run playbooks/site.yml > "$tmp/run1.log"
recap "$tmp/run1.log" 'changed>0'
for n in gpu-n01 gpu-n02 gpu-n03; do
  test -f "$root/$n/etc/security/limits.d/90-gpu-training.conf"
  test -f "$root/$n/etc/sysctl.d/90-gpu-training.conf"
  test -f "$root/$n/etc/ansible/facts.d/gpu_node.fact"
done
actions1="$(wc -l < "$root/gpu-n01/var/log/gpu_node_actions.log")"
echo "handlers ran on first run: $actions1 action lines on gpu-n01"
test "$actions1" -eq 3

echo "--- B. Second run is idempotent: zero changes, no handler"
run playbooks/site.yml > "$tmp/run2.log"
recap "$tmp/run2.log" 'changed=0'
actions2="$(wc -l < "$root/gpu-n01/var/log/gpu_node_actions.log")"
test "$actions2" -eq "$actions1"
echo "OK idempotence: changed=0 and the action log did not grow ($actions2 lines)"

echo "--- C. Drift: check mode reports it without fixing it"
limits="$root/gpu-n02/etc/security/limits.d/90-gpu-training.conf"
sed -i 's/unlimited/1/' "$limits"
drifted="$(cat "$limits")"
run playbooks/site.yml --check --diff --limit gpu-n02 > "$tmp/check.log"
grep -q '^-\* - memlock 1$' "$tmp/check.log"
grep -q '^+\* - memlock unlimited$' "$tmp/check.log"
recap "$tmp/check.log" 'changed>0'
test "$(cat "$limits")" = "$drifted"
echo "OK check mode: drift shown in the diff, file left untouched"
run playbooks/site.yml --limit gpu-n02 > "$tmp/fix.log"
grep -q 'memlock unlimited' "$limits"
run playbooks/site.yml > "$tmp/run3.log"
recap "$tmp/run3.log" 'changed=0'
echo "OK drift corrected, fleet idempotent again"

echo "--- D. Rolling rollout: canary first, then the rest"
rm -rf "$root" && mkdir -p "$root"
run playbooks/rolling.yml > "$tmp/roll.log"
recap "$tmp/roll.log" ok
first="$(head -n 1 "$root/rollout.log")"
case "$first" in *"drain gpu-n01") ;; *) echo "FAIL: canary was not first: $first"; exit 1;; esac
grep -c ' resume ' "$root/rollout.log" | grep -qx 3
echo "OK rolling order: first line of rollout.log = '${first#* }'"

echo "--- E. Rolling rollout with a failing canary: the remaining nodes stay untouched"
rm -rf "$root" && mkdir -p "$root"
if run playbooks/rolling.yml -e fail_host=gpu-n01 > "$tmp/roll_fail.log" 2>&1; then
  echo "FAIL: playbook should have failed"; exit 1
fi
test ! -e "$root/gpu-n02/etc/sysctl.d/90-gpu-training.conf"
test ! -e "$root/gpu-n03/etc/sysctl.d/90-gpu-training.conf"
test -e "$root/gpu-n01/etc/sysctl.d/90-gpu-training.conf"
absent ' resume ' "$root/rollout.log"
echo "OK abort path: gpu-n01 configured then failed; gpu-n02 and gpu-n03 never touched"

echo "--- F. Secrets: vaulted variable, 0600 file, nothing in the output"
secret="$("$PY" -c 'import secrets; print(secrets.token_hex(12))')"
umask 077
printf '%s' "$(head -c 24 /dev/urandom | base64)" > "$tmp/vault.pass"
"$VAULT" encrypt_string --vault-password-file "$tmp/vault.pass" "$secret" --name bmc_password > "$tmp/vault_vars.yml"
grep -q '^bmc_password: !vault' "$tmp/vault_vars.yml"
absent "$secret" "$tmp/vault_vars.yml"
rm -rf "$root" && mkdir -p "$root"
run playbooks/secrets.yml -e bmc_user=admin-sim -e "@$tmp/vault_vars.yml" --vault-password-file "$tmp/vault.pass" --diff > "$tmp/secrets.log" 2>&1
absent "$secret" "$tmp/secrets.log"
grep -q "password=$secret" "$root/gpu-n01/etc/gpu-node/bmc.env"
mode="$(stat -c '%a' "$root/gpu-n01/etc/gpu-node/bmc.env")"
test "$mode" = "600"
echo "OK secrets: deployed with mode $mode, plaintext absent from the vault file and from the --diff output"

echo "--- G. Anti-pattern: a timestamp in a managed file breaks idempotence (exercise 4)"
rm -rf "$root" && mkdir -p "$root"
run playbooks/site.yml -e gpu_node_stamp=true > "$tmp/stamp1.log"
run playbooks/site.yml -e gpu_node_stamp=true > "$tmp/stamp2.log"
recap "$tmp/stamp2.log" 'changed>0'
echo "OK with the timestamp the second run still changes every node: the fleet can never be reported as converged"

echo "OK ansible-node-role: converge, idempotence, check-mode drift, rolling abort, vaulted secret"
