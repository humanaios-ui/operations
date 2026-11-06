"""Adversarial offline fixtures only; no Gmail, network, or model call."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "experiments" / "risk_obs_001" / "verify_contract.py"
spec = importlib.util.spec_from_file_location("risk_obs_contract", SOURCE)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class RiskObservatoryContractTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.paths = {}
        rows = {}
        for name in checker.ARTIFACTS:
            data = ("synthetic:" + name + "\n").encode("utf-8")
            path = root / f"{name}.txt"
            path.write_bytes(data)
            self.paths[name] = path
            rows[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        self.manifest = {"schema": checker.EXPECTED_SCHEMA, "authority_effect": "NONE",
                         "source_custody": "QUALIFIED_ANALYST_PARAPHRASE",
                         "artifacts": rows, "p1_execution_authorized": False,
                         "p2_qualified": False, "public_release_authorized": False}
        self.receipt = {"phase": "P1", "leg": "CLAUDE", "peer_exposure": False,
                        "authority_effect": "NONE", "provider_run_ref": "synthetic:run:1",
                        "model_version": "synthetic-model", "output_sha256": "a" * 64,
                        "rendered_image": "NOT_PRODUCED", "image_sha256": None,
                        **{f"{name}_sha256": rows[name]["sha256"] for name in checker.ARTIFACTS}}

    def test_matching_bytes_only_not_admission(self):
        report = checker.verify_files(self.manifest, self.paths)
        self.assertEqual(report["status"], "DIGEST_MATCH_ONLY")
        self.assertFalse(report["p1_qualified"])
        self.assertFalse(report["public_release_authorized"])

    def test_changed_bytes_are_rejected(self):
        self.paths["packet"].write_text("changed", encoding="utf-8")
        self.assertIn("packet:digest_mismatch", checker.verify_files(self.manifest, self.paths)["errors"])

    def test_missing_packet_is_not_verified(self):
        self.paths["packet"].unlink()
        self.assertEqual(checker.verify_files(self.manifest, self.paths)["status"], "HOLD")

    def test_untrusted_manifest_privilege_claim_fails(self):
        self.manifest["public_release_authorized"] = True
        self.assertIn("privilege_claim", checker.verify_files(self.manifest, self.paths)["errors"])

    def test_invalid_or_extra_artifact_rejected(self):
        self.manifest["artifacts"]["private_gmail"] = {"bytes": 1, "sha256": "b" * 64}
        self.assertIn("invalid_artifact_set", checker.verify_files(self.manifest, self.paths)["errors"])

    def test_synthetic_receipt_only_candidate(self):
        self.assertEqual(checker.check_receipt(self.manifest, self.receipt)["status"], "CANDIDATE_UNVERIFIED")
        self.assertFalse(checker.check_receipt(self.manifest, self.receipt)["p1_qualified"])

    def test_peer_exposure_blocks_receipt(self):
        self.receipt["peer_exposure"] = True
        self.assertIn("peer_exposure_or_unknown", checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_forged_authority_blocks_receipt(self):
        self.receipt["authority_effect"] = "FULL"
        self.assertIn("invalid_authority", checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_missing_provider_reference_blocks_receipt(self):
        self.receipt["provider_run_ref"] = " "
        self.assertIn("missing_provider_run_ref", checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_prompt_mismatch_blocks_receipt(self):
        self.receipt["prompt_sha256"] = "f" * 64
        self.assertIn("prompt:digest_mismatch", checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_nonexistent_image_cannot_be_scored(self):
        self.receipt["rendered_image"] = "PRODUCED"
        self.assertIn("unverifiable_image", checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_missing_image_with_hash_is_rejected(self):
        self.receipt["image_sha256"] = "a" * 64
        self.assertIn("claimed_missing_image", checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_wrong_phase_and_leg_rejected(self):
        self.receipt.update(phase="P2", leg="WITNESS")
        errors = checker.check_receipt(self.manifest, self.receipt)["errors"]
        self.assertIn("wrong_phase", errors)
        self.assertIn("unknown_leg", errors)


if __name__ == "__main__":
    unittest.main()
