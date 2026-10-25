#!/usr/bin/env bash
# Checks of chapter 9 (about 1 s, no root, read-only): the IOMMU report on a SYNTHETIC 4-GPU server and on this machine,
# the dry run of the vfio-pci binding script, and the KubeVirt manifests (parsed, never applied: no cluster here).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
expect() { if ! grep -qF -- "$2" <<<"$1"; then echo "FAIL: '$2' not in:"; echo "$1"; exit 1; fi; }

echo "--- A. Synthetic server (fictitious layout, real PCI IDs)"
"$PY" make_fixture.py "$tmp/root" > /dev/null
out="$("$PY" iommu_report.py --root "$tmp/root")"; echo "$out"
expect "$out" "group 30: 2 endpoint(s), blocked by host driver(s): 0000:18:00.0=nvidia, 0000:19:00.0=mlx5_core"
expect "$out" "group 45: 1 endpoint(s), ready for VFIO"
expect "$out" "verdict            : 1 of 4 group(s) ready for VFIO"

echo "--- B. vfio-pci binding, dry run on the synthetic tree"
out="$(SYSFS="$tmp/root/sys" bash bind_vfio.sh 0000:18:00.0)"; echo "$out"
expect "$out" "# skip bridge 0000:17:00.0"
expect "$out" "echo vfio-pci > /sys/bus/pci/devices/0000:19:00.0/driver_override"
if SYSFS="$tmp/root/sys" bash bind_vfio.sh 0000:18:00.0 --apply 2>/dev/null; then echo "FAIL: --apply must refuse a non-live tree"; exit 1; fi
bash -n bind_vfio.sh
if command -v shellcheck >/dev/null 2>&1; then shellcheck bind_vfio.sh verify.sh && echo "shellcheck: ok"; else echo "shellcheck: not installed (skipped)"; fi

echo "--- C. This machine (real, read-only)"
rc=0
"$PY" iommu_report.py || rc=$?
echo "exit status $rc (0: a group is ready, 1: groups but none ready, 2: no IOMMU group)"

echo "--- D. KubeVirt manifests (parsed only)"
if "$PY" -c "import yaml" 2>/dev/null; then
  "$PY" - <<'PYEOF'
import yaml
cr = yaml.safe_load(open("manifests/kubevirt-permitted-gpu.yaml"))
vmi = yaml.safe_load(open("manifests/vmi-gpu-passthrough.yaml"))
permitted = {d["resourceName"] for d in cr["spec"]["configuration"]["permittedHostDevices"]["pciHostDevices"]}
asked = {g["deviceName"] for g in vmi["spec"]["domain"]["devices"]["gpus"]}
assert cr["kind"] == "KubeVirt" and vmi["kind"] == "VirtualMachineInstance"
assert asked <= permitted, (asked, permitted)
print(f"OK manifests: the VMI asks for {sorted(asked)}, permitted by the KubeVirt CR")
PYEOF
else
  echo "PyYAML not installed: manifests not parsed (skipped)"
fi
echo "OK virt-checks: IOMMU report and vfio-pci dry run proven on a SYNTHETIC tree; no VM, no GPU, no cluster here"
