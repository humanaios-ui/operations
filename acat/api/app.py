from __future__ import annotations
import os
from fastapi import FastAPI
from starlette.responses import JSONResponse
from acat.api.routes.assess_router import router as assess_router
from acat.api.routes.human_score_route import router as human_score_router
from acat.api.routes.intake_router import router as intake_router
app = FastAPI(title="ACAT API", version="0.1.0")


@app.middleware("http")
async def _acat_write_guard(request, call_next):
    """Write protection for acat/ mutating endpoints (S-062726 · acat/ audit reopen).

    Two layers, evaluated for every mutating request (POST/PUT/PATCH/DELETE):
      1. ACAT_WRITES_PAUSED kill-switch -> 503 (emergency / interim corpus-poisoning pause).
      2. API-key gate: when ACAT_API_KEYS is configured (comma-separated), the request must
         carry a matching X-ACAT-Key header, else 401. When ACAT_API_KEYS is unset, writes
         pass through -- the pause kill-switch is the interim protection until keys are
         provisioned, and tests / local dev run keyless.

    Reopen sequence for the operator: set ACAT_API_KEYS (enables the gate), then unset
    ACAT_WRITES_PAUSED (lifts the pause). GET / read endpoints are never guarded.

    NEXT INCREMENTS (audits/AUDIT_ACAT_S-062726.md §9): route anonymous public intake to a
    quarantine staging table; stop using the Supabase service_role key for caller-driven
    writes and enforce Row-Level Security on the canonical tables.
    """
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if os.getenv("ACAT_WRITES_PAUSED", "").strip().lower() in ("1", "true", "yes", "on"):
            return JSONResponse(status_code=503, content={"detail": "ACAT writes are paused for maintenance."})
        keys = {k.strip() for k in os.getenv("ACAT_API_KEYS", "").split(",") if k.strip()}
        if keys and request.headers.get("X-ACAT-Key", "").strip() not in keys:
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid X-ACAT-Key for a write endpoint."})
    return await call_next(request)


app.include_router(intake_router, prefix="/api/v1/acat", tags=["acat"])
app.include_router(assess_router, prefix="/api/v1/acat", tags=["acat"])
app.include_router(human_score_router, prefix="/api/v1/acat", tags=["acat"])
@app.get("/")
def root() -> dict:
 return {
 "status": "ok",
 "service": "acat-api",
 "message": "ACAT API is running",
 "health_url": "/api/v1/acat/health",
 "intake_phase1_url": "/api/v1/acat/intake/phase1",
 "intake_phase3_url": "/api/v1/acat/intake/phase3",
 "assess_url": "/api/v1/acat/assess",
 "human_score_url": "/api/v1/acat/human-score",
 "version": "0.1.0",
 }
@app.get("/api/v1/acat/health")
def health() -> dict:
 return {
 "status": "ok",
 "service": "acat-api",
 "version": "0.1.0",
 }
