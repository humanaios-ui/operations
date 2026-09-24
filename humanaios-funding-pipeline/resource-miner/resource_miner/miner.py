from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import ResourceCandidate
from .needs import load_needs, map_to_needs
from .routing import route_candidate
from .store import dedupe


def enrich(resources: Iterable[ResourceCandidate], needs_path: str | Path) -> list[ResourceCandidate]:
    needs = load_needs(needs_path)
    items = dedupe(resources)
    for resource in items:
        resource.need_matches = map_to_needs(resource, needs)
        route_candidate(resource)
    return sorted(
        items,
        key=lambda r: (
            0 if r.route == "VERIFY_NOW" else 1 if r.route == "WATCH" else 2,
            -(r.need_matches[0].score if r.need_matches else 0),
            r.deadline or "9999-12-31",
            r.title.lower(),
        ),
    )
