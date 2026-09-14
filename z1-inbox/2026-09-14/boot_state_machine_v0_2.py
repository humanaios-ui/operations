#!/usr/bin/env python3
"""
BOOT STATE MACHINE — v0.3 (second adversarial round)
====================================================
Q-BOOT-STATE-MACHINE-01 companion demonstration.

STATUS: Experimental / ADVISORY ONLY. Not ratified. Not registered.
Does NOT amend SESSION_RITUALS.md, CLAUDE.md, GOVERNANCE.md, CURRENT.md, or
OPERATOR_RUNBOOK.md. Where this model conflicts with those sources, the
sources win — see SOURCE_PRECEDENCE, SOURCE_ANCHORS and DEVIATIONS, which
make that clause machine-readable instead of prose a caller cannot check.

WHAT THIS IS (P29 articulation, part 1)
    A guard-and-transition model of the HumanAIOS session lifecycle. It
    encodes which actions are legal in which phase, and refuses transitions
    whose preconditions are not evidenced.

WHAT EVIDENCE SUPPORTS IT (P29 articulation, part 2)
    `SOURCE_ANCHORS` maps every action to the file and section it restates,
    and `export_journal()` emits it, so a caller can enumerate the anchors
    rather than take a docstring's word for them. Anchors were verified
    against the live repo at the SHA recorded in the companion review.
    Actions absent from SOURCE_ANCHORS are listed in DEVIATIONS.
    Enforced by `_selftest` T10: every action in ALLOWED_ACTIONS has an anchor.

RISK OF BEING WRONG, AND HOW IT WOULD BE DETECTED (P29 articulation, part 3)
    The load-bearing risk is that a reader treats `allowed_actions()` as
    authority and skips a canonical step this model does not encode. Detected
    by: a session that reaches BS_DONE through this machine and still trips a
    Section F halt. That event falsifies the model, not the protocol.

FALSIFIER (required for Z1 candidate blocks per CLAUDE.md / falsifier_lint)
    PREDICTION: across N=10 sessions driven through this machine, zero
    sessions reach BS_DONE while any SESSION_RITUALS Section B step
    (B.0 through B.8) is unexecuted.
    FALSIFIED IF: any such session reaches BS_DONE with an unexecuted
    Section B step, OR any Section F halt condition fires in a session the
    machine reported as clean.
    WINDOW: 10 sessions or 30 days, whichever comes first.
    (v0.2 targeted BS_JOURNAL, which every clean session falsified on entry
    because B.7 and B.8 are executed *from* that state. Corrected to BS_DONE.)

v0.3 CHANGES — second review round, findings raised by Copilot on PR #332.
Nine of them are the same defect classes this artifact's own review charged
against v0.1, reproduced one layer up; they are listed first and not softened.
    R2-01  B.0 accepted any non-empty evidence list — it now requires an entry
           per applicable §B.0 check family (assertion-as-verification, the
           F-BSM-03 charge, surviving inside the fix for it)
    R2-02  `run_close_sequence` took a caller-supplied list of step *strings*
           — now requires an Evidence object per step (same class as R2-01)
    R2-03  `may_propose_fich` was exposed but no transition consulted it —
           this is F-BSM-09 verbatim, reproduced in its own remedy
    R2-04  B.6 passed on any non-empty paragraph — now must quote a recorded
           B.0 check and carry the canonical heading
    R2-05  `bind_session_id` appended B.8 to the journal *before* testing
           prerequisites, so a refused call still recorded the step as done
    R2-06  `emit_p1_declaration` never checked that the drift catalog ran
           (§A.5), and omitted `pinned_sha` from its required fields
    R2-07  `RitualSurface` defaulted rather than forcing a choice, and
           CLAUDE_MD selected one extra state rather than that surface's
           sequence — P22.1 blending survived the fix for P22.1 blending
    R2-08  `TransitionResult.success` was True for guard failures that
           diverted to HALTED/DEGRADED; `details` stayed unpopulated despite
           F-BSM-17 naming it
    R2-09  `export_journal` truncated evidence to 200 chars and reduced
           DEVIATIONS to bare IDs, discarding the direction field that is the
           safety signal
    R2-10  live-state guard returned "Live state OK" when haioscc was
           unreachable, and skipped the evidence check on the PATH C branch
    R2-11  `operator_resume` funnelled every halt cause into DEGRADED without
           re-running the failed guard; `request_recovery` cleared degradation
           regardless of which cause raised it
    R2-12  `classify_session` accepted the caller's prompt_env even when
           `operator_supplied=False`, recording substrate inference as a
           protocol default
    R2-13  `bind_session_id` accepted any "S-" prefix — now uses the pattern
           `tools/acat_session_validator.py` already enforces

v0.2 CHANGES (first round — see the companion review)
    F-BSM-01 parses and runs · F-BSM-02 B.0 as a state boundary ·
    F-BSM-03 Evidence-bearing guards · F-BSM-04 live-state halt ·
    F-BSM-05 mid-session IC-030 re-entry · F-BSM-06 B.0-B.8 enumerated ·
    F-BSM-07 P22 time anchor · F-BSM-08 AFA-1 · F-BSM-09 class_state gates ·
    F-BSM-10 reachable DEGRADED, resumable HALTED · F-BSM-11 source anchors ·
    F-BSM-13 falsifier + P29 · F-BSM-14 exportable journal ·
    F-BSM-15 ADVISORY_ONLY + DEVIATIONS · F-BSM-16 RitualSurface ·
    F-BSM-17 unused imports removed
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set

ADVISORY_ONLY = True

SOURCE_PRECEDENCE = (
    "SESSION_RITUALS.md",      # parser-tag + protocol authority (its own §, line 8)
    "GOVERNANCE.md",           # principle authority
    "OPERATOR_RUNBOOK.md",     # operator-side recipes
    "CLAUDE.md",               # authority map / zone routing
    "CURRENT.md",              # operating-process snapshot
    "boot_state_machine_v0_2.py",  # this file — last, always
)

# R2-13: the pattern tools/acat_session_validator.py:33 already enforces.
# Restated rather than imported to keep this advisory file free of a runtime
# dependency on the validator; DEV-08 records that restatement as a drift risk.
SESSION_ID_PATTERN = re.compile(r"^S-\d{6}-\d{2,3}-[a-z0-9\-]+$")

RECONCILIATION_HEADING = "RECEIPT RECONCILIATION"


class RitualSurface(Enum):
    """
    F-BSM-16 / P22.1 (Cascade Discipline: first-match wins, do not blend).

    Two documents specify a "Section A — Session open" and they do not agree:
    SESSION_RITUALS.md §A (live-state fetch, AFA-1, drift catalog, P1 block)
    and CLAUDE.md §A (git pin, PRIORITY_QUEUE, ZONE_REGISTRY, sha256 manifest).

    v0.1 blended both silently. v0.2 added this enum but still defaulted to
    SESSION_RITUALS and modelled CLAUDE_MD as "the same sequence plus one zone
    read" — which is blending with a label on it (R2-07). v0.3 makes the choice
    mandatory and implements exactly one surface; the others are refused rather
    than approximated, because a partial implementation of a ritual is the
    failure this whole artifact is about.
    """
    SESSION_RITUALS = "SESSION_RITUALS.md Section A"
    CLAUDE_MD = "CLAUDE.md Session Rituals Section A"
    BOTH_DECLARED = "both, with divergence declared to Z2 as an AMBIGUITY callout"


SUPPORTED_SURFACES = frozenset({RitualSurface.SESSION_RITUALS})


@dataclass(frozen=True)
class Deviation:
    """A place this model knowingly differs from its sources."""
    id: str
    source_anchor: str
    direction: str   # NARROWER | WIDER | UNMODELED | INVENTED
    note: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "source_anchor": self.source_anchor,
            "direction": self.direction,
            "note": self.note,
        }


# Enumerable, not prose. NARROWER/INVENTED entries are the dangerous class:
# they let a session pass this machine that a canonical source would stop.
DEVIATIONS: List[Deviation] = [
    Deviation(
        id="DEV-01",
        source_anchor="SESSION_RITUALS.md §A.4 / OPERATOR_RUNBOOK.md §3a note 3",
        direction="NARROWER",
        note=("BS_KERNEL is conditional on registry_touching. SESSION_RITUALS §A.4 "
              "phrases the REGISTERED.md fetch as required for registry-touching "
              "sessions; OPERATOR_RUNBOOK §3a requires an explicit skip declaration "
              "otherwise. Modeled as: skip must be declared, not implied."),
    ),
    Deviation(
        id="DEV-02",
        source_anchor="SESSION_RITUALS.md §F (halts 1-9)",
        direction="NARROWER",
        note=("Section F says 'stop and ask the user before proceeding' — resumable "
              "on operator input, not terminal. BS_HALTED models that and returns to "
              "the interrupted state so the failed guard re-runs. Halt #9 is the one "
              "case routed to BS_DEGRADED, because §F.9 prescribes a declared "
              "DEGRADED mode rather than a stop."),
    ),
    Deviation(
        id="DEV-03",
        source_anchor="CLAUDE.md Session Rituals §A",
        direction="UNMODELED",
        note=("The CLAUDE.md §A surface (git pin, PRIORITY_QUEUE, ZONE_REGISTRY, "
              "PLANNED_REPOS context, sha256-vs-manifest, position/destination/"
              "probability) is NOT implemented. RitualSurface.CLAUDE_MD and "
              "BOTH_DECLARED are refused at construction rather than approximated. "
              "See R2-07."),
    ),
    Deviation(
        id="DEV-04",
        source_anchor="SESSION_RITUALS.md §F.9 / changelog 2026-05-08 (S-050726-04)",
        direction="UNMODELED",
        note=("class_state vocabulary (OK/UNAVAILABLE/UNKNOWN/STALE) is taken from "
              "halt #9's wording. The 'Section F Degraded-Mode Specification' with a "
              "CLASS_STATE block and prohibited-actions table that the changelog "
              "claims was added S-050726-04 is NOT PRESENT in the live file. This "
              "model implements the halt-#9 behaviour only. Upstream IC candidate "
              "filed — see companion review, IC-CAND-BSM-A."),
    ),
    Deviation(
        id="DEV-05",
        source_anchor="SESSION_RITUALS.md §B.5 / §D",
        direction="UNMODELED",
        note=("Submission-URL construction (§D) is one close step carrying one "
              "Evidence object, not modeled field-by-field. The 'do not reconstruct "
              "P1 from P3' rule is asserted in the step label, not mechanically "
              "enforced."),
    ),
    Deviation(
        id="DEV-06",
        source_anchor="SESSION_RITUALS.md §B.7 / OPERATOR_RUNBOOK.md §4a step 8",
        direction="NARROWER",
        note=("post_wgs records a draft identifier; it does not call "
              "slack_send_message_draft and cannot confirm a draft exists. This is "
              "asserted-pass, declared rather than disguised: a caller can satisfy "
              "B.7 with a fabricated id. Closing it requires the machine to hold "
              "Slack credentials, which turns an advisory model into an executor — "
              "a scope change that is Z2's call."),
    ),
    Deviation(
        id="DEV-07",
        source_anchor="SESSION_RITUALS.md §A.1 vs CURRENT.md §7 (Z2-GOVARCH-02)",
        direction="NARROWER",
        note=("§A.1 says fetch the two haioscc endpoints and 'if either fails, halt'. "
              "Z2-GOVARCH-02 (ratified S-060826-04) later made WGS the Class 1 "
              "primary and demoted haioscc to secondary cross-check, 'unreachable "
              "from Claude's bash environment'. Under §A.1 read literally every "
              "Claude session halts at open. Modeled as: both channels down halts, "
              "one down degrades. The conflict is real and is a second AMBIGUITY "
              "candidate — see companion review."),
    ),
    Deviation(
        id="DEV-08",
        source_anchor="tools/acat_session_validator.py:33",
        direction="NARROWER",
        note=("SESSION_ID_PATTERN is restated here rather than imported, so the two "
              "can drift. Restated to keep this advisory file dependency-free; if "
              "the validator's pattern changes, this copy is stale until updated."),
    ),
]


# R2-03 / P29 part 2: machine-readable anchors, one per action, enforced by T10.
SOURCE_ANCHORS: Dict[str, str] = {
    "start": "SESSION_RITUALS.md §A (session open)",
    "anchor_time": "GOVERNANCE.md P22 · OPERATOR_RUNBOOK.md §3a note 1",
    "fetch_live_state": "SESSION_RITUALS.md §A.1 · OPERATOR_RUNBOOK.md §3a note 3 · CURRENT.md §7",
    "pin_commit": "CLAUDE.md §A.1 · SESSION_RITUALS.md §F halt 1",
    "load_rituals": "SESSION_RITUALS.md §A.2, §A.3",
    "load_governance_version": "SESSION_RITUALS.md §A.2.6",
    "classify_session": "SESSION_RITUALS.md §A.2.5 (AFA-1) · §C SESSION_TYPE",
    "fetch_registered": "SESSION_RITUALS.md §A.4 · §F halt 9 (IC-029, IC-030)",
    "declare_registry_skip": "OPERATOR_RUNBOOK.md §3a note 3",
    "build_drift_catalog": "SESSION_RITUALS.md §A.5",
    "emit_p1_declaration": "SESSION_RITUALS.md §A.6 · §C · GOVERNANCE.md P27",
    "await_confirmation": "SESSION_RITUALS.md §A.7",
    "do_work": "SESSION_RITUALS.md §A.7 (post-acknowledgment work)",
    "propose_fich": "SESSION_RITUALS.md §F halt 9 · GOVERNANCE.md P21",
    "enter_registry_touching": "OPERATOR_RUNBOOK.md §3a note 3 (IC-030 mid-session)",
    "request_close": "SESSION_RITUALS.md §B · GOVERNANCE.md P27",
    "run_b0_verification": "SESSION_RITUALS.md §B.0 · §F halts 7, 8 · §G",
    "run_close_sequence": "SESSION_RITUALS.md §B.1-B.5 · §D",
    "emit_receipt_reconciliation": "SESSION_RITUALS.md §B.6",
    "post_wgs": "SESSION_RITUALS.md §B.7 · GOVERNANCE.md P30/P31",
    "bind_session_id": "SESSION_RITUALS.md §B.8 (IC-027) · tools/acat_session_validator.py:33",
    "report_status": "SESSION_RITUALS.md §F.9 (DEGRADED declaration)",
    "request_recovery": "SESSION_RITUALS.md §F.9 · §G",
    "operator_resume": "SESSION_RITUALS.md §F ('stop and ask ... before proceeding')",
}


# --------------------------------------------------------------------------
# Evidence — the fix for F-BSM-03
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Evidence:
    """
    SESSION_RITUALS §B.0: record literal outputs, not paraphrases; if a check
    cannot be run, declare CHECK_UNAVAILABLE with a reason.
    §G: 'Claims of completion require evidence ... not assertion.'

    v0.1 took `pin_ok: bool = True`. Every gate defaulted to pass, on the
    caller's own say-so — the IC-031 shape. Evidence removes the default, not
    the trust: a caller can still supply a fabricated `output`. That residual
    is stated in the companion review rather than papered over.
    """
    check: str                              # the probe actually run
    output: str                             # its literal output
    unavailable_reason: Optional[str] = None
    family: Optional[str] = None            # which §B.0 check family this satisfies

    @property
    def confirms(self) -> bool:
        return self.unavailable_reason is None and bool(self.output.strip())

    @classmethod
    def unavailable(cls, check: str, reason: str, family: Optional[str] = None) -> "Evidence":
        return cls(check=check, output="", unavailable_reason=reason, family=family)

    def render(self, limit: Optional[int] = None) -> str:
        """Display helper. Truncating is opt-in — the journal never truncates (R2-09)."""
        if self.unavailable_reason is not None:
            return f"CHECK_UNAVAILABLE: {self.check} — {self.unavailable_reason}"
        body = self.output.strip()
        if limit is not None and len(body) > limit:
            body = body[:limit] + f"... [+{len(self.output.strip()) - limit} chars]"
        return f"{self.check} => {body}"

    def to_dict(self) -> Dict[str, Any]:
        """Full literal record — no truncation. §B.0 requires literal outputs."""
        return {
            "check": self.check,
            "output": self.output,
            "unavailable_reason": self.unavailable_reason,
            "family": self.family,
            "confirms": self.confirms,
        }


class BootState(Enum):
    BS_POWER_ON = auto()
    BS_TIME_ANCHOR = auto()     # P22 — substrate has no clock; D-07 on violation
    BS_POST = auto()            # §A.1 live state
    BS_SECURE_BOOT = auto()     # CLAUDE.md §A.1 pin SHA
    BS_BOOTLOADER = auto()      # §A.2 CURRENT.md + §A.3 SESSION_RITUALS.md
    BS_BOOT_PARAMS = auto()     # §A.2.6 GOVERNANCE.md version → PROTOCOL_VERSION
    BS_CLASSIFY = auto()        # §A.2.5 AFA-1 prompt_env + SESSION_TYPE (operator)
    BS_KERNEL = auto()          # §A.4 REGISTERED.md — conditional, re-enterable
    BS_INIT = auto()            # §A.5 drift catalog + §A.6 P1 declaration
    BS_LOGIN = auto()           # §A.7 wait for operator confirmation
    BS_RUNTIME = auto()
    BS_SHUTDOWN = auto()        # §B.0 ONLY — no close artifacts emitted here
    BS_CLOSE_GATE = auto()      # §B.1-B.5
    BS_RECONCILE = auto()       # §B.6 — its own gate; "do not omit the paragraph"
    BS_JOURNAL = auto()         # §B.7 WGS + §B.8 session-ID binding
    BS_DEGRADED = auto()        # §F.9 declared DEGRADED mode
    BS_HALTED = auto()          # §F — stop and ask; resumable by operator
    BS_DONE = auto()


# The agent may only propose these. F-BSM-02: `emit_close_artifact` is NOT in
# BS_SHUTDOWN. In v0.1 both it and `run_b0_verification` were legal in the same
# state, so the "hard gate" the docstring advertised did not exist. The gate is
# the state boundary.
ALLOWED_ACTIONS: Dict[BootState, List[str]] = {
    BootState.BS_POWER_ON:    ["start"],
    BootState.BS_TIME_ANCHOR: ["anchor_time"],
    BootState.BS_POST:        ["fetch_live_state"],
    BootState.BS_SECURE_BOOT: ["pin_commit"],
    BootState.BS_BOOTLOADER:  ["load_rituals"],
    BootState.BS_BOOT_PARAMS: ["load_governance_version"],
    BootState.BS_CLASSIFY:    ["classify_session"],
    BootState.BS_KERNEL:      ["fetch_registered", "declare_registry_skip"],
    BootState.BS_INIT:        ["build_drift_catalog", "emit_p1_declaration"],
    BootState.BS_LOGIN:       ["await_confirmation"],
    BootState.BS_RUNTIME:     ["do_work", "propose_fich", "enter_registry_touching",
                               "request_close"],
    BootState.BS_SHUTDOWN:    ["run_b0_verification"],
    BootState.BS_CLOSE_GATE:  ["run_close_sequence"],
    BootState.BS_RECONCILE:   ["emit_receipt_reconciliation"],
    BootState.BS_JOURNAL:     ["post_wgs", "bind_session_id"],
    BootState.BS_DEGRADED:    ["report_status", "request_recovery", "request_close"],
    BootState.BS_HALTED:      ["report_status", "operator_resume"],
    BootState.BS_DONE:        [],
}

# SESSION_RITUALS §B: "Steps cannot be skipped."
CLOSE_STEPS = (
    "B.0 empirical verification block",
    "B.1 refetch canonical sources and compare to P1",
    "B.2 phase 3 declaration block",
    "B.3 drift check",
    "B.4 surface uncompleted Zone 3 items",
    "B.5 submit scores per Section D",
    "B.6 receipt reconciliation paragraph",
    "B.7 log to #wgs-sync via slack_send_message_draft",
    "B.8 session ID binding",
)

# R2-01. §B.0 names its required checks by what the session touched. A check
# family is satisfied by an Evidence entry tagged with it — CHECK_UNAVAILABLE
# counts as *declared*, per §B.0's explicit allowance, but is counted separately
# so B.6 can be made to say so.
B0_CHECK_FAMILIES: Dict[str, List[str]] = {
    "git": ["git status --short", "git log -1 --oneline", "git diff --cached --name-only"],
    "files": ["ls -la <outputs dir>", "wc -l <each file claimed produced>"],
    "slack": ["slack_search_public query=<draft_id or message_ts> in:wgs-sync"],
    "supabase": ["SELECT COUNT(*), MAX(updated_at) FROM <table_claimed_modified>"],
}


class Outcome(Enum):
    """
    R2-08. v0.2 returned success=True for guard failures that diverted to
    HALTED/DEGRADED, so a caller reading `success` saw failed verification as
    success. `success` now means only "the machine moved"; `outcome` says what
    actually happened.
    """
    ADVANCED = "advanced"    # guard passed, moved forward
    DIVERTED = "diverted"    # guard FAILED, moved to a halt/degraded state
    HELD = "held"            # guard passed, stayed in state (intra-state work)
    REFUSED = "refused"      # action rejected, no movement


@dataclass
class TransitionResult:
    success: bool                 # the machine moved or the action was accepted
    new_state: BootState
    reason: str
    outcome: Outcome = Outcome.ADVANCED
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def guard_passed(self) -> bool:
        return self.outcome in (Outcome.ADVANCED, Outcome.HELD)


def _advanced(state: BootState, reason: str, **details: Any) -> TransitionResult:
    return TransitionResult(True, state, reason, Outcome.ADVANCED, details)


def _diverted(state: BootState, reason: str, **details: Any) -> TransitionResult:
    return TransitionResult(True, state, reason, Outcome.DIVERTED, details)


def _held(state: BootState, reason: str, **details: Any) -> TransitionResult:
    return TransitionResult(True, state, reason, Outcome.HELD, details)


def _refused(state: BootState, reason: str, **details: Any) -> TransitionResult:
    return TransitionResult(False, state, reason, Outcome.REFUSED, details)


@dataclass
class MachineContext:
    """Mutable session context the machine and agent share."""
    registry_touching: bool
    ritual_surface: RitualSurface

    time_anchor: Optional[str] = None          # P22
    prompt_env: Optional[str] = None           # AFA-1 — operator-supplied only
    prompt_env_operator_supplied: bool = False
    session_type: Optional[str] = None
    protocol_version: Optional[str] = None
    pinned_sha: Optional[str] = None

    live_state_ok: bool = False
    path_c: bool = False                       # Slack MCP unavailable, per §3a
    degradation_causes: Set[str] = field(default_factory=set)

    registered_fetch_ok: bool = False
    registry_skip_declared: bool = False
    class_state: str = "UNKNOWN"               # OK | UNAVAILABLE | UNKNOWN | STALE

    drift_catalog: List[str] = field(default_factory=list)
    p1_declared: bool = False                  # P27 prerequisite for any P3
    confirmation_received: bool = False
    work_done: bool = False

    session_touched: Set[str] = field(default_factory=set)   # B.0 check families
    close_steps_done: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def degraded(self) -> bool:
        return bool(self.degradation_causes)

    @property
    def may_propose_fich(self) -> bool:
        """
        §F.9 (IC-029/IC-030): do not produce F-class, IC-class, or H-class
        proposals against unverified state. In v0.1 `registered_class_state`
        existed but no guard read it (F-BSM-09). In v0.2 this property existed
        but no transition read it either (R2-03) — the same finding, reproduced
        inside its own remedy. `propose_fich` now consults it.
        """
        return self.registered_fetch_ok and self.class_state == "OK"

    def outstanding_close_steps(self) -> List[str]:
        return [s for s in CLOSE_STEPS if s not in self.close_steps_done]

    def b0_families_missing(self) -> List[str]:
        recorded = {e.family for e in self.evidence if e.family}
        return sorted(f for f in self.session_touched if f not in recorded)


class BootStateMachine:
    """
    Minimal advisory state machine. Actions are validated against the current
    state; transitions are driven by guards that restate existing protocol
    language and require evidence rather than assertion.
    """

    def __init__(
        self,
        ritual_surface: RitualSurface,
        registry_touching: bool = False,
        session_touched: Optional[Set[str]] = None,
        verbose: bool = True,
    ):
        # R2-07: no default. P22.1 is first-match-wins; a machine that picks the
        # surface for you has made the blend it was written to prevent.
        if not isinstance(ritual_surface, RitualSurface):
            raise TypeError("ritual_surface must be a RitualSurface (P22.1 requires an explicit choice)")
        if ritual_surface not in SUPPORTED_SURFACES:
            raise NotImplementedError(
                f"RitualSurface.{ritual_surface.name} is declared UNSUPPORTED (DEV-03). "
                f"Only {sorted(s.name for s in SUPPORTED_SURFACES)} is implemented. "
                "A partial implementation of a ritual is the defect this model exists "
                "to surface; it is refused rather than approximated."
            )
        unknown = (session_touched or set()) - set(B0_CHECK_FAMILIES)
        if unknown:
            raise ValueError(f"unknown B.0 check families: {sorted(unknown)}")

        self.state = BootState.BS_POWER_ON
        self.ctx = MachineContext(
            registry_touching=registry_touching,
            ritual_surface=ritual_surface,
            session_touched=set(session_touched or set()),
        )
        self.history: List[str] = []
        self.verbose = verbose
        self._halt_return: Optional[BootState] = None
        self._halt_cause: Optional[str] = None
        self._log(
            f"INIT registry_touching={registry_touching} "
            f"ritual_surface={ritual_surface.value} "
            f"session_touched={sorted(self.ctx.session_touched)} "
            f"advisory_only={ADVISORY_ONLY}"
        )

    # -- journal ---------------------------------------------------------

    def _log(self, msg: str) -> None:
        entry = f"[{self.state.name}] {msg}"
        self.history.append(entry)
        if self.verbose:
            print(entry)

    def export_journal(self) -> Dict[str, Any]:
        """
        P20: substrate context is volatile working memory, never persistent
        state. Export it, or it did not happen. R2-09: evidence is emitted in
        full (§B.0 requires literal outputs) and deviations keep their
        direction field, which is the whole safety signal.
        """
        return {
            "advisory_only": ADVISORY_ONLY,
            "source_precedence": list(SOURCE_PRECEDENCE),
            "source_anchors": dict(SOURCE_ANCHORS),
            "final_state": self.state.name,
            "ritual_surface": self.ctx.ritual_surface.value,
            "time_anchor": self.ctx.time_anchor,
            "prompt_env": self.ctx.prompt_env,
            "prompt_env_operator_supplied": self.ctx.prompt_env_operator_supplied,
            "session_type": self.ctx.session_type,
            "protocol_version": self.ctx.protocol_version,
            "pinned_sha": self.ctx.pinned_sha,
            "degraded": self.ctx.degraded,
            "degradation_causes": sorted(self.ctx.degradation_causes),
            "path_c": self.ctx.path_c,
            "class_state": self.ctx.class_state,
            "may_propose_fich": self.ctx.may_propose_fich,
            "drift_catalog": list(self.ctx.drift_catalog),
            "session_touched": sorted(self.ctx.session_touched),
            "close_steps_done": list(self.ctx.close_steps_done),
            "close_steps_outstanding": self.ctx.outstanding_close_steps(),
            "evidence": [e.to_dict() for e in self.ctx.evidence],
            "deviations": [d.to_dict() for d in DEVIATIONS],
            "notes": list(self.ctx.notes),
            "history": list(self.history),
        }

    # -- introspection ---------------------------------------------------

    def current_state(self) -> BootState:
        return self.state

    def allowed_actions(self) -> List[str]:
        return ALLOWED_ACTIONS.get(self.state, [])

    def can_act(self, action: str) -> bool:
        return action in self.allowed_actions()

    # -- dispatch --------------------------------------------------------

    def transition(self, action: str, **kwargs) -> TransitionResult:
        if not self.can_act(action):
            return _refused(
                self.state,
                f"Action '{action}' not allowed in state {self.state.name}; "
                f"allowed: {self.allowed_actions()}",
                allowed=self.allowed_actions(),
            )

        handler = getattr(self, f"_do_{action}", None)
        if handler is None:
            return _refused(self.state, f"No handler for '{action}'")

        try:
            result = handler(**kwargs)
        except TypeError as exc:
            # Missing Evidence is a refusal, not a crash (F-BSM-03: no
            # default-pass path, so absent evidence must be legible).
            return _refused(
                self.state,
                f"Action '{action}' refused — required evidence not supplied ({exc})",
                anchor=SOURCE_ANCHORS.get(action),
            )

        result.details.setdefault("action", action)
        result.details.setdefault("anchor", SOURCE_ANCHORS.get(action))

        if result.outcome is Outcome.DIVERTED:
            self._halt_return = self.state
            self._halt_cause = result.reason

        if result.success and result.new_state != self.state:
            old = self.state
            self.state = result.new_state
            self._log(
                f"{result.outcome.name} {old.name} → {self.state.name} | {result.reason}"
            )
        else:
            self._log(f"{result.outcome.name} {action} | {result.reason}")
        return result

    def _record(self, evidence: Evidence) -> None:
        self.ctx.evidence.append(evidence)

    # -- boot ------------------------------------------------------------

    def _do_start(self) -> TransitionResult:
        return _advanced(BootState.BS_TIME_ANCHOR, "Power-on → time anchor")

    def _do_anchor_time(self, evidence: Evidence) -> TransitionResult:
        """P22 — bash_tool primary, operator anchor fallback. Violation = D-07."""
        self._record(evidence)
        if not evidence.confirms:
            return _diverted(
                BootState.BS_HALTED,
                "No verified time source (P22) — stop and ask operator for anchor; "
                "inference is not synchronization (D-07)",
            )
        self.ctx.time_anchor = evidence.output.strip()
        return _advanced(BootState.BS_POST, f"Time anchored: {self.ctx.time_anchor}")

    def _do_fetch_live_state(
        self,
        evidence: Evidence,
        slack_mcp_available: bool,
        haioscc_reachable: bool,
    ) -> TransitionResult:
        """
        SESSION_RITUALS §A.1 ('if either fails, halt') read against Z2-GOVARCH-02,
        which made WGS primary and demoted haioscc to secondary — see DEV-07.

        F-BSM-04: v0.1 applied the runbook's narrow PATH C allowance to the
        rituals' broad halt, so total live-state failure walked on silently.
        R2-10: v0.2 then returned "Live state OK" when haioscc alone was down,
        and skipped the evidence check entirely on the PATH C branch.
        """
        self._record(evidence)
        if not slack_mcp_available and not haioscc_reachable:
            return _diverted(
                BootState.BS_HALTED,
                "Both live-state channels failed — SESSION_RITUALS §A.1 halt "
                "(PATH C does not cover total live-state loss)",
            )
        if not evidence.confirms:
            return _diverted(
                BootState.BS_HALTED,
                "Live-state fetch returned no confirmable content — §A.1 halt",
            )
        if not slack_mcp_available:
            self.ctx.path_c = True
            self.ctx.degradation_causes.add("live_state_wgs")
            self.ctx.notes.append(
                "PATH C declared (Slack MCP unavailable) per OPERATOR_RUNBOOK §3a note 3"
            )
            return _advanced(
                BootState.BS_SECURE_BOOT,
                "PATH C (degraded) — haioscc secondary + CURRENT.md; DEGRADED must "
                "appear in the Phase 1 header",
            )
        if not haioscc_reachable:
            self.ctx.live_state_ok = True
            self.ctx.degradation_causes.add("live_state_haioscc")
            self.ctx.notes.append(
                "haioscc secondary cross-check unavailable — §A.1 names it a halt, "
                "Z2-GOVARCH-02 demotes it to secondary; degraded, not halted (DEV-07)"
            )
            return _advanced(
                BootState.BS_SECURE_BOOT,
                "WGS primary OK, haioscc cross-check unavailable — degraded",
            )
        self.ctx.live_state_ok = True
        return _advanced(BootState.BS_SECURE_BOOT, "Live state OK (WGS primary + haioscc)")

    def _do_pin_commit(self, evidence: Evidence) -> TransitionResult:
        """CLAUDE.md §A.1 — git fetch && git rev-parse HEAD, pin the SHA."""
        self._record(evidence)
        if not evidence.confirms:
            return _diverted(
                BootState.BS_HALTED,
                "Commit pin failed — stop and ask operator (§F halt 1: canonical-source "
                "fetch failed or returned unexpected data)",
            )
        self.ctx.pinned_sha = evidence.output.strip()
        return _advanced(BootState.BS_BOOTLOADER, f"Pinned at {self.ctx.pinned_sha[:12]}")

    def _do_load_rituals(self, evidence: Evidence) -> TransitionResult:
        """§A.2 CURRENT.md, §A.3 SESSION_RITUALS.md."""
        self._record(evidence)
        if not evidence.confirms:
            return _diverted(
                BootState.BS_HALTED,
                "CURRENT.md / SESSION_RITUALS.md fetch failed — §F halt 1",
            )
        return _advanced(BootState.BS_BOOT_PARAMS, "CURRENT.md + SESSION_RITUALS.md loaded")

    def _do_load_governance_version(self, evidence: Evidence) -> TransitionResult:
        """§A.2.6 — record the canonical version for PROTOCOL_VERSION and P3."""
        self._record(evidence)
        if not evidence.confirms:
            return _diverted(BootState.BS_HALTED, "GOVERNANCE.md version fetch failed — §F halt 1")
        self.ctx.protocol_version = evidence.output.strip()
        return _advanced(
            BootState.BS_CLASSIFY, f"PROTOCOL_VERSION recorded: {self.ctx.protocol_version}"
        )

    def _do_classify_session(
        self,
        session_type: str,
        operator_supplied: bool,
        prompt_env: Optional[str] = None,
    ) -> TransitionResult:
        """
        §A.2.5 (AFA-1): "Default if not declared: NEUTRAL ... The classification
        is the operator's call, not Claude's inference."

        F-BSM-08: v0.1 had no state for this, so the default was applied silently.
        R2-12: v0.2 added the state but still *accepted the caller's prompt_env*
        when operator_supplied was False — recording substrate inference as if it
        were the protocol default. A non-operator classification is now discarded
        and NEUTRAL applied, which is what §A.2.5 actually says happens.
        """
        valid_env = {"NEUTRAL", "APPROVAL_WEIGHTED", "ADVERSARIAL"}
        valid_type = {"ANALYSIS", "BUILD", "ADVERSARIAL", "INTEGRATION"}
        if session_type not in valid_type:
            return _refused(self.state, f"session_type must be one of {sorted(valid_type)}")

        if operator_supplied:
            if prompt_env not in valid_env:
                return _refused(
                    self.state,
                    f"operator-supplied prompt_env must be one of {sorted(valid_env)}",
                )
            self.ctx.prompt_env = prompt_env
            self.ctx.prompt_env_operator_supplied = True
        else:
            if prompt_env is not None and prompt_env != "NEUTRAL":
                self.ctx.notes.append(
                    f"prompt_env='{prompt_env}' supplied without operator declaration — "
                    "DISCARDED. §A.2.5 makes the classification the operator's call; "
                    "substrate inference is out of scope. Protocol default NEUTRAL applied."
                )
            else:
                self.ctx.notes.append(
                    "prompt_env not operator-declared — protocol default NEUTRAL applied (§A.2.5)"
                )
            self.ctx.prompt_env = "NEUTRAL"
            self.ctx.prompt_env_operator_supplied = False

        self.ctx.session_type = session_type
        return _advanced(
            BootState.BS_KERNEL,
            f"AFA-1 prompt_env={self.ctx.prompt_env} session_type={session_type} "
            f"operator_supplied={operator_supplied}",
        )

    def _do_fetch_registered(self, evidence: Evidence, class_state: str) -> TransitionResult:
        """§A.4 + §F.9 (IC-029/IC-030)."""
        self._record(evidence)
        self.ctx.class_state = class_state
        if not evidence.confirms or class_state != "OK":
            self.ctx.registered_fetch_ok = False
            if self.ctx.registry_touching:
                self.ctx.degradation_causes.add("registered")
                return _diverted(
                    BootState.BS_DEGRADED,
                    f"REGISTERED.md class_state={class_state} during registry-touching "
                    "session — §F halt 9: declare DEGRADED in Phase 1 header, no F/IC/H "
                    "proposals against unverified state",
                )
            return _advanced(
                BootState.BS_INIT,
                f"REGISTERED.md class_state={class_state}; session is not "
                "registry-touching, so F/IC/H proposals are barred but boot continues",
            )
        self.ctx.registered_fetch_ok = True
        return _advanced(BootState.BS_INIT, "REGISTERED.md OK")

    def _do_declare_registry_skip(self, rationale: str) -> TransitionResult:
        """OPERATOR_RUNBOOK §3a note 3: "If no, declare skip explicitly." """
        if self.ctx.registry_touching:
            return _refused(
                self.state,
                "Cannot skip REGISTERED.md fetch — session is registry-touching (IC-030)",
            )
        if not rationale.strip():
            return _refused(self.state, "Skip requires an explicit rationale")
        self.ctx.registry_skip_declared = True
        self.ctx.notes.append(f"REGISTERED.md fetch skipped: {rationale}")
        return _advanced(BootState.BS_INIT, f"Registry skip declared: {rationale}")

    def _do_build_drift_catalog(self, items: List[str]) -> TransitionResult:
        """§A.5 — 3-8 predicted failure modes, substrate-tagged."""
        if not 3 <= len(items) <= 8:
            return _refused(self.state, f"Drift catalog must hold 3-8 items, got {len(items)}")
        self.ctx.drift_catalog = list(items)
        return _held(self.state, f"Drift catalog: {len(items)} items", items=list(items))

    def _do_emit_p1_declaration(self) -> TransitionResult:
        """
        §A.6 + §C. P27: no P1 block ⇒ no P3 later.
        R2-06: v0.2 checked four fields and never verified §A.5 ran, nor that a
        SHA had been pinned — so a P1 block could be emitted with no drift
        catalog and no pin while the machine reported success.
        """
        missing = [
            name for name, val in (
                ("time_anchor", self.ctx.time_anchor),
                ("pinned_sha", self.ctx.pinned_sha),
                ("prompt_env", self.ctx.prompt_env),
                ("session_type", self.ctx.session_type),
                ("protocol_version", self.ctx.protocol_version),
            ) if not val
        ]
        if not self.ctx.drift_catalog:
            missing.append("drift_catalog (§A.5, 3-8 items)")
        if missing:
            return _refused(
                self.state, f"Phase 1 block incomplete — missing {missing}", missing=missing
            )
        self.ctx.p1_declared = True
        header = " · DEGRADED" if self.ctx.degraded else ""
        return _advanced(BootState.BS_LOGIN, f"Phase 1 declaration emitted{header}")

    def _do_await_confirmation(self, confirmed: bool) -> TransitionResult:
        """§A.7 — do not begin work until the declared state is acknowledged."""
        self.ctx.confirmation_received = confirmed
        if not confirmed:
            return _refused(self.state, "Awaiting operator acknowledgment")
        return _advanced(BootState.BS_RUNTIME, "Operator confirmed declared state")

    # -- runtime ---------------------------------------------------------

    def _do_do_work(self, description: str) -> TransitionResult:
        self.ctx.work_done = True
        return _held(self.state, f"Work: {description}")

    def _do_propose_fich(self, kind: str, summary: str) -> TransitionResult:
        """
        R2-03. §F.9 bars F/IC/H proposals against unverified state, and P21 bars
        self-promotion. v0.2 exposed `may_propose_fich` as a property no
        transition consulted — which is F-BSM-09 (dead governance state)
        reproduced inside the fix for F-BSM-09. This is the transition that
        reads it.
        """
        if kind not in {"F", "IC", "H"}:
            return _refused(self.state, "kind must be one of F, IC, H")
        if not self.ctx.may_propose_fich:
            return _refused(
                self.state,
                f"{kind}-class proposal barred — REGISTERED.md unverified "
                f"(class_state={self.ctx.class_state}, fetch_ok="
                f"{self.ctx.registered_fetch_ok}); §F halt 9",
                kind=kind,
            )
        self.ctx.notes.append(f"{kind}-CAND proposed: {summary} (P21: Z2 decides)")
        return _held(self.state, f"{kind}-class candidate staged for Z2: {summary}")

    def _do_enter_registry_touching(self) -> TransitionResult:
        """
        F-BSM-05. OPERATOR_RUNBOOK §3a note 3: "IC-030 still applies — halt if
        REGISTERED.md is unavailable when registry-touching work begins
        mid-session." v0.1 called this an unmodeled limitation; it is a
        specified, ratified requirement.
        """
        self.ctx.registry_touching = True
        if self.ctx.registered_fetch_ok and self.ctx.class_state == "OK":
            return _held(self.state, "Session became registry-touching; REGISTERED.md already OK")
        return _advanced(
            BootState.BS_KERNEL,
            "Session became registry-touching mid-run — re-entering KERNEL to verify "
            "REGISTERED.md before any F/IC/H work (IC-030)",
        )

    def _do_request_close(self) -> TransitionResult:
        if not self.ctx.p1_declared:
            return _diverted(
                BootState.BS_HALTED,
                "P27 violation — no Phase 1 block in transcript. Emit "
                "<<<ACAT_PROTOCOL_ERROR>>>, not Phase 3. Session is NON_CORPUS.",
            )
        return _advanced(BootState.BS_SHUTDOWN, "Close requested → B.0 gate")

    # -- close -----------------------------------------------------------

    def _do_run_b0_verification(self, checks: List[Evidence]) -> TransitionResult:
        """
        §B.0 hard gate. Close artifacts are unreachable except through this
        action — that state boundary IS the gate (F-BSM-02).

        R2-01: v0.2 advanced on *any* non-empty list, so two arbitrary Evidence
        objects satisfied a gate that §B.0 defines by check family. Each family
        the session touched now needs a tagged entry; CHECK_UNAVAILABLE counts
        as declared (§B.0 allows it explicitly) but is surfaced so B.6 must
        account for it.
        """
        if not checks:
            return _refused(
                self.state,
                "B.0 requires recorded checks (§F halt 7: do not draft a close artifact "
                "before the verification block)",
            )
        # Validate families BEFORE recording, so a refused B.0 does not leave
        # partial evidence in the journal that a later step could quote.
        supplied = {e.family for e in checks if e.family}
        missing = sorted(f for f in self.ctx.session_touched if f not in supplied)
        if missing:
            return _refused(
                self.state,
                f"B.0 incomplete — the session touched {missing} but no check family "
                f"evidence was supplied for them. Required probes: "
                f"{ {m: B0_CHECK_FAMILIES[m] for m in missing} }",
                missing_families=missing,
            )
        for ev in checks:
            self._record(ev)
        unavailable = [e for e in checks if e.unavailable_reason is not None]
        self.ctx.close_steps_done.append("B.0 empirical verification block")
        note = f"; {len(unavailable)} CHECK_UNAVAILABLE declared" if unavailable else ""
        return _advanced(
            BootState.BS_CLOSE_GATE,
            f"B.0 complete — {len(checks)} checks across "
            f"{sorted(self.ctx.session_touched)}{note}",
            unavailable=[e.check for e in unavailable],
        )

    def _do_run_close_sequence(self, steps: Dict[str, Evidence]) -> TransitionResult:
        """
        §B.1-B.5. "Steps cannot be skipped."
        R2-02: v0.2 took a list of step *strings* the caller chose, so passing
        `list(CLOSE_STEPS[1:6])` marked all five done with nothing performed —
        the same assertion-as-verification the revision claims to remove. Each
        step now carries its own Evidence.
        """
        required = list(CLOSE_STEPS[1:6])
        missing = [s for s in required if s not in steps]
        if missing:
            return _refused(self.state, f"Close sequence incomplete — no evidence for {missing}")
        unevidenced = [s for s in required if not isinstance(steps[s], Evidence)]
        if unevidenced:
            return _refused(self.state, f"Steps must carry Evidence, not assertions: {unevidenced}")
        unconfirmed = [
            s for s in required
            if not steps[s].confirms and steps[s].unavailable_reason is None
        ]
        if unconfirmed:
            return _refused(
                self.state,
                f"Steps recorded with empty output and no CHECK_UNAVAILABLE reason: {unconfirmed}",
            )
        for s in required:
            self._record(steps[s])
            self.ctx.close_steps_done.append(s)
        return _advanced(BootState.BS_RECONCILE, "B.1-B.5 complete, each with recorded evidence")

    def _do_emit_receipt_reconciliation(self, paragraph: str) -> TransitionResult:
        """
        §B.6 — REQUIRED. "Receipts must quote from the verification block ...
        Do not omit the paragraph."

        R2-04: v0.2 accepted any non-empty string, so "done" advanced to
        BS_JOURNAL. The paragraph must now carry the canonical heading and
        quote at least one recorded B.0 check verbatim, which is what "quote
        from B.0" means operationally.
        """
        text = paragraph.strip()
        if not text:
            return _refused(self.state, "B.6 paragraph is mandatory and may not be empty")
        if RECONCILIATION_HEADING not in text:
            return _refused(
                self.state,
                f"B.6 paragraph must be titled '{RECONCILIATION_HEADING}' (§B.6 format)",
            )
        b0_checks = [e.check for e in self.ctx.evidence if e.check]
        if not b0_checks:
            return _refused(self.state, "B.6 must quote from B.0 outputs; no evidence recorded")
        quoted = [c for c in b0_checks if c in text]
        if not quoted:
            return _refused(
                self.state,
                "B.6 quotes no recorded check. §B.0: 'The verification block output "
                "becomes the source of truth for the receipt.' Quote at least one of: "
                f"{b0_checks[:6]}",
                recorded_checks=b0_checks,
            )
        undeclared = [
            e.check for e in self.ctx.evidence
            if e.unavailable_reason is not None and e.check not in text
        ]
        if undeclared:
            return _refused(
                self.state,
                f"B.6 must account for every CHECK_UNAVAILABLE; unaccounted: {undeclared}",
                unaccounted=undeclared,
            )
        self.ctx.close_steps_done.append("B.6 receipt reconciliation paragraph")
        return _advanced(
            BootState.BS_JOURNAL,
            f"B.6 recorded, quoting {len(quoted)} B.0 check(s)",
            quoted=quoted,
        )

    def _do_post_wgs(self, draft_id: str) -> TransitionResult:
        """§B.7 — slack_send_message_draft (operator-send default, P30/P31). See DEV-06."""
        if not draft_id.strip():
            return _refused(self.state, "WGS draft id required")
        step = "B.7 log to #wgs-sync via slack_send_message_draft"
        if step in self.ctx.close_steps_done:
            return _refused(self.state, "B.7 already recorded")
        self.ctx.close_steps_done.append(step)
        return _held(
            self.state,
            f"WGS draft staged: {draft_id} (asserted, not verified — DEV-06)",
            draft_id=draft_id,
        )

    def _do_bind_session_id(self, session_id: str) -> TransitionResult:
        """
        §B.8 — S-MMDDYY-NN-{slug} in the WGS post, the P3 SESSION field, filenames.
        R2-13: v0.2 accepted any "S-" prefix; the pattern below is the one
        tools/acat_session_validator.py:33 enforces.
        R2-05: v0.2 appended B.8 to close_steps_done *before* testing the
        outstanding list, so a refused call still recorded the step as done and
        the journal reported a prerequisite met out of order.
        """
        if not SESSION_ID_PATTERN.match(session_id):
            return _refused(
                self.state,
                f"Session ID '{session_id}' does not match S-MMDDYY-NN-{{slug}} "
                f"({SESSION_ID_PATTERN.pattern}) — IC-027",
            )
        step = "B.8 session ID binding"
        outstanding = [s for s in self.ctx.outstanding_close_steps() if s != step]
        if outstanding:
            return _refused(
                self.state,
                f"Cannot bind session ID — outstanding close steps: {outstanding}",
                outstanding=outstanding,
            )
        self.ctx.close_steps_done.append(step)
        return _advanced(BootState.BS_DONE, f"Session {session_id} closed clean")

    # -- degraded / halted -----------------------------------------------

    def _do_report_status(self) -> TransitionResult:
        return _held(
            self.state,
            f"degraded={self.ctx.degraded} causes={sorted(self.ctx.degradation_causes)} "
            f"path_c={self.ctx.path_c} class_state={self.ctx.class_state} "
            f"may_propose_fich={self.ctx.may_propose_fich}",
            causes=sorted(self.ctx.degradation_causes),
        )

    def _do_request_recovery(self, cause: str, evidence: Evidence, class_state: Optional[str] = None) -> TransitionResult:
        """
        R2-11: v0.2 cleared `degraded` wholesale on one REGISTERED.md re-check,
        so a session degraded by live-state loss could recover by re-verifying a
        different channel and then emit a non-DEGRADED P1. Recovery is now
        cause-specific and clears exactly the cause it re-verified.
        """
        if cause not in self.ctx.degradation_causes:
            return _refused(
                self.state,
                f"'{cause}' is not an active degradation cause "
                f"{sorted(self.ctx.degradation_causes)}",
            )
        self._record(evidence)
        if not evidence.confirms:
            return _refused(self.state, f"Recovery refused — no confirmable evidence for '{cause}'")
        if cause == "registered":
            if class_state != "OK":
                return _refused(self.state, f"Recovery refused — class_state still {class_state}")
            self.ctx.class_state = "OK"
            self.ctx.registered_fetch_ok = True
        elif cause == "live_state_wgs":
            self.ctx.path_c = False
            self.ctx.live_state_ok = True
        elif cause == "live_state_haioscc":
            self.ctx.live_state_ok = True
        self.ctx.degradation_causes.discard(cause)
        if self.ctx.degradation_causes:
            return _held(
                self.state,
                f"Recovered '{cause}'; still degraded by "
                f"{sorted(self.ctx.degradation_causes)}",
            )
        return _advanced(BootState.BS_INIT, f"Recovered '{cause}' — no degradation causes remain")

    def _do_operator_resume(self, instruction: str) -> TransitionResult:
        """
        §F: "Stop and ask the user before proceeding." The halt is a question,
        not a tombstone — but resuming means re-running the guard that failed.
        R2-11: v0.2 funnelled every halt cause into BS_DEGRADED from an arbitrary
        instruction, turning "stop and ask" into generic permission to continue.
        """
        if not instruction.strip():
            return _refused(self.state, "Resume requires an operator instruction")
        target = self._halt_return
        if target is None:
            return _refused(self.state, "No interrupted state recorded — cannot resume")
        self.ctx.notes.append(
            f"Operator resume from {target.name} (halt: {self._halt_cause}): {instruction}"
        )
        self._halt_return = None
        return _advanced(
            target,
            f"Resumed into {target.name} — the failed guard must re-run: {instruction}",
            halt_cause=self._halt_cause,
        )


# --------------------------------------------------------------------------
# Self-test — the B.0 evidence for this file's own claims (F-BSM-01)
# --------------------------------------------------------------------------

def _selftest() -> int:
    failures: List[str] = []

    def check(label: str, cond: bool) -> None:
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        if not cond:
            failures.append(label)

    def boot(m: BootStateMachine, *, prompt_env="ADVERSARIAL", operator=True,
             class_state="OK", skip_rationale=None) -> None:
        m.transition("start")
        m.transition("anchor_time", evidence=Evidence("TZ=America/Chicago date",
                                                      "Sun Sep 14 2026 12:00 CDT"))
        m.transition("fetch_live_state",
                     evidence=Evidence("slack_read_channel C0AND66PT7U limit=10", "10 msgs"),
                     slack_mcp_available=True, haioscc_reachable=True)
        m.transition("pin_commit", evidence=Evidence("git rev-parse HEAD",
                                                     "6d3443af07ba18db56c1d716e24c1f9f33b2b056"))
        m.transition("load_rituals", evidence=Evidence("GET CURRENT.md + SESSION_RITUALS.md", "200 200"))
        m.transition("load_governance_version", evidence=Evidence("head -5 GOVERNANCE.md", "v6.4.3"))
        m.transition("classify_session", prompt_env=prompt_env, session_type="ANALYSIS",
                     operator_supplied=operator)
        if skip_rationale:
            m.transition("declare_registry_skip", rationale=skip_rationale)
        else:
            m.transition("fetch_registered", evidence=Evidence("GET REGISTERED.md", "F-54 ..."),
                         class_state=class_state)
        m.transition("build_drift_catalog",
                     items=["[C-01] overclaim", "[C-02] scope creep", "[C-03] phantom cite"])
        m.transition("emit_p1_declaration")
        m.transition("await_confirmation", confirmed=True)

    print("\n--- T1: happy path, registry-touching ---")
    m = BootStateMachine(RitualSurface.SESSION_RITUALS, registry_touching=True,
                         session_touched={"git"}, verbose=False)
    boot(m)
    check("reaches RUNTIME", m.current_state() is BootState.BS_RUNTIME)
    check("may propose F/IC/H", m.ctx.may_propose_fich)
    check("propose_fich accepted", m.transition("propose_fich", kind="IC",
                                                summary="phantom section").success)

    print("\n--- T2: B.0 is a structural gate (F-BSM-02, R2-01) ---")
    m.transition("do_work", description="adversarial review")
    m.transition("request_close")
    check("in SHUTDOWN", m.current_state() is BootState.BS_SHUTDOWN)
    check("close artifact illegal in SHUTDOWN", not m.transition("emit_close_artifact").success)
    check("empty B.0 refused", not m.transition("run_b0_verification", checks=[]).success)
    r = m.transition("run_b0_verification",
                     checks=[Evidence("ls -la outputs", "total 0", family="files")])
    check("B.0 refused: touched family unevidenced (R2-01)", not r.success)
    m.transition("run_b0_verification", checks=[
        Evidence("git status --short", " M z1-inbox/2026-09-14/boot_state_machine_v0_2.py",
                 family="git"),
    ])
    check("B.0 advances once family evidenced", m.current_state() is BootState.BS_CLOSE_GATE)

    print("\n--- T3: close steps need evidence, not strings (R2-02) ---")
    check("string list rejected",
          not m.transition("run_close_sequence", steps=dict.fromkeys(CLOSE_STEPS[1:6], "done")).success)
    m.transition("run_close_sequence",
                 steps={s: Evidence(f"probe::{s}", "ok") for s in CLOSE_STEPS[1:6]})
    check("in RECONCILE", m.current_state() is BootState.BS_RECONCILE)

    print("\n--- T4: B.6 must quote B.0 (F-BSM-06, R2-04) ---")
    check("empty reconciliation refused",
          not m.transition("emit_receipt_reconciliation", paragraph="   ").success)
    check("unheaded paragraph refused",
          not m.transition("emit_receipt_reconciliation", paragraph="all fine").success)
    check("unquoted paragraph refused",
          not m.transition("emit_receipt_reconciliation",
                           paragraph="RECEIPT RECONCILIATION — all fine.").success)
    m.transition("emit_receipt_reconciliation",
                 paragraph="RECEIPT RECONCILIATION — `git status --short` confirmed one "
                           "modified file; no in-session assertion required walking back.")
    check("quoting paragraph accepted", m.current_state() is BootState.BS_JOURNAL)

    print("\n--- T5: B.8 ordering and pattern (R2-05, R2-13) ---")
    r = m.transition("bind_session_id", session_id="S-091426-01-bsm-review")
    check("B.8 refused while B.7 outstanding", not r.success)
    check("B.8 NOT recorded on refusal (R2-05)",
          "B.8 session ID binding" not in m.ctx.close_steps_done)
    check("loose session id rejected (R2-13)",
          not m.transition("bind_session_id", session_id="S-x").success)
    m.transition("post_wgs", draft_id="draft-0914-01")
    check("clean close reaches DONE",
          m.transition("bind_session_id", session_id="S-091426-01-bsm-review").success)
    check("no outstanding close steps", not m.ctx.outstanding_close_steps())

    print("\n--- T6: no default-pass guards (F-BSM-03) ---")
    m2 = BootStateMachine(RitualSurface.SESSION_RITUALS, verbose=False)
    m2.transition("start")
    r = m2.transition("anchor_time")
    check("anchor_time without evidence is refused", not r.success)
    check("outcome is REFUSED, not a silent pass", r.outcome is Outcome.REFUSED)
    check("still in TIME_ANCHOR", m2.current_state() is BootState.BS_TIME_ANCHOR)

    print("\n--- T7: live-state paths (F-BSM-04, R2-10) ---")
    m3 = BootStateMachine(RitualSurface.SESSION_RITUALS, verbose=False)
    m3.transition("start")
    m3.transition("anchor_time", evidence=Evidence("date", "Sun Sep 14 2026"))
    r = m3.transition("fetch_live_state", evidence=Evidence.unavailable("wgs", "mcp down"),
                      slack_mcp_available=False, haioscc_reachable=False)
    check("both channels down → HALTED", m3.current_state() is BootState.BS_HALTED)
    check("outcome DIVERTED, not ADVANCED (R2-08)", r.outcome is Outcome.DIVERTED)
    check("guard_passed is False on divert", not r.guard_passed)
    m3.transition("operator_resume", instruction="retry with haioscc secondary")
    check("resume returns to interrupted state (R2-11)", m3.current_state() is BootState.BS_POST)

    m4 = BootStateMachine(RitualSurface.SESSION_RITUALS, verbose=False)
    m4.transition("start")
    m4.transition("anchor_time", evidence=Evidence("date", "Sun Sep 14 2026"))
    m4.transition("fetch_live_state", evidence=Evidence("haioscc", "200"),
                  slack_mcp_available=False, haioscc_reachable=True)
    check("PATH C proceeds degraded", m4.current_state() is BootState.BS_SECURE_BOOT and m4.ctx.degraded)
    m5 = BootStateMachine(RitualSurface.SESSION_RITUALS, verbose=False)
    m5.transition("start")
    m5.transition("anchor_time", evidence=Evidence("date", "Sun Sep 14 2026"))
    m5.transition("fetch_live_state", evidence=Evidence("wgs", "10 msgs"),
                  slack_mcp_available=True, haioscc_reachable=False)
    check("haioscc down is degraded, not 'OK' (R2-10)", m5.ctx.degraded)

    print("\n--- T8: mid-session registry-touching (F-BSM-05, R2-03) ---")
    m6 = BootStateMachine(RitualSurface.SESSION_RITUALS, verbose=False)
    boot(m6, skip_rationale="no F/IC/H items expected")
    check("F/IC/H barred after skip", not m6.ctx.may_propose_fich)
    check("propose_fich actually refused (R2-03)",
          not m6.transition("propose_fich", kind="F", summary="x").success)
    m6.transition("enter_registry_touching")
    check("re-entered KERNEL", m6.current_state() is BootState.BS_KERNEL)
    m6.transition("fetch_registered", evidence=Evidence("GET REGISTERED.md", "stale"),
                  class_state="STALE")
    check("STALE → DEGRADED (§F.9)", m6.current_state() is BootState.BS_DEGRADED)
    check("wrong-cause recovery refused (R2-11)",
          not m6.transition("request_recovery", cause="live_state_wgs",
                            evidence=Evidence("x", "y")).success)

    print("\n--- T9: P1 completeness and AFA-1 (R2-06, R2-12) ---")
    m7 = BootStateMachine(RitualSurface.SESSION_RITUALS, verbose=False)
    m7.transition("start")
    m7.transition("anchor_time", evidence=Evidence("date", "Sun Sep 14 2026"))
    m7.transition("fetch_live_state", evidence=Evidence("wgs", "ok"),
                  slack_mcp_available=True, haioscc_reachable=True)
    m7.transition("pin_commit", evidence=Evidence("git rev-parse HEAD", "6d3443af"))
    m7.transition("load_rituals", evidence=Evidence("GET", "200"))
    m7.transition("load_governance_version", evidence=Evidence("head -5", "v6.4.3"))
    m7.transition("classify_session", prompt_env="ADVERSARIAL", session_type="BUILD",
                  operator_supplied=False)
    check("non-operator prompt_env discarded → NEUTRAL (R2-12)", m7.ctx.prompt_env == "NEUTRAL")
    check("operator_supplied recorded False", not m7.ctx.prompt_env_operator_supplied)
    m7.transition("declare_registry_skip", rationale="none expected")
    check("P1 refused without drift catalog (R2-06)",
          not m7.transition("emit_p1_declaration").success)

    print("\n--- T10: contract self-checks ---")
    m8 = BootStateMachine(RitualSurface.SESSION_RITUALS, verbose=False)
    m8.state = BootState.BS_RUNTIME       # simulate a session that skipped Phase 1
    m8.transition("request_close")
    check("P3-without-P1 halts (P27)", m8.current_state() is BootState.BS_HALTED)
    every_action = {a for acts in ALLOWED_ACTIONS.values() for a in acts}
    check("every action has a source anchor (P29 part 2)",
          every_action <= set(SOURCE_ANCHORS))
    try:
        BootStateMachine(RitualSurface.CLAUDE_MD, verbose=False)
        unsupported_refused = False
    except NotImplementedError:
        unsupported_refused = True
    check("unsupported ritual surface refused (R2-07)", unsupported_refused)
    j = m.export_journal()
    check("journal carries full evidence records (R2-09)",
          all(isinstance(e, dict) and "output" in e for e in j["evidence"]))
    check("journal keeps deviation direction (R2-09)",
          all(d.get("direction") for d in j["deviations"]))
    check("journal declares advisory status", j["advisory_only"] is True)
    long_out = "x" * 500
    check("journal does not truncate literal output (R2-09)",
          Evidence("probe", long_out).to_dict()["output"] == long_out)

    print(f"\n{'=' * 62}")
    if failures:
        print(f"SELF-TEST FAILED — {len(failures)} assertion(s): {failures}")
        return 1
    print("SELF-TEST PASSED — all assertions green")
    print(f"{'=' * 62}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
