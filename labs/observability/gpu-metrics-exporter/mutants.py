"""Mutation check: break exporter.py in six ways and demand that the tests notice every one.

A test suite that stays green on a broken exporter protects nothing (same idea as the promtool mutants of lab 14.2).
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MUTANTS = [
    ("hot comparison inverted", "sum(t > self.hot_c for t in temps)", "sum(t < self.hot_c for t in temps)"),
    ("empty source counted as success", "if not gpus:", "if False:"),
    ("unbounded reason label", 'REASON_CLASS.get(reason, "other")', "REASON_CLASS.get(reason, reason)"),
    ("wait counted twice", "if jobid in self.seen or", "if False or"),
    ("draining and drained swapped", 'return "draining" if base in', 'return "drained" if base in'),
    ("max instead of min clock", "min(clocks) / med_clock", "max(clocks) / med_clock"),
]


def main():
    survivors = []
    for name, old, new in MUTANTS:
        src = (HERE / "exporter.py").read_text()
        assert src.count(old) == 1, f"mutation target for {name!r} not found exactly once"
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "exporter.py").write_text(src.replace(old, new))
            env = dict(os.environ, MUTANT_DIR=tmp, FIXDIR=str(HERE / "fixtures"), PYTHONDONTWRITEBYTECODE="1")
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider",
                                str(HERE / "tests")], env=env, capture_output=True, text=True, cwd=tmp)
        status = "killed" if r.returncode != 0 else "SURVIVED"
        print(f"  mutant {name:<34} {status}")
        if r.returncode == 0:
            survivors.append(name)
    if survivors:
        print("FAIL: surviving mutants:", survivors)
        return 1
    print(f"OK mutants: {len(MUTANTS)}/{len(MUTANTS)} killed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
