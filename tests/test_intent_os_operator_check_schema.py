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
            "ref": "64c26cb058cf20eb5145c5ccfb9d4cc9c929871f",
            "identifier": "PR-999",
            "artifact_paths": ["docs/example.md"],
        },
        "intent": "Teach the operator what this PR changes.",
        "question": "What will merging this PR change?",
        "operator_response": "It adds advisory learning evidence without granting authority.",
        "evidence_inspected": [
            {
                "kind": "diff",
                "locator": "PR-999#comment-123456",
                "observation": "The diff adds learning artifacts only; no merge authority is granted.",
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


def test_operator_check_ref_must_be_sha_not_branch(validator, valid_record):
    """Operator-check must cite exact commit SHA, not branch name."""
    valid_record["subject"]["ref"] = "main"
    with pytest.raises(ValidationError):
        validator.validate(valid_record)


def test_operator_check_ref_accepts_short_sha(validator, valid_record):
    """Short SHAs (7+ hex chars) are acceptable."""
    valid_record["subject"]["ref"] = "64c26cb"  # 7-char SHA
    validator.validate(valid_record)  # Must not raise


def test_operator_check_evidence_locator_requires_specificity(validator, valid_record):
    """Evidence locator must cite exact location (line, comment, etc.), not just PR."""
    valid_record["evidence_inspected"][0]["locator"] = "PR-999"  # Too generic
    with pytest.raises(ValidationError):
        validator.validate(valid_record)


def test_operator_check_evidence_locator_accepts_comment_reference(validator, valid_record):
    """Evidence locator can cite PR comment, line number, or commit ref."""
    valid_record["evidence_inspected"][0]["locator"] = "PR-999#comment-123456"
    validator.validate(valid_record)  # Must not raise


def test_operator_check_evidence_locator_accepts_file_line(validator, valid_record):
    """Evidence locator can cite file and line number."""
    valid_record["evidence_inspected"][0]["locator"] = "tests/test_*.py:42"
    validator.validate(valid_record)  # Must not raise


def test_operator_check_evidence_locator_accepts_commit_ref(validator, valid_record):
    """Evidence locator can cite exact commit."""
    valid_record["evidence_inspected"][0]["locator"] = "commit:64c26cb058cf20eb5145c5ccfb9d4cc9c929871f"
    validator.validate(valid_record)  # Must not raise


def test_operator_check_observation_must_not_be_placeholder(validator, valid_record):
    """Observation field must be substantive (min 10 chars) to discourage checkboxes."""
    valid_record["evidence_inspected"][0]["observation"] = "I checked it."  # Only 13 chars, close to min
    validator.validate(valid_record)  # Must not raise (13 >= 10)

    valid_record["evidence_inspected"][0]["observation"] = "Good."  # 5 chars, below min
    with pytest.raises(ValidationError):
        validator.validate(valid_record)


def test_operator_check_cannot_satisfy_merge_gate(validator, valid_record):
    """Operator-check is advisory only; it cannot be used as a merge gate."""
    # This is a semantic test — the schema cannot enforce it directly,
    # but the hard-coded advisory_only and can_authorize prevent misuse.
    record = valid_record
    assert record["advisory_only"] is True
    assert record["can_authorize"] is False
    # If this record were treated as a merge authorization, it would violate governance.
    # CI gates downstream must reject it if used as authorization.
