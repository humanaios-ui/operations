from fastapi import APIRouter

from acat.api.services.report_service import draft_report, get_report

router = APIRouter()


@router.post("/report/{assessment_id}/draft")
def post_draft_report(assessment_id: str):
    return draft_report(assessment_id)


@router.get("/report/{assessment_id}")
def read_report(assessment_id: str):
    return get_report(assessment_id)
