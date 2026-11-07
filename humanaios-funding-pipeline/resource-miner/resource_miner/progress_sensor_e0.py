"""Z1/E0 read-only opportunity progress signal projector.

Takes *sanitized, declarative* source and event summaries, optionally including
an existing Opportunity Journey projection. No Gmail, GitHub, credential, file,
clock, scheduler or network access. The caller is responsible for authenticating
source provenance; this module does NOT validate source identity or dispatch.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from zoneinfo import ZoneInfo

SCHEMA = "humanaios.progress_sensor.e0.v1"
PROJECTION_SCHEMA = "humanaios.progress_sensor.projection.e0.v1"
JOURNEY_SCHEMA = "humanaios.opportunity_journey.projection.e0.v1"
TOKEN = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
OFFICIAL_PREFIX = "https://"
SOURCE_FIELDS = {"opportunity_id", "canonical_url", "checked_at", "deadline_at", "source_revision"}
SIGNAL_FIELDS = {"observation_id", "opportunity_id", "kind", "source_kind", "observed_at", "evidence_ref"}
SIGNAL_SOURCES = {
    "INTERNAL_WORK_LINKED": "GITHUB_OBSERVATION",
    "CODE_TEST_REPORTED": "GITHUB_OBSERVATION",
    "PDF_READY_HUMAN_REPORTED": "HUMAN_REPORT",
    "HUMAN_REVIEW_REPORTED": "HUMAN_REPORT",
    "HUMAN_SUBMISSION_REPORTED": "HUMAN_REPORT",
    "PROVIDER_RECEIPT_OBSERVED": "GMAIL_CONNECTOR_OBSERVATION",
    "BLOCKER_OBSERVED": "GITHUB_OBSERVATION",
    "BLOCKER_HUMAN_REPORTED": "HUMAN_REPORT",
}
FOLLOWUPS = {
    "DEADLINE_NEAR_WITH_UNKNOWN_READINESS": "REVIEW_REPORT_AND_PROVIDER_SUBMISSION_STATE",
    "DEADLINE_PASSED_WITH_UNKNOWN_OUTCOME": "CHECK_PROVIDER_FOR_SUBMISSION_OUTCOME",
    "REVIEW_REPORTED_PROVIDER_RECEIPT": "INDEPENDENTLY_VERIFY_PROVIDER_RECEIPT",
    "SOURCE_STALE_RECHECK": "RECHECK_FIRST_PARTY_DEADLINE",
    "SOURCE_CONFLICT_HOLD": "RECONCILE_CONFLICTING_FIRST_PARTY_OBSERVATIONS",
    "BLOCKER_OBSERVED": "INSPECT_BLOCKER_AND_PROPOSE_NEXT_SAFE_STEP",
    "SOURCE_UNAVAILABLE_HOLD": "RETRIEVE_CURRENT_FIRST_PARTY_SOURCE",
}


def _exact(item: object, fields: set[str], label: str) -> dict:
    if not isinstance(item, dict) or set(item) != fields:
        raise ValueError("Invalid or private fields in " + label)
    return item


def _token(value: object, label: str) -> str:
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise ValueError("Invalid " + label)
    return value


def _utc(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("Expected UTC timestamp with Z")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as err:
        raise ValueError("Invalid UTC timestamp") from err
    if result.utcoffset().total_seconds() != 0:
        raise ValueError("Not UTC")
    return result


def _deadline(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Invalid deadline")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as err:
        raise ValueError("Invalid ISO deadline") from err
    if result.utcoffset() is None or result.utcoffset().total_seconds() % 60:
        raise ValueError("Deadline needs explicit timezone offset")
    return result.astimezone(timezone.utc)


def _public_url(value: object) -> str:
    if not isinstance(value, str) or not value.startswith(OFFICIAL_PREFIX) or len(value) > 2048:
        raise ValueError("Expected bounded HTTPS source URL")
    if ("@" in value or "?" in value or "#" in value or any(c.isspace() for c in value)
            or len(value.split("/")) < 4):
        raise ValueError("Private or unstable source URL")
    return value.rstrip("/")


def _stable_sha(obj: object) -> str:
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def evaluate_progress(payload: dict) -> dict:
    """Return a deterministic Z1-candidate projection, NEVER a runnable task."""
    if not isinstance(payload, dict) or set(payload) not in (
        {"schema", "opportunity_id", "canonical_url", "as_of", "source_observations", "signals", "prior_dedupe_keys"},
        {"schema", "opportunity_id", "canonical_url", "as_of", "source_observations", "signals", "prior_dedupe_keys", "journey_projection"},
    ) or payload["schema"] != SCHEMA:
        raise ValueError("Unexpected progress-sensor envelope")
    oid = _token(payload["opportunity_id"], "opportunity ID")
    url = _public_url(payload["canonical_url"])
    as_of = _utc(payload["as_of"])
    prior = payload["prior_dedupe_keys"]
    if (not isinstance(prior, list) or len(prior) > 256
            or any(not isinstance(x, str) or not HEX64.fullmatch(x) for x in prior)):
        raise ValueError("Invalid prior trigger keys")

    if "journey_projection" in payload:
        journey = payload["journey_projection"]
        if (not isinstance(journey, dict) or journey.get("schema") != JOURNEY_SCHEMA
                or journey.get("opportunity_id") != oid or journey.get("authority_effect") != "NONE"
                or journey.get("research_submission") != "UNVERIFIED"):
            raise ValueError("Mismatched or privileged Opportunity Journey projection")

    sources = payload["source_observations"]
    if not isinstance(sources, list) or len(sources) > 16:
        raise ValueError("Invalid source observations")
    parsed_sources = {}
    by_revision = {}
    for row in sources:
        row = _exact(row, SOURCE_FIELDS, "source observation")
        if _token(row["opportunity_id"], "source opportunity ID") != oid:
            raise ValueError("Wrong-opportunity source")
        if _public_url(row["canonical_url"]) != url:
            raise ValueError("Wrong canonical source")
        checked = _utc(row["checked_at"])
        if checked > as_of:
            raise ValueError("Future source observation")
        due = _deadline(row["deadline_at"])
        revision = _token(row["source_revision"], "source revision")
        if revision in by_revision and by_revision[revision] != due:
            # Same declared revision asserting two different deadlines is conflicting evidence.
            parsed_sources.setdefault(checked, set()).add((due, revision))
            parsed_sources[checked].add((by_revision[revision], revision))
        by_revision[revision] = due
        parsed_sources.setdefault(checked, set()).add((due, revision))

    conflict = False
    latest_checked = max(parsed_sources) if parsed_sources else None
    if latest_checked is not None and len({due for due, _ in parsed_sources[latest_checked]}) > 1:
        conflict = True
    # Conflicting reuse of a declared revision is also fail-closed, even across timestamps.
    revisions = {}
    for observations in parsed_sources.values():
        for due, rev in observations:
            revisions.setdefault(rev, set()).add(due)
    conflict = conflict or any(len(x) > 1 for x in revisions.values())
    latest = None
    if latest_checked is not None and not conflict:
        latest = sorted(parsed_sources[latest_checked], key=lambda x: x[1])[-1]

    signals = payload["signals"]
    if not isinstance(signals, list) or len(signals) > 64:
        raise ValueError("Invalid signal observations")
    unique = {}
    for item in signals:
        item = _exact(item, SIGNAL_FIELDS, "signal")
        if _token(item["opportunity_id"], "signal opportunity ID") != oid:
            raise ValueError("Wrong-sprint evidence is not admissible")
        kind = item["kind"]
        if kind not in SIGNAL_SOURCES or item["source_kind"] != SIGNAL_SOURCES[kind]:
            raise ValueError("Unsupported actor or evidence-kind impersonation")
        sid = _token(item["observation_id"], "observation ID")
        _token(item["evidence_ref"], "opaque evidence reference")
        if _utc(item["observed_at"]) > as_of:
            raise ValueError("Future signal observation")
        if sid in unique and unique[sid] != item:
            raise ValueError("Conflicting evidence ID")
        unique[sid] = item
    kinds = {row["kind"] for row in unique.values()}
    provider_seen = "PROVIDER_RECEIPT_OBSERVED" in kinds
    human_submit = "HUMAN_SUBMISSION_REPORTED" in kinds
    if provider_seen:
        standing = "PROVIDER_RECEIPT_OBSERVED_UNAUTHENTICATED"
    elif human_submit:
        standing = "HUMAN_SUBMISSION_REPORTED_NOT_PROVIDER_VERIFIED"
    else:
        standing = "SUBMISSION_NOT_VERIFIED"

    current_due = latest[0] if latest else None
    source_revision = latest[1] if latest else "NONE"
    status = "SOURCE_UNAVAILABLE" if latest_checked is None else "SOURCE_CONFLICT" if conflict else "SOURCE_OBSERVED_UNATTESTED"
    stale = bool(latest_checked and (as_of - latest_checked).total_seconds() > 72 * 3600)
    deadline_state = "UNKNOWN"
    if current_due is not None:
        seconds = (current_due - as_of).total_seconds()
        deadline_state = "PASSED" if seconds < 0 else "NEAR" if seconds <= 48 * 3600 else "OPEN"

    triggers = []
    def trigger(kind: str, extra_revision: str = "") -> None:
        fingerprint = _stable_sha([oid, url, kind, source_revision, extra_revision])
        triggers.append({
            "type": kind,
            "dedupe_key": fingerprint,
            "emission_state": "SUPPRESSED_REPLAY" if fingerprint in prior else "NEW_CANDIDATE",
            "next_action": FOLLOWUPS[kind],
            "authority_effect": "NONE",
            "activation_state": "NOT_ENABLED",
        })

    if latest_checked is None:
        trigger("SOURCE_UNAVAILABLE_HOLD")
    elif conflict:
        trigger("SOURCE_CONFLICT_HOLD")
    else:
        if stale:
            trigger("SOURCE_STALE_RECHECK")
        if deadline_state == "PASSED" and not provider_seen:
            trigger("DEADLINE_PASSED_WITH_UNKNOWN_OUTCOME")
        elif deadline_state == "NEAR" and not provider_seen:
            trigger("DEADLINE_NEAR_WITH_UNKNOWN_READINESS")
        elif deadline_state in ("NEAR", "PASSED") and provider_seen:
            trigger("REVIEW_REPORTED_PROVIDER_RECEIPT")
    if "BLOCKER_OBSERVED" in kinds or "BLOCKER_HUMAN_REPORTED" in kinds:
        blocker_ids = sorted(x["observation_id"] for x in unique.values() if x["kind"] in ("BLOCKER_OBSERVED", "BLOCKER_HUMAN_REPORTED"))
        trigger("BLOCKER_OBSERVED", _stable_sha(blocker_ids))

    return {
        "schema": PROJECTION_SCHEMA,
        "opportunity_id": oid,
        "canonical_url": url,
        "as_of": as_of.isoformat().replace("+00:00", "Z"),
        "source_standing": status,
        "source_checked_at": latest_checked.isoformat().replace("+00:00", "Z") if latest_checked else None,
        "source_age_stale": stale,
        "deadline_utc": current_due.isoformat().replace("+00:00", "Z") if current_due else None,
        "deadline_local_central": current_due.astimezone(ZoneInfo("America/Chicago")).isoformat() if current_due else None,
        "deadline_state": deadline_state,
        "internal_work_observed": "INTERNAL_WORK_LINKED" in kinds,
        "code_test_claim_observed": "CODE_TEST_REPORTED" in kinds,
        "report_pdf_ready_human_reported": "PDF_READY_HUMAN_REPORTED" in kinds,
        "human_review_human_reported": "HUMAN_REVIEW_REPORTED" in kinds,
        "submission_standing": standing,
        "provider_identity_verified_by_sensor": False,
        "trigger_candidates": triggers,
        "activation_state": "NOT_ENABLED",
        "can_dispatch": False,
        "can_submit": False,
        "can_change_permissions": False,
        "authority_effect": "NONE",
        "verification": "SANITIZED_DECLARED_OBSERVATIONS_ONLY_NOT_INDEPENDENT_SOURCE_ATTESTATION",
    }


def main(argv: list[str] | None = None) -> None:
    """CLI: take sanitized local snapshot only; emit an inert JSON projection."""
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description="Read-only INTENT-OS progress sensor E0")
    parser.add_argument("--input", type=Path, required=True,
                        help="Sanitized local JSON snapshot, never raw email")
    args = parser.parse_args(argv)
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(evaluate_progress(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
