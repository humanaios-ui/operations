"""Shared, version-bound, read-only screening evaluator (E0).

Evaluates synthetic or consented household facts against a frozen *rule pack*
(see ``rulepacks/``). It answers "which advisory route does this fact set
show?", never "is this household eligible?".

Invariants (enforced here and in tests):
  * output ``authority_effect`` is always ``NONE``; ``eligibility_status`` is
    always ``UNASSESSED``; the agency / program administrator decides.
  * no result state may claim eligibility, approval or authorization.
  * a pack is bound to its content digest; a caller may pin the expected
    digest and a mismatch raises.
  * a pack past its source-declared ``effective_through`` date yields
    ``STALE_RULES``; a pack that declares one requires ``as_of``; there is no
    arbitrary TTL and currency is never asserted.
  * sources are checked to be ``https`` URLs only. The digest proves the pack
    is self-consistent, NOT that a URL belongs to the program or that the
    rules are authentic: results say ``source_authenticity: NOT_VERIFIED``.
  * unexpected input fields (including ``authority_effect`` or PII-shaped
    keys) are rejected; missing facts are ``None`` (unknown), never assumed.
  * standard library only; no network, no file writes.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

RULEPACK_DIR = Path(__file__).resolve().parent.parent / "rulepacks"
SCHEMA = "humanaios.entitlement-rulepack.v1"

# Every state a pack may emit. None of these asserts eligibility.
ADVISORY_STATES = frozenset({
    "POSSIBLE_ROUTE_UNVERIFIED", "NO_ROUTE_SHOWN", "UNKNOWN_ROUTE_FACTS",
    "HOLD", "REVIEW_REQUIRED", "WORKSHEET_REQUIRED", "STALE_RULES",
    "SCOPE_REVIEW", "FACT_UNKNOWN", "OVER_PUBLISHED_LIMIT",
    "WITHIN_PUBLISHED_LIMIT_ONLY", "CRISIS_FUNDING_UNCONFIRMED",
})
# ``case`` is a test label only: a short opaque token, never free text.
CASE_TOKEN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
OPS = frozenset({"eq", "ne", "is_null", "not_null", "in", "any_in",
                 "le_cap", "gt_cap"})


def canonical_digest(pack: dict[str, Any]) -> str:
    """sha256 over canonical JSON of the pack without its own digest field."""
    body = {k: v for k, v in pack.items() if k != "pack_digest"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load_pack(name_or_path: str | Path, *, pinned_digest: str | None = None) -> dict[str, Any]:
    path = Path(name_or_path)
    if not path.suffix:
        path = RULEPACK_DIR / f"{name_or_path}.json"
    pack = json.loads(path.read_text(encoding="utf-8"))
    validate_pack(pack, pinned_digest=pinned_digest)
    return pack


def validate_pack(pack: dict[str, Any], *, pinned_digest: str | None = None) -> None:
    if not isinstance(pack, dict) or pack.get("schema") != SCHEMA:
        raise ValueError("unsupported rule pack schema")
    for key in ("pack_id", "program", "rule_version", "rule_observed_at",
                "sources", "facts", "rules", "pack_digest"):
        if key not in pack:
            raise ValueError(f"rule pack missing {key}")
    if not pack["sources"] or not all(
            isinstance(s, dict) and str(s.get("url", "")).startswith("https://")
            for s in pack["sources"]):
        raise ValueError("rule pack requires https sources (authenticity is not verified here)")
    if canonical_digest(pack) != pack["pack_digest"]:
        raise ValueError("rule pack digest mismatch (content changed without re-pinning)")
    if pinned_digest is not None and pack["pack_digest"] != pinned_digest:
        raise ValueError("rule pack digest does not match pinned digest")
    declared = set(pack["facts"])
    if declared & {"authority_effect", "eligibility_status", "authorization_state"}:
        raise ValueError("rule pack may not declare authority-bearing facts")
    states = set(pack.get("states", [])) | {r["state"] for r in pack["rules"]}
    states.add(pack.get("default_state", "UNKNOWN_ROUTE_FACTS"))
    if not states <= ADVISORY_STATES:
        raise ValueError(f"rule pack uses non-advisory states: {sorted(states - ADVISORY_STATES)}")
    for rule in pack["rules"]:
        for cond in rule.get("all", []):
            if cond.get("op") not in OPS:
                raise ValueError(f"unsupported op {cond.get('op')!r}")
            if cond.get("fact") not in declared:
                raise ValueError(f"rule references undeclared fact {cond.get('fact')!r}")


def _income_cap(pack: dict[str, Any], size: Any) -> int | None:
    spec = pack.get("income_cap")
    if not spec:
        return None
    max_size = spec.get("max_size", 8)
    if type(size) is not int or size < 1 or size > max_size:
        return None
    table = {int(k): v for k, v in spec["table"].items()}
    top = max(table)
    if size <= top:
        return table[size]
    extra = spec.get("extra_person")
    return None if extra is None else table[top] + extra * (size - top)


def _cond(pack: dict[str, Any], facts: dict[str, Any], cond: dict[str, Any]) -> bool:
    value = facts.get(cond["fact"])
    op, ref = cond["op"], cond.get("value")
    if op == "eq":
        return value == ref
    if op == "ne":
        return value != ref
    if op == "is_null":
        return value is None
    if op == "not_null":
        return value is not None
    if op == "in":
        return value in pack["lists"][ref]
    if op == "any_in":
        return isinstance(value, list) and any(v in pack["lists"][ref] for v in value)
    cap = _income_cap(pack, facts.get(pack["income_cap"]["size_fact"]))
    if cap is None or type(value) not in (int, float) or isinstance(value, bool):
        return False
    return value <= cap if op == "le_cap" else value > cap


def _check_facts(pack: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(facts, dict):
        raise ValueError("facts must be an object")
    unexpected = set(facts) - set(pack["facts"]) - {"case"}
    if unexpected:
        raise ValueError(f"unexpected fact fields rejected: {sorted(unexpected)}")
    case = facts.get("case")
    if case is not None and not (isinstance(case, str) and CASE_TOKEN.match(case)):
        raise ValueError("case must be a short opaque token (letters, digits, _ . -)")
    clean = {name: facts.get(name) for name in pack["facts"]}
    for name, spec in pack["facts"].items():
        v = clean[name]
        kind = spec.get("type")
        if v is None:
            continue
        ok = ((kind == "bool" and isinstance(v, bool)) or
              (kind == "int" and type(v) is int) or
              (kind == "money" and type(v) in (int, float) and v >= 0 and v == v and v != float("inf")) or
              (kind == "str" and isinstance(v, str)) or
              (kind == "str_list" and isinstance(v, list) and all(isinstance(i, str) for i in v)))
        if not ok:
            raise ValueError(f"fact {name!r} has invalid value for type {kind}")
        if "allowed" in spec and v not in spec["allowed"]:
            raise ValueError(f"fact {name!r} value not allowed")
    return clean


def evaluate(pack: dict[str, Any], facts: dict[str, Any], *, as_of: date | str | None = None,
             pinned_digest: str | None = None) -> dict[str, Any]:
    """First-match advisory screen. Raises on tampered pack or malformed facts."""
    validate_pack(pack, pinned_digest=pinned_digest)
    clean = _check_facts(pack, copy.deepcopy(facts))
    state, rule_id = pack.get("default_state", "UNKNOWN_ROUTE_FACTS"), "default"
    stale = False
    through = pack.get("effective_through")
    if through is not None and as_of is None:
        raise ValueError("as_of is required for a rule pack with a declared effective_through")
    if through is not None:
        when = date.fromisoformat(as_of) if isinstance(as_of, str) else as_of
        stale = when > date.fromisoformat(through)
    if stale:
        state, rule_id = "STALE_RULES", "stale"
    else:
        for rule in pack["rules"]:
            if all(_cond(pack, clean, c) for c in rule.get("all", [])):
                state, rule_id = rule["state"], rule["id"]
                break
    size_fact = (pack.get("income_cap") or {}).get("size_fact")
    return {
        "case": facts.get("case", "unnamed"),
        "program": pack["program"],
        "state": state,
        "rule_id": rule_id,
        "income_cap_usd": _income_cap(pack, clean.get(size_fact)) if size_fact else None,
        "next_step": pack.get("next_steps", {}).get(state),
        "pack_id": pack["pack_id"],
        "rule_version": pack["rule_version"],
        "pack_digest": pack["pack_digest"],
        "rule_observed_at": pack["rule_observed_at"],
        "effective_through": through,
        "sources": [s["url"] for s in pack["sources"]],
        "source_authenticity": "NOT_VERIFIED",
        "eligibility_status": "UNASSESSED",
        "determination": "ADVISORY_SCREEN_ONLY",
        "authority_effect": "NONE",
    }
