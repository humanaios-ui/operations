"""
P29_articulation_gate.py — Articulation Gate, as a state machine.

GOVERNANCE.md text: "Before producing any Zone 2-destined artifact...
the producing substrate must explicitly state: (1) what the artifact is
and what it does, (2) what evidence supports its claims, and (3) what
the risk of being wrong is and how it would be detected... Human (Night)
ratification remains the external reference point that validates
articulation quality; automated scoring of articulation is not a
substitute for this."

This is the one gate whose own text names the scope limit explicitly.
So this module deliberately does NOT score articulation quality — it
only checks PRESENCE of the three required fields, non-trivially filled.
Depth/quality judgment stays Night's, exactly as P29 requires.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

MIN_WORDS = 5  # presence check only — "non-trivial," not "good." No quality scoring here.


class ArtifactState(Enum):
    DRAFTED = "drafted"
    ARTICULATED = "articulation_present"
    ELIGIBLE_FOR_Z2 = "eligible_for_zone2"
    Z2_RATIFIED = "zone2_ratified"


class ArticulationGateError(Exception):
    """Hard-reject: mirrors P29's own text — presence of the three fields
    is mechanically checkable; whether they're GOOD is not this module's call."""


@dataclass
class Artifact:
    artifact_id: str
    description: str
    state: ArtifactState = ArtifactState.DRAFTED
    what_it_is: str | None = None
    evidence: str | None = None
    risk_and_detection: str | None = None
    ratifier: str | None = None
    history: list = field(default_factory=list)

    def _log(self, event: str):
        self.history.append({"event": event, "at": datetime.now(timezone.utc).isoformat()})


def draft(artifact_id: str, description: str) -> Artifact:
    a = Artifact(artifact_id=artifact_id, description=description)
    a._log("DRAFTED")
    return a


def _non_trivial(text: str | None) -> bool:
    return bool(text) and len(text.split()) >= MIN_WORDS


def articulate(artifact: Artifact, what_it_is: str, evidence: str, risk_and_detection: str) -> Artifact:
    """The three-part statement P29 requires, checked for PRESENCE only.
    A one-word non-answer in any field refuses — but a five-word answer
    that is technically present but shallow is NOT caught here, by design;
    that's the quality judgment P29 reserves for Night."""
    if artifact.state != ArtifactState.DRAFTED:
        raise ArticulationGateError(f"{artifact.artifact_id} already articulated (state={artifact.state})")

    missing = [
        name for name, val in
        [("what_it_is", what_it_is), ("evidence", evidence), ("risk_and_detection", risk_and_detection)]
        if not _non_trivial(val)
    ]
    if missing:
        raise ArticulationGateError(
            f"REFUSED: articulation incomplete for {artifact.artifact_id} — missing/trivial field(s): {missing}"
        )

    artifact.what_it_is = what_it_is
    artifact.evidence = evidence
    artifact.risk_and_detection = risk_and_detection
    artifact.state = ArtifactState.ARTICULATED
    artifact._log("ARTICULATED")
    return artifact


def submit_to_zone2(artifact: Artifact) -> Artifact:
    if artifact.state != ArtifactState.ARTICULATED:
        raise ArticulationGateError(
            f"REFUSED: {artifact.artifact_id} cannot reach Zone 2 — state is {artifact.state}, "
            f"not ARTICULATED (P29)."
        )
    artifact.state = ArtifactState.ELIGIBLE_FOR_Z2
    artifact._log("ELIGIBLE_FOR_Z2")
    return artifact


def night_ratifies_articulation(artifact: Artifact, ratifier: str, decision: bool) -> Artifact:
    """This is the actual quality check — a human judgment call, not automatable.
    The calibration-circularity guard in P29's own text means no ACAT-adjacent
    score is allowed to stand in for this call."""
    if artifact.state != ArtifactState.ELIGIBLE_FOR_Z2:
        raise ArticulationGateError(f"{artifact.artifact_id} not awaiting Z2 review (state={artifact.state})")
    artifact.ratifier = ratifier
    if decision:
        artifact.state = ArtifactState.Z2_RATIFIED
        artifact._log(f"Z2_RATIFIED by {ratifier}")
    else:
        artifact.state = ArtifactState.DRAFTED  # sent back — must re-articulate
        artifact._log(f"REJECTED by {ratifier} — returned to DRAFTED")
    return artifact


if __name__ == "__main__":
    # Real artifact from this session: reference_linter.py itself, articulated
    # the way it should have been stated before being presented as a Zone 1 draft.
    print("── Case 1: missing risk field, correctly refused ──")
    a1 = draft("reference_linter_v0_1", "canonical-URL liveness sweep across 4 governance files")
    try:
        articulate(
            a1,
            what_it_is="A script that extracts raw.githubusercontent.com URLs from governance files and fetches each.",
            evidence="Real run this session: 5 LIVE, 1 DEAD, independently reproduced the PRINCIPLES_SEED.md finding.",
            risk_and_detection="no",  # trivial — should refuse
        )
    except ArticulationGateError as e:
        print(f"  articulate() correctly refused: {e}")

    print("\n── Case 2: properly articulated, reaches Z2, Night ratifies ──")
    a2 = draft("reference_linter_v0_1", "canonical-URL liveness sweep across 4 governance files")
    articulate(
        a2,
        what_it_is="A script that extracts raw.githubusercontent.com URLs from governance files and fetches each with a real HTTP call.",
        evidence="Real run this session: 5 LIVE, 1 DEAD, independently reproduced the PRINCIPLES_SEED.md finding without being pointed at it.",
        risk_and_detection="Only catches one URL pattern; misses prose claims without a URL. Detected by comparing scan coverage against a manual read, which is how this gap was found in the first place.",
    )
    submit_to_zone2(a2)
    night_ratifies_articulation(a2, ratifier="night", decision=True)
    print(f"  final state: {a2.state.value}")
    for h in a2.history:
        print(f"    {h['at']}  {h['event']}")
