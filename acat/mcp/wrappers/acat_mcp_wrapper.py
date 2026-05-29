from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

ACAT_API_BASE_URL = os.getenv("ACAT_API_BASE_URL", "http://localhost:8000")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post_json(url: str, payload: dict, timeout: int = 15) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def initialize_acat_session(payload: dict) -> dict:
    working = dict(payload)
    working.setdefault("session_start_timestamp", _utcnow_iso())

    try:
        response = _post_json(
            f"{ACAT_API_BASE_URL}/api/v1/acat/intake/phase1",
            working,
        )
        return {
            "status": response.get("status", "accepted"),
            "session_id": response.get("session_id"),
            "assessment_id": response.get("assessment_id"),
            "contamination_status": response.get("contamination_status"),
            "contamination_delta_seconds": response.get("contamination_delta_seconds"),
        }
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {
            "status": "error",
            "error_type": "http_error",
            "status_code": exc.code,
            "detail": detail,
        }
    except urllib.error.URLError as exc:
        return {
            "status": "error",
            "error_type": "connection_error",
            "detail": str(exc),
        }
