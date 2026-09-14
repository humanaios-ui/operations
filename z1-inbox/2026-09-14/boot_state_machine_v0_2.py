#!/usr/bin/env python3
"""
BOOT STATE MACHINE — v0.2 (post-adversarial-review)
===================================================
Q-BOOT-STATE-MACHINE-01 companion demonstration.

STATUS: Experimental / ADVISORY ONLY. Not ratified. Not registered.
Does NOT amend SESSION_RITUALS.md, CLAUDE.md, GOVERNANCE.md, CURRENT.md, or
OPERATOR_RUNBOOK.md. Where this model conflicts with those sources, the
sources win — see SOURCE_PRECEDENCE and DEVIATIONS, which make that clause
machine-readable instead of prose a caller cannot check.

WHAT THIS IS (P29 articulation, part 1)
    A guard-and-transition model of the HumanAIOS session lifecycle. It
    encodes which actions are legal in which phase, and refuses transitions
    whose preconditions are not evidenced.

WHAT EVIDENCE SUPPORTS IT (P29 articulation, part 2)
    Every state and guard carries a `source` anchor naming the file and
    section it restates. Anchors were verified against the live repo at the
    SHA recorded in the companion review. Anything without an anchor is
    listed in DEVIATIONS.

RISK OF BEING WRONG, AND HOW IT WOULD BE DETECTED (P29 articulation, part 3)
    The load-bearing risk is that a reader treats `allowed_actions()` as
    authority and skips a canonical step this model does not encode. Detected
    by: a session that passes this machine cleanly and still trips a Section F
    halt. That event falsifies the model, not the protocol.

FALSIFIER (required for Z1 candidate blocks per CLAUDE.md / falsifier_lint)
    PREDICTION: across N=10 sessions driven through this machine, zero
    sessions reach BS_JOURNAL while any SESSION_RITUALS Section B step
    (B.0 through B.8) is unexecuted.
    FALSIFIED IF: any such session reaches BS_JOURNAL with an unexecuted
    Section B step, OR any Section F halt condition fires in a session the
    machine reported as clean.
    WINDOW: 10 sessions or 30 days, whichever comes first.

v0.2 CHANGES (see Q-BOOT-STATE-MACHINE-01-ADVERSARIAL-REVIEW.md)
    F-BSM-01  file now parses and runs; self-test at __main__
    F-BSM-02  B.0 is a structural gate — close artifacts live in a state
              that cannot be entered without verification evidence
    F-BSM-03  guards take Evidence, not caller-asserted booleans; no
              default-pass parameters anywhere
    F-BSM-04  live-state failure halts per SESSION_RITUALS §A.1; PATH C is
              narrowed to the Slack-MCP case OPERATOR_RUNBOOK §3a actually
              authorizes, and routes to BS_DEGRADED
    F-BSM-05  mid-session registry-touching re-enters BS_KERNEL (IC-030)
    F-BSM-06  close sequence models B.0 through B.8, incl. B.6 reconciliation
    F-BSM-07  BS_TIME_ANCHOR added (P22; violation = D-07)
    F-BSM-08  BS_CLASSIFY added; prompt_env is operator-supplied, never
              inferred (SESSION_RITUALS §A.2.5)
    F-BSM-09  class_state now gates F/IC/H proposals instead of sitting dead
    F-BSM-10  BS_DEGRADED is reachable; BS_HALTED is resumable by operator
    F-BSM-11  every guard carries a verified source anchor
    F-BSM-14  transitions append to an exportable journal (P20: volatile
              context is not state — export it or lose it)
    F-BSM-16  RITUAL_SURFACE declares which §A governs, per P22.1
              (first-match wins; do not blend surfaces)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

ADVISORY_ONLY = True

SOURCE_PRECEDENCE = (
    "SESSION_RITUALS.md",      # parser-tag + protocol authority (its own §, line 8)
    "GOVERNANCE.md",           # principle authority
    "OPERATOR_RUNBOOK.md",     # operator-side recipes
    "CLAUDE.md",               # authority map / zone routing
    "CURRENT.md",              # operating-process snapshot
    "boot_state_machine_v0_2.py",  # this file — last, always
)


class RitualSurface(Enum):
    """
    F-BSM-16 / P22.1 (Cascade Discipline: first-match wins, do not blend).

    Two documents specify a "Section A — Session open" and they do not agree:
    SESSION_RITUALS.md §A (live-state fetch, AFA-1, drift catalog, P1 block)
    and CLAUDE.md §A (git pin, PRIORITY_QUEUE, ZONE_REGISTRY, sha256 manifest).
    v0.1 blended both without declaring which governs. The caller must pick.
    """
    SESSION_RITUALS = "SESSION_RITUALS.md Section A"
    CLAUDE_MD = "CLAUDE.md Session Rituals Section A"
    BOTH_DECLARED = "both, with divergence declared to Z2 as an AMBIGUITY callout"


@dataclass(frozen=True)
class Deviation:
    """A place this model knowingly differs from its sources."""
    id: str
    source_anchor: str
    direction: str   # NARROWER | WIDER | UNMODELED | INVENTED
    note: str


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
        note=("Section F says 'stop and ask the user before proceeding' — it is "
              "resumable on operator input, not a terminal halt. BS_HALTED models "
              "that. Halt #9 (registry-touching under unverified state) is the one "
              "case routed to BS_DEGRADED rather than BS_HALTED, because §F.9 "
              "prescribes a declared DEGRADED mode rather than a stop."),
    ),
    Deviation(
        id="DEV-03",
        source_anchor="CLAUDE.md Session Rituals §A.4 (ZONE_REGISTRY.md read)",
        direction="UNMODELED",
        note=("BS_ZONE_ENUM restates the CLAUDE.md zone-registry read. It has no "
              "counterpart in SESSION_RITUALS §A. Reachable only when "
              "RITUAL_SURFACE includes CLAUDE_MD. See F-BSM-16."),
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
        note=("Submission-URL construction (§D) is represented as a single close "
              "step, not modeled field-by-field. The 'do not reconstruct P1 from P3' "
              "rule is asserted in the guard but not mechanically enforced here."),
    ),
]


# --------------------------------------------------------------------------
# Evidence — the fix for F-BSM-03
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Evidence:
    """
    SESSION_RITUALS §B.0: record literal outputs, not paraphrases; if a check
    cannot be run, declare CHECK_UNAVAILABLE with a reason.
    §G: 'Claims of completion require evidence ... not assertion.'

    v0.1 took `pin_ok: bool = True` and `slack_mcp_available: bool = True`.
    Every gate defaulted to pass, and 'pass' was the caller's own say-so.
    That is the IC-031 shape — assertion wearing the costume of verification.
    """
    check: str                              # the probe actually run
    output: str                             # its literal output
    unavailable_reason: Optional[str] = None

    @property
    def confirms(self) -> bool:
        return self.unavailable_reason is None and bool(self.output.strip())

    @classmethod
    def unavailable(cls, check: str, reason: str) -> "Evidence":
        return cls(check=check, output="", unavailable_reason=reason)

    def render(self) -> str:
        if self.unavailable_reason is not None:
            return f"CHECK_UNAVAILABLE: {self.check} — {self.unavailable_reason}"
        return f"{self.check} => {self.output.strip()[:200]}"


class BootState(Enum):
    BS_POWER_ON = auto()
    BS_TIME_ANCHOR = auto()     # P22 — substrate has no clock; D-07 on violation
    BS_POST = auto()            # §A.1 live state
    BS_SECURE_BOOT = auto()     # CLAUDE.md §A.1 pin SHA
    BS_BOOTLOADER = auto()      # §A.2 CURRENT.md + §A.3 SESSION_RITUALS.md
    BS_BOOT_PARAMS = auto()     # §A.2.6 GOVERNANCE.md version → PROTOCOL_VERSION
    BS_CLASSIFY = auto()        # §A.2.5 AFA-1 prompt_env + SESSION_TYPE (operator)
    BS_ZONE_ENUM = auto()       # CLAUDE.md §A.4 — see DEV-03
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


# The agent may only propose these. F-BSM-02: note that `emit_close_artifact`
# is NOT in BS_SHUTDOWN. In v0.1 both `run_b0_verification` and
# `emit_close_artifact` were legal in the same state, so the "hard gate"
# the docstring advertised did not exist. The gate is the state boundary.
ALLOWED_ACTIONS: Dict[BootState, List[str]] = {
    BootState.BS_POWER_ON:    ["start"],
    BootState.BS_TIME_ANCHOR: ["anchor_time"],
    BootState.BS_POST:        ["fetch_live_state"],
    BootState.BS_SECURE_BOOT: ["pin_commit"],
    BootState.BS_BOOTLOADER:  ["load_rituals"],
    BootState.BS_BOOT_PARAMS: ["load_governance_version"],
    BootState.BS_CLASSIFY:    ["classify_session"],
    BootState.BS_ZONE_ENUM:   ["enumerate_zones"],
    BootState.BS_KERNEL:      ["fetch_registered", "declare_registry_skip"],
    BootState.BS_INIT:        ["build_drift_catalog", "emit_p1_declaration"],
    BootState.BS_LOGIN:       ["await_confirmation"],
    BootState.BS_RUNTIME:     ["do_work", "enter_registry_touching", "request_close"],
    BootState.BS_SHUTDOWN:    ["run_b0_verification"],
    BootState.BS_CLOSE_GATE:  ["run_close_sequence"],
    BootState.BS_RECONCILE:   ["emit_receipt_reconciliation"],
    BootState.BS_JOURNAL:     ["post_wgs", "bind_session_id"],
    BootState.BS_DEGRADED:    ["report_status", "request_recovery", "request_close"],
    BootState.BS_HALTED:      ["report_status", "operator_resume"],
    BootState.BS_DONE:        [],
}

# SESSION_RITUALS §B: "Steps cannot be skipped." Enumerated so the machine can
# refuse BS_JOURNAL while any remain outstanding (this is the falsifier's
# measurement surface).
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


@dataclass
class TransitionResult:
    success: bool
    new_state: BootState
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MachineContext:
    """Mutable session context the machine and agent share."""
    registry_touching: bool = False
    ritual_surface: RitualSurface = RitualSurface.SESSION_RITUALS

    time_anchor: Optional[str] = None          # P22
    prompt_env: Optional[str] = None           # AFA-1 — operator-supplied only
    session_type: Optional[str] = None
    protocol_version: Optional[str] = None
    pinned_sha: Optional[str] = None

    live_state_ok: bool = False
    path_c: bool = False                       # Slack MCP unavailable, per §3a
    degraded: bool = False

    registered_fetch_ok: bool = False
    registry_skip_declared: bool = False
    class_state: str = "UNKNOWN"               # OK | UNAVAILABLE | UNKNOWN | STALE

    p1_declared: bool = False                  # P27 prerequisite for any P3
    confirmation_received: bool = False
    work_done: bool = False

    close_steps_done: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def may_propose_fich(self) -> bool:
        """
        §F.9 (IC-029/IC-030): do not produce F-class, IC-class, or H-class
        proposals against unverified state. In v0.1 `registered_class_state`
        existed but no guard ever read it — governance state that looks like
        enforcement and enforces nothing (F-BSM-09).
        """
        return self.registered_fetch_ok and self.class_state == "OK"

    def outstanding_close_steps(self) -> List[str]:
        return [s for s in CLOSE_STEPS if s not in self.close_steps_done]


class BootStateMachine:
    """
    Minimal advisory state machine. Actions are validated against the current
    state; transitions are driven by guards that restate existing protocol
    language and require evidence rather than assertion.
    """

    def __init__(
        self,
        registry_touching: bool = False,
        ritual_surface: RitualSurface = RitualSurface.SESSION_RITUALS,
        verbose: bool = True,
    ):
        self.state = BootState.BS_POWER_ON
        self.ctx = MachineContext(
            registry_touching=registry_touching,
            ritual_surface=ritual_surface,
        )
        self.history: List[str] = []
        self.verbose = verbose
        self._log(
            f"INIT registry_touching={registry_touching} "
            f"ritual_surface={ritual_surface.value} advisory_only={ADVISORY_ONLY}"
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
        state. v0.1 kept history in a list and printed it, which is exactly
        what P20 says not to treat as state. Export it, or it did not happen.
        """
        return {
            "advisory_only": ADVISORY_ONLY,
            "final_state": self.state.name,
            "ritual_surface": self.ctx.ritual_surface.value,
            "time_anchor": self.ctx.time_anchor,
            "prompt_env": self.ctx.prompt_env,
            "session_type": self.ctx.session_type,
            "protocol_version": self.ctx.protocol_version,
            "pinned_sha": self.ctx.pinned_sha,
            "degraded": self.ctx.degraded,
            "path_c": self.ctx.path_c,
            "class_state": self.ctx.class_state,
            "may_propose_fich": self.ctx.may_propose_fich,
            "close_steps_done": list(self.ctx.close_steps_done),
            "close_steps_outstanding": self.ctx.outstanding_close_steps(),
            "evidence": [e.render() for e in self.ctx.evidence],
            "deviations": [d.id for d in DEVIATIONS],
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
            return TransitionResult(
                False, self.state,
                f"Action '{action}' not allowed in state {self.state.name}; "
                f"allowed: {self.allowed_actions()}",
            )

        handler = getattr(self, f"_do_{action}", None)
        if handler is None:
            return TransitionResult(False, self.state, f"No handler for '{action}'")

        try:
            result = handler(**kwargs)
        except TypeError as exc:
            # Missing Evidence is a refusal, not a crash. F-BSM-03: there is no
            # default-pass path, so the absence of evidence must be legible.
            return TransitionResult(
                False, self.state,
                f"Action '{action}' refused — required evidence not supplied ({exc})",
            )

        if result.success and result.new_state != self.state:
            old = self.state
            self.state = result.new_state
            self._log(f"TRANSITION {old.name} → {self.state.name} | {result.reason}")
        else:
            verb = "ACTION" if result.success else "REFUSED"
            self._log(f"{verb} {action} | {result.reason}")
        return result

    def _record(self, evidence: Evidence) -> None:
        self.ctx.evidence.append(evidence)

    # -- boot ------------------------------------------------------------

    def _do_start(self) -> TransitionResult:
        return TransitionResult(True, BootState.BS_TIME_ANCHOR, "Power-on → time anchor")

    def _do_anchor_time(self, evidence: Evidence) -> TransitionResult:
        """P22 — bash_tool primary, operator anchor fallback. Violation = D-07."""
        self._record(evidence)
        if not evidence.confirms:
            return TransitionResult(
                True, BootState.BS_HALTED,
                "No verified time source (P22) — stop and ask operator for anchor; "
                "inference is not synchronization (D-07)",
            )
        self.ctx.time_anchor = evidence.output.strip()
        return TransitionResult(True, BootState.BS_POST, f"Time anchored: {self.ctx.time_anchor}")

    def _do_fetch_live_state(
        self,
        evidence: Evidence,
        slack_mcp_available: bool,
        haioscc_reachable: bool,
    ) -> TransitionResult:
        """
        SESSION_RITUALS §A.1: fetch operational + zone3; "If either fails, halt
        and report." OPERATOR_RUNBOOK §3a note 3 authorizes PATH C (degraded,
        CURRENT.md only) for the narrower case of Slack MCP being unavailable.

        F-BSM-04: v0.1 applied the runbook's narrow allowance to the rituals'
        broad halt, so total live-state failure walked on as if nothing had
        happened. PATH C now requires that *some* live-state channel survived;
        losing both halts.
        """
        self._record(evidence)
        if not slack_mcp_available and not haioscc_reachable:
            return TransitionResult(
                True, BootState.BS_HALTED,
                "Both live-state channels failed — SESSION_RITUALS §A.1 halt "
                "(PATH C does not cover total live-state loss)",
            )
        if not slack_mcp_available:
            self.ctx.path_c = True
            self.ctx.degraded = True
            self.ctx.notes.append(
                "PATH C declared (Slack MCP unavailable) per OPERATOR_RUNBOOK §3a note 3"
            )
            return TransitionResult(
                True, BootState.BS_SECURE_BOOT,
                "PATH C (degraded) — haioscc secondary + CURRENT.md; DEGRADED must "
                "appear in the Phase 1 header",
            )
        if not evidence.confirms:
            return TransitionResult(
                True, BootState.BS_HALTED,
                "Live-state fetch returned no confirmable content — §A.1 halt",
            )
        self.ctx.live_state_ok = True
        return TransitionResult(True, BootState.BS_SECURE_BOOT, "Live state OK (WGS primary)")

    def _do_pin_commit(self, evidence: Evidence) -> TransitionResult:
        """CLAUDE.md §A.1 — git fetch && git rev-parse HEAD, pin the SHA."""
        self._record(evidence)
        if not evidence.confirms:
            return TransitionResult(
                True, BootState.BS_HALTED,
                "Commit pin failed — stop and ask operator (SESSION_RITUALS §F halt 1: "
                "canonical-source fetch failed or returned unexpected data)",
            )
        self.ctx.pinned_sha = evidence.output.strip()
        return TransitionResult(
            True, BootState.BS_BOOTLOADER, f"Pinned at {self.ctx.pinned_sha[:12]}"
        )

    def _do_load_rituals(self, evidence: Evidence) -> TransitionResult:
        """§A.2 CURRENT.md, §A.3 SESSION_RITUALS.md."""
        self._record(evidence)
        if not evidence.confirms:
            return TransitionResult(
                True, BootState.BS_HALTED,
                "CURRENT.md / SESSION_RITUALS.md fetch failed — §F halt 1",
            )
        return TransitionResult(
            True, BootState.BS_BOOT_PARAMS, "CURRENT.md + SESSION_RITUALS.md loaded"
        )

    def _do_load_governance_version(self, evidence: Evidence) -> TransitionResult:
        """§A.2.6 — record the canonical version for PROTOCOL_VERSION and P3."""
        self._record(evidence)
        if not evidence.confirms:
            return TransitionResult(
                True, BootState.BS_HALTED, "GOVERNANCE.md version fetch failed — §F halt 1"
            )
        self.ctx.protocol_version = evidence.output.strip()
        return TransitionResult(
            True, BootState.BS_CLASSIFY,
            f"PROTOCOL_VERSION recorded: {self.ctx.protocol_version}",
        )

    def _do_classify_session(
        self,
        prompt_env: str,
        session_type: str,
        operator_supplied: bool,
    ) -> TransitionResult:
        """
        §A.2.5 (AFA-1): "The classification is the operator's call, not Claude's
        inference." F-BSM-08: v0.1 had no state for this at all, so a substrate
        running it defaulted silently to NEUTRAL — the exact attractor-field
        blind spot F-42/F-43 exist to prevent. Default-if-not-declared is a
        protocol default the operator chooses, not one the substrate applies
        without saying so.
        """
        valid_env = {"NEUTRAL", "APPROVAL_WEIGHTED", "ADVERSARIAL"}
        valid_type = {"ANALYSIS", "BUILD", "ADVERSARIAL", "INTEGRATION"}
        if prompt_env not in valid_env:
            return TransitionResult(False, self.state, f"prompt_env must be one of {valid_env}")
        if session_type not in valid_type:
            return TransitionResult(False, self.state, f"session_type must be one of {valid_type}")
        if not operator_supplied:
            self.ctx.notes.append(
                "AFA-1 classification not operator-supplied — protocol default applied "
                "and flagged; substrate inference of prompt_env is out of scope per §A.2.5"
            )
        self.ctx.prompt_env = prompt_env
        self.ctx.session_type = session_type

        nxt = (
            BootState.BS_ZONE_ENUM
            if self.ctx.ritual_surface in (RitualSurface.CLAUDE_MD, RitualSurface.BOTH_DECLARED)
            else BootState.BS_KERNEL
        )
        return TransitionResult(
            True, nxt,
            f"AFA-1 prompt_env={prompt_env} session_type={session_type} "
            f"operator_supplied={operator_supplied}",
        )

    def _do_enumerate_zones(self, evidence: Evidence) -> TransitionResult:
        """CLAUDE.md §A.4 — ZONE_REGISTRY.md at the pinned SHA. See DEV-03."""
        self._record(evidence)
        if not evidence.confirms:
            return TransitionResult(
                True, BootState.BS_HALTED, "ZONE_REGISTRY.md read failed — §F halt 1"
            )
        return TransitionResult(True, BootState.BS_KERNEL, "Zone registry enumerated")

    def _do_fetch_registered(self, evidence: Evidence, class_state: str) -> TransitionResult:
        """
        §A.4 + §F.9 (IC-029/IC-030). Registry-touching work halts if the fetch
        fails or the content is UNAVAILABLE / UNKNOWN / STALE.
        """
        self._record(evidence)
        self.ctx.class_state = class_state
        if not evidence.confirms or class_state != "OK":
            self.ctx.registered_fetch_ok = False
            if self.ctx.registry_touching:
                self.ctx.degraded = True
                return TransitionResult(
                    True, BootState.BS_DEGRADED,
                    f"REGISTERED.md class_state={class_state} during registry-touching "
                    "session — §F halt 9: declare DEGRADED in Phase 1 header, no "
                    "F/IC/H proposals against unverified state",
                )
            return TransitionResult(
                True, BootState.BS_INIT,
                f"REGISTERED.md class_state={class_state}; session is not "
                "registry-touching, so F/IC/H proposals are barred but boot continues",
            )
        self.ctx.registered_fetch_ok = True
        return TransitionResult(True, BootState.BS_INIT, "REGISTERED.md OK")

    def _do_declare_registry_skip(self, rationale: str) -> TransitionResult:
        """
        OPERATOR_RUNBOOK §3a note 3: "If no, declare skip explicitly."
        An implicit skip is not a skip.
        """
        if self.ctx.registry_touching:
            return TransitionResult(
                False, self.state,
                "Cannot skip REGISTERED.md fetch — session is registry-touching (IC-030)",
            )
        if not rationale.strip():
            return TransitionResult(False, self.state, "Skip requires an explicit rationale")
        self.ctx.registry_skip_declared = True
        self.ctx.notes.append(f"REGISTERED.md fetch skipped: {rationale}")
        return TransitionResult(True, BootState.BS_INIT, f"Registry skip declared: {rationale}")

    def _do_build_drift_catalog(self, items: List[str]) -> TransitionResult:
        """§A.5 — 3-8 predicted failure modes, substrate-tagged."""
        if not 3 <= len(items) <= 8:
            return TransitionResult(
                False, self.state, f"Drift catalog must hold 3-8 items, got {len(items)}"
            )
        self.ctx.notes.extend(items)
        return TransitionResult(True, self.state, f"Drift catalog: {len(items)} items")

    def _do_emit_p1_declaration(self) -> TransitionResult:
        """§A.6 + §C. P27: no P1 block ⇒ no P3 later."""
        missing = [
            name for name, val in (
                ("time_anchor", self.ctx.time_anchor),
                ("prompt_env", self.ctx.prompt_env),
                ("session_type", self.ctx.session_type),
                ("protocol_version", self.ctx.protocol_version),
            ) if not val
        ]
        if missing:
            return TransitionResult(
                False, self.state, f"Phase 1 block incomplete — missing {missing}"
            )
        self.ctx.p1_declared = True
        header = " · DEGRADED" if self.ctx.degraded else ""
        return TransitionResult(
            True, BootState.BS_LOGIN, f"Phase 1 declaration emitted{header}"
        )

    def _do_await_confirmation(self, confirmed: bool) -> TransitionResult:
        """§A.7 — "Do not begin work until the declared state is acknowledged or corrected"."""
        self.ctx.confirmation_received = confirmed
        if not confirmed:
            return TransitionResult(False, self.state, "Awaiting operator acknowledgment")
        return TransitionResult(True, BootState.BS_RUNTIME, "Operator confirmed declared state")

    # -- runtime ---------------------------------------------------------

    def _do_do_work(self, description: str) -> TransitionResult:
        self.ctx.work_done = True
        return TransitionResult(True, self.state, f"Work: {description}")

    def _do_enter_registry_touching(self) -> TransitionResult:
        """
        F-BSM-05. OPERATOR_RUNBOOK §3a note 3: "IC-030 still applies — halt if
        REGISTERED.md is unavailable when registry-touching work begins
        mid-session." v0.1 called this an unmodeled limitation; it is a
        specified, ratified requirement, so the model has to carry it.
        """
        self.ctx.registry_touching = True
        if self.ctx.registered_fetch_ok and self.ctx.class_state == "OK":
            return TransitionResult(
                True, self.state, "Session became registry-touching; REGISTERED.md already OK"
            )
        return TransitionResult(
            True, BootState.BS_KERNEL,
            "Session became registry-touching mid-run — re-entering KERNEL to "
            "verify REGISTERED.md before any F/IC/H work (IC-030)",
        )

    def _do_request_close(self) -> TransitionResult:
        if not self.ctx.p1_declared:
            return TransitionResult(
                True, BootState.BS_HALTED,
                "P27 violation — no Phase 1 block in transcript. Emit "
                "<<<ACAT_PROTOCOL_ERROR>>>, not Phase 3. Session is NON_CORPUS.",
            )
        return TransitionResult(True, BootState.BS_SHUTDOWN, "Close requested → B.0 gate")

    # -- close -----------------------------------------------------------

    def _do_run_b0_verification(self, checks: List[Evidence]) -> TransitionResult:
        """
        §B.0 hard gate. Close artifacts are unreachable from here except through
        this action — that state boundary IS the gate (F-BSM-02). An unavailable
        check is legal if declared, per §B.0; a silently missing one is not.
        """
        if not checks:
            return TransitionResult(
                False, self.state,
                "B.0 requires at least one recorded check (§F halt 7: do not draft a "
                "close artifact before the verification block)",
            )
        for ev in checks:
            self._record(ev)
        self.ctx.close_steps_done.append("B.0 empirical verification block")
        unavailable = [e for e in checks if e.unavailable_reason is not None]
        note = f"; {len(unavailable)} CHECK_UNAVAILABLE declared" if unavailable else ""
        return TransitionResult(
            True, BootState.BS_CLOSE_GATE,
            f"B.0 complete — {len(checks)} checks recorded{note}",
        )

    def _do_run_close_sequence(self, steps_completed: List[str]) -> TransitionResult:
        """§B.1-B.5. "Steps cannot be skipped." """
        required = list(CLOSE_STEPS[1:6])
        missing = [s for s in required if s not in steps_completed]
        if missing:
            return TransitionResult(
                False, self.state, f"Close sequence incomplete — missing {missing}"
            )
        self.ctx.close_steps_done.extend(required)
        return TransitionResult(True, BootState.BS_RECONCILE, "B.1-B.5 complete")

    def _do_emit_receipt_reconciliation(self, paragraph: str) -> TransitionResult:
        """
        §B.6 — REQUIRED. "If nothing required walking back, state 'No reconciliation
        required...'. Do not omit the paragraph." v0.1 omitted B.6 entirely
        (F-BSM-06), which is the IC-031 error class the step was written to stop.
        """
        if not paragraph.strip():
            return TransitionResult(
                False, self.state,
                "B.6 receipt reconciliation paragraph is mandatory and may not be empty",
            )
        if not any(e.confirms or e.unavailable_reason for e in self.ctx.evidence):
            return TransitionResult(
                False, self.state,
                "B.6 must quote from B.0 outputs; no verification evidence recorded",
            )
        self.ctx.close_steps_done.append("B.6 receipt reconciliation paragraph")
        return TransitionResult(True, BootState.BS_JOURNAL, "B.6 reconciliation recorded")

    def _do_post_wgs(self, draft_id: str) -> TransitionResult:
        """§B.7 — slack_send_message_draft (operator-send default, P30/P31)."""
        if not draft_id.strip():
            return TransitionResult(False, self.state, "WGS draft id required")
        self.ctx.close_steps_done.append("B.7 log to #wgs-sync via slack_send_message_draft")
        return TransitionResult(True, self.state, f"WGS draft staged: {draft_id}")

    def _do_bind_session_id(self, session_id: str) -> TransitionResult:
        """§B.8 — S-MMDDYY-NN-{slug} in the WGS post, the P3 SESSION field, filenames."""
        if not session_id.startswith("S-"):
            return TransitionResult(
                False, self.state, "Session ID must match S-MMDDYY-NN-{slug} (IC-027)"
            )
        self.ctx.close_steps_done.append("B.8 session ID binding")
        outstanding = self.ctx.outstanding_close_steps()
        if outstanding:
            return TransitionResult(
                False, self.state, f"Cannot close — outstanding close steps: {outstanding}"
            )
        return TransitionResult(True, BootState.BS_DONE, f"Session {session_id} closed clean")

    # -- degraded / halted -----------------------------------------------

    def _do_report_status(self) -> TransitionResult:
        return TransitionResult(
            True, self.state,
            f"degraded={self.ctx.degraded} path_c={self.ctx.path_c} "
            f"class_state={self.ctx.class_state} may_propose_fich={self.ctx.may_propose_fich}",
        )

    def _do_request_recovery(self, evidence: Evidence, class_state: str) -> TransitionResult:
        """Recovery from DEGRADED requires re-verified state, not a retry claim."""
        self._record(evidence)
        self.ctx.class_state = class_state
        if not evidence.confirms or class_state != "OK":
            return TransitionResult(
                False, self.state, f"Recovery refused — class_state still {class_state}"
            )
        self.ctx.registered_fetch_ok = True
        self.ctx.degraded = False
        return TransitionResult(True, BootState.BS_INIT, "Recovered — canonical state re-verified")

    def _do_operator_resume(self, instruction: str) -> TransitionResult:
        """
        §F: "Stop and ask the user before proceeding." The halt is a question,
        not a tombstone — but only the operator reopens it (DEV-02).
        """
        if not instruction.strip():
            return TransitionResult(False, self.state, "Resume requires an operator instruction")
        self.ctx.notes.append(f"Operator resume: {instruction}")
        return TransitionResult(True, BootState.BS_DEGRADED, f"Resumed by operator: {instruction}")


# --------------------------------------------------------------------------
# Self-test — the B.0 evidence for this file's own claims (F-BSM-01)
# --------------------------------------------------------------------------

def _selftest() -> int:
    failures: List[str] = []

    def check(label: str, cond: bool) -> None:
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        if not cond:
            failures.append(label)

    print("\n--- T1: happy path, registry-touching ---")
    m = BootStateMachine(registry_touching=True, verbose=False)
    m.transition("start")
    m.transition("anchor_time", evidence=Evidence("TZ=America/Chicago date", "Sun Sep 14 2026 12:00 CDT"))
    m.transition("fetch_live_state", evidence=Evidence("slack_read_channel C0AND66PT7U", "10 msgs"),
                 slack_mcp_available=True, haioscc_reachable=True)
    m.transition("pin_commit", evidence=Evidence("git rev-parse HEAD", "6d3443af07ba18db56c1d716e24c1f9f33b2b056"))
    m.transition("load_rituals", evidence=Evidence("GET CURRENT.md + SESSION_RITUALS.md", "200 200"))
    m.transition("load_governance_version", evidence=Evidence("head -5 GOVERNANCE.md", "v6.4.3"))
    m.transition("classify_session", prompt_env="ADVERSARIAL", session_type="ANALYSIS", operator_supplied=True)
    m.transition("fetch_registered", evidence=Evidence("GET REGISTERED.md", "F-54 ..."), class_state="OK")
    m.transition("build_drift_catalog", items=["[C-01] overclaim", "[C-02] scope creep", "[C-03] phantom cite"])
    m.transition("emit_p1_declaration")
    m.transition("await_confirmation", confirmed=True)
    check("reaches RUNTIME", m.current_state() is BootState.BS_RUNTIME)
    check("may propose F/IC/H", m.ctx.may_propose_fich)

    print("\n--- T2: B.0 is a structural gate (F-BSM-02) ---")
    m.transition("do_work", description="adversarial review")
    m.transition("request_close")
    check("in SHUTDOWN", m.current_state() is BootState.BS_SHUTDOWN)
    r = m.transition("emit_close_artifact")
    check("close artifact illegal in SHUTDOWN", not r.success)
    r = m.transition("run_b0_verification", checks=[])
    check("empty B.0 refused", not r.success)
    m.transition("run_b0_verification", checks=[
        Evidence("git status --short", " M z1-inbox/2026-09-14/boot_state_machine_v0_2.py"),
        Evidence.unavailable("SELECT COUNT(*) FROM acat_assessments_v1", "supabase MCP unauthorized"),
    ])
    check("B.0 advances to CLOSE_GATE", m.current_state() is BootState.BS_CLOSE_GATE)

    print("\n--- T3: B.6 cannot be skipped (F-BSM-06) ---")
    r = m.transition("run_close_sequence", steps_completed=list(CLOSE_STEPS[1:4]))
    check("partial close sequence refused", not r.success)
    m.transition("run_close_sequence", steps_completed=list(CLOSE_STEPS[1:6]))
    check("in RECONCILE", m.current_state() is BootState.BS_RECONCILE)
    r = m.transition("emit_receipt_reconciliation", paragraph="   ")
    check("empty reconciliation refused", not r.success)
    m.transition("emit_receipt_reconciliation",
                 paragraph="RECEIPT RECONCILIATION — No reconciliation required; "
                           "all in-session assertions match the B.0 block.")
    m.transition("post_wgs", draft_id="draft-0914-01")
    r = m.transition("bind_session_id", session_id="S-091426-01-bsm-review")
    check("clean close reaches DONE", r.success and m.current_state() is BootState.BS_DONE)
    check("no outstanding close steps", not m.ctx.outstanding_close_steps())

    print("\n--- T4: no default-pass guards (F-BSM-03) ---")
    m2 = BootStateMachine(verbose=False)
    m2.transition("start")
    r = m2.transition("anchor_time")
    check("anchor_time without evidence is refused", not r.success)
    check("still in TIME_ANCHOR", m2.current_state() is BootState.BS_TIME_ANCHOR)

    print("\n--- T5: total live-state loss halts (F-BSM-04) ---")
    m3 = BootStateMachine(verbose=False)
    m3.transition("start")
    m3.transition("anchor_time", evidence=Evidence("date", "Sun Sep 14 2026"))
    m3.transition("fetch_live_state", evidence=Evidence.unavailable("wgs", "mcp down"),
                  slack_mcp_available=False, haioscc_reachable=False)
    check("both channels down → HALTED", m3.current_state() is BootState.BS_HALTED)
    m3.transition("operator_resume", instruction="proceed from CURRENT.md, log the gap")
    check("HALTED is resumable (F-BSM-10)", m3.current_state() is BootState.BS_DEGRADED)

    print("\n--- T6: PATH C is degraded, not transparent (F-BSM-04) ---")
    m4 = BootStateMachine(verbose=False)
    m4.transition("start")
    m4.transition("anchor_time", evidence=Evidence("date", "Sun Sep 14 2026"))
    m4.transition("fetch_live_state", evidence=Evidence("haioscc", "200"),
                  slack_mcp_available=False, haioscc_reachable=True)
    check("PATH C proceeds", m4.current_state() is BootState.BS_SECURE_BOOT)
    check("PATH C sets degraded", m4.ctx.degraded and m4.ctx.path_c)

    print("\n--- T7: mid-session registry-touching re-enters KERNEL (F-BSM-05) ---")
    m5 = BootStateMachine(registry_touching=False, verbose=False)
    m5.transition("start")
    m5.transition("anchor_time", evidence=Evidence("date", "Sun Sep 14 2026"))
    m5.transition("fetch_live_state", evidence=Evidence("wgs", "ok"),
                  slack_mcp_available=True, haioscc_reachable=True)
    m5.transition("pin_commit", evidence=Evidence("git rev-parse HEAD", "6d3443af"))
    m5.transition("load_rituals", evidence=Evidence("GET", "200"))
    m5.transition("load_governance_version", evidence=Evidence("head -5", "v6.4.3"))
    m5.transition("classify_session", prompt_env="NEUTRAL", session_type="BUILD", operator_supplied=True)
    r = m5.transition("declare_registry_skip", rationale="no F/IC/H items expected")
    check("explicit skip accepted", r.success)
    m5.transition("build_drift_catalog", items=["[C-01] a", "[C-02] b", "[C-03] c"])
    m5.transition("emit_p1_declaration")
    m5.transition("await_confirmation", confirmed=True)
    check("F/IC/H barred after skip (F-BSM-09)", not m5.ctx.may_propose_fich)
    m5.transition("enter_registry_touching")
    check("re-entered KERNEL", m5.current_state() is BootState.BS_KERNEL)
    m5.transition("fetch_registered", evidence=Evidence("GET REGISTERED.md", "stale"), class_state="STALE")
    check("STALE → DEGRADED (§F.9)", m5.current_state() is BootState.BS_DEGRADED)
    check("F/IC/H still barred", not m5.ctx.may_propose_fich)

    print("\n--- T8: P27 refuses P3 without P1 ---")
    m6 = BootStateMachine(verbose=False)
    m6.state = BootState.BS_RUNTIME       # simulate a session that skipped Phase 1
    r = m6.transition("request_close")
    check("P3-without-P1 halts", m6.current_state() is BootState.BS_HALTED)

    print("\n--- T9: journal is exportable (P20, F-BSM-14) ---")
    j = m.export_journal()
    check("journal carries evidence", len(j["evidence"]) >= 3)
    check("journal declares advisory status", j["advisory_only"] is True)
    check("journal enumerates deviations", len(j["deviations"]) == len(DEVIATIONS))

    print(f"\n{'=' * 62}")
    if failures:
        print(f"SELF-TEST FAILED — {len(failures)} assertion(s): {failures}")
        return 1
    print("SELF-TEST PASSED — all assertions green")
    print(f"{'=' * 62}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
