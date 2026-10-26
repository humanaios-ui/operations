"""Read-only pathways regression tests; no network or user profile data."""
from __future__ import annotations

import unittest
from pathlib import Path

from resource_miner.pathways_view import MAX_CANDIDATES, project_pathways


BASE = Path(__file__).resolve().parents[1]


def sample(**overrides):
    row = {
        "resource_id": "RES-TEST", "title": "Research access", "source_name": "Test Feed",
        "source_url": "https://example.org/program", "mine_id": "",
        "discovered_at": "2026-10-02T00:00:00+00:00",
        "need_matches": [{"need_id": "research", "score": 0.8}],
        "requirement_matches": [{"requirement_id": "RR-1"}],
        "evidence": [{"url": "https://example.org/program"}],
        "status": "ACTIVE", "route": "VERIFY_NOW", "eligibility_assessed": True,
        "eligibility_status": "QUALIFIED", "raw": {"secret": "do-not-print"},
    }
    row.update(overrides)
    return row


def projection(rows=None, receipts=None, mines=None, origin="STORED_SNAPSHOT"):
    return project_pathways(
        mines if mines is not None else [{"mine_id": "MINE-ONE", "name": "Test Mine", "enabled": True}],
        [{"need_id": "research", "label": "Research access"}],
        [{"requirement_id": "RR-1", "label": "Independent validation", "gap_status": "CONFIRMED"}],
        rows if rows is not None else [sample()],
        receipts if receipts is not None else [],
        origin=origin, sampled_at="2026-10-26T00:00:00+00:00",
    )


class PathwaysProjectionTests(unittest.TestCase):
    def test_counts_are_observations_not_eligibility(self):
        p = projection()
        self.assertEqual(p["counts"]["candidate_paths"], 1)
        self.assertEqual(p["counts"]["linked_evidence_refs"], 1)
        self.assertEqual(p["counts"]["matched_candidates"], 1)
        self.assertIsNone(p["counts"]["verified_human_outcomes"])
        self.assertEqual(p["eligibility"], "NOT_ASSESSED")
        self.assertEqual(p["paths"][0]["availability"], "NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual(p["paths"][0]["eligibility"], "NOT_ASSESSED")
        self.assertEqual(p["paths"][0]["authority"], "NONE")

    def test_source_name_does_not_invent_mine_provenance(self):
        p = projection(rows=[sample(source_name="Test Mine")])
        self.assertIsNone(p["paths"][0]["mine_id"])
        self.assertEqual(p["paths"][0]["mine_binding"], "UNBOUND_SOURCE")
        bound = projection(rows=[sample(mine_id="MINE-ONE")])
        self.assertEqual(bound["paths"][0]["mine_binding"], "EXPLICIT")
        self.assertEqual(bound["paths"][0]["mine_id"], "MINE-ONE")

    def test_receipts_are_recorded_not_verified_acquisition(self):
        receipt = {"receipt_id": "RSTATE-1", "resource_id": "RES-TEST",
                   "to_resource_state": "ALREADY_ACQUIRED",
                   "observation_type": "OWNERSHIP", "observed_at": "2026-10-02"}
        p = projection(receipts=[receipt])
        self.assertEqual(p["counts"]["recorded_acquired_not_verified"], 1)
        self.assertIsNone(p["counts"]["verified_human_outcomes"])
        self.assertEqual(p["paths"][0]["receipts"][0]["recorded_status"], "ALREADY_ACQUIRED")

    def test_old_active_receipt_does_not_claim_current(self):
        receipt = {"receipt_id": "OLD-ACTIVE", "resource_id": "RES-TEST",
                   "to_status": "ACTIVE", "observation_type": "CURRENTNESS",
                   "observed_at": "2026-10-02"}
        p = projection(receipts=[receipt])
        self.assertEqual(p["paths"][0]["availability"], "NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual(p["paths"][0]["receipts"][0]["recorded_status"], "ACTIVE")

    def test_untrusted_fields_do_not_leak_and_bad_links_are_removed(self):
        p = projection(rows=[sample(
            source_url="http://localhost/private?token=leak",
            canonical_url="file:///Users/private-data",
            primary_source_url="javascript:alert(1)",
            title="Resource", raw={"ssn": "do-not-print"},
        )])
        self.assertIsNone(p["paths"][0]["source_url"])
        self.assertNotIn("do-not-print", str(p))
        self.assertNotIn("QUALIFIED", str(p))
        self.assertNotIn("localhost/private", str(p))

    def test_https_link_is_available_for_user_verification(self):
        p = projection()
        self.assertEqual(p["paths"][0]["source_url"], "https://example.org/program")

    def test_bound_and_deduplicate_rows(self):
        rows = [sample(resource_id=f"RES-{i}") for i in range(MAX_CANDIDATES + 12)]
        p = projection(rows=rows)
        self.assertEqual(p["counts"]["candidate_rows"], MAX_CANDIDATES + 12)
        self.assertEqual(p["counts"]["candidate_paths"], MAX_CANDIDATES)
        self.assertEqual(p["counts"]["unexamined_rows"], 12)
        d = projection(rows=[sample(), sample()])
        self.assertEqual(d["counts"]["candidate_paths"], 1)
        self.assertEqual(d["counts"]["unexamined_rows"], 1)

    def test_public_refresh_has_no_private_receipts(self):
        p = projection(receipts=[], origin="PUBLIC_REFRESH")
        self.assertEqual(p["refresh_semantics"], "PUBLIC_ADAPTER_READ_ON_REQUEST")
        self.assertEqual(p["execution"], "DISABLED")

    def test_invalid_origin_rejected(self):
        with self.assertRaises(ValueError):
            projection(origin="AUTHORIZED")

    def test_server_and_ui_preserve_local_gate(self):
        app = (BASE / "app.py").read_text(encoding="utf-8")
        ui = (BASE / "pathways.html").read_text(encoding="utf-8")
        self.assertIn('parsed.path == "/api/pathways"', app)
        self.assertIn('parsed.path == "/pathways"', app)
        self.assertIn('if not self._local_opportunities_allowed():', app)
        self.assertIn('fetch("/api/pathways?mode="', ui)
        self.assertIn('setInterval(', ui)
        self.assertIn('aria-live="polite"', ui)
        self.assertIn('No independent receipt linked', ui)


if __name__ == "__main__":
    unittest.main()
