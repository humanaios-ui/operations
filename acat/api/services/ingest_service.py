from datetime import datetime, timezone

from acat.api.services.normalize_service import normalize_phase1_payload


def ingest_phase1(payload: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    payload.setdefault("p1_timestamp", now)

    normalized = normalize_phase1_payload(payload)

    return {
        "status": "accepted",
        "phase": "phase1",
        "session_id": normalized.get("session_id"),
        "assessment_id": normalized.get("assessment_id"),
        "normalized": normalized
    }


def ingest_phase3(payload: dict) -> dict:
    payload.setdefault("submitted_at", datetime.now(timezone.utc).isoformat())
    return {
        "status": "accepted",
        "phase": "phase3",
        "session_id": payload.get("session_id"),
        "assessment_id": payload.get("assessment_id")
    }
