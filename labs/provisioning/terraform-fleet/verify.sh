#!/usr/bin/env bash
# Lab 6.2 check (about 10 s once the provider is cached, longer the first time; needs terraform >= 1.6 and the registry once).
# Works on a COPY of the lab in a temporary directory: no state, plugin or generated file lands in the repository.
# Every assertion is on exit codes, counts or file content.
set -euo pipefail
cd "$(dirname "$0")"
src="$PWD"
PY="${PYTHON:-python3}"
TF="${TERRAFORM:-terraform}"
command -v "$TF" >/dev/null 2>&1 || { echo "FAIL: terraform not found (set TERRAFORM=/path/to/terraform)" >&2; exit 2; }
export TF_IN_AUTOMATION=1 TF_INPUT=0 CHECKPOINT_DISABLE=1 TF_CLI_ARGS="-no-color"
export TF_PLUGIN_CACHE_DIR="${TF_PLUGIN_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/terraform-plugins}"
mkdir -p "$TF_PLUGIN_CACHE_DIR"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp -r "$src/modules" "$src/envs" "$tmp/"
echo "terraform: $("$TF" version | head -n 1)"

echo "--- A. Static checks"
"$TF" fmt -check -recursive "$tmp" && echo "fmt: ok"
(cd "$tmp/modules/fleet" && "$TF" init -backend=false >/dev/null && "$TF" validate)

echo "--- B. terraform test (validation rules and outputs, plan only)"
(cd "$tmp/modules/fleet" && "$TF" test | tail -n 3)

echo "--- C. Apply the prod environment"
out="$tmp/generated"
mkdir -p "$out"
cd "$tmp/envs/prod"
"$TF" init >/dev/null
"$TF" plan -var "output_dir=$out" -var-file=terraform.tfvars -out=plan.bin | grep -E '^Plan:'
"$TF" apply plan.bin | grep -E '^Apply complete'
"$TF" output -json summary > "$tmp/summary.json"
"$PY" - "$tmp/summary.json" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))
assert s["nodes"] == 6, s
assert s["gpus"] == 8 * 4 + 4 + 0, s
assert s["racks"] == {"r01": 2, "r02": 2, "r03": 2}, s
print("OK outputs:", json.dumps(s, sort_keys=True))
PYEOF
test "$("$TF" state list | wc -l)" -eq 11
echo "OK state: $("$TF" state list | wc -l) objects (6 terraform_data + 5 local_file)"
grep -q '^dhcp-host=02:00:00:00:02:05,gpu-n05,192.0.2.25$' "$out/prod-dhcp-hosts.conf"
grep -q '^NodeName=gpu-n01 Gres=gpu:8 Feature=h100,r01 State=UNKNOWN$' "$out/prod-slurm-nodes.conf"
echo "OK rendered files: $(wc -l < "$out/prod-dhcp-hosts.conf") DHCP lines, $(wc -l < "$out/prod-slurm-nodes.conf") Slurm lines"

echo "--- D. Idempotence: a second plan has nothing to do"
rc=0; "$TF" plan -var "output_dir=$out" -var-file=terraform.tfvars -detailed-exitcode >/dev/null || rc=$?
test "$rc" -eq 0
echo "OK plan -detailed-exitcode = $rc (no change)"

echo "--- E. Drift: someone edits a generated file by hand"
echo 'dhcp-host=02:de:ad:be:ef:00,rogue,192.0.2.99' >> "$out/prod-dhcp-hosts.conf"
rc=0; "$TF" plan -var "output_dir=$out" -var-file=terraform.tfvars -detailed-exitcode > "$tmp/drift.txt" || rc=$?
test "$rc" -eq 2
grep -E '^Plan:|will be (updated|replaced)|must be replaced' "$tmp/drift.txt" | head -n 3
echo "OK drift detected: plan -detailed-exitcode = $rc"
"$TF" apply -auto-approve -var "output_dir=$out" -var-file=terraform.tfvars | grep -E '^Apply complete'
if grep -q rogue "$out/prod-dhcp-hosts.conf"; then echo "FAIL: rogue line survived apply"; exit 1; fi
echo "OK apply restored the declared content"

echo "--- F. Remove a node from the map: what does the plan destroy?"
grep -v '"cpu-n01"' terraform.tfvars > "$tmp/five.tfvars"
rc=0; "$TF" plan -var "output_dir=$out" -var-file="$tmp/five.tfvars" -detailed-exitcode > "$tmp/remove.txt" || rc=$?
test "$rc" -eq 2
grep -E '^Plan:' "$tmp/remove.txt"
grep -q 'terraform_data.node\["cpu-n01"\] will be destroyed' "$tmp/remove.txt"
grep -q '^Plan: 4 to add, 0 to change, 5 to destroy' "$tmp/remove.txt"
echo "OK removing cpu-n01 destroys its record (1) and replaces the 4 node-dependent files (4 destroy + 4 add); dnsmasq.conf does not depend on the node list"

echo "--- G. Invalid input is rejected before any change"
sed 's/02:00:00:00:02:02/02:00:00:00:02:01/' terraform.tfvars > "$tmp/dupmac.tfvars"
rc=0; "$TF" plan -var "output_dir=$out" -var-file="$tmp/dupmac.tfvars" > "$tmp/dup.txt" 2>&1 || rc=$?
test "$rc" -ne 0
grep -q 'share the same MAC' "$tmp/dup.txt"
echo "OK duplicate MAC refused: $(grep -m1 -o 'Two nodes share the same MAC address' "$tmp/dup.txt")"

echo "--- H0. PXE server files: dnsmasq syntax and iPXE script structure"
if command -v dnsmasq >/dev/null 2>&1; then
  dnsmasq --test -C "$out/prod-dnsmasq.conf"
else
  echo "dnsmasq not installed (apt install dnsmasq-base): syntax check skipped"
fi
"$PY" - "$out/prod-boot.ipxe" <<'PYEOF'
import re, sys
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
assert lines[0] == "#!ipxe", lines[0]
labels = {l[1:] for l in lines if l.startswith(":")}
targets = set(re.findall(r"goto (\w+)", "\n".join(lines)))
missing = targets - labels
assert not missing, f"goto to undefined labels: {missing}"
nodes = [l for l in labels if l.startswith("node_")]
assert len(nodes) == 6, nodes
macs = re.findall(r"iseq \$\{net0/mac\} (\S+) ", "\n".join(lines))
assert len(macs) == len(set(macs)) == 6, macs
print(f"OK boot.ipxe: {len(nodes)} node labels, every goto resolves, MACs unique")
PYEOF

echo "--- H. The generated inventory is a valid Ansible inventory (skipped if ansible-inventory is absent)"
bindir="$(dirname "$(command -v "$PY")")"
AI=""
if [ -x "$bindir/ansible-inventory" ]; then AI="$bindir/ansible-inventory"; elif command -v ansible-inventory >/dev/null 2>&1; then AI="$(command -v ansible-inventory)"; fi
if [ -n "$AI" ]; then
  ANSIBLE_HOME="$tmp/ansible-home" "$AI" -i "$out/prod-inventory.yml" --list > "$tmp/inv.json"
  "$PY" - "$tmp/inv.json" <<'PYEOF'
import json, sys
inv = json.load(open(sys.argv[1]))
hosts = inv["_meta"]["hostvars"]
assert len(hosts) == 6, len(hosts)
assert hosts["gpu-n05"]["gpu_model"] == "a100" and hosts["gpu-n05"]["ansible_host"] == "192.0.2.25"
assert sorted(inv["gpu_nodes"]["children"]) == ["rack_r01", "rack_r02", "rack_r03"], inv["gpu_nodes"]
print("OK ansible-inventory parses the file: 6 hosts, 3 rack groups")
PYEOF
else
  echo "ansible-inventory not installed: step H skipped"
fi
echo "OK terraform-fleet: validate, test, apply, idempotence, drift, node removal, input validation"
