"""ATS E0 read-only integration and fail-closed source-status tests."""
from __future__ import annotations

import io
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import app
from resource_miner.ats_readiness import (
    PUBLIC_CASE, project_application_readiness, public_specimen_readiness,
)
from resource_miner.intent_os import evaluate_objective


class ATSReadinessTests(unittest.TestCase):
    def test_report_is_deterministic_and_has_no_execution(self):
        a = public_specimen_readiness()
        b = public_specimen_readiness()
        self.assertEqual(a, b)
        self.assertFalse(a["actionable"])
        self.assertEqual(a["authority"], "NONE")
        self.assertEqual(a["execution"], "DISABLED")
        self.assertEqual(a["role_closed"], "NOT_ESTABLISHED")
        self.assertEqual(a["ats_resume_parser"], "NOT_TESTED")
        self.assertEqual(a["applicant_qualification"], "NOT_ASSESSED")
        self.assertEqual(a["receipt_kind"], "UNSIGNED_PROJECTION_DIGEST_NOT_ATTESTATION")

    def test_user_report_does_not_become_employer_closure(self):
        row = public_specimen_readiness()
        self.assertEqual(row["source_status"], "REPORTED_UNAVAILABLE_AT_ORIGINAL_ENDPOINT")
        self.assertEqual(row["decision"], "HOLD_FOR_OFFICIAL_SOURCE_RECHECK")
        self.assertTrue(any(o["observation"] == "ROLE_NOT_LISTED_AT_LEVER_ENDPOINT"
                            for o in row["source_observations"]))

    def test_single_official_source_failure_cannot_invent_user_report(self):
        case = dict(PUBLIC_CASE)
        case["source_observations"] = [{
            "kind": "OFFICIAL_SITE_OBSERVATION",
            "observation": "SOURCE_UNAVAILABLE",
        }]
        result = project_application_readiness(case)
        self.assertIn("SOURCE_UNAVAILABLE", result["reason"])
        self.assertNotIn("later user report", result["reason"])
        self.assertNotIn("broken job link", result["reason"])
        self.assertEqual(result["role_closed"], "NOT_ESTABLISHED")

    def test_no_private_data_echo_even_if_case_has_injected_fields(self):
        case = dict(PUBLIC_CASE)
        case["resume"] = "SECRET PRIVATE CV"
        case["email"] = "person@example.org"
        case["source_observations"] = [
            dict(PUBLIC_CASE["source_observations"][0], notes="PRIVATE NOTES")
        ]
        raw = json.dumps(project_application_readiness(case))
        for leaked in ("SECRET PRIVATE CV", "person@example.org", "PRIVATE NOTES"):
            self.assertNotIn(leaked, raw)

    def test_unknown_or_positive_claim_fails_closed(self):
        with self.assertRaises(ValueError):
            project_application_readiness({"specimen_id": "WRONG", "source_observations": []})
        case = dict(PUBLIC_CASE)
        case["source_observations"] = [{
            "kind": "OFFICIAL_SITE_OBSERVATION", "observation": "ROLE_OPEN",
        }]
        with self.assertRaises(ValueError):
            project_application_readiness(case)

    def test_observations_bounded(self):
        case = dict(PUBLIC_CASE)
        case["source_observations"] = [PUBLIC_CASE["source_observations"][0]] * 17
        with self.assertRaises(ValueError):
            project_application_readiness(case)

    def test_route_returns_public_report_without_scanning(self):
        handler = object.__new__(app.Handler)
        handler.path = "/api/ats/readiness"
        results = []
        handler._send_json = lambda data, status=200: results.append((status, data))
        handler.do_GET()
        status, result = results[0]
        self.assertEqual(status, 200)
        self.assertFalse(result["actionable"])
        self.assertNotIn("SECRET", json.dumps(result))

    def test_unknown_query_returns_404(self):
        handler = object.__new__(app.Handler)
        handler.path = "/api/ats/readiness?specimen=unknown"
        results = []
        handler._send_json = lambda data, status=200: results.append((status, data))
        handler.do_GET()
        self.assertEqual(results[0][0], 404)

    def test_known_failed_candidate_status_is_not_surface_as_a_live_match(self):
        row = {
            "resource_id": "RM-TEST-STALE",
            "title": "Research program launch manager",
            "description": "Role for scientific research program operations",
            "source_name": "HumanAIOS Funding Pipeline",
            "canonical_url": "https://jobs.lever.co/convergentresearch/obsolete",
            "route": "VERIFY_NOW",
            "source_verification_status": "LINK_FAILED_404",
        }
        found = evaluate_objective(
            "Find research program manager",
            [row], source_mode="snapshot", source_status="CURATED_SNAPSHOT_NOT_LIVE"
        )
        self.assertEqual(found["shown_count"], 0)
        self.assertEqual(found["eligibility"], "NOT_ASSESSED")
        self.assertEqual(found["authority"], "NONE")


class ATSSearchTransportTests(unittest.TestCase):
    def test_failed_status_survives_real_search_without_raw_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "catalog.json"
            for status in ("LINK_FAILED_404", "ROLE_NOT_LISTED", "SOURCE_UNAVAILABLE", "RECHECK_REQUIRED", None):
                with self.subTest(status=status):
                    path.write_text(json.dumps([{
                        "name": "Convergent Research Program Launch Manager",
                        "url": PUBLIC_CASE["source_url"],
                        "category": "paid_work", "status": "active",
                        "source_verification_status": status,
                        "private_notes": "PRIVATE TRANSPORT CANARY",
                    }]), encoding="utf-8")
                    with patch.object(app, "DEFAULT_FUNDING", path), patch.object(app.devto, "discover", return_value=[]):
                        rows, source_status, warning = app._intent_scan()
                    self.assertEqual(len(rows), 1)
                    self.assertEqual(rows[0]["source_verification_status"], status)
                    self.assertNotIn("raw", rows[0])
                    self.assertNotIn("PRIVATE TRANSPORT CANARY", json.dumps(rows))
                    result = evaluate_objective(
                        "Find research program manager", rows, source_mode="live",
                        source_status=source_status, source_warning=warning,
                    )
                    self.assertEqual(result["shown_count"], 0 if status else 1)

    def test_adapter_does_not_promote_arbitrary_status_payload(self):
        from resource_miner.sources.funding_pipeline import discover
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "catalog.json"
            for value in ("PRIVATE CANARY", {"private": "PRIVATE CANARY"}):
                with self.subTest(value=value):
                    path.write_text(json.dumps([{
                        "name": "Research program manager", "url": "https://example.org/job",
                        "source_verification_status": value,
                    }]), encoding="utf-8")
                    row = next(discover(path)).to_dict()
                    self.assertIsNone(row["source_verification_status"])
                    self.assertNotIn("PRIVATE CANARY", json.dumps(row))

    def test_actual_catalog_role_stays_out_of_live_intent(self):
        with patch.object(app.devto, "discover", return_value=[]):
            rows, _, _ = app._intent_scan()
            role = [r for r in rows if r["canonical_url"] == PUBLIC_CASE["source_url"]]
            self.assertEqual(len(role), 1)
            self.assertEqual(role[0]["source_verification_status"], "LINK_FAILED_404")
            handler = object.__new__(app.Handler)
            handler.path = "/api/intent"
            body = json.dumps({"objective": "Convergent Research Program Launch Manager", "source_mode": "live"}).encode()
            handler.headers = {"Content-Type": "application/json", "Content-Length": str(len(body))}
            handler._read_intent_body = lambda length: body
            responses = []
            handler._send_json = lambda data, status=200: responses.append((status, data))
            handler.do_POST()
            self.assertEqual(responses[0][0], 200)
            self.assertNotIn(PUBLIC_CASE["source_url"], json.dumps(responses[0][1]))
            self.assertFalse(any(
                "Convergent Research Program Launch Manager" in row["title"]
                for row in responses[0][1]["candidates"]
            ))


if __name__ == "__main__":
    unittest.main()
