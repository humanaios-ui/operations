"""Versioned, read-only task milestone projection. Independent of legacy E0 journey.
Provider observations are claims until authenticated by a separate ingestion layer.
"""
import hashlib
import json
import re
from datetime import datetime

SCHEMA = "humanaios.opportunity_tasks.e1.v1"
TOKEN = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")
APPROVAL = "IDEA_APPROVED"
HOLD = "HARDWARE_HOLD_REPORTED"
RELEASE = "HARDWARE_VERIFIED"
EVENTS = {APPROVAL, HOLD, RELEASE}
TASK_IDS = {
    "task_ebbb0b082ada4455a86c455a91052150",
    "task_333855bc4e864798b00f46ff77ec5e90",
    "task_6f4550812cf949e6b7cf165fff22d70b",
}

def token(value):
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise ValueError("invalid opaque token")
    return value

def utc(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("UTC timestamp required")
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if d.utcoffset().total_seconds() != 0:
        raise ValueError("non UTC timestamp")
    return d.isoformat(timespec="auto").replace("+00:00", "Z")

def project_task_milestones(payload):
    if not isinstance(payload, dict) or set(payload) != {"schema", "opportunity_id", "events"}:
        raise ValueError("invalid envelope")
    if payload["schema"] != SCHEMA:
        raise ValueError("unsupported schema")
    opportunity = token(payload["opportunity_id"])
    if opportunity != "OPP-MERCOR-ODIN":
        raise ValueError("opportunity does not match the ODIN pilot")
    events = payload["events"]
    if not isinstance(events, list) or len(events) > 64:
        raise ValueError("invalid event count")
    unique = {}
    for e in events:
        if not isinstance(e, dict) or set(e) != {"event_id", "task_id", "kind", "observed_at", "evidence_ref", "source_kind"}:
            raise ValueError("invalid event fields")
        event_id, task_id = token(e["event_id"]), e["task_id"]
        if task_id not in TASK_IDS or e["kind"] not in EVENTS:
            raise ValueError("unknown task or event")
        token(e["evidence_ref"])
        if e["source_kind"] not in {"PROVIDER_UI_OBSERVATION", "HUMAN_REPORT"}:
            raise ValueError("invalid source")
        if e["kind"] == APPROVAL and e["source_kind"] != "PROVIDER_UI_OBSERVATION":
            raise ValueError("human report cannot establish provider approval")
        if e["kind"] == HOLD and e["source_kind"] != "HUMAN_REPORT":
            raise ValueError("hold needs human report")
        if e["kind"] == RELEASE:
            raise ValueError("hardware release requires separate attested gate")
        clean = {**e, "observed_at": utc(e["observed_at"])}
        if event_id in unique and unique[event_id] != clean:
            raise ValueError("conflicting event identity")
        unique[event_id] = clean
    ordered = sorted(unique.values(), key=lambda x: (x["observed_at"], x["event_id"]))
    approved = sorted({e["task_id"] for e in ordered if e["kind"] == APPROVAL})
    held = any(e["kind"] == HOLD for e in ordered)
    out = {
        "schema": "humanaios.opportunity_tasks.projection.e1.v1",
        "opportunity_id": opportunity,
        "approved_task_ids": approved,
        "approved_count": len(approved),
        "hardware_hold_reported": held,
        "state": "BLOCKED_HARDWARE" if held else "PREPARATION_UNVERIFIED",
        "recordings_submitted": "UNVERIFIED",
        "payment": "UNVERIFIED",
        "next_action": "VERIFY_MACOS_15_AND_35GB_THEN_RECORDING_TEST" if held else "CHECK_RECORDING_READINESS",
        "source_assurance": "UNAUTHENTICATED_OBSERVATION_SUMMARY",
        "authority_effect": "NONE",
        "can_record": False,
        "can_submit": False,
        "can_authorize_payment": False,
    }
    out["digest_sha256"] = hashlib.sha256(json.dumps(out, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return out
