#!/usr/bin/env python3
"""
Lint canonical skill entry points to detect substrate drift.

Ensures that .agents/skills/ and .claude/skills/ stubs do not diverge
from the canonical implementation in tools/skills/.

Exit 0 if all stubs conform; exit 1 if drift detected.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_RNOLA = ROOT / "tools" / "skills" / "repository_native_operator_learning" / "SKILL.md"
SUBSTRATE_PATHS = [
    ROOT / ".agents" / "skills" / "repository-native-operator-learning" / "SKILL.md",
    ROOT / ".claude" / "skills" / "repository-native-operator-learning" / "SKILL.md",
]

CANONICAL_HEADER = "# SKILL: repository_native_operator_learning"
CANONICAL_BOUNDARY = "Key boundary: RNOLA is advisory Zone 1 learning/calibration only."


def check_canonical_exists():
    """Verify canonical skill exists and has expected header."""
    if not CANONICAL_RNOLA.exists():
        print(f"ERROR: Canonical skill not found: {CANONICAL_RNOLA}")
        return False

    content = CANONICAL_RNOLA.read_text(encoding="utf-8")
    if CANONICAL_HEADER not in content:
        print(f"ERROR: Canonical skill missing expected header: {CANONICAL_HEADER}")
        return False

    if CANONICAL_BOUNDARY not in content:
        print(f"ERROR: Canonical skill missing boundary statement: {CANONICAL_BOUNDARY}")
        return False

    return True


def check_substrate_stubs(strict=False):
    """Verify substrate stubs are thin redirects, not divergent implementations."""
    all_good = True
    canonical_content = CANONICAL_RNOLA.read_text(encoding="utf-8")

    for stub_path in SUBSTRATE_PATHS:
        if not stub_path.exists():
            print(f"ERROR: Substrate stub not found (required): {stub_path}")
            all_good = False
            continue

        stub_content = stub_path.read_text(encoding="utf-8")

        # Stub must reference canonical; must not redefine rules
        if "tools/skills/repository_native_operator_learning/SKILL.md" not in stub_content:
            print(f"ERROR: Substrate stub does not reference canonical: {stub_path}")
            all_good = False

        # Stub must have exact boundary statement
        if CANONICAL_BOUNDARY not in stub_content:
            print(f"ERROR: Substrate stub missing exact boundary statement: {stub_path}")
            print(f"       Expected: {CANONICAL_BOUNDARY}")
            all_good = False

        # Stub must not redefine sections beyond the redirect
        lines = stub_content.strip().split("\n")
        if len(lines) > 15:  # Stubs should be thin — ~11 lines
            print(f"ERROR: Substrate stub is longer than expected ({len(lines)} lines): {stub_path}")
            print(f"       Stubs should be thin redirects; detected divergence.")
            all_good = False

    return all_good


def main():
    """Run all linting checks."""
    parser = argparse.ArgumentParser(
        description="Lint canonical skill entry points for substrate drift."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=str(ROOT),
        help="Repository root directory",
    )
    parser.add_argument(
        "--substrate-dirs",
        type=str,
        nargs="*",
        help="Additional substrate directories to check",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings as well as errors",
    )

    args = parser.parse_args()

    print("Linting canonical skill entry points...")

    if not check_canonical_exists():
        sys.exit(1)

    if not check_substrate_stubs(strict=args.strict):
        sys.exit(1)

    print("✓ All canonical skill entry points conform.")
    sys.exit(0)


if __name__ == "__main__":
    main()
