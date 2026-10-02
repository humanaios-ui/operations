from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .security_scope import ProgramScopeGraph, ScopeAsset


class TestingMode(str, Enum):
    PASSIVE_RECON = "PASSIVE_RECON"
    MANUAL_TESTING = "MANUAL_TESTING"
    BOUNDED_AUTOMATION = "BOUNDED_AUTOMATION"


class AuthorizationState(str, Enum):
    PASSIVE_RECON = "PASSIVE_RECON"
    MANUAL_TESTING = "MANUAL_TESTING"
    BOUNDED_AUTOMATION = "BOUNDED_AUTOMATION"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    SCOPE_CLARIFICATION_REQUIRED = "SCOPE_CLARIFICATION_REQUIRED"


@dataclass(frozen=True)
class SecurityAuthorizationRequest:
    asset_identifier: str
    mode: TestingMode
    program_current_verified: bool
    policy_reviewed: bool
    method_allowed: bool | None
    human_authorized: bool
    requested_finding_category: str | None = None
    destructive_action: bool = False
    denial_of_service: bool = False
    social_engineering: bool = False
    credential_attack: bool = False
    bulk_data_access: bool = False


@dataclass
class SecurityAuthorizationDecision:
    schema: str
    state: AuthorizationState
    asset_identifier: str
    reasons: list[str] = field(default_factory=list)
    authority_effect: str = "NONE"
    execution_capability: str = "NONE"

    @property
    def authorized(self) -> bool:
        return self.state in {
            AuthorizationState.PASSIVE_RECON,
            AuthorizationState.MANUAL_TESTING,
            AuthorizationState.BOUNDED_AUTOMATION,
        }

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data


def _normalized(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def _find_asset(graph: ProgramScopeGraph, identifier: str) -> ScopeAsset | None:
    target = _normalized(identifier)
    matches = [asset for asset in graph.assets if _normalized(asset.asset_identifier) == target]
    if len(matches) == 1:
        return matches[0]
    return None


def authorize_security_action(
    graph: ProgramScopeGraph,
    request: SecurityAuthorizationRequest,
) -> SecurityAuthorizationDecision:
    """Pure fail-closed gate. It does not make network requests or execute testing."""
    prohibited = {
        "destructive_action": request.destructive_action,
        "denial_of_service": request.denial_of_service,
        "social_engineering": request.social_engineering,
        "credential_attack": request.credential_attack,
        "bulk_data_access": request.bulk_data_access,
    }
    active_prohibitions = [name for name, enabled in prohibited.items() if enabled]
    if active_prohibitions:
        return SecurityAuthorizationDecision(
            "humanaios.security-authorization-decision.v1",
            AuthorizationState.NOT_AUTHORIZED,
            request.asset_identifier,
            [f"prohibited:{name}" for name in active_prohibitions],
        )

    if not request.program_current_verified:
        return SecurityAuthorizationDecision(
            "humanaios.security-authorization-decision.v1",
            AuthorizationState.SCOPE_CLARIFICATION_REQUIRED,
            request.asset_identifier,
            ["program_currentness_not_verified"],
        )

    if graph.submission_state.casefold() != "open":
        return SecurityAuthorizationDecision(
            "humanaios.security-authorization-decision.v1",
            AuthorizationState.NOT_AUTHORIZED,
            request.asset_identifier,
            [f"program_submission_state:{graph.submission_state}"],
        )

    asset = _find_asset(graph, request.asset_identifier)
    if asset is None:
        return SecurityAuthorizationDecision(
            "humanaios.security-authorization-decision.v1",
            AuthorizationState.SCOPE_CLARIFICATION_REQUIRED,
            request.asset_identifier,
            ["asset_not_uniquely_present_in_structured_scope"],
        )

    if not asset.eligible_for_submission:
        return SecurityAuthorizationDecision(
            "humanaios.security-authorization-decision.v1",
            AuthorizationState.NOT_AUTHORIZED,
            request.asset_identifier,
            ["asset_not_eligible_for_submission"],
        )

    if not request.policy_reviewed:
        return SecurityAuthorizationDecision(
            "humanaios.security-authorization-decision.v1",
            AuthorizationState.SCOPE_CLARIFICATION_REQUIRED,
            request.asset_identifier,
            ["program_policy_not_reviewed"],
        )

    if request.requested_finding_category:
        requested = _normalized(request.requested_finding_category)
        for exclusion in graph.exclusions:
            if requested == _normalized(exclusion.category):
                return SecurityAuthorizationDecision(
                    "humanaios.security-authorization-decision.v1",
                    AuthorizationState.NOT_AUTHORIZED,
                    request.asset_identifier,
                    [f"scope_exclusion:{exclusion.category}"],
                )

    if request.method_allowed is None:
        return SecurityAuthorizationDecision(
            "humanaios.security-authorization-decision.v1",
            AuthorizationState.SCOPE_CLARIFICATION_REQUIRED,
            request.asset_identifier,
            ["testing_method_permission_ambiguous"],
        )
    if request.method_allowed is False:
        return SecurityAuthorizationDecision(
            "humanaios.security-authorization-decision.v1",
            AuthorizationState.NOT_AUTHORIZED,
            request.asset_identifier,
            ["testing_method_disallowed_by_reviewed_policy"],
        )

    if not request.human_authorized:
        return SecurityAuthorizationDecision(
            "humanaios.security-authorization-decision.v1",
            AuthorizationState.NOT_AUTHORIZED,
            request.asset_identifier,
            ["human_authorization_absent"],
        )

    return SecurityAuthorizationDecision(
        "humanaios.security-authorization-decision.v1",
        AuthorizationState(request.mode.value),
        request.asset_identifier,
        [
            "program_currentness_verified",
            "asset_submission_eligible",
            "policy_reviewed",
            "method_allowed",
            "human_authorized",
        ],
    )
