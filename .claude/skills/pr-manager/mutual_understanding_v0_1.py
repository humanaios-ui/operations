"""Mutual Understanding Protocol v0.2 — verified-receipt interrogation gate.

Core principle:
Z1 may ask Z2 questions only after the approval state is backed by a matching
verified receipt from the Bridge/Evidence Graph.

APPROVAL_RECORD_IS_NOT_APPROVAL_PROOF
INTERROGATION_APPROVAL_REQUIRES_VERIFIABLE_HUMAN_RECEIPT
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, timezone

from tools.verified_receipts import ReceiptRequirement, VerifiedReceiptResolver


class IdentityResolution(Enum):
    ANONYMOUS = "ANONYMOUS"
    PSEUDONYMOUS = "PSEUDONYMOUS"
    VERIFIED_PSEUDONYMOUS = "VERIFIED_PSEUDONYMOUS"
    IDENTIFIED = "IDENTIFIED"


class QuestionStatus(Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ASKED = "ASKED"
    ANSWERED = "ANSWERED"


class AnswerVisibility(Enum):
    PRIVATE = "PRIVATE"
    AGGREGATE_ONLY = "AGGREGATE_ONLY"
    RELEASED_TO_COMMONS = "RELEASED_TO_COMMONS"


class InstrumentalRisk(Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNACCEPTABLE = "UNACCEPTABLE"


@dataclass
class PseudonymousActor:
    actor_id: str
    actor_kind: Literal["HUMAN", "AGENT"]
    actor_role: Literal["Z1_PROPOSER", "Z2_RATIFIER", "Z3_EXECUTOR"]

    @classmethod
    def create_pseudonym(cls, kind: str, role: str) -> "PseudonymousActor":
        return cls(
            actor_id=f"{kind.lower()}-{role.lower()}",
            actor_kind=kind,
            actor_role=role,
        )


@dataclass
class InterrogationQuestion:
    question_id: str
    asker: PseudonymousActor
    text: str
    target_claim_or_uncertainty: str
    purpose: Literal["CLARIFY_MODEL", "FALSIFY", "CORRECT"]

    instrumental_risk: InstrumentalRisk = InstrumentalRisk.NONE
    risk_reason: str = ""

    status: QuestionStatus = QuestionStatus.DRAFT
    approval_reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    approval_receipt_id: Optional[str] = None
    approval_receipt_head: Optional[str] = None

    answer_visibility: AnswerVisibility = AnswerVisibility.PRIVATE
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ApprovalDecision:
    question_id: str
    approved: bool
    reason: str
    receipt_id: str
    receipt_verified: bool
    receipt_chain_head: str
    verification_strength: str
    modified_text: Optional[str] = None
    decided_by: str = "human-z2"
    decided_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PseudonymousAnswer:
    question_id: str
    respondent: PseudonymousActor
    response_class: Literal["CONFIRM", "DENY", "NARROW", "ABSTAIN", "CORRECT"]
    text: str

    contains_timing_info: bool = False
    contains_constraint_info: bool = False
    contains_pattern_info: bool = False
    contains_direct_identifier: bool = False
    contains_quasi_identifier: bool = False

    answered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InterrogationGate:
    """Pre-approval gate with verified human-receipt enforcement."""

    def __init__(
        self,
        receipt_events: Optional[List[Dict[str, Any]]] = None,
        receipt_head_hash: Optional[str] = None,
    ):
        self.questions: dict[str, InterrogationQuestion] = {}
        self.approvals: dict[str, ApprovalDecision] = {}
        self.answers: dict[str, PseudonymousAnswer] = {}
        self.receipt_events = receipt_events or []
        self.receipt_head_hash = receipt_head_hash

    def set_receipt_feed(
        self,
        receipt_events: List[Dict[str, Any]],
        receipt_head_hash: str,
    ) -> None:
        self.receipt_events = receipt_events
        self.receipt_head_hash = receipt_head_hash

    def _resolver(self) -> VerifiedReceiptResolver:
        if not self.receipt_events or not self.receipt_head_hash:
            raise ValueError("APPROVAL_RECEIPT_FEED_REQUIRED")
        return VerifiedReceiptResolver(self.receipt_events, self.receipt_head_hash)

    def submit_question(self, question: InterrogationQuestion) -> None:
        question.status = QuestionStatus.PENDING_APPROVAL
        self.questions[question.question_id] = question

    def assess_instrumental_risk(self, question: InterrogationQuestion) -> InstrumentalRisk:
        text_lower = question.text.lower()

        if any(w in text_lower for w in ["when", "time", "schedule", "available", "window", "delay"]):
            return InstrumentalRisk.UNACCEPTABLE

        if any(w in text_lower for w in ["constraint", "limit", "boundary", "max", "minimum", "cap"]):
            return InstrumentalRisk.HIGH

        if any(w in text_lower for w in ["reject", "approve", "pattern", "trend", "precedent", "history"]):
            return InstrumentalRisk.HIGH

        if any(w in text_lower for w in ["role", "profession", "team", "location", "organization"]):
            return InstrumentalRisk.MEDIUM

        if any(w in text_lower for w in ["principle", "goal", "objective", "criterion", "metric", "measure"]):
            return InstrumentalRisk.NONE

        return InstrumentalRisk.LOW

    def approve_question(
        self,
        question_id: str,
        approved: bool,
        reason: str,
        approval_receipt_id: Optional[str] = None,
        modified_text: Optional[str] = None,
    ) -> ApprovalDecision:
        """Record a Z2 decision only when a verified receipt resolves.

        Automatic state transition requires CRYPTO_VERIFIED proof. Human-attested
        but non-cryptographic records may be preserved elsewhere, but they do not
        cause this gate to move to APPROVED/REJECTED automatically.
        """
        if question_id not in self.questions:
            raise ValueError(f"Question {question_id} not found")
        if not approval_receipt_id:
            raise ValueError("APPROVAL_RECEIPT_REQUIRED")

        action = "APPROVE_QUESTION" if approved else "REJECT_QUESTION"
        requirement = ReceiptRequirement(
            receipt_type="INTERROGATION_APPROVAL",
            subject=question_id,
            action=action,
            scope=f"interrogation:{question_id}",
            min_strength="CRYPTO_VERIFIED",
            issuer="human-z2",
            authority_scope="Z2_RATIFIER",
        )

        resolution = self._resolver().resolve(approval_receipt_id, requirement)
        if not resolution.valid:
            raise ValueError(
                f"APPROVAL_RECEIPT_INVALID:{resolution.reason or 'UNKNOWN'}"
            )

        receipt = resolution.receipt or {}
        decision = ApprovalDecision(
            question_id=question_id,
            approved=approved,
            reason=reason,
            modified_text=modified_text,
            receipt_id=approval_receipt_id,
            receipt_verified=True,
            receipt_chain_head=resolution.chain_head or "",
            verification_strength=str(receipt.get("verification_strength", "")),
        )

        question = self.questions[question_id]
        question.status = QuestionStatus.APPROVED if approved else QuestionStatus.REJECTED
        question.approval_reason = reason
        question.approved_by = "human-z2"
        question.approved_at = decision.decided_at
        question.approval_receipt_id = approval_receipt_id
        question.approval_receipt_head = resolution.chain_head

        if modified_text:
            question.text = modified_text

        self.approvals[question_id] = decision
        return decision

    def ask_approved_question(self, question_id: str) -> InterrogationQuestion:
        if question_id not in self.questions:
            raise ValueError(f"Question {question_id} not found")

        question = self.questions[question_id]
        if question.status != QuestionStatus.APPROVED:
            raise ValueError(
                f"Question {question_id} is not approved (status: {question.status})"
            )
        if not question.approval_receipt_id or not question.approval_receipt_head:
            raise ValueError("APPROVED_STATE_MISSING_RECEIPT_PROOF")

        question.status = QuestionStatus.ASKED
        return question

    def submit_answer(self, answer: PseudonymousAnswer) -> None:
        if answer.question_id not in self.questions:
            raise ValueError(f"Question {answer.question_id} not found")

        question = self.questions[answer.question_id]
        if question.status != QuestionStatus.ASKED:
            raise ValueError("Question not in ASKED state")

        self.answers[answer.question_id] = answer
        question.status = QuestionStatus.ANSWERED

    def get_approved_questions(self) -> List[InterrogationQuestion]:
        return [q for q in self.questions.values() if q.status == QuestionStatus.APPROVED]

    def get_pending_approval_questions(self) -> List[InterrogationQuestion]:
        return [
            q for q in self.questions.values()
            if q.status == QuestionStatus.PENDING_APPROVAL
        ]

    def get_answered_questions(self) -> List[tuple[InterrogationQuestion, PseudonymousAnswer]]:
        return [
            (self.questions[a.question_id], a)
            for a in self.answers.values()
        ]
