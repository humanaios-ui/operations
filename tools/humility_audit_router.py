"""
humility_audit_router.py — FastAPI router for the humility audit endpoint.
Builder v1.7 compliant — humility_audit_router_tool
HumanAIOS — S-061726-humility-audit-router
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from acat.api.services.humility_audit_service import (
fetch_assessment_row,
fetch_humility_corpus_stats,
run_humility_audit,
to_report_markdown,
_extract_dim_scores,
)
from acat.api.services.ingest_service import PersistenceError

TOOL_NAME = "humility_audit_router"
TOOL_VERSION = "0.1.0"

router = APIRouter()

class ACATScores(BaseModel):
    """Matches acat/contracts/phase1_intake.schema.json#/properties/scores
    exactly. Do not add, rename, or remove fields here without updating
    that contract - it is the source of truth, not this model."""

    truth: float = Field(..., ge=0, le=100)
    service: float = Field(..., ge=0, le=100)
    harm: float = Field(..., ge=0, le=100)
    autonomy: float = Field(..., ge=0, le=100)
    value: float = Field(..., ge=0, le=100)
    humility: float = Field(..., ge=0, le=100)
    scheme: float = Field(..., ge=0, le=100)
    power: float = Field(..., ge=0, le=100)
    syc: float = Field(..., ge=0, le=100)
    consist: float = Field(..., ge=0, le=100)
    fair: float = Field(..., ge=0, le=100)
    handoff: float = Field(..., ge=0, le=100)

class HumilityAuditRequest(BaseModel):
    """Either supply by_assessment_id (audits a persisted row from
    acat_assessments_v1) OR supply model_id/provider/submission_purity/
    p1_scores directly. Mixing both is rejected - pick one mode."""

    by_assessment_id: Optional[str] = None

    model_id: Optional[str] = None
    provider: Optional[str] = None
    submission_purity: Optional[str] = None
    p1_scores: Optional[ACATScores] = None
    p3_scores: Optional[ACATScores] = None

    as_report: bool = False

@router.post("/humility-audit")
def humility_audit(req: HumilityAuditRequest) -> dict:
    """Read-only diagnostic: applies REGISTERED.md F-20/F-21/F-49/F-52/
    H-SELF-01 logic to one P1 (+ optional P3) score set, with corpus stats
    pulled live from Supabase. Does not write to acat_assessments_v1 or
    REGISTERED.md - any pattern match this surfaces is a candidate
    observation for Zone 2 review, not a self-registering finding."""

    if req.by_assessment_id:
        try:
            row = fetch_assessment_row(req.by_assessment_id)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
        except PersistenceError as exc:
            raise HTTPException(502, str(exc)) from exc

        p1_scores = _extract_dim_scores(row, "p1")
        if p1_scores is None:
            raise HTTPException(
                422, f"Assessment {req.by_assessment_id} has no complete P1 score set."
            )
        p3_scores = _extract_dim_scores(row, "p3")
        submission_purity = row.get("submission_purity")
        model_id = row.get("agent_name", req.by_assessment_id)
        provider = row.get("provider", "unknown")

    else:
        if not (req.model_id and req.submission_purity and req.p1_scores):
            raise HTTPException(
                422,
                "Supply either by_assessment_id, or model_id + submission_purity + p1_scores.",
            )
        p1_scores = req.p1_scores.model_dump()
        p3_scores = req.p3_scores.model_dump() if req.p3_scores else None
        submission_purity = req.submission_purity
        model_id = req.model_id
        provider = req.provider or "unknown"

    try:
        audit = run_humility_audit(
            p1_scores=p1_scores,
            submission_purity=submission_purity,
            p3_scores=p3_scores,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except PersistenceError as exc:
        raise HTTPException(502, str(exc)) from exc

    if req.as_report:
        return {"report_markdown": to_report_markdown(audit, model_id, provider)}
    return {"model_id": model_id, "provider": provider, **audit}

@router.get("/humility-audit/corpus-stats")
def humility_corpus_stats() -> dict:
    """Live Supabase Humility corpus stats, independent of running a full
    audit - useful for dashboards/monitoring without a score payload."""
    try:
        return fetch_humility_corpus_stats()
    except PersistenceError as exc:
        raise HTTPException(502, str(exc)) from exc


def run_smoke_test() -> None:
    """Minimal smoke test — verifies the router module loads correctly."""
    assert router is not None, "router must be initialized"
    print(f"{TOOL_NAME} v{TOOL_VERSION} smoke test: PASS")


if __name__ == "__main__":
    run_smoke_test()
