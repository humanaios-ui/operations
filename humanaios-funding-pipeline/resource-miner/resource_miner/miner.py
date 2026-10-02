from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import ResourceCandidate
from .needs import load_needs, load_requirements, map_to_needs, map_to_requirements
from .routing import route_candidate
from .store import dedupe


def _ranking_score(resource: ResourceCandidate) -> float:
    scores = [match.score for match in resource.need_matches]
    scores.extend(
        match.score
        for match in resource.requirement_matches
        if match.gap_status == "CONFIRMED"
    )
    return max(scores, default=0.0)


def enrich(
    resources: Iterable[ResourceCandidate],
    needs_path: str | Path,
    requirements_path: str | Path | None = None,
) -> list[ResourceCandidate]:
    needs = load_needs(needs_path)
    requirements = load_requirements(requirements_path) if requirements_path else []
    items = dedupe(resources)
    for resource in items:
        resource.need_matches = map_to_needs(resource, needs)
        resource.requirement_matches = map_to_requirements(resource, requirements)
        route_candidate(resource)
    return sorted(
        items,
        key=lambda r: (
            0 if r.route == "VERIFY_NOW" else 1 if r.route == "WATCH" else 2,
            -_ranking_score(r),
            r.deadline or "9999-12-31",
            r.title.lower(),
        ),
    )
