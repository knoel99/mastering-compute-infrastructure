"""Starter admission model: nominal quota only. TO COMPLETE (the tests tell you what is missing).

What works: submit, finish, usage, FIFO admission inside nominal quota.
What you must write, in this order (each step turns more tests green):
  1. borrowing: a queue of a cohort may exceed its nominalQuota up to nominalQuota + borrowingLimit
     (no limit if absent) as long as the cohort has unused quota; lendingLimit keeps
     nominalQuota - lendingLimit for the owner (see _fits);
  2. queueing strategy: StrictFIFO lets only the head of the queue (priority, then creation order) try to be
     admitted; BestEffortFIFO lets the following workloads try (see _candidates);
  3. preemption (see _victims): withinClusterQueue, reclaimWithinCohort, borrowWithinCohort, with the candidate
     order "borrowing queues first, lowest priority, most recently admitted", then minimise the victim list.
The docstring of reference/admission.py lists the rules; read it only after your own attempt.
"""
from __future__ import annotations

from collections import defaultdict

from model import Event, QueueConfig, Workload


class Cluster:
    def __init__(self, queues: dict[str, QueueConfig]):
        self.queues = dict(queues)
        self.workloads: dict[str, Workload] = {}
        self._clock = 0
        self._admit_clock = 0

    def submit(self, wl: Workload) -> None:
        assert wl.name not in self.workloads and wl.queue in self.queues
        wl.created, wl.state, wl.admitted_seq = self._clock, "pending", -1
        self._clock += 1
        self.workloads[wl.name] = wl

    def finish(self, name: str) -> None:
        self.workloads.pop(name)

    def admitted(self, queue: str | None = None) -> list[Workload]:
        return [w for w in self.workloads.values() if w.state == "admitted" and (queue is None or w.queue == queue)]

    def pending(self, queue: str | None = None) -> list[Workload]:
        return [w for w in self.workloads.values() if w.state == "pending" and (queue is None or w.queue == queue)]

    def usage(self, queue: str, skip: frozenset = frozenset()) -> dict:
        u: dict = defaultdict(float)
        for w in self.admitted(queue):
            if w.name not in skip:
                for r, v in w.requests.items():
                    u[r] += v
        return u

    def _fits(self, cfg: QueueConfig, req: dict, skip: frozenset = frozenset(), allow_borrow: bool = True) -> bool:
        # TODO step 1: borrowing and lending. Today: nominal quota only, whatever the cohort says.
        used = self.usage(cfg.name, skip)
        return all(r in cfg.nominal and used[r] + v <= cfg.nominal[r] + 1e-9 for r, v in req.items())

    def _victims(self, wl: Workload) -> list[Workload] | None:
        return None   # TODO step 3: preemption

    def _candidates(self) -> list[Workload]:
        # TODO step 2: StrictFIFO must only offer the head of each queue. Today every pending workload is offered.
        out = []
        for name in self.queues:
            out += sorted(self.pending(name), key=lambda w: (-w.priority, w.created))
        return out

    def schedule(self) -> list[Event]:
        events: list[Event] = []
        progress = True
        while progress:
            progress = False
            for wl in sorted(self._candidates(), key=lambda w: (-w.priority, w.created)):
                if self._fits(self.queues[wl.queue], wl.requests):
                    wl.state, wl.admitted_seq = "admitted", self._admit_clock
                    self._admit_clock += 1
                    events.append(Event("admit", wl.name, wl.queue, "nominal"))
                    progress = True
                    break
        return events
