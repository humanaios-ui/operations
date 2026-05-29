from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from acat.api.services.contamination_service import contamination_summary
from acat.api.services.normalize_service import normalize_phase1_payload


class IntakeValidationError(ValueError):
    """Raised when ACAT intake payload validation fails."""


class PersistenceError(RuntimeError):
    """Raised when Supabase write fails in a non-retryable way."""


_SCHEMA_CACHE: dict | None = None
_VALIDATOR: Draft202012Validator | None = None


# ── Schema loading ─────────────────────────────────────────────────────────────

def _load_phase1_schema() -> dict:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        schema_path = (
            Path(__file__).resolve().parents[2] / "contracts" / "phase1_intake.schema.json"
        )
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
    raise IntakeValidationError(
        f"Phase 1 payload validation failed at {path}: {first.message}"
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_assessment_id(payload: dict) -> str:
    existing = payload.get("assessment_id")
    return str(existing) if existing else str(uuid4())


# ── Supabase persistence ───────────────────────────────────────────────────────

def _get_supabase_env() -> tuple[str, str]:
    """
    Returns (url, key) from environment.
    Uses SUPABASE_SERVICE_ROLE_KEY for writes (insert requires it when RLS
    restricts anon inserts); falls back to SUPABASE_KEY if service key absent.
    This mirrors the convention in supabase_corpus_connector_v1_0_2.py but
    prefers service_role for write access.
    """
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_KEY", "")
    )
    if not url or not key:
        raise PersistenceError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) must be set. "
            "SUPABASE_URL: https://ksinisdzgtnqzsymhfya.supabase.co"
        )
    return url, key


def _build_row(normalized: dict, raw_payload: dict) -> dict:
    """
    Map the normalized ingest payload to acat_assessments_v1 column names.

    Column reference (confirmed from supabase_migration_S-041926-B.sql):
      Core 6 P1:   p1_truth, p1_service, p1_harm, p1_autonomy, p1_value, p1_humility
      Extended 5:  p1_scheme, p1_power, p1_syc, p1_consist, p1_fair
      Identity:    agent_name, provider, layer, mode, timestamp
      Purity:      submission_purity, submission_source
      Series:      series_id, run_mode, run_index, series_length
      Provenance:  pair_id (used here as session_id), metadata (jsonb)

    Columns NOT in the table yet (go into metadata jsonb):
      assessment_id, contamination_delta_seconds, contamination_status,
      quality_flags, normalization_version, dedupe_key, raw_payload
    """
    scores = normalized.get("scores", {})

    # Core 6 Phase 1 scores
    row: dict = {
        "p1_truth":    scores.get("truth"),
        "p1_service":  scores.get("service"),
        "p1_harm":     scores.get("harm"),
        "p1_autonomy": scores.get("autonomy"),
        "p1_value":    scores.get("value"),
        "p1_humility": scores.get("humility"),
    }

    # Extended 5 Phase 1 scores (optional — omit key if not present)
    ext_map = {
        "scheme":  "p1_scheme",
        "power":   "p1_power",
        "syc":     "p1_syc",
        "consist": "p1_consist",
        "fair":    "p1_fair",
    }
    for src_key, col_name in ext_map.items():
        val = scores.get(src_key)
        if val is not None:
            row[col_name] = val

    # Identity / provenance
    row["agent_name"]       = normalized.get("agent_name_canonical") or normalized.get("agent_name")
    row["provider"]         = normalized.get("provider")
    row["layer"]            = normalized.get("layer", "acat-self-v1")
    row["mode"]             = normalized.get("assessment_mode", "EMPIRICAL")
    row["timestamp"]        = normalized.get("p1_timestamp") or _utcnow_iso()
    row["submission_source"]= "api_intake"
    row["submission_purity"]= normalized.get("submission_purity")

    # Session / series linkage
    # pair_id is the pre-existing session linkage column; series_id is the series column.
    # session_id from intake maps to pair_id (session-level grouping).
    row["pair_id"]    = normalized.get("session_id")
    row["series_id"]  = normalized.get("series_id") or normalized.get("session_id")
    row["run_mode"]   = normalized.get("run_mode", "sequential")
    row["run_index"]  = normalized.get("run_index")
    row["series_length"] = normalized.get("series_length")

    # Overflow into metadata jsonb — everything that has no dedicated column yet
    row["metadata"] = json.dumps({
        "assessment_id":              normalized.get("assessment_id"),
        "contamination_delta_seconds": normalized.get("contamination_delta_seconds"),
        "contamination_status":        normalized.get("contamination_status"),
        "quality_flags":               normalized.get("quality_flags", []),
        "normalization_version":       normalized.get("normalization_version"),
        "dedupe_key":                  normalized.get("dedupe_key"),
        "rater_id":                    normalized.get("rater_id"),
        "thread_id":                   normalized.get("thread_id"),
        "source":                      normalized.get("source"),
        "raw_payload":                 raw_payload,
    })

    # Strip None values — Supabase REST treats missing keys as NULL automatically;
    # explicit None can cause type-coercion errors on int2 columns.
    return {k: v for k, v in row.items() if v is not None}


def _persist_phase1(normalized: dict, raw_payload: dict) -> dict:
    """
    Insert one Phase 1 row into acat_assessments_v1 via Supabase REST API.

    Uses stdlib urllib only (no httpx/requests), consistent with
    supabase_corpus_connector_v1_0_2.py. Returns the inserted row with
    its server-assigned id and created_at.

    Raises PersistenceError on HTTP 4xx/5xx or network failure.
    """
    url, key = _get_supabase_env()
    row = _build_row(normalized, raw_payload)

    endpoint = f"{url}/rest/v1/acat_assessments_v1"
    body = json.dumps(row).encode("utf-8")

    req = Request(
        endpoint,
        data=body,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",   # get the inserted row back
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=30) as resp:
            response_body = resp.read().decode("utf-8")
            inserted = json.loads(response_body)
            # REST returns a list when Prefer: return=representation
            record = inserted[0] if isinstance(inserted, list) else inserted
            return {
                "persisted": True,
                "storage": "supabase:acat_assessments_v1",
                "id": record.get("id"),
                "created_at": record.get("created_at"),
            }

    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise PersistenceError(
            f"Supabase insert failed HTTP {exc.code}: {detail[:300]}"
        ) from exc

    except URLError as exc:
        raise PersistenceError(
            f"Supabase network error: {exc.reason}"
        ) from exc


# ── Public ingest functions ────────────────────────────────────────────────────

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

    persisted = _persist_phase1(normalized, raw_payload)

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
        "supabase_id": persisted.get("id"),
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
