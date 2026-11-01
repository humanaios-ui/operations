"""Issue #1091: six-source read-only characterization against existing Miner.

Every example is synthetic and de-identified. These tests intentionally preserve
known baseline shortcomings rather than claiming a new descriptor is deployed.
No network requests, private account reads, inventory changes, or authority.
"""
from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from resource_miner.needs import load_needs, load_requirements, map_to_needs, map_to_requirements
from resource_miner.normalize import normalize_generic, stable_resource_id
from resource_miner.planning import load_resource_plan, miner_requirements_from_plan, resolve_resource_plan
from resource_miner.resource_utility import project_resource_utility
from resource_miner.routing import route_candidate


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "resource_specialist_e0_synthetic.json"
AS_OF = date(2026, 10, 31)
OBSERVED_AT = "2026-10-31T00:00:00+00:00"  # fixture timestamp, NOT a real observation


def specimen_candidates():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if fixture.get("schema") != "humanaios.resource-specialist.e0.synthetic.v0.1":
        raise AssertionError("fixture schema drift")
    needs = load_needs(ROOT / "data" / "needs.seed.json")
    requirements = load_requirements(ROOT / "data" / "resource_requirements.seed.json")
    out = []
    for case in fixture["specimens"]:
        candidate = normalize_generic(
            title=case["title"],
            url=case["source_url"],
            source_name="SYNTHETIC_E0_NOT_A_REAL_PROVIDER",
            discovery_method="offline_synthetic_test",
            description=case["description"],
            source_category=case["source_category"],
            observed_at=OBSERVED_AT,
        )
        candidate.source_verification_status = case["simulated_source_status"]
        candidate.need_matches = map_to_needs(candidate, needs)
        candidate.requirement_matches = map_to_requirements(candidate, requirements)
        route_candidate(candidate, today=AS_OF)
        out.append((case, candidate))
    return fixture, out


class ResourceSpecialistE0(unittest.TestCase):
    def test_six_cases_source_bounded_and_zero_private_payload(self):
        fixture, items = specimen_candidates()
        self.assertEqual(len(items), 6)
        self.assertEqual(fixture["authority_effect"], "NONE")
        self.assertEqual(fixture["evidence_status"], "SYNTHETIC_ONLY_NOT_SOURCE_VERIFIED")
        self.assertEqual(len({row["case_id"] for row, _ in items}), 6)
        for row, candidate in items:
            with self.subTest(case=row["case_id"]):
                self.assertTrue(row["source_url"].startswith("https://example.org/synthetic/"))
                self.assertTrue(row["context_ref"].startswith("https://github.com/humanaios-ui/operations/"))
                self.assertTrue(row["form_facets"])
                self.assertFalse(candidate.eligibility_assessed)
                self.assertEqual(candidate.eligibility_status, "UNASSESSED")
                self.assertEqual(candidate.resource_state, "CANDIDATE")
                self.assertEqual(candidate.state_receipt_ids, [])
                self.assertEqual(candidate.cash_mentions_usd, [])
                self.assertNotIn("authority_effect", candidate.to_dict())

    def test_actual_baseline_type_affordance_and_need_routing(self):
        _, items = specimen_candidates()
        for row, candidate in items:
            with self.subTest(case=row["case_id"]):
                self.assertEqual(candidate.resource_types, [row["expected_type"]])
                self.assertEqual(candidate.resource_affordances, row["expected_affordances"])
                self.assertEqual(candidate.route, row["expected_baseline_route"])
                self.assertEqual(candidate.source_verification_status, row["simulated_source_status"])
        # An expected route is an investigation priority, never an eligibility claim.

    def test_internal_code_and_attention_are_not_typed_by_external_mechanism_rules(self):
        _, items = specimen_candidates()
        unmapped = [row["case_id"] for row, c in items if c.resource_types == ["general_resource"]]
        self.assertEqual(unmapped, ["E0-03", "E0-04"])
        # Characterization of a genuine scope gap; NOT a claim of improved retrieval.

    def test_source_404_not_promoted_to_closure_or_removed(self):
        _, items = specimen_candidates()
        case, candidate = next((row, c) for row, c in items if row["case_id"] == "E0-06")
        self.assertEqual(candidate.source_verification_status, "LINK_FAILED_404")
        # Existing generic route ignores source health. Record this baseline limitation.
        self.assertEqual(candidate.route, "VERIFY_NOW")
        self.assertNotEqual(candidate.status, "CLOSED")
        needs = load_needs(ROOT / "data" / "needs.seed.json")
        graph = project_resource_utility([{
            "resource_title": case["title"],
            "source_url": case["source_url"],
            "reported_status": "LINK_FAILED_404",
            "review_flags": [],
        }], needs)
        self.assertEqual(graph["edge_count"], 1)
        self.assertEqual(graph["edges"][0]["next_gate"], "INDEPENDENT_SOURCE_RECHECK")
        self.assertEqual(graph["edges"][0]["resource_control"], "NOT_ESTABLISHED")
        self.assertFalse(graph["delivery_executed"])

    def test_ids_stable_and_two_grants_not_collapsed(self):
        _, items = specimen_candidates()
        ids = [c.resource_id for _, c in items]
        self.assertEqual(len(ids), len(set(ids)))
        for case, candidate in items:
            self.assertEqual(candidate.resource_id, stable_resource_id(case["source_url"]))
        a = next(c for row, c in items if row["case_id"] == "E0-05")
        b = next(c for row, c in items if row["case_id"] == "E0-06")
        self.assertNotEqual(a.resource_id, b.resource_id)

    def test_reported_control_and_contract_do_not_prove_acquisition(self):
        _, items = specimen_candidates()
        for item_id in ("E0-01", "E0-02"):
            row, candidate = next((row, c) for row, c in items if row["case_id"] == item_id)
            self.assertNotEqual(row["control_proof"], "VERIFIED_ACQUIRED")
            self.assertEqual(candidate.resource_state, "CANDIDATE")
            self.assertFalse(candidate.eligibility_assessed)

    def test_existing_plan_keeps_internal_and_external_gaps_separate(self):
        plan = load_resource_plan(ROOT / "data" / "resource_plans" / "witness.seed.json")
        resolved = resolve_resource_plan(plan)
        status = {r["requirement_id"]: r["gap_status"]
                  for r in resolved["resource_requirements"]}
        self.assertEqual(status["RR-WITNESS-EVIDENCE-ACCESS-001"], "PARTIAL")
        self.assertEqual(status["RR-WITNESS-AGENT-RUNTIME-001"], "UNKNOWN")
        self.assertEqual(status["RR-WITNESS-LOCAL-COMPUTE-001"], "CONDITIONAL")
        self.assertEqual(status["RR-WITNESS-EXTERNAL-HUMAN-EXPERT-001"], "CONFIRMED")
        exported = {r["requirement_id"] for r in miner_requirements_from_plan(plan)}
        self.assertNotIn("RR-WITNESS-EVIDENCE-ACCESS-001", exported)
        self.assertIn("RR-WITNESS-LOCAL-COMPUTE-001", exported)
        self.assertEqual(resolved["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
