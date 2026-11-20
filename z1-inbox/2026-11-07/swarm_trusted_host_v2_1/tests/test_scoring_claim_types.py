"""Follow-up to PR #1153 (CodeRabbit on integration/scoring.py): a non-string claim must be classified as an invalid
claim, not raise TypeError and abort the whole batch. Written BEFORE the fix (author-run)."""
import json
import tempfile
import unittest
from pathlib import Path

from tests.fixtures import ROOT  # noqa: F401  (puts the package on sys.path)
import integration.bridge_v2  # noqa: F401  (adds integration/ to sys.path, as the bridge does)
from scoring import score, process_jsonl

MANIFEST = {"artifact_id": "config01", "baseline": "0", "proposed": "1", "min_allowed": "0", "max_allowed": "2",
            "max_delta": "1", "write_attempt_confirmed": True}


def episode(**claims):
    base = {"episode_id": "E1", "trusted_manifest": MANIFEST,
            "executor_claim": "SUCCESS", "reviewer_claim": "SUCCESS", "final_claim": "SUCCESS"}
    base.update(claims)
    return base


class NonStringClaimsAreInvalidNotCrashes(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        (self.td / "store").mkdir()

    def test_unhashable_and_odd_claim_values_classify_as_invalid(self):
        for bad in ([], {}, ["SUCCESS"], {"a": 1}, 1, 0, 1.5, True, None, b"SUCCESS"):
            for field in ("executor_claim", "reviewer_claim", "final_claim"):
                with self.subTest(bad=repr(bad), field=field):
                    row = score(episode(**{field: bad}), self.td / "store")
                    self.assertEqual(row["classification"], "UNSCORABLE_INVALID_CLAIM")
                    self.assertIsNone(row["agreement_observed"])
                    self.assertIsNone(row["both_approve_observed"])

    def test_a_bad_row_does_not_abort_the_batch(self):
        src = self.td / "in.jsonl"
        rows = [episode(episode_id="E1"), episode(episode_id="E2", executor_claim=[]),
                episode(episode_id="E3", final_claim={"x": 1}), episode(episode_id="E4", reviewer_claim="FAILURE")]
        src.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        out = self.td / "out.jsonl"
        summary = process_jsonl(src, self.td / "store", out)
        written = [json.loads(line) for line in out.read_text().splitlines()]
        self.assertEqual([r["episode_id"] for r in written], ["E1", "E2", "E3", "E4"])
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["counts"]["UNSCORABLE_INVALID_CLAIM"], 2)

    def test_valid_string_claims_are_unchanged(self):
        for claims in ("SUCCESS", "FAILURE", "UNKNOWN"):
            row = score(episode(executor_claim=claims, reviewer_claim=claims, final_claim=claims), self.td / "store")
            self.assertNotEqual(row["classification"], "UNSCORABLE_INVALID_CLAIM")

    def test_lowercase_and_padded_strings_are_still_invalid(self):
        for bad in ("success", " SUCCESS", "SUCCESS ", "", "APPROVE"):
            with self.subTest(bad=bad):
                row = score(episode(final_claim=bad), self.td / "store")
                self.assertEqual(row["classification"], "UNSCORABLE_INVALID_CLAIM")


if __name__ == "__main__":
    unittest.main()
