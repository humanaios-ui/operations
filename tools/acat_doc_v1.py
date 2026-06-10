
from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict, Any

EvidentiaryLabel = Literal["Factual", "Mixed", "Interpretive"]
CalibrationStrength = Literal["High", "Moderate", "Low"]
ConfidenceLevel = Literal["High", "Moderate", "Low"]
ScoreBasis = Literal["Text-internal", "Text + context"]

@dataclass
class EvidenceRow:
    section_passage: str
    concrete_examples: str
    supported_dimensions: List[str]
    evidentiary_label: EvidentiaryLabel
    exploratory_note: str = ""
    counterevidence: str = ""

@dataclass
class P3Scores:
    truth: Optional[int] = None
    service: Optional[int] = None
    harm: Optional[int] = None
    autonomy: Optional[int] = None
    value: Optional[int] = None
    humility: Optional[int] = None
    scheme: Optional[int] = None
    power: Optional[int] = None
    syc: Optional[int] = None
    consist: Optional[int] = None
    fair: Optional[int] = None
    handoff: Optional[int] = None

@dataclass
class DimensionSummary:
    agent: str
    p3: P3Scores = field(default_factory=P3Scores)
    overall_learning_index: Optional[float] = None
    score_basis: ScoreBasis = "Text-internal"

@dataclass
class Verdict:
    calibration_strength: CalibrationStrength
    confidence_level: ConfidenceLevel
    verdict: str

@dataclass
class ACATDocReport:
    document_id_title: str
    date_version: str
    document_type: str
    analyst: str
    core_claim_mission: str
    analytic_scope: str
    method_note: str
    evidence_analysis: List[EvidenceRow] = field(default_factory=list)
    dimension_summary: Optional[DimensionSummary] = None
    final_verdict: Optional[Verdict] = None
