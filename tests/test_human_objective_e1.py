"""E1 synthetic integration contract regressions; no provider or market calls."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("e1", ROOT / "experiments/human_objective_e1.py")
e1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e1)
FIXTURE = json.loads((ROOT / "experiments/e1_ura_fixture.json").read_text())


class E1ContractTests(unittest.TestCase):
    def evaluate(self, records=None, objective="Find training and certification resources useful for HumanAIOS"):
        return e1.recommend(objective, copy.deepcopy(FIXTURE["records"] if records is None else records))

    def test_first_human_objective(self):
        result = self.evaluate()
        self.assertEqual(result["intent"]["category"], "TRAINING_AND_CERTIFICATION")
        self.assertEqual(result["intent"]["beneficiary"], "HumanAIOS")
        self.assertEqual(result["state"], "SYNTHETIC_REVIEW_CANDIDATE")
        self.assertEqual(result["candidate"]["provenance"], "SUPPLIED_UNVERIFIED_SYNTHETIC")
        self.assertEqual(result["eligibility"], "UNASSESSED")

    def test_no_match_abstains(self):
        self.assertEqual(self.evaluate(objective="Find agricultural irrigation pumps")["state"], "ABSTAIN_INSUFFICIENT_MATCH")

    def test_authority_laundering_denied(self):
        records = copy.deepcopy(FIXTURE["records"])
        records[0]["authorization"] = "GRANTED"
        result = self.evaluate(records)
        self.assertEqual(result["state"], "ABSTAIN_INSUFFICIENT_MATCH")
        self.assertEqual(result["rejected_count"], 1)

    def test_execution_laundering_denied(self):
        records = copy.deepcopy(FIXTURE["records"])
        records[0]["execution"] = "ALLOWED"
        self.assertEqual(self.evaluate(records)["rejected_count"], 1)

    def test_provenance_mismatch_denied(self):
        records = copy.deepcopy(FIXTURE["records"])
        records[0]["evidence"][0]["url"] = "https://malicious.example"
        self.assertEqual(self.evaluate(records)["rejected_count"], 1)

    def test_missing_digest_denied(self):
        records = copy.deepcopy(FIXTURE["records"])
        records[0]["evidence"][0]["claim"] = "verified"
        self.assertEqual(self.evaluate(records)["rejected_count"], 1)

    def test_private_url_denied(self):
        records = copy.deepcopy(FIXTURE["records"])
        records[0]["source_url"] = records[0]["canonical_url"] = "http://localhost/private"
        records[0]["evidence"][0]["url"] = "http://localhost/private"
        self.assertEqual(self.evaluate(records)["rejected_count"], 1)

    def test_non_synthetic_origin_denied(self):
        with self.assertRaises(e1.EvidenceDenied):
            e1.recommend("Find training", FIXTURE["records"], fixture_origin="LIVE")

    def test_hmbm_dhp_isolation(self):
        result = self.evaluate()
        self.assertEqual(result["hmbm_effect"], "NONE")
        self.assertEqual(result["dhp_state_effect"], "NONE")
        self.assertEqual(result["authority"], "NONE")
        self.assertEqual(result["execution"], "DISABLED")

    def test_deterministic_receipt(self):
        self.assertEqual(self.evaluate()["receipt_sha256"], self.evaluate()["receipt_sha256"])


if __name__ == "__main__":
    unittest.main()
