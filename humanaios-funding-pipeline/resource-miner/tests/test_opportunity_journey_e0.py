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


if __name__ == "__main__":
    unittest.main()
