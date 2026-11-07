"""Synthetic offline guard: source holds must be reviewable, never actionable."""
from __future__ import annotations

import json
import unittest

from resource_miner.intent_os import evaluate_objective

BASE = {
    "resource_id": "TEST-SOURCE-001",
    "source_name": "HumanAIOS Funding Pipeline",
    "canonical_url": "https://example.org/research-compute-credits",
    "title": "Research compute credits",
    "description": "Research compute credits for an open source project",
    "route": "VERIFY_NOW",
    "status": "ACTIVE",
    "tags": ["research", "compute", "credits"],
    "eligibility_assessed": False,
}


def evaluate(rows, objective="Research compute credits"):
    return evaluate_objective(
        objective, rows, source_mode="snapshot",
        source_status="CURATED_SNAPSHOT_NOT_LIVE",
    )


class SourceHoldProjectionRegressionTests(unittest.TestCase):
    def test_conflicting_source_is_a_review_case_not_a_live_candidate(self):
        row = dict(BASE, source_verification_status="SOURCE_CONFLICT",
                   private_notes="PRIVATE_CATALOG_NOTE_DO_NOT_ECHO")
        result = evaluate([row])
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["verification_case_count"], 1)
        case = result["verification_cases"][0]
        self.assertEqual(case["resource_id"], BASE["resource_id"])
        self.assertEqual(case["verification_state"], "CONFLICTING")
        self.assertEqual(case["reason_code"], "SOURCE_CONFLICT")
        self.assertNotIn("PRIVATE_CATALOG_NOTE_DO_NOT_ECHO", json.dumps(result))
        self.assertEqual(result["authority"], "NONE")

    def test_unavailable_and_not_listed_emit_separate_cases(self):
        rows = [
            dict(BASE, resource_id="TEST-404-001", source_verification_status="LINK_FAILED_404"),
            dict(BASE, resource_id="TEST-ROLE-001", source_verification_status="ROLE_NOT_LISTED"),
            dict(BASE, resource_id="TEST-UNAVAILABLE-001", source_verification_status="SOURCE_UNAVAILABLE"),
        ]
        result = evaluate(rows)
        self.assertEqual(result["candidates"], [])
        states = {r["resource_id"]: (r["verification_state"], r["reason_code"])
                  for r in result["verification_cases"]}
        self.assertEqual(states["TEST-404-001"], ("UNAVAILABLE", "LINK_FAILED_404"))
        self.assertEqual(states["TEST-ROLE-001"], ("UNKNOWN", "ROLE_NOT_LISTED"))
        self.assertEqual(states["TEST-UNAVAILABLE-001"], ("UNAVAILABLE", "SOURCE_UNAVAILABLE"))

    def test_human_recheck_is_unknown_and_withheld(self):
        rows = [dict(BASE, source_verification_status="RECHECK_REQUIRED")]
        result = evaluate(rows)
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["verification_cases"][0]["verification_state"], "UNKNOWN")
        self.assertEqual(result["verification_cases"][0]["reason_code"], "RECHECK_REQUIRED")

    def test_legacy_recheck_is_withheld_without_false_verification(self):
        result = evaluate([dict(BASE, source_verification_status="UNVERIFIED_RECHECK")])
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["verification_cases"][0]["verification_state"], "UNKNOWN")
        self.assertEqual(result["verification_cases"][0]["reason_code"], "UNVERIFIED_RECHECK")

    def test_held_and_active_same_id_never_promotes_the_active_copy(self):
        held = dict(BASE, source_verification_status="SOURCE_CONFLICT")
        active = dict(BASE)
        for rows in ([active, held], [held, active]):
            with self.subTest(order=rows[0].get("source_verification_status")):
                result = evaluate(rows)
                self.assertEqual(result["candidates"], [])
                self.assertEqual(len(result["verification_cases"]), 1)
                self.assertEqual(result["verification_cases"][0]["verification_state"], "CONFLICTING")

    def test_private_source_is_not_leaked_to_verification_cases(self):
        private = dict(BASE, source_name="Private Gmail",
                       source_verification_status="SOURCE_CONFLICT")
        result = evaluate([private])
        self.assertEqual(result["verification_cases"], [])
        self.assertNotIn("TEST-SOURCE-001", json.dumps(result))

    def test_irrelevant_held_source_stays_out_of_results(self):
        unrelated = dict(BASE, resource_id="TEST-UNRELATED-001",
                         title="Woodworking workshop", description="Carpentry tools",
                         tags=["woodwork"], source_verification_status="SOURCE_UNAVAILABLE")
        result = evaluate([unrelated])
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["verification_cases"], [])

    def test_source_working_never_implies_independent_verification(self):
        result = evaluate([dict(BASE, source_verification_status="SOURCE_WORKING")])
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidates"][0]["verification_state"], "UNKNOWN")
        self.assertFalse(result["candidates"][0]["eligibility_assessed"])
        self.assertEqual(result["authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
