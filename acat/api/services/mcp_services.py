from __future__ import annotations

import json
from typing import Any

from acat.api.services.ingest_service import IntakeValidationError, PersistenceError
from acat.api.services.mcp_tools import call_tool, list_tools
from acat.api.services.provider_clients.anthropic_client import AnthropicClientError

MCP_PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "acat-api"
SERVER_VERSION = "0.1.0"


def _success(id_value: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": id_value,
        "result": result,
    }


def _error(id_value: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": id_value,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if data is not None:
        payload["error"]["data"] = data
    return payload


def handle_jsonrpc_message(message: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(message, dict):
        return _error(None, -32600, "Invalid Request")

    if message.get("jsonrpc") != "2.0":
        return _error(message.get("id"), -32600, "Invalid Request")

    method = message.get("method")
    params = message.get("params") or {}
    request_id = message.get("id")

    # Notifications do not require responses.
    is_notification = request_id is None

    try:
        if method == "initialize":
            result = {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {
                        "listChanged": False,
                    },
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION,
                },
            }
            return None if is_notification else _success(request_id, result)

        if method == "notifications/initialized":
            return None

        if method == "ping":
            return None if is_notification else _success(request_id, {})

        if method == "tools/list":
            result = {
                "tools": list_tools(),
            }
            return None if is_notification else _success(request_id, result)

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}

            if not isinstance(name, str) or not name:
                return None if is_notification else _error(request_id, -32602, "Invalid params", {"reason": "Missing tool name"})
            if not isinstance(arguments, dict):
                return None if is_notification else _error(request_id, -32602, "Invalid params", {"reason": "Tool arguments must be an object"})

            result = call_tool(name, arguments)
            return None if is_notification else _success(request_id, result)

        return None if is_notification else _error(request_id, -32601, f"Method not found: {method}")

    except ValueError as exc:
        return None if is_notification else _error(request_id, -32602, str(exc))
    except IntakeValidationError as exc:
        return None if is_notification else _error(request_id, -32602, str(exc))
    except (AnthropicClientError, PersistenceError) as exc:
        return None if is_notification else _error(request_id, -32000, str(exc))
    except Exception as exc:
        return None if is_notification else _error(request_id, -32603, f"Internal error: {exc}")


def sse_frame(data: dict[str, Any], event: str = "message") -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
