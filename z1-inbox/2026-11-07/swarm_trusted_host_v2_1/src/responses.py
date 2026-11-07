"""Strict, deterministic parsing of model responses for the signed response ledger.

The HOST parses the raw bytes the orchestrator relays; nobody asserts a claim or a ballot. Anything that is
not exactly one JSON object with the one expected key and a permitted value is UNKNOWN / UNPARSEABLE and is
never guessed. This module is pinned in the frozen plan (`responses_sha256`); the frozen prompts must instruct
the models to answer with exactly {"claim": ...} or {"ballot": ...}.
"""
import json

MAX_RAW = 32768
CLAIM_VALUES = frozenset({"SUCCESS", "FAILURE", "UNKNOWN"})
BALLOT_VALUES = frozenset({"APPROVE", "REJECT", "UNKNOWN"})
TRANSPORT = frozenset({"OK", "TIMEOUT", "ERROR"})
# kind -> (json key, permitted values, actors that may produce it)
KINDS = {
    "EXECUTOR_CLAIM": ("claim", CLAIM_VALUES, frozenset({"A"})),
    "REVIEWER_CLAIM": ("claim", CLAIM_VALUES, frozenset({"B"})),
    "FINAL_CLAIM": ("claim", CLAIM_VALUES, frozenset({"A", "B"})),
    "BALLOT": ("ballot", BALLOT_VALUES, frozenset({"A", "B"})),
}


def slot(kind, actor_id):
    """One response per slot. The swarm has ONE final claim, whichever actor gave it."""
    return (kind,) if kind == "FINAL_CLAIM" else (kind, actor_id)


def _no_duplicate_keys(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate key")
    return dict(pairs)


def parse_response(kind, raw, transport_status):
    """Return (value, parse_status). parse_status is OK, UNPARSEABLE or NOT_RECEIVED."""
    if transport_status != "OK":
        return "UNKNOWN", "NOT_RECEIVED"
    key, allowed, _ = KINDS[kind]
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    except (ValueError, UnicodeDecodeError, RecursionError):  # model text is hostile: deep nesting must not crash
        return "UNKNOWN", "UNPARSEABLE"
    if not isinstance(doc, dict) or set(doc) != {key}:
        return "UNKNOWN", "UNPARSEABLE"
    value = doc[key]
    if not isinstance(value, str) or value not in allowed:
        return "UNKNOWN", "UNPARSEABLE"
    return value, "OK"


def pinned_model(plan, actor_id):
    """The one model the frozen plan pins for this actor. The ledger may name no other."""
    return plan["protocol_pins"]["model_a" if actor_id == "A" else "model_b"]


def derive_observation(entries):
    """entries: ledger details (dicts with actor_id, kind, value). Returns (observation_or_None_per_slot, complete)."""
    by = {}
    for e in entries:
        by[slot(e["kind"], e["actor_id"])] = e["value"]
    final = by.get(("FINAL_CLAIM",))
    obs = {"executor_claim": by.get(("EXECUTOR_CLAIM", "A")), "reviewer_claim": by.get(("REVIEWER_CLAIM", "B")),
           "final_claim": final, "ballots": {"A": by.get(("BALLOT", "A")), "B": by.get(("BALLOT", "B"))}}
    complete = all(v is not None for v in (obs["executor_claim"], obs["reviewer_claim"], final,
                                           obs["ballots"]["A"], obs["ballots"]["B"]))
    return obs, complete
