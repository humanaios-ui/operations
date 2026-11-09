"""Minimal MCP (JSON-RPC 2.0) request handler. Standard library only."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable

log = logging.getLogger("research_hub")

SUPPORTED_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
SERVER_INFO = {"name": "research-hub", "version": "0.1.0"}


class ToolError(Exception):
    """Safe to show to the caller. Anything else becomes a generic error."""


@dataclass
class Tool:
    name: str
    description: str
    schema: dict[str, Any]
    fn: Callable[[dict[str, Any]], Any]
    read_only: bool = True

    def listing(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.schema,
            "annotations": {"readOnlyHint": self.read_only, "openWorldHint": False},
        }


_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool,
          "array": list, "object": dict}


def validate_args(schema: dict[str, Any], args: Any, path: str = "arguments") -> None:
    """Small JSON-Schema subset: type, required, enum, min/max, length, items."""
    t = schema.get("type")
    if t:
        py = _TYPES[t]
        ok = isinstance(args, py) and not (t in ("integer", "number") and isinstance(args, bool))
        if not ok:
            raise ToolError(f"{path} must be {t}")
    if "enum" in schema and args not in schema["enum"]:
        raise ToolError(f"{path} must be one of {schema['enum']}")
    if isinstance(args, str):
        if len(args) < schema.get("minLength", 0):
            raise ToolError(f"{path} is too short")
        if len(args) > schema.get("maxLength", 10**9):
            raise ToolError(f"{path} is too long")
    if isinstance(args, (int, float)) and not isinstance(args, bool):
        if "minimum" in schema and args < schema["minimum"]:
            raise ToolError(f"{path} must be >= {schema['minimum']}")
        if "maximum" in schema and args > schema["maximum"]:
            raise ToolError(f"{path} must be <= {schema['maximum']}")
    if isinstance(args, list):
        if len(args) > schema.get("maxItems", 10**9):
            raise ToolError(f"{path} has too many items")
        if len(args) < schema.get("minItems", 0):
            raise ToolError(f"{path} needs more items")
        for i, item in enumerate(args):
            if "items" in schema:
                validate_args(schema["items"], item, f"{path}[{i}]")
    if isinstance(args, dict):
        for key in schema.get("required", []):
            if key not in args:
                raise ToolError(f"{path}.{key} is required")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(args) - set(props)
            if extra:
                raise ToolError(f"{path} has unknown fields: {sorted(extra)}")
        for key, sub in props.items():
            if key in args:
                validate_args(sub, args[key], f"{path}.{key}")


def _err(rid: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def _ok(rid: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def handle_one(msg: Any, tools: dict[str, Tool]) -> dict[str, Any] | None:
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
        return _err(None, -32600, "Invalid Request")
    method, params, rid = msg.get("method"), msg.get("params") or {}, msg.get("id")
    notification = "id" not in msg
    if not isinstance(method, str) or not isinstance(params, dict):
        return None if notification else _err(rid, -32600, "Invalid Request")
    if notification:
        return None  # notifications/initialized, cancelled, etc.

    if method == "initialize":
        wanted = params.get("protocolVersion")
        version = wanted if wanted in SUPPORTED_VERSIONS else SUPPORTED_VERSIONS[0]
        return _ok(rid, {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": ("Research router. Outputs are advisory candidates "
                             "(authority_effect NONE). Graph writes are proposals only."),
        })
    if method == "ping":
        return _ok(rid, {})
    if method == "tools/list":
        return _ok(rid, {"tools": [t.listing() for t in tools.values()]})
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments") or {}
        tool = tools.get(name) if isinstance(name, str) else None
        if tool is None:
            return _err(rid, -32602, "Unknown tool")
        try:
            validate_args(tool.schema, args)
            out = tool.fn(args)
            text = json.dumps(out, ensure_ascii=False, default=str)
            return _ok(rid, {"content": [{"type": "text", "text": text}], "isError": False})
        except ToolError as exc:
            return _ok(rid, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        except Exception:  # never leak internals or keys
            log.exception("tool %s failed", name)
            return _ok(rid, {"content": [{"type": "text", "text": "Internal tool error"}],
                             "isError": True})
    return _err(rid, -32601, "Method not found")


def handle(payload: Any, tools: dict[str, Tool]) -> Any:
    """Return a response object, a list of them (batch), or None (nothing to send)."""
    if isinstance(payload, list):
        if not payload:
            return _err(None, -32600, "Invalid Request")
        out = [r for r in (handle_one(m, tools) for m in payload) if r is not None]
        return out or None
    return handle_one(payload, tools)
