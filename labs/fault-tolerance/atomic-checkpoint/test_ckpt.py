import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import torch

import ablate
import ckpt
import trainer

HERE = Path(__file__).resolve().parent


def parts(v):
    return {"model": {"w": torch.full((3,), float(v))}, "meta": {"v": v}}


def test_round_trip(tmp_path):
    ckpt.save(tmp_path, 10, parts(1))
    step, got, skipped = ckpt.load_latest(tmp_path)
    assert step == 10 and skipped == [] and got["meta"]["v"] == 1
    assert torch.equal(got["model"]["w"], torch.full((3,), 1.0))


def test_torn_save_is_invisible_and_cleaned(tmp_path):
    ckpt.save(tmp_path, 10, parts(1))
    code = textwrap.dedent(f"""
        import os, sys
        sys.path.insert(0, {str(HERE)!r})
        import ckpt, torch
        def die(name):
            if name == "model":
                os._exit(137)   # killed after the first part is durable, before MANIFEST.json
        ckpt.save({str(tmp_path)!r}, 20, {{"model": {{"w": torch.ones(3)}}, "meta": {{"v": 2}}}}, after_part=die)
    """)
    assert subprocess.run([sys.executable, "-c", code]).returncode == 137
    assert (tmp_path / "step-00000020.tmp").is_dir() and not (tmp_path / "step-00000020").exists()
    step, got, skipped = ckpt.load_latest(tmp_path)
    assert step == 10 and got["meta"]["v"] == 1
    ckpt.save(tmp_path, 30, parts(3))  # the next save removes the leftover
    assert not list(tmp_path.glob("*.tmp"))


def test_flipped_byte_falls_back(tmp_path):
    ckpt.save(tmp_path, 10, parts(1))
    latest = ckpt.save(tmp_path, 20, parts(2))
    f = latest / "model.pt"
    raw = bytearray(f.read_bytes())
    raw[len(raw) // 2] ^= 0x01
    f.write_bytes(bytes(raw))
    step, got, skipped = ckpt.load_latest(tmp_path)
    assert step == 10 and got["meta"]["v"] == 1
    assert skipped == [("step-00000020", "model.pt sha256 mismatch")]


def test_missing_manifest_is_rejected(tmp_path):
    ckpt.save(tmp_path, 10, parts(1))
    latest = ckpt.save(tmp_path, 20, parts(2))
    (latest / "MANIFEST.json").unlink()
    step, _, skipped = ckpt.load_latest(tmp_path)
    assert step == 10 and skipped[0][1] == "no MANIFEST.json"


def test_rotation_keeps_newest(tmp_path):
    for s in (10, 20, 30, 40, 50):
        ckpt.save(tmp_path, s, parts(s), keep=2)
    assert [s for s, _ in ckpt.committed(tmp_path)] == [40, 50]


def test_resume_is_bit_exact(tmp_path):
    r = ablate.experiment([])
    assert r["first_divergent_step"] is None and r["max_abs_loss_diff"] == 0.0 and r["final_digest_equal"]


@pytest.mark.parametrize("omit,first", [("optimizer", 31), ("scheduler", 32), ("rng", 30), ("cursor", 30)])
def test_each_omission_breaks_the_run(omit, first):
    r = ablate.experiment([omit])
    assert r["first_divergent_step"] == first
    assert r["max_abs_loss_diff"] > 0 and not r["final_digest_equal"]


def test_trainer_resumes_from_latest_valid_checkpoint(tmp_path):
    trainer.run(tmp_path, 60, 10, stop_after=35, log=False)
    latest = ckpt.committed(tmp_path / "ckpt")[-1][1]
    (latest / "optim.pt").write_bytes(b"garbage")  # corrupt the newest (step 30)
    tr = trainer.run(tmp_path, 60, 10, log=False)
    assert min(tr.losses) == 20  # fell back to step 20 and replayed from there
    assert (tmp_path / "ckpt" / "step-00000030.corrupt").is_dir()  # evidence kept, name freed
    assert ckpt.verify(tmp_path / "ckpt" / "step-00000030") is None  # and re-saved correctly
