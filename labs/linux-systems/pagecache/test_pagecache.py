import os

import pytest

import pagecache as pc

DISKSTATS = """ 254       0 vda 100 0 2048 10 50 0 4096 20 0 30 40 0 0 0 0
 254      16 vdb 7 0 16 1 0 0 0 0 0 1 1 0 0 0 0
"""


def test_parse_diskstats_reads_sectors_as_512_byte_units():
    assert pc.parse_diskstats(DISKSTATS, "vda") == 2048 * 512
    assert pc.parse_diskstats(DISKSTATS, "vdb") == 16 * 512
    with pytest.raises(KeyError):
        pc.parse_diskstats(DISKSTATS, "nope")


def test_resident_bytes_follows_the_cache_state_of_one_file(tmp_path):
    f = tmp_path / "x.dat"
    size = 8 << 20
    with open(f, "wb") as h:
        h.write(os.urandom(size))
        h.flush()
        os.fsync(h.fileno())
    assert pc.resident_bytes(f) >= 0.9 * size
    pc.drop_file_cache(f)
    assert pc.resident_bytes(f) < 0.1 * size
    pc.read_file(f, size)
    assert pc.resident_bytes(f) >= 0.9 * size


def test_resident_bytes_of_an_empty_file_is_zero(tmp_path):
    f = tmp_path / "e.dat"
    f.write_bytes(b"")
    assert pc.resident_bytes(f) == 0


def test_dirty_kib_is_a_non_negative_integer():
    assert pc.dirty_kib() >= 0
