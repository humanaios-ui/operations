from __future__ import annotations

from typing import Any

from acat.api.services.elicitation_service import run_assessment
from acat.api.services.ingest_service import ingest_phase1, ingest_phase3


def _health_impl(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "acat-api",
        "version": "0.1.0",
    }


TOOLS: list[dict[str, Any]] = [
    {
        "name": "health",
        "description": "Returns ACAT API health status.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": false,
        },
        "handler": _health_impl,
    },
    {
        "name": "intake_phase1",
        "description": "Submit an ACAT Phase 1 intake payload.",
        "inputSchema": {
            "type": "object",
            "required": ["session_id", "agent_name", "phase", "scores", "submission_purity"],
            "properties": {
                "session_id": {"type": "string", "minLength": 1},
                "assessment_id": {"type": "string", "minLength": 1},
                "agent_name": {"type": "string", "minLength": 1},
                "provider": {"type": "string"},
                "phase": {"type": "string", "enum": ["phase1"]},
                "p1_timestamp": {"type": "string", "format": "date-time"},
                "session_start_timestamp": {"type": "string", "format": "date-time"},
                "first_user_message_timestamp": {"type": "string", "format": "date-time"},
                "submission_purity": {
                    "type": "string",
                    "enum": [
                        "two_stage_verified",
                        "single_shot_legacy",
                        "external_only",
                        "agent_self_only",
                    ],
                },
                "scores": {
                    "type": "object",
                    "required": ["truth", "service", "harm", "autonomy", "value", "humility"],
                    "properties": {
                        "truth": {"type": "number", "minimum": 0, "maximum": 100},
                        "service": {"type": "number", "minimum": 0, "maximum": 100},
                        "harm": {"type": "number", "minimum": 0, "maximum": 100},
                        "autonomy": {"type": "number", "minimum": 0, "maximum": 100},
                        "value": {"type": "number", "minimum": 0, "maximum": 100},
                        "humility": {"type": "number", "minimum": 0, "maximum": 100},
                    },
                    "additionalProperties": false,
                },
                "metadata": {"type": "object"},
            },
            "additionalProperties": true,
        },
        "handler": ingest_phase1,
    },
    {
        "name": "intake_phase3",
        "description": "Submit an ACAT Phase 3 intake payload.",
        "inputSchema": {
            "type": "object",
            "required": ["phase", "scores"],
            "properties": {
                "session_id": {"type": "string", "minLength": 1},
                "assessment_id": {"type": "string", "minLength": 1},
                "agent_name": {"type": "string", "minLength": 1},
                "provider": {"type": "string"},
                "phase": {"type": "string", "enum": ["phase3"]},
                "submitted_at": {"type": "string", "format": "date-time"},
                "submission_purity": {
                    "type": "string",
                    "enum": [
                        "two_stage_verified",
                        "single_shot_legacy",
                        "external_only",
                        "agent_self_only",
                    ],
                },
                "scores": {
                    "type": "object",
                    "required": ["truth", "service", "harm", "autonomy", "value", "humility"],
                    "properties": {
                        "truth": {"type": "number", "minimum": 0, "maximum": 100},
                        "service": {"type": "number", "minimum": 0, "maximum": 100},
                        "harm": {"type": "number", "minimum": 0, "maximum": 100},
                        "autonomy": {"type": "number", "minimum": 0, "maximum": 100},
                        "value": {"type": "number", "minimum": 0, "maximum": 100},
                        "humility": {"type": "number", "minimum": 0, "maximum": 100},
                    },
                    "additionalProperties": false,
                },
                "metadata": {"type": "object"},
            },
            "anyOf": [
                {"required": ["assessment_id"]},
                {"required": ["session_id"]},
            ],
            "additionalProperties": true,
        },
        "handler": ingest_phase3,
    },
    {
        "name": "assess",
        "description": "Run a full ACAT assessment end-to-end using the configured provider request flow.",
        "inputSchema": {
            "type": "object",
            "required": ["agent_name", "provider", "api_key", "model"],
            "properties": {
                "agent_name": {"type": "string", "minLength": 1},
                "provider": {"type": "string", "enum": ["anthropic"]},
                "api_key": {"type": "string", "minLength": 1},
                "model": {"type": "string", "minLength": 1},
                "mode": {"type": "string", "enum": ["two_stage"], "default": "two_stage"},
                "wait_seconds": {"type": "integer", "minimum": 60, "default": 65},
                "assessment_id": {"type": "string", "minLength": 1},
                "session_id": {"type": "string", "minLength": 1},
                "metadata": {"type": "object"},
            },
            "additionalProperties": false,
        },
        "handler": run_assessment,
    },
]


TOOL_MAP: dict[str, dict[str, Any]] = {tool["name"]: tool for tool in TOOLS}


def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": tool["inputSchema"],
        }
        for tool in TOOLS
    ]


def call_tool(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    tool = TOOL_MAP.get(name)
    if tool is None:
        raise ValueError(f"Unknown tool: {name}")

    handler = tool["handler"]
    safe_args = arguments or {}
    result = handler(safe_args)

    return {
        "content": [
            {
                "type": "text",
                "text": str(result),
            }
        ],
        "structuredContent": result,
        "isError": False,
    }
