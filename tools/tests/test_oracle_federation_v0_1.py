#!/usr/bin/env python3
"""Regression tests for the #735 Workspace/Repository/Global Oracle pilot."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = ROOT / "oracles" / "engine" / "oracle_engine_v0_1.py"
FIXTURE = ROOT / "oracles" / "fixtures" / "workspace_drive_graph_2026-10-07.json"

spec = importlib.util.spec_from_file_location("oracle_engine_v0_1", ENGINE_PATH)
assert spec and spec.loader
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


class OracleFederationPilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace_snapshot = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_workspace_oracle_preserves_real_drive_contradiction(self):
        graph = oracle.WorkspaceOracle().project(self.workspace_snapshot)
        self.assertEqual(graph["authority"]["authority_effect"], "NONE")
        pairs = {
            (c["predicate"], tuple(sorted(map(str, c["observed_values"]))))
            for c in graph["conflicts"]
        }
        self.assertIn(("node_count", ("19", "22")), pairs)
        self.assertIn(("edge_count", ("44", "53")), pairs)
        self.assertTrue(all(c["resolution_state"] == "OPEN" for c in graph["conflicts"]))

    def test_repository_oracle_observes_operations_system_graph(self):
        graph = oracle.RepositoryOracle().project_operations(
            ROOT, observed_at=self.workspace_snapshot["observed_at"]
        )
        values = {
            a["predicate"]: a["value"]
            for a in graph["assertions"]
            if a["subject_ref"] == oracle.SYSTEM_GRAPH_REF
        }
        self.assertEqual(values["node_count"], 22)
        self.assertEqual(values["edge_count"], 53)
        self.assertEqual(values["generated_at"], "2026-09-13T15:12:28.926529")
        self.assertEqual(graph["authority"]["authority_effect"], "NONE")

    def test_global_oracle_reconciles_identity_without_erasing_conflict(self):
        workspace = oracle.WorkspaceOracle().project(self.workspace_snapshot)
        repository = oracle.RepositoryOracle().project_operations(
            ROOT, observed_at=self.workspace_snapshot["observed_at"]
        )
        global_graph = oracle.GlobalOracle().federate(workspace, repository)

        refs = [x["canonical_ref"] for x in global_graph["identity_reconciliations"]]
        self.assertIn(oracle.SYSTEM_GRAPH_REF, refs)
        self.assertGreaterEqual(len(global_graph["conflicts"]), 2)

        node_values = {
            a["value"]
            for a in global_graph["assertions"]
            if a["subject_ref"] == oracle.SYSTEM_GRAPH_REF
            and a["predicate"] == "node_count"
        }
        self.assertEqual(node_values, {19, 22})

    def test_candidate_change_is_advisory_and_routes_to_workbench(self):
        result = oracle.run_pilot(ROOT, self.workspace_snapshot)
        self.assertGreaterEqual(len(result["global"]["candidate_changes"]), 2)
        for candidate, route in zip(
            result["global"]["candidate_changes"], result["coordinator_routes"]
        ):
            self.assertEqual(candidate["authority_effect"], "NONE")
            self.assertFalse(candidate["can_authorize"])
            self.assertTrue(candidate["coordinator_input_only"])
            self.assertEqual(route["lane"], "WORKBENCH")
            self.assertFalse(route["details"]["admitted"])
            self.assertEqual(route["authority"]["authority_effect"], "NONE")

    def test_fail_closed_on_authority_inflation(self):
        bad = json.loads(json.dumps(self.workspace_snapshot))
        bad["authority"]["can_authorize"] = True
        with self.assertRaises(ValueError):
            oracle.WorkspaceOracle().project(bad)


if __name__ == "__main__":
    unittest.main()
