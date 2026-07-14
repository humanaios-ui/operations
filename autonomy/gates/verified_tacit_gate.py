"""
verified_tacit_gate.py — Zone 1 proof-of-concept for the `verified_tacit`
verification tier (schema proposal below, code demonstration here).

Does NOT reimplement cap logic — imports carry_tracker_v1_0.run() directly
and reuses its exact WARN_THRESHOLD=5 / ESCALATE_THRESHOLD=10 semantics,
repointed at a different accumulation: not "sessions an item has carried"
but "unresolved tacit-tier claims a given verifier has made since their
last retrospective review." Same shape, different trigger — same pattern
already used for the four P-gates.

Design constraint this file exists to enforce: `verified_tacit` must
NEVER be treated as equal-strength to `verified_substantive`. It routes
to a retrospective-review queue (track-record validation, per Operator_HIM
and the task_outcomes/Gap A thread) rather than promoting corpus_eligible
directly. The cap prevents "tacit" from becoming an unlimited, unchecked
escape hatch for calls that simply weren't articulated.
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent))
import carry_tracker_v1_0 as carry_tracker  # real reuse, not reimplementation


class VerificationStatus(Enum):
    UNVERIFIED = "unverified"
    VERIFIED_PASSIVE = "verified_passive"           # existing tier, §5.2
    VERIFIED_SUBSTANTIVE = "verified_substantive"    # existing tier, §5.2
    VERIFIED_TACIT = "verified_tacit"                # NEW — this proposal


class TacitGateError(Exception):
    """Hard-reject: fires when a verifier's unresolved tacit-claim count
    crosses ESCALATE_THRESHOLD (10, reused from carry_tracker) without an
    intervening retrospective review. No new tacit claims accepted past
    that point — matches carry_tracker's own FAIL semantics exactly."""


@dataclass
class TacitClaim:
    claim_id: str
    verifier_id: str
    context: str                     # what was being verified
    made_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    routed_to: str = "pending_retrospective_review"   # NEVER pending_Z2 directly


# In-memory ledger for this demo — a real deployment would back this with
# the same Supabase table pattern used elsewhere this session.
_TACIT_LEDGER: dict[str, list[TacitClaim]] = {}


def claim_tacit(claim_id: str, verifier_id: str, context: str) -> TacitClaim:
    """A verifier makes an explicit tacit claim: confident, real judgment,
    fails the specificity check (§5.1's _justification_is_specific), not
    because it's weak but because it's compressed below articulation —
    the Expert Blind Spot pattern, not evasion. This function does not
    evaluate whether that's true; it only records the claim and checks
    the cap via carry_tracker's real logic.

    Cap is checked BEFORE the claim is committed to the ledger — a refused
    claim must not be silently retained. (Caught by direct testing of this
    same file: an earlier version appended first and checked after, so an
    ESCALATE-refused claim was still sitting in the ledger post-refusal.
    Fixed here rather than left in the shipped proof-of-concept.)"""
    projected_n = len(_TACIT_LEDGER.get(verifier_id, [])) + 1
    carry_input = {
        "items": [{
            "id": verifier_id,
            "n": projected_n,
            "description": f"unresolved verified_tacit claims since last retrospective review",
            "subsystem": "TACIT_VERIFICATION",
        }]
    }
    result = carry_tracker.run(carry_input)
    item_status = result["items"][0]["status"]

    if item_status == "ESCALATE":
        raise TacitGateError(
            f"REFUSED: accepting this claim would put verifier '{verifier_id}' at "
            f"{projected_n} unresolved verified_tacit claims (>={carry_tracker.ESCALATE_THRESHOLD}) — "
            f"no new tacit claims accepted until retrospective_review() clears the backlog. "
            f"Claim NOT recorded. This is the exact ESCALATE threshold carry_tracker already "
            f"uses for P28, repointed at this trigger."
        )

    claim = TacitClaim(claim_id=claim_id, verifier_id=verifier_id, context=context)
    _TACIT_LEDGER.setdefault(verifier_id, []).append(claim)

    if item_status == "WARN":
        print(f"  [WARN] verifier '{verifier_id}' at {projected_n} unresolved tacit claims "
              f"(>={carry_tracker.WARN_THRESHOLD}) — retrospective review recommended, not yet blocking.")

    return claim


def retrospective_review(verifier_id: str, reviewer: str, outcomes_held_up: int, outcomes_total: int) -> dict:
    """Track-record validation, per Operator_HIM's shape: not 'explain each
    call,' but 'did this verifier's tacit calls hold up against real
    outcomes.' Clears the ledger regardless of the ratio — a poor ratio is
    itself a real finding (Zone 2 candidate), not a reason to hide the claims."""
    if verifier_id not in _TACIT_LEDGER or not _TACIT_LEDGER[verifier_id]:
        raise TacitGateError(f"No unresolved tacit claims for '{verifier_id}' to review")
    if reviewer == verifier_id:
        raise TacitGateError(
            f"REFUSED: reviewer cannot equal verifier ('{verifier_id}') — "
            f"same self-ratification prevention as P21."
        )

    cleared = len(_TACIT_LEDGER[verifier_id])
    hold_up_rate = round(outcomes_held_up / outcomes_total, 3) if outcomes_total else None
    _TACIT_LEDGER[verifier_id] = []

    return {
        "verifier_id": verifier_id, "reviewer": reviewer,
        "claims_cleared": cleared, "hold_up_rate": hold_up_rate,
        "outcomes_held_up": outcomes_held_up, "outcomes_total": outcomes_total,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    print("── Case 1: tacit claims accumulate, WARN fires at claim #5 ──")
    for i in range(1, 6):
        claim_tacit(f"claim-{i:02}", verifier_id="night", context=f"governance call #{i}")
    print(f"  ledger for 'night': {len(_TACIT_LEDGER['night'])} unresolved claims\n")

    print("── Case 2: claims continue past WARN toward ESCALATE ──")
    for i in range(6, 10):
        claim_tacit(f"claim-{i:02}", verifier_id="night", context=f"governance call #{i}")

    print("\n── Case 3: 10th claim hits ESCALATE — correctly refused ──")
    try:
        claim_tacit("claim-10", verifier_id="night", context="governance call #10")
    except TacitGateError as e:
        print(f"  claim_tacit() correctly refused: {e}")

    print("\n── Case 4: self-review attempt, correctly refused ──")
    try:
        retrospective_review("night", reviewer="night", outcomes_held_up=8, outcomes_total=9)
    except TacitGateError as e:
        print(f"  retrospective_review() correctly refused: {e}")

    print("\n── Case 5: proper retrospective review, clears the ledger, new claims accepted again ──")
    result = retrospective_review("night", reviewer="unit-zero-claude", outcomes_held_up=8, outcomes_total=9)
    print(f"  {result}")
    new_claim = claim_tacit("claim-11", verifier_id="night", context="governance call #11 — post-review")
    print(f"  new claim accepted: {new_claim.claim_id}, routed_to={new_claim.routed_to}")
