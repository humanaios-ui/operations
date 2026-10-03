import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "system_stance_v1.schema.json"
FIXTURES_PATH = ROOT / "fixtures" / "system_stance_v1"


@pytest.fixture(scope="module")
def validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def valid_stance():
    return load_json(FIXTURES_PATH / "valid_advisory.json")


def test_valid_advisory_stance_passes(validator, valid_stance):
    validator.validate(valid_stance)


def test_no_opportunities_can_be_reported_after_a_complete_scan(validator, valid_stance):
    valid_stance["opportunity_scan"]["status"] = "COMPLETE"
    valid_stance["opportunity_scan"]["opportunities"] = []
    validator.validate(valid_stance)


def test_unstarted_scan_cannot_claim_opportunities(validator, valid_stance):
    valid_stance["opportunity_scan"]["status"] = "NOT_STARTED"
    with pytest.raises(ValidationError):
        validator.validate(valid_stance)


def test_proposition_requires_explicit_certainty(validator, valid_stance):
    del valid_stance["opportunity_scan"]["opportunities"][0]["propositions"][0]["certainty"]
    with pytest.raises(ValidationError):
        validator.validate(valid_stance)


def test_proposition_evidence_requires_specific_locator(validator, valid_stance):
    evidence = valid_stance["opportunity_scan"]["opportunities"][0]["propositions"][0]["evidence"][0]
    evidence["locator"] = "schemas/intent_os_operator_check_v1.schema.json"
    with pytest.raises(ValidationError):
        validator.validate(valid_stance)


def test_verified_pre_action_check_requires_evidence(validator, valid_stance):
    requirement = valid_stance["pre_action_requirements"][1]
    requirement["evidence"] = []
    with pytest.raises(ValidationError):
        validator.validate(valid_stance)


def test_non_hex_commit_ref_is_rejected(validator, valid_stance):
    valid_stance["subject"]["ref"] = "not-a-commit"
    with pytest.raises(ValidationError):
        validator.validate(valid_stance)


def test_act_requires_every_pre_action_check_verified(validator, valid_stance):
    valid_stance["overall_stance"] = "ACT"
    with pytest.raises(ValidationError):
        validator.validate(valid_stance)


def test_golden_invalid_records_are_rejected(validator):
    base_record = load_json(FIXTURES_PATH / "valid_advisory.json")
    cases = load_json(FIXTURES_PATH / "invalid_cases.json")

    assert cases["base_record"] == "valid_advisory.json"
    validator.validate(base_record)

    for case in cases["cases"]:
        record = deepcopy(base_record)
        for replacement in case["replacements"]:
            path = replacement["path"].strip("/").split("/")
            target = record
            for part in path[:-1]:
                target = target[int(part)] if isinstance(target, list) else target[part]
            key = path[-1]
            if isinstance(target, list):
                target[int(key)] = replacement["value"]
            else:
                target[key] = replacement["value"]

        with pytest.raises(ValidationError, match="."):
            validator.validate(record)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("advisory_only", False),
        ("can_authorize", True),
        ("authority_effect", "GRANT"),
    ],
)
def test_stance_cannot_grant_authority(validator, valid_stance, field, value):
    valid_stance[field] = value
    with pytest.raises(ValidationError):
        validator.validate(valid_stance)
