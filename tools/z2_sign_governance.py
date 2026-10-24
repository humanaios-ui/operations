#!/usr/bin/env python3
"""
Z2 Governance Signature Generator
Builder v1.7 compliant - meta_governance_tool
HumanAIOS - Q-Z2-PRE-SIGNATURE-ENFORCEMENT-01

Generates cryptographic signatures for governance-layer changes.
Used by Z2 (Night) to ratify governance modifications before merge.

Usage:
  python3 tools/z2_sign_governance.py <file_path> [timestamp]
  python3 tools/z2_sign_governance.py --smoke-test

Example:
  python3 tools/z2_sign_governance.py CLAUDE.md
  # Output: Z2-SIGN: a1b2c3d4e5f6... (64-char SHA256)

Then paste into PR commit message or description:
  Fix constitution checker | Z2-SIGN: a1b2c3d4e5f6...
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

TOOL_NAME = "z2_sign_governance"
TOOL_VERSION = "1.0.0"


class SpecLoadFailed(Exception):
    """Exception raised when signature specification cannot be loaded."""
    pass


def generate_z2_signature(file_content: str, timestamp: str = None) -> str:
    """
    Generate Z2 content fingerprint for governance file.

    ⚠️  NOT CRYPTOGRAPHIC AUTHENTICATION
    This generates a deterministic hash of the file content for audit trails.
    Real Z2 signature requires asymmetric verification against Z2's public key.

    This fingerprint prevents accidental file mutations during review.
    It does NOT prevent intentional forgery.

    Args:
        file_content: Full content of the file being changed
        timestamp: Optional timestamp (default: now in UTC ISO format)

    Returns:
        64-character SHA256 hex hash (content fingerprint, not signature)
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    # Generate deterministic content fingerprint
    fingerprint_input = f"{file_content}"
    fingerprint = hashlib.sha256(fingerprint_input.encode()).hexdigest()
    return fingerprint


def run_smoke_test() -> bool:
    """Smoke test: verify signature generation works."""
    try:
        test_content = "Test governance file content"
        test_timestamp = "2026-10-22T22:00:00Z"
        sig = generate_z2_signature(test_content, test_timestamp)

        # Verify signature is 64-char hex string
        assert len(sig) == 64, f"Expected 64-char signature, got {len(sig)}"
        assert all(c in '0123456789abcdef' for c in sig), "Invalid hex characters"

        # Verify determinism: same input → same output
        sig2 = generate_z2_signature(test_content, test_timestamp)
        assert sig == sig2, "Signature not deterministic"

        # Verify signature changes with different content
        sig3 = generate_z2_signature("Different content", test_timestamp)
        assert sig != sig3, "Signature should change with content"

        print(f"✓ {TOOL_NAME} v{TOOL_VERSION} smoke test PASSED")
        return True
    except AssertionError as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ Smoke test ERROR: {e}")
        return False


def write_report(filepath: str, results: dict) -> None:
    """Write signature generation report to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Z2 Governance Signature Generator — Sign governance files before merge"
    )
    parser.add_argument("file_path", nargs='?', help="Path to governance file to sign")
    parser.add_argument("timestamp", nargs='?', help="Optional timestamp (ISO format)")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test")

    args = parser.parse_args()

    if args.smoke_test:
        success = run_smoke_test()
        sys.exit(0 if success else 1)

    if not args.file_path:
        print("Z2 Governance Signature Generator")
        print("=" * 50)
        print("Usage: python3 z2_sign_governance.py <file_path> [timestamp]")
        print("       python3 z2_sign_governance.py --smoke-test")
        print()
        print("Examples:")
        print("  python3 tools/z2_sign_governance.py CLAUDE.md")
        print("  python3 tools/z2_sign_governance.py constitution_checker.py 2026-10-22T22:30:00Z")
        print()
        print("Output: Z2-SIGN: <64-char-hash>")
        print("Paste into commit message or PR description before merge.")
        sys.exit(1)

    file_path = args.file_path
    timestamp = args.timestamp

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        sys.exit(1)

    sig = generate_z2_signature(content, timestamp)

    print(f"File: {file_path}")
    if timestamp:
        print(f"Timestamp: {timestamp}")
    else:
        print(f"Timestamp: {datetime.utcnow().isoformat()} (UTC)")
    print()
    print(f"Z2-SIGN: {sig}")
    print()
    print("Paste this into your commit message or PR description:")
    print(f"| Z2-SIGN: {sig}")


if __name__ == "__main__":
    main()
