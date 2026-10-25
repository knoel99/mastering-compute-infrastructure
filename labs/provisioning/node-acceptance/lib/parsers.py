"""Parsers for the evidence files of a node acceptance run.

Formats (all read on 2026-10-24, see README.md for the sources):
  * dcgmi diag -j      : JSON with "tests" lists holding "name", "results"[{"entity_id", "status"}] and "test_summary".
                         Only a fragment is shown in the DCGM documentation, so the parser walks any nesting.
  * nccl-tests -J file : JSON with "results"[{"size", "in_place": {"bus_bw", "nwrong"}}], "out_of_bounds", "average_bus_bandwidth"
                         (key names read in src/util.cu of nccl-tests, master branch).
  * gpu_burn stdout    : "Tested N GPUs:" then "\tGPU i: OK|FAULTY" (read in gpu_burn-drv.cpp).
  * dmesg              : "NVRM: Xid (PCI:0000:5a:00): 79, GPU has fallen off the bus." (example line of the NVIDIA XID catalog).
  * nvidia-smi --query-gpu=... --format=csv : header = field names; the field list is UNVERIFIED on a real GPU.
"""
import csv
import io
import json
import re

XID_RE = re.compile(r"NVRM: Xid \((?:PCI:)?(?P<bdf>[0-9a-fA-F:.]+)\):\s*(?P<code>\d+),")
BURN_RE = re.compile(r"^\s*GPU\s+(?P<idx>\d+):\s+(?P<state>OK|FAULTY)\s*$", re.M)


def _num(value):
    """'8', '8.0' -> int/float; '[N/A]', '', 'Enabled' -> None or the raw string."""
    v = value.strip()
    if v in ("", "[N/A]", "N/A", "[Not Supported]"):
        return None
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


def parse_smi_csv(text):
    """Return one dict per GPU row; header cells lose their ' [unit]' suffix."""
    rows = list(csv.reader(io.StringIO(text.strip()), skipinitialspace=True))
    if len(rows) < 2:
        return []
    header = [re.sub(r"\s*\[.*\]$", "", h).strip() for h in rows[0]]
    return [{h: _num(v) for h, v in zip(header, r)} for r in rows[1:] if r]


def _walk_tests(node, found):
    if isinstance(node, dict):
        if isinstance(node.get("tests"), list):
            for t in node["tests"]:
                if isinstance(t, dict) and "name" in t:
                    found.append(t)
        for v in node.values():
            _walk_tests(v, found)
    elif isinstance(node, list):
        for v in node:
            _walk_tests(v, found)


def parse_dcgm_json(text):
    """Return [{'name', 'status', 'failing_entities'}] in document order. Raises ValueError on bad JSON."""
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"dcgm.json is not valid JSON: {exc}") from exc
    tests = []
    _walk_tests(doc, tests)
    out = []
    for t in tests:
        results = t.get("results", [])
        summary = (t.get("test_summary") or {}).get("status")
        statuses = [r.get("status") for r in results if isinstance(r, dict)]
        status = summary or (statuses[0] if statuses else "Unknown")
        bad = [r.get("entity_id") for r in results if isinstance(r, dict) and r.get("status") not in ("Pass", "Skip")]
        out.append({"name": t["name"], "status": status, "failing_entities": bad})
    return out


def parse_nccl_json(text):
    """Return {'avg_busbw': float|None, 'out_of_bounds': int, 'nwrong': int, 'rows': n}."""
    doc = json.loads(text)
    rows = doc.get("results", [])
    nwrong = 0
    for r in rows:
        for side in ("out_of_place", "in_place"):
            v = (r.get(side) or {}).get("nwrong")
            if isinstance(v, (int, float)):
                nwrong += int(v)
    avg = (doc.get("average_bus_bandwidth") or {}).get("bandwidth")
    if avg is None and rows:
        last = rows[-1].get("in_place") or rows[-1].get("out_of_place") or {}
        avg = last.get("bus_bw")
    oob = (doc.get("out_of_bounds") or {}).get("count", 0)
    return {"avg_busbw": avg, "out_of_bounds": int(oob), "nwrong": nwrong, "rows": len(rows)}


def parse_burn_log(text):
    """Return {gpu_index: 'OK'|'FAULTY'} from the final summary of gpu_burn."""
    return {int(m["idx"]): m["state"] for m in BURN_RE.finditer(text)}


def parse_xid_log(text):
    """Return [(pci_bus_id, xid_code)] for every NVRM Xid line."""
    return [(m["bdf"], int(m["code"])) for m in XID_RE.finditer(text)]
