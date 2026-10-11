#!/usr/bin/env python3
"""HumanAIOS Builder v1.7 compliant — issue #806 immutable tree inventory.

This tool does NOT invoke CodeRabbit and cannot authenticate review receipts.
This pilot rejects REVIEWED claims pending independent protected witness integration.
"""
TOOL_NAME = "coderabbit_coverage_inventory"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "audit_tool"
TOOL_ZONE = 1

import argparse
import json
import re
import sys
import subprocess
from pathlib import Path

STATES = {"PENDING", "REVIEWED", "NOT_APPLICABLE", "UNSUPPORTED", "SKIPPED_LIMIT", "FAILED"}
EXCLUDED_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".ico", ".woff", ".woff2", ".lock"}
SENSITIVE_NAMES = {".env", ".env.local", "id_rsa", "id_ed25519"}


def git(*args):
    return subprocess.check_output(["git", *args], timeout=120)


def inventory(commit):
    # Require an immutable commit object: tag/branch names alone are not durable.
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        raise ValueError("Pass a complete 40-character hexadecimal commit SHA")
    commit = commit.lower()
    resolved = git("rev-parse", "--verify", commit + "^{commit}").decode().strip()
    if commit != resolved:
        raise ValueError("Resolved commit differs from requested exact commit SHA")
    raw = git("ls-tree", "-rz", "--full-tree", resolved)
    items = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, name = record.split(b"\t", 1)
        mode, kind, blob = metadata.decode("ascii").split()
        path = name.decode("utf-8", errors="surrogateescape")
        suffix = Path(path).suffix.lower()
        if Path(path).name in SENSITIVE_NAMES:
            status, reason = "NOT_APPLICABLE", "sensitive: excluded from external review"
        elif kind == "commit":
            status, reason = "UNSUPPORTED", "submodule commit, not a local file"
        elif suffix in EXCLUDED_SUFFIXES:
            status, reason = "UNSUPPORTED", "binary/lockfile: separate review required"
        else:
            status, reason = "PENDING", "not submitted to an authenticated reviewer"
        items.append({"path": path, "path_bytes_hex": name.hex(), "mode": mode, "git_type": kind, "git_oid": blob,
                      "status": status, "reason": reason, "review_receipt": None})
    items.sort(key=lambda row: row["path"].encode("utf-8", errors="surrogateescape"))
    return {"schema": "coderabbit_coverage_v0", "commit": resolved, "files": items}


def validate(doc):
    rows = doc["files"]
    paths = [r["path"] for r in rows]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate file path")
    if paths != sorted(paths, key=lambda path: path.encode("utf-8", errors="surrogateescape")):
        raise ValueError("inventory not sorted")
    counts = {state: 0 for state in sorted(STATES)}
    for row in rows:
        state = row["status"]
        if state not in STATES:
            raise ValueError("unknown state: " + state)
        if state == "REVIEWED":
            # Hard fail closed: artifact assertions are not protected GitHub App attestation.
            raise ValueError("REVIEWED forbidden without independently verified CodeRabbit witness")
        if state != "PENDING" and not row.get("reason"):
            raise ValueError("nonpending item needs reason")
        counts[state] += 1
    if sum(counts.values()) != len(rows):
        raise ValueError("coverage total mismatch")
    # No authenticated review provider is wired into this pilot.
    authenticated = 0
    complete = bool(rows) and counts["PENDING"] == 0 and counts["FAILED"] == 0 and counts["SKIPPED_LIMIT"] == 0 and counts["REVIEWED"] == len(rows) and authenticated == len(rows)
    return {"tracked": len(rows), "counts": counts, "reviewed_authenticated": authenticated,
            "complete": complete, "review_verdict": "VERIFIED" if complete else "NOT_VERIFIED"}


def run_smoke_test():
    sample = {"files": [{"path": "example.py", "status": "PENDING", "reason": "pending"}]}
    return validate(sample)["review_verdict"] == "NOT_VERIFIED"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--commit", help="full immutable 40-character commit SHA")
    p.add_argument("--output")
    p.add_argument("--smoke-test", action="store_true")
    args = p.parse_args()
    if args.smoke_test:
        if not run_smoke_test():
            raise SystemExit(1)
        print("smoke-test OK")
        return
    if not args.commit or not args.output:
        p.error("--commit and --output are required unless --smoke-test is used")
    try:
        doc = inventory(args.commit)
        doc["summary"] = validate(doc)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError, OSError) as exc:
        print(f"Inventory failed closed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    Path(args.output).write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps(doc["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
