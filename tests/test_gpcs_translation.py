import copy
import unittest
from gpcs.translation import translate, replay, ContractError

BASE = {
    "schema": "gpcs.observation.v0.1",
    "observation_id": "OBS-1",
    "agent_id": "oracle-resource",
    "session_id": "SESSION-1",
    "source_substrate": "github",
    "source_locator": "repo:humanaios-ui/operations/issues/775",
    "source_sha256": "a" * 64,
    "statement": "An observation exists; its truth remains unverified.",
    "as_of": "2026-10-09T20:00:00Z",
    "recorded_at": "2026-10-09T21:00:00Z",
    "epistemic_state": "OBSERVED_UNVERIFIED",
    "operation": "ADD",
    "related_observation_ids": []
}

class TestGPCS(unittest.TestCase):
    def test_projection_is_advisory(self):
        out = translate(BASE)
        for value in out.values():
            self.assertFalse(value["can_authorize"])
            self.assertEqual(value["authority_effect"], "NONE")
        self.assertEqual(out["coordinator_candidate"]["admission_state"], "NOT_REQUESTED")
        self.assertEqual(out["evidence_graph_delta"]["proof_status"], "NOT_ESTABLISHED")

    def test_deterministic(self):
        self.assertEqual(translate(BASE), translate(dict(reversed(list(BASE.items())))))

    def test_unknown_authority_field_rejected(self):
        for field in ["action_ready", "authorization", "api_key", "tool_call", "can_execute"]:
            row = {**BASE, field: True}
            with self.subTest(field=field), self.assertRaises(ContractError):
                translate(row)

    def test_missing_provenance_rejected(self):
        for field in ["source_sha256", "source_locator", "as_of", "session_id"]:
            row = copy.deepcopy(BASE)
            del row[field]
            with self.subTest(field=field), self.assertRaises(ContractError):
                translate(row)

    def test_naive_datetime_rejected(self):
        row = {**BASE, "recorded_at": "2026-10-09T21:00:00"}
        with self.assertRaises(ContractError):
            translate(row)

    def test_lineage_replay(self):
        later = {**BASE, "observation_id": "OBS-2", "operation": "CONTRADICT",
                 "epistemic_state": "CONTRADICTED", "related_observation_ids": ["OBS-1"]}
        results = replay([BASE, later])
        self.assertEqual(results[1]["evidence_graph_delta"]["operation"], "CONTRADICT")
        self.assertEqual(results[1]["evidence_graph_delta"]["related_observation_ids"], ["OBS-1"])

    def test_missing_lineage_rejected(self):
        row = {**BASE, "operation": "SUPERSEDE", "epistemic_state": "SUPERSEDED",
               "related_observation_ids": ["OBS-missing"]}
        with self.assertRaises(ContractError):
            replay([row])

    def test_duplicate_rejected(self):
        with self.assertRaises(ContractError):
            replay([BASE, BASE])

    def test_no_downgrade_to_authority(self):
        out = replay([BASE])[0]
        self.assertNotIn("action_ready", out["coordinator_candidate"])
        self.assertNotIn("status", out["coordinator_candidate"])

if __name__ == "__main__":
    unittest.main()
