#!/usr/bin/env python3
"""Report generator — TO WRITE (milestone 5).

build(results, fitres, peak_gflops=None) -> (markdown_text, rows). The text must contain the sections
"## Alpha-beta fit", "## Results" (a table with one line per (mode, p) built from analysis.analyze),
"## Definitions" (speedup, efficiency, Karp-Flatt, utilisation with its formula) and
"## Threats to validity" (at least four concrete threats specific to this study).
Runs whose result has "decomposed": true (bench.py --decompose) must be left out of the headline table
and used for an extra "## Communication breakdown" table (pack, wait, all-reduce, ring model prediction,
ratio) followed by a sentence saying that the extra barrier perturbs the step time.
Table rows look like: | strong | 2 | 0.0650 | ... |   (mode, p, step in seconds with 4 decimals).
"""
import sys


def build(results, fitres, peak_gflops=None):
    raise NotImplementedError


def main():
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
