"""Deterministic and structural tests for ckpt_io (no wall-clock thresholds except large-margin orderings)."""
import os

import numpy as np
import pytest

import ckpt_io as c


def test_atomic_failure_leaves_no_partial_final_file(tmp_path):
    path = str(tmp_path / "ckpt.bin")
    state = c.make_state(4 * c.MIB, seed=1)
    with pytest.raises(OSError):
        c.write_atomic(path, state, chunk=c.MIB, fail_after=2 * c.MIB)
    assert not os.path.exists(path), "a failed write must not create the final file"


def test_atomic_failure_keeps_previous_version(tmp_path):
    path = str(tmp_path / "ckpt.bin")
    old, new = c.make_state(c.MIB, seed=1), c.make_state(4 * c.MIB, seed=2)
    c.write_atomic(path, old)
    with pytest.raises(OSError):
        c.write_atomic(path, new, chunk=c.MIB, fail_after=2 * c.MIB)
    assert c.read_back_equal(path, old), "the previous checkpoint must survive a failed overwrite"
    c.write_atomic(path, new)
    assert c.read_back_equal(path, new)


@pytest.mark.parametrize("nbytes", [c.MIB, c.MIB + 123, 3 * c.MIB - 1])
def test_all_modes_round_trip(tmp_path, nbytes):
    state = c.make_state(nbytes, seed=3)
    for name, fn in (("buffered", c.write_buffered), ("atomic", c.write_atomic), ("direct", c.write_direct)):
        path = str(tmp_path / f"{name}.bin")
        fn(path, state)
        assert os.path.getsize(path) == nbytes, name
        assert c.read_back_equal(path, state), name


def _fstype(path: str) -> str:
    best, fstype = "", ""
    with open("/proc/mounts") as f:
        for line in f:
            _, mnt, typ = line.split()[:3]
            if os.path.realpath(path).startswith(mnt.rstrip("/") + "/") or os.path.realpath(path) == mnt:
                if len(mnt) > len(best):
                    best, fstype = mnt, typ
    return fstype


def test_direct_io_rejects_unaligned_writes(tmp_path):
    if _fstype(str(tmp_path)) == "tmpfs":
        pytest.skip("tmpfs is memory: alignment rules are not meaningful there")
    fd = os.open(str(tmp_path / "u.bin"), os.O_WRONLY | os.O_CREAT | os.O_DIRECT, 0o644)
    try:
        with pytest.raises(OSError) as err:
            os.write(fd, b"x" * 1000)
        assert err.value.errno == 22  # EINVAL
    finally:
        os.close(fd)


def test_fit_recovers_parameters_from_noisy_synthetic_times():
    rng = np.random.default_rng(0)
    alpha, bw = 0.01, 400 * c.MIB
    sizes = np.array([8, 16, 32, 64, 128, 256]) * c.MIB
    times = (alpha + sizes / bw) * (1 + 0.03 * rng.standard_normal(len(sizes)))
    a, b = c.fit_alpha_beta(list(sizes), list(times))
    assert b == pytest.approx(bw, rel=0.1)
    assert a == pytest.approx(alpha, abs=0.01)
    assert c.median_rel_error(list(sizes), list(times), a, b) < 0.1


def test_fit_rejects_times_that_do_not_grow():
    with pytest.raises(ValueError):
        c.fit_alpha_beta([1e6, 2e6, 4e6], [0.3, 0.2, 0.1])


def test_second_save_waits_for_the_first_persistence(tmp_path):
    state = c.make_state(2 * c.MIB, seed=4)
    ck = c.AsyncCheckpointer(str(tmp_path), throttle_mbps=20)  # SIMULATED slow storage: 2 MiB take about 100 ms
    ck.prepare(len(state))
    first = ck.save(1, state)
    second = ck.save(2, state)
    ck.wait()
    assert first["wait"] < second["wait"], "nothing was in flight at the first save, one persistence was at the second"
    assert second["wait"] > 0.03, "the second save must wait for the first persistence (one in flight at most)"
    assert sorted(os.listdir(tmp_path)) == ["ckpt-000001.bin", "ckpt-000002.bin"]


def test_persistence_error_is_raised_by_wait(tmp_path):
    state = c.make_state(c.MIB, seed=5)
    ck = c.AsyncCheckpointer(str(tmp_path / "missing-directory"))
    ck.save(1, state)
    with pytest.raises(OSError):
        ck.wait()


def test_async_blocks_less_than_sync_on_slow_storage(tmp_path):
    state = c.make_state(2 * c.MIB, seed=6)
    kw = dict(n_steps=40, step_s=0.01, ckpt_every=20, state=state, directory=str(tmp_path), throttle_mbps=40)
    sync = c.simulate_training(mode="sync", **kw)
    asyn = c.simulate_training(mode="async", **kw)
    assert sync["blocked_s"] > 0.08, "two sync writes of 2 MiB at 40 MiB/s block for about 100 ms in total"
    assert asyn["blocked_s"] < 0.5 * sync["blocked_s"]
