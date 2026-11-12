"""Permanent offline E0.3 ↔ Unit Zero v0.2 boundary tests.

No provider calls, credential reads, file writes, or real MCP conversation.
Compatible with the reconciled E0.3 build and the main-branch public bridge.
"""
from __future__ import annotations

import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, ProxyHandler, build_opener
from unittest.mock import patch

import app
from resource_miner import witness_bridge as bridge


def candidate():
    return {
        "resource_id": "RES-SYNTH-OFFLINE",
        "title": "Synthetic public resource",
        "source_name": "HumanAIOS Funding Pipeline",
        "source_url": "https://example.org/resource?session=NEVER_FORWARD#private",
        "route": "WATCH",
        "observed_at": "2026-11-11",
    }


def request_body(consent=True):
    return {
        "resource": candidate(),
        "question": "What would an independent reviewer check?",
        "consent": consent,
    }


class PublicPayloadBoundary(unittest.TestCase):
    def test_allowlist_and_url_sanitizing(self):
        envelope, question = bridge.public_envelope(request_body())
        self.assertEqual(envelope["source_url"], "https://example.org/resource")
        self.assertEqual(question, request_body()["question"])
        self.assertEqual(set(envelope) - bridge.ALLOWED_KEYS, set())
        self.assertNotIn("NEVER_FORWARD", json.dumps(envelope))
        self.assertNotIn("private", json.dumps(envelope))

    def test_consent_is_literal_true(self):
        for consent in (None, False, "true", 1, 0):
            with self.subTest(consent=consent):
                with self.assertRaises(ValueError):
                    bridge.public_envelope(request_body(consent))

    def test_reject_private_or_excess_fields(self):
        for field in ("private_notes", "application_body", "api_key",
                      "raw_email", "attachments", "user_identity"):
            with self.subTest(field=field):
                body = request_body()
                body["resource"][field] = "SYNTHETIC_PRIVATE_MARKER"
                with self.assertRaises(ValueError):
                    bridge.public_envelope(body)

    def test_reject_private_source_and_action_route(self):
        for key, value in (("source_name", "Private Gmail"),
                           ("route", "EXECUTE"), ("route", "APPLY")):
            with self.subTest(key=key, value=value):
                body = request_body()
                body["resource"][key] = value
                with self.assertRaises(ValueError):
                    bridge.public_envelope(body)

    def test_reject_private_url_forms(self):
        for url in ("http://127.0.0.1:8768/mcp", "file:///etc/passwd",
                    "https://localhost/private", "https://x.invalid/a",
                    "https://user:password@example.org/source"):
            with self.subTest(url=url):
                body = request_body()
                body["resource"]["source_url"] = url
                with self.assertRaises(ValueError):
                    bridge.public_envelope(body)

    def test_question_length_and_control_characters(self):
        for question in ("", "a", "x" * 351, "line1\nline2"):
            with self.subTest(size=len(question)):
                body = request_body()
                body["question"] = question
                with self.assertRaises(ValueError):
                    bridge.public_envelope(body)

    def test_disabled_bridge_does_not_touch_keychain_or_model(self):
        with patch.object(bridge, "enabled", return_value=False), \
             patch.object(bridge, "_keychain_token") as token, \
             patch.object(bridge, "_ask_mcp") as call:
            with self.assertRaises(bridge.WitnessBridgeUnavailable):
                bridge.ask_resource(request_body())
            token.assert_not_called()
            call.assert_not_called()

    def test_mocked_handoff_is_only_public_data(self):
        async def fake_mcp(envelope, question, bearer):
            self.assertEqual(bearer, "SYNTHETIC-NOT-A-SECRET")
            self.assertEqual(envelope["source_url"], "https://example.org/resource")
            self.assertNotIn("NEVER_FORWARD", json.dumps(envelope))
            self.assertEqual(question, request_body()["question"])
            return {"answer": "Synthetic local reply", "source_manifest": [],
                    "authority": "NONE", "execution": "DISABLED"}
        with patch.object(bridge, "enabled", return_value=True), \
             patch.object(bridge, "_keychain_token",
                          return_value="SYNTHETIC-NOT-A-SECRET"), \
             patch.object(bridge, "_ask_mcp", side_effect=fake_mcp) as call:
            got = bridge.ask_resource(request_body())
            self.assertEqual(got["authority"], "NONE")
            self.assertEqual(call.call_count, 1)


class LocalHttpFailClosed(unittest.TestCase):
    """Real loopback HTTP route: bridge disabled; no provider or Keychain use."""

    @classmethod
    def setUpClass(cls):
        cls.requests_observed = 0
        cls.requests_lock = threading.Lock()

        class CountingHandler(app.Handler):
            def do_POST(self):
                with cls.requests_lock:
                    cls.requests_observed += 1
                return super().do_POST()

        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), CountingHandler)
        cls.port = cls.httpd.server_address[1]
        cls.opener = build_opener(ProxyHandler({}))
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)

    def send(self, headers=None, body=None):
        if body is None:
            body = request_body()
        address = "http://127.0.0.1:%s" % self.port
        hdr = {"Content-Type": "application/json"}
        if headers:
            hdr.update(headers)
        data = json.dumps(body).encode("utf-8")
        req = Request(address + "/api/witness/ask-resource", data=data,
                      headers=hdr, method="POST")
        with self.requests_lock:
            before = self.requests_observed
        try:
            with self.opener.open(req, timeout=4) as response:
                result = response.status, response.read()
        except HTTPError as error:
            result = error.code, error.read()
        with self.requests_lock:
            after = self.requests_observed
        self.assertEqual(after, before + 1, "Request must reach the local app.Handler")
        return result

    def test_same_origin_disabled_503_without_provider(self):
        with patch.object(app, "witness_enabled", return_value=False), \
             patch.object(app, "ask_resource") as talk, \
             patch.object(bridge, "_keychain_token") as token:
            status, payload = self.send({"Origin": "http://127.0.0.1:%s" % self.port})
        self.assertEqual(status, 503)
        self.assertNotIn(b"NEVER_FORWARD", payload)
        talk.assert_not_called()
        token.assert_not_called()

    def test_missing_origin_denied(self):
        with patch.object(app, "ask_resource") as talk:
            status, _ = self.send()
        self.assertEqual(status, 403)
        talk.assert_not_called()

    def test_foreign_origin_denied(self):
        with patch.object(app, "ask_resource") as talk:
            status, _ = self.send({"Origin": "https://attacker.invalid"})
        self.assertIn(status, (403, 404))
        talk.assert_not_called()

    def test_cross_site_denied(self):
        with patch.object(app, "ask_resource") as talk:
            status, _ = self.send({
                "Origin": "http://127.0.0.1:%s" % self.port,
                "Sec-Fetch-Site": "cross-site"})
        self.assertIn(status, (403, 404))
        talk.assert_not_called()

    def test_hostile_proxy_environment_still_reaches_handler(self):
        hostile = {
            "HTTP_PROXY": "http://127.0.0.1:1",
            "HTTPS_PROXY": "http://127.0.0.1:1",
            "ALL_PROXY": "http://127.0.0.1:1",
            "NO_PROXY": "example.invalid",
            "http_proxy": "http://127.0.0.1:1",
            "https_proxy": "http://127.0.0.1:1",
            "all_proxy": "http://127.0.0.1:1",
            "no_proxy": "example.invalid",
        }
        with patch.dict(os.environ, hostile), patch.object(app, "ask_resource") as talk:
            status, _ = self.send({
                "Origin": "http://127.0.0.1:%s" % self.port,
                "Sec-Fetch-Site": "cross-site",
            })
        self.assertIn(status, (403, 404))
        talk.assert_not_called()

    def test_forged_host_denied(self):
        with patch.object(app, "ask_resource") as talk:
            status, _ = self.send({
                "Origin": "http://127.0.0.1:%s" % self.port,
                "Host": "attacker.invalid"})
        self.assertIn(status, (403, 404))
        talk.assert_not_called()


if __name__ == "__main__":
    unittest.main()