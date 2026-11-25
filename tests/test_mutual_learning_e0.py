"""Offline falsifiers for the advisory Mutual Learning E0 contract."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from mutual_learning_e0 import validate

FIXTURE = ROOT / "tests" / "fixtures" / "mutual_learning_e0_pr1089_public.json"


def record():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class MutualLearningE0Tests(unittest.TestCase):
    def test_valid_source_pinned_baseline(self):
        self.assertEqual(validate(record()), [])

    def test_never_accepts_memory_or_authority_escalation(self):
        for field, value in [
            ("can_authorize", True), ("authority_effect", "Z2"),
            ("memory_write", "ENABLED"), ("project_desk_sync", "ENABLED"),
            ("intentos_sync", "ENABLED"), ("execution", "ENABLED")
        ]:
            with self.subTest(field=field):
                x=record()
                x["governance"][field]=value
                self.assertTrue(validate(x))

    def test_does_not_infer_human_learning(self):
        x=record()
        x["human_learning"]["status"]="DEMONSTRATED"
        self.assertTrue(validate(x))
        y=record()
        y["human_learning"]["teach_back"]="I approve it"
        self.assertTrue(validate(y))

    def test_unverified_machine_adaptation(self):
        x=record()
        x["machine_adaptation"][0]["outcome_verified"]=True
        self.assertTrue(validate(x))

    def test_model_self_attribution_cannot_fake_external_review(self):
        x=record()
        x["observations"][0]["review_state"]="INDEPENDENT_REVIEW_RECORDED"
        self.assertTrue(validate(x))

    def test_evidence_sha_mismatch(self):
        x=record()
        x["observations"][0]["evidence"][0]["commit_sha"]="f"*40
        self.assertTrue(validate(x))

    def test_evidence_forged_host(self):
        x=record()
        x["observations"][0]["evidence"][0]["url"]="https://evil.example/operations/pull/1089"
        self.assertTrue(validate(x))

    def test_duplicate_observations(self):
        x=record()
        x["observations"].append(copy.deepcopy(x["observations"][0]))
        self.assertTrue(validate(x))

    def test_disagreement_cannot_self_resolve(self):
        x=record()
        x["disagreements"]=[{
            "observation_ids":["O-CHATGPT001","O-UNKNOWN"],
            "status":"RESOLVED_WITH_EVIDENCE","resolution_evidence":[]
        }]
        self.assertTrue(validate(x))

    def test_extra_payload_rejected(self):
        x=record()
        x["private_transcript"]="should not be ingested"
        self.assertTrue(validate(x))

    def test_cli_success_and_failure(self):
        result=subprocess.run([sys.executable, str(ROOT/"tools"/"mutual_learning_e0.py"), str(FIXTURE)],
            text=True,capture_output=True,check=False)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        self.assertTrue(json.loads(result.stdout)["valid"])
        self.assertEqual(json.loads(result.stdout)["writes_performed"],0)


if __name__ == "__main__":
    unittest.main()
