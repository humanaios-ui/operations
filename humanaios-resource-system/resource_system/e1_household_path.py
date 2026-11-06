"""E1: one synthetic-household path through the existing pieces.

Resource Miner handoff -> Entitlement Navigator intake -> shared rules
evaluator -> Opportunity Journey projection -> hash-chained decision history.

Read-only and deterministic: no network, no file writes, no clock reads (the
caller supplies ``as_of`` and ``observed_at``). Nothing here grants authority,
assesses eligibility or records an approval. Existing modules are loaded and
used unchanged; this file only composes them.

Integrity limit (stated, not hidden): the history is a plain SHA-256 chain.
Anyone who can recompute SHA-256 can rewrite it unless the head hash is kept
outside the ledger. ``verify_ledger(ledger, expected_head=...)`` checks such an
anchor; without one, truncation or a full re-chain cannot be detected. Every
entry field is still validated against the pinned pack, so a rewritten entry
cannot carry free text, an unknown rule, or an unpinned rule version.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from datetime import date
from typing import Any
from urllib.parse import urlsplit

from resource_system.adapters.resource_miner_adapter import load_handoff_module

_miner = load_handoff_module("resource-miner/resource_miner/entitlement_handoff.py")
_navigator = load_handoff_module("entitlement-navigator/entitlement/resource_handoff.py")
_evaluator = load_handoff_module("entitlement-navigator/entitlement/rules_evaluator.py")
_journey = load_handoff_module("resource-miner/resource_miner/opportunity_journey.py")

ENTRY_SCHEMA = "humanaios.e1.decision-entry.v1"
GENESIS = "0" * 64
TOKEN = re.compile(r"[A-Za-z0-9_-]{1,100}")
ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
UTC_STAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
HEX64 = re.compile(r"[0-9a-f]{64}")
SOURCE_NAME = re.compile(r"[\w ().,&/-]{1,80}")
HANDOFF_ID = re.compile(r"rm:[A-Za-z0-9_.:-]{1,100}")
# Candidate keys that would smuggle a benefit/approval claim into the path.
BENEFIT_KEYS = re.compile(r"(benefit|award|payment|approved|granted|discount_usd|amount|enroll)", re.I)
# Whole words that must not appear in values we store or print. `case` is an opaque test
# label, so it gets the broader list; `source_name` is a real organisation name, so it only
# loses status claims and amounts ("Benefits.gov" and "Medicaid Eligibility Office" are fine).
CASE_CLAIM_WORDS = frozenset({"approved", "approval", "eligible", "awarded", "granted", "enrolled",
                              "qualified", "benefit", "benefits", "payment", "payments"})
NAME_CLAIM_WORDS = frozenset({"approved", "awarded", "granted", "enrolled", "qualified"})
AMOUNT = re.compile(r"\$|[0-9]\s*(/|per|a)\s*mo(nth)?\b", re.I)


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^A-Za-z0-9]+", text.lower()) if w]


def case_has_claim(case: str) -> bool:
    words = _words(case)
    per_month = any(a == "per" and b in ("month", "mo") for a, b in zip(words, words[1:]))
    return bool(set(words) & CASE_CLAIM_WORDS) or per_month or bool(AMOUNT.search(case))


def name_has_claim(name: str) -> bool:
    return bool(set(_words(name)) & NAME_CLAIM_WORDS) or bool(AMOUNT.search(name)) \
        or "you qualify" in name.lower()


JOURNEY_CODES = frozenset({
    "REVIEW_AND_SELECT_OPPORTUNITY", "REVIEW_SIGNUP_OR_APPLICATION", "COMPLETE_REQUIRED_SURVEY",
    "VERIFY_PARTICIPANT_STANDING_WITH_PROVIDER", "REVIEW_CALENDAR_SCHEDULE",
    "REVIEW_EVENT_UPDATES_AND_RESEARCH_DELIVERABLE", "REVIEW_PREPARATION_PACKAGE",
    "COMPLETE_PREPARATION_CHECKS"})
JOURNEY_WARNINGS = frozenset({
    "SIGNUP_RECEIPT_WITHOUT_EXPLICIT_SELECTED_INTENT", "SURVEY_REPORT_WITHOUT_SIGNUP_RECEIPT",
    "CALENDAR_RECEIPT_WITHOUT_EXPLICIT_SELECTED_INTENT"})
CHANGE_KINDS = frozenset({"facts", "rules", "journey", "source", "screen", "path_status"})
ENTRY_KEYS = frozenset({
    "schema", "program", "case", "input_digest", "observed_at", "as_of", "source_identity", "rule",
    "screen", "path_status", "missing_facts", "journey", "authority_effect", "eligibility_status",
    "determination", "event", "changed", "seq", "prev_hash", "supersedes", "entry_hash"})

# Version binding: the E1 path only runs against these exact pack digests.
# Changing a pack changes its digest, so the path refuses until a human re-pins.
PINS = {
    "lifeline": {"pack_name": "us-lifeline-2026",
                 "pinned_digest": "26b0ea253160a3971a7a9ce7cf71dfbbf10ce1a9aafd4aeb0c4cd459376c3e88"},
    "liheap": {"pack_name": "fl-liheap-ffy2027",
               "pinned_digest": "ee4c857adaf4fb003e7e450dbd4e318d51d901bcc62706e0f80264f704316135"},
}
# Packs that earlier ledger entries were screened under (digest -> pack). Empty today.
RETIRED_PACKS: dict[str, dict[str, Any]] = {}


def default_registry() -> dict[str, dict[str, Any]]:
    """Load and verify the pinned packs. Raises if a pack no longer matches its pin."""
    registry = {}
    for program, pin in PINS.items():
        pack = _evaluator.load_pack(pin["pack_name"], pinned_digest=pin["pinned_digest"])
        if pack["pack_id"] != pin["pack_name"]:
            raise ValueError("pack_id does not match the pinned pack name")
        registry[program] = {"pack": pack, "pinned_digest": pin["pinned_digest"]}
    return registry


def _packs_for(program: str) -> dict[str, dict[str, Any]]:
    """Pinned pack plus any retired packs for this program, each digest-verified."""
    current = default_registry()[program]
    packs = {current["pinned_digest"]: current["pack"]}
    for digest, pack in RETIRED_PACKS.items():
        _evaluator.validate_pack(pack, pinned_digest=digest)
        if pack["program"] == current["pack"]["program"]:
            packs[digest] = pack
    return packs


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _sha(obj: Any) -> str:
    return hashlib.sha256(_canon(obj).encode("utf-8")).hexdigest()


def entry_hash(entry: dict[str, Any]) -> str:
    return _sha({k: v for k, v in entry.items() if k != "entry_hash"})


def head_hash(ledger: Any) -> str:
    """Hash to store outside the ledger (the integrity anchor)."""
    return ledger[-1]["entry_hash"] if ledger else GENESIS


def strict_https_host(url: Any) -> str | None:
    """Host of a plain https URL, or None for anything ambiguous (never raises)."""
    if not isinstance(url, str) or not url or url != url.strip():
        return None
    if "\\" in url or any(ord(c) < 33 or ord(c) == 127 for c in url):
        return None
    try:
        parts = urlsplit(url)
        host, port = parts.hostname, parts.port
    except ValueError:
        return None
    if parts.scheme != "https" or not host or port not in (None, 443) or parts.username or parts.password:
        return None
    return host[4:] if host.startswith("www.") else host


def _strict_date(value: Any, label: str) -> date:
    if not isinstance(value, str) or not ISO_DATE.fullmatch(value):
        raise ValueError(f"{label} must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} is not a real date") from exc


def _canonical_facts(facts: dict[str, Any]) -> dict[str, Any]:
    """Equal facts digest equally: 1000 == 1000.0 == -0.0 style noise, program order and case."""
    out = {}
    for key, value in facts.items():
        if key == "case":
            continue
        if type(value) is float and math.isfinite(value) and value == int(value):
            value = int(value)
        if isinstance(value, list) and all(isinstance(v, str) for v in value):
            value = sorted({v.strip().upper() for v in value})
        out[key] = value
    return out


def _missing_facts(pack: dict[str, Any], facts: dict[str, Any]) -> list[str]:
    read = {c["fact"] for r in pack["rules"] for c in r.get("all", [])}
    size_fact = (pack.get("income_cap") or {}).get("size_fact")
    missing = {f for f in read if facts.get(f) is None}
    if size_fact:
        read.add(size_fact)
        if _evaluator._income_cap(pack, facts.get(size_fact)) is None:
            missing.add(size_fact)  # absent, zero, negative or beyond the modeled sizes
    return sorted(missing)


def _check_entry(entry: Any, seq: int, prev: str, cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Structural + semantic validation of one entry. Returns its pack. Raises ValueError."""
    if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS or entry.get("schema") != ENTRY_SCHEMA:
        raise ValueError("ledger contains a malformed entry")
    if entry["seq"] != seq or entry["prev_hash"] != prev:
        raise ValueError("ledger chain broken (entry removed, reordered or inserted)")
    if entry["entry_hash"] != entry_hash(entry):
        raise ValueError("ledger entry content does not match its hash")
    if (entry["authority_effect"] != "NONE" or entry["eligibility_status"] != "UNASSESSED"
            or entry["determination"] != "ADVISORY_SCREEN_ONLY"):
        raise ValueError("ledger entry carries authority or an eligibility claim")
    if entry["program"] not in PINS:
        raise ValueError("ledger entry names an unknown program")
    if not (isinstance(entry["case"], str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", entry["case"])
            and not case_has_claim(entry["case"])):
        raise ValueError("ledger entry has an invalid case label")
    for key in ("input_digest", "prev_hash"):
        if not (isinstance(entry[key], str) and HEX64.fullmatch(entry[key])):
            raise ValueError(f"ledger entry has an invalid {key}")
    if not (isinstance(entry["observed_at"], str) and UTC_STAMP.fullmatch(entry["observed_at"])):
        raise ValueError("ledger entry has an invalid observed_at")
    _strict_date(entry["as_of"], "as_of")
    if entry["event"] not in ("SCREENED", "RESCREENED") or not isinstance(entry["changed"], list) \
            or not set(entry["changed"]) <= CHANGE_KINDS or len(set(entry["changed"])) != len(entry["changed"]):
        raise ValueError("ledger entry has an invalid event")
    if entry["path_status"] not in ("OK", "SOURCE_CONFLICT_HOLD"):
        raise ValueError("ledger entry has an invalid path_status")

    rule, screen = entry["rule"], entry["screen"]
    if not isinstance(rule, dict) or not isinstance(screen, dict):
        raise ValueError("ledger entry is malformed")
    if entry["program"] not in cache:
        cache[entry["program"]] = _packs_for(entry["program"])
    pack = cache[entry["program"]].get(rule.get("pack_digest"))
    if pack is None:
        raise ValueError("ledger entry was screened under an unknown rule pack")
    expected_rule = {"pack_id", "rule_version", "pack_digest", "rule_observed_at", "effective_through",
                     "rule_id", "rule_sources", "rule_source_attribution", "source_authenticity"}
    if set(rule) != expected_rule or rule["pack_id"] != pack["pack_id"] \
            or rule["rule_version"] != pack["rule_version"] \
            or rule["rule_observed_at"] != pack["rule_observed_at"] \
            or rule["effective_through"] != pack.get("effective_through") \
            or rule["rule_source_attribution"] != pack.get("rule_source_attribution", "NOT_STATED") \
            or rule["source_authenticity"] != "NOT_VERIFIED":
        raise ValueError("ledger entry rule block does not match its pack")
    by_id = {r["id"]: r for r in pack["rules"]}
    all_urls = [s["url"] for s in pack["sources"]]
    if rule["rule_id"] == "stale":
        want_state, want_urls = "STALE_RULES", all_urls
    elif rule["rule_id"] == "default":
        want_state, want_urls = pack.get("default_state", "UNKNOWN_ROUTE_FACTS"), all_urls
    elif rule["rule_id"] in by_id:
        matched = by_id[rule["rule_id"]]
        want_state = matched["state"]
        want_urls = [pack["sources"][i]["url"] for i in matched["sources"]] if matched.get("sources") else all_urls
    else:
        raise ValueError("ledger entry names an unknown rule")
    if set(screen) != {"state", "income_cap_usd", "next_step"} or screen["state"] != want_state \
            or screen["next_step"] != pack.get("next_steps", {}).get(want_state) \
            or rule["rule_sources"] != want_urls:
        raise ValueError("ledger entry screen or sources do not match its rule")
    cap = screen["income_cap_usd"]
    spec = pack.get("income_cap") or {}
    table = [v for v in spec.get("table", {}).values()]
    allowed_caps = set(table)
    if table and spec.get("extra_person") is not None:
        top = spec["table"][str(max(int(k) for k in spec["table"]))]
        allowed_caps |= {top + spec["extra_person"] * k
                         for k in range(1, spec.get("max_size", 8) - max(int(k) for k in spec["table"]) + 1)}
    if cap is not None and not (type(cap) is int and cap in allowed_caps):
        raise ValueError("ledger entry income limit is not a limit the pack publishes")
    if entry["as_of"] < pack["rule_observed_at"]:
        raise ValueError("ledger entry as_of is earlier than the rules observed date")
    if (entry["supersedes"] is None) != (entry["event"] == "SCREENED") \
            or (entry["event"] == "SCREENED") != (entry["changed"] == []):
        raise ValueError("ledger entry event does not match its history")
    facts_read = set(pack["facts"])
    if not (isinstance(entry["missing_facts"], list) and set(entry["missing_facts"]) <= facts_read
            and entry["missing_facts"] == sorted(set(entry["missing_facts"]))):
        raise ValueError("ledger entry has invalid missing facts")

    src, journey = entry["source_identity"], entry["journey"]
    if not isinstance(src, dict) or set(src) != {"resource_id", "handoff_id", "handoff_digest",
                                                  "primary_source_url", "source_name"}:
        raise ValueError("ledger entry source identity is malformed")
    if not (TOKEN.fullmatch(str(src["resource_id"])) and HANDOFF_ID.fullmatch(str(src["handoff_id"]))
            and HEX64.fullmatch(str(src["handoff_digest"]))
            and (src["primary_source_url"] is None or strict_https_host(src["primary_source_url"]))
            and SOURCE_NAME.fullmatch(str(src["source_name"])) and not name_has_claim(str(src["source_name"]))):
        raise ValueError("ledger entry source identity is invalid")
    if not isinstance(journey, dict) or set(journey) != {
            "opportunity_id", "digest_sha256", "next_action_codes", "signup_standing",
            "participant_standing", "warnings"}:
        raise ValueError("ledger entry journey is malformed")
    expected_opp = "OPP-" + hashlib.sha256(f"{src['resource_id']}|{entry['case']}".encode()).hexdigest()[:16]
    # This path only ever reports a discovery and an optional human selection, so the journey
    # can only be in one of two states and can carry no warnings or signup standing.
    if not (journey["opportunity_id"] == expected_opp
            and HEX64.fullmatch(str(journey["digest_sha256"]))
            and journey["next_action_codes"] in (["REVIEW_AND_SELECT_OPPORTUNITY"], ["REVIEW_SIGNUP_OR_APPLICATION"])
            and journey["warnings"] == []
            and journey["signup_standing"] == "UNVERIFIED"
            and journey["participant_standing"] == "NOT_CONFIRMED_BY_PROVIDER"):
        raise ValueError("ledger entry journey is invalid")
    if entry["path_status"] == "OK" and strict_https_host(src["primary_source_url"]) not in \
            {strict_https_host(u["url"]) for u in pack["sources"]}:
        raise ValueError("ledger entry says sources match but its source URL is not on a cited host")
    return pack


def verify_ledger(ledger: Any, expected_head: str | None = None) -> None:
    """Fail closed on a malformed, edited, reordered or authority-bearing ledger.

    Pass ``expected_head`` (stored outside the ledger) to also detect truncation or a
    wholesale re-chain; without it those cannot be detected.
    """
    if not isinstance(ledger, (list, tuple)):
        raise ValueError("ledger must be a list or tuple")
    prior_by_case: dict[tuple[str, str], str] = {}
    prev = GENESIS
    cache: dict[str, dict[str, Any]] = {}
    for seq, entry in enumerate(ledger):
        try:
            _check_entry(entry, seq, prev, cache)
        except (TypeError, KeyError, AttributeError, IndexError) as exc:
            raise ValueError("ledger contains a malformed entry") from exc
        key = (entry["program"], entry["case"])
        if entry["supersedes"] != prior_by_case.get(key):
            raise ValueError("ledger supersedes pointer does not match case history")
        prior_by_case[key] = entry["entry_hash"]
        prev = entry["entry_hash"]
    if expected_head is not None and expected_head != prev:
        raise ValueError("ledger head does not match the external anchor")


def case_history(ledger: Any, program: str, case: str) -> list[dict[str, Any]]:
    return [e for e in ledger if e["program"] == program and e["case"] == case]


def run_household(program: str, candidate: dict[str, Any], facts: dict[str, Any], *,
                  as_of: str, observed_at: str, ledger: Any = (),
                  expected_head: str | None = None,
                  human_selected_ref: str | None = None) -> dict[str, Any]:
    """Run one synthetic household. Returns the new/unchanged ledger and the entry."""
    ledger = () if ledger is None else ledger
    verify_ledger(ledger, expected_head)
    registry = default_registry()
    if program not in registry:
        raise ValueError("unknown program")
    if not isinstance(candidate, dict) or not isinstance(facts, dict):
        raise ValueError("candidate and facts must be objects")
    candidate, facts = dict(candidate), dict(facts)  # plain dicts: no subclass can answer .items() and .get() differently
    pack = registry[program]["pack"]
    pinned = registry[program]["pinned_digest"]
    as_of_date = _strict_date(as_of, "as_of")
    if as_of_date < date.fromisoformat(pack["rule_observed_at"]):
        raise ValueError("as_of is earlier than the date the rules were observed")
    if candidate.get("authority_effect") not in (None, "NONE"):
        raise ValueError("candidate carries an authority effect")
    if any(BENEFIT_KEYS.search(str(k)) for k in candidate):
        raise ValueError("candidate carries an unsupported benefit claim")
    source_name = candidate.get("source_name")
    if not (isinstance(source_name, str) and SOURCE_NAME.fullmatch(source_name)) or name_has_claim(source_name):
        raise ValueError("candidate source_name is missing or carries a claim")
    if "case" in facts and case_has_claim(str(facts["case"])):
        raise ValueError("case label carries a claim")

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

    # 2. Source identity: all three candidate source URLs must be plain https on a host
    #    the pack cites. Anything missing or ambiguous is a conflict (fail closed).
    pack_hosts = {strict_https_host(s["url"]) for s in pack["sources"]}
    seen = [candidate.get(k) for k in ("primary_source_url", "canonical_url", "source_url")]
    conflict = any(strict_https_host(u) is None or strict_https_host(u) not in pack_hosts for u in seen)

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

    clean_facts = _canonical_facts(facts)
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
            "primary_source_url": (candidate["primary_source_url"]
                                   if strict_https_host(candidate.get("primary_source_url")) else None),
            "source_name": source_name,
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
        "missing_facts": _missing_facts(pack, _evaluator._check_facts(pack, copy.deepcopy(facts))),
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
             "prev_hash": head_hash(ledger),
             "supersedes": prior["entry_hash"] if prior else None}
    entry["entry_hash"] = entry_hash(entry)
    new_ledger = tuple(copy.deepcopy(list(ledger))) + (entry,)
    verify_ledger(new_ledger)  # never hand back a ledger this module would itself reject
    return {"entry": copy.deepcopy(entry), "ledger": new_ledger, "duplicate": False, "changed": changed}
