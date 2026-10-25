"""Tests for the fat-tree sizing calculator (pure Python, deterministic)."""
import json
import random
from pathlib import Path

import pytest

import fabric


def test_al_fares_k4_and_k48():
    assert fabric.al_fares(4) == {"hosts": 16, "switches": 20, "core": 4, "pods": 4}
    k48 = fabric.al_fares(48)
    assert k48["hosts"] == 27648  # figure quoted in the SIGCOMM 2008 paper
    assert k48["switches"] == 2880


def test_three_level_matches_al_fares_when_full():
    # radix k, k^3/4 endpoints, non-blocking: 5k^2/4 switches
    for k in (4, 8, 16, 48):
        fab = fabric.size_fabric(k**3 // 4, k, levels=3)
        assert fab.switches == fabric.al_fares(k)["switches"]
        assert fab.oversubscription == pytest.approx(1.0)


def test_capacity_two_and_three_levels():
    assert fabric.capacity(64, 2) == 2048
    assert fabric.capacity(64, 3) == 65536
    with pytest.raises(ValueError):
        fabric.size_fabric(65537, 64)


def test_level_selection():
    assert fabric.size_fabric(64, 64).levels == 1
    assert fabric.size_fabric(65, 64).levels == 2
    assert fabric.size_fabric(2048, 64).levels == 2
    assert fabric.size_fabric(2049, 64).levels == 3


def test_port_budget_is_consistent():
    """Every link uses one port at each end: leaf ports = host links + tier-1 links, and so on."""
    rng = random.Random(7)  # seeded: the property test is reproducible
    for _ in range(200):
        radix = rng.choice([8, 16, 32, 64])
        down = rng.randrange(1, radix)
        cap3 = fabric.capacity(radix, 3, down)
        n = rng.randrange(1, cap3 + 1)
        fab = fabric.size_fabric(n, radix, down)
        if fab.levels == 1:
            continue
        assert fab.leaves * radix >= fab.host_links + fab.tier1_links
        assert fab.spines * radix >= fab.tier1_links + fab.tier2_links
        assert fab.cores * radix >= fab.tier2_links
        assert fab.host_links == n
        assert fab.oversubscription >= 1.0


def test_oversubscription_ratio():
    fab = fabric.size_fabric(2048, 64, leaf_down=48)
    assert fab.leaf_up == 16
    assert fab.oversubscription == pytest.approx(48 / 16, rel=0.02)  # 43 leaves: rounding up lowers it slightly
    full = fabric.size_fabric(2048, 64)
    assert full.bisection_tbps(400) > fab.bisection_tbps(400)
    assert full.switches > fab.switches  # oversubscription saves switches


def test_bisection_full():
    fab = fabric.size_fabric(1024, 64)
    assert fab.bisection_tbps(400) == pytest.approx(1024 / 2 * 0.4)


def test_published_superpod_rows():
    rows = fabric.compare_published()
    assert len(rows) == 8
    mismatches = [r["su"] for r in rows if not r["match"]]
    assert mismatches == [3]  # the only documented difference: spine count kept at 16 for 3 SU
    data = json.loads((Path(fabric.__file__).with_name("published.json")).read_text())
    for row in data["superpod_h100"]["rows"]:
        fab = fabric.size_fabric(row["gpus"], 64)
        assert fab.tier1_links == row["spine_leaf_cables"]


def test_rail_optimized_matches_flat_count():
    # 128 nodes x 8 rails = 1024 endpoints: 8 per-rail fabrics use as many switches as one flat fabric
    rail = fabric.rail_optimized(128, 8, 64)
    flat = fabric.size_fabric(1024, 64)
    assert rail["total_switches"] == flat.switches == 48


def test_effective_bandwidth():
    assert fabric.effective_bandwidth(50, 1, 1.0) == 50
    assert fabric.effective_bandwidth(50, 4, 0.0) == 50
    assert fabric.effective_bandwidth(50, 4, 1.0) == pytest.approx(12.5)
    assert fabric.effective_bandwidth(50, 7, 0.25) == pytest.approx(50 / 2.5)
    with pytest.raises(ValueError):
        fabric.effective_bandwidth(50, 0.5, 0.5)


def test_input_validation():
    with pytest.raises(ValueError):
        fabric.size_fabric(0, 64)
    with pytest.raises(ValueError):
        fabric.size_fabric(10, 7)
    with pytest.raises(ValueError):
        fabric.size_fabric(10, 64, leaf_down=64)


def test_goodput_and_mtu():
    assert fabric.min_ip_mtu(4096) == 4140
    assert fabric.largest_ib_mtu(1500) == 1024
    assert fabric.largest_ib_mtu(9000) == 4096
    assert fabric.largest_ib_mtu(100) == 0
    assert fabric.goodput_fraction(1024) == pytest.approx(0.9259, abs=1e-4)
    assert fabric.goodput_fraction(4096) == pytest.approx(0.9804, abs=1e-4)
    assert fabric.goodput_fraction(256) < fabric.goodput_fraction(4096) < 1
