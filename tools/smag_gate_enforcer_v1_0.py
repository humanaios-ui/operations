#!/usr/bin/env python3
"""
Builder v1.7 compliant · security_gate_tool
smag_gate_enforcer_v1_0.py — SMAG calibration state evaluator
HumanAIOS · S-092126

Evaluates the current state/evidence predicates for substrate-specific SMAG
calibration review. This tool does not treat elapsed time as merge authority.

Usage:
  python3 tools/smag_gate_enforcer_v1_0.py \
    --profile-path calibration_profiles/BASELINE_S092126.json \
    --ledger-path audits/smag_pilot_ledger.jsonl \
    --substrate "human:humanaios-ui" \
    --advisory-only

Returns:
  0 if calibration state was evaluated successfully
  1 if calibration review is required in blocking mode
  2 if configuration error
"""

TOOL_NAME = "smag_gate_enforcer"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "security_gate_tool"
TOOL_SESSION = "S-092126"
TOOL_ZONE = 1

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


AUTHORIZED_Z2_IDENTITIES = {
    "carly.r.anderson@gmail.com",
    "aioshuman@gmail.com",
}
RATIFICATION_HASH_RE = re.compile(r"^(?:[0-9a-f]{64}|sha256\(.+\))$")
REQUIRED_LEDGER_FIELDS = ("substrate", "timestamp", "failing_checks")


def load_profile(profile_path: str) -> dict:
    """Load calibration profile from JSON file."""
    try:
        with open(profile_path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        print(f"❌ Calibration profile not found: {profile_path}")
        sys.exit(2)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in calibration profile: {profile_path}")
        sys.exit(2)


def get_substrate_profile(profile: dict, substrate: str) -> dict:
    """Extract substrate-specific profile from full profile."""
    substrates = profile.get("substrates", {})
    if substrate not in substrates:
        print(f"❌ Substrate '{substrate}' not found in calibration profile")
        print(f"   Available substrates: {list(substrates.keys())}")
        sys.exit(2)
    return substrates[substrate]


def is_profile_ratified(profile: dict) -> bool:
    """
    Check whether the profile carries a currently admissible authority marker.

    This is intentionally conservative: a profile is not authority-valid unless
    it names an authorized Z2 identity and carries a sha256-form ratification
    token. Profiles with placeholder values remain advisory-only.
    """
    ratified_by = str(profile.get("ratified_by_z2", "")).strip()
    ratification_hash = str(profile.get("ratification_hash", "")).strip()

    if not ratified_by or ratified_by.startswith("TBD_"):
        return False
    if ratified_by not in AUTHORIZED_Z2_IDENTITIES:
        return False
    if not ratification_hash or ratification_hash.startswith("TBD_"):
        return False
    return bool(RATIFICATION_HASH_RE.fullmatch(ratification_hash))


def _is_iso_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def load_measurement_state(ledger_path: str, substrate: str) -> dict:
    """
    Load substrate-specific measurement state from the SMAG pilot ledger.

    Measurement contract for the target substrate:
    - source file exists and is valid JSONL
    - each target row is an object
    - each target row has substrate, timestamp, and failing_checks fields
    - timestamp is ISO-8601 text
    - failing_checks is a list
    """
    state = {
        "contract_valid": True,
        "issues": [],
        "rows": [],
        "row_count": 0,
        "failed_rows": 0,
        "gap_rate": 0.0,
    }

    path = Path(ledger_path)
    if not path.exists():
        state["contract_valid"] = False
        state["issues"].append(f"ledger missing: {ledger_path}")
        return state

    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    state["contract_valid"] = False
                    state["issues"].append(f"line {line_number}: malformed json")
                    continue

                if not isinstance(row, dict):
                    state["contract_valid"] = False
                    state["issues"].append(f"line {line_number}: row is not an object")
                    continue

                row_substrate = row.get("substrate")
                if row_substrate is None:
                    state["contract_valid"] = False
                    state["issues"].append(f"line {line_number}: missing substrate")
                    continue
                if row_substrate != substrate:
                    continue

                missing_fields = [name for name in REQUIRED_LEDGER_FIELDS if name not in row]
                if missing_fields:
                    state["contract_valid"] = False
                    joined = ", ".join(missing_fields)
                    state["issues"].append(f"line {line_number}: missing {joined}")
                    continue

                timestamp = row.get("timestamp")
                failing_checks = row.get("failing_checks")
                if not isinstance(timestamp, str) or not _is_iso_timestamp(timestamp):
                    state["contract_valid"] = False
                    state["issues"].append(f"line {line_number}: invalid timestamp")
                    continue
                if not isinstance(failing_checks, list):
                    state["contract_valid"] = False
                    state["issues"].append(f"line {line_number}: failing_checks must be a list")
                    continue

                state["rows"].append(row)
    except OSError as exc:
        state["contract_valid"] = False
        state["issues"].append(f"ledger unreadable: {exc}")
        return state

    state["row_count"] = len(state["rows"])
    state["failed_rows"] = sum(1 for row in state["rows"] if row["failing_checks"])
    if state["row_count"]:
        state["gap_rate"] = state["failed_rows"] / state["row_count"]
    return state


def compute_gap_rate(ledger_path: str, substrate: str) -> float:
    """Compute substrate-isolated gap_rate from the current ledger state."""
    return load_measurement_state(ledger_path, substrate)["gap_rate"]


def minimum_evidence_state_satisfied(measurement_state: dict, substrate_profile: dict) -> bool:
    """Return True when the substrate has enough measured rows to be actionable."""
    calibration_floor = int(substrate_profile.get("calibration_floor", 0) or 0)
    return measurement_state["row_count"] >= calibration_floor


def current_measured_state_exceeds_boundary(measurement_state: dict, substrate_profile: dict) -> bool:
    """Return True when measured state exceeds the ratified substrate boundary."""
    threshold = float(substrate_profile.get("merge_pause_threshold", 0.25))
    return measurement_state["gap_rate"] > threshold


def calibration_review_required(profile: dict, substrate_profile: dict, measurement_state: dict) -> bool:
    """Apply the explicit current-predicate shape from the reexamination issue."""
    return all(
        (
            is_profile_ratified(profile),
            measurement_state["contract_valid"],
            minimum_evidence_state_satisfied(measurement_state, substrate_profile),
            current_measured_state_exceeds_boundary(measurement_state, substrate_profile),
        )
    )


def enforce_review_bar(substrate_profile: dict) -> bool:
    """
    Report review_bar configuration without claiming CI enforcement.

    review_bar is a separate concern from gap_rate. The quality-baseline
    workflow only reports its configured value.
    """
    review_bar = substrate_profile.get("review_bar", "standard")
    print(f"📋 review_bar configured: {review_bar}")
    print("   Status: advisory only on this workflow surface")
    return True


def run_smoke_test() -> bool:
    """Smoke test: verify profile load and substrate-isolated measurement parsing."""
    try:
        test_profile_path = "calibration_profiles/BASELINE_S092126.json"
        test_ledger_path = "audits/smag_pilot_ledger.jsonl"

        if not Path(test_profile_path).exists():
            print(f"SMOKE_TEST: SKIP (profile not found at {test_profile_path})")
            return True

        profile = load_profile(test_profile_path)
        if "profile_id" not in profile:
            print("SMOKE_TEST: FAIL (profile missing profile_id)")
            return False

        gap_rate = compute_gap_rate(test_ledger_path, "human:humanaios-ui")
        if not isinstance(gap_rate, float) or gap_rate < 0.0 or gap_rate > 1.0:
            print(f"SMOKE_TEST: FAIL (invalid gap_rate: {gap_rate})")
            return False

        print(f"SMOKE_TEST: PASS (profile={profile.get('profile_id')}, gap_rate={gap_rate:.2%})")
        return True
    except Exception as exc:
        print(f"SMOKE_TEST: FAIL ({exc})")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SMAG calibration state evaluator (state/evidence based)"
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run smoke test and exit",
    )
    parser.add_argument(
        "--profile-path",
        default="calibration_profiles/BASELINE_S092126.json",
        help="Path to calibration profile JSON",
    )
    parser.add_argument(
        "--ledger-path",
        default="audits/smag_pilot_ledger.jsonl",
        help="Path to smag_pilot_ledger.jsonl",
    )
    parser.add_argument(
        "--substrate",
        default="human:humanaios-ui",
        help="Substrate to evaluate (e.g. human:humanaios-ui)",
    )
    parser.add_argument(
        "--advisory-only",
        action="store_true",
        help="Always exit 0 after reporting state",
    )

    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    profile = load_profile(args.profile_path)
    substrate_profile = get_substrate_profile(profile, args.substrate)
    measurement_state = load_measurement_state(args.ledger_path, args.substrate)

    authority_valid = is_profile_ratified(profile)
    evidence_satisfied = minimum_evidence_state_satisfied(measurement_state, substrate_profile)
    boundary_exceeded = current_measured_state_exceeds_boundary(measurement_state, substrate_profile)
    review_required = calibration_review_required(profile, substrate_profile, measurement_state)

    print(f"✓ Loaded calibration profile: {profile.get('profile_id', 'UNKNOWN')}")
    print(f"✓ Substrate: {args.substrate}")
    print()
    print("📊 Calibration state predicates:")
    print(f"   PROFILE_AUTHORITY_VALID = {authority_valid}")
    print(f"   MEASUREMENT_CONTRACT_VALID = {measurement_state['contract_valid']}")
    print(f"   MINIMUM_EVIDENCE_STATE_SATISFIED = {evidence_satisfied}")
    print(f"   CURRENT_MEASURED_STATE_EXCEEDS_RATIFIED_BOUNDARY = {boundary_exceeded}")
    print()

    enforce_review_bar(substrate_profile)
    print()
    print("📈 Measurement summary:")
    print(f"   Rows for substrate: {measurement_state['row_count']}")
    print(f"   Failed rows: {measurement_state['failed_rows']}")
    print(f"   gap_rate: {measurement_state['gap_rate']:.2%}")
    print(f"   calibration_floor: {substrate_profile.get('calibration_floor', 0)}")
    print(f"   merge_pause_threshold: {substrate_profile.get('merge_pause_threshold', 0.25)}")
    if measurement_state["issues"]:
        print("   contract issues:")
        for issue in measurement_state["issues"]:
            print(f"   - {issue}")
    print()

    if review_required:
        print("⚠️  CALIBRATION_REVIEW_REQUIRED = True")
        print("   Explicit current predicates are satisfied for this substrate.")
    else:
        print("ℹ️  CALIBRATION_REVIEW_REQUIRED = False")
        print("   Merge authority remains unchanged on this workflow surface.")

    if args.advisory_only:
        print("ℹ️  Advisory-only mode: reported calibration state without merge blocking.")
        sys.exit(0)

    sys.exit(1 if review_required else 0)


if __name__ == "__main__":
    main()
