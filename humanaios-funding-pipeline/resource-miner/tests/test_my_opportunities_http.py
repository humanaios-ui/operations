"""Real localhost HTTP contracts for My Opportunities and the journey projector."""
from __future__ import annotations

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
from unittest.mock import Mock

import app


class MyOpportunitiesHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.port = cls.server.server_address[1]
        cls.base = "http://127.0.0.1:" + str(cls.port)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()

    def get(self, route, headers=None):
        req = Request(self.base + route, headers=headers or {})
        with urlopen(req, timeout=5) as resp:
            return resp.status, resp.headers.get("Content-Type"), resp.read()

    def post(self, payload, headers=None):
        headers = {"Content-Type": "application/json", **(headers or {})}
        req = Request(self.base + "/api/my-opportunities/project",
                      data=json.dumps(payload).encode("utf-8"),
                      headers=headers, method="POST")
        with urlopen(req, timeout=5) as resp:
            return resp.status, json.load(resp)

    def starter(self):
        status, _, body = self.get("/api/my-opportunities/starter")
        self.assertEqual(status, 200)
        return json.loads(body)

    def test_new_page_and_link_render_from_real_http_server(self):
        status, mime, page = self.get("/my-opportunities")
        self.assertEqual(status, 200)
        self.assertIn("text/html", mime)
        self.assertIn(b"My Opportunities", page)
        self.assertIn(b"/api/my-opportunities/project", page)
        self.assertIn(b"Import local journey or private evidence bundle JSON", page)
        _, _, home = self.get("/intent-os")
        self.assertIn(b'href="/my-opportunities"', home)
        self.assertIn(b"myOpportunitiesLink", home)

    def test_report_controls_are_checkboxes_and_evidence_is_private(self):
        status, mime, raw = self.get("/my-opportunities")
        self.assertEqual(status, 200)
        self.assertIn("text/html", mime)
        page = raw.decode("utf-8")
        self.assertIn('type="checkbox" name="humanAction"', page)
        self.assertEqual(page.count('type="checkbox" name="humanAction"'), 3)
        self.assertNotIn('<select id="humanAction">', page)
        self.assertIn('id="evidenceLink"', page)
        self.assertIn('id="evidenceExcerpt"', page)
        self.assertIn('id="evidenceClaim"', page)
        self.assertIn("validatedEvidence", page)
        self.assertIn('const evidenceSchema="humanaios.my_opportunities.private_bundle.v0.1"', page)
        self.assertIn("download(\"intent-os-private-evidence-bundle.json\",bundle())", page)
        self.assertIn("localStorage.setItem(localKey,JSON.stringify(bundle()))", page)
        self.assertIn('method:"POST",headers:{"Content-Type":"application/json"},body', page)
        self.assertIn('Only the sanitized journey is sent to the local projection API', page)
        self.assertIn("user-supplied reference", page)
        self.assertNotIn("SYNTHETIC-EMAIL", page)

    def test_server_rejects_private_evidence_bundle_in_projection(self):
        payload = self.starter()
        payload["evidence"] = [{
            "claim": "SIGNUP_WELCOME_EMAIL_OBSERVED",
            "link": "https://mail.google.com/mail/u/0/#inbox/example",
        }]
        with self.assertRaises(HTTPError) as caught:
            self.post(payload)
        self.assertEqual(caught.exception.code, 400)
        # This service has no HTTP evidence collector.
        with self.assertRaises(HTTPError) as caught:
            self.get("/api/my-opportunities/evidence")
        self.assertEqual(caught.exception.code, 404)

    def test_demo_is_truthfully_marked_synthetic(self):
        status, mime, raw = self.get("/api/my-opportunities")
        self.assertEqual(status, 200)
        self.assertIn("application/json", mime)
        result = json.loads(raw)
        self.assertEqual(result["mode"], "SYNTHETIC_DEMONSTRATION_NOT_PERSONAL_EVIDENCE")
        self.assertEqual(result["authority"], "NONE")
        self.assertEqual(len(result["journeys"]), 1)
        journey = result["journeys"][0]
        self.assertEqual(journey["event_count"], 6)
        self.assertEqual(journey["participant_standing"], "NOT_CONFIRMED_BY_PROVIDER")
        self.assertEqual(journey["survey_standing"], "SUBMITTED_HUMAN_REPORTED")
        self.assertEqual(journey["research_submission"], "UNVERIFIED")
        self.assertFalse(journey["can_send_mail"])
        self.assertFalse(journey["can_read_discord"])

    def test_local_json_import_projection_does_not_persist(self):
        payload = self.starter()
        payload["events"] = [e for e in payload["events"]
                             if e["kind"] != "SURVEY_SUBMITTED_HUMAN"]
        status, result = self.post(payload)
        self.assertEqual(status, 200)
        self.assertEqual(result["mode"], "LOCAL_USER_PROVIDED_UNVERIFIED")
        journey = result["journeys"][0]
        self.assertEqual(journey["survey_standing"], "UNVERIFIED")
        self.assertIn("COMPLETE_REQUIRED_SURVEY", journey["next_action_codes"])
        # Import preview does not change the shipped demonstration.
        _, _, raw = self.get("/api/my-opportunities")
        self.assertEqual(json.loads(raw)["journeys"][0]["event_count"], 6)

    def test_http_rejects_secret_fields_and_fake_qualification(self):
        payload = self.starter()
        payload["events"][0]["private_email"] = "secret"
        with self.assertRaises(HTTPError) as ex:
            self.post(payload)
        self.assertEqual(ex.exception.code, 400)
        payload = self.starter()
        payload["events"][0]["kind"] = "PARTICIPANT_QUALIFIED"
        with self.assertRaises(HTTPError) as ex:
            self.post(payload)
        self.assertEqual(ex.exception.code, 400)

    def test_http_rejects_large_and_wrong_mime(self):
        payload = self.starter()
        request = Request(self.base + "/api/my-opportunities/project",
                          data=b"x" * 12289,
                          headers={"Content-Type": "application/json"},
                          method="POST")
        with self.assertRaises(HTTPError) as ex:
            urlopen(request, timeout=5)
        self.assertEqual(ex.exception.code, 400)
        with self.assertRaises(HTTPError) as ex:
            self.post(payload, {"Content-Type": "text/plain"})
        self.assertEqual(ex.exception.code, 400)

    def test_local_route_denied_on_wrong_host(self):
        header = {"Host": "evil.example"}
        for path in ("/my-opportunities", "/api/my-opportunities",
                     "/api/my-opportunities/starter"):
            with self.subTest(path=path):
                with self.assertRaises(HTTPError) as ex:
                    self.get(path, header)
                self.assertEqual(ex.exception.code, 404)

    def test_local_route_denied_on_wrong_origin(self):
        payload = self.starter()
        with self.assertRaises(HTTPError) as ex:
            self.post(payload, {"Origin": "https://evil.example"})
        self.assertEqual(ex.exception.code, 404)

    def test_rejects_wildcard_server_binding_even_for_loopback_peer(self):
        handler = object.__new__(app.Handler)
        handler.server = Mock()
        handler.server.server_address = ("0.0.0.0", 8766)
        handler.client_address = ("127.0.0.1", 11111)
        handler.headers = {"Host": "127.0.0.1:8766"}
        self.assertFalse(handler._local_opportunities_allowed())
        handler.server.server_address = ("127.0.0.1", 8766)
        handler.client_address = ("203.0.113.15", 11111)
        self.assertFalse(handler._local_opportunities_allowed())


if __name__ == "__main__":
    unittest.main()
