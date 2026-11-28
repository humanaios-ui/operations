"""Real localhost HTTP contract for the local-only form assistance packet route."""
from __future__ import annotations

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app

ROUTE = "/api/form-assistance/packet"
SECRET = "secret-applicant@example.org"


class FormAssistanceHttpTests(unittest.TestCase):
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

    def post(self, payload, headers=None, raw=None):
        headers = {"Content-Type": "application/json", **(headers or {})}
        data = raw if raw is not None else json.dumps(payload).encode("utf-8")
        req = Request(self.base + ROUTE, data=data, headers=headers, method="POST")
        with urlopen(req, timeout=5) as resp:
            return resp.status, json.load(resp)

    def fields(self, packet):
        return {f["id"]: f for f in packet["fields"]}

    def test_packet_is_read_only_and_authorityless(self):
        status, result = self.post({})
        self.assertEqual(status, 200)
        self.assertEqual(result["mode"], "LOCAL_USER_PROVIDED_UNVERIFIED")
        self.assertEqual(result["authority"], "NONE")
        packet = result["packet"]
        self.assertEqual(packet["submission"], "DISABLED")
        self.assertTrue(packet["requires_human_approval"])
        self.assertFalse(packet["policy_verified"])
        self.assertTrue(all(f["status"] == "NEEDS_INPUT" for f in packet["fields"]))

    def test_verified_value_suggested_with_origin_but_drafts_and_consent_blocked(self):
        _, result = self.post({
            "verified": {
                "public_profile": {"value": "https://example.org", "origin": "USER_VERIFIED", "evidence_ref": "public"},
                "project_detail": {"value": "Draft text", "origin": "USER_VERIFIED"},
                "public_consent": {"value": "yes", "origin": "USER_VERIFIED"},
            },
            "assistance_policy": "DRAFT_ALLOWED",
        })
        values = self.fields(result["packet"])
        self.assertEqual(values["public_profile"]["suggested_value"], "https://example.org")
        self.assertEqual(values["public_profile"]["origin"], "USER_VERIFIED")
        self.assertIsNone(values["project_detail"]["suggested_value"])
        self.assertIsNone(values["public_consent"]["suggested_value"])
        self.assertFalse(result["packet"]["policy_verified"])

    def test_unknown_fields_and_bad_types_rejected_without_echo(self):
        for payload in ({"submit": True}, {"verified": []}, {"assistance_policy": 1},
                        {"policy_evidence_ref": 1}, {"assistance_policy": "ANYTHING_" + SECRET}):
            with self.subTest(payload=payload):
                with self.assertRaises(HTTPError) as ex:
                    self.post(payload)
                self.assertEqual(ex.exception.code, 400)
                self.assertNotIn(SECRET.encode(), ex.exception.read())

    def test_rejects_wrong_mime_and_oversize(self):
        with self.assertRaises(HTTPError) as ex:
            self.post({}, {"Content-Type": "text/plain"})
        self.assertEqual(ex.exception.code, 400)
        with self.assertRaises(HTTPError) as ex:
            self.post(None, raw=b"x" * 12289)
        self.assertEqual(ex.exception.code, 400)

    def test_denied_on_wrong_host_or_origin(self):
        for headers in ({"Host": "evil.example"}, {"Origin": "https://evil.example"}):
            with self.subTest(headers=headers):
                with self.assertRaises(HTTPError) as ex:
                    self.post({}, headers)
                self.assertEqual(ex.exception.code, 404)

    def test_no_get_route_and_no_submission_route(self):
        for path in (ROUTE, "/api/form-assistance/submit"):
            with self.subTest(path=path):
                with self.assertRaises(HTTPError) as ex:
                    urlopen(self.base + path, timeout=5)
                self.assertEqual(ex.exception.code, 404)


    def test_page_served_locally_and_has_no_storage_or_external_calls(self):
        with urlopen(self.base + "/form-assistance", timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers.get("Content-Type"))
            page = resp.read().decode("utf-8")
        self.assertIn("/api/form-assistance/packet", page)
        self.assertIn("Read-only", page)
        for forbidden in ("localStorage", "sessionStorage", "indexedDB", "innerHTML", "http://", "https://"):
            self.assertNotIn(forbidden, page)

    def test_page_denied_on_wrong_host(self):
        req = Request(self.base + "/form-assistance", headers={"Host": "evil.example"})
        with self.assertRaises(HTTPError) as ex:
            urlopen(req, timeout=5)
        self.assertEqual(ex.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
