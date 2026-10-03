import json
import unittest
from pathlib import Path

from resource_miner.mines import load_mines
from resource_miner.verification_routing import compile_verification_routes
from resource_miner.work_queue import VerificationWorkItem

ROOT = Path(__file__).resolve().parents[1]


def work(
    operation_class,
    *,
    work_id="VWK-1111111111111111",
    candidate_origins=None,
):
    return VerificationWorkItem(
        schema="humanaios.verification-work-item.v1",
        work_id=work_id,
        verification_id="VFY-2222222222222222",
        adjudication_id="PAD-3333333333333333",
        resolution_set_id="PRS-4444444444444444",
        subject_key="program:alpha",
        operation_class=operation_class,
        requested_source_class="OFFICIAL_PRIMARY",
        candidate_origin_keys=list(candidate_origins or []),
        closure_condition="fixture",
        planning_state="PLANNED",
        execution_state="NOT_AUTHORIZED",
        authority_effect="NONE",
    )


class VerificationRoutingTests(unittest.TestCase):
    def setUp(self):
        self.mines = load_mines(ROOT / "data" / "mines.seed.json")

    def test_schema_preserves_execution_boundary(self):
        schema = json.loads(
            (ROOT / "schemas" / "verification-route.v1.schema.json").read_text()
        )
        self.assertEqual(
            schema["properties"]["execution_state"]["const"], "NOT_AUTHORIZED"
        )
        self.assertEqual(schema["properties"]["authority_effect"]["const"], "NONE")

    def test_direct_evidence_binds_to_existing_microsoft_mine(self):
        item = work(
            "SEEK_DIRECT_EVIDENCE",
            candidate_origins=["learn.microsoft.com"],
        )
        route = compile_verification_routes([item], self.mines)[0]
        microsoft = next(
            mine for mine in self.mines if mine.name == "Microsoft for Startups"
        )
        self.assertEqual(route.route_type, "EXISTING_MINE_REOBSERVE")
        self.assertEqual(route.capability_state, "AVAILABLE")
        self.assertEqual(route.target_mine_ids, [microsoft.mine_id])
        self.assertEqual(route.target_origin_keys, ["learn.microsoft.com"])
        self.assertEqual(route.execution_state, "NOT_AUTHORIZED")

    def test_known_origin_without_mine_stays_unbound(self):
        item = work(
            "SEEK_DIRECT_EVIDENCE",
            candidate_origins=["official.example"],
        )
        route = compile_verification_routes([item], self.mines)[0]
        self.assertEqual(route.route_type, "KNOWN_ORIGIN_REVIEW")
        self.assertEqual(route.capability_state, "UNBOUND")
        self.assertEqual(route.target_mine_ids, [])
        self.assertEqual(route.target_origin_keys, ["official.example"])

    def test_primary_source_discovery_does_not_invent_target(self):
        item = work("DISCOVER_PRIMARY_SOURCE")
        route = compile_verification_routes([item], self.mines)[0]
        self.assertEqual(route.route_type, "DISCOVERY_REQUIRED")
        self.assertEqual(route.capability_state, "DISCOVERY_REQUIRED")
        self.assertEqual(route.target_mine_ids, [])
        self.assertEqual(route.target_origin_keys, [])

    def test_conflict_always_routes_to_resolver_boundary(self):
        item = work(
            "RESOLVE_CONFLICT",
            candidate_origins=["hackerone.com", "learn.microsoft.com"],
        )
        route = compile_verification_routes([item], self.mines)[0]
        self.assertEqual(route.route_type, "RESOLVER_REQUIRED")
        self.assertEqual(route.capability_state, "RESOLVER_REQUIRED")
        self.assertEqual(
            route.target_origin_keys,
            ["hackerone.com", "learn.microsoft.com"],
        )
        self.assertEqual(route.target_mine_ids, [])

    def test_source_standing_work_routes_to_review(self):
        item = work(
            "ASSESS_SOURCE_STANDING",
            candidate_origins=["unknown.example"],
        )
        route = compile_verification_routes([item], self.mines)[0]
        self.assertEqual(route.route_type, "SOURCE_STANDING_REVIEW")
        self.assertEqual(route.capability_state, "REVIEW_REQUIRED")

    def test_relation_disambiguation_requires_discovery(self):
        item = work(
            "DISAMBIGUATE_RELATION",
            candidate_origins=["a.example", "b.example"],
        )
        route = compile_verification_routes([item], self.mines)[0]
        self.assertEqual(route.route_type, "DISCOVERY_REQUIRED")
        self.assertEqual(route.capability_state, "DISCOVERY_REQUIRED")
        self.assertEqual(route.target_mine_ids, [])

    def test_routes_are_order_independent(self):
        a = work(
            "SEEK_DIRECT_EVIDENCE",
            work_id="VWK-AAAAAAAAAAAAAAAA",
            candidate_origins=["learn.microsoft.com"],
        )
        b = work(
            "DISCOVER_PRIMARY_SOURCE",
            work_id="VWK-BBBBBBBBBBBBBBBB",
        )
        first = [
            row.to_dict()
            for row in compile_verification_routes([a, b], self.mines)
        ]
        second = [
            row.to_dict()
            for row in compile_verification_routes([b, a], reversed(self.mines))
        ]
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
