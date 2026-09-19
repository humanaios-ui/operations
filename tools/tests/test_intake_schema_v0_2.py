"""
test_intake_schema_v0_2.py
Builder v1.7 compliant
HumanAIOS
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import intake_schema_v0_2 as intake_schema  # noqa: E402


def _valid_row() -> dict:
    return {
        "intent_name": "SSI-backed intake mitigation",
        "author": {
            "originator_did": "did:key:z6MkhazExampleDid",
            "signature": "base64-ed25519-sig",
        },
        "status": "draft",
        "submitted_at": "2026-09-09T00:00:00Z",
        "problem": "Current intake can restate the symptom but still miss when the originator changes position under pressure.",
        "proposed_outcome": "Add falsifier, probability, and calibration gates so intake records endorsement separately from authorship.",
        "affected_users_and_systems": "Originators, intake operators, and downstream intake consumers all read the same structured fields.",
        "constraints": "Calibration must work without mandatory identity disclosure and must stay compatible with DID-based authorship.",
        "open_questions": ["What drift threshold should trigger re-declaration?"],
        "falsifier": "If ten intakes cannot distinguish stable from drifting endorsements, the added gates are insufficient.",
        "smag_p": 0.9,
        "calibration_check": {
            "status": "ENDORSE",
            "reviewed_at": "2026-09-09T00:05:00Z",
            "note": "Re-read after scenario pressure and still endorsed.",
        },
        "architecture_change": True,
    }


class TestIntakeSchema(unittest.TestCase):
    def test_valid_row_passes_without_warnings_when_signature_present(self):
        result = intake_schema.run(_valid_row())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["summary"]["failed"], 0)

    def test_did_without_signature_warns_but_does_not_fail(self):
        row = _valid_row()
        row["author"].pop("signature")
        result = intake_schema.run(row)
        self.assertEqual(result["status"], "WARN")
        self.assertTrue(any("cryptographically bound" in warning for warning in result["warnings"]))

    def test_missing_falsifier_fails(self):
        row = _valid_row()
        row["falsifier"] = "too short"
        result = intake_schema.run(row)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("falsifier" in error for error in result["items"][0]["errors"]))

    def test_architecture_change_requires_non_skipped_calibration(self):
        row = _valid_row()
        row["calibration_check"] = {"status": "SKIPPED", "note": "Deferred"}
        result = intake_schema.run(row)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("architecture_change" in error for error in result["items"][0]["errors"]))

    def test_gate_hashes_must_arrive_as_a_complete_trio(self):
        row = _valid_row()
        row["scope_hash"] = "a" * 64
        result = intake_schema.run(row)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("provided together" in error for error in result["items"][0]["errors"]))

    def test_jsonl_loader_accepts_line_delimited_rows(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            path = tmp_path / "intake.jsonl"
            path.write_text(
                '{"intent_name":"One question intake","author":{"name":"Night"},"status":"draft","submitted_at":"2026-09-09T00:00:00Z","problem":"Originators can agree with a symptom restatement while still drifting under pressure.","proposed_outcome":"Collect falsifier, probability, and calibration state in one row.","affected_users_and_systems":"Originators and intake consumers read the same row.","constraints":"No identity requirement for calibration usage.","open_questions":["What threshold triggers re-declaration?"],"falsifier":"If ten intakes cannot separate endorsement from drift, the schema fails.","smag_p":0.72,"calibration_check":{"status":"SKIPPED","note":"Feature-level draft."},"architecture_change":false}\n',
                encoding="utf-8",
            )
            loaded = intake_schema.load_input(str(path))
            self.assertIn("rows", loaded)
            result = intake_schema.run(loaded)
            self.assertEqual(result["status"], "WARN")


if __name__ == "__main__":
    unittest.main()
