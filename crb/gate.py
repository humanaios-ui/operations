"""Mechanical gate and independence policy for CRB prototype.

No model calls. No HumanAIOS service calls. No discretionary interpretation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

SUPPORTED = "SUPPORTED"
ADVANCE = "ADVANCE"
HOLD = "HOLD_REVISE_RETEST"

CLASSIFICATIONS = {
    "SELF_REVIEW",
    "INTERNAL_MACHINE_INDEPENDENT",
    "EXTERNALLY_REPLAYED",
    "THIRD_PARTY_REVIEWED",
}

RID_DIMS = ("S", "C", "T", "O", "D")
PROFILES = {
    "SELF_REVIEW": {"S": 0, "C": 0, "T": 0, "O": 0, "D": 0},
    "INTERNAL_MACHINE_INDEPENDENT": {"S": 1, "C": 2, "T": 1, "O": 0, "D": 1},
    "EXTERNALLY_REPLAYED": {"S": 1, "C": 2, "T": 1, "O": 2, "D": 1},
    "THIRD_PARTY_REVIEWED": {"S": 1, "C": 2, "T": 1, "O": 2, "D": 2},
}

DISQUALIFIERS = {
    "FIRST_PASS_CONTEXT_LEAK",
    "EVIDENCE_BUNDLE_HASH_MISMATCH",
    "REVIEW_CONTRACT_MUTATED_AFTER_START",
    "HIDDEN_SHARED_SUMMARY",
    "UNDECLARED_OPERATOR_SUBSTITUTION",
}


@dataclass(frozen=True)
class IndependenceResult:
    satisfied: bool
    deficits: tuple[str, ...]
    disqualifiers: tuple[str, ...]


def evaluate_independence(
    rid: Mapping[str, int],
    profile: str,
    *,
    disqualifiers: Iterable[str] = (),
    external_replay_performed: bool = False,
    third_party_controls_reviewer_selection: bool = False,
    third_party_controls_publication: bool = False,
) -> IndependenceResult:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}")

    deficits: list[str] = []
    for dim in RID_DIMS:
        value = rid.get(dim)
        if not isinstance(value, int) or value not in (0, 1, 2):
            deficits.append(f"{dim}:invalid")
            continue
        minimum = PROFILES[profile][dim]
        if value < minimum:
            deficits.append(f"{dim}:{value}<{minimum}")

    bad = tuple(sorted(set(disqualifiers) & DISQUALIFIERS))

    if profile == "EXTERNALLY_REPLAYED" and not external_replay_performed:
        deficits.append("external_replay:not_performed")

    if profile == "THIRD_PARTY_REVIEWED":
        if not external_replay_performed:
            deficits.append("external_replay:not_performed")
        if not third_party_controls_reviewer_selection:
            deficits.append("third_party:reviewer_selection_not_controlled")
        if not third_party_controls_publication:
            deficits.append("third_party:publication_not_controlled")

    return IndependenceResult(
        satisfied=not deficits and not bad,
        deficits=tuple(deficits),
        disqualifiers=bad,
    )


def compute_gate(
    seat_verdicts: Sequence[str],
    *,
    evidence_integrity: str,
    process_integrity: str,
    independence_satisfied: bool,
    unresolved_critical_challenges: int,
) -> str:
    if len(seat_verdicts) != 3:
        return HOLD
    if any(v != SUPPORTED for v in seat_verdicts):
        return HOLD
    if evidence_integrity != "VALID":
        return HOLD
    if process_integrity != "VALID":
        return HOLD
    if not independence_satisfied:
        return HOLD
    if unresolved_critical_challenges != 0:
        return HOLD
    return ADVANCE
