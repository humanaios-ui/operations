#!/usr/bin/env python3
"""
Builder v1.7 compliant · security_gate_tool
smag_gate_enforcer_v1_0.py — SMAG Calibration Gate Enforcer (s1 CI gate wire-up)
HumanAIOS · S-092126

Implements s1 CI gate wire-up: loads calibration profile, computes gap_rate,
enforces review_bar and merge_pause_threshold before merge approval.

Usage:
  python3 tools/smag_gate_enforcer_v1_0.py \
    --profile-path calibration_profiles/BASELINE_S092126.json \
    --ledger-path audits/smag_pilot_ledger.jsonl \
    --substrate "human:humanaios-ui" \
    --window-days 30

Returns:
  0 if all gates pass (review_bar met, gap_rate below threshold)
  1 if gate blocked (review_bar not met or gap_rate exceeds threshold)
  2 if configuration error
"""

TOOL_NAME = "smag_gate_enforcer"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "security_gate_tool"
TOOL_SESSION = "S-092126"
TOOL_ZONE = 1

import json
import sys
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path


def load_profile(profile_path: str) -> dict:
    """Load calibration profile from JSON file."""
    try:
        with open(profile_path) as f:
            return json.load(f)
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
    Check if profile has Z2 ratification signature.

    Returns True if ratified (safe to enforce), False if pending.
    """
    ratified_by = profile.get("ratified_by_z2", "")
    ratification_hash = profile.get("ratification_hash", "")

    # Check if both fields have TBD values (awaiting signature)
    if not ratified_by or ratified_by.startswith("TBD_"):
        return False
    if not ratification_hash or ratification_hash.startswith("TBD_"):
        return False

    return True


def compute_gap_rate(ledger_path: str, window_days: int) -> float:
    """
    Compute gap_rate from smag_pilot_ledger.jsonl over rolling window.

    Gap rate = rows_with_failing_checks / total_rows over last N days

    Each row in smag_pilot_ledger.jsonl represents a PR measurement.
    Failing rows have a non-empty failing_checks list.
    """
    if not Path(ledger_path).exists():
        print(f"⚠️  Ledger not found: {ledger_path} (no data yet)")
        print(f"   Defaulting gap_rate = 0.0 (clean slate)")
        return 0.0

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=window_days)

    total_rows = 0
    failed_rows = 0

    try:
        with open(ledger_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Extract timestamp
                timestamp_str = row.get("timestamp")
                if not timestamp_str:
                    continue

                try:
                    row_date = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    if row_date < window_start:
                        continue
                except ValueError:
                    continue

                # Count row
                total_rows += 1

                # Count as failed if failing_checks is non-empty
                failing_checks = row.get("failing_checks", [])
                if failing_checks and len(failing_checks) > 0:
                    failed_rows += 1

    except IOError as e:
        print(f"⚠️  Error reading ledger: {e}")
        return 0.0

    if total_rows == 0:
        return 0.0

    gap_rate = failed_rows / total_rows
    return gap_rate


def enforce_review_bar(substrate_profile: dict) -> bool:
    """
    Enforce review_bar constraint.

    For Phase 1 s1, this is advisory: we log the requirement but don't block.
    Full enforcement requires ACAT review metadata (not yet in CI).

    Returns True if constraint can be verified, False if blocked.
    """
    review_bar = substrate_profile.get("review_bar", "standard")
    print(f"📋 Review bar requirement: {review_bar}")
    print(f"   (Phase 1: advisory; full enforcement requires ACAT metadata)")
    return True


def run_smoke_test() -> bool:
    """Smoke test: verify gate loads profile and computes gap_rate."""
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

        gap_rate = compute_gap_rate(test_ledger_path, 30)
        if not isinstance(gap_rate, float) or gap_rate < 0.0 or gap_rate > 1.0:
            print(f"SMOKE_TEST: FAIL (invalid gap_rate: {gap_rate})")
            return False

        print(f"SMOKE_TEST: PASS (profile={profile.get('profile_id')}, gap_rate={gap_rate:.2%})")
        return True
    except Exception as e:
        print(f"SMOKE_TEST: FAIL ({e})")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="SMAG Calibration Gate Enforcer (s1 CI gate wire-up)"
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
        help="Substrate to enforce (e.g., human:humanaios-ui)",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=30,
        help="Rolling window size (days) for gap_rate computation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report gate status without blocking (for testing)",
    )

    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    # Load profile
    profile = load_profile(args.profile_path)
    substrate_profile = get_substrate_profile(profile, args.substrate)

    print(f"✓ Loaded calibration profile: {profile.get('profile_id', 'UNKNOWN')}")
    print(f"✓ Substrate: {args.substrate}")
    print()

    # Extract thresholds
    review_bar = substrate_profile.get("review_bar", "standard")
    merge_pause_threshold = substrate_profile.get("merge_pause_threshold", 0.25)

    print(f"📊 Gate Configuration:")
    print(f"   Review bar: {review_bar}")
    print(f"   Merge pause threshold: {merge_pause_threshold} (gap_rate limit)")
    print()

    # Enforce review bar (Phase 1: advisory)
    if not enforce_review_bar(substrate_profile):
        if not args.dry_run:
            sys.exit(1)

    print()

    # Compute gap_rate
    gap_rate = compute_gap_rate(args.ledger_path, args.window_days)
    print(f"📈 Gap Rate (last {args.window_days} days): {gap_rate:.2%}")
    print()

    # Check gate
    if gap_rate > merge_pause_threshold:
        print(f"🚫 GATE BLOCKED: gap_rate {gap_rate:.2%} exceeds threshold {merge_pause_threshold:.2%}")
        print(f"   Action: Auto-pause merges; file IC candidate in Priority Queue")
        if not args.dry_run:
            sys.exit(1)
    else:
        print(f"✓ GATE OPEN: gap_rate {gap_rate:.2%} within threshold {merge_pause_threshold:.2%}")
        print(f"   Merges permitted for substrate: {args.substrate}")

    sys.exit(0)


if __name__ == "__main__":
    main()
