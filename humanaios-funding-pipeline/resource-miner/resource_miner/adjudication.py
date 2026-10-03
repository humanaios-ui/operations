from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .proposition import PropositionCandidate
from .reconciliation import PropositionResolutionSet
from .source_standing import (
    PRIMARY_CLASSES,
    SourceStandingProfile,
    applicable_profiles,
)

POSTURES = {
    "PRIMARY_SOURCE_PRESENT",
    "MULTI_ORIGIN_NO_PRIMARY",
    "NONPRIMARY_SOURCE_ONLY",
    "DERIVED_ONLY",
    "CONTESTED",
    "UNRESOLVED",
    "SOURCE_STANDING_UNKNOWN",
}
GAP_TYPES = {
    "PRIMARY_SOURCE_MISSING",
    "DIRECT_EVIDENCE_MISSING",
    "CONFLICT_REQUIRES_RESOLUTION",
    "SOURCE_STANDING_UNKNOWN",
    "RELATION_UNRESOLVED",
}
DIRECT_EPISTEMIC_ROLES = {"OBSERVATION", "SOURCE_ASSERTION"}


@dataclass(frozen=True)
class VerificationFrontierItem:
    schema: str
    verification_id: str
    resolution_set_id: str
    adjudication_id: str
    gap_type: str
    requested_source_class: str
    proposition_type: str
    predicate: str
    subject_key: str
    reason: str
    state: str = "OPEN"
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PropositionAdjudication:
    schema: str
    adjudication_id: str
    adjudication_token: str
    resolution_set_id: str
    resolution_token: str
    posture: str
    member_proposition_ids: list[str]
    known_origin_keys: list[str]
    primary_origin_keys: list[str]
    nonprimary_origin_keys: list[str]
    unknown_origin_keys: list[str]
    standing_profile_ids: list[str]
    derived_only: bool
    verification_frontier: list[VerificationFrontierItem] = field(default_factory=list)
    truth_state: str = "NOT_DETERMINED"
    eligibility_state: str = "NOT_EVALUATED"
    warrant_state: str = "NOT_EVALUATED"
    authorization_state: str = "NOT_REQUESTED"
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["verification_frontier"] = [
            row.to_dict() for row in self.verification_frontier
        ]
        return data


def stable_adjudication_id(resolution_set_id: str) -> str:
    value = resolution_set_id.strip().upper()
    if not value:
        raise ValueError("resolution_set_id is required")
    return "PAD-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16].upper()


def adjudication_token(adjudication_id: str) -> str:
    return f"urn:humanaios:proposition-adjudication:{adjudication_id}"


def stable_verification_id(
    resolution_set_id: str,
    gap_type: str,
    requested_source_class: str,
    proposition_type: str,
    predicate: str,
) -> str:
    payload = "\0".join(
        [
            resolution_set_id.strip().upper(),
            gap_type.strip().upper(),
            requested_source_class.strip().upper(),
            proposition_type.strip().upper(),
            predicate.strip().casefold(),
        ]
    )
    return "VFY-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def _frontier_item(
    prs: PropositionResolutionSet,
    pad_id: str,
    *,
    gap_type: str,
    requested_source_class: str,
    reason: str,
) -> VerificationFrontierItem:
    if gap_type not in GAP_TYPES:
        raise ValueError(f"unsupported gap_type: {gap_type}")
    verification_id = stable_verification_id(
        prs.resolution_set_id,
        gap_type,
        requested_source_class,
        prs.proposition_type,
        prs.predicate,
    )
    return VerificationFrontierItem(
        schema="humanaios.verification-frontier-item.v1",
        verification_id=verification_id,
        resolution_set_id=prs.resolution_set_id,
        adjudication_id=pad_id,
        gap_type=gap_type,
        requested_source_class=requested_source_class,
        proposition_type=prs.proposition_type,
        predicate=prs.predicate,
        subject_key=prs.subject_key,
        reason=reason,
    )


def _member_profile_map(
    members: list[PropositionCandidate],
    profiles: list[SourceStandingProfile],
) -> dict[str, list[SourceStandingProfile]]:
    return {
        member.proposition_id: applicable_profiles(member, profiles)
        for member in members
    }


def adjudicate_resolution_set(
    prs: PropositionResolutionSet,
    members: list[PropositionCandidate],
    profiles: Iterable[SourceStandingProfile],
) -> PropositionAdjudication:
    profiles = list(profiles)
    pad_id = stable_adjudication_id(prs.resolution_set_id)
    profile_map = _member_profile_map(members, profiles)

    standing_profiles = {
        profile.profile_id: profile
        for rows in profile_map.values()
        for profile in rows
    }
    known_origins = sorted(
        {
            member.source_origin_key
            for member in members
            if profile_map.get(member.proposition_id)
        }
    )
    unknown_origins = sorted(
        {
            member.source_origin_key
            for member in members
            if not profile_map.get(member.proposition_id)
        }
    )

    primary_origins: set[str] = set()
    nonprimary_origins: set[str] = set()
    for member in members:
        rows = profile_map.get(member.proposition_id) or []
        for profile in rows:
            if profile.source_class in PRIMARY_CLASSES:
                primary_origins.add(member.source_origin_key)
            else:
                nonprimary_origins.add(member.source_origin_key)

    derived_only = bool(members) and all(
        member.epistemic_role not in DIRECT_EPISTEMIC_ROLES
        for member in members
    )

    if prs.state == "CONTESTED":
        posture = "CONTESTED"
    elif prs.state == "UNRESOLVED":
        posture = "UNRESOLVED"
    elif derived_only:
        posture = "DERIVED_ONLY"
    elif primary_origins:
        posture = "PRIMARY_SOURCE_PRESENT"
    elif prs.distinct_origin_count >= 2:
        posture = "MULTI_ORIGIN_NO_PRIMARY"
    elif unknown_origins:
        posture = "SOURCE_STANDING_UNKNOWN"
    else:
        posture = "NONPRIMARY_SOURCE_ONLY"

    frontier: list[VerificationFrontierItem] = []

    if prs.state == "CONTESTED":
        frontier.append(
            _frontier_item(
                prs,
                pad_id,
                gap_type="CONFLICT_REQUIRES_RESOLUTION",
                requested_source_class="OFFICIAL_PRIMARY",
                reason=(
                    "Reconciled propositions conflict; acquire current primary evidence "
                    "or an explicit resolver decision instead of selecting a winner by count."
                ),
            )
        )

    if prs.state == "UNRESOLVED":
        frontier.append(
            _frontier_item(
                prs,
                pad_id,
                gap_type="RELATION_UNRESOLVED",
                requested_source_class="OFFICIAL_PRIMARY",
                reason=(
                    "The relationship among member propositions is not safely inferable; "
                    "seek evidence that disambiguates scope, time, or meaning."
                ),
            )
        )

    if derived_only:
        frontier.append(
            _frontier_item(
                prs,
                pad_id,
                gap_type="DIRECT_EVIDENCE_MISSING",
                requested_source_class="DIRECT_SOURCE",
                reason=(
                    "All member propositions are classifications or text extractions; "
                    "seek a direct observation or explicit source assertion for this predicate."
                ),
            )
        )

    if not primary_origins:
        frontier.append(
            _frontier_item(
                prs,
                pad_id,
                gap_type="PRIMARY_SOURCE_MISSING",
                requested_source_class="OFFICIAL_PRIMARY",
                reason=(
                    "No applicable primary-source standing is present for this proposition; "
                    "independent secondary agreement is insufficient by itself."
                ),
            )
        )

    if unknown_origins:
        frontier.append(
            _frontier_item(
                prs,
                pad_id,
                gap_type="SOURCE_STANDING_UNKNOWN",
                requested_source_class="OFFICIAL_PRIMARY",
                reason=(
                    "At least one evidence origin has no scoped standing profile for this "
                    "proposition; verify the source role before relying on it."
                ),
            )
        )

    dedup = {row.verification_id: row for row in frontier}
    frontier = [dedup[key] for key in sorted(dedup)]

    return PropositionAdjudication(
        schema="humanaios.proposition-adjudication.v1",
        adjudication_id=pad_id,
        adjudication_token=adjudication_token(pad_id),
        resolution_set_id=prs.resolution_set_id,
        resolution_token=prs.resolution_token,
        posture=posture,
        member_proposition_ids=sorted(row.proposition_id for row in members),
        known_origin_keys=known_origins,
        primary_origin_keys=sorted(primary_origins),
        nonprimary_origin_keys=sorted(nonprimary_origins),
        unknown_origin_keys=unknown_origins,
        standing_profile_ids=sorted(standing_profiles),
        derived_only=derived_only,
        verification_frontier=frontier,
    )


def adjudicate_resolution_sets(
    resolution_sets: Iterable[PropositionResolutionSet],
    propositions: Iterable[PropositionCandidate],
    profiles: Iterable[SourceStandingProfile],
) -> list[PropositionAdjudication]:
    proposition_map = {row.proposition_id: row for row in propositions}
    profiles = list(profiles)
    output: list[PropositionAdjudication] = []
    for prs in sorted(resolution_sets, key=lambda row: row.resolution_set_id):
        members = [
            proposition_map[pid]
            for pid in prs.member_proposition_ids
            if pid in proposition_map
        ]
        output.append(adjudicate_resolution_set(prs, members, profiles))
    return output


def write_adjudications_jsonl(
    path: str | Path,
    adjudications: Iterable[PropositionAdjudication],
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(
            json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
            for row in adjudications
        ),
        encoding="utf-8",
    )


def write_verification_frontier_jsonl(
    path: str | Path,
    adjudications: Iterable[PropositionAdjudication],
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        item
        for adjudication in adjudications
        for item in adjudication.verification_frontier
    ]
    target.write_text(
        "".join(
            json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
            for row in sorted(rows, key=lambda row: row.verification_id)
        ),
        encoding="utf-8",
    )
