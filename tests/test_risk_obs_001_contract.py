"""Adversarial offline fixtures only; no Gmail, network, or model call."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
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
        # Baseline clean receipt: explicit peer_exposure=False + isolation_claim=CLEAN
        self.receipt = {"phase": "P1", "leg": "CLAUDE", "peer_exposure": False,
                        "isolation_claim": "CLEAN",
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

    def test_missing_privilege_key_fails(self):
        del self.manifest["p2_qualified"]
        self.assertIn("missing_p2_qualified", checker.verify_files(self.manifest, self.paths)["errors"])

    def test_invalid_or_extra_artifact_rejected(self):
        self.manifest["artifacts"]["private_gmail"] = {"bytes": 1, "sha256": "b" * 64}
        self.assertIn("invalid_artifact_set", checker.verify_files(self.manifest, self.paths)["errors"])

    def test_synthetic_receipt_only_candidate(self):
        self.assertEqual(checker.check_receipt(self.manifest, self.receipt)["status"], "CANDIDATE_UNVERIFIED")
        self.assertFalse(checker.check_receipt(self.manifest, self.receipt)["p1_qualified"])

    def test_peer_exposure_true_blocks_clean_receipt(self):
        self.receipt["peer_exposure"] = True
        # isolation still CLEAN => inconsistency
        errors = checker.check_receipt(self.manifest, self.receipt)["errors"]
        self.assertIn("clean_requires_no_peer_exposure", errors)

    def test_missing_peer_exposure_rejected(self):
        del self.receipt["peer_exposure"]
        self.assertIn("missing_peer_exposure", checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_peer_exposure_not_bool_rejected(self):
        self.receipt["peer_exposure"] = "false"
        self.assertIn("peer_exposure_not_bool", checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_qualified_exposure_requires_peer_true(self):
        self.receipt["isolation_claim"] = "QUALIFIED_WITH_EXPOSURE_LIMIT"
        self.receipt["peer_exposure"] = False
        self.assertIn("exposed_isolation_requires_peer_exposure_true",
                      checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_honest_qualified_exposure_is_candidate(self):
        self.receipt["isolation_claim"] = "QUALIFIED_WITH_EXPOSURE_LIMIT"
        self.receipt["peer_exposure"] = True
        report = checker.check_receipt(self.manifest, self.receipt)
        self.assertEqual(report["status"], "CANDIDATE_UNVERIFIED")
        self.assertFalse(report["p1_qualified"])

    def test_contaminated_requires_peer_true(self):
        self.receipt["isolation_claim"] = "CONTAMINATED"
        self.receipt["peer_exposure"] = False
        self.assertIn("exposed_isolation_requires_peer_exposure_true",
                      checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_invalid_isolation_claim_rejected(self):
        self.receipt["isolation_claim"] = "MOSTLY_CLEAN"
        self.assertIn("invalid_or_missing_isolation_claim",
                      checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_missing_isolation_claim_rejected(self):
        del self.receipt["isolation_claim"]
        self.assertIn("invalid_or_missing_isolation_claim",
                      checker.check_receipt(self.manifest, self.receipt)["errors"])

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

    # --- review items 1, 2, 3 and 6 (PR #1150 review) -------------------------------
    def _cli(self, manifest_text, receipt_texts=()):
        """Run main() on files in a temp dir; return (exit code, parsed stdout JSON)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "manifest.json").write_text(manifest_text, encoding="utf-8")
            argv = ["--manifest", str(root / "manifest.json")]
            argv += [x for name in checker.ARTIFACTS for x in (f"--{name}", str(self.paths[name]))]
            for index, text in enumerate(receipt_texts):
                (root / f"r{index}.json").write_text(text, encoding="utf-8")
                argv += ["--receipt", str(root / f"r{index}.json")]
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = checker.main(argv)
            return code, json.loads(buffer.getvalue())

    def _receipt_for(self, leg, run_ref, output_char):
        receipt = dict(self.receipt)
        receipt.update(leg=leg, provider_run_ref=run_ref, output_sha256=output_char * 64)
        return receipt

    # item 6: the digest comparison itself, with the length held equal
    def test_flipped_byte_with_same_length_is_rejected(self):
        data = bytearray(self.paths["packet"].read_bytes())
        data[0] ^= 0x01
        self.paths["packet"].write_bytes(bytes(data))
        self.assertEqual(len(data), self.manifest["artifacts"]["packet"]["bytes"])
        self.assertIn("packet:digest_mismatch", checker.verify_files(self.manifest, self.paths)["errors"])

    def test_prompt_trailing_lf_replaced_by_cr_same_length_is_rejected(self):
        data = self.paths["prompt"].read_bytes()
        self.assertTrue(data.endswith(b"\n"))
        self.paths["prompt"].write_bytes(data[:-1] + b"\r")
        self.assertEqual(len(data), self.manifest["artifacts"]["prompt"]["bytes"])
        self.assertIn("prompt:digest_mismatch", checker.verify_files(self.manifest, self.paths)["errors"])

    # item 1: malformed manifest must give HOLD, never an exception
    def test_string_artifact_row_with_receipt_holds_without_crashing(self):
        self.manifest["artifacts"]["packet"] = "x"
        result = checker.check_receipt(self.manifest, self.receipt)
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("packet:digest_mismatch", result["errors"])

    def test_non_object_manifest_with_receipt_holds_without_crashing(self):
        for bad in ("x", None, [], 7):
            with self.subTest(manifest=bad):
                self.assertEqual(checker.check_receipt(bad, self.receipt)["status"], "HOLD")

    def test_absent_manifest_digest_never_matches_absent_receipt_digest(self):
        del self.manifest["artifacts"]["prompt"]["sha256"]
        del self.receipt["prompt_sha256"]
        self.assertIn("prompt:digest_mismatch", checker.check_receipt(self.manifest, self.receipt)["errors"])

    def test_cli_malformed_manifest_with_receipt_returns_hold_json(self):
        self.manifest["artifacts"]["packet"] = "x"
        code, out = self._cli(json.dumps(self.manifest), [json.dumps(self.receipt)])
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "HOLD")
        self.assertEqual(out["receipt"]["status"], "HOLD")

    # item 2: duplicate keys and non-finite numbers must not be parsed quietly
    def test_cli_duplicate_manifest_key_is_hold(self):
        text = json.dumps(self.manifest)[:-1] + ', "authority_effect": "FULL"}'
        code, out = self._cli(text)
        self.assertEqual(code, 2)
        self.assertEqual(out["status"], "HOLD")
        self.assertIn("duplicate JSON key", out["errors"][0])

    def test_cli_duplicate_digest_key_in_artifact_row_is_hold(self):
        good = self.manifest["artifacts"]["packet"]["sha256"]
        text = json.dumps(self.manifest).replace(f'"sha256": "{good}"', f'"sha256": "{"0" * 64}", "sha256": "{good}"', 1)
        self.assertIn("0" * 64, text)
        code, out = self._cli(text)
        self.assertEqual(code, 2)
        self.assertIn("duplicate JSON key", out["errors"][0])

    def test_cli_nan_bytes_is_hold(self):
        size = self.manifest["artifacts"]["packet"]["bytes"]
        text = json.dumps(self.manifest).replace(f'"bytes": {size}', '"bytes": NaN', 1)
        self.assertIn("NaN", text)
        code, out = self._cli(text)
        self.assertEqual(code, 2)
        self.assertIn("nonfinite JSON number", out["errors"][0])

    def test_cli_duplicate_key_in_receipt_is_hold(self):
        text = json.dumps(self.receipt)[:-1] + ', "peer_exposure": true}'
        code, out = self._cli(json.dumps(self.manifest), [text])
        self.assertEqual(code, 2)
        self.assertIn("duplicate JSON key", out["errors"][0])

    # item 3: receipts compared with one another
    def test_distinct_receipt_set_is_candidate_only(self):
        receipts = [self._receipt_for("CHATGPT", "run-a", "a"), self._receipt_for("CLAUDE", "run-b", "b"),
                    self._receipt_for("GROK", "run-c", "c")]
        result = checker.check_receipt_set(self.manifest, receipts)
        self.assertEqual(result["status"], "CANDIDATE_UNVERIFIED")
        self.assertEqual(result["errors"], [])
        self.assertFalse(result["p1_qualified"])

    def test_shared_provider_run_ref_across_legs_is_rejected(self):
        receipts = [self._receipt_for("CLAUDE", "run-1", "a"), self._receipt_for("GROK", "run-1", "b")]
        result = checker.check_receipt_set(self.manifest, receipts)
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("shared_provider_run_ref", result["errors"])

    def test_run_ref_reused_with_case_and_space_changes_is_rejected(self):
        receipts = [self._receipt_for("CLAUDE", "Run-1", "a"), self._receipt_for("GROK", "  run-1 ", "b")]
        self.assertIn("shared_provider_run_ref", checker.check_receipt_set(self.manifest, receipts)["errors"])

    def test_identical_output_digest_across_legs_is_rejected(self):
        receipts = [self._receipt_for("CLAUDE", "run-1", "a"), self._receipt_for("GROK", "run-2", "a")]
        self.assertIn("shared_output_sha256", checker.check_receipt_set(self.manifest, receipts)["errors"])

    def test_same_leg_twice_is_rejected(self):
        receipts = [self._receipt_for("CLAUDE", "run-1", "a"), self._receipt_for("CLAUDE", "run-2", "b")]
        self.assertIn("duplicate_leg:CLAUDE", checker.check_receipt_set(self.manifest, receipts)["errors"])

    def test_one_bad_receipt_in_a_set_holds_the_set(self):
        bad = self._receipt_for("GROK", "run-2", "b")
        bad["peer_exposure"] = True
        result = checker.check_receipt_set(self.manifest, [self._receipt_for("CLAUDE", "run-1", "a"), bad])
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("receipt[1]:peer_exposure_or_unknown", result["errors"])

    def test_empty_or_non_list_receipt_set_holds(self):
        for bad in ([], None, "x"):
            with self.subTest(receipts=bad):
                self.assertEqual(checker.check_receipt_set(self.manifest, bad)["status"], "HOLD")

    def test_cli_two_receipts_sharing_a_run_ref_returns_hold(self):
        texts = [json.dumps(self._receipt_for("CLAUDE", "run-1", "a")), json.dumps(self._receipt_for("GROK", "run-1", "b"))]
        code, out = self._cli(json.dumps(self.manifest), texts)
        self.assertEqual(code, 1)
        self.assertIn("shared_provider_run_ref", out["receipt_set"]["errors"])


if __name__ == "__main__":
    unittest.main()
