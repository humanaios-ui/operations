import unittest

from integrations.schemas import EventType
from services.career_gradient import score_opportunity
from services.guiding_light import (
    build_witness_observation,
    events_for_snapshot,
    intervention_priorities,
    score_target,
)
from services.guiding_light_adapters import (
    entitlement_result_to_target,
    funding_source_to_target,
    resource_candidate_to_target,
)


class GuidingLightGeneralTests(unittest.TestCase):
    def test_hard_blocker_cannot_be_averaged_away(self):
        result = score_target({
            "id": "target",
            "title": "Blocked target",
            "domain": "custom",
            "value_axes": {"option_value": 1.0},
            "requirements": [
                {
                    "id": "a",
                    "label": "Strong existing evidence",
                    "mandatory": False,
                    "mapping_state": "DOCUMENTED",
                    "weight": 9.0,
                },
                {
                    "id": "b",
                    "label": "Required authority",
                    "mandatory": True,
                    "mapping_state": "BLOCKED",
                    "weight": 1.0,
                },
            ],
        })
        self.assertEqual("HOLD", result.classification)
        self.assertEqual("BLOCKED", result.assessment_state)
        self.assertIn("Required authority", result.mandatory_blockers)

    def test_mandatory_unknown_is_investigate_not_reachable(self):
        result = score_target({
            "id": "target",
            "title": "High-value unknown",
            "domain": "funding",
            "value_axes": {"value": 0.95},
            "requirements": [
                {
                    "id": "eligibility",
                    "label": "Applicant eligibility",
                    "mandatory": True,
                    "mapping_state": "UNKNOWN",
                    "weight": 0.1,
                },
                {
                    "id": "fit",
                    "label": "Strong domain fit",
                    "mandatory": False,
                    "mapping_state": "DOCUMENTED",
                    "weight": 9.9,
                },
            ],
        })
        self.assertEqual("FRONTIER", result.classification)
        self.assertEqual("INVESTIGATE", result.assessment_state)
        self.assertIn("Applicant eligibility", result.mandatory_unknowns)

    def test_project_maturity_can_be_a_bridge(self):
        result = score_target({
            "id": "production",
            "title": "Production ready",
            "domain": "project",
            "value_axes": {"scope": 0.9, "evidence_gain": 0.9},
            "requirements": [
                {
                    "id": "rollback",
                    "label": "Rollback",
                    "mandatory": True,
                    "mapping_state": "DOCUMENTED",
                    "weight": 1.0,
                },
                {
                    "id": "observability",
                    "label": "Observability",
                    "mandatory": True,
                    "mapping_state": "PARTIAL",
                    "gap_type": "evidence",
                    "weight": 1.0,
                },
            ],
        })
        self.assertEqual("BRIDGE", result.classification)

    def test_resource_miner_adapter_preserves_unassessed_eligibility(self):
        target = resource_candidate_to_target({
            "resource_id": "r-1",
            "title": "External resource",
            "eligibility_assessed": False,
            "eligibility_status": "UNASSESSED",
            "need_matches": [{"need_id": "n", "label": "Need", "score": 0.9}],
            "canonical_url": "https://example.test/resource",
        })
        result = score_target(target)
        self.assertEqual("UNKNOWN", target["requirements"][0]["mapping_state"])
        self.assertEqual("FRONTIER", result.classification)
        self.assertEqual("INVESTIGATE", result.assessment_state)

    def test_legacy_funding_tags_do_not_become_eligibility(self):
        target = funding_source_to_target({
            "name": "Funding source",
            "url": "https://example.test/funding",
            "native_eligible": True,
            "ai_safety_relevant": True,
        })
        self.assertEqual("UNKNOWN", target["requirements"][0]["mapping_state"])
        self.assertEqual("HOLD", score_target(target).classification)

    def test_entitlement_adapter_preserves_navigator_status(self):
        target = entitlement_result_to_target({
            "program_id": "p-1",
            "title": "Benefit pathway",
            "program_type": "benefit",
            "status": "RULE_MATCH",
            "predicates": [
                {
                    "label": "Program predicate",
                    "field": "predicate",
                    "state": "PASS",
                    "evidence": ["document if requested"],
                }
            ],
            "required_evidence": ["document if requested"],
            "next_actions": ["contact authority"],
            "sources": [{"url": "https://example.test/authority"}],
            "last_verified": "2026-09-27",
            "legal_note": "Screening only.",
        })
        self.assertEqual("RULE_MATCH", target["source_status"])
        self.assertEqual("USER_ATTESTED", target["requirements"][0]["mapping_state"])
        self.assertEqual("REACHABLE", score_target(target).classification)

    def test_interventions_are_tied_to_named_delta(self):
        rows = intervention_priorities([{
            "id": "t",
            "title": "Target",
            "domain": "research",
            "target_value": 1.0,
            "value_axes": {"option_value": 1.0},
            "requirements": [
                {
                    "id": "replication",
                    "label": "Independent replication",
                    "mapping_state": "PARTIAL",
                    "gap_type": "evidence",
                    "artifact_target": "replication report",
                }
            ],
        }])
        self.assertEqual("Independent replication", rows[0]["requirement"])
        self.assertEqual("BUILD_EVIDENCE", rows[0]["action"])
        self.assertEqual(["replication report"], rows[0]["artifact_targets"])

    def test_witness_never_authorizes(self):
        observation = build_witness_observation({
            "schema_version": "0.2.0",
            "subject": {"id": "x", "type": "project"},
            "domain": "project",
            "declared_goal_source": "owner",
            "targets": [],
        })
        self.assertEqual(
            "WITNESS_IS_NOT_THE_AUTHORITY",
            observation["non_authority_invariant"],
        )
        self.assertEqual(
            "NOT_GRANTED_BY_WITNESS",
            observation["authorization"]["state"],
        )

    def test_generic_events_use_account_hub_contract(self):
        events = events_for_snapshot({
            "schema_version": "0.2.0",
            "subject": {"id": "x", "type": "project"},
            "domain": "project",
            "declared_goal_source": "owner",
            "targets": [{
                "id": "pilot",
                "title": "Pilot",
                "domain": "project",
                "requirements": [{
                    "id": "test",
                    "label": "Test evidence",
                    "mapping_state": "PARTIAL",
                    "gap_type": "evidence",
                }],
            }],
        })
        self.assertEqual(EventType.TARGET_MAPPED, events[0].event_type)
        self.assertTrue(
            any(event.event_type == EventType.INTERVENTION_SIGNAL for event in events)
        )

    def test_career_adapter_preserves_harvest_vocabulary(self):
        result = score_opportunity({
            "id": "job",
            "title": "Reachable role",
            "gradient_axes": {"scope": 0.2},
            "requirements": [{
                "id": "r",
                "capability": "Operations",
                "mandatory": True,
                "mapping_state": "DOCUMENTED",
            }],
        })
        self.assertEqual("HARVEST", result.classification)


if __name__ == "__main__":
    unittest.main()
