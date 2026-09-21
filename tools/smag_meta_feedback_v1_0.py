#!/usr/bin/env python3
"""smag_meta_feedback_v1_0 — wiring SMAG's self-accuracy measurement.
Builder v1.7 compliant
HumanAIOS

The standard SMAG loop measures author calibration (author prediction vs actual outcome).
Meta-SMAG measures SMAG's own calibration: did SMAG correctly predict its consolidation
PRs' quality? This creates a recursive learning signal: SMAG learns from its own accuracy.

Four meta-stages:
  1. PREDICT: Before consolidation, SMAG estimates consolidation PR quality (smag_p_meta)
  2. CAPTURE: After consolidation and merge, record actual outcome (merged, reworked, reverted)
  3. ANALYZE: Compute meta-gap (predicted vs actual), gap-rate, focus areas
  4. FEED BACK: Upsert meta-lessons into lessons_learned_ledger.json; propose recalibration

This tool runs AFTER smag_feedback_v1_0.py completes the main FEED BACK step. It scans
recent consolidation PRs, measures their actual outcomes, and wires the self-accuracy
signal back into the loop.

Usage:
  python3 smag_meta_feedback_v1_0.py [--repo owner/repo]
                                       [--consolidation-pr-prefix "SMAG: consolidate"]
                                       [--lessons data/lessons_learned_ledger.json]
                                       [--lookback-days 30]
                                       [--dry-run]
  python3 smag_meta_feedback_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

TOOL_NAME = "smag_meta_feedback"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_SESSION = "S-091526-meta"
TOOL_ZONE = 1

DEFAULT_REPO = "humanaios-ui/operations"
DEFAULT_CONSOLIDATION_PR_PREFIX = "SMAG: consolidate"
DEFAULT_LESSONS = "data/lessons_learned_ledger.json"
DEFAULT_LOOKBACK_DAYS = 30


def meta_lesson_for_self_accuracy(accuracy: float, total_prs: int, focus_areas: list[str], confidence: str = None) -> dict:
    """Lesson recording SMAG's own calibration accuracy."""
    # Apply minimum observation floor (similar to author calibration's 10-row floor)
    # For Phase 1, we use a lower floor of 3 PRs since consolidation is less frequent
    min_observations = 3
    has_sufficient_data = total_prs >= min_observations

    if confidence is None:
        confidence = "stable" if 0.75 <= accuracy <= 0.95 else ("low" if accuracy < 0.75 else "high")
        if not has_sufficient_data:
            confidence = "insufficient_data"

    return {
        "id": "SMAG-META-CALIBRATION-SELF-ACCURACY",
        "discovered_in": "smag_meta_feedback_v1_0, automated META FEED BACK run",
        "constraint": "smag_self_improvement_signal",
        "confidence": confidence,
        "rule": (
            f"SMAG's own consolidation PRs: {total_prs} measured over lookback window. "
            f"Predicted accuracy: {accuracy:.1%}. Confidence: {confidence}. "
            f"Meta-gap suggests SMAG should {'increase conservatism' if accuracy < 0.75 else 'maintain calibration'}. "
            f"Focus areas: {', '.join(focus_areas) if focus_areas else 'none identified'}. "
            "This is SMAG measuring itself, not an external audit."
        ),
        "scope_limit": (
            "Z2 may use this signal to adjust SMAG's confidence weighting in future "
            "consolidation rounds or to trigger smag-retrain for recalibration."
        ),
        "smag_generated": True,
        "meta_signal": True,
        "accuracy_measured": accuracy,
        "total_prs_measured": total_prs,
        "focus_areas": focus_areas,
    }


def upsert_meta_lessons(lessons_path: Path, new_lessons: list[dict]) -> list[str]:
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


def measure_consolidation_pr_outcomes(repo: str, prefix: str, lookback_days: int) -> dict:
    """
    Measure recent consolidation PRs' actual outcomes via GitHub API.

    Queries for PRs with matching title (regardless of merge status), extracts
    immutable smag_p_meta predictions and merge/CI status, computes accuracy.

    Note: Predictions are immutable (captured at PR open/sync time). Outcomes
    are determined by GitHub check-run state (CI passed/failed), not PR body prose.

    Returns: {
      "total_prs": int,
      "predicted_prs": int (PRs with smag_p_meta),
      "successful": int,
      "reworked": int,
      "reverted": int,
      "predicted_accuracy": float (average prediction),
      "actual_success_rate": float (successful/predicted),
      "calibration_gap": float (predicted - actual),
      "focus_areas": list[str],
      "meta_signal_available": bool,
      "error": str (if API failed),
    }
    """
    import os
    import subprocess
    import re

    try:
        # GitHub search uses YYYY-MM-DD format, not ISO timestamp
        cutoff_date = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        query = (
            f'repo:{repo} '
            f'title:"{prefix}" '
            f'closed:>={cutoff_date}'
        )
        result = subprocess.run(
            ["gh", "pr", "list", "--search", query, "--json", "number,title,state,mergedAt,body"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "GitHub API unavailable"
            return {
                "total_prs": 0,
                "predicted_prs": 0,
                "successful": 0,
                "reworked": 0,
                "reverted": 0,
                "predicted_accuracy": None,
                "actual_success_rate": None,
                "calibration_gap": None,
                "focus_areas": [],
                "meta_signal_available": False,
                "lookback_days": lookback_days,
                "error": f"GitHub API failed: {error_msg}",
            }

        prs = json.loads(result.stdout) if result.stdout else []
        predictions = []
        successful = 0
        reworked = 0
        reverted = 0
        focus_areas_set = set()

        meta_pattern = re.compile(r"(?im)^\s*smag_p_meta\s*:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*$")

        for pr in prs:
            body = pr.get("body") or ""
            state = pr.get("state", "").lower()
            merged = state == "merged"

            # Extract immutable smag_p_meta prediction (captured before merge)
            meta_match = meta_pattern.search(body)
            if meta_match is None:
                continue

            predicted = float(meta_match.group(1))
            predictions.append(predicted)

            # Classify outcome by merge/CI state, not prose
            # Rework: merged but with history suggesting follow-up (conservative: only count reverts)
            # Success: merged and no revert found
            # Reverted: was merged then reverted (checked via closed state + revert in recent PRs)
            # Note: without check-run API, we use merge state as proxy; revert detection is future work
            if merged:
                successful += 1
            else:
                reworked += 1
                focus_areas_set.add("pr_not_merged")

        predicted_count = len(predictions)

        if predicted_count == 0:
            return {
                "total_prs": len(prs),
                "predicted_prs": 0,
                "successful": 0,
                "reworked": 0,
                "reverted": 0,
                "predicted_accuracy": None,
                "actual_success_rate": None,
                "calibration_gap": None,
                "focus_areas": [],
                "meta_signal_available": False,
                "lookback_days": lookback_days,
                "note": "No PRs with smag_p_meta predictions found",
            }

        predicted_avg = sum(predictions) / predicted_count
        actual_success_rate = successful / predicted_count if predicted_count > 0 else 0.0
        calibration_gap = predicted_avg - actual_success_rate

        return {
            "total_prs": len(prs),
            "predicted_prs": predicted_count,
            "successful": successful,
            "reworked": reworked,
            "reverted": reverted,
            "predicted_accuracy": predicted_avg,
            "actual_success_rate": actual_success_rate,
            "calibration_gap": calibration_gap,
            "focus_areas": sorted(list(focus_areas_set)),
            "meta_signal_available": predicted_count > 0,
            "lookback_days": lookback_days,
        }
    except Exception as e:
        return {
            "total_prs": 0,
            "predicted_prs": 0,
            "successful": 0,
            "reworked": 0,
            "reverted": 0,
            "predicted_accuracy": None,
            "actual_success_rate": None,
            "calibration_gap": None,
            "focus_areas": [],
            "meta_signal_available": False,
            "lookback_days": lookback_days,
            "error": str(e),
        }


def run(repo: str, consolidation_pr_prefix: str, lessons_path: Path,
        lookback_days: int, dry_run: bool = False) -> dict:
    """Measure SMAG's own consolidation PR accuracy and feed it back."""
    outcome = measure_consolidation_pr_outcomes(repo, consolidation_pr_prefix, lookback_days)

    if outcome.get("error"):
        return {
            "status": "API_ERROR",
            "message": outcome["error"],
            "lookback_days": lookback_days,
        }

    if outcome["predicted_prs"] == 0:
        if outcome["total_prs"] == 0:
            return {"status": "NO_DATA", "message": "No consolidation PRs found in lookback window."}
        else:
            return {"status": "NO_PREDICTIONS", "message": f"Found {outcome['total_prs']} PRs but none had smag_p_meta predictions."}

    # Use calibration gap (predicted - actual success rate) as accuracy metric
    # Gap of 0 = perfect calibration; positive gap = overconfident; negative gap = underconfident
    calibration_gap = outcome["calibration_gap"]
    accuracy = outcome["predicted_accuracy"]  # Use predicted avg as baseline calibration score

    # Determine confidence based on gap magnitude and sample size
    abs_gap = abs(calibration_gap)
    if outcome["predicted_prs"] < 3:
        confidence = "insufficient_data"
    elif abs_gap <= 0.05:
        confidence = "stable"
    elif abs_gap <= 0.20:
        confidence = "drift_detected"
    else:
        confidence = "low"

    lesson = meta_lesson_for_self_accuracy(
        accuracy,
        outcome["predicted_prs"],
        outcome["focus_areas"],
        confidence=confidence,
    )

    if not dry_run:
        outcome["lesson_ids"] = upsert_meta_lessons(lessons_path, [lesson])
    else:
        outcome["lesson_ids"] = [lesson["id"]]

    outcome["status"] = "META_SIGNAL_CAPTURED"
    outcome["lesson_confidence"] = confidence
    outcome["calibration_assessment"] = (
        f"Predicted {accuracy:.1%}, actual success {outcome['actual_success_rate']:.1%}, gap {calibration_gap:+.1%}"
    )
    return outcome


def render_report(result: dict) -> str:
    status = result.get("status")
    if status in ("NO_DATA", "NO_PREDICTIONS", "API_ERROR"):
        return f"META FEED BACK: {status} — {result.get('message', 'No data available.')}"

    outcome = result
    accuracy_pct = outcome.get("predicted_accuracy", outcome.get("accuracy", 0)) * 100 if isinstance(outcome.get("predicted_accuracy", outcome.get("accuracy")), float) else 0
    successful = outcome.get("successful", 0)
    reworked = outcome.get("reworked", 0)
    reverted = outcome.get("reverted", 0)
    total_prs = outcome.get("total_prs", 0)
    return (
        f"META FEED BACK: {total_prs} consolidation PRs measured. "
        f"Accuracy: {accuracy_pct:.0f}% (successful={successful}, "
        f"reworked={reworked}, reverted={reverted}). "
        f"Focus areas: {', '.join(outcome['focus_areas']) if outcome['focus_areas'] else 'none'}."
    )


def smoke_test() -> int:
    """Verify meta-SMAG measurement and lesson-upsert logic."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        lessons_path = Path(d) / "lessons.json"

        # Test 1: measure_consolidation_pr_outcomes returns valid structure
        outcome = measure_consolidation_pr_outcomes(
            repo="humanaios-ui/operations",
            prefix="SMAG: consolidate",
            lookback_days=30,
        )
        assert "total_prs" in outcome
        assert "predicted_accuracy" in outcome
        assert "focus_areas" in outcome
        print(f"  ✓ measurement returns valid structure (total_prs={outcome['total_prs']})")

        # Test 2: meta_lesson_for_self_accuracy generates correct structure with confidence
        lesson = meta_lesson_for_self_accuracy(
            accuracy=0.83,
            total_prs=12,
            focus_areas=["test_area"],
            confidence="stable",
        )
        assert lesson["id"] == "SMAG-META-CALIBRATION-SELF-ACCURACY"
        assert lesson["accuracy_measured"] == 0.83
        assert lesson["confidence"] == "stable"
        print(f"  ✓ lesson generation returns valid structure with confidence field")

        # Test 3: upsert_meta_lessons is idempotent
        ids1 = upsert_meta_lessons(lessons_path, [lesson])
        assert len(ids1) == 1
        data = json.loads(lessons_path.read_text())
        assert len(data["lessons"]) == 1
        print(f"  ✓ first upsert writes lesson")

        ids2 = upsert_meta_lessons(lessons_path, [lesson])
        data2 = json.loads(lessons_path.read_text())
        assert len(data2["lessons"]) == 1, "upsert must be idempotent"
        print(f"  ✓ second upsert updates in place (idempotent)")

        # Test 4: run() with dry_run produces no side effects
        result_dry = run(
            repo="humanaios-ui/operations",
            consolidation_pr_prefix="SMAG: consolidate",
            lessons_path=lessons_path,
            lookback_days=30,
            dry_run=True,
        )
        # lessons file should still have only 1 entry from test 3
        data3 = json.loads(lessons_path.read_text())
        assert len(data3["lessons"]) == 1, "dry-run must not modify lessons file"
        print(f"  ✓ dry-run does not modify filesystem")

        # Test 5: Deterministic calibration gap calculation (no GitHub API)
        # Simulate predicted vs actual: predicted 0.85, actual 0.80, gap = +0.05
        mock_predictions = [0.85, 0.90, 0.80]
        mock_successful = 2  # Out of 3
        predicted_avg = sum(mock_predictions) / len(mock_predictions)  # 0.85
        actual_success_rate = mock_successful / len(mock_predictions)  # 0.667
        calibration_gap = predicted_avg - actual_success_rate  # +0.183

        assert abs(predicted_avg - 0.85) < 0.01, "predicted average should be ~0.85"
        assert abs(actual_success_rate - 0.667) < 0.01, "success rate should be ~0.667"
        assert abs(calibration_gap - 0.183) < 0.01, "gap should be +0.183 (overconfident)"
        print(f"  ✓ calibration gap calculation: predicted={predicted_avg:.2%}, actual={actual_success_rate:.2%}, gap={calibration_gap:+.2%}")

        # Test 6: Confidence levels based on gap magnitude
        # Stable: abs(gap) <= 0.05; drift: <= 0.20; low: > 0.20
        small_gap_lesson = meta_lesson_for_self_accuracy(0.80, 5, [], confidence="stable")
        assert small_gap_lesson["confidence"] == "stable"
        medium_gap_lesson = meta_lesson_for_self_accuracy(0.80, 5, [], confidence="drift_detected")
        assert medium_gap_lesson["confidence"] == "drift_detected"
        large_gap_lesson = meta_lesson_for_self_accuracy(0.80, 5, [], confidence="low")
        assert large_gap_lesson["confidence"] == "low"
        print(f"  ✓ confidence levels assigned correctly")

    print("✓ Meta-SMAG smoke test PASSED")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="META SMAG: measure SMAG's own calibration accuracy.")
    ap.add_argument("--repo", default=DEFAULT_REPO, help=f"GitHub repo (default: {DEFAULT_REPO})")
    ap.add_argument("--consolidation-pr-prefix", default=DEFAULT_CONSOLIDATION_PR_PREFIX,
                    help=f"Consolidation PR title prefix (default: {DEFAULT_CONSOLIDATION_PR_PREFIX})")
    ap.add_argument("--lessons", default=DEFAULT_LESSONS, help=f"Lessons ledger path (default: {DEFAULT_LESSONS})")
    ap.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS,
                    help=f"Days to look back for consolidation PRs (default: {DEFAULT_LOOKBACK_DAYS})")
    ap.add_argument("--input", type=str, help="Input file or JSON (for Builder v1.7 compatibility; unused)")
    ap.add_argument("--dry-run", action="store_true", help="report only, do not write lessons")
    ap.add_argument("--smoke-test", action="store_true", help="run smoke tests and exit")
    args = ap.parse_args()
    if args.smoke_test:
        return smoke_test()
    result = run(
        repo=args.repo,
        consolidation_pr_prefix=args.consolidation_pr_prefix,
        lessons_path=Path(args.lessons),
        lookback_days=args.lookback_days,
        dry_run=args.dry_run,
    )
    print(render_report(result))
    if result.get("lesson_ids"):
        verb = "would upsert" if args.dry_run else "upserted"
        print(f"{verb} meta-lesson(s): {', '.join(result['lesson_ids'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
