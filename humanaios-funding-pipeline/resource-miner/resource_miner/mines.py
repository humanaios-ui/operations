from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .models import EvidenceRef, MineResolutionReceipt, ResourceCandidate, ResourceMine
from .normalize import canonicalize_url, utcnow_iso

MINE_KINDS = {
    "PROGRAM_PLATFORM",
    "MARKETPLACE",
    "REGISTRY",
    "GITHUB_REPOSITORY",
    "FEED",
}
MINE_ROLES = {
    "OPPORTUNITY_SOURCE",
    "EVIDENCE_SOURCE",
    "GOVERNED_SYSTEM",
    "CONTROLLED_RESOURCE_SOURCE",
}


def stable_mine_id(canonical_url: str) -> str:
    canonical = canonicalize_url(canonical_url)
    return "MINE-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16].upper()


def _identity_text(identity: str) -> str:
    value = identity.strip()
    if value.startswith(("http://", "https://")):
        return canonicalize_url(value)
    return " ".join(value.split()).casefold()


def stable_opportunity_id(mine_id: str, identity: str, opportunity_kind: str = "") -> str:
    normalized_identity = _identity_text(identity)
    if not normalized_identity:
        raise ValueError("opportunity identity is required")
    identity_text = "\0".join(
        [mine_id.strip().upper(), normalized_identity, opportunity_kind.strip().lower()]
    )
    return "OPP-" + hashlib.sha256(identity_text.encode("utf-8")).hexdigest()[:16].upper()


def opportunity_token(opportunity_id: str) -> str:
    return f"urn:humanaios:resource-opportunity:{opportunity_id}"


def _mine_from_row(row: dict) -> ResourceMine:
    name = str(row.get("name") or "").strip()
    canonical_url = str(row.get("canonical_url") or "").strip()
    mine_kind = str(row.get("mine_kind") or "").strip().upper()
    resolver = str(row.get("resolver") or "").strip()
    if not name or not canonical_url or not mine_kind or not resolver:
        raise ValueError("mine requires name, canonical_url, mine_kind, and resolver")
    if mine_kind not in MINE_KINDS:
        raise ValueError(f"unsupported mine_kind: {mine_kind}")
    roles = [str(x).strip().upper() for x in row.get("roles") or []]
    unknown_roles = [x for x in roles if x not in MINE_ROLES]
    if unknown_roles:
        raise ValueError(f"unsupported mine roles: {unknown_roles}")
    mine_id = str(row.get("mine_id") or stable_mine_id(canonical_url))
    return ResourceMine(
        mine_id=mine_id,
        name=name,
        mine_kind=mine_kind,
        canonical_url=canonicalize_url(canonical_url),
        resolver=resolver,
        enabled=bool(row.get("enabled", True)),
        cadence=str(row.get("cadence") or "daily"),
        roles=roles,
        config=dict(row.get("config") or {}),
    )


def load_mines(path: str | Path) -> list[ResourceMine]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("mine registry must be a JSON list")
    mines = [_mine_from_row(row) for row in payload if isinstance(row, dict)]
    ids = [mine.mine_id for mine in mines]
    if len(ids) != len(set(ids)):
        raise ValueError("mine registry contains duplicate mine_id values")
    return mines


def bind_opportunity(
    mine: ResourceMine,
    candidate: ResourceCandidate,
    *,
    opportunity_source_kind: str,
) -> ResourceCandidate:
    kind = candidate.opportunity_kind or opportunity_source_kind
    identity = candidate.opportunity_identity or candidate.canonical_url
    candidate.mine_id = mine.mine_id
    candidate.mine_name = mine.name
    candidate.mine_url = mine.canonical_url
    candidate.opportunity_identity = identity
    candidate.opportunity_kind = kind
    candidate.opportunity_source_kind = opportunity_source_kind
    candidate.opportunity_id = stable_opportunity_id(mine.mine_id, identity, kind)
    candidate.opportunity_token = opportunity_token(candidate.opportunity_id)
    return candidate


def _resolve_configured(mine: ResourceMine) -> list[ResourceCandidate]:
    from .sources.configured_mine import discover

    return list(discover(mine))


def _resolve_github_repository(mine: ResourceMine) -> list[ResourceCandidate]:
    from .sources.github_repository import discover

    return list(discover(mine))


def _resolve_hackerone(mine: ResourceMine) -> list[ResourceCandidate]:
    # Require scope-hydrated portfolio support from #680/#683. Program-level
    # discovery alone is intentionally insufficient: the bounded opportunity is
    # Program x bounty-eligible ScopeAsset.
    try:
        from .hackerone_portfolio import scan_portfolio
        from .sources.hackerone import HackerOneClient
    except ImportError as exc:
        raise ModuleNotFoundError(
            "HackerOne scope-hydrated resolver dependency is not present"
        ) from exc

    snapshot = scan_portfolio(HackerOneClient())
    out: list[ResourceCandidate] = []
    from .normalize import normalize_generic

    for program in snapshot.programs:
        graph = program.graph
        if graph is None or program.state != "OBSERVED":
            continue
        for asset in graph.assets:
            if not asset.eligible_for_bounty:
                continue
            actual_url = f"https://hackerone.com/{graph.handle}?type=team"
            identity = f"hackerone:{graph.handle}:scope:{asset.scope_id}"
            candidate = normalize_generic(
                title=f"{graph.name} — {asset.asset_identifier}",
                url=actual_url,
                source_name="HackerOne",
                discovery_method="persistent_mine:hackerone_portfolio",
                description=(
                    f"Bounty-eligible HackerOne scope asset; asset_type={asset.asset_type}; "
                    f"max_severity={asset.max_severity or 'unknown'}."
                ),
                sponsor=graph.name,
                tags=["hackerone", "bug-bounty", asset.asset_type.lower()],
                body_text=asset.instruction or "",
                observed_at=snapshot.observed_at,
                mine_name=mine.name,
                mine_url=mine.canonical_url,
                opportunity_identity=identity,
                opportunity_kind="hackerone_bounty_scope",
                opportunity_source_kind="hackerone_scope_asset",
                raw={
                    "program_handle": graph.handle,
                    "program_id": graph.program_id,
                    "scope_id": asset.scope_id,
                    "asset_identifier": asset.asset_identifier,
                    "eligible_for_bounty": asset.eligible_for_bounty,
                    "eligible_for_submission": asset.eligible_for_submission,
                    "max_severity": asset.max_severity,
                    "reference": asset.reference,
                    "updated_at": asset.updated_at,
                    "authority_effect": "NONE",
                    "execution_capability": "NONE",
                },
            )
            candidate.evidence.append(
                EvidenceRef(
                    url=actual_url,
                    kind="hackerone_scope",
                    observed_at=snapshot.observed_at,
                    claim=(
                        "Authenticated HackerOne scope observation: "
                        f"scope_id={asset.scope_id}; eligible_for_bounty=true"
                    ),
                )
            )
            if "bounty" not in candidate.resource_types:
                candidate.resource_types.append("bounty")
            out.append(candidate)
    return out


def resolve_mines(
    mines: Iterable[ResourceMine],
    *,
    observed_at: str | None = None,
) -> tuple[list[ResourceCandidate], list[MineResolutionReceipt]]:
    observed_at = observed_at or utcnow_iso()
    opportunities: list[ResourceCandidate] = []
    receipts: list[MineResolutionReceipt] = []

    resolvers = {
        "configured_mine": _resolve_configured,
        "github_repository": _resolve_github_repository,
        "hackerone_api": _resolve_hackerone,
    }

    for mine in mines:
        if not mine.enabled:
            receipts.append(
                MineResolutionReceipt(
                    mine_id=mine.mine_id,
                    mine_name=mine.name,
                    resolver=mine.resolver,
                    observed_at=observed_at,
                    state="DISABLED",
                )
            )
            continue

        if "OPPORTUNITY_SOURCE" not in mine.roles:
            receipts.append(
                MineResolutionReceipt(
                    mine_id=mine.mine_id,
                    mine_name=mine.name,
                    resolver=mine.resolver,
                    observed_at=observed_at,
                    state="ROLE_ONLY",
                )
            )
            continue

        resolver = resolvers.get(mine.resolver)
        if resolver is None:
            receipts.append(
                MineResolutionReceipt(
                    mine_id=mine.mine_id,
                    mine_name=mine.name,
                    resolver=mine.resolver,
                    observed_at=observed_at,
                    state="RESOLVER_UNAVAILABLE",
                    error_type="UnknownResolver",
                )
            )
            continue

        try:
            rows = resolver(mine)
            bound = [
                bind_opportunity(
                    mine,
                    candidate,
                    opportunity_source_kind=(
                        candidate.opportunity_source_kind or mine.resolver
                    ),
                )
                for candidate in rows
            ]
            opportunities.extend(bound)
            receipts.append(
                MineResolutionReceipt(
                    mine_id=mine.mine_id,
                    mine_name=mine.name,
                    resolver=mine.resolver,
                    observed_at=observed_at,
                    state="RESOLVED",
                    opportunity_count=len(bound),
                    opportunity_ids=[row.opportunity_id for row in bound],
                )
            )
        except ModuleNotFoundError as exc:
            receipts.append(
                MineResolutionReceipt(
                    mine_id=mine.mine_id,
                    mine_name=mine.name,
                    resolver=mine.resolver,
                    observed_at=observed_at,
                    state="DEPENDENCY_PENDING",
                    error_type=type(exc).__name__,
                )
            )
        except Exception as exc:
            # Never persist transport headers, credentials, or response bodies in
            # resolution receipts. Error class is sufficient for routing.
            receipts.append(
                MineResolutionReceipt(
                    mine_id=mine.mine_id,
                    mine_name=mine.name,
                    resolver=mine.resolver,
                    observed_at=observed_at,
                    state="OBSERVATION_FAILED",
                    error_type=type(exc).__name__,
                )
            )

    return opportunities, receipts


def receipts_to_jsonl(receipts: Iterable[MineResolutionReceipt]) -> str:
    return "".join(
        json.dumps(asdict(receipt), sort_keys=True) + "\n" for receipt in receipts
    )
