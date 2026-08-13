from __future__ import annotations

from datetime import datetime, timezone

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


def compute_server_timestamp_validation(
    p1_timestamp: str | None,
    received_at: str | None,
) -> dict:
    """Validate p1_timestamp against server-side received_at timestamp.

    This detects if an agent is gaming the contamination check by fabricating
    timestamps. A legitimate p1_timestamp should be very recent (within 5 seconds)
    of when the server received the submission.

    Returns dict with:
      - external_timestamp_valid: bool (p1_timestamp is fresh and credible)
      - server_submission_delta_seconds: int|None (seconds between p1_timestamp and received_at)
      - timestamp_fraud_risk: str ("low", "medium", "high")
    """
    p1_dt = _parse_iso_timestamp(p1_timestamp)
    received_dt = _parse_iso_timestamp(received_at)

    if p1_dt is None or received_dt is None:
        return {
            "external_timestamp_valid": False,
            "server_submission_delta_seconds": None,
            "timestamp_fraud_risk": "unknown",
            "reason": "unable_to_parse_timestamps",
        }

    # Calculate how long ago the agent claimed p1 was
    delta_seconds = int((received_dt - p1_dt).total_seconds())

    # A legitimate p1_timestamp should be received within a few seconds
    # (network latency + processing time). Timestamps claiming to be from
    # much earlier are likely fabricated to game the contamination check.
    if delta_seconds < 0:
        # Agent's p1_timestamp is in the future—impossible, high fraud risk
        return {
            "external_timestamp_valid": False,
            "server_submission_delta_seconds": delta_seconds,
            "timestamp_fraud_risk": "high",
            "reason": "p1_timestamp_in_future",
        }
    elif delta_seconds <= 5:
        # Legitimate: submitted almost immediately
        return {
            "external_timestamp_valid": True,
            "server_submission_delta_seconds": delta_seconds,
            "timestamp_fraud_risk": "low",
            "reason": "fresh_submission",
        }
    elif delta_seconds <= 30:
        # Suspicious: some delay, but could be legitimate (slow network/processing)
        return {
            "external_timestamp_valid": True,
            "server_submission_delta_seconds": delta_seconds,
            "timestamp_fraud_risk": "medium",
            "reason": "delayed_submission",
        }
    else:
        # Highly suspicious: agent is claiming a p1_timestamp from 30+ seconds ago
        # This is a strong indicator of timestamp fabrication to game contamination check
        return {
            "external_timestamp_valid": False,
            "server_submission_delta_seconds": delta_seconds,
            "timestamp_fraud_risk": "high",
            "reason": "stale_timestamp_likely_fabricated",
        }


def classify_contamination(delta_seconds: int | None) -> str:
    if delta_seconds is None:
        return "unknown"
    if delta_seconds <= CONTAMINATION_THRESHOLD_SECONDS:
        return "clean"
    return "contaminated"


def contamination_summary(
    p1_timestamp: str | None,
    first_user_message_timestamp: str | None,
    received_at: str | None = None,
) -> dict:
    """Generate contamination summary with optional external timestamp validation.

    Args:
        p1_timestamp: Agent's claimed timestamp when Phase 1 started
        first_user_message_timestamp: Agent's claimed timestamp of first user message
        received_at: Server-side timestamp when API received the submission

    Returns:
        dict with contamination_delta_seconds, contamination_status, and optionally
        server_validation data if received_at is provided.
    """
    delta_seconds = compute_contamination_delta_seconds(
        p1_timestamp=p1_timestamp,
        first_user_message_timestamp=first_user_message_timestamp,
    )
    status = classify_contamination(delta_seconds)

    result = {
        "contamination_delta_seconds": delta_seconds,
        "contamination_status": status,
    }

    # Add external timestamp validation if server-side timestamp is available
    if received_at is not None:
        result["external_timestamp_validation"] = compute_server_timestamp_validation(
            p1_timestamp=p1_timestamp,
            received_at=received_at,
        )

    return result
