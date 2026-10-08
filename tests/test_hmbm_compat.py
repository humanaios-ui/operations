"""Synthetic-only HMBM/URA compatibility tests; no market/provider I/O."""
import importlib.util
from pathlib import Path
import sys
import unittest

PATH = Path(__file__).resolve().parents[1] / "humanaios-funding-pipeline/resource-miner/resource_miner/hmbm_compat.py"
spec = importlib.util.spec_from_file_location("hmbm_compat", PATH)
compat = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = compat
spec.loader.exec_module(compat)

ASSET = "CG-20260930-R001-BTC"
URL = "https://example.org/synthetic-trial"
HASH = "a" * 64
CUTOFF = "2026-09-30T07:09:08-05:00"


class TestHMBMURA(unittest.TestCase):
    def setUp(self):
        self.resource = {
            "source_name": "TRIAL_SYNTHETIC", "source_url": URL,
            "authorization": "NOT_GRANTED", "authority_effect": "NONE",
            "execution": "NOT_AVAILABLE",
            "evidence": [{"url": URL, "claim": "digest:sha256:" + HASH}],
        }
        self.observation = {
            "provider_id": "TRIAL_SYNTHETIC", "asset_id": ASSET,
            "source_classification": "PUBLIC_METADATA",
            "observed_at": "2026-09-30T06:30:00-05:00",
            "available_at": "2026-09-30T06:45:00-05:00",
            "collected_at": "2026-09-30T08:00:00-05:00",
            "source_reference": URL, "content_hash": HASH,
            "coverage_state": "OBSERVED",
            "availability_verification": "INDEPENDENTLY_VERIFIED",
            "authorization_effect": "NONE",
        }

    def run_projection(self, updates=None, resource_updates=None):
        obs = dict(self.observation)
        obs.update(updates or {})
        resource = dict(self.resource)
        resource.update(resource_updates or {})
        return compat.project(
            resource, obs, cutoff=CUTOFF,
            frozen_assets=frozenset([ASSET]),
            registered_providers=frozenset(["TRIAL_SYNTHETIC"]),
        )

    def test_cutoff_eligible_not_prediction(self):
        result = self.run_projection()
        self.assertEqual(result["evaluation_state"], "ELIGIBLE_FOR_HMBM_EVALUATION")
        self.assertEqual(result["prediction_authority"], "NONE")
        self.assertEqual(result["dhp_state_effect"], "NONE")

    def test_unverified_availability_abstains(self):
        self.assertEqual(self.run_projection({"availability_verification": "CLAIM_ONLY"})["evaluation_state"], "MISSING_DATA")

    def test_late_availability_abstains(self):
        self.assertEqual(self.run_projection({"available_at": "2026-09-30T08:00:00-05:00"})["evaluation_state"], "MISSING_DATA")

    def test_asset_rejected(self):
        with self.assertRaises(compat.CompatibilityDenied):
            self.run_projection({"asset_id": "BTC"})

    def test_provider_rejected(self):
        with self.assertRaises(compat.CompatibilityDenied):
            self.run_projection({"provider_id": "OUTLIER_PUBLIC"})

    def test_private_source_rejected(self):
        with self.assertRaises(compat.CompatibilityDenied):
            self.run_projection({"source_classification": "PRIVATE_DASHBOARD"})

    def test_self_authorization_rejected(self):
        with self.assertRaises(compat.CompatibilityDenied):
            self.run_projection({"authorization_effect": "AUTHORIZE"})

    def test_execution_claim_rejected(self):
        with self.assertRaises(compat.CompatibilityDenied):
            self.run_projection({"claims_execution": True})

    def test_resource_authority_rejected(self):
        with self.assertRaises(compat.CompatibilityDenied):
            self.run_projection(resource_updates={"authorization": "GRANTED"})

    def test_provenance_mismatch_rejected(self):
        with self.assertRaises(compat.CompatibilityDenied):
            self.run_projection({"content_hash": "b" * 64})

    def test_source_mismatch_rejected(self):
        with self.assertRaises(compat.CompatibilityDenied):
            self.run_projection({"source_reference": "https://evil.example"})

    def test_nonobserved_flags_preserved(self):
        for flag in ("N/O", "STALE", "CONTRADICTED", "UNKNOWN_COVERAGE"):
            with self.subTest(flag=flag):
                result = self.run_projection({"coverage_state": flag})
                self.assertEqual(result["coverage_state"], flag)
                self.assertEqual(result["evaluation_state"], "MISSING_DATA")

    def test_inverted_time_denied(self):
        with self.assertRaises(compat.CompatibilityDenied):
            self.run_projection({"available_at": "2026-09-30T06:00:00-05:00"})

    def test_timezone_required(self):
        with self.assertRaises(compat.CompatibilityDenied):
            self.run_projection({"collected_at": "2026-09-30T08:00:00"})


if __name__ == "__main__":
    unittest.main()
