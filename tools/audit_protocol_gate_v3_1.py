#!/usr/bin/env python3
"""Read-only v3.1 audit contract checker. Results are not evidence or approval."""
import json
import math
import re
import sys

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
    scope = data.get("scope", {})
    scope_ok = isinstance(scope, dict) and bool(re.fullmatch(
        r"[0-9a-fA-F]{40}", str(scope.get("commit", ""))))
    scope_ok &= bool(scope.get("target") and scope.get("environment")
                     and scope.get("auditor") and scope.get("operator")
                     and scope.get("authorization_receipt")
                     and scope["auditor"] != scope["operator"])
    output = {"schema": "audit.v3.1", "independent_authentication": "UNVERIFIED",
              "authority_effect": "NONE", "merge_authority": False, "claims": {}}
    for claim, required in CONTROLS.items():
        item = data.get("claims", {}).get(claim, {})
        if item.get("applicability") == "NOT_CLAIMED":
            output["claims"][claim] = {"contract": "NOT_CLAIMED", "claim": "NOT_CLAIMED", "gaps": []}
            continue
        gaps = [] if scope_ok else ["INVALID_SCOPE"]
        if item.get("applicability") != "CLAIMED":
            gaps.append("UNDECLARED_APPLICABILITY")
        controls = item.get("controls", {})
        for key in required:
            test = controls.get(key, {})
            if test.get("state") != "OBSERVED_PASS":
                gaps.append(key + ":NOT_PASSED")
            if type(test.get("score")) is not int or test["score"] < 3:
                gaps.append(key + ":BELOW_FLOOR")
            if test.get("tier") not in ("E1", "E2") or not test.get("receipt"):
                gaps.append(key + ":NO_INDEPENDENT_RECEIPT")
        if claim == "C1":
            sample = item.get("risk_sample", {})
            n = sample.get("eligible")
            if type(n) is not int or n < 30:
                gaps.append("A5:INSUFFICIENT_RISK_SAMPLE")
            elif sample.get("selected") != sample_size(n):
                gaps.append("A5:WRONG_SAMPLE")
            if sample.get("unauthorized_bypasses") != 0:
                gaps.append("A5:BYPASS_UNKNOWN_OR_PRESENT")
        else:
            training = item.get("training", {})
            for field in ("teacher_version", "student_version", "baseline",
                          "sealed_holdout", "witness"):
                if not training.get(field):
                    gaps.append("C2:MISSING_" + field)
            vals = training.get("holdout_cycles", [])
            if not isinstance(vals, list) or len(vals) < 3:
                gaps.append("B3:FEWER_THAN_THREE_CYCLES")
            elif any(type(v) not in (float, int) or not math.isfinite(v) for v in vals):
                gaps.append("B3:INVALID_CYCLES")
            elif any(vals[0] - v > .02 + 1e-12 for v in vals):
                gaps.append("B3:CUMULATIVE_DROP")
            if type(training.get("gain")) not in (float, int) or training["gain"] <= 0:
                gaps.append("B8.4:NONPOSITIVE_GAIN")
        output["claims"][claim] = {
            "contract": "BLOCKED" if gaps else "ELIGIBLE_FOR_REVIEW",
            "claim": "INCONCLUSIVE_PENDING_INDEPENDENT_WITNESS",
            "gaps": sorted(set(gaps))
        }
    return output

if __name__ == "__main__":
    try:
        with open(sys.argv[1], encoding="utf8") as f:
            result = evaluate(json.load(f))
        print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(2 if any(x["contract"] == "BLOCKED" for x in result["claims"].values()) else 0)
    except (OSError, ValueError, IndexError, KeyError, TypeError) as exc:
        print(json.dumps({"contract": "BLOCKED", "error": str(exc), "authority_effect": "NONE"}))
        sys.exit(2)
