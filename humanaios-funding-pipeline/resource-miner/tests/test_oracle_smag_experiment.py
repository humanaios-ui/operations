"""Offline reproducibility and adversarial controls for Oracle × SMAG × Miner."""
from __future__ import annotations
import copy
import json
import unittest

from resource_miner.oracle_smag_experiment import (
    FIXTURES, offline_fixture_report, project_experiment,
)


def load_snapshots():
    return (
        json.loads((FIXTURES / "oracle_smag_predictions_20261021.json").read_text()),
        json.loads((FIXTURES / "oracle_smag_outcomes_20261021.json").read_text()),
    )


class OracleSMAGMinerExperimentTests(unittest.TestCase):
    def test_replay_has_two_resolved_three_censored(self):
        observed = offline_fixture_report()
        self.assertEqual(observed["sampling_frame"], [432, 573, 724, 817, 931])
        self.assertEqual(observed["frame_count"], 5)
        self.assertEqual(observed["resolved_count"], 2)
        self.assertEqual(observed["pending_count"], 3)
        self.assertAlmostEqual(observed["brier_smag_resolved"], (1 - .85) ** 2)
        self.assertAlmostEqual(observed["brier_constant_0_5_resolved"], 0.25)
        self.assertEqual(observed["miner_candidate_count"], 5)
        self.assertEqual(observed["miner_candidate_codes"], ["MISSING_VERIFICATION"] * 5)
        self.assertEqual(observed["oracle_claim_status"], "DESCRIPTIVE_ONLY")
        self.assertEqual(observed["authority_effect"], "NONE")
        self.assertFalse(observed["merge_authority"])
        self.assertFalse(observed["f3_challenge_performed"])
        self.assertFalse(observed["retrospective_precommitment_authenticated"])
        self.assertFalse(observed["outcomes_independently_attested"])

    def test_replay_is_deterministic(self):
        self.assertEqual(offline_fixture_report(), offline_fixture_report())

    def test_one_pending_pr_never_counts_as_failure_or_success(self):
        f, o = load_snapshots()
        o["rows"][1]["status"] = "OPEN"
        o["rows"][1]["merged_at"] = None
        result = project_experiment(f, o)
        self.assertEqual(result["resolved_count"], 1)
        self.assertEqual(result["pending_count"], 4)
        self.assertEqual(result["oracle_claim_status"], "DESCRIPTIVE_ONLY")

    def test_split_or_incomplete_sampling_frames_fail_closed(self):
        f, o = load_snapshots()
        o["rows"].pop()
        with self.assertRaisesRegex(ValueError, "sampling frames"):
            project_experiment(f, o)

    def test_future_merge_time_fails(self):
        f, o = load_snapshots()
        o["rows"][0]["merged_at"] = "2026-12-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "future merge"):
            project_experiment(f, o)

    def test_future_merge_subsecond_and_timezone_offsets_fail(self):
        for future in ("2026-10-21T20:00:00.500Z", "2026-10-21T19:30:00-01:00"):
            with self.subTest(future=future):
                f, o = load_snapshots()
                o["rows"][0]["merged_at"] = future
                with self.assertRaisesRegex(ValueError, "future merge"):
                    project_experiment(f, o)

    def test_equivalent_snapshot_offsets_are_accepted(self):
        baseline = offline_fixture_report()
        for forecast_time, outcome_time in (
            ("2026-10-21T20:00:00Z", "2026-10-21T22:00:00+02:00"),
            ("2026-10-21T19:00:00-01:00", "2026-10-21T20:00:00.000+00:00"),
        ):
            with self.subTest(forecast=forecast_time, outcome=outcome_time):
                f, o = load_snapshots()
                f["snapshot_at"] = forecast_time
                o["snapshot_at"] = outcome_time
                self.assertEqual(project_experiment(f, o), baseline)

    def test_different_snapshot_instants_fail(self):
        f, o = load_snapshots()
        o["snapshot_at"] = "2026-10-21T20:00:00.001Z"
        with self.assertRaisesRegex(ValueError, "observation times must match"):
            project_experiment(f, o)

    def test_unrecognized_closed_state_does_not_become_failure(self):
        f, o = load_snapshots()
        o["rows"][0]["status"] = "CLOSED"
        o["rows"][0]["merged_at"] = None
        with self.assertRaisesRegex(ValueError, "unsupported observation state"):
            project_experiment(f, o)

    def test_probabilities_and_heads_are_strict(self):
        f, o = load_snapshots()
        f["rows"][0]["smag_p_meta"] = True
        with self.assertRaisesRegex(ValueError, "SMAG"):
            project_experiment(f, o)
        f, o = load_snapshots()
        o["rows"][0]["head_sha"] = "forged"
        with self.assertRaisesRegex(ValueError, "head OID"):
            project_experiment(f, o)


if __name__ == "__main__":
    unittest.main()
