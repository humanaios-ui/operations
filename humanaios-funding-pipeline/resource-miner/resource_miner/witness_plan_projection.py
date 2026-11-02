"""Read-only Quiet Infrastructure -> existing Witness/Unit Zero context projection.

This module does not call MCP, Anthropic, GitHub, or any external service.
Output is an unsigned, untrusted *brief*, never a Witness observation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .planning import resolve_resource_plan

EXPECTED_PLAN_ID = "RP-QUIET-INFRA-001"
ALLOWED_EVIDENCE_STATES = frozenset({
    "OBSERVED", "SUPPORTED", "INFERRED", "HYPOTHESIZED",
    "UNVERIFIED", "CONTRADICTED",
})
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}\Z")
MAX_BYTES = 64_000
MAX_TOKENS = 24
MAX_REQUIREMENTS = 24


def _id(value: object) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError("Invalid bounded identifier in Witness plan.")
    return value


def project_witness_plan(plan: object) -> dict[str, Any]:
    """Produce a source-hashed, safe orientation, not a signed audit receipt.

    Input is a *public, fixed-scope Resource Plan*; arbitrary private plans
    must not be exported to a model. This projector only exposes allowlisted
    identifiers/statuses, not descriptions, claims, contact data or raw notes.
    """
    if not isinstance(plan, dict) or plan.get("plan_id") != EXPECTED_PLAN_ID:
        raise ValueError("Only the approved public Quiet Infrastructure plan ID is supported.")
    if plan.get("authority_effect") != "NONE" or plan.get("execution") != "DISABLED":
        raise ValueError("Witness cannot inherit approval or execution authority.")

    canonical = json.dumps(plan, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(canonical) > MAX_BYTES:
        raise ValueError("Plan exceeds public Witness projection budget.")

    resolved = resolve_resource_plan(plan)
    raw_tokens = plan.get("thesis_tokens")
    raw_reqs = resolved.get("resource_requirements")
    if (not isinstance(raw_tokens, list) or len(raw_tokens) > MAX_TOKENS
            or not isinstance(raw_reqs, list) or len(raw_reqs) > MAX_REQUIREMENTS):
        raise ValueError("Token or requirement budget exceeded.")

    known_needs = {_id(n["need_id"]) for n in plan["needs"]}
    tokens = []
    token_ids: set[str] = set()
    for token in raw_tokens:
        if not isinstance(token, dict):
            raise ValueError("Invalid Witness token.")
        tid = _id(token.get("token_id"))
        if tid in token_ids:
            raise ValueError("Duplicate Witness concept token.")
        token_ids.add(tid)
        state = token.get("evidence_state")
        if state not in ALLOWED_EVIDENCE_STATES:
            raise ValueError("Invalid Witness evidence state.")
        refs = token.get("source_refs")
        if not isinstance(refs, list) or not refs:
            raise ValueError("A Witness concept needs a source reference.")
        mapped = token.get("maps_to_need_ids")
        if not isinstance(mapped, list) or not mapped:
            raise ValueError("Witness concept must map to a need.")
        links = sorted({_id(x) for x in mapped})
        if not set(links).issubset(known_needs):
            raise ValueError("Witness concept references an unknown need.")
        # No source text or token free prose leaves this module.
        tokens.append({
            "token_id": tid,
            "evidence_state": state,
            "need_ids": links,
            "source_reference_count": len(refs),
        })

    requirements = []
    for row in raw_reqs:
        status = row.get("gap_status")
        rid = _id(row.get("requirement_id"))
        if status not in {
            "SATISFIED", "PARTIAL", "CONFIRMED", "UNKNOWN", "CONDITIONAL",
            "INACTIVE", "INTERNAL_COMPOSITION_GAP",
        }:
            raise ValueError("Unknown resolved requirement status.")
        requirements.append({
            "requirement_id": rid,
            "gap_status": status,
            "mine_external": row.get("mine_external") is True,
        })

    return {
        "schema_version": "quiet-witness-projection-v0.1",
        "plan_id": EXPECTED_PLAN_ID,
        "source_sha256": hashlib.sha256(canonical).hexdigest(),
        "source_digest_kind": "UNSIGNED_CONTENT_FINGERPRINT_NOT_ATTESTATION",
        "source_basis": "REPOSITORY_PLAN_CONTENT_NOT_RUNTIME_OBSERVATION",
        "witness_contract": "WITNESS_SERVICE_CONTRACT.md",
        "witness_agent_candidate": "Unit Zero / haios_talk (PR #1012)",
        "agent_runtime_verification": "NOT_PERFORMED_BY_THIS_PROJECTION",
        "concept_tokens": sorted(tokens, key=lambda x: x["token_id"]),
        "resource_requirements": sorted(requirements, key=lambda x: x["requirement_id"]),
        "omission_codes": ["NOT_OBSERVED", "OUT_OF_SCOPE"],
        "missing_evidence": [
            "independent MCP runtime readback",
            "P1/P2/P3 calibration history",
            "independent zero-egress observation",
            "human reviewer and buyer outcome",
        ],
        "handoff": "USER_OPT_IN_REQUIRED_USE_EXISTING_UNIT_ZERO_MCP",
        "provider_request": "NONE",
        "authority": "NONE",
        "execution": "DISABLED",
        "non_authority_invariant": "WITNESS_IS_NOT_THE_AUTHORITY",
        "anti_manipulation_invariant": "ADAPTATION_SERVES_COMPREHENSION_NOT_COMPLIANCE",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Quiet Infrastructure Witness brief")
    parser.add_argument("--file", required=True, help="Local public Quiet Infrastructure JSON plan")
    args = parser.parse_args()
    path = Path(args.file)
    if path.stat().st_size > MAX_BYTES:
        parser.error("Plan exceeds public Witness projection budget.")
    plan = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(project_witness_plan(plan), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
