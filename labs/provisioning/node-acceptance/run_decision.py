#!/usr/bin/env python3
"""Read an evidence directory, apply the decision rules, print a JSON verdict.

Usage: run_decision.py EVIDENCE_DIR [--impl reference|starter] [--policy policy.json] [--level quick|full]
Exit status: 0 accept, 1 reject, 3 retest (2 is reserved for usage errors, as in acceptance.sh).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
import parsers  # noqa: E402


def load_impl(name):
    sys.path.insert(0, os.path.join(HERE, name))
    import decide  # noqa: WPS433
    return decide


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return None


def evaluate(evidence_dir, impl, policy, level):
    d = impl
    versions = json.loads(read(os.path.join(evidence_dir, "versions.json")) or "{}")
    smi = read(os.path.join(evidence_dir, "smi.csv"))
    dcgm = read(os.path.join(evidence_dir, "dcgm.json"))
    rc_txt = read(os.path.join(evidence_dir, "dcgm.rc"))
    nccl = read(os.path.join(evidence_dir, "nccl.json"))
    burn = read(os.path.join(evidence_dir, "burn.log"))
    xid = read(os.path.join(evidence_dir, "xid.log")) or ""
    findings = []
    findings += d.check_stack(versions, policy)
    findings += d.check_smi(parsers.parse_smi_csv(smi) if smi else [], policy)
    findings += d.check_dcgm(parsers.parse_dcgm_json(dcgm) if dcgm else None, int(rc_txt) if rc_txt else None, policy)
    if nccl or level == "full":  # the quick level does not run nccl-tests, so its absence is not a finding there
        findings += d.check_nccl(parsers.parse_nccl_json(nccl) if nccl else None, policy)
    findings += d.check_burn(parsers.parse_burn_log(burn) if burn else None, policy["expected_gpus"], level == "full")
    findings += d.check_xid(parsers.parse_xid_log(xid))
    return {"verdict": d.decide(findings), "findings": [{"severity": s, "message": m} for s, m in findings]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("evidence")
    ap.add_argument("--impl", default=os.environ.get("IMPL", "reference"), choices=["reference", "starter"])
    ap.add_argument("--policy", default=os.path.join(HERE, "policy.json"))
    ap.add_argument("--level", default="full", choices=["quick", "full"])
    a = ap.parse_args()
    with open(a.policy, encoding="utf-8") as fh:
        policy = json.load(fh)
    result = evaluate(a.evidence, load_impl(a.impl), policy, a.level)
    print(json.dumps(result, indent=2, sort_keys=True))
    return {"accept": 0, "reject": 1, "retest": 3}[result["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
