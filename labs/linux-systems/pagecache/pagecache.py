#!/usr/bin/env python3
"""What really touches the disk? Dirty pages, resident pages and bytes read from the block device.

Timing is not used as evidence: a hypervisor or a disk controller may cache below the guest and hide the
difference. Three kernel counters are: Dirty in /proc/meminfo, mincore(2) for resident pages of a file,
and sectors read in /proc/diskstats. posix_fadvise(DONTNEED) drops the clean pages of ONE file without root.
"""
import argparse
import ctypes
import json
import mmap
import os
import sys
import tempfile

PAGE = os.sysconf("SC_PAGE_SIZE")
_libc = ctypes.CDLL(None, use_errno=True)
_libc.mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_char_p]


def parse_diskstats(text, name):
    """Bytes read so far by block device `name` (field 6 of /proc/diskstats is sectors read, 512 bytes each)."""
    for line in text.splitlines():
        p = line.split()
        if len(p) > 5 and p[2] == name:
            return int(p[5]) * 512
    raise KeyError(name)


def device_of(path):
    """Name of the block device under `path`, from its major:minor; None for tmpfs/overlayfs (no device)."""
    st = os.stat(path).st_dev
    major, minor = os.major(st), os.minor(st)
    with open("/proc/diskstats") as f:
        for line in f:
            p = line.split()
            if int(p[0]) == major and int(p[1]) == minor:
                return p[2]
    return None


def dirty_kib(meminfo="/proc/meminfo"):
    """System-wide Dirty (KiB), not the dirty pages of one file: other writers on the machine move it too."""
    with open(meminfo) as f:
        return next(int(line.split()[1]) for line in f if line.startswith("Dirty:"))


def resident_bytes(path):
    """Bytes of `path` currently in the page cache, via mincore(2) on a private mapping (no page is faulted in)."""
    size = os.path.getsize(path)
    if size == 0:
        return 0
    with open(path, "rb") as f:
        mm = mmap.mmap(f.fileno(), size, access=mmap.ACCESS_COPY)
        try:
            ref = ctypes.c_char.from_buffer(mm)
            vec = ctypes.create_string_buffer((size + PAGE - 1) // PAGE)
            if _libc.mincore(ctypes.c_void_p(ctypes.addressof(ref)), size, vec) != 0:
                raise OSError(ctypes.get_errno(), os.strerror(ctypes.get_errno()))
            resident = sum(b & 1 for b in vec.raw) * PAGE
            del ref
        finally:
            mm.close()
    return resident


def drop_file_cache(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    finally:
        os.close(fd)


def read_file(path, size, direct=False):
    if direct:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECT)
        buf = mmap.mmap(-1, 1 << 20)  # O_DIRECT needs an aligned buffer; an anonymous mmap is page-aligned
        off = 0
        while off < size:
            n = os.preadv(fd, [buf], off)
            if not n:
                break
            off += n
        os.close(fd)
    else:
        fd = os.open(path, os.O_RDONLY)
        while os.read(fd, 1 << 20):
            pass
        os.close(fd)


def experiment(directory, size_mib=256, device=None):
    """Return a list of stages, each with dirty_kib, resident_mib and device_read_mib since the previous stage."""
    device = device or device_of(directory)
    if device is None:
        raise SystemExit(f"{directory} has no block device behind it (tmpfs or overlayfs?): pass --dir on a disk or --device")
    size = size_mib << 20
    path = os.path.join(directory, "pagecache-lab.dat")
    stages = []

    def stage(name, read_before=None):
        now = parse_diskstats(open("/proc/diskstats").read(), device)
        stages.append({"stage": name, "dirty_kib": dirty_kib(), "resident_mib": round(resident_bytes(path) / (1 << 20)),
                       "device_read_mib": round((now - read_before) / (1 << 20)) if read_before is not None else None})

    def device_read():
        return parse_diskstats(open("/proc/diskstats").read(), device)

    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.write(fd, os.urandom(size))
        stage("after write()")
        os.fsync(fd)
        stage("after fsync()")
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        os.close(fd)
        stage("after DONTNEED")
        b = device_read()
        read_file(path, size)
        stage("cold buffered read", b)
        b = device_read()
        read_file(path, size)
        stage("warm buffered read", b)
        drop_file_cache(path)
        b = device_read()
        read_file(path, size, direct=True)
        stage("O_DIRECT read", b)
    finally:
        if os.path.exists(path):
            os.unlink(path)
    return stages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=tempfile.gettempdir())
    ap.add_argument("--size-mib", type=int, default=256)
    ap.add_argument("--device")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    stages = experiment(a.dir, a.size_mib, a.device)
    if a.json:
        print(json.dumps(stages))
    else:
        print(f"{'stage':<22}{'dirty KiB':>10}{'resident MiB':>14}{'device read MiB':>17}")
        for s in stages:
            print(f"{s['stage']:<22}{s['dirty_kib']:>10}{s['resident_mib']:>14}{str(s['device_read_mib'] if s['device_read_mib'] is not None else '-'):>17}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
