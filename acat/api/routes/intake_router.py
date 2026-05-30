from __future__ import annotations

from fastapi import APIRouter, HTTPException

from acat.api.services.ingest_service import (
    IntakeValidationError,
    PersistenceError,
    ingest_phase1,
    ingest_phase3,
)

router = APIRouter()


@router.post("/intake/phase1")
def intake_phase1(payload: dict) -> dict:
    try:
        return ingest_phase1(payload)
    except IntakeValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected phase1 failure: {exc}") from exc


@router.post("/intake/phase3")
def intake_phase3(payload: dict) -> dict:
    try:
        return ingest_phase3(payload)
    except IntakeValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected phase3 failure: {exc}") from exc
