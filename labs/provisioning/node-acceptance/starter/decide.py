"""STARTER: implement the seven functions below. Each returns a list of findings (see reference for the exact shape).

A finding is a tuple (severity, message) with severity "reject" or "retest".
Today every function returns [] so the node is always accepted: the tests in tests/ fail until you fill them in.
"""

CUDA_MIN_DRIVER = {}  # TODO: CUDA major -> minimal driver major (minor-version compatibility table of the CUDA Compatibility guide)


def check_stack(versions, policy):
    """Driver/CUDA compatibility, Fabric Manager (active, same version as the driver before NVLink5), nouveau absent."""
    return []


def check_smi(rows, policy):
    """GPU count, row-remapping failure (reject), pending remap/retired pages (retest after reset), uncorrected ECC, PCIe link."""
    return []


def check_dcgm(tests, rc, policy):
    """tests: parsed dcgmi diag -j or None when absent; rc: exit status or None. Do not trust rc alone."""
    return []


def check_nccl(summary, policy):
    """summary: parsed nccl-tests JSON or None. Wrong values reject; compare avg bus bandwidth to the site baseline."""
    return []


def check_burn(result, expect_gpus, required):
    """result: {gpu_index: 'OK'|'FAULTY'} or None when gpu_burn was not run; required: a full run must include it."""
    return []


def check_xid(events):
    """events: [(pci_bus_id, code)] seen in dmesg during the run."""
    return []


def decide(findings):
    """Return 'reject' if any finding rejects, else 'retest' if any retests, else 'accept'."""
    return "accept"
