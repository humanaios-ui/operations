from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .security_capability import normalize_asset_type


READY_STATE = "READY_FOR_POLICY_AND_METHOD_REVIEW"
METHOD_CLASS = "DPP_PASSIVE_DATA_EXPOSURE"

# The current DPP policy explicitly describes monitoring websites/apps and
# passive/read-only investigation of exposed information. These asset classes
# can therefore support a bounded DPP method review. This is suitability only,
# never authorization.
DIRECT_SURFACE_TYPES = {
    "url",
    "domain",
    "wildcard",
    "androidapk",
    "androidplaystore",
    "googleplayappid",
    "iosipa",
    "iosappstore",
    "iostestflight",
    "applestoreappid",
}

# These may contain relevant evidence, but the DPP policy does not by itself
# establish that the normal review method for the asset class is a permitted
# passive/read-only data-exposure method.
OBJECTIVE_EVIDENCE_TYPES = {
    "sourcecode",
    "aimodel",
    "cidr",
    "ipaddress",
    "windowsmicrosoftstore",
    "executable",
    "hardware",
    "hardwareiot",
    "smartcontract",
    "otherasset",
    "other",
}

INSTRUCTION_CONFLICT_TERMS = (
    "do not test",
    "no testing",
    "not allowed",
    "out of scope",
    "do not scan",
    "no scanning",
    "prohibited",
)


@dataclass
class MethodSuitabilityEntry:
    ready_rank: int
    scope_id: str
    asset_type: str
    review_mode_candidate: str
    suitability_state: str
    rationale: list[str] = field(default_factory=list)
    required_evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MethodSuitabilityResult:
    schema: str = "humanaios.hackerone-dpp-method-suitability.v1"
    method_class: str = METHOD_CLASS
    method_objective: str = "detect or verify Eternal data/configuration exposure"
    interaction_boundary: str = "passive/read-only; no active vulnerability testing"
    entries: list[MethodSuitabilityEntry] = field(default_factory=list)
    policy_support_present: bool = False
    authority_effect: str = "NONE"
    execution_capability: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for entry in self.entries:
            counts[entry.suitability_state] = counts.get(entry.suitability_state, 0) + 1
        return {
            **asdict(self),
            "summary": {
                "ready_entries_evaluated": len(self.entries),
                "suitability_state_counts": counts,
                "candidate_ready_ranks": [
                    item.ready_rank
                    for item in self.entries
                    if item.suitability_state == "CONDITIONALLY_SUITABLE"
                ],
                "policy_support_present": self.policy_support_present,
            },
        }


def _policy_supports_dpp_method(policy: str) -> bool:
    p = " ".join((policy or "").casefold().split())
    return (
        "data protection program" in p
        and ("passive monitoring" in p or "passive reconnaissance" in p or "passive monitoring and recon" in p)
        and (
            "publicly accessible data exposure" in p
            or "monitoring websites/apps for exposed information" in p
            or "scanning for exposed configuration files" in p
        )
        and (
            "active hunting" in p
            or "active exploitation" in p
            or "vulnerability testing on external systems" in p
        )
        and "read-only verification" in p
    )


def _scope_instructions(payload: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    programs = list((payload.get("portfolio") or {}).get("programs") or [])
    for program in programs:
        graph = program.get("graph") or {}
        for asset in graph.get("assets") or []:
            scope_id = str(asset.get("scope_id") or "")
            if scope_id:
                result[scope_id] = str(asset.get("instruction") or "")
    return result


def evaluate_dpp_method_suitability(payload: dict[str, Any]) -> MethodSuitabilityResult:
    programs = list((payload.get("portfolio") or {}).get("programs") or [])
    entries = list((payload.get("ranked_queue") or {}).get("entries") or [])
    instructions = _scope_instructions(payload)

    policies = [
        str((program.get("graph") or {}).get("policy") or "")
        for program in programs
        if (program.get("graph") or {}).get("policy")
    ]
    policy_support = any(_policy_supports_dpp_method(policy) for policy in policies)

    result = MethodSuitabilityResult(policy_support_present=policy_support)

    ready_rank = 0
    for entry in entries:
        if entry.get("review_state") != READY_STATE:
            continue

        ready_rank += 1
        scope_id = str(entry.get("scope_id") or "")
        asset_type = str(entry.get("asset_type") or "")
        normalized_type = normalize_asset_type(asset_type)
        instruction = instructions.get(scope_id, "")
        instruction_cf = instruction.casefold()

        rationale: list[str] = []
        required: list[str] = [
            "specific proposed action is limited to the DPP data-exposure objective",
            "interaction remains passive/read-only",
            "fresh scope exclusions are reviewed before any authorization decision",
            "human authorization is separate and still required for execution",
        ]

        conflict = next(
            (term for term in INSTRUCTION_CONFLICT_TERMS if term in instruction_cf),
            None,
        )

        if not policy_support:
            state = "POLICY_SUPPORT_NOT_ESTABLISHED"
            rationale.append("current policy packet does not fully establish the bounded DPP method")
        elif conflict:
            state = "SCOPE_INSTRUCTION_CONFLICT"
            rationale.append(f"scope instruction contains restrictive term: {conflict}")
        elif normalized_type in DIRECT_SURFACE_TYPES:
            state = "CONDITIONALLY_SUITABLE"
            rationale.extend([
                "asset class is a website/app surface contemplated by the current DPP policy",
                "suitability is limited to exposure-oriented passive/read-only observation",
                "general vulnerability reconnaissance is not implied",
            ])
            required.append("objective evidence must concern Eternal data, credentials, configuration, API keys, or access tokens")
        elif normalized_type in OBJECTIVE_EVIDENCE_TYPES:
            state = "OBJECTIVE_EVIDENCE_REQUIRED"
            rationale.append(
                "asset class may contain relevant evidence, but its ordinary review method is not established as a DPP passive method"
            )
            required.append("separate evidence must bind the proposed method to a permitted DPP exposure scenario")
        else:
            state = "OBJECTIVE_EVIDENCE_REQUIRED"
            rationale.append("asset type is not represented in the bounded DPP method model")
            required.append("explicit policy/method clarification is required")

        result.entries.append(
            MethodSuitabilityEntry(
                ready_rank=ready_rank,
                scope_id=scope_id,
                asset_type=asset_type,
                review_mode_candidate=str(entry.get("review_mode_candidate") or ""),
                suitability_state=state,
                rationale=rationale,
                required_evidence=required,
            )
        )

    return result
