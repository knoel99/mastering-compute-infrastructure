import triage


def snap(t, cpu_busy, cpu_total, cpu_some=0, mem_some=0, io_some=0, ticks=0, queue=0):
    return {"t": t, "cpu": {"busy": cpu_busy, "total": cpu_total},
            "psi": {"cpu_some": cpu_some, "memory_some": mem_some, "io_some": io_some},
            "disk": {"io_ticks_ms": ticks, "queue_ms": queue}}


def test_compute_turns_counters_into_fractions():
    m = triage.compute(snap(0, 0, 0), snap(10, 3600, 4000, cpu_some=8_000_000, io_some=1_000_000, ticks=5000, queue=20000))
    assert m["cpu_util"] == 0.9
    assert m["cpu_psi"] == 0.8 and m["io_psi"] == 0.1 and m["mem_psi"] == 0
    assert m["disk_util"] == 0.5 and m["disk_aqu_sz"] == 2.0


def test_idle_machine_has_no_finding():
    m = triage.compute(snap(0, 0, 0), snap(5, 20, 2000))
    assert triage.classify(m) == []


def test_cpu_saturation_needs_waiting_tasks_not_only_high_utilisation():
    busy_only = {"cpu_util": 0.99, "cpu_psi": 0.0, "mem_psi": 0, "io_psi": 0, "disk_util": 0, "disk_aqu_sz": 0}
    assert triage.classify(busy_only) == ["cpu: busy, but no task is waiting for a core"]
    saturated = dict(busy_only, cpu_psi=0.95)
    assert triage.classify(saturated) == ["cpu: saturated (busy and tasks waiting)"]


def test_memory_pressure_is_reported():
    m = {"cpu_util": 0.1, "cpu_psi": 0, "mem_psi": 0.3, "io_psi": 0, "disk_util": 0.1, "disk_aqu_sz": 0}
    assert triage.classify(m) == ["memory: tasks stall on reclaim or swap"]


def test_psi_blind_spot_is_called_out_when_the_disk_is_busy_without_stalls():
    m = {"cpu_util": 0.4, "cpu_psi": 0.02, "mem_psi": 0, "io_psi": 0.0, "disk_util": 0.94, "disk_aqu_sz": 3.6}
    (finding,) = triage.classify(m)
    assert finding.startswith("disk: busy, but no task stalls")


def test_io_stall_takes_precedence_over_the_blind_spot_message():
    m = {"cpu_util": 0.1, "cpu_psi": 0, "mem_psi": 0, "io_psi": 0.25, "disk_util": 0.9, "disk_aqu_sz": 1}
    assert triage.classify(m) == ["io: tasks are stalled waiting for the disk"]
