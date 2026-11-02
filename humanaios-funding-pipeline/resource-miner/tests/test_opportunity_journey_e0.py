"""Executable first-user opportunity lifecycle rules; all values synthetic."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from resource_miner.opportunity_journey import project_journey

EXAMPLE = Path(__file__).resolve().parents[1] / "fixtures" / "opportunity_journey_apart_synthetic.json"


class OpportunityJourneyTests(unittest.TestCase):
    def specimen(self):
        return json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_user_action_cycle_is_not_provider_qualification(self):
        record = project_journey(self.specimen())
        self.assertEqual(record["parent_resource_id"], "RES-APART-LAB")
        self.assertEqual(record["opportunity_id"], "OPP-APART-SPRINT")
        self.assertEqual(record["event_count"], 6)
        self.assertEqual(record["signup_standing"], "WELCOME_EMAIL_OBSERVED")
        self.assertEqual(record["survey_standing"], "SUBMITTED_HUMAN_REPORTED")
        self.assertEqual(record["calendar_standing"], "CREATED_CONNECTOR_REPORTED")
        self.assertEqual(record["discord_standing"], "JOINED_HUMAN_REPORTED")
        self.assertEqual(record["participant_standing"], "NOT_CONFIRMED_BY_PROVIDER")
        self.assertEqual(record["attendance"], "UNVERIFIED")
        self.assertEqual(record["research_submission"], "UNVERIFIED")
        self.assertEqual(record["prize_or_funding_outcome"], "UNVERIFIED")
        self.assertEqual(record["human_action_cycle"], "USER_ACTION_PROGRESS_REPORTED_NOT_PROVIDER_QUALIFIED")
        self.assertIn("VERIFY_PARTICIPANT_STANDING_WITH_PROVIDER", record["next_action_codes"])
        self.assertIn("REVIEW_EVENT_UPDATES_AND_RESEARCH_DELIVERABLE", record["next_action_codes"])

    def test_no_unauthorized_external_work(self):
        record = project_journey(self.specimen())
        for field in ("can_send_mail", "can_write_calendar", "can_read_discord",
                      "can_submit_application", "can_authorize_repository_change"):
            self.assertFalse(record[field], field)
        self.assertEqual(record["authority_effect"], "NONE")
        self.assertIn("UNSIGNED_LOCAL", record["receipt_kind"])

    def test_order_independent_and_idempotent_for_identical_receipt(self):
        payload = self.specimen()
        original = project_journey(payload)
        payload["events"] = list(reversed(payload["events"]))
        self.assertEqual(original, project_journey(payload))
        payload["events"].append(copy.deepcopy(payload["events"][0]))
        self.assertEqual(original, project_journey(payload))

    def test_conflicting_duplicate_event_id_fails_closed(self):
        payload = self.specimen()
        conflicted = copy.deepcopy(payload["events"][0])
        conflicted["evidence_ref"] = "OTHER-SOURCE"
        payload["events"].append(conflicted)
        with self.assertRaises(ValueError):
            project_journey(payload)

    def test_user_assertion_cannot_impersonate_gmail_receipt(self):
        payload = self.specimen()
        payload["events"][2]["source_kind"] = "HUMAN_REPORT"
        with self.assertRaises(ValueError):
            project_journey(payload)
        payload = self.specimen()
        payload["events"][4]["source_kind"] = "HUMAN_REPORT"
        with self.assertRaises(ValueError):
            project_journey(payload)

    def test_unknown_provider_qualification_status_is_not_admitted(self):
        payload = self.specimen()
        payload["events"].append({
            "event_id": "E7",
            "kind": "PARTICIPANT_QUALIFIED",
            "source_kind": "HUMAN_REPORT",
            "evidence_ref": "USER-ASSERTS-QUALIFIED",
            "observed_at": "2026-10-23T01:00:00Z",
        })
        with self.assertRaises(ValueError):
            project_journey(payload)

    def test_no_private_payload_fields(self):
        payload = self.specimen()
        payload["events"][2]["email_body"] = "secret"
        with self.assertRaises(ValueError):
            project_journey(payload)
        payload = self.specimen()
        payload["email_address"] = "private"
        with self.assertRaises(ValueError):
            project_journey(payload)
        payload = self.specimen()
        payload["events"][3]["evidence_ref"] = "https://mail.google.com/mail/u/0/"
        with self.assertRaises(ValueError):
            project_journey(payload)

    def test_missing_signup_does_not_mark_cycle_complete(self):
        payload = self.specimen()
        payload["events"] = [e for e in payload["events"] if e["kind"] != "SIGNUP_WELCOME_EMAIL_OBSERVED"]
        record = project_journey(payload)
        self.assertEqual(record["human_action_cycle"], "INCOMPLETE")
        self.assertIn("SURVEY_REPORT_WITHOUT_SIGNUP_RECEIPT", record["warnings"])
        self.assertIn("REVIEW_SIGNUP_OR_APPLICATION", record["next_action_codes"])

    def test_source_times_are_strictly_utc(self):
        for invalid in ("2026-10-22T10:00:00", "2026-10-22T10:00:00-07:00", "not-a-date", ""):
            with self.subTest(invalid=invalid):
                payload = self.specimen()
                payload["events"][0]["observed_at"] = invalid
                with self.assertRaises(ValueError):
                    project_journey(payload)

    def test_limits_and_parent_child_distinction(self):
        payload = self.specimen()
        payload["opportunity"]["parent_resource_id"] = payload["opportunity"]["id"]
        with self.assertRaises(ValueError):
            project_journey(payload)
        payload = self.specimen()
        payload["events"] = payload["events"] * 11
        with self.assertRaises(ValueError):
            project_journey(payload)


class PreparationTests(unittest.TestCase):
    def specimen(self):
        journey = json.loads(EXAMPLE.read_text())
        journey["preparation"] = {
            "required_files": ["INPUT", "METADATA"],
            "required_checks": [{"check_id": "CONSISTENCY", "file_ids": ["INPUT", "METADATA"]}],
            "files": [
                {"file_id": "INPUT", "version": 1, "sha256": "a" * 64, "role": "INPUT"},
                {"file_id": "METADATA", "version": 1, "sha256": "b" * 64, "role": "METADATA"},
            ],
            "checks": [{
                "check_id": "CONSISTENCY", "status": "PASS", "evidence_ref": "HUMAN-CHECK-1",
                "observed_at": "2026-10-28T12:00:00Z",
                "files": [
                    {"file_id": "INPUT", "version": 1, "sha256": "a" * 64},
                    {"file_id": "METADATA", "version": 1, "sha256": "b" * 64},
                ],
            }],
        }
        return journey

    def test_preparation_does_not_promote_outcomes_or_authority(self):
        payload = self.specimen()
        record = project_journey(payload)
        legacy = copy.deepcopy(payload)
        del legacy["preparation"]
        original = project_journey(legacy)
        self.assertNotIn("preparation", original)
        for field in ("participant_standing", "research_submission", "attendance",
                      "prize_or_funding_outcome", "authority_effect", "can_submit_application"):
            self.assertEqual(record[field], original[field])
        prep = record["preparation"]
        self.assertEqual(prep["standing"], "READY_FOR_HUMAN_REVIEW")
        self.assertFalse(prep["can_record"])
        self.assertFalse(prep["can_submit"])
        self.assertIn("NOT_INDEPENDENTLY_VERIFIED", prep["verification"])

    def test_changed_version_stales_exact_check_and_retains_history(self):
        payload = self.specimen()
        payload["preparation"]["files"].append({
            "file_id": "METADATA", "version": 2, "sha256": "c" * 64, "role": "METADATA",
        })
        record = project_journey(payload)
        prep = record["preparation"]
        self.assertEqual(prep["standing"], "NEEDS_PREPARATION")
        self.assertEqual(prep["checks"][0]["standing"], "STALE")
        self.assertEqual(len(prep["file_versions"]), 3)
        self.assertIn("COMPLETE_PREPARATION_CHECKS", record["next_action_codes"])
        ref = payload["preparation"]["checks"][0]["files"][1]
        ref.update(version=2, sha256="c" * 64)
        self.assertEqual(project_journey(payload)["preparation"]["standing"], "READY_FOR_HUMAN_REVIEW")

    def test_missing_files_and_unchecked_files_block(self):
        payload = self.specimen()
        payload["preparation"]["required_files"].append("REPORT")
        prep = project_journey(payload)["preparation"]
        self.assertIn("REPORT", prep["missing_files"])
        payload["preparation"]["files"].append({
            "file_id": "REPORT", "version": 1, "sha256": "d" * 64, "role": "OUTPUT",
        })
        prep = project_journey(payload)["preparation"]
        self.assertEqual(prep["missing_files"], [])
        self.assertEqual(prep["files_without_required_checks"], ["REPORT"])
        self.assertEqual(prep["standing"], "NEEDS_PREPARATION")

    def test_missing_failed_and_unknown_checks_block(self):
        for status in ("MISSING", "FAIL", "UNKNOWN"):
            with self.subTest(status=status):
                payload = self.specimen()
                if status == "MISSING":
                    payload["preparation"]["checks"] = []
                else:
                    payload["preparation"]["checks"][0]["status"] = status
                prep = project_journey(payload)["preparation"]
                self.assertEqual(prep["checks"][0]["standing"], status)
                self.assertEqual(prep["standing"], "NEEDS_PREPARATION")

    def test_empty_requirements_never_pass_vacuously(self):
        payload = self.specimen()
        payload["preparation"] = {k: [] for k in payload["preparation"]}
        self.assertEqual(project_journey(payload)["preparation"]["standing"], "NEEDS_PREPARATION")

    def test_bad_refs_missing_coverage_and_private_content_rejected(self):
        mutations = [
            lambda p: p["checks"][0]["files"][0].update(sha256="f" * 64),
            lambda p: p["checks"][0]["files"][0].update(version=2),
            lambda p: p["checks"][0]["files"].pop(),
            lambda p: p["files"][0].update(filename="private.pdf"),
            lambda p: p["files"][0].update(contents="secret"),
            lambda p: p["checks"][0].update(evidence_ref="https://mail.google.com/private"),
            lambda p: p["checks"][0].update(status="APPROVED"),
            lambda p: p["checks"][0].update(observed_at="2026-10-28"),
        ]
        for mutate in mutations:
            payload = self.specimen()
            mutate(payload["preparation"])
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                project_journey(payload)

    def test_conflicting_versions_and_bad_types_rejected(self):
        for field, value in (("version", True), ("version", 0), ("version", "1"),
                             ("sha256", "not-a-hash"), ("role", "APPROVED")):
            payload = self.specimen()
            payload["preparation"]["files"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                project_journey(payload)
        payload = self.specimen()
        payload["preparation"]["files"].append(copy.deepcopy(payload["preparation"]["files"][0]))
        with self.assertRaises(ValueError):
            project_journey(payload)

    def test_input_order_does_not_change_digest_or_mutate_payload(self):
        payload = self.specimen()
        original = copy.deepcopy(payload)
        expected = project_journey(payload)
        self.assertEqual(payload, original)
        prep = payload["preparation"]
        prep["required_files"].reverse()
        prep["required_checks"][0]["file_ids"].reverse()
        prep["files"].reverse()
        prep["checks"][0]["files"].reverse()
        self.assertEqual(expected, project_journey(payload))

    def test_preparation_collections_are_bounded(self):
        for key, count in (("required_files", 17), ("required_checks", 17), ("files", 33), ("checks", 17)):
            payload = self.specimen()
            payload["preparation"][key] = [None] * count
            with self.subTest(key=key), self.assertRaises(ValueError):
                project_journey(payload)
if __name__ == "__main__":
    unittest.main()
