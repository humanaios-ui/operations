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
    assert "--state" in args[0] and "all" in args[0]
    assert "--repo" in args[0]
    rows = [
        {"number": 432, "state": "MERGED", "body": "smag_p_meta: 0.85"},
        {"number": 573, "state": "MERGED", "body": "smag_p_meta: 0.85"},
        {"number": 724, "state": "OPEN", "body": "smag_p_meta: 0.85"},
        {"number": 817, "state": "OPEN", "body": "smag_p_meta: 0.85"},
        {"number": 931, "state": "OPEN", "body": "smag_p_meta: 0.85"},
    ]
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
            lesson = json.loads(ledger.read_text())["lessons"][0]
            self.assertEqual(lesson["accuracy_measured"], 1.0)
            self.assertEqual(lesson["observed_outcome_rate"], 1.0)
            self.assertAlmostEqual(lesson["mean_forecast_probability"], 0.85)
            self.assertEqual(lesson["pending_prs"], 3)
            # Idempotent rerun never rebrands probability as measured accuracy.
            with patch.object(smag, "measure_consolidation_pr_outcomes", return_value=observation):
                smag.run("humanaios-ui/operations", "SMAG: consolidate", ledger, 44)
            self.assertEqual(json.loads(ledger.read_text())["lessons"][0]["accuracy_measured"], 1.0)

    def test_only_open_items_do_not_claim_observed_accuracy(self):
        with patch("subprocess.run", return_value=SimpleNamespace(
            returncode=0,
            stdout=json.dumps([{"number": 931, "state": "OPEN", "body": "smag_p_meta: 0.85"}]),
            stderr="",
        )):
            observation = smag.measure_consolidation_pr_outcomes("humanaios-ui/operations", "SMAG: consolidate", 44)
        self.assertIsNone(observation["actual_success_rate"])
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "ledger.json"
            with patch.object(smag, "measure_consolidation_pr_outcomes", return_value=observation):
                result = smag.run("humanaios-ui/operations", "SMAG: consolidate", ledger, 44)
            self.assertEqual(result["status"], "INSUFFICIENT_RESOLVED_DATA")
            self.assertFalse(ledger.exists())

if __name__ == "__main__":
    unittest.main()
