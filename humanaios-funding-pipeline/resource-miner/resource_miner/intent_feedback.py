"""Human-governed INTENT-OS candidate feedback: offline review of an explicit export.

Feedback is a human report, not independently verified eligibility, funding,
application, participation or acquisition. No persistence, network or writes.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "humanaios.intent_os_feedback.v0.1"
STATUSES = frozenset({
    "SETUP_INCOMPLETE", "INTERESTED", "ALREADY_IN_USE",
    "NOT_RELEVANT", "VERIFY_LATER",
})
ROUTES = {
    "SETUP_INCOMPLETE": "COMPLETE_EXISTING_SETUP",
    "INTERESTED": "VERIFY_DETAILS_AND_DEADLINE",
    "ALREADY_IN_USE": "RECONCILE_EXISTING_RESOURCE",
    "NOT_RELEVANT": "HUMAN_NEGATIVE_MATCH",
    "VERIFY_LATER": "EVIDENCE_REQUIRED",
}
MAX_ENTRIES = 50


def public_link(link: object) -> str:
    """Validate a user-supplied reference; no dereference, DNS or redirect."""
    if not isinstance(link, str) or len(link) > 1000:
        raise ValueError("Invalid public link")
    try:
        url = urlsplit(link)
        host = (url.hostname or "").lower().rstrip(".")
        if url.scheme != "https" or url.username or url.password or url.port not in (None, 443):
            raise ValueError("Not a public HTTPS link")
        if "." not in host or host.startswith("0x") or host.endswith((
            ".local", ".internal", ".localhost", ".test", ".invalid", ".lan",
            ".nip.io", ".sslip.io", ".localtest.me", ".lvh.me",
        )):
            raise ValueError("Not a public HTTPS host")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError("An IP is not a public source reference")
        if not host or host == "localhost":
            raise ValueError("Local URL")
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid public link") from exc
    return link


def project_feedback(payload: dict) -> dict:
    """An untrusted browser-local export; preserve human choice, never promote it."""
    if not isinstance(payload, dict) or set(payload) != {"schema", "entries"} or payload["schema"] != SCHEMA:
        raise ValueError("Unexpected feedback schema")
    entries = payload["entries"]
    if not isinstance(entries, list) or len(entries) > MAX_ENTRIES:
        raise ValueError("Feedback must contain at most 50 records")
    decisions = {}
    for item in entries:
        if not isinstance(item, dict) or set(item) != {
            "resource_id", "source_url", "title", "status", "related_url",
        }:
            raise ValueError("Unexpected or private feedback field")
        identifier, title, status = item["resource_id"], item["title"], item["status"]
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 100:
            raise ValueError("Invalid candidate identifier")
        if not isinstance(title, str) or not 1 <= len(title) <= 180:
            raise ValueError("Invalid candidate title")
        if status not in STATUSES:
            raise ValueError("Unknown or authorizing feedback status")
        src = public_link(item["source_url"])
        related = item["related_url"]
        if related is not None:
            related = public_link(related)
        key = (identifier, src)
        if key in decisions:
            raise ValueError("Duplicate candidate feedback")
        decisions[key] = {
            "resource_id": identifier,
            "source_url": src,
            "title": title,
            "user_reported_status": status,
            "related_source_url": related,
            "next_review": ROUTES[status],
            "provenance": "UNVERIFIED_FIRST_PARTY_HUMAN_REPORT",
            "eligibility": "NOT_ASSESSED",
            "ownership_verified": False,
            "registration_verified": False,
            "publication_authorized": False,
            "authority_effect": "NONE",
        }
    ordered = sorted(decisions.values(), key=lambda x: (x["source_url"], x["resource_id"]))
    result = {
        "schema": "humanaios.intent_os_feedback_projection.v0.1",
        "records": ordered,
        "count": len(ordered),
        "statuses": {k: sum(1 for x in ordered if x["user_reported_status"] == k)
                     for k in sorted(STATUSES)},
        "can_auto_publish_seo": False,
        "can_auto_apply_or_enroll": False,
        "can_auto_retrain_ranker": False,
        "authority_effect": "NONE",
        "receipt_kind": "UNSIGNED_LOCAL_FEEDBACK_EXPORT_NOT_AN_ATTESTATION",
    }
    result["digest_sha256"] = hashlib.sha256(json.dumps(
        result, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Project an exported local feedback JSON safely")
    parser.add_argument("--input", required=True, type=Path, help="Local file; never upload private notes")
    options = parser.parse_args()
    data = json.loads(options.input.read_text(encoding="utf-8"))
    print(json.dumps(project_feedback(data), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
