"""Offline, synthetic E0 boundaries. Run: python3 -m unittest discover -s tests -p 'test_human_objective_e0.py' -v"""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("human_objective_e0", ROOT / "experiments" / "human_objective_e0.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
FIXTURE = json.loads((ROOT / "experiments" / "e0_fixture.json").read_text(encoding="utf-8"))


class HumanObjectiveE0Tests(unittest.TestCase):
    def test_objective_recommendation_is_synthetic(self):
        result = module.evaluate("Find training certification", FIXTURE)
        self.assertEqual(result["status"], "SYNTHETIC_CANDIDATE_ONLY")
        self.assertEqual(result["candidate"]["id"], "SYN-TRAIN-01")
        self.assertEqual(result["execution"], "DISABLED")
        self.assertEqual(result["authority"], "NONE")

    def test_unknown_objective_abstains(self):
        result = module.evaluate("Need agricultural irrigation pumps", FIXTURE)
        self.assertEqual(result["status"], "ABSTAIN_NO_SUPPORTED_MATCH")
        self.assertIsNone(result["candidate"])

    def test_fake_authority_is_rejected(self):
        modified = json.loads(json.dumps(FIXTURE))
        modified["candidates"].append({"id": "EVIL", "name": "Approved!", "tags": ["training"], "source": "SYNTHETIC_FIXTURE", "evidence": "SYNTHETIC_EXAMPLE_NOT_VERIFIED", "can_authorize": True})
        result = module.evaluate("Find training", modified)
        self.assertEqual(result["rejected_candidate_count"], 1)
        self.assertEqual(result["authority"], "NONE")

    def test_unsupported_provenance_rejected(self):
        modified = json.loads(json.dumps(FIXTURE))
        modified["candidates"][0]["source"] = "LIVE_PROVIDER_VERIFIED"
        result = module.evaluate("Find certification", modified)
        self.assertEqual(result["status"], "ABSTAIN_NO_SUPPORTED_MATCH")
        self.assertEqual(result["rejected_candidate_count"], 1)

    def test_live_fixture_denied(self):
        modified = json.loads(json.dumps(FIXTURE))
        modified["fixture_type"] = "LIVE"
        with self.assertRaises(ValueError):
            module.evaluate("Find training", modified)

    def test_receipt_is_deterministic(self):
        a = module.evaluate("Find startup grants", FIXTURE)
        b = module.evaluate("Find startup grants", FIXTURE)
        self.assertEqual(a["receipt_sha256"], b["receipt_sha256"])
        self.assertEqual(len(a["receipt_sha256"]), 64)

    def test_empty_objective_denied(self):
        with self.assertRaises(ValueError):
            module.evaluate("   ", FIXTURE)


if __name__ == "__main__":
    unittest.main()
