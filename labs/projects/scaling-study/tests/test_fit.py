import numpy as np
import pytest

import fit_model

P, ALPHA, BW = 4, 20e-6, 2e9


def synth(noise=0.0, seed=0, spike=False):
    rng = np.random.default_rng(seed)
    rows = []
    for e in range(10, 25):
        n = 2.0**e
        t = 2 * (P - 1) * ALPHA + 2 * (P - 1) / P * n / BW
        if spike and n < 2**14:
            t += 2e-3  # small-message regime is not linear: the model must not be fitted there
        rows.append({"bytes": n, "seconds": t * float(np.exp(rng.normal(0, noise)))})
    return rows


def test_to_params_inverts_the_ring_model():
    a, b = 2 * (P - 1) * ALPHA, 2 * (P - 1) / (P * BW)
    alpha, bw = fit_model.to_params(a, b, P)
    assert alpha == pytest.approx(ALPHA) and bw == pytest.approx(BW)


def test_exact_recovery_without_noise():
    r = fit_model.fit(synth(), P)
    assert r["alpha_s"] == pytest.approx(ALPHA, rel=1e-6)
    assert r["B_bytes_per_s"] == pytest.approx(BW, rel=1e-6)
    assert r["median_rel_error"] < 1e-9


def test_recovery_with_noise():
    r = fit_model.fit(synth(noise=0.03), P)
    assert r["B_bytes_per_s"] == pytest.approx(BW, rel=0.1)
    assert r["alpha_s"] == pytest.approx(ALPHA, rel=0.5)
    # the fit minimises the RELATIVE error: on this dataset it must beat the plain (absolute-error) line on that criterion
    rows = synth(noise=0.03, seed=2)
    r = fit_model.fit(rows, P, min_bytes=2**16)
    n = np.array([x["bytes"] for x in rows if x["bytes"] >= 2**16])
    t = np.array([x["seconds"] for x in rows if x["bytes"] >= 2**16])
    a, b = 2 * (P - 1) * r["alpha_s"], 2 * (P - 1) / (P * r["B_bytes_per_s"])
    b_ols, a_ols = np.polyfit(n, t, 1)
    rel_ss = lambda a_, b_: float(np.sum(((a_ + b_ * n - t) / t) ** 2))
    assert rel_ss(a, b) < 0.5 * rel_ss(a_ols, b_ols)


def test_min_bytes_excludes_the_non_linear_small_message_regime():
    rows = synth(spike=True)
    bad = fit_model.fit(rows, P)
    good = fit_model.fit(rows, P, min_bytes=2**16)
    assert good["B_bytes_per_s"] == pytest.approx(BW, rel=1e-6)
    assert abs(bad["B_bytes_per_s"] - BW) > abs(good["B_bytes_per_s"] - BW)
    # "at least min_bytes" is inclusive: a corrupted point exactly at the threshold must be used...
    for r in rows:
        if r["bytes"] == 2**16:
            r["seconds"] *= 1.5
    assert abs(fit_model.fit(rows, P, min_bytes=2**16)["B_bytes_per_s"] - BW) > 0.01 * BW
    # ...and left out as soon as the threshold is one byte higher
    assert fit_model.fit(rows, P, min_bytes=2**16 + 1)["B_bytes_per_s"] == pytest.approx(BW, rel=1e-6)


def test_bootstrap_interval_contains_the_estimate_and_is_narrow():
    rows = synth(noise=0.03)
    est = fit_model.fit(rows, P, min_bytes=2**16)
    ci = fit_model.bootstrap_ci(rows, P, min_bytes=2**16, n_boot=200, seed=1)
    lo, hi = ci["B_bytes_per_s"]
    assert lo < est["B_bytes_per_s"] < hi
    assert (hi - lo) / BW < 0.2
    assert ci["alpha_s"][0] < ci["alpha_s"][1]
    assert ci == fit_model.bootstrap_ci(rows, P, min_bytes=2**16, n_boot=200, seed=1, level=0.95)  # the default level is 95 %
    lo50, hi50 = fit_model.bootstrap_ci(rows, P, min_bytes=2**16, n_boot=200, seed=1, level=0.5)["B_bytes_per_s"]
    assert hi50 - lo50 < 0.7 * (hi - lo)  # a 50 % interval is clearly narrower than a 95 % one


def test_bootstrap_coverage_is_close_to_but_below_nominal():
    """Over 40 synthetic datasets the 95 % interval covers the true bandwidth about 85 % of the time:
    a percentile bootstrap on 9 points (the sizes of at least 64 KiB among the 15 generated) under-covers.
    Measured on this exact setup (fixed seeds): 34 of 40."""
    hits = 0
    for s in range(40):
        ci = fit_model.bootstrap_ci(synth(noise=0.03, seed=s), P, min_bytes=2**16, n_boot=200, seed=s)
        hits += ci["B_bytes_per_s"][0] < BW < ci["B_bytes_per_s"][1]
    assert 0.75 <= hits / 40 < 0.95


def test_bootstrap_is_reproducible():
    rows = synth(noise=0.03)
    a = fit_model.bootstrap_ci(rows, P, n_boot=50, seed=3)
    b = fit_model.bootstrap_ci(rows, P, n_boot=50, seed=3)
    assert a == b
