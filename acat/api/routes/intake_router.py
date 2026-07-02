from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from acat.api.security import require_write_token
from acat.api.services.ingest_service import (
    IntakeValidationError,
    PersistenceError,
    ingest_phase1,
    ingest_phase3,
)

logger = logging.getLogger("acat.intake")

router = APIRouter()


@router.post("/intake/phase1", dependencies=[Depends(require_write_token)])
def intake_phase1(payload: dict) -> dict:
    try:
        return ingest_phase1(payload)
    except IntakeValidationError as exc:
        # validation messages are safe to surface (no internal/infra detail)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("phase1 persistence failure", exc_info=exc)
        raise HTTPException(status_code=502, detail="Persistence error.") from exc
    except Exception as exc:
        logger.error("phase1 unexpected failure", exc_info=exc)
        raise HTTPException(status_code=500, detail="Unexpected phase1 failure.") from exc


@router.post("/intake/phase3", dependencies=[Depends(require_write_token)])
def intake_phase3(payload: dict) -> dict:
    try:
        return ingest_phase3(payload)
    except IntakeValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("phase3 persistence failure", exc_info=exc)
        raise HTTPException(status_code=502, detail="Persistence error.") from exc
    except Exception as exc:
        logger.error("phase3 unexpected failure", exc_info=exc)
        raise HTTPException(status_code=500, detail="Unexpected phase3 failure.") from exc
