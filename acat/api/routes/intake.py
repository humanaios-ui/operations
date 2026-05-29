from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from acat.api.services.ingest_service import (
    IntakeValidationError,
    PersistenceError,
    ingest_phase1,
    ingest_phase3,
)

router = APIRouter()


@router.post("/intake/phase1", status_code=status.HTTP_201_CREATED)
def post_phase1(payload: dict):
    try:
        return ingest_phase1(payload)
    except IntakeValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Phase 1 intake failed: {exc}",
        ) from exc


@router.post("/intake/phase3", status_code=status.HTTP_201_CREATED)
def post_phase3(payload: dict):
    try:
        return ingest_phase3(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Phase 3 intake failed: {exc}",
        ) from exc
