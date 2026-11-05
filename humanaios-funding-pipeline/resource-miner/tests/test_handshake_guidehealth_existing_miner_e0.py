"""Read-only E0 diagnostic: existing Miner vs one human-supplied Handshake listing.

Scope: instrument existing production modules, not implement the Handshake adapter.
All browser input is a redacted public posting specimen. An independent\nGuidehealth employer listing supports role/pay but its provider ID is not linked\nto the Handshake ID without a confirmed crosswalk. No account tokens,
personal identity, application requests, network I/O, or production writes.
Known gaps are asserted as CURRENT behavior; they are not acceptance passes.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from resource_miner.intent_os import PUBLIC_SOURCES, evaluate_objective
from resource_miner.miner import enrich
from resource_miner.normalize import normalize_generic
from resource_miner.opportunity_journey import SCHEMA, project_journey
from resource_miner.store import dedupe

ROOT = Path(__file__).resolve().parents[1]
NEEDS = ROOT / "data" / "needs.seed.json"
REQUIREMENTS = ROOT / "data" / "resource_requirements.seed.json"
HANDSHAKE = "https://app.joinhandshake.com/jobs/11737348"
SEARCH_VIEW = "https://app.joinhandshake.com/job-search/11737348?page=1&per_page=25"
SEARCH_ALIAS = "https://app.joinhandshake.com/jobs/11737348?searchId=synthetic-session"
TITLE = "Remote Clinical Quality Improvement Coordinator"
# Public job fields visible in an operator-approved browsing observation,
# timestamp not represented as an authenticated employer attestation.
DETAILS = (
    "Guidehealth healthcare quality improvement role. Full-time remote job. "
    "Advertised pay $28–30/hr. Apply by November 21, 2026 at 1:23 AM. "
    "Time zone unknown. No application submission attested."
)
OBSERVED_AT = "2026-11-04T23:00:00Z"  # synthetic fixture clock, NOT a source receipt


def candidate(url=HANDSHAKE, *, category="paid_work"):
    return normalize_generic(
        title=TITLE,
        url=url,
        source_name="Handshake",
        discovery_method="human_supplied_read_only_browser_observation",
        description=DETAILS,
        sponsor="Guidehealth",
        tags=["healthcare", "remote", "full_time"],
        source_category=category,
        primary_source_url=None,  # Provider cross-post equivalence has not been proven.
        observed_at=OBSERVED_AT,
    )


class HandshakeGuidehealthExistingMinerE0(unittest.TestCase):
    def test_exact_duplicate_collapses(self):
        self.assertEqual(len(dedupe([candidate(), candidate()])), 1)

    def test_noncanonical_handshake_aliases_still_generate_three_candidates(self):
        # CURRENT GAP: "job-search" and searchId are not provider-aware aliases.
        # Desired future acceptance = ONE unique Handshake job identity.
        rows = dedupe([candidate(HANDSHAKE), candidate(SEARCH_VIEW), candidate(SEARCH_ALIAS)])
        self.assertEqual(len(rows), 3)
        self.assertEqual(len({r.resource_id for r in rows}), 3)

    def test_explicit_paid_work_category_can_be_normalized(self):
        row = candidate()
        self.assertEqual(row.title, TITLE)
        self.assertEqual(row.resource_types, ["paid_work"])
        self.assertEqual(row.resource_affordances, ["earned_income"])
        self.assertEqual(row.deadline, "2026-11-21")
        self.assertEqual(row.source_name, "Handshake")
        self.assertIsNone(row.primary_source_url)
        self.assertFalse(row.eligibility_assessed)
        self.assertEqual(row.user_disposition, "UNSET")

    def test_missing_provider_category_misclassifies_job_as_general_resource(self):
        # CURRENT GAP: a Handshake importer must emit a typed paid_work mechanism.
        row = candidate(category=None)
        self.assertEqual(row.resource_types, ["general_resource"])

    def test_hourly_pay_range_is_not_preserved_as_structured_range(self):
        # CURRENT GAP: legacy money parser captures only the first $28 token.
        row = candidate()
        self.assertEqual(row.cash_mentions_usd, [28.0])
        self.assertNotIn(30.0, row.cash_mentions_usd)
        self.assertFalse(hasattr(row, "hourly_pay_min"))
        self.assertFalse(hasattr(row, "hourly_pay_max"))

    def test_deadline_only_has_date_not_time_zone(self):
        row = candidate()
        self.assertEqual(row.deadline, "2026-11-21")
        self.assertFalse(hasattr(row, "deadline_time_zone"))

    def test_real_need_graph_runs_without_authorizing_action(self):
        row = enrich([candidate()], NEEDS, REQUIREMENTS)[0]
        self.assertIn(row.route, {"VERIFY_NOW", "WATCH", "ARCHIVE"})
        self.assertFalse(row.eligibility_assessed)
        self.assertEqual(row.eligibility_status, "UNASSESSED")
        self.assertEqual(row.resource_state, "CANDIDATE")
        print(
            "GUIDEHEALTH_E0_MINER_PROJECTION="
            + json.dumps({
                "resource_id": row.resource_id,
                "type": row.resource_types,
                "affordance": row.resource_affordances,
                "route": row.route,
                "deadline": row.deadline,
                "need_matches": [{
                    "id": x.need_id, "score": x.score, "signals": x.signals
                } for x in row.need_matches],
                "requirement_matches": [{
                    "id": x.requirement_id, "gap": x.gap_status, "score": x.score
                } for x in row.requirement_matches],
                "eligibility": row.eligibility_status,
            }, sort_keys=True)
        )

    def test_handshake_is_excluded_from_current_public_intent_os_projection(self):
        # CURRENT GAP: INTENT-OS currently shows only curated funding + DEV.
        row = enrich([candidate()], NEEDS, REQUIREMENTS)[0]
        self.assertNotIn("Handshake", PUBLIC_SOURCES)
        result = evaluate_objective(
            "Find Guidehealth remote healthcare paid work",
            [row.to_dict()],
            source_mode="snapshot",
            source_status="HUMAN_PROVIDED_OBSERVATION_NOT_PROVIDER_VERIFIED",
        )
        self.assertEqual(result["shown_count"], 0)
        self.assertEqual(result["excluded_count"], 1)
        self.assertEqual(result["eligibility"], "NOT_ASSESSED")
        self.assertEqual(result["authority"], "NONE")
        self.assertEqual(result["execution"], "DISABLED")

    def test_saved_observation_cannot_be_mislabeled_as_application(self):
        # CURRENT GAP + SAFE FAIL-CLOSED: generic journey lacks typed SAVED.
        specimen = {
            "schema": SCHEMA,
            "opportunity": {"id": "guidehealth-example", "parent_resource_id": "handshake"},
            "events": [{
                "event_id": "sample-save",
                "kind": "SAVED_HUMAN_OBSERVED",
                "source_kind": "HUMAN_REPORT",
                "evidence_ref": "redacted-handshake-visit",
                "observed_at": OBSERVED_AT,
            }],
        }
        with self.assertRaisesRegex(ValueError, "Unknown event kind"):
            project_journey(specimen)

    def test_no_private_payload_in_public_candidate_projection(self):
        row = candidate()
        projected = row.to_dict()
        self.assertNotIn("raw", projected)
        self.assertNotIn("application_receipt", projected)
        self.assertFalse(projected["eligibility_assessed"])


if __name__ == "__main__":
    unittest.main()
