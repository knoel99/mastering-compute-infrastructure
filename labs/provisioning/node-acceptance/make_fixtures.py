#!/usr/bin/env python3
"""Write the SYNTHETIC evidence directories used by the tests (no GPU was involved, no number here was measured).

Each directory mimics what acceptance.sh collects on a real node: smi.csv, dcgm.json + dcgm.rc, nccl.json, burn.log,
xid.log, versions.json. The numbers are round on purpose (baseline 100 GB/s, 98 GB/s observed, ...): they exist to
exercise the decision rules, not to describe any hardware.

Usage: make_fixtures.py OUTDIR   (deterministic: running it twice gives byte-identical files)
"""
import json
import os
import sys

N_GPUS = 8
SMI_FIELDS = ["index", "uuid", "driver_version", "persistence_mode", "ecc.errors.uncorrected.volatile.total",
              "remapped_rows.pending", "remapped_rows.failure", "retired_pages.pending",
              "pcie.link.gen.current", "pcie.link.width.current"]


def base():
    rows = [{"index": i, "uuid": f"GPU-00000000-0000-0000-0000-{i:012d}", "driver_version": "580.0.1",
             "persistence_mode": "Enabled", "ecc.errors.uncorrected.volatile.total": 0, "remapped_rows.pending": 0,
             "remapped_rows.failure": 0, "retired_pages.pending": "[N/A]", "pcie.link.gen.current": 5,
             "pcie.link.width.current": 16} for i in range(N_GPUS)]

    def dcgm_test(name, statuses=None):
        statuses = statuses or ["Pass"] * N_GPUS
        results = [{"entity_group": "GPU", "entity_group_id": 1, "entity_id": i, "info": [], "status": s}
                   for i, s in enumerate(statuses)]
        summary = "Pass" if all(s == "Pass" for s in statuses) else "Fail"
        return {"name": name, "results": results, "test_summary": {"status": summary}}

    dcgm = {"DCGM Diagnostic": {"test_categories": [
        {"category": "Deployment", "tests": [dcgm_test("software")]},
        {"category": "Integration", "tests": [dcgm_test("pcie")]},
        {"category": "Hardware", "tests": [dcgm_test("memory")]}]}}
    sizes = [1 << 20, 1 << 26, 1 << 30]
    nccl = {"version": 1, "nccl_version": 0, "results": [
        {"size": s, "count": s // 4, "type": "float", "redop": "sum", "root": "-1",
         "out_of_place": {"time": 1.0, "alg_bw": 50.0, "bus_bw": 90.0, "nwrong": 0},
         "in_place": {"time": 1.0, "alg_bw": 55.0, "bus_bw": 98.0, "nwrong": 0}} for s in sizes],
        "out_of_bounds": {"count": 0, "okay": True},
        "average_bus_bandwidth": {"bandwidth": 98.0, "okay": "unchecked"}}
    return {"smi": rows, "dcgm": dcgm, "dcgm_rc": 0, "nccl": nccl,
            "burn": [f"GPU {i}: OK" for i in range(N_GPUS)], "xid": [],
            "versions": {"driver": "580.0.1", "cuda_runtime": "13.0", "fabric_manager": "580.0.1",
                         "nvswitch_generation": 3, "fabric_manager_active": True, "nouveau_loaded": False}}


def write(ev, path):
    os.makedirs(path, exist_ok=True)
    if ev["smi"] is not None:
        lines = [", ".join(SMI_FIELDS)] + [", ".join(str(r[f]) for f in SMI_FIELDS) for r in ev["smi"]]
        open(os.path.join(path, "smi.csv"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    if ev["dcgm"] is not None:
        open(os.path.join(path, "dcgm.json"), "w", encoding="utf-8").write(json.dumps(ev["dcgm"], indent=1, sort_keys=True) + "\n")
        open(os.path.join(path, "dcgm.rc"), "w", encoding="utf-8").write(f"{ev['dcgm_rc']}\n")
    if ev["nccl"] is not None:
        open(os.path.join(path, "nccl.json"), "w", encoding="utf-8").write(json.dumps(ev["nccl"], indent=1, sort_keys=True) + "\n")
    if ev["burn"] is not None:
        body = ["Tested %d GPUs:" % len(ev["burn"])] + ["\t" + b for b in ev["burn"]]
        open(os.path.join(path, "burn.log"), "w", encoding="utf-8").write("done\n\n" + "\n".join(body) + "\n")
    open(os.path.join(path, "xid.log"), "w", encoding="utf-8").write("".join(x + "\n" for x in ev["xid"]))
    open(os.path.join(path, "versions.json"), "w", encoding="utf-8").write(json.dumps(ev["versions"], indent=1, sort_keys=True) + "\n")


def scenarios():
    s = {"good": base()}

    e = base(); e["smi"][3]["remapped_rows.failure"] = 1; s["remap_failure"] = e
    e = base(); e["smi"][5]["remapped_rows.pending"] = 1; s["pending_remap"] = e
    e = base(); e["smi"][2]["pcie.link.width.current"] = 8; s["pcie_degraded"] = e
    e = base(); e["smi"][6]["ecc.errors.uncorrected.volatile.total"] = 2; s["ecc_uncorrected"] = e
    e = base(); e["smi"] = e["smi"][:7]; s["missing_gpu"] = e

    # DCGM reports a failing test although the exit status is 0: a verdict must not rely on the status alone.
    e = base()
    mem = e["dcgm"]["DCGM Diagnostic"]["test_categories"][2]["tests"][0]
    mem["results"][4]["status"] = "Fail"; mem["test_summary"]["status"] = "Fail"
    s["dcgm_fail_rc0"] = e
    e = base(); e["dcgm_rc"] = 226; s["dcgm_error_226"] = e
    e = base(); e["dcgm_rc"] = 205; s["dcgm_isolate_205"] = e
    e = base(); e["dcgm"] = None; e["dcgm_rc"] = None; s["dcgm_missing"] = e

    e = base(); e["nccl"]["average_bus_bandwidth"]["bandwidth"] = 61.0; s["nccl_slow"] = e
    e = base(); e["nccl"]["average_bus_bandwidth"]["bandwidth"] = 93.0; s["nccl_marginal"] = e
    e = base(); e["nccl"]["results"][1]["in_place"]["nwrong"] = 3; s["nccl_wrong_values"] = e
    e = base(); e["nccl"] = None; s["nccl_missing"] = e

    e = base(); e["burn"][6] = "GPU 6: FAULTY"; s["burn_faulty"] = e
    e = base(); e["burn"] = None; s["burn_missing"] = e
    # Example line taken from the NVIDIA XID catalog page (Xid 79, GPU has fallen off the bus).
    e = base(); e["xid"] = ["[ 1234.5] NVRM: Xid (PCI:0000:5a:00): 79, GPU has fallen off the bus."]; s["xid79"] = e

    e = base(); e["versions"]["fabric_manager"] = "575.0.1"; s["fm_mismatch"] = e
    e = base(); e["versions"]["fabric_manager_active"] = False; s["fm_inactive"] = e
    e = base(); e["versions"]["driver"] = "570.0.1"; s["cuda13_old_driver"] = e
    e = base(); e["versions"]["nouveau_loaded"] = True; s["nouveau_loaded"] = e
    # Several findings at once: one rejection (degraded PCIe link) hides two retests (pending remap, marginal bandwidth).
    e = base(); e["smi"][2]["pcie.link.width.current"] = 8; e["smi"][5]["remapped_rows.pending"] = 1
    e["nccl"]["average_bus_bandwidth"]["bandwidth"] = 93.0; s["multi"] = e
    return s


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    for name, ev in sorted(scenarios().items()):
        write(ev, os.path.join(sys.argv[1], name))
    print(f"wrote {len(scenarios())} scenarios to {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
