"""Node and queue exporter for a GPU training fleet (course module 14, lab 14.1).

Three collectors behind one /metrics endpoint, built with prometheus_client:

  GpuNodeCollector     reads the text a dcgm-exporter serves (or a fixture file) and exports node-level
                       summaries that are cheap to alert on: hot GPUs, busy-but-idle GPUs, clock spread.
  SlurmQueueCollector  reads `squeue --json` / `sinfo --json` (or fixtures) and exports queue and node state,
                       with bounded labels (pending reasons are grouped into classes).
  WaitHistogram        turns finished jobs from `sacct` into a Histogram of queue wait, each job counted once.

Design rules the tests enforce: a failing source never raises and never serves stale values (the scrape reports
success=0 instead), label values come from small closed sets, names follow the Prometheus naming guide.
"""
import argparse
import json
import statistics
import subprocess
import time
from datetime import datetime

from prometheus_client import CollectorRegistry, Histogram, generate_latest, start_http_server
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.parser import text_string_to_metric_families

HOT_C = 85.0           # alert-relevant threshold, tune per GPU model (the course only uses it as a default)
BUSY_UTIL = 80.0       # percent: "looks busy" for DCGM_FI_DEV_GPU_UTIL
IDLE_TENSOR = 0.05     # ratio: tensor pipe "looks idle"
WAIT_BUCKETS = (10, 30, 60, 300, 600, 1800, 3600, 4 * 3600, 12 * 3600, 24 * 3600)

# Pending reasons grouped by who can act. The grouping is this course's design, the reasons are Slurm's.
REASON_CLASS = {
    "Priority": "capacity", "Resources": "capacity", "ReqNodeNotAvail": "capacity",
    "JobHeldUser": "user", "Dependency": "user", "BeginTime": "user",
    "JobHeldAdmin": "admin", "Reservation": "admin", "PartitionDown": "admin",
    "InvalidAccount": "config", "InvalidQOS": "config",
}


def reason_class(reason):
    """Closed set {capacity,user,admin,config,other}: the label stays bounded whatever Slurm reports."""
    return REASON_CLASS.get(reason, "other")


# ----------------------------------------------------------------------------------------------- GPU side
def parse_dcgm(text):
    """Return {gpu_index: {metric_name: value, 'Hostname': ...}} from dcgm-exporter exposition text."""
    gpus = {}
    for family in text_string_to_metric_families(text):
        for s in family.samples:
            if "gpu" not in s.labels:
                continue
            g = gpus.setdefault(int(s.labels["gpu"]), {"Hostname": s.labels.get("Hostname", "unknown")})
            g[s.name] = s.value
    return gpus


class GpuNodeCollector:
    def __init__(self, read_text, hot_c=HOT_C):
        self.read_text, self.hot_c = read_text, hot_c

    def collect(self):
        t0, ok, gpus = time.monotonic(), 1, {}
        try:
            gpus = parse_dcgm(self.read_text())
            if not gpus:
                raise ValueError("no GPU sample in the source")
        except Exception:  # a broken source must not break the scrape, and must not leave old values behind
            ok, gpus = 0, {}
        if gpus:
            host = next(iter(gpus.values()))["Hostname"]
            temps = [g.get("DCGM_FI_DEV_GPU_TEMP", 0.0) for g in gpus.values()]
            tensor = [g.get("DCGM_FI_PROF_PIPE_TENSOR_ACTIVE", 0.0) for g in gpus.values()]
            # only busy GPUs: an idle GPU clocks down legitimately and would look like a straggler
            clocks = [g.get("DCGM_FI_DEV_SM_CLOCK", 0.0) for g in gpus.values()
                      if g.get("DCGM_FI_DEV_GPU_UTIL", 0) >= BUSY_UTIL] or \
                     [g.get("DCGM_FI_DEV_SM_CLOCK", 0.0) for g in gpus.values()]
            xid = sum(1 for g in gpus.values() if g.get("DCGM_FI_DEV_XID_ERRORS", 0) > 0)
            busy_idle = sum(1 for g in gpus.values()
                            if g.get("DCGM_FI_DEV_GPU_UTIL", 0) >= BUSY_UTIL
                            and g.get("DCGM_FI_PROF_PIPE_TENSOR_ACTIVE", 1) < IDLE_TENSOR)
            med_clock = statistics.median(clocks)
            for name, doc, value in [
                ("gpu_node_gpus", "GPUs seen in the last dcgm-exporter scrape.", len(gpus)),
                ("gpu_node_hot_gpus", "GPUs above the temperature threshold.", sum(t > self.hot_c for t in temps)),
                ("gpu_node_xid_gpus", "GPUs whose last XID error is non-zero.", xid),
                ("gpu_node_busy_but_tensor_idle_gpus",
                 "GPUs with high utilization and an idle tensor pipe (stall signature).", busy_idle),
                ("gpu_node_sm_clock_min_over_median_ratio",
                 "Slowest SM clock of the busy GPUs divided by their median (1 = no straggler).",
                 min(clocks) / med_clock if med_clock else 0.0),
                ("gpu_node_tensor_active_median_ratio", "Median tensor-pipe activity over the node's GPUs.",
                 statistics.median(tensor)),
            ]:
                m = GaugeMetricFamily(name, doc, labels=["node"])
                m.add_metric([host], value)
                yield m
        for name, doc, value in [("gpu_node_scrape_success", "1 when the dcgm source was read and parsed.", ok),
                                 ("gpu_node_scrape_duration_seconds", "Time spent reading the source.",
                                  time.monotonic() - t0)]:
            m = GaugeMetricFamily(name, doc)
            m.add_metric([], value)
            yield m


# --------------------------------------------------------------------------------------------- Slurm side
def node_state(states):
    """Collapse sinfo's state list (base state plus flags) to one word, as sinfo prints it."""
    s = {x.upper() for x in states}
    if "DOWN" in s:
        return "down"
    base = next(iter(s - {"DRAIN", "COMPLETING", "NOT_RESPONDING", "PLANNED"}), "UNKNOWN").lower()
    if "DRAIN" in s:
        return "draining" if base in ("allocated", "mixed") else "drained"
    return base


class SlurmQueueCollector:
    def __init__(self, read_squeue, read_sinfo, now=time.time):
        self.read_squeue, self.read_sinfo, self.now = read_squeue, read_sinfo, now

    def collect(self):
        t0, ok = time.monotonic(), 1
        jobs, parts = [], []
        try:
            jobs, parts = self.read_squeue()["jobs"], self.read_sinfo()["sinfo"]
        except Exception:
            ok, jobs, parts = 0, [], []
        if ok:
            counts, oldest = {}, {}
            for j in jobs:
                state = j["job_state"][0]
                rc = reason_class(j.get("state_reason", "")) if state == "PENDING" else "none"
                counts[(state, rc)] = counts.get((state, rc), 0) + 1
                if state == "PENDING":
                    age = self.now() - j["submit_time"]["number"]
                    oldest[rc] = max(oldest.get(rc, 0.0), age)
            m = GaugeMetricFamily("slurm_jobs", "Jobs by state; pending jobs by reason class.", labels=["state", "reason_class"])
            for (state, rc), n in sorted(counts.items()):
                m.add_metric([state.lower(), rc], n)
            yield m
            m = GaugeMetricFamily("slurm_pending_oldest_age_seconds", "Age of the oldest pending job per reason class.", labels=["reason_class"])
            for rc, age in sorted(oldest.items()):
                m.add_metric([rc], age)
            yield m
            nodes = GaugeMetricFamily("slurm_nodes", "Nodes by collapsed state.", labels=["partition", "state"])
            drain = GaugeMetricFamily("slurm_node_drain_info", "1 per drained or down node; the class is bounded.", labels=["node", "reason_class"])
            cpus = GaugeMetricFamily("slurm_cpus", "CPUs by allocation state.", labels=["partition", "state"])
            per_state = {}
            for p in parts:
                st = node_state(p["node"]["state"])
                name = p["partition"]["name"]
                per_state[(name, st)] = per_state.get((name, st), 0) + len(p["nodes"]["nodes"])
                for k in ("allocated", "idle", "other"):
                    cpus.add_metric([name, k], p["cpus"][k])
                if st in ("down", "drained", "draining"):
                    desc = p.get("reason", {}).get("description", "")
                    cls = "health" if desc.startswith("health:") else "maintenance" if desc.startswith("maint") else "other"
                    for n in p["nodes"]["nodes"]:
                        drain.add_metric([n, cls], 1)
            for (name, st), n in sorted(per_state.items()):
                nodes.add_metric([name, st], n)
            yield nodes
            yield drain
            yield cpus
        for name, doc, value in [("slurm_scrape_success", "1 when squeue and sinfo were read and parsed.", ok),
                                 ("slurm_scrape_duration_seconds", "Time spent reading the Slurm commands.",
                                  time.monotonic() - t0)]:
            g = GaugeMetricFamily(name, doc)
            g.add_metric([], value)
            yield g


class WaitHistogram:
    """Observe the queue wait of each finished job exactly once (a Histogram must only grow)."""

    def __init__(self, registry):
        self.hist = Histogram("slurm_job_wait_seconds", "Seconds between submit and start of a job.",
                              ["qos"], buckets=WAIT_BUCKETS, registry=registry)
        self.seen = set()

    def observe_sacct(self, text):
        """text: `sacct -X -P -n --format=JobID,QOS,State,Submit,Start` output."""
        new = 0
        for line in text.splitlines():
            jobid, qos, state, submit, start = line.split("|")[:5]
            if jobid in self.seen or start in ("Unknown", "None", ""):
                continue  # never started (or still pending): no wait to report yet
            self.seen.add(jobid)
            wait = (datetime.fromisoformat(start) - datetime.fromisoformat(submit)).total_seconds()
            self.hist.labels(qos=qos).observe(max(wait, 0.0))
            new += 1
        return new


# -------------------------------------------------------------------------------------------- assembling
def run_json(cmd):
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10).stdout)


def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def build_registry(dcgm_read, squeue_read, sinfo_read, now=time.time):
    """Return (registry, wait_histogram). The caller feeds the histogram with sacct output."""
    reg = CollectorRegistry()
    reg.register(GpuNodeCollector(dcgm_read))
    reg.register(SlurmQueueCollector(squeue_read, sinfo_read, now=now))
    return reg, WaitHistogram(reg)


SACCT_CMD = ["sacct", "-X", "-P", "-n", "--format=JobID,QOS,State,Submit,Start", "-S", "now-1hours"]


def fixture_readers(fixdir):
    return (lambda: read_file(f"{fixdir}/dcgm_node.prom"),
            lambda: json.loads(read_file(f"{fixdir}/slurm/squeue_busy.json")),
            lambda: json.loads(read_file(f"{fixdir}/slurm/sinfo_mixed.json")),
            lambda: read_file(f"{fixdir}/slurm/sacct.txt"))


def live_readers(dcgm_url):
    import urllib.request
    return (lambda: urllib.request.urlopen(dcgm_url, timeout=2).read().decode(),
            lambda: run_json(["squeue", "--json"]),
            lambda: run_json(["sinfo", "--json"]),
            lambda: subprocess.run(SACCT_CMD, capture_output=True, text=True, check=True, timeout=10).stdout)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=9877)
    ap.add_argument("--fixtures", help="directory with dcgm_node.prom and slurm/* (offline mode)")
    ap.add_argument("--dcgm-url", default="http://127.0.0.1:9400/metrics", help="live mode: dcgm-exporter URL")
    ap.add_argument("--once", action="store_true", help="print one scrape to stdout and exit")
    a = ap.parse_args(argv)
    dcgm, squeue, sinfo, sacct = fixture_readers(a.fixtures) if a.fixtures else live_readers(a.dcgm_url)
    reg, waits = build_registry(dcgm, squeue, sinfo)
    if a.once:
        waits.observe_sacct(sacct())
        print(generate_latest(reg).decode(), end="")
        return 0
    start_http_server(a.port, registry=reg)
    while True:  # sacct is polled here, not on every scrape: accounting queries are heavier than squeue
        try:
            waits.observe_sacct(sacct())
        except Exception:
            pass
        time.sleep(30)


if __name__ == "__main__":
    raise SystemExit(main())
