"""Regression tests for issue #1002 E1 shadow replay; no network or writes."""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
import unittest

from resource_miner.feedback_replay_1002 import replay

ROOT = Path(__file__).resolve().parents[1]


class FeedbackReplay1002Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = ROOT / "data/resources.snapshot.jsonl"
        cls.fixture = json.loads((ROOT / "fixtures/feedback_replay_1002_v1.json").read_text())

    def test_baseline_and_proposed_replay(self):
        before = self.snapshot.read_bytes()
        receipt = replay(self.snapshot, self.fixture)
        self.assertEqual(self.snapshot.read_bytes(), before, "Historical source changed")
        self.assertEqual(receipt["status"], "PASS_SHADOW_ONLY")
        self.assertEqual(receipt["stale_source_exposure_at_10_before"], 1)
        self.assertEqual(receipt["stale_source_exposure_at_10_after"], 0)
        self.assertEqual(receipt["unsupported_closure_claims_emitted"], 0)
        self.assertEqual(receipt["human_approval_state"], "NOT_APPROVED")
        self.assertFalse(receipt["shared_revision_applied"])
        self.assertEqual(receipt["external_reviewer_identity"], "NOT_AUTHENTICATED")
        self.assertEqual(receipt["verified_relevant_recall_at_10"],
                         "NOT_ESTABLISHED_NO_INDEPENDENT_RELEVANCE_LABELS")
        self.assertEqual(receipt["candidate_ids_before"].count(
            self.fixture["target"]["resource_id"]), 1)
        self.assertNotIn(self.fixture["target"]["resource_id"], receipt["candidate_ids_after"])
        self.assertEqual(receipt["heldout_candidate_ids_before"],
                         receipt["heldout_candidate_ids_after"])
        self.assertEqual(receipt["acat_state"],
                         "NOT_RUN_CANONICAL_VERSION_PREREQUISITE_750")
        self.assertTrue(all(receipt["conditions"].values()), receipt["conditions"])

    def test_stable_receipt_same_day(self):
        self.assertEqual(replay(self.snapshot, self.fixture),
                         replay(self.snapshot, self.fixture))

    def test_reject_mismatched_pins(self):
        f = copy.deepcopy(self.fixture)
        f["snapshot_git_blob_sha"] = "0" * 40
        with self.assertRaises(ValueError):
            replay(self.snapshot, f)
        f = copy.deepcopy(self.fixture)
        f["snapshot_row_count"] = 1
        with self.assertRaises(ValueError):
            replay(self.snapshot, f)

    def test_reject_unreviewed_status_and_forged_approval(self):
        f = copy.deepcopy(self.fixture)
        f["source_report"]["reported_status"] = "CLOSED_VERIFIED"
        with self.assertRaises(ValueError):
            replay(self.snapshot, f)
        f = copy.deepcopy(self.fixture)
        f["revision"]["shared_approval"] = "HUMAN_APPROVED"
        with self.assertRaises(ValueError):
            replay(self.snapshot, f)

    def test_reject_fuzzy_or_mismatched_source(self):
        f = copy.deepcopy(self.fixture)
        f["target"]["canonical_source_url"] += "?ignored=1"
        with self.assertRaises(ValueError):
            replay(self.snapshot, f)
        f = copy.deepcopy(self.fixture)
        f["external_observation"]["source_url"] = "https://example.org/other"
        with self.assertRaises(ValueError):
            replay(self.snapshot, f)

    def test_modified_source_bytes_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "snapshot.jsonl"
            fake.write_bytes(self.snapshot.read_bytes() + b"\n")
            with self.assertRaises(ValueError):
                replay(fake, self.fixture)


if __name__ == "__main__":
    unittest.main()
