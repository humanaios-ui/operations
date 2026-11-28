"""HARMONIC-0: deterministic, *simulated* local-first Witness router.

No actual model, MCP tool, network connection, provider key, or privileged action
is invoked here. This module is deliberately separate from the MCP service.
Receipts record routing facts, not prompts. Hash chaining detects accidental
changes; it is unsigned and is *not* independent attestation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import threading
from typing import Any

SCHEMA = "humanaios.harmonic0.routing_receipt.v0.1"
POLICY = "HARMONIC0-LOCAL-FIRST-Z1-v0.1"
SIMULATED_CLOUD_SCOPE = "HARMONIC0_SIMULATED_CLOUD_ONLY"
GENESIS = "0" * 64
NONPUBLIC_DIGEST = "NONPUBLIC_PAYLOAD_NOT_FINGERPRINTED"
ALLOWED_TASKS = frozenset({
    "haios_status", "haios_read_document", "haios_self_model",
    "haios_find_resources", "haios_talk",
})
ROUTES = frozenset({"LOCAL", "CLOUD", "UNAVAILABLE"})
PRIVACY = frozenset({"PUBLIC", "PRIVATE", "UNKNOWN"})


@dataclass(frozen=True)
class SimulatedEndpoint:
    """Deterministic endpoint stand-in; never loads a model or opens a socket."""
    name: str

    def process(self, *, should_fail: bool = False) -> str:
        if self.name == "UNAVAILABLE":
            return "SIMULATED_ABSTENTION"
        return "SIMULATED_FAILURE" if should_fail else "SIMULATED_SUCCESS"


ENDPOINTS = {name: SimulatedEndpoint(name) for name in sorted(ROUTES)}
MAX_JOURNAL_BYTES = 1_000_000
MAX_RECEIPTS = 1000


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class CloudGrant:
    """Explicitly *synthetic* operator intent, bound to this exact public text.

    NOT a credential, user authentication, external approval, or remote grant.
    HARMONIC-0 has no route that sends bytes over a network.
    """
    request_id: str
    payload_sha256: str
    scope: str = SIMULATED_CLOUD_SCOPE
    operator_confirmed: bool = True


@dataclass(frozen=True)
class RouteRequest:
    request_id: str
    text: str
    privacy: str
    task: str
    local_capable: bool = True
    local_healthy: bool = True
    cloud_healthy: bool = True
    # Simulated runtime failure after the local endpoint has been attempted.
    local_fails_during_call: bool = False
    cloud_fails_during_call: bool = False
    grant: CloudGrant | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.request_id):
            raise ValueError("Invalid bounded request ID")
        if not isinstance(self.text, str) or not 1 <= len(self.text) <= 4000:
            raise ValueError("Invalid bounded request text")
        if self.privacy not in PRIVACY:
            raise ValueError("Unknown privacy value")
        if not isinstance(self.task, str) or len(self.task) > 80:
            raise ValueError("Invalid tool name")
        if any(type(x) is not bool for x in (
            self.local_capable, self.local_healthy, self.cloud_healthy,
            self.local_fails_during_call, self.cloud_fails_during_call,
        )):
            raise ValueError("Runtime flags must be boolean")
        if self.grant is not None and not isinstance(self.grant, CloudGrant):
            raise ValueError("Invalid grant")


def permitted_cloud(meta: dict[str, Any]) -> bool:
    grant = meta.get("grant")
    return bool(
        meta["privacy"] == "PUBLIC"
        and isinstance(grant, dict)
        and grant.get("request_id") == meta["request_id"]
        and grant.get("payload_sha256") == meta["payload_sha256"]
        and grant.get("scope") == SIMULATED_CLOUD_SCOPE
        and grant.get("operator_confirmed") is True
    )


def evaluate(meta: dict[str, Any]) -> dict[str, Any]:
    """Pure, independently replayable policy and simulation decision.

    Metadata is explicit; no LLM privacy classifier is granted authority.
    Real provider fallback is impossible in this milestone.
    """
    if meta["task"] not in ALLOWED_TASKS:
        return _decision("UNAVAILABLE", "TOOL_NOT_ALLOWLISTED", [], False)
    if meta["privacy"] == "UNKNOWN":
        return _decision("UNAVAILABLE", "PRIVACY_CLASSIFICATION_UNKNOWN", [], False)
    cloud_ok = permitted_cloud(meta)
    attempts: list[dict[str, str]] = []
    if meta["local_capable"] and meta["local_healthy"]:
        if not meta["local_fails_during_call"]:
            attempts.append({"endpoint": "LOCAL", "result": ENDPOINTS["LOCAL"].process()})
            return _decision("LOCAL", "LOCAL_DEFAULT", attempts, False)
        attempts.append({"endpoint": "LOCAL", "result": ENDPOINTS["LOCAL"].process(should_fail=True)})
        local_reason = "LOCAL_RUNTIME_FAILURE"
    else:
        local_reason = ("LOCAL_CAPABILITY_INSUFFICIENT" if not meta["local_capable"]
                        else "LOCAL_RUNTIME_UNAVAILABLE")
    if not cloud_ok:
        reason = ("PRIVATE_CLOUD_BLOCKED" if meta["privacy"] == "PRIVATE"
                  else "CLOUD_GRANT_MISSING_OR_MISMATCHED")
        return _decision("UNAVAILABLE", local_reason + ":" + reason, attempts, False)
    if not meta["cloud_healthy"]:
        return _decision("UNAVAILABLE", local_reason + ":CLOUD_UNAVAILABLE", attempts, True)
    if meta["cloud_fails_during_call"]:
        attempts.append({"endpoint": "CLOUD", "result": ENDPOINTS["CLOUD"].process(should_fail=True)})
        return _decision("UNAVAILABLE", local_reason + ":CLOUD_RUNTIME_FAILURE", attempts, True)
    attempts.append({"endpoint": "CLOUD", "result": ENDPOINTS["CLOUD"].process()})
    return _decision("CLOUD", local_reason + ":EXPLICIT_SIMULATED_CLOUD_PERMISSION", attempts, True)


def _decision(route: str, reason: str, attempts: list[dict[str, str]],
              cloud_permission_valid: bool) -> dict[str, Any]:
    assert route in ROUTES
    return {
        "route": route,
        "endpoint_result": ENDPOINTS[route].process(),
        "reason_code": reason,
        "attempts": attempts,
        "cloud_permission_valid": cloud_permission_valid,
        "simulated_output_sha256": sha256(canonical({
            "route": route, "reason": reason,
            "result": "SIMULATED_ONLY_NO_MODEL_OR_NETWORK",
        })),
        "authority_effect": "NONE",
        "execution_kind": "SIMULATED_NO_NETWORK_NO_TOOL_INVOCATION",
    }


def metadata(req: RouteRequest) -> dict[str, Any]:
    # A plain SHA-256 of a small private prompt enables offline guessing.
    # Neither private nor unclassified text is fingerprinted in receipts.
    digest = (sha256(req.text.encode("utf-8")) if req.privacy == "PUBLIC"
              else NONPUBLIC_DIGEST)
    return {
        "request_id": req.request_id,
        "payload_sha256": digest,
        "privacy": req.privacy,
        "task": req.task,
        "local_capable": req.local_capable,
        "local_healthy": req.local_healthy,
        "cloud_healthy": req.cloud_healthy,
        "local_fails_during_call": req.local_fails_during_call,
        "cloud_fails_during_call": req.cloud_fails_during_call,
        "grant": ({
            "request_id": req.grant.request_id,
            "payload_sha256": req.grant.payload_sha256,
            "scope": req.grant.scope,
            "operator_confirmed": req.grant.operator_confirmed,
        } if req.grant and req.privacy == "PUBLIC" else None),
    }


def simulate(req: RouteRequest) -> dict[str, Any]:
    """Run three *simulated* endpoint possibilities through the policy gate."""
    return evaluate(metadata(req))


def _validate_receipt(record: dict[str, Any], sequence: int, previous: str) -> str:
    if not isinstance(record, dict) or set(record) != {
        "schema", "policy_revision", "sequence", "previous_hash", "observed_utc",
        "request", "decision", "receipt_kind", "receipt_hash",
    }:
        raise ValueError("Malformed routing receipt")
    if (record["schema"] != SCHEMA or record["policy_revision"] != POLICY
            or record["sequence"] != sequence or record["previous_hash"] != previous
            or record["receipt_kind"] != "UNSIGNED_LOCAL_CHAIN_NOT_ATTESTATION"):
        raise ValueError("Routing receipt identity/chain mismatch")
    original_hash = record["receipt_hash"]
    if not isinstance(original_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", original_hash):
        raise ValueError("Routing receipt hash malformed")
    if sha256(canonical({k: v for k, v in record.items() if k != "receipt_hash"})) != original_hash:
        raise ValueError("Routing receipt hash mismatch")
    meta = record["request"]
    if not isinstance(meta, dict) or set(meta) != {
        "request_id", "payload_sha256", "privacy", "task", "local_capable",
        "local_healthy", "cloud_healthy", "local_fails_during_call",
        "cloud_fails_during_call", "grant",
    }:
        raise ValueError("Routing request metadata invalid")
    if (not isinstance(meta["request_id"], str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", meta["request_id"])
            or meta["privacy"] not in PRIVACY
            or not isinstance(meta["payload_sha256"], str)
            or not (re.fullmatch(r"[a-f0-9]{64}", meta["payload_sha256"])
                    if meta["privacy"] == "PUBLIC"
                    else meta["payload_sha256"] == NONPUBLIC_DIGEST)
            or (meta["privacy"] != "PUBLIC" and meta["grant"] is not None)
            or not isinstance(meta["task"], str)):
        raise ValueError("Routing request identifiers invalid")
    if any(type(meta[k]) is not bool for k in (
        "local_capable", "local_healthy", "cloud_healthy",
        "local_fails_during_call", "cloud_fails_during_call")):
        raise ValueError("Routing request runtime flags invalid")
    if record["decision"] != evaluate(meta):
        raise ValueError("Routing policy replay diverges from recorded decision")
    return original_hash


class ReceiptJournal:
    """Single-writer, append-only local JSONL; not tamper-resistant attestation.

    The lock is process-local. Do not share one journal among concurrent agents.
    A missing journal has no externally verifiable history, and this log cannot
    prove that an omitted earlier receipt did not exist.
    """
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def verify(self) -> dict[str, Any]:
        if self.path.is_symlink():
            raise ValueError("Symlink journal refused")
        if not self.path.exists():
            return {"valid": True, "count": 0, "head_hash": GENESIS}
        if not self.path.is_file() or self.path.stat().st_size > MAX_JOURNAL_BYTES:
            raise ValueError("Journal type/size invalid")
        lines = self.path.read_bytes().splitlines(keepends=True)
        if len(lines) > MAX_RECEIPTS:
            raise ValueError("Receipt count exceeded")
        previous, used_ids = GENESIS, set()
        for i, line in enumerate(lines, 1):
            if not line.endswith(b"\n") or len(line) > 8192:
                raise ValueError("Incomplete or overlong receipt")
            try:
                record = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                raise ValueError("Unreadable routing receipt") from None
            previous = _validate_receipt(record, i, previous)
            identifier = record["request"]["request_id"]
            if identifier in used_ids:
                raise ValueError("Duplicate request ID in receipt history")
            used_ids.add(identifier)
        return {"valid": True, "count": len(lines), "head_hash": previous}

    def append(self, req: RouteRequest, *, observed_utc: str | None = None) -> dict[str, Any]:
        with self._lock:
            state = self.verify()
            if state["count"] >= MAX_RECEIPTS:
                raise ValueError("Receipt limit reached")
            if self.path.exists():
                # A request ID is a one-use journal identity in this prototype.
                # Do not append first and discover a duplicate only on replay.
                for line in self.path.read_bytes().splitlines():
                    if json.loads(line)["request"]["request_id"] == req.request_id:
                        raise ValueError("Duplicate request ID in journal")
            timestamp = observed_utc or datetime.now(timezone.utc).isoformat()
            if not isinstance(timestamp, str) or not timestamp.endswith(("Z", "+00:00")):
                raise ValueError("Timestamp must be UTC")
            record = {
                "schema": SCHEMA,
                "policy_revision": POLICY,
                "sequence": state["count"] + 1,
                "previous_hash": state["head_hash"],
                "observed_utc": timestamp,
                "request": metadata(req),
                "decision": simulate(req),
                "receipt_kind": "UNSIGNED_LOCAL_CHAIN_NOT_ATTESTATION",
            }
            record["receipt_hash"] = sha256(canonical(record))
            # Avoid printing or persisting raw text; only digest plus metadata.
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.is_symlink():
                raise ValueError("Symlink journal refused")
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(self.path, flags, 0o600)
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    raise ValueError("Journal must be a regular file")
                data = canonical(record) + b"\n"
                if os.fstat(fd).st_size + len(data) > MAX_JOURNAL_BYTES:
                    raise ValueError("Journal size limit reached")
                if os.write(fd, data) != len(data):
                    raise OSError("Partial journal append")
                os.fsync(fd)
            finally:
                os.close(fd)
            return record
