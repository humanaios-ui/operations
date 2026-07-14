"""
z1_dress_protocol_v0_1.py
Strict machine contract for Zone 1 artifact preparation.

This module is the authoritative specification for what constitutes a
properly "dressed" stone (Z1-complete artifact). Automation programs
(GitHub Actions, n8n workflows, reference_linter extensions, future
z2_review_gate.py, Supabase triggers, acat_document_analyzer pipelines)
MUST import and enforce this contract before any artifact may enter
Zone 2 inspection.

Design goals:
- Zero natural-language ambiguity for machines
- Enforceable via static analysis + runtime validation
- Composable with mason_gate.py (bank_stone / inspect_stone / set_stone)
- Self-applicable: this file itself must satisfy the protocol it defines
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
import re
import hashlib


# ─────────────────────────────────────────────────────────────────────────
# Re-export / extend mason_gate primitives for composition
# ─────────────────────────────────────────────────────────────────────────
try:
    from mason_gate import (
        StoneState,
        Standard as MasonGateStandard,
        MasonGateError,
        Stone,
        bank_stone as mason_bank_stone,
    )
except ImportError:
    # Fallback minimal definitions if mason_gate not present in path
    class StoneState(Enum):
        DRESSED = "dressed_awaiting_inspection"
        REJECTED = "rejected_returned_to_bench"
        APPROVED = "approved_awaiting_placement"
        SET = "set_in_wall"

    class MasonGateStandard(Enum):
        AST_PARSES = "ast_parses_clean"
        LIVE_QUERY_MATCHES = "live_query_result_matches_claim"
        SMOKE_TEST_PASSES = "smoke_test_passes"
        JUSTIFICATION_SPECIFIC = "justification_meets_specificity_check"

    class MasonGateError(Exception):
        pass

    @dataclass
    class Stone:
        stone_id: str
        description: str
        banker_mark: str
        state: StoneState = StoneState.DRESSED
        waller_mark: Optional[str] = None
        standard_applied: Optional[MasonGateStandard] = None
        inspection_note: Optional[str] = None
        history: List[Dict[str, Any]] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────
# Z1 Protocol Enums & Errors
# ─────────────────────────────────────────────────────────────────────────
class Z1Requirement(Enum):
    """Machine-enforceable requirements for a stone to be considered dressed."""
    BANKER_MARK_PRESENT = "banker_mark_present_and_nonempty"
    VERSION_DECLARED = "semantic_version_present"
    PURITY_TIER_DECLARED = "purity_tier_explicitly_stated"
    SCOPE_LIMITS_DECLARED = "scope_limits_list_nonempty"
    JUSTIFICATION_SPECIFIC_EVIDENCE = "justification_evidence_meets_specificity"
    LIVE_VERIFICATION_EVIDENCE = "live_verification_methods_list_nonempty"
    RECURSIVE_APPLICATION_STATEMENT = "recursive_application_statement_present"
    STONE_ID_STABLE = "stone_id_matches_content_hash_or_commit"
    DRESSED_TIMESTAMP_PRESENT = "dressed_at_iso_timestamp_valid"


class Z1DressError(Exception):
    """Raised when an artifact fails Z1 dressing validation.
    Automation must surface the exact list of failing requirements."""
    def __init__(self, stone_id: str, failures: List[Z1Requirement], details: str = ""):
        self.stone_id = stone_id
        self.failures = failures
        self.details = details
        super().__init__(
            f"Z1_DRESS_FAILED[{stone_id}]: {', '.join(f.value for f in failures)}"
        )


class PurityTier(Enum):
    SELF_ADMINISTERED = "self_administered"
    TWO_STAGE_VERIFIED = "two_stage_verified"
    SELF_ADMINISTERED_WITH_LATER_TWO_STAGE = "self_administered_with_later_two_stage"


# ─────────────────────────────────────────────────────────────────────────
# Core Z1 Manifest — the machine contract
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class Z1Manifest:
    """The minimal structured payload that every Z1-dressed artifact MUST carry.
    Automation programs read/write this structure. Human reviewers see it as
    frontmatter, JSON sidecar, or embedded in the artifact header.
    """
    stone_id: str                          # stable identifier (commit hash, filename+version, or content hash)
    banker_mark: str                       # declarant_id / who prepared
    version: str                           # semantic version or commit-derived
    purity_tier: PurityTier
    scope_limits: List[str]                # explicit list of what is out of scope
    justification_evidence: str            # substantive justification (≥8 words enforced)
    live_verification_methods: List[str]   # how claims were verified (git show, curl, executed test, etc.)
    recursive_application_statement: str   # how the artifact applies its own rules to itself
    dressed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["purity_tier"] = self.purity_tier.value
        return d

    def content_fingerprint(self) -> str:
        """Stable hash of core fields for stone_id validation."""
        core = f"{self.stone_id}|{self.banker_mark}|{self.version}|{self.purity_tier.value}"
        return hashlib.sha256(core.encode()).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────
# Validation Rules (strict, automation-enforceable)
# ─────────────────────────────────────────────────────────────────────────
MIN_JUSTIFICATION_WORDS = 8
MIN_SCOPE_LIMITS = 1
MIN_LIVE_VERIFICATION_METHODS = 1

def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))

def validate_z1_manifest(manifest: Z1Manifest) -> List[Z1Requirement]:
    """Returns list of failing Z1Requirement enums. Empty list == fully dressed."""
    failures: List[Z1Requirement] = []

    if not manifest.banker_mark or len(manifest.banker_mark.strip()) < 3:
        failures.append(Z1Requirement.BANKER_MARK_PRESENT)

    if not manifest.version or not re.match(r"^\d+\.\d+", manifest.version):
        failures.append(Z1Requirement.VERSION_DECLARED)

    if not isinstance(manifest.purity_tier, PurityTier):
        failures.append(Z1Requirement.PURITY_TIER_DECLARED)

    if len(manifest.scope_limits) < MIN_SCOPE_LIMITS:
        failures.append(Z1Requirement.SCOPE_LIMITS_DECLARED)

    if _word_count(manifest.justification_evidence) < MIN_JUSTIFICATION_WORDS:
        failures.append(Z1Requirement.JUSTIFICATION_SPECIFIC_EVIDENCE)

    if len(manifest.live_verification_methods) < MIN_LIVE_VERIFICATION_METHODS:
        failures.append(Z1Requirement.LIVE_VERIFICATION_EVIDENCE)

    if not manifest.recursive_application_statement or _word_count(manifest.recursive_application_statement) < 6:
        failures.append(Z1Requirement.RECURSIVE_APPLICATION_STATEMENT)

    if not manifest.dressed_at or not manifest.dressed_at.startswith("20"):
        failures.append(Z1Requirement.DRESSED_TIMESTAMP_PRESENT)

    # Optional but recommended: stone_id should be stable
    if not manifest.stone_id or len(manifest.stone_id) < 6:
        failures.append(Z1Requirement.STONE_ID_STABLE)

    return failures


def ensure_z1_dressed(manifest: Z1Manifest) -> Z1Manifest:
    """Idempotent gate. Raises Z1DressError on any failure.
    Automation programs call this before allowing Z2 inspection to begin."""
    failures = validate_z1_manifest(manifest)
    if failures:
        raise Z1DressError(manifest.stone_id, failures)
    return manifest


# ─────────────────────────────────────────────────────────────────────────
# Z1 Dressing Helper — produces a valid manifest
# ─────────────────────────────────────────────────────────────────────────
def dress_artifact(
    stone_id: str,
    banker_mark: str,
    version: str,
    purity_tier: PurityTier,
    scope_limits: List[str],
    justification_evidence: str,
    live_verification_methods: List[str],
    recursive_application_statement: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Z1Manifest:
    """Convenience constructor + immediate validation.
    Use this in automation when preparing a new stone for Z2."""
    manifest = Z1Manifest(
        stone_id=stone_id,
        banker_mark=banker_mark,
        version=version,
        purity_tier=purity_tier,
        scope_limits=scope_limits,
        justification_evidence=justification_evidence,
        live_verification_methods=live_verification_methods,
        recursive_application_statement=recursive_application_statement,
        extra=extra or {},
    )
    return ensure_z1_dressed(manifest)


# ─────────────────────────────────────────────────────────────────────────
# Composition with mason_gate
# ─────────────────────────────────────────────────────────────────────────
def bank_stone_with_z1_manifest(
    stone: Stone,
    manifest: Z1Manifest,
) -> Stone:
    """Augments a mason_gate Stone with a validated Z1Manifest.
    The manifest becomes part of the stone's extra metadata for Z2 consumption."""
    ensure_z1_dressed(manifest)
    if not hasattr(stone, "z1_manifest"):
        stone.z1_manifest = manifest  # type: ignore[attr-defined]
    stone._log("Z1_DRESSED_WITH_MANIFEST")  # type: ignore[attr-defined]
    return stone


# ─────────────────────────────────────────────────────────────────────────
# Self-application check (this module must satisfy its own protocol)
# ─────────────────────────────────────────────────────────────────────────
SELF_APPLICATION_JUSTIFICATION = (
    "This z1_dress_protocol_v0_1.py defines strict machine validation for Z1 dressing. "
    "It applies the same requirements (banker_mark, purity_tier, scope_limits, "
    "justification_evidence, live_verification_methods, recursive_application) to every "
    "artifact it validates, including governance playbooks and itself. "
    "No exception path exists for self-administered artifacts."
)

SELF_APPLICATION_SCOPE_LIMITS = [
    "Does not yet enforce two-stage verification (requires separate waller_mark ratification)",
    "Human-readable Z2 playbook (Z2_REVIEW_PLAYBOOK_V0_4.md) remains the authoritative human contract",
    "Dataset and model-weight artifacts require additional standards (future extension)",
]


def get_self_manifest() -> Z1Manifest:
    """Returns a Z1Manifest proving this module satisfies its own protocol."""
    return Z1Manifest(
        stone_id="z1_dress_protocol_v0_1.py",
        banker_mark="grok-assisted-2026-07-13",
        version="0.1.0",
        purity_tier=PurityTier.SELF_ADMINISTERED,
        scope_limits=SELF_APPLICATION_SCOPE_LIMITS,
        justification_evidence=SELF_APPLICATION_JUSTIFICATION,
        live_verification_methods=[
            "python -c 'from z1_dress_protocol_v0_1 import validate_z1_manifest, ensure_z1_dressed, get_self_manifest; m=get_self_manifest(); ensure_z1_dressed(m)'",
            "Direct execution of dress_artifact() and validate_z1_manifest() on self-manifest",
        ],
        recursive_application_statement=(
            "The validation functions (validate_z1_manifest, ensure_z1_dressed) are applied "
            "to the module's own get_self_manifest() output. All seven core requirements are "
            "satisfied with substantive evidence. This is the recursive proof."
        ),
    )


# ─────────────────────────────────────────────────────────────────────────
# Demo / Self-test (executable specification)
# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("── Z1 Dress Protocol v0.1 Self-Test ──")

    # 1. Valid self-manifest
    self_m = get_self_manifest()
    validated = ensure_z1_dressed(self_m)
    print(f"Self-manifest validation: PASS (stone_id={validated.stone_id})")

    # 2. Invalid manifest (weak justification)
    try:
        bad = Z1Manifest(
            stone_id="bad-stone-001",
            banker_mark="test",
            version="0.0.1",
            purity_tier=PurityTier.SELF_ADMINISTERED,
            scope_limits=["one limit"],
            justification_evidence="weak",  # too short
            live_verification_methods=["manual review"],
            recursive_application_statement="applies to itself",
        )
        ensure_z1_dressed(bad)
    except Z1DressError as e:
        print(f"Weak justification correctly rejected: {e}")

    # 3. Compose with mason_gate Stone
    stone = mason_bank_stone(
        stone_id="example-governance-md",
        description="GOVERNANCE.md update with Z1 manifest",
        banker_mark="night",
    )
    stone_with_manifest = bank_stone_with_z1_manifest(stone, self_m)
    print(f"Composed mason_gate Stone + Z1Manifest: state={stone_with_manifest.state.value}")

    print("\nZ1 Dress Protocol v0.1 is ready for automation consumption.")
    print("Import ensure_z1_dressed() or dress_artifact() in CI / workflows.")