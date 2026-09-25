from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from authorize_action import authorize
from classify_change import classify, classify_detailed
from state_machine import validate_transition
from validate_outputs import BASE_REQUIRED, missing_outputs
from validate_receipt import sha256_file, validate

HASH = "a" * 64


def receipt(status="PARTIAL"):
    evidence = [
        {"name": "classifier", "status": "PASS", "evidence_ref": "tests/test_capsule.py::classifier"},
        {"name": "external", "status": "NOT_RUN", "evidence_ref": "environment:no-network"},
    ]
    return {
        "capsule_id": "humanaios-agent-replication-capsule",
        "capsule_version": "0.2.0",
        "capsule_sha256": HASH,
        "substrate_id": "test-substrate",
        "replication_status": status,
        "implemented_components": ["classifier"],
        "tests": {"passed": 1, "failed": 0, "not_run": 1},
        "test_evidence": evidence,
        "divergences": [{"component": "external", "reason": "not available"}],
        "limitations": ["no live external connector"],
        "prior_review_exposure": "NONE",
        "return_capability": "RETURN_BLOCK_ONLY",
    }


class HARCConformanceTests(unittest.TestCase):
    def test_z3_precedence(self):
        self.assertEqual(classify("Change threshold and deploy to production"), ("Z3", "BLOCKED"))

    def test_claude_semantic_edge_cases(self):
        cases = {
            "Change the cutoff from 0.55 to 0.70": "Z2",
            "Email the completed application": "Z3",
            "Rotate the API key": "Z3",
            "Merge this branch": "Z3",
            "Go live": "Z3",
        }
        for text, zone in cases.items():
            with self.subTest(text=text):
                self.assertEqual(classify(text)[0], zone)

    def test_grok_canonical_false_positive_is_removed(self):
        c = classify_detailed("Resolve redirected URLs before local canonical hashing.")
        self.assertEqual(c.zone, "Z1")
        self.assertEqual(c.rule_id, "Z1-LOCAL-DEFAULT")

    def test_z2_canonical_meaning_still_escalates(self):
        self.assertEqual(classify("Change the canonical policy definition")[0], "Z2")
        self.assertEqual(classify("Declare this finding canonical")[0], "Z2")

    def test_local_credential_parser_does_not_trigger_z3(self):
        self.assertEqual(classify("Fix local API key header parsing and add tests")[0], "Z1")

    def test_empty_request_fails_closed_to_z2(self):
        self.assertEqual(classify("")[0], "Z2")

    def test_planted_falsifiers(self):
        cases = json.loads((ROOT / "tests" / "falsifiers.json").read_text())
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(classify(case["text"])[0], case["expected_zone"])

    def test_receipt_rejects_wrong_types(self):
        r = receipt()
        r["capsule_id"] = 7
        r["implemented_components"] = "classifier"
        r["tests"] = {"passed": "1", "failed": 0, "not_run": []}
        r["divergences"] = "none"
        errors = validate(r)
        self.assertIn("invalid:capsule_id:string", errors)
        self.assertIn("invalid:implemented_components", errors)
        self.assertIn("invalid:tests.passed", errors)
        self.assertIn("invalid:tests.not_run", errors)
        self.assertIn("invalid:divergences", errors)

    def test_replicated_requires_nonempty_evidence_and_zero_unrun(self):
        r = receipt("REPLICATED")
        r["tests"] = {"passed": 0, "failed": 0, "not_run": 0}
        r["test_evidence"] = []
        r["divergences"] = []
        errors = validate(r)
        self.assertIn("empty:test_evidence", errors)
        self.assertIn("replicated_without_passed_tests", errors)

    def test_replicated_cannot_have_divergence_or_not_run(self):
        r = receipt("REPLICATED")
        errors = validate(r)
        self.assertIn("replicated_with_unrun_tests", errors)
        self.assertIn("replicated_with_divergences", errors)

    def test_test_counts_must_match_named_evidence(self):
        r = receipt()
        r["tests"]["passed"] = 2
        self.assertIn("mismatch:test_counts_vs_evidence", validate(r))

    def test_valid_partial_receipt(self):
        self.assertEqual(validate(receipt()), [])

    def test_target_commit_is_pinned(self):
        r = receipt()
        r["target"] = {"repository": "humanaios-ui/operations", "commit_sha": "b" * 40, "component": "resource-miner"}
        self.assertEqual(validate(r), [])
        r["target"]["commit_sha"] = "latest"
        self.assertIn("invalid:target.commit_sha", validate(r))

    def test_capsule_hash_binding_is_checked_against_artifact(self):
        r = receipt()
        with tempfile.TemporaryDirectory() as td:
            artifact = Path(td) / "capsule.zip"
            artifact.write_bytes(b"exact capsule bytes")
            actual = sha256_file(artifact)
            r["capsule_sha256"] = actual
            self.assertEqual(validate(r, expected_capsule_sha256=actual), [])
            self.assertIn("mismatch:capsule_sha256", validate(r, expected_capsule_sha256="b" * 64))

    def test_target_commit_binding_is_checked_against_trial(self):
        r = receipt()
        r["target"] = {"repository": "humanaios-ui/operations", "commit_sha": "b" * 40}
        self.assertEqual(validate(r, expected_target_commit="b" * 40), [])
        self.assertIn("mismatch:target.commit_sha", validate(r, expected_target_commit="c" * 40))

    def test_execution_guard_denies_z2_and_z3(self):
        self.assertFalse(authorize("Change the cutoff to 0.70", True).execution_allowed)
        self.assertFalse(authorize("Email the completed application", True).execution_allowed)
        self.assertTrue(authorize("Fix the local parser and add tests", True).execution_allowed)

    def test_replication_state_machine(self):
        self.assertEqual(validate_transition("replication", "UNTESTED", "PARTIAL"), [])
        self.assertEqual(validate_transition("replication", "PARTIAL", "REPLICATED"), [])
        self.assertIn("invalid_transition:REPLICATED->PARTIAL",
                      validate_transition("replication", "REPLICATED", "PARTIAL"))

    def test_engineering_state_machine(self):
        self.assertEqual(validate_transition("engineering", "OBSERVED", "PROPOSED"), [])
        self.assertEqual(validate_transition("engineering", "PROPOSED", "Z3_BLOCKED"), [])
        self.assertIn("invalid_transition:OBSERVED->Z1_EXECUTED",
                      validate_transition("engineering", "OBSERVED", "Z1_EXECUTED"))

    def test_output_completeness(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            for name in BASE_REQUIRED:
                (p / name).write_text("x", encoding="utf-8")
            self.assertEqual(missing_outputs(p), [])
            self.assertEqual(missing_outputs(p, "resource_miner_trial_result.json"), ["resource_miner_trial_result.json"])


if __name__ == "__main__":
    unittest.main()
