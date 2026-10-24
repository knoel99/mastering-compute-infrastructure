#!/usr/bin/env python3
"""Incident timeline: milestones and durations from a log of timestamped events."""
import sys
from datetime import datetime, timezone

KINDS = ("ANOMALY", "DETECT", "ACK", "DIAG", "MITIGATE", "RESOLVE", "INFO")


def parse(text):
    """[(datetime UTC, source, kind, message)] from 'ISO|source|KIND|message' lines; '#' lines are comments.
    Timestamps must not go backwards."""
    events, last = [], None
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("|", 3)
        if len(parts) != 4:
            raise ValueError(f"line {n}: expected 4 fields separated by '|'")
        ts, source, kind, msg = (p.strip() for p in parts)
        if kind not in KINDS:
            raise ValueError(f"line {n}: unknown kind {kind!r}")
        t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if last is not None and t < last:
            raise ValueError(f"line {n}: timestamp goes backwards")
        last = t
        events.append((t, source, kind, msg))
    return events


def milestones(events):
    """First event of each KIND ANOMALY, DETECT, ACK, MITIGATE, RESOLVE; ValueError lists the missing ones."""
    first = {}
    for t, _src, kind, _msg in events:
        first.setdefault(kind, t)
    missing = [k for k in ("ANOMALY", "DETECT", "ACK", "MITIGATE", "RESOLVE") if k not in first]
    if missing:
        raise ValueError("missing milestones: " + ", ".join(missing))
    return first


def durations(events):
    """Seconds: ttd (anomaly to detection), tta (detection to acknowledgement), ttm (detection to mitigation),
    anomaly_to_mitigation, ttr (anomaly to resolution)."""
    m = milestones(events)
    sec = lambda a, b: (m[b] - m[a]).total_seconds()
    return {"ttd": sec("ANOMALY", "DETECT"), "tta": sec("DETECT", "ACK"), "ttm": sec("DETECT", "MITIGATE"),
            "anomaly_to_mitigation": sec("ANOMALY", "MITIGATE"), "ttr": sec("ANOMALY", "RESOLVE")}


def gpu_hours_idle(gpus, events):
    """GPU-hours during which the job held `gpus` GPUs and made no progress: anomaly to mitigation."""
    return gpus * durations(events)["anomaly_to_mitigation"] / 3600.0


def human(seconds):
    """'1 h 40 min' (rounded to the minute; hours omitted below one hour)."""
    minutes = int(round(seconds / 60.0))
    h, m = divmod(minutes, 60)
    return f"{h} h {m:02d} min" if h else f"{m} min"


def main():
    events = parse(open(sys.argv[1], encoding="utf-8").read())
    gpus = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    d = durations(events)
    print(f"time to detect (anomaly to detection):   {human(d['ttd'])}")
    print(f"time to acknowledge (detection to ack):  {human(d['tta'])}")
    print(f"time to mitigate (detection to fix):     {human(d['ttm'])}")
    print(f"anomaly to mitigation:                   {human(d['anomaly_to_mitigation'])}")
    print(f"anomaly to full resolution:              {human(d['ttr'])}")
    if gpus:
        print(f"GPU-hours without progress ({gpus} GPUs): {gpu_hours_idle(gpus, events):.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
