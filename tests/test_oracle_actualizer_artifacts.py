from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class OracleActualizerArtifactTests(unittest.TestCase):
    def test_oracle_state_matches_schema(self) -> None:
        state = _load_json("oracle_state.json")
        schema = _load_json("schemas/oracle-state.schema.json")
        Draft202012Validator(schema).validate(state)

    def test_actions_match_action_schema(self) -> None:
        state = _load_json("oracle_state.json")
        schema = _load_json("schemas/actualizer-action.schema.json")
        validator = Draft202012Validator(schema)

        for action in state["actions"]:
            validator.validate(action)

    def test_all_claims_include_epistemic_status(self) -> None:
        state = _load_json("oracle_state.json")
        self.assertTrue(state["policy"]["epistemic_status_required"])
        self.assertEqual("every_rendered_claim", state["policy"]["badge_visibility_rule"])

        for claim in state["claims"]:
            self.assertIn("epistemic_status", claim)
            self.assertTrue(claim["epistemic_status"])

    def test_unknown_or_disputed_warrants_not_ready_to_execute(self) -> None:
        state = _load_json("oracle_state.json")

        for action in state["actions"]:
            if action["lowest_warrant_status"] in {"UNKNOWN", "DISPUTED", "DEFEATED"}:
                self.assertTrue(action["human_approval_required"])
                self.assertNotEqual("READY_TO_EXECUTE", action["status"])

    def test_unverified_execution_consequences_have_48h_quarantine(self) -> None:
        state = _load_json("oracle_state.json")
        for receipt in state["execution_receipts"]:
            if receipt["consequence_status"] == "EXECUTION_CONSEQUENCE_UNVERIFIED":
                executed_at = _ts(receipt["executed_at"])
                quarantine_until = _ts(receipt["quarantine_until"])
                self.assertGreaterEqual((quarantine_until - executed_at).total_seconds(), 48 * 3600)
                self.assertEqual("PENDING", receipt["independent_verification"]["status"])

    def test_oracle_ui_references_badges_and_state_file(self) -> None:
        html = (ROOT / "ui/oracle.html").read_text(encoding="utf-8")
        self.assertIn("../oracle_state.json", html)
        self.assertIn("badge_visibility_rule", html)
        self.assertIn("PARTIALLY_SUPPORTED", html)
        self.assertIn("DISPUTED", html)
        self.assertIn("UNKNOWN", html)


if __name__ == "__main__":
    unittest.main()
