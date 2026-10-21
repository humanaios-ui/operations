"""Negative controls for the read-only #630 × #835 × #841 dashboard bridge."""
import importlib.util
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parent / "observation_bridge.py"
spec = importlib.util.spec_from_file_location("observation_bridge", PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
SHA = "a" * 40


def fixtures():
    rkg = {"authority_effect": "NONE", "graph_kind": "DERIVED_READ_MODEL",
           "source": {"repository": bridge.REPO, "head_commit": SHA, "worktree_state": "CLEAN"},
           "validation": {"valid": True},
           "nodes": [{"id": "artifact:REGISTERED.md", "type": "artifact", "label": "REGISTERED.md"}],
           "edges": []}
    atlas = {"authority_effect": "NONE", "merge_authority": False,
             "repository": bridge.REPO, "head_sha": SHA,
             "worktree_clean": True, "snapshot": "HEAD_WORKTREE",
             "nodes": [{"id": "session", "label": "Session"}, {"id": "governance", "label": "Governance"}],
             "edges": [{"source": "session", "target": "governance",
                        "kind": "doc_link", "evidence": [{"source": "REGISTERED.md", "target": "SEED.md", "line": 3}]}]}
    timeline = {"head": "historical", "source_head_sha": SHA, "nodes": [{"id": "REG", "name": "Registry",
                 "first_seen": "2026-09-01", "files": ["REGISTERED.md"], "date_source": "fallback"}], "edges": []}
    return rkg, atlas, timeline


class TestProjection(unittest.TestCase):
    def test_smoke(self):
        bridge.smoke_test()

    def test_exact_path_and_no_authority(self):
        inputs = fixtures()
        inputs[0]["edges"] = [{"from": "artifact:REGISTERED.md", "to": "artifact:REGISTERED.md"}]
        inputs[2]["edges"] = [{"source": "REG", "target": "REG"}]
        result = bridge.project(*inputs)
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertFalse(result["can_authorize"])
        self.assertFalse(result["merge_authority"])
        self.assertIn("EXACT_PATH_WITNESS", [e["relation"] for e in result["edges"]])
        self.assertIn("SOURCE_EDGE", [e["relation"] for e in result["edges"]])
        self.assertIn("TIMELINE_SOURCE_EDGE", [e["relation"] for e in result["edges"]])
        self.assertIn("FALLBACK_DATE", [e["standing"] for e in result["edges"]])

    def test_stale_head_rejected(self):
        rkg, atlas, timeline = fixtures()
        atlas["head_sha"] = "b" * 40
        with self.assertRaises(ValueError):
            bridge.project(rkg, atlas, timeline)

    def test_historical_source_head_rejected(self):
        rkg, atlas, timeline = fixtures()
        timeline["source_head_sha"] = "c" * 40
        with self.assertRaises(ValueError):
            bridge.project(rkg, atlas, timeline)

    def test_forged_atlas_worktree_rejected(self):
        rkg, atlas, timeline = fixtures()
        atlas["worktree_clean"] = False
        with self.assertRaises(ValueError):
            bridge.project(rkg, atlas, timeline)

    def test_dirty_rkg_rejected(self):
        rkg, atlas, timeline = fixtures()
        rkg["source"]["worktree_state"] = "DIRTY"
        with self.assertRaises(ValueError):
            bridge.project(rkg, atlas, timeline)

    def test_reject_false_auth(self):
        rkg, atlas, timeline = fixtures()
        atlas["authority_effect"] = "Z2"
        with self.assertRaises(ValueError):
            bridge.project(rkg, atlas, timeline)

    def test_reject_unvalidated_rkg(self):
        rkg, atlas, timeline = fixtures()
        rkg["validation"]["valid"] = False
        with self.assertRaises(ValueError):
            bridge.project(rkg, atlas, timeline)

    def test_fuzzy_label_not_identity(self):
        rkg, atlas, timeline = fixtures()
        rkg["nodes"][0]["id"] = "note:REGISTERED.md"
        result = bridge.project(rkg, atlas, timeline)
        self.assertNotIn("EXACT_PATH_WITNESS", [e["relation"] for e in result["edges"]])

    def test_deterministic(self):
        self.assertEqual(bridge.project(*fixtures()), bridge.project(*fixtures()))

    def test_record_identifiers_and_endpoints_must_be_strings(self):
        cases = ((0, "nodes", "id"), (0, "edges", "from"), (0, "edges", "to"),
                 (1, "nodes", "id"), (1, "edges", "source"), (1, "edges", "target"),
                 (2, "nodes", "id"), (2, "edges", "source"), (2, "edges", "target"))
        missing = object()
        for source, collection, field in cases:
            for value in (missing, None, 1, True, [], {}):
                with self.subTest(source=source, collection=collection, field=field, value=value):
                    inputs = fixtures()
                    inputs[0]["edges"] = [{"from": "artifact:REGISTERED.md", "to": "artifact:REGISTERED.md"}]
                    inputs[2]["edges"] = [{"source": "REG", "target": "REG"}]
                    record = inputs[source][collection][0]
                    if value is missing:
                        record.pop(field)
                    else:
                        record[field] = value
                    with self.assertRaises(ValueError):
                        bridge.project(*inputs)

    def test_non_object_records_rejected(self):
        for source in range(3):
            for collection in ("nodes", "edges"):
                for value in (None, 1, "record", []):
                    with self.subTest(source=source, collection=collection, value=value):
                        inputs = fixtures()
                        inputs[source][collection] = [value]
                        with self.assertRaises(ValueError):
                            bridge.project(*inputs)

    def test_record_collections_must_be_lists(self):
        for source in range(3):
            for collection in ("nodes", "edges"):
                for value in (None, 1, "records", {}):
                    with self.subTest(source=source, collection=collection, value=value):
                        inputs = fixtures()
                        inputs[source][collection] = value
                        with self.assertRaises(ValueError):
                            bridge.project(*inputs)

    def test_optional_edge_and_node_types_must_be_strings(self):
        cases = ((0, "nodes", "type"), (0, "edges", "relation"),
                 (0, "edges", "evidence_state"), (1, "edges", "kind"),
                 (2, "edges", "edge_type"))
        for source, collection, field in cases:
            for value in (None, 1, [], {}):
                with self.subTest(source=source, field=field, value=value):
                    inputs = fixtures()
                    inputs[0]["edges"] = [{"from": "artifact:REGISTERED.md", "to": "artifact:REGISTERED.md"}]
                    inputs[2]["edges"] = [{"source": "REG", "target": "REG"}]
                    inputs[source][collection][0][field] = value
                    with self.assertRaises(ValueError):
                        bridge.project(*inputs)

    def test_provenance_and_path_collections_must_be_lists(self):
        for source, collection, field in ((0, "nodes", "provenance"),
                                           (1, "edges", "evidence"), (2, "nodes", "files")):
            for value in (None, 1, "path", {}):
                with self.subTest(source=source, field=field, value=value):
                    inputs = fixtures()
                    inputs[source][collection][0][field] = value
                    with self.assertRaises(ValueError):
                        bridge.project(*inputs)

    def test_evidence_paths_must_be_strings(self):
        for witness in (None, [], {}, {"source": None}, {"source": 1}, {"source": []}):
            with self.subTest(witness=witness):
                inputs = fixtures()
                inputs[1]["edges"][0]["evidence"] = [witness]
                with self.assertRaises(ValueError):
                    bridge.project(*inputs)
        for path in (None, 1, [], {}):
            with self.subTest(path=path):
                inputs = fixtures()
                inputs[2]["nodes"][0]["files"] = [path]
                with self.assertRaises(ValueError):
                    bridge.project(*inputs)

    def test_provenance_is_limited_to_three_records(self):
        inputs = fixtures()
        records = [{"path": f"source-{i}.py"} for i in range(4)]
        inputs[0]["nodes"][0]["provenance"] = records
        result = bridge.project(*inputs)
        rkg_node = next(node for node in result["nodes"] if node["id"].startswith("rkg:"))
        self.assertEqual(rkg_node["provenance"]["records"], records[:3])
        self.assertEqual(inputs[0]["nodes"][0]["provenance"], records)


if __name__ == "__main__":
    unittest.main()
