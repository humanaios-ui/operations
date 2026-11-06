"""E1: one synthetic-household path through the existing pieces.

Resource Miner handoff -> Entitlement Navigator intake -> shared rules
evaluator -> Opportunity Journey projection -> hash-chained decision history.

Read-only and deterministic: no network, no file writes, no clock reads (the
caller supplies ``as_of`` and ``observed_at``). Nothing here grants authority,
assesses eligibility or records an approval. Existing modules are loaded and
used unchanged; this file only composes them.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any
from urllib.parse import urlsplit

from resource_system.adapters.resource_miner_adapter import load_handoff_module

_miner = load_handoff_module("resource-miner/resource_miner/entitlement_handoff.py")
_navigator = load_handoff_module("entitlement-navigator/entitlement/resource_handoff.py")
_evaluator = load_handoff_module("entitlement-navigator/entitlement/rules_evaluator.py")
_journey = load_handoff_module("resource-miner/resource_miner/opportunity_journey.py")

ENTRY_SCHEMA = "humanaios.e1.decision-entry.v1"
GENESIS = "0" * 64
TOKEN = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")
# Candidate keys that would smuggle a benefit/approval claim into the path.
BENEFIT_KEYS = re.compile(r"(benefit|award|payment|approved|granted|discount_usd|amount|enroll)", re.I)

# Version binding: the E1 path only runs against these exact pack digests.
# Changing a pack changes its digest, so the path refuses until a human re-pins.
PINS = {
    "lifeline": {"pack_name": "us-lifeline-2026",
                 "pinned_digest": "4e03bc7c109be2ebdec4615d10e684e13b2e375bac18446379473eb0f08eec0b"},
    "liheap": {"pack_name": "fl-liheap-ffy2027",
               "pinned_digest": "ecab7ad2a28c5742e3cb175c4b1aea074ff1547a02b27421c6c76a888b553da3"},
}


def default_registry() -> dict[str, dict[str, Any]]:
    """Load and verify the pinned packs. Raises if a pack no longer matches its pin."""
    registry = {}
    for program, pin in PINS.items():
        pack = _evaluator.load_pack(pin["pack_name"], pinned_digest=pin["pinned_digest"])
        registry[program] = {"pack": pack, "pinned_digest": pin["pinned_digest"]}
    return registry


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(obj: Any) -> str:
    return hashlib.sha256(_canon(obj).encode("utf-8")).hexdigest()


def entry_hash(entry: dict[str, Any]) -> str:
    return _sha({k: v for k, v in entry.items() if k != "entry_hash"})


def _host(url: Any) -> str | None:
    host = urlsplit(url).hostname if isinstance(url, str) else None
    return host[4:] if host and host.startswith("www.") else host


def _missing_facts(pack: dict[str, Any], facts: dict[str, Any]) -> list[str]:
    read = {c["fact"] for r in pack["rules"] for c in r.get("all", [])}
    size_fact = (pack.get("income_cap") or {}).get("size_fact")
    if size_fact:
        read.add(size_fact)
    return sorted(f for f in read if facts.get(f) is None)


def verify_ledger(ledger: Any) -> None:
    """Fail closed on any edit, deletion, reordering or forged authority."""
    prior_by_case: dict[tuple[str, str], str] = {}
    prev = GENESIS
    for seq, entry in enumerate(ledger):
        if not isinstance(entry, dict) or entry.get("schema") != ENTRY_SCHEMA:
            raise ValueError("ledger contains a malformed entry")
        if entry.get("seq") != seq or entry.get("prev_hash") != prev:
            raise ValueError("ledger chain broken (entry removed, reordered or inserted)")
        if entry.get("entry_hash") != entry_hash(entry):
            raise ValueError("ledger entry content does not match its hash")
        if (entry.get("authority_effect") != "NONE" or entry.get("eligibility_status") != "UNASSESSED"
                or entry.get("determination") != "ADVISORY_SCREEN_ONLY"):
            raise ValueError("ledger entry carries authority or an eligibility claim")
        key = (entry["program"], entry["case"])
        if entry.get("supersedes") != prior_by_case.get(key):
            raise ValueError("ledger supersedes pointer does not match case history")
        prior_by_case[key] = entry["entry_hash"]
        prev = entry["entry_hash"]


def case_history(ledger: Any, program: str, case: str) -> list[dict[str, Any]]:
    return [e for e in ledger if e["program"] == program and e["case"] == case]


def run_household(program: str, candidate: dict[str, Any], facts: dict[str, Any], *,
                  as_of: str, observed_at: str, ledger: Any = (),
                  human_selected_ref: str | None = None,
                  registry: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Run one synthetic household. Returns the new/unchanged ledger and the entry."""
    verify_ledger(ledger)
    registry = registry if registry is not None else default_registry()
    if program not in registry:
        raise ValueError("unknown program")
    if not isinstance(as_of, str) or not as_of:
        raise ValueError("as_of is required")
    if not isinstance(candidate, dict) or not isinstance(facts, dict):
        raise ValueError("candidate and facts must be objects")
    if candidate.get("authority_effect") not in (None, "NONE"):
        raise ValueError("candidate carries an authority effect")
    if any(BENEFIT_KEYS.search(str(k)) for k in candidate):
        raise ValueError("candidate carries an unsupported benefit claim")
    pack = registry[program]["pack"]
    pinned = registry[program]["pinned_digest"]

    # 1. Resource Miner handoff, then Navigator intake. Defence in depth: this path
    #    checks the authority fields itself, so it does not depend on the intake fix.
    handoff = _miner.build_entitlement_handoff(candidate)
    if handoff.get("authority_effect") != "NONE":
        raise ValueError("handoff carries an authority effect")
    investigation = _navigator.intake_resource_handoff(handoff)
    if (investigation.get("authority_effect") != "NONE"
            or investigation.get("eligibility_status") != "UNASSESSED"):
        raise ValueError("intake returned authority or an eligibility claim")
    handoff_digest = _sha(handoff)
    resource_id = investigation["resource_id"]

    # 2. Source identity: every candidate source must live on a host the pack cites.
    pack_hosts = {_host(s["url"]) for s in pack["sources"]}
    seen = [candidate.get(k) for k in ("primary_source_url", "canonical_url", "source_url") if candidate.get(k)]
    conflict = (not seen) or any(_host(u) not in pack_hosts for u in seen)

    # 3. Rules evaluator (digest-pinned). The decision comes only from here.
    screen = _evaluator.evaluate(pack, facts, as_of=as_of, pinned_digest=pinned)

    # 4. Opportunity Journey projection from receipts this path can honestly claim.
    opp = "OPP-" + hashlib.sha256(f"{resource_id}|{screen['case']}".encode()).hexdigest()[:16]
    events = [{"event_id": "EVT-" + handoff_digest[:16], "kind": "DISCOVERED",
               "source_kind": "RESOURCE_MINER_OBSERVATION",
               "evidence_ref": "HND-" + handoff_digest[:16], "observed_at": observed_at}]
    if human_selected_ref is not None:
        if not isinstance(human_selected_ref, str) or not TOKEN.fullmatch(human_selected_ref):
            raise ValueError("human_selected_ref must be an opaque token")
        events.append({"event_id": "EVT-SEL-" + human_selected_ref, "kind": "HUMAN_SELECTED",
                       "source_kind": "HUMAN_REPORT", "evidence_ref": human_selected_ref,
                       "observed_at": observed_at})
    projection = _journey.project_journey({
        "schema": _journey.SCHEMA,
        "opportunity": {"id": opp, "parent_resource_id": resource_id},
        "events": events})

    clean_facts = {k: v for k, v in facts.items() if k != "case"}
    body = {
        "schema": ENTRY_SCHEMA,
        "program": program,
        "case": screen["case"],
        "input_digest": _sha(clean_facts),
        "observed_at": observed_at,
        "as_of": as_of,
        "source_identity": {
            "resource_id": resource_id,
            "handoff_id": investigation["source_handoff_id"],
            "handoff_digest": handoff_digest,
            "primary_source_url": candidate.get("primary_source_url"),
            "source_name": investigation["provenance"]["source_name"],
        },
        "rule": {
            "pack_id": screen["pack_id"], "rule_version": screen["rule_version"],
            "pack_digest": screen["pack_digest"], "rule_observed_at": screen["rule_observed_at"],
            "effective_through": screen["effective_through"], "rule_id": screen["rule_id"],
            "rule_sources": screen["rule_sources"],
            "rule_source_attribution": screen["rule_source_attribution"],
            "source_authenticity": screen["source_authenticity"],
        },
        "screen": {"state": screen["state"], "income_cap_usd": screen["income_cap_usd"],
                   "next_step": screen["next_step"]},
        "path_status": "SOURCE_CONFLICT_HOLD" if conflict else "OK",
        "missing_facts": _missing_facts(pack, clean_facts),
        "journey": {
            "opportunity_id": projection["opportunity_id"],
            "digest_sha256": projection["digest_sha256"],
            "next_action_codes": projection["next_action_codes"],
            "signup_standing": projection["signup_standing"],
            "participant_standing": projection["participant_standing"],
            "warnings": projection["warnings"],
        },
        "authority_effect": "NONE",
        "eligibility_status": "UNASSESSED",
        "determination": "ADVISORY_SCREEN_ONLY",
    }

    history = case_history(ledger, program, body["case"])
    prior = history[-1] if history else None
    changed: list[str] = []
    if prior is not None:
        if prior["input_digest"] != body["input_digest"]:
            changed.append("facts")
        if prior["rule"]["pack_digest"] != body["rule"]["pack_digest"]:
            changed.append("rules")
        if prior["journey"]["digest_sha256"] != body["journey"]["digest_sha256"]:
            changed.append("journey")
        if prior["source_identity"]["handoff_digest"] != handoff_digest:
            changed.append("source")
        if prior["screen"]["state"] != body["screen"]["state"]:
            changed.append("screen")
        if prior["path_status"] != body["path_status"]:
            changed.append("path_status")
        if not changed:  # identical replay: no new history, no new decision
            return {"entry": copy.deepcopy(prior), "ledger": tuple(copy.deepcopy(list(ledger))),
                    "duplicate": True, "changed": []}

    entry = {**body, "event": "SCREENED" if prior is None else "RESCREENED",
             "changed": changed, "seq": len(ledger),
             "prev_hash": ledger[-1]["entry_hash"] if ledger else GENESIS,
             "supersedes": prior["entry_hash"] if prior else None}
    entry["entry_hash"] = entry_hash(entry)
    new_ledger = tuple(copy.deepcopy(list(ledger))) + (entry,)
    return {"entry": copy.deepcopy(entry), "ledger": new_ledger, "duplicate": False, "changed": changed}
