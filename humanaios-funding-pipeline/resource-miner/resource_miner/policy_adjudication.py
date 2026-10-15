from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any

from .dpp_action_contract import (
    DPPActionContract,
    evaluate_dpp_action_contract,
)
from .security_authorization import (
    SecurityAuthorizationRequest,
    TestingMode,
    authorize_security_action,
)
from .security_scope import build_scope_graph


READY_STATE = "READY_FOR_POLICY_AND_METHOD_REVIEW"


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def select_ranked_candidate(portfolio_payload: dict[str, Any], rank: int = 1) -> dict[str, Any]:
    entries = list((portfolio_payload.get("ranked_queue") or {}).get("entries") or [])
    ready = [entry for entry in entries if entry.get("review_state") == READY_STATE]
    if rank < 1 or rank > len(ready):
        raise ValueError(f"ready candidate rank {rank} is outside 1..{len(ready)}")
    return ready[rank - 1]


def _scope_binding(entry: dict[str, Any], graph: Any) -> tuple[bool, str]:
    matches = [asset for asset in graph.assets if asset.scope_id == str(entry.get("scope_id") or "")]
    if len(matches) != 1:
        return False, "scope_id_not_uniquely_present_in_fresh_scope"
    asset = matches[0]
    if asset.asset_identifier != str(entry.get("asset_identifier") or ""):
        return False, "asset_identifier_changed_since_ranking"
    if asset.asset_type != str(entry.get("asset_type") or ""):
        return False, "asset_type_changed_since_ranking"
    if not asset.eligible_for_submission:
        return False, "asset_no_longer_eligible_for_submission"
    return True, "fresh_scope_binding_verified"


def adjudicate_ranked_candidate(
    client: Any,
    portfolio_payload: dict[str, Any],
    *,
    rank: int = 1,
    mode: TestingMode = TestingMode.PASSIVE_RECON,
    method_allowed: bool | None = None,
    dpp_action_contract: DPPActionContract | None = None,
    requested_finding_category: str | None = None,
    human_authorization_ref: str | None = None,
    page_size: int = 100,
) -> dict[str, Any]:
    """Refresh one ranked candidate and pass evidence through the fail-closed gate.

    This function performs HackerOne metadata requests only. It does not contact
    any program asset and it has no execution capability.
    """
    entry = select_ranked_candidate(portfolio_payload, rank=rank)
    handle = str(entry.get("program_handle") or "").strip()
    if not handle:
        raise ValueError("ranked candidate is missing program_handle")

    program = client.find_program(handle, page_size=page_size)
    scopes = client.get_structured_scopes(handle, page_size=page_size)
    exclusions = client.get_scope_exclusions(handle)

    graph = build_scope_graph(
        program,
        scopes,
        exclusions,
        exclusions_state="OBSERVED",
    )

    binding_valid, binding_reason = _scope_binding(entry, graph)

    policy_packet = {
        "program_id": graph.program_id,
        "handle": graph.handle,
        "submission_state": graph.submission_state,
        "policy": graph.policy,
        "scope_id": entry.get("scope_id"),
        "asset_identifier": entry.get("asset_identifier"),
        "asset_type": entry.get("asset_type"),
        "scope_instruction": next(
            (
                asset.instruction
                for asset in graph.assets
                if asset.scope_id == str(entry.get("scope_id") or "")
            ),
            None,
        ),
        "scope_exclusions": [asdict(item) for item in graph.exclusions],
        "scope_exclusions_state": graph.exclusions_state,
    }

    program_current_ref = f"hackerone:program-current:sha256:{_digest({'program': program, 'scopes': scopes})}"
    policy_ref = f"hackerone:policy-review:sha256:{_digest(policy_packet)}"

    # Fresh policy + exclusions are reviewed as evidence. For the DPP path,
    # method permission can be derived only from an explicit action contract
    # evaluated against this fresh graph. Otherwise silence remains ambiguous.
    policy_evidence_complete = bool(graph.policy.strip()) and graph.exclusions_state == "OBSERVED"

    contract_review = None
    effective_method_allowed = method_allowed
    if dpp_action_contract is not None:
        contract_review = evaluate_dpp_action_contract(
            entry,
            graph,
            dpp_action_contract,
        )
        effective_method_allowed = bool(contract_review["method_allowed"])

    request = SecurityAuthorizationRequest(
        asset_identifier=str(entry.get("asset_identifier") or ""),
        mode=mode,
        program_current_verified=binding_valid,
        policy_reviewed=policy_evidence_complete,
        method_allowed=effective_method_allowed,
        human_authorized=bool(human_authorization_ref),
        program_currentness_evidence_ref=program_current_ref if binding_valid else None,
        policy_evidence_ref=policy_ref if policy_evidence_complete else None,
        human_authorization_ref=human_authorization_ref,
        requested_finding_category=requested_finding_category,
    )
    decision = authorize_security_action(graph, request)

    return {
        "schema": "humanaios.hackerone-policy-method-adjudication.v1",
        "selected_rank": rank,
        "selected_entry": entry,
        "fresh_scope_graph": graph.to_dict(),
        "policy_packet": policy_packet,
        "scope_binding": {
            "valid": binding_valid,
            "reason": binding_reason,
        },
        "method_review": {
            "mode": mode.value,
            "method_allowed": effective_method_allowed,
            "permission_inference": "ACTION_CONTRACT" if contract_review is not None else "NONE",
            "note": (
                "method permission derived from fresh-policy DPP action-contract review"
                if contract_review is not None
                else "method permission is explicit-only; silence remains ambiguous"
            ),
            "action_contract_review": contract_review,
        },
        "authorization_request": {
            **asdict(request),
            "mode": request.mode.value,
        },
        "authorization_decision": decision.to_dict(),
        "authority_effect": "NONE",
        "execution_capability": "NONE",
    }
