from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .normalize import utcnow_iso


@dataclass(frozen=True)
class ScopeAsset:
    scope_id: str
    asset_identifier: str
    asset_type: str
    eligible_for_submission: bool
    eligible_for_bounty: bool
    instruction: str | None = None
    max_severity: str | None = None
    reference: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class ScopeExclusion:
    exclusion_id: str
    category: str
    details: str = ""
    updated_at: str | None = None


@dataclass
class ProgramScopeGraph:
    schema: str
    source: str
    observed_at: str
    program_id: str
    handle: str
    name: str
    policy: str
    submission_state: str
    offers_bounties: bool | None
    open_scope: bool | None
    gold_standard_safe_harbor: bool | None
    assets: list[ScopeAsset] = field(default_factory=list)
    exclusions: list[ScopeExclusion] = field(default_factory=list)
    exclusions_state: str = "OBSERVED"
    exclusions_error: str | None = None
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_scope_graph(
    program: dict[str, Any],
    structured_scopes: list[dict[str, Any]],
    scope_exclusions: list[dict[str, Any]],
    *,
    observed_at: str | None = None,
    exclusions_state: str = "OBSERVED",
    exclusions_error: str | None = None,
) -> ProgramScopeGraph:
    attrs = program.get("attributes") or {}
    handle = str(attrs.get("handle") or "").strip()
    if not handle:
        raise ValueError("Program scope graph requires a program handle")

    assets: list[ScopeAsset] = []
    for row in structured_scopes:
        a = row.get("attributes") or {}
        identifier = str(a.get("asset_identifier") or "").strip()
        if not identifier:
            continue
        assets.append(
            ScopeAsset(
                scope_id=str(row.get("id") or ""),
                asset_identifier=identifier,
                asset_type=str(a.get("asset_type") or "UNKNOWN"),
                eligible_for_submission=a.get("eligible_for_submission") is True,
                eligible_for_bounty=a.get("eligible_for_bounty") is True,
                instruction=str(a.get("instruction")) if a.get("instruction") is not None else None,
                max_severity=str(a.get("max_severity")) if a.get("max_severity") is not None else None,
                reference=str(a.get("reference")) if a.get("reference") is not None else None,
                updated_at=str(a.get("updated_at")) if a.get("updated_at") is not None else None,
            )
        )

    exclusions: list[ScopeExclusion] = []
    for row in scope_exclusions:
        a = row.get("attributes") or {}
        category = str(a.get("category") or "").strip()
        if not category:
            continue
        exclusions.append(
            ScopeExclusion(
                exclusion_id=str(row.get("id") or ""),
                category=category,
                details=str(a.get("details") or ""),
                updated_at=str(a.get("updated_at")) if a.get("updated_at") is not None else None,
            )
        )

    return ProgramScopeGraph(
        schema="humanaios.hackerone-scope-graph.v1",
        source=f"https://hackerone.com/{handle}?type=team",
        observed_at=observed_at or utcnow_iso(),
        program_id=str(program.get("id") or ""),
        handle=handle,
        name=str(attrs.get("name") or handle),
        policy=str(attrs.get("policy") or ""),
        submission_state=str(attrs.get("submission_state") or "unknown"),
        offers_bounties=attrs.get("offers_bounties") if isinstance(attrs.get("offers_bounties"), bool) else None,
        open_scope=attrs.get("open_scope") if isinstance(attrs.get("open_scope"), bool) else None,
        gold_standard_safe_harbor=(
            attrs.get("gold_standard_safe_harbor")
            if isinstance(attrs.get("gold_standard_safe_harbor"), bool)
            else None
        ),
        assets=assets,
        exclusions=exclusions,
        exclusions_state=exclusions_state,
        exclusions_error=exclusions_error,
    )


def fetch_scope_graph(client: Any, handle: str) -> ProgramScopeGraph:
    """Fetch policy metadata only; never contacts an in-scope asset."""
    program = client.get_program(handle)
    scopes = client.get_structured_scopes(handle)
    exclusions = client.get_scope_exclusions(handle)
    return build_scope_graph(program, scopes, exclusions)
