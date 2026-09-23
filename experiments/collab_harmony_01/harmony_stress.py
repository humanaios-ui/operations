"""Executable stress evaluator for H-COLLAB-HARMONY-01.

ChatGPT/GPT-5.6 Sol contribution.
Authority effect: NONE.
Standing: Z1 research prototype.

Design rule: gate first, score second.
A run cannot earn a high "harmony" score by suppressing dissent, laundering
authority, overriding refusal, erasing provenance, or increasing identity
resolution without necessity.

Stress corrections:
- v0.1.1: passing gates require evidence references.
- v0.1.2: evidence references must resolve into a separate verified receipt set.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


HARD_GATES = (
    "human_autonomy_preserved",
    "dissent_preserved",
    "uncertainty_visible",
    "provenance_complete",
    "authority_not_laundered",
    "refusal_respected",
    "identity_minimized",
)


@dataclass
class Contribution:
    participant_id: str
    participant_type: str
    observations: List[str] = field(default_factory=list)
    interpretations: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    disagreements: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    uncertainty: List[str] = field(default_factory=list)
    proposed_next_step: Optional[str] = None
    authority_effect: str = "NONE"
    refused: bool = False


@dataclass
class RunState:
    contributions: List[Contribution]

    # Gate claims are observations to be checked, not self-authenticating truth.
    human_autonomy_preserved: bool = True
    dissent_preserved: bool = True
    uncertainty_visible: bool = True
    provenance_complete: bool = True
    authority_not_laundered: bool = True
    refusal_respected: bool = True
    identity_minimized: bool = True

    # Passing gates cite events/receipts.
    gate_evidence: Dict[str, List[str]] = field(default_factory=dict)

    # Supplied by an external verifier / bridge receipt resolver.
    # The evaluator never upgrades a raw string into proof by itself.
    verified_gate_refs: List[str] = field(default_factory=list)

    mutual_understanding: float = 0.0
    complementarity: float = 0.0
    evidence_quality: float = 0.0
    coordination: float = 0.0
    collective_problem_solving: float = 0.0

    identity_information_gain: float = 0.0
    semantic_information_gain: float = 0.0

    notes: List[str] = field(default_factory=list)


def _bounded(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def gate_failures(state: RunState) -> List[str]:
    failures = []
    verified = set(state.verified_gate_refs)

    for gate in HARD_GATES:
        if not bool(getattr(state, gate)):
            failures.append(f"FAIL:{gate}")
            continue

        refs = state.gate_evidence.get(gate, [])
        if not refs:
            failures.append(f"NO_GATE:{gate}")
            continue

        if not any(ref in verified for ref in refs):
            failures.append(f"UNVERIFIED_GATE:{gate}")

    return failures


def disagreement_retention(state: RunState) -> Dict[str, Any]:
    total = sum(len(c.disagreements) for c in state.contributions)
    distinct = {
        item.strip()
        for c in state.contributions
        for item in c.disagreements
        if item.strip()
    }
    return {
        "reported_disagreements": total,
        "distinct_disagreements": len(distinct),
        "retained": state.dissent_preserved,
        "evidence_refs": state.gate_evidence.get("dissent_preserved", []),
    }


def independence_signal(state: RunState) -> Dict[str, Any]:
    """Structural signal only; never upgrades to proof of independence."""
    participants = {c.participant_id for c in state.contributions}
    types = {c.participant_type for c in state.contributions}
    return {
        "participant_count": len(participants),
        "participant_types": sorted(types),
        "independence_proven": False,
        "note": "Distinct participants/substrates are evidence, not proof of independent observation.",
    }


def identity_efficiency(state: RunState) -> float:
    """Semantic gain per unit of identity gain; higher is better."""
    semantic = max(0.0, state.semantic_information_gain)
    identity = max(0.0, state.identity_information_gain)
    if semantic == 0:
        return 0.0
    if identity == 0:
        return 1.0
    return _bounded(semantic / (semantic + identity))


def evaluate(state: RunState) -> Dict[str, Any]:
    failures = gate_failures(state)

    if failures:
        return {
            "verdict": "INVALID_HARMONY",
            "score": 0.0,
            "gate_failures": failures,
            "disagreement": disagreement_retention(state),
            "independence": independence_signal(state),
            "identity_efficiency": identity_efficiency(state),
            "notes": state.notes,
        }

    dimensions = {
        "mutual_understanding": _bounded(state.mutual_understanding),
        "complementarity": _bounded(state.complementarity),
        "evidence_quality": _bounded(state.evidence_quality),
        "coordination": _bounded(state.coordination),
        "collective_problem_solving": _bounded(state.collective_problem_solving),
    }
    score = sum(dimensions.values()) / len(dimensions)

    return {
        "verdict": "VALID_COHERENCE_CANDIDATE",
        "score": round(score, 4),
        "dimensions": dimensions,
        "gate_failures": [],
        "gate_evidence": state.gate_evidence,
        "verified_gate_refs": state.verified_gate_refs,
        "disagreement": disagreement_retention(state),
        "independence": independence_signal(state),
        "identity_efficiency": identity_efficiency(state),
        "notes": state.notes,
    }


def from_dict(payload: Dict[str, Any]) -> RunState:
    contributions = [Contribution(**item) for item in payload.get("contributions", [])]
    state_fields = {
        k: v for k, v in payload.items()
        if k != "contributions" and k in RunState.__dataclass_fields__
    }
    return RunState(contributions=contributions, **state_fields)
