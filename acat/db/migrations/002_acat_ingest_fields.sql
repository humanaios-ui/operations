def initialize_acat_session(payload: dict) -> dict:
    return {
        "status": "initialized",
        "session_id": payload.get("session_id"),
        "assessment_id": payload.get("assessment_id")
    }
