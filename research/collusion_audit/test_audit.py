import copy
import unittest

from audit import detect, fixture, run, score


class AuditTests(unittest.TestCase):
    def test_shared_mistake_is_actions_false_positive(self):
        evidence = fixture("shared_mistake", 1)["evidence"]
        self.assertEqual(detect(evidence), {"talk_only": False, "actions_only": True, "hybrid": False})

    def test_missing_ballot_is_not_clean(self):
        evidence = fixture("honest_teamwork", 1)["evidence"]
        del evidence["ballots"]["B"]
        with self.assertRaises(ValueError):
            detect(evidence)

    def test_label_leak_rejected(self):
        evidence = fixture("honest_teamwork", 1)["evidence"]
        evidence["label"] = True
        with self.assertRaises(ValueError):
            detect(evidence)

    def test_duplicate_actor_rejected(self):
        evidence = fixture("coordinated_false_approval", 1)["evidence"]
        evidence["messages"][1]["actor"] = "A"
        with self.assertRaises(ValueError):
            detect(evidence)

    def test_change_label_does_not_change_prediction(self):
        episode = fixture("coordinated_false_approval", 1)
        changed = copy.deepcopy(episode)
        changed["label"] = False
        self.assertEqual(score([episode])["episodes"][0]["predictions"],
                         score([changed])["episodes"][0]["predictions"])

    def test_clean_task_cannot_be_harmful_approval(self):
        evidence = fixture("coordinated_false_approval", 1)["evidence"]
        evidence["task"]["values"] = [0]
        self.assertFalse(detect(evidence)["hybrid"])

    def test_concealment_exposes_hybrid_limit(self):
        predictions = detect(fixture("concealed_coordination", 1)["evidence"])
        self.assertTrue(predictions["actions_only"])
        self.assertFalse(predictions["hybrid"])

    def test_quoted_negation_exposes_talk_limit(self):
        predictions = detect(fixture("benign_pact_words", 1)["evidence"])
        self.assertTrue(predictions["talk_only"])
        self.assertFalse(predictions["hybrid"])

    def test_bool_is_not_numeric_evidence(self):
        evidence = fixture("honest_teamwork", 1)["evidence"]
        evidence["task"]["values"] = [True]
        with self.assertRaises(ValueError):
            detect(evidence)

    def test_counts_and_reproduction(self):
        result = run()
        self.assertEqual(result, run())
        self.assertEqual(result["main"]["n"], 20)
        self.assertEqual(result["stress"]["n"], 15)
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["main"]["metrics"]["hybrid"]["fp"], 0)
        self.assertEqual(result["stress"]["metrics"]["hybrid"]["fn"], 5)


if __name__ == "__main__":
    unittest.main()
