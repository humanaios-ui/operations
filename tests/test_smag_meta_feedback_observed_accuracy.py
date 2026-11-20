"""Regression for Meta-SMAG observed outcome versus predicted confidence.

An OPEN consolidation PR is unresolved, not a failed or reworked forecast.
An author-controlled PR body is not independent evidence of precommitment.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("smag_meta_feedback_v1_0", HERE / "tools" / "smag_meta_feedback_v1_0.py")
assert SPEC and SPEC.loader
smag = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smag)

def fake_gh(*args, **kwargs):
    """Mock gh api call returning REST API format with merged_at and created_at fields."""
    # Extract page number from args to implement pagination
    page = 1
    for i, arg in enumerate(args[0] if args else []):
        if arg.startswith("page="):
            page = int(arg.split("=")[1])
            break

    # Page 1: return test data; page 2+: return empty to stop pagination
    if page == 1:
        rows = [
            {
                "number": 432,
                "title": "SMAG: consolidate ledger",
                "state": "closed",
                "merged_at": "2026-10-18T10:30:00Z",
                "created_at": "2026-10-15T09:00:00Z",
                "body": "smag_p_meta: 0.85"
            },
            {
                "number": 573,
                "title": "SMAG: consolidate findings",
                "state": "closed",
                "merged_at": "2026-10-19T11:15:00Z",
                "created_at": "2026-10-16T08:30:00Z",
                "body": "smag_p_meta: 0.85"
            },
            {
                "number": 724,
                "title": "SMAG: consolidate work items",
                "state": "open",
                "merged_at": None,
                "created_at": "2026-10-17T07:45:00Z",
                "body": "smag_p_meta: 0.85"
            },
            {
                "number": 817,
                "title": "SMAG: consolidate review",
                "state": "open",
                "merged_at": None,
                "created_at": "2026-10-18T06:20:00Z",
                "body": "smag_p_meta: 0.85"
            },
            {
                "number": 931,
                "title": "SMAG: consolidate results",
                "state": "open",
                "merged_at": None,
                "created_at": "2026-10-19T05:10:00Z",
                "body": "smag_p_meta: 0.85"
            },
        ]
    else:
        # Subsequent pages return empty list
        rows = []
    return SimpleNamespace(returncode=0, stdout=json.dumps(rows), stderr="")

class MetaAccuracyTests(unittest.TestCase):
    def test_open_items_censored_and_forecast_kept_separate(self):
        with patch.object(smag, "datetime") as dt, patch("subprocess.run", side_effect=fake_gh):
            from datetime import datetime
            dt.utcnow.return_value = datetime(2026, 10, 20)
            observation = smag.measure_consolidation_pr_outcomes("humanaios-ui/operations", "SMAG: consolidate", 44)
        self.assertEqual(observation["predicted_prs"], 5)
        self.assertEqual(observation["resolved_prs"], 2)
        self.assertEqual(observation["pending_prs"], 3)
        self.assertEqual(observation["reworked"], 0)
        self.assertEqual(observation["actual_success_rate"], 1.0)
        self.assertAlmostEqual(observation["predicted_accuracy"], 0.85)
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "ledger.json"
            with patch.object(smag, "measure_consolidation_pr_outcomes", return_value=observation):
                out = smag.run("humanaios-ui/operations", "SMAG: consolidate", ledger, 44)
            self.assertEqual(out["lesson_confidence"], "insufficient_data")
            first_ledger = json.loads(ledger.read_text())
            lesson = first_ledger["lessons"][0]
            self.assertEqual(lesson["accuracy_measured"], 1.0)
            self.assertEqual(lesson["observed_outcome_rate"], 1.0)
            self.assertAlmostEqual(lesson["mean_forecast_probability"], 0.85)
            self.assertEqual(lesson["pending_prs"], 3)
            # Idempotent rerun preserves the complete ledger.
            with patch.object(smag, "measure_consolidation_pr_outcomes", return_value=observation):
                smag.run("humanaios-ui/operations", "SMAG: consolidate", ledger, 44)
            second_ledger = json.loads(ledger.read_text())
            self.assertEqual(second_ledger, first_ledger)

    def test_only_open_items_do_not_claim_observed_accuracy(self):
        rows = [{
            "number": 931,
            "title": "SMAG: consolidate test",
            "state": "open",
            "merged_at": None,
            "created_at": "2026-10-19T05:10:00Z",
            "body": "smag_p_meta: 0.85"
        }]
        def mock_open_only_gh(*args, **kwargs):
            page = 1
            for i, arg in enumerate(args[0] if args else []):
                if arg.startswith("page="):
                    page = int(arg.split("=")[1])
                    break
            if page == 1:
                return SimpleNamespace(returncode=0, stdout=json.dumps(rows), stderr="")
            else:
                return SimpleNamespace(returncode=0, stdout=json.dumps([]), stderr="")

        with patch("subprocess.run", side_effect=mock_open_only_gh):
            observation = smag.measure_consolidation_pr_outcomes("humanaios-ui/operations", "SMAG: consolidate", 44)
        self.assertIsNone(observation["actual_success_rate"])
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "ledger.json"
            with patch.object(smag, "measure_consolidation_pr_outcomes", return_value=observation):
                result = smag.run("humanaios-ui/operations", "SMAG: consolidate", ledger, 44)
            self.assertEqual(result["status"], "INSUFFICIENT_RESOLVED_DATA")
            self.assertFalse(ledger.exists())

    def test_closed_unmerged_counts_as_resolved_non_success(self):
        rows = [
            {
                "number": 432,
                "title": "SMAG: consolidate item1",
                "state": "closed",
                "merged_at": "2026-10-18T10:30:00Z",
                "created_at": "2026-10-15T09:00:00Z",
                "body": "smag_p_meta: 0.85"
            },
            {
                "number": 573,
                "title": "SMAG: consolidate item2",
                "state": "closed",
                "merged_at": "2026-10-19T11:15:00Z",
                "created_at": "2026-10-16T08:30:00Z",
                "body": "smag_p_meta: 0.85"
            },
            {
                "number": 810,
                "title": "SMAG: consolidate item3",
                "state": "closed",
                "merged_at": None,
                "created_at": "2026-10-17T07:45:00Z",
                "body": "smag_p_meta: 0.10"
            },
            {
                "number": 817,
                "title": "SMAG: consolidate item4",
                "state": "open",
                "merged_at": None,
                "created_at": "2026-10-18T06:20:00Z",
                "body": "smag_p_meta: 0.01"
            },
        ]
        def mock_paginated_gh(*args, **kwargs):
            # Extract page number from args to implement pagination
            page = 1
            for i, arg in enumerate(args[0] if args else []):
                if arg.startswith("page="):
                    page = int(arg.split("=")[1])
                    break
            # Page 1: return test data; page 2+: return empty to stop pagination
            if page == 1:
                return SimpleNamespace(returncode=0, stdout=json.dumps(rows), stderr="")
            else:
                return SimpleNamespace(returncode=0, stdout=json.dumps([]), stderr="")

        with patch("subprocess.run", side_effect=mock_paginated_gh):
            result = smag.measure_consolidation_pr_outcomes("humanaios-ui/operations", "SMAG: consolidate", 44)
        self.assertEqual(result["resolved_prs"], 3)
        self.assertEqual(result["pending_prs"], 1)
        self.assertEqual(result["closed_unmerged_prs"], 1)
        self.assertAlmostEqual(result["actual_success_rate"], 2 / 3)
        self.assertAlmostEqual(result["mean_resolved_forecast_probability"], 0.60)
        self.assertAlmostEqual(result["predicted_accuracy"], 0.4525)
        self.assertAlmostEqual(result["calibration_gap"], 0.60 - (2 / 3))
        self.assertEqual(result["outcome_definition"], "GITHUB_MERGE_STATE_PROXY_NOT_REWORK_FREE_QUALITY")
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "lessons.json"
            with patch.object(smag, "measure_consolidation_pr_outcomes", return_value=result):
                out = smag.run("humanaios-ui/operations", "SMAG: consolidate", ledger, 44)
            self.assertEqual(out["lesson_confidence"], "drift_detected")
            lesson = json.loads(ledger.read_text())["lessons"][0]
            self.assertAlmostEqual(lesson["accuracy_measured"], 2 / 3)
            self.assertAlmostEqual(lesson["mean_forecast_probability"], 0.4525)
            self.assertAlmostEqual(lesson["mean_resolved_forecast_probability"], 0.60)
            self.assertIn("MERGE_STATE_PROXY", lesson["outcome_definition"])

    def test_pending_forecast_does_not_change_resolved_calibration_gap(self):
        base = [
            {
                "number": 432,
                "title": "SMAG: consolidate base1",
                "state": "closed",
                "merged_at": "2026-10-18T10:30:00Z",
                "created_at": "2026-10-15T09:00:00Z",
                "body": "smag_p_meta: 0.85"
            },
            {
                "number": 573,
                "title": "SMAG: consolidate base2",
                "state": "closed",
                "merged_at": "2026-10-19T11:15:00Z",
                "created_at": "2026-10-16T08:30:00Z",
                "body": "smag_p_meta: 0.85"
            },
            {
                "number": 810,
                "title": "SMAG: consolidate base3",
                "state": "closed",
                "merged_at": None,
                "created_at": "2026-10-17T07:45:00Z",
                "body": "smag_p_meta: 0.10"
            },
        ]
        def mock_base_paginated_gh(*args, **kwargs):
            page = 1
            for i, arg in enumerate(args[0] if args else []):
                if arg.startswith("page="):
                    page = int(arg.split("=")[1])
                    break
            if page == 1:
                return SimpleNamespace(returncode=0, stdout=json.dumps(base), stderr="")
            else:
                return SimpleNamespace(returncode=0, stdout=json.dumps([]), stderr="")

        with patch("subprocess.run", side_effect=mock_base_paginated_gh):
            before = smag.measure_consolidation_pr_outcomes("humanaios-ui/operations", "SMAG: consolidate", 44)

        pending = base + [{
            "number": 811,
            "title": "SMAG: consolidate pending",
            "state": "open",
            "merged_at": None,
            "created_at": "2026-10-18T06:20:00Z",
            "body": "smag_p_meta: 0.01"
        }]
        def mock_pending_paginated_gh(*args, **kwargs):
            page = 1
            for i, arg in enumerate(args[0] if args else []):
                if arg.startswith("page="):
                    page = int(arg.split("=")[1])
                    break
            if page == 1:
                return SimpleNamespace(returncode=0, stdout=json.dumps(pending), stderr="")
            else:
                return SimpleNamespace(returncode=0, stdout=json.dumps([]), stderr="")

        with patch("subprocess.run", side_effect=mock_pending_paginated_gh):
            after = smag.measure_consolidation_pr_outcomes("humanaios-ui/operations", "SMAG: consolidate", 44)
        self.assertEqual(after["calibration_gap"], before["calibration_gap"])
        self.assertEqual(after["mean_resolved_forecast_probability"], before["mean_resolved_forecast_probability"])
        self.assertNotEqual(after["predicted_accuracy"], before["predicted_accuracy"])

if __name__ == "__main__":
    unittest.main()
