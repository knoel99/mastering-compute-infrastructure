"""Part D: one OpenTelemetry span per training step, with one child span per phase (data, compute, comm, update).

No collector and no network: the SDK's ConsoleSpanExporter writes each finished span as one JSON line to a file
(its `out=` and `formatter=` arguments). The phase durations are SIMULATED (assumed values below) and passed as
explicit span start and end times, so nothing depends on the machine's clock. Step 13 has a slow data loader.
The script reads the file back, rebuilds each step from the parent ids, and names the phase that made the slowest
step slow: this is what a trace adds to a step-duration metric.

    python3 trace_steps.py   (needs `pip install opentelemetry-sdk`; prints SKIPPED and exits 0 when it is absent)
"""
import json
import statistics
import sys
import tempfile
from datetime import datetime
from pathlib import Path

STEPS, SLOW_STEP = 20, 13
PHASES = (("data", 0.10), ("forward_backward", 1.20), ("all_reduce", 0.30), ("optimizer", 0.05))  # seconds, assumed
SLOW_DATA_S = 1.70                       # the injected fault: one slow read from storage at SLOW_STEP
NS = 1_000_000_000
EPOCH_NS = 1_700_000_000 * NS            # a fixed start: simulated time, not the wall clock


def phase_durations(step):
    durations = dict(PHASES)
    if step == SLOW_STEP:
        durations["data"] = SLOW_DATA_S
    return durations


def emit(path):
    """Write STEPS step spans, each the parent of one span per phase, as JSON lines."""
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    with open(path, "w", encoding="utf-8") as out:
        provider = TracerProvider(resource=Resource.create({"service.name": "trainer", "job_id": "4412", "rank": 0}))
        provider.add_span_processor(SimpleSpanProcessor(
            ConsoleSpanExporter(out=out, formatter=lambda span: span.to_json(indent=None) + "\n")))
        tracer = provider.get_tracer("lab14.3")
        t = EPOCH_NS
        for step in range(STEPS):
            durations = phase_durations(step)
            step_span = tracer.start_span("train_step", start_time=t, attributes={"step": step})
            ctx = trace.set_span_in_context(step_span)
            for name, _ in PHASES:
                child = tracer.start_span(name, context=ctx, start_time=t)
                t += round(durations[name] * NS)
                child.end(end_time=t)
            step_span.end(end_time=t)
        provider.shutdown()


def seconds(span):
    start, end = (datetime.fromisoformat(span[k].replace("Z", "+00:00")) for k in ("start_time", "end_time"))
    return (end - start).total_seconds()


def analyse(path):
    """Rebuild steps from parent ids; return True when the slow step and its phase are found."""
    spans = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    steps = {s["context"]["span_id"]: s for s in spans if s["name"] == "train_step"}
    phases = {}
    for s in spans:
        if s["name"] != "train_step":
            phases.setdefault(s["parent_id"], {})[s["name"]] = seconds(s)
    orphans = sum(len(v) for k, v in phases.items() if k not in steps)
    rows = sorted((s["attributes"]["step"], seconds(s), phases.get(sid, {})) for sid, s in steps.items())
    median_step = statistics.median(r[1] for r in rows)
    median_phase = {name: statistics.median(r[2][name] for r in rows) for name, _ in PHASES}
    step, duration, slow = max(rows, key=lambda r: r[1])
    culprit = max(slow, key=lambda name: slow[name] - median_phase[name])
    print(f"spans written: {len(spans)} ({len(rows)} steps x (1 + {len(PHASES)} phases)), one JSON line each, "
          f"{orphans} without a step parent")
    print(f"median step {median_step:.2f} s; slowest step {step}: {duration:.2f} s, "
          f"of which {culprit} {slow[culprit]:.2f} s (median {median_phase[culprit]:.2f} s)")
    ok = (len(spans) == STEPS * (1 + len(PHASES)) and orphans == 0 and step == SLOW_STEP and culprit == "data")
    print(f"OK part D: step {step} is slow because of {culprit}" if ok else "FAIL part D")
    return ok


def main():
    try:
        import opentelemetry.sdk.trace  # noqa: F401
    except ImportError:
        print("SKIPPED part D: opentelemetry-sdk not installed (pip install opentelemetry-sdk)")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "spans.jsonl"
        emit(path)
        return 0 if analyse(path) else 1


if __name__ == "__main__":
    sys.exit(main())
