#!/usr/bin/env python3
"""Strict, dependency-free validator for HARC v0.2 replication receipts.

The JSON Schema remains the declarative contract. This runtime validator mirrors
its safety-relevant constraints so validation does not depend on an optional
third-party package being installed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED = {
    "capsule_id", "capsule_version", "capsule_sha256", "substrate_id",
    "replication_status", "implemented_components", "tests", "test_evidence",
    "divergences", "limitations",
}
ALLOWED = REQUIRED | {
    "environment", "target", "warrant", "prior_review_exposure", "return_capability"
}
STATUSES = {"REPLICATED", "PARTIAL", "FAILED"}
TEST_STATUSES = {"PASS", "FAIL", "NOT_RUN"}
EXPOSURES = {"NONE", "PARTIAL", "FULL"}
RETURN_CAPABILITIES = {"INLINE_EMAIL", "RETURN_BLOCK_ONLY", "INLINE_ONLY", "OTHER"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(data: Any, *, expected_capsule_sha256: str | None = None, expected_target_commit: str | None = None) -> list[str]:
    if not isinstance(data, dict):
        return ["invalid:root:not_object"]

    errors: list[str] = []
    keys = set(data)
    errors.extend(f"missing:{key}" for key in sorted(REQUIRED - keys))
    errors.extend(f"unexpected:{key}" for key in sorted(keys - ALLOWED))

    for key in ("capsule_id", "capsule_version", "substrate_id"):
        if key in data and not _nonempty_string(data[key]):
            errors.append(f"invalid:{key}:string")

    capsule_hash = data.get("capsule_sha256")
    if not isinstance(capsule_hash, str) or not SHA256_RE.fullmatch(capsule_hash):
        errors.append("invalid:capsule_sha256")
    elif expected_capsule_sha256 is not None and capsule_hash != expected_capsule_sha256:
        errors.append("mismatch:capsule_sha256")

    status = data.get("replication_status")
    if status not in STATUSES:
        errors.append("invalid:replication_status")

    components = data.get("implemented_components")
    if not isinstance(components, list) or any(not _nonempty_string(x) for x in components):
        errors.append("invalid:implemented_components")
    elif status in {"REPLICATED", "PARTIAL"} and not components:
        errors.append("empty:implemented_components")

    tests = data.get("tests")
    if not isinstance(tests, dict):
        errors.append("invalid:tests")
        passed = failed = not_run = None
    else:
        expected = {"passed", "failed", "not_run"}
        if set(tests) != expected:
            errors.append("invalid:tests:keys")
        counts = {}
        for key in sorted(expected):
            value = tests.get(key)
            if not _is_int(value) or value < 0:
                errors.append(f"invalid:tests.{key}")
            else:
                counts[key] = value
        passed = counts.get("passed")
        failed = counts.get("failed")
        not_run = counts.get("not_run")

    evidence = data.get("test_evidence")
    status_counts = {"PASS": 0, "FAIL": 0, "NOT_RUN": 0}
    if not isinstance(evidence, list):
        errors.append("invalid:test_evidence")
    else:
        if status in {"REPLICATED", "PARTIAL"} and not evidence:
            errors.append("empty:test_evidence")
        seen_names: set[str] = set()
        for i, item in enumerate(evidence):
            prefix = f"test_evidence[{i}]"
            if not isinstance(item, dict):
                errors.append(f"invalid:{prefix}:object")
                continue
            if set(item) != {"name", "status", "evidence_ref"}:
                errors.append(f"invalid:{prefix}:keys")
            name = item.get("name")
            if not _nonempty_string(name):
                errors.append(f"invalid:{prefix}.name")
            elif name in seen_names:
                errors.append(f"duplicate:{prefix}.name")
            else:
                seen_names.add(name)
            item_status = item.get("status")
            if item_status not in TEST_STATUSES:
                errors.append(f"invalid:{prefix}.status")
            else:
                status_counts[item_status] += 1
            if not _nonempty_string(item.get("evidence_ref")):
                errors.append(f"invalid:{prefix}.evidence_ref")

    if all(_is_int(x) for x in (passed, failed, not_run)) and isinstance(evidence, list):
        if passed != status_counts["PASS"] or failed != status_counts["FAIL"] or not_run != status_counts["NOT_RUN"]:
            errors.append("mismatch:test_counts_vs_evidence")

    divergences = data.get("divergences")
    if not isinstance(divergences, list):
        errors.append("invalid:divergences")
    else:
        for i, item in enumerate(divergences):
            if not isinstance(item, dict) or set(item) != {"component", "reason"}:
                errors.append(f"invalid:divergences[{i}]")
            elif not _nonempty_string(item.get("component")) or not _nonempty_string(item.get("reason")):
                errors.append(f"invalid:divergences[{i}]:strings")

    limitations = data.get("limitations")
    if not isinstance(limitations, list) or any(not _nonempty_string(x) for x in limitations):
        errors.append("invalid:limitations")

    if "prior_review_exposure" in data and data["prior_review_exposure"] not in EXPOSURES:
        errors.append("invalid:prior_review_exposure")
    if "return_capability" in data and data["return_capability"] not in RETURN_CAPABILITIES:
        errors.append("invalid:return_capability")

    target = data.get("target")
    if target is not None:
        if not isinstance(target, dict):
            errors.append("invalid:target")
        else:
            allowed_target = {"repository", "commit_sha", "component"}
            if set(target) - allowed_target:
                errors.append("invalid:target:keys")
            if not _nonempty_string(target.get("repository")):
                errors.append("invalid:target.repository")
            commit_sha = target.get("commit_sha")
            if not isinstance(commit_sha, str) or not GIT_SHA_RE.fullmatch(commit_sha):
                errors.append("invalid:target.commit_sha")
            if "component" in target and not _nonempty_string(target.get("component")):
                errors.append("invalid:target.component")
            if expected_target_commit is not None and commit_sha != expected_target_commit:
                errors.append("mismatch:target.commit_sha")
    elif expected_target_commit is not None:
        errors.append("missing:target_for_expected_commit")

    if status == "REPLICATED":
        if _is_int(failed) and failed != 0:
            errors.append("replicated_with_failed_tests")
        if _is_int(not_run) and not_run != 0:
            errors.append("replicated_with_unrun_tests")
        if _is_int(passed) and passed <= 0:
            errors.append("replicated_without_passed_tests")
        if isinstance(divergences, list) and divergences:
            errors.append("replicated_with_divergences")

    return errors


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("receipt", type=Path)
    ap.add_argument("--capsule", type=Path, help="exact distributed capsule artifact to hash and bind")
    ap.add_argument("--target-commit", help="exact 40-hex target commit expected by the trial")
    args = ap.parse_args()
    if args.target_commit and not GIT_SHA_RE.fullmatch(args.target_commit):
        print("--target-commit must be 40 lowercase hex characters", file=sys.stderr)
        return 2
    data = json.loads(args.receipt.read_text(encoding="utf-8"))
    expected_capsule = sha256_file(args.capsule) if args.capsule else None
    errors = validate(data, expected_capsule_sha256=expected_capsule, expected_target_commit=args.target_commit)
    print(json.dumps({"valid": not errors, "errors": errors, "expected_capsule_sha256": expected_capsule}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
