"""Prometheus text exposition of simulated GPU samples, with dcgm-exporter metric names.

The allocation join metric slurm_job_gpu_allocated is this project's own convention.
"""
import http.server
import threading

from sim import MODEL

METRICS = [
    # (name, type, help, field)
    ("DCGM_FI_DEV_GPU_UTIL", "gauge", "GPU utilization (in %).", "util"),
    ("DCGM_FI_DEV_POWER_USAGE", "gauge", "Power draw (in W).", "power"),
    ("DCGM_FI_DEV_SM_CLOCK", "gauge", "SM clock frequency (in MHz).", "sm_clock"),
    ("DCGM_FI_DEV_GPU_TEMP", "gauge", "GPU temperature (in C).", "temp"),
    ("DCGM_FI_DEV_XID_ERRORS", "gauge", "Value of the last XID error encountered.", "xid"),
    ("DCGM_FI_PROF_PIPE_TENSOR_ACTIVE", "gauge", "Ratio of cycles the tensor (HMMA) pipe is active.", "tensor"),
]
CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


def _labels(s):
    return f'gpu="{s.gpu}",UUID="GPU-{s.host}-{s.gpu}",device="nvidia{s.gpu}",modelName="{MODEL}",Hostname="{s.host}"'


def render(samples):
    """Exposition text for one scrape: one HELP/TYPE per metric. Values are printed with %g (6 significant digits)."""
    out = []
    for name, typ, help_, field in METRICS:
        out += [f"# HELP {name} {help_}", f"# TYPE {name} {typ}"]
        out += [f"{name}{{{_labels(s)}}} {getattr(s, field):g}" for s in samples]
    out += ["# HELP slurm_job_gpu_allocated 1 when the GPU is allocated to the job in the job label.",
            "# TYPE slurm_job_gpu_allocated gauge"]
    out += [f'slurm_job_gpu_allocated{{Hostname="{s.host}",gpu="{s.gpu}",job="{s.job}"}} 1' for s in samples if s.job]
    return "\n".join(out) + "\n"


def serve(get_samples, port=0):
    """Start /metrics on 127.0.0.1 in a thread; get_samples() returns the latest list of samples.
    Return (server, port); call server.shutdown() to stop."""
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/metrics":
                self.send_error(404)
                return
            body = render(get_samples()).encode()
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]
