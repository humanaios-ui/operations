from __future__ import annotations

from datetime import datetime

CONTAMINATION_THRESHOLD_SECONDS = 60


def _parse_iso_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def compute_contamination_delta_seconds(
    p1_timestamp: str | None,
    first_user_message_timestamp: str | None,
) -> int | None:
    p1 = _parse_iso_timestamp(p1_timestamp)
    first = _parse_iso_timestamp(first_user_message_timestamp)

    if p1 is None or first is None:
        return None

    return int((first - p1).total_seconds())


def classify_contamination(delta_seconds: int | None) -> str:
    if delta_seconds is None:
        return "unknown"
    if delta_seconds <= CONTAMINATION_THRESHOLD_SECONDS:
        return "clean"
    return "contaminated"


def contamination_summary(
    p1_timestamp: str | None,
    first_user_message_timestamp: str | None,
) -> dict:
    delta_seconds = compute_contamination_delta_seconds(
        p1_timestamp=p1_timestamp,
        first_user_message_timestamp=first_user_message_timestamp,
    )
    status = classify_contamination(delta_seconds)
    return {
        "contamination_delta_seconds": delta_seconds,
        "contamination_status": status,
    }
