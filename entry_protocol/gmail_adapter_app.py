"""FastAPI Pub/Sub ingress for the private HumanAIOS Gmail adapter.

Deployment is intentionally fail-closed:
- Pub/Sub OIDC verification is required.
- Notification emailAddress must match GMAIL_USER_ID.
- Live Gmail credentials are read only from runtime secrets/env.
"""
from __future__ import annotations

from functools import lru_cache
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request

from entry_protocol.gmail_push_adapter import (
    GmailAdapterConfig,
    GmailInboundAdapter,
    GoogleGmailClient,
    PrivateMailLedger,
    decode_pubsub_notification,
    normalize_address,
)


app = FastAPI(title="HumanAIOS Private Gmail Adapter", version="0.1.0")


@lru_cache(maxsize=1)
def live_adapter() -> GmailInboundAdapter:
    config = GmailAdapterConfig.from_env()
    return GmailInboundAdapter(
        gmail=GoogleGmailClient.from_env(),
        store=PrivateMailLedger(config.database_path),
        config=config,
    )


def _verify_pubsub_oidc(authorization: str | None) -> dict[str, Any]:
    audience = os.environ.get("PUBSUB_OIDC_AUDIENCE", "").strip()
    allowed_service_account = normalize_address(
        os.environ.get("PUBSUB_PUSH_SERVICE_ACCOUNT", "")
    )
    if not audience or not allowed_service_account:
        raise HTTPException(
            status_code=503,
            detail="Pub/Sub OIDC verification is not configured",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing Pub/Sub bearer token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(
            token,
            GoogleRequest(),
            audience=audience,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid Pub/Sub OIDC token") from exc

    token_email = normalize_address(str(claims.get("email", "")))
    email_verified = claims.get("email_verified")
    if token_email != allowed_service_account or email_verified is not True:
        raise HTTPException(status_code=403, detail="Pub/Sub principal not authorized")
    return claims


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "mode": "private-gmail-adapter"}


@app.post("/gmail/push")
async def gmail_push(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _verify_pubsub_oidc(authorization)
    try:
        envelope = await request.json()
        email_address, history_id, pubsub_message_id = decode_pubsub_notification(
            envelope
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    adapter = live_adapter()
    expected = normalize_address(adapter.config.mailbox_address)
    if email_address != expected:
        raise HTTPException(
            status_code=403,
            detail="notification mailbox does not match configured mailbox",
        )

    result = adapter.handle_push(history_id)
    # No Gmail IDs, body text, addresses, or private event refs are returned.
    return {
        "status": result.status,
        "pubsub_message_present": bool(pubsub_message_id),
        "processed": result.processed,
        "ignored": result.ignored,
        "replays": result.replays,
        "held": result.held,
        "resync_required": (
            result.status in {
                "BASELINE_MISSING_RESYNC_REQUIRED",
                "HISTORY_EXPIRED_RESYNC_REQUIRED",
            }
        ),
    }
