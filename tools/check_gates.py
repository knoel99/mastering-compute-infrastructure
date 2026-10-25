#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.gates import check_gates

report = check_gates(Path("."))
for item in report.findings:
    print(f"{item.code.value}\t{item.path}\t{item.message}", file=sys.stderr)
raise SystemExit(0 if report.ok else 1)
