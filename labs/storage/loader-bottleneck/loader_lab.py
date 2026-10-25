"""Lab 8.1: find out whether a training loop is waiting for its data, and why.

SIMULATED parts (labelled on the course page): the dataset's I/O wait is a sleep, its decode cost is a CPU spin,
and the "GPU step" is a sleep. What is REAL: the PyTorch DataLoader (worker processes, queues, prefetching),
the wait time measured around `next()`, the CPU time of the workers (getrusage) and the PyTorch profiler.
"""
from __future__ import annotations

import os
import resource
import warnings
import statistics as st
import time
from dataclasses import dataclass

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset


# PyTorch warns when num_workers exceeds the CPU count. Here the workers mostly sleep (simulated remote reads),
# so oversubscription is harmless and the warning would only add noise to the lab output.
warnings.filterwarnings("ignore", message="This DataLoader will create")


class SyntheticDataset(Dataset):
    """Item i costs `io_s` (sleep: a remote read), then `cpu_s` of CPU (decode), plus rare slow reads.

    Which items are slow depends only on (seed, i): two runs see the same stragglers.
    """

    def __init__(self, n: int, io_s: float, cpu_s: float, slow_frac: float = 0.0, slow_mult: float = 1.0,
                 sample_floats: int = 256, seed: int = 0):
        self.n, self.io_s, self.cpu_s = n, io_s, cpu_s
        self.slow_frac, self.slow_mult = slow_frac, slow_mult
        self.sample_floats, self.seed = sample_floats, seed

    def __len__(self) -> int:
        return self.n

    def is_slow(self, i: int) -> bool:
        return np.random.default_rng((self.seed, i)).random() < self.slow_frac

    def __getitem__(self, i: int):
        io = self.io_s * (self.slow_mult if self.is_slow(i) else 1.0)
        if io > 0:
            time.sleep(io)
        t0 = time.process_time()  # CPU time of this process: it grows in wall time when cores are contended
        while time.process_time() - t0 < self.cpu_s:
            pass
        x = np.random.default_rng((self.seed, i, 1)).standard_normal(self.sample_floats, dtype=np.float32)
        return torch.from_numpy(x), i


@dataclass
class Result:
    workers: int
    prefetch: int | None
    batches: int
    batch_size: int
    wait_s: float
    step_s: float
    wall_s: float
    child_cpu_s: float

    @property
    def stall(self) -> float:
        return self.wait_s / (self.wait_s + self.step_s)

    @property
    def batches_per_s(self) -> float:
        return self.batches / self.wall_s

    @property
    def worker_cpu_util(self) -> float:
        """CPU seconds of the worker processes divided by (workers x wall time); 0 with no worker."""
        return self.child_cpu_s / (self.workers * self.wall_s) if self.workers else 0.0


def _children_cpu() -> float:
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime + r.ru_stime


def _worker_cpu(it) -> float | None:
    """CPU seconds (user + system) used so far by the live worker processes, read from /proc/<pid>/stat.

    Uses the iterator's `_workers` list (a private attribute of PyTorch's multiprocessing iterator); returns
    None if it is not there, and the caller falls back to getrusage(RUSAGE_CHILDREN) after shutdown.
    """
    workers = getattr(it, "_workers", None)
    if not workers:
        return None
    tick, total = os.sysconf("SC_CLK_TCK"), 0.0
    for w in workers:
        try:
            with open(f"/proc/{w.pid}/stat") as f:
                rest = f.read().rsplit(")", 1)[1].split()  # fields after the command name; state is field 3
        except OSError:
            return None
        total += (int(rest[11]) + int(rest[12])) / tick  # fields 14 (utime) and 15 (stime)
    return total


def run(ds: Dataset, workers: int, prefetch: int | None, batch_size: int, step_s: float, n_batches: int,
        warmup: int = 3, persistent: bool = False, in_order: bool = True) -> Result:
    """Consume `n_batches` batches with a simulated GPU step of `step_s` seconds and time the waits.

    `in_order=False` passes DataLoader(in_order=False) (batches may overtake each other; needs a PyTorch that has
    the parameter): it tests whether in-order delivery explains the gap between the model and the measure.
    """
    kw = {"num_workers": workers, "batch_size": batch_size, "shuffle": False, "drop_last": True}
    if workers:
        kw.update(prefetch_factor=prefetch, persistent_workers=persistent)
        if not in_order:
            kw["in_order"] = False
    loader = DataLoader(ds, **kw)
    it = iter(loader)
    for _ in range(warmup):  # start-up (fork, first batches) is not the steady state
        next(it)
        time.sleep(step_s)
    rc0, w0 = _children_cpu(), _worker_cpu(it)
    wait, step = 0.0, 0.0
    t_start = time.perf_counter()
    for _ in range(n_batches):
        t0 = time.perf_counter()
        next(it)
        t1 = time.perf_counter()
        time.sleep(step_s)  # the simulated GPU step
        t2 = time.perf_counter()
        wait += t1 - t0
        step += t2 - t1
    wall = time.perf_counter() - t_start
    w1 = _worker_cpu(it)
    if w0 is not None and w1 is not None:
        child_cpu = w1 - w0  # CPU used by the workers inside the measurement window
    else:
        del it  # shuts the workers down; their CPU time is accounted to RUSAGE_CHILDREN once they are reaped
        time.sleep(0.2)
        child_cpu = _children_cpu() - rc0 if workers else 0.0
    return Result(workers, prefetch if workers else None, n_batches, batch_size, wait, step, wall, child_cpu)


def predict_stall(workers: int, batch_size: int, io_s: float, cpu_s: float, step_s: float, cores: int,
                  slow_frac: float = 0.0, slow_mult: float = 1.0) -> float:
    """First-order model. Per-sample cost c = io*(1 + slow_frac*(slow_mult-1)) + cpu.

    * no worker: loading and the step are serial, stall = B c / (B c + step);
    * W workers: loader rate = min(W / (B c), cores / (B cpu)) batches/s, stall = max(0, 1 - step * rate).
    """
    c = io_s * (1 + slow_frac * (slow_mult - 1)) + cpu_s
    if workers == 0:
        return batch_size * c / (batch_size * c + step_s)
    rate = workers / (batch_size * c)
    if cpu_s > 0:
        rate = min(rate, cores / (batch_size * cpu_s))
    return max(0.0, 1.0 - step_s * rate)


def diagnose(stall: float, worker_cpu_util: float, workers: int, cores: int, threshold: float = 0.05) -> str:
    """The decision table of the lab, as code. Inputs are things you can measure on a real job."""
    if stall < threshold:
        return "GPU-bound: the loader keeps up; do not touch it"
    if workers == 0:
        return "serial loading: set num_workers > 0 first"
    if worker_cpu_util >= 0.7 or workers * worker_cpu_util >= 0.8 * cores:
        return "CPU-bound loader: cheaper transforms, pre-processed data, or more cores per GPU"
    return "latency-bound loader: more workers, deeper prefetch, bigger sequential reads (shards)"


def profile_loader(ds: Dataset, workers: int, batch_size: int, step_s: float, n_batches: int = 12) -> list[dict]:
    """Run the loop under torch.profiler (CPU only) and return the rows that name the DataLoader."""
    from torch.profiler import ProfilerActivity, profile

    loader = DataLoader(ds, num_workers=workers, batch_size=batch_size, drop_last=True,
                        prefetch_factor=2 if workers else None)
    with profile(activities=[ProfilerActivity.CPU]) as prof:
        for k, _ in enumerate(loader):
            time.sleep(step_s)
            if k + 1 >= n_batches:
                break
    rows = []
    for e in prof.key_averages():
        if "DataLoader" in e.key:
            rows.append({"name": e.key, "count": e.count, "cpu_total_ms": e.cpu_time_total / 1e3})
    return rows


def median(xs):
    return st.median(xs)
