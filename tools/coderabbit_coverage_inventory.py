#!/usr/bin/env python3
"""Issue #806: immutable tree inventory and conservative review coverage accounting.

This tool does NOT invoke CodeRabbit and cannot authenticate review receipts.
REVIEWED remains impossible until an independent protected witness adapter exists.
"""
import argparse
import json
import subprocess
from pathlib import Path

STATES = {"PENDING", "REVIEWED", "NOT_APPLICABLE", "UNSUPPORTED", "SKIPPED_LIMIT", "FAILED"}
EXCLUDED_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".ico", ".woff", ".woff2", ".lock"}
SENSITIVE_NAMES = {".env", ".env.local", "id_rsa", "id_ed25519"}


def git(*args):
    return subprocess.check_output(["git", *args])


def inventory(commit):
    # Require an immutable commit object: tag/branch names alone are not durable.
    resolved = git("rev-parse", "--verify", commit + "^{commit}").decode().strip()
    if commit != resolved:
        raise ValueError("Pass the complete 40-character commit SHA, not a moving ref")
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
        items.append({"path": path, "mode": mode, "git_type": kind, "git_oid": blob,
                      "status": status, "reason": reason, "review_receipt": None})
    return {"schema": "coderabbit_coverage_v0", "commit": resolved, "files": items}


def validate(doc):
    rows = doc["files"]
    paths = [r["path"] for r in rows]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate file path")
    if paths != sorted(paths):
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
    return {"tracked": len(rows), "counts": counts, "reviewed_authenticated": 0,
            "complete": False, "review_verdict": "NOT_VERIFIED"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--commit", required=True, help="full immutable 40-character commit SHA")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    doc = inventory(args.commit)
    doc["summary"] = validate(doc)
    Path(args.output).write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n")
    print(json.dumps(doc["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
