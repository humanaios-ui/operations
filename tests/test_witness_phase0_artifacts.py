from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class WitnessPhase0ArtifactsTests(unittest.TestCase):
    def test_required_phase0_artifacts_exist(self) -> None:
        required = {
            "ARTIFACT_INVENTORY.jsonl",
            "EVIDENCE_GRAPH.json",
            "GENESIS_READINESS.md",
            "WITNESS_STATE_V0_1.schema.json",
            "PARTICIPATION_CONTRACT_V0_1.schema.json",
            "WITNESS_SERVICE_CONTRACT.md",
        }
        missing = [name for name in required if not (ROOT / name).exists()]
        self.assertEqual([], missing, f"missing required Phase 0 artifacts: {missing}")

    def test_participation_contract_preserves_non_authority_boundary(self) -> None:
        schema = _load_json("PARTICIPATION_CONTRACT_V0_1.schema.json")
        props = schema["properties"]

        self.assertIn("governance_role_claim", props)
        self.assertIn("authority_resolution_ref", props)

        blocked = schema["not"]["anyOf"]
        blocked_required = {item["required"][0] for item in blocked}
        self.assertIn("effective_authority", blocked_required)
        self.assertIn("authority_granted", blocked_required)

    def test_witness_state_requires_record_based_authority_and_omission_metadata(self) -> None:
        schema = _load_json("WITNESS_STATE_V0_1.schema.json")
        self.assertEqual(
            "WITNESS_IS_NOT_THE_AUTHORITY",
            schema["properties"]["non_authority_invariant"]["const"],
        )

        authority_required = schema["properties"]["authority_context"]["required"]
        self.assertIn("effective_authority_ref", authority_required)

        omission_enum = (
            schema["properties"]["evidence_context"]["properties"]["omission_codes"]["items"]["enum"]
        )
        self.assertIn("MODEL_OMISSION", omission_enum)
        self.assertIn("INTERFACE_OMISSION", omission_enum)

    def test_evidence_graph_uses_required_types_and_edge_states(self) -> None:
        graph = _load_json("EVIDENCE_GRAPH.json")
        self.assertEqual(
            {"CLAIMED", "SPECIFIED", "IMPLEMENTED", "TESTED", "OBSERVED"},
            set(graph["edge_state_enum"]),
        )

        node_types = {node["type"] for node in graph["nodes"]}
        self.assertTrue(
            {
                "artifact",
                "claim",
                "control",
                "test",
                "evidence",
                "failure",
                "falsifier",
                "decision",
                "standard",
                "readiness_domain",
            }.issubset(node_types)
        )

    def test_inventory_contains_phase0_required_output_rows(self) -> None:
        rows = [
            json.loads(line)
            for line in (ROOT / "ARTIFACT_INVENTORY.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        artifact_ids = {row["artifact_id"] for row in rows}
        self.assertTrue(
            {
                "phase0.artifact_inventory",
                "phase0.evidence_graph",
                "phase0.genesis_readiness",
                "phase0.witness_state_schema",
                "phase0.participation_contract_schema",
                "phase0.service_contract",
            }.issubset(artifact_ids)
        )


if __name__ == "__main__":
    unittest.main()
