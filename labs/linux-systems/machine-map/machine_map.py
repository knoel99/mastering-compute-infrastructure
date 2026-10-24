#!/usr/bin/env python3
"""Machine map: CPU, NUMA, memory, PCI devices, network interfaces, disks, and who is close to whom.

Reads /proc and /sys under --sysroot (default /) so the same code runs on a live machine and on
recorded fixtures. lscpu and lsblk are used only when available on a live machine (JSON output).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

PCI_KINDS = [  # (class prefix as in /sys/bus/pci/devices/*/class, kind)
    ("0x0302", "gpu"), ("0x0300", "gpu"), ("0x0207", "infiniband"), ("0x0200", "ethernet"), ("0x0108", "nvme"),
]


def parse_cpulist(text):
    """'0-3,8-11' -> [0, 1, 2, 3, 8, 9, 10, 11]"""
    out = []
    for part in text.strip().split(","):
        if not part:
            continue
        lo, _, hi = part.partition("-")
        out += range(int(lo), int(hi or lo) + 1)
    return out


def parse_meminfo(text):
    """{'MemTotal': kB, ...} for lines of the form 'Key:  value [kB]' (a node file has 'Node N ' in front)."""
    out = {}
    for line in text.splitlines():
        m = re.match(r"(?:Node\s+\d+\s+)?(\w+):\s+(\d+)", line)
        if m:
            out[m.group(1)] = int(m.group(2))
    return out


def _read(path, default=""):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return default


def read_numa(root):
    base = os.path.join(root, "sys/devices/system/node")
    nodes = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            m = re.fullmatch(r"node(\d+)", name)
            if not m:
                continue
            d = os.path.join(base, name)
            mem = parse_meminfo(_read(os.path.join(d, "meminfo")))
            nodes.append({"id": int(m.group(1)), "cpus": parse_cpulist(_read(os.path.join(d, "cpulist"))),
                          "mem_total_kb": mem.get("MemTotal")})
    return sorted(nodes, key=lambda n: n["id"])


def read_pci(root):
    base = os.path.join(root, "sys/bus/pci/devices")
    devs = []
    if os.path.isdir(base):
        for addr in sorted(os.listdir(base)):
            d = os.path.join(base, addr)
            cls = _read(os.path.join(d, "class"))
            kind = next((k for prefix, k in PCI_KINDS if cls.startswith(prefix)), None)
            if kind:
                devs.append({"addr": addr, "kind": kind, "vendor": _read(os.path.join(d, "vendor")),
                             "device": _read(os.path.join(d, "device")),
                             "numa_node": int(_read(os.path.join(d, "numa_node"), "-1"))})
    return devs


def read_nics(root):
    base = os.path.join(root, "sys/class/net")
    nics = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            if name == "lo":
                continue
            d = os.path.join(base, name)
            nics.append({"name": name, "mtu": int(_read(os.path.join(d, "mtu"), "0")),
                         "state": _read(os.path.join(d, "operstate"), "unknown")})
    return nics


def cpu_summary(lscpu_json):
    """Flatten `lscpu --json` ({'lscpu': [{'field': 'CPU(s):', 'data': '4'}, ...]})."""
    f = {x["field"].rstrip(":"): x["data"] for x in lscpu_json["lscpu"]}
    return {"model": f.get("Model name"), "logical": int(f["CPU(s)"]), "sockets": int(f["Socket(s)"]),
            "cores_per_socket": int(f["Core(s) per socket"]), "threads_per_core": int(f["Thread(s) per core"])}


def _flag(v):
    """lsblk --json prints rota as a boolean, and older util-linux versions print the strings "0"/"1" (bool("0") is True)."""
    return str(v).lower() in ("1", "true")


def disk_summary(lsblk_json):
    return [{"name": d["name"], "size_bytes": int(d["size"]), "rotational_flag": _flag(d["rota"])}
            for d in lsblk_json["blockdevices"] if d["type"] == "disk" and int(d["size"]) > 0]


def locality(numa, pci):
    """Per NUMA node: which accelerators, NICs and NVMe devices hang off it. Node -1 = no affinity reported."""
    out = {n["id"]: {"gpu": [], "infiniband": [], "ethernet": [], "nvme": []} for n in numa}
    out.setdefault(-1, {"gpu": [], "infiniband": [], "ethernet": [], "nvme": []})
    for d in pci:
        out.setdefault(d["numa_node"], {"gpu": [], "infiniband": [], "ethernet": [], "nvme": []})[d["kind"]].append(d["addr"])
    return {str(k): v for k, v in sorted(out.items()) if any(v.values()) or k != -1}


def _run_json(cmd):
    if not shutil.which(cmd[0]):
        return None
    r = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout else None


def build_report(root="/", lscpu_json=None, lsblk_json=None):
    numa, pci = read_numa(root), read_pci(root)
    live = root == "/"
    lscpu_json = lscpu_json or (_run_json(["lscpu", "--json"]) if live else None)
    lsblk_json = lsblk_json or (_run_json(["lsblk", "--json", "-b", "-o", "NAME,TYPE,SIZE,ROTA,MOUNTPOINT"]) if live else None)
    return {
        "cpu": cpu_summary(lscpu_json) if lscpu_json else None,
        "memory_total_kb": parse_meminfo(_read(os.path.join(root, "proc/meminfo"))).get("MemTotal"),
        "numa": numa, "pci": pci, "nics": read_nics(root),
        "disks": disk_summary(lsblk_json) if lsblk_json else None,
        "locality": locality(numa, pci),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sysroot", default="/")
    ap.add_argument("--lscpu-json")
    ap.add_argument("--lsblk-json")
    a = ap.parse_args()
    load = lambda p: json.load(open(p)) if p else None
    json.dump(build_report(a.sysroot, load(a.lscpu_json), load(a.lsblk_json)), sys.stdout, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
