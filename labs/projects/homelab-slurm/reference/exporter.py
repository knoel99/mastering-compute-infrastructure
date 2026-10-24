"""Slurm metrics in Prometheus text format, from sinfo, squeue and sshare.

Commands (formats captured on Slurm 23.11.4, see fixtures/):
  sinfo -h -N -o "%P|%N|%t|%c|%m|%E"            partition|node|state|cpus|memory|reason
  squeue -h -o "%i|%P|%u|%a|%T|%r|%V"           id|partition|user|account|state|reason|submit time
  sshare -n -P -o Account,User,RawShares,NormShares,RawUsage,EffectvUsage,FairShare
Label values are BOUNDED on purpose: a free-text node reason or an unknown pending reason would create one time
series per distinct string.
"""
import calendar
import os
import re
import subprocess
import time

KNOWN_PENDING = {"Priority", "Resources", "Dependency", "InvalidAccount", "AssocGrpCpuLimit", "QOSMaxJobsPerUserLimit",
                 "ReqNodeNotAvail", "JobHeldUser", "BeginTime", "Licenses", "PartitionDown"}
UNHEALTHY = {"drain", "drng", "down", "fail", "failg", "maint"}


def norm_state(raw):
    """sinfo state with its trailing flags removed: 'mix~' -> 'mix', 'down*' -> 'down'."""
    return re.sub(r"[*#~!%$@^-]+$", "", raw.strip().lower())


def bounded_reason(text, limit=24):
    """Low-cardinality label from a free-text reason: the part before ':' or the first word, lower-cased."""
    t = text.strip().lower()
    if not t or t == "none":
        return "none"
    head = re.split(r"[:\s]", t, maxsplit=1)[0]
    return re.sub(r"[^a-z0-9_]", "_", head)[:limit] or "other"


def parse_sinfo(text):
    out = []
    for line in text.splitlines():
        if line.strip():
            part, node, state, cpus, mem, reason = (line.split("|") + [""] * 6)[:6]
            out.append({"partition": part.rstrip("*"), "node": node, "state": norm_state(state), "reason": reason})
    return out


def _epoch(ts):
    return calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%S"))


def parse_squeue(text):
    out = []
    for line in text.splitlines():
        if line.strip():
            jid, part, user, acct, state, reason, submit = (line.split("|") + [""] * 7)[:7]
            out.append({"id": jid, "partition": part, "user": user, "account": acct, "state": state,
                        "reason": reason, "submit": _epoch(submit) if submit else None})
    return out


def parse_sshare(text):
    """Rows with their depth. sshare indents the first column even with -P: strip it."""
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cols = line.split("|")
        account = cols[0].strip()
        fs = cols[6].strip() if len(cols) > 6 else ""
        out.append({"account": account, "user": cols[1].strip(), "raw_shares": float(cols[2] or 0) if len(cols) > 2 and cols[2] else 0.0,
                    "norm_shares": float(cols[3]) if len(cols) > 3 and cols[3] else 0.0,
                    "fairshare": float(fs) if fs else None})
    return out


def samples(sinfo_text, squeue_text, sshare_text, now):
    """Dict of metric name -> list of (labels dict, value)."""
    nodes, jobs, shares = parse_sinfo(sinfo_text), parse_squeue(squeue_text), parse_sshare(sshare_text)
    m = {}
    counts = {}
    for n in nodes:
        counts[(n["partition"], n["state"])] = counts.get((n["partition"], n["state"]), 0) + 1
    m["slurm_nodes"] = [({"partition": p, "state": s}, c) for (p, s), c in sorted(counts.items())]
    m["slurm_node_unhealthy"] = [({"partition": n["partition"], "node": n["node"], "reason": bounded_reason(n["reason"])}, 1)
                                 for n in nodes if n["state"] in UNHEALTHY]
    jc, rc, waits = {}, {}, {}
    for part in {n["partition"] for n in nodes}:  # zero-fill: an alert on "nothing runs" needs a series that says 0, not no series
        for st in ("PENDING", "RUNNING"):
            jc[(part, st)] = 0
    for j in jobs:
        jc[(j["partition"], j["state"])] = jc.get((j["partition"], j["state"]), 0) + 1
        if j["state"] == "PENDING":
            r = j["reason"] if j["reason"] in KNOWN_PENDING else "other"
            rc[r] = rc.get(r, 0) + 1
            if j["submit"] is not None:
                waits[j["partition"]] = max(waits.get(j["partition"], 0), now - j["submit"])
    m["slurm_jobs"] = [({"partition": p, "state": s}, c) for (p, s), c in sorted(jc.items())]
    m["slurm_jobs_pending_by_reason"] = [({"reason": r}, c) for r, c in sorted(rc.items())]
    m["slurm_job_max_pending_seconds"] = [({"partition": p}, w) for p, w in sorted(waits.items())]
    m["slurm_account_norm_shares"] = [({"account": s["account"]}, s["norm_shares"]) for s in shares if not s["user"]]
    m["slurm_user_fairshare"] = [({"account": s["account"], "user": s["user"]}, s["fairshare"]) for s in shares
                                 if s["user"] and s["fairshare"] is not None]
    return m


HELP = {
    "slurm_nodes": "Number of nodes by partition and normalised state.",
    "slurm_node_unhealthy": "1 for a node that is drained, draining, down, failing or in a maintenance reservation; reason is a bounded label.",
    "slurm_jobs": "Number of jobs by partition and state.",
    "slurm_jobs_pending_by_reason": "Pending jobs by scheduler reason (unknown reasons are grouped as other).",
    "slurm_job_max_pending_seconds": "Age of the oldest pending job, by partition.",
    "slurm_account_norm_shares": "Normalised fairshare allocation of an account.",
    "slurm_user_fairshare": "Fairshare factor of a user association as reported by sshare (see the Slurm priority documentation).",
}


def render(m, ok=True):
    lines = ["# HELP slurm_scrape_ok 1 when the last collection from sinfo, squeue and sshare succeeded.",
             "# TYPE slurm_scrape_ok gauge", f"slurm_scrape_ok {1 if ok else 0}"]
    if ok:
        for name, rows in m.items():
            lines += [f"# HELP {name} {HELP[name]}", f"# TYPE {name} gauge"]
            for labels, value in rows:
                lab = ",".join(f'{k}="{v}"' for k, v in labels.items())
                lines.append(f"{name}{{{lab}}} {value:g}")
    return "\n".join(lines) + "\n"


def run_cmd(argv):
    # squeue prints submit times in the LOCAL time zone and parse_squeue reads them as UTC: force UTC, otherwise every
    # pending age is off by the UTC offset (observed: TZ=America/New_York gave 14402 s for a job submitted 2 s earlier).
    r = subprocess.run(argv, capture_output=True, text=True, timeout=20, env={**os.environ, "TZ": "UTC"})
    if r.returncode != 0:
        raise RuntimeError(f"{argv[0]} failed: {r.stderr.strip()[:200]}")
    return r.stdout


def collect(run=run_cmd, now=None):
    """Exposition text for one scrape. Any failing command gives slurm_scrape_ok 0 and nothing else:
    stale numbers must not look fresh."""
    now = int(time.time()) if now is None else now
    try:
        sinfo = run(["sinfo", "-h", "-N", "-o", "%P|%N|%t|%c|%m|%E"])
        squeue = run(["squeue", "-h", "-o", "%i|%P|%u|%a|%T|%r|%V"])
        sshare = run(["sshare", "-n", "-P", "-o", "Account,User,RawShares,NormShares,RawUsage,EffectvUsage,FairShare"])
        return render(samples(sinfo, squeue, sshare, now))
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired):
        return render({}, ok=False)


def main():
    import argparse
    import http.server
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="print one scrape and exit")
    ap.add_argument("--port", type=int, default=9341)
    a = ap.parse_args()
    if a.once:
        print(collect(), end="")
        return 0

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/metrics":
                self.send_error(404)
                return
            body = collect().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    http.server.ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
