import math
import re
from pathlib import Path

import pytest

import sizing

HERE = Path(__file__).parent
H100 = 989e12  # BF16 dense peak used in the perf-models module


def test_training_flops_is_6_p_d():
    assert sizing.train_flops(70e9, 2e12) == pytest.approx(8.4e23)
    assert sizing.train_flops(1e9, 1e9) == 6e18


def test_training_days_by_hand():
    # 8.4e23 / (256 x 989e12 x 0.4) = 8.294e6 s = 95.99 days
    assert sizing.training_days(70e9, 2e12, 256, H100, 0.40) == pytest.approx(96.0, abs=0.05)
    assert sizing.training_days(70e9, 2e12, 512, H100, 0.40) == pytest.approx(48.0, abs=0.05)  # halving time doubles GPUs
    assert sizing.training_days(70e9, 2e12, 256, H100, 0.35) == pytest.approx(109.7, abs=0.1)


def test_gpus_for_deadline_rounds_up_to_whole_nodes():
    assert sizing.gpus_for_deadline(70e9, 2e12, 100, H100, 0.40) == 248  # exact 245.76
    assert sizing.gpus_for_deadline(70e9, 2e12, 96, H100, 0.40) == 256   # exact 255.99
    assert sizing.nodes(248) == 31 and sizing.nodes(249) == 32
    assert sizing.gpus_for_deadline(7e9, 1e12, 30, H100, 0.40) == 48  # exact 40.96: rounding to the NEAREST node (40) would miss the deadline
    assert sizing.gpus_for_deadline(7e9, 1e12, 30, H100, 0.30) == 56  # exact 54.6


def test_checkpoint_size_and_time():
    assert sizing.checkpoint_bytes(70e9, 14) == pytest.approx(980e9)
    assert sizing.checkpoint_seconds(980e9, 50) == pytest.approx(19.6)
    assert sizing.checkpoint_seconds(980e9, 5) == pytest.approx(196.0)


def test_job_mtbf_and_young_daly():
    assert sizing.job_mtbf_hours(256, 0.0002) == pytest.approx(1 / 0.0512)
    t, g = sizing.young_daly_goodput(ckpt_min=2.0, mtbf_min=1000.0, restart_min=10.0)
    assert t == pytest.approx(math.sqrt(4000)) and g == pytest.approx(1 - (2 / t + (t / 2 + 10) / 1000))


def test_summary_of_the_interview_prompt():
    s = sizing.summary(70e9, 2e12, 256, H100, 0.40, 14, 50, 0.0002, 15)
    assert s["nodes"] == 32 and s["days_ideal"] == pytest.approx(96.0, abs=0.05)
    assert s["checkpoint_gb"] == pytest.approx(980) and s["checkpoint_s"] == pytest.approx(19.6)
    assert s["job_mtbf_h"] == pytest.approx(19.53, abs=0.01)
    assert s["goodput"] == pytest.approx(0.964, abs=0.002)
    assert s["days_with_failures"] == pytest.approx(99.6, abs=0.1)
    assert s["days_with_failures"] < 100 < sizing.training_days(70e9, 2e12, 248, H100, 0.40) / s["goodput"]


def claims(path):
    text = (HERE / "answers" / path).read_text(encoding="utf-8")
    return text, [int(n) for n in re.findall(r"(\d+) jours", text)]


def test_solid_and_excellent_answers_quote_numbers_that_the_calculator_reproduces():
    s = sizing.summary(70e9, 2e12, 256, H100, 0.40, 14, 50, 0.0002, 15)
    fr = lambda x, nd: f"{x:.{nd}f}".replace(".", ",")  # French decimal comma
    for name in ("level2_solid.md", "level3_excellent.md"):
        text, days = claims(name)
        assert 96 in days, name
        for needle in (f"{s['checkpoint_gb']:.0f} Go", fr(s["job_mtbf_h"], 1) + " h", f"{s['ckpt_period_min']:.0f} min",
                       fr(s["days_with_failures"], 1) + " jours", f"{s['nodes']} nœuds"):
            assert needle in text, (name, needle)
    text3, days3 = claims("level3_excellent.md")
    assert 110 in days3  # the sensitivity to an MFU of 0.35
    assert round(sizing.training_days(70e9, 2e12, 256, H100, 0.35)) == 110
    assert f"{sizing.gpus_for_deadline(70e9, 2e12, 100, H100, 0.40)} GPU" in text3  # 248 GPUs on paper


def test_the_insufficient_answer_is_wrong_by_the_calculator_and_says_so_nowhere():
    text, days = claims("level1_insufficient.md")
    assert days and all(abs(d - 96) > 20 for d in days)  # 25 days: the order of magnitude is off by 4x
    assert "hypothèse" not in text.lower()  # it states no assumption: that is part of what the rubric penalises
