#!/usr/bin/env python3
"""Kill -9 a real training process at random moments and check that the run is unaffected.

1. run the trainer once, uninterrupted, in <out>/ref;
2. run it again in <out>/chaos, but SIGKILL its whole process group a random time after it said
   READY, restart it, and so on until a run ends normally (the first --min-kills lives are always
   killed; the kill delay grows with the number of lives so that the run always finishes);
3. compare final state digests and every loss ever logged for every step.
The storage is slowed down on purpose (--slow-ckpt-ms) so that kills often land in the middle of
a checkpoint write: that is a simulation of slow storage, not a measurement of any real system.
"""
import argparse
import json
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def spawn(workdir, args):
    cmd = [sys.executable, str(HERE / "trainer.py"), "--workdir", str(workdir), "--steps", str(args.steps),
           "--ckpt-every", str(args.ckpt_every), "--sleep-ms", str(args.sleep_ms), "--slow-ckpt-ms", str(args.slow_ckpt_ms)]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, start_new_session=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=100)
    ap.add_argument("--ckpt-every", type=int, default=10)
    ap.add_argument("--sleep-ms", type=float, default=8.0)
    ap.add_argument("--slow-ckpt-ms", type=float, default=15.0)
    ap.add_argument("--min-kills", type=int, default=3)
    ap.add_argument("--seed", type=int, default=7, help="seed of the kill schedule")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed)

    ref = out / "ref"
    p = spawn(ref, a)
    p.communicate()
    assert p.returncode == 0, "reference run failed"
    ref_final = json.loads((ref / "final.json").read_text())

    chaos = out / "chaos"
    kills, lives, log = 0, 0, []
    while True:
        lives += 1
        p = spawn(chaos, a)
        ready = p.stdout.readline().strip()
        if not ready.startswith("READY"):
            raise SystemExit(f"trainer did not start: {ready!r}")
        info = dict(kv.split("=") for kv in ready.split()[1:])
        delay = rng.uniform(0.25, 0.5) if kills < a.min_kills else rng.uniform(0.25, 0.8) * (1.3 ** (lives - a.min_kills))
        try:
            p.wait(timeout=delay)
            log.append({"life": lives, **info, "outcome": "completed"})
            break
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            kills += 1
            log.append({"life": lives, **info, "outcome": f"killed after {delay:.2f}s"})
    for row in log:
        print(row)

    final = json.loads((chaos / "final.json").read_text())
    seen = {}
    for line in (chaos / "loss.jsonl").read_text().splitlines():
        r = json.loads(line)
        seen.setdefault(r["step"], []).append(r["loss"])
    replayed = sum(len(v) - 1 for v in seen.values())
    consistent = all(len(set(v)) == 1 for v in seen.values())
    complete = sorted(seen) == list(range(a.steps))
    torn = sum(int(r["torn_tmp_found"]) for r in log)
    result = {"kills": kills, "lives": lives, "replayed_steps": replayed, "torn_tmp_dirs_met": torn,
              "every_step_logged": complete, "replayed_losses_identical": consistent,
              "final_digest_equal": final["digest"] == ref_final["digest"]}
    print(json.dumps(result))
    return 0 if complete and consistent and result["final_digest_equal"] and kills >= a.min_kills else 1


if __name__ == "__main__":
    sys.exit(main())
