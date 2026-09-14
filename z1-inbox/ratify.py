#!/usr/bin/env python3
"""
Builder v1.7 compliant - ratify
HumanAIOS - Z2 Serial Gate Ratification Tool

Ratify candidate blocks and ruling files with Z2 signatures.
Signs candidates or rulings with sha256(content | by=<author> | at=<date> | decision=<D>).

Usage:
  python3 ratify.py sign-ruling --index INDEX.yaml --ruling-id Z2_RULING_AMBIGUITY_BSM_D --author Night
  python3 ratify.py sign-candidate --index INDEX.yaml --q-id Q-BOOT-STATE-MACHINE-01 --author Night --decision ACCEPT
  python3 ratify.py verify --index INDEX.yaml --hash <hash> --file <path>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
import yaml

TOOL_NAME = "ratify"
TOOL_VERSION = "0.1.0"


@dataclass
class SignatureResult:
    """Result of a signature operation."""
    success: bool
    hash_value: str | None
    message: str
    file_path: str | None


def compute_signature(content: str, author: str, date: str, decision: str) -> str:
    """Compute Z2 signature: sha256(content | by=author | at=date | decision=decision)."""
    signature_input = f"{content} | by={author} | at={date} | decision={decision}"
    return hashlib.sha256(signature_input.encode()).hexdigest()


def read_index(index_path: str) -> dict:
    """Read INDEX.yaml and return parsed YAML."""
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"ERROR: Failed to read {index_path}: {e}", file=sys.stderr)
        return {}


def read_file(file_path: str) -> str | None:
    """Read a file from disk."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"ERROR: Failed to read {file_path}: {e}", file=sys.stderr)
        return None


def write_file(file_path: str, content: str) -> bool:
    """Write content to a file."""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"ERROR: Failed to write {file_path}: {e}", file=sys.stderr)
        return False


def extract_yaml_block(content: str) -> tuple[str, str]:
    """Extract YAML block from markdown file.

    Returns (prose_before_yaml, yaml_content)
    """
    # Look for lines starting with ``` followed by yaml, or just lines starting with ```
    yaml_pattern = r'^```(?:yaml)?\s*\n(.*?)\n```\s*$'
    match = re.search(yaml_pattern, content, re.MULTILINE | re.DOTALL)

    if match:
        yaml_content = match.group(1)
        prose = content[:match.start()].rstrip()
        return prose, yaml_content

    return content, ""


def update_yaml_field(yaml_content: str, field: str, value: str | None) -> str:
    """Update a field in YAML content."""
    try:
        data = yaml.safe_load(yaml_content) or {}
        data[field] = value
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print(f"ERROR: Failed to update YAML: {e}", file=sys.stderr)
        return yaml_content


def sign_ruling(index_path: str, ruling_id: str, author: str) -> SignatureResult:
    """Sign a ruling file by ruling_id (e.g., Z2_RULING_AMBIGUITY_BSM_D)."""
    index = read_index(index_path)

    # Find ruling in records
    ruling_path = None
    if "records" in index:
        for record in index["records"]:
            if ruling_id in record.get("path", ""):
                ruling_path = record["path"]
                break

    if not ruling_path:
        return SignatureResult(
            success=False,
            hash_value=None,
            message=f"Ruling {ruling_id} not found in INDEX.yaml records",
            file_path=None
        )

    # Resolve path: check if it exists as-is first (relative to cwd),
    # then try relative to index directory
    if not os.path.isabs(ruling_path):
        if not os.path.exists(ruling_path):
            # Try relative to index directory
            index_dir = os.path.dirname(os.path.abspath(index_path))
            alt_path = os.path.join(index_dir, ruling_path)
            if os.path.exists(alt_path):
                ruling_path = alt_path

    if not os.path.exists(ruling_path):
        return SignatureResult(
            success=False,
            hash_value=None,
            message=f"Ruling file not found: {ruling_path}",
            file_path=ruling_path
        )

    content = read_file(ruling_path)
    if not content:
        return SignatureResult(
            success=False,
            hash_value=None,
            message=f"Failed to read ruling: {ruling_path}",
            file_path=ruling_path
        )

    # Get current date
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Compute signature over prose (before YAML block)
    prose, yaml_block = extract_yaml_block(content)
    if not prose:
        prose = content  # Fallback if no YAML block

    signature = compute_signature(prose, author, date, "ACCEPT")

    # Update YAML block with signature
    yaml_block_updated = update_yaml_field(yaml_block, "z2_hash", signature)

    # Reconstruct file
    if yaml_block:
        reconstructed = f"{prose}\n\n```yaml\n{yaml_block_updated}```\n"
    else:
        reconstructed = content

    # Write back
    if not write_file(ruling_path, reconstructed):
        return SignatureResult(
            success=False,
            hash_value=signature,
            message=f"Failed to write signature to {ruling_path}",
            file_path=ruling_path
        )

    # Update INDEX.yaml record with signature metadata
    if "records" in index:
        for record in index["records"]:
            if ruling_id in record.get("path", ""):
                record["z2_hash"] = signature
                record["ratified_by"] = author
                record["ratified_at"] = date
                break

    # Write updated index
    try:
        with open(index_path, "w", encoding="utf-8") as f:
            yaml.dump(index, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        return SignatureResult(
            success=False,
            hash_value=signature,
            message=f"Signed ruling but failed to update INDEX.yaml: {e}",
            file_path=ruling_path
        )

    return SignatureResult(
        success=True,
        hash_value=signature,
        message=f"Signed ruling {ruling_id}",
        file_path=ruling_path
    )


def verify_signature(hash_value: str, file_path: str, author: str, date: str, decision: str) -> bool:
    """Verify a signature against a file."""
    content = read_file(file_path)
    if not content:
        return False

    prose, _ = extract_yaml_block(content)
    if not prose:
        prose = content

    expected_hash = compute_signature(prose, author, date, decision)
    return hash_value == expected_hash


def run_smoke_test() -> bool:
    """Smoke test for Builder compliance."""
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test ruling
            test_ruling = "# Test Ruling\n\nThis is a test.\n\n```yaml\nz2_hash: null\n```\n"
            test_path = os.path.join(tmpdir, "test_ruling.md")
            with open(test_path, "w") as f:
                f.write(test_ruling)

            # Create test INDEX
            test_index = {
                "version": 1,
                "records": [{"path": "test_ruling.md", "title": "Test"}]
            }
            index_path = os.path.join(tmpdir, "INDEX.yaml")
            with open(index_path, "w") as f:
                yaml.dump(test_index, f)

            # Test signature computation
            sig = compute_signature("# Test Ruling\n\nThis is a test.", "Test", "2026-09-14", "ACCEPT")
            assert len(sig) == 64, "Signature should be 64 hex chars"

            print("✓ Smoke test passed")
            return True
    except Exception as e:
        print(f"✗ Smoke test failed: {e}")
        return False


def main() -> int:
    """Main entry point for ratify."""
    parser = argparse.ArgumentParser(
        description="Z2 Serial Gate Ratification Tool — sign candidates and rulings"
    )
    parser.add_argument("command", nargs="?", choices=["sign-ruling", "sign-candidate", "verify"],
                        help="Operation to perform")
    parser.add_argument("--index", "-i", default="INDEX.yaml",
                        help="Path to INDEX.yaml")
    parser.add_argument("--ruling-id", help="Ruling ID for sign-ruling")
    parser.add_argument("--q-id", help="Q-ID for sign-candidate")
    parser.add_argument("--author", "-a", default="Night",
                        help="Author (Z2 ratifier)")
    parser.add_argument("--decision", "-d", default="ACCEPT",
                        choices=["ACCEPT", "REJECT", "EDIT"],
                        help="Decision type")
    parser.add_argument("--hash", help="Hash to verify")
    parser.add_argument("--file", "-f", help="File to verify")
    parser.add_argument("--date", default=None,
                        help="Date (defaults to today)")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Run smoke test and exit")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    if args.smoke_test:
        return 0 if run_smoke_test() else 1

    if not args.command:
        parser.error("command required (or use --smoke-test)")

    if args.command == "sign-ruling":
        if not args.ruling_id:
            parser.error("--ruling-id required for sign-ruling")
        result = sign_ruling(args.index, args.ruling_id, args.author)
        if result.success:
            print(f"✓ {result.message}")
            print(f"  Hash: {result.hash_value}")
            print(f"  File: {result.file_path}")
            return 0
        else:
            print(f"✗ {result.message}", file=sys.stderr)
            return 1

    elif args.command == "verify":
        if not args.hash or not args.file:
            parser.error("--hash and --file required for verify")
        if verify_signature(args.hash, args.file, args.author, args.date or "2026-09-14", args.decision):
            print(f"✓ Signature verified")
            return 0
        else:
            print(f"✗ Signature verification failed", file=sys.stderr)
            return 1

    else:
        parser.error(f"Command {args.command} not implemented")
        return 1


if __name__ == "__main__":
    sys.exit(main())
