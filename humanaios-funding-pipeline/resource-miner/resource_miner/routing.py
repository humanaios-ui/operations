from __future__ import annotations

from datetime import date

from .models import ResourceCandidate


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
    if not resource.need_matches:
        resource.route = "WATCH"
        resource.status = resource.status if resource.status != "UNKNOWN" else "UNMAPPED"
        return resource
    top = resource.need_matches[0].score
    resource.route = "VERIFY_NOW" if top >= 0.55 else "WATCH"
    resource.status = resource.status if resource.status != "UNKNOWN" else "DISCOVERED"
    return resource
