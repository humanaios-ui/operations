import json
import unittest
from pathlib import Path

from resource_miner.adjudication import adjudicate_resolution_sets
from resource_miner.proposition import (
    PropositionCandidate,
    proposition_semantic_key,
    stable_proposition_id,
)
from resource_miner.reconciliation import reconcile_propositions
from resource_miner.source_standing import (
    load_source_standing,
    source_standing_from_dict,
)

ROOT = Path(__file__).resolve().parents[1]


def prop(
    *,
    opportunity_id,
    origin,
    mine_id,
    subject_key,
    proposition_type,
    predicate,
    object_value,
    epistemic_role="SOURCE_ASSERTION",
    extracted_at="2026-10-03T12:00:00Z",
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
        epistemic_role=epistemic_role,
        subject=f"urn:humanaios:resource-opportunity:{opportunity_id}",
        predicate=predicate,
        object_value=object_value,
        statement=f"{predicate} = {object_value}",
        semantic_key=key,
        resolution_subject_key=subject_key,
        source_origin_key=origin,
        extracted_at=extracted_at,
        extraction_method="NORMALIZER_EXTRACTION",
        extraction_confidence=None,
        evidence=[],
        source_url=f"https://{origin}/source",
        mine_id=mine_id,
        mine_name=mine_id,
        authority_effect="NONE",
    )


def standing(origin, source_class, types):
    return source_standing_from_dict(
        {
            "schema": "humanaios.source-standing-profile.v1",
            "origin_key": origin,
            "source_class": source_class,
            "standing_for_types": types,
            "standing_for_predicates": [],
            "independence_group": origin,
            "notes": [],
            "authority_effect": "NONE",
        }
    )


class EvidenceAdjudicationTests(unittest.TestCase):
    def test_seed_source_standing_loads_with_stable_ids(self):
        rows = load_source_standing(ROOT / "data" / "source-standing.seed.json")
        self.assertGreaterEqual(len(rows), 2)
        self.assertTrue(all(row.profile_id.startswith("SSP-") for row in rows))
        self.assertTrue(all(row.authority_effect == "NONE" for row in rows))

    def test_schemas_preserve_non_authority_boundary(self):
        pad = json.loads(
            (ROOT / "schemas" / "proposition-adjudication.v1.schema.json").read_text()
        )
        vfy = json.loads(
            (ROOT / "schemas" / "verification-frontier-item.v1.schema.json").read_text()
        )
        self.assertEqual(pad["properties"]["truth_state"]["const"], "NOT_DETERMINED")
        self.assertEqual(pad["properties"]["authorization_state"]["const"], "NOT_REQUESTED")
        self.assertEqual(pad["properties"]["authority_effect"]["const"], "NONE")
        self.assertEqual(vfy["properties"]["authority_effect"]["const"], "NONE")

    def test_primary_source_improves_posture_without_declaring_truth(self):
        p = prop(
            opportunity_id="OPP-1000000000000001",
            origin="official.example",
            mine_id="MINE-OFFICIAL",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        prs = reconcile_propositions([p])
        pads = adjudicate_resolution_sets(
            prs,
            [p],
            [standing("official.example", "OFFICIAL_PRIMARY", ["STATUS"])],
        )
        pad = pads[0]
        self.assertEqual(pad.posture, "PRIMARY_SOURCE_PRESENT")
        self.assertEqual(pad.truth_state, "NOT_DETERMINED")
        self.assertEqual(pad.authorization_state, "NOT_REQUESTED")
        self.assertEqual(pad.verification_frontier, [])

    def test_two_secondary_origins_need_primary_source(self):
        a = prop(
            opportunity_id="OPP-1000000000000002",
            origin="secondary-a.example",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        b = prop(
            opportunity_id="OPP-1000000000000003",
            origin="secondary-b.example",
            mine_id="MINE-B",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        profiles = [
            standing("secondary-a.example", "SECONDARY_REPORT", ["STATUS"]),
            standing("secondary-b.example", "SECONDARY_REPORT", ["STATUS"]),
        ]
        pad = adjudicate_resolution_sets(
            reconcile_propositions([a, b]), [a, b], profiles
        )[0]
        self.assertEqual(pad.posture, "MULTI_ORIGIN_NO_PRIMARY")
        self.assertEqual(pad.primary_origin_keys, [])
        self.assertIn(
            "PRIMARY_SOURCE_MISSING",
            {row.gap_type for row in pad.verification_frontier},
        )
        self.assertEqual(pad.truth_state, "NOT_DETERMINED")

    def test_official_page_machine_classification_remains_derived(self):
        p = prop(
            opportunity_id="OPP-1000000000000004",
            origin="official.example",
            mine_id="MINE-OFFICIAL",
            subject_key="program:alpha",
            proposition_type="RESOURCE_TYPE",
            predicate="resource_type",
            object_value="grant",
            epistemic_role="CLASSIFICATION",
        )
        profile = standing(
            "official.example",
            "OFFICIAL_PRIMARY",
            ["RESOURCE_TYPE"],
        )
        pad = adjudicate_resolution_sets(
            reconcile_propositions([p]), [p], [profile]
        )[0]
        self.assertEqual(pad.posture, "DERIVED_ONLY")
        self.assertEqual(pad.primary_origin_keys, ["official.example"])
        gaps = {row.gap_type for row in pad.verification_frontier}
        self.assertIn("DIRECT_EVIDENCE_MISSING", gaps)
        self.assertNotIn("PRIMARY_SOURCE_MISSING", gaps)
        self.assertEqual(pad.truth_state, "NOT_DETERMINED")

    def test_contested_sources_emit_conflict_frontier_not_winner(self):
        a = prop(
            opportunity_id="OPP-1000000000000005",
            origin="official-a.example",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="CURRENTLY_AVAILABLE",
            predicate="currently_available",
            object_value=True,
        )
        b = prop(
            opportunity_id="OPP-1000000000000006",
            origin="official-b.example",
            mine_id="MINE-B",
            subject_key="program:alpha",
            proposition_type="CURRENTLY_AVAILABLE",
            predicate="currently_available",
            object_value=False,
        )
        profiles = [
            standing(
                "official-a.example",
                "OFFICIAL_PRIMARY",
                ["CURRENTLY_AVAILABLE"],
            ),
            standing(
                "official-b.example",
                "OFFICIAL_PRIMARY",
                ["CURRENTLY_AVAILABLE"],
            ),
        ]
        pad = adjudicate_resolution_sets(
            reconcile_propositions([a, b]), [a, b], profiles
        )[0]
        self.assertEqual(pad.posture, "CONTESTED")
        self.assertIn(
            "CONFLICT_REQUIRES_RESOLUTION",
            {row.gap_type for row in pad.verification_frontier},
        )
        self.assertEqual(pad.truth_state, "NOT_DETERMINED")

    def test_unknown_source_standing_fails_closed(self):
        p = prop(
            opportunity_id="OPP-1000000000000007",
            origin="unknown.example",
            mine_id="MINE-X",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        pad = adjudicate_resolution_sets(
            reconcile_propositions([p]), [p], []
        )[0]
        self.assertEqual(pad.posture, "SOURCE_STANDING_UNKNOWN")
        gaps = {row.gap_type for row in pad.verification_frontier}
        self.assertIn("SOURCE_STANDING_UNKNOWN", gaps)
        self.assertIn("PRIMARY_SOURCE_MISSING", gaps)

    def test_source_standing_is_scoped_not_global_prestige(self):
        p = prop(
            opportunity_id="OPP-1000000000000008",
            origin="official.example",
            mine_id="MINE-OFFICIAL",
            subject_key="program:alpha",
            proposition_type="RESOURCE_TYPE",
            predicate="resource_type",
            object_value="grant",
            epistemic_role="CLASSIFICATION",
        )
        profile = standing(
            "official.example",
            "OFFICIAL_PRIMARY",
            ["CURRENTLY_AVAILABLE"],
        )
        pad = adjudicate_resolution_sets(
            reconcile_propositions([p]), [p], [profile]
        )[0]
        self.assertEqual(pad.posture, "DERIVED_ONLY")
        self.assertEqual(pad.primary_origin_keys, [])
        self.assertIn(
            "SOURCE_STANDING_UNKNOWN",
            {row.gap_type for row in pad.verification_frontier},
        )

    def test_primary_source_arrival_closes_primary_source_gap(self):
        secondary = prop(
            opportunity_id="OPP-1000000000000011",
            origin="secondary.example",
            mine_id="MINE-S",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        official = prop(
            opportunity_id="OPP-1000000000000012",
            origin="official.example",
            mine_id="MINE-O",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        profiles = [
            standing("secondary.example", "SECONDARY_REPORT", ["STATUS"]),
            standing("official.example", "OFFICIAL_PRIMARY", ["STATUS"]),
        ]
        before = adjudicate_resolution_sets(
            reconcile_propositions([secondary]),
            [secondary],
            profiles,
        )[0]
        self.assertIn(
            "PRIMARY_SOURCE_MISSING",
            {row.gap_type for row in before.verification_frontier},
        )

        after = adjudicate_resolution_sets(
            reconcile_propositions([secondary, official]),
            [secondary, official],
            profiles,
        )[0]
        self.assertEqual(after.posture, "PRIMARY_SOURCE_PRESENT")
        self.assertNotIn(
            "PRIMARY_SOURCE_MISSING",
            {row.gap_type for row in after.verification_frontier},
        )

    def test_direct_assertion_arrival_closes_derived_only_gap(self):
        derived = prop(
            opportunity_id="OPP-1000000000000013",
            origin="official.example",
            mine_id="MINE-O",
            subject_key="program:alpha",
            proposition_type="RESOURCE_TYPE",
            predicate="resource_type",
            object_value="grant",
            epistemic_role="CLASSIFICATION",
        )
        direct = prop(
            opportunity_id="OPP-1000000000000014",
            origin="official.example",
            mine_id="MINE-O",
            subject_key="program:alpha",
            proposition_type="RESOURCE_TYPE",
            predicate="resource_type",
            object_value="grant",
            epistemic_role="SOURCE_ASSERTION",
        )
        profiles = [
            standing("official.example", "OFFICIAL_PRIMARY", ["RESOURCE_TYPE"])
        ]
        before = adjudicate_resolution_sets(
            reconcile_propositions([derived]),
            [derived],
            profiles,
        )[0]
        self.assertIn(
            "DIRECT_EVIDENCE_MISSING",
            {row.gap_type for row in before.verification_frontier},
        )

        after = adjudicate_resolution_sets(
            reconcile_propositions([derived, direct]),
            [derived, direct],
            profiles,
        )[0]
        self.assertEqual(after.posture, "PRIMARY_SOURCE_PRESENT")
        self.assertNotIn(
            "DIRECT_EVIDENCE_MISSING",
            {row.gap_type for row in after.verification_frontier},
        )

    def test_verification_frontier_is_order_independent(self):
        a = prop(
            opportunity_id="OPP-1000000000000009",
            origin="secondary-a.example",
            mine_id="MINE-A",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        b = prop(
            opportunity_id="OPP-1000000000000010",
            origin="secondary-b.example",
            mine_id="MINE-B",
            subject_key="program:alpha",
            proposition_type="STATUS",
            predicate="represented_status",
            object_value="open",
        )
        profiles = [
            standing("secondary-a.example", "SECONDARY_REPORT", ["STATUS"]),
            standing("secondary-b.example", "SECONDARY_REPORT", ["STATUS"]),
        ]
        first = [
            row.to_dict()
            for row in adjudicate_resolution_sets(
                reconcile_propositions([a, b]), [a, b], profiles
            )
        ]
        second = [
            row.to_dict()
            for row in adjudicate_resolution_sets(
                reconcile_propositions([b, a]), [b, a], list(reversed(profiles))
            )
        ]
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
