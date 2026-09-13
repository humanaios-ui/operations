#!/usr/bin/env python3
"""Recompute the ACAT corpus statistics reported in the reflexive calibration paper.

Companion to docs/REFLEXIVE_CALIBRATION_PAPER_V1_0.md §3.7 and
docs/paper-evidence/EVIDENCE_TABLE.md. Standard library only, no dependencies.

    python3 docs/paper-evidence/recompute_corpus_stats.py

Every figure the paper reports from committed data is produced by this script.
It reads acat/data/acat_corpus_v2.csv and prints the numbers the paper cites.

Caveat carried by the paper and repeated here: this file is NOT the published
629-row archive. It is a 604-row near-neighbour extract. Figures below are a
replication on that extract, not an audit of the canonical corpus.
"""

import csv
import statistics as st
from pathlib import Path

CORE6 = ["truth", "service", "harm", "autonomy", "value", "humility"]
SAFETY = ["service", "harm", "autonomy"]        # safety-training reinforced (F-20)
RISKY = ["humility", "value", "truth"]          # epistemically risky (F-20)

CSV_PATH = Path(__file__).resolve().parents[2] / "acat" / "data" / "acat_corpus_v2.csv"


def num(v):
    """Parse a score cell, returning None for blanks and non-numeric values."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def dimension_means(rows, dims=CORE6):
    """Mean of each dimension over rows where that dimension parses."""
    out = {}
    for d in dims:
        vals = [x for x in (num(r[d]) for r in rows) if x is not None]
        out[d] = (st.mean(vals), len(vals)) if vals else (float("nan"), 0)
    return out


def gradient(rows):
    """F-20 gradient, computed within-row then averaged.

    Per submission: mean(SAFETY) - mean(RISKY). Rows missing any of the six
    dimensions are dropped rather than partially imputed. Returns the mean,
    the normal-approximation 95% interval on its standard error, and t.
    """
    diffs = []
    for r in rows:
        s = [num(r[d]) for d in SAFETY]
        k = [num(r[d]) for d in RISKY]
        if any(v is None for v in s + k):
            continue
        diffs.append(st.mean(s) - st.mean(k))
    n = len(diffs)
    if n < 2:
        return None
    mean = st.mean(diffs)
    se = st.stdev(diffs) / n**0.5
    return {
        "n": n,
        "mean": mean,
        "se": se,
        "ci": (mean - 1.96 * se, mean + 1.96 * se),
        "t": mean / se if se else float("inf"),
    }


def main():
    with CSV_PATH.open(newline="", encoding="utf-8", errors="replace") as fh:
        rows = list(csv.DictReader(fh))

    p1 = [r for r in rows if r["phase"] == "phase1"]
    p3 = [r for r in rows if r["phase"] == "phase3"]
    ai = [r for r in p1 if r["layer"] == "ai-self-report"]
    human = [r for r in rows if r["layer"] == "human-assessment"]

    print(f"source: {CSV_PATH.relative_to(CSV_PATH.parents[2])}")
    print(f"data rows: {len(rows)}   phase1: {len(p1)}   phase3: {len(p3)}\n")

    print("Phase 1 Core 6 means (lowest first)")
    all_m = dimension_means(p1)
    ai_m = dimension_means(ai)
    print(f"  {'dimension':<10} {'all layers':>12} {'AI only':>12}")
    for d, (m, _) in sorted(all_m.items(), key=lambda kv: kv[1][0]):
        print(f"  {d:<10} {m:>12.2f} {ai_m[d][0]:>12.2f}")
    print(f"  (n = {len(p1)} all layers, {len(ai)} AI only)\n")

    p3_hum = [x for x in (num(r["humility"]) for r in p3) if x is not None]
    print(f"Phase 3 Humility mean: {st.mean(p3_hum):.2f} (n = {len(p3_hum)})\n")

    li = [x for x in (num(r["learning_index"]) for r in rows) if x is not None]
    print(f"Learning Index: n = {len(li)}  mean = {st.mean(li):.4f}  "
          f"median = {st.median(li):.4f}\n")

    # F-47: pair-level completion. Compare distinct pair_id sets, not row counts,
    # so a duplicated submission does not inflate either side.
    paired = [r for r in rows if r.get("pair_id", "").strip()]
    p1_ids = {r["pair_id"] for r in paired if r["phase"] == "phase1"}
    p3_ids = {r["pair_id"] for r in paired if r["phase"] == "phase3"}
    unmatched = p1_ids - p3_ids
    print("Pair completion (F-47)")
    print(f"  distinct phase1 pair_id: {len(p1_ids)}   phase3: {len(p3_ids)}")
    print(f"  unmatched phase1: {len(unmatched)}   matched: {len(p1_ids & p3_ids)}")
    print(f"  non-completion rate: {len(unmatched) / len(p1_ids) * 100:.1f}%\n")

    h_li = [x for x in (num(r["learning_index"]) for r in human) if x is not None]
    print("Human baseline")
    print(f"  rows: {len(human)}   with computable LI: {len(h_li)}")
    print(f"  mean LI over rows that have one: {st.mean(h_li):.4f}\n")

    print("F-20 gradient: mean(service, harm, autonomy) - mean(humility, value, truth)")
    for label, subset in (("Phase 1, all layers", p1),
                          ("Phase 1, AI self-report", ai)):
        g = gradient(subset)
        lo, hi = g["ci"]
        print(f"  {label:<26} n={g['n']:<4} {g['mean']:+.3f}  "
              f"95% CI [{lo:+.3f}, {hi:+.3f}]  t={g['t']:.2f}")


if __name__ == "__main__":
    main()
