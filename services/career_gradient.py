"""Guiding Light Career Gradient Pathway — career adapter over the v0.2 core.

This preserves the v0.1 career-facing contract (HARVEST / BRIDGE / FRONTIER /
HOLD and learning_priorities) while delegating deterministic scoring to the
domain-neutral Guiding Light engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from integrations.schemas import Event, EventType
from services.guiding_light import (
    HARD_BLOCKERS,
    INTERVENTION_FOR_GAP,
    MAPPING_SCORE,
    canonical_hash,
    intervention_priorities,
    score_target,
)

ACTION_FOR_GAP = INTERVENTION_FOR_GAP


@dataclass(frozen=True)
class OpportunityResult:
    opportunity_id: str
    title: str
    actionability: float
    gradient: float
    classification: str
    mandatory_blockers: tuple[str, ...]
    mandatory_unknowns: tuple[str, ...]


def _to_target(opportunity: dict[str, Any]) -> dict[str, Any]:
    target = dict(opportunity)
    target["domain"] = "career"
    target["target_value"] = opportunity.get(
        "opportunity_value",
        opportunity.get("target_value", 0.5),
    )
    target["value_axes"] = opportunity.get(
        "gradient_axes",
        opportunity.get("value_axes", {}),
    )
    target["requirements"] = []
    for requirement in opportunity.get("requirements") or []:
        normalized = dict(requirement)
        normalized.setdefault(
            "label",
            requirement.get("capability")
            or requirement.get("id")
            or "unnamed requirement",
        )
        target["requirements"].append(normalized)
    return target


def score_opportunity(opportunity: dict[str, Any]) -> OpportunityResult:
    result = score_target(_to_target(opportunity))
    classification = {
        "REACHABLE": "HARVEST",
        "BRIDGE": "BRIDGE",
        "FRONTIER": "FRONTIER",
        "HOLD": "HOLD",
    }[result.classification]
    return OpportunityResult(
        opportunity_id=result.target_id,
        title=result.title,
        actionability=result.actionability,
        gradient=result.gradient,
        classification=classification,
        mandatory_blockers=result.mandatory_blockers,
        mandatory_unknowns=result.mandatory_unknowns,
    )


def learning_priorities(opportunities: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = intervention_priorities(_to_target(opportunity) for opportunity in opportunities)
    return [
        {
            "capability": row["requirement"],
            "gap_type": row["gap_type"],
            "action": row["action"],
            "priority": row["priority"],
            "roles": row["targets"],
            "artifact_targets": row.get("artifact_targets", []),
        }
        for row in rows
    ]


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
    output["learning_priorities"] = learning_priorities(
        snapshot.get("opportunities") or []
    )
    return output


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
            "note": (
                "Application, enrollment, purchase, and career-change decisions "
                "remain human-authorized."
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
                event_type=EventType.OPPORTUNITY_MAPPED,
                resource_id=row["opportunity_id"],
                title=f"{row['classification']}: {row['title']}",
                data=row,
                actor="career_gradient_v0_1",
            )
        )
    for idx, row in enumerate(evaluated["learning_priorities"], 1):
        events.append(
            Event(
                timestamp=now,
                service="GuidingLight",
                event_type=EventType.LEARNING_SIGNAL,
                resource_id=f"learning-{idx}",
                title=f"{row['action']}: {row['capability']}",
                data=row,
                actor="career_gradient_v0_1",
            )
        )
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("snapshot", help="Guiding Light career snapshot JSON")
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
