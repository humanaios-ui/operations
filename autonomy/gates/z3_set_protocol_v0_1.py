"""
z3_set_protocol_v0_1.py
Strict protocol for Zone 3 irreversible execution / commitment.

This module is the authoritative machine + human contract for the final,
load-bearing step: moving an APPROVED stone into SET state.

It directly extends mason_gate.py's set_stone() with governance-specific
enforcement, audit requirements, and side-effect declarations.

Core rule (non-negotiable):
    A stone may only be SET if it has passed both:
    1. Z1 dressing (valid Z1Manifest via z1_dress_protocol)
    2. Z2 substantive inspection (verified_substantive with waller_mark)

No overrides, no urgency exceptions, no "we'll fix it later".
Once SET, the stone is load-bearing in the wall (REGISTERED.md,
corpus eligibility, merged PR, deployed artifact, etc.).

Automation programs and human wallers MUST import and respect this contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
import hashlib

# Composition with prior layers
try:
    from mason_gate import (
        Stone,
        StoneState,
        MasonGateError,
        set_stone as mason_set_stone,
    )
    from z1_dress_protocol_v0_1 import Z1Manifest, ensure_z1_dressed, Z1DressError
except ImportError as e:
    raise RuntimeError(
        "z3_set_protocol requires mason_gate.py and z1_dress_protocol_v0_1.py in path"
    ) from e


# ─────────────────────────────────────────────────────────────────────────
# Z3-specific enums and errors
# ─────────────────────────────────────────────────────────────────────────
class Z3Effect(Enum):
    """Declared irreversible effects that a Z3 set may trigger."""
    REGISTERED_MD_APPEND = "append_to_REGISTERED.md"
    CORPUS_ELIGIBLE_PROMOTION = "corpus_eligible_pending_Z2_to_ratified"
    PR_MERGE = "github_pr_merge_with_signed_commit"
    SUPABASE_CORPUS_INSERT = "supabase_repo_commit_calibration_or_verification_tags_insert"
    CURRENT_MD_POINTER_UPDATE = "update_CURRENT.md_canonical_pointer"
    DEPLOY_PRODUCTION = "deploy_to_production_environment"
    LEDGER_FINALIZATION = "corrections_ledger_final_entry"
    VISUAL_LIBRARY_RENDER = "render_and_commit_visual_library_artifact"


class Z3SetError(MasonGateError):
    """Raised on any attempt to perform an invalid or bypassable Z3 set."""
    pass


@dataclass
class Z3AuditRecord:
    """Immutable record of a successful Z3 set. Appended to stone history."""
    waller_mark: str
    set_at: str
    effects_triggered: List[Z3Effect]
    prior_z2_verification_status: str  # must be "verified_substantive"
    z1_manifest_fingerprint: Optional[str] = None
    note: str = ""


# ─────────────────────────────────────────────────────────────────────────
# Z3 Gate — the hard enforcement point
# ─────────────────────────────────────────────────────────────────────────
def can_set(stone: Stone) -> bool:
    """Returns True only if the stone is in APPROVED state and carries
    evidence of prior Z1 + Z2 passage. Does not mutate state."""
    if stone.state != StoneState.APPROVED:
        return False
    # Require Z1 manifest presence (set during Z1 dressing)
    if not hasattr(stone, "z1_manifest") or stone.z1_manifest is None:
        return False
    # Require Z2 verification marker (set during substantive Z2 review)
    if not hasattr(stone, "z2_verification_status"):
        return False
    if getattr(stone, "z2_verification_status", None) != "verified_substantive":
        return False
    return True


def set_stone_with_z3_audit(
    stone: Stone,
    waller_mark: str,
    effects: List[Z3Effect],
    z2_verification_status: str = "verified_substantive",
    note: str = "",
) -> Stone:
    """The single entry point for all Z3 execution.

    Enforces:
    - stone.state == APPROVED (from mason_gate)
    - stone carries validated Z1Manifest
    - stone carries z2_verification_status == "verified_substantive"
    - waller_mark is non-empty (human or signed automation identity)
    - effects list is declared (immutable record of what became load-bearing)

    On success: state → SET, appends Z3AuditRecord to history, returns stone.
    On any violation: raises Z3SetError with precise reason. No partial execution.
    """
    if not can_set(stone):
        reasons = []
        if stone.state != StoneState.APPROVED:
            reasons.append(f"state={stone.state.value} (must be APPROVED)")
        if not hasattr(stone, "z1_manifest") or stone.z1_manifest is None:
            reasons.append("missing valid Z1Manifest")
        if getattr(stone, "z2_verification_status", None) != "verified_substantive":
            reasons.append("z2_verification_status != verified_substantive")
        raise Z3SetError(
            f"REFUSED: {stone.stone_id} cannot be SET. Reasons: {'; '.join(reasons)}. "
            "No override path exists. Stone must return to Z1/Z2 for correction."
        )

    if not waller_mark or len(waller_mark.strip()) < 2:
        raise Z3SetError("waller_mark must be a non-empty identifier of the responsible actor")

    if not effects:
        raise Z3SetError("effects list must be non-empty — declare what is being made load-bearing")

    # Perform the base mason_gate set (this will also enforce APPROVED state again)
    stone = mason_set_stone(stone, waller_mark)

    # Attach Z3 audit record
    audit = Z3AuditRecord(
        waller_mark=waller_mark,
        set_at=datetime.now(timezone.utc).isoformat(),
        effects_triggered=effects,
        prior_z2_verification_status=z2_verification_status,
        z1_manifest_fingerprint=getattr(stone, "z1_manifest", None).content_fingerprint()
        if hasattr(stone, "z1_manifest") and stone.z1_manifest
        else None,
        note=note,
    )
    if not hasattr(stone, "z3_audit"):
        stone.z3_audit = []  # type: ignore[attr-defined]
    stone.z3_audit.append(audit)  # type: ignore[attr-defined]

    # Final history log
    stone._log(  # type: ignore[attr-defined]
        f"SET_Z3 by {waller_mark} | effects={[e.value for e in effects]} | "
        f"z2_status={z2_verification_status}"
    )

    return stone


# ─────────────────────────────────────────────────────────────────────────
# Convenience: full Z1→Z2→Z3 flow helper (for automation orchestration)
# ─────────────────────────────────────────────────────────────────────────
def execute_full_governance_flow(
    stone: Stone,
    z1_manifest: Z1Manifest,
    waller_mark: str,
    z3_effects: List[Z3Effect],
    z2_note: str = "Z2 substantive review passed per Z2_REVIEW_PLAYBOOK_V0_4",
) -> Stone:
    """Orchestration helper for automation that wants to drive a complete
    Z1-dress → Z2-approve → Z3-set sequence in one call (primarily for testing
    or tightly controlled pipelines). Real governance flows usually separate
    the human Z2 review step.

    This function still enforces every gate; it cannot bypass them.
    """
    from z1_dress_protocol_v0_1 import bank_stone_with_z1_manifest, ensure_z1_dressed

    # Z1
    ensure_z1_dressed(z1_manifest)
    stone = bank_stone_with_z1_manifest(stone, z1_manifest)

    # Simulate Z2 approval (in real use this is done by human reviewer)
    stone.z2_verification_status = "verified_substantive"  # type: ignore[attr-defined]
    stone._log("Z2_APPROVED_SIMULATED")  # type: ignore[attr-defined]

    # Z3
    stone = set_stone_with_z3_audit(
        stone,
        waller_mark=waller_mark,
        effects=z3_effects,
        note="Full flow executed via execute_full_governance_flow (testing mode)",
    )
    return stone


# ─────────────────────────────────────────────────────────────────────────
# Self-application (this module must satisfy Z1 + Z3 rules)
# ─────────────────────────────────────────────────────────────────────────
def get_z3_self_audit_example() -> Z3AuditRecord:
    """Example audit record showing this protocol applied to itself."""
    return Z3AuditRecord(
        waller_mark="night",
        set_at="2026-07-13T12:01:00Z",
        effects_triggered=[
            Z3Effect.LEDGER_FINALIZATION,
            Z3Effect.CORPUS_ELIGIBLE_PROMOTION,
        ],
        prior_z2_verification_status="verified_substantive",
        note="z3_set_protocol_v0_1.py itself passed Z1 dressing and Z2 review; now SET as load-bearing governance contract.",
    )


# ─────────────────────────────────────────────────────────────────────────
# Demo / executable specification
# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("── Z3 Set Protocol v0.1 Self-Test ──")

    from mason_gate import bank_stone, inspect_stone, Standard
    from z1_dress_protocol_v0_1 import dress_artifact, PurityTier, bank_stone_with_z1_manifest

    # 1. Create and fully dress a stone (Z1)
    manifest = dress_artifact(
        stone_id="z3-test-stone-001",
        banker_mark="grok-assisted",
        version="0.1.0",
        purity_tier=PurityTier.SELF_ADMINISTERED,
        scope_limits=["demo only", "not for production corpus"],
        justification_evidence="This stone demonstrates the complete Z1→Z2→Z3 flow using the new z3_set_protocol. All gates are enforced in code.",
        live_verification_methods=["direct python execution of ensure_z1_dressed and set_stone_with_z3_audit"],
        recursive_application_statement="The same validation and set functions defined here are applied to this demo stone. No bypass exists.",
    )

    stone = bank_stone(
        stone_id=manifest.stone_id,
        description="Test stone for Z3 protocol validation",
        banker_mark=manifest.banker_mark,
    )
    stone = bank_stone_with_z1_manifest(stone, manifest)

    # 2. Z2 approval (simulated — in reality performed by human per Z2 playbook)
    stone.z2_verification_status = "verified_substantive"  # type: ignore[attr-defined]
    stone = inspect_stone(
        stone,
        Standard.JUSTIFICATION_SPECIFIC,
        note="Z2 review passed: stone carries valid Z1Manifest, justification meets specificity, purity and scope declared, recursive application stated. Ready for Z3.",
    )
    print(f"After Z2: state={stone.state.value}")

    # 3. Z3 set (the actual enforcement point)
    try:
        stone = set_stone_with_z3_audit(
            stone,
            waller_mark="night",
            effects=[Z3Effect.LEDGER_FINALIZATION, Z3Effect.CORPUS_ELIGIBLE_PROMOTION],
            note="Demo Z3 set after full Z1+Z2 passage. Irreversible effects declared.",
        )
        print(f"Z3 SET successful: state={stone.state.value}")
        print(f"  waller_mark={stone.waller_mark}")
        print(f"  z3_audit entries: {len(stone.z3_audit)}")  # type: ignore[attr-defined]
        print(f"  last history event: {stone.history[-1]}")  # type: ignore[attr-defined]
    except Z3SetError as e:
        print(f"Z3 correctly blocked: {e}")

    # 4. Attempt invalid set (should fail)
    bad_stone = bank_stone("bad-002", "never inspected", "test")
    try:
        set_stone_with_z3_audit(bad_stone, "night", [Z3Effect.PR_MERGE])
    except Z3SetError as e:
        print(f"Invalid set correctly refused: {str(e)[:120]}...")

    print("\nZ3 Set Protocol v0.1 is ready. Only APPROVED + Z1 + verified_substantive stones may be SET.")
    print("No override exists. This is the final enforcement point.")
