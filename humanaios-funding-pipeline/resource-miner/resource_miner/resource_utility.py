"""Read-only public resource → HumanAIOS need → project workstream graph.

Derived from the existing seven need IDs and approved public resource names.
No private notes, source URLs with opaque IDs, authenticated resource claims,
repository writes, or autonomous acquisition. A proposed route is NOT delivery.
"""
from __future__ import annotations

from typing import Any

# Keys are public source/name words, not the operator's personal account facts.
# Each target maps to an existing resource need and a HUMANAIOS workstream.
_RULES: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("cerebras", "groq", "mistral", "google ai studio", "cloud", "aws activate",
      "oracle always free"), "compute-infrastructure", "ACAT evaluation and Witness inference"),
    (("langfuse", "phoenix", "arize"), "compute-infrastructure", "HumanAIOS calibration and observability"),
    (("supabase",), "compute-infrastructure", "INTENT-OS governed evidence and session graphs"),
    (("kaggle",), "external-validation", "ACAT repeatable external experimentation"),
    (("apart research", "govai", "research fellowship"), "research-collaboration",
      "ACAT research collaboration"),
    (("github sponsors",), "revenue-capital", "HumanAIOS mission funding"),
    (("sbir", "sttr", "bluedot", "emergent ventures", "manifund", "mozilla",
      "grant", "venture"), "revenue-capital", "HumanAIOS research funding and recovery mission"),
    (("sba 8(a)", "mbda", "business center"), "contracts-procurement",
      "HumanAIOS commerce and procurement"),
)
CONFIRMED_NEEDS = frozenset({
    "external-validation", "compute-infrastructure", "revenue-capital",
    "visibility-dissemination", "contracts-procurement",
    "research-collaboration", "training-credentials",
})


def project_resource_utility(latest_reports: list[dict[str, Any]],
                             needs: list[dict[str, Any]]) -> dict[str, Any]:
    """Map the latest *sanitized* source reports, never execute an action."""
    if not isinstance(latest_reports, list) or len(latest_reports) > 100:
        raise ValueError("Invalid bounded source review input")
    available = {str(row.get("need_id")) for row in needs if isinstance(row, dict)}
    if not available.issubset(CONFIRMED_NEEDS):
        raise ValueError("Unexpected need graph identities")
    edges = []
    for row in latest_reports:
        if not isinstance(row, dict):
            raise ValueError("Malformed source review")
        title = row.get("resource_title")
        url = row.get("source_url")
        state = row.get("reported_status")
        if not isinstance(title, str) or not 1 <= len(title) <= 180 or not isinstance(url, str):
            raise ValueError("Invalid resource node")
        if not url.startswith("https://") or "?" in url or "#" in url or "@" in url:
            raise ValueError("Unredacted resource URL in graph")
        name = title.lower()
        for phrases, need_id, workstream in _RULES:
            if need_id not in available or not any(phrase in name for phrase in phrases):
                continue
            flags = row.get("review_flags") or []
            if not isinstance(flags, list):
                raise ValueError("Invalid source-review flags")
            held = ("SOURCE_STATUS_NOTE_CONFLICT_RECHECK_REQUIRED" in flags or
                    state in ("LINK_FAILED_404", "PAGE_UNAVAILABLE_OTHER", "POSSIBLY_CLOSED"))
            edges.append({
                "resource_title": title,
                "source_url": url,
                "observed_status": state,
                "need_id": need_id,
                "workstream": workstream,
                "edge_type": "POSSIBLE_CAPABILITY_MATCH_UNVERIFIED",
                "next_gate": ("INDEPENDENT_SOURCE_RECHECK" if held else
                              "HUMAN_VERIFY_CONTROL_AND_CAPABILITY"),
                "resource_control": "NOT_ESTABLISHED",
                "deployment_state": "NOT_ESTABLISHED",
                "authority_effect": "NONE",
            })
            break
    return {
        "schema": "humanaios.resource_utility_graph.v0.1",
        "nodes_from": "USER_REPORTED_LOCAL_SOURCE_REVIEW",
        "edges": edges,
        "edge_count": len(edges),
        "delivery_executed": False,
        "private_identity_included": False,
        "resource_ownership_established": False,
        "recovery_outcome_established": False,
        "authority_effect": "NONE",
        "note": ("Proposal only; resource access, integration, spending, "
                 "deployment and recovery outcomes need separate human-granted "
                 "authority and independent receipts."),
    }
