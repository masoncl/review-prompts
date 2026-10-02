#!/usr/bin/env python3
"""compare-runs.py - put several build-guides.py runs side by side.

Meant for runs made with --no-sources --check-memory over the same wide set of
questions, one per reader model, all checked by the same model. For each run it
prints the totals, and then for each question how many corrections the checker
made and how much of the from-memory answer it rewrote, so you can see which
questions every reader already answers, which none does, and which depend on
the reader. See "Converting a guide" in kernel/docs/subsystem-questions.md.

Usage:
    compare-runs.py [--weak 40] [--fair 15] label=dir [label=dir ...]
"""

import argparse
import glob
import os
import re
import sys

ROW_RE = re.compile(r"\| `([^`]+)` \| (\d) \| (\d+) \| (\d+) \| (\d+|not checked) \| (\d+)?%? ?\|")


def load(path):
    report = os.path.join(path, "run-report.md")
    with open(report, encoding="utf-8") as f:
        text = f.read()
    rows = {}
    for m in ROW_RE.finditer(text):
        rows[m.group(1)] = (int(m.group(5)) if m.group(5).isdigit() else 0,
                            int(m.group(6) or 0))
    cost = re.search(r"cost: \$([\d.]+)", text)
    versions = []
    for p in glob.glob(os.path.join(path, "answers", "*.first.md")):
        with open(p, encoding="utf-8") as f:
            for line in f:
                m = (re.search(r"v?(\d+)\.(\d+)", line)
                     if line.lower().startswith("kernel assumed") else None)
                if m:
                    versions.append((int(m.group(1)), int(m.group(2))))
    return rows, (cost.group(1) if cost else "?"), sorted(versions)


def main():
    ap = argparse.ArgumentParser(description="Put several build-guides.py runs side by side.")
    ap.add_argument("runs", nargs="+", help="label=directory of a run")
    ap.add_argument("--weak", type=int, default=40,
                    help="a reader is weak on a question rewritten this much or more")
    ap.add_argument("--fair", type=int, default=15,
                    help="a reader is fair on a question rewritten this much or less")
    opts = ap.parse_args()
    runs = {}
    for spec in opts.runs:
        label, _, path = spec.partition("=")
        if not path:
            label, path = os.path.basename(spec.rstrip("/")), spec
        runs[label] = load(path)
    print(f"{'':12s} corrections  rewritten  <={opts.fair}%  >={opts.weak}%  kernel assumed   cost")
    for label, (rows, cost, vers) in runs.items():
        n = max(len(rows), 1)
        span = (f"{vers[0][0]}.{vers[0][1]} to {vers[-1][0]}.{vers[-1][1]}" if vers else "?")
        print(f"{label:12s} {sum(v[0] for v in rows.values()):8d}  "
              f"{sum(v[1] for v in rows.values()) // n:8d}%  "
              f"{sum(1 for v in rows.values() if v[1] <= opts.fair):5d}  "
              f"{sum(1 for v in rows.values() if v[1] >= opts.weak):5d}   {span:14s} ${cost}")
    ids = []
    for rows, _, _ in runs.values():
        ids += [q for q in rows if q not in ids]
    width = max(len(q) for q in ids)
    print()
    print(f"{'question':{width}s}  " + "  ".join(f"{label:>12s}" for label in runs) + "   verdict")
    for q in ids:
        cells, shares = [], []
        for rows, _, _ in runs.values():
            c, r = rows.get(q, (0, 0))
            cells.append(f"{r:3d}% ({c:2d})  ".rjust(14))
            shares.append(r)
        if min(shares) >= opts.weak:
            verdict = "all weak"
        elif max(shares) <= opts.fair:
            verdict = "all fair: drop, or shrink to a pointer"
        else:
            weak = [label for label, r in zip(runs, shares, strict=True) if r >= opts.weak]
            verdict = "weak: " + ", ".join(weak) if weak else "middling"
        print(f"{q:{width}s}  " + "".join(cells) + " " + verdict)
    print("\nRewritten is word-level and counts rewording, so read the corrections in each "
          "run-report.md\nbefore trusting a number. (n) is how many corrections the checker listed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
