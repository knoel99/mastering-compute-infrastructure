"""REFERENCE decision rules for a node acceptance run.

Every threshold comes from the policy (policy.json): they are site choices, not vendor facts.
What IS documented (see README): the CUDA minor-version-compatibility table, Fabric Manager's version check on
pre-NVLink5 systems, the row-remapping failure/pending flags, the DCGM exit codes 226 and 205, and the nccl-tests
rule "average bus bandwidth below 0.9 x NCCL_TESTS_MIN_BW is FAILED".
"""

# Minimal driver major version per CUDA toolkit major (CUDA Compatibility guide, "Minor Version Compatibility" table).
CUDA_MIN_DRIVER = {11: 450, 12: 525, 13: 580}

DCGM_NVVS_ERROR = 226     # "DCGM GPU Diagnostic was successfully executed, but reported an error."
DCGM_NVVS_ISOLATE = 205   # "The diagnostic returned an error that indicates the need for isolation"


def _driver_major(version):
    return int(str(version).split(".")[0])


def check_stack(versions, policy):
    out = []
    driver = versions.get("driver")
    cuda = versions.get("cuda_runtime")
    if driver and cuda:
        try:
            cuda_major = int(str(cuda).split(".")[0])
        except ValueError:  # acceptance.sh writes "unknown" when CUDA_RUNTIME_VERSION is not set
            cuda_major = None
        need = CUDA_MIN_DRIVER.get(cuda_major)
        if need is None:
            out.append(("retest", f"unknown CUDA major {cuda}: no entry in the compatibility table"))
        elif _driver_major(driver) < need:
            out.append(("reject", f"driver {driver} is older than the {need} required by CUDA {cuda}"))
    gen = versions.get("nvswitch_generation")
    if gen:
        if not versions.get("fabric_manager_active"):
            out.append(("reject", "NVSwitch system but nvidia-fabricmanager is not active"))
        elif gen < 4 and versions.get("fabric_manager") != driver:
            out.append(("reject", f"Fabric Manager {versions.get('fabric_manager')} != driver {driver} (must match before NVLink5)"))
    if versions.get("nouveau_loaded"):
        out.append(("reject", "nouveau driver is loaded"))
    return out


def check_smi(rows, policy):
    out = []
    if len(rows) != policy["expected_gpus"]:
        out.append(("reject", f"{len(rows)} GPUs visible, {policy['expected_gpus']} expected"))
    for r in rows:
        i = r.get("index")
        if (r.get("remapped_rows.failure") or 0) > 0:
            out.append(("reject", f"GPU {i}: row-remapping failure flag set (RMA candidate)"))
        if (r.get("remapped_rows.pending") or 0) > 0 or (r.get("retired_pages.pending") or 0) > 0:
            out.append(("retest", f"GPU {i}: remap/retirement pending, takes effect at the next GPU reset: reset then retest"))
        if (r.get("ecc.errors.uncorrected.volatile.total") or 0) > 0:
            out.append(("reject", f"GPU {i}: uncorrected ECC errors on a node that has not run a job yet"))
        gen, width = r.get("pcie.link.gen.current"), r.get("pcie.link.width.current")
        if gen is not None and gen < policy["expected_pcie_gen"] or width is not None and width < policy["expected_pcie_width"]:
            out.append(("reject", f"GPU {i}: PCIe link gen{gen} x{width} below gen{policy['expected_pcie_gen']} x{policy['expected_pcie_width']}"))
    return out


def check_dcgm(tests, rc, policy):
    out = []
    if rc == DCGM_NVVS_ISOLATE:
        out.append(("reject", f"dcgmi diag exit {rc}: the diagnostic asks to isolate the node"))
    elif rc == DCGM_NVVS_ERROR:
        out.append(("reject", f"dcgmi diag exit {rc}: diagnostic ran and reported an error"))
    elif rc not in (0, None):
        out.append(("retest", f"dcgmi diag exit {rc}: tool problem, not a verdict"))
    if tests is None:
        if rc is None:
            out.append(("retest", "dcgmi diag was not run"))
        return out
    seen = {t["name"] for t in tests}
    for name in policy["required_dcgm_tests"]:
        if name not in seen:
            out.append(("retest", f"required DCGM test '{name}' absent from the report"))
    for t in tests:
        if t["status"] not in ("Pass", "Skip"):
            out.append(("reject", f"DCGM test '{t['name']}' status {t['status']} (entities {t['failing_entities']})"))
    return out


def check_nccl(summary, policy):
    if summary is None:
        return [("retest", "nccl-tests did not run")]
    out = []
    if summary["out_of_bounds"] > 0 or summary["nwrong"] > 0:
        out.append(("reject", f"nccl-tests reports wrong values ({summary['out_of_bounds']} out of bounds, {summary['nwrong']} wrong)"))
    avg = summary["avg_busbw"]
    if avg is None:
        out.append(("retest", "no bus bandwidth in the nccl-tests report"))
        return out
    ratio = avg / policy["min_busbw_gbps"]
    if ratio < policy["nccl_reject_ratio"]:
        out.append(("reject", f"bus bandwidth {avg:.1f} GB/s is {ratio:.0%} of the baseline {policy['min_busbw_gbps']:.1f}"))
    elif ratio < policy["nccl_retest_ratio"]:
        out.append(("retest", f"bus bandwidth {avg:.1f} GB/s is {ratio:.0%} of the baseline: marginal, run again"))
    return out


def check_burn(result, expect_gpus, required):
    if result is None:
        return [("retest", "gpu_burn did not run")] if required else []
    out = [("reject", f"gpu_burn: GPU {i} FAULTY") for i, s in sorted(result.items()) if s != "OK"]
    if len(result) != expect_gpus:
        out.append(("reject", f"gpu_burn tested {len(result)} GPUs, {expect_gpus} expected"))
    return out


def check_xid(events):
    return [("reject", f"Xid {code} on {bdf} during the run") for bdf, code in events]


def decide(findings):
    sev = {s for s, _ in findings}
    if "reject" in sev:
        return "reject"
    if "retest" in sev:
        return "retest"
    return "accept"
