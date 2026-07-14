"""
P21_finding_gate.py — Finding Registration Gate, as a state machine.

GOVERNANCE.md text: "No finding promoted from candidate to registered
without Zone 2 Night approval. Auto-F-class promotion is prohibited.
Claude proposes; Night decides."

This codes the TRIGGER and the REFUSAL, not the decision. Whether a
candidate finding is good enough to ratify is Night's judgment, exactly
as it is in mason_gate.py's inspect_stone() — this module never scores
finding quality, it only enforces that promotion cannot happen without
a distinct ratifier.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class FindingState(Enum):
    CANDIDATE = "candidate"                # Claude drafted, real, unregistered
    PROPOSED = "proposed_to_z2"            # Claude explicitly asked for ratification
    RATIFIED = "ratified_by_night"
    REJECTED = "rejected_by_night"
    REGISTERED = "registered_in_registered_md"  # terminal — append-only per REGISTERED.md's own rule


class FindingGateError(Exception):
    """Hard-reject: mirrors P21's 'auto-F-class promotion is prohibited.'
    No code path in this module can move CANDIDATE -> REGISTERED directly."""


@dataclass
class Finding:
    finding_id: str
    synopsis: str
    proposer: str                  # always Claude in this system's real usage
    state: FindingState = FindingState.CANDIDATE
    ratifier: str | None = None
    history: list = field(default_factory=list)

    def _log(self, event: str):
        self.history.append({"event": event, "at": datetime.now(timezone.utc).isoformat()})


def propose(finding_id: str, synopsis: str, proposer: str) -> Finding:
    """Claude's half of P21: draft and explicitly propose. Real work, not yet decided."""
    f = Finding(finding_id=finding_id, synopsis=synopsis, proposer=proposer)
    f.state = FindingState.PROPOSED
    f._log(f"PROPOSED by {proposer}")
    return f


def ratify(finding: Finding, ratifier: str, decision: bool) -> Finding:
    """Night's half of P21. decision is the actual judgment call — this function
    does not evaluate synopsis quality, it only enforces WHO is allowed to call
    this (must differ from proposer) and records the outcome."""
    if finding.state != FindingState.PROPOSED:
        raise FindingGateError(f"{finding.finding_id} is not awaiting Z2 decision (state={finding.state})")
    if ratifier == finding.proposer:
        raise FindingGateError(
            f"REFUSED: ratifier '{ratifier}' cannot equal proposer '{finding.proposer}' — "
            f"self-ratification is exactly what P21 exists to prevent."
        )
    finding.ratifier = ratifier
    finding.state = FindingState.RATIFIED if decision else FindingState.REJECTED
    finding._log(f"{'RATIFIED' if decision else 'REJECTED'} by {ratifier}")
    return finding


def register(finding: Finding) -> Finding:
    """Terminal step — append to REGISTERED.md. Hard-refuses anything
    that did not pass through a real, distinct ratifier."""
    if finding.state != FindingState.RATIFIED:
        raise FindingGateError(
            f"REFUSED: {finding.finding_id} cannot be registered — state is {finding.state}, "
            f"not RATIFIED. No auto-promotion path exists (P21)."
        )
    finding.state = FindingState.REGISTERED
    finding._log("REGISTERED (append-only)")
    return finding


if __name__ == "__main__":
    # Real candidate from this session: the dead PRINCIPLES_SEED.md canonical
    # reference, found by reference_linter.py's actual run (5 LIVE / 1 DEAD).
    print("── Case 1: attempted self-ratification, correctly refused ──")
    f1 = propose(
        "IC-CAND-PRINCIPLES-SEED-DEAD-REF",
        "CURRENT.md Class 0b still points to PRINCIPLES_SEED.md (404, confirmed live by reference_linter.py); "
        "file deleted per git history, CURRENT.md pointer table never updated.",
        proposer="unit-zero-claude",
    )
    try:
        ratify(f1, ratifier="unit-zero-claude", decision=True)
    except FindingGateError as e:
        print(f"  ratify() correctly refused: {e}")

    print("\n── Case 2: same finding, properly ratified by a distinct party ──")
    f2 = propose(
        "IC-CAND-PRINCIPLES-SEED-DEAD-REF",
        "CURRENT.md Class 0b still points to PRINCIPLES_SEED.md (404, confirmed live); "
        "file deleted per git history, pointer table never updated.",
        proposer="unit-zero-claude",
    )
    ratify(f2, ratifier="night", decision=True)
    register(f2)
    print(f"  final state: {f2.state.value}")
    for h in f2.history:
        print(f"    {h['at']}  {h['event']}")

    print("\n── Case 3: registering without ratification, correctly refused ──")
    f3 = propose("IC-CAND-EXAMPLE-02", "unratified example", proposer="unit-zero-claude")
    try:
        register(f3)
    except FindingGateError as e:
        print(f"  register() correctly refused: {e}")
