"""Read the per-rank journals written by collective_journal.py and point at the culprit.

    python3 analyze_journal.py JOURNAL_DIR [--json]

The procedure mirrors what the analyzer of the real NCCL flight recorder does with its dumps:
  1. per rank: last completed sequence number and the collective still in flight;
  2. first sequence number where the ranks disagree on (operation, shape, tag): the ranks in the
     minority are the suspects;
  3. a rank with nothing in flight while the others wait is blocked OUTSIDE the collectives:
     read its Python stack next.
"""
import json
import sys
from collections import Counter
from pathlib import Path


def load(d):
    dumps = {}
    for p in sorted(Path(d).glob("rank*.json")):
        j = json.loads(p.read_text())
        dumps[j["rank"]] = j
    return dumps


def analyze(dumps):
    world = max(j["world"] for j in dumps.values())
    report = {"ranks": {}, "findings": []}
    entries = {r: {e["seq"]: e for e in j["entries"]} for r, j in dumps.items()}
    for r in sorted(dumps):
        done = [s for s, e in entries[r].items() if e["state"] == "completed"]
        flying = [e for e in entries[r].values() if e["state"] == "started"]
        report["ranks"][r] = {"last_completed": max(done) if done else -1,
                              "in_flight": flying[0] if flying else None, "reason": dumps[r]["reason"]}
    missing = sorted(set(range(world)) - set(dumps))
    if missing:
        report["findings"].append(f"no dump from rank(s) {missing}: process dead or stuck before the watchdog could write")
    # first divergence of (op, shape, tag), by majority vote at each sequence number
    last = max((max(e) for e in entries.values() if e), default=-1)
    for seq in range(last + 1):
        sig = {r: (entries[r][seq]["op"], tuple(entries[r][seq]["shape"]), entries[r][seq]["tag"])
               for r in entries if seq in entries[r]}
        if len(set(sig.values())) > 1:
            major, _ = Counter(sig.values()).most_common(1)[0]
            odd = sorted(r for r, s in sig.items() if s != major)
            report["findings"].append(
                f"first divergence at seq {seq}: majority did {major[0]} shape={list(major[1])} tag={major[2]!r}; "
                f"rank(s) {odd} did " + "; ".join(f"{sig[r][0]} tag={sig[r][2]!r} at {entries[r][seq]['site']}" for r in odd)
                + " -> they skipped the collective of the majority's tag")
            break
    # ranks that never reached the collective the others are stuck in
    flying = {r: v["in_flight"] for r, v in report["ranks"].items() if v["in_flight"]}
    if flying:
        stuck_seq = Counter(e["seq"] for e in flying.values()).most_common(1)[0][0]
        waiting = sorted(r for r, e in flying.items() if e["seq"] == stuck_seq)
        absent = [r for r in sorted(report["ranks"]) if r not in waiting and report["ranks"][r]["last_completed"] < stuck_seq
                  and report["ranks"][r]["in_flight"] is None]
        if absent:
            report["findings"].append(
                f"ranks {waiting} wait in seq {stuck_seq} ({flying[waiting[0]]['op']}, {flying[waiting[0]]['tag']}); rank(s) {absent} "
                f"completed only up to seq {min(report['ranks'][r]['last_completed'] for r in absent)} and have nothing in flight "
                "-> blocked outside the collectives: dump their Python stack")
        mism = sorted(r for r, e in flying.items() if e["seq"] == stuck_seq and e["op"] != flying[waiting[0]]["op"])
        ops = {r: (e["seq"], e["op"], e["tag"]) for r, e in flying.items()}
        if len(set(e["op"] for e in flying.values())) > 1:
            report["findings"].append("in-flight operations differ across ranks: " + ", ".join(f"rank {r}: {o} (seq {s}, {t})" for r, (s, o, t) in sorted(ops.items())))
    return report


def render(report):
    lines = ["rank  last_completed  in_flight"]
    for r, v in report["ranks"].items():
        f = v["in_flight"]
        desc = f"seq {f['seq']} {f['op']} {f['tag']!r} at {f['site']}" if f else "-"
        lines.append(f"{r:>4}  {v['last_completed']:>14}  {desc}")
    lines += ["", "findings:"] + [f"  - {x}" for x in report["findings"]]
    return "\n".join(lines)


if __name__ == "__main__":
    rep = analyze(load(sys.argv[1]))
    print(json.dumps(rep, indent=1) if "--json" in sys.argv else render(rep))
