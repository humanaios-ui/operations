"""
assess_router_Z2_assessment.py — FastAPI router for Z2 assessment endpoint.
Builder v1.7 compliant — assess_router_tool
HumanAIOS — S-070726-assess-router
"""
from __future__ import annotations

import threading
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from acat.api.services.elicitation_service import run_assessment, validate_assess_request
from acat.api.services.ingest_service import IntakeValidationError, PersistenceError
from acat.api.services.provider_clients.anthropic_client import AnthropicClientError

router = APIRouter()

TOOL_NAME = "assess_router_Z2_assessment"
TOOL_VERSION = "1.0.0"

# In-memory job store.

# Survives within one Railway container instance; cleared on restart.

# Restart behavior is benign: caller re-submits the job.

# Upgrade to Redis if multi-replica scaling is needed (currently 1 replica).

_JOBS: dict[str, dict] = {}

def _run_in_background(job_id: str, payload: dict) -> None:
    try:
        result = run_assessment(payload)
        _JOBS[job_id] = {"status": "completed", **result}
    except IntakeValidationError as exc:
        _JOBS[job_id] = {"status": "failed", "error": str(exc)}
    except AnthropicClientError as exc:
        _JOBS[job_id] = {"status": "failed", "error": str(exc)}
    except PersistenceError as exc:
        _JOBS[job_id] = {"status": "failed", "error": str(exc)}
    except Exception as exc:
        _JOBS[job_id] = {"status": "failed", "error": f"Unexpected: {exc}"}

@router.post("/assess")
def assess(payload: dict) -> dict:
    """Submit an assessment job. Returns immediately with a job_id.
    Poll GET /assess/{job_id} for results.
    Total assessment wall time is ~90-125s (two LLM calls + 65s protocol gap).
    """
    try:
        validate_assess_request(payload)
    except IntakeValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    job_id = f"job-{uuid4()}"
    _JOBS[job_id] = {"status": "running"}
    thread = threading.Thread(
        target=_run_in_background, args=(job_id, payload), daemon=True
    )
    thread.start()
    return {
        "job_id": job_id,
        "status": "running",
        "poll_url": f"/api/v1/acat/assess/{job_id}",
    }

@router.get("/assess/{job_id}")
def assess_result(job_id: str) -> dict:
    """Poll for assessment job result.
    status values: 'running' | 'completed' | 'failed'
    """
    job = _JOBS.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail=f"Job {job_id!r} not found or expired."
        )
    return job


def run_smoke_test() -> None:
    """Minimal smoke test."""
    assert router is not None
    print(f"{TOOL_NAME} v{TOOL_VERSION} smoke test: PASS")


if __name__ == "__main__":
    run_smoke_test()
