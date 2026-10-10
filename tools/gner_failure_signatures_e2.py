"""GNER-E2: conservative cross-run failure signature candidates (no authority).

Input must be independently established from GitHub workflow/job logs. This
offline pure function does not certify the authenticity of supplied evidence.

Builder v1.7 compliant · analysis_tool
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict

TOOL_NAME = "gner_failure_signatures_e2"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "analysis_tool"
TOOL_ZONE = 1

ALLOWED_REPO = "humanaios-ui/operations"
CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,80}$")
PATH = re.compile(r"^[a-zA-Z0-9_./-]{1,180}$")
SHA = re.compile(r"^[a-f0-9]{40}$")
# Deliberately avoid parsing arbitrary logs: caller extracts a bounded known diagnostic.
def signature(failure: dict) -> str | None:
    if not isinstance(failure, dict) or set(failure) != {"code", "test_path", "test_name"}:
        return None
    code, path, test = (failure.get(k) for k in ("code", "test_path", "test_name"))
    if not (isinstance(code, str) and CODE.fullmatch(code)
            and isinstance(path, str) and PATH.fullmatch(path)
            and isinstance(test, str) and PATH.fullmatch(test)):
        return None
    # A named diagnostic is stable across run ids, while avoiding free-text/log secrets.
    return hashlib.sha256((code + "\0" + path + "\0" + test).encode()).hexdigest()


def correlate(records: list) -> dict:
    if not isinstance(records, list) or len(records) > 100:
        raise ValueError("bounded record list required")
    groups: dict[str, list[dict]] = defaultdict(list)
    rejected = 0
    for record in records:
        if not isinstance(record, dict):
            rejected += 1
            continue
        if (record.get("repository") != ALLOWED_REPO
            or record.get("verification_state") != "CANONICAL_VERIFIED"
            or record.get("conclusion") != "failure"
            or type(record.get("run_id")) is not int or record["run_id"] <= 0
            or not isinstance(record.get("head_sha"), str)
            or not SHA.fullmatch(record["head_sha"])
            or not isinstance(record.get("workflow"), str)
            or not 0 < len(record["workflow"]) < 100):
            rejected += 1
            continue
        key = signature(record.get("failure"))
        if key is None:
            rejected += 1
            continue
        groups[key].append(record)
    output = []
    for key, group in sorted(groups.items()):
        distinct = {(r["run_id"], r["head_sha"]) for r in group}
        if len(distinct) < 2:
            continue
        ordered = sorted(distinct)
        output.append({"signature_sha256": key,
                       "diagnostic_code": group[0]["failure"]["code"],
                       "test_path": group[0]["failure"]["test_path"],
                       "test_name": group[0]["failure"]["test_name"],
                       "run_ids": sorted({r for r, _ in ordered}),
                       "distinct_run_head_pairs": len(ordered),
                       "state": "SHARED_FAILURE_SIGNATURE_CANDIDATE",
                       "root_cause_verified": False})
    return {"schema": "GNER-E2-v0.1", "groups": output, "rejected": rejected,
            "authority": "NONE", "execution": "DISABLED",
            "evidence_warning": "Caller-supplied metadata is not authenticated by this function. Matching diagnostic signatures are not proof of a shared root cause."}


def run_smoke_test() -> bool:
    """Smoke test for Builder v1.7 compliance."""
    tests = []

    try:
        result = signature({"code": "TEST_ERROR", "test_path": "tests/test_foo.py", "test_name": "test_bar"})
        tests.append(("signature_valid", result is not None and len(result) == 64))
    except Exception as e:
        tests.append(("signature_valid", False))

    try:
        result = signature({"code": "BAD", "test_path": "", "test_name": ""})
        tests.append(("signature_invalid", result is None))
    except Exception as e:
        tests.append(("signature_invalid", False))

    try:
        records = [
            {"repository": "humanaios-ui/operations", "verification_state": "CANONICAL_VERIFIED", "conclusion": "failure", "run_id": 1, "head_sha": "a" * 40, "workflow": "quality-baseline", "failure": {"code": "TEST_FAIL", "test_path": "tests/t.py", "test_name": "test_x"}},
            {"repository": "humanaios-ui/operations", "verification_state": "CANONICAL_VERIFIED", "conclusion": "failure", "run_id": 2, "head_sha": "b" * 40, "workflow": "quality-baseline", "failure": {"code": "TEST_FAIL", "test_path": "tests/t.py", "test_name": "test_x"}},
        ]
        result = correlate(records)
        tests.append(("correlate_valid", result["schema"] == "GNER-E2-v0.1" and len(result["groups"]) > 0))
    except Exception as e:
        tests.append(("correlate_valid", False))

    try:
        result = correlate([])
        tests.append(("correlate_empty", result["rejected"] == 0 and len(result["groups"]) == 0))
    except Exception as e:
        tests.append(("correlate_empty", False))

    passed = sum(1 for _, p in tests if p)
    print(f"{TOOL_NAME} smoke test: {passed}/{len(tests)} checks")
    for name, passed_test in tests:
        if not passed_test:
            print(f"  ::error::{name}")
    return passed == len(tests)


def main() -> None:
    parser = argparse.ArgumentParser(description="Failure signature analyzer")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test")
    parser.add_argument("--correlate", type=str, help="JSON file with failure records")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.correlate:
        try:
            with open(args.correlate) as f:
                records = json.load(f)
            result = correlate(records)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
