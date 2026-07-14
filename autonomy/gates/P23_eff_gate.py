"""
P23_eff_gate.py — External Framework Filter, as a state machine.

GOVERNANCE.md text: "When engaging a collaborator's governance framework,
apply it as a diagnostic lens... Document what surfaces. Treat findings
as Zone 2 candidates for ratification, not automatic implementations...
EFF findings never self-execute. EFF findings never enter external
communications without Night ratification."

Codes the trigger-detection and the communication-refusal. Does NOT
judge whether an external framework is a genuine hybrid signal — that's
the interpretive core P23 leaves to Night, same as P25's 3-signal
heuristic remains a human read, not a formula this module evaluates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class TriggerType(Enum):
    COLLABORATOR_GOVERNANCE_DOC = "collaborator_produces_governance_document"
    EXTERNAL_FRAMEWORK_REVIEW = "external_research_framework_reviewed"
    RETROSPECTIVE_CASE_ANALYSIS = "retrospective_case_analysis"


class EFFState(Enum):
    DETECTED = "trigger_detected"
    SURFACED = "surfaces_documented"          # Claude's output: named list of what surfaced
    RATIFIED_FOR_COMMS = "ratified_for_external_comms"
    HELD_INTERNAL = "held_internal_only"       # default terminal state without ratification


class EFFGateError(Exception):
    """Hard-reject: 'EFF findings never enter external communications
    without Night ratification' — enforced as a code path, not a reminder."""


@dataclass
class EFFFinding:
    finding_id: str
    trigger: TriggerType
    surfaced_items: list                       # the named list P23 requires as output
    state: EFFState = EFFState.DETECTED
    ratifier: str | None = None
    history: list = field(default_factory=list)

    def _log(self, event: str):
        self.history.append({"event": event, "at": datetime.now(timezone.utc).isoformat()})


def detect_trigger(finding_id: str, trigger: TriggerType) -> EFFFinding:
    f = EFFFinding(finding_id=finding_id, trigger=trigger, surfaced_items=[])
    f._log(f"DETECTED — {trigger.value}")
    return f


def surface(finding: EFFFinding, surfaced_items: list) -> EFFFinding:
    """Claude's required output per P23: a NAMED list of what the external
    framework revealed. An empty list is not a valid surfacing — refuses."""
    if finding.state != EFFState.DETECTED:
        raise EFFGateError(f"{finding.finding_id} already surfaced (state={finding.state})")
    if not surfaced_items:
        raise EFFGateError("REFUSED: surfacing requires a named list — empty list is not valid output")
    finding.surfaced_items = surfaced_items
    finding.state = EFFState.SURFACED
    finding._log(f"SURFACED {len(surfaced_items)} item(s): {surfaced_items}")
    return finding


def ratify_for_external_comms(finding: EFFFinding, ratifier: str, decision: bool) -> EFFFinding:
    if finding.state != EFFState.SURFACED:
        raise EFFGateError(f"{finding.finding_id} not awaiting comms ratification (state={finding.state})")
    finding.ratifier = ratifier
    finding.state = EFFState.RATIFIED_FOR_COMMS if decision else EFFState.HELD_INTERNAL
    finding._log(f"{'RATIFIED_FOR_COMMS' if decision else 'HELD_INTERNAL'} by {ratifier}")
    return finding


def send_external(finding: EFFFinding, channel: str) -> str:
    """The actual send. Hard-refuses anything not explicitly ratified —
    HELD_INTERNAL and SURFACED both refuse here, DETECTED refuses too."""
    if finding.state != EFFState.RATIFIED_FOR_COMMS:
        raise EFFGateError(
            f"REFUSED: {finding.finding_id} cannot go to '{channel}' — state is {finding.state}, "
            f"not RATIFIED_FOR_COMMS. EFF findings never self-execute (P23)."
        )
    finding._log(f"SENT to {channel}")
    return f"sent to {channel}"


if __name__ == "__main__":
    # Real trigger from this session: applying the Journal of Learning Analytics
    # "collaboration analytics" conceptual model as a diagnostic lens on
    # HumanAIOS's own production_li / functional_node_id schema — exactly
    # P23's "external research framework reviewed for alignment" condition.
    print("── Case 1: attempt to send before ratification, correctly refused ──")
    f1 = detect_trigger("EFF-COLLAB-ANALYTICS-01", TriggerType.EXTERNAL_FRAMEWORK_REVIEW)
    surface(f1, [
        "Gašević et al. 2021 feedback-loop model maps onto §5's verification gate directly",
        "functional_node_id / production_li fields exist in schema but 0 populated rows (live-queried) — "
        "framework applied to real data surfaced a gap the WGS narrative didn't mention",
    ])
    try:
        send_external(f1, channel="public-pr-comment")
    except EFFGateError as e:
        print(f"  send_external() correctly refused: {e}")

    print("\n── Case 2: properly ratified, then sends ──")
    ratify_for_external_comms(f1, ratifier="night", decision=True)
    result = send_external(f1, channel="public-pr-comment")
    print(f"  {result}")
    for h in f1.history:
        print(f"    {h['at']}  {h['event']}")

    print("\n── Case 3: Night declines — held internal, still refuses to send ──")
    f2 = detect_trigger("EFF-COLLAB-ANALYTICS-02", TriggerType.EXTERNAL_FRAMEWORK_REVIEW)
    surface(f2, ["draft comparison, not yet reviewed"])
    ratify_for_external_comms(f2, ratifier="night", decision=False)
    try:
        send_external(f2, channel="public-pr-comment")
    except EFFGateError as e:
        print(f"  send_external() correctly refused: {e}")
