"""Negative transport tests for optional read-only Resource Miner MCP adapter."""
from __future__ import annotations
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from haios_mcp.core import HumanAIOSBridge, MAX_MINER_RESPONSE_BYTES


def good_payload():
    return {
        "status": "CANDIDATES_FOR_HUMAN_REVIEW",
        "source_mode": "snapshot",
        "source_status": "CURATED_SNAPSHOT_NOT_LIVE",
        "source_warning": "Availability not independently verified",
        "matched_count": 1, "shown_count": 1, "unexamined_count": 0,
        "receipt_sha256": "c" * 64,
        "authority": "NONE", "execution": "DISABLED",
        "eligibility": "NOT_ASSESSED",
        "candidates": [{
            "resource_id": "RES-PUBLIC", "title": "Compute credits",
            "source_name": "HumanAIOS Funding Pipeline",
            "source_url": "https://example.org/compute",
            "route": "WATCH", "eligibility_assessed": False,
        }],
    }


class NegativeResourceTransportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        for name in ("CURRENT.md", "REGISTERED.md", "GOVERNANCE.md"):
            (root / name).write_text("public context")
        self.bridge = HumanAIOSBridge(root)

    def invoke(self, *, payload=None, status=200, mime="application/json", location=None, raw=None):
        body = raw if raw is not None else json.dumps(payload if payload is not None else good_payload()).encode()
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(status)
                self.send_header("Content-Type", mime)
                if location:
                    self.send_header("Location", location)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *_):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        runner = threading.Thread(target=server.serve_forever, daemon=True)
        runner.start()
        try:
            with patch.dict(os.environ, {"HAIOS_RESOURCE_MINER_ORIGIN": f"http://127.0.0.1:{server.server_port}"}):
                return self.bridge.find_resources("compute credits")
        finally:
            server.shutdown()
            server.server_close()
            runner.join(timeout=3)

    def test_refuses_unexpected_content_type(self):
        with self.assertRaisesRegex(RuntimeError, "JSON"):
            self.invoke(mime="text/html")

    def test_refuses_oversize_body(self):
        with self.assertRaisesRegex(RuntimeError, "size limit"):
            self.invoke(raw=b"X" * (MAX_MINER_RESPONSE_BYTES + 1))

    def test_refuses_upstream_authority_claim(self):
        payload = good_payload()
        payload["authority"] = "AUTO_APPROVE"
        with self.assertRaisesRegex(RuntimeError, "unexpected public snapshot schema"):
            self.invoke(payload=payload)

    def test_refuses_remote_source_class(self):
        payload = good_payload()
        payload["candidates"][0]["source_name"] = "Private Gmail"
        with self.assertRaisesRegex(RuntimeError, "non-public candidate"):
            self.invoke(payload=payload)

    def test_does_not_follow_http_redirect(self):
        reached = []
        class Target(BaseHTTPRequestHandler):
            def do_GET(self):
                reached.append(self.path)
                self.send_response(200)
                self.end_headers()
            def do_POST(self):
                reached.append(self.path)
                self.send_response(200)
                self.end_headers()
            def log_message(self, *_): pass
        target = ThreadingHTTPServer(("127.0.0.1", 0), Target)
        thread = threading.Thread(target=target.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(RuntimeError):
                self.invoke(
                    status=302, location=f"http://127.0.0.1:{target.server_port}/not-allowed"
                )
            self.assertEqual(reached, [])
        finally:
            target.shutdown()
            target.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
