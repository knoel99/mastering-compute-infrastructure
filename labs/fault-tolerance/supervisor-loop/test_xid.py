from pathlib import Path

import xid_triage as X

FIX = Path(__file__).resolve().parent / "fixtures" / "kernel_log_sample.txt"


def test_fixture_counts_and_verdict():
    per_gpu, verdict = X.triage(FIX.open())
    assert dict(per_gpu["0000:3b:00"]) == {63: 1, 48: 1, 154: 1, 45: 2}
    assert dict(per_gpu["0000:86:00"]) == {74: 3}
    assert dict(per_gpu["0000:5e:00"]) == {13: 1}
    assert verdict == "drain-node"


def test_user_error_alone_only_restarts_the_job():
    assert X.triage(["NVRM: Xid (0000:5e:00): 13, Graphics Engine Exception"])[1] == "restart-job"


def test_quiet_log_is_a_watch():
    assert X.triage(["kernel: nothing to see", "NVRM: Xid (0000:3b:00): 63, Row remapping event"])[1] == "watch"
