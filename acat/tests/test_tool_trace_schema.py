"""
test_tool_trace_schema.py
Builder v1.7 compliant
HumanAIOS

Stage 5's meta.tool_trace property was added to both ACAT contract schemas
without any test exercising it (a Copilot review finding on PR #302).
Covers the null/empty/valid/invalid cases for both phase1_intake and
phase3_submission, using the same jsonschema.Draft202012Validator pattern
as test_batch_submission_goal4.py.
"""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "contracts"


def load_schema(name):
    return json.loads((CONTRACTS_DIR / name).read_text(encoding="utf-8"))


def phase1_base_payload():
    return {
        "phase": "phase1",
        "session_id": "sess_tool_trace_001",
        "assessment_id": "acat_tool_trace_001",
        "agent_name": "Claude",
        "provider": "anthropic",
        "submission_purity": "two_stage_verified",
        "scores": {
            "truth": 85, "service": 88, "harm": 80, "autonomy": 82,
            "value": 86, "humility": 75, "scheme": 78, "power": 80,
            "syc": 72, "consist": 84, "fair": 83, "handoff": 81,
        },
    }


def phase3_base_payload():
    return {
        "phase": "phase3",
        "session_id": "sess_tool_trace_001",  # schema's anyOf needs session_id or assessment_id
        "scores": {
            "truth": 85, "service": 88, "harm": 80, "autonomy": 82,
            "value": 86, "humility": 75, "scheme": 78, "power": 80,
            "syc": 72, "consist": 84, "fair": 83, "handoff": 81,
        },
    }


VALID_TOOL_CALL = {
    "seq": 1, "at": "2026-09-13T00:00:00+00:00", "tool_name": "Read",
    "input_digest": "a" * 64, "input_keys": ["file_path"],
}

SCHEMA_CASES = [
    ("phase1_intake.schema.json", phase1_base_payload),
    ("phase3_submission.schema.json", phase3_base_payload),
]


@pytest.mark.parametrize("schema_file,base_payload", SCHEMA_CASES)
class TestToolTraceSchema:
    def _validate(self, schema_file, payload):
        schema = load_schema(schema_file)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        return list(validator.iter_errors(payload))

    def test_null_tool_trace_is_valid(self, schema_file, base_payload):
        """No hooks wired / pre-Stage-5 / non-Claude-Code substrate."""
        payload = base_payload()
        payload["meta"] = {"tool_trace": None}
        errors = self._validate(schema_file, payload)
        assert errors == [], [e.message for e in errors]

    def test_empty_tool_trace_is_valid(self, schema_file, base_payload):
        """Captured, zero tools called — distinct from null."""
        payload = base_payload()
        payload["meta"] = {"tool_trace": []}
        errors = self._validate(schema_file, payload)
        assert errors == [], [e.message for e in errors]

    def test_valid_tool_call_entry_is_valid(self, schema_file, base_payload):
        payload = base_payload()
        payload["meta"] = {"tool_trace": [dict(VALID_TOOL_CALL)]}
        errors = self._validate(schema_file, payload)
        assert errors == [], [e.message for e in errors]

    def test_invalid_tool_call_datetime_is_invalid(self, schema_file, base_payload):
        entry = dict(VALID_TOOL_CALL)
        entry["at"] = "not-a-date-time"
        payload = base_payload()
        payload["meta"] = {"tool_trace": [entry]}
        errors = self._validate(schema_file, payload)
        assert errors, "expected a validation error for an invalid tool_trace.at date-time"

    def test_missing_input_digest_is_invalid(self, schema_file, base_payload):
        """input_digest is always emitted by the reader; a row missing it
        should fail validation, not silently pass (this is the same field
        the schema's own 'required' list must actually enforce)."""
        entry = dict(VALID_TOOL_CALL)
        del entry["input_digest"]
        payload = base_payload()
        payload["meta"] = {"tool_trace": [entry]}
        errors = self._validate(schema_file, payload)
        assert errors, "expected a validation error for a missing input_digest"

    def test_missing_input_keys_is_invalid(self, schema_file, base_payload):
        entry = dict(VALID_TOOL_CALL)
        del entry["input_keys"]
        payload = base_payload()
        payload["meta"] = {"tool_trace": [entry]}
        errors = self._validate(schema_file, payload)
        assert errors, "expected a validation error for a missing input_keys"

    def test_missing_seq_is_invalid(self, schema_file, base_payload):
        entry = dict(VALID_TOOL_CALL)
        del entry["seq"]
        payload = base_payload()
        payload["meta"] = {"tool_trace": [entry]}
        errors = self._validate(schema_file, payload)
        assert errors, "expected a validation error for a missing seq"

    def test_tool_trace_as_object_is_invalid(self, schema_file, base_payload):
        """tool_trace must be array or null, never a bare object."""
        payload = base_payload()
        payload["meta"] = {"tool_trace": {"seq": 1}}
        errors = self._validate(schema_file, payload)
        assert errors, "expected a validation error for tool_trace as an object"
