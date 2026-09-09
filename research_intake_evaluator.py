#!/usr/bin/env python3
"""
research_intake_evaluator.py  —  v0.2 (post red-team, 2026-09-08)
HumanAIOS Research Intake Protocol Implementation
Specimen: pseudonymous specimen_id only (no legal name / contract id in tree — RT-07)
Status: Prototype for Cycle 1; Tier 2, ADV required before OPERATED.

Changes from v0.1 (each maps to a red-team finding RT-xx in research-intake_redteam_090826.md):
  RT-01  Brier score is now computed on a bounded [0,1] error, and only on
         probabilistic/normalised forecasts. Raw-scale squared error (which gave
         33.6 for a 5.8-point quality miss) is gone; the RQ1 threshold 0.4 is now
         meaningful.
  RT-02  Receipt hash covers the *commitment* (predictions as issued, CredPolicy
         output, chain_link_prior). Resolutions are hashed separately, so the
         receipt is stable after predictions resolve and prior-link tampering is
         detected.
  RT-03  publish_record() requires a Z2 ratification hash that binds to the receipt
         hash; a status flag alone no longer publishes.
  RT-04  CredPolicy agreement is recorded from an explicit actual_choice; RQ2
         falsifier can now actually fire. Prediction is registered *before* the
         recommendation is disclosed (disclosed_at) so contamination is visible.
  RT-05  Acceptance-rate forecast clamped to [0,1]; forecasts are no longer the
         input relabeled (+5 / *1.05) — they are shrunk toward a prior.
  RT-06  REVERT is mechanical: revert_rule is structured (threshold), evaluated by
         code, emits REVERT event and F/IC candidate. RQ1 REVERT-rate and RQ3
         falsifiers implemented.
  RT-08  receipt_status defaults to CLAIM; CLAIM_WITH_LINK / VERIFIED require
         verification_sources.
  RT-09  Timezone-aware timestamps; specimen_id no longer carries a cycle number.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


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


class ImprovementTrajectory(str, Enum):
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DECLINING = "DECLINING"
    NO_DATA = "NO_DATA"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class RevertRule:
    """Mechanical revert rule. `kind` = 'abs_below' | 'abs_above' | 'equals'."""
    kind: str
    threshold: float

    def tripped(self, predicted: float, actual: float) -> bool:
        if self.kind == "abs_below":      # actual fell more than threshold below prediction
            return (predicted - actual) > self.threshold
        if self.kind == "abs_above":
            return (actual - predicted) > self.threshold
        if self.kind == "equals":         # binary outcome; trip when actual == threshold
            return actual == self.threshold
        raise ValueError(f"unknown revert rule kind {self.kind}")


@dataclass
class MoltPrediction:
    """A single forecast. `prediction_value` is on the variable's *normalised* scale
    ([0,1]); `scale_max` records how to map the raw observation onto it."""
    prediction_id: str
    variable: str
    prediction_value: float            # in [0,1]
    confidence: float                  # in [0,1]; used as the probability for binary vars
    measurement_window_days: int
    predicted_at: datetime
    revert_rule: RevertRule
    scale_max: float = 1.0             # raw = normalised * scale_max
    binary: bool = False
    resolved_at: Optional[datetime] = None
    actual_value: Optional[float] = None   # normalised
    brier_score: Optional[float] = None
    reverted: bool = False

    def __post_init__(self):
        if not 0.0 <= self.prediction_value <= 1.0:
            raise ValueError(f"{self.prediction_id}: prediction_value {self.prediction_value} outside [0,1]")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"{self.prediction_id}: confidence outside [0,1]")

    def commitment(self) -> Dict:
        """The fields committed at issue time — these and only these are hashed
        into the receipt. Resolution fields are excluded so the receipt is stable."""
        return {
            "prediction_id": self.prediction_id,
            "variable": self.variable,
            "prediction_value": self.prediction_value,
            "confidence": self.confidence,
            "measurement_window_days": self.measurement_window_days,
            "predicted_at": self.predicted_at.isoformat(),
            "revert_rule": asdict(self.revert_rule),
            "scale_max": self.scale_max,
            "binary": self.binary,
        }

    def resolve(self, actual_raw: float) -> Tuple[float, bool]:
        """Resolve against a raw observation. Returns (brier, reverted).
        Brier: for binary variables, (p - outcome)^2 with p = confidence-weighted
        forecast; for continuous variables, squared *normalised* error, bounded [0,1]."""
        if self.resolved_at is not None:
            raise RuntimeError(f"{self.prediction_id} already resolved")
        actual = max(0.0, min(1.0, actual_raw / self.scale_max))
        self.resolved_at = utcnow()
        self.actual_value = actual
        if self.binary:
            p = self.prediction_value * self.confidence + (1 - self.prediction_value) * (1 - self.confidence)
            self.brier_score = (p - actual) ** 2
        else:
            self.brier_score = (self.prediction_value - actual) ** 2
        self.reverted = self.revert_rule.tripped(self.prediction_value, actual)
        return self.brier_score, self.reverted


@dataclass
class CredPolicyOutput:
    priority_score: float              # 0-100
    recommended_next_tasks: List[str]
    envelope_constraint: str
    rationale: str
    predicted_choice: str
    registered_at: datetime
    disclosed_at: Optional[datetime] = None   # when the specimen saw the recommendation
    actual_choice: Optional[str] = None
    agreement: Optional[bool] = None

    def commitment(self) -> Dict:
        d = asdict(self)
        for k in ("disclosed_at", "actual_choice", "agreement"):
            d.pop(k)
        d["registered_at"] = self.registered_at.isoformat()
        return d

    def record_actual(self, actual_choice: str) -> bool:
        if not actual_choice:
            raise ValueError("actual_choice must be non-empty")
        self.actual_choice = actual_choice
        self.agreement = (self.predicted_choice == actual_choice)
        return self.agreement


@dataclass
class BehavioralObservations:
    task_acceptance_rate: float
    revision_cycles_per_task: float
    response_time_minutes: float
    quality_score: Optional[float]     # 0-100 or None
    guideline_adherence: float
    annotation_variance: float
    error_rate: float
    revision_acceptance_rate: float
    improvement_trajectory: ImprovementTrajectory
    confidence_trend: str

    def __post_init__(self):
        for name in ("task_acceptance_rate", "guideline_adherence", "annotation_variance",
                     "error_rate", "revision_acceptance_rate"):
            v = getattr(self, name)
            if not 0.0 <= v <= 1.0:
                raise ValueError(f"{name}={v} outside [0,1]")
        if self.quality_score is not None and not 0.0 <= self.quality_score <= 100.0:
            raise ValueError("quality_score outside [0,100]")

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SpecimenInput:
    work_period_start: datetime
    work_period_end: datetime
    platform: str
    tasks_assigned: int
    tasks_completed: int
    tasks_revised: int
    task_categories: List[str]
    verification_sources: List[str] = field(default_factory=list)  # e.g. ["micro1-platform-export:<sha>"]


@dataclass
class IntakeRecord:
    intake_id: str
    cycle_number: int
    specimen_id: str
    timestamp: datetime
    evaluator: str
    evaluation_status: EvaluationStatus
    specimen_input: SpecimenInput
    behavioral_observations: BehavioralObservations
    chain_link_prior: Optional[str]                     # committed — part of the hash
    molt_predictions: List[MoltPrediction] = field(default_factory=list)
    credential_policy_output: Optional[CredPolicyOutput] = None
    receipt_hash: Optional[str] = None
    receipt_status: ReceiptStatus = ReceiptStatus.CLAIM
    ratification_hash: Optional[str] = None
    ratified_by: Optional[str] = None
    ratified_at: Optional[datetime] = None

    def compute_hash(self) -> str:
        """SHA256 over the *commitment*: identity, inputs, observations, prediction
        commitments, CredPolicy commitment, and the prior link. Excludes anything
        that legitimately changes after issue (resolutions, status, ratification)."""
        commit = {
            "intake_id": self.intake_id,
            "cycle_number": self.cycle_number,
            "specimen_id": self.specimen_id,
            "timestamp": self.timestamp.isoformat(),
            "evaluator": self.evaluator,
            "chain_link_prior": self.chain_link_prior,
            "specimen_input": asdict(self.specimen_input),
            "behavioral_observations": self.behavioral_observations.to_dict(),
            "molt_predictions": [p.commitment() for p in self.molt_predictions],
            "credential_policy_output": self.credential_policy_output.commitment()
            if self.credential_policy_output else None,
        }
        return hashlib.sha256(json.dumps(commit, sort_keys=True, default=str).encode()).hexdigest()

    def resolution_hash(self) -> str:
        """Separate hash over resolutions; chained to receipt_hash."""
        res = {
            "receipt_hash": self.receipt_hash,
            "resolutions": [
                {"prediction_id": p.prediction_id, "actual_value": p.actual_value,
                 "brier_score": p.brier_score, "reverted": p.reverted,
                 "resolved_at": p.resolved_at.isoformat() if p.resolved_at else None}
                for p in self.molt_predictions
            ],
            "credpolicy_actual": self.credential_policy_output.actual_choice
            if self.credential_policy_output else None,
        }
        return hashlib.sha256(json.dumps(res, sort_keys=True).encode()).hexdigest()


# ============================================================================
# ENGINE
# ============================================================================

class RatificationError(RuntimeError):
    pass


class ResearchIntakeEvaluator:
    """Evaluates research-intake cycles. Z1 proposes; Z2 ratifies by hash; code measures."""

    # Prior toward which forecasts are shrunk (RT-05). Constants — molt-governed.
    PRIOR_QUALITY = 0.75
    PRIOR_ACCEPTANCE = 0.85
    SHRINK = 0.3

    def __init__(self, specimen_id: str):
        self.specimen_id = specimen_id
        self.cycles: List[IntakeRecord] = []
        self.nf_ledger: List[Dict] = []
        self.molt_events: List[Dict] = []
        self.fic_candidates: List[Dict] = []

    # -- intake ---------------------------------------------------------------

    def create_intake_record(self, cycle_number: int, specimen_input: SpecimenInput,
                             behavioral_observations: BehavioralObservations,
                             evaluator: str = "Z1") -> IntakeRecord:
        if any(c.cycle_number == cycle_number for c in self.cycles):
            raise ValueError(f"cycle {cycle_number} already published")
        prior = self.cycles[-1].receipt_hash if self.cycles else None
        now = utcnow()
        return IntakeRecord(
            intake_id=f"intake-{self.specimen_id}-c{cycle_number}-{now.strftime('%Y%m%dT%H%M%SZ')}",
            cycle_number=cycle_number, specimen_id=self.specimen_id, timestamp=now,
            evaluator=evaluator, evaluation_status=EvaluationStatus.PENDING,
            specimen_input=specimen_input, behavioral_observations=behavioral_observations,
            chain_link_prior=prior,
        )

    # -- forecasts ------------------------------------------------------------

    def _forecast_quality(self, obs: BehavioralObservations) -> float:
        if obs.quality_score is not None:
            base = obs.quality_score / 100.0
        else:
            base = obs.guideline_adherence * 0.8 + (1 - obs.error_rate) * 0.2
        drift = {ImprovementTrajectory.IMPROVING: 0.02, ImprovementTrajectory.DECLINING: -0.05}.get(
            obs.improvement_trajectory, 0.0)
        raw = base + drift
        return max(0.0, min(1.0, (1 - self.SHRINK) * raw + self.SHRINK * self.PRIOR_QUALITY))

    def _forecast_acceptance(self, obs: BehavioralObservations) -> float:
        raw = obs.task_acceptance_rate
        return max(0.0, min(1.0, (1 - self.SHRINK) * raw + self.SHRINK * self.PRIOR_ACCEPTANCE))

    def generate_molt_predictions(self, record: IntakeRecord) -> List[MoltPrediction]:
        obs = record.behavioral_observations
        now = utcnow()
        preds = [
            MoltPrediction(
                prediction_id=f"molt-{record.intake_id}-rq1-quality", variable="task_quality_score",
                prediction_value=self._forecast_quality(obs), confidence=0.7, measurement_window_days=7,
                predicted_at=now, scale_max=100.0,
                revert_rule=RevertRule("abs_below", 0.20),      # actual > 20 points below forecast
            ),
            MoltPrediction(
                prediction_id=f"molt-{record.intake_id}-rq2-acceptance", variable="task_acceptance_rate",
                prediction_value=self._forecast_acceptance(obs), confidence=0.65, measurement_window_days=14,
                predicted_at=now, scale_max=1.0,
                revert_rule=RevertRule("abs_below", 0.10),
            ),
            MoltPrediction(
                prediction_id=f"molt-{record.intake_id}-rq3-improvement", variable="improvement_trajectory",
                prediction_value=1.0 if obs.improvement_trajectory == ImprovementTrajectory.IMPROVING else 0.0,
                confidence=0.6, measurement_window_days=30, predicted_at=now, binary=True,
                revert_rule=RevertRule("equals", 0.0),           # trajectory did not improve
            ),
        ]
        record.molt_predictions = preds
        return preds

    # -- CredPolicy -------------------------------------------------------------

    def generate_credpolicy_recommendation(self, record: IntakeRecord) -> CredPolicyOutput:
        obs = record.behavioral_observations
        engagement = obs.task_acceptance_rate * 30
        quality = (obs.quality_score / 100 * 30) if obs.quality_score is not None else 15
        consistency = (1 - obs.annotation_variance) * 20
        learning = obs.revision_acceptance_rate * 20 if obs.improvement_trajectory == ImprovementTrajectory.IMPROVING else 0
        priority = engagement + quality + consistency + learning

        tasks: List[str] = []
        if obs.task_acceptance_rate > 0.8:
            tasks.append("high-complexity-annotation")
        if obs.guideline_adherence > 0.9:
            tasks.append("output-evaluation")
        if obs.improvement_trajectory == ImprovementTrajectory.IMPROVING:
            tasks.append("feedback-incorporation")
        if not tasks:
            tasks = ["general-annotation"]

        si = record.specimen_input
        completion = si.tasks_completed / max(si.tasks_assigned, 1)
        envelope = ("max 30 hours/week, prioritize high-complexity" if completion > 0.95
                    else "max 25 hours/week" if completion > 0.80
                    else "reduce to 15 hours/week, focus on completion rate")

        out = CredPolicyOutput(
            priority_score=priority, recommended_next_tasks=tasks, envelope_constraint=envelope,
            rationale=(f"Engagement {obs.task_acceptance_rate:.1%}, Quality {obs.quality_score if obs.quality_score is not None else 'pending'}, "
                       f"Consistency {1 - obs.annotation_variance:.1%}, Trajectory {obs.improvement_trajectory.value}"),
            predicted_choice=tasks[0], registered_at=utcnow(),
        )
        record.credential_policy_output = out
        return out

    # -- receipts & ratification --------------------------------------------------

    def compute_receipt(self, record: IntakeRecord) -> Tuple[str, ReceiptStatus]:
        if not record.molt_predictions or record.credential_policy_output is None:
            raise RuntimeError("receipt requires predictions and CredPolicy output to be registered first")
        record.receipt_hash = record.compute_hash()
        # RT-08: evidence tier is earned, not asserted.
        record.receipt_status = (ReceiptStatus.CLAIM_WITH_LINK if record.specimen_input.verification_sources
                                 else ReceiptStatus.CLAIM)
        record.evaluation_status = EvaluationStatus.PRELIMINARY
        return record.receipt_hash, record.receipt_status

    @staticmethod
    def ratification_hash_for(receipt_hash: str, ratified_by: str, ratified_at: datetime) -> str:
        """What Z2 signs: binds identity + time to the receipt. Z2 produces this value
        out-of-band and supplies it; code only checks it."""
        return hashlib.sha256(f"{receipt_hash}|{ratified_by}|{ratified_at.isoformat()}".encode()).hexdigest()

    def ratify(self, record: IntakeRecord, ratified_by: str, ratified_at: datetime, ratification_hash: str) -> None:
        if record.receipt_hash is None:
            raise RatificationError("no receipt to ratify")
        if record.compute_hash() != record.receipt_hash:
            raise RatificationError("record mutated since receipt was issued")
        expected = self.ratification_hash_for(record.receipt_hash, ratified_by, ratified_at)
        if ratification_hash != expected:
            raise RatificationError("ratification hash does not bind to this receipt")
        record.ratification_hash, record.ratified_by, record.ratified_at = ratification_hash, ratified_by, ratified_at
        record.evaluation_status = EvaluationStatus.VERIFIED

    def publish_record(self, record: IntakeRecord) -> bool:
        """RT-03: publishing requires a ratification hash, not a status flag."""
        if record.ratification_hash is None or record.evaluation_status != EvaluationStatus.VERIFIED:
            return False
        if record.compute_hash() != record.receipt_hash:
            return False
        record.evaluation_status = EvaluationStatus.PUBLISHED
        self.cycles.append(record)
        self._nf_write(record)
        self._molt_event("INTAKE_PUBLISHED", record)
        return True

    # -- measurement ----------------------------------------------------------

    def resolve_cycle(self, record: IntakeRecord, actual_quality: Optional[float],
                      actual_acceptance: float, actual_trajectory: ImprovementTrajectory,
                      actual_choice: str) -> Dict:
        """Called at window close with observed values. Mechanical: emits MEASURE,
        REVERT events and F/IC candidates without discretion (RT-06)."""
        if record.evaluation_status != EvaluationStatus.PUBLISHED:
            raise RuntimeError("only published records are measured")
        raw = {
            "task_quality_score": actual_quality if actual_quality is not None else None,
            "task_acceptance_rate": actual_acceptance,
            "improvement_trajectory": 1.0 if actual_trajectory == ImprovementTrajectory.IMPROVING else 0.0,
        }
        reverted_ids = []
        for p in record.molt_predictions:
            if raw[p.variable] is None:
                continue
            _, rev = p.resolve(raw[p.variable])
            if rev:
                reverted_ids.append(p.prediction_id)
        record.credential_policy_output.record_actual(actual_choice)
        self._nf_write(record, update=True)
        self._molt_event("MEASURE", record, resolution_hash=record.resolution_hash())
        for pid in reverted_ids:
            record.evaluation_status = EvaluationStatus.REVERTED
            self._molt_event("REVERT", record, prediction_id=pid)
            self.fic_candidates.append({
                "kind": "IC", "source": pid, "cycle": record.cycle_number,
                "claim": "forecast tripped its revert rule; predictor constant under suspicion",
                "falsifier": "next cycle's forecast on the same variable resolves inside its revert band",
            })
        return {"brier": [p.brier_score for p in record.molt_predictions],
                "reverted": reverted_ids,
                "credpolicy_agreement": record.credential_policy_output.agreement}

    # -- ledgers -----------------------------------------------------------------

    def _nf_write(self, record: IntakeRecord, update: bool = False) -> None:
        if update:
            self.nf_ledger = [e for e in self.nf_ledger if e["intake_id"] != record.intake_id]
        for p in record.molt_predictions:
            self.nf_ledger.append({
                "molt_id": p.prediction_id, "intake_id": record.intake_id, "cycle": record.cycle_number,
                "variable": p.variable, "prediction_value": p.prediction_value, "confidence": p.confidence,
                "predicted_at": p.predicted_at.isoformat(),
                "resolved_at": p.resolved_at.isoformat() if p.resolved_at else None,
                "actual_value": p.actual_value, "brier_score": p.brier_score, "reverted": p.reverted,
                "specimen_id": record.specimen_id,
            })

    def _molt_event(self, event_type: str, record: IntakeRecord, **extra) -> None:
        prev = self.molt_events[-1]["event_hash"] if self.molt_events else None
        ev = {
            "event_type": event_type, "cycle": record.cycle_number, "intake_id": record.intake_id,
            "timestamp": utcnow().isoformat(), "receipt_hash": record.receipt_hash,
            "chain_link_prior": record.chain_link_prior, "ratification_hash": record.ratification_hash,
            "credpolicy_agreement": record.credential_policy_output.agreement if record.credential_policy_output else None,
            "specimen_id": record.specimen_id, "prev_event_hash": prev, **extra,
        }
        ev["event_hash"] = hashlib.sha256(json.dumps(ev, sort_keys=True, default=str).encode()).hexdigest()
        self.molt_events.append(ev)

    # -- falsifiers ------------------------------------------------------------

    def average_brier(self, variable: Optional[str] = None) -> Optional[float]:
        s = [e["brier_score"] for e in self.nf_ledger
             if e["brier_score"] is not None and (variable is None or e["variable"] == variable)]
        return sum(s) / len(s) if s else None

    def revert_rate(self) -> Optional[float]:
        resolved = [e for e in self.nf_ledger if e["brier_score"] is not None]
        return (sum(1 for e in resolved if e["reverted"]) / len(resolved)) if resolved else None

    def falsifier_check(self) -> List[str]:
        out = []
        resolved_cycles = sorted({e["cycle"] for e in self.nf_ledger if e["brier_score"] is not None})
        # RQ1: after 10 resolved predictions, mean Brier > 0.4 or REVERT rate > 30%
        n_resolved = sum(1 for e in self.nf_ledger if e["brier_score"] is not None)
        if n_resolved >= 10:
            b, r = self.average_brier(), self.revert_rate()
            if b is not None and b > 0.4:
                out.append(f"RQ1_FALSIFIER: mean Brier {b:.3f} > 0.4 over {n_resolved} resolved forecasts")
            if r is not None and r > 0.30:
                out.append(f"RQ1_FALSIFIER: REVERT rate {r:.1%} > 30%")
        # RQ2: agreement < 60% on 3+ consecutive measured cycles
        measured = [e for e in self.molt_events if e["event_type"] == "MEASURE"]
        if len(measured) >= 3:
            last3 = [e["credpolicy_agreement"] for e in measured[-3:]]
            if all(a is not None for a in last3) and sum(last3) / 3 < 0.6:
                out.append("RQ2_FALSIFIER: CredPolicy agreement < 60% on 3 consecutive cycles")
        # RQ3: no quality improvement in 2 consecutive cycles
        q = {}
        for c in self.cycles:
            if c.behavioral_observations.quality_score is not None:
                q[c.cycle_number] = c.behavioral_observations.quality_score
        ks = sorted(q)
        if len(ks) >= 3:
            d1, d2 = q[ks[-2]] - q[ks[-3]], q[ks[-1]] - q[ks[-2]]
            if d1 <= 0 and d2 <= 0:
                out.append("RQ3_FALSIFIER: no quality improvement in 2 consecutive cycles")
        return out


# ============================================================================
# EXAMPLE (synthetic; no legal name or contract id — RT-07)
# ============================================================================

def example_cycle_1() -> ResearchIntakeEvaluator:
    ev = ResearchIntakeEvaluator(specimen_id="SPC-01")
    si = SpecimenInput(datetime(2026, 9, 13, tzinfo=timezone.utc), datetime(2026, 9, 19, tzinfo=timezone.utc),
                       platform="micro1", tasks_assigned=25, tasks_completed=24, tasks_revised=3,
                       task_categories=["data-pipeline-annotation", "output-comparison", "response-writing"])
    obs = BehavioralObservations(0.96, 0.25, 12.5, 87.0, 0.94, 0.08, 0.06, 0.67,
                                 ImprovementTrajectory.IMPROVING, "increasing")
    rec = ev.create_intake_record(1, si, obs)
    ev.generate_molt_predictions(rec)
    ev.generate_credpolicy_recommendation(rec)
    receipt, status = ev.compute_receipt(rec)

    # Z2 ratifies OUT OF BAND by producing this hash over the receipt. Simulated here.
    t = utcnow()
    ev.ratify(rec, "Z2", t, ResearchIntakeEvaluator.ratification_hash_for(receipt, "Z2", t))
    assert ev.publish_record(rec)

    print("=== CYCLE 1 (synthetic) ===")
    print(f"intake {rec.intake_id}  status {rec.evaluation_status.value}  receipt {status.value} {receipt[:16]}…")
    for p in rec.molt_predictions:
        print(f"  {p.variable:24s} forecast {p.prediction_value:.3f}  conf {p.confidence:.2f}  window {p.measurement_window_days}d")
    cp = rec.credential_policy_output
    print(f"  CredPolicy priority {cp.priority_score:.1f}  predicted_choice {cp.predicted_choice}")
    return ev


if __name__ == "__main__":
    example_cycle_1()
