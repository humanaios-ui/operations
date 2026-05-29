from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from acat.api.services.contamination_service import contamination_summary
from acat.api.services.normalize_service import normalize_phase1_payload


class IntakeValidationError(ValueError):
    """Raised when ACAT intake payload validation fails."""


_SCHEMA_CACHE: dict | None = None
_VALIDATOR: Draft202012Validator | None = None


def _load_phase1_schema() -> dict:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        schema_path = Path(__file__).resolve().parents[2] / "contracts" / "phase1_intake.schema.json"
        _SCHEMA_CACHE = json.loads(schema_path.read_text(encoding="utf-8"))
    return _SCHEMA_CACHE


def _get_phase1_validator() -> Draft202012Validator:
    global _VALIDATOR
    if _VALIDATOR is None:
        schema = _load_phase1_schema()
        _VALIDATOR = Draft202012Validator(schema, format_checker=FormatChecker())
    return _VALIDATOR


def validate_phase1_payload(payload: dict) -> None:
    validator = _get_phase1_validator()
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))

    if not errors:
        return

    first = errors[0]
    path = ".".join(str(p) for p in first.absolute_path) or "$"
    raise IntakeValidationError(f"Phase 1 payload validation failed at {path}: {first.message}")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_assessment_id(payload: dict) -> str:
    existing = payload.get("assessment_id")
    if existing:
        return str(existing)
    return str(uuid4())


def _persist_phase1(payload: dict) -> dict:
    """
    Placeholder persistence hook.

    Replace this with:
    - Supabase REST insert/upsert
    - direct DB write
    - or a repository-specific persistence adapter
    """
    return {
        "persisted": True,
        "storage": "stub",
        "record": payload,
    }


def ingest_phase1(payload: dict) -> dict:
    raw_payload = dict(payload)

    working = dict(payload)
    working.setdefault("p1_timestamp", _utcnow_iso())
    working["assessment_id"] = _ensure_assessment_id(working)

    validate_phase1_payload(working)

    contamination = contamination_summary(
        p1_timestamp=working.get("p1_timestamp"),
        first_user_message_timestamp=working.get("first_user_message_timestamp"),
    )
    working.update(contamination)

    normalized = normalize_phase1_payload(working)

    persisted = _persist_phase1(
        {
            **normalized,
            "raw_payload": raw_payload,
        }
    )

    return {
        "status": "accepted",
        "phase": "phase1",
        "session_id": normalized.get("session_id"),
        "assessment_id": normalized.get("assessment_id"),
        "submission_purity": normalized.get("submission_purity"),
        "quality_flags": normalized.get("quality_flags", []),
        "contamination_delta_seconds": normalized.get("contamination_delta_seconds"),
        "contamination_status": normalized.get("contamination_status"),
        "persisted": persisted.get("persisted", False),
    }


def ingest_phase3(payload: dict) -> dict:
    payload = dict(payload)
    payload.setdefault("submitted_at", _utcnow_iso())
    payload.setdefault("assessment_id", _ensure_assessment_id(payload))

    return {
        "status": "accepted",
        "phase": "phase3",
        "session_id": payload.get("session_id"),
        "assessment_id": payload.get("assessment_id"),
    }
