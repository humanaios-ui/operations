#!/usr/bin/env python3
"""
Enforce Z2/Z3 authority boundaries for operator-checks.

Prevents operator-checks from being misused as:
- Authorization for merge gates
- Sole evidence for Z2 ratification
- Substitutes for CI, test evidence, or repository provenance

Run during CI to catch boundary violations before merge.
"""

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "intent_os_operator_check_v1.schema.json"
OUTPUTS_RNOLA = ROOT / "outputs" / "rnola"


def load_schema():
    """Load the operator-check schema."""
    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema not found: {SCHEMA_PATH}")
        return None
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        return schema
    except Exception as e:
        print(f"ERROR: Failed to load or validate schema: {e}")
        return None


def check_rnola_records_exist(strict=False):
    """
    Check any operator-check records in outputs/rnola/ for misuse patterns.
    Returns True if all checks pass; False if violations found.
    """
    if not OUTPUTS_RNOLA.exists():
        # No RNOLA records yet — pass
        return True

    schema = load_schema()
    if not schema:
        return False

    validator = Draft202012Validator(schema)
    violations = []

    for record_file in OUTPUTS_RNOLA.glob("*.json"):
        try:
            record = json.loads(record_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {record_file}: {e}")
            return False

        # Validate against schema
        try:
            validator.validate(record)
        except ValidationError as e:
            violations.append(f"{record_file}: Schema validation failed: {e.message}")
            continue

        # Check 1: advisory_only and can_authorize are hard-coded
        if record.get("advisory_only") is not True:
            violations.append(f"{record_file}: advisory_only is not True (VIOLATION)")
        if record.get("can_authorize") is not False:
            violations.append(f"{record_file}: can_authorize is not False (VIOLATION)")

        # Check 2: evidence_inspected is not empty
        evidence = record.get("evidence_inspected", [])
        if not evidence:
            violations.append(f"{record_file}: evidence_inspected is empty (CHECKBOX PATTERN)")

        # Check 3: calibration.demonstrated is not empty
        calibration = record.get("calibration", {})
        demonstrated = calibration.get("demonstrated", [])
        if not demonstrated:
            violations.append(f"{record_file}: calibration.demonstrated is empty (NO LEARNING)")

        # Check 4: operator_response is substantive
        response = record.get("operator_response", "")
        if len(response) < 20:
            violations.append(f"{record_file}: operator_response is too brief ({len(response)} chars)")

    if violations:
        for violation in violations:
            print(f"VIOLATION: {violation}")
        return False

    return True


def check_pr_reviews_for_operator_check_misuse(pr_body_text=None):
    """
    Check PR description or review comments for patterns suggesting operator-checks
    are being treated as authorization.

    Patterns to reject:
    - "The operator-check approves this"
    - "operator-check satisfies review"
    - "based on operator-check, merge"
    """
    if not pr_body_text:
        return True

    dangerous_phrases = [
        "operator-check approves",
        "operator-check satisfies",
        "based on operator-check merge",
        "operator check is authorization",
        "operator check permits",
        "operator check authorizes",
    ]

    text_lower = pr_body_text.lower()
    violations = []

    for phrase in dangerous_phrases:
        if phrase in text_lower:
            violations.append(f"Found dangerous phrase: '{phrase}'")

    if violations:
        for violation in violations:
            print(f"VIOLATION: {violation}")
        return False

    return True


def check_schema_hard_constraints():
    """Verify schema has hard constraints on advisory_only and can_authorize."""
    schema = load_schema()
    if not schema:
        return False

    properties = schema.get("properties", {})
    advisory_only = properties.get("advisory_only", {})
    can_authorize = properties.get("can_authorize", {})

    # Both must use "const" to hard-code the values
    if advisory_only.get("const") is not True:
        print("ERROR: Schema does not hard-code advisory_only=true")
        return False

    if can_authorize.get("const") is not False:
        print("ERROR: Schema does not hard-code can_authorize=false")
        return False

    # Both should have comment warnings
    if "$comment" not in advisory_only:
        print("WARNING: advisory_only missing $comment boundary warning")
    if "$comment" not in can_authorize:
        print("WARNING: can_authorize missing $comment boundary warning")

    return True


def main():
    """Run all boundary enforcement checks."""
    parser = argparse.ArgumentParser(
        description="Enforce Z2/Z3 authority boundaries for RNOLA operator-checks."
    )
    parser.add_argument(
        "--check-schemas",
        action="store_true",
        help="Validate schema hard constraints (default: enabled)",
    )
    parser.add_argument(
        "--pr-event",
        type=str,
        help="Path to GitHub PR event JSON for boundary checks in PR body",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings; default allows warnings",
    )

    args = parser.parse_args()

    print("Enforcing Z2/Z3 authority boundaries for RNOLA operator-checks...")

    all_pass = True

    # Check 1: Schema hard constraints
    if not check_schema_hard_constraints():
        all_pass = False

    # Check 2: RNOLA records conform to anti-misuse patterns
    if not check_rnola_records_exist(strict=args.strict):
        all_pass = False

    # Check 3: PR body doesn't suggest operator-check as authorization
    pr_body = None
    if args.pr_event:
        try:
            with open(args.pr_event, encoding="utf-8") as f:
                event = json.load(f)
                pr_body = event.get("pull_request", {}).get("body", "")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"WARNING: Could not read PR event: {e}")

    if not check_pr_reviews_for_operator_check_misuse(pr_body):
        all_pass = False

    if all_pass:
        print("✓ All Z2/Z3 boundary checks passed.")
        sys.exit(0)
    else:
        print("✗ One or more Z2/Z3 boundary violations detected.")
        sys.exit(1)


if __name__ == "__main__":
    main()
