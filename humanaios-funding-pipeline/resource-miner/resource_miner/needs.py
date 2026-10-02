from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import NeedMatch, RequirementMatch, ResourceCandidate


def _load_array(path: str | Path, label: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{label} must be a JSON array")
    return data


def load_needs(path: str | Path) -> list[dict[str, Any]]:
    return _load_array(path, "Needs graph")


def load_requirements(path: str | Path) -> list[dict[str, Any]]:
    return _load_array(path, "Resource requirements")


def _candidate_text(resource: ResourceCandidate) -> str:
    return " ".join(
        [
            resource.title,
            resource.description,
            resource.sponsor,
            " ".join(resource.tags),
            " ".join(resource.resource_types),
        ]
    ).lower()


def _score(resource: ResourceCandidate, record: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    text = _candidate_text(resource)
    types = set(resource.resource_types)
    configured_types = {str(x) for x in record.get("resource_types", [])}
    signals = [str(x).lower() for x in record.get("signals", []) if str(x).strip()]
    type_hits = sorted(types & configured_types)
    signal_hits = sorted({s for s in signals if s in text})
    type_score = 0.45 if type_hits else 0.0
    signal_score = min(0.55, 0.11 * len(signal_hits))
    score = round(min(1.0, type_score + signal_score), 2)
    return score, type_hits, signal_hits


def map_to_needs(resource: ResourceCandidate, needs: list[dict[str, Any]]) -> list[NeedMatch]:
    matches: list[NeedMatch] = []
    for need in needs:
        need_id = str(need.get("need_id") or "").strip()
        if not need_id:
            continue
        score, type_hits, signal_hits = _score(resource, need)
        if score >= 0.2:
            matches.append(
                NeedMatch(
                    need_id=need_id,
                    label=str(need.get("label") or need_id),
                    score=score,
                    signals=[*(f"type:{x}" for x in type_hits), *(f"text:{x}" for x in signal_hits)],
                )
            )
    return sorted(matches, key=lambda x: (-x.score, x.need_id))


def map_to_requirements(
    resource: ResourceCandidate,
    requirements: list[dict[str, Any]],
) -> list[RequirementMatch]:
    matches: list[RequirementMatch] = []
    for requirement in requirements:
        requirement_id = str(requirement.get("requirement_id") or "").strip()
        if not requirement_id:
            continue
        score, type_hits, signal_hits = _score(resource, requirement)
        if score >= 0.2:
            matches.append(
                RequirementMatch(
                    requirement_id=requirement_id,
                    label=str(requirement.get("label") or requirement_id),
                    gap_status=str(requirement.get("gap_status") or "UNKNOWN").upper(),
                    score=score,
                    signals=[*(f"type:{x}" for x in type_hits), *(f"text:{x}" for x in signal_hits)],
                )
            )
    return sorted(matches, key=lambda x: (-x.score, x.requirement_id))
