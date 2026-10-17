"""IEW-002: distinguish self-reported receipts from trusted execution observations.

This module deliberately does NOT grant admission, validate GitHub runner identity,
or execute arbitrary submitted code. It is a strict evidence translation boundary.
"""
from __future__ import annotations
import hashlib
import hmac
import json
from typing import Mapping, Any

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def classify_evidence(receipt: Mapping[str, Any], *, observed: Mapping[str, Any] | None,
                      expected_source_sha256: str, expected_input_sha256: str,
                      trusted_context: bool = False) -> dict[str, Any]:
    """Compare witness-captured bytes with declarations, never promote authority.

    The observed dictionary MUST originate outside the candidate's control.
    trusted_context is assigned by the caller's protected infrastructure, never
    parsed from a receipt. Passing it here is not itself an identity attestation.
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
