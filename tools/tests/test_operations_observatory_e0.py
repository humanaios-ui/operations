"""E0 three-repository observatory: offline static and projection contract tests.

Read-only. No GitHub access, secrets, network reads or production writes.
"""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIEW = ROOT / "ui" / "operations-observatory-e0.html"
SCRIPT = ROOT / "ui" / "operations-observatory-e0.js"
CANVAS = ROOT / "ui" / "living-operations-canvas.html"
NODE_TEST = ROOT / "tools" / "tests" / "operations_observatory_e0.test.cjs"


class ObservatoryE0Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = VIEW.read_text(encoding="utf-8")
        cls.js = SCRIPT.read_text(encoding="utf-8")
        cls.canvas = CANVAS.read_text(encoding="utf-8")

    def test_companion_link_and_existing_graph_retained(self):
        self.assertIn('href="operations-observatory-e0.html"', self.canvas)
        self.assertIn("system_graph.json", self.canvas)
        self.assertIn("Graph validation:", self.canvas)
        self.assertIn("graph_timeline/system_graph_timeline.html", self.canvas)
        self.assertIn('src="operations-observatory-e0.js"', self.html)

    def test_three_repositories_and_rolling_window(self):
        for repo in ("humanaios-ui/humanaios",
                     "humanaios-ui/operations",
                     "humanaios-ui/lasting-light-ai"):
            with self.subTest(repo=repo):
                self.assertIn('"' + repo + '"', self.js)
        self.assertIn("const DAYS = 28;", self.js)
        self.assertIn("const MAX_PAGES = 4;", self.js)
        self.assertIn("COMPLETE_WINDOW", self.js)
        self.assertIn("PARTIAL_PAGE_LIMIT", self.js)
        self.assertIn("STALE_LAST_SUCCESS", self.js)
        self.assertIn("UNAVAILABLE", self.js)

    def test_no_write_no_authority_no_client_storage(self):
        self.assertIn('method: "GET"', self.js)
        self.assertIn("api.github.com/repos/", self.js)
        self.assertNotRegex(
            self.js, r'(?i)\bmethod\s*:\s*["\x27](post|put|patch|delete)["\x27]'
        )
        for forbidden in ("localStorage", "sessionStorage", "indexedDB",
                          ".innerHTML", "document.cookie", "eval(", "sendBeacon("):
            self.assertNotIn(forbidden, self.js)
        self.assertIn("textContent", self.js)
        self.assertIn("noopener noreferrer", self.js)
        self.assertIn("Authority effect: none", self.html)
        self.assertIn("not connected", self.html)

    def test_clearly_bounded_kinetics_and_attention(self):
        for token in ("last_touch_buckets", "last_touch_last_7d",
                      "last_touch_prior_7d", "SOURCE_LABEL_MATCH",
                      "OPEN_ITEM_CANDIDATE", "rejected"):
            self.assertIn(token, self.js)
        self.assertIn("not event volume", self.js)
        self.assertIn("Human Attention Queue", self.html)
        self.assertIn("not an approval queue", self.html)
        self.assertIn("not necessarily merged", self.html)

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable: run JS falsifiers when installed")
    def test_node_behavioral_falsifiers(self):
        outcome = subprocess.run(
            ["node", "--test", str(NODE_TEST)], cwd=ROOT,
            capture_output=True, text=True, timeout=45, check=False
        )
        self.assertEqual(outcome.returncode, 0, outcome.stdout + "\n" + outcome.stderr)


if __name__ == "__main__":
    unittest.main()
