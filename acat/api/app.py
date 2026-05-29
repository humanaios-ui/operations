from fastapi import FastAPI

from acat.api.routes import intake, scoring, reports, health

app = FastAPI(title="ACAT API", version="0.1.0")

app.include_router(intake.router, prefix="/api/v1/acat")
app.include_router(scoring.router, prefix="/api/v1/acat")
app.include_router(reports.router, prefix="/api/v1/acat")
app.include_router(health.router, prefix="/api/v1/acat")


@app.get("/")
def root():
    return {"service": "acat-api", "status": "ok"}
