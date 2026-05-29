from acat.normalization.purity import validate_submission_purity
from acat.normalization.flags import derive_quality_flags


def normalize_phase1_payload(payload: dict) -> dict:
    validate_submission_purity(payload.get("submission_purity"))

    normalized = dict(payload)
    normalized["agent_name_canonical"] = payload.get("agent_name", "").strip().lower()
    normalized["quality_flags"] = derive_quality_flags(normalized)
    return normalized
