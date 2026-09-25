import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "intent_os_operator_check_v1.schema.json"


@pytest.fixture(scope="module")
def validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture()
def valid_record():
    return {
        "schema": "intentos/operator_check_v1",
        "advisory_only": True,
        "can_authorize": False,
        "subject": {
            "type": "pull_request",
            "repository": "humanaios-ui/operations",
            "ref": "abc123",
            "identifier": "PR-999",
            "artifact_paths": ["docs/example.md"],
        },
        "intent": "Teach the operator what this PR changes.",
        "question": "What will merging this PR change?",
        "operator_response": "It adds advisory learning evidence without granting authority.",
        "evidence_inspected": [
            {
                "kind": "diff",
                "locator": "PR-999",
                "observation": "The diff adds learning artifacts only.",
            }
        ],
        "calibration": {
            "demonstrated": ["proposal versus authorization"],
            "partial": ["CI detail"],
            "not_tested": ["rollback"],
            "unknown": [],
        },
        "authority_consequence": "Merge changes repository state; the operator check cannot authorize another action.",
        "next_learning_object": "Inspect the validating CI job.",
        "created_at": "2026-09-25T18:00:00Z",
    }


def test_valid_operator_check_passes(validator, valid_record):
    validator.validate(valid_record)


def test_operator_check_cannot_claim_authority(validator, valid_record):
    valid_record["can_authorize"] = True
    with pytest.raises(ValidationError):
        validator.validate(valid_record)


def test_operator_check_must_remain_advisory(validator, valid_record):
    valid_record["advisory_only"] = False
    with pytest.raises(ValidationError):
        validator.validate(valid_record)


def test_operator_check_requires_inspected_evidence(validator, valid_record):
    valid_record["evidence_inspected"] = []
    with pytest.raises(ValidationError):
        validator.validate(valid_record)


def test_calibration_rejects_numeric_score_field(validator, valid_record):
    valid_record["calibration"]["score"] = 0.9
    with pytest.raises(ValidationError):
        validator.validate(valid_record)
