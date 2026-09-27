import unittest

from services.career_gradient import (
    build_witness_observation,
    learning_priorities,
    score_opportunity,
)


class CareerGradientTests(unittest.TestCase):
    def test_mandatory_not_held_blocks_actionability_class(self):
        result = score_opportunity({
            "id": "x",
            "title": "Credential-gated role",
            "gradient_axes": {"scope": 1.0},
            "requirements": [
                {"id": "r1", "capability": "Required license", "mandatory": True, "mapping_state": "NOT_HELD", "weight": 1.0}
            ],
        })
        self.assertEqual("HOLD", result.classification)
        self.assertEqual(("Required license",), result.mandatory_blockers)

    def test_bridge_is_separate_from_actionability(self):
        result = score_opportunity({
            "id": "x",
            "title": "Bridge role",
            "gradient_axes": {"scope": 0.9, "evidence_gain": 0.9},
            "requirements": [
                {"id": "r1", "capability": "A", "mandatory": True, "mapping_state": "DOCUMENTED", "weight": 1.0},
                {"id": "r2", "capability": "B", "mandatory": False, "mapping_state": "PARTIAL", "weight": 1.0},
            ],
        })
        self.assertEqual("BRIDGE", result.classification)
        self.assertGreater(result.gradient, 0.55)

    def test_learning_priority_names_gap_action(self):
        rows = learning_priorities([{
            "id": "f",
            "title": "Frontier",
            "opportunity_value": 1.0,
            "gradient_axes": {"scope": 1.0},
            "requirements": [
                {"id": "r1", "capability": "Architecture evidence", "mapping_state": "PARTIAL", "gap_type": "evidence", "weight": 1.0}
            ],
        }])
        self.assertEqual("BUILD_EVIDENCE", rows[0]["action"])
        self.assertEqual("Architecture evidence", rows[0]["capability"])

    def test_witness_never_grants_authority(self):
        obs = build_witness_observation({
            "schema_version": "0.1.0",
            "profile_id": "p",
            "declared_goal_source": "user",
            "opportunities": [],
        })
        self.assertEqual("WITNESS_IS_NOT_THE_AUTHORITY", obs["non_authority_invariant"])
        self.assertEqual("NOT_GRANTED_BY_WITNESS", obs["authorization"]["state"])


if __name__ == "__main__":
    unittest.main()
