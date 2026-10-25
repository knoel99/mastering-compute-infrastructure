"""What happens when a worker dies: tasks, actors, actor state, retries.

Failures are injected with os._exit(1) inside the worker process. Marker files
make the failure happen only once, so that a retry can succeed.
"""
import json
import os

import ray


def atomic_write_json(path, obj):
    """Write-then-rename: a reader never sees a half-written file."""
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(obj, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


@ray.remote
class Counter:
    """A stateful actor. If `ckpt` is given, state survives a restart."""

    def __init__(self, ckpt=None):
        self.ckpt = ckpt
        self.n = 0
        if ckpt and os.path.exists(ckpt):
            with open(ckpt) as f:
                self.n = json.load(f)["n"]

    def inc(self):
        self.n += 1
        if self.ckpt:
            atomic_write_json(self.ckpt, {"n": self.n})
        return self.n

    def die(self):
        os._exit(1)

    def pid(self):
        return os.getpid()

    def work(self, i, log, marker):
        """Append `i` to a log (a side effect), crash once, then succeed."""
        with open(log, "a") as f:
            f.write(f"{i}\n")
        if not os.path.exists(marker):
            open(marker, "w").close()
            os._exit(1)
        return i


@ray.remote
def flaky_task(marker):
    """Crash the worker process on the first attempt only."""
    if not os.path.exists(marker):
        open(marker, "w").close()
        os._exit(1)
    return "ok"


def call_until_alive(fn, timeout_s=30.0):
    """Retry `fn()` while the actor is restarting (RayActorError)."""
    import time
    t0 = time.time()
    while True:
        try:
            return ray.get(fn())
        except ray.exceptions.RayActorError:
            if time.time() - t0 > timeout_s:
                raise
            time.sleep(0.2)
