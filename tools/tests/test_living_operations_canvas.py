"""Read-only contract checks for the living system graph canvas.

No network, credentials, changes to the graph, or browser tooling required.
These checks protect the advisory UI contract, not runtime health.
"""
import base64
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANVAS = ROOT / "ui" / "living-operations-canvas.html"
TIMELINE = ROOT / "graph_timeline" / "system_graph_timeline.html"
GRAPH = ROOT / "system_graph.json"


class LivingOperationsCanvasContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = CANVAS.read_text(encoding="utf-8")
        match = re.search(
            r'<script type="application/json" id="offline">(.*?)</script>',
            cls.html,
            re.DOTALL,
        )
        if match is None:
            raise AssertionError("Offline snapshot script not found")
        cls.snapshot = json.loads(match.group(1))

    def test_embedded_artwork_is_actual_image(self):
        match = re.search(
            r'src="data:image/webp;base64,([A-Za-z0-9+/=]+)"', self.html
        )
        self.assertIsNotNone(match, "Illustrative artwork must remain embedded")
        blob = base64.b64decode(match.group(1), validate=True)
        self.assertTrue(blob.startswith(b"RIFF"))
        self.assertEqual(blob[8:12], b"WEBP")

    def test_snapshot_has_declared_topology(self):
        nodes = self.snapshot["nodes"]
        edges = self.snapshot["edges"]
        self.assertEqual(len(nodes), 22)
        self.assertEqual(len(edges), 53)
        self.assertEqual(
            sum(n["status"] == "OPERATED" for n in nodes.values()), 11
        )
        self.assertEqual(sum(n["status"] == "LAID" for n in nodes.values()), 11)
        self.assertTrue(all(e["source"] in nodes and e["target"] in nodes for e in edges))

    def test_current_graph_is_not_edited_by_view(self):
        graph = json.loads(GRAPH.read_text(encoding="utf-8"))
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        self.assertIn("validation_status", graph)
        self.assertIn("Graph validation:", self.html)
        self.assertIn("not proof that a runtime is healthy", self.html)

    def test_timeline_is_retained_and_linked(self):
        self.assertTrue(TIMELINE.is_file(), "Do not remove existing timeline")
        self.assertIn('../graph_timeline/system_graph_timeline.html', self.html)
        self.assertIn("graph_timeline/system_graph_timeline.html", self.html)

    def test_source_reads_public_canonical_file(self):
        self.assertIn("raw.githubusercontent.com", self.html)
        self.assertIn("/main/system_graph.json", self.html)
        self.assertIn("cache:'no-store'", self.html)
        self.assertIn("LAST SUCCESSFUL FETCH (STALE)", self.html)
        self.assertIn("OFFLINE SNAPSHOT", self.html)

    def test_no_browser_write_path(self):
        scripts = re.findall(r"<script(?:[^>]*)>(.*?)</script>", self.html, re.DOTALL)
        executable = "\n".join(s for s in scripts if "const REPO=" in s)
        self.assertTrue(executable)
        self.assertEqual(executable.count("fetch("), 1)
        self.assertNotRegex(
            executable, r"\b(?:POST|PATCH|DELETE|PUT)\b|localStorage|sessionStorage"
        )
        self.assertNotIn("eval(", executable)

    def test_accessibility_controls(self):
        for token in (
            'type="button" id="refresh"',
            'type="button" id="reset"',
            'type="search"',
            'aria-live="polite"',
            "role:'button'",
            "ev.key==='Enter'",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.html)


if __name__ == "__main__":
    unittest.main()
