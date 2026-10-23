import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "system_stance_v1.schema.json"
FIXTURES_DIR = ROOT / "fixtures" / "system_stance_v1"


@pytest.fixture(scope="module")
def validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


@pytest.fixture()
def valid_stance():
    return {
        "schema": "humanaios/system_stance_v1",
        "advisory_only": True,
        "can_authorize": False,
        "authority_effect": "NONE",
        "subject": {
            "repository": "humanaios-ui/operations",
            "ref": "64c26cb058cf20eb5145c5ccfb9d4cc9c929871f",
            "scope": "Potential evidence-integrity improvements",
        },
        "overall_stance": "ACQUIRE_EVIDENCE",
        "stance_rationale": "The opportunity is plausible, but unresolved eligibility and authority checks remain.",
        "certainty": {
            "level": "MODERATE",
            "basis": "One repository specification and a matching implementation were inspected.",
            "limitations": ["External adoption has not been measured."],
        },
        "opportunity_scan": {
            "status": "PARTIAL",
            "scope": "Repository evidence only",
            "limitations": ["External dependencies were not contacted."],
            "opportunities": [
                {
                    "id": "OP-1",
                    "description": "Improve evidence provenance before consequential decisions.",
                    "propositions": [
                        {
                            "claim": "The proposed check can detect missing source references.",
                            "evidence": [
                                {
                                    "relation": "SUPPORTS",
                                    "kind": "source",
                                    "locator": "schemas/intent_os_operator_check_v1.schema.json:108",
                                    "observation": "The schema requires each evidence locator to include a specificity marker.",
                                },
                                {
                                    "relation": "CONTRADICTS",
                                    "kind": "source",
                                    "locator": "docs/INTENT_OS_RNOLA_INTEGRATION.md#limitations",
                                    "observation": "The integration remains advisory and does not establish source truth.",
                                },
                            ],
                            "certainty": {
                                "level": "MODERATE",
                                "basis": "The schema requirement is explicit, but no external-source validation is performed.",
                                "limitations": ["The schema cannot verify that cited evidence is accurate."],
                            },
                        }
                    ],
                }
            ],
        },
        "pre_action_requirements": [
            {
                "check": "Confirm that the evidence is current and applicable.",
                "status": "OPEN",
                "verification": "Re-read the cited source at the exact version relevant to the proposed action.",
                "evidence": [],
            },
            {
                "check": "Confirm the required authority for any consequential action.",
                "status": "VERIFIED",
                "verification": "Inspect the current governance authority boundary.",
                "evidence": [
                    {
                        "relation": "SUPPORTS",
                        "kind": "source",
                        "locator": "GOVERNANCE.md:14",
                        "observation": "The governance document assigns ratification and execution to their defined roles.",
                    }
                ],
            },
        ],
        "not_established": ["That acting on this opportunity will produce the intended outcome."],
        "created_at": "2026-10-03T16:00:00Z",
    }


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


def test_subject_ref_must_be_lowercase_hex_commit_sha(validator, valid_stance):
    valid_stance["subject"]["ref"] = "main"
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


def test_act_requires_every_pre_action_check_verified(validator, valid_stance):
    valid_stance["overall_stance"] = "ACT"
    with pytest.raises(ValidationError):
        validator.validate(valid_stance)


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


def test_golden_valid_fixture_passes(validator):
    payload = json.loads(
        (FIXTURES_DIR / "valid_acquire_evidence.json").read_text(encoding="utf-8")
    )
    validator.validate(payload)


@pytest.mark.parametrize(
    "filename",
    [
        "invalid_act_with_open.json",
        "invalid_not_started_with_opportunity.json",
        "invalid_verified_without_evidence.json",
        "invalid_non_hex_subject_ref.json",
    ],
)
def test_golden_invalid_fixtures_fail(validator, filename):
    payload = json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        validator.validate(payload)
