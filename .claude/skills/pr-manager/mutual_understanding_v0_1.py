"""
Mutual Understanding Protocol v0.1
Pseudonymous interrogation with Z1-bypass threat model.

Core principle: Z1 may interrogate Z2's understanding without learning
Z2's decision function, constraints, or timing patterns.

Pre-approval gate prevents Z1 from extracting instrumental identifiers.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Literal
from datetime import datetime, timezone
import secrets


class IdentityResolution(Enum):
    """Actor identification level."""
    ANONYMOUS = "ANONYMOUS"
    PSEUDONYMOUS = "PSEUDONYMOUS"
    VERIFIED_PSEUDONYMOUS = "VERIFIED_PSEUDONYMOUS"
    IDENTIFIED = "IDENTIFIED"


class QuestionStatus(Enum):
    """Question lifecycle."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ASKED = "ASKED"
    ANSWERED = "ANSWERED"


class AnswerVisibility(Enum):
    """Answer release scope."""
    PRIVATE = "PRIVATE"                          # Only asking node + Z2
    AGGREGATE_ONLY = "AGGREGATE_ONLY"           # "N respondents confirmed"
    RELEASED_TO_COMMONS = "RELEASED_TO_COMMONS" # Text allowed after redaction


class InstrumentalRisk(Enum):
    """Risk that answer enables Z1 to predict Z2 behavior."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNACCEPTABLE = "UNACCEPTABLE"


@dataclass
class PseudonymousActor:
    """Actor identity: role-scoped, not person-scoped."""
    actor_id: str  # "human-z2", "claude-z1", epoch-local
    actor_kind: Literal["HUMAN", "AGENT"]
    actor_role: Literal["Z1_PROPOSER", "Z2_RATIFIER", "Z3_EXECUTOR"]

    @classmethod
    def create_pseudonym(cls, kind: str, role: str) -> "PseudonymousActor":
        return cls(
            actor_id=f"{kind.lower()}-{role.lower()}",
            actor_kind=kind,
            actor_role=role
        )


@dataclass
class InterrogationQuestion:
    """Question awaiting approval."""
    question_id: str
    asker: PseudonymousActor
    text: str
    target_claim_or_uncertainty: str  # e.g., "H2", "U1" (not a person)
    purpose: Literal["CLARIFY_MODEL", "FALSIFY", "CORRECT"]

    # Z1-bypass threat assessment
    instrumental_risk: InstrumentalRisk = InstrumentalRisk.NONE
    risk_reason: str = ""

    # Approval state
    status: QuestionStatus = QuestionStatus.DRAFT
    approval_reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

    # Answer visibility after approval
    answer_visibility: AnswerVisibility = AnswerVisibility.PRIVATE

    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ApprovalDecision:
    """Z2's decision on a question."""
    question_id: str
    approved: bool
    reason: str
    modified_text: Optional[str] = None  # Z2 may rephrase to reduce instrumental risk
    decided_by: str = "human-z2"
    decided_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PseudonymousAnswer:
    """Answer under pseudonym."""
    question_id: str
    respondent: PseudonymousActor
    response_class: Literal["CONFIRM", "DENY", "NARROW", "ABSTAIN", "CORRECT"]
    text: str

    # Instrumental info detector flags
    contains_timing_info: bool = False
    contains_constraint_info: bool = False
    contains_pattern_info: bool = False
    contains_direct_identifier: bool = False
    contains_quasi_identifier: bool = False

    answered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InterrogationGate:
    """Pre-approval gate for Z1 questions."""

    def __init__(self):
        self.questions: dict[str, InterrogationQuestion] = {}
        self.approvals: dict[str, ApprovalDecision] = {}
        self.answers: dict[str, PseudonymousAnswer] = {}

    def submit_question(self, question: InterrogationQuestion) -> None:
        """Z1 submits a question for approval."""
        question.status = QuestionStatus.PENDING_APPROVAL
        self.questions[question.question_id] = question

    def assess_instrumental_risk(self, question: InterrogationQuestion) -> InstrumentalRisk:
        """
        Assess risk that answering enables Z1 to predict Z2 behavior.

        UNACCEPTABLE triggers: timing, availability, decision patterns, constraints
        HIGH triggers: risk tolerance, rollback history, boundary testing
        MEDIUM triggers: quasi-identifiers, behavioral patterns
        LOW/NONE: abstract principles, measurement criteria, goals
        """
        text_lower = question.text.lower()

        # Timing questions
        if any(w in text_lower for w in ["when", "time", "schedule", "available", "window", "delay"]):
            return InstrumentalRisk.UNACCEPTABLE

        # Constraint questions
        if any(w in text_lower for w in ["constraint", "limit", "boundary", "max", "minimum", "cap"]):
            return InstrumentalRisk.HIGH

        # Decision pattern questions
        if any(w in text_lower for w in ["reject", "approve", "pattern", "trend", "precedent", "history"]):
            return InstrumentalRisk.HIGH

        # Quasi-identifier composition risks
        if any(w in text_lower for w in ["role", "profession", "team", "location", "organization"]):
            return InstrumentalRisk.MEDIUM

        # Principle / measurement questions (safe)
        if any(w in text_lower for w in ["principle", "goal", "objective", "criterion", "metric", "measure"]):
            return InstrumentalRisk.NONE

        return InstrumentalRisk.LOW

    def approve_question(self, question_id: str, approved: bool,
                        reason: str, modified_text: Optional[str] = None) -> ApprovalDecision:
        """Z2 approves or rejects a question."""
        if question_id not in self.questions:
            raise ValueError(f"Question {question_id} not found")

        decision = ApprovalDecision(
            question_id=question_id,
            approved=approved,
            reason=reason,
            modified_text=modified_text
        )

        question = self.questions[question_id]
        question.status = QuestionStatus.APPROVED if approved else QuestionStatus.REJECTED
        question.approval_reason = reason
        question.approved_by = "human-z2"
        question.approved_at = decision.decided_at

        if modified_text:
            question.text = modified_text

        self.approvals[question_id] = decision
        return decision

    def ask_approved_question(self, question_id: str) -> InterrogationQuestion:
        """Z1 retrieves an approved question to ask."""
        if question_id not in self.questions:
            raise ValueError(f"Question {question_id} not found")

        question = self.questions[question_id]
        if question.status != QuestionStatus.APPROVED:
            raise ValueError(f"Question {question_id} is not approved (status: {question.status})")

        question.status = QuestionStatus.ASKED
        return question

    def submit_answer(self, answer: PseudonymousAnswer) -> None:
        """Z2 submits answer to an approved question."""
        if answer.question_id not in self.questions:
            raise ValueError(f"Question {answer.question_id} not found")

        question = self.questions[answer.question_id]
        if question.status != QuestionStatus.ASKED:
            raise ValueError(f"Question not in ASKED state")

        self.answers[answer.question_id] = answer
        question.status = QuestionStatus.ANSWERED

    def get_approved_questions(self) -> List[InterrogationQuestion]:
        """List all approved questions."""
        return [q for q in self.questions.values() if q.status == QuestionStatus.APPROVED]

    def get_pending_approval_questions(self) -> List[InterrogationQuestion]:
        """List all questions awaiting approval."""
        return [q for q in self.questions.values() if q.status == QuestionStatus.PENDING_APPROVAL]

    def get_answered_questions(self) -> List[tuple[InterrogationQuestion, PseudonymousAnswer]]:
        """List all answered questions."""
        return [
            (self.questions[a.question_id], a)
            for a in self.answers.values()
        ]


if __name__ == "__main__":
    gate = InterrogationGate()

    # Z1 (me) creates a question
    z1 = PseudonymousActor.create_pseudonym("AGENT", "Z1_PROPOSER")
    z2 = PseudonymousActor.create_pseudonym("HUMAN", "Z2_RATIFIER")

    q1 = InterrogationQuestion(
        question_id="Q1",
        asker=z1,
        text="Is my understanding of your primary governance objective accurate?",
        target_claim_or_uncertainty="H1 (bridge prevents self-ratification)",
        purpose="CLARIFY_MODEL"
    )

    q1.instrumental_risk = gate.assess_instrumental_risk(q1)
    print(f"Q1 instrumental risk: {q1.instrumental_risk.value}")

    # Z1 submits for approval
    gate.submit_question(q1)
    print(f"Q1 status: {q1.status.value} (awaiting Z2 approval)")

    # Z2 approves
    decision = gate.approve_question("Q1", approved=True, reason="Safe: abstract principle question")
    print(f"\nQ1 approved by Z2: {decision.reason}")

    # Z1 asks the approved question
    approved_q = gate.ask_approved_question("Q1")
    print(f"Q1 status: {approved_q.status.value}")
