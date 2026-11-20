"""E0: research-support application states in existing private opportunity journey.

All IDs, times, and observations are synthetic. No live foundation submission,
account access, provider receipt, grant, or persistent storage is claimed.
"""
import copy
import unittest

from resource_miner.opportunity_journey import SCHEMA, project_journey


def specimen():
    return {
        "schema": SCHEMA,
        "workflow": "RESEARCH_SUPPORT_APPLICATION",
        "opportunity": {"id": "synthetic-research-application", "parent_resource_id": "synthetic-research-funding"},
        "events": [
            {"event_id": "human-selected", "kind": "HUMAN_SELECTED",
             "source_kind": "HUMAN_REPORT", "evidence_ref": "synthetic-selection",
             "observed_at": "2026-11-04T22:00:00Z"}
        ],
    }


def action(kind, event_id, at):
    return {"event_id": event_id, "kind": kind, "source_kind": "HUMAN_REPORT",
            "evidence_ref": "synthetic-private-claim", "observed_at": at}


class ResearchApplicationJourneyE0(unittest.TestCase):
    def test_blank_application_does_not_claim_submission(self):
        projected = project_journey(specimen())
        self.assertEqual(projected["workflow"], "RESEARCH_SUPPORT_APPLICATION")
        self.assertEqual(projected["application_standing"], "SUBMISSION_NOT_DOCUMENTED")
        self.assertEqual(projected["provider_review_standing"], "NOT_OBSERVED")
        self.assertEqual(projected["provider_decision_standing"], "UNVERIFIED")
        self.assertEqual(projected["grant_or_support_outcome"], "UNVERIFIED")
        self.assertIn("REVIEW_APPLICATION_AND_CONFIRM_SUBMISSION", projected["next_action_codes"])
        self.assertFalse(projected["can_submit_application"])
        self.assertEqual(projected["authority_effect"], "NONE")

    def test_human_submission_is_not_provider_confirmation(self):
        p = specimen()
        p["events"].append(action("APPLICATION_SUBMITTED_HUMAN", "reported", "2026-11-04T22:01:00Z"))
        result = project_journey(p)
        self.assertEqual(result["application_standing"], "SUBMITTED_HUMAN_REPORTED")
        self.assertEqual(result["confirmation_page_standing"], "UNVERIFIED")
        self.assertEqual(result["provider_receipt_email_standing"], "UNVERIFIED")
        self.assertEqual(result["provider_decision_standing"], "UNVERIFIED")
        self.assertEqual(result["next_action_codes"], ["REVIEW_AND_RECORD_CONFIRMATION"])

    def test_confirmation_page_is_observed_not_authenticated(self):
        p = specimen()
        p["events"] += [
            action("APPLICATION_SUBMITTED_HUMAN", "reported", "2026-11-04T22:01:00Z"),
            action("APPLICATION_CONFIRMATION_PAGE_HUMAN_OBSERVED", "page", "2026-11-04T22:02:00Z"),
        ]
        result = project_journey(p)
        self.assertEqual(result["event_count"], 3)
        self.assertEqual(result["application_standing"], "SUBMITTED_AND_CONFIRMATION_PAGE_HUMAN_OBSERVED")
        self.assertEqual(result["confirmation_page_standing"], "HUMAN_OBSERVED_NOT_CONNECTOR_AUTHENTICATED")
        self.assertEqual(result["provider_receipt_email_standing"], "UNVERIFIED")
        self.assertEqual(result["provider_review_standing"], "NOT_OBSERVED")
        self.assertEqual(result["grant_or_support_outcome"], "UNVERIFIED")
        self.assertEqual(result["next_action_codes"], ["CHECK_FOR_PROVIDER_RESPONSE"])
        self.assertFalse(result["can_send_mail"])
        self.assertFalse(result["can_submit_application"])

    def test_confirmation_without_submission_is_flagged(self):
        p = specimen()
        p["events"].append(action("APPLICATION_CONFIRMATION_PAGE_HUMAN_OBSERVED", "page", "2026-11-04T22:02:00Z"))
        out = project_journey(p)
        self.assertEqual(out["application_standing"], "CONFIRMATION_PAGE_ONLY_HUMAN_OBSERVED")
        self.assertIn("CONFIRMATION_PAGE_WITHOUT_SUBMISSION_REPORT", out["warnings"])

    def test_duplicate_reimport_and_reordered_events_have_same_digest(self):
        p = specimen()
        p["events"] += [action("APPLICATION_SUBMITTED_HUMAN", "reported", "2026-11-04T22:01:00Z"),
                         action("APPLICATION_CONFIRMATION_PAGE_HUMAN_OBSERVED", "page", "2026-11-04T22:02:00Z")]
        expected = project_journey(p)
        p["events"] = list(reversed(p["events"])) + [copy.deepcopy(p["events"][1])]
        self.assertEqual(expected, project_journey(p))

    def test_conflicting_event_id_or_forged_source_fails_closed(self):
        p = specimen()
        p["events"].append(action("APPLICATION_SUBMITTED_HUMAN", "reported", "2026-11-04T22:01:00Z"))
        p["events"].append(action("APPLICATION_CONFIRMATION_PAGE_HUMAN_OBSERVED", "reported", "2026-11-04T22:02:00Z"))
        with self.assertRaisesRegex(ValueError, "Conflicting reuse"):
            project_journey(p)
        p = specimen()
        event = action("APPLICATION_SUBMITTED_HUMAN", "faked", "2026-11-04T22:01:00Z")
        event["source_kind"] = "PROVIDER_RECEIPT"
        p["events"].append(event)
        with self.assertRaisesRegex(ValueError, "Untrusted source"):
            project_journey(p)

    def test_application_events_cannot_mutate_legacy_or_cross_into_survey(self):
        p = specimen()
        p.pop("workflow")
        p["events"].append(action("APPLICATION_SUBMITTED_HUMAN", "reported", "2026-11-04T22:01:00Z"))
        with self.assertRaisesRegex(ValueError, "Unknown event"):
            project_journey(p)
        p = specimen()
        p["events"].append({
            "event_id": "survey", "kind": "SURVEY_SUBMITTED_HUMAN",
            "source_kind": "HUMAN_REPORT", "evidence_ref": "synthetic",
            "observed_at": "2026-11-04T22:01:00Z"
        })
        with self.assertRaisesRegex(ValueError, "Unknown event"):
            project_journey(p)

    def test_private_field_and_authority_claims_are_rejected(self):
        p = specimen()
        p["provider_decision"] = "ACCEPTED"
        with self.assertRaises(ValueError):
            project_journey(p)
        p = specimen()
        p["events"][0]["email"] = "private@example.com"
        with self.assertRaises(ValueError):
            project_journey(p)
        p = specimen()
        p["workflow"] = "AUTO_APPLY"
        with self.assertRaisesRegex(ValueError, "Unsupported application workflow"):
            project_journey(p)


if __name__ == "__main__":
    unittest.main()
