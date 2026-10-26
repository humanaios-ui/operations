"""Read-only, privacy-scoped projection for the Resource Miner pathway view.

A source observation is not proof of program currentness, a matched need is not
eligibility, and a state receipt is not independently verified acquisition.
The projection reads existing records and never updates them.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

MAX_CANDIDATES = 200


def _text(value: Any, limit: int = 180) -> str:
    return str(value or "")[:limit] if isinstance(value, (str, int, float)) else ""


def _ref_ids(items: Any, key: str) -> list[str]:
    if not isinstance(items, list):
        return []
    return list(dict.fromkeys(
        _text(item.get(key), 100)
        for item in items[:25]
        if isinstance(item, dict) and _text(item.get(key), 100)
    ))


def _receipt_summary(receipt: dict[str, Any]) -> dict[str, str]:
    return {
        "id": _text(receipt.get("receipt_id"), 100),
        "observed_at": _text(receipt.get("observed_at"), 50),
        "type": _text(receipt.get("observation_type"), 60),
        "recorded_status": _text(receipt.get("to_status") or receipt.get("to_resource_state"), 70),
        "authority": "NONE",
    }


def project_pathways(
    mines: list[dict[str, Any]],
    needs: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
    *,
    origin: str,
    source_status: str = "",
    sampled_at: str | None = None,
) -> dict[str, Any]:
    """Build bounded path records from current local files or public adapter output.

    Only explicit candidate.mine_id binds a candidate to a configured Mine.
    Matching its source label to a Mine's name would invent provenance.
    """
    if origin not in {"PERSISTED_RUNTIME", "STORED_SNAPSHOT", "PUBLIC_REFRESH"}:
        raise ValueError("Unknown pathway data origin.")
    if not all(isinstance(x, list) for x in (mines, needs, requirements, rows, receipts)):
        raise ValueError("Pathway inputs must be arrays.")
    observed_ids = set()
    by_resource: dict[str, list[dict[str, str]]] = {}
    for receipt in receipts[:1000]:
        if not isinstance(receipt, dict):
            continue
        rid = _text(receipt.get("resource_id"), 100)
        if rid:
            by_resource.setdefault(rid, []).append(_receipt_summary(receipt))
    mine_ids = {_text(m.get("mine_id"), 100) for m in mines if isinstance(m, dict)}
    paths = []
    evidence_count = 0
    matches = 0
    recorded_acquired = 0
    disposition_count = 0
    max_observed_at = ""
    source_names: Counter[str] = Counter()
    for row in rows:
        if len(paths) >= MAX_CANDIDATES:
            break
        if not isinstance(row, dict):
            continue
        rid = _text(row.get("resource_id"), 100)
        if not rid or rid in observed_ids:
            continue
        observed_ids.add(rid)
        evidence = row.get("evidence")
        evidence_count += min(25, len(evidence)) if isinstance(evidence, list) else 0
        need_ids = _ref_ids(row.get("need_matches"), "need_id")
        requirement_ids = _ref_ids(row.get("requirement_matches"), "requirement_id")
        if need_ids or requirement_ids:
            matches += 1
        receipt_list = by_resource.get(rid, [])
        if any(r["recorded_status"] == "ALREADY_ACQUIRED" for r in receipt_list):
            recorded_acquired += 1
        if any(r["type"] == "USER_DISPOSITION" for r in receipt_list):
            disposition_count += 1
        mine_id = _text(row.get("mine_id"), 100)
        explicit_mine = mine_id if mine_id in mine_ids else ""
        source = _text(row.get("source_name"), 110) or "Unidentified source"
        source_names[source] += 1
        discovered_at = _text(row.get("discovered_at"), 50)
        if discovered_at > max_observed_at:
            max_observed_at = discovered_at
        # No links are returned: a route should never trust arbitrary source
        # URLs as safe merely because they were copied from a JSONL row.
        paths.append({
            "id": rid,
            "title": _text(row.get("title"), 170) or rid,
            "source": source,
            "mine_id": explicit_mine or None,
            "mine_binding": "EXPLICIT" if explicit_mine else "UNBOUND_SOURCE",
            "need_ids": need_ids,
            "requirement_ids": requirement_ids,
            "route": _text(row.get("route"), 35) or "UNKNOWN",
            "discovered_at": discovered_at,
            "evidence_refs": min(25, len(evidence)) if isinstance(evidence, list) else 0,
            "receipts": receipt_list[:15],
            "availability": "NOT_INDEPENDENTLY_VERIFIED",
            "eligibility": "NOT_ASSESSED",
            "authority": "NONE",
        })
    checked = sampled_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schema": "HUMANAIOS_RESOURCE_PATHWAYS_V0_1",
        "sampled_at": checked,
        "origin": origin,
        "source_status": _text(source_status, 120),
        "oldest_possible_warning": "Source dates, eligibility and availability are not independently verified by this view.",
        "observed_at_latest": max_observed_at or None,
        "authority": "NONE",
        "execution": "DISABLED",
        "eligibility": "NOT_ASSESSED",
        "scope": "LOCAL_LOOPBACK_ONLY",
        "refresh_semantics": ("PUBLIC_ADAPTER_READ_ON_REQUEST" if origin == "PUBLIC_REFRESH"
                              else "LOCAL_FILES_REREAD_ON_REQUEST_NO_EXTERNAL_SCAN"),
        "counts": {
            "configured_mines": len(mines),
            "source_groups": len(source_names),
            "candidate_rows": len(rows),
            "candidate_paths": len(paths),
            "unexamined_rows": max(0, len(rows) - len(paths)),
            "linked_evidence_refs": evidence_count,
            "need_records": len(needs),
            "requirement_records": len(requirements),
            "matched_candidates": matches,
            "state_receipts": len(receipts),
            "disposition_receipts_linked": disposition_count,
            "recorded_acquired_not_verified": recorded_acquired,
            "verified_human_outcomes": None,
        },
        "mines": [
            {"id": _text(m.get("mine_id"), 100), "label": _text(m.get("name"), 100),
             "enabled": m.get("enabled") is True}
            for m in mines if isinstance(m, dict)
        ][:50],
        "needs": [
            {"id": _text(n.get("need_id"), 100), "label": _text(n.get("label"), 140)}
            for n in needs if isinstance(n, dict)
        ][:50],
        "requirements": [
            {"id": _text(r.get("requirement_id"), 100), "label": _text(r.get("label"), 140),
             "gap_status": _text(r.get("gap_status"), 35)}
            for r in requirements if isinstance(r, dict)
        ][:50],
        "sources": [{"label": name, "count": count} for name, count in sorted(source_names.items())],
        "paths": paths,
        "boundary_notes": [
            "Configured Mines are not assumed to be the origin of unbound candidate rows.",
            "A recorded acquisition claim is not an independent outcome receipt.",
            "ZERO_MATCHES_OBSERVED is not NO_ENTITLEMENT.",
            "No external action, application or claim is authorized by this view.",
        ],
    }
