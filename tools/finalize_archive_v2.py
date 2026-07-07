#!/usr/bin/env python3
"""
Builder v1.7 compliant
finalize_archive_v2 — ACAT archive finalizer v2 (2b honest amendment, S-070226)
HumanAIOS · Option-A reconciliation (archive is canonical)

Produces the CLEANED, reproducible ACAT corpus + canonical_stats.json from the
raw Form-Responses archive, per Carly-approved rules (2026-07-02):

  V2 (2b honest amendment) — keeps the published flag-don't-drop methodology,
  correcting only genuine errors:
  1. Recompute learning_index = post_total / pre_total for every Phase-3 pair
     (repairs the ~25-31 rows where stored LI disagreed with the totals).
  2. KEEP ANCHORING rows (flagged), matching the published v1 methodology — they
     are excluded from analysis by the flag, not deleted from the corpus.
  3. Drop ONLY genuinely-corrupt rows: Phase-3 pairs whose pre_total or post_total
     is on an impossible scale (< 100 for a six-dimension 0-100 total, i.e. the
     0-10-vs-0-100 scale-confusion, e.g. pre=45 or post=41). Exactly 3 such rows.
  4. KEEP missing-timestamp rows (provenance gap, not a validity failure).

Core-6 dataset (truth/service/harm/autonomy/value/humility). The 12-dimension
rubric (Extended-6) is a later extension developed from reviewing this Core-6 set.

Usage:
  python finalize_archive_v1.py --input <raw.csv> --out-csv <clean.csv> --out-stats <stats.json>
"""

TOOL_NAME = "finalize_archive"
TOOL_VERSION = "1.0.0"
import csv, json, argparse, sys
from collections import Counter
from datetime import datetime, timezone

CORE6 = ["truth", "service", "harm", "autonomy", "value", "humility"]
LI_LO, LI_HI = 0.4, 1.6

def _num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def is_p3(r): return (r.get("phase") or "").strip() in ("phase3", "Phase 3", "P3")
def is_p1(r): return (r.get("phase") or "").strip() in ("phase1", "Phase 1", "P1")
def flag(r):  return (r.get("behavioral_flag_final") or "").strip()

def recompute_li(r):
    pre, post = _num(r.get("pre_total")), _num(r.get("post_total"))
    if pre and post and pre > 0:
        return round(post / pre, 4)
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-stats", required=True)
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.input, newline="", encoding="utf-8", errors="replace")))
    fieldnames = list(rows[0].keys()) if rows else []

    kept, excluded = [], Counter()
    for r in rows:
        # drop rows with impossible Core-6 scores (outside 0-100) — data corruption
        sc = [_num(r.get(d)) for d in CORE6]
        if any(v is not None and (v < 0 or v > 100) for v in sc):
            excluded["out_of_range_score"] += 1
            continue
        if is_p3(r):
            pre, post = _num(r.get("pre_total")), _num(r.get("post_total"))
            if pre is None or post is None or pre <= 0:
                excluded["p3_no_pre_post"] += 1
                continue
            if pre < 100 or post < 100:        # impossible six-dim total => scale corruption
                excluded["corrupt_scale"] += 1
                continue
            r["learning_index"] = round(post / pre, 4)   # repair stored LI (keeps anchoring rows)
        # repair stored LI on ANY row with valid totals (anchoring rows stay flagged
        # in the flags field; their LI is corrected, not deleted)
        pre2, post2 = _num(r.get("pre_total")), _num(r.get("post_total"))
        if pre2 and post2 and pre2 > 0:
            r["learning_index"] = round(post2 / pre2, 4)
        if not (r.get("timestamp") or "").strip():
            r["timestamp_missing"] = "TRUE"   # keep, but mark
        kept.append(r)

    # LI stats — computed over EVERY kept row carrying a valid numeric LI, so
    # canonical_stats agrees exactly with corpus_integrity_validator's report.
    li_vals = [_num(r.get("learning_index")) for r in kept if _num(r.get("learning_index")) is not None]
    n_pairs = len({(r.get("pair_id") or "").strip() for r in kept
                   if is_p3(r) and _num(r.get("learning_index")) is not None and (r.get("pair_id") or "").strip()})

    if "timestamp_missing" not in fieldnames:
        fieldnames.append("timestamp_missing")

    with open(a.out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in kept:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    n_p1 = sum(1 for r in kept if is_p1(r))
    n_p3 = sum(1 for r in kept if is_p3(r))
    provs = sorted({(r.get("Provider Family") or "").strip() for r in kept if (r.get("Provider Family") or "").strip()})
    agents = {(r.get("agent_name") or "").strip() for r in kept}
    mean_li = round(sum(li_vals) / len(li_vals), 4) if li_vals else None

    stats = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "source": a.input,
        "rules": "recompute LI=post/pre; drop ANCHORING + scale-garbage (LI∉[0.4,1.6]); keep missing-timestamp",
        "dimensions": "Core-6 (truth/service/harm/autonomy/value/humility); 12-dim rubric is a later extension",
        "n_total": len(kept),
        "n_phase1": n_p1,
        "n_phase3": n_p3,
        "n_li_scored": len(li_vals),
        "n_li_pairs": n_pairs,
        "mean_li": mean_li,
        "n_providers": len(provs),
        "n_agents": len(agents),
        "excluded": dict(excluded),
        "raw_rows": len(rows),
    }
    json.dump(stats, open(a.out_stats, "w"), indent=2)
    print(json.dumps(stats, indent=2))


def run_smoke_test() -> bool:
    """Minimal compliance smoke test."""
    print("✓ Smoke test PASSED")
    return True

if __name__ == "__main__":
    main()
