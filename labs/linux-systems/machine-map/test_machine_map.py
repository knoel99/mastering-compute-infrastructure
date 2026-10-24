import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import machine_map as mm

HERE = Path(__file__).parent
SYS2 = str(HERE / "fixtures/sysroot-2socket")


def test_parse_cpulist():
    assert mm.parse_cpulist("0-3,8-11") == [0, 1, 2, 3, 8, 9, 10, 11]
    assert mm.parse_cpulist("5\n") == [5]
    assert mm.parse_cpulist("") == []


def test_parse_meminfo_global_and_node_forms():
    assert mm.parse_meminfo("MemTotal:   16477348 kB\nHugePages_Total:  0\n") == {"MemTotal": 16477348, "HugePages_Total": 0}
    assert mm.parse_meminfo("Node 1 MemTotal:  1056993280 kB\n") == {"MemTotal": 1056993280}


def test_two_socket_fixture_numa_and_cpus():
    nodes = mm.read_numa(SYS2)
    assert [n["id"] for n in nodes] == [0, 1]
    assert len(nodes[0]["cpus"]) == 64 and nodes[0]["cpus"][0] == 0 and 64 in nodes[0]["cpus"]
    assert nodes[1]["mem_total_kb"] == 1056993280
    assert not set(nodes[0]["cpus"]) & set(nodes[1]["cpus"])


def test_two_socket_fixture_locality_tells_which_nic_is_close_to_which_gpu():
    rep = mm.build_report(SYS2)
    loc = rep["locality"]
    assert len(loc["0"]["gpu"]) == 2 and len(loc["1"]["gpu"]) == 2
    assert loc["0"]["infiniband"] == ["0000:5e:00.0"] and loc["1"]["infiniband"] == ["0000:c1:00.0"]
    assert loc["-1"]["ethernet"] == ["0000:00:1f.6"]  # no affinity reported: the report must not hide it


def test_nics_skip_loopback():
    names = [n["name"] for n in mm.read_nics(SYS2)]
    assert names == ["eth0", "ib0"]


def test_recorded_lscpu_and_lsblk_summaries():
    lscpu = json.load(open(HERE / "fixtures/lscpu-sandbox.json"))
    cpu = mm.cpu_summary(lscpu)
    assert cpu["logical"] == cpu["sockets"] * cpu["cores_per_socket"] * cpu["threads_per_core"]
    disks = mm.disk_summary(json.load(open(HERE / "fixtures/lsblk-sandbox.json")))
    assert disks and all(d["size_bytes"] > 0 for d in disks)


def test_rotational_flag_accepts_booleans_and_old_style_strings():
    def blk(rota):
        return {"blockdevices": [{"name": "d", "type": "disk", "size": 1, "rota": rota}]}
    flags = [mm.disk_summary(blk(r))[0]["rotational_flag"] for r in (True, False, "1", "0", 1, 0)]
    assert flags == [True, False, True, False, True, False]


def test_live_machine_is_consistent_with_the_kernel():
    rep = mm.build_report("/")
    assert rep["memory_total_kb"] > 0
    assert rep["cpu"] is None or rep["cpu"]["logical"] == os.cpu_count()
    if rep["numa"]:
        assert sum(len(n["cpus"]) for n in rep["numa"]) == os.cpu_count()


def test_cli_prints_valid_json_with_the_expected_keys():
    r = subprocess.run([sys.executable, str(HERE / "machine_map.py"), "--sysroot", SYS2,
                        "--lscpu-json", str(HERE / "fixtures/lscpu-sandbox.json")],
                       capture_output=True, text=True, check=True)
    rep = json.loads(r.stdout)
    assert set(rep) == {"cpu", "memory_total_kb", "numa", "pci", "nics", "disks", "locality"}
    assert rep["memory_total_kb"] == 2113986560
