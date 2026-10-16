"""Contract falsifiers for observational graph interchange. Run: python -m unittest discover -s tests -p 'test_graph_projection_contract.py' -v"""
import copy
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "docs/graph_integration/observation_projection_v0.schema.json").read_text(encoding="utf-8"))

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None
    FormatChecker = None

VALID = {
    "schema_version": "humanaios.graph.observation_projection.v0",
    "projection_id": "atlas:sha123",
    "source": {
        "system": "codebase_atlas", "source_ref": "humanaios-ui/operations",
        "revision": "a" * 40, "observed_at": "2026-10-16T10:00:00Z",
        "visibility": "internal",
    },
    "nodes": [
        {"id": "file:A", "kind": "source_file",
         "evidence": {"kind": "source_file", "reference": "src/a.py:2", "state": "observed"}},
        {"id": "file:B", "kind": "source_file",
         "evidence": {"kind": "inference", "reference": "unmatched target", "state": "unresolved"}},
    ],
    "edges": [
        {"id": "edge:1", "from": "file:A", "to": "file:B", "relation": "imports",
         "evidence": {"kind": "source_file", "reference": "src/a.py:2", "state": "observed"}},
    ],
}

def validate(record):
    """Schema and cross-record validity. Never verifies authenticity or admission."""
    if Draft202012Validator is None:
        raise RuntimeError("Install jsonschema to run graph contract tests; refusing false green")
    Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(record)
    nodes = [n["id"] for n in record["nodes"]]
    edges = [e["id"] for e in record["edges"]]
    if len(nodes) != len(set(nodes)) or len(edges) != len(set(edges)):
        raise ValueError("duplicate graph identifiers")
    ids = set(nodes)
    if any(e["from"] not in ids or e["to"] not in ids for e in record["edges"]):
        raise ValueError("dangling graph endpoint")
    if record["source"]["visibility"] == "private":
        # This is a schema boundary, not permission to disclose private records.
        if any(n["evidence"]["state"] == "redacted" and n.get("label") for n in record["nodes"]):
            raise ValueError("redacted private record leaks label")

@unittest.skipIf(Draft202012Validator is None, "jsonschema dependency unavailable; test must be rerun in protected CI")
class ProjectionContractTests(unittest.TestCase):
    def test_valid_observation(self):
        validate(copy.deepcopy(VALID))

    def test_missing_provenance_is_rejected(self):
        value = copy.deepcopy(VALID)
        del value["nodes"][0]["evidence"]
        with self.assertRaises(Exception):
            validate(value)

    def test_authority_injection_is_rejected(self):
        value = copy.deepcopy(VALID)
        value["admission_approved"] = True
        with self.assertRaises(Exception):
            validate(value)

    def test_forged_verified_state_is_rejected(self):
        value = copy.deepcopy(VALID)
        value["nodes"][0]["evidence"]["state"] = "verified"
        with self.assertRaises(Exception):
            validate(value)

    def test_unknown_revision_rejected(self):
        value = copy.deepcopy(VALID)
        value["source"]["revision"] = ""
        with self.assertRaises(Exception):
            validate(value)

    def test_unresolved_nodes_allowed_explicitly(self):
        validate(copy.deepcopy(VALID))

    def test_dangling_edge_rejected(self):
        value = copy.deepcopy(VALID)
        value["edges"][0]["to"] = "missing"
        with self.assertRaises(ValueError):
            validate(value)

    def test_duplicate_node_rejected(self):
        value = copy.deepcopy(VALID)
        value["nodes"].append(copy.deepcopy(value["nodes"][0]))
        with self.assertRaises(ValueError):
            validate(value)

    def test_private_redaction_leak_rejected(self):
        value = copy.deepcopy(VALID)
        value["source"]["visibility"] = "private"
        value["nodes"][1]["evidence"]["state"] = "redacted"
        value["nodes"][1]["label"] = "secret content"
        with self.assertRaises(ValueError):
            validate(value)

    def test_malformed_timestamp_rejected(self):
        value = copy.deepcopy(VALID)
        value["source"]["observed_at"] = "yesterday"
        with self.assertRaises(Exception):
            validate(value)


if __name__ == "__main__":
    unittest.main()
