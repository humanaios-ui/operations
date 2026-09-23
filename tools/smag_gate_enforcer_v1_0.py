#!/usr/bin/env python3
"""
SMAG Calibration Gate Enforcer v1.0

Implements s1 CI gate wire-up: loads calibration profile, computes gap_rate,
enforces review_bar and merge_pause_threshold before merge approval.

Profile ratification validation: Gate operates in two modes:
- ENFORCING: Profile has Z2 ratification hash (blocks on threshold)
- ADVISORY: Profile pending ratification (logs status but permits merges)

Usage:
  python3 tools/smag_gate_enforcer_v1_0.py \
    --profile-path calibration_profiles/BASELINE_S092126.json \
    --ledger-path ledgers/NF_LEDGER.jsonl \
    --substrate "human:humanaios-ui" \
    --window-days 30

Returns:
  0 if gate permits merges (ratified + threshold OK, or pending ratification)
  1 if gate blocks (ratified + threshold exceeded)
  2 if configuration error (missing profile, invalid substrate, etc.)
"""

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


def get_substrate_profile(profile: dict, substrate: str) -> dict:
    """Extract substrate-specific profile from full profile."""
    substrates = profile.get("substrates", {})
    if substrate not in substrates:
        print(f"❌ Substrate '{substrate}' not found in calibration profile")
        print(f"   Available substrates: {list(substrates.keys())}")
        sys.exit(2)
    return substrates[substrate]


def compute_gap_rate(ledger_path: str, window_days: int) -> float:
    """
    Compute gap_rate from NF_LEDGER.jsonl over rolling window.

    Gap rate = failed_checks / total_checks over last N days

    Counts VERDICT events marked as failing_check: true.
    Handles malformed timestamps gracefully (skips unparseable events).
    """
    if not Path(ledger_path).exists():
        print(f"⚠️  Ledger not found: {ledger_path} (no data yet)")
        print(f"   Defaulting gap_rate = 0.0 (clean slate)")
        return 0.0

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=window_days)

    total_checks = 0
    failed_checks = 0

    try:
        with open(ledger_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Filter by type (only count VERDICT events)
                if event.get("type") != "VERDICT":
                    continue

                event_at = event.get("at")
                if not event_at:
                    continue

                # Parse timestamp and filter by window
                try:
                    event_date = datetime.fromisoformat(event_at.replace("Z", "+00:00"))
                    if event_date < window_start:
                        continue
                except (ValueError, TypeError):
                    continue

                # Count check
                total_checks += 1

                # Count as failed if marked failing_check: true
                if event.get("failing_check"):
                    failed_checks += 1

    except IOError as e:
        print(f"⚠️  Error reading ledger: {e}")
        return 0.0

    if total_checks == 0:
        return 0.0

    gap_rate = failed_checks / total_checks
    return gap_rate


def enforce_review_bar(substrate_profile: dict) -> bool:
    """
    Enforce review_bar constraint.

    For Phase 1 s1, this is advisory: we log the requirement but don't block.
    Full enforcement requires ACAT review metadata (not yet in CI).

    Returns True (constraint logged, never blocks in Phase 1).
    """
    review_bar = substrate_profile.get("review_bar", "standard")
    print(f"📋 Review bar requirement: {review_bar}")
    print(f"   (Phase 1: advisory; full enforcement requires ACAT metadata)")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="SMAG Calibration Gate Enforcer (s1 CI gate wire-up)"
    )
    parser.add_argument(
        "--profile-path",
        default="calibration_profiles/BASELINE_S092126.json",
        help="Path to calibration profile JSON",
    )
    parser.add_argument(
        "--ledger-path",
        default="ledgers/NF_LEDGER.jsonl",
        help="Path to NF_LEDGER.jsonl",
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

    # Load profile
    profile = load_profile(args.profile_path)
    substrate_profile = get_substrate_profile(profile, args.substrate)

    print(f"✓ Loaded calibration profile: {profile.get('profile_id', 'UNKNOWN')}")
    print(f"✓ Substrate: {args.substrate}")
    print()

    # Check ratification status
    is_ratified = is_profile_ratified(profile)
    ratified_by = profile.get("ratified_by_z2", "PENDING")
    ratification_hash = profile.get("ratification_hash", "TBD_AWAITING_Z2_SIGNATURE")

    if is_ratified:
        print(f"🔐 Profile RATIFIED by Z2")
        print(f"   Ratifier: {ratified_by}")
        print(f"   Hash: {ratification_hash[:16]}...")
        print(f"   Mode: ENFORCING (gate will block on threshold)")
    else:
        print(f"⏳ Profile AWAITING Z2 RATIFICATION")
        print(f"   Status: {ratified_by}")
        print(f"   Mode: ADVISORY (gate will not block merges)")
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

    # Check gate (only enforces if ratified)
    if gap_rate > merge_pause_threshold:
        if is_ratified:
            print(f"🚫 GATE BLOCKED: gap_rate {gap_rate:.2%} exceeds threshold {merge_pause_threshold:.2%}")
            print(f"   Action: Auto-pause merges; file IC candidate in Priority Queue")
            if not args.dry_run:
                sys.exit(1)
        else:
            print(f"⚠️  Gap rate {gap_rate:.2%} exceeds threshold {merge_pause_threshold:.2%}")
            print(f"   Status: ADVISORY (profile not yet ratified)")
            print(f"   Once ratified: merges will auto-pause at this threshold")
    else:
        print(f"✓ GATE OPEN: gap_rate {gap_rate:.2%} within threshold {merge_pause_threshold:.2%}")
        print(f"   Merges permitted for substrate: {args.substrate}")

    sys.exit(0)


if __name__ == "__main__":
    main()
