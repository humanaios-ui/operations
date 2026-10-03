from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .models import ResourceMine
from .work_queue import VerificationWorkItem

ROUTE_TYPES = {
    "EXISTING_MINE_REOBSERVE",
    "KNOWN_ORIGIN_REVIEW",
    "DISCOVERY_REQUIRED",
    "RESOLVER_REQUIRED",
    "SOURCE_STANDING_REVIEW",
}
CAPABILITY_STATES = {
    "AVAILABLE",
    "UNBOUND",
    "DISCOVERY_REQUIRED",
    "RESOLVER_REQUIRED",
    "REVIEW_REQUIRED",
}


@dataclass(frozen=True)
class VerificationRoute:
    schema: str
    route_id: str
    work_id: str
    verification_id: str
    adjudication_id: str
    resolution_set_id: str
    subject_key: str
    route_type: str
    target_mine_ids: list[str]
    target_origin_keys: list[str]
    capability_state: str
    execution_state: str = "NOT_AUTHORIZED"
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_route_id(work_id: str, route_type: str, targets: Iterable[str]) -> str:
    payload = "\0".join(
        [
            work_id.strip().upper(),
            route_type.strip().upper(),
            *sorted(str(x).strip().casefold() for x in targets if str(x).strip()),
        ]
    )
    return "VRT-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def _mine_origin_map(mines: Iterable[ResourceMine]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for mine in mines:
        origins = mine.config.get("evidence_origins") or []
        for origin in origins:
            key = str(origin).strip().casefold()
            if not key:
                continue
            mapping.setdefault(key, []).append(mine.mine_id)
    return {key: sorted(set(value)) for key, value in mapping.items()}


def _route_for_work(
    work: VerificationWorkItem,
    mine_origin_map: dict[str, list[str]],
) -> VerificationRoute:
    operation = work.operation_class
    target_origins = sorted(set(work.candidate_origin_keys))
    target_mines: list[str] = []

    if operation == "DISCOVER_PRIMARY_SOURCE":
        route_type = "DISCOVERY_REQUIRED"
        capability_state = "DISCOVERY_REQUIRED"
        target_origins = []
    elif operation == "RESOLVE_CONFLICT":
        route_type = "RESOLVER_REQUIRED"
        capability_state = "RESOLVER_REQUIRED"
    elif operation == "ASSESS_SOURCE_STANDING":
        route_type = "SOURCE_STANDING_REVIEW"
        capability_state = "REVIEW_REQUIRED"
    elif operation == "DISAMBIGUATE_RELATION":
        route_type = "DISCOVERY_REQUIRED"
        capability_state = "DISCOVERY_REQUIRED"
    elif operation == "SEEK_DIRECT_EVIDENCE":
        for origin in target_origins:
            target_mines.extend(mine_origin_map.get(origin.casefold(), []))
        target_mines = sorted(set(target_mines))
        if target_mines:
            route_type = "EXISTING_MINE_REOBSERVE"
            capability_state = "AVAILABLE"
        elif target_origins:
            route_type = "KNOWN_ORIGIN_REVIEW"
            capability_state = "UNBOUND"
        else:
            route_type = "DISCOVERY_REQUIRED"
            capability_state = "DISCOVERY_REQUIRED"
    else:
        raise ValueError(f"unsupported verification operation: {operation}")

    route_targets = [*target_origins, *target_mines]
    return VerificationRoute(
        schema="humanaios.verification-route.v1",
        route_id=stable_route_id(work.work_id, route_type, route_targets),
        work_id=work.work_id,
        verification_id=work.verification_id,
        adjudication_id=work.adjudication_id,
        resolution_set_id=work.resolution_set_id,
        subject_key=work.subject_key,
        route_type=route_type,
        target_mine_ids=target_mines,
        target_origin_keys=target_origins,
        capability_state=capability_state,
    )


def compile_verification_routes(
    work_items: Iterable[VerificationWorkItem],
    mines: Iterable[ResourceMine],
) -> list[VerificationRoute]:
    origin_map = _mine_origin_map(mines)
    routes = [_route_for_work(item, origin_map) for item in work_items]
    unique = {row.route_id: row for row in routes}
    return [unique[key] for key in sorted(unique)]


def write_verification_routes_jsonl(
    path: str | Path,
    routes: Iterable[VerificationRoute],
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(
            json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
            for row in sorted(routes, key=lambda row: row.route_id)
        ),
        encoding="utf-8",
    )
