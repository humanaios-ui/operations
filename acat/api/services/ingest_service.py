from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker

from acat.api.services.contamination_service import contamination_summary
from acat.api.services.normalize_service import normalize_phase1_payload


class IntakeValidationError(ValueError):
    """Raised when ACAT intake payload validation fails."""


class PersistenceError(RuntimeError):
    """Raised when ACAT persistence fails."""


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


def _get_supabase_env() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if not url:
        raise PersistenceError("Missing required env var: SUPABASE_URL")
    if not key:
        raise PersistenceError("Missing required env var: SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY")

    return url.rstrip("/"), key


def _build_phase1_row(payload: dict) -> dict:
    scores = payload["scores"]
    return {
        "assessment_id": payload.get("assessment_id"),
        "session_id": payload.get("session_id"),
        "phase": payload.get("phase"),
        "agent_name": payload.get("agent_name_raw") or payload.get("agent_name"),
        "agent_name_canonical": payload.get("agent_name_canonical"),
        "submission_purity": payload.get("submission_purity"),
        "p1_timestamp": payload.get("p1_timestamp"),
        "session_start_timestamp": payload.get("session_start_timestamp"),
        "first_user_message_timestamp": payload.get("first_user_message_timestamp"),
        "contamination_delta_seconds": payload.get("contamination_delta_seconds"),
        "contamination_status": payload.get("contamination_status"),
        "quality_flags": payload.get("quality_flags", []),
        "normalization_version": payload.get("normalization_version"),
        "dedupe_key": payload.get("dedupe_key"),
        "p1_truth": scores.get("truth"),
        "p1_service": scores.get("service"),
        "p1_harm": scores.get("harm"),
        "p1_autonomy": scores.get("autonomy"),
        "p1_value": scores.get("value"),
        "p1_humility": scores.get("humility"),
        "raw_payload": payload.get("raw_payload"),
    }


def _persist_phase1(payload: dict) -> dict:
    supabase_url, service_key = _get_supabase_env()
    row = _build_phase1_row(payload)

    body = json.dumps(row).encode("utf-8")
    request = Request(
        f"{supabase_url}/rest/v1/acat_assessments_v1",
        data=body,
        headers={
            "Content-Type": "application/json",
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Prefer": "return=representation",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else []
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise PersistenceError(f"Supabase persistence failed with HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise PersistenceError(f"Supabase persistence connection failed: {exc}") from exc

    if not isinstance(parsed, list) or not parsed:
        raise PersistenceError("Supabase persistence failed: empty response body")

    row0 = parsed[0]
    return {
        "persisted": True,
        "supabase_id": row0.get("id"),
        "created_at": row0.get("created_at"),
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
        "supabase_id": persisted.get("supabase_id"),
        "created_at": persisted.get("created_at"),
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
