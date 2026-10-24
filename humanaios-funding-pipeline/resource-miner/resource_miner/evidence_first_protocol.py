"""Read-only, deterministic Witness feedback projection.

This module never grants authority, executes actions, or changes opportunity status.
The caller supplies already-redacted references; no raw private text is persisted.
"""
from dataclasses import dataclass
from typing import Literal

EvidenceState = Literal["OBSERVED", "SUPPORTED", "INFERRED", "HYPOTHESIZED", "UNVERIFIED", "CONTRADICTED"]
FeedbackKind = Literal["SOURCE_CORRECTION", "INTENT_CORRECTION", "QUESTION", "CONDITIONAL_WILLINGNESS"]

@dataclass(frozen=True)
class WitnessFeedback:
    case_id: str
    kind: FeedbackKind
    source_state: EvidenceState
    source_ref: str
    correction: str
    intent_ref: str = ""
    authority: str = "NONE"
    execution: str = "DISABLED"

    def __post_init__(self):
        if not self.case_id or not self.source_ref:
            raise ValueError("case_id and source_ref are required")
        if self.kind not in ("SOURCE_CORRECTION", "INTENT_CORRECTION", "QUESTION", "CONDITIONAL_WILLINGNESS"):
            raise ValueError("Unsupported Witness feedback kind")
        if self.source_state not in ("OBSERVED", "SUPPORTED", "INFERRED", "HYPOTHESIZED", "UNVERIFIED", "CONTRADICTED"):
            raise ValueError("Unsupported Witness source state")
        if self.authority != "NONE" or self.execution != "DISABLED":
            raise ValueError("Witness feedback cannot grant authority or execution")

def project_feedback(record: WitnessFeedback) -> dict:
    """Return a public-safe projection, excluding correction and private intent text.

    The caller must ensure case_id and source_ref are public-safe identifiers.
    """
    return {
        "case_id": record.case_id,
        "kind": record.kind,
        "source_state": record.source_state,
        "source_ref": record.source_ref,
        "has_correction": bool(record.correction),
        "has_intent_reference": bool(record.intent_ref),
        "authority": "NONE",
        "execution": "DISABLED",
        "requires_human_review": True,
    }

