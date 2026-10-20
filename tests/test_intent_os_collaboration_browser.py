"""Browser proof for the two-login finder collaboration rehearsal.

The Worker cryptography and Access boundary are covered by the Node tests. This
test serves the real browser UI with small same-origin API doubles, then exercises
the local export/import handoff between two distinct verified actor codes.
"""

import json
import os
import threading
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / "ui" / "intent-os-collaboration.html").read_bytes()
JAVASCRIPT = (ROOT / "ui" / "intent-os-collaboration.js").read_bytes()
ACTORS = {
    "finder": "USR-AAAAAAAAAAAAAAAAAAAAAAAA",
    "principal": "USR-BBBBBBBBBBBBBBBBBBBBBBBB",
}

sync_api = pytest.importorskip("playwright.sync_api", reason="playwright not installed")


class CollaborationHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format, *_args):
        return

    def _actor(self):
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        actor = cookie.get("test_actor")
        return ACTORS.get(actor.value if actor else "", ACTORS["finder"])

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, value):
        self._send(status, json.dumps(value).encode(), "application/json")

    def _body(self):
        size = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(size) or b"{}")

    def do_GET(self):
        if self.path in ("/", "/intent-os-collaboration.html"):
            self._send(200, HTML, "text/html; charset=utf-8")
            return
        if self.path == "/intent-os-collaboration.js":
            self._send(200, JAVASCRIPT, "text/javascript; charset=utf-8")
            return
        if self.path == "/api/session":
            self._json(200, {
                "actor_id": self._actor(),
                "authentication": "CLOUDFLARE_ACCESS_JWT_VERIFIED",
                "authority_effect": "NONE",
                "execution": "DISABLED",
            })
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        body = self._body()
        if self.path == "/api/collaboration/attest":
            with self.server.receipt_lock:
                self.server.receipt_count += 1
                serial = self.server.receipt_count
            receipt_id = f"RCP-{serial:08X}-0000-4000-8000-{serial:012X}"
            receipt = {
                "schema_version": "humanaios.collaboration.receipt.v0.1",
                "receipt_id": receipt_id,
                "event_type": body["event_type"],
                "relationship_id": body["relationship_id"],
                "artifact_sha256": body["artifact_sha256"],
                "actor_id": self._actor(),
                "actor_role": body["actor_role"],
                "counterparty_actor_id": body.get("counterparty_actor_id"),
                "opportunity_id": body.get("opportunity_id"),
                "authentication": "CLOUDFLARE_ACCESS_JWT_VERIFIED",
                "observed_at": "2026-10-20T00:00:00.000Z",
                "authority_effect": "NONE",
                "execution": "DISABLED",
                "statement": "Test receipt; no authority or execution.",
            }
            envelope = {
                "receipt": receipt,
                "receipt_sha256": "a" * 64,
                "signature": {
                    "algorithm": "HMAC-SHA256",
                    "key_scope": "INTENT_OS_COLLABORATION_WORKER",
                    "value": "b" * 64,
                },
            }
            with self.server.receipt_lock:
                self.server.issued_envelopes[receipt_id] = envelope
            self._json(201, envelope)
            return
        if self.path == "/api/collaboration/verify":
            supplied = body.get("receipt") if isinstance(body, dict) else None
            receipt_id = supplied.get("receipt_id") if isinstance(supplied, dict) else None
            with self.server.receipt_lock:
                authentic = self.server.issued_envelopes.get(receipt_id)
            if authentic != body:
                self._json(400, {"valid": False, "reason": "untrusted envelope"})
                return
            self._json(200, {
                "valid": True,
                "receipt_id": receipt_id,
                "actor_id": supplied["actor_id"],
                "event_type": supplied["event_type"],
                "authority_effect": "NONE",
            })
            return
        if self.path == "/api/intent":
            self._json(200, {
                "candidates": [{
                    "resource_id": "OPP-BROWSER-001",
                    "title": "<img src=x onerror=alert(1)> Contract lead",
                    "description": "A bounded public opportunity.",
                    "source_name": "Public source",
                    "source_url": "https://work.example.org/lead",
                    "observed_at": "2026-10-20T00:00:00Z",
                }],
                "shown_count": 1,
                "source_warning": None,
                "eligibility": "NOT_ASSESSED",
                "authority": "NONE",
                "execution": "DISABLED",
            })
            return
        self._json(404, {"error": "not found"})


@pytest.fixture(scope="module")
def app_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), CollaborationHandler)
    server.receipt_count = 0
    server.receipt_lock = threading.Lock()
    server.issued_envelopes = {}
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    yield f"http://{host}:{port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as playwright:
        executable = os.environ.get("INTENT_OS_CHROMIUM") or None
        try:
            instance = playwright.chromium.launch(executable_path=executable)
        except Exception as exc:
            if os.environ.get("CI"):
                pytest.fail(f"Chromium missing in CI: {exc}")
            pytest.skip(f"Chromium not available: {exc}")
        yield instance
        instance.close()


def _page(browser, app_server, actor):
    context = browser.new_context(accept_downloads=True)
    context.add_cookies([{"name": "test_actor", "value": actor, "url": app_server}])
    page = context.new_page()
    page.goto(f"{app_server}/intent-os-collaboration.html")
    sync_api.expect(page.locator("#loginStatus")).to_have_text("VERIFIED")
    return context, page


def _onboard(page, label):
    page.fill("#displayName", label)
    for control in ("#identityBoundary", "#authorityBoundary", "#actionBoundary"):
        page.check(control)
    page.click("#completeOnboarding")
    sync_api.expect(page.locator("#onboardingStatus")).to_have_text("COMPLETE")


def _export(page, target):
    with page.expect_download() as transfer:
        page.click("#exportCapsule")
    transfer.value.save_as(target)
    return json.loads(target.read_text(encoding="utf-8"))


def test_two_verified_users_match_terms_before_one_unsent_introduction(browser, app_server, tmp_path):
    finder_context, finder = _page(browser, app_server, "finder")
    principal_context = None
    try:
        _onboard(finder, "Finder user")
        finder.fill("#principalLabel", "Service owner")
        finder.fill("#serviceUrl", "https://services.example.org/offer")
        finder.fill("#commissionMin", "5")
        finder.fill("#commissionMax", "10")
        finder.fill("#trigger", "A referred contract is signed and the client pays.")
        finder.click("#createRelationship")
        sync_api.expect(finder.locator("#relationshipStatus")).to_have_text("DRAFT")
        finder.click("#acceptFinder")
        sync_api.expect(finder.locator("#relationshipStatus")).to_have_text(
            "DISCOVERY_ONLY_PENDING_PRINCIPAL"
        )
        sync_api.expect(finder.locator("#introStatus")).to_have_text("BLOCKED")
        assert finder.locator("#authorizeIntro").is_disabled()

        finder.fill("#objective", "Find contract automation work for the service owner")
        finder.click("#mine")
        sync_api.expect(finder.locator("#results h3")).to_have_text(
            "<img src=x onerror=alert(1)> Contract lead"
        )
        assert finder.locator("#results img").count() == 0
        finder.get_by_role("button", name="Attach to finder capsule").click()
        assert finder.locator("#authorizeIntro").is_disabled()

        finder_export = tmp_path / "finder.private.json"
        first_capsule = _export(finder, finder_export)
        assert first_capsule["state"] == "DISCOVERY_ONLY_PENDING_PRINCIPAL"
        assert first_capsule["opportunities"][0]["eligibility"] == "NOT_ASSESSED"

        principal_context, principal = _page(browser, app_server, "principal")
        _onboard(principal, "Service owner user")
        principal.set_input_files("#importCapsule", finder_export)
        sync_api.expect(principal.locator("#relationshipStatus")).to_have_text(
            "DISCOVERY_ONLY_PENDING_PRINCIPAL"
        )
        principal.fill("#commissionExact", "7.5")
        principal.click("#confirmPrincipal")
        sync_api.expect(principal.locator("#relationshipStatus")).to_have_text(
            "PENDING_FINDER_RECONFIRMATION"
        )

        principal_export = tmp_path / "principal.private.json"
        second_capsule = _export(principal, principal_export)
        assert second_capsule["principal"]["actor_id"] == ACTORS["principal"]
        assert second_capsule["offer"]["exact_percent"] == 7.5

        finder.set_input_files("#importCapsule", principal_export)
        sync_api.expect(finder.locator("#relationshipStatus")).to_have_text(
            "PENDING_FINDER_RECONFIRMATION"
        )
        finder.click("#acceptFinder")
        sync_api.expect(finder.locator("#relationshipStatus")).to_have_text(
            "READY_FOR_INTRODUCTION_REVIEW"
        )
        sync_api.expect(finder.locator("#introStatus")).to_have_text("SELECT A LEAD")

        # Already attached leads remain selectable after a two-user import.
        finder.locator("#attachedResults").get_by_role("button", name="Select attached lead").click()
        sync_api.expect(finder.locator("#introStatus")).to_have_text("READY")
        finder.click("#authorizeIntro")
        sync_api.expect(finder.locator("#introStatus")).to_have_text("AUTHORIZED · NOT SENT")
        assert finder.locator("#authorizeIntro").is_disabled()
        sync_api.expect(finder.locator("#introText")).to_contain_text("Nothing was sent")

        # A forged principal envelope with the ID of a genuine finder receipt
        # must not inherit trust from the verified original.
        before_attack = tmp_path / "before-attack.private.json"
        current = _export(finder, before_attack)
        tampered = json.loads(json.dumps(current))
        originals = tampered["receipts"]
        finder_receipt = next(
            row for row in reversed(originals)
            if row["receipt"]["event_type"] == "FINDER_ROLE_ACCEPTED"
        )
        forged = json.loads(json.dumps(finder_receipt))
        forged["receipt"]["event_type"] = "PRINCIPAL_MANDATE_CONFIRMED"
        forged["receipt"]["actor_role"] = "PRINCIPAL"
        forged["receipt"]["actor_id"] = ACTORS["principal"]
        forged["receipt"]["counterparty_actor_id"] = ACTORS["finder"]
        tampered["receipts"] = [
            row for row in originals
            if row["receipt"]["event_type"] != "PRINCIPAL_MANDATE_CONFIRMED"
        ] + [forged]
        forged_file = tmp_path / "forged.private.json"
        forged_file.write_text(json.dumps(tampered), encoding="utf-8")
        finder.set_input_files("#importCapsule", forged_file)
        sync_api.expect(finder.locator("#relationshipStatus")).not_to_have_text("READY_FOR_INTRODUCTION_REVIEW")
        assert finder.locator("#authorizeIntro").is_disabled()

        finder.set_input_files("#importCapsule", before_attack)
        sync_api.expect(finder.locator("#relationshipStatus")).to_have_text("READY_FOR_INTRODUCTION_REVIEW")
        final_export = tmp_path / "authorized.private.json"
        final_capsule = _export(finder, final_export)
        events = [item["receipt"]["event_type"] for item in final_capsule["receipts"]]
        assert events == [
            "FINDER_ROLE_ACCEPTED",
            "PRINCIPAL_MANDATE_CONFIRMED",
            "FINDER_ROLE_ACCEPTED",
            "INTRODUCTION_AUTHORIZED",
        ]
        assert all(item["receipt"]["execution"] == "DISABLED" for item in final_capsule["receipts"])
    finally:
        if principal_context:
            principal_context.close()
        finder_context.close()
