"""Standalone stdlib falsifiers for read-only graph cost observation."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "graph_resource_observer.py"
spec = importlib.util.spec_from_file_location("observer", SOURCE)
obs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(obs)


class ResourceObservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "existing.json"
        self.path.write_text(json.dumps({
            "nodes": {"A": {"id": "A"}, "B": {"id": "B"}},
            "edges": [{"source": "A", "target": "B"},
                      {"source": "B", "target": "B"}],
        }), encoding="utf-8")

    def test_cost_receipt_and_nonmutation(self):
        before = self.path.read_bytes()
        result = obs.observe(self.root, "existing.json", "system_graph", trials=3,
                             node_id="B", context_id="mac-test")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertEqual(result["source"]["revision"], "sha256:" + obs.hashlib.sha256(before).hexdigest())
        row = result["observation"]
        self.assertEqual((row["nodes_count"], row["edges_count"], row["incident_edges_count"]), (2, 2, 2))
        self.assertEqual(len(row["trials"]), 3)
        self.assertTrue(all(set(r) == {"wall_ns", "cpu_ns", "peak_python_alloc_bytes"}
                            and all(v >= 0 for v in r.values()) for r in row["trials"]))
        self.assertIsInstance(row["median_wall_ns"], (int, float))

    def test_list_nodes_and_from_to_edges(self):
        self.path.write_text(json.dumps({"nodes": [{"id": "q"}],
                                         "edges": [{"from": "q", "to": "z"}]}))
        row = obs.observe(self.root, "existing.json", "evidence_graph",
                          trials=1, node_id="q")["observation"]
        self.assertEqual(row["incident_edges_count"], 1)

    def test_missing_node_refused_not_zero(self):
        with self.assertRaisesRegex(obs.ObservationRefused, "not present"):
            obs.observe(self.root, "existing.json", "system_graph", node_id="missing")

    def test_malformed_edge_refused_for_scan(self):
        self.path.write_text(json.dumps({"nodes": [{"id": "A"}], "edges": [{"id": "x"}]}))
        with self.assertRaisesRegex(obs.ObservationRefused, "from/to or source/target"):
            obs.observe(self.root, "existing.json", "system_graph", node_id="A")

    def test_disallow_path_escape_and_symlinks(self):
        for path in ("../private.json", "/etc/passwd", "./existing.json", "private.txt"):
            with self.subTest(path=path), self.assertRaises(obs.ObservationRefused):
                obs.observe(self.root, path, "system_graph")
        (self.root / "link.json").symlink_to(self.path)
        with self.assertRaisesRegex(obs.ObservationRefused, "symlink"):
            obs.observe(self.root, "link.json", "system_graph")

    def test_bounded_bytes_and_invalid_shapes(self):
        with mock.patch.object(obs, "MAX_BYTES", 8):
            with self.assertRaisesRegex(obs.ObservationRefused, "16 MiB"):
                obs.observe(self.root, "existing.json", "system_graph")
        self.path.write_text('{"nodes":{},"edges":{}}')
        with self.assertRaisesRegex(obs.ObservationRefused, "edges list"):
            obs.observe(self.root, "existing.json", "system_graph")

    def test_no_result_if_revision_changes(self):
        real = obs.measure_once
        calls = 0
        def tamper(path, node_id):
            nonlocal calls
            calls += 1
            if calls == 2:
                self.path.write_text(json.dumps({"nodes": {}, "edges": []}))
            return real(path, node_id)
        with mock.patch.object(obs, "measure_once", side_effect=tamper):
            with self.assertRaisesRegex(obs.ObservationRefused, "changed"):
                obs.observe(self.root, "existing.json", "system_graph", trials=2)

    def test_invalid_trials_and_context_refused(self):
        for n in (0, 16, True):
            with self.assertRaises(obs.ObservationRefused):
                obs.observe(self.root, "existing.json", "system_graph", trials=n)
        with self.assertRaises(obs.ObservationRefused):
            obs.observe(self.root, "existing.json", "system_graph", context_id="private local user")

    def test_failure_does_not_emit_successful_json(self):
        self.assertEqual(obs.main(["--repo", str(self.root), "--graph", "missing.json",
                                   "--system", "system_graph"]), 2)


if __name__ == "__main__":
    unittest.main()
