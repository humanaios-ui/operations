from __future__ import annotations

from fastapi import FastAPI

from acat.api.routes.assess_router import router as assess_router
from acat.api.routes.intake_router import router as intake_router

app = FastAPI(title="ACAT API", version="0.1.0")

app.include_router(intake_router, prefix="/api/v1/acat", tags=["acat"])
app.include_router(assess_router, prefix="/api/v1/acat", tags=["acat"])


@app.get("/api/v1/acat/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "acat-api",
        "version": "0.1.0",
    }
