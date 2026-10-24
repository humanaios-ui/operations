"""Contract and HTTP-boundary tests for the existing Miner -> INTENT-OS bridge."""
from __future__ import annotations

import io
import json
import unittest
from unittest.mock import Mock, patch

import app
from resource_miner.intent_os import evaluate_objective


def candidate(**changes):
    row = {
        "resource_id": "RES-TEST-PUBLIC",
        "title": "Cloud compute credit grant for research",
        "description": "Cloud capacity for AI research",
        "source_name": "HumanAIOS Funding Pipeline",
        "canonical_url": "https://example.org/grant",
        "discovered_at": "2026-10-02T10:00:00Z",
        "tags": ["grant", "compute"],
        "resource_types": ["compute_credit"],
        "resource_affordances": ["compute_capacity"],
        "route": "VERIFY_NOW",
        "eligibility_assessed": True,  # untrusted upstream claim may not become authorization
    }
    row.update(changes)
    return row


class ObjectiveContractTests(unittest.TestCase):
    def evaluate(self, rows, objective="Find grants for cloud compute"):
        return evaluate_objective(
            objective, rows, source_mode="snapshot",
            source_status="CURATED_SNAPSHOT_NOT_LIVE",
        )

    def test_all_eighteen_matches_reach_browser_for_show_more(self):
        rows = [candidate(resource_id=f"RES-{i}", canonical_url=f"https://example.org/grant/{i}")
                for i in range(18)]
        result = self.evaluate(rows)
        self.assertEqual(result["matched_count"], 18)
        self.assertEqual(result["shown_count"], 18)
        self.assertEqual(len(result["candidates"]), 18)

    def test_matches_existing_candidate_and_never_claims_eligibility(self):
        result = self.evaluate([candidate()])
        self.assertEqual(result["status"], "CANDIDATES_FOR_HUMAN_REVIEW")
        self.assertEqual(result["candidates"][0]["resource_id"], "RES-TEST-PUBLIC")
        self.assertFalse(result["candidates"][0]["eligibility_assessed"])
        self.assertEqual(result["eligibility"], "NOT_ASSESSED")
        self.assertEqual(result["execution"], "DISABLED")
        self.assertEqual(result["authority"], "NONE")

    def test_unrelated_goal_abstains(self):
        result = self.evaluate([candidate()], "Find theatrical costumes")
        self.assertEqual(result["status"], "NO_SUPPORTED_MATCH")
        self.assertEqual(result["candidates"], [])

    def test_private_records_are_never_exposed(self):
        result = self.evaluate([
            candidate(source_name="HackerOne", description="secret grant"),
            candidate(source_name="Private Gmail", description="private grant"),
        ])
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["excluded_count"], 2)

    def test_url_scheme_is_rejected(self):
        self.assertEqual(self.evaluate([candidate(canonical_url="javascript:alert(1)")])["candidates"], [])
        self.assertEqual(self.evaluate([candidate(canonical_url="http://127.0.0.1/")])["candidates"], [])

    def test_private_network_link_disguises_are_rejected(self):
        addresses = [
            "https://192.168.1.55/grant",
            "https://10.0.0.2/grant",
            "https://169.254.169.254/latest/meta-data",
            "https://[::1]/grant",
            "https://service.internal/grant",
            "https://service.local/grant",
            "https://localhost/grant",
            "https://2130706433/grant",
            "https://127.0.0.1.nip.io/grant",
            "https://example.org:8080/grant",
        ]
        for address in addresses:
            with self.subTest(address=address):
                result = self.evaluate([candidate(canonical_url=address)])
                self.assertEqual(result["candidates"], [])

    def test_past_deadline_is_excluded_even_when_route_is_stale(self):
        self.assertEqual(
            self.evaluate([candidate(deadline="2020-01-01", route="VERIFY_NOW")])["candidates"], []
        )

    def test_newest_source_is_not_misrepresented_as_verified(self):
        result = evaluate_objective(
            "Find research grants", [candidate()],
            source_mode="live", source_status="PUBLIC_DEV_LIVE_PLUS_CURATED_FUNDING",
        )
        self.assertEqual(result["eligibility"], "NOT_ASSESSED")
        self.assertEqual(result["receipt_kind"],
                         "UNSIGNED_INPUT_AND_SELECTION_DIGEST_NOT_AN_ATTESTATION")

    def test_objective_is_bounded(self):
        with self.assertRaises(ValueError):
            self.evaluate([candidate()], " " * 501)
        with self.assertRaises(ValueError):
            self.evaluate([candidate()], "grant " * 150)

    def test_actual_committed_miner_snapshot_produces_human_readable_matches(self):
        rows = app._read_jsonl(app.SNAPSHOT_OUT)
        self.assertGreater(len(rows), 0, "Existing Resource Miner snapshot missing")
        result = self.evaluate(rows, "Find grants to support AI research")
        self.assertGreater(result["shown_count"], 0)
        self.assertTrue(all(row["source_name"] == "HumanAIOS Funding Pipeline"
                            for row in result["candidates"]))
        self.assertTrue(all(row["eligibility_assessed"] is False
                            for row in result["candidates"]))

    def test_search_limit_discloses_unexamined_candidates(self):
        rows = [candidate(resource_id=f"RES-{i}", title="Unrelated item", description="unrelated",
                          tags=[], resource_types=[], resource_affordances=[]) for i in range(500)]
        rows.append(candidate(resource_id="RES-BEYOND-LIMIT"))
        result = self.evaluate(rows)
        self.assertEqual(result["status"], "PARTIAL_SEARCH_NO_MATCH")
        self.assertEqual(result["unexamined_count"], 1)
        self.assertIn("incomplete", result["source_warning"].lower())

    def test_digest_changes_when_candidate_evidence_changes(self):
        first = self.evaluate([candidate()])["receipt_sha256"]
        second = self.evaluate([candidate(description="Changed grant details")])["receipt_sha256"]
        self.assertNotEqual(first, second)

    def test_deterministic_receipt(self):
        a = self.evaluate([candidate()])
        b = self.evaluate([candidate()])
        self.assertEqual(a["receipt_sha256"], b["receipt_sha256"])


class HttpIntentTests(unittest.TestCase):
    def invoke(self, body, content_type="application/json"):
        raw = json.dumps(body).encode("utf-8")
        handler = object.__new__(app.Handler)
        handler.path = "/api/intent"
        handler.connection = Mock()
        handler.headers = {"Content-Type": content_type, "Content-Length": str(len(raw))}
        handler.rfile = io.BytesIO(raw)
        observed = []
        handler._send_json = lambda response, status=200: observed.append((int(status), response))
        with patch.object(app, "_intent_scan", return_value=([candidate()], "PUBLIC_DEV_LIVE_PLUS_CURATED_FUNDING", "")) as scan:
            handler.do_POST()
        return observed[0], scan

    def test_page_is_served_by_existing_http_service(self):
        handler = object.__new__(app.Handler)
        handler.path = "/intent-os"
        handler.wfile = io.BytesIO()
        headers = []
        handler._headers = lambda status, content_type, length: headers.append(
            (status, content_type, length)
        )
        handler.do_GET()
        page = handler.wfile.getvalue()
        self.assertEqual(headers[0][0], 200)
        self.assertIn(b"INTENT-OS", page)
        self.assertIn(b"/api/intent", page)
        self.assertIn(b"source_mode", page)
        self.assertIn(b"Observed: ", page)
        self.assertIn(b"Not verified", page)
        self.assertIn(b'if(error.name==="AbortError")throw error;', page)

    def test_chunked_read_completes_under_total_deadline(self):
        raw = b'{"objective":"Find grants"}'
        handler = object.__new__(app.Handler)
        handler.connection = Mock()
        handler.rfile = Mock()
        handler.rfile.read1.side_effect = [raw[:8], raw[8:]]
        with patch.object(app, "monotonic", side_effect=[0.0, 0.0, 0.5, 1.0, 1.5]):
            self.assertEqual(handler._read_intent_body(len(raw)), raw)
        self.assertEqual(handler.rfile.read1.call_count, 2)
        self.assertEqual(handler.connection.settimeout.call_count, 2)

    def test_incomplete_body_fails_closed(self):
        raw = b'{"objective":"Find grants"}'
        handler = object.__new__(app.Handler)
        handler.connection = Mock()
        handler.rfile = io.BytesIO(raw[:8])
        with self.assertRaisesRegex(ValueError, "Incomplete request body"):
            handler._read_intent_body(len(raw))

    def test_drip_feed_exceeds_total_deadline_and_never_scans(self):
        raw = b'{"objective":"Find grants"}'
        handler = object.__new__(app.Handler)
        handler.path = "/api/intent"
        handler.connection = Mock()
        handler.headers = {"Content-Type": "application/json", "Content-Length": str(len(raw))}
        handler.rfile = Mock()
        handler.rfile.read1.side_effect = [raw[:8], raw[8:]]
        observed = []
        handler._send_json = lambda response, status=200: observed.append((int(status), response))
        with patch.object(app, "monotonic", side_effect=[0, 0, 1, 1, 16]), \
             patch.object(app, "_intent_scan") as scan:
            handler.do_POST()
        self.assertEqual(observed[0][0], 408)
        self.assertEqual(observed[0][1]["error"], "Request body deadline exceeded.")
        self.assertTrue(handler.close_connection)
        scan.assert_not_called()

    def test_legacy_admin_routes_fail_closed_without_token(self):
        paths = ("/api/resources", "/api/entitlement/handoff?resource_id=TEST",
                 "/api/scan?persist=1")
        with patch.dict(app.os.environ, {"RESOURCE_MINER_ADMIN_TOKEN": "S" * 32}), \
             patch.object(app, "_run_scan") as scan, \
             patch.object(app, "_read_jsonl") as read:
            for path in paths:
                handler = object.__new__(app.Handler)
                handler.path = path
                handler.headers = {}
                observed = []
                handler._send_json = lambda data, status=200: observed.append((int(status), data))
                handler.do_GET()
                self.assertEqual(observed[0][0], 403, path)
            handler = object.__new__(app.Handler)
            handler.path = "/api/scan"
            handler.headers = {}
            observed = []
            handler._send_json = lambda data, status=200: observed.append((int(status), data))
            handler.do_POST()
            self.assertEqual(observed[0][0], 403)
        scan.assert_not_called()
        read.assert_not_called()

    def test_admin_requires_configured_strong_token_and_matches_exactly(self):
        handler = object.__new__(app.Handler)
        observed = []
        handler._send_json = lambda data, status=200: observed.append((int(status), data))
        secret = "T" * 32
        for configured, given in (("", secret), ("weak", "weak"), (secret, "wrong")):
            handler.headers = {"X-Resource-Miner-Admin-Token": given}
            with patch.dict(app.os.environ, {"RESOURCE_MINER_ADMIN_TOKEN": configured}):
                self.assertFalse(handler._admin_allowed())
            self.assertEqual(observed[-1][0], 403)
            self.assertNotIn(secret, str(observed[-1][1]))
        handler.headers = {"X-Resource-Miner-Admin-Token": secret}
        with patch.dict(app.os.environ, {"RESOURCE_MINER_ADMIN_TOKEN": secret}):
            self.assertTrue(handler._admin_allowed())

    def test_authorized_admin_scan_retains_existing_function(self):
        secret = "T" * 32
        handler = object.__new__(app.Handler)
        handler.path = "/api/scan"
        handler.headers = {"X-Resource-Miner-Admin-Token": secret}
        observed = []
        handler._send_json = lambda data, status=200: observed.append((int(status), data))
        with patch.dict(app.os.environ, {"RESOURCE_MINER_ADMIN_TOKEN": secret}), \
             patch.object(app, "_run_scan", return_value=[]) as scan:
            handler.do_GET()
        self.assertEqual(observed[0][0], 200)
        self.assertEqual(observed[0][1]["count"], 0)
        scan.assert_called_once()

    def test_oversized_request_rejected_without_reading_body(self):
        handler = object.__new__(app.Handler)
        handler.path = "/api/intent"
        handler.connection = Mock()
        handler.headers = {"Content-Type": "application/json", "Content-Length": "999999"}
        handler.rfile = io.BytesIO(b"")
        observed = []
        handler._send_json = lambda response, status=200: observed.append((int(status), response))
        with patch.object(app, "_intent_scan") as scan:
            handler.do_POST()
        self.assertEqual(observed[0][0], 400)
        scan.assert_not_called()

    def test_live_request_reaches_miner(self):
        (status, result), scan = self.invoke({"objective": "Find grants for compute"})
        self.assertEqual(status, 200)
        scan.assert_called_once()
        self.assertEqual(result["shown_count"], 1)

    def test_snapshot_request_does_not_call_live_adapters(self):
        with patch.object(app, "_read_jsonl", return_value=[candidate()]):
            (status, result), scan = self.invoke({"objective": "Find grants", "source_mode": "snapshot"})
        self.assertEqual(status, 200)
        scan.assert_not_called()
        self.assertEqual(result["source_status"], "CURATED_SNAPSHOT_NOT_LIVE")

    def test_missing_snapshot_is_service_unavailable_not_no_match(self):
        with patch.object(app, "SNAPSHOT_OUT") as snapshot, \
             patch.object(app, "_read_jsonl") as read:
            snapshot.is_file.return_value = False
            (status, result), scan = self.invoke({
                "objective": "Find grants", "source_mode": "snapshot",
            })
        self.assertEqual(status, 503)
        self.assertEqual(result["error"], "Stored snapshot unavailable")
        scan.assert_not_called()
        read.assert_not_called()

    def test_unknown_source_and_injected_execution_are_rejected_before_scan(self):
        for body in (
            {"objective": "grants", "source_mode": "private_gmail"},
            {"objective": "grants", "persist": True},
            {"objective": "grants", "source": "hackerone"},
        ):
            (status, _), scan = self.invoke(body)
            self.assertEqual(status, 400)
            scan.assert_not_called()

    def test_non_json_is_rejected(self):
        (status, _), scan = self.invoke({"objective": "grants"}, "text/plain")
        self.assertEqual(status, 400)
        scan.assert_not_called()

    def test_source_failure_is_explicit_not_a_fake_success(self):
        raw = b'{"objective":"Find grants"}'
        handler = object.__new__(app.Handler)
        handler.path = "/api/intent"
        handler.connection = Mock()
        handler.headers = {"Content-Type": "application/json", "Content-Length": str(len(raw))}
        handler.rfile = io.BytesIO(raw)
        observed = []
        handler._send_json = lambda response, status=200: observed.append((int(status), response))
        with patch.object(app, "_intent_scan", side_effect=RuntimeError("upstream")):
            handler.do_POST()
        self.assertEqual(observed[0][0], 503)
        self.assertNotIn("upstream", str(observed[0][1]))


if __name__ == "__main__":
    unittest.main()
