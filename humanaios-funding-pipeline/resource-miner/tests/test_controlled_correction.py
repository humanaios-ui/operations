"""Deterministic negative controls for read-only correction proposals (#993, #1037)."""
from __future__ import annotations

import copy
import unittest

from resource_miner.controlled_correction import propose, project
from resource_miner.intent_os import evaluate_objective
from resource_miner.models import ResourceCandidate


class ControlledCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.resource = ResourceCandidate(
            resource_id="RES-TEST-001", title="Research Program Launch Manager",
            source_name="HumanAIOS Funding Pipeline",
            source_url="https://example.org/positions/program-launch",
            canonical_url="https://example.org/positions/program-launch",
            discovery_method="test_fixture", discovered_at="2026-10-26T12:00:00Z",
            description="A research program role to review.", tags=["research"],
            resource_types=["paid_work"], eligibility_assessed=False,
            raw={"PRIVATE_UNTRUSTED_NOTE": "MUST NEVER LEAK"},
        )
        self.observation = {
            "resource_id": "RES-TEST-001",
            "source_url": "https://example.org/positions/program-launch",
            "observed_at": "2026-10-26T12:05:00Z",
            "finding": "LINK_FAILED_404",
            "evidence_url": "https://example.org/positions/program-launch",
        }

    def _intent(self, rows):
        return evaluate_objective("research program", rows, source_mode="snapshot",
                                  source_status="CURATED_SNAPSHOT_NOT_LIVE")

    def test_baseline_still_displays_uncorrected_lead(self):
        self.assertEqual(self._intent([self.resource.to_dict()])["matched_count"], 1)

    def test_correction_holds_lead_end_to_end(self):
        before = copy.deepcopy(self.resource.to_dict(include_raw=True))
        p = propose(self.resource, self.observation)
        projection = project([self.resource], [p])
        self.assertEqual(projection["held_count"], 1)
        self.assertEqual(self._intent(projection["rows"])["matched_count"], 0)
        self.assertEqual(self.resource.to_dict(include_raw=True), before)
        self.assertNotIn("PRIVATE_UNTRUSTED_NOTE", repr(projection))
        self.assertEqual(projection["execution"], "DISABLED")
        self.assertEqual(projection["realized_benefit"], "NOT_VERIFIED")

    def test_status_does_not_falsely_claim_role_closed(self):
        p = propose(self.resource, self.observation)
        self.assertEqual(p["source_verification_status"], "RECHECK_REQUIRED")
        self.assertEqual(p["verification"], "UNVERIFIED_SOURCE_OBSERVATION")
        self.assertEqual(p["authority_effect"], "NONE")
        self.assertEqual(p["human_decision"], "PENDING")

    def test_official_recheck_does_not_release_without_human_review(self):
        o = {**self.observation, "finding": "OFFICIAL_SOURCE_RECHECKED"}
        p = propose(self.resource, o)
        self.assertEqual(p["source_verification_status"], "UNVERIFIED_RECHECK")
        self.assertEqual(self._intent(project([self.resource], [p])["rows"])["matched_count"], 0)

    def test_mismatched_resource_fails(self):
        with self.assertRaises(ValueError):
            propose(self.resource, {**self.observation, "resource_id": "RES-OTHER"})

    def test_mismatched_source_fails(self):
        with self.assertRaises(ValueError):
            propose(self.resource, {**self.observation, "source_url": "https://elsewhere.example/path"})

    def test_stale_source_version_fails(self):
        p = propose(self.resource, self.observation)
        changed = copy.deepcopy(self.resource)
        changed.title = "Updated listing at another revision"
        with self.assertRaises(ValueError):
            project([changed], [p])

    def test_forged_authorization_fails(self):
        p = {**propose(self.resource, self.observation), "authority_effect": "APPROVED"}
        with self.assertRaises(ValueError):
            project([self.resource], [p])

    def test_added_private_field_fails(self):
        p = {**propose(self.resource, self.observation), "email_body": "secret"}
        with self.assertRaises(ValueError):
            project([self.resource], [p])

    def test_modified_correction_fails(self):
        p = {**propose(self.resource, self.observation), "source_verification_status": "CONFIRMED_OPEN"}
        with self.assertRaises(ValueError):
            project([self.resource], [p])

    def test_replay_duplicate_proposals_fails(self):
        p = propose(self.resource, self.observation)
        with self.assertRaises(ValueError):
            project([self.resource], [p, p])

    def test_duplicate_source_records_fail(self):
        with self.assertRaises(ValueError):
            project([self.resource, copy.deepcopy(self.resource)], [])

    def test_unknown_finding_fails(self):
        with self.assertRaises(ValueError):
            propose(self.resource, {**self.observation, "finding": "YOU_QUALIFY"})

    def test_source_with_private_credentials_fails(self):
        with self.assertRaises(ValueError):
            propose(self.resource, {**self.observation, "evidence_url": "https://user:password@example.org/path"})

    def test_private_source_scheme_fails(self):
        with self.assertRaises(ValueError):
            propose(self.resource, {**self.observation, "evidence_url": "file:///home/user/tax.pdf"})

    def test_naive_timestamp_fails(self):
        with self.assertRaises(ValueError):
            propose(self.resource, {**self.observation, "observed_at": "2026-10-26"})

    def test_tax_credit_is_not_rebate_and_not_refund(self):
        c = copy.deepcopy(self.resource)
        c.title = "Research tax credit (candidate)"
        c.resource_types = ["rebate"]  # Regression baseline: broad lexical classifier.
        p = propose(c, {**self.observation, "finding": "TAX_CREDIT_AS_REBATE"})
        rows = project([c], [p])["rows"]
        self.assertEqual(rows[0]["tax_mechanism_proposed"], "CREDIT")
        self.assertEqual(rows[0]["resource_types"], ["rebate"])  # No unauthorized source mutation.
        self.assertFalse(rows[0]["eligibility_assessed"])
        self.assertEqual(self._intent(rows)["matched_count"], 0)
        self.assertEqual(p["financial_roi"], "NOT_MEASURED")

    def test_grant_is_not_silently_tax_excluded(self):
        p = propose(self.resource, {**self.observation, "finding": "TAXABLE_GRANT_AS_EXCLUDED"})
        rows = project([self.resource], [p])["rows"]
        self.assertEqual(rows[0]["tax_mechanism_proposed"], "GENERALLY_TAXABLE")
        self.assertEqual(p["eligibility"], "UNASSESSED")

    def test_deadline_dispute_is_not_calendar_event_or_acquisition(self):
        p = propose(self.resource, {**self.observation, "finding": "DEADLINE_CONFLICT"})
        projection = project([self.resource], [p])
        self.assertEqual(projection["realized_benefit"], "NOT_VERIFIED")
        self.assertEqual(projection["financial_roi"], "NOT_MEASURED")
        self.assertEqual(projection["next_human_action"],
                         "Verify official source, review correction, authorize any separate branch repair.")

    def test_no_corrections_preserve_intent_behavior(self):
        original = self.resource.to_dict(include_raw=False)
        rows = project([self.resource], [])["rows"]
        self.assertEqual(rows, [original])
        self.assertEqual(self._intent(rows), self._intent([original]))

    def test_many_proposals_fail_closed(self):
        with self.assertRaises(ValueError):
            project([self.resource], [{}] * 501)


if __name__ == "__main__":
    unittest.main()
