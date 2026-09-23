#!/usr/bin/env python3
"""
Verified Receipt Resolver — v0.1
Builder v1.7 compliant · validation_tool
HumanAIOS · H-COLLAB-HARMONY-01

Resolve typed receipts from a separately pinned append-only hash chain.
The tool checks integrity, status, verification strength, and exact
subject/action/scope matching. It does not establish the underlying
real-world truth of a receipt.

Usage:
  python3 tools/verified_receipts.py --smoke-test
  python3 tools/verified_receipts.py --help
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import argparse
import fcntl
import hashlib
import json
import os
import re
import sys


TOOL_NAME = "verified_receipts"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "validation_tool"
TOOL_SESSION = "H-COLLAB-HARMONY-01"
TOOL_ZONE = 1

ZERO_HASH = "0" * 64

STRENGTH_RANK = {
    "OBSERVED": 1,
    "ATTESTED": 2,
    "CRYPTO_VERIFIED": 3,
}

ALLOWED_VERIFICATION_METHODS = {
    "BRIDGE_EVENT_HASH_CHAIN",
    "ED25519",
    "EXTERNAL_SHA256",
    "HARDWARE_ATTESTATION",
}

_RECEIPT_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def canonical_verification_method(value: Any) -> str:
    """Canonicalize a verification-method token before policy checks."""
    return str(value or "").strip().upper()


def valid_receipt_id(value: Any) -> bool:
    return isinstance(value, str) and bool(_RECEIPT_ID_RE.fullmatch(value))


def _canon(obj: Dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def event_hash(event_without_hash: Dict[str, Any]) -> str:
    return hashlib.sha256(_canon(event_without_hash)).hexdigest()


@dataclass(frozen=True)
class ReceiptRequirement:
    receipt_type: str
    subject: str
    action: str
    scope: str
    min_strength: str = "OBSERVED"
    issuer: Optional[str] = None
    authority_scope: Optional[str] = None


@dataclass(frozen=True)
class ReceiptResolution:
    valid: bool
    receipt_id: Optional[str] = None
    reason: Optional[str] = None
    receipt: Optional[Dict[str, Any]] = None
    chain_head: Optional[str] = None


class VerifiedReceiptResolver:
    """Resolve typed receipts from a pinned, hash-chained event stream."""

    def __init__(self, events: Iterable[Dict[str, Any]], pinned_head_hash: str):
        self.events = [dict(e) for e in events]
        self.pinned_head_hash = pinned_head_hash
        self.chain_error = self._verify_chain()
        self._receipts: Dict[str, Dict[str, Any]] = {}
        self._revoked: set[str] = set()
        self._consumed: set[str] = set()
        if self.chain_error is None:
            self._project()

    def _verify_chain(self) -> Optional[str]:
        if not self.events:
            return "EMPTY_RECEIPT_CHAIN"
        if not self.pinned_head_hash:
            return "MISSING_PINNED_HEAD"

        prev = ZERO_HASH
        prior_seq: Optional[int] = None

        for event in self.events:
            if event.get("prev_hash") != prev:
                return f"PREV_HASH_MISMATCH:{event.get('seq')}"

            seq = event.get("seq")
            if not isinstance(seq, int):
                return "INVALID_SEQUENCE"
            if prior_seq is not None and seq != prior_seq + 1:
                return f"SEQUENCE_GAP:{seq}"

            body = {k: v for k, v in event.items() if k != "hash"}
            expected = event_hash(body)
            if event.get("hash") != expected:
                return f"EVENT_HASH_MISMATCH:{seq}"

            prev = expected
            prior_seq = seq

        if prev != self.pinned_head_hash:
            return "PINNED_HEAD_MISMATCH"

        return None

    def _project(self) -> None:
        for event in self.events:
            event_type = event.get("type")
            receipt_id = event.get("receipt_id")
            if not receipt_id:
                continue

            if event_type == "RECEIPT_VERIFIED":
                self._receipts[receipt_id] = event
            elif event_type == "RECEIPT_REVOKED":
                self._revoked.add(receipt_id)
            elif event_type == "RECEIPT_CONSUMED":
                self._consumed.add(receipt_id)

    def resolve(
        self,
        receipt_id: str,
        requirement: ReceiptRequirement,
    ) -> ReceiptResolution:
        if self.chain_error is not None:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason=f"CHAIN_INVALID:{self.chain_error}",
                chain_head=self.pinned_head_hash,
            )

        receipt = self._receipts.get(receipt_id)
        if receipt is None:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="RECEIPT_NOT_FOUND",
                chain_head=self.pinned_head_hash,
            )

        if receipt_id in self._revoked:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="RECEIPT_REVOKED",
                receipt=dict(receipt),
                chain_head=self.pinned_head_hash,
            )

        if receipt.get("one_time") and receipt_id in self._consumed:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="RECEIPT_ALREADY_CONSUMED",
                receipt=dict(receipt),
                chain_head=self.pinned_head_hash,
            )

        if receipt.get("verification_status") != "VERIFIED":
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="VERIFICATION_STATUS_NOT_VERIFIED",
                receipt=dict(receipt),
                chain_head=self.pinned_head_hash,
            )

        if not valid_receipt_id(receipt_id):
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="INVALID_RECEIPT_ID",
                receipt=dict(receipt),
                chain_head=self.pinned_head_hash,
            )

        method = canonical_verification_method(receipt.get("verification_method"))
        if method not in ALLOWED_VERIFICATION_METHODS:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason=f"UNSUPPORTED_VERIFICATION_METHOD:{method or 'EMPTY'}",
                receipt=dict(receipt),
                chain_head=self.pinned_head_hash,
            )

        strength = str(receipt.get("verification_strength", "")).strip().upper()
        minimum = requirement.min_strength.strip().upper()
        if strength not in STRENGTH_RANK or minimum not in STRENGTH_RANK:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="UNKNOWN_VERIFICATION_STRENGTH",
                receipt=dict(receipt),
                chain_head=self.pinned_head_hash,
            )
        if STRENGTH_RANK[strength] < STRENGTH_RANK[minimum]:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason=f"INSUFFICIENT_STRENGTH:{strength}<{minimum}",
                receipt=dict(receipt),
                chain_head=self.pinned_head_hash,
            )

        checks = (
            ("receipt_type", requirement.receipt_type),
            ("subject", requirement.subject),
            ("action", requirement.action),
            ("scope", requirement.scope),
        )
        for field, expected in checks:
            if receipt.get(field) != expected:
                return ReceiptResolution(
                    valid=False,
                    receipt_id=receipt_id,
                    reason=f"{field.upper()}_MISMATCH",
                    receipt=dict(receipt),
                    chain_head=self.pinned_head_hash,
                )

        if requirement.issuer is not None and receipt.get("issuer") != requirement.issuer:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="ISSUER_MISMATCH",
                receipt=dict(receipt),
                chain_head=self.pinned_head_hash,
            )

        if (
            requirement.authority_scope is not None
            and receipt.get("authority_scope") != requirement.authority_scope
        ):
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="AUTHORITY_SCOPE_MISMATCH",
                receipt=dict(receipt),
                chain_head=self.pinned_head_hash,
            )

        return ReceiptResolution(
            valid=True,
            receipt_id=receipt_id,
            receipt=dict(receipt),
            chain_head=self.pinned_head_hash,
        )


@contextmanager
def ledger_lock(path: str, *, exclusive: bool = True):
    """Serialize ledger access with a sidecar advisory lock."""
    p = Path(path)
    lock_path = p.with_suffix(p.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _read_events_unlocked(p: Path) -> List[Dict[str, Any]]:
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def _verify_existing_chain(events: List[Dict[str, Any]]) -> Optional[str]:
    if not events:
        return None
    head = events[-1].get("hash")
    resolver = VerifiedReceiptResolver(events, head)
    if resolver.chain_error is not None:
        raise ValueError(f"existing receipt ledger invalid: {resolver.chain_error}")
    return head


def _append_event_unlocked(
    p: Path,
    events: List[Dict[str, Any]],
    event: Dict[str, Any],
) -> str:
    prev = events[-1]["hash"] if events else ZERO_HASH
    seq = events[-1]["seq"] + 1 if events else 1

    body = dict(event)
    body["seq"] = seq
    body["prev_hash"] = prev
    body["hash"] = event_hash({k: v for k, v in body.items() if k != "hash"})

    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(body, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return body["hash"]


def append_receipt_event(path: str, event: Dict[str, Any]) -> str:
    """Atomically append one event to the NF-style receipt hash chain."""
    p = Path(path)
    with ledger_lock(path, exclusive=True):
        events = _read_events_unlocked(p)
        _verify_existing_chain(events)
        return _append_event_unlocked(p, events, event)


def consume_receipt_atomic(
    path: str,
    *,
    receipt_id: str,
    requirement: ReceiptRequirement,
    expected_head_hash: str,
    consumed_by: str,
    subject: str,
) -> str:
    """Compare-and-consume a receipt while holding the ledger writer lock.

    The independently pinned expected head must still equal the ledger head at
    the instant of consumption. A concurrent append therefore causes a stale
    head failure instead of allowing replay or double-spend.
    """
    p = Path(path)
    with ledger_lock(path, exclusive=True):
        events = _read_events_unlocked(p)
        current_head = _verify_existing_chain(events)
        if current_head != expected_head_hash:
            raise ValueError("STALE_RECEIPT_HEAD")

        resolution = VerifiedReceiptResolver(events, expected_head_hash).resolve(
            receipt_id, requirement
        )
        if not resolution.valid:
            raise ValueError(
                f"RECEIPT_NOT_CONSUMABLE:{resolution.reason or 'UNKNOWN'}"
            )

        receipt = resolution.receipt or {}
        if not receipt.get("one_time"):
            raise ValueError("RECEIPT_NOT_ONE_TIME")

        return _append_event_unlocked(
            p,
            events,
            {
                "type": "RECEIPT_CONSUMED",
                "by": consumed_by,
                "receipt_id": receipt_id,
                "subject": subject,
            },
        )

def build_receipt_chain_for_testing(events: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], str]:
    """Testing helper: hash-chain supplied receipt event bodies."""
    chained: List[Dict[str, Any]] = []
    prev = ZERO_HASH
    for idx, raw in enumerate(events, start=1):
        body = dict(raw)
        body["seq"] = idx
        body["prev_hash"] = prev
        body["hash"] = event_hash({k: v for k, v in body.items() if k != "hash"})
        chained.append(body)
        prev = body["hash"]
    return chained, prev


def read_receipt_events(path: str) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Read a receipt ledger under a shared lock and return its local head.

    The returned head is an observation, not an independent trust anchor.
    """
    p = Path(path)
    with ledger_lock(path, exclusive=False):
        events = _read_events_unlocked(p)
        head = events[-1].get("hash") if events else None
        return events, head


# ── Builder v1.7 smoke test / entry point ────────────────────────────────────

def run_smoke_test() -> bool:
    """Exercise one valid and one invalid receipt resolution."""
    try:
        raw = [{
            "type": "RECEIPT_VERIFIED",
            "receipt_id": "smoke-r1",
            "receipt_type": "HARMONY_GATE",
            "subject": "dissent_preserved",
            "action": "ASSERT_GATE",
            "scope": "run:smoke",
            "issuer": "bridge-evidence-graph",
            "authority_scope": "NONE",
            "verification_status": "VERIFIED",
            "verification_strength": "OBSERVED",
            "verification_method": "BRIDGE_EVENT_HASH_CHAIN",
            "evidence_ref": "smoke:evidence",
            "one_time": False,
        }]
        events, head = build_receipt_chain_for_testing(raw)
        requirement = ReceiptRequirement(
            receipt_type="HARMONY_GATE",
            subject="dissent_preserved",
            action="ASSERT_GATE",
            scope="run:smoke",
            min_strength="OBSERVED",
        )
        good = VerifiedReceiptResolver(events, head).resolve("smoke-r1", requirement)
        assert good.valid, good

        bad = VerifiedReceiptResolver(events, ZERO_HASH).resolve("smoke-r1", requirement)
        assert not bad.valid and "PINNED_HEAD_MISMATCH" in (bad.reason or ""), bad

        print("smoke-test OK — pinned receipt resolution and mismatch refusal verified.")
        return True
    except Exception as exc:
        print(f"smoke-test FAIL — {exc}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve HumanAIOS typed receipts from a pinned append-only receipt chain."
    )
    parser.add_argument("--smoke-test", action="store_true", help="run self-test and exit")
    args = parser.parse_args()
    if args.smoke_test:
        raise SystemExit(0 if run_smoke_test() else 1)
    parser.print_help()


if __name__ == "__main__":
    main()
