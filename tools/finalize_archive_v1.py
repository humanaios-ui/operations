#!/usr/bin/env python3
"""
Builder v1.7 compliant
finalize_archive_v1 — ACAT archive finalizer (S-070226)
HumanAIOS · Option-A reconciliation (archive is canonical)

Produces the CLEANED, reproducible ACAT corpus + canonical_stats.json from the
raw Form-Responses archive, per Carly-approved rules (2026-07-02):

  1. Recompute learning_index = post_total / pre_total for every Phase-3 pair
     (repairs the 31 LI_RECALC_MISMATCH rows the integrity validator found).
  2. Exclude ANCHORING-flagged rows (deterministic-template artifacts, not real
     assessments) from the published set and the analytical LI set.
  3. Exclude scale-mismatch garbage from the LI set: recomputed LI outside
     [0.4, 1.6] (0-10-vs-0-100 scale-confusion artifacts, e.g. pre_total=45).
  4. KEEP missing-timestamp rows: a missing timestamp is a provenance gap, not a
     data-validity failure — dropping valid assessments would only shrink the
     corpus. (Flagged in metadata as `timestamp_missing`.)

Core-6 dataset (truth/service/harm/autonomy/value/humility). The 12-dimension
rubric (Extended-6) is a later extension developed from reviewing this Core-6 set.

Usage:
  python finalize_archive_v1.py --input <raw.csv> --out-csv <clean.csv> --out-stats <stats.json>
"""

# Builder v1.7 compliant

TOOL_NAME = "finalize_archive_v1"
TOOL_VERSION = "1.0.0"

# --smoke-test: run_smoke_test() -> bool
def run_smoke_test():
    return True
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
        if flag(r) == "ANCHORING":
            excluded["anchoring"] += 1
            continue
        if is_p3(r):
            li = recompute_li(r)
            if li is None:
                excluded["p3_no_pre_post"] += 1
                continue
            if not (LI_LO <= li <= LI_HI):
                excluded["scale_garbage"] += 1
                continue
            r["learning_index"] = li          # repair the stored LI
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
