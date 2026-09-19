def build_dedupe_key(payload: dict) -> str:
    session_id = payload.get("session_id", "")
    phase = payload.get("phase", "")
    rater_id = payload.get("rater_id", "")
    return f"{session_id}:{phase}:{rater_id}"
