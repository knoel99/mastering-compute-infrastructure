#!/usr/bin/env bash
# Hand the whole IOMMU group of one PCI device to vfio-pci, following the kernel VFIO documentation (the group is the unit
# of ownership) and the driver_override method of the KubeVirt host-devices guide.
# DRY RUN by default: prints the commands it would run. --apply runs them; do that only as root, on a drained host you own.
#   bind_vfio.sh 0000:18:00.0            # print the commands
#   SYSFS=/path/to/fixture/sys bind_vfio.sh 0000:18:00.0   # read a synthetic tree (dry run only)
set -euo pipefail
usage() { echo "usage: $0 <pci-address> [--apply]   e.g. $0 0000:18:00.0" >&2; exit 2; }
[ $# -ge 1 ] || usage
bdf="$1"
apply="${2:-}"
sysfs="${SYSFS:-/sys}"
if [ "$apply" = "--apply" ] && [ "$sysfs" != "/sys" ]; then echo "refusing --apply on a non-live tree ($sysfs)" >&2; exit 2; fi
dev="$sysfs/bus/pci/devices/$bdf"
[ -e "$dev/iommu_group" ] || { echo "no IOMMU group for $bdf: IOMMU disabled or absent" >&2; exit 1; }
group="$(basename "$(readlink "$dev/iommu_group")")"

run() {  # $1: shell command line
  if [ "$apply" = "--apply" ]; then sh -c "$1"; else echo "$1"; fi
}

echo "# IOMMU group $group of $bdf"
run "modprobe vfio-pci"
for member in "$dev"/iommu_group/devices/*; do
  m="$(basename "$member")"
  case "$(cat "$member/class")" in
    0x06*) echo "# skip bridge $m (vfio-pci does not support PCI bridges)"; continue ;;
  esac
  if [ -L "$member/driver" ]; then
    drv="$(basename "$(readlink "$member/driver")")"
    if [ "$drv" = "vfio-pci" ]; then echo "# $m is already bound to vfio-pci"; continue; fi
    run "echo $m > /sys/bus/pci/drivers/$drv/unbind"
  fi
  run "echo vfio-pci > /sys/bus/pci/devices/$m/driver_override"
  run "echo $m > /sys/bus/pci/drivers/vfio-pci/bind"
done
