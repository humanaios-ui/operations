from __future__ import annotations

from fastapi import APIRouter, HTTPException

from acat.api.services.elicitation_service import run_assessment
from acat.api.services.ingest_service import IntakeValidationError, PersistenceError
from acat.api.services.provider_clients.anthropic_client import AnthropicClientError

router = APIRouter()


@router.post("/assess")
def assess(payload: dict) -> dict:
    try:
        return run_assessment(payload)
    except IntakeValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AnthropicClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected assess failure: {exc}") from exc
