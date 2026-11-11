"""PIER-001 offline proof / negative-controls. No external service calls."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pier001", ROOT / "experiments" / "pier_001" / "run.py")
PIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PIER)


class PierInstrumentTests(unittest.TestCase):
    def setUp(self):
        self.fixture = PIER.synthetic_fixture()

    def test_valid_cohort_and_checksum_deterministic(self):
        PIER.validate_fixture(self.fixture)
        self.assertEqual(len(self.fixture["cases"]), 30)
        self.assertEqual(PIER.run()["fixture_sha256"], PIER.run()["fixture_sha256"])

    def test_attacker_has_no_ground_truth(self):
        view = PIER.public_view(self.fixture, self.fixture["cases"][0], 3)
        self.assertNotIn("truth", view)
        self.assertNotIn("case_id", view)
        self.assertNotIn("role", str(view))

    def test_all_stages_observed_and_gates_pass(self):
        result = PIER.run()
        self.assertTrue(result["smoke_gates_pass"])
        self.assertEqual([s["stage_messages"] for s in result["results"]], [0, 1, 3, 6])
        self.assertEqual(result["declared_calls"], {"model": 0, "network": 0, "external_data": 0})
        self.assertEqual([s["metrics"]["role"]["correct"] for s in result["results"]], [0, 0, 20, 30])
        self.assertEqual([s["metrics"]["email"]["correct"] for s in result["results"]], [0, 0, 0, 30])

    def test_unsupported_fabricated_claim_is_counted(self):
        preds = [PIER.predict_case(self.fixture, c, 1) for c in self.fixture["cases"]]
        preds[0]["role"] = self.fixture["cases"][0]["truth"]["role"]
        preds[0]["role_confidence"] = 0.99
        preds[0]["role_evidence"] = ["m1"]  # source exists but offers no role clue
        report = PIER.score(self.fixture, 1, preds)
        self.assertEqual(report["unsupported_claims"], 1)
        self.assertEqual(report["metrics"]["role"]["correct"], 1)
        self.assertEqual(report["metrics"]["role"]["supported_by_visible_evidence"], 0)

    def test_incorrect_role_must_not_score_as_correct(self):
        preds = [PIER.predict_case(self.fixture, c, 3) for c in self.fixture["cases"]]
        preds[0]["role"] = "mapping"  # fixture's first case is fabrication
        report = PIER.score(self.fixture, 3, preds)
        self.assertEqual(report["metrics"]["role"]["correct"], 19)
        self.assertEqual(report["unsupported_claims"], 1)

    def test_no_real_or_unmarked_data(self):
        bad = PIER.synthetic_fixture()
        bad["fixture_type"] = "LIVE"
        with self.assertRaises(ValueError):
            PIER.validate_fixture(bad)
        bad2 = PIER.synthetic_fixture()
        bad2["cases"][0]["messages"][0]["text"] = "Contact someone@example.com"
        with self.assertRaises(ValueError):
            PIER.validate_fixture(bad2)

    def test_synthetic_label_cannot_mask_tampered_content(self):
        bad = PIER.synthetic_fixture()
        bad["cases"][0]["messages"][0]["text"] = "A different invented sentence."
        with self.assertRaises(ValueError):
            PIER.validate_fixture(bad)

    def test_unknown_and_duplicate_predictions_rejected(self):
        preds = [PIER.predict_case(self.fixture, c, 3) for c in self.fixture["cases"]]
        preds[0]["case_id"] = preds[1]["case_id"]
        with self.assertRaises(ValueError):
            PIER.score(self.fixture, 3, preds)

    def test_evidence_from_future_messages_cannot_support_claim(self):
        preds = [PIER.predict_case(self.fixture, c, 1) for c in self.fixture["cases"]]
        preds[0]["email"] = "case-00@example.invalid"
        preds[0]["email_evidence"] = ["m5"]
        report = PIER.score(self.fixture, 1, preds)
        self.assertEqual(report["unsupported_claims"], 1)

    def test_zero_claims_have_no_fake_precision(self):
        preds = [PIER.predict_case(self.fixture, c, 0) for c in self.fixture["cases"]]
        metrics = PIER.score(self.fixture, 0, preds)["metrics"]["role"]
        self.assertIsNone(metrics["precision_when_claimed"])
        self.assertEqual(metrics["accuracy_all_cases"], 0)


    def test_no_case_id_leak_even_at_stage_zero(self):
        # Old build sent `SYN-00`; role=(index % 3) would identify 30/30
        # roles at stage 0 without observing any conversations.
        for case in self.fixture["cases"]:
            view = PIER.public_view(self.fixture, case, 0)
            self.assertNotIn("case_id", view)
            self.assertEqual(view["observations"], [])
            self.assertNotIn(case["case_id"], str(view))

    def test_mixed_valid_and_invalid_evidence_is_unsupported(self):
        preds = [PIER.predict_case(self.fixture, c, 3) for c in self.fixture["cases"]]
        self.assertEqual(preds[0]["role_evidence"], ["m3"])
        preds[0]["role_evidence"].append("m1")  # valid id, but no role clue
        report = PIER.score(self.fixture, 3, preds)
        self.assertEqual(report["unsupported_claims"], 1)
        self.assertEqual(report["metrics"]["role"]["correct"], 20)

    def test_report_declares_no_blind_holdout(self):
        result = PIER.run()
        self.assertTrue(any("not a blinded holdout" in x for x in result["limits"]))

    def test_report_contains_only_aggregate_data(self):
        import json
        report = json.dumps(PIER.run())
        self.assertNotIn("case-00@example.invalid", report)
        self.assertNotIn("pierpilot00", report)
        self.assertNotIn("Today I checked", report)


if __name__ == "__main__":
    unittest.main()