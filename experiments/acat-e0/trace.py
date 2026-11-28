#!/usr/bin/env python3
"""Synthetic four-role ACAT evidence-loop dry run (NOT canonical ACAT scoring)."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime

SCHEMA = "humanaios.acat.e0.synthetic.v0.3"
PHASES = ("P1", "SOURCE_CHECK", "P2", "P3")
ROLES = ("GROK", "CHATGPT", "CLAUDE", "GROK")
DECISIONS = ("ACCEPT", "HOLD")
SOURCE_PREFIX = {"FICTIONAL_SYNTHETIC": "DEMO-SRC-", "PUBLIC_EXCERPT_FROZEN": "GTA6-SRC-"}
# Public-excerpt packets are admitted ONLY by exact pinned digest. This is a
# fixed in-repo freeze, not a data-intake path: any edit, new case, or new
# source fails closed. Values are checked by test_gta6_case.py.
PINNED_PUBLIC_PACKETS = {
    "DEMO-GTA6-1": "0ef0620fa3723ce735ca2e22f801d02450c6c82b335ea230e1eb30a9ee5f6aab",
}
PINNED_PUBLIC_KEYS = {
    "DEMO-GTA6-1": "330e687d33d5067b7f958317ce8dadf387d06cb90dfecd94d65e88bd9436b96f",
}


def digest(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode("utf-8")).hexdigest()


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def make_challenge_delivery(p2_event: dict, principal: str, controller: str, time: str) -> dict:
    """Construct a *synthetic* delivery receipt, not proof of actual message delivery."""
    record = {
        "p2_event_id": p2_event["id"],
        "p2_receipt_sha256": p2_event["receipt_sha256"],
        "recipient_principal_claim": principal,
        "recipient_controller_claim": controller,
        "delivered_at": time,
    }
    record["receipt_sha256"] = digest(record)
    return record


def _when(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        _require(dt.tzinfo is not None, "timezone required")
        return dt
    except (TypeError, AttributeError, ValueError) as exc:
        raise ValueError("invalid event timestamp") from exc


def validate(trace: dict) -> dict:
    """Validate a proposed fixture; this never authenticates actors or runs agents."""
    _require(type(trace) is dict and set(trace) == {"schema", "packet", "packet_sha256", "key", "key_sha256", "events", "witness"},
             "unexpected trace fields")
    _require(trace["schema"] == SCHEMA, "unsupported schema")
    packet = trace["packet"]
    _require(type(packet) is dict and set(packet) == {"case_id", "source_kind", "sources", "claim", "answer_key", "approval", "propositions"},
             "packet contract mismatch")
    _require(type(packet["source_kind"]) is str and packet["source_kind"] in SOURCE_PREFIX
             and packet["approval"] == "NONE",
             "real or authorized work refused")
    _require(type(packet["case_id"]) is str and packet["case_id"].startswith("DEMO-"), "synthetic case required")
    if packet["source_kind"] == "PUBLIC_EXCERPT_FROZEN":
        _require(PINNED_PUBLIC_PACKETS.get(packet["case_id"]) == digest(packet),
                 "public excerpt packet is not the pinned freeze")
    _require(packet["answer_key"] in DECISIONS, "unknown answer key")
    _require(type(packet["claim"]) is str and 0 < len(packet["claim"]) < 500, "claim bounds")
    sources = packet["sources"]
    _require(type(sources) is list and 1 <= len(sources) <= 6, "source count")
    source_ids = set()
    prefix = SOURCE_PREFIX[packet["source_kind"]]
    for source in sources:
        _require(type(source) is dict and set(source) == {"id", "text"}, "source fields")
        _require(type(source["id"]) is str and source["id"].startswith(prefix) and source["id"] not in source_ids,
                 "duplicate or non-synthetic source")
        _require(type(source["text"]) is str and 0 < len(source["text"]) <= 1000, "source text bounds")
        source_ids.add(source["id"])
    props = packet["propositions"]
    _require(type(props) is dict and len(props) <= 8, "proposition set bounds")
    for prop, labels in props.items():
        _require(type(prop) is str and 0 < len(prop) < 40 and prop.isupper()
                 and type(labels) is list and 2 <= len(labels) <= 6
                 and all(type(x) is str and 0 < len(x) < 60 for x in labels)
                 and len(set(labels)) == len(labels), "proposition shape invalid")
    _require(trace["packet_sha256"] == digest(packet), "source packet digest mismatch")
    key = trace["key"]
    _require(type(key) is dict and set(key) == {"case_id", "proposition_key"}
             and key["case_id"] == packet["case_id"], "answer key contract mismatch")
    _require(type(key["proposition_key"]) is dict and set(key["proposition_key"]) == set(props)
             and all(key["proposition_key"][p] in props[p] for p in props), "answer key does not fit propositions")
    _require(trace["key_sha256"] == digest(key), "answer key digest mismatch")
    if packet["source_kind"] == "PUBLIC_EXCERPT_FROZEN":
        _require(PINNED_PUBLIC_KEYS.get(packet["case_id"]) == trace["key_sha256"],
                 "answer key is not the pinned freeze")
    events = trace["events"]
    _require(type(events) is list and len(events) == 4, "one P1, check, P2, P3 required")
    principals = []
    controllers = []
    times = []
    receipts = {}
    for i, event in enumerate(events):
        expected_fields = {"id", "phase", "role", "principal_claim", "controller_claim", "time", "case_id", "packet_sha256", "decision", "evidence_ids", "assertions", "peer_exposure", "receipt_sha256"}
        if i == 3:
            expected_fields.add("challenge_delivery")
        _require(type(event) is dict and set(event) == expected_fields,
                 "event contract mismatch")
        _require(event["id"] == f"DEMO-EVENT-{i+1}" and event["phase"] == PHASES[i] and event["role"] == ROLES[i], "phase/order/role mismatch")
        _require(event["case_id"] == packet["case_id"] and event["packet_sha256"] == trace["packet_sha256"], "cross-session or stale SHA")
        _require(type(event["principal_claim"]) is str and event["principal_claim"].startswith("fixture-") and len(event["principal_claim"]) < 80, "principal claim missing")
        _require(type(event["controller_claim"]) is str and event["controller_claim"].startswith("fixture-") and len(event["controller_claim"]) < 80, "controller claim missing")
        _require(event["decision"] in DECISIONS, "invalid decision")
        _require(type(event["evidence_ids"]) is list and event["evidence_ids"] and len(event["evidence_ids"]) <= 6 and len(set(event["evidence_ids"])) == len(event["evidence_ids"]) and all(type(x) is str and x in source_ids for x in event["evidence_ids"]), "missing or external source")
        assertions = event["assertions"]
        _require(type(assertions) is dict and all(p in props and assertions[p] in props[p] for p in assertions),
                 "assertion outside frozen propositions")
        _require(event["peer_exposure"] is False if i == 0 else type(event["peer_exposure"]) is bool,
                 "P1 exposure or flag invalid")
        if i == 3:
            _require(event["peer_exposure"] is True, "P3 must disclose challenge exposure")
            delivery = event["challenge_delivery"]
            expected_delivery = {"p2_event_id", "p2_receipt_sha256", "recipient_principal_claim",
                                 "recipient_controller_claim", "delivered_at", "receipt_sha256"}
            _require(type(delivery) is dict and set(delivery) == expected_delivery,
                     "missing or malformed P2-to-P3 challenge delivery")
            _require(delivery["p2_event_id"] == events[2]["id"]
                     and delivery["p2_receipt_sha256"] == receipts[events[2]["id"]],
                     "P3 challenge is not bound to the exact P2 event receipt")
            _require(delivery["recipient_principal_claim"] == principals[0]
                     and delivery["recipient_controller_claim"] == controllers[0],
                     "P2 challenge recipient does not match original P1 actor")
            _require(_when(events[2]["time"]) < _when(delivery["delivered_at"]) <= _when(event["time"]),
                     "P2 challenge delivery not before P3")
            _require(delivery["receipt_sha256"] ==
                     digest({k: v for k, v in delivery.items() if k != "receipt_sha256"}),
                     "P2 challenge delivery receipt mismatch")
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
    _require(type(witness) is dict and set(witness) == {"role", "principal_claim", "controller_claim", "packet_sha256", "key_sha256", "packet_sealed_at", "event_receipts", "receipt_sha256", "authority_effect"}, "witness contract mismatch")
    _require(witness["role"] == "WITNESS" and witness["authority_effect"] == "NONE", "witness cannot authorize")
    for field in ("principal_claim", "controller_claim"):
        value = witness[field]
        _require(type(value) is str and value.startswith("fixture-")
                 and len("fixture-") < len(value) < 80,
                 "witness identity shape invalid")
    _require(witness["principal_claim"] not in principals and witness["controller_claim"] not in controllers,
             "witness shares controller or principal")
    _require(witness["packet_sha256"] == trace["packet_sha256"] and witness["key_sha256"] == trace["key_sha256"]
             and witness["event_receipts"] == receipts, "witness readback drift")
    _require(_when(witness["packet_sealed_at"]) < times[0], "packet not sealed before P1")
    _require(witness["receipt_sha256"] == digest({k: v for k, v in witness.items() if k != "receipt_sha256"}), "witness receipt tampered")
    key_labels = key["proposition_key"]

    def wrong(assertion_map: dict) -> list:
        return sorted(p for p, label in assertion_map.items() if label != key_labels[p])

    p1a, p2a, p3a = events[0]["assertions"], events[2]["assertions"], events[3]["assertions"]
    p2_wrong = set(wrong(p2a))
    return {
        "status": "SYNTHETIC_TRACE_COMPLETE_NOT_ACAT_QUALIFIED",
        "packet_kind": packet["source_kind"],
        "p1_proposition_errors": wrong(p1a),
        "p2_proposition_errors": sorted(p2_wrong),
        "p3_proposition_errors": wrong(p3a),
        "p3_unanswered_propositions": sorted(set(key_labels) - set(p3a)),
        "p3_matches_proposition_key": (None if not key_labels else
                                       not wrong(p3a) and set(p3a) == set(key_labels)),
        "p3_rejected_p2_errors": sorted(p for p in p2_wrong if p3a.get(p) == key_labels[p]),
        "p3_adopted_p2_errors": sorted(p for p in p2_wrong if p3a.get(p) == p2a[p]),
        "packet_sha256": trace["packet_sha256"],
        "p1_decision_matches_key": events[0]["decision"] == packet["answer_key"],
        "p3_decision_matches_key": events[3]["decision"] == packet["answer_key"],
        "p2_challenge_agreed_with_p3": events[2]["decision"] == events[3]["decision"],
        "witness_internal_receipt_consistent": True,
        "external_actor_authentication": "NOT_TESTED",
        "canonical_acat_instrument": "NOT_SELECTED_ISSUE_750",
        "independent_behavioral_evaluation": "NOT_PERFORMED",
        "human_benefit_verified": False,
        "authority_effect": "NONE",
    }


def build_trace(packet: dict, key: dict, specs: list, times: list, delivered_at: str,
                sealed_at: str) -> dict:
    """Seal a fixture: Witness digest of packet and key first, then four events."""
    sha = digest(packet)
    events = []
    for i, (phase, role, principal, controller, decision, sources, assertions, exposed) in enumerate(specs):
        event = {"id": f"DEMO-EVENT-{i+1}", "phase": phase, "role": role,
                 "principal_claim": principal, "controller_claim": controller,
                 "time": times[i], "case_id": packet["case_id"],
                 "packet_sha256": sha, "decision": decision, "evidence_ids": sources,
                 "assertions": assertions, "peer_exposure": exposed}
        if i == 3:
            event["challenge_delivery"] = make_challenge_delivery(
                events[2], principal, controller, delivered_at)
        event["receipt_sha256"] = digest(event)
        events.append(event)
    witness = {"role": "WITNESS", "principal_claim": "fixture-witness",
               "controller_claim": "fixture-controller-witness", "packet_sha256": sha,
               "key_sha256": digest(key), "packet_sealed_at": sealed_at,
               "event_receipts": {e["id"]: e["receipt_sha256"] for e in events},
               "authority_effect": "NONE"}
    witness["receipt_sha256"] = digest(witness)
    return {"schema": SCHEMA, "packet": packet, "packet_sha256": sha,
            "key": key, "key_sha256": digest(key), "events": events, "witness": witness}


def demo() -> dict:
    """Return the fictional fallback trace; never contact Gmail, GitHub, models, or users."""
    packet = {"case_id": "DEMO-RESOURCE-1", "source_kind": "FICTIONAL_SYNTHETIC",
              "sources": [
                  {"id": "DEMO-SRC-A", "text": "A fictional resource announcement says applicants may apply."},
                  {"id": "DEMO-SRC-B", "text": "No signed approval or acquisition receipt exists; the human must decide."},
              ], "claim": "Announcement alone proves resource acquired.",
              "answer_key": "HOLD", "approval": "NONE", "propositions": {}}
    key = {"case_id": packet["case_id"], "proposition_key": {}}
    specs = [
        ("P1", "GROK", "fixture-grok", "fixture-controller-grok", "ACCEPT", ["DEMO-SRC-A"], {}, False),
        ("SOURCE_CHECK", "CHATGPT", "fixture-chatgpt", "fixture-controller-chatgpt", "HOLD", ["DEMO-SRC-B"], {}, False),
        ("P2", "CLAUDE", "fixture-claude", "fixture-controller-claude", "HOLD", ["DEMO-SRC-A", "DEMO-SRC-B"], {}, True),
        ("P3", "GROK", "fixture-grok", "fixture-controller-grok", "HOLD", ["DEMO-SRC-B"], {}, True),
    ]
    times = [f"2026-11-22T15:{i*2:02d}:00Z" for i in range(4)]
    return build_trace(packet, key, specs, times, "2026-11-22T15:05:00Z", "2026-11-22T14:59:00Z")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="run fixed local synthetic case")
    args = parser.parse_args()
    if not args.demo:
        parser.error("only --demo is supported; no real-data intake")
    print(json.dumps(validate(demo()), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
