#!/usr/bin/env python3
"""Minimal deterministic event-envelope helpers for the Workspace Evidence Bus.

No network access. No authority transitions. The module validates the public-safe
cross-plane envelope and computes canonical payload hashes.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Mapping

REQUIRED = {
    "event_id", "event_type", "subject_ref", "actor_ref", "source_system",
    "source_ref", "observed_at", "idempotency_key", "state_version",
    "previous_event_hash", "payload_hash", "privacy_class", "authority_effect",
}
SOURCE_SYSTEMS = {"GMAIL", "DRIVE", "APPS_SCRIPT", "GITHUB", "OTHER"}
PRIVACY_CLASSES = {"PRIVATE", "PUBLIC_SAFE"}
AUTHORITY_EFFECTS = {"NONE", "Z1", "Z2_REQUIRED", "Z3_REQUIRED"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _is_datetime(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_event(event: Mapping[str, Any], *, verify_payload_hash: bool = True) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED - set(event))
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
        return errors

    if not isinstance(event["event_id"], str) or not event["event_id"].startswith("EVT-"):
        errors.append("event_id must start with EVT-")
    if event["source_system"] not in SOURCE_SYSTEMS:
        errors.append("invalid source_system")
    if event["privacy_class"] not in PRIVACY_CLASSES:
        errors.append("invalid privacy_class")
    if event["authority_effect"] not in AUTHORITY_EFFECTS:
        errors.append("invalid authority_effect")
    if not isinstance(event["state_version"], int) or event["state_version"] < 0:
        errors.append("state_version must be a non-negative integer")
    if not _is_datetime(event["observed_at"]):
        errors.append("observed_at must be ISO-8601")
    if event.get("valid_at") is not None and not _is_datetime(event.get("valid_at")):
        errors.append("valid_at must be null or ISO-8601")
    if event["previous_event_hash"] is not None and not _is_sha256(event["previous_event_hash"]):
        errors.append("previous_event_hash must be null or lowercase SHA-256")
    if not _is_sha256(event["payload_hash"]):
        errors.append("payload_hash must be lowercase SHA-256")
    elif verify_payload_hash and "payload" in event:
        observed = sha256_json(event["payload"])
        if observed != event["payload_hash"]:
            errors.append(f"payload_hash mismatch: expected {observed}")

    for i, ref in enumerate(event.get("artifact_refs", [])):
        if not isinstance(ref, dict):
            errors.append(f"artifact_refs[{i}] must be an object")
            continue
        for key in ("store", "opaque_id", "sha256"):
            if key not in ref:
                errors.append(f"artifact_refs[{i}] missing {key}")
        if "sha256" in ref and not _is_sha256(ref["sha256"]):
            errors.append(f"artifact_refs[{i}].sha256 invalid")

    return errors


def build_event(*, event_id: str, event_type: str, subject_ref: str, actor_ref: str,
                source_system: str, source_ref: str, observed_at: str,
                idempotency_key: str, state_version: int, payload: dict[str, Any],
                previous_event_hash: str | None = None,
                privacy_class: str = "PUBLIC_SAFE",
                authority_effect: str = "NONE",
                valid_at: str | None = None,
                artifact_refs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "event_type": event_type,
        "subject_ref": subject_ref,
        "actor_ref": actor_ref,
        "source_system": source_system,
        "source_ref": source_ref,
        "observed_at": observed_at,
        "valid_at": valid_at,
        "idempotency_key": idempotency_key,
        "state_version": state_version,
        "previous_event_hash": previous_event_hash,
        "payload_hash": sha256_json(payload),
        "privacy_class": privacy_class,
        "authority_effect": authority_effect,
        "artifact_refs": artifact_refs or [],
        "payload": payload,
    }
