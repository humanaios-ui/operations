from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .proposition import PropositionCandidate

SOURCE_CLASSES = {
    "OFFICIAL_PRIMARY",
    "FIRST_PARTY_OPERATIONAL",
    "DIRECT_SOURCE",
    "SECONDARY_REPORT",
    "AGGREGATOR",
    "UNKNOWN",
}
PRIMARY_CLASSES = {"OFFICIAL_PRIMARY", "FIRST_PARTY_OPERATIONAL", "DIRECT_SOURCE"}


@dataclass(frozen=True)
class SourceStandingProfile:
    schema: str
    profile_id: str
    origin_key: str
    source_class: str
    standing_for_types: list[str] = field(default_factory=list)
    standing_for_predicates: list[str] = field(default_factory=list)
    independence_group: str = ""
    notes: list[str] = field(default_factory=list)
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_source_standing_id(origin_key: str, source_class: str) -> str:
    payload = "\0".join(
        [origin_key.strip().casefold(), source_class.strip().upper()]
    )
    return "SSP-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def source_standing_from_dict(data: dict[str, Any]) -> SourceStandingProfile:
    source_class = str(data.get("source_class") or "UNKNOWN").strip().upper()
    if source_class not in SOURCE_CLASSES:
        raise ValueError(f"unsupported source_class: {source_class}")
    origin_key = str(data.get("origin_key") or "").strip().casefold()
    if not origin_key:
        raise ValueError("source standing requires origin_key")
    authority_effect = str(data.get("authority_effect") or "NONE").strip().upper()
    if authority_effect != "NONE":
        raise ValueError("source standing cannot grant authority")
    return SourceStandingProfile(
        schema=str(data.get("schema") or "humanaios.source-standing-profile.v1"),
        profile_id=str(
            data.get("profile_id")
            or stable_source_standing_id(origin_key, source_class)
        ),
        origin_key=origin_key,
        source_class=source_class,
        standing_for_types=sorted(
            {str(x).strip().upper() for x in data.get("standing_for_types") or []}
        ),
        standing_for_predicates=sorted(
            {str(x).strip().casefold() for x in data.get("standing_for_predicates") or []}
        ),
        independence_group=str(data.get("independence_group") or origin_key).strip().casefold(),
        notes=[str(x) for x in data.get("notes") or []],
        authority_effect="NONE",
    )


def load_source_standing(path: str | Path) -> list[SourceStandingProfile]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("source-standing registry must be a list")
    rows = [source_standing_from_dict(row) for row in payload if isinstance(row, dict)]
    ids = [row.profile_id for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("source-standing registry contains duplicate profile IDs")
    return rows


def profile_applies(
    profile: SourceStandingProfile,
    proposition: PropositionCandidate,
) -> bool:
    if profile.origin_key != proposition.source_origin_key.casefold():
        return False
    type_ok = (
        not profile.standing_for_types
        or proposition.proposition_type.upper() in profile.standing_for_types
    )
    predicate_ok = (
        not profile.standing_for_predicates
        or proposition.predicate.casefold() in profile.standing_for_predicates
    )
    return type_ok and predicate_ok


def applicable_profiles(
    proposition: PropositionCandidate,
    profiles: Iterable[SourceStandingProfile],
) -> list[SourceStandingProfile]:
    return sorted(
        [row for row in profiles if profile_applies(row, proposition)],
        key=lambda row: row.profile_id,
    )
