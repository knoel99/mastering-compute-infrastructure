"""Hang and stall detectors over scrape-level observations (see sim.py for the Obs fields).

Each detector has update(obs) -> bool, True while it would be alarming. Alarm time = first True.
Time is carried by the observations, never by the wall clock, so results are reproducible.
"""


class UtilLow:
    """Naive: GPU utilization below `thr` percent for `window_s`. Sees idle GPUs, is blind to a hang that spins."""
    def __init__(self, window_s, thr=10.0):
        self.window_s, self.thr, self.since = window_s, thr, None

    def update(self, o):
        if o.util < self.thr:
            self.since = o.t if self.since is None else self.since
        else:
            self.since = None
        return self.since is not None and o.t - self.since >= self.window_s


class TensorIdle:
    """Tensor pipe idle for `window_s`: sees a hang, but also every checkpoint and data stall."""
    def __init__(self, window_s, thr=0.05):
        self.window_s, self.thr, self.since = window_s, thr, None

    def update(self, o):
        if o.tensor < self.thr:
            self.since = o.t if self.since is None else self.since
        else:
            self.since = None
        return self.since is not None and o.t - self.since >= self.window_s


class StepStall:
    """No new optimizer step for `window_s`. An absent series (process gone) says nothing: that is a different alert."""
    def __init__(self, window_s):
        self.window_s, self.last, self.changed = window_s, None, None

    def update(self, o):
        if o.steps is None:
            return False
        if self.last is None or o.steps != self.last:
            self.last, self.changed = o.steps, o.t
        return o.t - self.changed >= self.window_s


class Heartbeat:
    """Liveness only: the trainer stops answering for `timeout_s`. Catches crashes, not hangs (the thread still ticks)."""
    def __init__(self, timeout_s):
        self.timeout_s, self.since = timeout_s, None

    def update(self, o):
        if not o.alive:
            self.since = o.t if self.since is None else self.since
        else:
            self.since = None
        return self.since is not None and o.t - self.since >= self.timeout_s


class PhaseAware:
    """Progress stall judged per phase: `train_s` without a step while training, or longer than the phase's allowance
    while the trainer says it is checkpointing / evaluating. The allowances come from YOUR measured pauses."""
    def __init__(self, train_s, allow=None):
        self.train_s, self.allow = train_s, allow or {"ckpt": 600.0, "eval": 900.0}
        self.step = StepStall(train_s)
        self.phase, self.entered = None, None

    def update(self, o):
        if o.phase is None:
            return False
        if o.phase != self.phase:
            self.phase, self.entered = o.phase, o.t
        if o.phase == "train":
            return self.step.update(o)
        self.step.update(o)  # keep the step clock moving so that coming back to `train` starts fresh
        self.step.changed = o.t
        return o.t - self.entered >= self.allow.get(o.phase, self.train_s)


class AnyOf:
    def __init__(self, *ds):
        self.ds = ds

    def update(self, o):
        return any([d.update(o) for d in self.ds])  # evaluate all: detectors keep state
