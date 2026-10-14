import json
import unittest
from pathlib import Path

from resource_miner.combinations import load_snapshot
from resource_miner.outcome_probe import (run_shadow_trial, runtime_prerequisites, verify_source_queue)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "data/experiments/resource_complementarity_pilot.v1.json").read_text())


class OutcomeShadowTests(unittest.TestCase):
    def setUp(self):
        self.rows = load_snapshot(ROOT / "data/resources.snapshot.jsonl")

    def test_real_source_review_task_does_not_fake_synergy(self):
        result = run_shadow_trial(self.rows, CONFIG)
        self.assertEqual(result["mode"], "LOCAL_REAL_EXECUTION_NO_EXTERNAL_PROVIDERS")
        self.assertEqual(result["comparison"]["baseline"]["generated_verification_questions"], 1)
        self.assertEqual(result["comparison"]["bundle"]["generated_verification_questions"], 3)
        self.assertEqual(result["comparison"]["reported_affordance_delta"], 2)
        self.assertEqual(result["comparison"]["verified_outcome_delta"], 0)
        self.assertEqual(result["verified_synergy"], "NOT_ESTABLISHED")
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertEqual(result["incremental_dollar_cost"], "NOT_MEASURED")
        self.assertNotEqual(result["comparison"]["baseline"]["artifact_sha256"],
                            result["comparison"]["bundle"]["artifact_sha256"])

    def test_individual_work_product_is_real_review_queue_not_verified_access(self):
        rid = CONFIG["candidate_ids"][0]
        out = verify_source_queue(self.rows, [rid])
        self.assertEqual(out["verification_questions_generated"], 1)
        self.assertEqual(out["verified_task_outcomes"], 0)
        self.assertEqual(out["external_calls"], 0)
        self.assertEqual(out["items"][0]["actual_access"], "NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual(out["items"][0]["eligibility"], "UNASSESSED")
        self.assertEqual(out["authorization_state"], "NOT_REQUESTED")

    def test_fake_access_and_status_do_not_elevate_work_product(self):
        rid = CONFIG["candidate_ids"][0]
        rows = [dict(x) for x in self.rows]
        for item in rows:
            if item.get("resource_id") == rid:
                item["eligibility_assessed"] = True
                item["eligibility_status"] = "ELIGIBLE"
                item["status"] = "ACTIVE"
                item["last_verified_at"] = "2026-10-14"
        out = verify_source_queue(rows, [rid])
        self.assertEqual(out["items"][0]["eligibility"], "UNASSESSED")
        self.assertEqual(out["items"][0]["source_currentness"], "NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual(out["verified_task_outcomes"], 0)

    def test_empty_evidence_cannot_complete_task(self):
        rid = CONFIG["candidate_ids"][0]
        rows = [dict(x) for x in self.rows]
        for item in rows:
            if item.get("resource_id") == rid:
                item["evidence"] = []
        with self.assertRaisesRegex(ValueError, "Missing evidence"):
            verify_source_queue(rows, [rid])

    def test_missing_ids_are_denied(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            verify_source_queue(self.rows, ["DOES_NOT_EXIST"])
        with self.assertRaisesRegex(ValueError, "unique"):
            verify_source_queue(self.rows, ["X", "X"])

    def test_no_runtime_credentials_means_live_trial_blocked(self):
        out = runtime_prerequisites({})
        self.assertEqual(out["provider_live_trial"], "BLOCKED_MISSING_RUNTIME")
        self.assertIn("AZURE_EXECUTION_RECEIPT", out["missing_configuration"])
        self.assertIn("CEREBRAS_API_KEY", out["missing_configuration"])
        self.assertEqual(out["execution_capability"], "NONE")

    def test_env_appearance_is_neither_permission_nor_provider_proof(self):
        fake = {name: "fictional" for name in
                ("AZURE_EXECUTION_RECEIPT", "CEREBRAS_API_KEY", "LANGFUSE_PUBLIC_KEY",
                 "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL")}
        out = runtime_prerequisites(fake)
        self.assertEqual(out["provider_live_trial"], "PREFLIGHT_ONLY_NOT_AUTHORIZED")
        self.assertEqual(out["azure_compute_witness"], "NOT_VERIFIED")
        self.assertEqual(out["provider_interoperability"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
