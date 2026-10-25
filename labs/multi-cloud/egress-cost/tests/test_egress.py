import math
import random

import pytest

import egress as E
from conftest import RATES

R = E.load_rates(RATES)
AWS = R["aws_use1_internet_out"]
AZ = R["azure_westeurope_internet_out"]
FLAT = [{"upto_gb": None, "usd_per_gb": 0.1}]


def cost(card, gb, **kw):
    return E.tiered_cost(gb, card["tiers"], card["free_gb_month"], **kw)


def test_free_allowance_is_free():
    assert cost(AWS, 0) == 0
    assert cost(AWS, AWS["free_gb_month"]) == 0


def test_first_tier_exact_arithmetic():
    # 1000 GB: 100 GB free, 900 GB at 0.09
    assert cost(AWS, 1000) == pytest.approx(900 * 0.09)


def test_second_tier_exact_arithmetic():
    # 20 000 GB: 100 free; 10 240 at 0.09; the remaining 9 660 at 0.085
    assert cost(AWS, 20000) == pytest.approx(10240 * 0.09 + (20000 - 100 - 10240) * 0.085)


def test_top_tier_exact_arithmetic():
    gb = 200_000
    expected = 10240 * 0.09 + (51200 - 10240) * 0.085 + (153600 - 51200) * 0.07 + (gb - 100 - 153600) * 0.05
    assert cost(AWS, gb) == pytest.approx(expected)


def test_continuous_at_every_breakpoint():
    for card in (AWS, AZ):
        for t in card["tiers"][:-1]:
            x = card["free_gb_month"] + t["upto_gb"]
            assert cost(card, x + 1e-6) - cost(card, x - 1e-6) == pytest.approx(0, abs=1e-5)


def test_monotone_and_marginal_rate_never_increases_after_free_tier():
    xs = [AWS["free_gb_month"] + i * 997 for i in range(0, 400)]
    c = [cost(AWS, x) for x in xs]
    assert all(b >= a for a, b in zip(c, c[1:]))
    slopes = [(c[i + 1] - c[i]) / (xs[i + 1] - xs[i]) for i in range(1, len(c) - 1)]
    assert all(b <= a + 1e-12 for a, b in zip(slopes, slopes[1:]))


def test_used_gb_moves_along_the_tiers():
    # account already billed 100 GB (free allowance used up): the next 1000 GB cost 1000 * 0.09
    assert cost(AWS, 1000, used_gb=100) == pytest.approx(90.0)
    # and the sum of two successive moves equals one move of the sum
    a = cost(AWS, 3000)
    b = cost(AWS, 5000, used_gb=3000)
    assert a + b == pytest.approx(cost(AWS, 8000))


def test_split_over_months_trades_free_allowance_for_tiers():
    small, large = 300, 400_000
    # small volumes: splitting reuses the free allowance each month -> cheaper
    assert E.split_cost(small, 3, AWS["tiers"], AWS["free_gb_month"]) < cost(AWS, small)
    # huge volumes: splitting loses the cheap top tier -> dearer
    assert E.split_cost(large, 4, AWS["tiers"], AWS["free_gb_month"]) > cost(AWS, large)
    assert E.split_cost(large, 1, AWS["tiers"], AWS["free_gb_month"]) == pytest.approx(cost(AWS, large))


def test_split_cost_rejects_zero_months():
    with pytest.raises(ValueError):
        E.split_cost(100, 0, FLAT)


def test_free_egress_card_is_zero():
    assert cost(R["r2_egress"], 1e9) == 0


def test_transfer_hours_exact_and_validated():
    # 100 TB = 100 000 GB over 10 Gbit/s at 80 %: 100000*8/(8)/3600 = 27.78 h
    assert E.transfer_hours(100_000, 10, 0.8) == pytest.approx(100_000 * 8 / 8 / 3600)
    assert E.transfer_hours(0, 10) == 0
    for bad in ((100, 0, 0.8), (100, -1, 0.8), (100, 10, 0), (100, 10, 1.5)):
        with pytest.raises(ValueError):
            E.transfer_hours(*bad)


def test_storage_cost_tiers_and_months():
    s3 = R["storage"]["aws_s3_standard_use1"]["tiers"]
    assert E.storage_cost(1000, s3, 1) == pytest.approx(1000 * 0.023)
    assert E.storage_cost(1000, s3, 3) == pytest.approx(3 * 1000 * 0.023)
    assert E.storage_cost(60_000, s3, 1) == pytest.approx(51200 * 0.023 + (60_000 - 51200) * 0.022)


def test_move_cost_breakdown_adds_up():
    st = R["storage"]
    m = E.move_cost(50_000, AWS, st["r2_standard"], st["aws_s3_standard_use1"], overlap_months=1.0)
    assert m["total"] == pytest.approx(m["egress"] + m["dst_storage"] + m["src_storage"])
    assert m["egress"] == pytest.approx(cost(AWS, 50_000))
    assert m["dst_storage"] == pytest.approx(50_000 * 0.015)
    assert m["src_storage"] == pytest.approx(E.storage_cost(50_000, st["aws_s3_standard_use1"]["tiers"], 1.0))
    assert m["days"] == pytest.approx(m["hours"] / 24)


def test_move_cost_without_source_storage_and_with_split():
    st = R["storage"]
    one = E.move_cost(10_000, AWS, st["r2_standard"])
    assert one["src_storage"] == 0
    two = E.move_cost(10_000, AWS, st["r2_standard"], split_months=2)
    assert two["egress"] == pytest.approx(E.split_cost(10_000, 2, AWS["tiers"], 100))


def test_breakeven_gpu_hours():
    assert E.breakeven_gpu_hours(1000, 8, 0.5) == pytest.approx(250)
    assert E.breakeven_gpu_hours(1000, 8, 0) == math.inf
    assert E.breakeven_gpu_hours(1000, 8, -1) == math.inf


def test_copy_vs_remote_read_breakeven():
    r2 = R["storage"]["r2_standard"]
    copy, remote, k = E.copy_vs_remote_read(150, 1, AWS, r2)
    assert copy == pytest.approx(50 * 0.09 + 150 * 0.015)
    assert remote == pytest.approx(50 * 0.09)
    assert k == 2
    _, remote3, _ = E.copy_vs_remote_read(150, 3, AWS, r2)
    assert remote3 == pytest.approx(cost(AWS, 450))


def test_copy_vs_remote_read_free_egress_never_breaks_even():
    copy, remote, k = E.copy_vs_remote_read(1000, 5, R["r2_egress"], R["storage"]["r2_standard"], max_epochs=50)
    assert remote == 0 and k is None and copy > 0


def test_random_volumes_monotone_in_volume_for_every_card():
    rng = random.Random(7)  # fixed seed: the property must hold for any volume, the sample is just a probe
    for _ in range(200):
        a = rng.uniform(0, 400_000)
        b = a + rng.uniform(0, 50_000)
        for card in (AWS, AZ, R["aws_use1_to_eu_ireland"]):
            assert cost(card, b) >= cost(card, a) - 1e-9
