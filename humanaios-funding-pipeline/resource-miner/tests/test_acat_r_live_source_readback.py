"""ACAT-R E2: real prior Miner snapshot -> independent official HTTP readback
-> curated source hold -> real INTENT-OS HTTP response.

The 2026-10-30 independent source response is preserved in a GitHub Actions
artifact. These regression tests use that observed receipt offline. They NEVER
make live provider requests and DO NOT infer the employer closed the role.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import app
from resource_miner.snapshot_status import reconcile_snapshot_source_holds

SOURCE = ("https://jobs.lever.co/convergentresearch/"
          "7b0506c1-caf2-4e92-9a44-d062c7a9b988")
RESOURCE_ID = "RES-26D48CDE47BB2BB0"
RECEIPT = "https://github.com/humanaios-ui/operations/actions/runs/41120112081/job/124284382569"
AS_OF = "2026-10-30T20:02:34.479535+00:00"


def request(objective, *, mode):
    raw = json.dumps({"objective": objective, "source_mode": mode}).encode("utf-8")
    handler = object.__new__(app.Handler)
    handler.path = "/api/intent"
    handler.connection = object()
    handler.headers = {"Content-Type": "application/json", "Content-Length": str(len(raw))}
    handler._read_intent_body = lambda n: raw
    received = []
    handler._send_json = lambda value, status=200: received.append((int(status), value))
    handler.do_POST()
    return received[0]


class ActualSourceTransitionTests(unittest.TestCase):
    def test_original_snapshot_retains_prior_active_candidate_and_provenance(self):
        # P1 is a previous mine declaration, not independent truth.
        rows = app._read_jsonl(app.SNAPSHOT_OUT)
        old = next(row for row in rows if row["canonical_url"] == SOURCE)
        self.assertEqual(old["resource_id"], RESOURCE_ID)
        self.assertEqual(old["route"], "VERIFY_NOW")
        self.assertEqual(old["status"], "ACTIVE")
        self.assertIsNone(old.get("source_verification_status"))
        self.assertEqual(old["source_name"], "HumanAIOS Funding Pipeline")

    def test_new_http_404_is_source_unavailable_not_job_confirmed_closed(self):
        catalog = json.loads(app.DEFAULT_FUNDING.read_text(encoding="utf-8"))
        item = next(r for r in catalog if r.get("url") == SOURCE)
        self.assertEqual(item["source_verification_status"], "LINK_FAILED_404")
        self.assertEqual(item["status"], "unverified")
        self.assertFalse(item["url_ok"])
        self.assertEqual(item["last_checked"], "2026-10-30")
        observation = item["source_verification_observation"]
        self.assertEqual(observation["kind"], "INDEPENDENT_HTTP_READBACK")
        self.assertEqual(observation["http_status"], 404)
        self.assertEqual(observation["method"], "HTTPS_GET_NO_REDIRECT")
        self.assertEqual(observation["observed_at"], AS_OF)
        self.assertEqual(observation["source_url"], SOURCE)
        self.assertEqual(observation["evidence_url"], RECEIPT)
        self.assertEqual(observation["authority_effect"], "NONE")
        self.assertIn("does not prove", observation["claim"])
        self.assertEqual(len(item["source_verification_history"]), 1)
        self.assertEqual(item["source_verification_history"][0]["kind"], "USER_REPORTED")
        self.assertEqual(item["source_verification_history"][0]["observed_on"], "2026-10-22")

    def test_snapshot_overlay_keeps_old_file_unchanged(self):
        before = app.SNAPSHOT_OUT.read_bytes()
        catalog_before = app.DEFAULT_FUNDING.read_bytes()
        original = app._read_jsonl(app.SNAPSHOT_OUT)
        projected, count = reconcile_snapshot_source_holds(original, app.DEFAULT_FUNDING)
        self.assertGreaterEqual(count, 1)
        after = next(row for row in projected if row["resource_id"] == RESOURCE_ID)
        old = next(row for row in original if row["resource_id"] == RESOURCE_ID)
        self.assertEqual(after["source_verification_status"], "LINK_FAILED_404")
        self.assertNotIn("source_verification_status", old)
        self.assertEqual(app.SNAPSHOT_OUT.read_bytes(), before)
        self.assertEqual(app.DEFAULT_FUNDING.read_bytes(), catalog_before)

    def test_snapshot_http_projects_real_change_instead_of_old_active_status(self):
        before = hashlib.sha256(app.SNAPSHOT_OUT.read_bytes()).digest()
        with patch.object(app, "_intent_scan", side_effect=AssertionError("no live scan")):
            code, response = request("Convergent Research Program Launch Manager", mode="snapshot")
        self.assertEqual(code, 200)
        self.assertNotIn(RESOURCE_ID, {r["resource_id"] for r in response["candidates"]})
        cases = [r for r in response["verification_cases"] if r["resource_id"] == RESOURCE_ID]
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["verification_state"], "UNAVAILABLE")
        self.assertEqual(cases[0]["reason_code"], "LINK_FAILED_404")
        self.assertGreaterEqual(response["verification_case_count"], 1)
        self.assertIn("withheld", response["source_warning"])
        self.assertEqual(response["authority"], "NONE")
        self.assertEqual(response["execution"], "DISABLED")
        self.assertEqual(response["eligibility"], "NOT_ASSESSED")
        self.assertNotIn("INDEPENDENT_HTTP_READBACK", json.dumps(response))
        self.assertNotIn("USER_REPORTED", json.dumps(response))
        self.assertEqual(hashlib.sha256(app.SNAPSHOT_OUT.read_bytes()).digest(), before)

    def test_live_http_reuses_actual_curated_hold_when_external_dev_adapter_fails(self):
        # This exercises the live-code path using the real funding adapter and
        # a simulated DEV adapter failure. It is not an independent second probe.
        with patch.object(app.devto, "discover", side_effect=RuntimeError("offline isolated")):
            code, response = request("Convergent Research Program Launch Manager", mode="live")
        self.assertEqual(code, 200)
        self.assertNotIn(RESOURCE_ID, {r["resource_id"] for r in response["candidates"]})
        cases = [r for r in response["verification_cases"] if r["resource_id"] == RESOURCE_ID]
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["verification_state"], "UNAVAILABLE")
        self.assertEqual(cases[0]["reason_code"], "LINK_FAILED_404")
        self.assertEqual(response["source_status"], "CURATED_ONLY_LIVE_SOURCE_FAILED")
        self.assertEqual(response["authority"], "NONE")
        self.assertEqual(response["execution"], "DISABLED")

    def test_previous_human_recheck_remains_unknown_and_is_not_job_closure(self):
        with patch.object(app, "_intent_scan", side_effect=AssertionError("no live scan")):
            code, response = request("Deepgram Senior Program Manager Data Operations", mode="snapshot")
        self.assertEqual(code, 200)
        matches = [r for r in response["verification_cases"]
                   if r["resource_id"] == "RES-F6915EA87AD51B54"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["verification_state"], "UNKNOWN")
        self.assertEqual(matches[0]["reason_code"], "RECHECK_REQUIRED")
        self.assertNotIn("RETIRED", json.dumps(matches))


if __name__ == "__main__":
    unittest.main()
