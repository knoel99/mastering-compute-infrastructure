#!/usr/bin/env python3
"""Toy training loop that checkpoints atomically when it receives SIGUSR1 and resumes from the checkpoint."""
import json
import os
import signal
import sys
import time

CKPT = os.environ.get("CKPT_FILE", "/tmp/ckpt-demo.json")
TOTAL = int(os.environ.get("TOTAL_STEPS", "200"))
stop = False


def on_usr1(signum, frame):
    global stop
    stop = True


def save(step):
    tmp = CKPT + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"step": step}, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, CKPT)  # atomic: a crash never leaves a half-written checkpoint


signal.signal(signal.SIGUSR1, on_usr1)
step = json.load(open(CKPT))["step"] if os.path.exists(CKPT) else 0
print(f"start at step {step}", flush=True)
while step < TOTAL and not stop:
    time.sleep(0.1)
    step += 1
if stop:
    save(step)
    print(f"SIGUSR1: checkpoint saved at step {step}", flush=True)
    sys.exit(0)
save(step)
print(f"finished at step {step}", flush=True)
