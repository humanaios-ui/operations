from fastapi import APIRouter

from acat.api.services.scoring_service import score_session, validate_session_score

router = APIRouter()


@router.post("/score/session/{assessment_id}")
def post_score_session(assessment_id: str):
    return score_session(assessment_id)


@router.post("/score/validate/{assessment_id}")
def post_validate_session(assessment_id: str):
    return validate_session_score(assessment_id)
