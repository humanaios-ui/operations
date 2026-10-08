"""Synthetic, network-free URA contract tests — issue #755."""
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).resolve().parents[2] / "humanaios-funding-pipeline" / "resource-miner" / "resource_miner" / "universal_adapter.py"
spec = importlib.util.spec_from_file_location("universal_adapter", MODULE)
ura = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ura
spec.loader.exec_module(ura)

DIGEST = "a" * 64


class TestUniversalResourceAdapter(unittest.TestCase):
    def setUp(self):
        self.registry = ura.synthetic_reference_registry()

    def test_three_providers_share_resource_contract(self):
        data = [
            ("GITHUB_PUBLIC", "OPEN_SOURCE_RESOURCE", "https://github.com/humanaios-ui/operations"),
            ("OUTLIER_PUBLIC", "HUMAN_NETWORK_REWARD", "https://outlier.ai/faq"),
            ("TRIAL_SYNTHETIC", "AI_EVALUATION_ENVIRONMENT", "https://example.org/synthetic-trial"),
        ]
        outputs = []
        for provider, category, url in data:
            outputs.append(self.registry.normalize(ura.Observation(
                provider, "synthetic-1", "Synthetic opportunity", url, category,
                "2026-10-08T00:00:00Z", DIGEST)))
        self.assertEqual(len({x["resource_id"] for x in outputs}), 3)
        for x in outputs:
            self.assertEqual(x["authorization"], "NOT_GRANTED")
            self.assertEqual(x["authority_effect"], "NONE")
            self.assertEqual(x["execution"], "NOT_AVAILABLE")
            self.assertEqual(x["eligibility_status"], "UNASSESSED")
            self.assertEqual(x["status"], "UNKNOWN")
            self.assertEqual(len(x["evidence"]), 1)

    def test_manifest_cannot_self_grant(self):
        for overrides in (
            {"authority_effect": "AUTHORIZE"},
            {"adapter_mode": "EXECUTE"},
            {"source_class": "AUTHENTICATED"},
        ):
            args = dict(provider_id="BAD", version="1", hosts=("example.org",),
                        categories=("X",), public_paths=("/a",))
            args.update(overrides)
            with self.assertRaises(ura.AdapterDenied):
                self.registry.register(ura.ProviderManifest(**args))

    def test_provenance_and_scope_fail_closed(self):
        baseline = dict(provider_id="OUTLIER_PUBLIC", external_id="1", title="Synthetic",
                        source_url="https://outlier.ai/faq",
                        category="HUMAN_NETWORK_REWARD", observed_at="2026-10-08",
                        evidence_digest=DIGEST)
        for changes in (
            {"source_url": "https://app.outlier.ai/referrals"},
            {"source_url": "https://outlier.ai.evil.test/faq"},
            {"source_url": "https://outlier.ai/faq?token=secret"},
            {"source_url": "http://outlier.ai/faq"},
            {"source_class": "PRIVATE_DASHBOARD"},
            {"category": "PAID_TASK_DATA"},
            {"evidence_digest": "missing"},
            {"provider_id": "UNKNOWN"},
        ):
            args = dict(baseline)
            args.update(changes)
            with self.subTest(changes=changes):
                with self.assertRaises(ura.AdapterDenied):
                    self.registry.normalize(ura.Observation(**args))

    def test_registry_never_executes_even_with_receipt(self):
        for provider in self.registry.providers():
            for receipt in (None, True, {"signed": True, "provider_id": provider}):
                with self.assertRaises(ura.AdapterDenied):
                    self.registry.request_action(provider, "EXECUTE", receipt)

    def test_duplicate_registration_denied(self):
        with self.assertRaises(ura.AdapterDenied):
            self.registry.register(ura.ProviderManifest(
                "OUTLIER_PUBLIC", "0.1", ("outlier.ai",), ("X",), ("/faq",)))


if __name__ == "__main__":
    unittest.main()
