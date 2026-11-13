"""Synthetic fail-closed tests for Apart multi-sprint discovery and receipt separation."""
from __future__ import annotations

import copy
import unittest

from resource_miner.apart_sprints import (
    SCHEMA, canonical_sprint_url, project_apart_sprints,
)

SWARM = "https://apartresearch.com/sprints/swarm-alignment-2026"
COLLUSION = "https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25"


def event(event_id="S1", url=SWARM, kind="APPLICATION_SUBMITTED_HUMAN",
          source="HUMAN_REPORT", receipt="SYNTHETIC-HUMAN"):
    return {
        "event_id": event_id, "sprint_url": url, "kind": kind,
        "source_kind": source, "evidence_ref": receipt,
        "observed_at": "2026-11-04T20:00:00Z",
    }


def payload(*records):
    return {"schema": SCHEMA, "records": list(records)}


def record(url, *events):
    return {"sprint_url": url, "events": list(events)}


def card(projected, url):
    return next(c for c in projected["cards"] if c["url"] == url)


class ApartSprintsTests(unittest.TestCase):
    def test_five_distinct_public_opportunities(self):
        p = project_apart_sprints()
        self.assertEqual(len(p["cards"]), 5)
        self.assertEqual(len({c["url"] for c in p["cards"]}), 5)
        self.assertTrue(all(c["stage"] == "DISCOVERED_PUBLIC_SOURCE" for c in p["cards"]))
        self.assertTrue(all(c["award"] == "UNVERIFIED" for c in p["cards"]))
        self.assertEqual(p["legacy_local_case"], "UNCHANGED_NOT_IMPORTED")
        self.assertEqual(card(p, COLLUSION)["linked_research"][0].split("/")[-1],
                         "talk-actions-and-planted-approval-pacts-an-exploratory-audit-d106")

    def test_canonical_identity_suppresses_utm_duplicates(self):
        self.assertEqual(canonical_sprint_url(SWARM + "/?utm_source=email#signup"), SWARM)
        a = event()
        p = project_apart_sprints(payload(
            record(SWARM + "?utm_campaign=x", a),
            record(SWARM, copy.deepcopy(a)),
        ))
        self.assertEqual(len(p["cards"]), 5)
        self.assertEqual(len(card(p, SWARM)["evidence_summary"]), 1)
        self.assertEqual(card(p, SWARM)["stage"], "APPLIED_HUMAN_REPORTED")

    def test_human_application_does_not_prove_signup_or_award(self):
        p = project_apart_sprints(payload(record(SWARM, event())))
        c = card(p, SWARM)
        self.assertEqual(c["stage"], "APPLIED_HUMAN_REPORTED")
        self.assertEqual(c["legacy_journey"]["signup_standing"], "UNVERIFIED")
        self.assertEqual(c["participant_qualified"], "UNVERIFIED")
        self.assertEqual(c["benefit_realized"], "UNVERIFIED")
        self.assertEqual(c["authority_effect"], "NONE")

    def test_provider_message_is_not_prize_proof(self):
        submitted = event("C1", COLLUSION, "PROJECT_RECEIPT_EMAIL_OBSERVED",
                          "GMAIL_CONNECTOR_OBSERVATION", "SYNTHETIC-RECEIPT")
        judged = event("C2", COLLUSION, "JUDGING_UPDATE_EMAIL_OBSERVED",
                       "GMAIL_CONNECTOR_OBSERVATION", "SYNTHETIC-JUDGING")
        p = project_apart_sprints(payload(record(COLLUSION, submitted, judged)))
        c = card(p, COLLUSION)
        self.assertEqual(c["stage"], "REVIEW_PENDING_PROVIDER_MESSAGE_OBSERVED")
        self.assertEqual(c["legacy_journey"]["research_submission"], "UNVERIFIED")
        self.assertEqual(c["award"], "UNVERIFIED")
        self.assertEqual(c["benefit_realized"], "UNVERIFIED")

    def test_legacy_reducer_kept_for_existing_event_kinds(self):
        signup = event("S2", SWARM, "SIGNUP_WELCOME_EMAIL_OBSERVED",
                       "GMAIL_CONNECTOR_OBSERVATION", "SYNTHETIC-WELCOME")
        p = project_apart_sprints(payload(record(SWARM, signup)))
        c = card(p, SWARM)
        self.assertEqual(c["legacy_journey"]["signup_standing"], "WELCOME_EMAIL_OBSERVED")
        self.assertEqual(c["legacy_journey"]["participant_standing"], "NOT_CONFIRMED_BY_PROVIDER")

    def test_conflicting_duplicate_event_fails(self):
        first = event()
        altered = event(receipt="OTHER-RECEIPT")
        with self.assertRaises(ValueError):
            project_apart_sprints(payload(record(SWARM, first, altered)))

    def test_wrong_sprint_evidence_fails(self):
        with self.assertRaises(ValueError):
            project_apart_sprints(payload(record(SWARM, event(url=COLLUSION))))
        with self.assertRaises(ValueError):
            project_apart_sprints(payload(
                record(SWARM, event()),
                record(COLLUSION, event(url=COLLUSION)),
            ))

    def test_missing_confirmation_keeps_unknown(self):
        p = project_apart_sprints(payload(record(SWARM)))
        self.assertEqual(card(p, SWARM)["stage"], "DISCOVERED_PUBLIC_SOURCE")
        self.assertEqual(card(p, SWARM)["legacy_journey"]["signup_standing"], "UNVERIFIED")

    def test_impersonated_source_and_private_content_fail(self):
        fake = event(kind="PROJECT_RECEIPT_EMAIL_OBSERVED", source="HUMAN_REPORT")
        with self.assertRaises(ValueError):
            project_apart_sprints(payload(record(SWARM, fake)))
        private = event()
        private["email_body"] = "secret"
        with self.assertRaises(ValueError):
            project_apart_sprints(payload(record(SWARM, private)))
        private = event(receipt="https://mail.google.com/private")
        with self.assertRaises(ValueError):
            project_apart_sprints(payload(record(SWARM, private)))

    def test_rejects_external_and_non_event_urls(self):
        for url in ("https://example.com/sprints/swarm-alignment-2026",
                    "http://apartresearch.com/sprints/swarm-alignment-2026",
                    "https://apartresearch.com/sprints",
                    "https://apartresearch.com.evil/sprints/swarm-alignment-2026"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonical_sprint_url(url)

    def test_rejects_bad_time_and_unbounded_payload(self):
        wrong = event()
        wrong["observed_at"] = "2026-11-04T12:00:00-08:00"
        with self.assertRaises(ValueError):
            project_apart_sprints(payload(record(SWARM, wrong)))
        with self.assertRaises(ValueError):
            project_apart_sprints(payload(record(SWARM, *[event(str(i)) for i in range(65)])))

    def test_determinism_and_no_input_mutation(self):
        data = payload(record(SWARM, event("S1"), event("S2", kind="HUMAN_SELECTED")))
        before = copy.deepcopy(data)
        first = project_apart_sprints(data)
        self.assertEqual(data, before)
        data["records"][0]["events"].reverse()
        self.assertEqual(first, project_apart_sprints(data))


if __name__ == "__main__":
    unittest.main()
