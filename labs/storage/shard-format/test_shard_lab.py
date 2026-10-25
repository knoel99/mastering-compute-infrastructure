"""Tests for shard_lab: layouts hold the same samples, readers agree, counters behave as the model says."""
import random

import pytest

import shard_lab as S

N, SHARDS, ROWS = 64, 4, 16


@pytest.fixture(scope="module")
def ds(tmp_path_factory):
    pytest.importorskip("pyarrow")
    return S.build(str(tmp_path_factory.mktemp("ds")), n=N, shards=SHARDS, rows_per_group=ROWS)


def test_sample_bytes_are_seeded_and_sized():
    assert S.sample_bytes(3) == S.sample_bytes(3) and S.sample_bytes(3) != S.sample_bytes(4)
    assert len(S.sample_bytes(0)) == S.SAMPLE_BYTES
    assert S.sample_bytes(3, seed=1) != S.sample_bytes(3, seed=0)


def test_every_reader_computes_the_same_checksum(ds):
    order = list(range(N))
    expected = 0
    for i in order:
        expected ^= S.digest(i, S.sample_bytes(i))
    for (fmt, pat), fn in S.READERS.items():
        assert fn(ds, order) == expected, (fmt, pat)


def test_random_order_covers_what_it_asks_for(ds):
    order = random.Random(1).sample(range(N), 20)
    expected = 0
    for i in order:
        expected ^= S.digest(i, S.sample_bytes(i))
    for key in [("files", "random"), ("tar shards", "random"), ("packed pread", "random"),
                ("packed mmap", "random"), ("parquet", "random")]:
        assert S.READERS[key](ds, order) == expected, key


def test_tar_index_points_at_payloads(ds):
    assert len(ds.shard_index) == N
    k, off, size = ds.shard_index[10]
    with open(ds.shard_paths[k], "rb") as f:
        f.seek(off)
        assert f.read(size) == S.sample_bytes(10)


def test_shards_are_readable_by_the_real_webdataset_library(ds):
    wds = pytest.importorskip("webdataset")
    got = {}
    for rec in wds.WebDataset(ds.shard_paths, shardshuffle=False):
        got[int(rec["__key__"])] = rec["bin"]
    assert sorted(got) == list(range(N))
    assert all(got[i] == S.sample_bytes(i) for i in range(N))


def test_open_counts_are_exact_and_parquet_amplification_matches_the_row_group(ds):
    order = list(range(N))
    files = S.measure(ds, "files", "sequential", order)
    shards = S.measure(ds, "tar shards", "sequential", order)
    packed = S.measure(ds, "packed pread", "sequential", order)
    assert (files["opens"], shards["opens"], packed["opens"]) == (N, SHARDS, 1)
    assert all(m["checksum_ok"] for m in (files, shards, packed))
    rnd = S.measure(ds, "parquet", "random", random.Random(0).sample(range(N), 8))
    assert rnd["requested_over_payload"] == pytest.approx(ROWS, rel=0.25)  # a whole row group per sample
