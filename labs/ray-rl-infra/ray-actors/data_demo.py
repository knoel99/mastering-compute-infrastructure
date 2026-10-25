"""Ray Data streaming with a stateful stage pinned to a logical resource (chapters 3 and 7).

SIMULATION: 'eval_gpu' is a logical resource declared on a CPU-only machine, and the scoring stage
sleeps instead of running a model. What is real: Ray Data's streaming executor, the actor pool,
and the scheduler honouring the resource request.
"""
import os
import time

import numpy as np
import ray


def preprocess(batch):
    batch["x"] = (batch["id"] % 97).astype(np.float64) / 97.0
    return batch


class Scorer:
    """Stateful stage: built once per actor (a model would be loaded here)."""

    def __init__(self):
        self.pid = os.getpid()

    def __call__(self, batch):
        time.sleep(0.02)                    # SIMULATED inference time
        batch["score"] = np.tanh(batch["x"])
        batch["pid"] = np.full(len(batch["x"]), self.pid)
        return batch


def main(rows=4000, blocks=40):
    ray.init(num_cpus=4, resources={"eval_gpu": 2}, include_dashboard=False,
             logging_level="ERROR", log_to_driver=False)
    ds = (ray.data.range(rows, override_num_blocks=blocks)
          .map_batches(preprocess, batch_format="numpy")
          .map_batches(Scorer, batch_format="numpy", batch_size=100, concurrency=2,
                       num_cpus=0, resources={"eval_gpu": 1}))
    n, pids, first_at = 0, set(), None
    t0 = time.perf_counter()
    for batch in ds.iter_batches(batch_size=100, batch_format="numpy"):
        if first_at is None:
            first_at = time.perf_counter() - t0
        n += len(batch["x"])
        pids.update(batch["pid"].tolist())
    total = time.perf_counter() - t0
    print(f"rows={n} scorer processes={len(pids)} (concurrency=2, eval_gpu=2)")
    print(f"first batch after {first_at:.2f} s, whole stream after {total:.2f} s")
    assert n == rows
    assert len(pids) == 2
    ray.shutdown()
    print("OK data-demo")


if __name__ == "__main__":
    main()
