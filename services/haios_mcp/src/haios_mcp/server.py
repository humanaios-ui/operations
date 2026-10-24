"""MCP v2 service: stdio for local clients, authenticated loopback HTTP for tunnel use."""

from __future__ import annotations

import argparse
import hmac
import os
from typing import Any

from haios_mcp.core import HumanAIOSBridge


class RequireLocalBearer:
    """Outer ASGI gate. Runs before MCP routes, including initialization."""

    def __init__(self, app: Any, token: str):
        if len(token) < 32:
            raise ValueError("HAIOS_MCP_TOKEN must be at least 32 characters")
        self.app = app
        self.token = token.encode("utf-8")

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.lower(): v for k, v in scope.get("headers", [])}
        value = headers.get(b"authorization", b"")
        if not hmac.compare_digest(value, b"Bearer " + self.token):
            await send({"type": "http.response.start", "status": 401,
                        "headers": [(b"content-type", b"text/plain"),
                                    (b"cache-control", b"no-store"),
                                    (b"www-authenticate", b"Bearer")]})
            await send({"type": "http.response.body", "body": b"Unauthorized"})
            return
        await self.app(scope, receive, send)


def create_server(bridge: HumanAIOSBridge):
    from mcp.server import MCPServer

    mcp = MCPServer(
        "HumanAIOS Witness",
        instructions="Read-only HumanAIOS context and bounded Unit Zero conversation. No action authority.",
    )

    @mcp.tool()
    def haios_status() -> dict:
        """Report local HumanAIOS document availability and agent setup, without network calls."""
        return bridge.status()

    @mcp.tool()
    def haios_read_document(filename: str, limit: int = 12000) -> dict:
        """Read an allowlisted public operations file with its SHA-256 and truncation status."""
        return bridge.read_document(filename, limit)

    @mcp.tool()
    def haios_talk(message: str, session_id: str = "") -> dict:
        """Ask Unit Zero using bounded, source-attributed context. Reuse session_id for follow-ups."""
        return bridge.talk(message, session_id)

    return mcp


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Read-only HumanAIOS MCP service")
    parser.add_argument("--transport", choices=("stdio", "http"), default="stdio")
    parser.add_argument("--port", type=int, default=8768)
    parser.add_argument("--repo", default=os.environ.get("HAIOS_REPO_ROOT", ""))
    args = parser.parse_args(argv)
    if not args.repo:
        parser.error("Pass --repo or set HAIOS_REPO_ROOT")
    if args.transport == "http" and not 1024 <= args.port <= 65535:
        parser.error("HTTP port must be 1024 to 65535")
    bridge = HumanAIOSBridge(args.repo)
    mcp = create_server(bridge)
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        token = os.environ.get("HAIOS_MCP_TOKEN", "")
        if len(token) < 32:
            parser.error("HTTP mode requires HAIOS_MCP_TOKEN of 32+ characters")
        import uvicorn
        app = RequireLocalBearer(mcp.streamable_http_app(), token)
        # Intentionally no non-loopback or public host override.
        uvicorn.run(app, host="127.0.0.1", port=args.port,
                    proxy_headers=False, access_log=False)


if __name__ == "__main__":
    main()
