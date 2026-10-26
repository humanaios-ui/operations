"""Bounded offline review of user-reported external source observations.

A screenshot digest or user-reported HTTP status is NOT an independent
reachability test. This utility makes no network calls, no updates to source
catalogs or ranking, and never issues application/eligibility decisions.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

SCHEMA = "humanaios.resource_source_review.v0.1"
STATES = {
    "LINK_FAILED_404": "RECHECK_SOURCE_URL_AND_OFFICIAL_BOARD",
    "PAGE_UNAVAILABLE_OTHER": "RECHECK_SOURCE_AVAILABILITY",
    "SOURCE_WORKING": "INDEPENDENT_REACHABILITY_CHECK",
    "REPLACEMENT_FOUND": "VERIFY_REPLACEMENT_AGAINST_OFFICIAL_SOURCE",
    "POSSIBLY_CLOSED": "VERIFY_CURRENT_EMPLOYER_STATUS",
    "ALREADY_IN_USE": "RECONCILE_CONTROLLED_RESOURCE",
    "OTHER": "REVIEW_HUMAN_OBSERVATION",
}
MAX_RECORDS = 100

# Conservative, deterministic risk flags: only explicit job-listing absence
# should request a source hold. Submission rules and setup failures are
# constraints, NOT evidence of a missing public source.
_JOB_NOT_LISTED = re.compile(
    r"\\b(?:job|role|listing|position)\\b.{0,72}\\b(?:not found|not listed|unavailable|removed)\\b"
    r"|\\bnot (?:on|listed on) (?:the )?(?:official )?(?:website|job board)\\b",
    re.IGNORECASE,
)
_USE_POLICY = re.compile(
    r"\\b(?:restrict(?:s|ed|ions)?|reject(?:s|ed)?|prohibit(?:s|ed)?|"
    r"no longer accepts)\\b.{0,85}\\b(?:ai|automated|written|application)\\b"
    r"|\\b(?:ai-written|ai generated|ai-generated)\\b.{0,85}\\b(?:reject|restrict|prohibit)",
    re.IGNORECASE,
)
_SETUP_ISSUE = re.compile(r"\\b(?:could not|unable to|failed to)\\b.{0,55}\\b(?:set up|connect|configure|integrat)", re.IGNORECASE)
_OPAQUE_SEGMENT = re.compile(
    r"^(?:org_|prj_|project_|session_|user_|token_|cm[a-z0-9]{15,}|[A-Za-z0-9_-]{38,}|eyJ[A-Za-z0-9_.-]+)$",
    re.IGNORECASE,
)


def review_flags(state: str, note: str) -> list[str]:
    """Do not equate link reachability, provider policy and operational setup."""
    flags = []
    if state == "SOURCE_WORKING" and (
        _JOB_NOT_LISTED.search(note) or "STATUS_NOTE_CONFLICT_RECHECK_REQUIRED" in note
    ):
        flags.append("SOURCE_STATUS_NOTE_CONFLICT_RECHECK_REQUIRED")
    if _USE_POLICY.search(note):
        flags.append("SUBMISSION_OR_AI_POLICY_RESTRICTION_UNVERIFIED")
    if _SETUP_ISSUE.search(note):
        flags.append("RESOURCE_SETUP_DIFFICULTY_USER_REPORTED")
    return flags


def redacted_public_url(raw: object) -> str | None:
    """Export only safe public URL structure; never a session query or opaque ID."""
    if not raw:
        return None
    _public_https(raw)
    p = urlsplit(raw)
    path = []
    for segment in p.path.split("/"):
        if segment and (_OPAQUE_SEGMENT.fullmatch(segment) or len(segment) > 70):
            break
        path.append(segment)
    from urllib.parse import urlunsplit
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), "/".join(path), "", ""))


def public_review_packet(packet: dict) -> dict:
    """Sanitized v0.1 packet for intentional export; never exports raw notes.

    Originals remain only in the private browser store. Flags are constrained
    synthetic evidence labels, not copied personal notes or provider findings.
    """
    if not isinstance(packet, dict) or packet.get("schema") != SCHEMA or not isinstance(packet.get("records"), list):
        raise ValueError("Invalid review packet")
    result = []
    for row in packet["records"]:
        if not isinstance(row, dict) or not isinstance(row.get("evidence"), dict):
            raise ValueError("Invalid report")
        note = row["evidence"].get("note", "")
        if not isinstance(note, str):
            raise ValueError("Invalid note")
        flags = review_flags(str(row.get("status") or ""), note)
        result.append({
            "id": row["id"], "resource_title": row["resource_title"],
            "source_url": redacted_public_url(row["source_url"]),
            "status": row["status"], "observed_at": row["observed_at"],
            "evidence": {"note": " ".join(flags), "replacement_url":
                         redacted_public_url(row["evidence"].get("replacement_url")) or "",
                         "screenshot": None},
        })
    return {"schema": SCHEMA, "records": result}



def _public_https(raw: object) -> str:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 1600:
        raise ValueError("Invalid source URL")
    try:
        p = urlsplit(raw)
        host = (p.hostname or "").rstrip(".").lower()
        if p.scheme != "https" or p.username or p.password or p.port not in (None, 443):
            raise ValueError("Invalid source URL")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError("IP references are unsupported")
        if "." not in host or host.endswith((".local", ".localhost", ".internal",
            ".lan", ".test", ".invalid", ".nip.io", ".sslip.io")):
            raise ValueError("Not a public hostname")
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid public HTTPS reference") from exc
    return raw


def project_source_reviews(payload: dict) -> dict:
    """Convert local observations into review tasks without claiming verification."""
    if not isinstance(payload, dict) or set(payload) != {"schema", "records"} or payload["schema"] != SCHEMA:
        raise ValueError("Unexpected review schema")
    records = payload["records"]
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise ValueError("Bad review record count")
    results = []
    ids = set()
    for item in records:
        if not isinstance(item, dict) or set(item) != {
            "id", "resource_title", "source_url", "status", "evidence", "observed_at",
        }:
            raise ValueError("Unexpected review record fields")
        identifier = item["id"]
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", identifier):
            raise ValueError("Invalid report identifier")
        if identifier in ids:
            raise ValueError("Duplicate report ID")
        ids.add(identifier)
        title = item["resource_title"]
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 180:
            raise ValueError("Invalid resource title")
        source_url = _public_https(item["source_url"])
        state = item["status"]
        if not isinstance(state, str) or state not in STATES:
            raise ValueError("Unknown review state")
        evidence = item["evidence"]
        if not isinstance(evidence, dict) or set(evidence) != {"note", "replacement_url", "screenshot"}:
            raise ValueError("Unexpected private evidence")
        if not isinstance(evidence["note"], str) or len(evidence["note"]) > 500:
            raise ValueError("Invalid note length")
        replacement = evidence["replacement_url"]
        if not isinstance(replacement, str):
            raise ValueError("Invalid replacement link")
        if replacement:
            replacement = _public_https(replacement)
        shot = evidence["screenshot"]
        if shot is not None:
            if not isinstance(shot, dict) or set(shot) != {"mime", "size_bytes", "sha256"}:
                raise ValueError("Invalid evidence file fingerprint")
            if not isinstance(shot["mime"], str) or not re.fullmatch(r"[a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+", shot["mime"]):
                raise ValueError("Invalid evidence file type")
            if not isinstance(shot["size_bytes"], int) or isinstance(shot["size_bytes"], bool) or not 1 <= shot["size_bytes"] <= 10485760:
                raise ValueError("Invalid evidence file size")
            if not isinstance(shot["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", shot["sha256"]):
                raise ValueError("Invalid evidence file digest")
        stamp = item["observed_at"]
        if not isinstance(stamp, str) or not stamp.endswith("Z"):
            raise ValueError("Invalid observation time")
        try:
            parsed = datetime.fromisoformat(stamp[:-1] + "+00:00")
        except ValueError as exc:
            raise ValueError("Invalid observation time") from exc
        if parsed.utcoffset().total_seconds() != 0:
            raise ValueError("Non-UTC time")
        flags = review_flags(state, evidence["note"])
        results.append({
            "report_id": identifier,
            "resource_title": title,
            "source_url": redacted_public_url(source_url),
            "reported_status": state,
            "review_flags": flags,
            "source_hold_recommended": "SOURCE_STATUS_NOTE_CONFLICT_RECHECK_REQUIRED" in flags,
            "review_gate": ("RECHECK_REQUIRED" if "SOURCE_STATUS_NOTE_CONFLICT_RECHECK_REQUIRED" in flags
                            else "HUMAN_REVIEW_ONLY"),
            "observed_at_user_claim": stamp,
            "next_action": STATES[state],
            "replacement_url_user_claim": (redacted_public_url(replacement)
                if redacted_public_url(replacement) != redacted_public_url(source_url) else None),
            "attachment_digest_present": shot is not None,
            "attachment_contents_saved": False,
            "screenshot_digest_present": shot is not None,
            "screenshot_bytes_verified": False,
            "source_availability_verified": False,
            "opportunity_closed_verified": False,
            "claim_provenance": "UNVERIFIED_HUMAN_SOURCE_OBSERVATION",
            "authority_effect": "NONE",
        })
    results.sort(key=lambda x: (x["source_url"], x["observed_at_user_claim"], x["report_id"]))
    # Preserve immutable report history, but present only latest by canonical
    # redacted source URL to human operators. Sorting by timestamp avoids
    # import-order artifacts. This makes a VIEW, never deletes observations.
    latest = {}
    for r in results:
        key = r["source_url"]
        if key not in latest or (r["observed_at_user_claim"], r["report_id"]) > (
            latest[key]["observed_at_user_claim"], latest[key]["report_id"]
        ):
            latest[key] = r
    output = {
        "schema": "humanaios.resource_source_review_projection.v0.1",
        "count": len(results),
        "latest_count": len(latest),
        "latest_by_source": [latest[k] for k in sorted(latest)],
        "reports": results,
        "source_catalog_modified": False,
        "ranking_modified": False,
        "eligibility_assessed": False,
        "sent_to_provider": False,
        "authority_effect": "NONE",
        "receipt_kind": "UNSIGNED_OFFLINE_REVIEW_PROJECTION_NOT_ATTESTATION",
    }
    output["digest_sha256"] = hashlib.sha256(json.dumps(
        output, separators=(",", ":"), sort_keys=True).encode()).hexdigest()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate user-exported source review packets offline")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(project_source_reviews(
        json.loads(args.input.read_text(encoding="utf-8"))), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
