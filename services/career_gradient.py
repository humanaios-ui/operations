"""Guiding Light Career Gradient Pathway — deterministic v0.1 scorer.

Consumes already-mapped opportunity requirements. It does not perform semantic resume
matching and does not infer missing credentials or experience.
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

ACTION_FOR_GAP = {
    "unknown": "INTERROGATE",
    "knowledge": "LEARN",
    "evidence": "BUILD_EVIDENCE",
    "credential": "CREDENTIAL_DECISION",
    "experience": "EXPERIENCE_REQUIRED",
    "blocker": "BLOCKER",
}


@dataclass(frozen=True)
class OpportunityResult:
    opportunity_id: str
    title: str
    actionability: float
    gradient: float
    classification: str
    mandatory_blockers: tuple[str, ...]
    mandatory_unknowns: tuple[str, ...]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _gradient_score(opportunity: dict[str, Any]) -> float:
    axes = opportunity.get("gradient_axes") or {}
    if not axes:
        return 0.0
    values = [_clamp01(v) for v in axes.values()]
    return sum(values) / len(values)


def score_opportunity(opportunity: dict[str, Any]) -> OpportunityResult:
    requirements = opportunity.get("requirements") or []
    weighted_total = 0.0
    weighted_covered = 0.0
    blockers: list[str] = []
    unknowns: list[str] = []

    for req in requirements:
        weight = max(0.0, float(req.get("weight", 1.0)))
        state = str(req.get("mapping_state", "UNKNOWN")).upper()
        if state not in MAPPING_SCORE:
            state = "UNKNOWN"
        weighted_total += weight
        weighted_covered += weight * MAPPING_SCORE[state]
        if req.get("mandatory") and state in HARD_BLOCKERS:
            blockers.append(str(req.get("capability") or req.get("id") or "unnamed requirement"))
        if req.get("mandatory") and state == "UNKNOWN":
            unknowns.append(str(req.get("capability") or req.get("id") or "unnamed requirement"))

    actionability = weighted_covered / weighted_total if weighted_total else 0.0
    gradient = _gradient_score(opportunity)

    if blockers:
        classification = "HOLD"
    elif actionability >= 0.80 and gradient < 0.55:
        classification = "HARVEST"
    elif actionability >= 0.55 and gradient >= 0.55:
        classification = "BRIDGE"
    elif actionability < 0.55 and gradient >= 0.55:
        classification = "FRONTIER"
    else:
        classification = "HOLD"

    return OpportunityResult(
        opportunity_id=str(opportunity.get("id", "")),
        title=str(opportunity.get("title", "Untitled opportunity")),
        actionability=round(actionability, 4),
        gradient=round(gradient, 4),
        classification=classification,
        mandatory_blockers=tuple(blockers),
        mandatory_unknowns=tuple(unknowns),
    )


def learning_priorities(opportunities: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregate: dict[str, dict[str, Any]] = {}
    for opp in opportunities:
        result = score_opportunity(opp)
        opportunity_value = _clamp01(opp.get("opportunity_value", 0.5))
        # Frontier/bridge roles should influence the learning queue more than harvest roles.
        pathway_factor = {"FRONTIER": 1.0, "BRIDGE": 0.85, "HARVEST": 0.35, "HOLD": 0.20}[result.classification]
        for req in opp.get("requirements") or []:
            state = str(req.get("mapping_state", "UNKNOWN")).upper()
            score = MAPPING_SCORE.get(state, 0.0)
            if score >= 0.75:
                continue
            capability = str(req.get("capability") or req.get("id") or "unnamed requirement")
            gap_type = str(req.get("gap_type", "unknown")).lower()
            row = aggregate.setdefault(capability, {
                "capability": capability,
                "gap_type": gap_type,
                "action": ACTION_FOR_GAP.get(gap_type, "INTERROGATE"),
                "priority": 0.0,
                "roles": [],
            })
            weight = max(0.0, float(req.get("weight", 1.0)))
            delta = 1.0 - score
            row["priority"] += weight * delta * max(result.gradient, 0.1) * opportunity_value * pathway_factor
            row["roles"].append(result.opportunity_id)

    rows = list(aggregate.values())
    for row in rows:
        row["priority"] = round(row["priority"], 4)
        row["roles"] = sorted(set(row["roles"]))
    rows.sort(key=lambda r: (-r["priority"], r["capability"]))
    return rows


def evaluate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    results = [score_opportunity(o) for o in snapshot.get("opportunities") or []]
    output = dict(snapshot)
    output["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    output["results"] = [
        {
            "opportunity_id": r.opportunity_id,
            "title": r.title,
            "actionability": r.actionability,
            "gradient": r.gradient,
            "classification": r.classification,
            "mandatory_blockers": list(r.mandatory_blockers),
            "mandatory_unknowns": list(r.mandatory_unknowns),
        }
        for r in results
    ]
    output["learning_priorities"] = learning_priorities(snapshot.get("opportunities") or [])
    return output


def canonical_hash(snapshot: dict[str, Any]) -> str:
    stable = {k: v for k, v in snapshot.items() if k not in {"evaluated_at", "witness_observation"}}
    raw = json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_witness_observation(snapshot: dict[str, Any]) -> dict[str, Any]:
    evaluated = evaluate_snapshot(snapshot)
    return {
        "observation_type": "career_gradient",
        "schema_version": "0.1.0",
        "observed_at": evaluated["evaluated_at"],
        "snapshot_sha256": canonical_hash(snapshot),
        "profile_id": snapshot.get("profile_id"),
        "declared_goal_source": snapshot.get("declared_goal_source", "user"),
        "selected_target": snapshot.get("selected_target"),
        "results": evaluated["results"],
        "learning_priorities": evaluated["learning_priorities"],
        "source_refs": snapshot.get("source_refs", []),
        "omissions": snapshot.get("omissions", []),
        "uncertainty": snapshot.get("uncertainty", []),
        "non_authority_invariant": "WITNESS_IS_NOT_THE_AUTHORITY",
        "authorization": {
            "state": "NOT_GRANTED_BY_WITNESS",
            "note": "Application, enrollment, purchase, and career-change decisions remain human-authorized.",
        },
    }


def events_for_snapshot(snapshot: dict[str, Any]) -> list[Event]:
    evaluated = evaluate_snapshot(snapshot)
    now = datetime.now(timezone.utc)
    events: list[Event] = []
    for row in evaluated["results"]:
        events.append(Event(
            timestamp=now,
            service="GuidingLight",
            event_type=EventType.OPPORTUNITY_MAPPED,
            resource_id=row["opportunity_id"],
            title=f"{row['classification']}: {row['title']}",
            data=row,
            actor="career_gradient_v0_1",
        ))
    for idx, row in enumerate(evaluated["learning_priorities"], 1):
        events.append(Event(
            timestamp=now,
            service="GuidingLight",
            event_type=EventType.LEARNING_SIGNAL,
            resource_id=f"learning-{idx}",
            title=f"{row['action']}: {row['capability']}",
            data=row,
            actor="career_gradient_v0_1",
        ))
    return events


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("snapshot", help="Guiding Light snapshot JSON")
    ap.add_argument("--witness", action="store_true", help="emit Witness observation instead of evaluated snapshot")
    args = ap.parse_args()

    data = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    result = build_witness_observation(data) if args.witness else evaluate_snapshot(data)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
