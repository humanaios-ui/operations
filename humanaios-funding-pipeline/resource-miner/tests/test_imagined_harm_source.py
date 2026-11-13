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


    def test_p2_must_bind_to_same_p1_resource_revision_and_source(self):
        for field, replacement in (
            ("resource_id", "RES-DIFFERENT"),
            ("source_revision", "REV-DIFFERENT"),
        ):
            with self.subTest(field=field):
                s = self.specimen()
                s["p2"][field] = replacement
                with self.assertRaises(ValueError):
                    evaluate_trace(s)
        s = self.specimen()
        s["p2"]["source_review_packet"]["records"][0]["source_url"] = (
            "https://jobs.example.org/positions/another-role"
        )
        with self.assertRaises(ValueError):
            evaluate_trace(s)
        # Agreement between two untrusted claims is not independent proof.
        s = self.specimen()
        s["p1"]["source_url"] = "https://jobs.example.org/positions/another-role"
        s["p2"]["source_review_packet"]["records"][0]["source_url"] = s["p1"]["source_url"]
        self.assertFalse(evaluate_trace(s)["source_availability_verified"])

    def test_working_source_report_does_not_allow_unqualified_live_promotion(self):
        s = self.specimen()
        s["p2"]["source_review_packet"]["records"][0]["status"] = "SOURCE_WORKING"
        s["p3"]["presentation"] = "LIVE_UNQUALIFIED"
        result = evaluate_trace(s)
        self.assertTrue(result["review_required"])
        self.assertIn("UNVERIFIED_WORKING_SOURCE_PRESENTED_UNQUALIFIED", result["findings"])

    def test_reported_burden_does_not_justify_severe_harm_escalation(self):
        s = self.specimen()
        s["p1"]["harm_forecast"] = "TIME_LOSS_POSSIBLE"
        s["p3"]["harm_assessment"] = "SEVERE_HARM_POSSIBLE"
        s["history"]["human_outcome_observation"] = "USER_REPORTED_BURDEN"
        result = evaluate_trace(s)
        self.assertIn("HARM_ESCALATION_WITHOUT_INDEPENDENT_EVIDENCE", result["findings"])
        self.assertIn("SEVERE_HARM_NOT_INDEPENDENTLY_VERIFIED", result["findings"])
        self.assertFalse(result["human_benefit_verified"])

    def test_repeated_exposure_alone_requests_review_not_verified_outcome(self):
        s = self.specimen()
        s["history"]["unqualified_presentations_after_report"] = 2
        result = evaluate_trace(s)
        self.assertTrue(result["review_required"])
        self.assertIn("REPORTED_REPEAT_EXPOSURE_REQUIRES_VALIDATION", result["findings"])
        self.assertFalse(result["human_benefit_verified"])

    def test_digest_binds_source_observation_and_heldout_inputs(self):
        baseline = evaluate_trace(self.specimen())
        s = self.specimen()
        s["p2"]["source_review_packet"]["records"][0]["observed_at"] = "2026-10-23T19:00:00Z"
        changed_time = evaluate_trace(s)
        self.assertNotEqual(baseline["digest_sha256"], changed_time["digest_sha256"])
        self.assertNotEqual(baseline["p2_observation_projection_digest_sha256"],
                            changed_time["p2_observation_projection_digest_sha256"])
        s = self.specimen()
        s["p1"]["source_url"] = "https://jobs.example.org/positions/fictional-002"
        s["p2"]["source_review_packet"]["records"][0]["source_url"] = s["p1"]["source_url"]
        self.assertNotEqual(baseline["digest_sha256"], evaluate_trace(s)["digest_sha256"])
        s = self.specimen()
        s["heldout"]["visible_before"] = False
        after_control = evaluate_trace(s)
        self.assertNotEqual(baseline["digest_sha256"], after_control["digest_sha256"])
        self.assertEqual(after_control["heldout_resource_id"], "RES-HELDOUT-UNAFFECTED")
        self.assertFalse(after_control["heldout_visible_before"])


    def test_every_unverified_source_state_rejects_unqualified_live_presentation(self):
        # A status of OTHER, SOURCE_WORKING, or REPLACEMENT_FOUND is still
        # only a user claim; it is not an independently authenticated source.
        from resource_miner.source_review import STATES
        for state in STATES:
            with self.subTest(state=state):
                s = self.specimen()
                s["p2"]["source_review_packet"]["records"][0]["status"] = state
                s["p3"]["presentation"] = "LIVE_UNQUALIFIED"
                result = evaluate_trace(s)
                self.assertTrue(result["review_required"])
                self.assertIn("UNVERIFIED_SOURCE_PRESENTED_UNQUALIFIED", result["findings"])
                self.assertFalse(result["source_availability_verified"])


if __name__ == "__main__":
    unittest.main()
