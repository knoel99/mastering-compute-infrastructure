#!/usr/bin/env python3
"""Median and 90th-percentile queue wait (Submit -> Start) of the jobs sacct reports for the last 7 days."""
import subprocess
import sys
from datetime import datetime
from statistics import median, quantiles

out = subprocess.run(["sacct", "-X", "-P", "-n", "--format=Submit,Start", "-S", "now-7days"],
                     capture_output=True, text=True, check=True).stdout
waits = []
for line in out.splitlines():
    submit, start = line.split("|")
    if start not in ("Unknown", "None", ""):  # a job that has not started yet has no wait to measure
        waits.append((datetime.fromisoformat(start) - datetime.fromisoformat(submit)).total_seconds())
if len(waits) < 2:
    sys.exit("need at least two started jobs to compute a percentile")
# method="inclusive" never goes beyond the largest observed wait; the default "exclusive" does on small samples
p90 = quantiles(waits, n=10, method="inclusive")[-1]
print(f"jobs: {len(waits)}  median wait: {median(waits):.0f} s  p90: {p90:.0f} s")
