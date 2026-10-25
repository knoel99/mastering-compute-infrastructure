#!/usr/bin/env python3
"""Scenario table for the egress-cost lab. Rates: rates.yaml (read 2026-10-24); volumes and GPU price gaps are inputs.

Usage: python3 scenarios.py [--impl reference|starter]
"""
import argparse
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", default="reference", choices=["reference", "starter"])
    args = ap.parse_args()
    sys.path.insert(0, str(HERE / args.impl))
    E = importlib.import_module("egress")
    R = E.load_rates(HERE / "rates.yaml")
    aws, az, r2e = R["aws_use1_internet_out"], R["azure_westeurope_internet_out"], R["r2_egress"]
    s3, r2s = R["storage"]["aws_s3_standard_use1"], R["storage"]["r2_standard"]

    def eg(card, gb, **kw):
        return E.tiered_cost(gb, card["tiers"], card["free_gb_month"], **kw)

    print(f"rates read on {R['read_on']} (see rates.yaml for sources)")
    print("\n[S1] 150 GB leaving AWS us-east-1 (volume of the dataset in the SkyPilot paper, section 5.1.1)")
    print(f"  free allowance still available : {eg(aws, 150):8.2f} USD")
    print(f"  free allowance already used up : {eg(aws, 150, used_gb=100):8.2f} USD")
    print("[S2] same, dataset 4x larger (600 GB)")
    print(f"  free allowance already used up : {eg(aws, 600, used_gb=100):8.2f} USD")

    print("\n[S3] 50 TB (50 000 GB) AWS S3 -> R2, one month of double storage, 10 Gbit/s link at 80 %")
    m = E.move_cost(50_000, aws, r2s, s3, overlap_months=1.0, gbit_per_s=10, efficiency=0.8)
    print(f"  egress {m['egress']:9.2f}  dst storage {m['dst_storage']:8.2f}  src storage {m['src_storage']:8.2f}"
          f"  TOTAL {m['total']:9.2f} USD  in {m['hours']:.1f} h ({m['days']:.2f} d)")
    gap = 0.50
    print(f"[S3b] if the destination saves {gap} USD per GPU-hour on 64 GPUs: pays back after "
          f"{E.breakeven_gpu_hours(m['total'], 64, gap):.1f} h of use (price gap is an INPUT, not a market price)")

    print("\n[S4] 200 TB (200 000 GB) leaving AWS us-east-1: one month vs split over several months")
    for k in (1, 2, 4):
        c = E.split_cost(200_000, k, aws["tiers"], aws["free_gb_month"])
        print(f"  split over {k} month(s): {c:10.2f} USD   (avg {c / 200_000:.4f} USD/GB)")
    print("[S4b] the same 200 TB leaving Azure westeurope (Routing Preference Internet)")
    print(f"  one month: {eg(az, 200_000):10.2f} USD")
    print(f"[S4c] for reference, the same 200 TB leaving a provider with free egress (R2): {eg(r2e, 200_000):.2f} USD")

    print("\n[S5] copy 150 GB once to R2, or re-read it from AWS at every epoch (same month)")
    copy, remote1, k = E.copy_vs_remote_read(150, 1, aws, r2s)
    print(f"  copy once: {copy:.2f} USD; one remote epoch: {remote1:.2f} USD; copying wins from epoch {k}")
    for n in (10, 90):
        c, r, _ = E.copy_vs_remote_read(150, n, aws, r2s)
        print(f"  {n:3d} epochs: copy {c:8.2f} USD vs remote {r:9.2f} USD")


if __name__ == "__main__":
    main()
