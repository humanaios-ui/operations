"""Synthetic-only bounded tests for read-only Z1 progress sensor E0."""
from __future__ import annotations

import copy
import json
import unittest
from resource_miner.progress_sensor_e0 import evaluate_progress, SCHEMA

ID = "OPP-APART-SWARM-20261106"
URL = "https://apartresearch.com/sprints/swarm-alignment-2026"
NOW = "2026-11-07T21:00:00Z"
DUE = "2026-11-08T23:59:00-12:00"


def sample():
    return {
        "schema": SCHEMA,
        "opportunity_id": ID,
        "canonical_url": URL,
        "as_of": NOW,
        "source_observations": [{
            "opportunity_id": ID, "canonical_url": URL,
            "checked_at": "2026-11-07T20:00:00Z",
            "deadline_at": DUE, "source_revision": "public-brief-v1"
        }],
        "signals": [{
            "observation_id": "code-observation-1", "opportunity_id": ID,
            "kind": "INTERNAL_WORK_LINKED", "source_kind": "GITHUB_OBSERVATION",
            "observed_at": "2026-11-07T20:20:00Z", "evidence_ref": "pr1153-linked"
        }],
        "prior_dedupe_keys": [],
    }


def signal(kind, observation_id="signal-2", source_kind=None, opportunity_id=ID):
    sources = {
        "INTERNAL_WORK_LINKED": "GITHUB_OBSERVATION",
        "CODE_TEST_REPORTED": "GITHUB_OBSERVATION",
        "PDF_READY_HUMAN_REPORTED": "HUMAN_REPORT",
        "HUMAN_REVIEW_REPORTED": "HUMAN_REPORT",
        "HUMAN_SUBMISSION_REPORTED": "HUMAN_REPORT",
        "PROVIDER_RECEIPT_OBSERVED": "GMAIL_CONNECTOR_OBSERVATION",
        "BLOCKER_OBSERVED": "GITHUB_OBSERVATION",
        "BLOCKER_HUMAN_REPORTED": "HUMAN_REPORT",
    }
    return {"observation_id": observation_id, "opportunity_id": opportunity_id,
            "kind": kind, "source_kind": source_kind or sources[kind],
            "observed_at": "2026-11-07T20:30:00Z", "evidence_ref": "opaque-local-reference"}


class ProgressSensorE0Tests(unittest.TestCase):
    def test_apart_aoe_time_conversion(self):
        result = evaluate_progress(sample())
        self.assertEqual(result["deadline_utc"], "2026-11-09T11:59:00Z")
        self.assertEqual(result["deadline_local_central"], "2026-11-09T05:59:00-06:00")
        self.assertEqual(result["deadline_state"], "NEAR")

    def test_near_deadline_with_only_code_link_flags_unknown_readiness(self):
        r = evaluate_progress(sample())
        self.assertTrue(r["internal_work_observed"])
        self.assertEqual(r["submission_standing"], "SUBMISSION_NOT_VERIFIED")
        self.assertIn("DEADLINE_NEAR_WITH_UNKNOWN_READINESS", [x["type"] for x in r["trigger_candidates"]])

    def test_code_tests_cannot_mark_external_submission(self):
        x = sample(); x["signals"].append(signal("CODE_TEST_REPORTED"))
        r = evaluate_progress(x)
        self.assertTrue(r["code_test_claim_observed"])
        self.assertEqual(r["submission_standing"], "SUBMISSION_NOT_VERIFIED")
        self.assertFalse(r["can_submit"])

    def test_untrusted_human_submission_only_reports(self):
        x = sample(); x["signals"].append(signal("HUMAN_SUBMISSION_REPORTED"))
        r = evaluate_progress(x)
        self.assertEqual(r["submission_standing"], "HUMAN_SUBMISSION_REPORTED_NOT_PROVIDER_VERIFIED")
        self.assertIn("DEADLINE_NEAR_WITH_UNKNOWN_READINESS", [i["type"] for i in r["trigger_candidates"]])

    def test_wrong_sprint_provider_receipt_rejected(self):
        x = sample(); x["signals"].append(signal("PROVIDER_RECEIPT_OBSERVED",opportunity_id="OPP-APART-OCT2026"))
        with self.assertRaises(ValueError): evaluate_progress(x)

    def test_correct_sprint_provider_receipt_remains_unattested(self):
        x = sample(); x["signals"].append(signal("PROVIDER_RECEIPT_OBSERVED"))
        r = evaluate_progress(x)
        self.assertEqual(r["submission_standing"], "PROVIDER_RECEIPT_OBSERVED_UNAUTHENTICATED")
        self.assertFalse(r["provider_identity_verified_by_sensor"])
        self.assertIn("REVIEW_REPORTED_PROVIDER_RECEIPT", [i["type"] for i in r["trigger_candidates"]])

    def test_same_named_receipt_must_be_from_mail_connector(self):
        x = sample(); x["signals"].append(signal("PROVIDER_RECEIPT_OBSERVED",source_kind="HUMAN_REPORT"))
        with self.assertRaises(ValueError): evaluate_progress(x)

    def test_old_opportunity_journey_cannot_close_current_sprint(self):
        x = sample(); x["journey_projection"] = {"schema":"humanaios.opportunity_journey.projection.e0.v1",
            "opportunity_id":"OPP-APART-SPRINT", "authority_effect":"NONE", "research_submission":"UNVERIFIED"}
        with self.assertRaises(ValueError): evaluate_progress(x)

    def test_matching_journey_does_not_promote(self):
        x = sample(); x["journey_projection"] = {"schema":"humanaios.opportunity_journey.projection.e0.v1",
            "opportunity_id":ID, "authority_effect":"NONE", "research_submission":"UNVERIFIED"}
        self.assertEqual(evaluate_progress(x)["submission_standing"], "SUBMISSION_NOT_VERIFIED")

    def test_duplicate_signal_idempotent(self):
        x = sample(); original = evaluate_progress(x)
        x["signals"].append(copy.deepcopy(x["signals"][0]))
        self.assertEqual(original,evaluate_progress(x))

    def test_duplicate_signal_id_conflict_rejected(self):
        x = sample(); y=copy.deepcopy(x["signals"][0]);y["evidence_ref"]="different";x["signals"].append(y)
        with self.assertRaises(ValueError):evaluate_progress(x)

    def test_duplicate_alert_suppressed_without_external_state_changes(self):
        x=sample(); r=evaluate_progress(x); key=r["trigger_candidates"][0]["dedupe_key"]
        x["prior_dedupe_keys"]=[key]
        self.assertEqual(evaluate_progress(x)["trigger_candidates"][0]["emission_state"],"SUPPRESSED_REPLAY")

    def test_repeated_day_same_source_keeps_alert_key(self):
        x=sample(); k=evaluate_progress(x)["trigger_candidates"][0]["dedupe_key"]
        x["as_of"]="2026-11-08T11:00:00Z"
        self.assertEqual(evaluate_progress(x)["trigger_candidates"][0]["dedupe_key"],k)

    def test_deadline_extension_uses_latest_source(self):
        x=sample(); x["source_observations"].append(dict(x["source_observations"][0],
            checked_at="2026-11-07T20:30:00Z",deadline_at="2026-11-20T23:59:00-12:00",source_revision="updated-brief"))
        r=evaluate_progress(x)
        self.assertEqual(r["deadline_state"],"OPEN")
        self.assertNotIn("DEADLINE_NEAR_WITH_UNKNOWN_READINESS",[z["type"] for z in r["trigger_candidates"]])

    def test_same_time_different_deadlines_holds(self):
        x=sample();x["source_observations"].append(dict(x["source_observations"][0],
            source_revision="other",deadline_at="2026-11-10T23:59:00-12:00"))
        r=evaluate_progress(x)
        self.assertEqual(r["source_standing"],"SOURCE_CONFLICT")
        self.assertEqual(r["deadline_state"],"UNKNOWN")
        self.assertIn("SOURCE_CONFLICT_HOLD",[z["type"] for z in r["trigger_candidates"]])

    def test_reused_revision_different_deadline_holds(self):
        x=sample();x["source_observations"].append(dict(x["source_observations"][0],
            checked_at="2026-11-07T20:30:00Z",deadline_at="2026-11-10T23:59:00-12:00"))
        self.assertEqual(evaluate_progress(x)["source_standing"],"SOURCE_CONFLICT")

    def test_stale_source_flagged(self):
        x=sample();x["as_of"]="2026-11-12T21:00:00Z"
        r=evaluate_progress(x)
        self.assertTrue(r["source_age_stale"])
        self.assertIn("SOURCE_STALE_RECHECK",[z["type"] for z in r["trigger_candidates"]])

    def test_no_source_fails_closed(self):
        x=sample();x["source_observations"]=[]
        r=evaluate_progress(x)
        self.assertIsNone(r["deadline_utc"])
        self.assertIn("SOURCE_UNAVAILABLE_HOLD",[z["type"] for z in r["trigger_candidates"]])

    def test_expired_deadline_unknown_outcome(self):
        x=sample();x["as_of"]="2026-11-10T12:00:00Z"
        r=evaluate_progress(x)
        self.assertEqual(r["deadline_state"],"PASSED")
        self.assertIn("DEADLINE_PASSED_WITH_UNKNOWN_OUTCOME",[z["type"] for z in r["trigger_candidates"]])

    def test_blocker_is_separate_signal(self):
        x=sample();x["signals"].append(signal("BLOCKER_OBSERVED"))
        r=evaluate_progress(x)
        self.assertIn("BLOCKER_OBSERVED",[z["type"] for z in r["trigger_candidates"]])

    def test_future_timestamps_rejected(self):
        x=sample(); x["source_observations"][0]["checked_at"]="2026-11-08T23:00:00Z"
        with self.assertRaises(ValueError):evaluate_progress(x)

    def test_naive_deadline_rejected(self):
        x=sample();x["source_observations"][0]["deadline_at"]="2026-11-08T23:59:00"
        with self.assertRaises(ValueError):evaluate_progress(x)

    def test_private_fields_rejected(self):
        x=sample(); x["signals"][0]["gmail_thread_id"]="PRIVATE-SECRET"
        with self.assertRaises(ValueError):evaluate_progress(x)

    def test_private_url_token_rejected(self):
        x=sample(); x["canonical_url"]="https://example.test/private?token=secret"
        with self.assertRaises(ValueError):evaluate_progress(x)

    def test_strict_no_authority(self):
        r=evaluate_progress(sample())
        self.assertEqual(r["authority_effect"],"NONE")
        self.assertEqual(r["activation_state"],"NOT_ENABLED")
        self.assertFalse(r["can_dispatch"])
        self.assertFalse(r["can_change_permissions"])
        self.assertTrue(all(z["activation_state"]=="NOT_ENABLED" and z["authority_effect"]=="NONE" for z in r["trigger_candidates"]))

    def test_out_of_order_source_observations_unchanged(self):
        x=sample();x["source_observations"].append(dict(x["source_observations"][0], checked_at="2026-11-07T19:00:00Z", source_revision="older"))
        a=evaluate_progress(x);x["source_observations"].reverse();self.assertEqual(a,evaluate_progress(x))


    def test_november_provider_receipt_after_deadline_is_not_award(self):
        # Sanitized synthetic projection of observed Nov 9 provider receipt. No private Gmail data.
        x = sample()
        x["as_of"] = "2026-11-09T13:30:00Z"
        x["signals"].append(dict(
            signal("PROVIDER_RECEIPT_OBSERVED", "swarm-2026-paper-receipt"),
            observed_at="2026-11-09T11:28:02Z",
            evidence_ref="opaque-provider-paper-receipt",
        ))
        r = evaluate_progress(x)
        self.assertEqual(r["deadline_state"], "PASSED")
        self.assertEqual(r["submission_standing"], "PROVIDER_RECEIPT_OBSERVED_UNAUTHENTICATED")
        self.assertFalse(r["provider_identity_verified_by_sensor"])
        types = [i["type"] for i in r["trigger_candidates"]]
        self.assertIn("REVIEW_REPORTED_PROVIDER_RECEIPT", types)
        self.assertNotIn("DEADLINE_PASSED_WITH_UNKNOWN_OUTCOME", types)
        self.assertFalse(r["can_submit"])
        self.assertFalse(r["can_dispatch"])
        self.assertEqual(r["authority_effect"], "NONE")

    def test_followon_funding_form_must_not_impersonate_paper_receipt(self):
        # The Notion acknowledgment is a distinct child application, unsupported by E0 schema.
        x = sample()
        x["as_of"] = "2026-11-09T13:30:00Z"
        x["signals"].append({
            "observation_id": "funding-form-2026-received",
            "opportunity_id": ID,
            "kind": "FUNDING_REQUEST_RECEIPT_OBSERVED",
            "source_kind": "GMAIL_CONNECTOR_OBSERVATION",
            "observed_at": "2026-11-09T13:22:41Z",
            "evidence_ref": "opaque-funding-form-ack",
        })
        with self.assertRaises(ValueError):
            evaluate_progress(x)



if __name__ == "__main__":
    unittest.main()
