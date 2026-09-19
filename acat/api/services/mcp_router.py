from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from acat.api.services.mcp_service import (
    MCP_PROTOCOL_VERSION,
    handle_jsonrpc_message,
    sse_frame,
)

router = APIRouter()


@router.get("/mcp")
async def mcp_sse(
    origin: str | None = Header(default=None),
) -> StreamingResponse:
    # Minimal origin pass-through. Tighten this to an allowlist before broad exposure.
    async def event_stream() -> AsyncIterator[str]:
        yield sse_frame(
            {
                "jsonrpc": "2.0",
                "method": "notifications/message",
                "params": {
                    "level": "info",
                    "data": "ACAT MCP stream connected",
                },
            },
            event="message",
        )

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
    }
    if origin:
        headers["Access-Control-Allow-Origin"] = origin

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=headers,
    )


@router.post("/mcp")
async def mcp_post(
    request: Request,
    origin: str | None = Header(default=None),
) -> Response:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc}") from exc

    response_payload = handle_jsonrpc_message(payload)

    # JSON-RPC notification: no response body required.
    if response_payload is None:
        headers = {"MCP-Protocol-Version": MCP_PROTOCOL_VERSION}
        if origin:
            headers["Access-Control-Allow-Origin"] = origin
        return Response(status_code=202, headers=headers)

    headers = {"MCP-Protocol-Version": MCP_PROTOCOL_VERSION}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin

    return JSONResponse(content=response_payload, headers=headers)
