"""
test_smag_predict_lint.py
Builder v1.7 compliant
HumanAIOS
"""
from __future__ import annotations

import importlib.util
import sys
import types
from collections import defaultdict
from pathlib import Path

TOOL_NAME = "test_smag_predict_lint"
TOOL_VERSION = "1.0.0"
TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import smag_predict_lint as lint  # noqa: E402
import smag_pr_autocapture_v1_0 as autocapture  # noqa: E402
import smag_gap_analysis_v1_0 as gap_analysis  # noqa: E402

sys.modules.setdefault("anthropic", types.SimpleNamespace(Anthropic=object))
GAP_ANALYZER_SPEC = importlib.util.spec_from_file_location(
    "smag_gap_analyzer",
    TOOLS_DIR / "smag_gap_analyzer.py",
)
gap_analyzer = importlib.util.module_from_spec(GAP_ANALYZER_SPEC)
assert GAP_ANALYZER_SPEC and GAP_ANALYZER_SPEC.loader
GAP_ANALYZER_SPEC.loader.exec_module(gap_analyzer)


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
        {"pr": "4", "predicted": "Outcome: landed\nsmag_p:0.25"},
    ]
    assert [row["pr"] for row in lint.find_void_rows(rows)] == ["2", "3", "4"]


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


def test_gap_analysis_excludes_void_predictions_from_calibration_counts():
    rows = [
        {"pr": "1", "substrate": "Copilot", "predicted": "smag_p:0.25", "measured": "merged=True; checks: success:1"},
        {"pr": "2", "substrate": "Copilot", "predicted": lint.VOID_PREDICTION, "measured": "merged=True; checks: failure:1"},
    ]
    result = gap_analysis.analyze(rows)

    assert result["n_rows"] == 2
    assert result["calibration_rows"] == 1
    assert result["void_rows"] == 1
    assert result["overall"]["clean"] == 1
    assert result["overall"]["friction"] == 0


def test_gap_analyzer_predictions_ignore_void_rows():
    rows = [
        {"pr": "1", "predicted": "smag_p:0.25", "measured": "merged=True; checks: success:1"},
        {"pr": "2", "predicted": lint.VOID_PREDICTION, "measured": "merged=True; checks: failure:1"},
    ]

    filtered = gap_analyzer.prediction_rows(rows)
    predictions = gap_analyzer.generate_predictions(defaultdict(list), filtered)

    assert [row["pr"] for row in filtered] == ["1"]
    assert predictions["metrics"]["total_rows"] == 1
    assert predictions["metrics"]["gap_rate"] == 0.0


def run_smoke_test() -> bool:
    try:
        assert TOOL_NAME == "test_smag_predict_lint"
        assert TOOL_VERSION
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(0 if run_smoke_test() else 1)
