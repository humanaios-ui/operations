from datetime import datetime


def compute_contamination_delta_seconds(p1_timestamp: str, first_user_message_timestamp: str) -> int | None:
    if not p1_timestamp or not first_user_message_timestamp:
        return None
    p1 = datetime.fromisoformat(p1_timestamp.replace("Z", "+00:00"))
    first = datetime.fromisoformat(first_user_message_timestamp.replace("Z", "+00:00"))
    return int((first - p1).total_seconds())


def classify_contamination(delta_seconds: int | None) -> str:
    if delta_seconds is None:
        return "unknown"
    if delta_seconds <= 60:
        return "clean"
    return "contaminated"
