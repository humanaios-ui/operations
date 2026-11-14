"""Project Observatory INTENT-OS bridge: localhost-only HTTP contract tests.

Tests actual existing Observatory files with a live loopback HTTP server.
No external network requests, GitHub writes or user-owned data.
"""
from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


class ProjectObservatoryBridgeHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.base = "http://127.0.0.1:" + str(cls.server.server_address[1])
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()

    def read(self, path, headers=None):
        req = Request(self.base + path, headers=headers or {})
        with urlopen(req, timeout=5) as response:
            return response.status, response.headers, response.read()

    def error(self, path, headers=None):
        with self.assertRaises(HTTPError) as caught:
            self.read(path, headers=headers)
        return caught.exception

    def test_link_from_existing_intent_os_and_on_track(self):
        for route in ("/intent-os", "/on-track"):
            with self.subTest(route=route):
                status, _, body = self.read(route)
                self.assertEqual(status, 200)
                self.assertIn(b'href="/project-observatory"', body)
                self.assertIn(b"local read-only preview", body)

    def test_reuses_existing_html_and_script_without_state_writes(self):
        status, headers, body = self.read("/project-observatory")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        html = body.decode("utf-8")
        self.assertIn("Operations Observatory", html)
        self.assertIn('src="/project-observatory.js"', html)
        self.assertIn('href="/intent-os"', html)
        self.assertIn('href="/on-track"', html)
        self.assertIn("Human Attention Queue", html)
        self.assertIn("not an approval queue", html)
        self.assertNotIn("project-observatory", app.OBSERVATORY_UI.joinpath("operations-observatory-e0.html").read_text())
        status, js_headers, script = self.read("/project-observatory.js")
        self.assertEqual(status, 200)
        self.assertIn("application/javascript", js_headers["Content-Type"])
        self.assertEqual(
            script, (app.OBSERVATORY_UI / "operations-observatory-e0.js").read_bytes()
        )
        for forbidden in (b"localStorage", b"sessionStorage", b"document.cookie",
                          b"sendBeacon(", b"method: \"POST\""):
            self.assertNotIn(forbidden, script)

    def test_only_observatory_gets_public_github_connect_csp(self):
        _, headers, _ = self.read("/project-observatory")
        csp = headers["Content-Security-Policy"]
        self.assertIn("connect-src https://api.github.com", csp)
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("script-src 'unsafe-inline'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertEqual(headers.get("Referrer-Policy"), "no-referrer")
        _, core_headers, _ = self.read("/intent-os")
        self.assertIn("connect-src 'self'", core_headers["Content-Security-Policy"])
        self.assertNotIn("https://api.github.com", core_headers["Content-Security-Policy"])

    def test_host_and_origin_must_be_local(self):
        for path in ("/project-observatory", "/project-observatory.js"):
            with self.subTest(path=path):
                err = self.error(path, {"Host": "not-local.example"})
                self.assertEqual(err.code, 404)
                err = self.error(path, {"Origin": "https://not-local.example"})
                self.assertEqual(err.code, 404)

    def test_missing_or_drifted_assets_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            with patch.object(app, "OBSERVATORY_UI", path):
                err = self.error("/project-observatory")
                self.assertEqual(err.code, 503)
                self.assertEqual(json.load(err)["status"], "NOT_CONNECTED")
                err = self.error("/project-observatory.js")
                self.assertEqual(err.code, 503)
            original = (app.OBSERVATORY_UI / "operations-observatory-e0.html").read_text()
            (path / "operations-observatory-e0.html").write_text(
                original.replace('src="operations-observatory-e0.js"',
                                 'src="changed-not-reviewed.js"'),
                encoding="utf-8",
            )
            with patch.object(app, "OBSERVATORY_UI", path):
                err = self.error("/project-observatory")
                self.assertEqual(err.code, 503)
                self.assertEqual(json.load(err)["status"], "TEMPLATE_DRIFT")

    def test_no_private_profile_or_decision_authority(self):
        status, _, body = self.read("/project-observatory")
        self.assertEqual(status, 200)
        text = body.decode("utf-8")
        self.assertIn("Authority effect: none", text)
        self.assertIn("not connected", text)
        self.assertNotIn("/api/my-opportunities/project", text)
        self.assertNotIn("private_profile", text)


if __name__ == "__main__":
    unittest.main()
