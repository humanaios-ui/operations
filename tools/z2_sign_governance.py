#!/usr/bin/env python3
"""
Z2 Governance Signature Generator

Generates cryptographic signatures for governance-layer changes.
Used by Z2 (Night) to ratify governance modifications before merge.

Usage:
  python3 tools/z2_sign_governance.py <file_path> [timestamp]

Example:
  python3 tools/z2_sign_governance.py CLAUDE.md
  # Output: Z2-SIGN: a1b2c3d4e5f6... (64-char SHA256)

Then paste into PR commit message or description:
  Fix constitution checker | Z2-SIGN: a1b2c3d4e5f6...
"""

import hashlib
import sys
from datetime import datetime
from pathlib import Path


def generate_z2_signature(file_content: str, timestamp: str = None) -> str:
    """
    Generate Z2 signature for governance file.

    Args:
        file_content: Full content of the file being changed
        timestamp: Optional timestamp (default: now in UTC ISO format)

    Returns:
        64-character SHA256 hex signature
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    signature_input = f"{file_content} | by=Night | {timestamp}"
    signature = hashlib.sha256(signature_input.encode()).hexdigest()
    return signature


def main():
    if len(sys.argv) < 2:
        print("Z2 Governance Signature Generator")
        print("=" * 50)
        print("Usage: python3 z2_sign_governance.py <file_path> [timestamp]")
        print()
        print("Examples:")
        print("  python3 tools/z2_sign_governance.py CLAUDE.md")
        print("  python3 tools/z2_sign_governance.py constitution_checker.py 2026-10-22T22:30:00Z")
        print()
        print("Output: Z2-SIGN: <64-char-hash>")
        print("Paste into commit message or PR description before merge.")
        sys.exit(1)

    file_path = sys.argv[1]
    timestamp = sys.argv[2] if len(sys.argv) > 2 else None

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
