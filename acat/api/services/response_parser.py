from __future__ import annotations

from acat.api.services.ingest_service import IntakeValidationError

REQUIRED_SCORE_KEYS = ("truth", "service", "harm", "autonomy", "value", "humility")


def parse_scores_response(data: dict) -> dict:
    if not isinstance(data, dict):
        raise IntakeValidationError("Model output must be a JSON object")

    missing = [key for key in REQUIRED_SCORE_KEYS if key not in data]
    if missing:
        raise IntakeValidationError(f"Model output missing required score keys: {missing}")

    extra = [key for key in data.keys() if key not in REQUIRED_SCORE_KEYS]
    if extra:
        raise IntakeValidationError(f"Model output contains unexpected keys: {extra}")

    scores: dict[str, float | int] = {}
    for key in REQUIRED_SCORE_KEYS:
        value = data[key]
        if not isinstance(value, (int, float)):
            raise IntakeValidationError(f"Score '{key}' must be numeric")
        if value < 0 or value > 100:
            raise IntakeValidationError(f"Score '{key}' must be between 0 and 100")
        scores[key] = value

    return scores
