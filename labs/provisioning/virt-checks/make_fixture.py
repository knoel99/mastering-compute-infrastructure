#!/usr/bin/env python3
"""Write a SYNTHETIC sysfs tree of a fictitious 4-GPU server, for iommu_report.py --root and bind_vfio.sh (SYSFS=...).

Nothing here was read from a real machine. The PCI IDs are real entries of the pci.ids database (10de:2330 H100 SXM5 80GB,
15b3:1021 ConnectX-7, 1000:c010 PEX880xx PCIe switch), the layout is invented for exercise 13 of the provisioning module:
two GPUs share an IOMMU group with a NIC and a switch port, two GPUs are alone in their group.

  make_fixture.py DIR
"""
import os
import sys
from pathlib import Path

# (group, address, vendor, device, class, driver or None)
DEVICES = [
    (30, "0000:17:00.0", "1000", "c010", "060400", None),
    (30, "0000:18:00.0", "10de", "2330", "030200", "nvidia"),
    (30, "0000:19:00.0", "15b3", "1021", "020700", "mlx5_core"),
    (31, "0000:2a:00.0", "1000", "c010", "060400", None),
    (31, "0000:2b:00.0", "10de", "2330", "030200", "nvidia"),
    (31, "0000:2c:00.0", "15b3", "1021", "020700", "mlx5_core"),
    (45, "0000:3d:00.0", "10de", "2330", "030200", "vfio-pci"),
    (46, "0000:4e:00.0", "10de", "2330", "030200", "nvidia"),
]


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    sysfs = root / "sys"
    (root / "proc").mkdir(parents=True, exist_ok=True)
    (root / "dev").mkdir(exist_ok=True)
    (root / "proc/cmdline").write_text("BOOT_IMAGE=/vmlinuz root=/dev/sda1 ro intel_iommu=on iommu=pt\n")
    (root / "proc/cpuinfo").write_text("processor\t: 0\nflags\t\t: fpu vme de pse msr pae vmx ept\n")
    (root / "dev/kvm").write_text("")  # a placeholder file: the report only tests that the path exists
    for drv in {"nvidia", "mlx5_core", "vfio-pci"}:
        (sysfs / "bus/pci/drivers" / drv).mkdir(parents=True, exist_ok=True)
    for group, bdf, vendor, device, cls, drv in DEVICES:
        dev = sysfs / "bus/pci/devices" / bdf
        dev.mkdir(parents=True, exist_ok=True)
        (dev / "vendor").write_text(f"0x{vendor}\n")
        (dev / "device").write_text(f"0x{device}\n")
        (dev / "class").write_text(f"0x{cls}\n")
        gdir = sysfs / "kernel/iommu_groups" / str(group) / "devices"
        gdir.mkdir(parents=True, exist_ok=True)
        os.symlink(f"../../../../kernel/iommu_groups/{group}", dev / "iommu_group")
        os.symlink(f"../../../../bus/pci/devices/{bdf}", gdir / bdf)
        if drv:
            os.symlink(f"../../drivers/{drv}", dev / "driver")
    print(f"synthetic tree written under {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
