from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker

from acat.api.services.contamination_service import contamination_summary
from acat.api.services.normalize_service import normalize_phase1_payload


class IntakeValidationError(ValueError):
    """Raised when ACAT intake payload validation fails."""


class PersistenceError(RuntimeError):
    """Raised when ACAT persistence fails."""


_PHASE1_SCHEMA_CACHE: dict | None = None
_PHASE1_VALIDATOR: Draft202012Validator | None = None
_PHASE3_SCHEMA_CACHE: dict | None = None
_PHASE3_VALIDATOR: Draft202012Validator | None = None


def _load_phase1_schema() -> dict:
    global _PHASE1_SCHEMA_CACHE
    if _PHASE1_SCHEMA_CACHE is None:
        schema_path = Path(__file__).resolve().parents[2] / "contracts" / "phase1_intake.schema.json"
        _PHASE1_SCHEMA_CACHE = json.loads(schema_path.read_text(encoding="utf-8"))
    return _PHASE1_SCHEMA_CACHE


def _get_phase1_validator() -> Draft202012Validator:
    global _PHASE1_VALIDATOR
    if _PHASE1_VALIDATOR is None:
        schema = _load_phase1_schema()
        _PHASE1_VALIDATOR = Draft202012Validator(schema, format_checker=FormatChecker())
    return _PHASE1_VALIDATOR


def _load_phase3_schema() -> dict:
    global _PHASE3_SCHEMA_CACHE
    if _PHASE3_SCHEMA_CACHE is None:
        schema_path = Path(__file__).resolve().parents[2] / "contracts" / "phase3_submission.schema.json"
        _PHASE3_SCHEMA_CACHE = json.loads(schema_path.read_text(encoding="utf-8"))
    return _PHASE3_SCHEMA_CACHE


def _get_phase3_validator() -> Draft202012Validator:
    global _PHASE3_VALIDATOR
    if _PHASE3_VALIDATOR is None:
        schema = _load_phase3_schema()
        _PHASE3_VALIDATOR = Draft202012Validator(schema, format_checker=FormatChecker())
    return _PHASE3_VALIDATOR


def validate_phase1_payload(payload: dict) -> None:
    validator = _get_phase1_validator()
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))

    if not errors:
        return

    first = errors[0]
    path = ".".join(str(p) for p in first.absolute_path) or "$"
    raise IntakeValidationError(f"Phase 1 payload validation failed at {path}: {first.message}")


def validate_phase3_payload(payload: dict) -> None:
    validator = _get_phase3_validator()
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))

    if not errors:
        return

    first = errors[0]
    path = ".".join(str(p) for p in first.absolute_path) or "$"
    raise IntakeValidationError(f"Phase 3 payload validation failed at {path}: {first.message}")


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


def _fetch_existing_assessment_row(payload: dict) -> dict:
    supabase_url, service_key = _get_supabase_env()

    assessment_id = payload.get("assessment_id")
    session_id = payload.get("session_id")

    if assessment_id:
        filter_expr = f"assessment_id=eq.{quote(str(assessment_id), safe='')}"
    elif session_id:
        filter_expr = f"session_id=eq.{quote(str(session_id), safe='')}"
    else:
        raise PersistenceError("Phase 3 persistence requires assessment_id or session_id")

    request = Request(
        f"{supabase_url}/rest/v1/acat_assessments_v1?select=*&{filter_expr}&limit=1",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else []
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise PersistenceError(f"Supabase lookup failed with HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise PersistenceError(f"Supabase lookup connection failed: {exc}") from exc

    if not isinstance(parsed, list) or not parsed:
        raise PersistenceError("Phase 3 persistence failed: assessment row not found")

    return parsed[0]


def _build_phase1_row(payload: dict) -> dict:
    scores = payload["scores"]
    row = {
        "assessment_id": payload.get("assessment_id"),
        "agent_name": payload.get("agent_name_raw") or payload.get("agent_name"),
        "submission_purity": payload.get("submission_purity"),
        "contamination_delta_seconds": payload.get("contamination_delta_seconds"),
        "contamination_status": payload.get("contamination_status"),
        "p1_truth": scores.get("truth"),
        "p1_service": scores.get("service"),
        "p1_harm": scores.get("harm"),
        "p1_autonomy": scores.get("autonomy"),
        "p1_value": scores.get("value"),
        "p1_humility": scores.get("humility"),
    }

    if payload.get("provider") is not None:
        row["provider"] = payload.get("provider")
    if payload.get("thread_id") is not None:
        row["thread_id"] = payload.get("thread_id")
    if payload.get("assessment_mode") is not None:
        row["assessment_mode"] = payload.get("assessment_mode")
    if payload.get("submission_source") is not None:
        row["submission_source"] = payload.get("submission_source")
    if payload.get("metadata") is not None:
        row["metadata"] = payload.get("metadata")

    return row


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


def _compute_learning_index(existing_row: dict, phase3_scores: dict) -> float | None:
    p1_fields = [
        existing_row.get("p1_truth"),
        existing_row.get("p1_service"),
        existing_row.get("p1_harm"),
        existing_row.get("p1_autonomy"),
        existing_row.get("p1_value"),
        existing_row.get("p1_humility"),
    ]

    if any(v is None for v in p1_fields):
        return None

    p1_total = sum(float(v) for v in p1_fields)
    if p1_total <= 0:
        return None

    p3_total = sum(
        float(phase3_scores[k])
        for k in ["truth", "service", "harm", "autonomy", "value", "humility"]
    )

    return round(p3_total / p1_total, 4)


def _build_phase3_row(payload: dict, existing_row: dict) -> dict:
    scores = payload["scores"]
    learning_index = _compute_learning_index(existing_row, scores)

    row = {
        "p3_truth": scores.get("truth"),
        "p3_service": scores.get("service"),
        "p3_harm": scores.get("harm"),
        "p3_autonomy": scores.get("autonomy"),
        "p3_value": scores.get("value"),
        "p3_humility": scores.get("humility"),
        "learning_index": learning_index,
    }

    if payload.get("agent_name_raw") is not None:
        row["agent_name"] = payload.get("agent_name_raw")
    elif payload.get("agent_name") is not None:
        row["agent_name"] = payload.get("agent_name")

    if payload.get("submission_purity") is not None:
        row["submission_purity"] = payload.get("submission_purity")
    if payload.get("provider") is not None:
        row["provider"] = payload.get("provider")
    if payload.get("assessment_mode") is not None:
        row["assessment_mode"] = payload.get("assessment_mode")
    if payload.get("metadata") is not None:
        row["metadata"] = payload.get("metadata")

    return row


def _persist_phase3(payload: dict) -> dict:
    supabase_url, service_key = _get_supabase_env()
    existing_row = _fetch_existing_assessment_row(payload)
    row = _build_phase3_row(payload, existing_row)

    assessment_id = existing_row.get("assessment_id") or payload.get("assessment_id")
    session_id = existing_row.get("session_id") or payload.get("session_id")

    if assessment_id:
        filter_expr = f"assessment_id=eq.{quote(str(assessment_id), safe='')}"
    elif session_id:
        filter_expr = f"session_id=eq.{quote(str(session_id), safe='')}"
    else:
        raise PersistenceError("Phase 3 persistence failed: no stable identifier available for PATCH")

    body = json.dumps(row).encode("utf-8")
    request = Request(
        f"{supabase_url}/rest/v1/acat_assessments_v1?{filter_expr}",
        data=body,
        headers={
            "Content-Type": "application/json",
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Prefer": "return=representation",
        },
        method="PATCH",
    )

    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else []
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise PersistenceError(f"Supabase phase3 PATCH failed with HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise PersistenceError(f"Supabase phase3 PATCH connection failed: {exc}") from exc

    if not isinstance(parsed, list) or not parsed:
        raise PersistenceError("Supabase phase3 PATCH failed: empty response body")

    row0 = parsed[0]
    return {
        "persisted": True,
        "supabase_id": row0.get("id"),
        "updated_at": row0.get("updated_at") or row0.get("created_at"),
        "learning_index": row0.get("learning_index", row.get("learning_index")),
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
    raw_payload = dict(payload)

    working = dict(payload)
    working.setdefault("submitted_at", _utcnow_iso())

    validate_phase3_payload(working)

    if working.get("agent_name") is not None:
        working = normalize_phase1_payload(working)

    persisted = _persist_phase3(
        {
            **working,
            "raw_payload": raw_payload,
        }
    )

    return {
        "status": "accepted",
        "phase": "phase3",
        "session_id": working.get("session_id"),
        "assessment_id": working.get("assessment_id"),
        "submission_purity": working.get("submission_purity"),
        "persisted": persisted.get("persisted", False),
        "supabase_id": persisted.get("supabase_id"),
        "updated_at": persisted.get("updated_at"),
        "learning_index": persisted.get("learning_index"),
    }
