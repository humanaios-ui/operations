from __future__ import annotations

from datetime import date

from .models import ResourceCandidate


def _routing_score(resource: ResourceCandidate) -> float:
    scores = [match.score for match in resource.need_matches]
    scores.extend(
        match.score
        for match in resource.requirement_matches
        if match.gap_status == "CONFIRMED"
    )
    return max(scores, default=0.0)


def route_candidate(resource: ResourceCandidate, today: date | None = None) -> ResourceCandidate:
    today = today or date.today()
    if resource.deadline:
        try:
            deadline = date.fromisoformat(resource.deadline)
        except ValueError:
            deadline = None
        if deadline and deadline < today:
            resource.route = "ARCHIVE"
            resource.status = "CLOSED_OR_STALE"
            return resource
        if deadline:
            resource.status = "OPEN_OR_UPCOMING"

    top = _routing_score(resource)
    if top == 0.0:
        resource.route = "WATCH"
        resource.status = resource.status if resource.status != "UNKNOWN" else "UNMAPPED"
        return resource

    resource.route = "VERIFY_NOW" if top >= 0.55 else "WATCH"
    resource.status = resource.status if resource.status != "UNKNOWN" else "DISCOVERED"
    return resource
