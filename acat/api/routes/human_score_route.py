"""
Route: POST /api/v1/acat/human-score
Session: S-060126-02
Z2 authority: Z2-IC-02 (S-053026-02) — human scores in linked table acat_human_scores
Z2 authority: Z2-IC-03 (S-053026-02) — rater_id anonymous token default

Receipt object structure (returned on success):
  - ai_scores: P3 scores from existing assessment row
  - human_scores: scores just submitted
  - gap: per-dimension (ai_p3 - human); positive = AI scored itself higher
  - corpus_comparison: live Supabase mean P1 per dimension (N from acat_assessments_v1)
  - originstamp: async hash anchor (non-blocking; null if unavailable)
"""
from __future__ import annotations

import hashlib
import json
import os
import ssl
import uuid
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import certifi
from fastapi import APIRouter, Depends, HTTPException, status

from acat.api.security import require_write_token
from jsonschema import Draft202012Validator, FormatChecker
from pathlib import Path

router = APIRouter()

_HUMAN_SCORE_SCHEMA_CACHE: dict | None = None
_HUMAN_SCORE_VALIDATOR: Draft202012Validator | None = None

CORE_6 = ["truth", "service", "harm", "autonomy", "value", "humility"]
ALL_12 = CORE_6 + ["scheme", "power", "syc", "consist", "fair", "handoff"]


def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_supabase_env() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url:
        raise RuntimeError("Missing SUPABASE_URL")
    if not key:
        raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY")
    return url.rstrip("/"), key


def _load_human_score_schema() -> dict:
    global _HUMAN_SCORE_SCHEMA_CACHE
    if _HUMAN_SCORE_SCHEMA_CACHE is None:
        schema_path = (
            Path(__file__).resolve().parents[2] / "contracts" / "human_score.schema.json"
        )
        _HUMAN_SCORE_SCHEMA_CACHE = json.loads(schema_path.read_text(encoding="utf-8"))
    return _HUMAN_SCORE_SCHEMA_CACHE


def _get_human_score_validator() -> Draft202012Validator:
    global _HUMAN_SCORE_VALIDATOR
    if _HUMAN_SCORE_VALIDATOR is None:
        _HUMAN_SCORE_VALIDATOR = Draft202012Validator(
            _load_human_score_schema(), format_checker=FormatChecker()
        )
    return _HUMAN_SCORE_VALIDATOR


def _validate_human_score_payload(payload: dict) -> None:
    validator = _get_human_score_validator()
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
    if not errors:
        return
    first = errors[0]
    path = ".".join(str(p) for p in first.absolute_path) or "$"
    raise ValueError(f"Human score validation failed at {path}: {first.message}")


def _fetch_assessment_row(assessment_id: str) -> dict:
    """Fetch the existing AI assessment row for receipt construction."""
    supabase_url, service_key = _get_supabase_env()
    filter_expr = f"assessment_id=eq.{quote(assessment_id, safe='')}"
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
        with urlopen(request, timeout=15, context=_ssl_context()) as resp:
            parsed = json.loads(resp.read().decode("utf-8") or "[]")
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Supabase assessment lookup failed: {exc}") from exc

    if not isinstance(parsed, list) or not parsed:
        raise ValueError(f"Assessment not found: {assessment_id}")
    return parsed[0]


def _fetch_corpus_means() -> dict:
    """
    Fetch live mean P1 scores per dimension from acat_assessments_v1.
    Returns dict keyed by dimension name. Non-blocking — returns empty on failure.
    """
    supabase_url, service_key = _get_supabase_env()
    # Aggregate mean of all 12 P1 columns
    select_cols = ",".join(f"avg(p1_{d})" for d in ALL_12)
    request = Request(
        f"{supabase_url}/rest/v1/acat_assessments_v1?select={select_cols}"
        "&p1_truth=not.is.null",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=10, context=_ssl_context()) as resp:
            parsed = json.loads(resp.read().decode("utf-8") or "[]")
        if isinstance(parsed, list) and parsed:
            row = parsed[0]
            return {
                d: round(float(row[f"avg(p1_{d})"]), 2)
                for d in ALL_12
                if row.get(f"avg(p1_{d})") is not None
            }
    except Exception:  # non-blocking
        pass
    return {}


def _anchor_originstamp(receipt_hash: str) -> dict | None:
    """
    Non-blocking OriginStamp hash anchor.
    Posts the SHA-256 hash of the receipt to OriginStamp for blockchain provenance.
    Returns the API response dict or None if unavailable.
    """
    api_key = os.getenv("ORIGINSTAMP_API_KEY")
    if not api_key:
        return None

    body = json.dumps({"hash": receipt_hash, "comment": "ACAT human score receipt"}).encode()
    request = Request(
        "https://api.originstamp.com/v4/timestamp/create",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": api_key,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10, context=_ssl_context()) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _persist_human_score(
    assessment_uuid: str,
    assessment_id: str,
    rater_id: str,
    scores: dict,
    gaps: dict,
    notes: str | None,
    rated_at: str,
) -> dict:
    """Write human score row to acat_human_scores."""
    supabase_url, service_key = _get_supabase_env()

    row = {
        "assessment_uuid": assessment_uuid,
        "assessment_id": assessment_id,
        "rater_id": rater_id,
        "rated_at": rated_at,
        **{f"h_{d}": scores[f"h_{d}"] for d in ALL_12},
        **{f"gap_{d}": gaps.get(d) for d in ALL_12},
    }
    if notes:
        row["notes"] = notes

    body = json.dumps(row).encode("utf-8")
    request = Request(
        f"{supabase_url}/rest/v1/acat_human_scores",
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
        with urlopen(request, timeout=15, context=_ssl_context()) as resp:
            parsed = json.loads(resp.read().decode("utf-8") or "[]")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Human score persist failed HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Human score persist connection failed: {exc}") from exc

    if not isinstance(parsed, list) or not parsed:
        raise RuntimeError("Human score persist failed: empty response")
    return parsed[0]


def _build_receipt(
    ai_row: dict,
    human_scores: dict,
    gaps: dict,
    corpus_means: dict,
    persisted_row: dict,
    originstamp: dict | None,
) -> dict:
    """Construct the full receipt object."""

    # AI P3 scores from existing row
    ai_p3 = {d: ai_row.get(f"p3_{d}") for d in ALL_12}
    ai_p1 = {d: ai_row.get(f"p1_{d}") for d in ALL_12}

    # Human scores (strip h_ prefix for display consistency)
    h_scores = {d: human_scores[f"h_{d}"] for d in ALL_12}

    receipt = {
        "assessment_id": ai_row.get("assessment_id"),
        "human_score_id": persisted_row.get("id"),
        "rated_at": persisted_row.get("rated_at"),
        "ai_scores": {
            "p1": ai_p1,
            "p3": ai_p3,
            "learning_index": ai_row.get("learning_index"),
        },
        "human_scores": h_scores,
        "gap": gaps,  # positive = AI P3 scored itself higher than human
        "corpus_comparison": {
            "source": "live acat_assessments_v1",
            "metric": "mean P1 per dimension",
            "values": corpus_means,
        },
        "originstamp": originstamp,
    }
    return receipt


@router.post(
    "/human-score",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write_token)],
)
def post_human_score(payload: dict):
    """
    Submit human scores for an existing ACAT assessment.

    Required: assessment_id, scores (all 12 h_ dimensions)
    Optional: rater_id (anonymous token generated if omitted), notes, rated_at

    Returns: full receipt with AI scores, human scores, per-dimension gap,
             live corpus comparison, and OriginStamp provenance anchor.
    """
    try:
        _validate_human_score_payload(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    assessment_id = payload["assessment_id"]
    scores = payload["scores"]
    rater_id = payload.get("rater_id") or f"anon-{uuid.uuid4().hex[:12]}"
    notes = payload.get("notes")
    rated_at = payload.get("rated_at") or _utcnow_iso()

    # Fetch existing AI assessment row
    try:
        ai_row = _fetch_assessment_row(assessment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    assessment_uuid = ai_row.get("id")
    if not assessment_uuid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assessment row missing UUID id — cannot link human score",
        )

    # Compute per-dimension gaps (AI P3 - human; positive = AI scored itself higher)
    gaps: dict = {}
    for d in ALL_12:
        ai_val = ai_row.get(f"p3_{d}")
        h_val = scores.get(f"h_{d}")
        if ai_val is not None and h_val is not None:
            gaps[d] = int(ai_val) - int(h_val)
        else:
            gaps[d] = None

    # Fetch live corpus means (non-blocking)
    corpus_means = _fetch_corpus_means()

    # Persist human score row
    try:
        persisted_row = _persist_human_score(
            assessment_uuid=assessment_uuid,
            assessment_id=assessment_id,
            rater_id=rater_id,
            scores=scores,
            gaps=gaps,
            notes=notes,
            rated_at=rated_at,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    # Build receipt content for hashing
    receipt = _build_receipt(
        ai_row=ai_row,
        human_scores=scores,
        gaps=gaps,
        corpus_means=corpus_means,
        persisted_row=persisted_row,
        originstamp=None,  # placeholder until hash computed
    )

    # OriginStamp: hash the receipt JSON and anchor it (non-blocking)
    receipt_json = json.dumps(receipt, sort_keys=True, default=str)
    receipt_hash = hashlib.sha256(receipt_json.encode()).hexdigest()
    originstamp_result = _anchor_originstamp(receipt_hash)

    receipt["originstamp"] = originstamp_result
    receipt["receipt_hash_sha256"] = receipt_hash

    return receipt
