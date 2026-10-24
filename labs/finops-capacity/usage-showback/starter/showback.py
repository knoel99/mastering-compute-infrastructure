#!/usr/bin/env python3
"""Showback from a scheduler export: who used how many GPU-hours, how much was lost, how long users waited.

Input: the output of `sacct -X -P` (pipe-separated, header line first, lines starting with '#' ignored) with at least the
columns Account, State, Submit, Start, End, ElapsedRaw, AllocTRES. The unit is a TRES name: `gres/gpu` on a GPU cluster,
`cpu` on the CPU-only sandbox of the Slurm module (used here as a stand-in for GPUs).

Definitions
  allocated hours  = TRES count * elapsed seconds / 3600, clipped to the reporting window
  utilization      = allocated hours / (capacity * window hours)           (allocation, not useful work)
  lost candidates  = allocated hours of jobs ending in FAILED, TIMEOUT, NODE_FAIL, OUT_OF_MEMORY or PREEMPTED:
                     an UPPER BOUND of the avoidable loss (a job with checkpoints loses far less than its whole run)
  full cost        = capacity * window hours * rate; every unit of it is allocated to a team or to the platform
"""
import argparse
import json
import sys
from datetime import datetime

LOSS_STATES = ("FAILED", "TIMEOUT", "NODE_FAIL", "OUT_OF_MEMORY", "PREEMPTED")
UNKNOWN = ("", "Unknown", "None", "N/A")


def parse_tres(text):
    """'billing=8,cpu=8,gres/gpu=8,mem=64G,node=1' -> {'billing': 8.0, 'cpu': 8.0, 'gres/gpu': 8.0, 'node': 1.0}.
    Entries whose value is not a plain number (mem=64G) are skipped."""
    raise NotImplementedError("TODO: implement parse_tres (see the docstring and tests/)")


def _time(text):
    return None if text in UNKNOWN else datetime.fromisoformat(text)


def parse_rows(lines):
    """List of dicts, one per job, with parsed Start/End/Submit (datetime or None), elapsed seconds and TRES dict."""
    rows, header = [], None
    for line in lines:
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        cells = line.split("|")
        if header is None:
            header = cells
            continue
        r = dict(zip(header, cells))
        r["_submit"], r["_start"], r["_end"] = _time(r.get("Submit", "")), _time(r.get("Start", "")), _time(r.get("End", ""))
        r["_elapsed"] = float(r["ElapsedRaw"]) if r.get("ElapsedRaw", "") not in UNKNOWN else 0.0
        r["_tres"] = parse_tres(r.get("AllocTRES", ""))
        rows.append(r)
    return rows


def alloc_hours(row, unit, window=None):
    """Allocated unit-hours of one job, clipped to window=(start, end) when given."""
    raise NotImplementedError("TODO: implement alloc_hours (see the docstring and tests/)")


def usage_by_account(rows, unit, window=None):
    """{account: {'jobs': n, 'alloc_h': hours}} (jobs that never started count in 'jobs' with 0 hours)."""
    raise NotImplementedError("TODO: implement usage_by_account (see the docstring and tests/)")


def lost_candidates(rows, unit, window=None):
    """{state: hours} for the states in LOSS_STATES (hours of jobs that did not end normally)."""
    raise NotImplementedError("TODO: implement lost_candidates (see the docstring and tests/)")


def utilization(rows, unit, capacity, window):
    """Allocated hours inside the window divided by capacity * window hours."""
    raise NotImplementedError("TODO: implement utilization (see the docstring and tests/)")


def percentile(values, q):
    """Linear-interpolation percentile (q in [0, 100]) of a list; same convention as numpy's default."""
    raise NotImplementedError("TODO: implement percentile (see the docstring and tests/)")


def wait_stats(rows, account=None):
    """{'n', 'p50_h', 'p90_h'} of Start - Submit in hours, over started jobs (of one account if given)."""
    raise NotImplementedError("TODO: implement wait_stats (see the docstring and tests/)")


def allocate_idle(direct, idle_cost, method):
    """Spread the cost of idle capacity. direct: {account: direct cost}. Returns {account: share, 'platform': share}
    whose sum is idle_cost. method: 'proportional' (to direct cost), 'equal' (same amount per account), 'platform'."""
    raise NotImplementedError("TODO: implement allocate_idle (see the docstring and tests/)")


def cost_report(rows, unit, capacity, rate, window, idle_method="proportional"):
    """Full-cost allocation: direct cost per account + idle share = capacity * window hours * rate, exactly."""
    raise NotImplementedError("TODO: implement cost_report (see the docstring and tests/)")


def default_window(rows):
    starts = [r["_start"] for r in rows if r["_start"]]
    ends = [r["_end"] for r in rows if r["_end"]]
    return min(starts), max(ends)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("trace")
    ap.add_argument("--unit", default="gres/gpu", help="TRES to count: gres/gpu (default) or cpu")
    ap.add_argument("--capacity", type=float, required=True, help="number of units (GPUs or CPUs) of the fleet")
    ap.add_argument("--rate", type=float, default=1.0, help="full cost of one unit-hour, any currency (FICTIONAL in the lab)")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--idle", default="proportional", choices=["proportional", "equal", "platform"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    with open(a.trace, encoding="utf-8") as fh:
        rows = parse_rows(fh)
    lo, hi = default_window(rows)
    window = (datetime.fromisoformat(a.start) if a.start else lo, datetime.fromisoformat(a.end) if a.end else hi)
    rep = cost_report(rows, a.unit, a.capacity, a.rate, window, a.idle)
    if a.json:
        json.dump(rep, sys.stdout, indent=1, default=str)
        print()
        return 0
    print("unit=%s capacity=%g window=%.1f h  full cost=%.0f  idle cost=%.0f" % (a.unit, a.capacity, rep["window_hours"], rep["full_cost"], rep["idle_cost"]))
    print("%-8s %6s %10s %9s %9s %9s %8s %8s" % ("account", "jobs", "alloc_h", "direct", "idle", "total", "p50 wait", "p90 wait"))
    for acct, v in sorted(rep["accounts"].items(), key=lambda kv: -kv[1]["total"]):
        w = v["wait"]
        print("%-8s %6d %10.1f %9.0f %9.0f %9.0f %7.2fh %7.2fh" % (acct, v["jobs"], v["alloc_h"], v["direct"], v["idle_share"], v["total"],
                                                              w["p50_h"] or 0.0, w["p90_h"] or 0.0))
    total_alloc = sum(v["alloc_h"] for v in rep["accounts"].values())
    lost = rep["lost"]
    print("utilization (allocated / capacity): %.1f %%" % (100 * rep["utilization"]))
    print("lost candidates: %s = %.1f %% of allocated hours" % (", ".join("%s %.0f" % (s, h) for s, h in lost.items() if h), 100 * sum(lost.values()) / total_alloc if total_alloc else 0.0))
    print("fleet wait: p50 %.2f h, p90 %.2f h" % (rep["wait"]["p50_h"] or 0.0, rep["wait"]["p90_h"] or 0.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
