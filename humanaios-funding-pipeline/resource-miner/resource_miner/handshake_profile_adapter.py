"""Read-only Handshake profile comparison against the exact-path private master.

Dependency: private_profile_bridge from draft PR #1029. One caller-supplied,
owner-observed profile snapshot. No browser automation, credentials, network
access, writes, application action, or cross-platform account-ownership claim.

Return values are PRIVATE review material. Never post a real result to GitHub.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

from .private_profile_bridge import load_private_master, project_personal
from .profile_presence import canonical_profile_url

SCHEMA = "humanaios.handshake-profile-observation.v0.1"
OUTPUT_SCHEMA = "humanaios.private-handshake-profile-diff.v0.1"
_PROFILE_PATH = re.compile(r"^/profiles/[a-z0-9]{4,24}/?$")


def _bounded(value: Any, name: str, limit: int = 300) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"invalid {name}")
    if any(ord(c) < 32 for c in value):
        raise ValueError(f"control character in {name}")
    return value.strip()


def _snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(snapshot, dict) or set(snapshot) != {
        "schema", "source_url", "observed_at", "fields",
    } or snapshot["schema"] != SCHEMA:
        raise ValueError("unsupported Handshake snapshot contract")
    url = _bounded(snapshot["source_url"], "source_url", 300)
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != "app.joinhandshake.com"
            or parsed.username or parsed.password or parsed.port
            or parsed.query or parsed.fragment
            or not _PROFILE_PATH.fullmatch(parsed.path)):
        raise ValueError("snapshot must be an exact Handshake profile URL")
    stamp = _bounded(snapshot["observed_at"], "observed_at", 40)
    try:
        parsed_stamp = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if parsed_stamp.tzinfo is None:
            raise ValueError("observation timestamp needs a time zone")
    except ValueError as exc:
        raise ValueError("invalid observed_at timestamp") from exc
    fields = snapshot["fields"]
    if not isinstance(fields, dict) or set(fields) != {
        "summary", "skills", "work_experience", "education", "projects", "links",
    }:
        raise ValueError("unknown or missing observed profile fields")
    if fields["summary"] is not None:
        if not isinstance(fields["summary"], str) or len(fields["summary"]) > 600:
            raise ValueError("invalid observed summary")
    for name, max_items in (
        ("skills", 50), ("work_experience", 40), ("education", 30),
        ("projects", 40),
    ):
        rows = fields[name]
        if rows is not None and (not isinstance(rows, list) or len(rows) > max_items):
            raise ValueError(f"invalid {name} collection")
    if fields["skills"] is not None:
        for s in fields["skills"]:
            _bounded(s, "observed skill", 100)
    for name, keys in (
        ("work_experience", {"role", "organization"}),
        ("education", {"degree", "school"}),
    ):
        if fields[name] is None:
            continue
        for row in fields[name]:
            if not isinstance(row, dict) or set(row) != keys:
                raise ValueError(f"invalid {name} entry")
            for key in keys:
                _bounded(row[key], key, 180)
    if fields["projects"] is not None:
        for p in fields["projects"]:
            u = urlsplit(_bounded(p, "project URL", 350))
            if (u.scheme != "https" or u.hostname != "app.joinhandshake.com"
                    or u.query or u.fragment or not re.fullmatch(
                        r"/ai-showcase/projects/[0-9]+/?", u.path)):
                raise ValueError("not an exact Handshake Showcase project")
        if len(set(fields["projects"])) != len(fields["projects"]):
            raise ValueError("duplicate Showcase project links")
    links = fields["links"]
    if links is not None:
        if not isinstance(links, dict) or not set(links).issubset({"linkedin", "github"}):
            raise ValueError("unsupported profile-link keys")
        for provider, candidate in links.items():
            if candidate is not None:
                canonical_profile_url(provider, candidate)
    return snapshot


def _work_key(row: dict) -> tuple[str, str]:
    return (row["role"].casefold().strip(), row["organization"].casefold().strip())


def _education_key(row: dict) -> tuple[str, str]:
    return (row["degree"].casefold().strip(), row["school"].casefold().strip())


def compare_handshake_profile(
    master: dict[str, Any], master_revision: str, snapshot: dict[str, Any],
    *, owner_approved: bool = False,
) -> dict[str, Any]:
    """Private proposed field diff; never executes or authorizes external edits."""
    if not owner_approved:
        raise PermissionError("explicit owner consent required for profile comparison")
    observed = _snapshot(snapshot)
    projection = project_personal(master, master_revision, owner_approved=True)
    fields = observed["fields"]
    proposals: list[dict[str, Any]] = []
    conflicts: list[str] = []

    summary = (master.get("summary") or {}).get("professional_brief")
    if fields["summary"] == "" and isinstance(summary, str) and summary.strip():
        proposals.append({
            "field": "summary",
            "action": "DRAFT_FROM_PRIVATE_MASTER",
            "source_ref": "master.summary.professional_brief",
            "candidate": summary.strip() if len(summary.strip()) <= 300 else None,
            "max_chars": 300,
            "needs_shortening": len(summary.strip()) > 300,
            "review": "HUMAN_REVIEW_REQUIRED",
        })
    elif fields["summary"] and isinstance(summary, str) and fields["summary"].strip() != summary.strip():
        conflicts.append("SUMMARY_DIFF_REVIEW_NO_OVERWRITE")

    if fields["skills"] is not None:
        existing = {value.strip().casefold() for value in fields["skills"]}
        competencies = master.get("competencies") or {}
        # Only source-backed skill phrases, not inferred job requirements.
        pool = []
        for k in ("data_quality", "operations", "ai_research"):
            items = competencies.get(k) or []
            if isinstance(items, list):
                pool.extend(items)
        for name in pool[:30]:
            if isinstance(name, str) and 0 < len(name) <= 80 and name.casefold() not in existing:
                proposals.append({
                    "field": "skill", "action": "CONSIDER_ADD",
                    "candidate": name, "source_ref": "master.competencies",
                    "review": "HUMAN_REVIEW_REQUIRED",
                })
                existing.add(name.casefold())
            if len([p for p in proposals if p["field"] == "skill"]) >= 10:
                break

    if fields["work_experience"] is not None:
        existing_work = {_work_key(row) for row in fields["work_experience"]}
        for i, row in enumerate((master.get("experience") or [])[:30]):
            if not isinstance(row, dict):
                continue
            role, org = row.get("role"), row.get("organization")
            if not isinstance(role, str) or not isinstance(org, str):
                continue
            if (role.casefold().strip(), org.casefold().strip()) in existing_work:
                continue
            proposals.append({
                "field": "work_experience", "action": "CONSIDER_ADD",
                "candidate": {
                    "role": role, "organization": org,
                    "start_date": row.get("start_date"),
                    "end_date": row.get("end_date"),
                },
                "source_ref": f"master.experience[{i}]",
                "review": "HUMAN_REVIEW_REQUIRED",
            })

    if fields["education"] is not None:
        existing_education = {_education_key(row) for row in fields["education"]}
        for i, row in enumerate((master.get("education") or [])[:15]):
            if not isinstance(row, dict) or not isinstance(row.get("degree"), str) or not isinstance(row.get("school"), str):
                continue
            if _education_key(row) in existing_education:
                continue
            proposals.append({
                "field": "education", "action": "CONSIDER_ADD",
                "candidate": {
                    "degree": row["degree"], "school": row["school"],
                    "status": row.get("status") or "NOT_SPECIFIED",
                    "year_completed": row.get("year_completed"),
                    "year_expected": row.get("year_expected"),
                },
                "source_ref": f"master.education[{i}]",
                "review": "HUMAN_REVIEW_REQUIRED",
            })

    link_results: list[dict[str, str]] = []
    social = (master.get("contact") or {}).get("social") or {}
    for provider in ("github", "linkedin"):
        observed_url = (fields["links"] or {}).get(provider) if fields["links"] is not None else None
        master_url = social.get(provider)
        master_canonical = None
        if isinstance(master_url, str):
            try:
                master_canonical = canonical_profile_url(provider, master_url)
            except ValueError:
                conflicts.append("MASTER_SOCIAL_LINK_NEEDS_REVIEW:" + provider)
        if observed_url is None:
            state = "UNOBSERVED_OR_NOT_LINKED"
        elif master_canonical and canonical_profile_url(provider, observed_url) == master_canonical:
            state = "LINK_MATCH_NOT_OWNERSHIP_PROOF"
        else:
            state = "LINK_CONFLICT_REVIEW_REQUIRED"
            conflicts.append("LINK_CONFLICT:" + provider)
        link_results.append({"provider": provider, "state": state})

    canonical_json = json.dumps(observed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "schema": OUTPUT_SCHEMA,
        "private": True,
        "read_mode": "OWNER_SUPPLIED_SNAPSHOT_AND_PINNED_MASTER_REVISION",
        "handshake_observed_at": observed["observed_at"],
        "master_revision": master_revision,
        "snapshot_sha256": hashlib.sha256(canonical_json.encode("utf-8")).hexdigest(),
        "capability_codes": projection["capability_codes"],
        "observed_showcase_count": None if fields["projects"] is None else len(fields["projects"]),
        "link_results": link_results,
        "proposals": proposals,
        "conflicts": sorted(set(conflicts)),
        "application_submission": "NOT_INFERRED",
        "profile_write": "DISABLED",
        "eligibility_assessed": False,
        "authority_effect": "NONE",
        "next_action": "PRIVATE_HUMAN_FIELD_REVIEW",
    }


def review_handshake_profile(
    private_checkout: str, snapshot: dict[str, Any],
    *, owner_approved: bool = False, operations_checkout: str | None = None,
) -> dict[str, Any]:
    """Actual PR #1029 exact-path git bridge and optional PER-grounded review."""
    if not owner_approved:
        raise PermissionError("explicit owner consent required")
    master, revision = load_private_master(private_checkout)
    result = compare_handshake_profile(master, revision, snapshot, owner_approved=True)
    if operations_checkout is None:
        result["profile_objective"] = "LEGACY_UNRANKED_REVIEW"
        result["per_evidence_scope"] = "NOT_REQUESTED"
        return result
    from .handshake_profile_objective import (
        enrich_profile_proposals, load_project_evidence,
    )
    pers, per_revision = load_project_evidence(operations_checkout)
    return enrich_profile_proposals(
        result, master, pers, per_revision, _snapshot(snapshot)["fields"],
    )
