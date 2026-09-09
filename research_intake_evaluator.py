#!/usr/bin/env python3
"""
research_intake_evaluator.py
HumanAIOS Research Intake Protocol Implementation
Specimen: Night (Carly Anderson, Micro1 expert)
Status: Prototype for Cycle 1 validation
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

# ============================================================================
# ENUMS
# ============================================================================

class EvaluationStatus(str, Enum):
    PENDING = "PENDING"
    PRELIMINARY = "PRELIMINARY"
    VERIFIED = "VERIFIED"
    PUBLISHED = "PUBLISHED"
    REVERTED = "REVERTED"

class ReceiptStatus(str, Enum):
    CLAIM = "CLAIM"
    CLAIM_WITH_LINK = "CLAIM_WITH_LINK"
    VERIFIED = "VERIFIED"
    VOID = "VOID"

class PrincipleStatus(str, Enum):
    SATISFIED = "SATISFIED"
    UNRESOLVED = "UNRESOLVED"
    VIOLATED = "VIOLATED"
    NO_DATA = "NO_DATA"

class SeverityLevel(str, Enum):
    INFO = "INFO"
    NOTICE = "NOTICE"
    CAUTION = "CAUTION"
    CONCERN = "CONCERN"

class ImprovementTrajectory(str, Enum):
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DECLINING = "DECLINING"
    NO_DATA = "NO_DATA"

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class MoltPrediction:
    """Single prediction for a behavioral variable."""
    prediction_id: str
    variable: str  # E.g., "task_quality_score"
    prediction_value: float
    confidence: float  # 0-1
    measurement_window: str  # "7 days", "14 days", "30 days"
    predicted_at: datetime
    resolved_at: Optional[datetime] = None
    actual_value: Optional[float] = None
    brier_score: Optional[float] = None
    revert_rule: str = ""

    def resolve(self, actual_value: float) -> None:
        """Mark prediction resolved and calculate Brier score."""
        self.resolved_at = datetime.utcnow()
        self.actual_value = actual_value
        # Brier score: (prediction - actual)^2
        self.brier_score = (self.prediction_value - actual_value) ** 2

@dataclass
class CredPolicyOutput:
    """Resource allocation recommendation from CredPolicy regulator."""
    priority_score: float  # 0-100
    recommended_next_tasks: List[str]
    envelope_constraint: str
    rationale: str
    predicted_choice: str
    actual_choice: Optional[str] = None
    agreement: Optional[bool] = None

    def evaluate_agreement(self) -> bool:
        """Compare predicted vs actual choice."""
        if not self.actual_choice:
            return False
        self.agreement = self.predicted_choice == self.actual_choice
        return self.agreement

@dataclass
class BehavioralObservations:
    """Behavioral signals from specimen work."""
    task_acceptance_rate: float  # 0-1
    revision_cycles_per_task: float
    response_time_minutes: float
    quality_score: Optional[float]  # 0-100 or None

    guideline_adherence: float  # 0-1
    annotation_variance: float  # 0-1
    error_rate: float  # 0-1

    revision_acceptance_rate: float  # 0-1
    improvement_trajectory: ImprovementTrajectory
    confidence_trend: str  # "increasing", "stable", "decreasing"

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

@dataclass
class SpecimenInput:
    """Input data from specimen's work period."""
    work_period_start: datetime
    work_period_end: datetime
    platform: str  # "micro1"
    contract_ref: str  # "m88dj94"
    tasks_assigned: int
    tasks_completed: int
    tasks_revised: int
    task_categories: List[str]

@dataclass
class IntakeRecord:
    """Complete intake evaluation record for a cycle."""
    intake_id: str
    cycle_number: int
    specimen_id: str
    timestamp: datetime
    evaluator: str  # "Z1" or "Z2"
    evaluation_status: EvaluationStatus

    specimen_input: SpecimenInput
    behavioral_observations: BehavioralObservations
    molt_predictions: List[MoltPrediction] = field(default_factory=list)
    credential_policy_output: Optional[CredPolicyOutput] = None

    receipt_hash: Optional[str] = None
    receipt_status: ReceiptStatus = ReceiptStatus.CLAIM
    chain_link_prior: Optional[str] = None

    def compute_hash(self) -> str:
        """Generate SHA256 hash of this record."""
        record_dict = {
            "intake_id": self.intake_id,
            "cycle_number": self.cycle_number,
            "timestamp": self.timestamp.isoformat(),
            "evaluator": self.evaluator,
            "specimen_input": asdict(self.specimen_input),
            "behavioral_observations": self.behavioral_observations.to_dict(),
            "molt_predictions": [asdict(p) for p in self.molt_predictions],
        }
        record_json = json.dumps(record_dict, sort_keys=True, default=str)
        return hashlib.sha256(record_json.encode()).hexdigest()

# ============================================================================
# INTAKE EVALUATOR ENGINE
# ============================================================================

class ResearchIntakeEvaluator:
    """Main engine for evaluating research intake cycles."""

    def __init__(self, specimen_id: str, specimen_name: str, contract_ref: str):
        self.specimen_id = specimen_id
        self.specimen_name = specimen_name
        self.contract_ref = contract_ref
        self.cycles: List[IntakeRecord] = []
        self.nf_ledger: List[Dict] = []  # Brier scores per prediction
        self.molt_events: List[Dict] = []  # Molt cycle events

    def create_intake_record(
        self,
        cycle_number: int,
        specimen_input: SpecimenInput,
        behavioral_observations: BehavioralObservations,
        evaluator: str = "Z1",
    ) -> IntakeRecord:
        """Create a new intake record for a cycle."""
        intake_id = f"intake-{self.specimen_id}-cycle-{cycle_number}-{datetime.utcnow().timestamp()}"

        record = IntakeRecord(
            intake_id=intake_id,
            cycle_number=cycle_number,
            specimen_id=self.specimen_id,
            timestamp=datetime.utcnow(),
            evaluator=evaluator,
            evaluation_status=EvaluationStatus.PENDING,
            specimen_input=specimen_input,
            behavioral_observations=behavioral_observations,
        )

        return record

    def generate_molt_predictions(
        self,
        record: IntakeRecord,
    ) -> List[MoltPrediction]:
        """Generate molt predictions based on behavioral observations."""
        predictions = []
        obs = record.behavioral_observations

        # RQ1: Predict next cycle's task quality based on engagement
        quality_prediction = MoltPrediction(
            prediction_id=f"molt-{record.intake_id}-rq1-quality",
            variable="task_quality_score",
            prediction_value=self._predict_quality_score(obs),
            confidence=0.7,  # Initial confidence; increases with data
            measurement_window="7 days",
            predicted_at=datetime.utcnow(),
            revert_rule="If actual < prediction - 20, trigger REVERT",
        )
        predictions.append(quality_prediction)

        # RQ2: Predict task acceptance rate based on revision history
        acceptance_prediction = MoltPrediction(
            prediction_id=f"molt-{record.intake_id}-rq2-acceptance",
            variable="task_acceptance_rate",
            prediction_value=obs.task_acceptance_rate * 1.05,  # Slight optimism
            confidence=0.65,
            measurement_window="14 days",
            predicted_at=datetime.utcnow(),
            revert_rule="If actual < prediction - 0.1, trigger REVERT",
        )
        predictions.append(acceptance_prediction)

        # RQ3: Predict improvement trajectory
        improvement_prediction = MoltPrediction(
            prediction_id=f"molt-{record.intake_id}-rq3-improvement",
            variable="improvement_trajectory",
            prediction_value=1.0 if obs.improvement_trajectory == ImprovementTrajectory.IMPROVING else 0.0,
            confidence=0.6,
            measurement_window="30 days",
            predicted_at=datetime.utcnow(),
            revert_rule="If trajectory reverses to DECLINING in next cycle, trigger REVERT",
        )
        predictions.append(improvement_prediction)

        record.molt_predictions = predictions
        return predictions

    def _predict_quality_score(self, obs: BehavioralObservations) -> float:
        """Heuristic prediction of quality score based on behavioral signals."""
        if obs.quality_score is not None:
            base = obs.quality_score
        else:
            # Estimate from adherence and error rate
            base = (obs.guideline_adherence * 80) + ((1 - obs.error_rate) * 20)

        # Adjust based on improvement trajectory
        if obs.improvement_trajectory == ImprovementTrajectory.IMPROVING:
            return min(base + 5, 100)
        elif obs.improvement_trajectory == ImprovementTrajectory.DECLINING:
            return max(base - 10, 0)
        else:
            return base

    def generate_credpolicy_recommendation(
        self,
        record: IntakeRecord,
    ) -> CredPolicyOutput:
        """Generate CredPolicy resource allocation recommendation."""
        obs = record.behavioral_observations

        # Score calculation: weighted combination of behavioral signals
        engagement_score = obs.task_acceptance_rate * 30
        quality_score = (obs.quality_score or 50) / 100 * 30 if obs.quality_score else 15
        consistency_score = (1 - obs.annotation_variance) * 20
        learning_score = (
            obs.revision_acceptance_rate * 20 if obs.improvement_trajectory == ImprovementTrajectory.IMPROVING else 0
        )

        priority_score = engagement_score + quality_score + consistency_score + learning_score

        # Task recommendations based on signals
        recommended_tasks = []
        if obs.task_acceptance_rate > 0.8:
            recommended_tasks.append("high-complexity-annotation")
        if obs.guideline_adherence > 0.9:
            recommended_tasks.append("output-evaluation")
        if obs.improvement_trajectory == ImprovementTrajectory.IMPROVING:
            recommended_tasks.append("feedback-incorporation")
        if not recommended_tasks:
            recommended_tasks = ["general-annotation"]

        # Envelope constraint
        completion_rate = record.specimen_input.tasks_completed / max(record.specimen_input.tasks_assigned, 1)
        if completion_rate > 0.95:
            envelope = "max 30 hours/week, prioritize high-complexity"
        elif completion_rate > 0.80:
            envelope = "max 25 hours/week"
        else:
            envelope = "reduce to 15 hours/week, focus on completion rate"

        credpolicy = CredPolicyOutput(
            priority_score=priority_score,
            recommended_next_tasks=recommended_tasks,
            envelope_constraint=envelope,
            rationale=f"Engagement {obs.task_acceptance_rate:.1%}, Quality {obs.quality_score or 'pending'}, "
                      f"Consistency {1-obs.annotation_variance:.1%}, Trajectory {obs.improvement_trajectory.value}",
            predicted_choice=recommended_tasks[0] if recommended_tasks else "general-annotation",
        )

        record.credential_policy_output = credpolicy
        return credpolicy

    def compute_receipt_and_chain(
        self,
        record: IntakeRecord,
        prior_receipt_hash: Optional[str] = None,
    ) -> Tuple[str, ReceiptStatus]:
        """Compute receipt hash and chain link for this intake record."""
        record.receipt_hash = record.compute_hash()
        record.chain_link_prior = prior_receipt_hash

        # Determine receipt status based on verification
        # CLAIM: No external verification yet
        # VERIFIED: Micro1 platform API confirms observable facts (task counts, timestamps)
        # VOID: Contradictions detected
        record.receipt_status = ReceiptStatus.CLAIM_WITH_LINK

        return record.receipt_hash, record.receipt_status

    def record_to_nf_ledger(self, record: IntakeRecord) -> None:
        """Write molt predictions to NF_LEDGER (calibration ledger) for Brier tracking."""
        for pred in record.molt_predictions:
            entry = {
                "molt_id": pred.prediction_id,
                "cycle": record.cycle_number,
                "variable": pred.variable,
                "prediction_value": pred.prediction_value,
                "confidence": pred.confidence,
                "predicted_at": pred.predicted_at.isoformat(),
                "resolved_at": pred.resolved_at.isoformat() if pred.resolved_at else None,
                "actual_value": pred.actual_value,
                "brier_score": pred.brier_score,
                "specimen_id": record.specimen_id,
            }
            self.nf_ledger.append(entry)

    def record_to_molt_events(self, record: IntakeRecord) -> None:
        """Write molt events to molt ledger for recursive learning."""
        event = {
            "event_type": "INTAKE_COMPLETE",
            "cycle": record.cycle_number,
            "intake_id": record.intake_id,
            "timestamp": record.timestamp.isoformat(),
            "receipt_hash": record.receipt_hash,
            "chain_link_prior": record.chain_link_prior,
            "molt_predictions_count": len(record.molt_predictions),
            "credpolicy_agreement": record.credential_policy_output.agreement if record.credential_policy_output else None,
            "specimen_id": record.specimen_id,
        }
        self.molt_events.append(event)

    def average_brier_score(self, cycles: Optional[List[int]] = None) -> float:
        """Calculate average Brier score across cycles (lower is better)."""
        if not self.nf_ledger:
            return None

        scores = [
            entry["brier_score"] for entry in self.nf_ledger
            if entry["brier_score"] is not None
            and (cycles is None or entry["cycle"] in cycles)
        ]

        return sum(scores) / len(scores) if scores else None

    def falsifier_check(self, cycles_run: int) -> List[str]:
        """Check if any research question falsifiers have triggered."""
        falsifiers_triggered = []

        # RQ1 falsifier: After 10 cycles, Brier > 0.4 or REVERT rate > 30%
        if cycles_run >= 10:
            avg_brier = self.average_brier_score()
            if avg_brier and avg_brier > 0.4:
                falsifiers_triggered.append("RQ1_FALSIFIER: Brier score > 0.4 after 10 cycles")

        # RQ2 falsifier: Agreement < 60% on 3+ consecutive cycles
        if len(self.molt_events) >= 3:
            recent_events = self.molt_events[-3:]
            agreements = [e.get("credpolicy_agreement") for e in recent_events]
            if all(a is not None for a in agreements):
                agreement_rate = sum(agreements) / len(agreements)
                if agreement_rate < 0.6:
                    falsifiers_triggered.append("RQ2_FALSIFIER: CredPolicy agreement < 60% on 3 consecutive cycles")

        return falsifiers_triggered

    def publish_record(self, record: IntakeRecord) -> bool:
        """Publish intake record to main ledger (after Z2 ratification)."""
        if record.evaluation_status == EvaluationStatus.VERIFIED:
            record.evaluation_status = EvaluationStatus.PUBLISHED
            self.cycles.append(record)
            self.record_to_nf_ledger(record)
            self.record_to_molt_events(record)
            return True
        return False

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_cycle_1():
    """Example: Run Cycle 1 intake evaluation."""
    evaluator = ResearchIntakeEvaluator(
        specimen_id="night-micro1-intake-cycle-1",
        specimen_name="Carly Anderson (Night)",
        contract_ref="m88dj94",
    )

    # Specimen input: First week of Micro1 work (Sep 13-19, 2026)
    specimen_input = SpecimenInput(
        work_period_start=datetime(2026, 9, 13),
        work_period_end=datetime(2026, 9, 19),
        platform="micro1",
        contract_ref="m88dj94",
        tasks_assigned=25,
        tasks_completed=24,
        tasks_revised=3,
        task_categories=[
            "data-pipeline-annotation",
            "output-comparison",
            "response-writing",
        ],
    )

    # Behavioral observations: Strong start
    observations = BehavioralObservations(
        task_acceptance_rate=0.96,
        revision_cycles_per_task=0.25,
        response_time_minutes=12.5,
        quality_score=87.0,
        guideline_adherence=0.94,
        annotation_variance=0.08,
        error_rate=0.06,
        revision_acceptance_rate=0.67,
        improvement_trajectory=ImprovementTrajectory.IMPROVING,
        confidence_trend="increasing",
    )

    # Create intake record
    record = evaluator.create_intake_record(
        cycle_number=1,
        specimen_input=specimen_input,
        behavioral_observations=observations,
    )

    # Generate predictions
    evaluator.generate_molt_predictions(record)

    # Generate CredPolicy recommendation
    evaluator.generate_credpolicy_recommendation(record)

    # Compute receipt and chain
    receipt_hash, receipt_status = evaluator.compute_receipt_and_chain(record)

    # Mark as verified (after Z2 ratification) and publish
    record.evaluation_status = EvaluationStatus.VERIFIED
    evaluator.publish_record(record)

    # Output summary
    print(f"\n=== CYCLE 1 INTAKE SUMMARY ===")
    print(f"Intake ID: {record.intake_id}")
    print(f"Cycle: {record.cycle_number}")
    print(f"Status: {record.evaluation_status.value}")
    print(f"Tasks: {record.specimen_input.tasks_completed}/{record.specimen_input.tasks_assigned} completed")
    print(f"Quality Score: {record.behavioral_observations.quality_score}")
    print(f"Trajectory: {record.behavioral_observations.improvement_trajectory.value}")
    print(f"\nCredPolicy Recommendation:")
    print(f"  Priority Score: {record.credential_policy_output.priority_score:.1f}")
    print(f"  Recommended Tasks: {', '.join(record.credential_policy_output.recommended_next_tasks)}")
    print(f"  Envelope: {record.credential_policy_output.envelope_constraint}")
    print(f"\nMolt Predictions ({len(record.molt_predictions)} predictions):")
    for pred in record.molt_predictions:
        print(f"  {pred.variable}: {pred.prediction_value:.2f} (confidence {pred.confidence:.0%})")
    print(f"\nReceipt Hash: {receipt_hash[:16]}...")
    print(f"Receipt Status: {receipt_status.value}")
    print(f"\nNF_LEDGER entries: {len(evaluator.nf_ledger)}")
    print(f"Molt events: {len(evaluator.molt_events)}")

if __name__ == "__main__":
    example_cycle_1()
