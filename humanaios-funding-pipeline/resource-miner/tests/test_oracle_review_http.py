"""Local-only HTTP contract for live Oracle read-only shadow surface."""
import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import app
from resource_miner.oracle_review_telemetry import OracleReadbackError


class OracleRouteTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = "http://127.0.0.1:" + str(self.server.server_address[1])

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(self, path, host=None):
        headers = {"Host": host} if host else {}
        req = Request(self.origin + path, headers=headers)
        try:
            with urlopen(req, timeout=4) as response:
                return response.status, response.read(), dict(response.headers)
        except HTTPError as exc:
            return exc.code, exc.read(), dict(exc.headers)

    def test_default_disabled_fail_closed(self):
        with patch.dict(os.environ, {"HUMANAIOS_ORACLE_GITHUB_READONLY": ""}):
            status, _, _ = self.request("/api/oracle/review-telemetry")
            self.assertEqual(status, 503)
            status, _, _ = self.request("/oracle-review")
            self.assertEqual(status, 503)

    def test_local_opt_in_calls_readback_and_shows_view(self):
        model = {"schema": "humanaios.oracle_review_telemetry.v0.1",
                 "authority_effect": "NONE", "execution": "DISABLED"}
        with patch.dict(os.environ, {"HUMANAIOS_ORACLE_GITHUB_READONLY": "1"}):
            with patch.object(app, "oracle_read_cycle", return_value=model) as probe:
                status, data, _ = self.request("/api/oracle/review-telemetry")
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(data), model)
                probe.assert_called_once_with()
            status, html, _ = self.request("/oracle-review")
            self.assertEqual(status, 200)
            self.assertIn(b"Oracle graph telemetry", html)
            status, html, _ = self.request("/intent-os")
            self.assertEqual(status, 200)
            self.assertIn(b"/oracle-review", html)

    def test_missing_evidence_returns_sanitized_error(self):
        with patch.dict(os.environ, {"HUMANAIOS_ORACLE_GITHUB_READONLY": "1"}):
            with patch.object(app, "oracle_read_cycle", side_effect=OracleReadbackError("secret material")):
                code, body, _ = self.request("/api/oracle/review-telemetry")
                self.assertEqual(code, 503)
                self.assertNotIn(b"secret", body)
                self.assertEqual(json.loads(body)["state"], "UNVERIFIED")

    def test_reject_cross_origin_and_dns_rebinding(self):
        with patch.dict(os.environ, {"HUMANAIOS_ORACLE_GITHUB_READONLY": "1"}):
            status, _, _ = self.request("/api/oracle/review-telemetry", "evil.example")
            self.assertEqual(status, 404)
        req = Request(self.origin + "/api/oracle/review-telemetry", headers={
            "Origin": "https://evil.example"})
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req, timeout=4)
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
