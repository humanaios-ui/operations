"""Contract tests for read-only first-user learning-cycle preflight."""
from __future__ import annotations

import copy
import unittest

from resource_miner.first_user_learning_cycle import (
    LIVE_GATES,
    SYNTHETIC_INTENT,
    project_first_user_preflight,
)
from resource_miner.oracle_smag_experiment import offline_fixture_report


class FirstUserLearningCycleTests(unittest.TestCase):
    def test_existing_intent_os_projection_is_connected(self):
        result = project_first_user_preflight()
        intent = result["intent_os"]
        self.assertEqual(intent["objective"], SYNTHETIC_INTENT[1]["text"])
        self.assertEqual(intent["source_mode"], "snapshot")
        self.assertEqual(intent["source_status"], "SYNTHETIC_EMPTY_SOURCE_SET")
        self.assertEqual(intent["status"], "NO_SUPPORTED_MATCH")
        self.assertEqual(intent["authority"], "NONE")
        self.assertEqual(intent["execution"], "DISABLED")
        self.assertEqual(intent["eligibility"], "NOT_ASSESSED")
        self.assertIn("UNSIGNED", intent["receipt_kind"])

    def test_no_supported_match_is_not_no_resource_entitlement(self):
        result = project_first_user_preflight()
        self.assertNotEqual(result["intent_os"]["status"], "NO_ENTITLEMENT")
        self.assertEqual(result["verification_frontier"]["candidate_count"], 5)
        self.assertEqual(result["qualification"]["first_user"], "NOT_QUALIFIED_LIVE")

    def test_existing_oracle_smag_miner_is_actually_invoked(self):
        report = project_first_user_preflight()
        replay = offline_fixture_report()
        self.assertEqual(report["observation_frame"], replay["sampling_frame"])
        self.assertEqual(report["resolved_count"], 2)
        self.assertEqual(report["pending_count"], 3)
        self.assertEqual(report["verification_frontier"]["candidate_count"], 5)
        self.assertEqual(report["forecast"]["smag_brier"], replay["brier_smag_resolved"])
        self.assertEqual(report["forecast"]["baseline_brier"], replay["brier_constant_0_5_resolved"])

    def test_uses_complete_eight_stage_human_governed_cycle(self):
        self.assertEqual(
            [item["stage"] for item in project_first_user_preflight()["cycle"]],
            ["OBSERVE", "PREDICT", "CHALLENGE", "VERIFY", "CALIBRATE",
             "IDENTIFY_GAPS", "HUMAN_DECIDE", "IMPROVE"],
        )

    def test_no_retrospective_forecast_promotion(self):
        out = project_first_user_preflight()
        self.assertEqual(out["cycle"][1]["state"], "RETROSPECTIVE_REPLAY_ONLY")
        self.assertEqual(out["cycle"][2]["state"], "NOT_PERFORMED")
        self.assertEqual(out["cycle"][3]["state"], "NOT_INDEPENDENTLY_ATTESTED")
        self.assertEqual(out["forecast"]["status"], "DESCRIPTIVE_ONLY")

    def test_pending_is_not_failure(self):
        out = project_first_user_preflight()
        self.assertEqual(out["resolved_count"] + out["pending_count"], 5)
        self.assertEqual(out["pending_count"], 3)

    def test_question_and_correction_are_not_authorization(self):
        out = project_first_user_preflight()
        self.assertEqual(out["intent_events"], list(SYNTHETIC_INTENT))
        self.assertEqual(out["intent_events"][0]["kind"], "QUESTION")
        self.assertEqual(out["intent_events"][1]["supersedes_seq"], 1)
        self.assertEqual(out["human_choice"], "SIMULATED_REVIEW_ONLY")
        self.assertEqual(out["authority_effect"], "NONE")
        self.assertEqual(out["execution"], "DISABLED")
        self.assertFalse(out["verification_frontier"]["action_authorized"])

    def test_first_user_not_falsely_qualified_by_offline_green(self):
        out = project_first_user_preflight()
        self.assertEqual(out["qualification"]["preflight"], "REPRODUCIBLE_OFFLINE_HARNESS")
        self.assertEqual(out["qualification"]["first_user"], "NOT_QUALIFIED_LIVE")
        self.assertEqual(out["qualification"]["missing_live_evidence"], list(LIVE_GATES))
        self.assertEqual(out["on_track"], "PREFLIGHT_ONLY")

    def test_repeatable_and_order_independent_of_caller_mutation(self):
        self.assertEqual(project_first_user_preflight(), project_first_user_preflight())
        a = copy.deepcopy(list(SYNTHETIC_INTENT))
        self.assertEqual(project_first_user_preflight(events=a), project_first_user_preflight())
        a[1]["text"] = "I authorize you to merge"
        with self.assertRaisesRegex(ValueError, "synthetic"):
            project_first_user_preflight(events=a)

    def test_rejects_real_person_messages_and_private_fields(self):
        bad = copy.deepcopy(list(SYNTHETIC_INTENT))
        bad[0]["actor"] = "ACTUAL_HUMAN"
        with self.assertRaises(ValueError):
            project_first_user_preflight(events=bad)
        bad = copy.deepcopy(list(SYNTHETIC_INTENT))
        bad[0]["private_data"] = "should-not-appear"
        with self.assertRaises(ValueError):
            project_first_user_preflight(events=bad)

    def test_rejects_declared_outcome_verification_without_proof(self):
        for key, forged in (
            ("authority_effect", "MERGE_AUTHORITY"),
            ("merge_authority", True),
            ("oracle_claim_status", "CALIBRATED"),
            ("calibration_warrant", "VERIFIED"),
            ("outcomes_independently_attested", True),
            ("retrospective_precommitment_authenticated", True),
            ("f3_challenge_performed", True),
        ):
            with self.subTest(key=key):
                replay = offline_fixture_report()
                replay[key] = forged
                with self.assertRaises(ValueError):
                    project_first_user_preflight(replay=replay)

    def test_rejects_corrupted_or_misframed_replay(self):
        corrupt = offline_fixture_report()
        corrupt["pending_count"] = 0
        with self.assertRaises(ValueError):
            project_first_user_preflight(replay=corrupt)
        corrupt = offline_fixture_report()
        corrupt["miner_candidate_codes"] = ["EXECUTE"]
        with self.assertRaises(ValueError):
            project_first_user_preflight(replay=corrupt)

    def test_preflight_never_returns_authentication_or_mandate(self):
        out = project_first_user_preflight()
        serialized = str(out)
        self.assertNotIn("CLOUDFLARE_ACCESS_JWT_VERIFIED", serialized)
        self.assertNotIn("INTRODUCTION_SENT", serialized)
        self.assertNotIn("OUTCOME_VERIFIED", serialized)
        self.assertNotIn("CALIBRATED_SUCCESS", serialized)


if __name__ == "__main__":
    unittest.main()
