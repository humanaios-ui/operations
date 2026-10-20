"""Thin, read-only INTENT-OS objective projection over existing Resource Miner candidates.

Candidate text is untrusted data, not instructions or authorization.
This module makes no network requests, does not assess eligibility and has no writes.
"""
from __future__ import annotations

from datetime import date
import hashlib
import ipaddress
import json
import re
from urllib.parse import urlsplit

from .source_risk import promotional_claim_flags
from .query_quality import (
    blocked_resource_types, fuse_rankings, has_exact_anchors, query_terms,
)

MAX_OBJECTIVE = 500
MAX_ROWS = 500
PUBLIC_SOURCES = {"HumanAIOS Funding Pipeline", "DEV Community"}


def _words(value: str) -> set[str]:
    return query_terms(value)


def _public_https(value: object) -> str | None:
    if not isinstance(value, str) or len(value) > 2000:
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return None
        host = parsed.hostname.lower().rstrip(".")
        # Reject literal IP targets, including public IPs (official source links
        # should be hostnames). No DNS fetch is performed by this projection.
        try:
            ipaddress.ip_address(host)
            return None
        except ValueError:
            pass
        if (
            "." not in host
            or host == "localhost"
            or host.endswith((
                ".localhost", ".local", ".internal", ".lan", ".home",
                ".test", ".invalid", ".nip.io", ".sslip.io",
                ".localtest.me", ".lvh.me",
            ))
            or re.fullmatch(r"[0-9.]+", host)
            or host.startswith("0x")
            or parsed.port not in (None, 443)
        ):
            return None
    except ValueError:
        return None
    return value


def _is_expired(row: dict) -> bool:
    if row.get("route") == "ARCHIVE" or row.get("status") == "CLOSED_OR_STALE":
        return True
    deadline = row.get("deadline")
    if isinstance(deadline, str):
        try:
            return date.fromisoformat(deadline) < date.today()
        except ValueError:
            return False
    return False


def evaluate_objective(objective: str, rows: list[dict], *, source_mode: str,
                       source_status: str, source_warning: str = "") -> dict:
    """Rank candidate discovery observations against a human objective.

    There is no eligibility determination, ranking authorization, or application.
    Results are not a live confirmation that a program remains open.
    """
    if not isinstance(objective, str) or not 3 <= len(objective.strip()) <= MAX_OBJECTIVE:
        raise ValueError("Describe what you need in 3 to 500 characters.")
    if source_mode not in {"live", "snapshot"}:
        raise ValueError("source_mode must be live or snapshot.")
    if not isinstance(rows, list):
        raise ValueError("Candidate data is unavailable.")
    objective = " ".join(objective.split())
    wanted = _words(objective)
    if not wanted:
        raise ValueError("Please add a specific goal, such as grants, training, or compute credits.")

    matches = []
    omitted = 0
    unexamined_count = max(0, len(rows) - MAX_ROWS)
    for row in rows[:MAX_ROWS]:
        if not isinstance(row, dict) or row.get("source_name") not in PUBLIC_SOURCES:
            omitted += 1
            continue
        url = _public_https(row.get("primary_source_url") or row.get("canonical_url") or row.get("source_url"))
        if not url or _is_expired(row):
            omitted += 1
            continue
        title = str(row.get("title") or "")[:180]
        desc = str(row.get("description") or "")[:550]
        tags = row.get("tags") if isinstance(row.get("tags"), list) else []
        types = row.get("resource_types") if isinstance(row.get("resource_types"), list) else []
        affordances = row.get("resource_affordances") if isinstance(row.get("resource_affordances"), list) else []
        needs = row.get("need_matches") if isinstance(row.get("need_matches"), list) else []
        terms = " ".join(str(v)[:80] for v in [*tags[:30], *types[:15], *affordances[:15]])
        labels = " ".join(
            str(n.get("label") or "")[:80] for n in needs[:10] if isinstance(n, dict)
        )
        # Only explicit negative mechanism constraints filter candidate types.
        if blocked_resource_types(objective) & {
            str(value).casefold() for value in types[:15]
        }:
            omitted += 1
            continue
        # Never approximate a structured ID from loose semantic tokens.
        if not has_exact_anchors(objective, " ".join((title, desc, terms, labels))):
            continue
        title_hits = wanted & _words(title)
        taxonomy_hits = wanted & _words(" ".join((terms, labels)))
        other_hits = wanted & _words(" ".join((desc, terms, labels)))
        hits = title_hits | other_hits
        if not hits:
            continue
        score = 3 * len(title_hits) + len(other_hits)
        matches.append({
            "resource_id": str(row.get("resource_id") or "")[:100],
            "title": title,
            "description": desc[:280],
            "review_flags": promotional_claim_flags(" ".join((title, desc))),
            "review_flags_kind": "TEXT_PATTERN_MATCH_NOT_FRAUD_DETERMINATION",
            "source_name": row["source_name"],
            "source_url": url,
            "observed_at": str(row.get("discovered_at") or "")[:50],
            "last_verified_at": str(row.get("last_verified_at") or "")[:50] or None,
            "deadline": row.get("deadline") if isinstance(row.get("deadline"), str) else None,
            "route": row.get("route") if row.get("route") in {"VERIFY_NOW", "WATCH"} else "WATCH",
            "matched_terms": sorted(hits),
            "relevance_score": score,
            "_taxonomy_hit_count": len(taxonomy_hits),
            "eligibility_assessed": False,
            "action": "Review official source and verify current rules before pursuing.",
        })
    matches = fuse_rankings(matches)
    shown = matches[:10]
    receipt_input = json.dumps({
        "objective": objective, "mode": source_mode, "status": source_status,
        "candidates": shown, "unexamined_count": unexamined_count,
    }, sort_keys=True, separators=(",", ":"))
    return {
        "objective": objective,
        "status": ("PARTIAL_CANDIDATES_FOR_HUMAN_REVIEW" if shown else "PARTIAL_SEARCH_NO_MATCH") if unexamined_count else ("CANDIDATES_FOR_HUMAN_REVIEW" if shown else "NO_SUPPORTED_MATCH"),
        "source_mode": source_mode,
        "source_status": source_status,
        "source_warning": (source_warning + (" Search incomplete: " + str(unexamined_count) + " source row(s) were not examined." if unexamined_count else "")).strip(),
        "candidates": shown,
        "matched_count": len(matches),
        "shown_count": len(shown),
        "excluded_count": omitted,
        "unexamined_count": unexamined_count,
        "eligibility": "NOT_ASSESSED",
        "verification": "Discovery only. Links, deadlines, applicant eligibility and availability must be checked with the official source.",
        "authority": "NONE",
        "execution": "DISABLED",
        "receipt_sha256": hashlib.sha256(receipt_input.encode("utf-8")).hexdigest(),
        "receipt_kind": "UNSIGNED_INPUT_AND_SELECTION_DIGEST_NOT_AN_ATTESTATION",
        "ranking_strategy": "LEXICAL_PLUS_DECLARED_TAXONOMY_RRF_K60_V1",
        "retrieval_scope": "COLLECTED_PUBLIC_CANDIDATES_ONLY_NOT_OPEN_WEB_SEARCH",
        "language_support": "BOUNDED_ENGLISH_SPANISH_TERMS_NOT_GENERAL_TRANSLATION",
        "source_diversity": {
            "visible_sources": len({row["source_name"] for row in shown}),
            "visible_source_urls": len({row["source_url"] for row in shown}),
        },
    }
