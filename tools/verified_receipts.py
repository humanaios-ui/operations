"""Verified receipt resolver shared by HumanAIOS prototype consumers.

Authority effect: NONE.
Standing: Z1 prototype.

Security model:
- Consumers never trust their own booleans or raw receipt IDs.
- Receipt events must form an intact append-only hash chain.
- The chain head must match a separately pinned head hash.
- Receipt fields must match the exact consumer requirement.
- Stub/simulated/format-only verification methods are refused.
- Revoked receipts are refused.
- One-time receipts are refused after consumption.

Important: a pinned head must come from an independent/trusted channel. Supplying
an attacker-controlled event list and attacker-controlled head together does not
create trust.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import hashlib
import json


ZERO_HASH = "0" * 64

STRENGTH_RANK = {
    "OBSERVED": 1,
    "ATTESTED": 2,
    "CRYPTO_VERIFIED": 3,
}

DISALLOWED_METHODS = {
    "STUB",
    "SIMULATED",
    "FORMAT_ONLY",
    "SIMULATED_FETCH_HASH",
    "MOCK",
    "NONE",
}


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
                receipt=receipt,
                chain_head=self.pinned_head_hash,
            )

        if receipt.get("one_time") and receipt_id in self._consumed:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="RECEIPT_ALREADY_CONSUMED",
                receipt=receipt,
                chain_head=self.pinned_head_hash,
            )

        if receipt.get("verification_status") != "VERIFIED":
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="VERIFICATION_STATUS_NOT_VERIFIED",
                receipt=receipt,
                chain_head=self.pinned_head_hash,
            )

        method = str(receipt.get("verification_method", "")).upper()
        if not method or method in DISALLOWED_METHODS:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason=f"DISALLOWED_VERIFICATION_METHOD:{method or 'EMPTY'}",
                receipt=receipt,
                chain_head=self.pinned_head_hash,
            )

        strength = str(receipt.get("verification_strength", "")).upper()
        minimum = requirement.min_strength.upper()
        if strength not in STRENGTH_RANK or minimum not in STRENGTH_RANK:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="UNKNOWN_VERIFICATION_STRENGTH",
                receipt=receipt,
                chain_head=self.pinned_head_hash,
            )
        if STRENGTH_RANK[strength] < STRENGTH_RANK[minimum]:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason=f"INSUFFICIENT_STRENGTH:{strength}<{minimum}",
                receipt=receipt,
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
                    receipt=receipt,
                    chain_head=self.pinned_head_hash,
                )

        if requirement.issuer is not None and receipt.get("issuer") != requirement.issuer:
            return ReceiptResolution(
                valid=False,
                receipt_id=receipt_id,
                reason="ISSUER_MISMATCH",
                receipt=receipt,
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
                receipt=receipt,
                chain_head=self.pinned_head_hash,
            )

        return ReceiptResolution(
            valid=True,
            receipt_id=receipt_id,
            receipt=receipt,
            chain_head=self.pinned_head_hash,
        )


def append_receipt_event(path: str, event: Dict[str, Any]) -> str:
    """Append one receipt event using the NF-style hash-chain format.

    This function preserves integrity only. It does not decide whether a claimed
    verification is substantively true.
    """
    p = Path(path)
    events: List[Dict[str, Any]] = []
    if p.exists():
        events = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
        if events:
            existing_head = events[-1].get("hash")
            resolver = VerifiedReceiptResolver(events, existing_head)
            if resolver.chain_error is not None:
                raise ValueError(f"existing receipt ledger invalid: {resolver.chain_error}")

    prev = events[-1]["hash"] if events else ZERO_HASH
    seq = events[-1]["seq"] + 1 if events else 1

    body = dict(event)
    body["seq"] = seq
    body["prev_hash"] = prev
    body["hash"] = event_hash({k: v for k, v in body.items() if k != "hash"})

    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(body, sort_keys=True) + "\n")

    return body["hash"]


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
    """Read a receipt ledger and return (events, head_hash).

    Reading does not itself make the head trusted. Callers must compare the
    returned head with a head pinned through an independent channel.
    """
    p = Path(path)
    if not p.exists():
        return [], None
    events = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    head = events[-1].get("hash") if events else None
    return events, head
