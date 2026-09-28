# AUTHORIZATION_EVIDENCE_MAPPING.md — Authorization & Evidence Assurance → Executable Checks
## Layer 4: Assurance Questions → Executable Checks

**Mapping Date:** 2026-09-27
**Authority:** Ratified by Z2 (Night), 2026-09-28 — see REGISTERED.md Q-AUTHORIZATION-EVIDENCE-MAPPING-01 for the ratification record and hash
**Status:** RATIFIED (Q-AUTHORIZATION-EVIDENCE-MAPPING-01) — ratifying this map does not itself resolve the open items in Action Items #2–5 below; those remain on their own tracks per the REGISTERED.md ratification's own "Ratified Scope" note
**Code:** [`authorization_evidence.py`](./authorization_evidence.py) (stdlib only, one function) · standing check: `python3 authorization_evidence.py --smoke-test`

---

## Executive Summary

A set of authorization-and-evidence assurance questions was put to this repository: is the system authorized to operate, does a given actor have sufficient evidence and authority for a given action right now, does it stay inside a safe envelope, was there enough epistemic justification to grant the action, how is authority demonstrated when evidence is stale or conflicting and the action is irreversible, is the system sufficiently assured, can it detect its own protocol violations, can it establish provenance and custody, does it render one of eight decision primitives, and does it prevent one model of reality from monopolizing the control loop.

These are not hypothetical. HumanAIOS already has mechanisms answering most of them, built for other stated reasons (anti-cascade, IC-030, RNOLA's authority boundary, the gate registry) and never assembled into one index against this question list. This document is that index. Following the rule Layer 3 set: a row that ends in nothing runnable is prose, not a mapping, and does not belong here. Where no artifact exists — one case, §13 — this document adds the smallest one that runs.

| Layer | Document | Maps | Onto |
|:---|:---|:---|:---|
| 1 | `FRAMEWORK_MAPPING.md` | 5 AI engineering concepts | Z-roles, governance files, CI gates |
| 2 | `BOOT_PROCESS_MAP.md` | Session rituals §A / §B | Boot-chain stages, resource states |
| 3 | `FIVE_RINGS_MAPPING.md` | Musashi's five books | Functions, commands, gates |
| 4 | `AUTHORIZATION_EVIDENCE_MAPPING.md` (this) | Authorization & evidence assurance questions | Gates, schemas, ledgers, one new function |

**Reading rule.** *Question* paraphrases the assurance question in one line. *Mechanism* is what already answers it, cited by file. *Status* is honest: ANSWERED (a real, running check), PARTIAL (specified but not fully enforced — cited as such, not hidden), or GAP (nothing exists; this document proposes the minimum).

---

## 1. Is this system authorized to operate at all?

**Mechanism:** `ADMIRAL_AUTHORITY_CONFIRMATION.md` is the root authority record (Carly Anderson, decision `GOV-2026-07-30-GOVERNANCE-UNIFICATION`). `.github/workflows/z2_ratification_gate.yml` checks every push/PR touching governance paths against that root: `git log -1 --format=%ae` (HEAD commit author) checked against the two authorized Z2 identities in `CLAUDE.md` (`carly.r.anderson@gmail.com`, `aioshuman@gmail.com`, ratified `Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01`). `repository-admission-gate.yml` answers the same question per-repo: a zone must resolve to `ACTIVE/MAINTENANCE/WORKBENCH/CONTROL_PLANE` under `REPOSITORY_COORDINATOR_POLICY.json`, or it fails closed.

**Status: PARTIAL, honestly.** The commit-authorship check in `z2_ratification_gate.yml` is advisory (`exit 0` either branch) — it reports, it does not block. The gate's own header records that from 2026-09-10 to 2026-09-13 the file was invalid YAML (duplicate top-level `name:` key) and every one of its 122 runs completed in zero seconds with zero jobs and `conclusion=failure` — a gate that had never once executed, on the exact question this section asks. That is not a hypothetical failure mode; it is this repository's own recorded answer to "was the system ever actually authorized to operate," and the honest answer for those three days is *the check that was supposed to say so never ran*. What actually blocks merge today is narrower: Z1-inbox index integrity (`.z1-control/validate.py`) and a Seed Constitution ratification-line check — real, but smaller than "authorized to operate."

---

## 2. Does this actor, at this moment, have sufficient evidence and authority for this action?

**Mechanism:** RNOLA's five-state ladder (`docs/INTENT_OS_RNOLA_INTEGRATION.md` §1) refuses to collapse **INTENDED → PROPOSED → VERIFIED → AUTHORIZED → OBSERVED**. "Sufficient" is not a feeling; it is a specific claim about which state the action has actually reached. A green CI run is VERIFIED, not AUTHORIZED. An AI's own review of its work is PROPOSED, not AUTHORIZED. The `intent_os_operator_check_v1` schema hard-codes this at the type level: `advisory_only: const true`, `can_authorize: const false` — a record cannot even be constructed claiming to authorize anything, and `scripts/enforce_z2_z3_boundary.py` (blocking step in `rnola-governance-validation.yml`) rejects any that try.

**Status: ANSWERED**, with one honest gap: `autonomy/gates/GATE_REGISTRY.md` records **IC-050** — the orchestrator that is supposed to halt on an uncleared gate currently only warns and continues through every phase. A gate existing in the codebase but not in enforced runtime behavior is exactly "this actor had authority on paper but not in fact at this moment," and the registry names it as an open blocking prerequisite rather than papering over it.

---

## 3. Is the system remaining inside a defined safe envelope?

**Mechanism:** The envelope is the anti-cascade rule set (`MOLT_STATE.md`, `molt_cycle.py`): one open molt per constant, K=3 open system-wide, freeze after two consecutive reverts on the same constant (Z2 Tier-2 ruling required to reopen), no bypassing Priority Queue rank. `ZONE_REGISTRY.md` per-zone resource caps and `behavior_spec.json` Z3 agent caps are the same envelope at the zone/agent level. `render_decision()`'s `in_envelope` signal (§13) is this check, composed.

**Status: PARTIAL.** `molt_cycle.py`'s `check_anti_cascade_rules()` is currently a stub returning a static all-clear — the rule text is real and lives in `MOLT_STATE.md` and CI, but the function named to enforce it in code does not yet do the check itself. Cited here rather than assumed fixed.

---

## 4. Was there enough epistemic justification for granting the action?

**Mechanism:** The falsifier doctrine, as code: `Claim(statement, falsifier).stands()` in `five_rings.py` — a claim only stands if its stated falsifier does not trip. `FIVE_RINGS_MAPPING.md`'s own line for this: *"the falsifier is the shape of the void around a claim — a claim that cannot be shown false claims nothing."* `PRIORITY_QUEUE.md`'s admission predicate makes evidence one of five **independent, ANDed** conjuncts — `READY(work) = AUTHORITY ∧ DEPENDENCIES ∧ RESOURCES ∧ EVIDENCE ∧ SAFETY` — so authority alone (a capability) never substitutes for evidence, and vice versa.

**Status: ANSWERED.**

---

## 5. Permission exists, but evidence is stale, two sources conflict, and the action is irreversible — how is evidence demonstrated for authority?

This is `render_decision()`'s reason for existing (§13): stale and conflicting are different failures with different exits.

**Conflicting sources:** `divergence-detect.yml` (daily cron) is the existing mechanical detector — it builds a consistency matrix from `GOVERNANCE_RATIFICATIONS_REGISTRY.yaml` and `AUTHORITY_ASSIGNMENTS.yaml` and exits non-zero on a HIGH-severity divergence. `CLAUDE.md`'s **AMBIGUITY** callout ("two Z2 decisions conflict on same topic") is the human-legible name for the same condition.

**Stale evidence:** IC-030 ("live-fetch, pin SHA, never reason from a cached belief") is the doctrine; `know_the_void(fetch)` in `five_rings.py` is its executable form — a failed or unattempted fetch returns the `VOID` sentinel, never a fabricated value standing in for fresh evidence.

**Irreversible + either failure:** `render_decision()` composes these three signals and does not return ACT. If the action is also consequential (crosses a Z1→Z2/Z3 authority boundary), the answer is ESCALATE, not ACQUIRE_EVIDENCE — a human resolves a conflict on an irreversible action; code does not adjudicate which of two disagreeing sources to trust and then proceed.

**Status: ANSWERED** for detection (divergence-detect, know_the_void); the composition into one verdict is the new part, §13.

---

## 6. Is this system sufficiently assured?

**Mechanism:** `REGISTERED.md` **F-64 — "Assurance Is Accumulating; Evidence Is Not"** (ratified, `Q-RBE-01`, 2026-09-13) already asked this question of the tree mechanically and answered it: 94 ratified artifacts (RAT-art), 165 `NF_LEDGER.jsonl` events (106 PIN, 58 TOKEN, 1 OPEN) — and **zero** sourced evidence rows (EVID-row). Every pin is a forecast; none has been resolved against a tree read, so Brier score is undefined for the calibration programme this whole apparatus exists to run.

**Status: ANSWERED, and the honest answer is no, not yet.** This is not a defect in this document's argument — it is the correct behavior of the system it is documenting: distinguishing "we have ratified a lot" (assurance, a stock of artifacts) from "we have resolved anything against reality" (evidence, a stock of closed forecasts) is exactly Five Rings' Void teaching ("by knowing what exists you know what does not"). A system that could not produce F-64 about itself would be the less assured one.

---

## 7. Does this actor have sufficient warrant and authority to perform this action **now**?

**Mechanism:** "Now" is checked at the exact commit that will merge, not at some earlier ratification: `z2_ratification_gate.yml`'s authorship check reads `git log -1 --format=%ae` — HEAD, at gate time — against the CLAUDE.md allowlist. `BOOT_PROCESS_MAP.md`'s resource-based model makes the same point structurally: authority does not carry forward on a clock ("Z2 ratifies when capacity permits," not "within 48h") — it is re-established at the moment of use, not assumed from the moment of grant.

**Status: PARTIAL** — see §1: the specific check is advisory today, and the three-day silent-failure incident is the concrete counterexample to "now" ever being safely assumed from "once, in the past."

---

## 8. Does activity validation identify limitations/errors, assess deterioration, and determine when to recalibrate?

**Mechanism:** The molt cycle's MEASURED state (`MOLT_STATE.md`) is exactly this: Brier score computed over the pinned observation set, KEEP if the falsifier held, REVERT (deterioration confirmed) if it tripped. Recalibration timing is itself evidence-gated, not clock-gated, under `Q-MOLT-TEMPORAL-PURITY-01`'s **`MEASUREMENT_STARVED`** predicate — fires when the pinned observation set has not grown across two consecutive resource censuses, and its effect is a **GAUGE** callout to Z2, never an automatic close. `verified_tacit_gate.py`'s `WARN_THRESHOLD=5` / `ESCALATE_THRESHOLD=10` unresolved-claim counters (reused from `carry_tracker_v1_0`) are the same pattern at the individual-verifier level: deterioration is a counted, thresholded state, not a vibe.

**Status: ANSWERED.**

---

## 9. Observed divergence → challenge → inside the authorized adaptation envelope? → validate → modify → observe → retain/rollback — not naive failure → modify

**Mechanism:** This is the molt state machine, read state-by-state instead of paraphrased:

| This document's step | `MOLT_STATE.md` state | What actually happens |
|:---|:---|:---|
| Observed divergence | (pre-PROPOSED) | GAUGE/DRIFT callout or a REGISTERED.md finding |
| Challenge | `PROPOSED` | Z1 proposes a molt_candidate with a stated falsifier |
| Inside the authorized adaptation envelope? | anti-cascade check at `PROPOSED → ACCEPTED` | K=3 not exceeded, constant not frozen, one open molt on this constant |
| Validate | `ACCEPTED → RATIFIED` | Z2 signs `sha256(molt_candidate \| by \| at \| molt_id)` |
| Modify | `APPLIED` | code applies the ratified constant change |
| Observe | `MEASURED` | falsifier tested over the pinned observation set |
| Retain / rollback | `KEPT` / `REVERTED` | prediction held (permanent) or falsifier tripped (constant restored to `prior_value`, F/IC filed) |

The gap between this and naive "failure → modify" is precisely the states this table has that a bare loop does not: `REJECTED`, `CONTESTED`, and the frozen-constant stop are all legitimate places to halt between "something diverged" and "something changed." Fire's *mountain-sea change* law — "never the same technique a third time; when it has failed twice, change completely" — is named in `FIVE_RINGS_MAPPING.md` as *being* anti-cascade rule 4, not merely resembling it.

**Status: ANSWERED.**

---

## 10. Can the system auto-identify these seven patterns?

| Pattern | Detector | Note |
|:---|:---|:---|
| Unauthorized paths | `repository-admission-gate.yml` (fail-closed, reads only default-branch policy, never PR-head code — closes the self-admission exploit) | ANSWERED |
| Skipped approvals | `rnola-governance-validation.yml` → `scripts/enforce_z2_z3_boundary.py` (blocking) | ANSWERED for the RNOLA boundary specifically |
| Unexpected delegation | `docs/RNOLA_FAILURE_MODES.md` #1 (operator-check treated as authorization) and #7 (Z3 executor authority bleeds through learning records) — both name a concrete detection query | ANSWERED as *specified*; detection is a documented grep/audit procedure, not yet a standing CI gate |
| Repeated escalation | `.claude/skills/pr-manager/escalation_contract.py` tracks `list_pending_escalations` / `list_expired_escalations` against a 48h window; F-62 is the system noticing its *own* escalation channel is oversubscribed (130 open items, ~26h of measured Z2 work against an undeclared capacity) | ANSWERED |
| Missing human intervention | F-63 — the queue formula had no cost term, so it could never say "no" to more work regardless of who was available to review it; fixed by the ratified `UNPRICED_ROW_POLICY = REFUSED_TO_START` | ANSWERED, and the fix is dated (2026-09-13) |
| Intervention that came too late | `BOOT_PROCESS_MAP.md` replaced "Z2 responds within 48h" with "ratifies when capacity permits" — which removes false lateness, but F-62 documents that "too late" is still undefined without Z2 declaring an actual capacity number | PARTIAL, honestly (capacity was declared 2026-09-13 at 600 RAT-min/week per F-62; whether that number holds is itself a molt to be measured) |
| Model behavior diverging from protocol | `agent-principle-compliance-check.yml`, `behavioral-compliance.yml`, `divergence-detect.yml`; `MOLT_STATE.md`'s under-claim falsifier via `molt-tier-check.yml` — a PR whose author claims a lower molt tier than `tools/molting_protocol_diff_v1_0.py` measures **is** a quantified instance of this pattern, target < 5% over a rolling 30-day window | ANSWERED |

**Cross-cutting gap, named rather than hidden:** `autonomy/gates/GATE_REGISTRY.md`'s **IC-050** is a documented case of pattern #7 one layer down — a gate exists in the codebase and is not enforced in the runtime that is supposed to halt on it. The registry itself calls out the parallel to IC-041 ("a gate that exists in the codebase but not in enforced behavior") and sequences the fix as a named prerequisite rather than treating "gate count" as the success metric.

---

## 11. Can the system establish provenance, custody, and transformation history of the evidence used to reconstruct what happened?

**Mechanism:** Distributed but real, not a single API: `NF_LEDGER.jsonl` entries hash-chain (`prior_hash` / `hash` fields per row); `ratification_hash = sha256(candidate | by | at | decision)` pins the exact ratified bytes (`.z1-control/ratify.py`); git SHAs pinned at session open (IC-030) are the version identifier RNOLA's own ten-concept cross-map names as "Provenance" (`docs/INTENT_OS_RNOLA_INTEGRATION.md` §2); `persist_or_void(record, ledger_path)` in `five_rings.py` is the code-level enactment of the doctrine "what is not in the ledger did not happen" — B.6 receipt reconciliation (`SESSION_RITUALS.md`, `BOOT_PROCESS_MAP.md` §B.1–B.2) is the same discipline applied to session claims specifically, walking claim against tree and filing **RECEIPT-GAP** on any mismatch.

**Status: ANSWERED**, distributed across four mechanisms rather than one schema — worth a Z2 decision (§ Action Items) on whether that should stay distributed or consolidate once the Witness Ledger (still `Q-INTENT-OS-WITNESS-LEDGER-01`, **not yet ratified**) is decided.

---

## 12. Does the system validate the boundaries used in defining a thread for consequential agency?

**Mechanism:** Z1/Z2/Z3 (`CLAUDE.md`) is the coarse boundary; RNOLA's AUTHORIZED state is the fine one — a thread of action becomes consequential exactly where it would cross from PROPOSED/VERIFIED into AUTHORIZED, and RNOLA's entire falsifier doctrine (§12, its SKILL.md) exists to keep that crossing visible rather than blurred by vocabulary. `autonomy/gates/GATE_REGISTRY.md`'s five typed exceptions — `SameSubstrateRejection`, `CredentialMissing`, `ClaimNotAdmissible`, `OutcomeAsymmetryRejection`, `SupabaseUnreachable` — are this boundary as actual raised exceptions, each guarding one specific way a thread of agency could overreach its authorized scope.

**Status: PARTIAL** — same IC-050 caveat as §2 and §10: the boundary is well-typed in the gate files themselves; whether the orchestrator halts on a raised one, system-wide, is the open item.

---

## 13. Does the system render ACT / ABSTAIN / ESCALATE / ACQUIRE EVIDENCE / REDUCE SCOPE / MAKE REVERSIBLE / SANDBOX / ROLL BACK?

**Status: GAP, until this document.** No file in the repository names this taxonomy. The closest existing primitives — `Stance` (`UPPER`=commit, `MIDDLE`=observe, `LOWER`=recover, `LEFT`=route around, `RIGHT`=escalate; `five_rings.py`), `EscalationContract` (a real 48h-window ESCALATE, `.claude/skills/pr-manager/escalation_contract.py`), molt REVERT (ROLL_BACK), and `Claim.stands()` (a partial ACQUIRE_EVIDENCE precursor) — are each one primitive, not the set, and none of them compose.

`authorization_evidence.py`'s `render_decision()` is the minimum artifact that closes this gap: one function, nine boolean signals (all already computed elsewhere in this repo — see the table below), returning exactly one of the eight primitives plus its reason.

| Signal | Cautious default | Where it already comes from |
|:---|:---|:---|
| `frozen` | `False` | `anti_cascade_check.frozen_constant` (`MOLT_STATE.md`) |
| `capability_present` | `False` | Z1/Z2/Z3 grant (`CLAUDE.md`) or INTENT-OS capability signature |
| `in_envelope` | `False` | K=3, zone resource cap (`ZONE_REGISTRY.md`), `behavior_spec.json` |
| `evidence_fresh` | `False` | live-fetch-and-pin this session (IC-030) |
| `evidence_conflicting` | `False` | `divergence-detect.yml` consistency matrix, **AMBIGUITY** callout |
| `reversible` | `False` | a stated undo / prior_value restore path |
| `sandboxable` | `False` | a dry-run / non-committing rehearsal exists |
| `consequential` | `True` | crosses PROPOSED → AUTHORIZED (RNOLA) |
| `human_available` | `True` | a Z2 ratifier reachable inside the real decision window |

Every default is the cautious one, so an incompletely-wired caller degrades toward ABSTAIN/ESCALATE, never toward ACT. `python3 authorization_evidence.py --smoke-test` exercises all eight branches; each scenario in the smoke test names which repo doctrine it encodes.

---

## 14. Is obtaining another piece of evidence actually worth the time, money, or delay?

**Mechanism:** `PRIORITY_QUEUE.md`'s Resource-Based Economy already ratified the cost side of this exact question as **F-63 — "A Benefit-Only Queue Cannot Reject Work"**: the incumbent formula `score = impact + Σimpact(unblocks)` had no cost term, so no row — including a row asking for more evidence — could ever be "too expensive." The ratified fix (`QUEUE_SCORING_MODE` molt, 2026-09-13) switches to `resource` mode with `UNPRICED_ROW_POLICY = REFUSED_TO_START`: an unpriced ask for more evidence is refused to start, not silently granted. `RESOURCE_UNITS.yaml` carries the demand priors that make "worth it" a computed yield-per-constraint-minute rather than an intuition.

**Status: ANSWERED**, and dated — this is a live example of the system answering its own version of this question in the same 2026-09-13 session that produced F-64's honest "not yet."

---

## 15. Does the system prevent one model of reality from monopolizing the control loop?

**Mechanism, ratified:** `Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01` already splits sole ratification across two identities (`carly.r.anderson@gmail.com`, `aioshuman@gmail.com`) rather than one. `five_rings.py`'s `twofold_gaze(kan, ken)` — perception of the whole *and* sight of the detail, "neither alone" — and Wind's named anti-pattern `fixed_gaze` ("single-metric fixation... tunnel vision on one log line") are the executable and the anti-pattern sides of the same rule. F-50 ("Parallel Instrument Independence as Convergent Validity Prerequisite") is the calibration-program version: no single instrument's read is trusted as ground truth.

**Mechanism, not yet ratified — named honestly:** `REGISTERED.md`'s `H-CAND-GOVERNANCE-CAPTURE-SURFACE-01` is this exact question asked at the governance root: a sole Z2 ratifier (N=1) is hypothesized to be the minimum-cost capture path (citing the XZ Utils pattern and bus-factor-1 corpus data), with a concrete Tier 0/1/2 remedy ladder (status quo → external-reviewer veto-comment on root-class decisions → 2-of-3 threshold on doctrine paths) modeled on TUF's threshold-compromise design and DNSSEC's affiliation-exclusion quorum. Its own promotion gate (a red-team tabletop with documented cost deltas, plus a separate Z2_CHARTER amendment PR) has not been met.

**Status: PARTIAL, honestly.** The two-identity dual-authority model is real and ratified. The deeper structural question — does *any* number of colluding-or-captured identities still leave one model of reality in sole control — is a CANDIDATE hypothesis with a designed remedy that Z2 has not yet promoted. Reporting this as solved would itself be the failure mode §6 exists to catch.

---

## 16. Who may act, on what evidence, under what uncertainty, inside what constraints, under whose authority, with what means of intervention, and what did reality subsequently teach it?

One `NF_LEDGER.jsonl` molt entry, annotated against each clause — this is the full tuple already recorded per ratified molt, not a new schema:

```json
{
  "molt_id": "M-20260916-0001",                          // WHAT (unit of action)
  "constant": "behavior_spec.json:impact_dial",           // WHAT, precisely
  "z2_ratifier": "carly.r.anderson@gmail.com",            // UNDER WHOSE AUTHORITY
  "prediction": {"metric": "Brier", "target": 0.15,       // ON WHAT EVIDENCE (a bounded,
                 "falsifier": "Brier >= 0.20 at closure"}, //   falsifiable claim, not a vibe)
  "ratification_hash": "sha256(...)",                     // WHO MAY ACT (the signature IS the "who")
  "anti_cascade_check": {"open_molt_count": 1,            // INSIDE WHAT CONSTRAINTS
                          "rank_in_queue": 4,
                          "frozen_constant": false},
  "brier_actual": 0.14,                                   // WHAT UNCERTAINTY (measured, not assumed)
  "outcome": "KEEP"                                        // WHAT REALITY TAUGHT IT
}
```

The one clause with no field above is **means of intervention** — that lives outside the ledger row, in `EscalationContract` (§10) and the molt REVERT path itself (`prior_value` restoration is the means; the ledger row is only the record that it fired).

**Status: ANSWERED**, as a read of an existing schema rather than a new one.

---

## Gap Analysis (at a glance)

| § | Question | Status |
|:--|:---|:---|
| 1 | Authorized to operate at all | PARTIAL — advisory check; documented 3-day silent gate failure |
| 2 | Actor/moment/action sufficiency | ANSWERED — with IC-050 as a named runtime gap |
| 3 | Safe envelope | PARTIAL — rules real, enforcement stub in `molt_cycle.py` |
| 4 | Epistemic justification | ANSWERED |
| 5 | Stale/conflicting + irreversible | ANSWERED (detection) + this doc (composition) |
| 6 | Sufficiently assured | ANSWERED — honest **no** (F-64) |
| 7 | Warrant/authority *now* | PARTIAL — same advisory-check caveat as §1 |
| 8 | Validation/deterioration/recalibration | ANSWERED |
| 9 | Divergence→envelope→validate→modify→observe→retain/rollback | ANSWERED |
| 10 | 7-pattern detection surface | ANSWERED (6/7) + IC-050 named |
| 11 | Provenance/custody/transformation history | ANSWERED (distributed) |
| 12 | Consequential-agency boundaries | PARTIAL — typed, not fully enforced (IC-050) |
| 13 | 8-way decision taxonomy | **GAP — closed by this document** (`authorization_evidence.py`) |
| 14 | Evidence worth the cost | ANSWERED, dated 2026-09-13 |
| 15 | No single model of reality | PARTIAL — dual-authority ratified; N-of-M capture remedy still CANDIDATE |
| 16 | Full attribution tuple | ANSWERED |

Nine of sixteen ANSWERED outright, five PARTIAL with the specific open item named rather than glossed, one genuine GAP closed here. That ratio is itself the evidence this document is not marketing copy: F-64 already established that this repository reports its own shortfalls, and this table follows the same rule.

---

## Falsifier for this mapping

A row above that cites a mechanism which does not actually run, or reports ANSWERED where the cited file itself says PARTIAL/PROPOSED, falsifies its own row and the row is struck. `python3 authorization_evidence.py --smoke-test` (all 8 decisions exercised) is the standing check for §13; every other row's check is the CI gate or file already named in it — this document adds no new claim about their state beyond what they already say about themselves.

---

## Action Items for Z2 Ratification

1. ~~Ratify `AUTHORIZATION_EVIDENCE_MAPPING.md` as Layer 4 of the concept-to-code stack (Q-AUTHORIZATION-EVIDENCE-MAPPING-01).~~ **Done** — ratified by Z2 (Night), 2026-09-28; see REGISTERED.md.
2. Decide whether `render_decision()` runs advisory (posts its verdict, does not block) or blocking, and at which gate (candidate host: alongside `enforce_z2_z3_boundary.py` in `rnola-governance-validation.yml`, or a new step in `z2_ratification_gate.yml`).
3. Decide whether the §1/§7 advisory authorship check in `z2_ratification_gate.yml` should be made blocking, given the documented 122-run silent-failure precedent this document cites in §1.
4. Decide whether `molt_cycle.py`'s `check_anti_cascade_rules()` stub (§3) should be prioritized ahead of new envelope-consuming code such as `render_decision()`'s `in_envelope` signal, since the latter is only as honest as the former.
5. Note, do not re-litigate here: IC-050 (orchestrator warns instead of halting) is cited in §2, §10, §12 as a standing blocking prerequisite already registered in `autonomy/gates/GATE_REGISTRY.md` — its sequencing is that document's decision, not this one's.

---

## Metadata

```yaml
metadata:
  layer: 4
  stack: ["FRAMEWORK_MAPPING.md", "BOOT_PROCESS_MAP.md", "FIVE_RINGS_MAPPING.md", "AUTHORIZATION_EVIDENCE_MAPPING.md"]
  code: "authorization_evidence.py (stdlib only, one function: render_decision)"
  exported_primitives: 8
  authority: "Ratified by Z2 (Night), 2026-09-28"
  candidate_id: "Q-AUTHORIZATION-EVIDENCE-MAPPING-01"
  ratification_hash: "d44b986feb44aab056480650886575f98f011db35689a10b8be86f1f7e0fa23a"
  ratification_record: "REGISTERED.md, Q-AUTHORIZATION-EVIDENCE-MAPPING-01 / Z2 Ratification — 2026-09-28"
  cites_findings: ["F-62", "F-63", "F-64", "H-CAND-GOVERNANCE-CAPTURE-SURFACE-01"]
  cites_open_items: ["IC-050", "Q-MOLT-TEMPORAL-PURITY-01", "Q-INTENT-OS-WITNESS-LEDGER-01 (not yet ratified)"]
  last_updated: "2026-09-28T00:00:00Z"
```
