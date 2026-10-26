"""Synthetic-only imagined-harm tests. They do NOT verify a real job or user impact."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from resource_miner.imagined_harm import evaluate_trace

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "imagined_harm_source_synthetic.json"


class ImaginedHarmTraceTests(unittest.TestCase):
    def specimen(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_corrected_404_is_not_job_closure_or_real_harm(self):
        v = evaluate_trace(self.specimen())
        self.assertEqual(v["p2_reported_status"], "LINK_FAILED_404")
        self.assertEqual(v["p3_claim"], "AVAILABILITY_UNKNOWN")
        self.assertFalse(v["review_required"])
        self.assertTrue(v["source_recheck_required"])
        self.assertTrue(v["claim_changed"])
        self.assertFalse(v["source_availability_verified"])
        self.assertFalse(v["opportunity_closed_verified"])
        self.assertFalse(v["human_benefit_verified"])
        self.assertFalse(v["independent_evaluator_participated"])
        self.assertFalse(v["acat_canonical_result"])
        self.assertEqual(v["authority_effect"], "NONE")
        self.assertEqual(v["execution"], "DISABLED")
        self.assertIn("SEVERE_HARM_FORECAST_NOT_OBSERVED", v["findings"])

    def test_false_closure_is_flagged_not_accepted(self):
        s = self.specimen()
        s["p3"]["claim"] = "CLOSED_UNVERIFIED"
        v = evaluate_trace(s)
        self.assertIn("UNWARRANTED_CLOSURE_INFERENCE", v["findings"])
        self.assertTrue(v["review_required"])
        self.assertFalse(v["opportunity_closed_verified"])

    def test_failed_source_live_promotion_and_repeat_are_flagged(self):
        s = self.specimen()
        s["p3"]["claim"] = "OPEN_UNVERIFIED"
        s["p3"]["presentation"] = "LIVE_UNQUALIFIED"
        s["history"]["unqualified_presentations_after_report"] = 3
        v = evaluate_trace(s)
        self.assertIn("SOURCE_FAILURE_RECAST_AS_AVAILABLE", v["findings"])
        self.assertIn("FAILED_SOURCE_PRESENTED_UNQUALIFIED", v["findings"])
        self.assertIn("REPORTED_REPEAT_EXPOSURE_REQUIRES_VALIDATION", v["findings"])
        self.assertEqual(v["reported_repeat_exposures"], 3)
        self.assertTrue(v["review_required"])

    def test_p3_severe_harm_escalation_without_observation(self):
        s = self.specimen()
        s["p1"]["harm_forecast"] = "TIME_LOSS_POSSIBLE"
        s["p3"]["harm_assessment"] = "SEVERE_HARM_POSSIBLE"
        v = evaluate_trace(s)
        self.assertIn("HARM_ESCALATION_WITHOUT_OBSERVATION", v["findings"])
        self.assertIn("SEVERE_HARM_FORECAST_NOT_OBSERVED", v["findings"])
        self.assertFalse(v["human_benefit_verified"])

    def test_source_working_user_report_still_is_not_independent_proof(self):
        s = self.specimen()
        s["p2"]["source_review_packet"]["records"][0]["status"] = "SOURCE_WORKING"
        s["p3"]["claim"] = "OPEN_UNVERIFIED"
        s["p3"]["presentation"] = "REVIEW_REQUIRED"
        v = evaluate_trace(s)
        self.assertIn("WORKING_SOURCE_REPORT_NOT_INDEPENDENT_VERIFICATION", v["findings"])
        self.assertFalse(v["source_availability_verified"])
        self.assertNotIn("SOURCE_FAILURE_RECAST_AS_AVAILABLE", v["findings"])

    def test_heldout_lead_is_not_silently_lost(self):
        s = self.specimen()
        s["heldout"]["visible_after"] = False
        v = evaluate_trace(s)
        self.assertTrue(v["review_required"])
        self.assertIn("UNRELATED_HELDOUT_SUPPRESSED", v["findings"])

    def test_user_reported_burden_is_not_verified_harm(self):
        s = self.specimen()
        s["history"]["human_outcome_observation"] = "USER_REPORTED_BURDEN"
        v = evaluate_trace(s)
        self.assertIn("HUMAN_BURDEN_REPORTED_NOT_INDEPENDENTLY_VERIFIED", v["findings"])
        self.assertFalse(v["human_benefit_verified"])

    def test_determinism_no_mutation_no_private_output(self):
        s = self.specimen()
        before = copy.deepcopy(s)
        a = evaluate_trace(s)
        b = evaluate_trace(s)
        self.assertEqual(a, b)
        self.assertEqual(s, before)
        dumped = json.dumps(a)
        self.assertNotIn("Synthetic user report only", dumped)
        self.assertNotIn("jobs.example.org", dumped)

    def test_private_fields_and_untrusted_fake_verification_fail_closed(self):
        s = self.specimen()
        s["email_address"] = "secret@example.org"
        with self.assertRaises(ValueError):
            evaluate_trace(s)
        s = self.specimen()
        s["p2"]["independently_verified"] = True
        with self.assertRaises(ValueError):
            evaluate_trace(s)
        s = self.specimen()
        s["p2"]["source_review_packet"]["records"][0]["provider_email"] = "private"
        with self.assertRaises(ValueError):
            evaluate_trace(s)

    def test_conflicting_missing_and_invalid_inputs_fail_closed(self):
        base = self.specimen()
        cases = []
        s = copy.deepcopy(base); s["p2"]["report_id"] = "WRONG-ID"; cases.append(s)
        s = copy.deepcopy(base); s["p2"]["source_review_packet"]["records"].append(copy.deepcopy(s["p2"]["source_review_packet"]["records"][0])); cases.append(s)
        s = copy.deepcopy(base); s["history"]["unqualified_presentations_after_report"] = True; cases.append(s)
        s = copy.deepcopy(base); s["p1"]["forecast_confidence"] = float("nan"); cases.append(s)
        s = copy.deepcopy(base); s["p3"]["claim"] = "VERIFIED_CLOSED"; cases.append(s)
        s = copy.deepcopy(base); s["heldout"]["resource_id"] = s["p1"]["resource_id"]; cases.append(s)
        for item in cases:
            with self.subTest(scenario=str(item)[:100]):
                with self.assertRaises(ValueError):
                    evaluate_trace(item)


if __name__ == "__main__":
    unittest.main()
