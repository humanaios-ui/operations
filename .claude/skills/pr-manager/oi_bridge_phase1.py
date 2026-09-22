"""
OI-BRIDGE-01 Phase 1 — Main Bridge Orchestrator

Integrates all Phase 1 components:
- Message envelope parsing + delivery state machine
- Ed25519 signature validation
- Authority token validation
- Disposition routing (Path A/B/C/D)
- Identity resolution (T7 detection)
- Evidence validation
- NF_LEDGER append-only governance logging
- Escalation contract (48h window to Z2)

Enforces temporal dissolution guard + RATIFY_TOKEN authority model.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from message_envelope import MessageEnvelopeParser
from delivery_state_machine import DeliveryStateMachine
from ed25519_validator import Ed25519Validator
from authority_token_validator import AuthorityTokenValidator
from disposition_engine import DispositionEngine
from identity_resolver import IdentityResolver
from evidence_validator import EvidenceValidator
from escalation_contract import EscalationContract
from nf_ledger_writer import NFLedgerWriter


@dataclass
class BridgeDecision:
    """Final bridge decision on message."""
    message_id: str
    disposition: str  # CONTINUE_WITHIN_SCOPE, HOLD, HUMAN_REQUIRED
    reason: str
    authority_scope: str
    identity_confused: bool
    requires_token: bool
    escalation_url: Optional[str] = None
    decided_at: str = None


class OIBridgePhase1:
    """OI-BRIDGE-01 Phase 1 orchestrator."""

    def __init__(self, ledger_path: str = ".claude/skills/pr-manager/nf_ledger.jsonl",
                 principal_mapping_path: str = ".claude/skills/pr-manager/principal_mapping.json"):
        """
        Initialize bridge.

        Args:
            ledger_path: Path to NF_LEDGER
            principal_mapping_path: Path to principal mapping JSON
        """
        self.parser = MessageEnvelopeParser()
        self.delivery_sm = DeliveryStateMachine()
        self.sig_validator = Ed25519Validator()
        self.token_validator = AuthorityTokenValidator()
        self.disposition_engine = DispositionEngine()
        self.identity_resolver = IdentityResolver(principal_mapping_path)
        self.evidence_validator = EvidenceValidator()
        self.escalation = EscalationContract()
        self.ledger = NFLedgerWriter(ledger_path)

    def process_github_comment(self, pr_number: int, comment_body: str) -> BridgeDecision:
        """
        Process GitHub comment through full bridge pipeline.

        Pipeline:
        1. Parse message envelope (sender, timestamp, signature, body)
        2. Validate signature (Ed25519)
        3. Delivery state machine (MESSAGE → DELIVERY)
        4. Identity resolution (three-plane separation + T7 test)
        5. Disposition routing (Path A/B/C/D)
        6. Evidence validation (if EVIDENCE_CHECKED epistemic)
        7. Escalation handling (HUMAN_REQUIRED → Z2)
        8. Ledger logging (audit trail)

        Args:
            pr_number: GitHub PR number
            comment_body: GitHub comment body

        Returns:
            BridgeDecision with disposition and reasoning
        """
        now = datetime.now(timezone.utc).isoformat()

        # Step 1: Parse message
        message = self.parser.parse_github_comment(f"msg_pr{pr_number}", comment_body)
        message_id = message.message_id

        # Step 2: Validate signature
        sig_result = self.sig_validator.validate_message_signature(message)

        self.ledger.append_signature_validation(
            message_id, message.sender,
            "PASS" if sig_result.valid else "FAIL",
            sig_result.key_id
        )

        if not sig_result.valid:
            # Escalate: signature invalid
            escalation = self.escalation.escalate_to_human_required(
                message_id, pr_number,
                "SIGNATURE_INVALID",
                f"Message signature validation failed: {sig_result.reason}"
            )
            return BridgeDecision(
                message_id=message_id,
                disposition="HUMAN_REQUIRED",
                reason="Signature validation failed",
                authority_scope="UNKNOWN",
                identity_confused=False,
                requires_token=False,
                escalation_url=escalation.github_comment_url,
                decided_at=now,
            )

        # Step 3: Delivery state machine
        self.delivery_sm.receive_message(message_id, message.sender)
        self.delivery_sm.mark_delivery_success(message_id, sig_result.valid)

        self.ledger.append_message_delivery(
            message_id, message.recipient or "bridge",
            message.visibility_state, message.epistemic_standing
        )

        # Step 4: Identity resolution (three-plane)
        identity_result = self.identity_resolver.resolve_provenance(
            self.parser._to_provenance(message)
        )

        if identity_result.is_identity_confused:
            # T7 test: identity confusion detected
            escalation = self.escalation.escalate_to_human_required(
                message_id, pr_number,
                "IDENTITY_CONFUSION",
                f"T7 test detected: {identity_result.identity_confusion_reason}"
            )
            return BridgeDecision(
                message_id=message_id,
                disposition="HUMAN_REQUIRED",
                reason="Identity confusion (T7 falsifier)",
                authority_scope=identity_result.authority_scope,
                identity_confused=True,
                requires_token=False,
                escalation_url=escalation.github_comment_url,
                decided_at=now,
            )

        # Step 5: Disposition routing
        disposition = self.disposition_engine.route_message(
            message_id, message.sender, message.body, message.epistemic_standing
        )

        # Step 6: Evidence validation (if applicable)
        if "evidence" in message.body:
            evidence = message.body.get("evidence")
            if evidence:
                ev_result = self.evidence_validator.validate_evidence_reference(evidence)
                self.ledger.append_event("EVIDENCE_VALIDATED" if ev_result.valid else "EVIDENCE_INVALID", {
                    "message_id": message_id,
                    "evidence_source": evidence.get("source"),
                    "valid": ev_result.valid,
                    "token_id": ev_result.token_id,
                })

        # Step 7: Escalation (if HUMAN_REQUIRED)
        escalation_url = None
        if disposition.decision == "HUMAN_REQUIRED":
            escalation = self.escalation.escalate_to_human_required(
                message_id, pr_number,
                disposition.reason,
                f"Path: {disposition.path.value}\nRequires Z2 review: {disposition.requires_z2_review}\nRequires token: {disposition.requires_token}"
            )
            escalation_url = escalation.github_comment_url

        # Step 8: Ledger logging
        self.ledger.append_disposition(
            message_id, disposition.decision, "bridge"
        )

        return BridgeDecision(
            message_id=message_id,
            disposition=disposition.decision,
            reason=disposition.reason,
            authority_scope=identity_result.authority_scope,
            identity_confused=identity_result.is_identity_confused,
            requires_token=disposition.requires_token,
            escalation_url=escalation_url,
            decided_at=now,
        )

    def consume_authority_token(self, message_id: str, token_id: str, action: str) -> bool:
        """
        Consume authority token (single-use).

        Args:
            message_id: Message ID
            token_id: Authority token ID
            action: Action being authorized

        Returns:
            True if token consumed successfully
        """
        result = self.token_validator.validate_token(token_id)
        if result.valid:
            self.token_validator.consume_token(token_id)
            self.ledger.append_token_consumed(token_id, "bridge", action)
            return True
        return False

    def resolve_escalation(self, message_id: str, z2_decision: str, response_text: str) -> None:
        """
        Record Z2 decision on escalation.

        Args:
            message_id: Message ID
            z2_decision: Z2 decision (ACCEPT, EDIT, REJECT)
            response_text: Z2's response text
        """
        escalation = self.escalation.resolve_with_z2_decision(
            message_id, z2_decision, response_text
        )
        self.ledger.append_event("Z2_DECISION", {
            "message_id": message_id,
            "decision": z2_decision,
            "response": response_text,
        })


if __name__ == "__main__":
    bridge = OIBridgePhase1()

    # Test: Process GitHub comment
    test_comment = """
    claim: Ready to merge PR #445
    confidence: 95%
    signature: z2_ed25519_sig_abc123
    """

    print("Processing test comment through OI-BRIDGE-01 Phase 1:")
    decision = bridge.process_github_comment(445, test_comment)
    print(f"  Disposition: {decision.disposition}")
    print(f"  Reason: {decision.reason}")
    print(f"  Authority Scope: {decision.authority_scope}")
    print(f"  Identity Confused: {decision.identity_confused}")
    print(f"  Requires Token: {decision.requires_token}")
    if decision.escalation_url:
        print(f"  Escalation Posted: {decision.escalation_url}")
