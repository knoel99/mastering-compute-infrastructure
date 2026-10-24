"""Wall-clock stagnation watcher: the production counterpart of detectors.StepStall."""


class Stagnation:
    """update(now, step) -> True once `step` has not changed for `window_s`. step None (no file yet) never alarms."""

    def __init__(self, window_s):
        self.window_s, self.last, self.changed = window_s, None, None

    def update(self, now, step):
        if step is None:
            return False
        if step != self.last:
            self.last, self.changed = step, now
        return now - self.changed >= self.window_s
