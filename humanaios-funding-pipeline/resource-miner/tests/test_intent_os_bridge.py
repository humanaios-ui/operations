"""Contract and HTTP-boundary tests for the existing Miner -> INTENT-OS bridge."""
from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch

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

    def test_deterministic_receipt(self):
        a = self.evaluate([candidate()])
        b = self.evaluate([candidate()])
        self.assertEqual(a["receipt_sha256"], b["receipt_sha256"])


class HttpIntentTests(unittest.TestCase):
    def invoke(self, body, content_type="application/json"):
        raw = json.dumps(body).encode("utf-8")
        handler = object.__new__(app.Handler)
        handler.path = "/api/intent"
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

    def test_oversized_request_rejected_without_reading_body(self):
        handler = object.__new__(app.Handler)
        handler.path = "/api/intent"
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
