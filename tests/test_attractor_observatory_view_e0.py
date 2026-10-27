"""No-script E0 dashboard rendering and output safety."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("attractor", ROOT / "tools/attractor_observatory_e0.py")
attractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(attractor)
spec = importlib.util.spec_from_file_location("view", ROOT / "tools/attractor_observatory_view_e0.py")
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)

GRAPH = {"nodes": {"A":{"id":"A"}, "B":{"id":"B"}}, "edges":[{"source":"A","target":"B"}]}


class ViewTests(unittest.TestCase):
    def test_html_is_self_contained_and_reports_missing_evidence(self):
        report = attractor.build(GRAPH)
        html = view.render(report)
        self.assertIn("NOT_MEASURED", html)
        self.assertIn("READ ONLY", html)
        self.assertIn("<table>", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)

    def test_escaped_untrusted_node_id(self):
        report = attractor.build(GRAPH)
        poisoned = copy.deepcopy(report)
        poisoned["internal"]["strongly_connected_components"][0]["node_ids"] = ['<img src=x onerror="alert(1)">']
        html = view.render(poisoned)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;img", html)

    def test_non_authorizing_only(self):
        report = attractor.build(GRAPH)
        report["execution"] = "ENABLED"
        with self.assertRaisesRegex(ValueError, "authority"):
            view.render(report)


if __name__ == "__main__":
    unittest.main()
