from acat.scoring.calculators import compute_li, compute_sag, compute_him


def score_session(assessment_id: str) -> dict:
    # NOT wired to the persistence layer. The live LI/SAG are computed during Phase 3
    # ingest by ingest_service._compute_learning_index (which delegates to
    # calculators.compute_li). The previous body hardcoded p1_total=p3_total=0, which
    # made compute_li return None — a fake "score" that looked real (acat/ audit S-062726).
    # Fail loudly rather than emit a phantom result.
    raise NotImplementedError(
        "score_session is not wired to persistence. Live LI is computed in "
        "ingest_service._compute_learning_index during Phase 3 ingest."
    )


def validate_session_score(assessment_id: str) -> dict:
    return {
        "assessment_id": assessment_id,
        "validation_status": "pending",
        "agreement": None
    }
