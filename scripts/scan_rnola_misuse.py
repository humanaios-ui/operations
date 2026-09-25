#!/usr/bin/env python3
"""
Scan RNOLA operator-check records for misuse patterns and falsifier violations.

Falsifiers:
1. operator check treated as authorization
2. RNOLA produces conclusions without citing artifact/ref
3. operator teach-back becomes a checkbox without evidence inspection
4. repository cognitive load increases (RNOLA duplicates state)
5. learning records make it harder to distinguish proposed, verified, authorized, observed states

This script detects patterns indicative of falsifier violation.
Exit 0 if all records pass; exit 1 if falsifier violations found.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_RNOLA = ROOT / "outputs" / "rnola"


def scan_record_for_checkbox_pattern(record, path):
    """
    Detect checkbox pattern: teach-back without evidence inspection.

    Indicators:
    - evidence_inspected is empty or has <2 items
    - observation fields are generic/placeholder
    - calibration.demonstrated is empty
    """
    violations = []

    evidence = record.get("evidence_inspected", [])
    if not evidence or len(evidence) < 2:
        violations.append("CHECKBOX: evidence_inspected has <2 items (too few artifacts inspected)")

    for i, ev in enumerate(evidence):
        observation = ev.get("observation", "").lower()
        if any(phrase in observation for phrase in ["i checked", "looks good", "seems fine", "appears ok"]):
            violations.append(f"CHECKBOX: evidence[{i}] observation is generic/placeholder")

    calibration = record.get("calibration", {})
    demonstrated = calibration.get("demonstrated", [])
    if not demonstrated:
        violations.append("CHECKBOX: calibration.demonstrated is empty (no learning claims)")

    partial = calibration.get("partial", [])
    not_tested = calibration.get("not_tested", [])
    if not partial and not not_tested:
        violations.append("CHECKBOX: no partial or not_tested items (no nuance/boundary identified)")

    return violations


def scan_record_for_authorization_pattern(record, path):
    """
    Detect authorization pattern: operator-check treated as merge approval.

    Indicators:
    - advisory_only or can_authorize are not hard-coded values
    - authority_consequence uses permissive language
    """
    violations = []

    if record.get("advisory_only") is not True:
        violations.append("AUTHORIZATION: advisory_only is not True")
    if record.get("can_authorize") is not False:
        violations.append("AUTHORIZATION: can_authorize is not False")

    consequence = record.get("authority_consequence", "").lower()
    dangerous_words = ["approve", "permit", "authorize", "enable merge", "ready to merge"]
    for word in dangerous_words:
        if word in consequence:
            violations.append(f"AUTHORIZATION: authority_consequence uses dangerous word '{word}'")

    return violations


def scan_record_for_undefined_artifact(record, path):
    """
    Detect undefined artifact pattern: conclusions without citing exact artifact/ref.

    Indicators:
    - subject.ref is a branch name, not a SHA
    - evidence_inspected has no locator
    - operator_response makes claims but doesn't tie them to code
    """
    violations = []

    subject = record.get("subject", {})
    ref = subject.get("ref", "")

    # Check if ref looks like a branch name (contains /, starts with known branch patterns)
    if ref in ["main", "master", "develop", "staging"]:
        violations.append("UNDEFINED: subject.ref is a branch name, not a commit SHA")

    evidence = record.get("evidence_inspected", [])
    for i, ev in enumerate(evidence):
        locator = ev.get("locator", "")
        if not locator or len(locator) < 5:
            violations.append(f"UNDEFINED: evidence[{i}] locator is missing or too generic")

    return violations


def scan_record_freshness(record, path):
    """
    Detect stale records: operator-checks created days/weeks after PR merge.

    A PR merged on Monday but operator-check created the following Friday
    suggests post-hoc rationalization rather than evidence-driven learning.
    """
    violations = []

    created_at = record.get("created_at")
    if not created_at:
        violations.append("FRESHNESS: created_at is missing")
        return violations

    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        violations.append(f"FRESHNESS: created_at is malformed: {created_at}")
        return violations

    # Check if created_at is more than 7 days in the past
    age = datetime.now(created.tzinfo) - created
    if age > timedelta(days=7):
        violations.append(f"FRESHNESS WARNING: operator-check is {age.days} days old (post-hoc evidence?)")

    return violations


def scan_all_records():
    """Scan all RNOLA records for falsifier violations."""
    if not OUTPUTS_RNOLA.exists():
        print("ℹ No RNOLA records found (outputs/rnola/ does not exist or is empty)")
        return True

    all_violations = {}
    record_count = 0

    for record_file in OUTPUTS_RNOLA.glob("*.json"):
        record_count += 1
        try:
            record = json.loads(record_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {record_file}: {e}")
            all_violations[record_file.name] = ["PARSE_ERROR: Invalid JSON"]
            continue

        violations = []
        violations.extend(scan_record_for_checkbox_pattern(record, record_file))
        violations.extend(scan_record_for_authorization_pattern(record, record_file))
        violations.extend(scan_record_for_undefined_artifact(record, record_file))
        violations.extend(scan_record_freshness(record, record_file))

        if violations:
            all_violations[record_file.name] = violations

    if not all_violations:
        if record_count > 0:
            print(f"✓ Scanned {record_count} RNOLA record(s); no falsifier violations detected.")
        return True

    # Report violations
    for filename, violations in sorted(all_violations.items()):
        print(f"\n{filename}:")
        for violation in violations:
            print(f"  ✗ {violation}")

    print(f"\n✗ Found falsifier violations in {len(all_violations)} record(s).")
    return False


def main():
    """Run RNOLA falsifier scan."""
    print("Scanning RNOLA operator-check records for falsifier violations...")

    if scan_all_records():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
