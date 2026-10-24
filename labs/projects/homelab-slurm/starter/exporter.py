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
    """TO WRITE (milestone 3). sinfo state without its trailing flags: 'mix~' -> 'mix', 'DOWN*' -> 'down'."""
    raise NotImplementedError


def bounded_reason(text, limit=24):
    """TO WRITE. A low-cardinality label from a free-text reason: 'none' for empty or 'none'; otherwise the part
    before ':' or the first word, lower-cased, non [a-z0-9_] characters replaced by '_', at most `limit` characters."""
    raise NotImplementedError


def parse_sinfo(text):
    """TO WRITE. [{"partition" (without the trailing '*'), "node", "state" (normalised), "reason"}] from fixtures/sinfo_*.txt."""
    raise NotImplementedError


def parse_squeue(text):
    """TO WRITE. [{"id", "partition", "user", "account", "state", "reason", "submit"}], submit as epoch seconds (UTC),
    from fixtures/squeue_mixed.txt."""
    raise NotImplementedError


def parse_sshare(text):
    """TO WRITE. [{"account", "user", "raw_shares", "norm_shares", "fairshare"}] from fixtures/sshare.txt. sshare indents the
    first column even with -P: strip it. An empty FairShare column gives fairshare None."""
    raise NotImplementedError


def samples(sinfo_text, squeue_text, sshare_text, now):
    """TO WRITE. Dict metric name -> [(labels dict, value)] with the metrics listed in HELP:
    slurm_nodes{partition,state} counts; slurm_node_unhealthy{partition,node,reason}=1 for UNHEALTHY states with a
    bounded reason; slurm_jobs{partition,state} counts, ZERO-FILLED for PENDING and RUNNING for every partition seen in
    sinfo (an alert on 'nothing runs' needs a 0, not a missing series); slurm_jobs_pending_by_reason{reason} with unknown
    reasons grouped as 'other'; slurm_job_max_pending_seconds{partition} = now - oldest pending submit time;
    slurm_account_norm_shares{account} for rows without user; slurm_user_fairshare{account,user} for rows with a FairShare."""
    raise NotImplementedError


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
    """TO WRITE. Prometheus text: always `slurm_scrape_ok 1|0` with HELP and TYPE gauge; only when ok, every metric of m
    with HELP, TYPE gauge, and one line per sample: name{k="v",...} value (format %g)."""
    raise NotImplementedError


def run_cmd(argv):
    # squeue prints submit times in the LOCAL time zone and parse_squeue reads them as UTC: force UTC, otherwise every
    # pending age is off by the UTC offset (observed: TZ=America/New_York gave 14402 s for a job submitted 2 s earlier).
    r = subprocess.run(argv, capture_output=True, text=True, timeout=20, env={**os.environ, "TZ": "UTC"})
    if r.returncode != 0:
        raise RuntimeError(f"{argv[0]} failed: {r.stderr.strip()[:200]}")
    return r.stdout


def collect(run=run_cmd, now=None):
    """TO WRITE. Exposition text of one scrape: run the three commands (see the module docstring), build the samples and
    render them. If ANY command raises (RuntimeError, OSError, ValueError, TimeoutExpired), return render({}, ok=False):
    stale numbers must not look fresh."""
    raise NotImplementedError


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
