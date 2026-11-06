"""Plain-language explanation of one E1 decision-history entry.

A pure function of a hash-verified ledger entry. It takes no overrides, never
changes the recorded state, and cannot display an approval: the only inputs it
trusts are the fields the rules evaluator and the journey projection recorded.
"""
from __future__ import annotations

from typing import Any

from resource_system.e1_household_path import GENESIS, _check_entry, case_history, entry_hash, verify_ledger

SCHEMA = "humanaios.e1.explanation.v1"

PROGRAM = {
    "lifeline": ("FCC Lifeline", "the USAC National Verifier"),
    "liheap": ("Florida LIHEAP (Okaloosa County)", "Tri-County Community Council"),
}
# Every state the packs can emit. A missing state raises: no silent fallback text.
STATE_TEXT = {
    "POSSIBLE_ROUTE_UNVERIFIED": "The facts given match a published route that may be worth investigating. Nothing has been checked or confirmed.",
    "WORKSHEET_REQUIRED": "A route may exist, but this household shares an address with another beneficiary. A household worksheet is needed first.",
    "WITHIN_PUBLISHED_LIMIT_ONLY": "The stated income is at or below the published limit. No other requirement has been checked.",
    "CRISIS_FUNDING_UNCONFIRMED": "The stated income is within the published limit and a disconnection notice was reported, but crisis funding is unconfirmed. Ask the county provider.",
    "OVER_PUBLISHED_LIMIT": "The stated income is above the published limit. The agency may still look at how income is counted. This is not a denial.",
    "NO_ROUTE_SHOWN": "The facts given show no route. This is not a denial; new facts or other routes may change it.",
    "UNKNOWN_ROUTE_FACTS": "There are not enough facts to show any route.",
    "FACT_UNKNOWN": "A needed fact is unknown. Nothing can be shown until it is provided.",
    "REVIEW_REQUIRED": "A person must review this case before any route can be shown.",
    "HOLD": "This household already reports a discount. One benefit per household applies, so this is on hold.",
    "SCOPE_REVIEW": "This case is outside the scope of the rules used. Check the rules for the right state, county or program.",
    "STALE_RULES": "The rules used are past the date their source declared. Do not rely on this result until the rules are refreshed.",
}
INVESTIGATE = frozenset({"POSSIBLE_ROUTE_UNVERIFIED", "WORKSHEET_REQUIRED",
                         "WITHIN_PUBLISHED_LIMIT_ONLY", "CRISIS_FUNDING_UNCONFIRMED"})
SHOW_LIMIT = frozenset({"POSSIBLE_ROUTE_UNVERIFIED", "WORKSHEET_REQUIRED", "WITHIN_PUBLISHED_LIMIT_ONLY",
                        "CRISIS_FUNDING_UNCONFIRMED", "OVER_PUBLISHED_LIMIT", "NO_ROUTE_SHOWN"})
NOT_ESTABLISHED = (
    "An approval or an eligibility decision",
    "Identity, income or program participation",
    "Enrollment or service from any provider",
    "Any benefit amount",
)


def explain(entry: dict[str, Any], ledger: Any = None, expected_head: str | None = None) -> dict[str, Any]:
    """Explain a recorded entry. Raises if the entry or ledger fails verification.

    Pass the ledger (and, if you keep one outside it, ``expected_head``) so the whole
    history is verified. With no ledger only this one entry's hash and fields are checked.
    """
    if not isinstance(entry, dict) or entry.get("entry_hash") != entry_hash(entry):
        raise ValueError("entry does not match its hash; refusing to explain an altered decision")
    if (entry.get("authority_effect") != "NONE" or entry.get("eligibility_status") != "UNASSESSED"
            or entry.get("determination") != "ADVISORY_SCREEN_ONLY"):
        raise ValueError("entry carries authority or an eligibility claim")
    history = [entry]
    if ledger is None:
        seq = entry.get("seq")
        if type(seq) is not int or seq < 0:
            raise ValueError("entry has an invalid seq")
        _check_entry(entry, seq, entry.get("prev_hash"), {})
        if (seq == 0) != (entry.get("prev_hash") == GENESIS):
            raise ValueError("entry position does not match its prev_hash")
        integrity = "ENTRY_ONLY_CHAIN_NOT_CHECKED"
    else:
        verify_ledger(ledger, expected_head)
        if not any(e["entry_hash"] == entry["entry_hash"] for e in ledger):
            raise ValueError("entry is not part of the supplied ledger")
        history = case_history(ledger, entry["program"], entry["case"])
        integrity = "HASH_CHAIN_ANCHORED" if expected_head is not None else "HASH_CHAIN_UNANCHORED"
    state = entry["screen"]["state"]
    if state not in STATE_TEXT:
        raise ValueError("no explanation text for this state")
    label, administrator = PROGRAM[entry["program"]]
    conflict = entry["path_status"] == "SOURCE_CONFLICT_HOLD"

    next_actions = []
    if conflict:
        next_actions.append("RESOLVE_SOURCE_CONFLICT: the resource's source does not match the sources the rules cite.")
    if entry["screen"]["next_step"]:
        next_actions.append(entry["screen"]["next_step"])
    next_actions += list(entry["journey"]["next_action_codes"])
    next_actions.append(f"Confirm everything with {administrator}; they decide.")

    rule = entry["rule"]
    card = {
        "schema": SCHEMA,
        "decision_hash": entry["entry_hash"],
        "program": label,
        "case": entry["case"],
        "screen_state": state,
        "headline": STATE_TEXT[state],
        "worth_investigating": state in INVESTIGATE and not conflict,
        "source_conflict_notice": (
            "The sources for this resource do not match the sources the rules cite. "
            "The screen result below is unchanged but is on hold." if conflict else None),
        "missing_facts": list(entry["missing_facts"]),
        "rule_support": {
            "rule_id": rule["rule_id"], "sources": list(rule["rule_sources"]),
            "attribution": rule["rule_source_attribution"],
            "source_authenticity": rule["source_authenticity"],
        },
        "rule_version": {"pack_id": rule["pack_id"], "rule_version": rule["rule_version"],
                         "pack_digest": rule["pack_digest"], "observed_at": rule["rule_observed_at"],
                         "effective_through": rule["effective_through"]},
        "published_income_limit_usd": (entry["screen"]["income_cap_usd"]
                                       if state in SHOW_LIMIT and not conflict else None),
        "history_integrity": integrity,
        "next_actions": next_actions,
        "not_established": list(NOT_ESTABLISHED),
        "history": [{"seq": e["seq"], "event": e["event"], "changed": list(e["changed"]),
                     "screen_state": e["screen"]["state"], "pack_digest": e["rule"]["pack_digest"],
                     "entry_hash": e["entry_hash"]} for e in history],
    }
    card["text"] = render_text(card)
    return card


def render_text(card: dict[str, Any]) -> str:
    lines = [f"{card['program']} - case {card['case']}", card["headline"]]
    if card["source_conflict_notice"]:
        lines.append("NOTICE: " + card["source_conflict_notice"])
    lines.append("Screening only. Not established: " + "; ".join(card["not_established"]) + ".")
    if card["missing_facts"]:
        lines.append("Facts not yet provided that the rules read: " + ", ".join(card["missing_facts"]) + ".")
    if card["published_income_limit_usd"] is not None:
        lines.append(f"Published income limit used: ${card['published_income_limit_usd']:,} a year.")
    support = card["rule_support"]
    lines.append(f"Rule {support['rule_id']} cites: " + "; ".join(support["sources"])
                 + f" (attribution {support['attribution']}; source authenticity {support['source_authenticity']}).")
    version = card["rule_version"]
    lines.append(f"Rules {version['rule_version']} (pack {version['pack_id']}, digest {version['pack_digest'][:12]}, "
                 f"observed {version['observed_at']}).")
    lines.append("Next: " + " | ".join(card["next_actions"]))
    lines.append(f"History: {len(card['history'])} recorded step(s); decision {card['decision_hash'][:12]}; "
                 f"integrity {card['history_integrity']}"
                 + (" (a person able to recompute hashes could rewrite it)." if card["history_integrity"] == "HASH_CHAIN_UNANCHORED" else "."))
    return "\n".join(lines)
