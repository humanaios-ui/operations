from fastapi import APIRouter

from acat.api.services.ingest_service import ingest_phase1, ingest_phase3

router = APIRouter()


@router.post("/intake/phase1")
def post_phase1(payload: dict):
    return ingest_phase1(payload)


@router.post("/intake/phase3")
def post_phase3(payload: dict):
    return ingest_phase3(payload)
