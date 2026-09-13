#!/usr/bin/env python3
"""smag_feedback_v1_0 — the FEED BACK step of the recursive-learning loop.
Builder v1.7 compliant
HumanAIOS

audits/SMAG_RECURSIVE_LOOP.md names FEED BACK as the one stage left manual:
"gap cues -> lessons_learned_ledger.json + promote hard patterns to
behavioral-compliance.yml / a REGISTERED finding". This tool automates the
first half (a mechanical, idempotent upsert into the lessons ledger) and
prepares the second half as a proposal rather than an action: promoting a
pattern to a blocking gate, or filing a REGISTERED finding, changes what can
merge — that is a Z2 act (CLAUDE.md: PRIORITY_QUEUE.md / REGISTERED.md are
Z2-ratified), not something this tool does unattended.

Reuses tools/smag_gap_analysis_v1_0.py's analyze() directly rather than
re-deriving gap_drivers from the ledger — one definition, not two that
disagree (the same rule Q-TOOLCONTROL-02 applied to the tool scaffolder).

Two honest outcomes, not one:
  - INSUFFICIENT_DATA: fewer than --min-calibration-rows ledger rows carry a
    pinned `smag_p:` prediction. Gap-driver counts under the current
    (post-IC-SMAG-01) VOID rule are computed only over pinned rows, so with
    too few of them a "dominant driver" claim would be noise dressed as
    signal. This is itself the cue worth recording: the instrument isn't
    collecting enough calibration data yet.
  - CUES: enough calibration rows exist, and one or more failing checks
    recur at or above --driver-threshold among them. Each becomes an
    idempotent lesson-ledger entry (upsert by a stable SMAG-<slug> id, not a
    fresh append every run) plus a printed proposal block for a human to file
    as a REGISTERED finding / Priority Queue row if the pattern holds.

Usage:
  python3 smag_feedback_v1_0.py [--ledger audits/smag_pilot_ledger.jsonl]
                                 [--lessons data/lessons_learned_ledger.json]
                                 [--min-calibration-rows 10] [--driver-threshold 3]
                                 [--dry-run]
  python3 smag_feedback_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from smag_gap_analysis_v1_0 import analyze, load_rows

TOOL_NAME = "smag_feedback"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"

DEFAULT_LEDGER = "audits/smag_pilot_ledger.jsonl"
DEFAULT_LESSONS = "data/lessons_learned_ledger.json"
DEFAULT_MIN_CALIBRATION_ROWS = 10
DEFAULT_DRIVER_THRESHOLD = 3

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """A short, stable, readable identifier fragment. Not injective, but
    stable across runs for the same driver name, which is what upsert needs."""
    return _SLUG_RE.sub("-", name.lower()).strip("-")[:40]


def compute_cues(analysis: dict, min_calibration_rows: int, driver_threshold: int) -> dict:
    """The mechanical FEED BACK decision: insufficient data, no drivers yet, or
    named cues. Pure function of analyze()'s own output — no re-derivation."""
    n = analysis["calibration_rows"]
    if n < min_calibration_rows:
        return {
            "status": "INSUFFICIENT_DATA",
            "calibration_rows": n,
            "void_rows": analysis["void_rows"],
            "min_required": min_calibration_rows,
        }
    drivers = analysis.get("gap_drivers", {})
    cues = [
        {"check": name, "n": count, "gap_rate": analysis["overall"].get("gap_rate")}
        for name, count in drivers.items()
        if count >= driver_threshold
    ]
    if not cues:
        return {"status": "NO_DRIVERS", "calibration_rows": n, "gap_rate": analysis["overall"].get("gap_rate")}
    return {"status": "CUES", "calibration_rows": n, "cues": cues}


def lesson_for_insufficient_data(result: dict) -> dict:
    return {
        "id": "SMAG-FEEDBACK-CALIBRATION-STARVED",
        "discovered_in": "smag_feedback_v1_0, automated FEED BACK run",
        "constraint": "gap_driver_claims_require_a_calibration_floor",
        "rule": (
            f"Only {result['calibration_rows']} of the SMAG ledger's rows carry a pinned "
            f"`smag_p:` prediction (below the {result['min_required']}-row floor); "
            f"{result['void_rows']} are VOID. A 'dominant failing check' claim computed "
            "over this few pinned rows would be noise dressed as calibration signal — "
            "do not promote a gap-driver finding to a hard gate or a REGISTERED claim "
            "until calibration_rows clears the floor."
        ),
        "scope_limit": (
            "Resolves once PR authors actually pin `smag_p:` (see "
            ".github/PULL_REQUEST_TEMPLATE.md) at a rate that clears the floor within a "
            "rolling window; re-run this tool to check."
        ),
        "smag_generated": True,
    }


def lesson_for_cue(cue: dict, calibration_rows: int) -> dict:
    slug = slugify(cue["check"])
    return {
        "id": f"SMAG-FEEDBACK-DRIVER-{slug.upper()}",
        "discovered_in": f"smag_feedback_v1_0, automated FEED BACK run ({calibration_rows} calibration rows)",
        "constraint": "recurring_failing_check_on_pinned_prs",
        "rule": (
            f"The check `{cue['check']}` failed on {cue['n']} pinned-prediction PR(s) "
            f"(overall gap_rate {cue['gap_rate']}). Read this as one systemic issue "
            "(a broken or advisory gate merged over), not independent quality misses, per "
            "audits/smag_gap_report.md's own reading rule. Fix or de-advisory the check "
            "before treating its PRs as independent calibration evidence."
        ),
        "scope_limit": (
            "A recurring driver is a proposal for Z2 review (REGISTERED finding / Priority "
            "Queue row), not authorization to make the check blocking — see CLAUDE.md's "
            "governance-files table."
        ),
        "smag_generated": True,
    }


def upsert_lessons(lessons_path: Path, new_lessons: list[dict]) -> list[str]:
    """Idempotent upsert by id. Returns the ids added or updated."""
    if lessons_path.exists():
        ledger = json.loads(lessons_path.read_text(encoding="utf-8"))
    else:
        ledger = {"ledger_version": "1.0", "purpose": "SMAG feedback cues.", "lessons": []}
    by_id = {entry.get("id"): i for i, entry in enumerate(ledger["lessons"])}
    touched = []
    for lesson in new_lessons:
        idx = by_id.get(lesson["id"])
        if idx is None:
            ledger["lessons"].append(lesson)
        else:
            ledger["lessons"][idx] = lesson
        touched.append(lesson["id"])
    lessons_path.parent.mkdir(parents=True, exist_ok=True)
    lessons_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    return touched


def render_report(result: dict) -> str:
    if result["status"] == "INSUFFICIENT_DATA":
        return (
            f"FEED BACK: INSUFFICIENT_DATA — {result['calibration_rows']}/"
            f"{result['calibration_rows'] + result['void_rows']} rows pinned "
            f"(need >= {result['min_required']}). Recorded as a lesson; no gap-driver "
            "claim made."
        )
    if result["status"] == "NO_DRIVERS":
        return (
            f"FEED BACK: NO_DRIVERS — {result['calibration_rows']} calibration rows, "
            f"gap_rate {result['gap_rate']}, no check recurs enough to cue. Nothing to record."
        )
    lines = [f"FEED BACK: CUES — {result['calibration_rows']} calibration rows."]
    for cue in result["cues"]:
        lines.append(f"  - `{cue['check']}` on {cue['n']} PR(s) — propose to Z2 as a REGISTERED finding")
    return "\n".join(lines)


def run(ledger_path: Path, lessons_path: Path, min_calibration_rows: int,
        driver_threshold: int, dry_run: bool = False) -> dict:
    rows = load_rows(ledger_path)
    analysis = analyze(rows)
    result = compute_cues(analysis, min_calibration_rows, driver_threshold)
    if result["status"] == "INSUFFICIENT_DATA":
        lessons = [lesson_for_insufficient_data(result)]
    elif result["status"] == "CUES":
        lessons = [lesson_for_cue(c, result["calibration_rows"]) for c in result["cues"]]
    else:
        lessons = []
    if lessons and not dry_run:
        result["lesson_ids"] = upsert_lessons(lessons_path, lessons)
    elif lessons:
        result["lesson_ids"] = [entry["id"] for entry in lessons]
    return result


def smoke_test() -> int:
    # INSUFFICIENT_DATA: fewer pinned rows than the floor.
    few_rows = [
        {"predicted": "smag_p:0.5", "measured": "merged=True; checks: success:1",
         "timestamp": "2026-01-01T00:00:00Z", "substrate": "x", "failing_checks": []},
    ]
    a = analyze(few_rows)
    r = compute_cues(a, min_calibration_rows=10, driver_threshold=3)
    assert r["status"] == "INSUFFICIENT_DATA", r
    lesson = lesson_for_insufficient_data(r)
    assert lesson["id"] == "SMAG-FEEDBACK-CALIBRATION-STARVED"

    # CUES: enough pinned rows, one check recurs past the threshold.
    many_rows = []
    for i in range(12):
        failing = ["pr-fuzzing (address)"] if i < 4 else []
        checks = "checks: failure:1" if failing else "checks: success:1"
        many_rows.append({
            "predicted": f"smag_p:0.{50 + i % 5}", "measured": f"merged=True; {checks}",
            "timestamp": f"2026-01-{i+1:02d}T00:00:00Z", "substrate": "x",
            "failing_checks": failing,
        })
    a2 = analyze(many_rows)
    r2 = compute_cues(a2, min_calibration_rows=10, driver_threshold=3)
    assert r2["status"] == "CUES", r2
    assert r2["cues"][0]["check"] == "pr-fuzzing (address)"
    assert r2["cues"][0]["n"] == 4

    # NO_DRIVERS: enough rows, nothing recurs past threshold.
    clean_rows = [
        {"predicted": f"smag_p:0.9", "measured": "merged=True; checks: success:1",
         "timestamp": f"2026-01-{i+1:02d}T00:00:00Z", "substrate": "x", "failing_checks": []}
        for i in range(10)
    ]
    a3 = analyze(clean_rows)
    r3 = compute_cues(a3, min_calibration_rows=10, driver_threshold=3)
    assert r3["status"] == "NO_DRIVERS", r3

    # upsert is idempotent: same id updates in place, doesn't duplicate.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "lessons.json"
        ids1 = upsert_lessons(path, [lesson_for_insufficient_data(r)])
        ids2 = upsert_lessons(path, [lesson_for_insufficient_data(r)])
        assert ids1 == ids2 == ["SMAG-FEEDBACK-CALIBRATION-STARVED"]
        data = json.loads(path.read_text())
        assert len(data["lessons"]) == 1, "upsert must not duplicate on re-run"

        # a second, different id appends rather than overwriting the first.
        upsert_lessons(path, [lesson_for_cue(r2["cues"][0], r2["calibration_rows"])])
        data = json.loads(path.read_text())
        assert len(data["lessons"]) == 2

    assert "INSUFFICIENT_DATA" in render_report(r)
    assert "CUES" in render_report(r2)
    assert "NO_DRIVERS" in render_report(r3)
    print("✓ Smoke test PASSED")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="SMAG loop FEED BACK: gap cues -> lessons ledger.")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--lessons", default=DEFAULT_LESSONS)
    ap.add_argument("--min-calibration-rows", type=int, default=DEFAULT_MIN_CALIBRATION_ROWS)
    ap.add_argument("--driver-threshold", type=int, default=DEFAULT_DRIVER_THRESHOLD)
    ap.add_argument("--dry-run", action="store_true", help="report only, do not write the lessons ledger")
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()
    if args.smoke_test:
        return smoke_test()
    result = run(Path(args.ledger), Path(args.lessons), args.min_calibration_rows,
                 args.driver_threshold, dry_run=args.dry_run)
    print(render_report(result))
    if result.get("lesson_ids"):
        verb = "would upsert" if args.dry_run else "upserted"
        print(f"{verb} lesson(s): {', '.join(result['lesson_ids'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
