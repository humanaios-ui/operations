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
        results.append({
            "report_id": identifier,
            "resource_title": title,
            "source_url": source_url,
            "reported_status": state,
            "observed_at_user_claim": stamp,
            "next_action": STATES[state],
            "replacement_url_user_claim": replacement or None,
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
    output = {
        "schema": "humanaios.resource_source_review_projection.v0.1",
        "count": len(results),
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
