"""ACAT-R E1: four source verification conditions through real /api/intent.

Precommitted expected states. Synthetic snapshots, curated source fixtures,
offline HTTP handler only. No external source access or actions.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import app

URL_BASE = "https://example.org/acat-r-verify/"


def record(identifier, *, deadline=None, url=None, **extra):
    row = {
        "resource_id": identifier,
        "title": "Research compute credits " + identifier,
        "description": "Research compute credits for an open source experiment",
        "source_name": "HumanAIOS Funding Pipeline",
        "canonical_url": url or URL_BASE + identifier.lower(),
        "discovered_at": "2026-10-15T10:00:00Z",
        "route": "VERIFY_NOW",
        "tags": ["research", "compute", "credits"],
        "eligibility_assessed": False,
    }
    if deadline is not None:
        row["deadline"] = deadline
    row.update(extra)
    return row


def snapshot_request():
    handler = object.__new__(app.Handler)
    handler.path = "/api/intent"
    body = json.dumps({
        "objective": "Research compute credits",
        "source_mode": "snapshot",
    }).encode("utf-8")
    handler.headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
    }
    handler._read_intent_body = lambda length: body
    output = []
    handler._send_json = lambda obj, status=200: output.append((status, obj))
    with patch.object(
        app, "_intent_scan",
        side_effect=AssertionError("live adapter must not run"),
    ):
        handler.do_POST()
    return output[0]


class ResourceMinerFourStateExperiment(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.snapshot = root / "synthetic-snapshot.jsonl"
        self.catalog = root / "synthetic-curated-catalog.json"
        self.rows = [
            record("ACATR-STALE", source_evidence_valid_until="2020-01-01"),
            record("ACATR-UNKNOWN"),
            record("ACATR-CONFLICTING"),
            record("ACATR-UNAVAILABLE"),
        ]
        self.save_rows(self.rows)
        self.save_catalog([
            {"url": URL_BASE + "acatr-conflicting",
             "source_verification_status": "SOURCE_WORKING",
             "source_verification_observation": {"observed_on": "2026-10-29"},
             "private_notes": "PRIVATE_CATALOG_NOTE_DO_NOT_ECHO"},
            {"url": URL_BASE + "acatr-conflicting",
             "source_verification_status": "SOURCE_UNAVAILABLE",
             "source_verification_observation": {"observed_on": "2026-10-29"}},
            {"url": URL_BASE + "acatr-unavailable",
             "source_verification_status": "SOURCE_UNAVAILABLE",
             "source_verification_observation": {"kind": "USER_REPORTED"}},
        ])

    def save_rows(self, rows):
        self.snapshot.write_text(
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
            encoding="utf-8",
        )

    def save_catalog(self, records):
        self.catalog.write_text(
            json.dumps(records, sort_keys=True), encoding="utf-8",
        )

    def invoke(self):
        with patch.object(app, "SNAPSHOT_OUT", self.snapshot), patch.object(
            app, "DEFAULT_FUNDING", self.catalog
        ):
            return snapshot_request()

    def test_p1_four_conditions_have_explicit_machine_readable_states(self):
        status, output = self.invoke()
        self.assertEqual(status, 200)
        visible = {row["resource_id"]: row for row in output["candidates"]}
        review = {row["resource_id"]: row for row in output["verification_cases"]}
        self.assertEqual(visible["ACATR-UNKNOWN"]["verification_state"], "UNKNOWN")
        self.assertEqual(
            visible["ACATR-UNKNOWN"]["verification_reason_code"],
            "CURRENT_SOURCE_NOT_INDEPENDENTLY_VERIFIED",
        )
        self.assertEqual(review["ACATR-STALE"]["verification_state"], "STALE")
        self.assertEqual(review["ACATR-STALE"]["reason_code"], "EVIDENCE_EXPIRED")
        self.assertEqual(review["ACATR-CONFLICTING"]["verification_state"], "CONFLICTING")
        self.assertEqual(review["ACATR-UNAVAILABLE"]["verification_state"], "UNAVAILABLE")
        self.assertEqual(set(visible), {"ACATR-UNKNOWN"})
        self.assertEqual(set(review), {
            "ACATR-STALE", "ACATR-CONFLICTING", "ACATR-UNAVAILABLE",
        })
        self.assertEqual(output["authority"], "NONE")
        self.assertEqual(output["execution"], "DISABLED")
        self.assertEqual(output["eligibility"], "NOT_ASSESSED")
        self.assertNotIn("PRIVATE_CATALOG_NOTE_DO_NOT_ECHO", json.dumps(output))

    def test_p2_remove_curated_holds_reverts_to_unknown_not_verified(self):
        first_status, first = self.invoke()
        self.assertEqual(first_status, 200)
        self.save_catalog([])
        status, second = self.invoke()
        self.assertEqual(status, 200)
        visible = {r["resource_id"]: r for r in second["candidates"]}
        self.assertEqual(
            {visible[k]["verification_state"] for k in
             ("ACATR-UNKNOWN", "ACATR-CONFLICTING", "ACATR-UNAVAILABLE")},
            {"UNKNOWN"},
        )
        self.assertEqual(
            {x["resource_id"] for x in second["verification_cases"]},
            {"ACATR-STALE"},
        )
        self.assertEqual(first["authority"], second["authority"])

    def test_p3_replayed_snapshot_does_not_erase_newer_source_holds(self):
        before = self.snapshot.read_bytes()
        status1, first = self.invoke()
        status2, second = self.invoke()
        self.assertEqual((status1, status2), (200, 200))
        self.assertEqual(first["receipt_sha256"], second["receipt_sha256"])
        self.assertEqual(first["verification_cases"], second["verification_cases"])
        self.assertEqual(self.snapshot.read_bytes(), before)
        self.assertEqual(
            hashlib.sha256(self.snapshot.read_bytes()).digest(),
            hashlib.sha256(before).digest(),
        )
        self.assertNotIn(
            "ACATR-CONFLICTING", {x["resource_id"] for x in second["candidates"]}
        )
        self.assertNotIn(
            "ACATR-UNAVAILABLE", {x["resource_id"] for x in second["candidates"]}
        )

    def test_unavailable_source_not_equated_with_closed_opportunity(self):
        status, result = self.invoke()
        self.assertEqual(status, 200)
        row = next(r for r in result["verification_cases"]
                   if r["resource_id"] == "ACATR-UNAVAILABLE")
        self.assertEqual(row["verification_state"], "UNAVAILABLE")
        self.assertEqual(row["reason_code"], "SOURCE_UNAVAILABLE")
        self.assertNotIn("CLOSED", json.dumps(row))
        self.assertNotIn("RETIRED", json.dumps(row))

    def test_unknown_must_not_become_verified_from_untrusted_recency_field(self):
        changed = copy.deepcopy(self.rows)
        changed[1]["last_verified_at"] = "2026-10-30T10:00:00Z"
        changed[1]["eligibility_assessed"] = True
        self.save_rows(changed)
        status, result = self.invoke()
        self.assertEqual(status, 200)
        row = next(r for r in result["candidates"]
                   if r["resource_id"] == "ACATR-UNKNOWN")
        self.assertEqual(row["verification_state"], "UNKNOWN")
        self.assertFalse(row["eligibility_assessed"])

    def test_private_source_with_similar_terms_never_reaches_review_cases(self):
        changed = copy.deepcopy(self.rows) + [
            record("ACATR-PRIVATE", source_name="Private Gmail"),
        ]
        self.save_rows(changed)
        status, result = self.invoke()
        self.assertEqual(status, 200)
        self.assertNotIn("ACATR-PRIVATE", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
