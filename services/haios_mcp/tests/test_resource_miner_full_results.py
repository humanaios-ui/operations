"""Full-public-result compatibility tests for the Witness 10-item display boundary."""
from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from haios_mcp.core import HumanAIOSBridge

class FullSnapshotResultsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        for name in ("CURRENT.md", "REGISTERED.md", "GOVERNANCE.md"):
            (root / name).write_text("read-only public context")
        self.bridge = HumanAIOSBridge(root)

    def test_upstream_twenty_six_show_only_ten_but_retain_count(self):
        rows = [dict(resource_id=f"RES-{n}", title=f"Compute credits {n}",
                     description="synthetic fixture", source_name="HumanAIOS Funding Pipeline",
                     source_url=f"https://example.org/opportunity/{n}", route="WATCH",
                     eligibility_assessed=False) for n in range(26)]
        result = self._invoke(rows)
        self.assertEqual(result["matched_count"], 26)
        self.assertEqual(result["upstream_shown_count"], 26)
        self.assertEqual(result["shown_count"], 10)
        self.assertEqual(result["unshown_match_count"], 16)
        self.assertTrue(result["more_available"])
        self.assertEqual(len(result["candidates"]), 10)
        self.assertEqual(result["authority"], "NONE")
        self.assertEqual(result["eligibility"], "NOT_ASSESSED")
        self.assertEqual(result["execution"], "DISABLED")

    def test_private_source_at_hidden_index_rejected(self):
        rows = [dict(resource_id=f"RES-{n}", title=f"Compute credits {n}",
                     source_name="HumanAIOS Funding Pipeline",
                     source_url=f"https://example.org/{n}", route="WATCH",
                     eligibility_assessed=False) for n in range(26)]
        rows[20]["source_name"] = "HackerOne private program"
        with self.assertRaisesRegex(RuntimeError, "non-public candidate"):
            self._invoke(rows)

    def _invoke(self, rows):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                posted = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if posted != {"objective": "compute credits", "source_mode": "snapshot"}:
                    raise AssertionError(posted)
                body = json.dumps({
                    "status": "CANDIDATES_FOR_HUMAN_REVIEW", "source_mode": "snapshot",
                    "source_status": "CURATED_SNAPSHOT_NOT_LIVE",
                    "source_warning": "Dates, eligibility and availability unverified.",
                    "matched_count": len(rows), "shown_count": len(rows),
                    "unexamined_count": 0,
                    "eligibility": "NOT_ASSESSED", "execution": "DISABLED",
                    "authority": "NONE", "receipt_sha256": "a" * 64,
                    "candidates": rows
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *_): pass
        service = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=service.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ, {"HAIOS_RESOURCE_MINER_ORIGIN":
                                       f"http://127.0.0.1:{service.server_port}"}):
                return self.bridge.find_resources("compute credits")
        finally:
            service.shutdown()
            service.server_close()
            thread.join(timeout=3)

if __name__ == "__main__":
    unittest.main()
