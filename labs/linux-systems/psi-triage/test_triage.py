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


def test_read_cpu_counts_iowait_as_idle_and_ignores_guest_time(tmp_path):
    (tmp_path / "proc").mkdir()
    #                       user nice system idle iowait irq softirq steal guest guest_nice
    (tmp_path / "proc/stat").write_text("cpu  100 10 50 800 40 5 5 0 70 7\ncpu0 1 1 1 1 1 1 1 1 1 1\n")
    assert triage.read_cpu(str(tmp_path)) == {"busy": 170, "total": 1010}


def test_read_psi_returns_the_cumulative_microsecond_totals(tmp_path):
    (tmp_path / "proc/pressure").mkdir(parents=True)
    (tmp_path / "proc/pressure/cpu").write_text("some avg10=0.00 avg60=0.00 avg300=0.00 total=111\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=0\n")
    (tmp_path / "proc/pressure/memory").write_text("some avg10=0.00 avg60=0.00 avg300=0.00 total=222\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=22\n")
    (tmp_path / "proc/pressure/io").write_text("some avg10=0.00 avg60=0.00 avg300=0.00 total=333\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=33\n")
    psi = triage.read_psi(str(tmp_path))
    assert (psi["cpu_some"], psi["memory_some"], psi["io_some"], psi["io_full"]) == (111, 222, 333, 33)


def test_read_disk_picks_io_ticks_and_weighted_queue_time_by_device_name(tmp_path):
    (tmp_path / "proc").mkdir()
    # fields: major minor name, then 9 counters and in_flight, then io_ticks (ms) and time_in_queue (ms)
    (tmp_path / "proc/diskstats").write_text(
        " 254 0 vda 1 0 2 3 4 0 5 6 0 700 800 0 0 0 0\n 254 16 vdb 1 0 2 3 4 0 5 6 0 1 2 0 0 0 0\n")
    assert triage.read_disk("vda", str(tmp_path)) == {"io_ticks_ms": 700, "queue_ms": 800}
    assert triage.read_disk("vdb", str(tmp_path)) == {"io_ticks_ms": 1, "queue_ms": 2}
