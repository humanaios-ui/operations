"""Executable stress evaluator for H-COLLAB-HARMONY-01.

ChatGPT/GPT-5.6 Sol contribution.
Authority effect: NONE.
Standing: Z1 research prototype.

Design rule: gate first, score second.

v0.2 receipt integration:
- raw `verified_gate_refs` are no longer trusted;
- each gate cites typed receipt IDs;
- receipts must resolve through a pinned append-only receipt chain;
- receipt subject/action/scope must match the gate and run;
- stub/simulated receipt methods fail closed.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from tools.verified_receipts import ReceiptRequirement, VerifiedReceiptResolver


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
    run_id: str = "default"

    # Gate claims remain explicit observations to be tested.
    human_autonomy_preserved: bool = True
    dissent_preserved: bool = True
    uncertainty_visible: bool = True
    provenance_complete: bool = True
    authority_not_laundered: bool = True
    refusal_respected: bool = True
    identity_minimized: bool = True

    # Each gate cites one or more receipt IDs.
    gate_evidence: Dict[str, List[str]] = field(default_factory=dict)

    # Fed by the Bridge / Evidence Graph. The trusted head is deliberately
    # NOT part of RunState; it must enter evaluate() through a separate trust
    # boundary.
    receipt_events: List[Dict[str, Any]] = field(default_factory=list)

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


def _resolver(
    state: RunState,
    trusted_receipt_head_hash: Optional[str],
) -> Optional[VerifiedReceiptResolver]:
    if not state.receipt_events or not trusted_receipt_head_hash:
        return None
    return VerifiedReceiptResolver(state.receipt_events, trusted_receipt_head_hash)


def gate_failures(
    state: RunState,
    trusted_receipt_head_hash: Optional[str],
) -> List[str]:
    failures: List[str] = []
    resolver = _resolver(state, trusted_receipt_head_hash)

    for gate in HARD_GATES:
        if not bool(getattr(state, gate)):
            failures.append(f"FAIL:{gate}")
            continue

        receipt_ids = state.gate_evidence.get(gate, [])
        if not receipt_ids:
            failures.append(f"NO_GATE:{gate}")
            continue

        if resolver is None:
            failures.append(f"UNVERIFIED_GATE:{gate}:NO_RECEIPT_FEED")
            continue

        requirement = ReceiptRequirement(
            receipt_type="HARMONY_GATE",
            subject=gate,
            action="ASSERT_GATE",
            scope=f"run:{state.run_id}",
            min_strength="OBSERVED",
        )

        reasons: List[str] = []
        passed = False
        for receipt_id in receipt_ids:
            result = resolver.resolve(receipt_id, requirement)
            if result.valid:
                passed = True
                break
            reasons.append(result.reason or "UNKNOWN")

        if not passed:
            reason = reasons[-1] if reasons else "NO_MATCHING_RECEIPT"
            failures.append(f"UNVERIFIED_GATE:{gate}:{reason}")

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
        "receipt_ids": state.gate_evidence.get("dissent_preserved", []),
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
    semantic = max(0.0, state.semantic_information_gain)
    identity = max(0.0, state.identity_information_gain)
    if semantic == 0:
        return 0.0
    if identity == 0:
        return 1.0
    return _bounded(semantic / (semantic + identity))


def evaluate(
    state: RunState,
    *,
    trusted_receipt_head_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate collaboration state against an independently supplied receipt head."""
    failures = gate_failures(state, trusted_receipt_head_hash)

    if failures:
        return {
            "verdict": "INVALID_HARMONY",
            "score": 0.0,
            "gate_failures": failures,
            "receipt_head_hash": trusted_receipt_head_hash,
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
        "receipt_head_hash": trusted_receipt_head_hash,
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
