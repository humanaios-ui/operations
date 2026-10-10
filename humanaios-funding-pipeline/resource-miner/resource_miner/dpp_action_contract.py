from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .security_capability import normalize_asset_type


METHOD_CLASS = "DPP_PASSIVE_DATA_EXPOSURE"
SUPPORTED_ACTION = "PUBLIC_EXPOSURE_OBSERVATION"
DIRECT_SURFACE_TYPES = {"url", "domain", "wildcard"}


@dataclass(frozen=True)
class DPPActionContract:
    schema: str = "humanaios.hackerone-dpp-action-contract.v1"
    method_class: str = METHOD_CLASS
    action: str = SUPPORTED_ACTION
    objective: str = "detect publicly exposed Eternal data/configuration"
    authentication: bool = False
    state_change: bool = False
    exploit_payloads: bool = False
    brute_force: bool = False
    high_volume_scanning: bool = False
    bulk_download: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_dpp_action_contract() -> DPPActionContract:
    return DPPActionContract()


def _policy_supports_contract(policy: str) -> bool:
    p = " ".join((policy or "").casefold().split())
    return (
        "data protection program" in p
        and ("passive monitoring" in p or "passive reconnaissance" in p or "passive monitoring and recon" in p)
        and (
            "observing publicly accessible data exposure" in p
            or "monitoring websites/apps for exposed information" in p
        )
        and (
            "active hunting" in p
            or "active exploitation" in p
            or "vulnerability testing on external systems" in p
        )
        and "read-only verification" in p
    )


def evaluate_dpp_action_contract(
    entry: dict[str, Any],
    graph: Any,
    contract: DPPActionContract,
) -> dict[str, Any]:
    reasons: list[str] = []

    if contract.method_class != METHOD_CLASS:
        reasons.append("unsupported_method_class")
    if contract.action != SUPPORTED_ACTION:
        reasons.append("unsupported_action")

    prohibited = {
        "authentication": contract.authentication,
        "state_change": contract.state_change,
        "exploit_payloads": contract.exploit_payloads,
        "brute_force": contract.brute_force,
        "high_volume_scanning": contract.high_volume_scanning,
        "bulk_download": contract.bulk_download,
    }
    for name, enabled in prohibited.items():
        if enabled:
            reasons.append(f"contract_prohibited:{name}")

    if not _policy_supports_contract(str(getattr(graph, "policy", "") or "")):
        reasons.append("fresh_policy_does_not_support_dpp_contract")

    if str(getattr(graph, "exclusions_state", "")) != "OBSERVED":
        reasons.append("fresh_scope_exclusions_not_observed")

    normalized_type = normalize_asset_type(str(entry.get("asset_type") or ""))
    if normalized_type not in DIRECT_SURFACE_TYPES:
        reasons.append(f"asset_type_not_supported:{entry.get('asset_type')}")

    scope_id = str(entry.get("scope_id") or "")
    matches = [
        asset for asset in getattr(graph, "assets", [])
        if str(getattr(asset, "scope_id", "")) == scope_id
    ]
    if len(matches) != 1:
        reasons.append("scope_id_not_uniquely_present")
    else:
        asset = matches[0]
        if not bool(getattr(asset, "eligible_for_submission", False)):
            reasons.append("asset_not_eligible_for_submission")
        instruction = str(getattr(asset, "instruction", "") or "").casefold()
        for term in (
            "do not test",
            "no testing",
            "not allowed",
            "out of scope",
            "do not scan",
            "no scanning",
            "prohibited",
        ):
            if term in instruction:
                reasons.append(f"scope_instruction_conflict:{term}")
                break

    allowed = len(reasons) == 0

    return {
        "schema": "humanaios.hackerone-dpp-action-contract-review.v1",
        "method_allowed": allowed,
        "state": "METHOD_ALLOWED" if allowed else "METHOD_NOT_ESTABLISHED",
        "reasons": reasons or [
            "fresh_policy_supports_dpp_passive_data_exposure",
            "fresh_scope_exclusions_observed",
            "direct_web_surface",
            "no_scope_instruction_conflict",
            "contract_is_passive_read_only",
        ],
        "contract": contract.to_dict(),
        "authority_effect": "NONE",
        "execution_capability": "NONE",
    }
