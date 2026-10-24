import math
import os

import pytest

import capacity
import mmc_sim

REQ = capacity.load(os.path.join(os.path.dirname(__file__), "..", os.environ.get("IMPL", "starter"), "requirements.yaml"))
R = lambda g: {"market": "reserved", "gpus": g}
E = lambda m: {"market": m}


def design(pretrain, finetune, eval_, dev):
    return {"pools": {"pretrain": pretrain, "finetune": finetune, "eval": eval_, "dev": dev}}


C = design(E("spot"), E("on_demand"), E("on_demand"), R(4))


def test_erlang_c_exact_cases():
    assert capacity.erlang_c(2, 1.0) == pytest.approx(1 / 3)
    assert capacity.erlang_c(1, 0.8) == pytest.approx(0.8)  # M/M/1: P(wait) = rho
    assert capacity.erlang_c(3, 3.0) == 1.0  # unstable
    assert capacity.erlang_c(0, 0.5) == 1.0


def test_wait_stats_mm1_closed_forms():
    rho, pw, mean, p90 = capacity.wait_stats(1, 0.5, 1.0)
    assert rho == 0.5 and pw == pytest.approx(0.5)
    assert mean == pytest.approx(1.0)  # rho / (mu - lambda)
    assert p90 == pytest.approx(math.log(5) / 0.5)
    assert capacity.wait_stats(10, 0.5, 1.0)[3] == 0.0  # P(wait) below 10 %: the 90th percentile of the wait is zero
    assert capacity.wait_stats(2, 5.0, 1.0)[2] == math.inf
    assert capacity.wait_stats(2, 2.0, 1.0)[2] == math.inf  # utilisation exactly 1: still unstable


@pytest.mark.parametrize("servers,lam,service", [(4, 3.0, 1.0), (10, 4.0, 2.0)])  # utilisation 0.75 and 0.8
def test_formulas_agree_with_an_independent_simulation(servers, lam, service):
    _, pw, mean, p90 = capacity.wait_stats(servers, lam, service)
    sims = [mmc_sim.simulate(servers, lam, service, n_jobs=300_000, seed=s) for s in range(3)]
    sim_mean = sum(s[0] for s in sims) / 3
    sim_pw = sum(s[1] for s in sims) / 3
    sim_p90 = sum(s[2] for s in sims) / 3
    assert sim_pw == pytest.approx(pw, rel=0.03)
    assert sim_mean == pytest.approx(mean, rel=0.05)
    assert sim_p90 == pytest.approx(p90, rel=0.05)


def test_goodput_closed_form_and_monotonicity():
    rate, c, r = REQ["gpu_failure_rate_per_gpu_hour"], REQ["checkpoint_cost_min"], REQ["restart_cost_min"]
    m = 60.0 / (128 * rate)
    t = math.sqrt(2 * c * m)
    assert capacity.young_daly_goodput(128, rate, c, r) == pytest.approx(1 - (c / t + (t / 2 + r) / m))
    g = [capacity.young_daly_goodput(n, rate, c, r) for n in (1, 8, 32, 128, 512)]
    assert g == sorted(g, reverse=True)
    assert capacity.young_daly_goodput(128, rate, c, r, extra_rate_per_job_hour=0.15) < g[3]
    assert capacity.young_daly_goodput(1024, 1.0, 60, 600) == 0.05  # floored
    assert capacity.young_daly_goodput(1, 0.0, c, r) == 1.0  # no failure at all: nothing is lost, no division by zero


def test_cost_accounting_reserved_versus_elastic():
    out = capacity.evaluate(REQ, C)["classes"]
    assert out["dev"]["cost_u"] == pytest.approx(4 * 730 * REQ["prices_u_per_gpu_hour"]["reserved"])
    assert out["finetune"]["cost_u"] == pytest.approx(out["finetune"]["used_gpu_h"] * REQ["prices_u_per_gpu_hour"]["on_demand"])
    assert out["pretrain"]["cost_u"] == pytest.approx(out["pretrain"]["used_gpu_h"] * REQ["prices_u_per_gpu_hour"]["spot"])
    assert out["pretrain"]["p90_wait_h"] == REQ["provision_wait_h"]
    rate, c, r = REQ["gpu_failure_rate_per_gpu_hour"], REQ["checkpoint_cost_min"], REQ["restart_cost_min"]
    assert out["finetune"]["goodput"] == pytest.approx(capacity.young_daly_goodput(16, rate, c, r))  # on demand: no spot interruptions
    assert out["pretrain"]["goodput"] == pytest.approx(
        capacity.young_daly_goodput(128, rate, c, r, REQ["spot_interruptions_per_job_hour"]))
    odd = capacity.evaluate(REQ, design(E("spot"), R(40), E("on_demand"), R(4)))["classes"]["finetune"]
    assert odd["servers"] == 2 and odd["cost_u"] == pytest.approx(40 * 730 * REQ["prices_u_per_gpu_hour"]["reserved"])  # gangs of 16, paid for all 40 GPU
    spec = REQ["classes"]["pretrain"]
    assert out["pretrain"]["used_gpu_h"] == pytest.approx(
        spec["jobs_per_month"] * spec["gpus_per_job"] * spec["mean_work_hours"] / out["pretrain"]["goodput"])


def test_unstable_reserved_pool_violates_its_slo():
    bad = capacity.evaluate(REQ, design(E("spot"), E("on_demand"), E("on_demand"), R(1)))
    assert not bad["classes"]["dev"]["slo_ok"] and not bad["all_slo_ok"]
    # a failing class that is NOT the last one must fail the design too (here: 5 h to get capacity against a 4 h objective)
    slow = capacity.evaluate(dict(REQ, provision_wait_h=5.0), C)
    assert not slow["classes"]["finetune"]["slo_ok"] and slow["classes"]["dev"]["slo_ok"] and not slow["all_slo_ok"]

    def with_dev_slo(slo):
        classes = {**REQ["classes"], "dev": {**REQ["classes"]["dev"], "slo": slo}}
        return dict(REQ, classes=classes)
    two = design(E("spot"), E("on_demand"), E("on_demand"), R(2))  # dev: mean wait 0.49 h, p90 1.72 h
    assert capacity.evaluate(with_dev_slo({"metric": "mean_wait_h", "max": 1.0}), two)["classes"]["dev"]["slo_ok"]
    assert not capacity.evaluate(with_dev_slo({"metric": "p90_wait_h", "max": 1.0}), two)["classes"]["dev"]["slo_ok"]
    # an objective equal to the provisioning delay is met (<=, not <)
    a = design(E("on_demand"), E("on_demand"), E("on_demand"), E("on_demand"))
    assert capacity.evaluate(with_dev_slo({"metric": "p90_wait_h", "max": REQ["provision_wait_h"]}), a)["classes"]["dev"]["slo_ok"]


def test_candidate_designs_have_the_expected_verdicts():
    res = {name: capacity.evaluate(REQ, d) for name, d in {
        "A": design(E("on_demand"), E("on_demand"), E("on_demand"), E("on_demand")),
        "B": design(R(256), R(32), R(16), R(4)),
        "C": C,
        "D": design(E("on_demand"), E("on_demand"), E("on_demand"), R(4)),
        "J": design(E("spot"), E("on_demand"), E("on_demand"), R(2)),
    }.items()}
    assert res["C"]["cost_u"] == pytest.approx(317161, abs=1) and res["C"]["within_budget"] and res["C"]["all_slo_ok"]
    assert not res["A"]["classes"]["dev"]["slo_ok"]  # 15 minutes of provisioning cannot meet a 5 minute objective
    assert res["B"]["all_slo_ok"] and not res["B"]["within_budget"]
    assert [res["B"]["classes"][k]["servers"] for k in ("pretrain", "finetune", "eval", "dev")] == [2, 2, 2, 4]  # pool // job size
    cost = res["C"]["cost_u"]
    assert capacity.evaluate(dict(REQ, budget_per_month_u=cost * 1.01), C)["within_budget"]
    assert not capacity.evaluate(dict(REQ, budget_per_month_u=cost * 0.99), C)["within_budget"]
    assert res["D"]["all_slo_ok"] and not res["D"]["within_budget"]
    assert not res["J"]["classes"]["dev"]["slo_ok"] and res["J"]["classes"]["dev"]["p90_wait_h"] == pytest.approx(1.72, abs=0.01)


def test_spot_is_cheaper_than_on_demand_until_about_one_interruption_per_job_hour():
    def pretrain_cost(market, extra):
        req = dict(REQ, spot_interruptions_per_job_hour=extra)
        return capacity.evaluate(req, C if market == "spot" else design(E("on_demand"), E("on_demand"), E("on_demand"), R(4)))["classes"]["pretrain"]["cost_u"]
    od = pretrain_cost("on_demand", 0.0)
    assert pretrain_cost("spot", 0.15) < 0.5 * od
    assert pretrain_cost("spot", 0.5) < od < pretrain_cost("spot", 1.5)
