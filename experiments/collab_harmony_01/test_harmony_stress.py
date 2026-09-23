import json
import unittest
from pathlib import Path

from experiments.collab_harmony_01.harmony_stress import evaluate, from_dict


HERE = Path(__file__).resolve().parent


class HarmonyStressVectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = json.loads((HERE / "test_vectors.json").read_text())

    def test_all_preregistered_vectors(self):
        for vector in self.vectors:
            with self.subTest(vector=vector["id"]):
                result = evaluate(from_dict(vector["state"]))
                self.assertEqual(vector["expected_verdict"], result["verdict"])

    def test_perfect_scores_cannot_override_gate_failure(self):
        state = from_dict({
            "contributions": [],
            "dissent_preserved": False,
            "mutual_understanding": 1.0,
            "complementarity": 1.0,
            "evidence_quality": 1.0,
            "coordination": 1.0,
            "collective_problem_solving": 1.0
        })
        result = evaluate(state)
        self.assertEqual("INVALID_HARMONY", result["verdict"])
        self.assertEqual(0.0, result["score"])

    def test_distinct_participants_do_not_prove_independence(self):
        state = from_dict({
            "contributions": [
                {"participant_id": "a", "participant_type": "AI"},
                {"participant_id": "b", "participant_type": "AI"}
            ]
        })
        result = evaluate(state)
        self.assertFalse(result["independence"]["independence_proven"])


if __name__ == "__main__":
    unittest.main()
