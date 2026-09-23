import copy
import json
import unittest
from pathlib import Path

from experiments.collab_harmony_01.harmony_stress import HARD_GATES, evaluate, from_dict
from tools.verified_receipts import build_receipt_chain_for_testing


HERE = Path(__file__).resolve().parent


def attach_valid_gate_receipts(payload):
    payload = copy.deepcopy(payload)
    run_id = payload.setdefault("run_id", "stress-healthy")
    gate_evidence = payload.get("gate_evidence", {})

    raw_events = []
    for gate in HARD_GATES:
        for receipt_id in gate_evidence.get(gate, []):
            raw_events.append({
                "type": "RECEIPT_VERIFIED",
                "receipt_id": receipt_id,
                "receipt_type": "HARMONY_GATE",
                "subject": gate,
                "action": "ASSERT_GATE",
                "scope": f"run:{run_id}",
                "issuer": "bridge-evidence-graph",
                "authority_scope": "NONE",
                "verification_status": "VERIFIED",
                "verification_strength": "OBSERVED",
                "verification_method": "BRIDGE_EVENT_HASH_CHAIN",
                "evidence_ref": f"evidence:{receipt_id}",
                "one_time": False,
            })

    events, head = build_receipt_chain_for_testing(raw_events)
    payload["receipt_events"] = events
    payload["receipt_head_hash"] = head
    return payload


class HarmonyStressVectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = json.loads((HERE / "test_vectors.json").read_text())

    def test_all_preregistered_vectors(self):
        for vector in self.vectors:
            with self.subTest(vector=vector["id"]):
                payload = vector["state"]
                if vector["id"] == "CH-01-HEALTHY-DISSENT":
                    payload = attach_valid_gate_receipts(payload)
                result = evaluate(from_dict(payload))
                self.assertEqual(vector["expected_verdict"], result["verdict"])

    def test_perfect_scores_cannot_override_gate_failure(self):
        state = from_dict({
            "contributions": [],
            "dissent_preserved": False,
            "mutual_understanding": 1.0,
            "complementarity": 1.0,
            "evidence_quality": 1.0,
            "coordination": 1.0,
            "collective_problem_solving": 1.0,
        })
        result = evaluate(state)
        self.assertEqual("INVALID_HARMONY", result["verdict"])
        self.assertEqual(0.0, result["score"])

    def test_raw_verified_ref_list_no_longer_counts(self):
        state = from_dict({
            "contributions": [],
            "gate_evidence": {gate: [f"receipt:{gate}"] for gate in HARD_GATES},
            "verified_gate_refs": [f"receipt:{gate}" for gate in HARD_GATES],
        })
        result = evaluate(state)
        self.assertEqual("INVALID_HARMONY", result["verdict"])
        self.assertTrue(any("NO_RECEIPT_FEED" in x for x in result["gate_failures"]))

    def test_tampered_receipt_chain_fails(self):
        payload = attach_valid_gate_receipts({
            "contributions": [],
            "run_id": "tamper",
            "gate_evidence": {gate: [f"r:{gate}"] for gate in HARD_GATES},
        })
        payload["receipt_events"][0]["subject"] = "tampered"
        result = evaluate(from_dict(payload))
        self.assertEqual("INVALID_HARMONY", result["verdict"])
        self.assertTrue(any("CHAIN_INVALID" in x for x in result["gate_failures"]))

    def test_wrong_scope_receipt_fails(self):
        payload = attach_valid_gate_receipts({
            "contributions": [],
            "run_id": "expected",
            "gate_evidence": {gate: [f"r:{gate}"] for gate in HARD_GATES},
        })
        # Rebuild a valid chain after intentionally changing one receipt's scope.
        raw = []
        for event in payload["receipt_events"]:
            body = {k: v for k, v in event.items() if k not in {"seq", "prev_hash", "hash"}}
            if body["subject"] == "human_autonomy_preserved":
                body["scope"] = "run:other"
            raw.append(body)
        events, head = build_receipt_chain_for_testing(raw)
        payload["receipt_events"] = events
        payload["receipt_head_hash"] = head

        result = evaluate(from_dict(payload))
        self.assertEqual("INVALID_HARMONY", result["verdict"])
        self.assertTrue(any("SCOPE_MISMATCH" in x for x in result["gate_failures"]))

    def test_simulated_receipt_method_fails(self):
        payload = attach_valid_gate_receipts({
            "contributions": [],
            "run_id": "simulated",
            "gate_evidence": {gate: [f"r:{gate}"] for gate in HARD_GATES},
        })
        raw = []
        for event in payload["receipt_events"]:
            body = {k: v for k, v in event.items() if k not in {"seq", "prev_hash", "hash"}}
            if body["subject"] == "provenance_complete":
                body["verification_method"] = "SIMULATED"
            raw.append(body)
        events, head = build_receipt_chain_for_testing(raw)
        payload["receipt_events"] = events
        payload["receipt_head_hash"] = head

        result = evaluate(from_dict(payload))
        self.assertEqual("INVALID_HARMONY", result["verdict"])
        self.assertTrue(any("DISALLOWED_VERIFICATION_METHOD" in x for x in result["gate_failures"]))

    def test_distinct_participants_do_not_prove_independence(self):
        state = from_dict({
            "contributions": [
                {"participant_id": "a", "participant_type": "AI"},
                {"participant_id": "b", "participant_type": "AI"},
            ]
        })
        result = evaluate(state)
        self.assertFalse(result["independence"]["independence_proven"])


if __name__ == "__main__":
    unittest.main()
