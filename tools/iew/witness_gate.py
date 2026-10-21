"""IEW-002: distinguish self-reported receipts from trusted execution observations.

This module compares witness-captured bytes with receipt declarations.
Admission, GitHub runner identity validation, and submitted code execution are
outside this evidence translation boundary.

Builder v1.7 compliant - iew_witness_gate
HumanAIOS
"""
from __future__ import annotations
import hashlib
import hmac
import json
import re
from typing import Mapping, Any

TOOL_NAME = "iew_witness_gate"
TOOL_VERSION = "0.1.0"

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def classify_evidence(receipt: Mapping[str, Any], *, observed: Mapping[str, Any] | None,
                      expected_source_sha256: str, expected_input_sha256: str,
                      trusted_context: bool = False) -> dict[str, Any]:
    """Compare witness-captured byte digests and exit status with declarations.

    The caller is responsible for obtaining observed outside candidate control
    and assigning trusted_context through protected infrastructure rather than
    receipt data. A match describes evidence consistency, not authorization or
    an identity attestation.
    """
    base = {"admission_effect": "NONE", "merge_authority": False,
            "independently_attested": False, "result": "BLOCKED"}
    if not trusted_context or observed is None:
        return {**base, "reason": "NO_INDEPENDENT_WITNESS"}
    required = ("source_sha256", "input_sha256", "stdout_sha256", "exit_code")
    if any(key not in observed for key in required):
        return {**base, "reason": "WITNESS_FIELDS_MISSING"}
    if not all(isinstance(observed[k], str) for k in required[:3]):
        return {**base, "reason": "WITNESS_FIELDS_INVALID"}
    if re.fullmatch(r"[0-9a-fA-F]{64}", observed["stdout_sha256"]) is None:
        return {**base, "reason": "WITNESS_FIELDS_INVALID"}
    if observed["source_sha256"] != expected_source_sha256 or observed["input_sha256"] != expected_input_sha256:
        return {**base, "reason": "SOURCE_OR_INPUT_MISMATCH"}
    if not isinstance(observed["exit_code"], int) or isinstance(observed["exit_code"], bool):
        return {**base, "reason": "EXIT_CODE_INVALID"}
    try:
        receipt_out = str(receipt["stdout"]).encode("utf-8")
        claimed_exit = receipt["exit_code"]
    except (KeyError, TypeError):
        return {**base, "reason": "AUTHOR_CLAIM_MISSING"}
    if not isinstance(claimed_exit, int) or isinstance(claimed_exit, bool):
        return {**base, "reason": "AUTHOR_CLAIM_INVALID"}
    if not hmac.compare_digest(digest(receipt_out), observed["stdout_sha256"]) or claimed_exit != observed["exit_code"]:
        return {**base, "reason": "OUTCOME_MISMATCH"}
    return {**base, "result": "OUTCOME_MATCH", "reason": "EVIDENCE_CONSISTENT_NOT_AUTHORIZATION",
            "independently_attested": False}

def run_smoke_test():
    source_sha256, input_sha256 = digest(b"source"), digest(b"input")
    result = classify_evidence(
        {"stdout": "ACTUAL", "exit_code": 0},
        observed={"source_sha256": source_sha256, "input_sha256": input_sha256,
                  "stdout_sha256": digest(b"ACTUAL"), "exit_code": 0},
        expected_source_sha256=source_sha256, expected_input_sha256=input_sha256,
        trusted_context=True)
    return result["result"] == "OUTCOME_MATCH" and result["admission_effect"] == "NONE"

if __name__ == "__main__":
    raise SystemExit(0 if run_smoke_test() else 1)
