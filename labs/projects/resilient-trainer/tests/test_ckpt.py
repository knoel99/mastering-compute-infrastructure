import torch

import ckpt


def state(step):
    return {
        "step": step,
        "model": {"w": torch.arange(10.0) + step},
        "opt": {"lr": 0.01, "state": {}},
        "rng_torch": torch.get_rng_state(),
    }


def test_roundtrip(tmp_path):
    ckpt.save(tmp_path, 5, state(5))
    step, st, skipped = ckpt.load_latest(tmp_path)
    assert step == 5 and skipped == []
    assert torch.equal(st["model"]["w"], state(5)["model"]["w"])


def test_optimizer_and_rng_state_are_saved(tmp_path):
    ckpt.save(tmp_path, 5, state(5))
    _, st, _ = ckpt.load_latest(tmp_path)
    assert st["opt"]["lr"] == 0.01
    assert torch.equal(st["rng_torch"], state(5)["rng_torch"])


def test_empty_dir_returns_none(tmp_path):
    assert ckpt.load_latest(tmp_path) == (None, None, [])


def test_no_temporary_file_left(tmp_path):
    ckpt.save(tmp_path, 1, state(1))
    names = sorted(p.name for p in (tmp_path / "ckpt").iterdir())
    assert names == ["ckpt-00000001.pt"]


def test_rotation_keeps_newest(tmp_path):
    for s in range(1, 7):
        ckpt.save(tmp_path, s, state(s), keep=3)
    names = sorted(p.name for p in (tmp_path / "ckpt").iterdir())
    assert names == ["ckpt-00000004.pt", "ckpt-00000005.pt", "ckpt-00000006.pt"]


def test_flipped_byte_falls_back_to_previous(tmp_path):
    ckpt.save(tmp_path, 1, state(1))
    ckpt.save(tmp_path, 2, state(2))
    newest = tmp_path / "ckpt" / "ckpt-00000002.pt"
    blob = bytearray(newest.read_bytes())
    blob[len(blob) // 2] ^= 0xFF
    newest.write_bytes(bytes(blob))
    step, st, skipped = ckpt.load_latest(tmp_path)
    assert step == 1
    assert [name for name, _ in skipped] == ["ckpt-00000002.pt"]


def test_truncated_file_falls_back(tmp_path):
    ckpt.save(tmp_path, 1, state(1))
    ckpt.save(tmp_path, 2, state(2))
    newest = tmp_path / "ckpt" / "ckpt-00000002.pt"
    newest.write_bytes(newest.read_bytes()[:30])
    assert ckpt.load_latest(tmp_path)[0] == 1


def test_stale_tmp_file_is_ignored_and_cleaned(tmp_path):
    ckpt.save(tmp_path, 1, state(1))
    (tmp_path / "ckpt" / "ckpt-00000002.pt.tmp").write_bytes(b"garbage")
    assert ckpt.load_latest(tmp_path)[0] == 1
    ckpt.save(tmp_path, 3, state(3))
    assert not list((tmp_path / "ckpt").glob("*.tmp"))
