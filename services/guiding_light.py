"""Guiding Light — domain-neutral evidence-to-target gradient engine.

The engine consumes already-mapped target requirements. It does not infer facts from
raw resumes, grant listings, entitlement records, procurement notices, or project
documents. Domain adapters are responsible for preserving provenance and uncertainty.

The engine answers:
- what is reachable from the current mapped evidence state,
- which targets are bridge/frontier states,
- what evidence/capability delta remains,
- which bounded intervention class corresponds to that delta.

It never grants authority to take a consequential action.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from integrations.schemas import Event, EventType


MAPPING_SCORE = {
    "DOCUMENTED": 1.00,
    "USER_ATTESTED": 0.80,
    "TRANSFERABLE": 0.70,
    "PARTIAL": 0.50,
    "PLANNED": 0.25,
    "UNKNOWN": 0.00,
    "NOT_HELD": 0.00,
    "BLOCKED": 0.00,
}

HARD_BLOCKERS = {"NOT_HELD", "BLOCKED"}

INTERVENTION_FOR_GAP = {
    "unknown": "INTERROGATE",
    "knowledge": "LEARN",
    "evidence": "BUILD_EVIDENCE",
    "credential": "CREDENTIAL_DECISION",
    "experience": "EXPERIENCE_REQUIRED",
    "authority": "VERIFY_AUTHORITY",
    "partnership": "FIND_PARTNER",
    "resource": "ACQUIRE_RESOURCE",
    "capability": "BUILD_CAPABILITY",
    "blocker": "RESOLVE_BLOCKER",
}


@dataclass(frozen=True)
class TargetResult:
    target_id: str
    title: str
    domain: str
    actionability: float
    gradient: float
    classification: str
    assessment_state: str
    mandatory_blockers: tuple[str, ...]
    mandatory_unknowns: tuple[str, ...]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _requirement_label(requirement: dict[str, Any]) -> str:
    return str(
        requirement.get("label")
        or requirement.get("capability")
        or requirement.get("id")
        or "unnamed requirement"
    )


def _gradient_score(target: dict[str, Any]) -> float:
    axes = target.get("value_axes") or target.get("gradient_axes") or {}
    if not axes:
        return 0.0
    values = [_clamp01(v) for v in axes.values()]
    return sum(values) / len(values)


def score_target(target: dict[str, Any]) -> TargetResult:
    """Score one mapped target without inferring missing evidence.

    REACHABLE means high evidence coverage with no mandatory blocker/unknown and a
    comparatively low option-value gradient. BRIDGE and FRONTIER indicate increasing
    delta to a higher-value target. HOLD includes hard blockers, unmapped targets, or
    low-actionability/low-gradient states.
    """
    requirements = target.get("requirements") or []
    if not requirements:
        return TargetResult(
            target_id=str(target.get("id") or target.get("target_id") or ""),
            title=str(target.get("title", "Untitled target")),
            domain=str(target.get("domain", "custom")),
            actionability=0.0,
            gradient=round(_gradient_score(target), 4),
            classification="HOLD",
            assessment_state="UNMAPPED",
            mandatory_blockers=(),
            mandatory_unknowns=(),
        )

    weighted_total = 0.0
    weighted_covered = 0.0
    blockers: list[str] = []
    unknowns: list[str] = []

    for requirement in requirements:
        weight = max(0.0, float(requirement.get("weight", 1.0)))
        state = str(requirement.get("mapping_state", "UNKNOWN")).upper()
        if state not in MAPPING_SCORE:
            state = "UNKNOWN"

        weighted_total += weight
        weighted_covered += weight * MAPPING_SCORE[state]

        if requirement.get("mandatory") and state in HARD_BLOCKERS:
            blockers.append(_requirement_label(requirement))
        if requirement.get("mandatory") and state == "UNKNOWN":
            unknowns.append(_requirement_label(requirement))

    actionability = weighted_covered / weighted_total if weighted_total else 0.0
    gradient = _gradient_score(target)

    if blockers:
        classification = "HOLD"
        assessment_state = "BLOCKED"
    elif unknowns:
        # Unknown mandatory predicates are never "reachable now". A high-value target
        # remains visible as a frontier specification until the unknown is resolved.
        classification = "FRONTIER" if gradient >= 0.55 else "HOLD"
        assessment_state = "INVESTIGATE"
    elif actionability >= 0.80 and gradient < 0.55:
        classification = "REACHABLE"
        assessment_state = "MAPPED"
    elif actionability >= 0.55 and gradient >= 0.55:
        classification = "BRIDGE"
        assessment_state = "MAPPED"
    elif actionability < 0.55 and gradient >= 0.55:
        classification = "FRONTIER"
        assessment_state = "MAPPED"
    else:
        classification = "HOLD"
        assessment_state = "MAPPED"

    return TargetResult(
        target_id=str(target.get("id") or target.get("target_id") or ""),
        title=str(target.get("title", "Untitled target")),
        domain=str(target.get("domain", "custom")),
        actionability=round(actionability, 4),
        gradient=round(gradient, 4),
        classification=classification,
        assessment_state=assessment_state,
        mandatory_blockers=tuple(blockers),
        mandatory_unknowns=tuple(unknowns),
    )


def intervention_priorities(targets: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate unresolved requirements across targets into evidence-producing actions."""
    aggregate: dict[str, dict[str, Any]] = {}

    for target in targets:
        result = score_target(target)
        target_value = _clamp01(
            target.get("target_value", target.get("opportunity_value", 0.5))
        )
        pathway_factor = {
            "FRONTIER": 1.00,
            "BRIDGE": 0.85,
            "REACHABLE": 0.35,
            "HOLD": 0.20,
        }[result.classification]

        for requirement in target.get("requirements") or []:
            state = str(requirement.get("mapping_state", "UNKNOWN")).upper()
            score = MAPPING_SCORE.get(state, 0.0)
            if score >= 0.75:
                continue

            label = _requirement_label(requirement)
            gap_type = str(requirement.get("gap_type", "unknown")).lower()
            row = aggregate.setdefault(
                label,
                {
                    "requirement": label,
                    "gap_type": gap_type,
                    "action": INTERVENTION_FOR_GAP.get(gap_type, "INTERROGATE"),
                    "priority": 0.0,
                    "targets": [],
                    "artifact_targets": [],
                },
            )

            weight = max(0.0, float(requirement.get("weight", 1.0)))
            delta = 1.0 - score
            row["priority"] += (
                weight
                * delta
                * max(result.gradient, 0.1)
                * target_value
                * pathway_factor
            )
            row["targets"].append(result.target_id)

            artifact = requirement.get("artifact_target")
            if artifact:
                row["artifact_targets"].append(str(artifact))

    rows = list(aggregate.values())
    for row in rows:
        row["priority"] = round(row["priority"], 4)
        row["targets"] = sorted(set(row["targets"]))
        row["artifact_targets"] = sorted(set(row["artifact_targets"]))

    rows.sort(key=lambda row: (-row["priority"], row["requirement"]))
    return rows


def evaluate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    results = [score_target(target) for target in snapshot.get("targets") or []]
    output = dict(snapshot)
    output["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    output["results"] = [
        {
            "target_id": row.target_id,
            "title": row.title,
            "domain": row.domain,
            "actionability": row.actionability,
            "gradient": row.gradient,
            "classification": row.classification,
            "assessment_state": row.assessment_state,
            "mandatory_blockers": list(row.mandatory_blockers),
            "mandatory_unknowns": list(row.mandatory_unknowns),
        }
        for row in results
    ]
    output["intervention_priorities"] = intervention_priorities(
        snapshot.get("targets") or []
    )
    return output


def canonical_hash(snapshot: dict[str, Any]) -> str:
    stable = {
        key: value
        for key, value in snapshot.items()
        if key not in {"evaluated_at", "witness_observation"}
    }
    raw = json.dumps(
        stable,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_witness_observation(snapshot: dict[str, Any]) -> dict[str, Any]:
    evaluated = evaluate_snapshot(snapshot)
    return {
        "observation_type": "guiding_light_gradient",
        "schema_version": "0.2.0",
        "observed_at": evaluated["evaluated_at"],
        "snapshot_sha256": canonical_hash(snapshot),
        "subject": snapshot.get("subject", {}),
        "domain": snapshot.get("domain", "custom"),
        "declared_goal_source": snapshot.get("declared_goal_source", "user"),
        "selected_target": snapshot.get("selected_target"),
        "results": evaluated["results"],
        "intervention_priorities": evaluated["intervention_priorities"],
        "source_refs": snapshot.get("source_refs", []),
        "omissions": snapshot.get("omissions", []),
        "uncertainty": snapshot.get("uncertainty", []),
        "non_authority_invariant": "WITNESS_IS_NOT_THE_AUTHORITY",
        "authorization": {
            "state": "NOT_GRANTED_BY_WITNESS",
            "note": (
                "Guiding Light and the Witness expose evidence, deltas, and reachable "
                "states. Consequential action remains human- or authority-authorized."
            ),
        },
    }


def events_for_snapshot(snapshot: dict[str, Any]) -> list[Event]:
    evaluated = evaluate_snapshot(snapshot)
    now = datetime.now(timezone.utc)
    events: list[Event] = []

    for row in evaluated["results"]:
        events.append(
            Event(
                timestamp=now,
                service="GuidingLight",
                event_type=EventType.TARGET_MAPPED,
                resource_id=row["target_id"],
                title=f"{row['classification']}: {row['title']}",
                data=row,
                actor="guiding_light_v0_2",
            )
        )

    for idx, row in enumerate(evaluated["intervention_priorities"], 1):
        events.append(
            Event(
                timestamp=now,
                service="GuidingLight",
                event_type=EventType.INTERVENTION_SIGNAL,
                resource_id=f"intervention-{idx}",
                title=f"{row['action']}: {row['requirement']}",
                data=row,
                actor="guiding_light_v0_2",
            )
        )

    return events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("snapshot", help="Guiding Light mapped-target snapshot JSON")
    parser.add_argument(
        "--witness",
        action="store_true",
        help="emit Witness observation instead of evaluated snapshot",
    )
    args = parser.parse_args()

    data = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    result = build_witness_observation(data) if args.witness else evaluate_snapshot(data)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
