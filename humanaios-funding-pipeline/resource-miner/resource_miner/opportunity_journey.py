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
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def project_preparation(payload: object) -> dict:
    """Validate declared versions/checks, without reading files or attesting claims."""
    if not isinstance(payload, dict) or set(payload) != {
        "required_files", "required_checks", "files", "checks",
    }:
        raise ValueError("Unexpected preparation fields")

    def items(key, limit):
        value = payload[key]
        if not isinstance(value, list) or len(value) > limit:
            raise ValueError("Invalid preparation " + key)
        return value

    required_files = [_token(x, "required file") for x in items("required_files", 16)]
    if len(set(required_files)) != len(required_files):
        raise ValueError("Duplicate required file")
    required_checks = {}
    for requirement in items("required_checks", 16):
        if not isinstance(requirement, dict) or set(requirement) != {"check_id", "file_ids"}:
            raise ValueError("Unexpected check requirement")
        check_id = _token(requirement["check_id"], "required check")
        ids = requirement["file_ids"]
        if (not isinstance(ids, list) or not 1 <= len(ids) <= 16
                or any(not isinstance(x, str) or x not in required_files for x in ids)
                or len(set(ids)) != len(ids) or check_id in required_checks):
            raise ValueError("Invalid check file requirements")
        required_checks[check_id] = sorted(ids)

    versions = {}
    current = {}
    for file in items("files", 32):
        if not isinstance(file, dict) or set(file) != {"file_id", "version", "sha256", "role"}:
            raise ValueError("Unexpected/private file fields")
        file_id = _token(file["file_id"], "file ID")
        version, digest, role = file["version"], file["sha256"], file["role"]
        if (type(version) is not int or not 1 <= version <= 1000000
                or not isinstance(digest, str) or not SHA256.fullmatch(digest)
                or role not in ("INPUT", "METADATA", "OUTPUT", "ARTIFACT", "INSTRUCTIONS")):
            raise ValueError("Invalid file version")
        key = (file_id, version)
        if key in versions or (file_id in current and current[file_id]["role"] != role):
            raise ValueError("Conflicting/duplicate file version or role")
        versions[key] = dict(file)
        if file_id not in current or current[file_id]["version"] < version:
            current[file_id] = dict(file)

    checks = {}
    for check in items("checks", 16):
        if not isinstance(check, dict) or set(check) != {
            "check_id", "status", "evidence_ref", "observed_at", "files",
        }:
            raise ValueError("Unexpected/private preparation check fields")
        check_id = _token(check["check_id"], "check ID")
        if check_id not in required_checks or check_id in checks:
            raise ValueError("Undeclared/duplicate preparation check")
        status = check["status"]
        if status not in ("PASS", "FAIL", "UNKNOWN"):
            raise ValueError("Unknown preparation check status")
        refs = check["files"]
        if not isinstance(refs, list) or not 1 <= len(refs) <= 16:
            raise ValueError("Invalid checked file versions")
        checked = {}
        for ref in refs:
            if not isinstance(ref, dict) or set(ref) != {"file_id", "version", "sha256"}:
                raise ValueError("Unexpected checked file fields")
            fid = _token(ref["file_id"], "checked file ID")
            ver = ref["version"]
            if type(ver) is not int or not isinstance(ref["sha256"], str):
                raise ValueError("Invalid checked file version")
            known = versions.get((fid, ver))
            if fid in checked or not known or known["sha256"] != ref["sha256"]:
                raise ValueError("Unknown/conflicting checked file version")
            checked[fid] = ref
        if sorted(checked) != required_checks[check_id]:
            raise ValueError("Check must cover its exact required file set")
        stale = any(current[fid]["version"] != ref["version"]
                    for fid, ref in checked.items())
        checks[check_id] = {
            "check_id": check_id, "reported_status": status,
            "standing": "STALE" if stale else status,
            "evidence_ref": _token(check["evidence_ref"], "opaque check evidence reference"),
            "observed_at": _timestamp(check["observed_at"]),
            "files": [dict(checked[fid]) for fid in sorted(checked)],
        }

    missing_files = sorted(set(required_files) - set(current))
    check_results = [checks.get(cid, {
        "check_id": cid, "reported_status": "UNVERIFIED", "standing": "MISSING",
    }) for cid in sorted(required_checks)]
    covered = {fid for ids in required_checks.values() for fid in ids}
    unchecked_files = sorted(set(required_files) - covered)
    ready = (bool(required_files) and bool(required_checks) and not missing_files
             and not unchecked_files and all(c["standing"] == "PASS" for c in check_results))
    return {
        "standing": "READY_FOR_HUMAN_REVIEW" if ready else "NEEDS_PREPARATION",
        "verification": "USER_SUPPLIED_METADATA_AND_CHECK_REPORTS_NOT_INDEPENDENTLY_VERIFIED",
        "required_files": sorted(required_files),
        "missing_files": missing_files, "files_without_required_checks": unchecked_files,
        "file_versions": [versions[k] for k in sorted(versions)],
        "current_files": [current[k] for k in sorted(current)], "checks": check_results,
        "can_record": False, "can_submit": False, "authority_effect": "NONE",
    }


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
    if not isinstance(payload, dict) or set(payload) not in (
        {"schema", "opportunity", "events"},
        {"schema", "opportunity", "events", "preparation"},
    ):
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
    if "preparation" in payload:
        result["preparation"] = project_preparation(payload["preparation"])
        result["next_action_codes"].insert(0, (
            "REVIEW_PREPARATION_PACKAGE" if result["preparation"]["standing"] == "READY_FOR_HUMAN_REVIEW"
            else "COMPLETE_PREPARATION_CHECKS"
        ))
    # Raw evidence/source contents are excluded. Preparation uses opaque IDs and hashes only.
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
