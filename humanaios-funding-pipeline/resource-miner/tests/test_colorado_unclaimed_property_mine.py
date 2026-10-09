import unittest
from pathlib import Path

from resource_miner.adjudication import adjudicate_resolution_sets
from resource_miner.mines import bind_opportunity, load_mines
from resource_miner.proposition import propositions_from_candidate
from resource_miner.reconciliation import reconcile_propositions
from resource_miner.source_standing import load_source_standing
from resource_miner.sources.configured_mine import discover
from resource_miner.verification_routing import compile_verification_routes
from resource_miner.work_queue import compile_verification_work_queue

ROOT = Path(__file__).resolve().parents[1]


def fake_transport(url):
    return {
        "status": 200,
        "final_url": "https://unclaimedproperty.colorado.gov/",
        "content_type": "text/html",
        "body": (
            b"<html><title>Colorado Great Colorado Payback</title>"
            b"<body>Official Colorado unclaimed property pathway.</body></html>"
        ),
    }


class ColoradoUnclaimedPropertyMineTests(unittest.TestCase):
    def setUp(self):
        self.mines = load_mines(ROOT / "data" / "mines.seed.json")
        self.mine = next(
            mine for mine in self.mines
            if mine.name == "Colorado Great Colorado Payback"
        )
        self.profiles = load_source_standing(
            ROOT / "data" / "source-standing.seed.json"
        )

    def test_registry_boundary_is_explicit(self):
        self.assertEqual(self.mine.mine_kind, "REGISTRY")
        self.assertIn("OPPORTUNITY_SOURCE", self.mine.roles)
        self.assertIn("EVIDENCE_SOURCE", self.mine.roles)
        self.assertEqual(
            self.mine.config["evidence_origins"],
            ["unclaimedproperty.colorado.gov"],
        )
        self.assertEqual(
            self.mine.config["claimant_search_policy"],
            "REQUIRE_EXPLICIT_CLAIMANT_REQUEST",
        )
        self.assertEqual(
            self.mine.config["claim_submission_policy"],
            "PROHIBITED_IN_MINE_TEST",
        )

    def test_pathway_resolves_without_claimant_search(self):
        candidates = list(discover(self.mine, transport=fake_transport))
        self.assertEqual(len(candidates), 1)
        candidate = bind_opportunity(
            self.mine,
            candidates[0],
            opportunity_source_kind="configured_endpoint",
        )
        self.assertTrue(candidate.opportunity_id.startswith("OPP-"))
        self.assertEqual(
            candidate.opportunity_kind,
            "unclaimed_property_recovery_pathway",
        )
        self.assertEqual(candidate.status, "UNKNOWN")
        self.assertFalse(candidate.eligibility_assessed)
        self.assertEqual(candidate.eligibility_status, "UNASSESSED")
        self.assertEqual(
            candidate.raw["observation"]["state"],
            "OBSERVED",
        )

    def test_current_machine_proves_pathway_not_claimant_property(self):
        candidate = bind_opportunity(
            self.mine,
            list(discover(self.mine, transport=fake_transport))[0],
            opportunity_source_kind="configured_endpoint",
        )
        propositions = propositions_from_candidate(candidate)
        proposition_types = {row.proposition_type for row in propositions}

        self.assertIn("OPPORTUNITY_EXISTS", proposition_types)
        self.assertIn("CURRENTLY_AVAILABLE", proposition_types)
        self.assertIn("RESOURCE_TYPE", proposition_types)

        # The current ontology has no claimant/property-match proposition.
        self.assertNotIn("CLAIMANT_MATCH", proposition_types)
        self.assertNotIn("PROPERTY_MATCH", proposition_types)

        resolutions = reconcile_propositions(propositions)
        adjudications = adjudicate_resolution_sets(
            resolutions,
            propositions,
            self.profiles,
        )

        by_type = {
            resolution.proposition_type: adjudication
            for resolution, adjudication in zip(resolutions, adjudications)
        }
        self.assertEqual(
            by_type["OPPORTUNITY_EXISTS"].posture,
            "PRIMARY_SOURCE_PRESENT",
        )
        self.assertEqual(
            by_type["CURRENTLY_AVAILABLE"].posture,
            "PRIMARY_SOURCE_PRESENT",
        )

        # Source category is deliberately not pre-added to the taxonomy.
        # The test should expose the ontology gap instead of concealing it.
        type_prop = next(
            row for row in propositions
            if row.proposition_type == "RESOURCE_TYPE"
        )
        self.assertEqual(type_prop.object_value, "general_resource")
        self.assertEqual(
            by_type["RESOURCE_TYPE"].posture,
            "DERIVED_ONLY",
        )

        frontier = {
            item.gap_type
            for adjudication in adjudications
            for item in adjudication.verification_frontier
        }
        self.assertIn("DIRECT_EVIDENCE_MISSING", frontier)

        work = compile_verification_work_queue(adjudications)
        routes = compile_verification_routes(work, self.mines)
        self.assertTrue(
            all(row.execution_state == "NOT_AUTHORIZED" for row in routes)
        )
        self.assertTrue(
            all(row.authority_effect == "NONE" for row in routes)
        )

        # Architectural finding: there is no claimant-search work item yet.
        self.assertFalse(
            any("CLAIMANT" in row.operation_class for row in work)
        )


if __name__ == "__main__":
    unittest.main()
