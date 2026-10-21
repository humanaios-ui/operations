import json
import tempfile
import unittest
from pathlib import Path

from workspace_evidence_bus.tools.workspace_lifecycle import (
    ROUNDTRIP_VERIFIED,
    project_current_state,
    validate_roundtrip_receipt,
)


def valid_receipt():
    return {
        "artifact_type": "WORKSPACE_ROUNDTRIP_GATE_RECEIPT",
        "event_id": "EVT-gha-1",
        "event_type": "ROUNDTRIP_TEST",
        "workflow_run_id": 1,
        "first_attempt": {"status": "PASS", "replayed": False},
        "replay_attempt": {"status": "PASS", "replayed": True},
        "secrets_present_check": "PASS",
        "apps_script_post": "PASS",
        "drive_write_readback_hash": "PASS",
        "idempotent_replay": "PASS",
        "authority_effect": "NONE",
        "hmbm_effect": {"prediction_authorized": False},
    }


class WorkspaceLifecycleTests(unittest.TestCase):
    def write_receipt(self, payload):
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "receipt.json"
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        self.addCleanup(tmp.cleanup)
        return path

    def test_valid_roundtrip_projects_verified_state(self):
        path = self.write_receipt(valid_receipt())
        state = project_current_state(
            path,
            historical_drive_file_id="drive-snapshot-1",
            historical_recorded_at="2026-10-02T20:52:00Z",
        )
        self.assertEqual(state["state"], ROUNDTRIP_VERIFIED)
        self.assertEqual(state["authority_effect"], "NONE")
        self.assertEqual(state["historical_snapshots"][0]["current_status"], "SUPERSEDED_AS_CURRENT_STATE")

    def test_committed_current_state_matches_projection(self):
        repo_root = Path(__file__).resolve().parents[2]
        receipt = repo_root / "workspace_evidence_bus/receipts/roundtrip_gate_receipt.json"
        committed = repo_root / "workspace_evidence_bus/state/current_state.json"
        projected = project_current_state(
            receipt,
            receipt_locator="workspace_evidence_bus/receipts/roundtrip_gate_receipt.json",
            historical_drive_file_id="11EgHtelUYGFGA5uYHZPzn6wIf1q717tg",
            historical_recorded_at="2026-10-02T20:52:00Z",
        )
        self.assertEqual(json.loads(committed.read_text(encoding="utf-8")), projected)

    def test_missing_required_pass_field_rejected(self):
        receipt = valid_receipt()
        receipt["drive_write_readback_hash"] = "FAIL"
        self.assertIn("drive_write_readback_hash must equal PASS", validate_roundtrip_receipt(receipt))

    def test_authority_expansion_rejected(self):
        receipt = valid_receipt()
        receipt["authority_effect"] = "Z2"
        self.assertIn("authority_effect must remain NONE", validate_roundtrip_receipt(receipt))

    def test_replay_contract_rejected_if_not_idempotent(self):
        receipt = valid_receipt()
        receipt["replay_attempt"]["replayed"] = False
        self.assertTrue(any("replay_attempt" in e for e in validate_roundtrip_receipt(receipt)))

    def test_prediction_authority_cannot_be_smuggled_through_receipt(self):
        receipt = valid_receipt()
        receipt["hmbm_effect"]["prediction_authorized"] = True
        self.assertIn("roundtrip receipt cannot authorize prediction", validate_roundtrip_receipt(receipt))


if __name__ == "__main__":
    unittest.main()
