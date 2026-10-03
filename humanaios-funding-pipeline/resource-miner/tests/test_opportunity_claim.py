import unittest

from resource_miner.mines import bind_opportunity
from resource_miner.models import EvidenceRef, ResourceMine
from resource_miner.normalize import normalize_generic
from resource_miner.opportunity_claim import (
    add_claim_evidence,
    build_opportunity_claim,
    record_falsifier_evaluation,
    stable_claim_id,
)


def candidate(
    *,
    title="Azure startup credit",
    source_kind="configured_endpoint",
    evidence_kind="mine_observation",
):
    mine = ResourceMine(
        mine_id="MINE-TEST",
        name="Microsoft for Startups",
        mine_kind="PROGRAM_PLATFORM",
        canonical_url="https://www.microsoft.com/en-us/startups",
        resolver="configured_mine",
        roles=["OPPORTUNITY_SOURCE"],
    )
    row = normalize_generic(
        title=title,
        url="https://example.test/credit",
        source_name="Microsoft for Startups",
        discovery_method="test",
        description="Startup credit opportunity",
        source_category="compute_credit",
        observed_at="2026-10-03T14:00:00Z",
        opportunity_identity="credit:entry",
        opportunity_kind="startup_credit_entry",
        opportunity_source_kind=source_kind,
    )
    row.evidence = [
        EvidenceRef(
            url=row.canonical_url,
            kind=evidence_kind,
            observed_at="2026-10-03T14:00:00Z",
            claim="Observed authoritative opportunity surface",
        )
    ]
    return bind_opportunity(mine, row, opportunity_source_kind=source_kind)


class OpportunityClaimTests(unittest.TestCase):
    def test_claim_identity_is_stable_across_title_changes(self):
        first = build_opportunity_claim(candidate(title="Old wording"))
        second = build_opportunity_claim(candidate(title="New wording"))
        self.assertEqual(first.opportunity_id, second.opportunity_id)
        self.assertEqual(first.claim_id, second.claim_id)
        self.assertEqual(
            first.claim_token,
            f"urn:humanaios:opportunity-claim:{first.claim_id}",
        )

    def test_claim_requires_tokenized_opportunity(self):
        row = normalize_generic(
            title="Untokenized",
            url="https://example.test/raw",
            source_name="Example",
            discovery_method="test",
        )
        with self.assertRaises(ValueError):
            build_opportunity_claim(row)

    def test_resource_miner_never_self_promotes_eligibility_or_authorization(self):
        claim = build_opportunity_claim(candidate())
        facets = {facet.name: facet for facet in claim.facets}
        self.assertEqual(facets["ELIGIBILITY"].state, "UNASSESSED")
        self.assertEqual(facets["ATTAINABILITY"].state, "UNASSESSED")
        self.assertEqual(claim.warrant_state, "NOT_EVALUATED")
        self.assertEqual(claim.authorization_state, "NOT_REQUESTED")
        self.assertEqual(claim.actionability_state, "NOT_ACTIONABLE")
        self.assertEqual(claim.authority_effect, "NONE")

    def test_current_observation_supports_currentness(self):
        claim = build_opportunity_claim(candidate())
        facets = {facet.name: facet for facet in claim.facets}
        self.assertEqual(facets["CURRENTNESS"].state, "SUPPORTED")
        self.assertEqual(claim.overall_state, "SUPPORTED")

    def test_observation_failure_is_unknown_not_falsified(self):
        claim = build_opportunity_claim(
            candidate(evidence_kind="mine_observation_failed")
        )
        facets = {facet.name: facet for facet in claim.facets}
        self.assertEqual(facets["CURRENTNESS"].state, "UNKNOWN")
        self.assertNotEqual(claim.overall_state, "FALSIFIED")

    def test_currentness_falsifier_retires_without_erasing_existence(self):
        claim = build_opportunity_claim(candidate())
        current = next(f for f in claim.falsifiers if f.facet == "CURRENTNESS")
        updated = record_falsifier_evaluation(
            claim,
            current.falsifier_id,
            observed=True,
            evidence=EvidenceRef(
                url="https://example.test/credit",
                kind="authoritative_closure",
                observed_at="2026-10-04T00:00:00Z",
                claim="Program page states this opportunity is closed.",
            ),
        )
        facets = {facet.name: facet for facet in updated.facets}
        self.assertEqual(facets["CURRENTNESS"].state, "FALSIFIED")
        self.assertEqual(facets["EXISTENCE"].state, "SUPPORTED")
        self.assertEqual(updated.overall_state, "RETIRED")

    def test_terms_falsifier_contests_claim_without_destroying_identity(self):
        claim = build_opportunity_claim(candidate())
        terms = next(f for f in claim.falsifiers if f.facet == "TERMS")
        updated = record_falsifier_evaluation(
            claim,
            terms.falsifier_id,
            observed=True,
            evidence=EvidenceRef(
                url="https://example.test/credit",
                kind="authoritative_terms",
                observed_at="2026-10-04T00:00:00Z",
                claim="Published value differs materially from represented value.",
            ),
        )
        facets = {facet.name: facet for facet in updated.facets}
        self.assertEqual(facets["TERMS"].state, "FALSIFIED")
        self.assertEqual(facets["EXISTENCE"].state, "SUPPORTED")
        self.assertEqual(updated.overall_state, "CONTESTED")
        self.assertEqual(updated.claim_id, claim.claim_id)

    def test_falsifier_boolean_without_evidence_is_rejected(self):
        claim = build_opportunity_claim(candidate())
        current = next(f for f in claim.falsifiers if f.facet == "CURRENTNESS")
        with self.assertRaises(ValueError):
            record_falsifier_evaluation(
                claim,
                current.falsifier_id,
                observed=True,
                evidence=EvidenceRef(
                    url="",
                    kind="closure",
                    observed_at="",
                    claim="unreceipted boolean",
                ),
            )

    def test_supporting_eligibility_evidence_cannot_self_promote_eligibility(self):
        claim = build_opportunity_claim(candidate())
        updated = add_claim_evidence(
            claim,
            facet="ELIGIBILITY",
            relation="SUPPORTS",
            evidence=EvidenceRef(
                url="https://example.test/rules",
                kind="rule_observation",
                observed_at="2026-10-04T00:00:00Z",
                claim="Observed an eligibility rule.",
            ),
        )
        facets = {facet.name: facet for facet in updated.facets}
        self.assertEqual(facets["ELIGIBILITY"].state, "UNASSESSED")

    def test_existence_falsifier_falsifies_claim(self):
        claim = build_opportunity_claim(candidate())
        existence = next(f for f in claim.falsifiers if f.facet == "EXISTENCE")
        updated = record_falsifier_evaluation(
            claim,
            existence.falsifier_id,
            observed=True,
            evidence=EvidenceRef(
                url="https://example.test/correction",
                kind="authoritative_correction",
                observed_at="2026-10-04T00:00:00Z",
                claim="Source confirms the represented opportunity never existed.",
            ),
        )
        self.assertEqual(updated.overall_state, "FALSIFIED")

    def test_claim_id_derives_from_opportunity_not_resource_id(self):
        row = candidate()
        claim = build_opportunity_claim(row)
        self.assertEqual(claim.claim_id, stable_claim_id(row.opportunity_id))
        self.assertNotIn(row.resource_id, claim.claim_id)


if __name__ == "__main__":
    unittest.main()
