"""Schema tests for the Engineering Evidence Cycle record."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "engineering_evidence_cycle.schema.json"
)


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def build_valid_record():
    return {
        "work_id": "ENG-501",
        "request": {
            "problem_statement": "Standardize an evidence-bearing engineering lifecycle.",
            "requester": "@humanaios-ui",
            "target_artifact": "mail-evidence lifecycle integration",
            "constraints": [
                "Do not create a parallel governance stack.",
                "Preserve authority boundaries."
            ],
            "authority_boundary": "Z1 integration candidate only; governance changes escalate.",
            "success_condition": "Lifecycle record is traceable from request through finalization.",
            "non_goals": ["Canonical Z2/Z3 authority changes"]
        },
        "plan": {
            "proposed_method": "Add a strict lifecycle record schema and validate it with focused tests.",
            "affected_components": ["schemas/engineering_evidence_cycle.schema.json", "tests"],
            "dependencies": ["jsonschema Draft 2020-12 validator"],
            "expected_artifacts": ["Engineering Evidence Cycle schema", "schema validation tests"],
            "falsifiers": ["Schema permits missing review/finalization limits."],
            "stop_conditions": ["Required phase evidence cannot be represented precisely."],
            "zone_expectation": "Z1"
        },
        "capability_assessment": {
            "available_tools": ["jsonschema", "pytest"],
            "unavailable_capabilities": ["private mail store access"],
            "authority_limitations": ["Cannot ratify governance semantics"],
            "data_privacy_boundary": "Public repository only; no private email content.",
            "resource_constraints": ["Repository-only change"],
            "execution_posture": "CAN_EXECUTE"
        },
        "prediction": {
            "predicted_result": "A compact schema can bind the lifecycle record without changing authority.",
            "predicted_failure_modes": ["Overly loose required fields", "Phase omissions"],
            "confidence": 0.77,
            "confidence_change_triggers": ["Conflicting existing schema conventions", "Validation failures"]
        },
        "execution_receipts": [
            {
                "phase": "PERFORM",
                "action": "Add schema file",
                "artifact_ref": "schemas/engineering_evidence_cycle.schema.json",
                "receipt": "git diff",
                "performed_at": "2026-09-24T16:30:00Z"
            }
        ],
        "self_review": {
            "actual_tests": ["jsonschema validation against a valid fixture"],
            "not_tested": ["Runtime adoption by downstream tools"],
            "known_limitations": ["Schema cannot prove independent review quality"],
            "assumptions": ["Lifecycle records will be emitted by higher-level tooling"],
            "implementation_spec_gaps": ["No runtime writer yet"],
            "contradictory_evidence": [],
            "confidence": 0.74,
            "falsifiers": ["A required invariant cannot be expressed in the schema"]
        },
        "independent_reviews": [
            {
                "reviewer": "security-review",
                "scope": "schema surface",
                "status": "not_requested",
                "findings": []
            }
        ],
        "discoveries": [
            {
                "kind": "ARCHITECTURE_GAP",
                "summary": "Lifecycle wording existed in issue/comment threads but not in a canonical schema artifact.",
                "zone_impact": "Z1",
                "proposed_update": "Add a repository schema first; leave governance unchanged."
            }
        ],
        "zone_decisions": [
            {
                "subject": "Engineering Evidence Cycle schema integration",
                "proposed_zone": "Z1",
                "decision": "Proceed as repository-local specification artifact",
                "authority_basis": "Issue #501 states this is a Z1 integration candidate."
            }
        ],
        "finalization": {
            "status": "PARTIAL",
            "requested_output_status": "Schema added and locally validated",
            "artifact_refs": ["schemas/engineering_evidence_cycle.schema.json"],
            "verification_receipts": ["tests/test_engineering_evidence_cycle_schema.py"],
            "unresolved": ["No runtime producer consumes this schema yet"],
            "accepted_discoveries": ["Need for a canonical lifecycle record schema"],
            "rejected_discoveries": [],
            "zone_authority_outcome": "No authority-boundary change performed",
            "handoff_next_state": "Optional downstream adoption by tools or ledgers",
            "not_established": ["Independent review is not yet automated or enforced"]
        }
    }


def validate(payload):
    validator = Draft202012Validator(load_schema(), format_checker=FormatChecker())
    return list(validator.iter_errors(payload))


def test_valid_engineering_evidence_cycle_record_passes():
    assert validate(build_valid_record()) == []


def test_missing_request_non_goals_fails():
    payload = build_valid_record()
    del payload["request"]["non_goals"]
    assert validate(payload)


def test_invalid_execution_posture_fails():
    payload = build_valid_record()
    payload["capability_assessment"]["execution_posture"] = "AUTO_EXECUTE"
    assert validate(payload)


def test_missing_finalization_not_established_fails():
    payload = build_valid_record()
    del payload["finalization"]["not_established"]
    assert validate(payload)


def test_unexpected_top_level_property_fails():
    payload = build_valid_record()
    payload["silent_scope_change"] = True
    assert validate(payload)


def test_invalid_receipt_timestamp_fails():
    payload = build_valid_record()
    payload["execution_receipts"] = copy.deepcopy(payload["execution_receipts"])
    payload["execution_receipts"][0]["performed_at"] = "not-a-date-time"
    assert validate(payload)
