from __future__ import annotations

import re
from datetime import date

from .models import ResourceCandidate

# A title that reports a result ("Congrats to the ... Winners", "Winners
# announced ...") rather than inviting participation. A bare "Winners" is not
# enough: "Join the ... Prizes for FIVE Winners!" is an invitation. Only applied
# when the candidate has no open date or deadline.
_OUTCOME_TITLE = re.compile(
    r"\b(congrats|congratulations)\b"
    r"|\b(announc\w*|meet|celebrat\w*)\s+(the\s+)?winners\b"
    r"|\bwinners?\s+(are\s+|have\s+been\s+)?(announced|named|selected|chosen)\b",
    re.IGNORECASE,
)


def _is_outcome_announcement(resource: ResourceCandidate) -> bool:
    if resource.deadline or resource.opens_at:
        return False
    return bool(_OUTCOME_TITLE.search(resource.title or ""))


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

    if _is_outcome_announcement(resource):
        resource.route = "WATCH"
        resource.status = resource.status if resource.status != "UNKNOWN" else "UNMAPPED"
        return resource

    top = _routing_score(resource)
    if top == 0.0:
        resource.route = "WATCH"
        resource.status = resource.status if resource.status != "UNKNOWN" else "UNMAPPED"
        return resource

    resource.route = "VERIFY_NOW" if top >= 0.55 else "WATCH"
    resource.status = resource.status if resource.status != "UNKNOWN" else "DISCOVERED"
    return resource
