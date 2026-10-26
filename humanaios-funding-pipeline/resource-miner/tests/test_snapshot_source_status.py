"""Regression: held source status carries through stored snapshots to HTTP intent.

No live provider requests, no mutation of historical snapshots or catalog.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import app
from resource_miner.snapshot_status import reconcile_snapshot_source_holds

CONVERGENT_URL = (
    "https://jobs.lever.co/convergentresearch/"
    "7b0506c1-caf2-4e92-9a44-d062c7a9b988"
)


def intent_request(objective: str, mode: str = "snapshot"):
    handler = object.__new__(app.Handler)
    handler.path = "/api/intent"
    body = json.dumps({"objective": objective, "source_mode": mode}).encode("utf-8")
    handler.headers = {"Content-Type": "application/json", "Content-Length": str(len(body))}
    handler._read_intent_body = lambda length: body
    replies = []
    handler._send_json = lambda payload, status=200: replies.append((status, payload))
    # A snapshot-mode request must never invoke live or private adapters.
    with patch.object(app, "_intent_scan", side_effect=AssertionError("network scan attempted")):
        handler.do_POST()
    return replies[0]


class SnapshotSourceHoldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.catalog = root / "catalog.json"
        self.snapshot = root / "snapshot.jsonl"

    def write_fixture(self):
        records = [
            {"url": CONVERGENT_URL, "name": "Convergent Research Program Launch Manager",
             "source_verification_status": "ROLE_NOT_LISTED",
             "private_notes": "SECRET_DO_NOT_ECHO"},
            {"url": CONVERGENT_URL + "?id=other", "name": "Different same-named job"},
        ]
        rows = [
            {"resource_id": "RES-HELD", "title": "Convergent Research Program Launch Manager",
             "canonical_url": CONVERGENT_URL, "source_name": "HumanAIOS Funding Pipeline",
             "route": "VERIFY_NOW", "description": "compute credits for research",
             "eligibility_assessed": False},
            {"resource_id": "RES-DIFFERENT", "title": "Convergent Research Program Launch Manager",
             "canonical_url": CONVERGENT_URL + "?id=other",
             "source_name": "HumanAIOS Funding Pipeline", "route": "WATCH",
             "description": "compute credits for research", "eligibility_assessed": False},
            {"resource_id": "RES-OTHER-SOURCE", "title": "Convergent Research Program Launch Manager",
             "canonical_url": CONVERGENT_URL, "source_name": "DEV Community",
             "route": "WATCH", "description": "compute credits for research",
             "eligibility_assessed": False},
        ]
        self.catalog.write_text(json.dumps(records), encoding="utf-8")
        self.snapshot.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        return rows

    def test_exact_url_only_and_immutable_snapshot(self):
        original_rows = self.write_fixture()
        before = self.snapshot.read_bytes()
        projected, held = reconcile_snapshot_source_holds(original_rows, self.catalog)
        self.assertEqual(held, 1)
        self.assertEqual(projected[0]["source_verification_status"], "ROLE_NOT_LISTED")
        self.assertNotIn("source_verification_status", projected[1])
        self.assertNotIn("source_verification_status", projected[2])
        self.assertNotIn("source_verification_status", original_rows[0])
        self.assertEqual(self.snapshot.read_bytes(), before)

    def test_snapshot_http_removes_only_exact_held_url_and_discloses_hold(self):
        self.write_fixture()
        original_hash = hashlib.sha256(self.snapshot.read_bytes()).hexdigest()
        with patch.object(app, "SNAPSHOT_OUT", self.snapshot), patch.object(app, "DEFAULT_FUNDING", self.catalog):
            status, result = intent_request("Convergent Research Program Launch Manager")
        self.assertEqual(status, 200)
        visible_ids = {c["resource_id"] for c in result["candidates"]}
        self.assertNotIn("RES-HELD", visible_ids)
        self.assertIn("RES-DIFFERENT", visible_ids)
        self.assertIn("RES-OTHER-SOURCE", visible_ids)
        self.assertEqual(result["shown_count"], 2)
        self.assertEqual(result["matched_count"], 2)
        self.assertIn("1 catalog-matched source(s) withheld", result["source_warning"])
        self.assertEqual(result["eligibility"], "NOT_ASSESSED")
        self.assertEqual(result["execution"], "DISABLED")
        self.assertEqual(result["authority"], "NONE")
        self.assertNotIn("SECRET_DO_NOT_ECHO", json.dumps(result))
        self.assertEqual(hashlib.sha256(self.snapshot.read_bytes()).hexdigest(), original_hash)

    def test_unknown_source_status_does_not_suppress(self):
        self.write_fixture()
        self.catalog.write_text(json.dumps([{
            "url": CONVERGENT_URL, "source_verification_status": "SOURCE_WORKING"
        }]), encoding="utf-8")
        with patch.object(app, "SNAPSHOT_OUT", self.snapshot), patch.object(app, "DEFAULT_FUNDING", self.catalog):
            status, result = intent_request("Convergent Research Program Launch Manager")
        self.assertEqual(status, 200)
        self.assertEqual(result["shown_count"], 3)

    def test_missing_catalog_fails_closed_instead_of_reintroducing_role(self):
        self.write_fixture()
        with patch.object(app, "SNAPSHOT_OUT", self.snapshot), patch.object(app, "DEFAULT_FUNDING", self.catalog.parent / "absent.json"):
            status, result = intent_request("Convergent Research Program Launch Manager")
        self.assertEqual(status, 503)
        self.assertNotIn("RES-HELD", json.dumps(result))

    def test_deepgram_recheck_carries_to_real_snapshot_http_search(self):
        # Real catalog's USER_REPORTED hold is a recheck, not verified closure.
        deepgram = ("https://jobs.ashbyhq.com/Deepgram/"
                    "681c5324-1234-4222-b783-a8a7a9440005")
        catalog = json.loads(app.DEFAULT_FUNDING.read_text(encoding="utf-8"))
        row = next(row for row in catalog if row.get("url") == deepgram)
        self.assertEqual(row.get("source_verification_status"), "RECHECK_REQUIRED")
        self.assertEqual(row.get("source_verification_observation", {}).get("kind"),
                         "USER_REPORTED")
        before = hashlib.sha256(app.SNAPSHOT_OUT.read_bytes()).hexdigest()
        self.assertIn(deepgram.encode("utf-8"), app.SNAPSHOT_OUT.read_bytes())
        status, result = intent_request("Deepgram Senior Program Manager Data Operations")
        self.assertEqual(status, 200)
        self.assertNotIn(deepgram, json.dumps(result.get("candidates", [])))
        self.assertIn("withheld", result["source_warning"])
        self.assertEqual(result["eligibility"], "NOT_ASSESSED")
        self.assertEqual(result["authority"], "NONE")
        self.assertEqual(hashlib.sha256(app.SNAPSHOT_OUT.read_bytes()).hexdigest(), before)

    def test_actual_curated_source_hold_survives_actual_snapshot_read(self):
        # The historical snapshot contains the disputed candidate; the later
        # curated catalog records ROLE_NOT_LISTED. They are intentionally not
        # rewritten during a query.
        catalog_bytes = app.DEFAULT_FUNDING.read_bytes()
        snapshot_bytes = app.SNAPSHOT_OUT.read_bytes()
        known = next(
            row for row in json.loads(catalog_bytes)
            if row.get("url") == CONVERGENT_URL
        )
        self.assertEqual(known["source_verification_status"], "ROLE_NOT_LISTED")
        self.assertIn(CONVERGENT_URL.encode("utf-8"), snapshot_bytes)
        status, result = intent_request("compute credits for AI research")
        self.assertEqual(status, 200)
        self.assertGreater(result["matched_count"], 0)
        self.assertNotIn(CONVERGENT_URL, json.dumps(result))
        self.assertIn("withheld", result["source_warning"])
        self.assertEqual(result["authority"], "NONE")
        self.assertEqual(result["eligibility"], "NOT_ASSESSED")
        self.assertEqual(hashlib.sha256(app.DEFAULT_FUNDING.read_bytes()).digest(), hashlib.sha256(catalog_bytes).digest())
        self.assertEqual(hashlib.sha256(app.SNAPSHOT_OUT.read_bytes()).digest(), hashlib.sha256(snapshot_bytes).digest())


if __name__ == "__main__":
    unittest.main()
