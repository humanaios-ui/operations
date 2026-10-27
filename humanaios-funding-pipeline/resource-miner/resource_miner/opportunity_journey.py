"""Read-only evidence-bounded opportunity journey for INTENT-OS.

Projection only: no credentials, networking, storage, submissions or authority.
Input is an untrusted event summary, not cryptographically verified evidence.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

SCHEMA = "humanaios.opportunity_journey.e0.v1"
EVENT_SOURCE = {
    "DISCOVERED": "RESOURCE_MINER_OBSERVATION",
    "HUMAN_SELECTED": "HUMAN_REPORT",
    "SIGNUP_WELCOME_EMAIL_OBSERVED": "GMAIL_CONNECTOR_OBSERVATION",
    "SURVEY_SUBMITTED_HUMAN": "HUMAN_REPORT",
    "CALENDAR_EVENT_CREATED": "CALENDAR_CONNECTOR_RECEIPT",
    "DISCORD_JOINED_HUMAN": "HUMAN_REPORT",
}
MAX_EVENTS = 64
TOKEN = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")


def _token(value: object, label: str) -> str:
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise ValueError("Invalid " + label)
    return value


def _timestamp(value: object) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("Expected a UTC observation timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("Invalid UTC observation timestamp") from exc
    if parsed.utcoffset().total_seconds() != 0:
        raise ValueError("Non-UTC observation timestamp")
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def project_journey(payload: dict) -> dict:
    """Reduce an explicitly bounded set of receipt *claims*, not raw evidence.

    Authentication of the person/provider and durable storage are separate
    future connector-broker concerns. This reducer cannot grant authority.
    """
    if not isinstance(payload, dict) or set(payload) != {"schema", "opportunity", "events"}:
        raise ValueError("Unexpected journey envelope")
    if payload["schema"] != SCHEMA:
        raise ValueError("Unsupported journey version")
    opportunity = payload["opportunity"]
    if not isinstance(opportunity, dict) or set(opportunity) != {"id", "parent_resource_id"}:
        raise ValueError("Unexpected opportunity fields")
    opportunity_id = _token(opportunity["id"], "opportunity")
    parent = _token(opportunity["parent_resource_id"], "parent resource")
    if parent == opportunity_id:
        raise ValueError("An event and its parent resource must be distinct")
    events = payload["events"]
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise ValueError("Too many journey observations")

    unique = {}
    for event in events:
        if not isinstance(event, dict) or set(event) != {
            "event_id", "kind", "source_kind", "evidence_ref", "observed_at",
        }:
            raise ValueError("Unexpected/private event field")
        event_id = _token(event["event_id"], "event ID")
        kind = event["kind"]
        source_kind = event["source_kind"]
        if not isinstance(kind, str) or kind not in EVENT_SOURCE:
            raise ValueError("Unknown event kind: no implicit outcome promotion")
        if source_kind != EVENT_SOURCE[kind]:
            raise ValueError("Untrusted source cannot assert that event kind")
        record = {
            "event_id": event_id,
            "kind": kind,
            "source_kind": source_kind,
            "evidence_ref": _token(event["evidence_ref"], "opaque evidence reference"),
            "observed_at": _timestamp(event["observed_at"]),
        }
        if event_id in unique:
            if unique[event_id] != record:
                raise ValueError("Conflicting reuse of one event ID")
        else:
            unique[event_id] = record

    ordered = sorted(unique.values(), key=lambda e: (e["observed_at"], e["event_id"]))
    kinds = {event["kind"] for event in ordered}
    observed = {kind: kind in kinds for kind in EVENT_SOURCE}
    signup = observed["SIGNUP_WELCOME_EMAIL_OBSERVED"]
    survey = observed["SURVEY_SUBMITTED_HUMAN"]
    selected = observed["HUMAN_SELECTED"]
    calendar = observed["CALENDAR_EVENT_CREATED"]
    discord = observed["DISCORD_JOINED_HUMAN"]
    warnings = []
    if signup and not selected:
        warnings.append("SIGNUP_RECEIPT_WITHOUT_EXPLICIT_SELECTED_INTENT")
    if survey and not signup:
        warnings.append("SURVEY_REPORT_WITHOUT_SIGNUP_RECEIPT")
    if calendar and not selected:
        warnings.append("CALENDAR_RECEIPT_WITHOUT_EXPLICIT_SELECTED_INTENT")

    pending = []
    if not selected:
        pending.append("REVIEW_AND_SELECT_OPPORTUNITY")
    elif not signup:
        pending.append("REVIEW_SIGNUP_OR_APPLICATION")
    else:
        if not survey:
            pending.append("COMPLETE_REQUIRED_SURVEY")
        else:
            pending.append("VERIFY_PARTICIPANT_STANDING_WITH_PROVIDER")
        if not calendar:
            pending.append("REVIEW_CALENDAR_SCHEDULE")
        pending.append("REVIEW_EVENT_UPDATES_AND_RESEARCH_DELIVERABLE")

    result = {
        "schema": "humanaios.opportunity_journey.projection.e0.v1",
        "opportunity_id": opportunity_id,
        "parent_resource_id": parent,
        "event_count": len(ordered),
        "observations": observed,
        "signup_standing": "WELCOME_EMAIL_OBSERVED" if signup else "UNVERIFIED",
        "survey_standing": "SUBMITTED_HUMAN_REPORTED" if survey else "UNVERIFIED",
        "calendar_standing": "CREATED_CONNECTOR_REPORTED" if calendar else "UNVERIFIED",
        "discord_standing": "JOINED_HUMAN_REPORTED" if discord else "UNVERIFIED",
        "participant_standing": "NOT_CONFIRMED_BY_PROVIDER",
        "attendance": "UNVERIFIED",
        "research_submission": "UNVERIFIED",
        "prize_or_funding_outcome": "UNVERIFIED",
        "human_action_cycle": (
            "USER_ACTION_PROGRESS_REPORTED_NOT_PROVIDER_QUALIFIED"
            if signup and survey and calendar else "INCOMPLETE"
        ),
        "next_action_codes": pending,
        "warnings": warnings,
        "can_send_mail": False,
        "can_write_calendar": False,
        "can_read_discord": False,
        "can_submit_application": False,
        "can_authorize_repository_change": False,
        "authority_effect": "NONE",
        "receipt_kind": "UNSIGNED_LOCAL_PROJECTION_NOT_INDEPENDENT_ATTESTATION",
    }
    # Source IDs are intentionally excluded; only the count and stable digest are exported.
    result["digest_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Project a local sanitized opportunity journey")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(project_journey(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
