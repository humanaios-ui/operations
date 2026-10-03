import json
import unittest
from pathlib import Path

from resource_miner.adjudication import (
    PropositionAdjudication,
    VerificationFrontierItem,
)
from resource_miner.work_queue import compile_verification_work_queue

ROOT = Path(__file__).resolve().parents[1]


def adjudication(gap_type, *, known=None, primary=None, verification_id="VFY-1111111111111111"):
    pad_id = "PAD-2222222222222222"
    prs_id = "PRS-3333333333333333"
    vfy = VerificationFrontierItem(
        schema="humanaios.verification-frontier-item.v1",
        verification_id=verification_id,
        resolution_set_id=prs_id,
        adjudication_id=pad_id,
        gap_type=gap_type,
        requested_source_class="OFFICIAL_PRIMARY",
        proposition_type="STATUS",
        predicate="represented_status",
        subject_key="program:alpha",
        reason="fixture",
        state="OPEN",
        authority_effect="NONE",
    )
    return PropositionAdjudication(
        schema="humanaios.proposition-adjudication.v1",
        adjudication_id=pad_id,
        adjudication_token=f"urn:humanaios:proposition-adjudication:{pad_id}",
        resolution_set_id=prs_id,
        resolution_token=f"urn:humanaios:proposition-resolution:{prs_id}",
        posture="SOURCE_STANDING_UNKNOWN",
        member_proposition_ids=["PRP-4444444444444444"],
        known_origin_keys=list(known or []),
        primary_origin_keys=list(primary or []),
        nonprimary_origin_keys=[],
        unknown_origin_keys=[],
        standing_profile_ids=[],
        derived_only=False,
        verification_frontier=[vfy],
    )


class VerificationWorkQueueTests(unittest.TestCase):
    def test_schema_is_planning_only(self):
        schema = json.loads(
            (ROOT / "schemas" / "verification-work-item.v1.schema.json").read_text()
        )
        self.assertEqual(schema["properties"]["planning_state"]["const"], "PLANNED")
        self.assertEqual(
            schema["properties"]["execution_state"]["const"], "NOT_AUTHORIZED"
        )
        self.assertEqual(schema["properties"]["authority_effect"]["const"], "NONE")

    def test_gap_types_map_to_expected_operations(self):
        expected = {
            "PRIMARY_SOURCE_MISSING": "DISCOVER_PRIMARY_SOURCE",
            "DIRECT_EVIDENCE_MISSING": "SEEK_DIRECT_EVIDENCE",
            "CONFLICT_REQUIRES_RESOLUTION": "RESOLVE_CONFLICT",
            "SOURCE_STANDING_UNKNOWN": "ASSESS_SOURCE_STANDING",
            "RELATION_UNRESOLVED": "DISAMBIGUATE_RELATION",
        }
        for index, (gap, operation) in enumerate(expected.items(), start=1):
            pad = adjudication(
                gap,
                verification_id=f"VFY-{index:016X}",
            )
            item = compile_verification_work_queue([pad])[0]
            self.assertEqual(item.operation_class, operation)
            self.assertEqual(item.execution_state, "NOT_AUTHORIZED")
            self.assertEqual(item.authority_effect, "NONE")

    def test_primary_source_discovery_does_not_guess_origin(self):
        pad = adjudication(
            "PRIMARY_SOURCE_MISSING",
            known=["secondary.example"],
        )
        item = compile_verification_work_queue([pad])[0]
        self.assertEqual(item.operation_class, "DISCOVER_PRIMARY_SOURCE")
        self.assertEqual(item.candidate_origin_keys, [])

    def test_direct_evidence_prefers_known_primary_origin(self):
        pad = adjudication(
            "DIRECT_EVIDENCE_MISSING",
            known=["secondary.example", "official.example"],
            primary=["official.example"],
        )
        item = compile_verification_work_queue([pad])[0]
        self.assertEqual(item.operation_class, "SEEK_DIRECT_EVIDENCE")
        self.assertEqual(item.candidate_origin_keys, ["official.example"])

    def test_conflict_work_preserves_all_known_origins(self):
        pad = adjudication(
            "CONFLICT_REQUIRES_RESOLUTION",
            known=["official-b.example", "official-a.example"],
            primary=["official-a.example", "official-b.example"],
        )
        item = compile_verification_work_queue([pad])[0]
        self.assertEqual(item.operation_class, "RESOLVE_CONFLICT")
        self.assertEqual(
            item.candidate_origin_keys,
            ["official-a.example", "official-b.example"],
        )

    def test_queue_is_order_independent(self):
        a = adjudication(
            "PRIMARY_SOURCE_MISSING",
            verification_id="VFY-AAAAAAAAAAAAAAAA",
        )
        b = adjudication(
            "SOURCE_STANDING_UNKNOWN",
            verification_id="VFY-BBBBBBBBBBBBBBBB",
        )
        first = [row.to_dict() for row in compile_verification_work_queue([a, b])]
        second = [row.to_dict() for row in compile_verification_work_queue([b, a])]
        self.assertEqual(first, second)

    def test_resolved_frontier_item_disappears(self):
        pad = adjudication("PRIMARY_SOURCE_MISSING")
        self.assertEqual(len(compile_verification_work_queue([pad])), 1)
        pad.verification_frontier = []
        self.assertEqual(compile_verification_work_queue([pad]), [])


if __name__ == "__main__":
    unittest.main()
