import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crb.gate import ADVANCE, HOLD, compute_gate, evaluate_independence
from crb.graph_bridge import build_projection, validate
from crb.prp import event_hash, package_root, verify_event_chain


class GateTests(unittest.TestCase):
    def test_internal_profile_satisfies(self):
        result = evaluate_independence(
            {"S": 1, "C": 2, "T": 1, "O": 0, "D": 1},
            "INTERNAL_MACHINE_INDEPENDENT",
        )
        self.assertTrue(result.satisfied)

    def test_external_requires_external_operator(self):
        result = evaluate_independence(
            {"S": 2, "C": 2, "T": 2, "O": 1, "D": 2},
            "EXTERNALLY_REPLAYED",
            external_replay_performed=True,
        )
        self.assertFalse(result.satisfied)
        self.assertIn("O:1<2", result.deficits)

    def test_disqualifier_blocks(self):
        result = evaluate_independence(
            {"S": 2, "C": 2, "T": 2, "O": 2, "D": 2},
            "EXTERNALLY_REPLAYED",
            external_replay_performed=True,
            disqualifiers=["FIRST_PASS_CONTEXT_LEAK"],
        )
        self.assertFalse(result.satisfied)

    def test_gate_is_mechanical(self):
        self.assertEqual(
            compute_gate(
                ["SUPPORTED", "SUPPORTED", "SUPPORTED"],
                evidence_integrity="VALID",
                process_integrity="VALID",
                independence_satisfied=True,
                unresolved_critical_challenges=0,
            ),
            ADVANCE,
        )
        self.assertEqual(
            compute_gate(
                ["SUPPORTED", "NOT_SUPPORTED", "SUPPORTED"],
                evidence_integrity="VALID",
                process_integrity="VALID",
                independence_satisfied=True,
                unresolved_critical_challenges=0,
            ),
            HOLD,
        )


class PackageTests(unittest.TestCase):
    def test_digest_excludes_its_own_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "receipts").mkdir()
            (root / "claim.txt").write_text("claim", encoding="utf-8")
            before = package_root(root)
            (root / "receipts" / "package.sha256").write_text(before, encoding="utf-8")
            after = package_root(root)
            self.assertEqual(before, after)

    def test_event_chain(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.jsonl"
            first = {
                "seq": 1,
                "event_type": "SUBMITTED",
                "artifact_refs": [],
                "prev_event_hash": None,
            }
            first["event_hash"] = event_hash(first)
            second = {
                "seq": 2,
                "event_type": "EVIDENCE_FROZEN",
                "artifact_refs": ["evidence:root"],
                "prev_event_hash": first["event_hash"],
            }
            second["event_hash"] = event_hash(second)
            path.write_text(
                json.dumps(first, sort_keys=True) + "\n" +
                json.dumps(second, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(verify_event_chain(path), (True, "VALID"))


class GraphBridgeTests(unittest.TestCase):
    def test_graph_contract_is_closed(self):
        result = validate()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["counts"]["capability_stages"], 11)
        self.assertEqual(result["counts"]["change_levels"], 5)
        self.assertEqual(result["counts"]["graph_delta_events"], 6)
        self.assertEqual(result["counts"]["projection_types"], 3)
        self.assertEqual(result["counts"]["tier_mapped_levels"], 5)
        self.assertEqual(result["counts"]["workflows"], 6)

    def test_molt_tier_mapping_is_recorded_not_enforced(self):
        morphogenesis = json.loads(
            (Path(__file__).resolve().parents[1] / "crb" / "morphogenesis.json").read_text()
        )
        mapping = morphogenesis["molt_tier_mapping"]
        self.assertEqual(mapping["status"], "RECORDED_NON_ENFORCING")
        by_level = {entry["level"]: entry for entry in mapping["levels"]}
        self.assertEqual(by_level["CHANGE-L1"]["measured_tier"], 1)
        self.assertEqual(by_level["CHANGE-L3"]["measured_tier"], 2)
        self.assertEqual(by_level["CHANGE-L4"]["measured_tier"], 2)
        # The two places the path classifier under-measures are named, not hidden.
        self.assertIsNotNone(by_level["CHANGE-L2"]["gap"])
        self.assertIsNotNone(by_level["CHANGE-L4"]["gap"])

    def test_projection_has_no_dangling_local_edges(self):
        projection = build_projection()
        node_ids = {n["id"] for n in projection["nodes"]}
        for edge in projection["edges"]:
            self.assertIn(edge["from"], node_ids)
            self.assertIn(edge["to"], node_ids)

    def test_projection_contains_governed_graph_delta_lifecycle(self):
        projection = build_projection()
        edges = {
            (edge["from"], edge["to"], edge["rel"])
            for edge in projection["edges"]
        }
        self.assertIn(
            ("MORPHOGENIC_SIGNAL", "GRAPH_DELTA_CANDIDATE", "triggers_candidate"),
            edges,
        )
        self.assertIn(
            ("GRAPH_DELTA_REVIEW", "GRAPH_DELTA_AUTHORIZATION", "warrants"),
            edges,
        )
        self.assertIn(
            ("GRAPH_DELTA_CANDIDATE", "CHANGE-L3", "classified_as"),
            edges,
        )

    def test_projection_exposes_hep_specializations(self):
        projection = build_projection()
        nodes = {node["id"]: node for node in projection["nodes"]}
        self.assertEqual(nodes["HEP-PRP"]["specializes"], "HEP")
        self.assertEqual(nodes["HEP-AUTH"]["specializes"], "HEP")
        edges = {
            (edge["from"], edge["to"], edge["rel"])
            for edge in projection["edges"]
        }
        self.assertIn(("CRB-PRP", "HEP-PRP", "specializes_as"), edges)
        self.assertIn(("HEP-AUTH", "CRB-EXT", "reconstructable_by"), edges)

    def test_validate_rejects_missing_change_hierarchy_baseline(self):
        original = Path("crb/morphogenesis.json").read_text(encoding="utf-8")
        mutated = json.loads(original)
        mutated["change_hierarchy"] = mutated["change_hierarchy"][1:]

        def fake_load_json(path):
            if path == "crb/morphogenesis.json":
                return mutated
            return json.loads(Path(path).read_text(encoding="utf-8"))

        with patch("crb.graph_bridge.load_json", side_effect=fake_load_json):
            result = validate()

        self.assertFalse(result["valid"])
        self.assertIn(
            "change hierarchy must include CHANGE-L0..CHANGE-L4 with matching levels",
            result["errors"],
        )

    def test_validate_rejects_missing_graph_delta_lifecycle_event(self):
        original = Path("crb/morphogenesis.json").read_text(encoding="utf-8")
        mutated = json.loads(original)
        mutated["event_types"] = [
            entry
            for entry in mutated["event_types"]
            if entry["id"] != "GRAPH_DELTA_AUTHORIZATION"
        ]

        def fake_load_json(path):
            if path == "crb/morphogenesis.json":
                return mutated
            return json.loads(Path(path).read_text(encoding="utf-8"))

        with patch("crb.graph_bridge.load_json", side_effect=fake_load_json):
            result = validate()

        self.assertFalse(result["valid"])
        self.assertIn(
            "graph delta event types must include the governed review lifecycle",
            result["errors"],
        )

    def test_validate_rejects_incomplete_review_requirements(self):
        original = Path("crb/morphogenesis.json").read_text(encoding="utf-8")
        mutated = json.loads(original)
        mutated["review_requirements"] = [
            field
            for field in mutated["review_requirements"]
            if field != "rollback_plan"
        ]

        def fake_load_json(path):
            if path == "crb/morphogenesis.json":
                return mutated
            return json.loads(Path(path).read_text(encoding="utf-8"))

        with patch("crb.graph_bridge.load_json", side_effect=fake_load_json):
            result = validate()

        self.assertFalse(result["valid"])
        self.assertIn(
            "graph delta review requirements must match the expected contract",
            result["errors"],
        )

    def test_validate_rejects_unknown_review_requirements(self):
        original = Path("crb/morphogenesis.json").read_text(encoding="utf-8")
        mutated = json.loads(original)
        mutated["review_requirements"] = list(mutated["review_requirements"]) + [
            "unsupported_field"
        ]

        def fake_load_json(path):
            if path == "crb/morphogenesis.json":
                return mutated
            return json.loads(Path(path).read_text(encoding="utf-8"))

        with patch("crb.graph_bridge.load_json", side_effect=fake_load_json):
            result = validate()

        self.assertFalse(result["valid"])
        self.assertIn(
            "graph delta review requirements must match the expected contract",
            result["errors"],
        )


if __name__ == "__main__":
    unittest.main()
