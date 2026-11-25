"""Read-only routing of reviewed public resource to seeded HumanAIOS needs."""
from __future__ import annotations
import json
from pathlib import Path
import unittest

from resource_miner.resource_utility import project_resource_utility

ROOT = Path(__file__).resolve().parents[1]
NEEDS = json.loads((ROOT / "data/needs.seed.json").read_text())


def row(title, state="SOURCE_WORKING", flags=()):
    return {"resource_title": title, "source_url": "https://example.org/public",
            "reported_status": state, "review_flags": list(flags)}


class ResourceUtilityTests(unittest.TestCase):
    def test_recommends_distinct_project_needs_without_control_claims(self):
        graph = project_resource_utility([
            row("Cerebras Free API"), row("Phoenix Arize OSS"),
            row("Supabase Free Tier"), row("GitHub Sponsors"),
            row("NSF SBIR STTR Phase I"), row("Apart Research Hackathons"),
        ], NEEDS)
        self.assertEqual(graph["edge_count"], 6)
        mapped = {e["resource_title"]: (e["need_id"], e["workstream"])
                  for e in graph["edges"]}
        self.assertEqual(mapped["Cerebras Free API"][0], "compute-infrastructure")
        self.assertIn("observability", mapped["Phoenix Arize OSS"][1].lower())
        self.assertEqual(mapped["Supabase Free Tier"][0], "compute-infrastructure")
        self.assertEqual(mapped["GitHub Sponsors"][0], "revenue-capital")
        self.assertEqual(mapped["Apart Research Hackathons"][0], "research-collaboration")
        self.assertFalse(graph["delivery_executed"])
        self.assertFalse(graph["resource_ownership_established"])
        self.assertFalse(graph["recovery_outcome_established"])
        self.assertEqual(graph["authority_effect"], "NONE")
        for e in graph["edges"]:
            self.assertEqual(e["resource_control"], "NOT_ESTABLISHED")
            self.assertEqual(e["authority_effect"], "NONE")

    def test_conflicting_or_failed_source_can_only_propose_recheck(self):
        graph = project_resource_utility([
            row("Research grant", flags=["SOURCE_STATUS_NOTE_CONFLICT_RECHECK_REQUIRED"]),
            row("Mozilla grant", state="LINK_FAILED_404"),
        ], NEEDS)
        self.assertEqual(graph["edge_count"], 2)
        self.assertTrue(all(e["next_gate"]=="INDEPENDENT_SOURCE_RECHECK"
                            for e in graph["edges"]))

    def test_refuses_url_with_query_or_inline_private_identity(self):
        for url in ("https://example.org/?session=private",
                    "https://person@example.org/resource"):
            record = row("Cerebras")
            record["source_url"] = url
            with self.assertRaises(ValueError):
                project_resource_utility([record], NEEDS)

    def test_rejects_unknown_need_graph_nodes(self):
        with self.assertRaises(ValueError):
            project_resource_utility([row("Cerebras")],
                                     [{"need_id": "USER_CREATED_ADMIN_EXECUTOR"}])


if __name__ == "__main__":
    unittest.main()
