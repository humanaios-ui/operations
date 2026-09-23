"""
OI-BRIDGE-01 Phase 1 — NF_LEDGER Writer

Appends events to append-only governance ledger.
Maintains hash chain for tamper evidence.
"""

import json
import hashlib
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class LedgerEntry:
    """Single entry in NF_LEDGER."""
    event_type: str
    payload: Dict[str, Any]
    hash: str  # SHA256 of (prior_hash | json(payload))
    timestamp: str  # ISO8601 UTC


class NFLedgerWriter:
    """Write events to append-only NF_LEDGER."""

    def __init__(self, ledger_path: str = ".claude/skills/pr-manager/nf_ledger.jsonl"):
        """
        Initialize ledger writer.

        Args:
            ledger_path: Path to ledger file
        """
        self.ledger_path = ledger_path
        self.prior_hash = ""  # Initialize with empty string for first entry

    def _compute_hash(self, entry_json: str) -> str:
        """
        Compute SHA256 of (prior_hash | entry_json).

        Args:
            entry_json: JSON string of entry

        Returns:
            SHA256 hex digest
        """
        combined = f"{self.prior_hash}{entry_json}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    def append_event(self, event_type: str, payload: Dict[str, Any]) -> LedgerEntry:
        """
        Append event to ledger.

        Args:
            event_type: Type of event (SIGNATURE_VALIDATION, MESSAGE_DELIVERY, etc.)
            payload: Event payload (dict)

        Returns:
            LedgerEntry with computed hash
        """
        now = datetime.now(timezone.utc).isoformat()

        # Create entry
        entry = {
            "event_type": event_type,
            **payload,
            "timestamp": now,
        }

        # Compute hash
        entry_json = json.dumps(entry, separators=(',', ':'), sort_keys=True)
        hash_value = self._compute_hash(entry_json)

        # Add hash to entry
        entry["hash"] = hash_value
        entry_json = json.dumps(entry, separators=(',', ':'), sort_keys=True)

        # Write to file
        try:
            with open(self.ledger_path, 'a') as f:
                f.write(entry_json + '\n')
                f.flush()
                os.fsync(f.fileno())  # Force disk write for ACID compliance
        except IOError as e:
            raise Exception(f"LEDGER_WRITE_FAILED: {e}")

        # Update prior hash for next entry
        self.prior_hash = hash_value

        return LedgerEntry(
            event_type=event_type,
            payload=payload,
            hash=hash_value,
            timestamp=now
        )

    def append_signature_validation(self, message_id: str, sender: str,
                                   result: str, key_id: str) -> LedgerEntry:
        """Log signature validation event."""
        return self.append_event("SIGNATURE_VALIDATION", {
            "message_id": message_id,
            "sender": sender,
            "result": result,
            "key_id": key_id,
        })

    def append_message_delivery(self, message_id: str, recipient: str,
                               visibility: str, epistemic: str) -> LedgerEntry:
        """Log message delivery event."""
        return self.append_event("MESSAGE_DELIVERY", {
            "message_id": message_id,
            "recipient": recipient,
            "visibility": visibility,
            "epistemic": epistemic,
        })

    def append_token_issued(self, token_id: str, issued_by: str, issued_to: str,
                           scope: str, expires_at: str) -> LedgerEntry:
        """Log token issuance event."""
        return self.append_event("TOKEN_ISSUED", {
            "token_id": token_id,
            "issued_by": issued_by,
            "issued_to": issued_to,
            "scope": scope,
            "expires_at": expires_at,
        })

    def append_token_consumed(self, token_id: str, consumed_by: str,
                             action: str) -> LedgerEntry:
        """Log token consumption event."""
        return self.append_event("TOKEN_CONSUMED", {
            "token_id": token_id,
            "consumed_by": consumed_by,
            "action": action,
        })

    def append_consequential_action(self, message_id: str, action: str,
                                   actor: str, token_consumed: Optional[str],
                                   result: str) -> LedgerEntry:
        """Log consequential action event."""
        payload = {
            "message_id": message_id,
            "action": action,
            "actor": actor,
            "result": result,
        }
        if token_consumed:
            payload["token_consumed"] = token_consumed

        return self.append_event("CONSEQUENTIAL_ACTION", payload)

    def append_escalation(self, message_id: str, reason: str,
                         disposition: str) -> LedgerEntry:
        """Log escalation to HUMAN_REQUIRED event."""
        return self.append_event("ESCALATION", {
            "message_id": message_id,
            "reason": reason,
            "disposition": disposition,
        })

    def append_disposition(self, message_id: str, decision: str,
                          decided_by: str) -> LedgerEntry:
        """Log Z2 disposition decision event."""
        return self.append_event("DISPOSITION", {
            "message_id": message_id,
            "decision": decision,
            "decided_by": decided_by,
        })

    def initialize_ledger(self) -> None:
        """
        Initialize ledger file with schema validation entry.
        Idempotent: only creates if file doesn't exist.
        """
        if os.path.exists(self.ledger_path):
            # Load prior hash from last entry
            try:
                with open(self.ledger_path, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_entry = json.loads(lines[-1])
                        self.prior_hash = last_entry.get("hash", "")
            except Exception as e:
                raise Exception(f"LEDGER_INIT_FAILED: {e}")
        else:
            # Create new ledger with schema entry
            self.append_event("SCHEMA", {
                "version": "1.0",
                "description": "OI-BRIDGE-01 Phase 1 Governance Ledger",
                "entry_types": [
                    "SIGNATURE_VALIDATION",
                    "MESSAGE_DELIVERY",
                    "TOKEN_ISSUED",
                    "TOKEN_CONSUMED",
                    "CONSEQUENTIAL_ACTION",
                    "ESCALATION",
                    "DISPOSITION",
                ],
            })


if __name__ == "__main__":
    # Test ledger writer
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = os.path.join(tmpdir, "test_ledger.jsonl")
        writer = NFLedgerWriter(ledger_path)

        # Initialize
        writer.initialize_ledger()
        print(f"Ledger initialized at {ledger_path}")

        # Append some events
        entry1 = writer.append_signature_validation(
            "msg_001", "claude-z1", "PASS", "z1_pub_key_2026_09_22"
        )
        print(f"Event 1: {entry1.hash[:16]}...")

        entry2 = writer.append_message_delivery(
            "msg_001", "bridge", "PRIVATE", "CLAIMED"
        )
        print(f"Event 2: {entry2.hash[:16]}...")

        # Read back
        with open(ledger_path, 'r') as f:
            entries = [json.loads(line) for line in f.readlines()]
            print(f"\nTotal entries: {len(entries)}")
            for entry in entries:
                print(f"  {entry['event_type']}: {entry['hash'][:16]}...")
