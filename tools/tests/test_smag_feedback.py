"""
test_smag_feedback.py
Builder v1.7 compliant
HumanAIOS

Covers the FEED BACK step's three honest outcomes (INSUFFICIENT_DATA / CUES /
NO_DRIVERS) and the idempotent-upsert property that keeps repeated weekly runs
from duplicating lessons in data/lessons_learned_ledger.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import smag_feedback_v1_0 as fb  # noqa: E402
from smag_gap_analysis_v1_0 import analyze  # noqa: E402

TOOL_NAME = "test_smag_feedback"
TOOL_VERSION = "1.0.0"


def _row(smag_p, failing=None, day=1):
    checks = "checks: failure:1" if failing else "checks: success:1"
    return {
        "predicted": f"smag_p:{smag_p}" if smag_p is not None else "prose, not a pin",
        "measured": f"merged=True; {checks}",
        "timestamp": f"2026-02-{day:02d}T00:00:00Z",
        "substrate": "human:x",
        "failing_checks": failing or [],
    }


def test_smoke_test_passes():
    assert fb.smoke_test() == 0


def test_insufficient_data_below_floor():
    rows = [_row("0.5", day=i + 1) for i in range(3)]
    a = analyze(rows)
    r = fb.compute_cues(a, min_calibration_rows=10, driver_threshold=3)
    assert r["status"] == "INSUFFICIENT_DATA"
    assert r["calibration_rows"] == 3


def test_void_rows_excluded_from_calibration_count():
    # Unpinned rows must not count toward the calibration floor, even though
    # they carry real failing_checks data (IC-SMAG-01's whole point).
    rows = [_row(None, failing=["x"], day=i + 1) for i in range(20)]
    a = analyze(rows)
    r = fb.compute_cues(a, min_calibration_rows=10, driver_threshold=3)
    assert r["status"] == "INSUFFICIENT_DATA"
    assert r["calibration_rows"] == 0
    assert r["void_rows"] == 20


def test_cues_at_or_above_threshold():
    rows = [_row("0.6", failing=["flaky-gate"], day=i + 1) for i in range(3)]
    rows += [_row("0.7", day=i + 4) for i in range(8)]
    a = analyze(rows)
    r = fb.compute_cues(a, min_calibration_rows=10, driver_threshold=3)
    assert r["status"] == "CUES"
    assert r["cues"] == [{"check": "flaky-gate", "n": 3, "gap_rate": r["cues"][0]["gap_rate"]}]


def test_driver_below_threshold_is_not_a_cue():
    rows = [_row("0.6", failing=["rare-flake"], day=1)]
    rows += [_row("0.7", day=i + 2) for i in range(10)]
    a = analyze(rows)
    r = fb.compute_cues(a, min_calibration_rows=10, driver_threshold=3)
    assert r["status"] == "NO_DRIVERS"


def test_upsert_is_idempotent_by_id(tmp_path):
    path = tmp_path / "lessons.json"
    lesson = fb.lesson_for_insufficient_data(
        {"calibration_rows": 2, "void_rows": 40, "min_required": 10})
    fb.upsert_lessons(path, [lesson])
    fb.upsert_lessons(path, [lesson])
    data = json.loads(path.read_text())
    assert len(data["lessons"]) == 1
    assert data["lessons"][0]["id"] == "SMAG-FEEDBACK-CALIBRATION-STARVED"


def test_upsert_updates_in_place_not_appends_stale_copy(tmp_path):
    path = tmp_path / "lessons.json"
    old = fb.lesson_for_insufficient_data(
        {"calibration_rows": 1, "void_rows": 50, "min_required": 10})
    new = fb.lesson_for_insufficient_data(
        {"calibration_rows": 5, "void_rows": 50, "min_required": 10})
    fb.upsert_lessons(path, [old])
    fb.upsert_lessons(path, [new])
    data = json.loads(path.read_text())
    assert len(data["lessons"]) == 1
    assert "5" in data["lessons"][0]["rule"] or "5 of" in data["lessons"][0]["rule"]


def test_upsert_preserves_unrelated_existing_lessons(tmp_path):
    path = tmp_path / "lessons.json"
    path.write_text(json.dumps({
        "ledger_version": "1.0", "purpose": "p",
        "lessons": [{"id": "L1", "constraint": "unrelated"}],
    }))
    fb.upsert_lessons(path, [fb.lesson_for_insufficient_data(
        {"calibration_rows": 0, "void_rows": 10, "min_required": 10})])
    data = json.loads(path.read_text())
    ids = {entry["id"] for entry in data["lessons"]}
    assert ids == {"L1", "SMAG-FEEDBACK-CALIBRATION-STARVED"}


def test_dry_run_does_not_write(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("\n".join(json.dumps(_row("0.5", day=i + 1)) for i in range(3)))
    lessons = tmp_path / "lessons.json"
    result = fb.run(ledger, lessons, min_calibration_rows=10, driver_threshold=3, dry_run=True)
    assert result["status"] == "INSUFFICIENT_DATA"
    assert not lessons.exists()
    assert result["lesson_ids"] == ["SMAG-FEEDBACK-CALIBRATION-STARVED"]


def test_render_report_names_each_status():
    for status, builder in [
        ("INSUFFICIENT_DATA", lambda: {"status": "INSUFFICIENT_DATA", "calibration_rows": 1,
                                        "void_rows": 9, "min_required": 10}),
        ("NO_DRIVERS", lambda: {"status": "NO_DRIVERS", "calibration_rows": 10, "gap_rate": 0.0}),
        ("CUES", lambda: {"status": "CUES", "calibration_rows": 10,
                           "cues": [{"check": "x", "n": 3, "gap_rate": 0.3}]}),
    ]:
        assert status in fb.render_report(builder())
