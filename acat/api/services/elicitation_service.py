from __future__ import annotations

# Option B (pilot): /assess elicits Core 6 from the model and zero-fills
# the extended 6 dimensions before passing to ingest_phase1/phase3.
# Zero is a sentinel value — no model scores 0 in corpus; distinguishable
# from real scores analytically. Schema keys use Supabase abbreviated forms
# (syc, consist, fair) per IC-032 lesson. LI computation remains Core 6
# only per Z2-IC-01. Extended 6 zero rows are analytically inert for
# H-VERIF-01. Option A (production): extend prompt_templates + response_parser
# to elicit all 12; remove this zero-fill block.
_EXTENDED_SCORE_DEFAULTS: dict[str, int] = {
    "scheme": 0,
    "power": 0,
    "syc": 0,
    "consist": 0,
    "fair": 0,
    "handoff": 0,
}

import json
import time
from pathlib import Path
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker

from acat.api.services.ingest_service import (
    IntakeValidationError,
    PersistenceError,
    ingest_phase1,
    ingest_phase3,
)
from acat.api.services.prompt_templates import build_phase1_prompt, build_phase3_prompt
from acat.api.services.provider_clients.anthropic_client import (
    AnthropicClient,
    AnthropicClientError,
)
from acat.api.services.response_parser import parse_scores_response


_REQUEST_SCHEMA_CACHE: dict | None = None
_REQUEST_VALIDATOR: Draft202012Validator | None = None


def _load_assess_request_schema() -> dict:
    global _REQUEST_SCHEMA_CACHE
    if _REQUEST_SCHEMA_CACHE is None:
        schema_path = Path(__file__).resolve().parents[2] / "contracts" / "assess_request.schema.json"
        _REQUEST_SCHEMA_CACHE = json.loads(schema_path.read_text(encoding="utf-8"))
    return _REQUEST_SCHEMA_CACHE


def _get_assess_request_validator() -> Draft202012Validator:
    global _REQUEST_VALIDATOR
    if _REQUEST_VALIDATOR is None:
        _REQUEST_VALIDATOR = Draft202012Validator(
            _load_assess_request_schema(),
            format_checker=FormatChecker(),
        )
    return _REQUEST_VALIDATOR


def validate_assess_request(payload: dict) -> None:
    validator = _get_assess_request_validator()
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
    if not errors:
        return

    first = errors[0]
    path = ".".join(str(p) for p in first.absolute_path) or "$"
    raise IntakeValidationError(f"Assess request validation failed at {path}: {first.message}")


def _generate_assessment_id() -> str:
    return f"acat-{uuid4()}"


def _generate_session_id() -> str:
    return f"S-{uuid4()}"


def run_assessment(request_payload: dict) -> dict:
    validate_assess_request(request_payload)

    provider = request_payload["provider"]
    mode = request_payload.get("mode", "two_stage")
    wait_seconds = int(request_payload.get("wait_seconds", 65))

    if provider != "anthropic":
        raise IntakeValidationError("provider must be 'anthropic'")
    if mode != "two_stage":
        raise IntakeValidationError("mode must be 'two_stage'")
    if wait_seconds < 60:
        raise IntakeValidationError("wait_seconds must be at least 60")

    assessment_id = request_payload.get("assessment_id") or _generate_assessment_id()
    session_id = request_payload.get("session_id") or _generate_session_id()
    agent_name = request_payload["agent_name"]
    model = request_payload["model"]
    api_key = request_payload["api_key"]
    metadata = request_payload.get("metadata") or {}

    client = AnthropicClient()

    try:
        phase1_raw = client.complete_json(
            api_key=api_key,
            model=model,
            prompt=build_phase1_prompt(agent_name),
        )
        phase1_scores = parse_scores_response(phase1_raw)
        # Option B: zero-fill extended 6 so ingest_phase1 schema accepts payload.
        # Core 6 scores are authoritative; extended keys are zero sentinel values.
        phase1_scores_full = {**phase1_scores, **_EXTENDED_SCORE_DEFAULTS}

        phase1_payload = {
            "assessment_id": assessment_id,
            "session_id": session_id,
            "agent_name": agent_name,
            "provider": provider,
            "phase": "phase1",
            "submission_purity": "agent_self_only",
            "scores": phase1_scores_full,
            "metadata": metadata,
        }
        phase1_result = ingest_phase1(phase1_payload)

        time.sleep(wait_seconds)

        phase3_raw = client.complete_json(
            api_key=api_key,
            model=model,
            prompt=build_phase3_prompt(agent_name),
        )
        phase3_scores = parse_scores_response(phase3_raw)
        # Option B: same zero-fill for phase3.
        phase3_scores_full = {**phase3_scores, **_EXTENDED_SCORE_DEFAULTS}

        phase3_payload = {
            "assessment_id": assessment_id,
            "session_id": session_id,
            "agent_name": agent_name,
            "provider": provider,
            "phase": "phase3",
            "submission_purity": "two_stage_verified",
            "scores": phase3_scores_full,
            "metadata": metadata,
        }
        phase3_result = ingest_phase3(phase3_payload)

    except (AnthropicClientError, PersistenceError, IntakeValidationError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Unexpected assessment failure: {exc}") from exc

    return {
        "status": "completed",
        "assessment_id": assessment_id,
        "session_id": session_id,
        "agent_name": agent_name,
        "provider": provider,
        "model": model,
        "mode": mode,
        "submission_purity": phase3_result.get("submission_purity"),
        "phase1": {
            "persisted": phase1_result.get("persisted"),
            "supabase_id": phase1_result.get("supabase_id"),
            "created_at": phase1_result.get("created_at"),
            "p1_committed_at": phase1_result.get("p1_committed_at"),
            "scores": phase1_scores,
        },
        "phase3": {
            "persisted": phase3_result.get("persisted"),
            "supabase_id": phase3_result.get("supabase_id"),
            "updated_at": phase3_result.get("updated_at"),
            "p3_committed_at": phase3_result.get("p3_committed_at"),
            "scores": phase3_scores,
        },
        "learning_index": phase3_result.get("learning_index"),
    }
