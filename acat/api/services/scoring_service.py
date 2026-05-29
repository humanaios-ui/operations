from acat.scoring.calculators import compute_li, compute_sag, compute_him


def score_session(assessment_id: str) -> dict:
    # TODO: fetch p1 + p3 inputs from persistence layer
    p1_total = 0
    p3_total = 0

    return {
        "assessment_id": assessment_id,
        "score_status": "provisional",
        "scorer_version": "0.1.0",
        "li": compute_li(p1_total, p3_total),
        "sag": compute_sag(p1_total, p3_total),
        "him": compute_him({})
    }


def validate_session_score(assessment_id: str) -> dict:
    return {
        "assessment_id": assessment_id,
        "validation_status": "pending",
        "agreement": None
    }
