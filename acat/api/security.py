"""ACAT write-access gate (interim mitigation — audit S-062726 P0-URGENT).

Fail-closed guard for mutating endpoints. Until a full auth model is chosen
(Z2 decision), this stops anonymous callers from poisoning stored assessments
AND the corpus statistics derived from them.

Behaviour (fail-closed):
  * If env ACAT_WRITE_TOKEN is unset/empty  -> 503 (writes paused).
  * If request header X-ACAT-Write-Token is missing or does not match -> 401.
  * Otherwise the write proceeds.

Deploy note (Z3/Night): set ACAT_WRITE_TOKEN in the service environment and
distribute it only to legitimate ingest pipelines. Read endpoints (health,
GET /assess/{job_id}) are intentionally NOT gated.
"""
from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException, status


def require_write_token(
    x_acat_write_token: str | None = Header(default=None),
) -> None:
    """FastAPI dependency guarding mutating endpoints. Fail-closed."""
    expected = os.environ.get("ACAT_WRITE_TOKEN", "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ACAT writes are paused (no write token configured).",
        )
    supplied = x_acat_write_token or ""
    # constant-time compare to avoid leaking the token via timing
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid write token.",
        )
