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
        result = bridge.project(*fixtures())
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertFalse(result["can_authorize"])
        self.assertFalse(result["merge_authority"])
        self.assertIn("EXACT_PATH_WITNESS", [e["relation"] for e in result["edges"]])
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


if __name__ == "__main__":
    unittest.main()
