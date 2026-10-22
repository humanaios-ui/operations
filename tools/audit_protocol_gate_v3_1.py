#!/usr/bin/env python3
"""HumanAIOS — fail-closed audit contract checker v3.1.
Builder v1.7 compliant

Synthetic contract completeness check only. No claim verification or admission.
Usage: python tools/audit_protocol_gate_v3_1.py --smoke-test
"""
import argparse
import json
import math
import re
import sys

TOOL_NAME = "audit_protocol_gate_v3_1"
TOOL_VERSION = "3.1.0"
TOOL_CATEGORY = "validation_tool"
TOOL_ZONE = 1

CONTROLS = {
    "C1": [f"A{i}" for i in range(1, 6)],
    "C2": [f"B{i}" for i in range(1, 8)] + [f"B8.{i}" for i in range(1, 5)],
}

def sample_size(n):
    if type(n) is not int or n < 0:
        raise ValueError("Invalid population")
    return min(n, max(30, math.ceil(n * .1)))

def upper95_zero_failures(n):
    return 1 - .05 ** (1 / n) if type(n) is int and n > 0 else None

def evaluate(data):
    if not isinstance(data, dict):
        raise ValueError("AUDIT_INPUT_NOT_OBJECT")
    scope = data.get("scope_manifest", data.get("scope", {}))
    if not isinstance(scope, dict):
        raise ValueError("SCOPE_NOT_OBJECT")
    records = data.get("claims", {})
    if not isinstance(records, dict):
        raise ValueError("CLAIMS_NOT_OBJECT")
    scope_ok = isinstance(scope, dict) and bool(re.fullmatch(
        r"[0-9a-fA-F]{40}", str(scope.get("repo_commit_40hex", scope.get("commit", "")))))
    scope_ok &= bool((scope.get("target_name") or scope.get("target")) and scope.get("environment")
                     and scope.get("auditor") and scope.get("operator")
                     and scope.get("authorization_receipt")
                     and scope["auditor"] != scope["operator"])
    output = {"schema": "audit.v3.1", "independent_authentication": "UNVERIFIED",
              "authority_effect": "NONE", "merge_authority": False, "claims": {}}
    for claim, required in CONTROLS.items():
        item = records.get(claim) or {}
        if not isinstance(item, dict):
            raise ValueError("CLAIM_NOT_OBJECT")
        if item.get("applicability") == "NOT_CLAIMED":
            output["claims"][claim] = {"contract": "NOT_CLAIMED", "claim": "NOT_CLAIMED", "gaps": []}
            continue
        gaps = [] if scope_ok else ["INVALID_SCOPE"]
        if item.get("applicability") != "CLAIMED":
            gaps.append("UNDECLARED_APPLICABILITY")
        controls = item.get("controls") or {}
        if not isinstance(controls, dict):
            raise ValueError("CONTROLS_NOT_OBJECT")
        for key in required:
            test = controls.get(key) or {}
            if not isinstance(test, dict):
                raise ValueError("CONTROL_NOT_OBJECT")
            if test.get("state") != "OBSERVED_PASS":
                gaps.append(key + ":NOT_PASSED")
            if type(test.get("score")) is not int or not 3 <= test["score"] <= 4:
                gaps.append(key + ":BELOW_FLOOR")
            if test.get("tier") not in ("E1", "E2") or not test.get("receipt"):
                gaps.append(key + ":NO_INDEPENDENT_RECEIPT")
        if claim == "C1":
            sample = item.get("risk_sample") or {}
            if not isinstance(sample, dict):
                raise ValueError("RISK_SAMPLE_NOT_OBJECT")
            n = sample.get("eligible")
            if type(n) is not int or n < 30:
                gaps.append("A5:INSUFFICIENT_RISK_SAMPLE")
            elif sample.get("selected") != sample_size(n):
                gaps.append("A5:WRONG_SAMPLE")
            if sample.get("unauthorized_bypasses") != 0:
                gaps.append("A5:BYPASS_UNKNOWN_OR_PRESENT")
        else:
            training = item.get("training") or {}
            if not isinstance(training, dict):
                raise ValueError("TRAINING_NOT_OBJECT")
            for field in ("teacher_version", "student_version", "baseline",
                          "sealed_holdout", "witness"):
                if not training.get(field):
                    gaps.append("C2:MISSING_" + field)
            vals = training.get("holdout_cycles", [])
            if not isinstance(vals, list) or len(vals) < 3:
                gaps.append("B3:FEWER_THAN_THREE_CYCLES")
            elif any(type(v) not in (float, int) or not math.isfinite(v) for v in vals):
                gaps.append("B3:INVALID_CYCLES")
            else:
                if any(vals[0] - v > .02 + 1e-12 for v in vals):
                    gaps.append("B3:CUMULATIVE_DROP")
                if any(vals[i - 1] - vals[i] > .02 + 1e-12
                       for i in range(1, len(vals))):
                    gaps.append("B3:ADJACENT_DROP")
            if type(training.get("gain")) not in (float, int) or not math.isfinite(training["gain"]) or training["gain"] <= 0:
                gaps.append("B8.4:NONPOSITIVE_GAIN")
        output["claims"][claim] = {
            "contract": "BLOCKED" if gaps else "ELIGIBLE_FOR_REVIEW",
            "claim": "INCONCLUSIVE_PENDING_INDEPENDENT_WITNESS",
            "gaps": sorted(set(gaps))
        }
    return output

def run_smoke_test():
    assert sample_size(0) == 0 and sample_size(30) == 30
    assert upper95_zero_failures(5) > .4
    sample = {"scope": {"target": "synthetic", "commit": "a" * 40,
              "environment": "isolated", "auditor": "observer",
              "operator": "actor", "authorization_receipt": "synthetic"},
              "claims": {"C1": {"applicability": "CLAIMED", "controls": {}},
                         "C2": {"applicability": "NOT_CLAIMED"}}}
    result = evaluate(sample)
    assert result["claims"]["C1"]["contract"] == "BLOCKED"
    assert not result["merge_authority"]
    print("smoke-test OK: fail-closed synthetic gates")
    return 0

if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        sys.exit(run_smoke_test())
    try:
        with open(sys.argv[1], encoding="utf8") as f:
            result = evaluate(json.load(f))
        print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(2 if any(x["contract"] == "BLOCKED" for x in result["claims"].values()) else 0)
    except (OSError, ValueError, IndexError, KeyError, TypeError, AttributeError) as exc:
        print(json.dumps({"contract": "BLOCKED", "error": str(exc), "authority_effect": "NONE"}))
        sys.exit(2)
