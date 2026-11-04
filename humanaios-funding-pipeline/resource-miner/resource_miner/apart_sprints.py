"""Bounded, read-only Apart sprint source and receipt projection.

This is a public source snapshot and an optional sanitized *claim* overlay.
It never reads private mail, stores a personal journey, or grants authority.
"""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from .opportunity_journey import project_journey, SCHEMA as LEGACY_SCHEMA

SCHEMA = "humanaios.apart_sprints.claims.e0.v1"
SNAPSHOT = Path(__file__).resolve().parents[1] / "fixtures" / "apart_sprints_public_20261104.json"
TOKEN = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SOURCES = {
    "DISCOVERED": "RESOURCE_MINER_OBSERVATION",
    "HUMAN_SELECTED": "HUMAN_REPORT",
    "SIGNUP_WELCOME_EMAIL_OBSERVED": "GMAIL_CONNECTOR_OBSERVATION",
    "SURVEY_SUBMITTED_HUMAN": "HUMAN_REPORT",
    "CALENDAR_EVENT_CREATED": "CALENDAR_CONNECTOR_RECEIPT",
    "DISCORD_JOINED_HUMAN": "HUMAN_REPORT",
    "APPLICATION_SUBMITTED_HUMAN": "HUMAN_REPORT",
    "PROJECT_RECEIPT_EMAIL_OBSERVED": "GMAIL_CONNECTOR_OBSERVATION",
    "JUDGING_UPDATE_EMAIL_OBSERVED": "GMAIL_CONNECTOR_OBSERVATION",
    "RESULT_EMAIL_OBSERVED": "GMAIL_CONNECTOR_OBSERVATION",
}
LEGACY_KINDS = set(SOURCES) - {
    "APPLICATION_SUBMITTED_HUMAN", "PROJECT_RECEIPT_EMAIL_OBSERVED",
    "JUDGING_UPDATE_EMAIL_OBSERVED", "RESULT_EMAIL_OBSERVED",
}


def canonical_sprint_url(url: str) -> str:
    """Strict event identity: ignore tracking queries, never merge other hosts."""
    if not isinstance(url, str) or len(url) > 500:
        raise ValueError("Invalid sprint URL")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "apartresearch.com"
            or parsed.username or parsed.password or parsed.port):
        raise ValueError("Untrusted sprint origin")
    parts = parsed.path.rstrip("/").split("/")
    if len(parts) != 3 or parts[1] != "sprints" or not SLUG.fullmatch(parts[2]):
        raise ValueError("Not an Apart sprint event URL")
    return "https://apartresearch.com/sprints/" + parts[2]


def _token(value: object, label: str) -> str:
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise ValueError("Invalid " + label)
    return value


def _utc(value: object) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("Expected UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("Invalid UTC timestamp") from exc
    if parsed.utcoffset().total_seconds() != 0:
        raise ValueError("Expected UTC timestamp")
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def _public_catalog() -> list[dict]:
    payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if set(payload) != {"schema", "checked_on", "sprints"} or payload["schema"] != "humanaios.apart_sprints.public.e0.v1":
        raise ValueError("Invalid public snapshot")
    if not isinstance(payload["sprints"], list) or len(payload["sprints"]) != 5:
        raise ValueError("Unexpected public sprint count")
    seen = set()
    for item in payload["sprints"]:
        if set(item) != {"title", "url", "starts_on", "ends_on", "deadline", "linked_research"}:
            raise ValueError("Unexpected public source field")
        url = canonical_sprint_url(item["url"])
        if url != item["url"] or url in seen:
            raise ValueError("Duplicate or noncanonical source")
        seen.add(url)
        if not isinstance(item["linked_research"], list) or len(item["linked_research"]) > 3:
            raise ValueError("Invalid research references")
    return payload["sprints"]


def project_apart_sprints(claims: dict | None = None) -> dict:
    """Project separate sprint cards; claims are NOT authenticated receipts.

    A cross-sprint event reference, conflicting duplicate, or private field
    causes rejection rather than promotion or a partial merge.
    """
    events_by_url: dict[str, dict[str, dict]] = {}
    seen_ids: dict[str, str] = {}
    known = {item["url"]: item for item in _public_catalog()}
    if claims is not None:
        if not isinstance(claims, dict) or set(claims) != {"schema", "records"} or claims["schema"] != SCHEMA:
            raise ValueError("Unexpected claims envelope")
        records = claims["records"]
        if not isinstance(records, list) or len(records) > 10:
            raise ValueError("Too many sprint records")
        total = 0
        for record in records:
            if not isinstance(record, dict) or set(record) != {"sprint_url", "events"}:
                raise ValueError("Unexpected/private sprint record field")
            url = canonical_sprint_url(record["sprint_url"])
            if url not in known:
                raise ValueError("Sprint not in checked source catalog")
            events = record["events"]
            if not isinstance(events, list):
                raise ValueError("Invalid sprint event list")
            total += len(events)
            if total > 64:
                raise ValueError("Too many sprint events")
            bucket = events_by_url.setdefault(url, {})
            for event in events:
                if not isinstance(event, dict) or set(event) != {
                    "event_id", "sprint_url", "kind", "source_kind", "evidence_ref", "observed_at",
                }:
                    raise ValueError("Unexpected/private event field")
                if canonical_sprint_url(event["sprint_url"]) != url:
                    raise ValueError("Wrong-sprint evidence")
                eid = _token(event["event_id"], "event ID")
                kind = event["kind"]
                if not isinstance(kind, str) or kind not in SOURCES or event["source_kind"] != SOURCES[kind]:
                    raise ValueError("Unsupported claim or evidence source")
                clean = {
                    "event_id": eid, "kind": kind, "source_kind": SOURCES[kind],
                    "evidence_ref": _token(event["evidence_ref"], "opaque evidence reference"),
                    "observed_at": _utc(event["observed_at"]),
                }
                if eid in seen_ids and seen_ids[eid] != url:
                    raise ValueError("Event ID reused across sprints")
                seen_ids[eid] = url
                if eid in bucket and bucket[eid] != clean:
                    raise ValueError("Conflicting duplicate receipt")
                bucket[eid] = clean

    cards = []
    for url, public in known.items():
        observations = sorted(events_by_url.get(url, {}).values(),
                              key=lambda e: (e["observed_at"], e["event_id"]))
        legacy = [e for e in observations if e["kind"] in LEGACY_KINDS]
        slug = url.rsplit("/", 1)[1]
        base = project_journey({
            "schema": LEGACY_SCHEMA,
            "opportunity": {"id": "OPP-APART-" + slug, "parent_resource_id": "RES-APART-SPRINTS"},
            "events": legacy,
        })
        kinds = {e["kind"] for e in observations}
        if "RESULT_EMAIL_OBSERVED" in kinds:
            stage, action = "RESULT_MESSAGE_OBSERVED_NOT_VERIFIED", "REVIEW_PROVIDER_RESULT"
        elif "JUDGING_UPDATE_EMAIL_OBSERVED" in kinds:
            stage, action = "REVIEW_PENDING_PROVIDER_MESSAGE_OBSERVED", "FOLLOW_JUDGING_UPDATE"
        elif "PROJECT_RECEIPT_EMAIL_OBSERVED" in kinds:
            stage, action = "PROJECT_RECEIPT_MESSAGE_OBSERVED", "FOLLOW_JUDGING_UPDATE"
        elif "APPLICATION_SUBMITTED_HUMAN" in kinds:
            stage, action = "APPLIED_HUMAN_REPORTED", "VERIFY_SIGNUP_WITH_PROVIDER"
        elif base["signup_standing"] != "UNVERIFIED":
            stage, action = "WELCOME_EMAIL_OBSERVED", "CHECK_EVENT_PREPARATION"
        elif "HUMAN_SELECTED" in kinds:
            stage, action = "SELECTED_HUMAN_REPORTED", "REVIEW_APPLICATION"
        else:
            stage, action = "DISCOVERED_PUBLIC_SOURCE", "REVIEW_FIT_AND_SOURCE"
        cards.append({
            **public,
            "opportunity_id": base["opportunity_id"],
            "parent_resource_id": base["parent_resource_id"],
            "source_checked_on": "2026-11-04",
            "stage": stage, "next_action_code": action,
            "evidence_summary": [
                {"kind": e["kind"], "source_kind": e["source_kind"],
                 "evidence_ref": e["evidence_ref"], "observed_at": e["observed_at"]}
                for e in observations
            ],
            "legacy_journey": base,
            "participant_qualified": "UNVERIFIED",
            "award": "UNVERIFIED", "benefit_realized": "UNVERIFIED",
            "authority_effect": "NONE",
        })
    return {
        "schema": "humanaios.apart_sprints.projection.e0.v1",
        "mode": "PUBLIC_SNAPSHOT_AND_OPTIONAL_UNAUTHENTICATED_CLAIMS",
        "source_checked_on": "2026-11-04", "cards": cards,
        "legacy_local_case": "UNCHANGED_NOT_IMPORTED",
        "authority_effect": "NONE",
    }
