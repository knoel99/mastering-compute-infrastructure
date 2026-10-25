import os
import subprocess
import sys

import pytest

import parsers

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CASES = [
    ("good", "accept", None),
    ("remap_failure", "reject", "row-remapping failure"),
    ("pending_remap", "retest", "reset then retest"),
    ("pcie_degraded", "reject", "PCIe link"),
    ("ecc_uncorrected", "reject", "ECC"),
    ("missing_gpu", "reject", "7 GPUs visible"),
    ("dcgm_fail_rc0", "reject", "DCGM test 'memory'"),
    ("dcgm_error_226", "reject", "226"),
    ("dcgm_isolate_205", "reject", "isolate"),
    ("dcgm_missing", "retest", "not run"),
    ("nccl_slow", "reject", "61%"),
    ("nccl_marginal", "retest", "marginal"),
    ("nccl_wrong_values", "reject", "wrong values"),
    ("nccl_missing", "retest", "nccl-tests did not run"),
    ("burn_faulty", "reject", "GPU 6 FAULTY"),
    ("burn_missing", "retest", "gpu_burn did not run"),
    ("xid79", "reject", "Xid 79"),
    ("fm_mismatch", "reject", "Fabric Manager"),
    ("fm_inactive", "reject", "not active"),
    ("cuda13_old_driver", "reject", "older than"),
    ("nouveau_loaded", "reject", "nouveau"),
    ("multi", "reject", "PCIe link"),
]


@pytest.mark.parametrize("scenario,expected,needle", CASES, ids=[c[0] for c in CASES])
def test_verdict(verdict, scenario, expected, needle):
    result = verdict(scenario)
    assert result["verdict"] == expected, result
    if needle:
        assert any(needle in f["message"] for f in result["findings"]), result["findings"]
    else:
        assert result["findings"] == []


def test_quick_level_does_not_require_gpu_burn_or_nccl(verdict):
    assert verdict("burn_missing", level="quick")["verdict"] == "accept"
    assert verdict("nccl_missing", level="quick")["verdict"] == "accept"


def test_unknown_cuda_version_is_a_retest_not_a_crash(impl, policy):
    findings = impl.check_stack({"driver": "580.0.1", "cuda_runtime": "unknown"}, policy)
    assert findings and all(severity == "retest" for severity, _ in findings), findings


def test_parse_xid_documented_example_line():
    line = "[...] NVRM: Xid (PCI:0000:5a:00): 79, GPU has fallen off the bus."
    assert parsers.parse_xid_log(line) == [("0000:5a:00", 79)]


def test_parse_smi_strips_units_and_na():
    rows = parsers.parse_smi_csv("index, memory.total [MiB], remapped_rows.pending\n0, 81920 MiB, [N/A]\n")
    assert rows == [{"index": 0, "memory.total": "81920 MiB", "remapped_rows.pending": None}]


def test_parse_burn_summary():
    assert parsers.parse_burn_log("Tested 2 GPUs:\n\tGPU 0: OK\n\tGPU 1: FAULTY\n") == {0: "OK", 1: "FAULTY"}


@pytest.mark.parametrize("scenario,rc", [("good", 0), ("remap_failure", 1), ("nccl_marginal", 3)])
def test_cli_exit_status_maps_the_verdict(scenario, rc):
    env = dict(os.environ)
    p = subprocess.run([sys.executable, os.path.join(HERE, "run_decision.py"), os.path.join(HERE, "fixtures", scenario)],
                       capture_output=True, text=True, env=env, check=False)
    assert p.returncode == rc, p.stdout + p.stderr
