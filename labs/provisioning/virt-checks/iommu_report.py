#!/usr/bin/env python3
"""Report what a Linux machine offers for PCI passthrough (VFIO), read from sysfs only (standard library, read-only).

  iommu_report.py                 # the machine you run it on
  iommu_report.py --root DIR      # a copy or a synthetic tree laid out like / (sys/, proc/, dev/)

For every IOMMU group it lists the PCI devices (address, vendor:device, class, bound driver) and says whether the group
is ready for VFIO. The rule comes from the kernel VFIO documentation: the group is the unit of ownership, and every
device of the group must be bound to a VFIO driver, or at least unbound from its host driver, before the group can be
used. Bridges are listed but not counted as endpoints (vfio-pci does not support PCI bridges).
Exit status: 0 when at least one group is ready, 1 when none is, 2 when the machine has no IOMMU group at all.
"""
import argparse
import os
import sys
from pathlib import Path

# PCI class codes (base class, sub-class) as listed in the pci.ids database (pci-ids.ucw.cz, read 2026-10-25).
CLASS_NAMES = {"0600": "host bridge", "0604": "PCI bridge", "0200": "Ethernet controller", "0207": "InfiniBand controller",
               "0300": "VGA controller", "0302": "3D controller", "0100": "SCSI storage", "0180": "mass storage",
               "0108": "NVMe controller"}
# Virtio 1.2 specification, section 4.1.2: vendor 0x1AF4, device ID = 0x1040 + virtio device ID (section 5).
VIRTIO_TYPES = {1: "network card", 2: "block device", 4: "entropy source", 5: "memory balloon", 19: "socket (vsock)"}
VFIO_DRIVERS = {"vfio-pci"}


def read(path, default=""):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return default


def describe(dev: Path):
    vendor, device = read(dev / "vendor")[2:], read(dev / "device")[2:]
    cls = read(dev / "class")[2:6]
    name = CLASS_NAMES.get(cls, f"class {cls}")
    if vendor == "1af4" and 0x1040 <= int(device or "0", 16) <= 0x107F:
        name = "virtio " + VIRTIO_TYPES.get(int(device, 16) - 0x1040, "device")
    drv = os.path.basename(os.readlink(dev / "driver")) if (dev / "driver").is_symlink() else "-"
    return {"bdf": dev.name, "id": f"{vendor}:{device}", "class": cls, "name": name, "driver": drv,
            "bridge": cls.startswith("06")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="/", help="directory laid out like / (default: this machine)")
    a = ap.parse_args()
    root = Path(a.root)
    cmdline = read(root / "proc/cmdline").split()
    iommu_args = [w for w in cmdline if w.split("=")[0] in ("intel_iommu", "amd_iommu", "iommu", "iommu.passthrough")]
    flags = set()
    for line in read(root / "proc/cpuinfo").splitlines():
        if line.startswith("flags"):
            flags.update(line.split(":", 1)[1].split())
    print(f"kernel IOMMU args  : {' '.join(iommu_args) or '(none)'}")
    print(f"CPU virt. flags    : {' '.join(sorted(flags & {'vmx', 'svm'})) or '(none: no vmx/svm flag)'}")
    print(f"/dev/kvm           : {'present' if (root / 'dev/kvm').exists() else 'absent'}")
    print(f"vfio-pci driver    : {'registered' if (root / 'sys/bus/pci/drivers/vfio-pci').is_dir() else 'not registered'}")
    pci = sorted((root / "sys/bus/pci/devices").glob("*"))
    print(f"PCI devices        : {len(pci)}")
    groups_dir = root / "sys/kernel/iommu_groups"
    groups = sorted(groups_dir.glob("*"), key=lambda p: int(p.name)) if groups_dir.is_dir() else []
    print(f"IOMMU groups       : {len(groups)}")
    if not groups:
        for dev in pci:
            d = describe(dev)
            print(f"  {d['bdf']}  {d['id']}  {d['name']:<24} driver={d['driver']}  iommu_group=none")
        print("verdict            : no IOMMU group, so no device of this machine can be handed to a VM with VFIO")
        return 2
    ready = 0
    for g in groups:
        devs = [describe(p) for p in sorted((g / "devices").glob("*"))]
        ends = [d for d in devs if not d["bridge"]]
        blocking = [d for d in ends if d["driver"] not in VFIO_DRIVERS | {"-"}]
        state = "ready for VFIO" if ends and not blocking else (
            "bridges only" if not ends else "blocked by host driver(s): " + ", ".join(f"{d['bdf']}={d['driver']}" for d in blocking))
        ready += state == "ready for VFIO"
        print(f"group {g.name}: {len(ends)} endpoint(s), {state}")
        for d in devs:
            print(f"  {d['bdf']}  {d['id']}  {d['name']:<24} driver={d['driver']}")
        if len(ends) > 1:
            print(f"  -> these {len(ends)} endpoints can only be given together, to one VM")
    print(f"verdict            : {ready} of {len(groups)} group(s) ready for VFIO")
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
