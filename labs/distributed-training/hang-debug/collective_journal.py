"""A tiny "flight recorder" for gloo collectives (an educational analogue, not the real thing).

PyTorch's real NCCL flight recorder (TORCH_NCCL_TRACE_BUFFER_SIZE, TORCH_NCCL_DUMP_ON_TIMEOUT)
only exists for the NCCL backend, which needs GPUs. This module reproduces its idea in pure Python
for gloo so that the investigation procedure can be practised on a laptop:

  * every collective gets a sequence number (per rank), an operation name, a tensor shape and dtype,
    the call site (file:line) and a free-form tag (here the training step);
  * entries go to a ring buffer with a state: "started" then "completed";
  * a watchdog thread dumps the buffer to <dir>/rank<r>.json when a collective has been "started"
    for more than `stall_s` seconds, or when nothing has happened for `idle_s` seconds (the thread keeps
    running while the main thread is blocked, because PyTorch releases the GIL while it waits).
"""
import json
import os
import sys
import threading
import time
from collections import deque

import torch.distributed as dist


class Journal:
    def __init__(self, rank, world, outdir, capacity=256, stall_s=2.0, idle_s=2.5):
        self.rank, self.world, self.outdir = rank, world, outdir
        self.entries, self.seq, self.tag, self.stall_s, self.idle_s = deque(maxlen=capacity), 0, "", stall_s, idle_s
        self._dumped, self.last_activity = False, time.time()
        os.makedirs(outdir, exist_ok=True)
        threading.Thread(target=self._watchdog, daemon=True).start()

    def _start(self, op, tensor):
        frame = sys._getframe(2)  # the caller of all_reduce()/barrier() below
        entry = {"seq": self.seq, "op": op, "tag": self.tag, "state": "started", "t": time.time(),
                 "site": f"{os.path.basename(frame.f_code.co_filename)}:{frame.f_lineno}",
                 "shape": list(tensor.shape) if tensor is not None else [],
                 "dtype": str(tensor.dtype).replace("torch.", "") if tensor is not None else ""}
        self.seq += 1
        self.entries.append(entry)
        self.last_activity = time.time()
        return entry

    def all_reduce(self, tensor):
        e = self._start("all_reduce", tensor)
        dist.all_reduce(tensor)
        e["state"] = "completed"
        self.last_activity = time.time()

    def barrier(self):
        e = self._start("barrier", None)
        dist.barrier()
        e["state"] = "completed"
        self.last_activity = time.time()

    def dump(self, reason):
        with open(os.path.join(self.outdir, f"rank{self.rank}.json"), "w") as f:
            json.dump({"rank": self.rank, "world": self.world, "reason": reason, "entries": list(self.entries)}, f)

    def _watchdog(self):
        while True:
            time.sleep(0.25)
            pending = [e for e in list(self.entries) if e["state"] == "started"]
            if self._dumped:
                continue
            if pending and time.time() - pending[0]["t"] > self.stall_s:
                self._dumped = True
                self.dump(f"watchdog: collective seq {pending[0]['seq']} started more than {self.stall_s}s ago and is not completed")
            elif not pending and self.entries and time.time() - self.last_activity > self.idle_s:
                self._dumped = True  # nothing in flight and nothing happening: stuck outside the collectives
                self.dump(f"watchdog: no collective activity for more than {self.idle_s}s")
