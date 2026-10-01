#!/usr/bin/env python3
"""
Control-Plane GitHub Adapter — v0.1.0
Builder v1.7 compliant · pipeline_tool
HumanAIOS · CPC-002

Transform exported GitHub event/API evidence into the raw observation shape
consumed by control_plane_custody_observer_v0_1.py.

The adapter is intentionally conservative:
- account identity does not prove human origin;
- decision custody defaults to UNKNOWN;
- authority evidence defaults to UNKNOWN;
- boundary state defaults to UNKNOWN unless mechanically supplied;
- authority_effect is always NONE.

Usage:
  python3 tools/control_plane_github_adapter_v0_1.py --input evidence.json
  python3 tools/control_plane_github_adapter_v0_1.py --input evidence.json --output observations.json
  python3 tools/control_plane_github_adapter_v0_1.py --smoke-test
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List


TOOL_NAME = "control_plane_github_adapter"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "pipeline_tool"
TOOL_SESSION = "CPC-002"
TOOL_ZONE = 1


class AdapterError(ValueError):
    """Raised when GitHub evidence cannot be adapted without guessing."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _unique(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _login(payload: Dict[str, Any]) -> str | None:
    for key in ("sender", "user", "actor", "merged_by"):
        item = payload.get(key)
        if isinstance(item, dict) and _text(item.get("login")):
            return _text(item.get("login"))
    return None


def positive_origin(login: str | None, evidence_text: str) -> Dict[str, Any]:
    """Return positive provenance only; otherwise abstain."""
    low_login = (login or "").lower()
    low = evidence_text.lower()
    evidence: List[str] = []

    if low_login.endswith("[bot]"):
        return {
            "origin_class": "KNOWN_BOT",
            "agent": login,
            "evidence": ["GitHub bot/app login"],
        }

    if "humanaios-origin: ai-agent" in low:
        match = re.search(r"agent=([^;\n>]+)", evidence_text, flags=re.I)
        agent = match.group(1).strip() if match else "AI agent"
        evidence.append("explicit humanaios-origin ai-agent watermark")
        return {"origin_class": "KNOWN_AI", "agent": agent, "evidence": evidence}

    if (
        "generated with claude code" in low
        or "claude-session:" in low
        or "noreply@anthropic.com" in low
        or "co-authored-by: claude" in low
    ):
        return {
            "origin_class": "KNOWN_AI",
            "agent": "Claude Code",
            "evidence": ["Claude Code watermark"],
        }

    if "copilot" in low_login or "generated with github copilot" in low:
        return {
            "origin_class": "KNOWN_AI",
            "agent": "GitHub Copilot",
            "evidence": ["Copilot watermark/login"],
        }

    return {
        "origin_class": "SHARED_ACCOUNT_ORIGIN_UNKNOWN",
        "agent": None,
        "evidence": [],
    }


def _source_payload(bundle: Dict[str, Any]) -> Dict[str, Any]:
    payload = bundle.get("payload")
    if not isinstance(payload, dict):
        raise AdapterError("payload must be an object")
    return payload


def _immutable_ref(source_type: str, payload: Dict[str, Any]) -> str | None:
    if source_type == "commit":
        return _text(payload.get("sha")) or None
    if source_type in {"workflow_run", "check_run"}:
        return _text(payload.get("head_sha")) or None
    if source_type == "pull_request":
        head = payload.get("head") or {}
        if isinstance(head, dict):
            return _text(head.get("sha")) or None
    if source_type == "pr_comment":
        return _text(payload.get("head_sha")) or None
    if source_type == "ref_error":
        return _text(payload.get("attempted_sha")) or None
    return None


def _object_for(source_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if source_type == "commit":
        sha = _text(payload.get("sha"))
        if not sha:
            raise AdapterError("commit.sha is required")
        return {
            "type": "commit",
            "id": sha,
            "url": payload.get("html_url"),
            "immutable_ref": sha,
        }

    if source_type in {"workflow_run", "check_run"}:
        native_id = _text(payload.get("id"))
        if not native_id:
            raise AdapterError(f"{source_type}.id is required")
        return {
            "type": source_type,
            "id": native_id,
            "url": payload.get("html_url"),
            "immutable_ref": _immutable_ref(source_type, payload),
        }

    if source_type == "pr_comment":
        native_id = _text(payload.get("id"))
        if not native_id:
            raise AdapterError("pr_comment.id is required")
        return {
            "type": "pull_request_comment",
            "id": native_id,
            "url": payload.get("html_url"),
            "immutable_ref": _immutable_ref(source_type, payload),
        }

    if source_type == "pull_request":
        number = _text(payload.get("number"))
        if not number:
            raise AdapterError("pull_request.number is required")
        return {
            "type": "pull_request",
            "id": number,
            "url": payload.get("html_url"),
            "immutable_ref": _immutable_ref(source_type, payload),
        }

    if source_type == "ref_error":
        ref = _text(payload.get("ref"))
        if not ref:
            raise AdapterError("ref_error.ref is required")
        return {
            "type": "git_ref",
            "id": ref,
            "url": payload.get("html_url"),
            "immutable_ref": _immutable_ref(source_type, payload),
        }

    raise AdapterError(f"unsupported source_type: {source_type}")


def _observed_at(source_type: str, payload: Dict[str, Any]) -> str | None:
    keys = {
        "commit": ("committed_at", "timestamp", "created_at"),
        "workflow_run": ("updated_at", "run_started_at", "created_at"),
        "check_run": ("completed_at", "started_at", "created_at"),
        "pr_comment": ("created_at", "updated_at"),
        "pull_request": ("merged_at", "closed_at", "updated_at", "created_at"),
        "ref_error": ("observed_at",),
    }.get(source_type, ())
    for key in keys:
        value = _text(payload.get(key))
        if value:
            return value
    return None


def _evidence_text(source_type: str, payload: Dict[str, Any]) -> str:
    fields = [
        payload.get("message"),
        payload.get("body"),
        payload.get("title"),
        json.dumps(payload.get("commit") or {}, sort_keys=True),
    ]
    return "\n".join(_text(value) for value in fields if value is not None)


def _action_outcome(source_type: str, payload: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    if source_type == "commit":
        return "COMMIT_CREATED", {
            "state": "SUCCEEDED",
            "summary": _text(payload.get("message")) or "Git commit observed.",
            "consequence_ref": None,
        }

    if source_type in {"workflow_run", "check_run"}:
        conclusion = _text(payload.get("conclusion")).lower()
        state = "UNKNOWN"
        if conclusion == "success":
            state = "SUCCEEDED"
        elif conclusion in {"failure", "timed_out", "cancelled", "action_required"}:
            state = "FAILED"
        elif conclusion:
            state = "OBSERVED"
        name = _text(payload.get("name")) or source_type
        return "WORKFLOW_COMPLETED", {
            "state": state,
            "summary": f"{name} concluded {conclusion or 'unknown'}.",
            "consequence_ref": None,
        }

    if source_type == "pr_comment":
        return "COMMENT_CREATED", {
            "state": "OBSERVED",
            "summary": "Pull-request comment observed.",
            "consequence_ref": None,
        }

    if source_type == "pull_request":
        merged = bool(payload.get("merged"))
        state = _text(payload.get("state")).lower()
        if merged:
            summary = "Pull request merged."
            outcome_state = "SUCCEEDED"
        elif state == "closed":
            summary = "Pull request closed without merge."
            outcome_state = "OBSERVED"
        else:
            summary = f"Pull request state observed: {state or 'unknown'}."
            outcome_state = "OBSERVED"
        return "PULL_REQUEST_STATE_CHANGED", {
            "state": outcome_state,
            "summary": summary,
            "consequence_ref": None,
        }

    if source_type == "ref_error":
        return "REF_UPDATE_ATTEMPT", {
            "state": "REFUSED",
            "summary": _text(payload.get("message")) or "Git ref update refused.",
            "consequence_ref": None,
        }

    raise AdapterError(f"unsupported source_type: {source_type}")


def _execution_custodian(source_type: str, payload: Dict[str, Any], login: str | None) -> str:
    if source_type == "ref_error":
        return "GitHub ref API"
    if source_type in {"workflow_run", "check_run"}:
        return login or "github-actions[bot]"
    return login or "UNKNOWN"


def adapt_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(bundle, dict):
        raise AdapterError("evidence bundle must be an object")

    source_type = _text(bundle.get("source_type"))
    repository = _text(bundle.get("repository"))
    if not source_type or not repository:
        raise AdapterError("source_type and repository are required")

    payload = _source_payload(bundle)
    obj = _object_for(source_type, payload)
    login = _login(payload) or _text(bundle.get("carrier_account")) or None
    origin = positive_origin(login, _evidence_text(source_type, payload))
    action, outcome = _action_outcome(source_type, payload)

    event_id = _text(bundle.get("event_id"))
    if not event_id:
        ref = obj.get("immutable_ref") or "no-ref"
        event_id = f"github:{source_type}:{obj['id']}:{ref}"

    authority = bundle.get("authority_evidence")
    if authority is None:
        authority = {"state": "UNKNOWN", "scope": None, "refs": []}
    if not isinstance(authority, dict):
        raise AdapterError("authority_evidence must be an object when supplied")

    boundary = bundle.get("boundary")
    if boundary is None:
        boundary = {"state": "UNKNOWN", "mechanism": None, "evidence_refs": []}
    if not isinstance(boundary, dict):
        raise AdapterError("boundary must be an object when supplied")

    decision = _text(bundle.get("decision_custodian")) or "UNKNOWN"
    info = _unique(bundle.get("information_custodians") or ["UNKNOWN"])

    refs = _unique(bundle.get("evidence_refs") or [])
    if obj.get("url"):
        refs.append(str(obj["url"]))
    refs = _unique(refs)
    if not refs:
        refs = [f"github-object:{obj['type']}:{obj['id']}"]

    return {
        "event_id": event_id,
        "observed_at": _observed_at(source_type, payload),
        "repository": repository,
        "object": obj,
        "action": action,
        "outcome": outcome,
        "carrier_account": login,
        "actor_origin": origin,
        "authority_evidence": {
            "state": _text(authority.get("state")) or "UNKNOWN",
            "scope": authority.get("scope"),
            "refs": _unique(authority.get("refs") or []),
        },
        "boundary": {
            "state": _text(boundary.get("state")) or "UNKNOWN",
            "mechanism": boundary.get("mechanism"),
            "evidence_refs": _unique(boundary.get("evidence_refs") or []),
        },
        "custody": {
            "execution": _execution_custodian(source_type, payload, login),
            "decision": decision,
            "information": info,
        },
        "evidence_refs": refs,
        "uncertainty": _unique(bundle.get("uncertainty") or []),
        "authority_effect": "NONE",
    }


def load_bundles(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise AdapterError("input must be a JSON array")
    return data


def render(observations: List[Dict[str, Any]]) -> str:
    return json.dumps(observations, indent=2, sort_keys=True) + "\n"


def smoke_test() -> int:
    commit = adapt_bundle({
        "source_type": "commit",
        "repository": "owner/repo",
        "payload": {
            "sha": "a" * 40,
            "html_url": "https://github.com/owner/repo/commit/" + "a" * 40,
            "message": "change\n\nhumanaios-origin: ai-agent; agent=ChatGPT; purpose=test",
            "sender": {"login": "shared-account"},
            "committed_at": "2026-10-01T00:00:00Z",
        },
    })
    assert commit["actor_origin"]["origin_class"] == "KNOWN_AI"
    assert commit["actor_origin"]["agent"] == "ChatGPT"
    assert commit["custody"]["decision"] == "UNKNOWN"
    assert commit["authority_evidence"]["state"] == "UNKNOWN"
    assert commit["authority_effect"] == "NONE"

    bot = positive_origin("github-actions[bot]", "")
    assert bot["origin_class"] == "KNOWN_BOT"

    unknown = positive_origin("humanaios-ui", "")
    assert unknown["origin_class"] == "SHARED_ACCOUNT_ORIGIN_UNKNOWN"

    print("smoke-test OK — GitHub evidence adaptation abstains on unsupported authority/custody.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        return smoke_test()
    if args.input is None:
        parser.error("--input is required unless --smoke-test is used")

    observations = [adapt_bundle(bundle) for bundle in load_bundles(args.input)]
    text = render(observations)
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
