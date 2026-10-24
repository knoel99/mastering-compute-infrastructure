from datetime import datetime, timezone
from pathlib import Path

import pytest

import postmortem_lint as pm
import timeline

HERE = Path(__file__).parent
LOG = (HERE / "incident.log").read_text(encoding="utf-8")
GOOD = (HERE / "postmortem_example.md").read_text(encoding="utf-8")
EV = timeline.parse(LOG)


def test_parse_skips_comments_and_reads_utc_times():
    assert len(EV) == 9
    assert EV[0][2] == "INFO" and EV[1][0] == datetime(2026, 3, 14, 2, 11, 40, tzinfo=timezone.utc)


def test_parse_rejects_bad_lines():
    with pytest.raises(ValueError, match="4 fields"):
        timeline.parse("2026-03-14T02:11:40Z|x|ANOMALY")
    with pytest.raises(ValueError, match="unknown kind"):
        timeline.parse("2026-03-14T02:11:40Z|x|WHATEVER|m")
    with pytest.raises(ValueError, match="backwards"):
        timeline.parse("2026-03-14T02:11:40Z|x|INFO|a\n2026-03-14T02:00:00Z|x|INFO|b")


def test_milestones_report_what_is_missing():
    with pytest.raises(ValueError, match="DETECT.*ACK|ACK.*DETECT"):
        timeline.milestones(timeline.parse("2026-03-14T02:11:40Z|x|ANOMALY|m"))


def test_durations_are_hand_checkable():
    d = timeline.durations(EV)
    assert d["ttd"] == 100 * 60          # 02:11:40 -> 03:51:40
    assert d["tta"] == 4 * 60            # 03:51:40 -> 03:55:40
    assert d["ttm"] == 18 * 60           # 03:51:40 -> 04:09:40
    assert d["anomaly_to_mitigation"] == 118 * 60
    assert d["ttr"] == 140 * 60          # 02:11:40 -> 04:31:40


def test_gpu_hours_and_human_format():
    assert timeline.gpu_hours_idle(128, EV) == pytest.approx(128 * 7080 / 3600)
    assert timeline.human(6000) == "1 h 40 min" and timeline.human(240) == "4 min" and timeline.human(7080) == "1 h 58 min"


def test_the_example_postmortem_passes_with_the_log_it_describes():
    assert pm.lint(GOOD, EV, 128) == []


def errs(old, new, **kw):
    assert old in GOOD, old
    return pm.lint(GOOD.replace(old, new, 1), EV, 128)


@pytest.mark.parametrize("title", pm.SECTIONS)
def test_each_missing_section_is_reported(title):
    assert any(f"missing section '## {title}'" in e for e in pm.lint(GOOD.replace(f"## {title}\n", f"## X {title}\n"), EV, 128))


def test_blame_vocabulary_is_flagged_in_the_analysis_sections():
    assert any("blame" in e for e in errs("La perte du GPU de gpu-17 a laissé", "L'ingénieur a oublié de surveiller : la perte du GPU a laissé"))


def test_actions_need_owner_date_and_a_verification():
    assert any("YYYY-MM-DD" in e for e in errs("2026-03-28", "fin mars"))
    assert any("empty field" in e for e in errs("| équipe plateforme | 2026-04-11 |", "|  | 2026-04-11 |"))
    assert any("how success is checked" in e for e in errs("exercice consigné avec un délai de détection mesuré inférieur à 10 minutes", "fait"))
    assert any("Actions needs a table" in e for e in errs("| Action | Propriétaire |", "| Tâche | Propriétaire |"))


def test_durations_written_in_the_text_must_match_the_log():
    assert any("Délai de détection" in e and "log gives" in e for e in errs("Délai de détection : 1 h 40 min", "Délai de détection : 1 h 10 min"))
    assert any("Délai d'acquittement" in e for e in errs("Délai d'acquittement : 4 min", "Délai d'acquittement : 9 min"))
    assert any("must state" in e for e in errs("Délai d'atténuation : 18 min", "Atténuation en 18 minutes"))


def test_the_impact_must_be_quantified_and_consistent_with_the_log():
    assert any("GPU-heures sans progression" in e and "log gives" in e for e in errs("251,7", "300,0"))
    # the dedicated line is required when the log is given...
    assert any("must state 'GPU-heures sans progression" in e for e in errs("GPU-heures sans progression : 251,7", "Perte importante"))
    # ...and an Impact section without figures is refused even without a log
    start = GOOD.index("## Impact")
    end = GOOD.index("## Chronologie")
    vague = GOOD[:start] + "## Impact\n\nPerte importante, quelques heures de travail.\n\n" + GOOD[end:]
    assert any("Impact must quantify" in e for e in pm.lint(vague))


def test_timeline_needs_timestamps_and_markers_are_rejected():
    few = GOOD
    for stamp in ("- 02:12", "- 03:51", "- 03:55", "- 04:03", "- 04:09"):
        few = few.replace(stamp, "- plus tard")
    assert any("Chronologie needs" in e for e in pm.lint(few, EV, 128))
    assert any("unfinished" in e for e in errs("## Leçons\n", "## Leçons\n\nTODO\n"))
