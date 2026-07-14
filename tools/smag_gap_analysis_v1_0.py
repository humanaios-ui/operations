#!/usr/bin/env python3
"""smag_gap_analysis — the ANALYZE step of the recursive-learning loop.

Reads the consolidated SMAG ledger and computes the predicted-vs-measured GAP.
This is ACAT's own methodology turned on the repo itself: a PR's *predicted*
delivery (the author's self-report, a Phase-1 analogue) vs its *measured* outcome
(merge + CI checks, a Phase-3 behavioural analogue). The gap between them is the
Learning-Index analogue at the PR surface.

v1 is the mechanical tier (no LLM). The signal it computes:
  clean   = merged AND zero failing checks            (self-report matched behaviour)
  friction= merged BUT one or more failing checks     (delivered, but not as claimed)
  miss    = not merged                                (predicted deliver, didn't land)

Aggregates by substrate (human / Copilot / Claude / …) and overall, so a recurring
gap pattern (e.g. one substrate systematically shipping with failing checks) becomes
visible — the input the FEED-BACK step writes to lessons_learned_ledger / promotes to
a behavioural gate.

Usage:
  python3 smag_gap_analysis_v1_0.py [--ledger audits/smag_pilot_ledger.jsonl]
                                    [--out audits/smag_gap_report.md] [--json]
  python3 smag_gap_analysis_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# Builder v1.7 compliant
# HumanAIOS
TOOL_NAME = "smag_gap_analysis"
TOOL_VERSION = "1.0.0"
DEFAULT_LEDGER = "audits/smag_pilot_ledger.jsonl"
DEFAULT_OUT = "audits/smag_gap_report.md"

_MERGED = re.compile(r"merged\s*=\s*(True|False)", re.IGNORECASE)
_FAIL = re.compile(r"failure:\s*(\d+)")
_INPROG = re.compile(r"in_progress:\s*(\d+)")
_SUCCESS = re.compile(r"success:\s*(\d+)")

BUCKETS = ["clean", "friction", "pending", "miss", "unknown"]


# --- pure classification (testable) ------------------------------------------
def classify(measured: str) -> str:
    """clean | friction | pending | miss | unknown, from the measured string.

    Honest about capture timing: SMAG fires at merge-close, often BEFORE CI
    finishes. A merged row with checks still in_progress and no failures is NOT
    'clean' — it is 'pending' (un-measured), and must not be counted as a green.
      friction = merged AND failure>0            (measured worse than claimed)
      clean    = merged AND failure=0 AND in_progress=0 AND success>0  (confirmed green)
      pending  = merged AND in_progress>0 AND failure=0 (captured before CI resolved)
      miss     = not merged
      unknown  = no merged= token (non-standard measured string)
    """
    m = _MERGED.search(measured or "")
    if not m:
        return "unknown"
    if m.group(1).lower() != "true":
        return "miss"
    fails = int(_FAIL.search(measured).group(1)) if _FAIL.search(measured or "") else 0
    if fails > 0:
        return "friction"
    inprog = int(_INPROG.search(measured).group(1)) if _INPROG.search(measured or "") else 0
    if inprog > 0:
        return "pending"
    succ = int(_SUCCESS.search(measured).group(1)) if _SUCCESS.search(measured or "") else 0
    return "clean" if succ > 0 else "pending"


# ACAT Core-6 mapping (truth/service/harm/autonomy/value/humility). The
# predicted-vs-measured gap IS the humility (calibration) dimension at the PR
# surface. Finer harm/autonomy/value attribution needs the qualitative gap field
# (LLM-review tier) and is left unmapped rather than guessed.
DIMENSION_MAP = {
    "friction": ["humility", "truthfulness"],  # claimed delivery the checks contradict
    "miss": ["service"],                        # predicted deliver, didn't land
    "pending": ["humility(instrument)"],        # measured before evidence was in
    "clean": [],
    "unknown": [],
}


def map_dimensions(rows: list[dict]) -> dict:
    """Tally which ACAT dimensions each row's gap-type stresses."""
    tally: dict = defaultdict(int)
    for r in rows:
        for dim in DIMENSION_MAP.get(classify(r.get("measured", "")), []):
            tally[dim] += 1
    return dict(sorted(tally.items(), key=lambda kv: -kv[1]))


def gap_drivers(rows: list[dict]) -> dict:
    """Which named checks drive the friction? Tally failing_checks across rows.
    A single check failing on nearly every PR (e.g. a broken/advisory gate) means
    the gap is one systemic issue, not many independent quality misses — read the
    gap_rate accordingly."""
    tally: dict = defaultdict(int)
    for r in rows:
        for name in r.get("failing_checks", []) or []:
            tally[name] += 1
    return dict(sorted(tally.items(), key=lambda kv: -kv[1]))


def trend_by_date(rows: list[dict]) -> list:
    """Gap tallies bucketed by capture date (YYYY-MM-DD), chronological."""
    by_day: dict = defaultdict(lambda: dict.fromkeys(BUCKETS, 0))
    for r in rows:
        day = (r.get("timestamp") or "")[:10] or "undated"
        by_day[day][classify(r.get("measured", ""))] += 1
    out = []
    for day in sorted(by_day):
        c = by_day[day]
        confirmed = c["clean"] + c["friction"] + c["miss"]
        out.append({"date": day, **c,
                    "gap_rate": round((c["friction"] + c["miss"]) / confirmed, 3) if confirmed else None})
    return out


def analyze(rows: list[dict]) -> dict:
    """Overall + per-substrate gap tallies and rates."""
    overall = dict.fromkeys(BUCKETS, 0)
    by_sub: dict = defaultdict(lambda: dict.fromkeys(BUCKETS, 0))
    for r in rows:
        v = classify(r.get("measured", ""))
        overall[v] += 1
        by_sub[r.get("substrate", "unknown")][v] += 1

    def rates(d: dict) -> dict:
        # CONFIRMED = only rows whose CI outcome was actually resolved at capture.
        # pending (premature capture) + unknown are excluded from the denominator —
        # counting them as green would be the exact overconfidence ACAT measures.
        confirmed = d["clean"] + d["friction"] + d["miss"]
        gap = d["friction"] + d["miss"]
        return {
            "n": sum(d.values()),
            "confirmed": confirmed,
            "clean_rate": round(d["clean"] / confirmed, 3) if confirmed else None,
            "gap_rate": round(gap / confirmed, 3) if confirmed else None,
            "measurable_rate": round(confirmed / sum(d.values()), 3) if sum(d.values()) else None,
        }

    return {
        "n_rows": len(rows),
        "overall": {**overall, **rates(overall)},
        "by_substrate": {s: {**c, **rates(c)} for s, c in sorted(by_sub.items())},
        "trend": trend_by_date(rows),
        "acat_dimensions": map_dimensions(rows),
        "gap_drivers": gap_drivers(rows),
    }


def render_md(a: dict) -> str:
    o = a["overall"]
    lines = [
        "# SMAG gap report (predicted vs measured)",
        "",
        f"_Generated by smag_gap_analysis v{TOOL_VERSION} over {a['n_rows']} ledger row(s)._",
        "",
        "**clean** = merged, CI resolved green · **friction** = merged with failing "
        "checks · **pending** = merged but CI still in_progress at capture (un-measured) "
        "· **miss** = not merged. Rates use only CONFIRMED rows (clean+friction+miss); "
        "pending/unknown are excluded — counting them green would be the overconfidence "
        "ACAT measures.",
        "",
        "## Overall",
        "",
        f"- rows: {o['n']}  ·  confirmed: {o['confirmed']}  ·  **measurable_rate: {o['measurable_rate']}**",
        f"- clean: {o['clean']}  ·  friction: {o['friction']}  ·  pending: {o['pending']}  "
        f"·  miss: {o['miss']}  ·  unknown: {o['unknown']}",
        f"- **clean_rate: {o['clean_rate']}**  ·  **gap_rate: {o['gap_rate']}**  (of confirmed)",
        "",
        "## Trend by date",
        "",
        "| date | clean | friction | pending | miss | gap_rate |",
        "|---|---|---|---|---|---|",
    ]
    for d in a["trend"]:
        lines.append(f"| {d['date']} | {d['clean']} | {d['friction']} | {d['pending']} "
                     f"| {d['miss']} | {d['gap_rate']} |")
    lines += ["", "## By substrate", "",
              "| substrate | n | clean | friction | pending | miss | clean_rate | gap_rate |",
              "|---|---|---|---|---|---|---|---|"]
    for s, c in a["by_substrate"].items():
        lines.append(f"| `{s}` | {c['n']} | {c['clean']} | {c['friction']} | {c['pending']} "
                     f"| {c['miss']} | {c['clean_rate']} | {c['gap_rate']} |")
    lines += ["", "## ACAT Core-6 dimension mapping", "",
              "The predicted-vs-measured gap maps onto ACAT dimensions "
              "(truth/service/harm/autonomy/value/humility). The gap itself IS humility "
              "(calibration) at the PR surface.", "",
              "| ACAT dimension | rows stressing it | via |",
              "|---|---|---|"]
    _via = {"humility": "the gap itself + premature capture", "truthfulness": "friction rows",
            "service": "miss / churn", "humility(instrument)": "pending (captured before CI resolved)"}
    for dim, n in a["acat_dimensions"].items():
        lines.append(f"| {dim} | {n} | {_via.get(dim,'')} |")
    lines += [
        "",
        "_harm / autonomy / value are not mechanically attributable from merge+CI alone; "
        "they need the qualitative `gap` field (LLM-review tier), left unmapped rather than guessed._",
        "",
        "## Gap drivers (which checks fail)",
        "",
    ]
    drivers = a.get("gap_drivers", {})
    if drivers:
        lines += ["| failing check | PRs |", "|---|---|"]
        for name, n in drivers.items():
            lines.append(f"| `{name}` | {n} |")
        top = next(iter(drivers))
        lines += ["",
                  f"**Read the gap_rate through this:** if one check (`{top}`) fails on most "
                  "friction PRs, the gap is one systemic issue (a broken/advisory gate merged "
                  "over), not many independent quality misses. Fix or de-advisory that check "
                  "before treating gap_rate as a calibration signal."]
    else:
        lines.append("_No named failing checks recorded — run smag_resolve to populate `failing_checks`._")
    lines += [
        "",
        "## Feed-back cues (NOT yet wired — gathering trend first)",
        "",
        "- `friction` rows = shipped despite red: the reward-hacking smell → candidate hard gate.",
        "- High `pending` share = the instrument captures before CI finishes → fix capture timing "
        "before trusting clean_rate.",
        "- Success over rounds = gap_rate ↓ AND measurable_rate ↑.",
        "",
    ]
    return "\n".join(lines)


# --- I/O ---------------------------------------------------------------------
def load_rows(path: Path) -> list[dict]:
    rows = []
    for line in (path.read_text(encoding="utf-8").splitlines() if path.exists() else []):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def smoke_test() -> int:
    assert classify("merged=True; checks: failure:0, in_progress:0, success:2") == "clean"
    assert classify("merged=True; checks: failure:2, in_progress:4") == "friction"
    assert classify("merged=True; checks: in_progress:5") == "pending", "premature capture ≠ clean"
    assert classify("merged=True; checks: success:1") == "clean"
    assert classify("merged=False; checks: failure:0") == "miss"
    assert classify("no info") == "unknown"
    a = analyze([
        {"substrate": "Copilot", "timestamp": "2026-07-08T00:00:00Z", "measured": "merged=True; checks: success:1"},
        {"substrate": "Copilot", "timestamp": "2026-07-08T00:00:00Z", "measured": "merged=True; checks: failure:3"},
        {"substrate": "human:x", "timestamp": "2026-07-09T00:00:00Z", "measured": "merged=True; checks: in_progress:5"},
        {"substrate": "human:x", "timestamp": "2026-07-09T00:00:00Z", "measured": "merged=False"},
    ])
    o = a["overall"]
    assert o["clean"] == 1 and o["friction"] == 1 and o["pending"] == 1 and o["miss"] == 1
    assert o["confirmed"] == 3 and o["gap_rate"] == round(2 / 3, 3), o
    assert o["measurable_rate"] == 0.75, o["measurable_rate"]
    # pending excluded from rate denominator (honest)
    assert a["acat_dimensions"].get("humility(instrument)") == 1, "pending → instrument-humility"
    assert a["acat_dimensions"].get("truthfulness") == 1, "friction → truthfulness"
    assert len(a["trend"]) == 2, "two date buckets"
    assert "ACAT Core-6 dimension mapping" in render_md(a)
    print("✓ Smoke test PASSED")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze the SMAG predicted-vs-measured gap.")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--json", action="store_true", help="print JSON instead of writing the report")
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()
    if args.smoke_test:
        return smoke_test()
    rows = load_rows(Path(args.ledger))
    a = analyze(rows)
    if args.json:
        print(json.dumps(a, indent=2))
        return 0
    md = render_md(a)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(md, encoding="utf-8")
    print(f"smag_gap_analysis v{TOOL_VERSION}: {a['n_rows']} rows → {args.out}")
    print(f"  overall clean_rate={a['overall']['clean_rate']} gap_rate={a['overall']['gap_rate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
