"""
test_smag_predict_lint.py
Builder v1.7 compliant
HumanAIOS
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import smag_predict_lint as lint  # noqa: E402
import smag_pr_autocapture_v1_0 as autocapture  # noqa: E402


def test_lint_pr_body_accepts_pinned_probability():
    result = lint.lint_pr_body("## What & why\nsmag_p: 0.25\n")
    assert result["status"] == "PASS"
    assert result["prediction"] == "smag_p:0.25"
    assert result["probability"] == 0.25


def test_lint_pr_body_rejects_missing_probability():
    result = lint.lint_pr_body("## What & why\nTemplate text only.\n")
    assert result["status"] == "VOID"
    assert result["prediction"] == lint.VOID_PREDICTION


def test_find_void_rows_flags_non_prediction_rows():
    rows = [
        {"pr": "1", "predicted": "smag_p:0.25"},
        {"pr": "2", "predicted": lint.VOID_PREDICTION},
        {"pr": "3", "predicted": "dependabot changelog"},
    ]
    assert [row["pr"] for row in lint.find_void_rows(rows)] == ["2", "3"]


def test_autocapture_build_fields_uses_probability_and_void_marker():
    ok = autocapture.build_fields(
        {"number": 7, "title": "t", "body": "smag_p: 0.42", "user": {"login": "Copilot"}, "merged": True},
        [{"conclusion": "success"}],
    )
    assert ok["predicted"] == "smag_p:0.42"
    assert ok["gap"] == ""

    void = autocapture.build_fields(
        {"number": 8, "title": "t", "body": "template only", "user": {"login": "Copilot"}, "merged": True},
        [{"conclusion": "success"}],
    )
    assert void["predicted"] == lint.VOID_PREDICTION
    assert void["gap"] == lint.VOID_GAP
