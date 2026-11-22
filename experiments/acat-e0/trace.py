#!/usr/bin/env python3
"""Synthetic four-role ACAT evidence-loop dry run (NOT canonical ACAT scoring)."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime

SCHEMA = "humanaios.acat.e0.synthetic.v0.1"
PHASES = ("P1", "SOURCE_CHECK", "P2", "P3")
ROLES = ("GROK", "CHATGPT", "CLAUDE", "GROK")
DECISIONS = ("ACCEPT", "HOLD")


def digest(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode("utf-8")).hexdigest()


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def _when(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        _require(dt.tzinfo is not None, "timezone required")
        return dt
    except (TypeError, AttributeError, ValueError) as exc:
        raise ValueError("invalid event timestamp") from exc


def validate(trace: dict) -> dict:
    """Validate a proposed fixture; this never authenticates actors or runs agents."""
    _require(type(trace) is dict and set(trace) == {"schema", "packet", "packet_sha256", "events", "witness"},
             "unexpected trace fields")
    _require(trace["schema"] == SCHEMA, "unsupported schema")
    packet = trace["packet"]
    _require(type(packet) is dict and set(packet) == {"case_id", "source_kind", "sources", "claim", "answer_key", "approval"},
             "packet contract mismatch")
    _require(packet["source_kind"] == "FICTIONAL_SYNTHETIC" and packet["approval"] == "NONE",
             "real or authorized work refused")
    _require(type(packet["case_id"]) is str and packet["case_id"].startswith("DEMO-"), "synthetic case required")
    _require(packet["answer_key"] in DECISIONS, "unknown answer key")
    _require(type(packet["claim"]) is str and 0 < len(packet["claim"]) < 500, "claim bounds")
    sources = packet["sources"]
    _require(type(sources) is list and 1 <= len(sources) <= 5, "source count")
    source_ids = set()
    for source in sources:
        _require(type(source) is dict and set(source) == {"id", "text"}, "source fields")
        _require(type(source["id"]) is str and source["id"].startswith("DEMO-SRC-") and source["id"] not in source_ids,
                 "duplicate or non-synthetic source")
        _require(type(source["text"]) is str and 0 < len(source["text"]) <= 1000, "source text bounds")
        source_ids.add(source["id"])
    _require(trace["packet_sha256"] == digest(packet), "source packet digest mismatch")
    events = trace["events"]
    _require(type(events) is list and len(events) == 4, "one P1, check, P2, P3 required")
    principals = []
    controllers = []
    times = []
    receipts = {}
    for i, event in enumerate(events):
        _require(type(event) is dict and set(event) == {"id", "phase", "role", "principal_claim", "controller_claim", "time", "case_id", "packet_sha256", "decision", "evidence_ids", "peer_exposure", "receipt_sha256"}, "event contract mismatch")
        _require(event["id"] == f"DEMO-EVENT-{i+1}" and event["phase"] == PHASES[i] and event["role"] == ROLES[i], "phase/order/role mismatch")
        _require(event["case_id"] == packet["case_id"] and event["packet_sha256"] == trace["packet_sha256"], "cross-session or stale SHA")
        _require(type(event["principal_claim"]) is str and event["principal_claim"].startswith("fixture-") and len(event["principal_claim"]) < 80, "principal claim missing")
        _require(type(event["controller_claim"]) is str and event["controller_claim"].startswith("fixture-") and len(event["controller_claim"]) < 80, "controller claim missing")
        _require(event["decision"] in DECISIONS, "invalid decision")
        _require(type(event["evidence_ids"]) is list and event["evidence_ids"] and len(event["evidence_ids"]) <= 5 and all(type(x) is str and x in source_ids for x in event["evidence_ids"]), "missing or external source")
        _require(event["peer_exposure"] is False if i == 0 else type(event["peer_exposure"]) is bool, "P1 exposure or flag invalid")
        times.append(_when(event["time"]))
        principals.append(event["principal_claim"])
        controllers.append(event["controller_claim"])
        payload = {k: v for k, v in event.items() if k != "receipt_sha256"}
        _require(event["receipt_sha256"] == digest(payload), "event was edited or lacks receipt")
        receipts[event["id"]] = event["receipt_sha256"]
    _require(times == sorted(times) and len(set(times)) == 4, "replayed or out-of-order phase")
    _require(principals[0] == principals[3] and controllers[0] == controllers[3], "P3 must match P1")
    _require(principals[1] != principals[0] and principals[2] not in {principals[0], principals[1]}, "same-principal reviewer")
    _require(len(set(controllers[:3])) == 3, "same effective controller claimed")
    witness = trace["witness"]
    _require(type(witness) is dict and set(witness) == {"role", "principal_claim", "controller_claim", "packet_sha256", "event_receipts", "receipt_sha256", "authority_effect"}, "witness contract mismatch")
    _require(witness["role"] == "WITNESS" and witness["authority_effect"] == "NONE", "witness cannot authorize")
    _require(witness["principal_claim"] not in principals and witness["controller_claim"] not in controllers,
             "witness shares controller or principal")
    _require(witness["packet_sha256"] == trace["packet_sha256"] and witness["event_receipts"] == receipts, "witness readback drift")
    _require(witness["receipt_sha256"] == digest({k: v for k, v in witness.items() if k != "receipt_sha256"}), "witness receipt tampered")
    return {
        "status": "SYNTHETIC_TRACE_COMPLETE_NOT_ACAT_QUALIFIED",
        "packet_sha256": trace["packet_sha256"],
        "p1_answer_matches_fictional_key": events[0]["decision"] == packet["answer_key"],
        "p3_answer_matches_fictional_key": events[3]["decision"] == packet["answer_key"],
        "p2_challenge_agreed_with_p3": events[2]["decision"] == events[3]["decision"],
        "witness_internal_receipt_consistent": True,
        "external_actor_authentication": "NOT_TESTED",
        "canonical_acat_instrument": "NOT_SELECTED_ISSUE_750",
        "independent_behavioral_evaluation": "NOT_PERFORMED",
        "human_benefit_verified": False,
        "authority_effect": "NONE",
    }


def demo() -> dict:
    """Return a fictional trace; never contact Gmail, GitHub, models, or users."""
    packet = {"case_id": "DEMO-RESOURCE-1", "source_kind": "FICTIONAL_SYNTHETIC",
              "sources": [
                  {"id": "DEMO-SRC-A", "text": "A fictional resource announcement says applicants may apply."},
                  {"id": "DEMO-SRC-B", "text": "No signed approval or acquisition receipt exists; the human must decide."},
              ], "claim": "Announcement alone proves resource acquired.",
              "answer_key": "HOLD", "approval": "NONE"}
    sha = digest(packet)
    events = []
    specs = [
        ("P1", "GROK", "fixture-grok", "fixture-controller-grok", "ACCEPT", ["DEMO-SRC-A"], False),
        ("SOURCE_CHECK", "CHATGPT", "fixture-chatgpt", "fixture-controller-chatgpt", "HOLD", ["DEMO-SRC-B"], False),
        ("P2", "CLAUDE", "fixture-claude", "fixture-controller-claude", "HOLD", ["DEMO-SRC-A", "DEMO-SRC-B"], True),
        ("P3", "GROK", "fixture-grok", "fixture-controller-grok", "HOLD", ["DEMO-SRC-B"], True),
    ]
    for i, (phase, role, principal, controller, decision, sources, exposed) in enumerate(specs):
        event = {"id": f"DEMO-EVENT-{i+1}", "phase": phase, "role": role,
                 "principal_claim": principal, "controller_claim": controller,
                 "time": f"2026-11-22T15:{i*2:02d}:00Z", "case_id": packet["case_id"],
                 "packet_sha256": sha, "decision": decision, "evidence_ids": sources,
                 "peer_exposure": exposed}
        event["receipt_sha256"] = digest(event)
        events.append(event)
    witness = {"role": "WITNESS", "principal_claim": "fixture-witness",
               "controller_claim": "fixture-controller-witness", "packet_sha256": sha,
               "event_receipts": {e["id"]: e["receipt_sha256"] for e in events},
               "authority_effect": "NONE"}
    witness["receipt_sha256"] = digest(witness)
    return {"schema": SCHEMA, "packet": packet, "packet_sha256": sha,
            "events": events, "witness": witness}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="run fixed local synthetic case")
    args = parser.parse_args()
    if not args.demo:
        parser.error("only --demo is supported; no real-data intake")
    print(json.dumps(validate(demo()), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
