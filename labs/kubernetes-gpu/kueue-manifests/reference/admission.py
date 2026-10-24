"""Reference admission model: quota, cohort borrowing and lending, Classic Preemption (simplified).

Rules implemented, with the documentation they come from (Kueue v0.20, ClusterQueue CRD and "Preemption" page):
  * a workload is admitted as a whole (all-or-nothing): its requests are compared with the quota, never pod by pod;
  * inside a ClusterQueue, workloads are ordered by priority, then by creation time (queueingStrategy docs);
  * StrictFIFO: an older workload that cannot be admitted blocks the newer ones of the same queue;
    BestEffortFIFO: it does not;
  * a queue may use nominalQuota + borrowingLimit (no limit if absent) as long as the cohort has unused quota;
  * lendingLimit: the queue keeps nominalQuota - lendingLimit for itself, only the rest is lendable;
  * Classic Preemption: a workload that does not fit may evict (a) lower priority workloads of its own queue
    (withinClusterQueue), (b) workloads of other queues that are borrowing, when it fits its own nominal quota
    (reclaimWithinCohort), (c) such workloads even if it must borrow (borrowWithinCohort, with a priority threshold).
    Candidates: borrowing queues first, then lowest priority, then most recently admitted. The victim list is
    then minimised by putting workloads back in reverse order when the preemptor still fits.
Preempted workloads go back to their queue with their original creation order.
"""
from __future__ import annotations

import math
from collections import defaultdict

from model import Event, QueueConfig, Workload

MAX_CYCLES = 10_000   # guard against ping-pong between preemptions


class Cluster:
    def __init__(self, queues: dict[str, QueueConfig]):
        self.queues = dict(queues)
        self.workloads: dict[str, Workload] = {}
        self._clock = 0
        self._admit_clock = 0

    # ---------------------------------------------------------------- bookkeeping
    def submit(self, wl: Workload) -> None:
        assert wl.name not in self.workloads, f"duplicate workload {wl.name}"
        assert wl.queue in self.queues, f"unknown queue {wl.queue}"
        wl.created, wl.state, wl.admitted_seq = self._clock, "pending", -1
        self._clock += 1
        self.workloads[wl.name] = wl

    def finish(self, name: str) -> None:
        """A running or pending workload ends: its quota is released."""
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

    # ---------------------------------------------------------------- quota arithmetic
    def _cohort_members(self, cfg: QueueConfig) -> list[QueueConfig]:
        return [q for q in self.queues.values() if q.cohort and q.cohort == cfg.cohort]

    @staticmethod
    def _guaranteed(cfg: QueueConfig, res: str) -> float:
        """Part of the nominal quota that the queue keeps for itself (nominalQuota - lendingLimit)."""
        lend = cfg.lending_limit.get(res)
        return 0.0 if lend is None else max(0.0, cfg.nominal.get(res, 0.0) - lend)

    def _fits(self, cfg: QueueConfig, req: dict, skip: frozenset = frozenset(), allow_borrow: bool = True) -> bool:
        """Would `req` fit in `cfg`'s queue if the workloads named in `skip` were not running?"""
        for res, amount in req.items():
            if res not in cfg.nominal:
                return False                                   # the queue has no quota for this resource
            mine = self.usage(cfg.name, skip)[res] + amount
            limit = cfg.nominal[res]
            if cfg.cohort and allow_borrow:
                limit += cfg.borrowing_limit.get(res, math.inf)
            if mine > limit + 1e-9:
                return False
            if cfg.cohort:
                members = self._cohort_members(cfg)
                capacity = sum(m.nominal.get(res, 0.0) - self._guaranteed(m, res) for m in members)
                used = sum(max(0.0, (mine if m.name == cfg.name else self.usage(m.name, skip)[res]) - self._guaranteed(m, res))
                           for m in members)
                if used > capacity + 1e-9:
                    return False
        return True

    def _borrowing(self, cfg: QueueConfig, skip: frozenset = frozenset(), only: tuple = ()) -> bool:
        """Is the queue using more than its nominal quota (for at least one of `only`, or any resource)?"""
        u = self.usage(cfg.name, skip)
        return any(u[r] > cfg.nominal.get(r, 0.0) + 1e-9 for r in (only or cfg.nominal))

    # ---------------------------------------------------------------- preemption
    def _victims(self, wl: Workload) -> list[Workload] | None:
        cfg = self.queues[wl.queue]
        req = wl.requests
        own_usage = self.usage(cfg.name)
        within_nominal = all(own_usage[r] + v <= cfg.nominal.get(r, 0.0) + 1e-9 for r, v in req.items())

        def same_queue_ok(v: Workload) -> bool:
            if cfg.within_cq == "LowerPriority":
                return v.priority < wl.priority
            if cfg.within_cq == "LowerOrNewerEqualPriority":
                return v.priority < wl.priority or (v.priority == wl.priority and v.created > wl.created)
            return False

        def other_queue_ok(v: Workload, mode: str) -> bool:
            if mode == "reclaim":
                return cfg.reclaim == "Any" or (cfg.reclaim == "LowerPriority" and v.priority < wl.priority)
            if mode == "borrow":
                ok = cfg.borrow_policy == "LowerPriority" and v.priority < wl.priority
                return ok and (cfg.borrow_threshold is None or v.priority <= cfg.borrow_threshold)
            return False

        modes = []
        if within_nominal and cfg.cohort:
            modes.append(("reclaim", False))     # reclaim the nominal quota: no borrowing allowed for the preemptor
        if cfg.cohort and cfg.borrow_policy != "Never":
            modes.append(("borrow", True))       # preempt while borrowing
        modes.append(("own", True))              # only the preemptor's own queue; borrowing allowed up to the limit
        for mode, allow_borrow in modes:
            targets = self._select(wl, cfg, mode, allow_borrow, same_queue_ok, other_queue_ok)
            if targets:
                return targets
        return None

    def _select(self, wl, cfg, mode, allow_borrow, same_queue_ok, other_queue_ok):
        candidates = [v for v in self.admitted(cfg.name) if same_queue_ok(v)]
        if mode in ("reclaim", "borrow"):
            for m in self._cohort_members(cfg):
                if m.name != cfg.name:
                    candidates += [v for v in self.admitted(m.name) if other_queue_ok(v, mode)]
        # borrowing queues first, then lowest priority, then most recently admitted
        candidates.sort(key=lambda v: (v.queue == cfg.name, v.priority, -v.admitted_seq))
        if not candidates:
            return None
        chosen: list[Workload] = []
        for v in candidates:
            skip = frozenset(c.name for c in chosen)
            if v.queue != cfg.name and not self._borrowing(self.queues[v.queue], skip):
                continue                         # that queue is back at (or under) its nominal quota
            chosen.append(v)
            if self._fits(cfg, wl.requests, frozenset(c.name for c in chosen), allow_borrow):
                break
        else:
            return None
        for v in reversed(list(chosen)):         # minimise: put back whatever is not needed
            rest = frozenset(c.name for c in chosen if c is not v)
            if self._fits(cfg, wl.requests, rest, allow_borrow):
                chosen.remove(v)
        return chosen

    # ---------------------------------------------------------------- scheduling cycle
    def _candidates(self) -> list[Workload]:
        out = []
        for name, cfg in self.queues.items():
            ordered = sorted(self.pending(name), key=lambda w: (-w.priority, w.created))
            out += ordered[:1] if cfg.strategy == "StrictFIFO" else ordered
        return out

    def schedule(self) -> list[Event]:
        """Admit (and preempt for) pending workloads until nothing changes; returns the events in order."""
        events: list[Event] = []
        for _ in range(MAX_CYCLES):
            cands = self._candidates()
            # workloads that fit without borrowing first, then higher priority, then older
            cands.sort(key=lambda w: (self._borrowing_if_admitted(w), -w.priority, w.created))
            for wl in cands:
                cfg = self.queues[wl.queue]
                if self._fits(cfg, wl.requests):
                    events.append(self._admit(wl))
                    break
                victims = self._victims(wl)
                if victims:
                    for v in victims:
                        v.state, v.admitted_seq = "pending", -1
                        scope = "InClusterQueue" if v.queue == wl.queue else "InCohort"
                        events.append(Event("preempt", v.name, v.queue, f"{scope} by {wl.name}"))
                    events.append(self._admit(wl))
                    break
            else:
                return events
        raise RuntimeError("scheduling did not converge: preemption ping-pong")

    def _borrowing_if_admitted(self, wl: Workload) -> bool:
        cfg = self.queues[wl.queue]
        u = self.usage(cfg.name)
        return any(u[r] + v > cfg.nominal.get(r, 0.0) + 1e-9 for r, v in wl.requests.items())

    def _admit(self, wl: Workload) -> Event:
        cfg = self.queues[wl.queue]
        mode = "borrowing" if self._borrowing_if_admitted(wl) else "nominal"
        wl.state, wl.admitted_seq = "admitted", self._admit_clock
        self._admit_clock += 1
        return Event("admit", wl.name, wl.queue, mode)
