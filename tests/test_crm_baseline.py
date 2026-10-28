"""Offline tests for CRM source-pinned baseline and legacy scanner boundaries."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import crm_baseline as crm  # noqa: E402
import haios_collab_scanner_v1_0 as scanner  # noqa: E402

BASELINE = ROOT / "collaborator-ops/crm/baseline-2026-10-28.json"


class CRMSourceBaselineTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(BASELINE.read_text(encoding="utf-8"))

    def test_exact_pins_and_public_scope(self):
        result = crm.validate_baseline(self.doc)
        self.assertEqual(result["base_commit"], "52aa7c0ed70f6e24ec050d0d56788a791e5f78f7")
        self.assertEqual(len(result["records"]), 7)
        self.assertTrue(all(row["sources"] for row in result["records"]))
        self.assertTrue(all(row["current_state"] != "ACTIVE" for row in result["records"]))

    def test_summary_never_claims_authority(self):
        report = crm.summary(crm.validate_baseline(self.doc))
        self.assertEqual(report["authority_effect"], "NONE")
        self.assertEqual(report["execution"], "DISABLED")
        self.assertEqual(report["status"], "Z1_PROPOSAL_NOT_RATIFIED")

    def test_duplicate_id_rejected(self):
        self.doc["records"][1]["id"] = self.doc["records"][0]["id"]
        with self.assertRaises(crm.BaselineError):
            crm.validate_baseline(self.doc)

    def test_changed_source_url_rejected(self):
        self.doc["records"][0]["sources"][0]["url"] = "https://github.com/humanaios-ui/operations/blob/main/collaborators/DEMARIUS_J_LAWSON.md"
        with self.assertRaises(crm.BaselineError):
            crm.validate_baseline(self.doc)

    def test_changed_blob_rejected_when_local_verification_enabled(self):
        valid = crm.validate_baseline(self.doc)
        with patch.object(crm.subprocess, "run", return_value=CompletedProcess([], 0, "0" * 40 + "\n", "")):
            with self.assertRaises(crm.BaselineError):
                crm.verify_local_pins(valid, ROOT)

    def test_contact_or_extraneous_field_rejected(self):
        self.doc["records"][0]["email"] = "not-for-public-example.invalid"
        with self.assertRaises(crm.BaselineError):
            crm.validate_baseline(self.doc)

    def test_contact_string_rejected(self):
        self.doc["records"][0]["label"] = "person@example.invalid"
        with self.assertRaises(crm.BaselineError):
            crm.validate_baseline(self.doc)

    def test_authority_escalation_rejected(self):
        self.doc["ratification"] = "APPROVED"
        with self.assertRaises(crm.BaselineError):
            crm.validate_baseline(self.doc)

    def test_unverified_current_state_required(self):
        self.doc["records"][0]["current_state"] = "ACTIVE"
        with self.assertRaises(crm.BaselineError):
            crm.validate_baseline(self.doc)

    def test_private_path_traversal_rejected(self):
        self.doc["records"][0]["sources"][0]["path"] = "../private.csv"
        with self.assertRaises(crm.BaselineError):
            crm.validate_baseline(self.doc)

    def test_scanner_empty_adapters_are_not_live_scans(self):
        output = scanner.run({"sources": ["github", "gmail"]})
        self.assertEqual(output["status"], "WARN")
        self.assertEqual(output["sources_scanned"], [])
        self.assertEqual(output["z2_queue_items"], [])
        self.assertEqual(output["source_mode"], "CALLER_SUPPLIED_FIXTURES_ONLY")

    def test_scanner_attaches_baseline_without_approving_any_record(self):
        result = scanner.run({"sources": [], "crm_baseline_path": str(BASELINE)})
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["crm_baseline"]["count"], 7)
        self.assertEqual(result["crm_baseline"]["authority_effect"], "NONE")
        self.assertEqual(result["new_candidates"], [])
        self.assertEqual(result["z2_queue_items"], [])

    def test_scanner_rejects_fake_baseline(self):
        result = scanner.run({"sources": [], "crm_baseline_path": str(BASELINE) + ".missing"})
        self.assertEqual(result["status"], "FAIL")
        self.assertIsNone(result["crm_baseline"])

    def test_scanner_does_not_auto_ratify_external_signal(self):
        result = scanner.run({
            "sources": ["github"],
            "_github_results": [{
                "name": "Unseen evaluation researcher",
                "source_type": "github",
                "source_ref": "https://github.com/org/repo/issues/10",
                "text": "benchmark",
                "signal": "mentioned in issue",
            }],
        })
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["new_candidates"][0]["relationship_status"], "UNVERIFIED")
        self.assertEqual(result["new_candidates"][0]["z2_action"], "REVIEW_CANDIDATE")
        self.assertEqual(result["z2_queue_items"][0]["type"], "ratification")
        # Queue item requests a human look; does not constitute ratification.
        self.assertEqual(len(result["z2_queue_items"]), 1)

    def test_unsourced_signal_cannot_become_candidate(self):
        result = scanner.run({"sources": ["github"], "_github_results": [{"name": "Maybe", "text": "research"}]})
        self.assertEqual(result["new_candidates"], [])
        self.assertEqual(result["status"], "WARN")


if __name__ == "__main__":
    unittest.main()
