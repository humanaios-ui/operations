"""EBEE-001 Independent Execution Witness verification tests.

Tests cover:
- Legitimate execution reproducibility
- Fabrication resistance (import-then-print detection)
- Source modification evidence invalidation
- Admission state elevation constraints
"""
import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import independent_execution_witness_v0_1 as iew


class IndependentExecutionWitnessTests(unittest.TestCase):
    """Tests for EBEE-001 Independent Execution Witness."""

    def test_criterion_1_reproducible_execution(self):
        """Legitimate execution produces reproducible results."""
        test_input = {
            "molt_id": "molt_test_001",
            "constant_name": "test_constant",
            "proposed_value": 0.5,
            "priority_score": 75,
            "prediction_window_hours": 24,
            "falsifier": "test_condition",
            "evidence_url": "https://example.com",
        }

        evidence_1 = iew.perform_witness_verification(
            iew.REFERENCE_FIXTURE, test_input, witness_id="test_witness_1"
        )
        evidence_2 = iew.perform_witness_verification(
            iew.REFERENCE_FIXTURE, test_input, witness_id="test_witness_2"
        )

        # Source must be identical
        self.assertEqual(
            evidence_1.source_sha256, evidence_2.source_sha256,
            "Source hash must be identical across executions"
        )

        # Both must succeed
        self.assertEqual(evidence_1.return_code, 0, "First execution must succeed")
        self.assertEqual(evidence_2.return_code, 0, "Second execution must succeed")

        # Output structure must match
        try:
            out1 = json.loads(evidence_1.stdout)
            out2 = json.loads(evidence_2.stdout)
            self.assertEqual(
                set(out1.keys()), set(out2.keys()),
                "Output structure must be identical"
            )
        except json.JSONDecodeError:
            self.fail("Output must be valid JSON")

    def test_criterion_2_fabrication_detection(self):
        """Import-then-print fabrication attempt fails verification."""
        test_input = {
            "molt_id": "molt_test_002",
            "constant_name": "test_constant_2",
            "proposed_value": 0.6,
            "priority_score": 50,
            "prediction_window_hours": 0,
            "falsifier": "test_condition",
        }

        is_fabricated, reason = iew.fabrication_test(iew.REFERENCE_FIXTURE, test_input)

        self.assertTrue(
            is_fabricated,
            f"Fabrication must be detected. Reason: {reason}"
        )
        self.assertIn(
            "Fabricated", reason,
            "Detection reason must identify fabrication"
        )

    def test_criterion_3_source_modification_invalidates(self):
        """Source modification invalidates corresponding execution evidence."""
        test_input = {
            "molt_id": "molt_test_003",
            "constant_name": "test_constant_3",
            "proposed_value": 0.7,
            "priority_score": 60,
            "prediction_window_hours": 12,
            "falsifier": "test_condition",
        }

        # Get original evidence
        evidence_original = iew.perform_witness_verification(
            iew.REFERENCE_FIXTURE, test_input, witness_id="test_witness_orig"
        )

        # Create modified version
        import tempfile
        source, _ = iew.read_source(iew.REFERENCE_FIXTURE)
        modified_source = source.replace(
            'tier = MoltTier.FINDING',
            'tier = MoltTier.UNKNOWN  # MODIFIED'
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(modified_source)
            modified_path = f.name

        try:
            evidence_modified = iew.perform_witness_verification(
                modified_path, test_input, witness_id="test_witness_mod"
            )

            # Source hashes must differ
            self.assertNotEqual(
                evidence_original.source_sha256,
                evidence_modified.source_sha256,
                "Modified source must have different hash"
            )
        finally:
            Path(modified_path).unlink()

    def test_criterion_4_admission_elevation_prevented(self):
        """Failed witness verification cannot elevate admission state."""
        test_input_invalid = {
            "molt_id": "molt_test_004",
            "constant_name": "test_constant_4",
            "proposed_value": 0.8,
            # Missing falsifier - should fail
            "priority_score": 70,
            "prediction_window_hours": 48,
        }

        evidence_invalid = iew.perform_witness_verification(
            iew.REFERENCE_FIXTURE, test_input_invalid, witness_id="test_witness_inv"
        )

        # Failed witness cannot grant admission
        cannot_admit = (
            evidence_invalid.return_code != 0
            or bool(evidence_invalid.discrepancies)
            or evidence_invalid.is_fabricated
        )

        self.assertTrue(
            cannot_admit,
            "Failed witness must not grant admission eligibility"
        )

    def test_acceptance_criteria_all_pass(self):
        """All four EBEE-001 acceptance criteria pass."""
        results = iew.run_acceptance_criteria_tests()

        self.assertIn("criterion_1", results)
        self.assertIn("criterion_2", results)
        self.assertIn("criterion_3", results)
        self.assertIn("criterion_4", results)

        for criterion_name, result in results.items():
            self.assertTrue(
                result.get("passed", False),
                f"{criterion_name} must pass. Result: {result}"
            )

    def test_execution_evidence_records_discrepancies(self):
        """Execution evidence records discrepancies between actual and expected."""
        test_input = {
            "molt_id": "molt_test_discrep",
            "constant_name": "discrep_const",
            "proposed_value": 0.9,
            "priority_score": 80,
            "prediction_window_hours": 6,
            "falsifier": "discrep_test",
        }

        expected_output = {
            "molt_id": "WRONG_ID",
            "tier": "WRONG_TIER",
        }

        evidence = iew.perform_witness_verification(
            iew.REFERENCE_FIXTURE, test_input, expected_output=expected_output
        )

        # Should record discrepancies
        self.assertTrue(
            len(evidence.discrepancies) > 0,
            "Discrepancies must be recorded for mismatched expected output"
        )

    def test_reference_fixture_exists(self):
        """Reference fixture (molt_tier_calculator) exists and is readable."""
        source, sha256 = iew.read_source(iew.REFERENCE_FIXTURE)

        self.assertIsNotNone(source, "Reference fixture must exist")
        self.assertGreater(len(source), 0, "Reference fixture must not be empty")
        self.assertEqual(
            len(sha256), 64,
            "SHA256 hash must be 64 hex characters"
        )


if __name__ == "__main__":
    unittest.main()
