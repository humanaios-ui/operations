"""Opt-in local Witness handoff: no implicit private-data export or authority."""
from __future__ import annotations
import io
import json
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

import app
from resource_miner import witness_bridge as bridge


def resource():
    return {
        "resource_id": "RES-TEST-PUBLIC",
        "title": "Public compute research credits",
        "source_name": "HumanAIOS Funding Pipeline",
        "source_url": "https://example.org/compute?session=SECRET-TRACKING",
        "route": "WATCH",
        "observed_at": "2026-10-25",
    }


def payload():
    return {
        "resource": resource(), "consent": True,
        "question": "Could this advance HumanAIOS responsibly?",
    }


class PublicHandoffTests(unittest.TestCase):
    def test_metadata_allowlist_and_query_removal(self):
        record, question = bridge.public_envelope(payload())
        self.assertEqual(record["source_url"], "https://example.org/compute")
        self.assertNotIn("SECRET-TRACKING", str(record))
        self.assertEqual(question, payload()["question"])

    def test_cannot_send_raw_notes_attachment_credentials_or_private_source(self):
        for extra in ("raw", "api_key", "private_notes", "evidence", "user_identity"):
            bad = payload()
            bad["resource"][extra] = "DO_NOT_SEND"
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                bridge.public_envelope(bad)
        bad = payload()
        bad["resource"]["source_name"] = "Private Gmail"
        with self.assertRaises(ValueError):
            bridge.public_envelope(bad)
        bad = payload()
        bad["resource"]["source_url"] = "http://127.0.0.1:8768/mcp"
        with self.assertRaises(ValueError):
            bridge.public_envelope(bad)

    def test_consent_and_boundaries_required(self):
        for consent in (False, "true", None):
            with self.subTest(consent=consent):
                bad = payload()
                bad["consent"] = consent
                with self.assertRaises(ValueError):
                    bridge.public_envelope(bad)
        bad = payload()
        bad["question"] = "Q" * 351
        with self.assertRaises(ValueError):
            bridge.public_envelope(bad)

    def test_disabled_bridge_never_opens_keychain_or_provider(self):
        with patch.object(bridge, "enabled", return_value=False), \
             patch.object(bridge, "_keychain_token") as keychain, \
             patch.object(bridge, "_ask_mcp") as talk:
            with self.assertRaises(bridge.WitnessBridgeUnavailable):
                bridge.ask_resource(payload())
        keychain.assert_not_called()
        talk.assert_not_called()

    def test_service_requires_loopback_host_peer_and_origin(self):
        raw = json.dumps(payload()).encode("utf-8")
        handler = object.__new__(app.Handler)
        handler.path = "/api/witness/ask-resource"
        handler.server = Mock(server_address=("127.0.0.1", 8769))
        handler.client_address = ("127.0.0.1", 55555)
        handler.connection = Mock()
        handler.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(raw)),
            "Host": "127.0.0.1:8769",
            "Origin": "http://127.0.0.1:8769",
        }
        handler._read_intent_body = lambda length: raw
        sent = []
        handler._send_json = lambda obj, status=200: sent.append((int(status), obj))
        expected = {
            "answer": "Unverified, check source", "source_manifest": [],
            "resource_id": resource()["resource_id"],
            "authority": "NONE", "execution": "DISABLED",
        }
        with patch.object(app, "witness_enabled", return_value=True), \
             patch.object(app, "ask_resource", return_value=expected) as asked:
            handler.do_POST()
        self.assertEqual(sent[0][0], 200)
        asked.assert_called_once_with(payload())
        self.assertEqual(sent[0][1]["authority"], "NONE")

        for host, origin, bound in [
            ("evil.example", "http://127.0.0.1:8769", "127.0.0.1"),
            ("127.0.0.1:8769", "https://evil.example", "127.0.0.1"),
            ("127.0.0.1:8769", None, "127.0.0.1"),
            ("127.0.0.1:8769", "http://127.0.0.1:8769", "0.0.0.0"),
        ]:
            with self.subTest(host=host, origin=origin, bound=bound):
                handler.headers = dict(handler.headers, Host=host)
                if origin is None:
                    handler.headers.pop("Origin", None)
                else:
                    handler.headers["Origin"] = origin
                handler.server.server_address = (bound, 8769)
                sent.clear()
                with patch.object(app, "witness_enabled", return_value=True), \
                     patch.object(app, "ask_resource") as asked:
                    handler.do_POST()
                self.assertIn(sent[0][0], (403, 404))
                asked.assert_not_called()

    def test_public_browser_assets_relocated(self):
        root = Path(app.__file__).resolve().parent
        intent = (root / "intent-os.html").read_text(encoding="utf-8")
        ontrack = (root / "on-track.html").read_text(encoding="utf-8")
        self.assertNotIn('id="ats-show"', intent)
        self.assertIn('id="ats-show"', ontrack)
        self.assertIn('"/api/ats/readiness"', ontrack)
        self.assertIn("Ask the Witness about this Resource", intent)
        self.assertNotIn("Teach the Witness about this resource", intent)
        self.assertIn("connect-src 'self'", ontrack)


if __name__ == "__main__":
    unittest.main()
