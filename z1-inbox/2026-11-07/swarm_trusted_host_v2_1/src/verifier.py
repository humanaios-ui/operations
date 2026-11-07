"""Public-key-only proof verification. No writer signing key is loaded here.

This verifies consistency of signed host observations, NOT host trustworthiness or
actor intent. The root must be a read-only host-created snapshot in production.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .pins import file_sha256
from .writer import GENESIS, canonical, digest, ident, sha_bytes, parse_utc, EvidenceError


def _safe_bytes(path):
    from .writer import open_read_no_follow
    p = Path(path).absolute()
    for seg in (p, *p.parents):
        if seg.is_symlink():
            raise EvidenceError("SYMLINK_EVIDENCE_REJECTED")
    try:
        return open_read_no_follow(p)
    except OSError as exc:
        raise EvidenceError("EVIDENCE_READ_FAILURE") from exc


def _json_file(path):
    raw = _safe_bytes(path)
    try:
        item = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise EvidenceError("EVIDENCE_INVALID_JSON") from exc
    if canonical(item) != raw:
        raise EvidenceError("NON_CANONICAL_EVIDENCE")
    return item, raw


def verify(plan: dict, pinned_plan_sha256: str, public_key_bytes: bytes, root: Path):
    """Return trusted host observation or raise EvidenceError; no private keys."""
    if digest(plan) != pinned_plan_sha256:
        raise EvidenceError("PLAN_HASH_CHANGED")
    pins = plan.get("protocol_pins")
    if not isinstance(pins, dict) or pins.get("verifier_sha256") != file_sha256(__file__):
        raise EvidenceError("VERIFIER_CODE_NOT_PINNED")
    if not isinstance(public_key_bytes, bytes) or len(public_key_bytes) != 32:
        raise EvidenceError("PUBKEY_INVALID")
    if sha_bytes(public_key_bytes) != plan.get("writer_pubkey_sha256"):
        raise EvidenceError("PUBLIC_KEY_NOT_PINNED")
    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    except ValueError as exc:
        raise EvidenceError("PUBLIC_KEY_NOT_ED25519") from exc
    ep = Path(root).absolute() / ident(plan["run_id"]) / ident(plan["episode_id"])
    if ep.is_symlink() or not ep.is_dir() or ep.parent.is_symlink():
        raise EvidenceError("EPISODE_NOT_TRUSTED")
    if {p.name for p in ep.iterdir()} != {"events", "artifacts", "snapshot.json"}:
        raise EvidenceError("EPISODE_CONTAINS_UNEXPECTED_FILES")
    snapshot, _ = _json_file(ep / "snapshot.json")
    if not isinstance(snapshot, dict) or set(snapshot) != {"payload", "signature_ed25519_b64"}:
        raise EvidenceError("RECEIPT_SCHEMA_INVALID")
    payload = snapshot["payload"]
    expected = {"schema", "run_id", "episode_id", "plan_sha256", "writer_pubkey_sha256",
                "event_count", "tip_sha256", "tool_status", "artifact_sha256", "actor_id",
                "request_id", "nonce", "finalized_utc", "protocol_pins_sha256"}
    if not isinstance(payload, dict) or set(payload) != expected:
        raise EvidenceError("RECEIPT_PAYLOAD_INVALID")
    try:
        sig = base64.b64decode(snapshot["signature_ed25519_b64"], validate=True)
        public_key.verify(sig, canonical(payload))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise EvidenceError("UNAUTHENTICATED_SIGNATURE") from exc
    if (payload["schema"] != "humanaios.tool_receipt.v2"
        or (payload["run_id"], payload["episode_id"], payload["plan_sha256"], payload["writer_pubkey_sha256"])
        != (plan["run_id"], plan["episode_id"], pinned_plan_sha256, plan["writer_pubkey_sha256"])):
        raise EvidenceError("RECEIPT_SCOPE_MISMATCH")
    if payload["protocol_pins_sha256"] != digest(plan["protocol_pins"]):
        raise EvidenceError("RECEIPT_PINS_MISMATCH")
    if not isinstance(payload["event_count"], int) or payload["event_count"] not in (1, 3):
        raise EvidenceError("RECEIPT_EVENT_COUNT_INVALID")
    if not isinstance(payload["nonce"], str) or len(payload["nonce"]) != 32:
        raise EvidenceError("NONCE_INVALID")
    ident(payload["request_id"])
    if payload["actor_id"] != "A":
        raise EvidenceError("ACTOR_MISMATCH")
    if payload["tool_status"] not in {"COMPLETED", "NO_ATTEMPT", "FAILED"}:
        raise EvidenceError("STATUS_INVALID")
    events_dir = ep / "events"
    names = {p.name for p in events_dir.iterdir()}
    if len(names) != payload["event_count"] or any(len(n) != 69 or not n.endswith(".json") for n in names):
        raise EvidenceError("EVENT_CHAIN_GAP_OR_EXTRA_EVENT")
    # Follow the SIGNED tip backwards by content hash; never trust a
    # caller-named tool_event.json file or unsigned sequence listing.
    cursor = payload["tip_sha256"]
    events_reverse = []
    visited = set()
    keys = {"schema", "sequence", "run_id", "episode_id", "plan_sha256", "kind", "status", "actor_id",
            "request_id", "nonce", "artifact_sha256", "observed_utc", "previous_event_hash"}
    for expected_seq in range(payload["event_count"], 0, -1):
        filename = cursor + ".json"
        if filename not in names or filename in visited:
            raise EvidenceError("EVENT_CHAIN_GAP_OR_EXTRA_EVENT")
        item, raw = _json_file(events_dir / filename)
        if sha_bytes(raw) != cursor:
            raise EvidenceError("CONTENT_ADDRESS_HASH_MISMATCH")
        if not isinstance(item, dict) or set(item) != keys:
            raise EvidenceError("EVENT_SCHEMA_INVALID")
        if item["schema"] != "humanaios.tool_event.v2" or item["sequence"] != expected_seq:
            raise EvidenceError("EVENT_SEQUENCE_INVALID")
        if (item["run_id"], item["episode_id"], item["plan_sha256"]) != (
            plan["run_id"], plan["episode_id"], pinned_plan_sha256):
            raise EvidenceError("CROSS_EPISODE_EVENT")
        if (item["actor_id"], item["request_id"], item["nonce"]) != (
            payload["actor_id"], payload["request_id"], payload["nonce"]):
            raise EvidenceError("EVENT_REQUEST_ID_MISMATCH")
        parse_utc(item["observed_utc"], "EVENT_TIMESTAMP_INVALID")
        visited.add(filename)
        cursor = item["previous_event_hash"]
        events_reverse.append(item)
    if cursor != GENESIS or visited != names:
        raise EvidenceError("BROKEN_EVENT_CHAIN")
    tip = payload["tip_sha256"]
    events = list(reversed(events_reverse))
    window_start = parse_utc(plan["window"]["not_before"], "WINDOW_INVALID")
    window_end = parse_utc(plan["window"]["not_after"], "WINDOW_INVALID")
    stamps = [parse_utc(e["observed_utc"], "EVENT_TIMESTAMP_INVALID") for e in events]
    stamps.append(parse_utc(payload["finalized_utc"], "EVENT_TIMESTAMP_INVALID"))
    if any(not (window_start <= s <= window_end) for s in stamps):
        raise EvidenceError("EVENT_OUTSIDE_WINDOW")
    if any(later < earlier for earlier, later in zip(stamps, stamps[1:])):
        raise EvidenceError("EVENT_TIMESTAMP_ORDER")
    if events[-1]["kind"] != "SNAPSHOT_FINALIZED" or events[-1]["status"] != payload["tool_status"]:
        raise EvidenceError("FREEZE_EVENT_CONFLICT")
    if events[-1]["artifact_sha256"] != payload["artifact_sha256"]:
        raise EvidenceError("FREEZE_ARTIFACT_MISMATCH")
    if payload["event_count"] == 1:
        if payload["tool_status"] != "NO_ATTEMPT" or payload["artifact_sha256"] is not None:
            raise EvidenceError("SPURIOUS_NO_REQUEST_SUCCESS")
    else:
        first, second = events[:2]
        if first["kind"] != "REQUEST_RECORDED" or first["status"] not in {"ACCEPTED", "REJECTED"}:
            raise EvidenceError("REQUEST_EVENT_INVALID")
        if second["kind"] != "WRITE_RESULT" or second["status"] != payload["tool_status"]:
            raise EvidenceError("WRITE_RESULT_EVENT_INVALID")
        if second["artifact_sha256"] != payload["artifact_sha256"]:
            raise EvidenceError("WRITE_EVENT_HASH_CONFLICT")
        if (first["status"] == "REJECTED") != (second["status"] == "NO_ATTEMPT"):
            raise EvidenceError("INVALID_WRITE_STATE_TRANSITION")
    artifact_dir = ep / "artifacts"
    filename = plan["task"]["artifact_id"] + ".json"
    artifact_names = [p.name for p in artifact_dir.iterdir()]
    if payload["tool_status"] == "COMPLETED":
        if artifact_names != [filename]:
            raise EvidenceError("ATTESTED_ARTIFACT_MISSING_OR_EXTRA")
        file_content = _safe_bytes(artifact_dir / filename)
        if sha_bytes(file_content) != payload["artifact_sha256"]:
            raise EvidenceError("ARTIFACT_TAMPER_DETECTED")
        try:
            doc = json.loads(file_content)
        except ValueError as exc:
            raise EvidenceError("ARTIFACT_NOT_JSON") from exc
        if canonical(doc) != file_content or not isinstance(doc, dict) or set(doc) != {"artifact_id", "value"} or doc["artifact_id"] != plan["task"]["artifact_id"]:
            raise EvidenceError("ARTIFACT_CONTENT_INVALID")
    else:
        if artifact_names or payload["artifact_sha256"] is not None:
            raise EvidenceError("UNATTESTED_ARTIFACT_EXISTS")
    return {
        "proof_status": "VERIFIED_HOST_RECEIPT", "tool_status": payload["tool_status"],
        "run_id": plan["run_id"], "episode_id": plan["episode_id"],
        "artifact_sha256": payload["artifact_sha256"], "event_count": payload["event_count"],
        "event_tip": tip, "actor_id": payload["actor_id"], "request_id": payload["request_id"],
        "nonce": payload["nonce"], "artifact_dir": artifact_dir,
        "protocol_pins_sha256": payload["protocol_pins_sha256"],
        "authority": "NOT_ASSESSED", "os_isolation": "NOT_ASSESSED",
        # Route binding only. Same-UID peers are not distinguished; needs an OS-principal access test.
        "actor_id_authenticated": "UNKNOWN",
    }
