import json
import unittest
from pathlib import Path

from resource_miner.mines import bind_opportunity
from resource_miner.models import EvidenceRef, ResourceMine
from resource_miner.normalize import normalize_generic
from resource_miner.opportunity_claim import build_opportunity_claim, claims_from_candidates
from resource_miner.proposition import (
    proposition_semantic_key,
    propositions_from_candidate,
    stable_proposition_id,
)

ROOT = Path(__file__).resolve().parents[1]


def specimen():
    mine = ResourceMine(
        mine_id="MINE-PROP",
        name="Certification Mine",
        mine_kind="PROGRAM_PLATFORM",
        canonical_url="https://example.test",
        resolver="fixture",
        roles=["OPPORTUNITY_SOURCE"],
    )
    row = normalize_generic(
        title="Free certification example",
        url="https://example.test/cert",
        source_name="Example",
        discovery_method="fixture",
        description="Free certification with a $100 exam voucher. Deadline October 31, 2026.",
        source_category="training",
        body_text="Apply by October 31, 2026. $100 exam voucher.",
        observed_at="2026-10-03T15:00:00Z",
        opportunity_identity="certification:example",
        opportunity_kind="online_certification_path",
    )
    row.resource_types = ["training", "credential"]
    row.resource_affordances = ["skill_development", "credential_evidence"]
    row.applicant_types = ["individual"]
    row.deadline = "2026-10-31"
    row.cash_mentions_usd = [100.0]
    row.evidence = [
        EvidenceRef(
            url=row.canonical_url,
            kind="mine_observation",
            observed_at="2026-10-03T15:00:00Z",
            claim="Opportunity endpoint observed.",
        )
    ]
    return bind_opportunity(mine, row, opportunity_source_kind="configured_endpoint")


class PropositionMiningTests(unittest.TestCase):
    def test_schema_defines_non_authoritative_prp_identity(self):
        schema = json.loads(
            (ROOT / "schemas" / "proposition-candidate.v1.schema.json").read_text()
        )
        self.assertEqual(schema["properties"]["authority_effect"]["const"], "NONE")
        self.assertIn("semantic_key", schema["required"])
        self.assertIn("epistemic_role", schema["required"])

    def test_one_record_mines_many_propositions(self):
        props = propositions_from_candidate(specimen())
        kinds = {row.proposition_type for row in props}
        self.assertIn("OPPORTUNITY_EXISTS", kinds)
        self.assertIn("CURRENTLY_AVAILABLE", kinds)
        self.assertIn("RESOURCE_TYPE", kinds)
        self.assertIn("AFFORDANCE", kinds)
        self.assertIn("DEADLINE", kinds)
        self.assertIn("CASH_MENTION", kinds)
        self.assertIn("APPLICANT_TYPE", kinds)
        self.assertGreater(len(props), 5)
        self.assertEqual(len({row.proposition_id for row in props}), len(props))

    def test_proposition_identity_is_semantic_not_title_based(self):
        row = specimen()
        first = propositions_from_candidate(row)
        row.title = "Completely different display title"
        second = propositions_from_candidate(row)
        self.assertEqual(
            {p.semantic_key: p.proposition_id for p in first},
            {p.semantic_key: p.proposition_id for p in second},
        )

    def test_different_objects_remain_distinct_propositions(self):
        key_free = proposition_semantic_key("STATUS", "price_state", "free")
        key_paid = proposition_semantic_key("STATUS", "price_state", "paid")
        a = stable_proposition_id("OPP-TEST", key_free)
        b = stable_proposition_id("OPP-TEST", key_paid)
        self.assertNotEqual(a, b)

    def test_classification_proposition_does_not_self_validate_truth(self):
        row = specimen()
        prop = next(
            p for p in propositions_from_candidate(row)
            if p.proposition_type == "RESOURCE_TYPE"
        )
        claim = build_opportunity_claim(row, prop)
        facets = {f.name: f.state for f in claim.facets}
        self.assertEqual(facets["TERMS"], "UNKNOWN")
        self.assertIn("proposition_truth", claim.unknowns)
        self.assertEqual(claim.proposition_id, prop.proposition_id)

    def test_direct_observation_proposition_can_support_currentness(self):
        row = specimen()
        prop = next(
            p for p in propositions_from_candidate(row)
            if p.proposition_type == "CURRENTLY_AVAILABLE"
        )
        claim = build_opportunity_claim(row, prop)
        facets = {f.name: f.state for f in claim.facets}
        self.assertEqual(facets["CURRENTNESS"], "SUPPORTED")

    def test_multiple_prp_claims_do_not_collapse_to_one_clm(self):
        row = specimen()
        claims = claims_from_candidates([row])
        self.assertGreater(len(claims), 1)
        self.assertEqual(len({c.claim_id for c in claims}), len(claims))
        self.assertTrue(all(c.opportunity_id == row.opportunity_id for c in claims))
        proposition_claims = [c for c in claims if c.proposition_id]
        self.assertEqual(
            {c.proposition_id for c in proposition_claims},
            {p.proposition_id for p in propositions_from_candidate(row)},
        )

    def test_cash_mention_is_not_rewritten_as_award_value(self):
        prop = next(
            p for p in propositions_from_candidate(specimen())
            if p.proposition_type == "CASH_MENTION"
        )
        self.assertIn("mention", prop.statement)
        self.assertIn("not a guaranteed award value", prop.statement)

    def test_extraction_confidence_is_not_truth_state(self):
        prop = next(
            p for p in propositions_from_candidate(specimen())
            if p.proposition_type == "OPPORTUNITY_EXISTS"
        )
        self.assertEqual(prop.extraction_confidence, 1.0)
        self.assertFalse(hasattr(prop, "truth_confidence"))
        self.assertEqual(prop.authority_effect, "NONE")


if __name__ == "__main__":
    unittest.main()
