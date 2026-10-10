import json
import unittest
from pathlib import Path

from resource_miner.proposition import (
    PropositionCandidate,
    proposition_semantic_key,
    stable_proposition_id,
)
from resource_miner.reconciliation import reconcile_propositions

ROOT = Path(__file__).resolve().parents[1]


def prop(
    *,
    opportunity_id,
    mine_id,
    subject_key,
    proposition_type,
    predicate,
    object_value,
    extracted_at="2026-10-03T12:00:00Z",
    source_origin_key=None,
):
    key = proposition_semantic_key(proposition_type, predicate, object_value)
    pid = stable_proposition_id(opportunity_id, key)
    return PropositionCandidate(
        schema="humanaios.proposition-candidate.v1",
        proposition_id=pid,
        proposition_token=f"urn:humanaios:proposition:{pid}",
        opportunity_id=opportunity_id,
        opportunity_token=f"urn:humanaios:resource-opportunity:{opportunity_id}",
        proposition_type=proposition_type,
        epistemic_role="SOURCE_ASSERTION",
        subject=f"urn:humanaios:resource-opportunity:{opportunity_id}",
        predicate=predicate,
        object_value=object_value,
        statement=f"{predicate} = {object_value}",
        semantic_key=key,
        resolution_subject_key=subject_key,
        source_origin_key=source_origin_key or mine_id.casefold(),
        extracted_at=extracted_at,
        extraction_method="NORMALIZER_EXTRACTION",
        extraction_confidence=None,
        evidence=[],
        source_url="https://example.test/source",
        mine_id=mine_id,
        mine_name=mine_id,
        authority_effect="NONE",
    )


class PropositionReconciliationTests(unittest.TestCase):
    def test_schemas_preserve_non_authority_boundary(self):
        prs = json.loads(
            (ROOT / "schemas" / "proposition-resolution-set.v1.schema.json").read_text()
        )
        rel = json.loads(
            (ROOT / "schemas" / "proposition-relation.v1.schema.json").read_text()
        )
        self.assertEqual(prs["properties"]["authority_effect"]["const"], "NONE")
        self.assertEqual(prs["properties"]["truth_state"]["const"], "NOT_DETERMINED")
        self.assertEqual(prs["properties"]["authorization_state"]["const"], "NOT_REQUESTED")
        self.assertEqual(rel["properties"]["authority_effect"]["const"], "NONE")

    def test_independent_same_assertion_is_corroborated_not_truth(self):
        a = prop(
            opportunity_id="OPP-0000000000000001",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        b = prop(
            opportunity_id="OPP-0000000000000002",
            mine_id="MINE-B",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        result = reconcile_propositions([a, b])
        self.assertEqual(len(result), 1)
        prs = result[0]
        self.assertEqual(prs.state, "CORROBORATED")
        self.assertEqual(prs.distinct_source_count, 2)
        self.assertEqual(prs.distinct_origin_count, 2)
        self.assertEqual(prs.truth_state, "NOT_DETERMINED")
        self.assertEqual(prs.authority_effect, "NONE")
        kinds = {r.relation_type for r in prs.relations}
        self.assertEqual(kinds, {"SAME_AS", "SUPPORTS"})

    def test_same_words_different_subjects_do_not_merge(self):
        a = prop(
            opportunity_id="OPP-0000000000000011",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        b = prop(
            opportunity_id="OPP-0000000000000012",
            mine_id="MINE-B",
            subject_key="program:beta",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        result = reconcile_propositions([a, b])
        self.assertEqual(len(result), 2)
        self.assertNotEqual(result[0].resolution_set_id, result[1].resolution_set_id)

    def test_same_day_exclusive_boolean_conflict_is_contested(self):
        a = prop(
            opportunity_id="OPP-0000000000000021",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="CURRENTLY_AVAILABLE",
            predicate="currently_available",
            object_value=True,
            extracted_at="2026-10-03T10:00:00Z",
        )
        b = prop(
            opportunity_id="OPP-0000000000000022",
            mine_id="MINE-B",
            subject_key="program:alpha",
            proposition_type="CURRENTLY_AVAILABLE",
            predicate="currently_available",
            object_value=False,
            extracted_at="2026-10-03T10:00:00Z",
        )
        prs = reconcile_propositions([a, b])[0]
        self.assertEqual(prs.state, "CONTESTED")
        self.assertIn("CONTRADICTS", {r.relation_type for r in prs.relations})
        self.assertIsNone(prs.canonical_object_value)

    def test_different_day_cross_source_boolean_change_fails_closed(self):
        a = prop(
            opportunity_id="OPP-0000000000000031",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="CURRENTLY_AVAILABLE",
            predicate="currently_available",
            object_value=True,
            extracted_at="2026-10-01T10:00:00Z",
        )
        b = prop(
            opportunity_id="OPP-0000000000000032",
            mine_id="MINE-B",
            subject_key="program:alpha",
            proposition_type="CURRENTLY_AVAILABLE",
            predicate="currently_available",
            object_value=False,
            extracted_at="2026-10-03T10:00:00Z",
        )
        prs = reconcile_propositions([a, b])[0]
        self.assertEqual(prs.state, "UNRESOLVED")
        self.assertEqual({r.relation_type for r in prs.relations}, {"UNRESOLVED"})

    def test_same_mine_later_status_supersedes_without_deleting_history(self):
        old = prop(
            opportunity_id="OPP-0000000000000041",
            mine_id="MINE-A",
            subject_key="application:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="verification_required",
            extracted_at="2026-10-01T10:00:00Z",
        )
        new = prop(
            opportunity_id="OPP-0000000000000042",
            mine_id="MINE-A",
            subject_key="application:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="verification_approved",
            extracted_at="2026-10-02T10:00:00Z",
        )
        prs = reconcile_propositions([old, new])[0]
        self.assertEqual(prs.state, "SUPERSEDED")
        self.assertEqual(len(prs.member_proposition_ids), 2)
        rel = next(r for r in prs.relations if r.relation_type == "SUPERSEDES")
        self.assertEqual(rel.source_proposition_id, new.proposition_id)
        self.assertEqual(rel.target_proposition_id, old.proposition_id)

    def test_multivalued_resource_types_are_qualified_not_contradictory(self):
        a = prop(
            opportunity_id="OPP-0000000000000051",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="RESOURCE_TYPE",
            predicate="resource_type",
            object_value="grant",
        )
        b = prop(
            opportunity_id="OPP-0000000000000052",
            mine_id="MINE-B",
            subject_key="program:alpha",
            proposition_type="RESOURCE_TYPE",
            predicate="resource_type",
            object_value="training",
        )
        prs = reconcile_propositions([a, b])[0]
        self.assertEqual(prs.state, "QUALIFIED")
        self.assertEqual({r.relation_type for r in prs.relations}, {"CONTEXT_FOR"})
        self.assertNotIn("CONTRADICTS", {r.relation_type for r in prs.relations})

    def test_different_mines_same_origin_are_not_independent_corroboration(self):
        a = prop(
            opportunity_id="OPP-0000000000000057",
            mine_id="MINE-GMAIL",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
            source_origin_key="hackerone.com",
        )
        b = prop(
            opportunity_id="OPP-0000000000000058",
            mine_id="MINE-HACKERONE",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
            source_origin_key="hackerone.com",
        )
        prs = reconcile_propositions([a, b])[0]
        self.assertEqual(prs.distinct_source_count, 2)
        self.assertEqual(prs.distinct_origin_count, 1)
        self.assertEqual(prs.state, "SINGLE_SOURCE")
        self.assertNotIn("SUPPORTS", {r.relation_type for r in prs.relations})

    def test_same_source_repetition_is_not_independent_corroboration(self):
        a = prop(
            opportunity_id="OPP-0000000000000061",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        b = prop(
            opportunity_id="OPP-0000000000000062",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        prs = reconcile_propositions([a, b])[0]
        self.assertEqual(prs.state, "SINGLE_SOURCE")
        self.assertEqual(prs.distinct_source_count, 1)
        self.assertNotIn("SUPPORTS", {r.relation_type for r in prs.relations})

    def test_prs_identity_survives_new_membership(self):
        a = prop(
            opportunity_id="OPP-0000000000000071",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        b = prop(
            opportunity_id="OPP-0000000000000072",
            mine_id="MINE-B",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        one = reconcile_propositions([a])[0]
        two = reconcile_propositions([a, b])[0]
        self.assertEqual(one.resolution_set_id, two.resolution_set_id)

    def test_reconciliation_is_order_independent(self):
        a = prop(
            opportunity_id="OPP-0000000000000081",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        b = prop(
            opportunity_id="OPP-0000000000000082",
            mine_id="MINE-B",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        first = [row.to_dict() for row in reconcile_propositions([a, b])]
        second = [row.to_dict() for row in reconcile_propositions([b, a])]
        self.assertEqual(first, second)

    def test_dict_roundtrip_reconciliation(self):
        a = prop(
            opportunity_id="OPP-0000000000000091",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        prs = reconcile_propositions([a.to_dict()])[0]
        self.assertEqual(prs.member_proposition_ids, [a.proposition_id])


if __name__ == "__main__":
    unittest.main()
